# FOA hardware results

## 27 November 2026

The 30-minute floor-on baseline started after the desktop launcher verified all three serial ports, flashed each board, and verified each boot line. Arduino CLI enumerated three USB serial ports and found ESP8266 core 3.1.2. The command-line compiler failed to launch in the experiment session. The desktop Arduino IDE compiled the floor-on node 0 sketch successfully. It reported 280,812 of 1,048,576 bytes of flash code, 51,248 of 80,192 bytes of static RAM, and 61,031 of 65,536 bytes of instruction RAM including cache. Physical plug-in checks mapped node 0 to COM10, node 1 to COM16, and node 2 to COM17. Windows denied direct serial opens on all three ports, and the Arduino IDE upload to COM10 also failed with Access is denied. The attempted floor_clean run stopped at the serial preflight and recorded the error in its README. Those attempts ended before flashing. The later successful flash and capture are stored in floor_clean_retry_20261127_140354.

Two older runs were found in the separate Desktop copy of the floor3 package. Both boot logs omit the floor marker. These figures describe the historical logs and cannot establish the result of the floor-on baseline.

| Old run | Node | Logged learning span (min) | Samples flagged (%) | Mean peers | Final spread / calibrated spread |
| --- | ---: | ---: | ---: | ---: | ---: |
| floor3 | 0 | 31.60 | 36.82 | 0.00 | 0.7089 |
| floor3 | 1 | 31.59 | 50.27 | 0.00 | 0.7089 |
| floor3 | 2 | 31.60 | 44.93 | 0.00 | 0.7089 |
| floor4 | 0 | 15.33 | 77.17 | 1.88 | 0.0361 |
| floor4 | 1 | 15.31 | 72.36 | 1.90 | 0.0347 |
| floor4 | 2 | 15.31 | 73.14 | 1.90 | 0.0347 |

One floor4 record for node 1 did not parse. The historical telemetry sink logs were empty in both runs. The floor3 boot logs report Wi-Fi disconnected. The floor4 boot logs report Wi-Fi connected.

No live poisoning, decoy, or forgery trials were run. The completed-capture section records which normal-traffic comparisons, timing readings, and power readings are available. The planned testbed has three boards, short runs, and laptop-generated traffic for attack comparisons. The INA226 is read every 40 ms. The configuration averages sixteen 1.1 ms shunt and bus conversions, so its electrical averaging window is about 35 ms. The stage timing and board power are reported separately. [INA226 datasheet](https://www.ti.com/lit/ds/symlink/ina226.pdf)

## Proposed paper text

The archived ESP8266 logs recorded a pronounced spread contraction in the peer-connected run. Report the minimum spread ratio and false alarms independently for the floor-on baseline. Replace the prior power assumption with the measured board power where the operating period is comparable. Keep learning energy labeled as an estimate until phase-resolved measurements are available.

<!-- BEGIN COMPLETED RUNS -->
## Completed hardware captures

| Run | Node | Learning min | Cycles | False alarms | Last 5 min | Both peers | Min spread ratio | Final centre distance / s0 | Rejected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| continued_clean_20261127_142002 | 0 | 13.25 | 105 | 100.00% | 100.00% | 0.00% | 1.0000 | 4.9335 | 0 |
| continued_clean_20261127_142002 | 1 | 13.27 | 107 | 100.00% | 100.00% | 98.13% | 1.0000 | 4.5839 | 0 |
| continued_clean_20261127_142002 | 2 | 13.26 | 107 | 100.00% | 100.00% | 99.07% | 1.0000 | 3.5062 | 0 |
| diverse_no_drift_clean_20261127_142002 | 0 | 36.51 | 291 | 2.41% | 4.48% | 89.69% | 1.0000 | 5.5399 | 0 |
| diverse_no_drift_clean_20261127_142002 | 1 | 36.51 | 291 | 25.17% | 25.82% | 88.66% | 1.0000 | 4.2802 | 3 |
| diverse_no_drift_clean_20261127_142002 | 2 | 36.51 | 291 | 0.67% | 1.82% | 91.07% | 1.0000 | 3.7028 | 0 |
| diverse_shared_drift_clean_20261127_142002 | 0 | 36.49 | 291 | 34.58% | 100.00% | 89.35% | 1.0000 | 4.6359 | 0 |
| diverse_shared_drift_clean_20261127_142002 | 1 | 36.50 | 291 | 50.59% | 100.00% | 88.66% | 1.0000 | 4.5358 | 0 |
| diverse_shared_drift_clean_20261127_142002 | 2 | 36.49 | 291 | 33.63% | 100.00% | 88.32% | 1.0000 | 3.3572 | 1 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 0 | 36.37 | 292 | 40.47% | 100.00% | 0.00% | 1.0000 | 4.9335 | 0 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 1 | 36.39 | 292 | 49.84% | 100.00% | 99.32% | 1.0000 | 4.5839 | 0 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 2 | 36.39 | 292 | 33.07% | 100.00% | 99.32% | 1.0000 | 3.5062 | 0 |
| floor_clean_retry_20261127_140354 | 0 | 24.42 | 196 | 25.27% | 25.18% | 96.43% | 1.0000 | 4.6833 | 1 |
| floor_clean_retry_20261127_140354 | 1 | 24.66 | 198 | 25.25% | 25.12% | 95.45% | 1.0000 | 4.6449 | 0 |
| floor_clean_retry_20261127_140354 | 2 | 24.53 | 197 | 25.24% | 25.12% | 96.95% | 1.0000 | 4.5611 | 0 |
| rotated_calibration_clean_20261127_142002 | 0 | 36.48 | 291 | 1.65% | 1.60% | 90.03% | 1.0000 | 3.8451 | 0 |
| rotated_calibration_clean_20261127_142002 | 1 | 36.48 | 291 | 1.43% | 1.42% | 90.03% | 1.0000 | 3.7918 | 0 |
| rotated_calibration_clean_20261127_142002 | 2 | 36.48 | 291 | 1.72% | 1.33% | 88.32% | 1.0000 | 3.5984 | 0 |
| static_control_clean_20261127_142002 | 0 | 36.42 | 290 | 48.17% | 50.17% | 91.38% | 1.0000 | 0.0000 | 0 |
| static_control_clean_20261127_142002 | 1 | 36.42 | 291 | 47.83% | 50.18% | 93.47% | 1.0000 | 0.0000 | 1 |
| static_control_clean_20261127_142002 | 2 | 36.42 | 291 | 47.73% | 49.97% | 90.72% | 1.0000 | 0.0000 | 0 |

The baseline reached a minimum logged spread ratio of 1.0000 and a highest per-node false-alarm rate of 25.27%. The coverage floor bounds spread. Centre movement can still shift which samples the detector flags.

### Baseline timing

| Node | Proposal mean / max (us) | FOA step and apply mean / max (us) | Signing mean / max (us) | Verify work mean / max per cycle (us) |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 21564.2 / 22261 | 1836.8 / 3760 | 596.2 / 621 | 976.4 / 1048 |
| 1 | 21469.4 / 22490 | 1632.7 / 3698 | 600.1 / 606 | 926.6 / 974 |
| 2 | 21385.7 / 22615 | 1937.6 / 3778 | 592.9 / 609 | 1007.8 / 1048 |

Proposal timing includes batch classification. Verify work sums time for frames processed in the cycle. Radio wait time is recorded separately only if instrumented.

### Matched learning window for calibration controls

| Run | Node | False alarms in first 20 learning minutes |
| --- | ---: | ---: |
| floor_clean_retry_20261127_140354 | 0 | 25.30% |
| floor_clean_retry_20261127_140354 | 1 | 25.27% |
| floor_clean_retry_20261127_140354 | 2 | 25.27% |
| rotated_calibration_clean_20261127_142002 | 0 | 1.69% |
| rotated_calibration_clean_20261127_142002 | 1 | 1.53% |
| rotated_calibration_clean_20261127_142002 | 2 | 1.70% |
| static_control_clean_20261127_142002 | 0 | 46.40% |
| static_control_clean_20261127_142002 | 1 | 45.80% |
| static_control_clean_20261127_142002 | 2 | 45.83% |

Each trial has its own boot and calibration. This comparison uses 20 minutes of logged learning from each node. It controls duration within the learning phase.

### Normal telemetry change

| Run | Node | False alarms, 10 min before | False alarms, 10 min after |
| --- | ---: | ---: | ---: |
| diverse_no_drift_clean_20261127_142002 | 0 | 2.07% | 3.92% |
| diverse_no_drift_clean_20261127_142002 | 1 | 25.70% | 25.60% |
| diverse_no_drift_clean_20261127_142002 | 2 | 0.51% | 0.41% |
| diverse_shared_drift_clean_20261127_142002 | 0 | 2.83% | 99.86% |
| diverse_shared_drift_clean_20261127_142002 | 1 | 25.95% | 99.89% |
| diverse_shared_drift_clean_20261127_142002 | 2 | 0.47% | 99.85% |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 0 | 4.29% | 98.95% |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 1 | 25.03% | 99.33% |
| diverse_shared_drift_no_peers_clean_20261127_142002 | 2 | 0.00% | 99.12% |

The no-drift control emitted a time marker without changing its period. Separate boots recalibrated the boards for each run. These comparisons are descriptive.

| Suite | Node | Contrast in before-to-after alarm changes | Percentage points |
| --- | ---: | --- | ---: |
| 20261127_142002 | 0 | Shared drift minus no drift | +95.18 |
| 20261127_142002 | 0 | Ignore peers minus receive peers under shared drift | -2.37 |
| 20261127_142002 | 1 | Shared drift minus no drift | +74.04 |
| 20261127_142002 | 2 | Shared drift minus no drift | +99.48 |

### Measured board power

| Run | Operating period | INA226 samples | Mean power (mW) |
| --- | --- | ---: | ---: |
| diverse_no_drift_clean_20261127_142002 | Calibrated operation | 54441 | 384.09 |
| diverse_no_drift_clean_20261127_142002 | Calibration | 3623 | 383.83 |
| diverse_no_drift_clean_20261127_142002 | Warm-up | 4376 | 383.61 |
| diverse_shared_drift_clean_20261127_142002 | Calibrated operation | 54499 | 381.81 |
| diverse_shared_drift_clean_20261127_142002 | Calibration | 3498 | 381.69 |
| diverse_shared_drift_clean_20261127_142002 | Warm-up | 4501 | 382.03 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | Calibrated operation | 54825 | 384.32 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | Calibration | 3542 | 384.47 |
| diverse_shared_drift_no_peers_clean_20261127_142002 | Warm-up | 4501 | 384.46 |
| floor_clean_retry_20261127_140354 | Calibrated operation | 36760 | 391.18 |
| floor_clean_retry_20261127_140354 | Calibration | 3742 | 389.89 |
| floor_clean_retry_20261127_140354 | Warm-up | 4301 | 389.55 |
| rotated_calibration_clean_20261127_142002 | Calibrated operation | 54436 | 387.93 |
| rotated_calibration_clean_20261127_142002 | Calibration | 3692 | 387.98 |
| rotated_calibration_clean_20261127_142002 | Warm-up | 4351 | 387.92 |
| static_control_clean_20261127_142002 | Calibrated operation | 54555 | 383.86 |
| static_control_clean_20261127_142002 | Calibration | 3642 | 383.34 |
| static_control_clean_20261127_142002 | Warm-up | 4401 | 383.74 |

These are sample means for logged operating periods. The 40 ms logging interval and approximately 35.2 ms sensor averaging window leave per-cycle learning energy and radio phase power unresolved. The calibration transition is approximate because progress lines appear every ten seconds.

<!-- END COMPLETED RUNS -->
