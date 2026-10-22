# Rebuild the power-measurement circuit in CircuitLab

CircuitLab cannot import schematic files (only SPICE text for one custom device), and it has no ESP32 or INA219 part.
So redraw the analog part by hand. It shows the idea: a tiny shunt resistor in series with the node's supply, and the
voltage across it tells you the current. The I2C and microcontroller half cannot be simulated there.

## Parts (all from the CircuitLab library)
| Label | Part | Value | Stands for |
|---|---|---|---|
| V1 | DC voltage source | 5 V | the 5 V supply |
| R_SHUNT | Resistor | 0.1 ohm | the shunt inside the INA219 |
| R_LOAD | Resistor | 40 ohm | the ESP32 node (about 125 mA) |
| GND | Ground | - | common ground |

## Wiring
1. V1 positive terminal to one end of R_SHUNT. Name this node **5V_IN**.
2. Other end of R_SHUNT to one end of R_LOAD. Name this node **NODE_5V**.
3. Other end of R_LOAD to GND.
4. V1 negative terminal to GND.

## Probes (Simulate, then DC Solver or Time Domain)
- Voltage probe across R_SHUNT (5V_IN to NODE_5V): this is what the INA219 measures.
- Voltage probe at NODE_5V: the voltage the node actually sees.
- Current through R_SHUNT: the current the INA219 reports.

## Expected values (check these)
- Current: 5 / 40.1 = about 124.7 mA
- Shunt voltage: about 12.5 mV (the INA219 resolves 10 uV steps, which is about 0.1 mA with a 0.1 ohm shunt)
- Node voltage: about 4.9875 V (the shunt costs about 12.5 mV)

## Optional: mimic Wi-Fi bursts
Replace R_LOAD with R_LOAD in series with a switch driven by a pulse source (for example 1 ms on, 9 ms off) in parallel with
a second 20 ohm resistor, to see the shunt voltage jump during a burst. This shows why short bursts need averaging.

## Where each piece sits in the real circuit
V1 = USB 5 V supply, R_SHUNT = INA219 (VIN+ to VIN-), R_LOAD = the ESP32 node under test.
The monitor ESP32 and the I2C lines (SDA, SCL, 3V3) have no CircuitLab equivalent: see the KiCad file.
