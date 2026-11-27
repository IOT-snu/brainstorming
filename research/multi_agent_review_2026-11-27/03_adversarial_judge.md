ADVERSARIAL NOVELTY AND EVIDENCE REVIEW: FOA (CSD457 G-04), 27 Nov 2026
Read only. I modified, committed and pushed nothing. I checked a few repo facts myself (paper/theory.tex lines 49, 60, 72; firmware/esp8266_foa/foa_config.h:26; esp8266_foa.ino:51, 228; the RESULTS.md on origin/hardware-results-20261127). Papers marked [V] I found and opened in this run. Papers marked [S] come from the three sweeps in this same workflow run and I did not re-open them.

======================================================================
0. NEW PRIOR ART I FOUND THAT THE SWEEPS MISSED
======================================================================
These are the works most likely to be used to refute novelty.

N1 [V] Y. Chen, S. Kar, J. M. F. Moura, "Resilient Distributed Estimation: Sensor Attacks", arXiv 1709.06156 (v3, 2018) [preprint; I could not confirm a journal version]. https://arxiv.org/abs/1709.06156
- The SIU update is x_n(t+1) = x_n - beta_t * sum over neighbours (x_n - x_l) + alpha_t * K_n(t) * (y_n - x_n).
- The local innovation is saturated to norm gamma_t. All estimates converge if fewer than half of the sensors are attacked, whatever the topology.
- Structurally this is "peer consensus plus a norm-bounded local term, with a breakdown below one half". That is the skeleton of FOA.
- Differences: the parameter is static (the paper lists drift as future work). gamma_t SHRINKS over time, while FOA's budget GROWS. It is estimation, not anomaly detection. It has no freeze analysis and no hardware.
- This is the single most dangerous citation for us. It must go in the paper.

N2 [V] H. J. LeBlanc, H. Zhang, X. Koutsoukos, S. Sundaram, "Resilient Asymptotic Consensus in Robust Networks", IEEE JSAC 31(4), 2013. https://cs.vuse.vanderbilt.edu/koutsoxd/www/Publications/resilientConsensusJSAC2013.pdf
- W-MSR resilient consensus, the classical root of "robust consensus with local filtering".
- An examiner from control theory will ask why it is not cited.

N3 [V] B. Krishnamachari, S. Iyengar, "Distributed Bayesian Algorithms for Fault-Tolerant Event Region Detection in Wireless Sensor Networks", IEEE Trans. Computers 53(3), 2004. https://ceng.usc.edu/~bkrishna/research/papers/KrishnamachariIyengarBayesianEventDetectionTC03.pdf
- Uses neighbour agreement to tell shared events from single-sensor faults. This is the non-adversarial ancestor of FOA's split into a "shared part" and a "device-only part".

N4 [V] I. Vervlimmeren, X. Chesterman, T. Verstraeten, A. Nowe, J. Helsen, "Scalable SCADA-driven Failure Prediction for Offshore Wind Turbines Using Autoencoder-Based NBM and Fleet-Median Filtering", Wind Energy Science Discussions, doi 10.5194/wes-2025-49, 2025 [preprint, in discussion]. https://wes.copernicus.org/preprints/wes-2025-49/
- Compares each turbine to a windowed fleet MEDIAN to remove common effects. Fleet-median referencing is established industrial practice.
- It filters scores. It does not gate adaptation, and it has no adversary.

N5 [V] D. Stankovic et al. (consensus-based distributed blind calibration), Sensors 18(11):4027, 2018. https://www.mdpi.com/1424-8220/18/11/4027
- Neighbour consensus corrects drifting sensors. I found no Byzantine version.

N6 [V] Y. Wang, S. Jha, K. Chaudhuri, "An Investigation of Data Poisoning Defenses for Online Learning", arXiv 1905.12121 (2019/2020) [preprint]. https://arxiv.org/abs/1905.12121
- Gives conditions under which standard defenses allow or prevent RAPID poisoning of online learners. This is the closest formal antecedent to "time to compromise".

N7 [V] A. Bose, L. Lessard, M. Fazel, K. Dvijotham, "Keeping up with dynamic attackers: Certifying robustness to adaptive online data poisoning", AISTATS 2025, PMLR 258. https://arxiv.org/abs/2502.16737
- Confirmed. It certifies the effect of an adaptive online poisoner.

N8 [V] M. Kravchik, A. Shabtai, "Can't Boil This Frog: Robustness of Online-Trained Autoencoder-Based Anomaly Detectors to Adversarial Poisoning Attacks", arXiv 2002.02741 (2020) [preprint]. https://arxiv.org/abs/2002.02741
- Gradual poisoning of online-retrained ICS detectors worked only in limited cases. Reviewers may say the threat is weaker in practice than we claim.

N9 [V, grey literature, not a paper] GitHub gotsevrossen/ML-router-anomaly-detection, README dated around Oct 2026. https://github.com/gotsevrossen/ML-router-anomaly-detection
- A per-device router detector with "daily and cumulative shift budgets" and a slow anchor model. The README says a boiling-frog ramp is caught only by the cumulative budget.
- No peers. It shows that cumulative adaptation budgets are already engineering folk practice. Do not claim the budget idea itself.

N10 [V, search snippet only] Zhang, He, Huang, Ling, "Byzantine-Robust and Communication-Efficient Personalized Federated Learning", IEEE Trans. Signal Processing, 2025. https://signalprocessingsociety.org/publications-resources/ieee-transactions-signal-processing/2025/01/byzantine-robust-and-communication-efficient-personalized-federated-learning
- Robust aggregation of a shared model plus local personal models. Check the author list before citing.

Also re-found in my own searches: Kloft and Laskov JMLR 2012 [V]; Alhelou et al., ISCAS 2026, Essex repository [V]; ANTIDOTE, IMC 2009 [V]; Korycki and Krawczyk [V, arXiv 2009.09497]; Gaucher et al. (2405.03449) [V].

======================================================================
1. CLOSEST PRIOR WORKS, PER AXIS
======================================================================
Axes: (a) multi-device consensus, (b) Byzantine or poisoning robustness, (c) drift adaptation, (d) bounded updates and time to compromise, (e) split into shared and device-only parts, (f) freeze resistance, (g) MCU hardware.

| Work | a | b | c | d | e | f | g |
|---|---|---|---|---|---|---|---|
| Chen, Kar, Moura SIU [V] | H | H (<1/2) | none (static) | M: per-step saturation, shrinking | M: consensus term vs local innovation | none | none |
| BALANCE, CCS 2024 [S] | H | H | none | M: shrinking radius | L | none (invites a freeze) | none |
| ClippedGossip / CS+ [S] | H | H | none | M: per-step clip | L | none | none |
| CIoTA, JPDC 2020 [S] | H | M | M (claimed) | L | L | L | L (RPi) |
| Kloft and Laskov 2012 [V] | none | H | L | H: attacker gain bound | none | none | none |
| Bose et al. 2025 [V] | none | H | none | H: certificate | none | none | none |
| Krishnamachari 2004 [V]; fleet median 2025 [V]; WAFL, Ochiai 2023 [S] | H | L / none | none | none | H, non-adversarial | none | none |
| BR-MTRL / Toso [S]; personalized FL TSP 2025 [V] | M (server) | H | none | none | H | none | none |
| Alhelou ISCAS 2026 [V] | M (server) | M | M | none | none (drops drifted clients) | none | L |
| Atarmla 2609.23254 [S]; router repo [V] | none | L | H | H: budget accounting | none | L | none |
| WARDEN 2607.21673 [S] | none | M | H | M | none | M | none |
| Ieropoulos, IoTJ 2026 [S] | M | M | none | none | none | none | H |

Per-axis verdict on FOA's combination:
- (a) and (b): fully covered. Geometric-median consensus with a breakdown below one half is textbook (Minsker, RFA, SIU, W-MSR).
- (c) with (b) in the same system: thin. We found Alhelou (server, removes drifted clients) and SIU (static parameter). We found no decentralized detector that tracks honest shared drift while resisting Byzantine peers.
- (d): per-step bounds are covered (SIU, ClippedGossip, BALANCE, FLAME). Cumulative budgets exist in grey practice (N9) and in accounting form (Atarmla). Kloft, Bose and Wang/Jha/Chaudhuri bound attacker progress for single learners. We found no collaborative detector with a GROWING residual budget and a stated minimum time to compromise. The bound itself is simple arithmetic, so reviewers will not count it as deep theory.
- (e): the concept is covered in non-adversarial sensing (N3, N4, WAFL) and in robust personalized FL (shared and personal parts). We found no work that uses the peer-consensus split to decide how much of each device's own ADAPTATION to accept under poisoning.
- (f): poisoning that cancels adaptation is noted (Korycki). WARDEN's frozen reserve is itself a stop-style design. We found no explicit freeze analysis of stop-learning gates for adaptive detectors. However, FOA has its own stall (see O6), so this claim must be narrowed.
- (g): MCU inference and MCU federated learning exist (Ieropoulos, Gist, TinyFed, Manocchio ESP8266). We found no robust-aggregation gossip of detector updates on MCUs over ESP-NOW. This is an engineering contribution, not a scientific one.

Refutation attempt, honest result: I could not find a single work that covers (c)+(d)+(e) together under an adversary. SIU comes closest on structure. Fleet-median and event/fault work comes closest on the decomposition idea. The novelty therefore survives only as a COMBINATION and an APPLICATION. No single mechanism is new.

======================================================================
2. DEFENSIBLE NOVELTY STATEMENT
======================================================================
Say:
"We found no prior work that, for a fleet of adaptive anomaly detectors, uses a robust consensus of vulnerability-diverse peers to split each device's proposed adaptation into a fleet-shared part and a device-only residual, follows the shared part only as far as the device's own traffic agrees, and rations the residual with a cumulative, growing budget, so that a device-only poisoner needs a stated minimum number of cycles. We also found no prior work that analyses how stop-learning gates in such detectors can be driven into a freeze. Each building block is known: geometric-median aggregation (Minsker; Pillutla et al.), consensus with bounded local innovation (Chen, Kar and Moura), clipped gossip (He et al.), fleet-median referencing (Krishnamachari and Iyengar; Vervlimmeren et al.) and poisoning bounds for centroid detectors (Kloft and Laskov). Our contribution is putting them together for drift-versus-poisoning in IoT detectors, plus an ESP8266 implementation."

Do NOT claim:
1. Novel robust aggregation, consensus or Byzantine tolerance.
2. Novel bounded or budgeted updates, or the "boiling frog" defence idea (N1, N9, Atarmla, Kloft).
3. Novel decomposition into shared and local parts as a concept (N3, N4, personalized FL). Claim only its use for adaptation under poisoning.
4. Prevention of poisoning. The bound is a DELAY: about 2 to 20 minutes for the victims at M = 1.3 to 1.9. It also excludes the common channel.
5. Any Byzantine guarantee on the 3-board testbed (K = 2), or for E6b at f = 4 (outside f < K/2).
6. General freeze immunity. The boards stalled at 100% false alarms after an abrupt shared drift.
7. Hardware validation of security or drift tracking. No attack trials were run, and the drift runs failed.
8. A false-alarm advantage. With the floor, FOA+floor is 2.5% vs single+floor 0.8% on strong drift, and 24.6% vs 0.9% on device-only drift.
9. Robustness to mimicry (16.4% vs 17.1%) or to a botnet that hits most peers (monoculture 0% is by construction).
10. "On-device learning" in the neural-network sense. It is a centroid update.
11. That DriftXpert pauses updates (our "or" gate is our own construction), that RTTAD "stops", or that the TinyML survey found "no security".
12. Anything worded as "first" or "unique".

======================================================================
3. TEN STRONGEST REVIEWER OBJECTIONS AND HOW TO ANSWER OR FIX THEM
======================================================================
O1. "The guarantee is trivial: a budget of B per cycle trivially gives distance/B cycles."
Answer: agree it holds by construction. The contribution is WHICH component gets budgeted (the residual only), so honest shared drift still gets through.
Fix:
- Report time-to-track next to time-to-compromise as a function of B: a Pareto curve from E7 plus the drift runs.
- Run a greedy optimal attacker against the exact rule (as in Kloft and Laskov) to show how tight the bound is.
- State Cor 1 in minutes, and state that the common channel is excluded.

O2. "This is SIU / ClippedGossip / BALANCE applied to a centroid."
Answer: those assume a static target with shrinking tolerance, which would reject late honest drift.
Fix:
- Cite N1, N2, BALANCE and ClippedGossip.
- Add BALANCE (gamma*exp(-kappa*t/T) acceptance) and ClippedGossip as sim baselines with paired twins. A few lines each in fleet.py.
- Show that they fail on late shared drift (CESNET, E1). If they do not fail, the novelty shrinks and the paper must say so.

O3. "Common-mode attacks look like shared drift. Mirai and BASHLITE infect whole fleets."
Answer: this is the stated assumption: fewer than half of the peers share an exploit.
Fix:
- Measure vulnerability diversity: count shared CVEs across the N-BaIoT device families (Garcia et al., DSN 2011).
- Evaluate attacks that hit a majority of peers and report the failure honestly.
- Drop the monoculture 0% as evidence, since it is by construction.

O4. "The Byzantine theorem is wrong or vacuous."
- Lemma: theory.tex:60 says "more than (1-alpha)K", and line 72 asserts K-f > (1-f/K)K, which is false. Restate with "at least".
- Weiszfeld: 10 iterations give an approximate median. Bound the error or state the limit.
- Coverage: the theorem does not cover the spread channel, which is where E6/E6b found the Byzantine-assisted compromises.
- Testbed: K = 2 gives no protection. State it, or include the device's own proposal in the median so that K = 3.
- E6b: f = 4 is outside the theorem.
- Untested attack: ALIE-style small colluding shifts (Baruch et al., NeurIPS 2019). Add it.

O5. "The hardware shows nothing about security, and its drift result is a failure."
Facts from RESULTS.md:
- No attack trials. Single runs. Placeholder basis (FEAT_MEAN=0, random W) and development keys.
- Calibration aliasing confounds every earlier run. The static control gave 46 to 48% false alarms.
- Abrupt shared drift: 100% false alarms in the last 5 minutes on all nodes, with and without peers.
- The rotated-stride 1.4 to 1.7% has NO matched static control with rotated calibration. It cannot be credited to FOA adaptation rather than to good calibration.
- New observation: in continued_clean, the final centre distance / s0 equals the no-peers drift run to 4 decimals on all three nodes (4.9335, 4.5839, 3.5062). If the continuation started from that state, the centres did not move in 105 cycles, which is direct evidence of the stall. Node 0 also shows 0% "both peers" there, so the continuation ran the no-peer build on node 0 and is not a with-peers run. Check this before using it.
Fix:
- Commit the builds and raw logs.
- Run boundary-poisoner, decoy and forgery trials with twins, at least 3 repetitions each.
- Fit the basis on testbed traffic.
- Present the hardware as a feasibility and failure-mode study only.

O6. "FOA has its own freeze: it learns only from accepted core points."
Facts: after a step change, n_core < 5 everywhere, so proposals are zero, lambda decays and the peers send zeros. An attacker who can force a fleet-wide step (traffic flood, jamming, period change) can freeze FOA. This contradicts the spirit of Prop 4(ii).
Fix:
- Restrict Prop 4 to gate-induced freezes.
- Add a re-anchoring move triggered when own core is empty and the n_core field (sent but unused) shows that a majority of diverse peers are also empty. Cap it by the common budget and count it in C.
- Evaluate it against attackers who cause step changes.

O7. "The baselines are strawmen or misattributed."
Facts: the "DriftXpert style" gate inverts DriftXpert (which triggers updates). TOA is an oracle. There is no federated-learning or robust-gossip baseline.
Fix:
- Rename it "outlier-ratio pause gate (our construction)".
- Add BALANCE, ClippedGossip and an Alhelou-style drop-the-drifted (Krum) baseline.
- Correct the RTTAD and TinyML-survey wording.

O8. "The evaluation is synthetic."
Facts:
- Drift is a feature transform on N-BaIoT. The poisoner works on feature vectors.
- CESNET is aggregated research-network IP traffic with a modelled scanner, 5 seeds, one institution.
- Victims are selected on the same held-out attack traffic used for scoring.
Fix:
- Label each element as real or modelled in one table.
- Add a gradual-injection schedule parameterised by poisoned-data rate (Nguyen et al., DISS 2020).
- Justify the victim rule, or select victims on a disjoint split.

O9. "FOA trades availability for integrity, and the headline false-alarm number is an artefact."
Facts:
- Device-only drift costs 36% vs 26% (no floor) and 24.6% vs 0.9% (floor).
- Clean false alarms with the floor are 2.5% vs 0.8%.
- The 9.4% vs 43.1% compromise gap is mostly the boundary attacker (0.0% vs 75.4%). Core attacker 11.8% vs 36.8%. Mimicry is equal.
- Any drift at or below the budget speed is undetectable by design (Atarmla's blind set).
Fix:
- Rewrite the abstract and intro to lead with "safety under drift", broken down per attacker type.
- Show availability and integrity Pareto curves.
- State the blind set.

O10. "The authentication model breaks the threat model."
Facts:
- FOA_KEYS[N_NODES][32] is on every board, so one captured board can speak as all peers and f is no longer below K/2.
- Replay is possible after a peer has been silent for 60 s (PEER_RESET_MS, ino:51/228).
- Development keys are in the public repo.
Fix:
- Per-pair keys with N-1 truncated tags per frame, or muTESLA-style delayed disclosure (RFC 4082). ECDSA is too slow on ESP8266, about 248 ms per signature per Pearson et al.
- A persistent epoch counter in flash.
- Remove the keys from the repo.
- Until fixed, state that the model is an outsider attacker only.

Also expect questions on process:
- The independent code review was never run.
- FOA_Demo_Evidence.md cites a chatgpt.com link.
- The plot is named hardware_attacks.png although no attacks were run.
- Timing is inconsistent: 15, 19 and 14.4 ms in the paper vs about 25 ms measured.
- Power is 365 mW in the paper vs 382 to 391 mW measured.
- The paper says ESP32, but the boards are ESP8266.
- The deck now uses the unblurred photo by default.

======================================================================
4. VERDICT: DO THE RESULTS SUPPORT THE CLAIMS?
======================================================================
Simulation (held-out seeds 2 to 11, paired twins). Supports a NARROW claim:
- Against a boundary-hugging poisoner hidden in shared drift, FOA is far harder to compromise than single-device adaptation: 0% vs 63 to 75%. Core attacker 11.8% vs 36.8% with the floor.
- Overall poisoning under drift: 10.8% vs 39.2% (E3).
- The freeze contrast against our own KL gate holds: 100% vs 11.8%.
- Keyless forgery and replay fail (E6).

Simulation does NOT support:
- A false-alarm advantage once the floor is added.
- Robustness to mimicry.
- Robustness when Byzantine peers combine with a poisoner (40 to 60% at f = 2 to 4).
- Majority-infected fleets.
- Generality beyond one CESNET institution and 5 seeds.
- Real IoT drift: N-BaIoT drift is synthetic.
"0 violations of Cor 1" is an implementation check, not empirical evidence, because the bound holds by construction.

Hardware (3 ESP8266 boards, one run per configuration). Supports feasibility only:
- C matches Python: 480 cycles, 0 mismatches, 23,040 bit flips rejected.
- About 25 ms of compute per cycle, and it fits in memory (93% IRAM, little headroom).
- The floor holds the spread at 1.0.
- Board power is 382 to 391 mW, dominated by Wi-Fi. FOA's own energy cannot be resolved at that level.
- The 160/200/240 ms natural experiment is solid evidence of a calibration-aliasing bug.

Hardware does NOT support any security claim (no attacks were run), any fleet benefit (peers vs no peers differed by about 2 pp and both ended at 100%), or drift tracking. The drift runs show a real failure mode of the method. It should be reported as a finding and fixed (O6), not hidden.

Overall: the idea is a defensible, modestly novel combination with honest simulation support for one specific threat (a device-only poisoner exploiting shared drift). The Byzantine theory needs repair. The hardware is an implementation and failure-mode study, not validation.

Key files referenced:
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/theory.tex (lines 49, 60, 72)
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/foa_config.h (line 26)
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/esp8266_foa.ino (lines 51, 213, 227 to 228)
- origin/hardware-results-20261127:FOA_floor3/experiments/hardware/RESULTS.md
- Extracted wind-turbine PDF (scratch): /Users/rishitkamboj/.claude/projects/-Users-rishitkamboj-Collegeactual-Study-SEM5-iot-research-project-brainstorming/4d8240d3-c477-4b31-a868-b4b7306e3e48/tool-results/webfetch-1795791563790-68fd64.pdf