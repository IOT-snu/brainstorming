FOA TECHNICAL IMPROVEMENT PLAN (CSD457 G-04), 27 Nov 2026
Scope: I only read files. I modified, committed and pushed nothing. Every paper or document cited below was found by web search or fetch in this run. Effort is in person-hours. "Board time" is unattended run time on the boards.

======================================================================
0. NEW REPO FACTS FROM THIS PASS (they change the plan)
======================================================================
F1. The stall is confirmed by the logs, not just inferred. On origin/hardware-results-20261127 (FOA_floor3/experiments/hardware/RESULTS.md), the final centre distances in continued_clean (4.9335, 4.5839, 3.5062 s0) match diverse_shared_drift_no_peers to 4 decimals. So the centres did not move at all during the 13-minute continuation.

F2. The cause is in two places in the code. firmware/esp8266_foa/foa_core.c:154 (`if (n_acc == 0 || n_core < 5) return;`) and experiments/foa/detector.py (`if len(core) < 5: return zero`) give a zero proposal and own_along = 0. Prop 4(i) in paper/theory.tex is exactly the clause that keeps alarmed points out of learning. So any fix must let alarmed points in through a channel that has its own budget and needs peers to agree. A fix that does not do this breaks the freeze proof.

F3. k_min = 2 in experiments/foa/fleet.py (Policy). On the 3-board testbed (K = 2) the common channel is therefore active, and its "geometric median" is the midpoint of the two peers. One Byzantine peer controls half of it.

F4. The common budget is loose on hardware timescales: (B0c + Bc t) rho = (0.75 + 0.06 t) rho, which is 18 rho after the 290 cycles of a 36-minute run. It constrains nothing in practice, and the common spread budget (B0cs 0.7, Bcs 0.02) is similarly generous.

F5. The fair static control has not been run. The 1.43 to 1.72% FPR run (rotated_calibration_clean) is FOA with the rotated stride. The static control (47.7 to 48.2%) used the old fixed stride. So the boards do not yet show FOA beating static.

F6. ESP8266 cost structure:
- The ESP8266 has no hardware FPU, so float math runs in software (esp8266.com forum notes of the core configuration, https://esp8266.com/viewtopic.php?p=92290; secondhand but consistent).
- foa_propose takes a score (a sqrt) for each of 150 x 16-D samples. This likely explains why the proposal takes 21.5 ms on the ESP8266 against 11.2 ms in the paper.
- Upper bound on FOA's energy: even if the whole board power (384 mW) is charged to the 25 ms of FOA compute, that is about 9.6 mJ per 10 s cycle, against about 3.84 J per cycle for the board. That is at most about 0.25%. Energy is dominated by the always-on radio (WIFI_NONE_SLEEP plus the 300 ms gossip wait), not by FOA.

F7. The frame (foa_core.c foa_frame_pack) has a free bit. n_core is at most 150, so bit 15 of the u16 n_core field can carry a flag without changing the 92-byte frame. The ESP-NOW v1 payload limit is 250 bytes (Espressif docs, https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/network/esp_now.html). That leaves room for per-pair tags for up to 10 receivers at 16 B each (76 B body + 16(N-1) <= 250).

======================================================================
1. RANKED PLAN (impact per effort, highest first)
======================================================================
Summary table: rank | item | effort (h) | impact | risk

| Rank | Item | Effort (h) | Impact | Risk |
|---|---|---|---|---|
| 1 | Calibration by reservoir sampling plus a self-check | 3 | very high | low |
| 2 | Fair controls on the boards (static / single / FOA, fixed calibration, 3 reps, fixed no-peer build) | 4, plus about 12 board | very high | low |
| 3 | K<3 guard: own-direction common channel, or add 2 boards | 1 to 3 | high | low |
| 4 | Fix the abrupt-drift stall (quorum-gated re-anchoring with its own budget) | 12 to 16 | very high | medium |
| 5 | Hardware attack trials (boundary, decoy, flood probe; forge/replay with a 4th board) | 8, plus about 16 board | very high | medium |
| 6 | Byzantine fix for the common spread channel, plus tighter common budgets | 6 to 10 | high | medium |
| 7 | Adaptive attacker suite in simulation | 10 to 14, plus compute | high | low |
| 8 | Key management: per-pair tags and a persistent epoch | 6 to 8 | medium-high | low |
| 9 | BALANCE / ClippedGossip baselines and a true DriftXpert trigger | 5 to 7 | medium-high | low |
| 10 | More seeds and bootstrap CIs; time-to-track (liveness) metric | 4, plus compute | medium | low |
| 11 | Gradual drift on the boards | 2, plus 8 board | medium | low |
| 12 | Device-only drift cost: saturation event, per-device B, operator re-baseline | 4 to 10 | medium | medium |
| 13 | Proposal timing: sqrt-free and fixed-point classification | 3 to 6 | medium | low |
| 14 | Energy per cycle measurement method | 5 to 7 | medium | low |
| 15 | IRAM headroom | 1 to 2 | low-medium | low |
| 16 | Peer trust, honey vectors, config digest | 3 to 6 each | low-medium | medium |

Theory fixes that the audit already listed (Minsker "at least", Weiszfeld approximation, K = 2 note, Cor 1 in minutes) take about 3 h and should be done alongside rank 1. They are not repeated below, except where a method change alters a proof.

======================================================================
2. (a) METHOD FIXES
======================================================================
A1 [rank 4]. Abrupt-drift freeze: quorum-gated re-anchoring that is itself poisoning-safe

Why
- Hardware shows 99.9% FPR forever after a shared step. Old Prop 4(ii) is true but empty, because B rho is admitted only of proposals that are zero (F2).

Design ("stall mode")
- Stall flag. A device sets stall = 1 if n_core < 5 for S consecutive cycles (S = 6, i.e. 1 minute). A CUSUM on the per-cycle alarm fraction is a better-calibrated alternative (Page 1954). The flag is sent in bit 15 of n_core, with FOA_FRAME_VERSION bumped. Because the flag travels inside the HMAC-covered body, keyless attackers cannot set it.
- Quorum. Stall mode runs only if the device itself is stalled AND at least ceil((K+1)/2) of its verified peers carry stall = 1 in the same cycle. This is a supermajority filter in the spirit of CIoTA's abnormality filtration (Mirsky et al. 2020).
- Direction comes from the device, not the peers. g = eta * (coordinate-wise median of the WHOLE batch - mu), with alarmed points included. This is the same robust statistic as the existing dmed, but taken over all points.
- Peers only confirm and scale. lambda_q = clip(median over stalled peers of (their g_j . u) / ||g||, 0, 1), with u = g/||g||. Peers send their own g_j in the dmu slot while stalled. This mirrors the existing "own" common_dir mode: Byzantine peers can scale the move down but cannot steer it, which matters at K = 2.
- New anchor accumulator A, with a per-cycle cap and its own budget. Step a_q = project(lambda_q * g) so that ||a_q|| <= b_q * rho (for example b_q = 0.05) and ||A|| <= (B0a + Ba * n_q(t)) rho. Here n_q(t) counts quorum-stall cycles only, so A cannot grow at all in normal operation.
- The spread gets the same treatment: a whole-batch MAD-based log-spread step, with |a_qs| <= b_qs.

Effect on the proofs
- Thm 1 becomes mu = mu0 + C + R + A, with ||A|| <= La(t) rho. The induction is unchanged.
- Cor 1 becomes d50 <= tau * e^{Cs + Ls + Las} + tau (L(t) + La(t)). Because La only grows in quorum-stall cycles, t* is unchanged unless more than half the fleet is stalled.
- Prop 4(i) holds verbatim whenever fewer than half the peers are stalled: a decoy flood on one device trips its own stall flag but no quorum.
- Prop 4(ii) gains real content: after a fleet-wide step, learning resumes within S cycles at b_q rho per cycle. Recovery from a jump of Delta alarm radii takes about S + Delta/b_q cycles, about 4 to 7 minutes for Delta = 1 to 2 at 10 s cycles.

Honest limit
- An attacker who can flood MORE than half the fleet at once (for example, the whole LAN) can drag every device at b_q rho per cycle, up to La. This is the fleet-level version of Prop 3 and of WARDEN's two-world theorem: a fleet-wide jump and a fleet-wide attack look the same without labels. Say so in the paper.
- Mitigations: a small b_q and Ba; emit a "fleet stall" event to the operator (a fleet-wide 100% alarm rate is alert-worthy anyway); optionally require a signed operator acknowledgement before La exceeds 1 rho.

Rejected alternatives (and why)
- Periodic recalibration: poisonable by design.
- WARDEN-style frozen reserve: cannot follow a regime change.
- Spread inflation alone: widens acceptance for the attacker, and the 0.001/cycle budget is far too slow.

Files
- experiments/foa/detector.py (whole-batch g in Proposal), foa_rule.py (stall branch, A accumulator), fleet.py (Policy fields S, b_q, B0a, Ba; flag propagation), attacks.py (multi-device decoy).
- firmware/esp8266_foa/foa_core.c and .h (propose, step, frame flag), esp8266_foa.ino (log A and the stall flag), mirrored in firmware/esp32_foa.
- firmware/make_vectors.py and host_test.c; paper/theory.tex (Thm 1, Cor 1, Prop 4).

Tests
- Property test in experiments/foa/tests/test_foa.py: 1e5 random steps with random stall flags and Byzantine frames. Assert ||R|| <= L rho, ||A|| <= La rho, and that A changes only in quorum cycles.
- The existing E5 decoy bit-for-bit test must pass unchanged.
- New E13 (sim, held-out seeds 2 to 11): shared step of 1, 2 and 4 alarm radii on N-BaIoT and CESNET. Report time-to-recover (FPR below 2x the pre-step level) for FOA, FOA+stall, single, static and KL.
- E13b: decoy flood on m of N devices (m = 1 to N), followed by the boundary attacker. Expected: no change for m < N/2, and a bounded drag for m > N/2.
- Hardware: rerun the period-halving drift run. Success means FPR under 5% within 10 minutes.
- Before trusting the trigger, test it against drift that window-based detectors miss (Hinder et al. 2025).

Effort and risk
- About 12 to 16 h (sim 6, firmware 4, tests and theory 4).
- Medium risk: the S and b_q choices trade recovery speed against the drag in the m > N/2 attack. Choose them on dev seeds 0 and 1 only.

A2 [rank 6]. Byzantine common spread channel (open problem; E6b compromises trace to it)

Why
- The channel uses a 1-D median of peer dls with a generous budget.
- lam_s = ps_ema/ms_ema uses the EMA of the device's own (non-robust) proposal, which a local poisoner can push to 1.
- Thm 2 does not cover this channel.

What to do
(1) Make lam_s robust. Replace it with the median, over core points, of the radius ratio (score / current s), giving a median-based own spread change in the same way own_along replaced p_ema. Its cost is one sort of at most 150 floats, which the firmware already does for `along`.
(2) Use an asymmetric budget. Spread GROWTH widens acceptance and is what an attacker wants; shrinking is a false-alarm problem that the coverage floor already bounds. Cap common-channel growth tightly (for example Bcs_up = 0.002/cycle and B0cs_up = 0.1) and leave shrinking under the old budget and the floor.
(3) Add a 1-D lemma to theory.tex. With f < K/2 the median lies between the minimum and maximum honest values, so |ms - ms^H| <= max_j |e_j^H - ms^H|. This is elementary and needs no Minsker constant. With it, Thm 2 covers both channels. Also add the projection-based "Byzantine can scale but not steer" statement for common_dir = "own".
(4) Tighten Bc (F4). Sweep Bc in {0.005, 0.01, 0.02, 0.06} on dev seeds, measuring liveness (E1/E11 shared-drift FPR) against E6b compromise, then pick the knee.

Files
- foa_rule.py (lam_s and the asymmetric clip), detector.py (radius-ratio median), fleet.py (Policy fields), foa_core.c, theory.tex, robust.py (minsker_constant docstring).

Tests
- Rerun E6b (f = 0 to 4, plus the poisoner). Target: below 40% at f = 2 and a lower number at f = 3. Report the cost on E1/E11 FPR.
- Property test for the asymmetric spread budget.

Effort and risk
- 6 to 10 h plus compute.
- Medium risk: a tighter growth budget may raise FPR when honest variance grows (camera devices).

A3 [rank 3]. K < 3 guard

Why
- F3: the geometric median of 2 points gives no Byzantine protection, so Thm 2 says nothing about the testbed.

What to do
- When K < 3, switch to common_dir = "own" automatically. That code path already exists in foa_rule.py: direction from the device's own robust median, with peers only scaling it.
- Alternatively, set k_min = 3 and buy 2 more ESP8266 boards (5 boards give K = 4, which tolerates f = 1).
- Report the testbed as "K = 2: Byzantine claims rest on own-direction scaling, not on Lemma 1".

Files
- fleet.py (k_min and auto mode), foa_core.c (the own-direction path, if not already ported; check), .ino.

Tests
- Rerun E6b at N = 3 with f = 1 in both modes.

Effort and risk
- 1 h code; boards about 2 h to flash. Low risk.

A4 [rank 12]. Device-only drift cost (FOA+floor 24.6% vs single+floor 0.9%)

Why
- Prop 3 makes this cost unavoidable from traffic alone, so the options either change how the cost is reported or add a trusted side channel. Say this plainly.

Options, cheapest first
(a) Budget-saturation event. When ||R|| >= 0.9 L(t) rho for S cycles, raise ONE "device-only drift exceeds budget" event, and report alarm events per day next to per-sample FPR. The update rule is untouched, so no proof changes. This is a reporting improvement, not better detection. 2 h.
(b) Per-device B, set from the measured honest drift rate of each device class on dev seeds (cameras faster). Thm 1 and Cor 1 then hold with a per-device B and per-device t*. Expected effect: lower FPR on fast-drifting devices and a shorter t* there, so report both. 3 h plus compute.
(c) Operator-signed re-baseline. An authenticated maintenance message (operator key, not a peer key) sets mu0 := mu, R := 0 and t_join := now. This is the only way to break Prop 3, because it adds labels. It changes the threat model (the operator key becomes critical). Cor 1 holds between re-baselines. 4 h.
(d) Do NOT add an adaptive B_t driven by a traffic statistic without a hard B_max. With B_t <= B_max, Thm 1 holds with L(t) <= B0 + B_max t, but an attacker can imitate whatever "smooth persistent drift" the trigger looks for (Hinder et al. 2025). The guarantee is then only the B_max one.

Files
- foa_rule.py, fleet.py, experiments.py (new metric), .ino (event line), paper eval and theory text.

Tests
- E1 device-only rows; E12; Cor 1 checker per device.

======================================================================
3. (b) MISSING EXPERIMENTS
======================================================================
B1 [rank 1 prerequisite, rank 2]. Fair controls on the boards

What
- In ONE session, with the fixed calibration (C3 below), run static, single (ignore peers) and FOA.
- Order: randomized ABC blocks, 3 repetitions each, 36 minutes each.
- The no-peer build must keep the GOSSIP_WAIT_MS receive wait and only drop the frames. The 27 Nov build skipped the wait, which is the confound noted in the log.
- Metrics: FPR over the full run and in the first 20 minutes, centre walk divided by rho, and a 95% CI across the repetitions.
- Commit every build as a -D flag set plus the binary's SHA-256, together with the raw serial logs.

Files
- esp8266_foa.ino (an IGNORE_PEERS flag that keeps the wait), experiments/hardware/analyze.py (CIs, rho-normalised walk), a new runner script under experiments/hardware/.

Effort and risk
- 4 h, plus about 12 h board time (overnight). Low risk.

B2 [rank 5]. Hardware attack trials

What
- Boundary: firmware/laptop/poisoner.py --mode boiling --share 0.3 --ramp 1800 against one node. Then --mode flood for 5 minutes as the compromise probe: recall = alarm fraction during the flood.
- Decoy: --mode decoy for 10 minutes. FOA centre should not move (with A1: no quorum, so no anchor movement).
- Paired attacker-free twins: the same configuration, boot order and duration with the poisoner off. Use ABAB alternation and 3 repetitions. Configurations: FOA, single, static.
- Forgery, replay and bit flips need a 4th ESP8266 as the attacker radio, because the laptop cannot inject ESP-NOW. Firmware for it: record frames, replay them after 1 s and after 61 s (this tests the PEER_RESET_MS hole), forge with a wrong key, flip bits. Expected: all rejected except the 61 s replay, which should succeed today. That is a finding to report, and it is fixed by C5.
- Report per-cycle d50 against the Cor 1 bound in minutes. Be careful: the features are damped statistics of the whole node's traffic, so on the boards "share p" does not mean p of the samples, as it does in the simulations.

Files
- firmware/laptop/poisoner.py (a run-tag and log marker), a new firmware/attacker_esp8266/ sketch, experiments/hardware/analyze.py.

Effort and risk
- 8 h, plus about 16 h board time.
- Medium risk: with 3 boards, effects may be within run-to-run variance. That is why there are 3 repetitions.

B3 [rank 11]. Gradual drift on the boards

What
- Ramp TX_PERIOD_MS from 200 to 100 ms linearly over 60 minutes, and again over 180 minutes, on all boards (shared drift). Also run the ramp on one board only (device-only drift).
- Prediction to state before the run: shared drift passes through the common channel. Device-only drift is admitted at most at B rho = 0.005 rho per 10 s cycle, i.e. 0.03 rho per minute. So the 60-minute device-only ramp should exceed the budget and the 180-minute one may not.
- Compare FOA, single and static.

Effort
- 2 h (a period-schedule build flag), plus 8 h board time.

B4 [rank 10]. More seeds, CIs and liveness

What
- Extend the held-out seeds from 2 to 11 to 2 to 31 for E3 and E12. Bootstrap CIs over seeds and victims. Report CESNET with 10 seeds, and more institutions if the dataset allows.
- Add time-to-track: the number of cycles until a shared or device-only drift's FPR returns below 2x baseline, as a function of B and Bc. This answers the "liveness" question raised in W3 of the sweeps.
- Keep the victim rule unchanged and pre-register it in RESEARCH_LOG.md.

Files
- experiments/foa/experiments.py, floor_eval.py, paper/make_numbers.py.

Effort
- 4 h, plus compute.

B5 [rank 7]. Stronger adaptive attackers (all in attacks.py, with paired twins)

(i) Budget-saturating straight-line attacker. Each cycle it moves the residual exactly B rho toward the target (the greedy optimum against this rule, in the spirit of Kloft and Laskov 2012). This tests how tight Cor 1 is. If the measured t* is close to (M - 1.2)/0.006, the bound is tight. If not, report the gap.
(ii) ALIE colluding peers (Baruch et al. 2019). f peers propose m^H + z_max * sigma * u, just under the significance ramp, with u held fixed over cycles. This is the time-coupled attack of Karimireddy et al. 2021. Report the common displacement against the Thm 2 rate bound.
(iii) Frog-boiling peers (Chan-Tin et al. 2009). The same attack, but the bias grows slowly over time.
(iv) Stall-trigger attacker, for A1: decoy floods on m of N devices followed by a boundary attack.
(v) White-box attacker that reads the live state (C, R, lambda, w) and picks the direction that maximises lambda's agreement, set against a grey-box attacker that knows only mu0. These are the knowledge levels of Cong et al. 2024 (IEEE S&P).
(vi) Gradual injection parameterised by poisoned-data rate (Nguyen et al. 2020), so the numbers are comparable with the DIoT backdoor results.

Metrics
- Compromise rate, t* in minutes, and Korycki and Krawczyk's "relative loss of robustness".

Effort
- 10 to 14 h, plus compute.

B6 [rank 9]. Baselines

What
- BALANCE (Fang et al., CCS 2024): accept peer j if ||mu_i - mu_j|| <= gamma * exp(-kappa t/T) * ||mu_i||, then mix.
- ClippedGossip (He et al., preprint): clip each peer delta to a ball around the node's own centre.
- A true DriftXpert-style trigger (drift detection that TRIGGERS an update), replacing or sitting beside the "or" pause gate, which should be renamed.
- Expected, to state up front: BALANCE fails on shared drift late in deployment because its radius shrinks. Test this on E1/E11 and E13.

Files
- fleet.py modes; experiments.py.

Effort
- 5 to 7 h.

======================================================================
4. (c) HARDWARE AND FIRMWARE
======================================================================
C1 [rank 1]. Calibration aliasing: reservoir sampling plus a self-check

Why
- The fixed CAL_EVERY = 10 stride (esp8266_foa.ino:190) is phase-locked to the 200 ms telemetry. The rotated stride is a patch that happens to work for 160/200/240 ms. It still fails for a period whose remainder against the stride cycle is unlucky.

What
- Replace the stride with Vitter's Algorithm R over a longer window (for example 600 s, at 50 ms sampling, into CAL_CYCLES x BATCH = 300 slots). Use the existing xorshift rng_state seeded from the MAC address and micros(). Uniform random selection cannot phase-lock to any period.
- Add plus or minus 10% random jitter to SAMPLE_MS.
- Self-check: hold out 20% of the reservoir. If the held-out FPR is above 3x the nominal 1%, recalibrate before operation starts. Calibration is assumed clean in the threat model, so this adds no attack surface. State that assumption.
- Fit the real basis with fit_calibration.py --from-logs and stop using the PLACEHOLDER W/FEAT_MEAN/FEAT_STD in foa_config.h before any feature-level claim.

Files
- esp8266_foa.ino sample(), foa_config.h, the firmware/esp32_foa twin, host_test.c (a fixture at 160/200/240 ms and a 250 ms adversarial case), fit_calibration.py.

Tests
- Host fixture: flagged fraction of 400 clean samples at or below 2% for all periods (today: fixed stride 101/400, rotated 11/400).
- Boards: the B1 static control.

Effort and risk
- 3 h. Low risk. Memory is unchanged: same buffer, plus one counter.

C2 [rank 13]. Proposal timing 21.5 ms; fix the paper's inconsistent numbers

What
- Compare squared distances against (tau*s)^2 and (c*s)^2, which removes 150 sqrtf calls per cycle in software float (F6).
- Optionally use a Q15/Q16 fixed-point classification loop. Re-measure with micros() split into classification, median and the rest.
- Then report ONE set of ESP8266 numbers, and separately the ESP32 ones, in the abstract, hardware.tex and cost.tex.

Tests
- host_test equivalence (it must still show 0 mismatches; fixed point needs a tolerance study).

Effort and risk
- 3 h for the float fix, 6 h with fixed point. Low risk.

C3 [rank 14]. Energy per cycle: measurement method

Why
- The INA226 is read every 40 ms with about 35 ms averaging, so 1.6 ms phases cannot be resolved.

Method
(1) Differential microbenchmark. With Wi-Fi off (WiFi.mode(WIFI_OFF) plus forced modem sleep), run foa_propose / foa_step / HMAC in a tight loop for 30 s, then delay() for 30 s, and alternate 10 times. Then E_phase = (P_loop - P_idle) x t_phase. This removes the radio from the measurement.
(2) Phase markers. Toggle a GPIO around each phase and sample the INA226 at 140 us conversion time with averaging 1. The datasheet allows 140 us to 8.244 ms and averaging from 1 to 1024 (TI SBOS547B). Do the sampling from a SECOND MCU or a logic-analyser-equipped board, so the device under test is not disturbed by the I2C polling. Align the samples to the markers.
(3) Report three numbers: board energy per cycle (about 3.84 J at 384 mW x 10 s), the FOA compute share (upper bound 9.6 mJ, F6), and the radio share (gossip wait plus TX). The honest message is that FOA's compute is negligible and the radio policy dominates. Then test a duty-cycled gossip window (modem sleep outside a scheduled 300 ms slot) as the real energy lever.

Files
- a new firmware/energy_bench/, firmware/ina219_monitor/ (or an INA226 sampler on the second board), experiments/hardware/analyze.py.

Effort
- 5 to 7 h, plus 2 h board time.

C4 [rank 15]. IRAM at 93%

What
- Measure before changing anything: xtensa-lx106-elf-nm --size-sort -S on the .elf, filtered to .iram sections. Nothing in firmware/esp8266_foa uses IRAM_ATTR or ICACHE_RAM_ATTR (grep), so the usage is the core, Wi-Fi and lwIP.
- If headroom is needed (new ISR code, or the energy GPIO ISR), use the core's MMU option "16KB cache + 48KB IRAM" (-DMMU_IRAM_SIZE=0xC000 -DMMU_ICACHE_SIZE=0x4000; arduino-esp8266 docs). It trades cache for IRAM, so re-measure C2 timing afterwards, because flash-resident code may slow down.
- Keep the ESP-NOW receive callback out of IRAM, and do not add float printf in ISRs.

Effort and risk
- 1 to 2 h. Low risk if timing is re-measured.

C5 [rank 8]. Key management and replay

Why
- FOA_KEYS[N_NODES][32] is on every board, so capturing one board yields every identity.
- The PEER_RESET_MS = 60 s exception (esp8266_foa.ino:228) reopens replay.

What
- Per-pair keys: each frame carries N-1 truncated 128-bit tags, one per receiver, so a captured board can only speak as itself.
  - Cost: (N-1) x about 0.6 ms of signing (measured on our build). For comparison, Pearson et al. (ICC 2019) measured 182 us per HMAC-SHA256 on an ESP8266.
  - Frame: 108 B for N = 3, within the 250 B v1 limit up to N = 11.
  - Per-cycle ECDSA is not viable: Pearson et al. report about 2.48e5 us (about 248 ms) per ECC signature generation on the ESP8266.
  - For larger fleets, muTESLA/TESLA (Perrig et al., SPINS 2002; RFC 4082) gives broadcast authentication from symmetric primitives with delayed key disclosure. It costs one cycle of latency, which FOA can absorb because it already uses EMAs.
- Persistent epoch: a boot counter in flash, incremented once per boot. Frames carry epoch||cycle, and receivers accept only lexicographically larger values. Remove the 60 s exception. Receivers persist each peer's last epoch on change, which is rare, so flash wear is about one write per peer reboot.
- Use n_core. In normal mode, exclude peers reporting n_core < 5 from the median instead of letting them vote zero. Test the effect on E1 liveness, because this changes the dynamics.

Files
- foa_core.c (pack/verify), foa_config.h (key generation per pair in fit_calibration.py), esp8266_foa.ino, gossip.py (the sim frame), E6 in experiments.py.

Tests
- host_test (tamper and RFC 4231 cases), the B2 forge/replay trials.

Effort and risk
- 6 to 8 h. Low risk. Development keys must not stay in the public repo.

======================================================================
5. (d) IDEAS BORROWED FROM PRIOR ART (all found in this run)
======================================================================
1. Minsker, "Geometric median and robust estimation in Banach spaces", Bernoulli 21(4):2308-2335, 2015. https://arxiv.org/abs/1308.1334
   Restate Lemma 1 with "at least (1-alpha)K".
2. Pillutla, Kakade, Harchaoui, "Robust Aggregation for Federated Learning" (RFA), IEEE Trans. Signal Processing 70:1142-1154, 2022. https://arxiv.org/abs/1912.13445
   Smoothed Weiszfeld with a fixed iteration count gives bounded board timing and avoids the 1e-9 distance clamp when two peers coincide.
3. Karimireddy, He, Jaggi, "Learning from History for Byzantine Robust Optimization", ICML 2021, PMLR 139:5311-5319. https://proceedings.mlr.press/v139/karimireddy21a.html
   Time-coupled attacks are the formal motivation for the growing budget. Centered clipping around the previous aggregate is an alternative for the common channel.
4. He, Karimireddy, Jaggi, "Byzantine-Robust Decentralized Learning via ClippedGossip", arXiv 2202.01545 [preprint]. https://arxiv.org/abs/2202.01545
   Use as a baseline and as an aggregator option at small K.
5. Fang, Zhang, Hairi, Khanduri, Liu, Lu, Liu, Gong, "Byzantine-Robust Decentralized Federated Learning" (BALANCE), ACM CCS 2024. https://arxiv.org/abs/2406.10416
   Use as a baseline (B6).
6. Gaucher, Dieuleveut, Hendrikx, "Unified Breakdown Analysis for Byzantine Robust Gossip", ICML 2025, PMLR 267:18868-18896. https://proceedings.mlr.press/v267/gaucher25a.html
   Use the CS+ aggregator and the paper's breakdown bound to state what K = 2 or 4 can tolerate. Use its decentralised attack in B5.
7. Baruch, Baruch, Goldberg, "A Little Is Enough: Circumventing Defenses For Distributed Learning", NeurIPS 2019. https://arxiv.org/abs/1902.06156
   The ALIE attacker (B5-ii).
8. Chan-Tin, Feldman, Hopper, Kim, "The Frog-Boiling Attack: Limitations of Anomaly Detection for Secure Network Coordinate Systems", SecureComm 2009 (Springer); extended in ACM TISSEC 2011. https://www-users.cs.umn.edu/~hopper/frogBoiling.pdf
   Motivation, and attacker B5-iii. The paper should say that FOA's defence rests on the cumulative budget, not the per-step gate.
9. Kloft, Laskov, "Security Analysis of Online Centroid Anomaly Detection", JMLR 13:3681-3724, 2012. https://jmlr.org/papers/v13/kloft12b.html
   The greedy optimal attack, as a tightness test of Cor 1 (B5-i).
10. Bose, Lessard, Fazel, Dvijotham, "Keeping up with dynamic attackers: Certifying robustness to adaptive online data poisoning", AISTATS 2025, PMLR 258. https://proceedings.mlr.press/v258/bose25b.html
    Longer term: compute a certificate on the worst long-run centre offset for (B, b_q, z), and tune B by benign FPR + kappa * certificate instead of by hand.
11. Atarmla, "The Price of Self-Calibration: Exact Evidence Budgets and Manufactured Blind Sets in Adaptive Monitoring", arXiv 2609.23254, Sept 2026 [preprint]. https://arxiv.org/abs/2609.23254
    State FOA's blind set (residual drift at or below B per cycle). Calibrate the stall trigger's windowed alarm rate on the 1/L scale the paper derives, not the binomial 1/sqrt(L).
12. Balachandran, "Self-Poisoning in Adaptive Out-of-Distribution Detection: A Sharp-Threshold Theory and Certified Label-Free Calibration" (WARDEN), arXiv 2607.21673, July 2026 [preprint]. https://arxiv.org/abs/2607.21673
    Its two-world theorem is the honest frame for the m > N/2 limit of A1.
13. Page, "Continuous Inspection Schemes", Biometrika 41(1-2):100-115, 1954. https://doi.org/10.1093/biomet/41.1-2.100
    A CUSUM stall trigger (A1).
14. Sunaga, Yamada, Matsutani, "A Sequential Approach to Detect Drifts and Retrain Neural Networks on Resource-Limited Edge Devices", IEICE Trans. Inf. & Syst. E107-D(6), 2024. https://www.jstage.jst.go.jp/article/transinf/E107.D/6/E107.D_2023EDP7123/_article
    Preprint: Yamada, Matsutani, arXiv 2212.09637.
    A cheap sequential drift detector validated on a Raspberry Pi Pico, as an alternative stall/drift trigger with small memory.
15. Hinder, Vaquet, Hammer, "Adversarial Attacks for Drift Detection", ESANN 2025 (arXiv 2411.16591). https://arxiv.org/abs/2411.16591
    Evaluate any trigger (A1, A4d) against drift built to evade window-based detectors.
16. Mirsky, Golomb, Elovici, "Lightweight Collaborative Anomaly Detection for the IoT using Blockchain", J. Parallel and Distributed Computing 145:75-97, 2020. https://arxiv.org/abs/2006.10587
    A supermajority filter, used as the A1 quorum.
17. Vitter, "Random Sampling with a Reservoir", ACM TOMS 11(1):37-57, 1985. https://doi.org/10.1145/3147.3165
    Calibration sampling (C1).
18. Perrig, Szewczyk, Wen, Culler, Tygar, "SPINS: Security Protocols for Sensor Networks", Wireless Networks 8:521-534, 2002 (https://www.doi.org/10.1023/A:1016598314198); and Perrig, Song, Canetti, Tygar, Briscoe, RFC 4082 (TESLA), 2005 (https://www.rfc-editor.org/rfc/rfc4082). RFC 4082 is an Informational RFC, not peer reviewed.
    Broadcast authentication (C5).
19. Pearson, Luo, Zhang, Dey, Ling, Bassiouni, Fu, "On Misconception of Hardware and Cost in IoT Security and Privacy", IEEE ICC 2019. https://par.nsf.gov/servlets/purl/10149710
    Table II: HMAC 182 us, ECC signature generation about 2.48e5 us on the ESP8266. These numbers justify keeping HMAC and rule out per-cycle ECDSA.
20. Nguyen, Rieger, Miettinen, Sadeghi, "Poisoning Attacks on Federated Learning-based IoT Intrusion Detection System", NDSS DISS 2020. https://www.ndss-symposium.org/wp-content/uploads/2020/04/diss2020-23003-paper.pdf
    Gradual-injection attacker swept by poisoned-data rate (B5-vi). Name it as FOA's threat model.
21. Fung, Zhang, Aib, Boutaba, "Dirichlet-Based Trust Management for Effective Collaborative Intrusion Detection Networks", IEEE TNSM 8(2), 2011. https://personal.ntu.edu.sg/zhangj/paper/tnsm10.pdf
    Rank 16: a per-peer trust score (a few bytes per peer) that down-weights peers whose proposals keep landing outside the honest interval. It must enter only as a weight in [0,1] on the median input, so Thm 1 still holds.
22. Garcia, Bessani, Gashi, Neves, Obelheiro, "OS diversity for intrusion tolerance: Myth or reality?", IEEE/IFIP DSN 2011. https://openaccess.city.ac.uk/id/eprint/526/
    Measure shared CVEs across the N-BaIoT device families to justify the "fewer than half of peers share an exploit" assumption instead of asserting it. About 4 h.
23. Korycki, Krawczyk, "Adversarial concept drift detection under poisoning attacks for robust data stream mining", Machine Learning 112:4013-4048, 2023. https://link.springer.com/article/10.1007/s10994-022-06177-w
    The "relative loss of robustness" metric. Note the bib year is wrong (it says 2022).
24. Cong, He, Shen, Zhang, "Test-Time Poisoning Attacks Against Test-Time Adaptation Models", IEEE S&P 2024. https://arxiv.org/abs/2308.08505
    Attacker knowledge levels (B5-v).
25. Toso, Anderson, Pinot, Gupta, "Byzantine-Robust Federated Representation Learning", arXiv 2609.36660, Sept 2026 [preprint]. https://arxiv.org/abs/2609.36660
    Theoretical support for aggregating only the shared part robustly. Borrow its bound structure when restating Thm 2.
26. Ochiai, Nishihata, Tomiyama, Sun, Esaki, "Detection of Global Anomalies on Distributed IoT Edges with Device-to-Device Communication", ACM MobiHoc AIoT workshop 2023 (arXiv 2407.11308). https://arxiv.org/abs/2407.11308
    Gossiped thresholds with a self-weight, as an alternative design for the spread channel to compare against A2.
27. Ino, Yoshida, Matsutani, Fujino, Sensors 24(19):6416, 2024. https://doi.org/10.3390/s24196416
    Physical sensor-injection poisoning. This only applies if FOA's features include sensor values. Today they are packet size and gap statistics (foa_features.c), so it is low priority and should be said as such.

Supporting documentation used
- Espressif ESP-NOW docs (250 B v1 payload; multicast encryption not supported).
- arduino-esp8266 MMU docs (https://arduino-esp8266.readthedocs.io/en/3.1.1/mmu.html).
- TI INA226 datasheet SBOS547B (https://www.ti.com/lit/ds/symlink/ina226.pdf).

======================================================================
6. HONEST CAVEATS ON THIS PLAN
======================================================================
- A1 does not make FOA safe against an attacker who controls more than half the fleet's traffic at once. It converts a permanent freeze into a bounded, observable drag. Any claim beyond that is an overclaim.
- A4 cannot remove the device-only drift cost without a trusted side channel (Prop 3). Options (a) and (b) reframe or reallocate the cost, and only (c) removes it, at the price of an operator key.
- The hardware results will stay weak evidence with 3 boards and K = 2 until B1, B2 and A3 are done. Even then, the traffic is the boards' own telemetry, not real IoT traffic.
- The effort estimates assume the simulation harness runs as documented. Compute time for the 30-seed reruns was not measured in this pass.
- The ESP8266 no-FPU fact comes from secondhand forum sources found in this run. Confirm it against Espressif's LX106 documentation before putting it in the paper.
- Several sources were read only at abstract or table level: Bose, Gaucher, Toso, Yamada/Sunaga, Garcia, Fung, Page and Vitter. For Pearson et al., only Table II was read, and its column layout in pdftotext output should be checked against the PDF.

Key repo paths for this plan
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/experiments/foa/foa_rule.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/experiments/foa/detector.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/experiments/foa/fleet.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/experiments/foa/tests/test_foa.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/foa_core.c
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/esp8266_foa.ino
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/foa_config.h
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/laptop/poisoner.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/theory.tex
- origin/hardware-results-20261127:FOA_floor3/experiments/hardware/RESULTS.md