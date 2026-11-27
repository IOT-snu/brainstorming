# FOA demo evidence

## Three ESP8266 boards under normal traffic

| Configuration | False alarms over the first 20 learning minutes | Minimum spread / calibrated spread |
| --- | ---: | ---: |
| Static control | 45.80–46.40% | 1.0000 |
| FOA with coverage floor, fixed calibration stride | 25.27–25.30% | 1.0000 |
| FOA with coverage floor, rotated calibration stride | **1.53–1.70%** | **1.0000** |

Values are per-board ranges. The rotated run recorded 291 learning cycles on each board and 1.43–1.72% false alarms over the full capture. Each configuration used a separate boot and calibration, with one run per configuration. Source is the completed runs in `experiments/hardware/RESULTS.md`.

The laptop regression exercised the calibration change on a synthetic repeating signal. Fixed-stride calibration flagged **101 of 400** held-out normal samples. Rotating the stride flagged **11 of 400**. This fixture shows how a fixed stride can miss phases of repeating traffic. Source is `experiments/hardware/firmware_checks_20261127_142444.txt`.

## Abrupt change in normal traffic on the boards

At 30 minutes of uptime, the telemetry intervals changed from 160/200/240 ms to 80/100/120 ms. The table shows false alarms in the ten minutes on either side of that point for node 0.

| Run | Before | After |
| --- | ---: | ---: |
| No rate change, peers enabled | 2.07% | 3.92% |
| Rate change, peers enabled | 2.83% | 99.86% |
| Rate change, peer reception disabled on node 0 | 4.29% | 98.95% |

The spread ratio stayed at or above 1.0000. In the peer-enabled drift trial, each board logged zero core samples in 78 of the 79 post-change cycles. The abrupt shift left the detector with almost no core samples for adaptation. The final build continued for about 13 more minutes, with 100% false alarms on all three boards. Each row represents one hardware run. Source is `experiments/hardware/RESULTS.md` and the corresponding serial logs.

## Held-out poisoning simulation

| Method with coverage floor | Simulated runs compromised during poisoning hidden inside shared drift |
| --- | ---: |
| Single-device adaptation | 43.1% |
| FOA | **9.4%** |

That is a **33.7 percentage point** difference. The simulation compared each run with an attacker-free twin to distinguish compromise from the effect of ordinary drift. With the floor in place, the same simulation reported 0.8% clean false alarms for single-device adaptation and 2.5% for FOA. [G04_Project_Explained.pdf](https://chatgpt.com/library?file_id=libfile_b137254cfa708191a3abe905827011df&account_id=personal)

## What to say in the viva

“On three ESP8266 boards, the coverage floor held throughout the clean runs. Rotating the calibration sampling interval brought false alarms down from about 25% to about 1.5–1.7% over the same 20-minute learning window. Doubling the normal telemetry rate abruptly still drove false alarms to nearly 100%. For poisoning during shared drift, our held-out simulation measured 9.4% compromised runs with FOA versus 43.1% for the single-device baseline, both with the floor. The poisoning figures come from simulation.”
