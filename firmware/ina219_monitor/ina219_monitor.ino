/*
 * Energy monitor node: an ESP32 reading an INA219 high-side current sensor placed in the 5 V supply
 * line of one FOA node (circuit/ina219_energy_monitor.kicad_sch), streaming samples over Serial.
 *
 * Wiring: INA219 SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND; VIN+ from the supply,
 * VIN- to the measured node's 5V pin. Shunt on the common breakout: 0.1 ohm.
 *
 * Output lines:  PWR,<micros>,<bus_mV>,<shunt_uV>,<current_mA>,<power_mW>
 * ~1 kHz sampling (12-bit, 1 sample per conversion, 532 us shunt + bus conversion).
 * The laptop aligns these with the node's "FOA,..." cycle log to integrate energy per learning cycle.
 *
 * No library needed: the INA219 registers are read directly over I2C (TI datasheet SBOS448).
 */
#include <Wire.h>

#define INA_ADDR 0x40
#define REG_CONFIG 0x00
#define REG_SHUNT 0x01
#define REG_BUS 0x02
#define R_SHUNT_OHM 0.1f

static void write16(uint8_t reg, uint16_t v) {
    Wire.beginTransmission(INA_ADDR);
    Wire.write(reg); Wire.write(v >> 8); Wire.write(v & 0xFF);
    Wire.endTransmission();
}

static int16_t read16(uint8_t reg) {
    Wire.beginTransmission(INA_ADDR);
    Wire.write(reg);
    Wire.endTransmission(false);
    Wire.requestFrom(INA_ADDR, 2);
    uint16_t hi = Wire.read(), lo = Wire.read();
    return (int16_t)((hi << 8) | lo);
}

void setup() {
    Serial.begin(921600);
    Wire.begin(21, 22);
    Wire.setClock(400000);
    /* 16 V bus range, PGA /2 (+-80 mV shunt, 800 mA max with 0.1 ohm), 12-bit single samples,
       shunt and bus continuous: BRNG=0, PG=01, BADC=0011, SADC=0011, MODE=111 */
    write16(REG_CONFIG, (0 << 13) | (1 << 11) | (3 << 7) | (3 << 3) | 7);
    Serial.println("HDR,PWR,micros,bus_mV,shunt_uV,current_mA,power_mW");
}

void loop() {
    static uint32_t last = 0;
    uint32_t now = micros();
    if (now - last < 1000) return;
    last = now;
    int16_t sh = read16(REG_SHUNT);                 /* LSB 10 uV */
    int16_t bus = read16(REG_BUS);                  /* bits 15:3, LSB 4 mV */
    float shunt_uV = sh * 10.0f;
    float bus_mV = (float)((bus >> 3) * 4);
    float current_mA = shunt_uV / 1000.0f / R_SHUNT_OHM;
    float power_mW = current_mA * (bus_mV + shunt_uV / 1000.0f) / 1000.0f;
    Serial.printf("PWR,%lu,%.0f,%.0f,%.2f,%.1f\n", (unsigned long)now, bus_mV, shunt_uV, current_mA, power_mW);
}
