/*
 * FOA node firmware for the ESP32-DevKitC testbed (Arduino-ESP32 core 3.x).
 *
 * Each node
 *   1. sends telemetry over UDP to the laptop and listens for incoming packets (the laptop's
 *      poisoner sends crafted traffic here),
 *   2. keeps Kitsune-style damped statistics of its own outgoing and incoming packets and samples a
 *      60-feature vector every SAMPLE_MS, projected into the fleet's shared 10-D space,
 *   3. calibrates its detector on-device from the first CAL_CYCLES clean cycles,
 *   4. every BATCH samples runs one learning cycle: propose an update (signature-free core rule),
 *      broadcast it as a 68-byte HMAC-authenticated frame over ESP-NOW, collect peers' frames for
 *      GOSSIP_WAIT_MS, apply the Fleet-Orthogonal Adaptation step,
 *   5. prints one CSV line per cycle over Serial with the detector state and the time each stage
 *      took, for the laptop collector and for alignment with the INA219 energy log.
 *
 * Build:   arduino-cli compile --fqbn esp32:esp32:esp32 firmware/esp32_foa
 * Per node: add --build-property "build.extra_flags=-DNODE_ID=<n>"
 * Calibration logging (RAW lines for fit_calibration.py): add -DCALIB_LOG
 */
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_now.h>
#include <esp_wifi.h>

#include "foa_core.h"
#include "foa_features.h"
#include "foa_config.h"

static foa_detector_t det;
static foa_state_t st;
static foa_params_t prm;
static foa_feat_t fx;
static WiFiUDP udp;

static float batch[BATCH * FOA_D];
static float *calbuf = nullptr, *scratch = nullptr;   /* heap, freed after calibration */
static int nb = 0, ncal = 0;
static bool calibrated = false;
static uint32_t cycle = 0, t_join = 0;

/* ESP-NOW receive path: the Wi-Fi task copies frames into a small ring, the loop verifies them. */
#define RING 32
static uint8_t ring[RING][FOA_FRAME_BYTES];
static volatile int ring_head = 0, ring_tail = 0;
static portMUX_TYPE ring_mux = portMUX_INITIALIZER_UNLOCKED;
static const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static void on_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
    (void)info;
    if (len != FOA_FRAME_BYTES) return;
    portENTER_CRITICAL(&ring_mux);
    int nxt = (ring_head + 1) % RING;
    if (nxt != ring_tail) { memcpy(ring[ring_head], data, FOA_FRAME_BYTES); ring_head = nxt; }
    portEXIT_CRITICAL(&ring_mux);
}

static bool ring_pop(uint8_t *out) {
    bool ok = false;
    portENTER_CRITICAL(&ring_mux);
    if (ring_tail != ring_head) { memcpy(out, ring[ring_tail], FOA_FRAME_BYTES); ring_tail = (ring_tail + 1) % RING; ok = true; }
    portEXIT_CRITICAL(&ring_mux);
    return ok;
}

static void send_telemetry() {
    static uint32_t seq = 0;
    char msg[96];
    int n = snprintf(msg, sizeof msg, "{\"node\":%d,\"seq\":%lu,\"t\":%lu,\"v\":%.2f}", NODE_ID,
                     (unsigned long)seq++, (unsigned long)millis(), 20.0f + 0.01f * (float)(esp_random() % 500));
    udp.beginPacket(IPAddress(COLLECTOR_IP), COLLECTOR_PORT);
    udp.write((const uint8_t *)msg, n);
    udp.endPacket();
    feat_observe(&fx, FEAT_OUT, (float)(n + 42), micros());   /* + UDP/IP/Ethernet headers */
}

static void sample() {
    float raw[FEAT_N], z[FOA_D];
    uint32_t now = micros();
    feat_vector(&fx, now, raw);
#ifdef CALIB_LOG
    Serial.print("RAW");
    for (int i = 0; i < FEAT_N; i++) { Serial.print(','); Serial.print(raw[i], 6); }
    Serial.println();
#endif
    feat_project(raw, FEAT_MEAN, FEAT_STD, FEAT_W, z);
    if (!calibrated) {
        memcpy(calbuf + ncal * FOA_D, z, sizeof z);
        if (++ncal == CAL_CYCLES * BATCH) {
            calibrated = foa_calibrate(&det, calbuf, ncal, scratch, 0.5f) == 0;
            free(calbuf); free(scratch); calbuf = scratch = nullptr;
            foa_state_init(&st);
            t_join = cycle;
            Serial.printf("CAL,%d,s0=%.4f,tau=%.3f,c=%.3f,beta=%.3f,f0=%.3f\n", NODE_ID, det.s0, det.tau, det.c, det.beta, det.f0);
        }
        return;
    }
    if (nb < BATCH) memcpy(batch + nb * FOA_D, z, sizeof z), nb++;
}

static void learning_cycle() {
    foa_proposal_t prop;
    uint8_t frame[FOA_FRAME_BYTES];
    static float pdmu[FOA_MAX_PEERS * FOA_D], pdls[FOA_MAX_PEERS];
    uint32_t t0 = micros();
    float u[FOA_D];
    foa_propose(&det, batch, nb, foa_consensus_direction(&st, u) ? u : NULL, &prop);
    uint32_t t1 = micros();
    foa_frame_pack(frame, NODE_ID, cycle, prop.dmu, prop.dls, prop.n_core, FOA_KEYS[NODE_ID]);
    uint32_t t2 = micros();
    esp_now_send(BROADCAST, frame, FOA_FRAME_BYTES);

    int K = 0, rejected = 0;
    uint32_t verify_us = 0, deadline = millis() + GOSSIP_WAIT_MS;
    bool seen[N_NODES] = {false};
    while ((int32_t)(deadline - millis()) > 0 && K < N_NODES - 1) {
        uint8_t f[FOA_FRAME_BYTES];
        if (!ring_pop(f)) { delay(2); continue; }
        uint8_t snd = foa_frame_sender(f);
        if (snd >= N_NODES || snd == NODE_ID || seen[snd]) { rejected++; continue; }
        uint16_t nc; uint32_t v0 = micros();
        int rc = foa_frame_verify(f, FOA_FRAME_BYTES, FOA_KEYS[snd], cycle, pdmu + K * FOA_D, pdls + K, &nc);
        verify_us += micros() - v0;
        if (rc != FOA_OK) { rejected++; continue; }
        seen[snd] = true; K++;
    }
    float dmu[FOA_D], dls;
    uint32_t t3 = micros();
    foa_step(&st, &prm, det.tau * det.s0, cycle - t_join, &prop, pdmu, pdls, K, dmu, &dls);
    foa_apply(&det, dmu, dls);
    uint32_t t4 = micros();

    float disp = 0, R = 0, C = 0;
    for (int i = 0; i < FOA_D; i++) {
        disp += (det.mu[i] - det.mu0[i]) * (det.mu[i] - det.mu0[i]);
        R += st.R[i] * st.R[i]; C += st.C[i] * st.C[i];
    }
    float rho = det.tau * det.s0;
    Serial.printf("FOA,%d,%lu,%d,%.4f,%u,%d,%.3f,%.3f,%.4f,%.4f,%.4f,%.4f,%lu,%lu,%lu,%lu,%d\n", NODE_ID, (unsigned long)cycle, nb,
                  prop.alarm, prop.n_core, K, st.lam, st.w, sqrtf(R) / rho, sqrtf(C) / rho, det.s / det.s0,
                  sqrtf(disp) / det.s0, (unsigned long)(t1 - t0), (unsigned long)(t4 - t3), (unsigned long)(t2 - t1),
                  (unsigned long)verify_us, rejected);
    cycle++;
    nb = 0;
}

void setup() {
    Serial.begin(115200);
    calbuf = (float *)malloc(sizeof(float) * CAL_CYCLES * BATCH * FOA_D);
    scratch = (float *)malloc(sizeof(float) * CAL_CYCLES * BATCH);
    if (!calbuf || !scratch) Serial.println("ERR,calibration buffers");
    foa_default_params(&prm);
    feat_init(&fx);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CHANNEL);
    for (int k = 0; k < 40 && WiFi.status() != WL_CONNECTED; k++) delay(250);
    esp_wifi_set_ps(WIFI_PS_NONE);
    udp.begin(NODE_PORT);
    if (esp_now_init() != ESP_OK) Serial.println("ERR,esp_now_init");
    esp_now_register_recv_cb(on_recv);
    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, BROADCAST, 6);
    peer.channel = 0;
    peer.encrypt = false;                       /* frames carry their own HMAC; ESP-NOW encryption has no broadcast */
    esp_now_add_peer(&peer);
    Serial.printf("BOOT,%d,wifi=%d,ch=%d,frame=%d\n", NODE_ID, WiFi.status() == WL_CONNECTED, WIFI_CHANNEL, FOA_FRAME_BYTES);
    Serial.println("HDR,node,cycle,n,alarm,n_core,peers,lam,w,R,C,s_ratio,disp,us_propose,us_step,us_mac,us_verify,rejected");
}

void loop() {
    static uint32_t last_tx = 0, last_sample = 0;
    uint32_t now = millis();
    if (now - last_tx >= TX_PERIOD_MS) { last_tx = now; send_telemetry(); }
    int len = udp.parsePacket();
    if (len > 0) {
        static uint8_t buf[1500];
        udp.read(buf, sizeof buf);
        feat_observe(&fx, FEAT_IN, (float)(len + 42), micros());
    }
    if (now - last_sample >= SAMPLE_MS) {
        last_sample = now;
        sample();
        if (calibrated && nb >= BATCH) learning_cycle();
    }
}
