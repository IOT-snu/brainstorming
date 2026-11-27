# FOA multi-agent research review (27 Nov 2026)

## 1. Executive summary

- **What FOA is.** Each IoT detector keeps adapting its centroid. Peers that are vulnerability-diverse form a robust consensus (a geometric median with a significance gate and the device's own agreement, lambda) that splits each device's proposed update into a fleet-shared part and a device-only residual. The residual is limited by a cumulative budget that grows over time but never closes. This gives a minimum time before a device-only poisoner can compromise the detector (Cor 1), and the design has no stop switch an attacker can trip (Prop 4).
- **Strongest simulation result: poisoning hidden in strong shared drift (E3).** On held-out seeds 2 to 11, with paired attacker-free twins and 6,720 runs, FOA was compromised in 10.8% of runs. Single-device adaptation was compromised in 39.2%, the KL switch-off in 29.9% and the frozen reserve in 27.4%. With the coverage floor (E12) the figures are 9.4% vs 43.1%, and most of that gap is the boundary attacker (0.0% vs 75.4%).
- **What the simulations do not support.**
  - A false-alarm advantage once both methods use the floor: FOA+floor 2.5% vs single+floor 0.8%.
  - Robustness to mimicry: 16.4% vs 17.1%.
  - Device-only drift: 24.6% vs 0.9% with the floor.
  - Byzantine peers combined with a poisoner: 40 to 60% compromised at f = 2 to 4.
- **Hardware supports feasibility only.** Three ESP8266 boards were used.
  - The C core matches Python: 480 cycles, 0 mismatches, 23,040 bit flips rejected.
  - Compute is about 25 ms per cycle. Board power is 382 to 391 mW and is dominated by Wi-Fi.
  - The floor held the spread ratio at 1.0000.
  - No attack, decoy, forgery or replay trials have been run on the boards.
- **Two failure modes found on the boards on 27 Nov.**
  - **Calibration aliasing:** CAL_EVERY=10 is phase-locked to the 200 ms telemetry. This confounds every earlier hardware number. The static control alone gave about 46 to 48% FPR, while FOA+floor with a rotated stride gave 1.43 to 1.72%.
  - **Abrupt-drift starvation:** after a fleet-wide step, every core was empty, every proposal was zero, and false alarms stayed at 100% with or without peers.
- **The Byzantine theorem needs repair.**
  - The Minsker lemma is stated with "more than" where it needs "at least".
  - The proof covers the exact median, but the code runs 10 Weiszfeld iterations.
  - The spread channel is not covered.
  - The 3-board testbed has K = 2, where the theorem says nothing.
  - E6b at f = 4 lies outside f < K/2.
- **The firmware breaks the threat model.** Every board holds every node's HMAC key, so capturing one board yields all identities. A 60 s silence reset (PEER_RESET_MS) also reopens replay.
- **Prior art.** We found no prior work that combines all of: per-device adaptation, a diverse-peer consensus used only for the shared part, a growing cumulative residual budget with a time-to-compromise statement, and a freeze analysis of stop-learning gates, on MCUs. Every single ingredient has prior art. The closest works are Chen, Kar and Moura (SIU), CIoTA, BALANCE, ClippedGossip, Kloft and Laskov, and Bose et al.
- **Novelty is defensible only as a combination and an application.** Do not claim robust aggregation, budgets, the shared/local split or freeze immunity as new on their own.
- **Highest-value next steps.**
  - Theory and related-work text fixes.
  - Reservoir-sampled calibration.
  - Fair board controls with 3 repetitions.
  - A K < 3 guard.
  - Quorum-gated re-anchoring for the stall.
  - Hardware attack trials.
  - BALANCE and ClippedGossip baselines.
  - Per-pair keys with a persistent epoch.

## 2. What we implemented and showed

| Component | Evidence | Sim or hardware | Status |
|---|---|---|---|
| Centroid detector (experiments/foa/detector.py): score = \|\|x-mu\|\|/s, tau at the 99th percentile, "naive" and signature-free "auto" proposals | Unit tests: `pytest experiments/foa/tests/test_foa.py`, 16 passed | Sim | Working. Gives a zero proposal when fewer than 5 core points exist, which is the root of the stall. |
| FOA rule (experiments/foa/foa_rule.py `foa_step`): geometric median, EMA, z ramp, robust lambda, common budget, residual budget, optional floor | E1 to E12 | Sim | Working. The module docstring describes a joint budget, but the default uses separate budgets. |
| Robust primitives (robust.py): Weiszfeld (10 iterations), ball projection, Minsker constant | Unit tests | Sim | Working. The `minsker_constant` docstring repeats the lemma slip. |
| Baselines (fleet.py): static, naive, auto, clip, frozen, kl, or, toa (oracle), ciota (same model) | E1 to E12 | Sim | Working. The "or" gate is mislabelled "DriftXpert style". |
| Attackers (attacks.py): boundary, core, mimicry, multidir, aligned, decoy, pulsing, Byzantine, Sybil | E3, E5, E6, E6b | Sim | Working. Missing: ALIE, frog-boiling peers, greedy budget-saturating attacker, stall-trigger attacker. |
| Liveness under strong shared drift (E1) | FOA 9.0%, single 24.6%, gates 45 to 59%, static 78% FPR (no floor) | Sim, held-out | An artefact of the spread ratchet. With the floor: FOA 2.5% vs single 0.8%. |
| Poisoning under drift (E3) | FOA 10.8%, single 39.2%, KL 29.9%, frozen 27.4%, TOA 5.5% (oracle); boundary attacker 0% vs 63%; core 34% and mimicry 29% at p=0.4 | Sim, held-out, 6,720 runs | Supported for boundary and core attackers. Mimicry is not helped. |
| No drift (E2) | FOA 5%, single 7%, naive 36% | Sim | Supported. |
| Monoculture (E4) | Same-model consensus 0% (1 of 3 infected), 100% (2 or 3 infected); FOA diverse 0% | Sim | Holds by construction. A demonstration, not a measurement. |
| Freeze (E5) | KL switch-off 100% FPR with decoys (26% without); FOA 11.8% vs 11.8%, bit-for-bit equal | Sim | Supported against gate-induced freezes only. |
| Gossip authentication (gossip.py, E6) | Keyless forge/replay 0% (100% without HMAC); 6.4% FPR at 0% frame loss vs 6.7% at 50% | Sim | Supported for outsiders only. |
| Byzantine (E6b) | Alone: 0% up to f=4. With a poisoner: 0, 2, 40, 56, 60% at f=0..4; single device 80% | Sim, 5 victims | A real limit. Traced to the common spread channel. |
| Budget sweep (E7) | No compromise for B <= 0.005; 75% at B=0.04 | Sim | Supported. |
| Ablations (E8) | Discard residual: 54% FPR; no peers: 43%; no residual budget: 67% compromised | Sim | Supported. |
| Four-node fleet (E10) | 0% compromised, 11% FPR | Sim | Supported. |
| CESNET real drift (E11) | Compromised: FOA 0%, single 18%, naive 91%. FPR: FOA 9.1%, single 11.6%, static 5.9% | Sim: real drift, modelled attack, 5 seeds, 11 victims, one institution | Limited generality. |
| Cor 1 bound check | 0 violations in 3,630 + 120 runs, and in 1,710 runs with the floor | Sim | An implementation check only, since the bound holds by construction. |
| Coverage floor (E12) | 7,310 runs: FPR 2.5% vs 0.8%; compromised 9.4% vs 43.1%; boundary 0.0% vs 75.4%, core 11.8% vs 36.8%, mimicry 16.4% vs 17.1% | Sim, held-out | Supported, with the caveats above. |
| Theory (paper/theory.tex): Thm 1, Cor 1, Minsker lemma, Thm 2, Prop 3, Prop 4 | Proofs | Theory | Thm 2 needs repair (see section 6, O4). Prop 4(ii) needs narrowing. |
| C99 firmware core (firmware/esp8266_foa, esp32_foa) | host_test: 480 cycles, 0 mismatches, worst relative error 5.4e-4; 23,040 bit flips rejected; RFC 4231 passes | Bench | Working. Placeholder basis and development keys. |
| ESP32 footprint (paper/cost.tex) | +22 KB flash, +20 KB static RAM, 452 B state | Compile only | Stale: the boards are ESP8266. |
| ESP8266 build | Flash 280,812 / 1,048,576 B; RAM 51,248 / 80,192 B (63%); IRAM 61,031 / 65,536 B (93%) | Hardware build | Working, with little IRAM headroom. |
| Board runs (branch origin/hardware-results-20261127) | See section 3 | Hardware | Feasibility and failure-mode evidence only. |
| Laptop poisoner (firmware/laptop/poisoner.py) | None | Hardware | Exists but has never been used on the boards. |

## 3. Hardware status today

Source: branch origin/hardware-results-20261127, commit 2676673, FOA_floor3/experiments/hardware/RESULTS.md.

**Setup**
- Three ESP8266 boards (COM10, COM16, COM17), floor = 1.0.
- Each board heard both peers in about 88 to 99% of cycles.

**Runs** (one run per configuration, with separate boots and calibrations)

| Run | Result |
|---|---|
| Floor-on baseline (24.5 min) | Spread ratio 1.0000 on all nodes. FPR 25.24 to 25.27%. |
| Static control (about 36 min, old fixed stride) | FPR 47.7 to 48.2% (45.8 to 46.4% in the opening 20 min). The calibration itself was bad. |
| Rotated calibration stride (9, 9, 9, 13) | FPR 1.43 to 1.72% over the full run (1.53 to 1.70% in the opening 20 min). |
| Varied periods, no drift (160/200/240 ms) | 200 ms node 25.17%; 160 and 240 ms nodes 2.41% and 0.67%. |
| Shared abrupt drift (periods halved at 30 min) | Before/after FPR 2.8/99.9%, 26/99.9%, 0.5/99.9%. Zero core samples in 78 of 79 cycles after the change. |
| Same drift, node 0 ignores peers | 4.3% to 99.0%. Confounded, because this build also skips the receive wait. |
| Continuation (about 13 min) | 100% FPR on all boards, no recovery. |

**Findings**
- **Calibration aliasing.**
  - Samples arrive every 50 ms and calibration keeps every 10th one, i.e. one every 500 ms.
  - 500 mod 200 = 100 ms, so a 200 ms node is sampled at only 2 of its 4 phases. With 160 or 240 ms the remainder is 20 ms, so all phases are seen.
  - The host fixture agrees: the fixed stride flags 101 of 400 samples, the rotated stride 11 of 400.
  - The old "90% collapse" therefore had two causes: the spread ratchet (real; spread 0.035 in floor4) and bad calibration (about 46% FPR on its own).
- **Abrupt-drift starvation.**
  - The cause is in firmware/esp8266_foa/foa_core.c:154 (`if (n_acc == 0 || n_core < 5) return;`) and detector.py. Proposals are zero, lambda decays, and peers also send zero.
  - The judge and the technical-plan agent confirmed the stall from the logs: the final centre distances in continued_clean (4.9335, 4.5839, 3.5062 s0) match the no-peers drift run to 4 decimals.
  - In that continuation, node 0 shows 0% "both peers", so it likely ran the no-peer build. The no-peers run logs 99.32% "both peers" on nodes 1 and 2. Both points should be checked.
- **Clean centre walk.**
  - The centre moved 3.5 to 5.5 calibrated spreads (about 0.65 to 1.0 alarm radii, with tau about 5.4 to 5.6) in under 40 minutes with no attacker.
  - This is inside the budget: 0.1 + 0.005 x 291 = 1.56 radii.
- **No fair FOA-vs-static comparison yet.** The rotated-stride run has no matched static control that also used rotated calibration.
- **Cost.**
  - Proposal 21.4 to 21.6 ms (including batch classification), step 1.6 to 1.9 ms, sign about 0.6 ms, verify about 1.0 ms. Total about 25 ms.
  - Power 381.7 to 391.2 mW in every phase, read from the INA226 every 40 ms with about 35 ms averaging.
  - FOA's own energy cannot be resolved at board level. The upper bound is about 9.6 to 10 mJ per cycle, at most about 0.25% of board energy.
- **Not done.**
  - No attack, decoy, forgery or replay trials.
  - Placeholder basis (FEAT_MEAN = 0, FEAT_STD = 1, random W).
  - Development keys.
  - Single runs, so no confidence intervals.
  - The traffic is the boards' own telemetry.
  - K = 2 peers per board.
- **Reproducibility gaps on the branch.**
  - The rotated-stride, drift and no-peer builds are not committed.
  - The raw serial logs and followup_20261127_142002.txt are not committed.
  - The plot is named hardware_attacks.png although no attacks were run.
  - FOA_Demo_Evidence.md cites a chatgpt.com link as a source.
  - The branch's RESEARCH_LOG.md differs from main's; copying it over would erase the Oct/Nov history.

## 4. Prior art

Axes: (a) multi-device consensus, (b) poisoning or Byzantine robustness, (c) drift adaptation, (d) bounded or budgeted updates and time to compromise, (e) shared vs device-only split, (f) freeze resistance, (g) MCU hardware. Ratings: H, M, L, or "-" for none.

| Citation | Year | Preprint | URL | a | b | c | d | e | f | g | Closeness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Y. Chen, S. Kar, J. M. F. Moura, "Resilient Distributed Estimation: Sensor Attacks", arXiv 1709.06156 | 2018 | Yes (no journal version confirmed) | https://arxiv.org/abs/1709.06156 | H | H | - | M | M | - | - | Very high (structural skeleton) |
| Mirsky, Golomb, Elovici, "Lightweight Collaborative Anomaly Detection for the IoT using Blockchain", J. Parallel and Distributed Computing 145, 2020; Golomb, Mirsky, Elovici, "CIoTA: Collaborative IoT Anomaly Detection via Blockchain", NDSS DISS 2018 | 2020 / 2018 | No | https://arxiv.org/abs/2006.10587 ; https://arxiv.org/abs/1803.03807 | H | M | M | L | L | L | L | Very high |
| Fang, Zhang, Hairi, Khanduri, Liu, Lu, Liu, Gong, "Byzantine-Robust Decentralized Federated Learning" (BALANCE), ACM CCS 2024 | 2024 | No | https://arxiv.org/abs/2406.10416 | H | H | - | M | L | - | - | High |
| He, Karimireddy, Jaggi, "Byzantine-Robust Decentralized Learning via ClippedGossip", arXiv 2202.01545 | 2022 | Yes (venue not verified) | https://arxiv.org/abs/2202.01545 | H | H | - | M | L | - | - | High |
| Kloft, Laskov, "Security Analysis of Online Centroid Anomaly Detection", JMLR 13:3681-3724, 2012 | 2012 | No | https://jmlr.org/papers/v13/kloft12b.html | - | H | L | H | - | - | - | High (same detector) |
| Bose, Lessard, Fazel, Dvijotham, "Keeping up with dynamic attackers: Certifying robustness to adaptive online data poisoning", AISTATS 2025, PMLR 258 | 2025 | No | https://arxiv.org/abs/2502.16737 ; https://proceedings.mlr.press/v258/bose25b.html | - | H | - | H | - | - | - | High |
| Ieropoulos, Anthi, Spyridopoulos, Burnap, Carnelli, Khan, "Federated Detection at the Edge: Collaborative Anomaly Detection for Resource-Limited IoT", IEEE Internet of Things Journal 13(11):24205-24218, 2026 | 2026 | No | https://orca.cardiff.ac.uk/179135/ | M | M | - | - | - | - | H | Medium-high (MCU) |
| Ochiai, Nishihata, Tomiyama, Sun, Esaki, "Detection of Global Anomalies on Distributed IoT Edges with Device-to-Device Communication", ACM MobiHoc AIoT workshop 2023 | 2023 | No (workshop) | https://arxiv.org/abs/2407.11308 | H | L | - | L | M | - | - | Medium-high (concept) |
| Alhelou, Singh, Wang, "Adaptive Federated Learning Defense Against Byzantine Attacks and Concept Drift in IIoT", IEEE ISCAS 2026 (in press) | 2026 | No | https://repository.essex.ac.uk/42630/ | M | M | M | - | - | - | L | Medium (only drift plus Byzantine work found) |
| Balachandran, "Self-Poisoning in Adaptive Out-of-Distribution Detection: A Sharp-Threshold Theory and Certified Label-Free Calibration" (WARDEN), arXiv 2607.21673 | 2026 | Yes | https://arxiv.org/abs/2607.21673 | - | H | H | M | - | M | - | Medium |
| Atarmla, "The Price of Self-Calibration: Exact Evidence Budgets and Manufactured Blind Sets in Adaptive Monitoring", arXiv 2609.23254 | 2026 | Yes | https://arxiv.org/abs/2609.23254 | - | L | H | H | - | L | - | Medium |
| Le, Moothedath, "Byzantine Resilient Federated Multi-Task Representation Learning" (BR-MTRL), arXiv 2503.19209 | 2025 | Yes | https://arxiv.org/abs/2503.19209 | M | H | - | - | H | - | - | Medium |
| Toso, Anderson, Pinot, Gupta, "Byzantine-Robust Federated Representation Learning", arXiv 2609.36660 | 2026 | Yes | https://arxiv.org/abs/2609.36660 | M | H | - | - | H | - | - | Medium |
| B. Krishnamachari, S. Iyengar, "Distributed Bayesian Algorithms for Fault-Tolerant Event Region Detection in Wireless Sensor Networks", IEEE Trans. Computers 53(3), 2004 | 2004 | No | https://ceng.usc.edu/~bkrishna/research/papers/KrishnamachariIyengarBayesianEventDetectionTC03.pdf | H | L | - | - | H | - | - | Medium (non-adversarial ancestor of the split) |
| I. Vervlimmeren, X. Chesterman, T. Verstraeten, A. Nowe, J. Helsen, "Scalable SCADA-driven Failure Prediction for Offshore Wind Turbines Using Autoencoder-Based NBM and Fleet-Median Filtering", Wind Energy Science Discussions, 2025 | 2025 | Yes (in discussion) | https://wes.copernicus.org/preprints/wes-2025-49/ | H | - | - | - | H | - | - | Medium (fleet-median referencing) |
| H. J. LeBlanc, H. Zhang, X. Koutsoukos, S. Sundaram, "Resilient Asymptotic Consensus in Robust Networks", IEEE JSAC 31(4), 2013 | 2013 | No | https://cs.vuse.vanderbilt.edu/koutsoxd/www/Publications/resilientConsensusJSAC2013.pdf | H | H | - | - | - | - | - | Medium (classical root) |
| Gaucher, Dieuleveut, Hendrikx, "Unified Breakdown Analysis for Byzantine Robust Gossip", ICML 2025, PMLR 267 | 2025 | No | https://arxiv.org/abs/2410.10418 | H | H | - | L | - | - | - | Medium |
| Karimireddy, He, Jaggi, "Learning from History for Byzantine Robust Optimization", ICML 2021, PMLR 139:5311-5319 | 2021 | No | https://proceedings.mlr.press/v139/karimireddy21a.html | M | H | - | M | - | - | - | Medium (motivates the cumulative budget) |
| Chan-Tin, Feldman, Hopper, Kim, "The Frog-Boiling Attack: Limitations of Anomaly Detection for Secure Network Coordinate Systems", SecureComm 2009 | 2009 | No | https://www-users.cs.umn.edu/~hopper/frogBoiling.pdf | H | H (attack) | - | - | - | - | - | Medium (problem statement) |
| Baruch, Baruch, Goldberg, "A Little Is Enough: Circumventing Defenses For Distributed Learning", NeurIPS 2019 | 2019 | No | https://arxiv.org/abs/1902.06156 | M | H (attack) | - | - | - | - | - | Medium (untested attack on FOA) |
| Nguyen, Rieger, Miettinen, Sadeghi, "Poisoning Attacks on Federated Learning-based IoT Intrusion Detection System", NDSS DISS 2020 | 2020 | No (workshop) | https://www.ndss-symposium.org/wp-content/uploads/2020/04/diss2020-23003-paper.pdf | M | H (attack) | L | - | - | - | - | Medium (same threat model) |
| Nguyen, Marchal, Miettinen, Fereidooni, Asokan, Sadeghi, "DIoT: A Federated Self-learning Anomaly Detection System for IoT", IEEE ICDCS 2019 | 2019 | No | https://arxiv.org/abs/1804.07474 | M | L | L | - | L | - | - | Low-medium |
| Meidan, Avraham, Libhaber, Shabtai, "CADeSH: Collaborative Anomaly Detection for Smart Homes", IEEE Internet of Things Journal 2022 | 2022 | No | https://arxiv.org/abs/2303.01021 | M | L | - | - | L | - | - | Low-medium |
| Pillutla, Kakade, Harchaoui, "Robust Aggregation for Federated Learning" (RFA), IEEE Trans. Signal Processing 70:1142-1154, 2022 | 2022 | No | https://arxiv.org/abs/1912.13445 | M | H | - | - | - | - | - | Low-medium (same primitive) |
| X. Cao, M. Fang, J. Liu, N. Z. Gong, FLTrust, NDSS 2021 | 2021 | No | https://arxiv.org/abs/2012.13995 | M | H | - | - | - | - | - | Low-medium |
| Y. Wang, S. Jha, K. Chaudhuri, "An Investigation of Data Poisoning Defenses for Online Learning", arXiv 1905.12121 | 2019/2020 | Yes | https://arxiv.org/abs/1905.12121 | - | H | - | M | - | - | - | Low-medium |
| Korycki, Krawczyk, "Adversarial concept drift detection under poisoning attacks for robust data stream mining", Machine Learning 112:4013-4048, 2023 | 2023 | No | https://link.springer.com/article/10.1007/s10994-022-06177-w | - | H | H | - | - | M | - | Low-medium |
| Rubinstein et al., "ANTIDOTE: Understanding and Defending against Poisoning of Anomaly Detectors", ACM IMC 2009 | 2009 | No | https://ptolemy.berkeley.edu/projects/truststc/pubs/725/IMC.2009.pdf | - | H | L | L | - | - | - | Low-medium |
| Ito, Tsukada, Matsutani, "An On-Device Federated Learning Approach for Cooperative Model Update between Edge Devices", IEEE Access 2021 | 2021 | No | https://arxiv.org/abs/2002.12301 | H | - | M | - | - | - | L | Medium (Keio line) |
| Ino, Yoshida, Matsutani, Fujino, "Data Poisoning Attack against Neural Network-Based On-Device Learning Anomaly Detector by Physical Attacks on Sensors", Sensors 24(19):6416, 2024 | 2024 | No | https://pmc.ncbi.nlm.nih.gov/articles/PMC11479347/ | - | H (attack) | M | - | - | - | H | Medium (Keio line) |
| Asadi, Bengu, Wulfert, Wohrle, Kellerer, "Gist: Optimizing Segmentation for Decentralized Federated Learning on Tiny Devices", FLEdge-AI '25 | 2025 | No (workshop) | https://asadi.io/files/papers/NavidrezaAsadi_MobiCom2025-FLEdgeAI_Gist.pdf | H | - | - | - | L | - | H | Low-medium (MCU gossip precedent) |
| Zewail, Ehab, Ali, Mahrous, Awad, Mokhtar, "On-Edge Acoustic Continual Anomaly Detection: A Cross-Platform Comparative Study", JAC-ECC 2026 | 2026 | No (accepted) | https://arxiv.org/abs/2611.15465 | - | - | H | - | - | - | H | Medium (same detector family) |
| Kargar, Zorbas, Gaffney, O'Flynn, Tedesco, "Concept Drift Mitigation on Resource-Constrained IoT Devices via Self-Learning", IEEE SAS 2025 | 2025 | No | https://research.ucc.ie/en/publications/concept-drift-mitigation-on-resource-constrained-iot-devices-via-/ | - | - | H | - | - | - | H | Medium |
| Manocchio, Layeghy, Portmann, "Network Intrusion Detection System in a Light Bulb", arXiv 2210.03254 | 2022 | Yes | https://arxiv.org/abs/2210.03254 | - | - | - | - | - | - | H | Low-medium (ESP8266 IDS) |
| Alsalem, "Securing AI-Driven Systems for Environmental Sustainability in IoT Applications: A Lightweight Message-Authentication Scheme Against Telemetry Poisoning", Sensors 26(19):6276, 2026 | 2026 | No | https://pmc.ncbi.nlm.nih.gov/articles/PMC13667637 | - | M | - | - | - | - | H | Medium (authentication axis) |
| Cong, He, Shen, Zhang, "Test-Time Poisoning Attacks Against Test-Time Adaptation Models", IEEE S&P 2024 | 2024 | No | https://arxiv.org/abs/2308.08505 | - | H | M | - | - | - | - | Low |
| Huang, Qiao, Zhang, Ye, Shang, Fu, "When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection" (RTTAD), arXiv 2605.10242 | 2026 | Yes | https://arxiv.org/abs/2605.10242 | - | L | H | L | - | - | - | Low |
| Zha, Kang, Liu, Shen, Zhang, "Navigating the Latent Manifold: Proactive Concept Drift Adaptation for Resilient NIDS" (DriftXpert), arXiv 2609.08623 | 2026 | Yes | https://arxiv.org/abs/2609.08623 | - | - | H | - | - | - | L | Low |
| Hinder, Vaquet, Hammer, "Adversarial Attacks for Drift Detection", ESANN 2025 | 2025 | arXiv version | https://arxiv.org/abs/2411.16591 | - | - | H | - | - | L | - | Low |
| Hu, Duan, "Theory of Continual Learning Against Data Poisoning Attacks", arXiv 2606.29841 | 2026 | Yes | https://arxiv.org/abs/2606.29841 | - | H | M | M | - | - | - | Low |
| M. Kravchik, A. Shabtai, "Can't Boil This Frog: Robustness of Online-Trained Autoencoder-Based Anomaly Detectors to Adversarial Poisoning Attacks", arXiv 2002.02741 | 2020 | Yes | https://arxiv.org/abs/2002.02741 | - | H | M | - | - | - | - | Low (counter-evidence on threat strength) |
| Tripathi, Sharma, Mishra, Maiti, "SpectralKrum: A Spectral-Geometric Defense Against Byzantine Attacks in Federated Learning", arXiv 2512.11760 | 2025 | Yes | https://arxiv.org/abs/2512.11760 | M | H | L | - | M | - | - | Low |
| Nguyen et al., "FLAME: Taming Backdoors in Federated Learning", USENIX Security 2022 | 2022 | No | https://www.usenix.org/conference/usenixsecurity22/presentation/nguyen | M | H | - | M | - | - | - | Low |
| Rey, Sanchez Sanchez, Huertas Celdran, Bovet, Jaggi, "Federated Learning for Malware Detection in IoT Devices", Computer Networks 2022 | 2022 | No | https://arxiv.org/abs/2104.09994 | M | M | - | - | - | - | - | Low (same dataset, N-BaIoT) |
| Kailkhura, Brahma, Varshney, "Consensus based Detection in the Presence of Data Falsification Attacks", arXiv 1504.03413 | 2015/2016 | Venue to verify | https://arxiv.org/abs/1504.03413 | H | H | L | - | - | - | - | Low |
| Fung, Zhang, Aib, Boutaba, "Dirichlet-Based Trust Management for Effective Collaborative Intrusion Detection Networks", IEEE TNSM 2011 | 2011 | No | https://personal.ntu.edu.sg/zhangj/paper/tnsm10.pdf | H | M | - | - | - | - | - | Low |
| GitHub gotsevrossen/ML-router-anomaly-detection (grey literature) | about 2026 | Not a paper | https://github.com/gotsevrossen/ML-router-anomaly-detection | - | L | H | H | - | - | - | Low (shows cumulative budgets are folk practice) |

Supporting references (not detectors):
- Garcia, Bessani, Gashi, Neves, Obelheiro, "OS diversity for intrusion tolerance: Myth or reality?", IEEE/IFIP DSN 2011, https://openaccess.city.ac.uk/id/eprint/526/ . Evidence for the diversity assumption.
- Minsker, "Geometric median and robust estimation in Banach spaces", Bernoulli 21(4):2308-2335, 2015, https://arxiv.org/abs/1308.1334
- Perrig, Song, Canetti, Tygar, Briscoe, RFC 4082 (TESLA), 2005, https://www.rfc-editor.org/rfc/rfc4082
- Perrig, Szewczyk, Wen, Culler, Tygar, "SPINS: Security Protocols for Sensor Networks", Wireless Networks 8, 2002, https://www.doi.org/10.1023/A:1016598314198
- Pearson, Luo, Zhang, Dey, Ling, Bassiouni, Fu, "On Misconception of Hardware and Cost in IoT Security and Privacy", IEEE ICC 2019, https://par.nsf.gov/servlets/purl/10149710 . HMAC-SHA256 about 182 us and ECC signing about 248 ms on the ESP8266; recheck Table II before quoting.
- Espressif ESP-NOW docs, https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/network/esp_now.html . Broadcast and multicast encryption are not supported; the v1 payload is 250 B.
- Nozomi Networks, "ESP-NOW Protocol Analysis and Vulnerability Research" (vendor white paper), https://cdn.prod.website-files.com/645a4534705010e2cb244f50/67e3ab1eec0b2be8f630f641_Nozomi-Networks-WP-ESP-NOW.pdf
- Meidan et al., "N-BaIoT", IEEE Pervasive Computing 17(3), 2018, https://arxiv.org/abs/1805.03409
- Koumar, Hynek, Cejka, Siska, "CESNET-TimeSeries24", Scientific Data 12:338, 2025, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11865510/

### The closest works in detail

1. **Chen, Kar, Moura (SIU), arXiv 1709.06156**
   - The update is x_n(t+1) = x_n - beta_t * sum over neighbours (x_n - x_l) + alpha_t * K_n(t) * (y_n - x_n). The local innovation is saturated to norm gamma_t, and estimates converge whatever the topology as long as fewer than half the sensors are attacked.
   - This is the skeleton of FOA: peer consensus plus a norm-bounded local term, with breakdown below one half.
   - Differences: the target is static (drift is listed as future work), and gamma_t shrinks while FOA's budget grows. It is estimation, not anomaly detection, and has no freeze analysis or hardware.
   - It must be cited. It is the most dangerous citation for novelty.

2. **CIoTA / Mirsky, Golomb, Elovici, JPDC 2020**
   - Same-type devices train Markov models and merge them by model attestation plus abnormality filtration (pa% supermajority), with blockchain bookkeeping. It was run on 48 Raspberry Pis.
   - It has a larger deployment, a supermajority rule, a signed bootstrap and a count of how many models an attacker must poison.
   - It erases honest device-only drift: anything the majority has not seen is filtered out.
   - It has no budget, no time-to-compromise, no freeze analysis and no MCU implementation.
   - It needs a large homogeneous population, which works against FOA's deliberately diverse setting.

3. **BALANCE, Fang et al., CCS 2024**
   - A node accepts neighbour j if \|\|w_i - w_j\|\| <= gamma * exp(-kappa * t/T) * \|\|w_i\|\|, then mixes. Convergence is proven under poisoning.
   - Its radius shrinks over time, so a real shift late in deployment is rejected. This is effectively a self-inflicted freeze.
   - It has no split and no growing budget.
   - It is the most important baseline to add, and ClippedGossip should be added with it.

4. **Kloft and Laskov, JMLR 2012, and Bose et al., AISTATS 2025**
   - **Kloft and Laskov:** the same centroid detector, with attacker-gain bounds and a greedy optimal attack tested on real traces.
   - **Bose et al.:** a computable certificate against an adaptive online poisoner, used to tune eta and the defence.
   - Both assume a stationary normal distribution and a single learner.
   - FOA adds non-stationarity, peers, the split, a finite-horizon time-to-compromise and the freeze/liveness side. Its guarantee holds by construction rather than as a tight worst-case bound.

5. **Ieropoulos et al., IEEE IoTJ 2026**
   - ESP32 boards run a centrally trained autoencoder, multicast their predictions, isolate inconsistent nodes with a trust threshold, and check model consistency with MD5.
   - It has live attacks on hardware.
   - It has no on-device adaptation, no keyed authentication, no poisoning theory and no freeze analysis.
   - Its benchmark numbers were seen only in search snippets. Do not quote them.

## 5. Novelty verdict

**Defensible statement** (from the adversarial judge):

"We found no prior work that, for a fleet of adaptive anomaly detectors, uses a robust consensus of vulnerability-diverse peers to split each device's proposed adaptation into a fleet-shared part and a device-only residual, follows the shared part only as far as the device's own traffic agrees, and rations the residual with a cumulative, growing budget, so that a device-only poisoner needs a stated minimum number of cycles. We also found no prior work that analyses how stop-learning gates in such detectors can be driven into a freeze. Each building block is known: geometric-median aggregation (Minsker; Pillutla et al.), consensus with bounded local innovation (Chen, Kar and Moura), clipped gossip (He et al.), fleet-median referencing (Krishnamachari and Iyengar; Vervlimmeren et al.) and poisoning bounds for centroid detectors (Kloft and Laskov). Our contribution is putting them together for drift-versus-poisoning in IoT detectors, plus an ESP8266 implementation."

The marks scheme explicitly counts "a new combination of techniques" as novelty, so this framing fits the rubric.

**What not to claim**
1. Novel robust aggregation, consensus or Byzantine tolerance.
2. Novel bounded or budgeted updates, or the boiling-frog defence idea (SIU, the router repo, Atarmla, Kloft).
3. The shared/local decomposition as a new concept. Claim only its use for adaptation under poisoning.
4. Prevention of poisoning. The bound is a delay of minutes and excludes the common channel.
5. Any Byzantine guarantee on the 3-board testbed (K = 2), or for E6b at f = 4.
6. General freeze immunity. The boards stalled at 100% after an abrupt shared drift.
7. Hardware validation of security or drift tracking.
8. A false-alarm advantage once the floor is used.
9. Robustness to mimicry, or to a botnet that hits most peers. The monoculture 0% holds by construction.
10. "On-device learning" in the neural-network sense. FOA updates a centroid.
11. That DriftXpert pauses updates, that RTTAD "stops", or that the TinyML survey found "no security".
12. Any wording such as "unique" or a priority claim.

## 6. Reviewer objections and answers

**O1. "The guarantee is trivial: B per cycle gives distance/B cycles."**
- Answer: agreed, it holds by construction. The contribution is which component gets budgeted (only the residual), so honest shared drift still passes.
- Fix:
  - Report time-to-track next to time-to-compromise as a Pareto curve over B.
  - Run a greedy budget-saturating attacker to test how tight the bound is.
  - State Cor 1 in minutes and note that the common channel is excluded.

**O2. "This is SIU, ClippedGossip or BALANCE applied to a centroid."**
- Answer: those methods assume a static target with a shrinking tolerance, so they would reject late honest drift.
- Fix:
  - Cite SIU, W-MSR, BALANCE and ClippedGossip.
  - Add BALANCE and ClippedGossip as simulation baselines with paired twins.
  - Test on late shared drift (E1, E11). If they do not fail, say the novelty shrinks.

**O3. "Common-mode attacks look like shared drift."**
- Answer: this is the stated assumption that fewer than half of the peers share an exploit.
- Fix:
  - Measure shared CVEs across the N-BaIoT device families (Garcia et al.).
  - Evaluate majority-infected fleets and report the failure.
  - Drop monoculture 0% as evidence.

**O4. "The Byzantine theorem is wrong or vacuous."**
- Fix:
  - Restate the lemma as "at least (1-alpha)K" (theory.tex:60, 72; robust.py).
  - State that the theorem covers the exact median only, or bound the Weiszfeld error.
  - Cover the spread channel with a 1-D median lemma, or state that it is excluded.
  - State K = 2 on the testbed.
  - Label E6b at f = 4 as outside the theorem.
  - Add the ALIE attack (Baruch et al.).

**O5. "The hardware shows nothing about security and its drift result is a failure."**
- Facts:
  - No attack trials, single runs, a placeholder basis.
  - Aliasing confounds all earlier runs.
  - Both drift runs ended at 100% FPR.
  - The rotated-stride 1.4 to 1.7% has no matched static control.
- Fix:
  - Commit the builds and logs.
  - Run attack trials with twins and 3 repetitions.
  - Fit the basis on testbed traffic.
  - Present the hardware as a feasibility and failure-mode study.

**O6. "FOA has its own freeze."**
- Facts: when n_core < 5 everywhere, all proposals are zero. An attacker who forces a fleet-wide step can freeze FOA.
- Fix:
  - Restrict Prop 4 to gate-induced freezes.
  - Add quorum-gated re-anchoring with its own budget (section 7, A1).
  - Evaluate it against attackers who cause step changes.

**O7. "The baselines are strawmen or misattributed."**
- Fix:
  - Rename the "or" gate "outlier-ratio pause gate (our construction)".
  - Add BALANCE, ClippedGossip and an Alhelou-style drop-the-drifted (Krum) baseline.
  - Correct the RTTAD and TinyML-survey wording.

**O8. "The evaluation is synthetic."**
- Fix:
  - One table labelling each element as real or modelled.
  - A gradual-injection schedule swept by poisoned-data rate (Nguyen et al. 2020).
  - Justify the victim rule, or select victims on a disjoint split.

**O9. "FOA trades availability for integrity, and the headline FPR is an artefact."**
- Facts:
  - Device-only drift: 36% vs 26% without the floor, 24.6% vs 0.9% with it.
  - Clean FPR with the floor: 2.5% vs 0.8%.
  - The compromise gap is mostly the boundary attacker.
  - Drift at or below the budget speed is undetectable by design (Atarmla's blind set).
- Fix:
  - Lead with safety under drift, broken down per attacker type.
  - Show Pareto curves.
  - State the blind set.

**O10. "The authentication model breaks the threat model."**
- Facts:
  - FOA_KEYS[N_NODES][32] is on every board.
  - Replay is possible after 60 s of silence.
  - Development keys are public.
- Fix:
  - Per-pair keys with N-1 truncated tags, or muTESLA/TESLA.
  - A persistent epoch counter.
  - Remove the keys from the repo.
  - Until then, state that the model covers outsider attackers only.

**Process questions to expect**
- The independent code review planned for 24 Oct never ran.
- FOA_Demo_Evidence.md cites a chatgpt.com link.
- hardware_attacks.png is misnamed.
- The timing and power numbers are inconsistent.
- The paper says ESP32 but the boards are ESP8266.
- The deck's default photo is unblurred.

## 7. Technical improvement plan (ranked by impact per effort)

| Rank | Item | Effort (h) | Impact | Risk |
|---|---|---|---|---|
| 1 | Calibration by reservoir sampling (Vitter Algorithm R), +/-10% jitter, held-out self-check; fit the real basis | 3 | Very high | Low |
| 2 | Fair board controls: static / single / FOA with fixed calibration, randomized ABC blocks, 3 repetitions, no-peer build that keeps the receive wait | 4, plus about 12 board | Very high | Low |
| 3 | K < 3 guard: auto-switch to common_dir = "own", or add 2 boards (K = 4 tolerates f = 1) | 1 to 3 | High | Low |
| 4 | Abrupt-drift stall fix: quorum-gated re-anchoring with its own budget | 12 to 16 | Very high | Medium |
| 5 | Hardware attack trials: boundary, decoy, flood probe; forge/replay/bit flips from a 4th ESP8266 (expect the 61 s replay to succeed today) | 8, plus about 16 board | Very high | Medium |
| 6 | Byzantine fix for the common spread channel: robust lam_s, asymmetric growth budget, 1-D median lemma, tighter Bc | 6 to 10 | High | Medium |
| 7 | Adaptive attacker suite: budget-saturating greedy, ALIE peers, frog-boiling peers, stall-trigger, white-box vs grey-box, PDR-swept gradual injection | 10 to 14, plus compute | High | Low |
| 8 | Key management: per-pair tags (108 B frame at N = 3), persistent epoch, exclude peers with n_core < 5 | 6 to 8 | Medium-high | Low |
| 9 | BALANCE and ClippedGossip baselines; a true DriftXpert-style trigger | 5 to 7 | Medium-high | Low |
| 10 | Held-out seeds 2 to 31, bootstrap CIs, time-to-track metric | 4, plus compute | Medium | Low |
| 11 | Gradual drift on the boards (200 to 100 ms over 60 and 180 min; shared and device-only) | 2, plus 8 board | Medium | Low |
| 12 | Device-only drift cost: budget-saturation event, per-device B, operator-signed re-baseline | 4 to 10 | Medium | Medium |
| 13 | Proposal timing: compare squared distances (removes 150 sqrtf calls in software float), optional fixed point | 3 to 6 | Medium | Low |
| 14 | Energy per cycle: Wi-Fi-off differential microbenchmark plus GPIO phase markers with the INA226 at 140 us conversion | 5 to 7 | Medium | Low |
| 15 | IRAM headroom: measure with nm; MMU 16 KB cache + 48 KB IRAM option if needed | 1 to 2 | Low-medium | Low |
| 16 | Peer trust score, honey vectors, config digest in the frame | 3 to 6 each | Low-medium | Medium |

Theory text fixes (about 3 h) go alongside rank 1: Minsker "at least", the Weiszfeld note, the K = 2 note, Cor 1 in minutes, and narrowing Prop 4.

**A1 design (rank 4)**

How it works:
- **Stall flag.** A device sets the flag if n_core < 5 for S = 6 consecutive cycles. A CUSUM on the alarm fraction is an alternative. The flag is carried in bit 15 of the n_core field, which sits inside the HMAC-covered body, so the frame stays 92 bytes.
- **Quorum.** Stall mode needs the device itself to be stalled and at least ceil((K+1)/2) verified peers to be stalled in the same cycle.
- **Direction.** g = eta * (coordinate-wise median of the whole batch - mu), with alarmed points included.
- **Peer role.** Peers only scale the move, through lambda_q clipped to [0,1]. They cannot steer it.
- **Budget.** A separate accumulator A with per-cycle cap b_q * rho and \|\|A\|\| <= (B0a + Ba * n_q(t)) rho, where n_q(t) counts quorum-stall cycles only.

Effect on the proofs:
- Thm 1 becomes mu = mu0 + C + R + A.
- t* is unchanged unless more than half the fleet is stalled.
- Recovery takes about S + Delta/b_q cycles (about 4 to 7 minutes for Delta = 1 to 2).

Limit to state: an attacker who floods more than half the fleet can drag every device at b_q * rho per cycle, up to La. This is the fleet-level form of Prop 3 and of WARDEN's two-world theorem.

Tests:
- A property test.
- The E5 bit-for-bit test must still pass.
- E13: shared steps of 1, 2 and 4 alarm radii.
- E13b: decoy floods on m of N devices.
- A hardware rerun, where success means FPR under 5% within 10 minutes.

**Other notes**
- The common budget (0.75 + 0.06 t) rho reaches 18 rho after 290 cycles. It constrains nothing on hardware timescales, so sweep Bc in {0.005, 0.01, 0.02, 0.06} on dev seeds.
- Device-only drift cost cannot be removed from traffic alone (Prop 3) without a trusted side channel such as an operator-signed re-baseline.
- Do not add an adaptive B_t without a hard B_max.

## 8. Marks and viva plan

**Marks scheme** (from "Research Based Group Project Ideas.pdf"; the project is 30% of the course grade)
- Survey, presentations and report: 10
- Implementation and results: 5
- Novelty: 5 ("a new combination of techniques" counts)
- Faculty assessment: 10

**Required items that are missing** (all cheap to add)
- An explicit research question and hypothesis.
- A top-level README.md.
- A related-work comparison table.

**Research question and hypothesis**
- **RQ:** "Can an on-device IoT detector keep adapting to drift while bounding how fast a poisoner can hide, without a stop rule an attacker can trigger?"
- **H:** "Following only the peer-backed part of an update, and budgeting the rest, lowers compromise under drift compared with single-device and gated adaptation, at bounded cost on an ESP8266."

**Story order**
1. The dilemma: get poisoned, get frozen, or drown in false alarms.
2. The insight: neighbours are a second witness.
3. The mechanism.
4. The guarantee, stated as a delay.
5. Simulation evidence, then the hardware lessons.
6. The self-correction: the FPR advantage was an artefact, and security under drift is what survives.

**Lead results, in order**
1. E3, broken down by attacker type.
2. E5 freeze.
3. E11 CESNET, with caveats.
4. E4, presented as why diversity matters.
5. The Cor 1 check.
6. E8 ablations.
7. An honest-limits slide: E6b at 56%, device-only drift, mimicry.

**Hardware framing.** "Hardware did not validate our attack results. It found two failure modes simulation missed, it confirmed the fix for one, and it isolated a calibration bug with a control run. Attack results are from simulation."

**Slides to change**
- **Slide 5 (theory):** add t* in minutes and a line saying the Byzantine bound does not apply at K = 2.
- **Slide 6:** replace with the positioning table (about 8 rows).
- **Slide 8:** add the per-attacker breakdown and "mimicry not helped".
- **Slide 9:** rename the "or" gate.
- **Slide 11:** revert to the blurred demo/testbed_photo.jpg.
- **Slide 12:** about 25 ms, 382 to 391 mW, the ESP8266 build figures, "learning energy not resolvable".
- **Slide 15:** "spread ratio held at 1.0000 on the boards".
- **Slide 16:** add starvation, the shared key table, K = 2, single runs, the placeholder basis.
- **Slide 18:** fix the wording or move it to backup.

**Slides to add**
- Hardware controls: a bar chart of static 46% / fixed stride 25% / rotated 1.6%, with the 160/200/240 ms inset.
- What broke: abrupt shared drift.
- RQ and hypothesis.

**Slides to merge or cut**
- Merge slides 13 and 14, re-attributing the collapse to ratchet plus aliasing.
- Move the formula-heavy material and E6b/E7/E10 details to backups.

**Viva guide (demo/build_viva_prep.py) changes**
- Line 108: about 385 mW.
- Line 109: "about 10 mJ upper-bound estimate".
- Line 111: "no attack trials yet; time went to calibration controls".
- Line 123: "floor held at 1.0 on the boards".
- Add Q4, Q6, Q7, Q8, Q9, Q11, Q14 and Q20.

**Examiner questions most likely to bite, with short answers**
- **Q4, does the Byzantine theorem apply to the boards?** No. K = 2.
- **Q6, time to compromise in real time?** About 2 to 15 or 20 minutes, a delay rather than immunity. Reconcile the cycle time (see section 9).
- **Q8, what caused the 90% false alarms?** The ratchet plus aliasing.
- **Q9, did FOA fail on abrupt drift?** Yes, by starvation. The fix is proposed, not evaluated.
- **Q11, the shared key table?** A real limit. The fix is per-pair keys or TESLA.
- **Q14, is the gate DriftXpert?** No, it is our own construction.
- **Q18, does FOA reduce false alarms?** Not once the floor is used.
- **Q20, has ALIE been tested?** No. It is the next Byzantine experiment.

**48-hour priority list**

*Hours 0 to 6 (correctness):*
1. Theory text: the lemma wording, exact median, spread channel, K = 2, t* in minutes, Prop 4(ii).
2. Related work:
   - RTTAD, DriftXpert and TinyML wording.
   - Korycki year 2023.
   - Add Nguyen 2020, DIoT, BALANCE, ClippedGossip, Karimireddy 2021, frog-boiling, ALIE, Bose 2025, RFA, Ieropoulos 2026, Alhelou 2026, Ochiai, TESLA, Garcia DSN 2011 and SIU.
   - Add the positioning table.
3. Numeric consistency: about 25 ms, 382 to 391 mW, 23,040 bit flips, ESP8266 in the keywords, ESP32 footprint labelled compile-only.
4. Abstract and intro: lead with security under drift; add the RQ and hypothesis.
5. Revert the deck photo to the blurred file.

*Hours 6 to 12 (evidence hygiene):*

6. Commit the rotated-stride, drift and no-peer builds, the raw 27 Nov logs and the follow-up file.
7. Rename hardware_attacks.png and remove the chatgpt.com link.
8. Merge the branch RESEARCH_LOG.md into main's log rather than overwriting it.
9. Rewrite paper/hardware.tex.
10. Add a top-level README.md: setup, pytest, make_numbers.py, building the deck, flashing.

*Hours 12 to 30 (only if the boards are free):*

11. A gradual shared drift run on the rotated-stride build, with a no-peers twin that keeps the receive wait.
12. Two more rotated-stride clean baselines, giving 3 runs.
13. Stretch: one boundary-poisoner run with an attacker-free twin, only if a rehearsal works.

Do not change the FOA rule before the viva.

*Hours 30 to 40:*

14. 95% Wilson intervals for the E3, E5, E11 and E12 headlines.
15. Optionally, a BALANCE baseline in simulation.

*Hours 40 to 48:*

16. Regenerate numbers.tex, the paper, G04_FOA_Final.pptx and G04_Viva_Prep.pdf. Grep for "15 ms", "365 mW", "not yet run on the boards", "DriftXpert-style" and "no security mechanism".
17. Assign answer blocks and do two timed rehearsals with a mock examiner.

## 9. Inconsistencies to fix in paper, slides and code

**Theory**
- The Minsker lemma says "more than (1-alpha)K" (paper/theory.tex:60). The Thm 2 proof asserts K-f > (1-f/K)K (line 72), which is false. Use "at least". The same wording is in the robust.py `minsker_constant` docstring.
- Thm 2 covers the exact median, but the code runs 10 Weiszfeld iterations. It omits the spread channel, it is vacuous at K = 2, and E6b at f = 4 lies outside it.
- Prop 4(ii) ("no input stops FOA from learning") is contradicted by the hardware stall.

**Related work**
- RTTAD is described as stopping. It adapts on both pseudo-normal and pseudo-anomalous samples.
- The "DriftXpert style" baseline inverts DriftXpert, which triggers updates rather than pausing them.
- The TinyML survey is said to find "no security mechanism". The survey does not cover security.
- research/references.json marks the TinyML survey as read in full text, which overstates what was read.
- Korycki and Krawczyk is 2023, not 2022 (bib.tex).

**Numbers**
- Compute per cycle: abstract 15 ms; hardware.tex 19 ms; the table sums to 14.4 ms; measured about 25 ms.
- Board power: 365 mW in the paper vs 381.7 to 391.2 mW measured.
- Energy per cycle: the viva guide says 7 mJ; the upper-bound estimate is about 10 mJ.
- Tamper test: the cost table says "0 of 23,104" and the text says 23,040.
- Cycle time: the audit uses 7.8 to 10 s (t* about 2 to 20 minutes) and the marks plan uses 7.5 s (291 cycles in 36.5 minutes, t* about 2 to 15 minutes). Pick one source.

**Hardware text**
- The keywords and contributions say ESP32, but the boards are ESP8266. The footprint is ESP32 compile-only.
- hardware.tex and the slides say the floor has not been run on the boards. It has, and the spread held at 1.0.
- The paper attributes the 90% FPR to the ratchet alone. Calibration aliasing contributed about 46%.

**Framing**
- The abstract and intro lead with 9.0% vs 24.6% FPR, which E12 shows is an artefact.

**Code**
- The foa_rule.py docstring describes a joint budget, but the default uses separate budgets.
- n_core is transmitted but unused, so empty peers vote with a zero vector.

**Firmware security**
- One shared key table on every board.
- PEER_RESET_MS = 60 s replay hole (esp8266_foa.ino:51, 228).
- Development keys are committed.

**Evidence files**
- testbed_sim.txt shows 0/20 in every condition, so it cannot distinguish the methods. Do not use it as evidence.
- On the branch: hardware_attacks.png is misnamed, the chatgpt.com link is cited as a source, and the RESEARCH_LOG.md would overwrite main's.

**Privacy**
- The uncommitted change in demo/build_final_deck.py makes the unblurred research.jpeg the default photo.

## 10. Method note and caveats

**How this review was done.** Several agents worked on separate angles in one workflow run on 27 Nov 2026:

| Angle | What it did |
|---|---|
| Repository audit | Read-only pass over paper/*.tex, experiments/foa/*, firmware/*, experiments/hardware/*, the demo build scripts, research/references.json and branch origin/hardware-results-20261127. The unit tests passed (16 passed). |
| Sweep: collaborative IoT | Collaborative, federated and peer-to-peer anomaly and intrusion detection for IoT. |
| Sweep: drift and poisoning | Drift and test-time adaptation under poisoning, budgeted updates, freeze attacks, shared/local decomposition, geometric-median aggregation. |
| Sweep: TinyML and hardware | On-device learning on MCUs, ESP-NOW/BLE gossip, energy, hardware IDS testbeds, authenticated frames. |
| Adversarial judge | Tried to refute novelty with fresh searches, checked repo facts and wrote the objections and the novelty statement. |
| Technical planner | Ranked fixes and experiments, with effort and proof impact. |
| Marks planner | Mapped the evidence to the course marks scheme and the viva. |

All agents were read-only. Nothing was modified, committed or pushed.

**Caveats**
- **Citations need checking.** All citations were found by web search or fetch on 27 Nov 2026. Verify each one (authors, venue, year, numbers) before final submission.
- **Search coverage.** The searches were targeted queries, not a systematic review. "We found no prior work" means none was found in these searches.
- **Reading depth varied.**
  - Many works were read at abstract or snippet level only: Ieropoulos IoTJ 2026 (PDF returned 403), TinyFed, Bose, Gaucher, Toso, Yamada/Sunaga, Garcia, Fung, Page, Vitter, and the frog-boiling paper (certificate error).
  - Pearson et al. was read only for Table II, via pdftotext.
  - Zhang, He, Huang, Ling (TSP 2025) was seen only in a snippet. Its author list needs checking.
- **Preprints.** Works marked as preprints are not peer reviewed. The router repository and the Nozomi document are grey literature.
- **Unresolved checks.**
  - The Manocchio PDF index says ESP32 WROOM while the abstract says ESP8266.
  - Confirm that "sensors2024" in bib.tex is Ino et al. 2024.
  - Confirm the ESP8266 no-FPU fact against Espressif documentation.
  - Confirm the ClippedGossip venue.
- **Dropped items.** Works that came up without a URL, or could not be confirmed, are left out of the tables. Examples: the MDPI IoT 2026 K-means paper, an ACM Computing Surveys TinyML security paper, a Scientific Reports Federated TinyML paper, and entries given only as arXiv numbers.
- **Hardware evidence is weak.** The hardware numbers come from single runs on one branch, with uncommitted builds and logs. Treat them as descriptive only until they are committed and repeated.

## 11. Follow-up (27 Nov 2026, later)

- **Paper fixes applied** (paper/*.tex, rebuilt paper/main.pdf, compiles with no undefined references):
  Minsker lemma "at least" and the equality in the Theorem 2 proof; a "Scope of the theorem" paragraph
  (Weiszfeld approximation, spread channel, K = 2 on the testbed); Cor 1 in minutes and days;
  Prop 4 renamed "No stop state", narrowed to gates, with starvation and the board-feature caveat;
  RTTAD, DriftXpert and TinyML survey wording; Korycki year; new citations (SIU, BALANCE, ClippedGossip,
  the Darktrace patent, RFC 8520, Mirai); E6b f = 4 outside the theorem; CESNET honesty sentence (static
  wins there); new hardware subsection with the 27 Nov board results; abstract, intro and conclusion no
  longer lead with the false-alarm result that the floor removes; "applied in full" replaced.
- **Reality check** written: `06_reality_check.md` (performance without spin, real use cases, better or
  existing alternatives, what would make FOA useful).
- **New finding while checking the firmware**: board features summarise all incoming packets
  together, so attacker traffic shifts every sample; the freeze result and the agreement-median
  argument assume separate samples. Only the budget argument carries over unchanged to the boards.
