# Codex: robustness trials of our own detector on our own 3-board lab testbed (v2, 28 Nov 2026)

## Scope and authorization
University research project (CSD457 IoT, Group G-04). Everything runs on equipment we own, on our own
local Wi-Fi: 3 ESP8266 boards running our own firmware and one laptop. No other hosts, networks or
devices are involved. The goal is to measure how well OUR detector resists manipulated input traffic,
a standard evaluation in anomaly-detection research. All test traffic comes from our existing laptop
script `firmware/laptop/poisoner.py` and goes only to our own boards' local IPs on port 5006.
This is a defensive evaluation of our own detector on hardware we own.

Work autonomously. Ask the user only physical questions (ports, Wi-Fi, wiring), all at the start.
Log every action with a timestamp in `experiments/hardware/trials_v2/SESSION_LOG.md`.
Read `MASTER_PLAN.md` (section 3, D2) first: it explains why the design below is what it is.

## Background you need
- Detector on each board: score = ||x - mu|| / s, flagged if score > tau; alarm radius rho = tau * s0.
  Learns only from unflagged samples; core samples (score <= 80th percentile) drive the update.
- FOA: each cycle the boards share a signed proposed update over ESP-NOW; FOA follows the robust
  middle of the peers' proposals as far as the board's own traffic agrees (common part, budget
  (0.75 + 0.06 t) rho) and limits the board-only remainder to (0.1 + 0.005 t) rho, plus spread budgets
  and a coverage floor (s >= s0).
- IMPORTANT: with fewer than 2 peers the firmware sets the common part to zero and still budgets the
  rest. So "ignore peers" is a budget-only ablation, NOT a lone device. A lone device (single-device
  adaptation) applies its own proposal in full, with no budget. The firmware has no such mode yet.
- The board features summarise ALL incoming packets together (`foa_features.c`), so test traffic
  shifts every sample. Expect the slow-ramp trial to test the budget cleanly and the loud-outlier
  trial to starve learning while it lasts. Both are findings; report them as they come.
- Results so far (branch `origin/hardware-results-20261127`): floor holds on the boards; fixed-stride
  calibration aliased with the 200 ms telemetry (about 25% flags); rotated stride (gaps 9, 9, 9, 13)
  gave 1.5 to 1.7%; halving all telemetry periods at once starved every board (about 99% flags).

## Step 0: builds and checks (keep defaults unchanged, everything behind flags)
1. `CAL_ROTATE`: rotated calibration stride (as on the branch). All trials use it.
2. `RULE_SINGLE`: skip `foa_step`; apply the board's own proposal in full (`prop.dmu`, `prop.dls`),
   still enforcing the coverage floor (cap the cumulative log-spread change at log(S_FLOOR)). Ignore
   peer frames. This is the lone-device baseline.
3. `NO_PEERS`: ignore peer frames, keep `foa_step` (budget-only ablation).
4. Replay fix: today a frame with an old cycle number is accepted after 60 s of silence from that peer
   (`PEER_RESET_MS`). Make cycle numbers strictly increase across reboots instead (for example a boot
   counter kept in flash or RTC memory in the high bits), then remove the silence exception. Keep the
   92-byte frame. Update the Python mirror if the frame changes, and rerun `firmware/host_test`.
5. Commit each change. Confirm the boot line prints all flags.

## Step 1: preregistration (before any trial)
Write and commit `experiments/PREREG_2026-11-28.md` containing: the trial table below, the outcome
measure, the predictions, and the analysis plan. Do not change it after trials start; if something
must change, add a dated amendment with the reason.

Outcome measure: each trial ends with a 3-minute reference-profile check on node 0 (`--mode flood`).
Recognition = share of check samples flagged. "Model shifted" = recognition below 50% while the
paired attacker-free control is at 90% or more. Also log every cycle: node 0's centre displacement
along the test-profile direction in alarm radii, cumulative R and C against their budgets, spread
ratio, core count, peers heard.

Prediction (write the numbers in before running): measure M, the reference profile's distance from
normal in alarm radii on calibrated node 0 (2 minutes of `--mode flood`, score / tau). FOA and
budget-only should not shift before about t* = (M - 1.2) / 0.006 cycles (cycle is about 7.8 s); the
lone device may shift as soon as the ramp is gradual enough to stay inside its radius.

## Step 2: the 2x3 trial (3 repeats per cell, balanced order, each with a paired control)

| Condition | Lone device (`RULE_SINGLE` on node 0) | Budget only (`NO_PEERS` on node 0) | FOA |
|---|---|---|---|
| A. Slow ramp on node 0 only: `poisoner.py --mode boiling --share 0.3 --ramp 1800`, 35 min then check | expect shifted | expect held to budget line | expect held to budget line |
| B. Gradual shared drift: all boards' telemetry period ramps 200 to 100 ms (scaled per node) over 45 min, no test traffic | expect follows | expect falls behind (more flags) | expect follows |

Nodes 1 and 2 always run FOA. Order the 18 runs as balanced blocks (for example ABC, CBA, BCA per
condition). Each run: reboot, warm-up, calibration, then the schedule. If condition B shows core
counts falling below 5, slow the ramp and record the change as an amendment.

## Step 3: other trials
1. Static control with `CAL_ROTATE` (never learns), 35 min, for a fair false-alarm comparison.
2. Frame integrity: frames signed with a wrong key, and repeats of captured frames (including a repeat
   after more than 60 s of silence, before and after the replay fix), sent by a laptop script or by
   node 2 built with a `BADFRAMES` flag. Expect 0 accepted after the fix.
3. Loud outlier traffic: `--mode decoy --duration 1200` on node 0 during condition B's drift, FOA vs
   alarm-rate switch-off if a build for it exists. Expect starvation during the flood with aggregate
   features; record whether each build recovers after it.
4. If time remains: a `PER_SOURCE` build that keeps statistics per source IP, and repeat trial 3.

## Outputs
- Raw logs and `run.json` per run (git hash, flags, commands, times, target, control).
- `tools/analyze_trials.py` producing `trials_summary.csv`, `TRIAL_RESULTS.md` and figures:
  `fig_budget_line.png` (node 0's displacement over time against (B0 + Bt) rho, three builds, all
  repeats), `fig_shared_drift.png` (flags over time, three builds), a frame-integrity table.
- `TRIAL_RESULTS.md`: per-run numbers, predictions vs outcomes, everything that failed, limits
  (3 boards, laptop-generated traffic, one target node). Propose one slide; do not edit the paper.
- Append a dated section to `experiments/foa/RESEARCH_LOG.md`.

## Rules
- Only our own boards and laptop on our own network. Never send traffic anywhere else.
- Never commit or log Wi-Fi credentials; restore the `foa_config.h` placeholders before each commit.
- Never commit zips, photos, decks, course PDFs, `experiments/data/` or `__pycache__`; do not edit
  `.gitignore`.
- Commit as `git -c user.name=<the committer's own name> -c user.email=<their own email> commit`.
  No AI names or Co-Authored-By lines. Push to a branch `hardware-trials-v2`, never to main.
- No links to private services in any file.
- Report numbers exactly. Do not change test traffic or firmware after seeing results to favour FOA.
  If FOA does worse, that is a finding.
- Plain English, no em dashes; say "we found no prior work", never "first".
