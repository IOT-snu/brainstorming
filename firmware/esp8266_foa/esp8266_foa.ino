/*
 * FOA node firmware for ESP8266 (NodeMCU / Wemos D1 mini), Arduino core esp8266 3.x.
 * One firmware for all four boards; only NODE_ID differs. Each board detects what is attached:
 *   INA226 (I2C 0x40)  -> also acts as the energy monitor, printing PWR lines about 25 times a second
 *   SSD1306 OLED (I2C 0x3C) -> live status screen
 *   DHT22 on D5        -> real temperature and humidity in the telemetry (dummy values if absent)
 *   LEDs on D6 (red) and D7 (green) -> red while the last batch raised alarms, green otherwise
 *
 * Wiring (NodeMCU pin names): I2C SDA = D2 (GPIO4), SCL = D1 (GPIO5); DHT22 data = D5 (GPIO14);
 * red LED = D6 (GPIO12), green LED = D7 (GPIO13), each through a 220 ohm resistor to GND.
 *
 * Every cycle: sample traffic features, propose an update, broadcast a 92-byte HMAC frame over
 * ESP-NOW, collect peers' frames, apply the FOA step, print one CSV line ("FOA,...") over Serial.
 *
 * Build:  arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 --build-property "build.extra_flags=-DNODE_ID=0" firmware/esp8266_foa
 */
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <espnow.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#undef B0   /* Arduino's binary.h defines B0; it is a budget field name in foa_core.h */
extern "C" {
#include "foa_core.h"
#include "foa_features.h"
}
#include "foa_config.h"

#define PIN_DHT 14      /* D5 */
#define PIN_RED 12      /* D6 */
#define PIN_GREEN 13    /* D7 */
#define INA_ADDR 0x40
#define OLED_ADDR 0x3C
#define R_SHUNT 0.1f    /* "R100" on the CJMCU-226 board */

static foa_detector_t det;
static foa_state_t st;
static foa_params_t prm;
static foa_feat_t fx;
static WiFiUDP udp;
static Adafruit_SSD1306 oled(128, 64, &Wire, -1);
static DHT dht(PIN_DHT, DHT22);
static bool has_oled = false, has_ina = false, has_dht = false;
static float temp_c = 22.0f, hum = 45.0f;

static float batch[BATCH * FOA_D];
static float *calbuf = nullptr, *scratch = nullptr;
static int nb = 0, ncal = 0, cal_target = CAL_CYCLES * BATCH;
static bool calibrated = false;
static uint32_t cycle = 0, t_join = 0;
static float last_alarm = 0.0f;
static int last_peers = 0;

/* ESP-NOW receive callback runs in the system context: copy into a ring, verify in loop(). */
#define RING 16
static uint8_t ring[RING][FOA_FRAME_BYTES];
static volatile int ring_head = 0, ring_tail = 0;
static uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static void on_recv(uint8_t *mac, uint8_t *data, uint8_t len) {
    (void)mac;
    if (len != FOA_FRAME_BYTES) return;
    int nxt = (ring_head + 1) % RING;
    if (nxt != ring_tail) { memcpy(ring[ring_head], data, FOA_FRAME_BYTES); ring_head = nxt; }
}

static bool ring_pop(uint8_t *out) {
    bool ok = false;
    noInterrupts();
    if (ring_tail != ring_head) { memcpy(out, ring[ring_tail], FOA_FRAME_BYTES); ring_tail = (ring_tail + 1) % RING; ok = true; }
    interrupts();
    return ok;
}

/* ---------------------------------------------------------------- INA226 energy monitor */
static bool i2c_present(uint8_t addr) { Wire.beginTransmission(addr); return Wire.endTransmission() == 0; }

static void ina_write(uint8_t reg, uint16_t v) {
    Wire.beginTransmission(INA_ADDR); Wire.write(reg); Wire.write(v >> 8); Wire.write(v & 0xFF); Wire.endTransmission();
}

static uint16_t ina_read(uint8_t reg) {
    Wire.beginTransmission(INA_ADDR); Wire.write(reg); Wire.endTransmission(false);
    Wire.requestFrom(INA_ADDR, 2);
    uint16_t hi = Wire.read(), lo = Wire.read();
    return (hi << 8) | lo;
}

static void ina_setup() {
    if (!i2c_present(INA_ADDR) || ina_read(0xFE) != 0x5449) return;   /* manufacturer ID "TI" */
    /* averages 16, bus and shunt conversion 1.1 ms each, continuous: one result every ~35 ms */
    ina_write(0x00, 0x4527);
    has_ina = true;
}

static void ina_sample() {
    float shunt_uV = (int16_t)ina_read(0x01) * 2.5f;      /* LSB 2.5 uV */
    float bus_mV = ina_read(0x02) * 1.25f;                /* LSB 1.25 mV */
    float mA = shunt_uV / 1000.0f / R_SHUNT;
    Serial.printf("PWR,%lu,%.0f,%.0f,%.2f,%.1f\n", (unsigned long)micros(), bus_mV, shunt_uV, mA, mA * bus_mV / 1000.0f);
}

/* ---------------------------------------------------------------- display and LEDs */
static void progress() {          /* one line every 10 s until calibration is done */
    static uint32_t last = 0;
    if (calibrated || millis() - last < 10000) return;
    last = millis();
    if (millis() < WARMUP_MS) Serial.printf("WARMUP,%lu s left\n", (unsigned long)((WARMUP_MS - millis()) / 1000));
    else Serial.printf("CALIBRATING,%d/%d\n", ncal, cal_target);
}

static void show() {
    bool alarm = last_alarm > 0.05f;
    digitalWrite(PIN_RED, alarm ? HIGH : LOW);
    digitalWrite(PIN_GREEN, alarm ? LOW : HIGH);
    if (!has_oled) return;
    oled.clearDisplay();
    oled.setTextSize(1); oled.setTextColor(SSD1306_WHITE); oled.setCursor(0, 0);
    oled.printf("FOA node %d  cyc %lu\n", NODE_ID, (unsigned long)cycle);
    if (!calibrated && millis() < WARMUP_MS) {
        oled.printf("\nWarming up...\n%lu s left\n", (unsigned long)((WARMUP_MS - millis()) / 1000));
    } else if (!calibrated) {
        oled.printf("\nCalibrating...\n%d / %d samples\n", ncal, cal_target);
    } else {
        float R = 0, C = 0;
        for (int i = 0; i < FOA_D; i++) { R += st.R[i] * st.R[i]; C += st.C[i] * st.C[i]; }
        float rho = det.tau * det.s0;
        oled.printf("peers %d  %.1fC %.0f%%\n", last_peers, temp_c, hum);
        oled.setTextSize(2); oled.setCursor(0, 20);
        oled.print(alarm ? "ALARM" : "normal");
        oled.setTextSize(1); oled.setCursor(0, 40);
        oled.printf("alarms %.1f%%\n", 100.0f * last_alarm);
        oled.printf("C %.2f R %.2f lam %.2f\n", sqrtf(C) / rho, sqrtf(R) / rho, st.lam);
    }
    oled.display();
}

/* ---------------------------------------------------------------- traffic and learning */
static void send_telemetry() {
    static uint32_t seq = 0;
    if (has_dht) {
        float t = dht.readTemperature(), h = dht.readHumidity();
        if (!isnan(t) && !isnan(h)) { temp_c = t; hum = h; }
    } else {
        temp_c = 22.0f + 0.01f * (float)(RANDOM_REG32 % 300); hum = 45.0f + 0.01f * (float)(RANDOM_REG32 % 500);
    }
    char msg[96];
    int n = snprintf(msg, sizeof msg, "{\"node\":%d,\"seq\":%lu,\"t\":%.2f,\"h\":%.1f}", NODE_ID, (unsigned long)seq++, temp_c, hum);
    udp.beginPacket(IPAddress(COLLECTOR_IP), COLLECTOR_PORT);
    udp.write((const uint8_t *)msg, n);
    udp.endPacket();
    feat_observe(&fx, FEAT_OUT, (float)(n + 42), micros());
}

static void sample() {
    float raw[FEAT_N], z[FOA_D];
    feat_vector(&fx, micros(), raw);
#ifdef CALIB_LOG
    Serial.print("RAW");
    for (int i = 0; i < FEAT_N; i++) { Serial.print(','); Serial.print(raw[i], 6); }
    Serial.println();
#endif
    feat_project(raw, FEAT_MEAN, FEAT_STD, FEAT_W, z);
    if (!calibrated) {
        static uint32_t skip = 0;
        if (millis() < WARMUP_MS || ++skip % CAL_EVERY) return;
        memcpy(calbuf + ncal * FOA_D, z, sizeof z);
        if (++ncal == cal_target) {
            calibrated = foa_calibrate(&det, calbuf, ncal, scratch, 0.5f) == 0;
            if (calbuf != batch) free(calbuf);
            free(scratch); calbuf = scratch = nullptr;
            foa_state_init(&st);
            t_join = cycle;
            Serial.printf("CAL,%d,s0=%.4f,tau=%.3f,c=%.3f,beta=%.3f,f0=%.3f\n", NODE_ID, det.s0, det.tau, det.c, det.beta, det.f0);
        }
        return;
    }
    if (nb < BATCH) { memcpy(batch + nb * FOA_D, z, sizeof z); nb++; }
}

static void learning_cycle() {
    foa_proposal_t prop;
    uint8_t frame[FOA_FRAME_BYTES];
    static float pdmu[FOA_MAX_PEERS * FOA_D], pdls[FOA_MAX_PEERS];
    float u[FOA_D];
    uint32_t t0 = micros();
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

    float disp = 0, R = 0, C = 0, rho = det.tau * det.s0;
    for (int i = 0; i < FOA_D; i++) {
        disp += (det.mu[i] - det.mu0[i]) * (det.mu[i] - det.mu0[i]);
        R += st.R[i] * st.R[i]; C += st.C[i] * st.C[i];
    }
    Serial.printf("FOA,%d,%lu,%d,%.4f,%u,%d,%.3f,%.3f,%.4f,%.4f,%.4f,%.4f,%lu,%lu,%lu,%lu,%d\n", NODE_ID, (unsigned long)cycle, nb,
                  prop.alarm, prop.n_core, K, st.lam, st.w, sqrtf(R) / rho, sqrtf(C) / rho, det.s / det.s0, sqrtf(disp) / det.s0,
                  (unsigned long)(t1 - t0), (unsigned long)(t4 - t3), (unsigned long)(t2 - t1), (unsigned long)verify_us, rejected);
    last_alarm = prop.alarm; last_peers = K;
    cycle++;
    nb = 0;
}

void setup() {
    Serial.begin(115200);
    delay(200);
    pinMode(PIN_RED, OUTPUT); pinMode(PIN_GREEN, OUTPUT);
    Wire.begin(4, 5);                                   /* SDA = D2, SCL = D1 */
    has_oled = i2c_present(OLED_ADDR) && oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
    ina_setup();
    dht.begin(); delay(100);
    has_dht = !isnan(dht.readTemperature());
    calbuf = (float *)malloc(sizeof(float) * CAL_CYCLES * BATCH * FOA_D);
    scratch = (float *)malloc(sizeof(float) * CAL_CYCLES * BATCH);
    if (!calbuf || !scratch) {           /* low on heap: calibrate on one batch, in the batch buffer */
        free(calbuf); free(scratch);
        calbuf = batch; cal_target = BATCH;
        scratch = (float *)malloc(sizeof(float) * BATCH);
        Serial.println("WARN,calibrating on one batch (low heap)");
    }
    foa_default_params(&prm);
    feat_init(&fx);

    WiFi.mode(WIFI_STA);
    WiFi.setSleepMode(WIFI_NONE_SLEEP);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    for (int k = 0; k < 60 && WiFi.status() != WL_CONNECTED; k++) delay(250);
    udp.begin(NODE_PORT);
    if (esp_now_init() != 0) Serial.println("ERR,esp_now_init");
    esp_now_set_self_role(ESP_NOW_ROLE_COMBO);
    esp_now_register_recv_cb(on_recv);
    esp_now_add_peer(BROADCAST, ESP_NOW_ROLE_COMBO, WiFi.channel(), NULL, 0);   /* frames carry their own HMAC */

    Serial.printf("BOOT,%d,wifi=%d,ch=%d,ip=%s,oled=%d,ina226=%d,dht22=%d,heap=%u\n", NODE_ID, WiFi.status() == WL_CONNECTED,
                  WiFi.channel(), WiFi.localIP().toString().c_str(), has_oled, has_ina, has_dht, ESP.getFreeHeap());
    Serial.println("HDR,node,cycle,n,alarm,n_core,peers,lam,w,R,C,s_ratio,disp,us_propose,us_step,us_mac,us_verify,rejected");
    show();
}

void loop() {
    static uint32_t last_tx = 0, last_sample = 0, last_pwr = 0, last_show = 0;
    uint32_t now = millis();
    if (now - last_tx >= TX_PERIOD_MS) { last_tx = now; send_telemetry(); }
    int len = udp.parsePacket();
    if (len > 0) {
        static uint8_t buf[1500];
        udp.read(buf, sizeof buf);
        feat_observe(&fx, FEAT_IN, (float)(len + 42), micros());
    }
    if (has_ina && now - last_pwr >= 40) { last_pwr = now; ina_sample(); }
    if (now - last_sample >= SAMPLE_MS) {
        last_sample = now;
        sample();
        if (calibrated && nb >= BATCH) learning_cycle();
    }
    if (now - last_show >= 1000) { last_show = now; show(); progress(); }
    yield();
}
