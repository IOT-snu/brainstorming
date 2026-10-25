/*
 * Footprint baseline: the same Wi-Fi, UDP telemetry and ESP-NOW setup as esp32_foa.ino with the
 * detector, features, FOA and HMAC removed. Compiling both and subtracting gives FOA's own flash and
 * static RAM cost:  arduino-cli compile --fqbn esp32:esp32:esp32 firmware/footprint_baseline
 */
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_now.h>
#include <esp_wifi.h>

static WiFiUDP udp;
static const uint8_t BROADCAST[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static volatile int received = 0;

static void on_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len) { (void)info; (void)data; (void)len; received++; }

void setup() {
    Serial.begin(115200);
    WiFi.mode(WIFI_STA);
    WiFi.begin("your-ssid", "your-password", 6);
    esp_wifi_set_ps(WIFI_PS_NONE);
    udp.begin(5006);
    esp_now_init();
    esp_now_register_recv_cb(on_recv);
    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, BROADCAST, 6);
    esp_now_add_peer(&peer);
}

void loop() {
    static uint32_t last = 0;
    if (millis() - last >= 200) {
        last = millis();
        char msg[64];
        int n = snprintf(msg, sizeof msg, "{\"t\":%lu}", (unsigned long)last);
        udp.beginPacket(IPAddress(192, 168, 1, 100), 5005);
        udp.write((const uint8_t *)msg, n);
        udp.endPacket();
        uint8_t frame[68] = {0};
        esp_now_send(BROADCAST, frame, sizeof frame);
    }
    int len = udp.parsePacket();
    if (len > 0) { static uint8_t buf[1500]; udp.read(buf, sizeof buf); }
}
