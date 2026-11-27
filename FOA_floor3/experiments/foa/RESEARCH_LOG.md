# FOA research log

## 27 November 2026

Located the Windows ESP8266 firmware package and two historical runs. Both historical boot logs lacked a coverage-floor marker. The older peer-connected run recorded final spread ratios of 0.0347 to 0.0361 and 72.36% to 77.17% flagged samples across nodes. The new floor-on baseline is pending while we identify the boards and resolve compiler and serial access. See the hardware results for the per-node breakdown.
The desktop Arduino IDE compiled the default floor-on build for node 0. Direct serial capture from the experiment session remains blocked.
The three boards were mapped to COM10, COM16, and COM17 in node order. Windows listed all three ports but denied serial access. The baseline launcher passed a simulated capture and floor-check test and recorded the real preflight failure.

## 27 November 2026, floor-on hardware follow-up

The desktop launcher opened COM10, COM16, and COM17, flashed three node IDs, and verified Wi-Fi and floor=1.00 on each boot. All three boards subsequently heard both peers. Node 0 detected the INA226. The baseline budget is 30 minutes after the last verified boot, including warm-up and calibration. The hardware results file records completed metrics.

The first clean learning cycles showed approximately 25% alarms alongside a spread ratio of 1.0000. That combination motivated two controlled checks. A fixed-detector trial holds the calibrated centre and spread fixed with telemetry and gossip active. A rotation trial retains calibration samples at intervals of 9, 9, 9, and 13 sampling ticks. Both this schedule and the original stride collect four retained samples per 40 ticks. With 50 ms sampling and 200 ms telemetry, the nominal original schedule reaches two of four phases and the rotated schedule reaches all four. Real timing jitter can blur this effect. This is a proposed explanation to test, and the baseline alone cannot identify the cause.

The four-hour desktop queue waits for verified baseline completion and the floor check. It then schedules the control, calibration rotation, and matched normal-traffic runs. The latter use per-node periods of 160, 200, and 240 ms. In the drift runs those values halve at 30 minutes of device uptime. The no-drift run records the same time marker. The final comparison ignores peer updates on node 0 and leaves the other two boards operating normally. Each comparison uses a fresh boot and 42-minute capture. Defaults remain the original firmware behavior.

The host floor regression ran 250 contraction updates. Without the floor, the final spread ratios were 0.70539 with no peers and 0.00241 with two matching peers. With the floor both were 1.00000. This fixture exercises the portable rule with synthetic proposals and does not represent a hardware trial.

The synthetic four-phase fixture held its training and holdout distributions fixed and changed only the calibration stride. The original stride flagged 101 of 400 examples, and phase rotation flagged 11 of 400. This shows that periodic sampling can produce the observed pattern in a controlled example. It does not establish why the real boards flagged samples. The board runs compare the original and rotated strides over the same first 20 learning minutes.

### Completed baseline at 14:38 IST

The 30-minute floor-on capture completed. The nodes produced 196, 198, and 197 learning cycles over 24.42 to 24.66 logged learning minutes. All three reported a minimum and final spread ratio of 1.0000. False alarms were 25.27%, 25.25%, and 25.24%, respectively. Both peers were received in 95.45% to 96.95% of cycles across the fleet. Final centre displacement ranged from 4.5611 to 4.6833 times calibrated spread. These data support the floor check and identify a remaining clean alarm problem.

Node 0 averaged 391.18 mW in calibrated operation. Startup and calibration means were 389.55 mW and 389.89 mW. The measurement resolution is insufficient for energy per learning cycle or radio phase. The baseline proposal took 21.39 to 21.56 ms on average per node, and the FOA step and apply took 1.63 to 1.94 ms. These timings exclude time waiting for peer frames. The detailed stage maxima and peer stats are in the hardware results.

The follow-up plan passed its baseline gate and began the fixed-detector control at 14:38:07 IST. Follow-up launch status and failures are tracked in experiments/hardware/followup_20261127_142002.txt. The scheduled four-hour window ends around 18:38 IST. Checks at 15:44, 16:44, 17:44, and 18:44 IST verify progress and reconcile the results.

The fixed-detector trial flashed all three boards and automatically reset them via RTS. Its 42-minute capture started at 14:41:32 IST after the floor and Wi-Fi boot checks. The peer-disabled build in the later shared-drift comparison skips peer processing and the receive wait on node 0. Its change in runtime workload limits attribution to peer information alone.

### Completed hardware follow-ups at 18:38 IST

All five clean follow-up captures and the final continuation completed. Each capture produced learning records on all three boards and a minimum spread ratio of 1.0000. The analyzer refreshed the results, CSV, and plot after the continuation. The static control's calibrated-operation power mean is 383.86 mW across 54,555 valid records. One concatenated serial line was excluded after checking the power record format and retaining the raw log.

Rotated calibration had 1.53% to 1.70% false alarms across nodes in the matched 20-minute learning window, compared with 25.27% to 25.30% for the floor-on baseline and 45.80% to 46.40% for the static control. These are descriptive comparisons across separate boots and calibrations. In the varied-traffic control, the full-capture rates were 2.41%, 25.17%, and 0.67% on nodes 0 through 2.

Both shared-drift builds recorded the telemetry periods changing from 160/200/240 ms to 80/100/120 ms at 30 minutes of uptime. In the peer-enabled run, the three boards had 99.85% to 99.89% false alarms in the ten minutes after the change. Each board had zero core samples in 78 of the 79 cycles in that window. Node 0 recorded 99.86% post-change false alarms with peer reception and 98.95% in the matched build that disabled its peer reception. The continuation retained that build and recorded 100% false alarms on all three boards for about 13 additional minutes. The results establish a failure to recover from this abrupt change within the recorded window. The hardware suite used normal traffic throughout.
