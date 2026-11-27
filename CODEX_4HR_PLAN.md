# Codex: 4-hour autonomous hardware session for the FOA project

You will run alone for about 4 hours. Write your own scripts, run the experiments, store every
result, fix what is broken, and use your judgement. The user is nearby only for physical things:
ask everything you need from them in the FIRST 10 MINUTES (Wi-Fi SSID/password, which USB port is
which board, whether the INA226 is wired to node 0), then work without them. If something physical
blocks you later, write it to `experiments/hardware/session_2026-11-27/BLOCKERS.md` and move on to
the next task that does not need it.

---------------------------------------------------------------------------------------------------
## 1. Research context (read this carefully, it is what the results must support)

**Project.** CSD457 IoT research project, Group G-04. Method: **FOA, Fleet-Orthogonal Adaptation**.
An earlier method, **TOA (Threat-Orthogonal Adaptation)**, needed an attack signature; FOA does not.

**Problem.** An IoT anomaly detector must adapt to honest drift (traffic changes over time), but an
attacker can hide slow poisoning inside that drift (the "boiling frog"), dragging the normal model
towards the attack until the attack is no longer detected. Freezing the detector stops poisoning
but then honest drift causes false alarms.

**Detector (per device).** score = ||x - mu|| / s; alarm if score > tau (99th percentile of
calibration). Alarm radius rho = tau * s0. Core samples: score <= c (80th percentile). Learning uses
only accepted (non-alarmed) samples, so loud traffic never enters learning. eta = 0.5.

**FOA rule (per learning cycle t).**
- Each device proposes a centre shift d from its core samples and gossips it (authenticated frame,
  HMAC-SHA256, cycle number against replay) over ESP-NOW.
- m = geometric median of peers' proposals (Weiszfeld); m_avg = EMA of m, alpha = 0.2.
- Significance: sigma = median||d_j - m|| / sqrt(K); z = ||m_avg|| / (sigma_avg * sqrt(alpha/(2-alpha)));
  w = clip((z-2)/2, 0, 1).
- Agreement: lambda = clip(g_avg / ||m_avg||, 0, 1), g = eta * median over core of (x - mu) . u
  (u = unit consensus direction). A device only follows the fleet as far as its OWN traffic agrees.
- Common part a = w * lambda * m_avg, cumulative ||C|| <= (0.75 + 0.06 t) rho.
- Residual r = d - a (what only this device sees), cumulative ||R|| <= (0.1 + 0.005 t) rho.
  This residual budget is the ONE knob: B = 0.005 alarm radii per cycle.
- Spread budgets: residual 0.1 + 0.001 t, common 0.7 + 0.02 t.
- **Coverage floor**: s >= s0 (spread never shrinks below its calibration value). Added after the
  hardware collapse; chosen on dev seeds, held-out result E12.

**Theory.** Boundedness by construction (projection onto a ball each cycle, induction, triangle
inequality) gives a minimum time-to-compromise t*. Byzantine robustness of the geometric median
(Minsker lemma, C_beta = (1-beta) sqrt(1/(1-2 beta))). Freeze proposition: decoys outside the alarm
radius never change FOA's trajectory (unit test: bit-for-bit identical).

**Simulation results (held-out seeds 2-11; dev seeds 0-1 only for design).**
- Strong shared drift, fleet false alarms: FOA 9.0%, single-device 24.6%, alarm-rate switch-off 45%,
  frozen reserve 59%, static 78%. Device-only drift: FOA 36% vs single 26% (known cost).
- Poisoning hidden in drift: compromised FOA 10.8%, single 39.2%, switch-off 29.9%, frozen 27.4%.
- With coverage floor (E12): FOA 9.4% vs single 43.1% compromised; floor removes most false alarms
  for single-device too, so FOA's false-alarm advantage does not survive the floor, its safety does.
- Monoculture botnet: same-model consensus 100% compromised when 2-3 of 3 infected; FOA 0%.
- Freeze attack: alarm-rate switch-off locked at 100% false alarms; FOA identical with/without decoys.
  Outlier-ratio (DriftXpert-style) gate reopened.
- HMAC: all forged and replayed frames rejected (100% compromised without it). Frame loss up to 70%
  harmless.
- Byzantine peers alone: 0% up to 4. With a poisoner: 0/2/40/56/60% for 0-4 Byzantine peers vs 80%
  single-device. Open problem (common spread channel).
- B sweep: B <= 0.005 gives 0% compromised. Bound violated 0 times in 3,630 attacked runs.
- CESNET real drift: FOA 0% compromised (single 18%).
- Evaluation rules: victims need >= 1.3 alarm radii margin; every attacked run is paired with an
  attacker-free twin and only loss the twin keeps counts; decoys pushed to >= 2 alarm radii.

**Hardware so far (the weak part; this session exists to fix it).**
- 3 ESP8266 NodeMCU boards (nodes 0, 1, 2), laptop collector, INA226 at 0x44 on node 0.
- First runs collapsed: identical boards sending repetitive UDP, spread under 2%, ~90% false alarms
  in 20 min. Coverage floor added. NO attack has ever been run on the boards. The floor has never been
  verified on the boards. Power 365 mW measured; ~7 mJ per learning cycle is only an estimate
  (365 mW x 19 ms).
- Latest logs `floor3.zip` (26 Nov, 244 cycles): BOOT shows `wifi=0, ip=(IP unset)` on all boards,
  `peers=0` in every cycle, `s_ratio` falls 0.90 -> 0.72 identically on all nodes despite
  S_FLOOR = 1.0, false alarms rise to ~51%. BOOT line lacks the floor setting, so boards may run old
  firmware (`floor3_update.zip` vs `firmware/esp8266_foa/`). Boards are currently on that build.

**Code map.**
- `firmware/esp8266_foa/` node firmware (`esp8266_foa.ino`, `foa_core.c/.h`, `foa_config.h`,
  features, sha256). Flags: NODE_ID, S_FLOOR, WARMUP_MS, CAL_EVERY, CALIB_LOG.
  Log lines: BOOT, HDR, FOA (node,cycle,n,alarm,n_core,peers,lam,w,R,C,s_ratio,disp,us_propose,
  us_step,us_mac,us_verify,rejected), PWR (time_us, bus_mV, current, ..., mW).
- `firmware/flash_esp8266.sh <port> <id> [calib]`, `firmware/laptop/collector.py`,
  `firmware/laptop/poisoner.py` (boiling, pulse, decoy, flood), `firmware/host_test.c` (C vs Python).
- `experiments/foa/` Python reference (`foa_rule.py`, `detector.py`, `fleet.py`, tests),
  `experiments/foa/RESEARCH_LOG.md`, `experiments/hardware/` old logs and `analyze.py`.
- `paper/*.tex` paper; `demo/build_final_deck.py`, `demo/build_viva_prep.py` slides and viva guide.

---------------------------------------------------------------------------------------------------
## 2. Hard rules (never break)
- Never commit Wi-Fi SSID/password or put them in any log or doc. Keep them in a local untracked
  file and restore `foa_config.h` placeholders before every commit.
- Never commit: `research.jpeg`, `G04_FOA_Final.pptx`, `*.zip`, course lecture PDFs,
  `experiments/data/`, `__pycache__`. Do not edit `.gitignore`. Do not push.
- Commits only as the user: `git -c user.name=rishitkam -c user.email=<ask the user> commit`.
  No Co-Authored-By, no AI names anywhere. Commit small and often, with plain messages.
- Never invent or round up numbers. A failed or noisy run is reported as failed, with its log.
- Every attacked run gets an attacker-free twin (same build, same duration, same time of day if
  possible). Runs are long enough to matter (>= 20 min, ideally 30).
- Firmware changes go behind build flags; defaults keep current behaviour. If `foa_core.c` changes,
  rerun `firmware/host_test` (C must still match Python) and the Python tests.
- Writing style: plain English, no em dashes, no "first"; say "we found no prior work".

---------------------------------------------------------------------------------------------------
## 3. The 4-hour schedule

Make a session folder `experiments/hardware/session_2026-11-27/` and keep `SESSION_LOG.md` in it:
timestamped entry for every action, build, run, finding and decision. Each run gets its own
sub-folder with raw logs plus `run.json` (name, start/end, git hash, build flags, attacker command,
target node, twin name, notes).

### Hour 0:00-0:45 Fix the testbed (nothing else counts until this works)
1. Ask the user the physical questions (see top). Then work alone.
2. Write `tools/parse_logs.py`: parses BOOT/FOA/PWR lines (ignore garbage bytes at boot) into
   CSV/pandas; per node per cycle: alarm, peers, lam, w, R, C, s_ratio, timings, rejected.
3. Analyse floor3 with it; save `floor3_diagnosis.md`.
4. Find why the floor does not hold: read what `s_ratio` is and where `s_floor` is applied in
   `foa_core.c` and the `.ino`; compare with `experiments/foa/foa_rule.py`. Diff
   `floor3_update/` against the repo. Fix, test on host (`host_test`, Python tests), flash current
   code to all 3 boards.
5. Fix Wi-Fi (credentials, channel; ESP-NOW and Wi-Fi share one channel) and peers. BOOT line must
   show wifi=1, an IP and the floor setting; FOA lines must show peers = 2.
6. Remove the collapse cause: give each node its own traffic pattern (telemetry period/jitter by
   NODE_ID or a laptop traffic generator) so the boards are not identical. Document it.
7. Smoke test 10 min: peers 2, s_ratio >= 1.0, alarms near the calibration rate. If it still fails,
   keep debugging; this is the most important hour.

### Hour 0:45-1:30 Clean baselines (run in background, analyse while it runs)
- `floor_clean`: 30 min, all honest, floor on. Report false alarms and s_ratio over time.
- `nofloor_clean`: 20 min with `-DS_FLOOR=0.0f` (only if time allows) to show the collapse the
  floor fixes, on the same setup.
- While running: write `tools/run_experiment.py` that flashes (if needed), starts the collector,
  starts/stops the attacker at set times, and writes `run.json`, so later runs are one command.
- Add `-DNO_PEERS` build flag (node ignores peer frames = single-device adaptation baseline) and
  `-DTIMING` if the existing us_* fields are not enough.

### Hour 1:30-2:45 Attacks (the main deliverable)
Always target node 0 (it has the INA226). Pair each with a twin.
1. `poison_foa` (30 min): `poisoner.py --mode boiling --share 0.3 --ramp 1500`, then 2 min
   `--mode flood` to test that the attack is still detected. Twin: same, no attacker.
2. `poison_single` (30 min): same with node 0 built `-DNO_PEERS`. Twin as well if time.
   Compromised = flood detection rate drops while the twin keeps detecting.
   Report node 0's cumulative R and C against their budgets each cycle.
3. `freeze` (20 min): `--mode decoy`. FOA's trajectory (mu, s, R, C) should match the twin; check
   how many samples were alarmed and skipped.
4. `forgery` (10 min, can overlap another run): write `tools/forge_frames.py` that sends frames
   with a wrong key and replays of captured frames. Report accepted vs rejected (the `rejected`
   field). If sending ESP-NOW from the laptop is impossible, flash node 2 with `-DFORGE` that sends
   bad frames instead, and say so.
Run shorter versions (e.g. 15 min) if time is short, and say so; never fake a full run.

### Hour 2:45-3:20 Measurements
- `power`: from PWR lines, split by phase using cycle timestamps: idle/sampling, learning step,
  gossip/HMAC. Report mean mW per phase, mJ per learning cycle (measured, replacing the estimate).
- `timing`: per stage mean/max from us_propose, us_step, us_mac, us_verify; flash and RAM from
  compile output with and without FOA (`firmware/footprint_baseline` if it builds for ESP8266).
- If time: `shared_drift` (change all boards' traffic at once mid-run, FOA vs NO_PEERS), a
  Byzantine board (`-DBYZ` sends biased but validly signed frames), 50% frame drop (`-DDROP50`).

### Hour 3:20-4:00 Results, docs, fixes
1. `tools/analyze_session.py` -> `summary.csv`, `RESULTS.md`, figures:
   `fig_floor.png` (s_ratio and false alarms, floor vs no floor), `fig_poison.png` (node 0
   detection and R/C vs budget, FOA vs single vs twin), `fig_freeze.png`, `fig_power.png`.
   Clean, labelled, readable at slide size.
2. `RESULTS.md`: what ran, exact numbers, what failed, honest limits (3 boards, laptop-generated
   attacker, short runs, one target node). Compare each result with the simulation claim in
   section 1 and say plainly whether it agrees.
3. Append a dated section to `experiments/foa/RESEARCH_LOG.md` (follow its style).
4. Small paper/doc fixes (allowed):
   - `paper/related.tex`: RTTAD wording says it "stops otherwise"; correct to: it adapts in rounds
     from confident normal and abnormal samples, and rounds end when not enough such samples remain.
   - Byzantine proof slip in `paper/theory.tex`: "K-f > (1-f/K)K" is an equality, fix it.
   - `paper/hardware.tex`: add a paragraph with the measured hardware results (only real numbers).
   - Slides 3/4 wording "learned in full" should become "gets a large allowance": change the
     text in `demo/build_final_deck.py` and `demo/build_viva_prep.py` only; do NOT regenerate the
     deck (it embeds an unblurred photo). List what the user should rebuild.
   - Propose (do not apply) a new hardware results slide in `RESULTS.md` with its text and figure.
5. Final commit(s). Write `HANDOFF.md`: what is done, what is not, exact commands to repeat any run.

---------------------------------------------------------------------------------------------------
## 4. Use your judgement
- If something in this plan is wrong for the real code, fix the plan, write why in SESSION_LOG.md.
- Prefer one solid, fully paired result over five half-done ones. Priority if time runs out:
  working testbed > floor_clean > poison_foa vs poison_single > freeze > forgery > power > rest.
- Run long experiments in the background and do analysis/scripts/doc work in parallel.
- If boards crash or reboot, detect it (BOOT lines mid-run), note it, and rerun if needed.
- Anything surprising (FOA loses, floor hurts, numbers disagree with simulation) is a finding:
  record it honestly; do not tune on attacked runs to make it look better.
