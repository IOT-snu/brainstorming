/* I2C test for the INA226 on an ESP8266: scans with SDA=D2/SCL=D1 and with the two swapped. */
#include <Wire.h>

static void scan(int sda, int scl, const char *label) {
    Wire.begin(sda, scl);
    delay(20);
    int found = 0;
    Serial.printf("Scanning with %s ...\n", label);
    for (int a = 8; a < 120; a++) {
        Wire.beginTransmission(a);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  FOUND device at 0x%02X", a);
            Wire.beginTransmission(a); Wire.write(0xFE); Wire.endTransmission(false);
            if (Wire.requestFrom(a, 2) == 2) { int hi = Wire.read(), lo = Wire.read(); Serial.printf("  id=0x%04X", (hi << 8) | lo); }
            Serial.println();
            found++;
        }
    }
    if (!found) Serial.println("  nothing found");
}

void setup() { Serial.begin(115200); delay(500); }

void loop() {
    Serial.println();
    scan(4, 5, "correct wiring (SDA=D2, SCL=D1)");
    scan(5, 4, "swapped wiring (SDA=D1, SCL=D2)");
    Serial.printf("Line levels (should both be 1 when the sensor is powered): D2=%d D1=%d\n",
                  (pinMode(4, INPUT), digitalRead(4)), (pinMode(5, INPUT), digitalRead(5)));
    delay(3000);
}
