> **Superseded (28 Nov 2026).** Use `CODEX_ROBUSTNESS_TRIALS.md` instead. This brief's run 2b treats
> `-DNO_PEERS` as single-device adaptation, which is wrong: with no peers the firmware still budgets
> the residual, so it is the budget-only ablation. The new brief adds a real `RULE_SINGLE` baseline.

# Task for Codex: run the FOA hardware experiments

You are helping run experiments on a 3-board ESP8266 (NodeMCU) testbed for the FOA project
(Fleet-Orthogonal Adaptation, an on-device anomaly detector that adapts with help from its peers).
A human is at the desk with the boards plugged in over USB. Ask them for anything physical
(plugging in, Wi-Fi details, which port is which board).

## Read first
- `firmware/README.md`: layout and build commands. It was written for ESP32; the testbed now uses
  `firmware/esp8266_foa/`.
- `firmware/esp8266_foa/esp8266_foa.ino` and `foa_config.h`: node firmware. Build flags available:
  `NODE_ID`, `S_FLOOR` (coverage floor, default 1.0; 0.0 reproduces the old collapse), `WARMUP_MS`,
  `CAL_EVERY`, `CALIB_LOG`.
- `firmware/flash_esp8266.sh <port> <node id> [calib]`: flash one board.
- `firmware/laptop/collector.py <out_dir> --serial <ports...> [--summarise]`: logs every board.
- `firmware/laptop/poisoner.py --node <ip> --mode {boiling,pulse,decoy,flood} --share --ramp --duration`.
- `experiments/hardware/` (old logs, `analyze.py`), `experiments/foa/RESEARCH_LOG.md` (history and known gaps).

## Hard rules
- Never commit Wi-Fi SSID or password. Set them in `foa_config.h` locally only, then restore the
  placeholders (`your-ssid` / `your-password`) before any commit.
- Do not commit: `research.jpeg`, `G04_FOA_Final.pptx`, any `*.zip`, course PDFs, `experiments/data/`, `__pycache__`.
- Git commits as the user only: `git -c user.name=rishitkam -c user.email=<user's email> commit ...`.
  No Co-Authored-By or AI attribution lines. Do not push unless the user says so.
- Every attacked run needs a paired attacker-free twin with the same settings and duration.
- Report honestly. If a run fails or is noisy, say so and keep the log. Never invent numbers.
- Write in plain English, no em dashes. Say "we found no prior work", never "first".

## Setup (once)
1. `arduino-cli board list` to find the 3 ports. Ask the user which is node 0, 1, 2.
2. Confirm the laptop IP matches `COLLECTOR_IP` in `foa_config.h`; fix locally if not.
3. Flash all 3 with the floor on: `bash firmware/flash_esp8266.sh <port> <id>`.
4. Check the boot line on each shows the floor setting and peers being heard.
5. Known issue: identical boards with repetitive UDP traffic collapsed before (spread under 2%,
   about 90% false alarms in 20 min). If traffic is still identical, add per-node variety
   (different telemetry period or jitter by NODE_ID) and record exactly what you changed.

## Experiments, in priority order
Save each run to `experiments/hardware/<run_name>/` with a `README.txt` listing: date, flags,
duration, attacker command, which node was targeted.

| # | Run | How | What to report |
|---|---|---|---|
| 1 | `floor_clean` | All 3 boards honest, floor on, 30 min | False alarms and spread over time per node; does it collapse? |
| 1b | `nofloor_clean` (optional) | Same, `-DS_FLOOR=0.0f` | Shows the collapse the floor fixes |
| 2 | `poison_foa` + twin | `poisoner.py --node <node0 ip> --mode boiling --share 0.3 --ramp 1800`, 30 min; then `--mode flood` for 2 min to check detection | Centre shift of node 0 vs its twin; is the flood still detected? |
| 2b | `poison_single` + twin | Same, but node 0 ignores peers (add a `-DNO_PEERS` build flag that skips peer frames; keep the change minimal) | Single-device adaptation is expected to be pulled further |
| 3 | `freeze` + twin | `--mode decoy --duration 1200` on node 0 | FOA trajectory with vs without decoys (should match); learning updates skipped |
| 4 | `forgery` | Small laptop script sending forged frames (wrong key) and replays of captured frames to node 0 | Count accepted vs rejected (expected 0 accepted) |
| 5 | `power` | INA226 on the measured node; idle, learning cycle, gossip | Mean mW per phase and mJ per learning cycle, replacing the 365 mW x 19 ms estimate |
| 6 | `timing` | Add `micros()` around detector, FOA step, HMAC verify; print once per cycle | Mean and max per stage, plus flash and RAM from the compile output |
| 7 | `shared_drift` + no-drift twin | Mid-run, change traffic for all 3 boards at once (for example halve the telemetry period) | False alarms after drift, FOA vs `poison_single`-style no-peers build |
| 8 | Extras if time | One board sends biased frames with valid keys (Byzantine); 50% frame drop in firmware; drift on one board only | Same metrics |

Runs 1 to 5 are the minimum. Stop and tell the user if run 1 still collapses; later runs are
meaningless until it does not.

## Deliverables
1. Logs and `README.txt` per run in `experiments/hardware/`.
2. `experiments/hardware/analyze_runs.py` producing one summary table and one figure
   (`hardware_attacks.png`): per run, false alarms, compromised yes/no, frames rejected, mJ per cycle.
3. A short `experiments/hardware/RESULTS.md`: what ran, numbers, what failed, honest limits
   (3 boards, laptop-generated attacker traffic, run lengths).
4. Append a dated section to `experiments/foa/RESEARCH_LOG.md`.
5. Any firmware change kept behind a build flag, with defaults unchanged. Run
   `firmware/host_test` again if `foa_core.c` was touched.
6. Do not edit the paper or slides; list proposed text updates in `RESULTS.md` instead.
