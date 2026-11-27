MARKS PLAN FOR THE FOA VIVA AND REPORT (CSD457 G-04), 27 Nov 2026
I only read files. I changed, committed and pushed nothing. I found every paper below by web search in this run. Papers marked [preprint] are not peer reviewed.

======================================================================
0. WHAT THE MARKS REWARD
======================================================================
The marks scheme is in "Research Based Group Project Ideas.pdf". The project is 30% of the course grade:
- Survey, presentations and report: 10 marks
- Implementation and results: 5 marks
- Novelty: 5 marks. The scheme says plainly that "a new combination of techniques" or "a solution designed for a specific IoT constraint" counts as novelty.
- Faculty assessment: 10 marks

Required items:
- a literature table
- a clearly stated gap, research question and hypothesis
- baselines and metrics
- an architecture figure
- an IEEE two-column report that "clearly distinguishes existing work and your own work"
- one code zip with a README.md that explains setup and how to run

Gaps against that list:
1. paper/intro.tex has a Contributions paragraph but no explicit research question or hypothesis.
2. There is no top-level README.md. Only firmware/README.md, circuit/README.md and experiments/foa/README.md exist.
3. The related-work section has no comparison table.
All three are cheap to fix and map directly onto marks.

======================================================================
1. STORY AND FRAMING
======================================================================
One-line claim:
"An IoT detector must keep learning as normal traffic drifts. FOA lets it learn the part of the drift that vulnerability-diverse neighbours also see, and rations the part only it sees with a budget that grows but never closes. That gives a minimum time before a poisoner can hide, and no switch that an attacker can use to freeze learning."

Tell it in this order:
1. The dilemma. Choose your poison:
   - trust yourself and get poisoned (boiling frog, ANTIDOTE, Kloft and Laskov);
   - stop when suspicious and get frozen (our E5);
   - never learn and drown in false alarms (static, 78%).
   From one device's stream, honest drift and poisoning can look identical. That is our Prop 3, and WARDEN argues the same [preprint].
2. The insight. A router or firmware change reaches many devices. An exploit usually reaches one vendor. So neighbours give a second witness.
3. The mechanism: geometric median, then a significance gate, then the device's own agreement, then a split into a shared part and a device-only part, with a budget on the device-only part.
4. The guarantee, stated honestly. The budget turns "eventually compromised" into "not before t*". It is a delay, not prevention. Give t* in minutes (section 3, Q6).
5. The evidence: simulation on real traffic first, then the hardware lessons.
6. The correction. The floor experiment showed that our false-alarm advantage was an artefact. What survives is security under drift. Examiners reward self-correction when you present it as the method working.

What to stop saying:
- Do not lead with "9.0% vs 24.6% FPR" (E1). E12 shows it came from the spread ratchet: with the floor, single+floor is 0.8% and FOA+floor is 2.5%.
- Do not say "validated on hardware" for drift tracking, attacks or Byzantine robustness.
- Do not say "first". Say "we found no prior work that combines ...".

Framing for the novelty marks:
- The novelty is the COMBINATION: per-device adaptation, plus a consensus of diverse peers used only for the shared component, plus a never-closing cumulative budget with a time-to-compromise statement, plus a freeze analysis of stop-learning gates, all running on an MCU over ESP-NOW.
- Consensus and Byzantine robustness on their own are crowded (CIoTA, BALANCE, ClippedGossip). Say so before the examiner does.

======================================================================
2. WHICH RESULTS TO LEAD WITH (in this order)
======================================================================
1. E3, poisoning hidden in strong drift. 6,720 runs on held-out seeds 2 to 11, each paired with an attacker-free twin.
   - Compromised: FOA 10.8%, single device 39.2%, KL switch-off 29.9%, frozen reserve 27.4%. TOA reaches 5.5% only because it was given the oracle attack signature.
   - Always show the breakdown by attacker, not just the total:
     - boundary: FOA 0% at every share, single device 63%;
     - core-hiding: 34% at p=0.4;
     - mimicry: 29% at p=0.4.
   - The floored version is E12, 9.4% vs 43.1%. Most of that gap is the boundary attacker (0.0% vs 75.4%). Core is 11.8% vs 36.8%. Mimicry is 16.4% vs 17.1%, i.e. no advantage.
2. E5, freeze. A KL switch-off goes to 100% FPR with 5% decoys (26% without decoys). FOA's numbers are identical with and without decoys (11.8% vs 11.8%), and a unit test shows they are equal bit for bit. This is the cleanest qualitative result, and the related-work sweeps found no prior collaborative-IoT work that studies freeze attacks.
3. E11, CESNET with real drift (40 weeks, real ISP network) and a modelled attack.
   - Compromised: FOA 0%, single device 18%, naive 91%.
   - Caveats to state: 5 seeds, 11 victims, one institution, research-network IPs rather than IoT devices.
4. E4, monoculture. Same-model consensus reaches 100% compromised once 2 of 3 cameras are infected. FOA with diverse peers stays at 0%. Present this as a demonstration of WHY diversity matters, not as a measured win: with diverse peer selection, 0% is guaranteed by construction.
5. Bound check. Cor 1 had 0 violations in 3,630 attacked runs plus 120 synthetic runs, and in 1,710 runs with the floor.
6. Ablations (E8):
   - discarding the residual (CIoTA-style): 54% FPR;
   - no peers: 43% FPR;
   - no residual budget: 67% compromised.
   Each component earns its place.
7. Honest limits, shown on a slide rather than hidden:
   - E6b: Byzantine peers plus a poisoner, f=3 of 7, compromise 56% of victims;
   - device-only drift is worse under FOA (24.6% vs 0.9% with the floor);
   - mimicry is not helped.

======================================================================
3. HOW TO PRESENT THE HARDWARE HONESTLY
======================================================================
This is now a strength, because the 27 Nov runs include controls. Source: origin/hardware-results-20261127:FOA_floor3/experiments/hardware/RESULTS.md.

What it shows:
- Floor on the boards. The minimum and final spread ratio was 1.0000 on all three nodes in every run. The ratchet collapse is fixed on the hardware.
- Calibration aliasing found and controlled. In the same matched 20-minute window:
  - static control (no adaptation): 45.8 to 46.4% FPR;
  - FOA+floor with the fixed stride: 25.3%;
  - FOA+floor with the rotated stride: 1.53 to 1.70%.
  Over the full 36.5 minutes the rotated-stride run was 1.43 to 1.72%, with about 90% of cycles hearing both peers. This is the best hardware headline. Caveat: one run per configuration, separate boots.
- Natural experiment. Calibration keeps every 10th sample at 50 ms, i.e. one sample every 500 ms. With telemetry periods of 160, 200 and 240 ms:
  - only the 200 ms node is badly hit: 25.2% FPR, against 2.4% and 0.7% for the other two;
  - the reason is that 500 mod 200 = 100 ms, so calibration only sees 2 of the 4 phases, while 500 mod 160 and 500 mod 240 are both 20 ms, so those nodes cycle through every phase;
  - the host fixture agrees: the fixed stride flags 101 of 400 samples, the rotated stride 11 of 400.
  This is a well-designed IoT lesson. Show it as a figure.
- Re-attribute the old "90% collapse". Two causes were mixed: the spread ratchet (real, spread 0.035 in floor4) and the bad calibration (about 46% FPR on its own, per the static control). Say this explicitly. It corrects the paper's attribution.
- Failure 1, abrupt shared drift (telemetry periods halved at 30 minutes):
  - FPR went to 99.9% on all boards, with or without peers;
  - each board had zero core samples in 78 of 79 cycles after the change;
  - call it "starvation": with no accepted points, every proposal is zero, so peers also send zero;
  - it is a limit of learning only from accepted samples, which every rule we tested shares (static, single device, gates);
  - it contradicts the wording of Prop 4(ii). Restate Prop 4 as "no attacker input can switch learning off", and add "learning can starve if all traffic leaves the alarm radius at once".
- Failure 2, centre walk. In clean runs the centre moved 3.5 to 5.5 calibrated spreads, about 0.65 to 1.0 alarm radii, in under 40 minutes. This sits inside the budget: the residual budget alone allows 0.1 + 0.005 x 291 = 1.56 alarm radii after 291 cycles. It shows that the budget is generous on wall-clock time.
- Cost:
  - proposal about 21.5 ms (including batch classification), step 1.6 to 1.9 ms, sign about 0.6 ms, verify about 1.0 ms, so about 25 ms per cycle of about 7.5 s (291 cycles in 36.5 minutes), roughly 0.3% duty;
  - board power 381.7 to 391.2 mW, the same in every phase;
  - an upper-bound estimate of energy per cycle is 25 ms x about 385 mW, roughly 10 mJ. Label it an estimate. It replaces the old "7 mJ" and "365 mW";
  - ESP8266 build: flash 280,812 B, RAM 51,248 / 80,192 B (63%), IRAM 61,031 / 65,536 B (93%). The IRAM figure leaves almost no headroom, which is worth saying.
- Not done:
  - no attack, decoy, forgery or replay trials on the boards;
  - placeholder basis (FEAT_MEAN = 0, FEAT_STD = 1, random W);
  - traffic is the boards' own telemetry;
  - one run per configuration, so no confidence intervals;
  - the no-peers build also skips the receive wait, so that comparison is confounded;
  - K = 2 peers, so the Byzantine lemma says nothing on the testbed.

Script line for the hardware slide:
"Hardware did not validate our attack results. It found two failure modes simulation missed, it confirmed the fix for one, and it isolated a calibration bug with a control run. Attack results are from simulation."

======================================================================
4. RELATED-WORK POSITIONING TABLE (verified this run)
======================================================================
Columns:
- A = consensus across devices
- B = poisoning or Byzantine robustness
- C = drift adaptation
- D = cumulative budget or time-to-compromise
- E = split into shared and device-only parts
- F = freeze or availability analysis
- G = MCU hardware
Y = yes, P = partial, N = no.

| Work | A | B | C | D | E | F | G | One-line difference from FOA |
|---|---|---|---|---|---|---|---|---|
| CIoTA (Golomb, Mirsky, Elovici, NDSS DISS 2018) and Mirsky, Golomb, Elovici, JPDC 2020 | Y | P | P | N | N | N | N (48 Raspberry Pis) | Same-model consensus; discards behaviour the majority has not seen, so honest device-only drift is erased |
| DIoT (Nguyen, Marchal, Miettinen, Fereidooni, Asokan, Sadeghi, IEEE ICDCS 2019) | P (server FL) | N | P | N | P (per type) | N | N | Federated, per-device-type models at gateways |
| Nguyen, Rieger, Miettinen, Sadeghi, NDSS DISS 2020 | P | Y (attack) | N | N | N | N | N | Our threat model in FL form: compromised devices slowly inject traffic. Attack only, no defence of our kind |
| BALANCE (Fang et al., ACM CCS 2024) | Y | Y | N | P (per-round radius) | N | N | N | Radius shrinks over time, so late real drift is rejected |
| ClippedGossip (He, Karimireddy, Jaggi) [preprint] | Y | Y | N | P (per-step clip) | N | N | N | Clips peers to a ball around own model; per step, not cumulative |
| Karimireddy, He, Jaggi, ICML 2021 | P | Y | N | P | N | N | N | Shows attacks spread across rounds beat rules that ignore history; the reason for a cumulative budget |
| Baruch, Baruch, Goldberg, NeurIPS 2019 (ALIE) | P | Y (attack) | N | N | N | N | N | Small in-variance shifts defeat median-type rules; untested against FOA |
| Chan-Tin, Feldman, Hopper, Kim, SecureComm 2009 (frog-boiling) | Y | Y (attack) | N | N | N | N | N | Outlier gating in gossip fails against sub-threshold steps |
| ANTIDOTE (Rubinstein et al., ACM IMC 2009) | N | Y | P | N | N | N | N | Boiling-frog poisoning of PCA; robust PCA defence |
| Kloft and Laskov, JMLR 13, 2012 | N | Y | N | Y (attacker-gain bounds) | N | N | N | Same centroid detector, single device, stationary normal |
| Bose, Lessard, Fazel, Dvijotham, AISTATS 2025 | N | Y | N | Y (certificate) | N | N | N | Certified bound vs adaptive online poisoner; no drift, single learner |
| Korycki and Krawczyk, Machine Learning 112, 2023 | N | Y | Y | N | N | P | N | Fake-drift poisoning of drift detectors |
| WARDEN (Balachandran, arXiv 2607.21673) [preprint] | N | Y | Y | P | N | P | N | Self-poisoning threshold; argues one stream cannot separate drift from contamination |
| Alhelou, Singh, Wang, IEEE ISCAS 2026 (in press) | P (server) | Y | Y | N | N | N | N (Raspberry Pi) | Treats drifted clients as outliers to drop, the opposite of FOA's split |
| Ochiai et al., WAFL-Autoencoder, MobiHoc 2023 AIoT workshop | Y | N | N | N | P (local vs global anomaly) | N | N | Device-to-device mean pull, no adversary |
| Ieropoulos, Anthi, Spyridopoulos, Burnap et al., IEEE IoT Journal 13(11), 2026 | P (outputs) | P | N | N | N | N | Y (ESP32) | Frozen centrally trained model; peers cross-check predictions |
| Ino, Yoshida, Matsutani, Fujino, Sensors 24(19):6416, 2024 | N | Y (physical attack) | P | N | N | N | Y | Physical poisoning of an on-device learner; calls for defences |
| Manocchio, Layeghy, Portmann, ITNAC 2022 | N | N | N | N | N | N | Y (ESP8266 per abstract) | Static supervised decision tree in a smart bulb |
| FOA (ours) | Y | Y (sim; vacuous at K=2) | Y (sim; fails on abrupt drift on boards) | Y (Cor 1) | Y | Y (sim) | P (3 ESP8266, no attacks) | The combination |

URLs:
- CIoTA: https://arxiv.org/abs/1803.03807 ; JPDC 2020: https://arxiv.org/abs/2006.10587
- DIoT: https://arxiv.org/abs/1804.07474
- Nguyen 2020: https://www.ndss-symposium.org/wp-content/uploads/2020/04/diss2020-23003-paper.pdf
- BALANCE: https://arxiv.org/abs/2406.10416
- ClippedGossip: https://arxiv.org/abs/2202.01545
- Karimireddy 2021: https://proceedings.mlr.press/v139/karimireddy21a.html
- ALIE: https://arxiv.org/abs/1902.06156
- Frog-boiling: https://link.springer.com/doi/10.1007/978-3-642-05284-2_26
- ANTIDOTE: https://ptolemy.berkeley.edu/projects/truststc/pubs/725/IMC.2009.pdf
- Kloft and Laskov: https://jmlr.org/papers/v13/kloft12b.html
- Bose 2025: https://proceedings.mlr.press/v258/bose25b.html
- Korycki and Krawczyk: https://link.springer.com/article/10.1007/s10994-022-06177-w
- WARDEN: https://arxiv.org/abs/2607.21673
- Alhelou: https://repository.essex.ac.uk/42630/
- Ochiai: https://arxiv.org/abs/2407.11308
- Ieropoulos: https://orca.cardiff.ac.uk/179135/
- Ino: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11479347/
- Manocchio: https://arxiv.org/abs/2210.03254

Notes on these entries:
- I could not confirm a venue for ClippedGossip.
- The Ochiai venue comes from the arXiv comment.
- Manocchio's PDF index terms say ESP32 WROOM while the abstract says ESP8266. Check before citing.
- I read the Ieropoulos benchmark numbers only in snippets. Do not quote them.

Supporting references (also verified):
- Minsker, "Geometric median and robust estimation in Banach spaces", Bernoulli 21(4), 2015. https://arxiv.org/abs/1308.1334
- Pillutla, Kakade, Harchaoui, "Robust Aggregation for Federated Learning" (RFA), IEEE Trans. Signal Processing 70:1142-1154, 2022. https://arxiv.org/abs/1912.13445. Cite next to Minsker for the Weiszfeld geometric median.
- Garcia, Bessani, Gashi, Neves, Obelheiro, "OS Diversity for Intrusion Tolerance: Myth or Reality?", IEEE/IFIP DSN 2011. https://openaccess.city.ac.uk/id/eprint/526/. Evidence for the diversity assumption.
- Perrig, Song, Canetti, Tygar, Briscoe, RFC 4082 (TESLA), 2005. https://www.rfc-editor.org/rfc/rfc4082. The fix for the shared-key table.
- Pearson, Luo, Zhang, Dey, Ling, Bassiouni, Fu, "On Misconception of Hardware and Cost in IoT Security and Privacy", IEEE ICC 2019. https://par.nsf.gov/servlets/purl/10149710. The ESP8266 HMAC benchmark (about 182 us, as read by the hardware sweep; recheck Table II before quoting).
- Meidan et al., "N-BaIoT", IEEE Pervasive Computing 17(3), 2018. https://arxiv.org/abs/1805.03409
- Koumar, Hynek, Cejka, Siska, "CESNET-TimeSeries24", Scientific Data 12:338, 2025. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11865510/
- ESP-IDF ESP-NOW docs: encrypting multicast vendor-specific action frames is not supported. https://docs.espressif.com/projects/esp-idf/en/v5.1.3/esp32c3/api-reference/network/esp_now.html

Wording fixes needed in paper/related.tex and slide 18 (build_final_deck.py line 342 onward):
- RTTAD: say it "adapts at test time on high-confidence pseudo-normal and pseudo-anomalous samples, ignores ambiguous ones, and iterates until too few confident samples remain".
- DriftXpert: rename our "or" baseline to "outlier-ratio pause gate (our construction)". DriftXpert triggers updates on drift; it does not pause them.
- TinyML survey: replace "no security mechanism among about 70 works" (deck line 357) with "the survey does not cover security or poisoning".
- Korycki and Krawczyk: the year is 2023, not 2022.

======================================================================
5. LIKELY EXAMINER QUESTIONS, WITH CRISP ANSWERS
======================================================================
Q1. What is actually new?
A: Peers, geometric medians and budgets each exist. We found no prior work that combines a diverse-peer consensus used only for the shared part of an update, a never-closing cumulative budget on the device-only part with a time-to-compromise bound, and a freeze analysis, running on MCUs. The closest works are CIoTA, BALANCE and Kloft and Laskov.

Q2. Why not just use BALANCE or ClippedGossip?
A: Both limit each round relative to the node's own model. BALANCE's radius shrinks over time, so real drift late in deployment gets rejected. Karimireddy et al. (ICML 2021) show that rules which ignore history can be beaten by attacks spread across rounds, and our budget is cumulative. We have not yet run BALANCE as a baseline. That is the first next experiment.

Q3. Frog-boiling showed that outlier gating in gossip fails. Isn't your z gate the same?
A: Yes, the per-step gate alone would fail. Safety rests on the cumulative budget, not on the gate. The gate decides only how much of the shared part to follow.

Q4. Does your Byzantine theorem apply to your 3 boards?
A: No. Each board has K = 2 peers, and the geometric median of 2 points tolerates no bad peer. Byzantine claims are simulation-only, with K of 7 or more. We also fixed a slip in the lemma: it should say "at least (1-alpha)K points", per Minsker's Lemma 2.1. The theorem also covers the exact median rather than 10 Weiszfeld iterations, and it does not cover the spread channel.

Q5. E6b uses f=4 of 7. That breaks f < K/2.
A: Correct. It is a deliberate stress test outside the theorem, and we report it as such: 56% compromised at f=3, 60% at f=4.

Q6. What is time-to-compromise in real time?
A: t* is about (M - 1.2)/0.006 cycles. For borderline victims, M = 1.3 to 1.9 alarm radii, that is 17 to 117 cycles. At the boards' 7.5 s cycle that is about 2 to 15 minutes. It is a minimum delay, not immunity. It excludes the common channel. B should be set per hour of wall-clock time for a real deployment.

Q7. Your clean centre moved almost one alarm radius in 36 minutes with no attacker.
A: Yes. That is within the budget, which already allows 1.56 radii after 291 cycles. It shows the budget is generous at this cycle rate. It also argues for tying B to wall-clock time and for a frozen anchor region, as WARDEN suggests.

Q8. What caused the 90% false alarms on the boards?
A: Two causes. First, the spread ratchet: the floor fixed it and spread held at 1.0. Second, calibration aliasing: CAL_EVERY=10 is phase-locked to the 200 ms telemetry. The static control alone gave 46 to 48%. With a rotated stride, FOA+floor gave 1.4 to 1.7% over 36 minutes. The 160/200/240 ms run isolates the effect.

Q9. Under abrupt drift your boards went to 100%. Did FOA fail?
A: Yes, through starvation. All traffic left the alarm radius at once, so no device had accepted samples, and every proposal, including the peers', was zero. Every rule that learns only from accepted samples shares this, the static detector included. We restate Prop 4 accordingly. The proposed fix is a re-anchoring move when own core and most peers' n_core are empty, capped by the common budget. We have not evaluated it, so we do not claim it.

Q10. How much energy does learning cost?
A: Too little to measure at board level. The board draws about 382 to 391 mW in every phase, dominated by the radio. Compute is about 25 ms per 7.5 s cycle, so an upper-bound estimate is about 10 mJ per cycle. Phase-marked GPIO measurement is future work.

Q11. Your HMAC uses one key table on every board.
A: Yes. Capturing one board yields every identity. That is a real limit of the current firmware, and it means f is no longer below K/2. The fixes are per-pair keys (N-1 tags per frame, about 0.2 to 0.6 ms each) or TESLA-style delayed key disclosure (RFC 4082). We also need a per-boot epoch, because of the 60 s replay reset.

Q12. Isn't the monoculture result true by construction?
A: Yes. With diverse peer selection, an infected same-model camera is never a peer. The experiment shows why diversity matters. It does not measure it. Diversity is an assumption. Garcia et al. (DSN 2011) give evidence that shared vulnerabilities are rare across diverse OSes, while BASHLITE infecting all nine N-BaIoT devices shows the limits.

Q13. You picked victims using the attack traffic. Is that leakage?
A: The rule (margin of at least 1.3 alarm radii) was fixed before testing. It selects which devices can be victims, not any parameter, and it is the same for every method.

Q14. Is your "DriftXpert-style" baseline DriftXpert?
A: No. DriftXpert uses drift detection to trigger updates. Ours is an outlier-ratio pause gate of our own construction, and we have renamed it.

Q15. How much of the evaluation is synthetic?
A: Real: N-BaIoT traffic and botnets, and CESNET drift. Ours: the N-BaIoT drift (feature transforms), the fleet concurrency, the feature-level poisoner, the CESNET attack, and the board traffic.

Q16. Why a centroid and not a neural network?
A: It fits an ESP8266 (about 25 ms per cycle), it has a known poisoning analysis (Kloft and Laskov), and it makes the budget exact. We adapt a centroid. We do not train a network on the device.

Q17. Why is single device + floor worse on security than without the floor?
A: The floor keeps the region wider, so more boundary attacks fit inside it: 63.2% rises to 75.4%.

Q18. So does FOA reduce false alarms?
A: Not once both use the floor (2.5% vs 0.8%). Its benefit is security under drift (9.4% vs 43.1% compromised). We corrected the claim.

Q19. Isn't your threat model Nguyen et al. 2020?
A: Same family: compromised devices slowly inject traffic into a learner. They attack federated learning at gateways. We defend an on-device learner.

Q20. Have you tried an ALIE-style colluding attack?
A: No. Colluders shifting just under the gate each cycle are bounded by the same cumulative budget in principle. It is untested and is our next Byzantine experiment.

Q21. How confident are your percentages?
A: There are 10 held-out seeds and thousands of paired runs. Show 95% Wilson intervals; this needs computing (see section 7). The hardware numbers are single runs and descriptive only.

Q22. Can a peer with no data still vote?
A: Today, yes: a zero proposal counts. n_core is transmitted but unused. Filtering on it is a small fix, and it helps Q9.

======================================================================
6. SLIDES TO ADD, CHANGE OR CUT
======================================================================
The deck (demo/build_final_deck.py) has 18 slides, created from line 139 to line 342.

Change:
- Slide 5, theory (line 182). Add t* in minutes (2 to 15 minutes at 7.5 s cycles) and one line: "Byzantine bound needs K of 7 or more peers. On our 3-board testbed K = 2, so it does not apply."
- Slide 6, related (line 194). Replace it with the positioning table from section 4, trimmed to about 8 rows: CIoTA, BALANCE, Karimireddy, frog-boiling, Kloft, Ieropoulos, Alhelou, FOA. This is the literature-table mark.
- Slide 8, headline (line 218). Add the bar breakdown by attacker (boundary, core, mimicry) and say "mimicry not helped".
- Slide 9, all rules (line 224). Rename the "or" gate "outlier-ratio pause gate (ours)".
- Slide 11, photo (line 251). The uncommitted change makes research.jpeg, the UNBLURRED photo, the default. Revert to demo/testbed_photo.jpg before building. This is a privacy issue.
- Slide 12, hardware (line 260):
  - 15 ms becomes about 25 ms (21.5 + 1.8 + 0.6 + 1.0);
  - 365 mW becomes 382 to 391 mW;
  - add the ESP8266 flash/RAM/IRAM figures and "learning energy not resolvable".
- Slide 15, floor (line 305). Replace "fix not yet run on the boards" with "on the boards the spread ratio held at 1.0000 in every run".
- Slide 16, limits (line 315). Add: abrupt-drift starvation, shared key table, K = 2, single runs, placeholder basis.
- Slide 18, six recent papers (line 342). Fix RTTAD, DriftXpert and the survey wording, or move the slide to backup. The positioning table covers it.

Add (3 slides):
- A. "Hardware controls, 27 Nov". A 3-bar chart of matched 20-minute FPR: static 46%, FOA+floor fixed stride 25%, FOA+floor rotated stride 1.6%. Add the 160/200/240 ms inset with the 500 mod 200 = 100 ms arithmetic.
- B. "What broke: abrupt shared drift". A before/after FPR plot (about 3% to 99.9%, with and without peers), the starvation explanation, and the proposed re-anchoring fix marked "not evaluated".
- C. "Research question and hypothesis".
  - RQ: "Can an on-device IoT detector keep adapting to drift while bounding how fast a poisoner can hide, without a stop rule an attacker can trigger?"
  - H: "Following only the peer-backed part of an update, and budgeting the rest, lowers compromise under drift compared with single-device and gated adaptation, at bounded cost on an ESP8266."
  - Put it after slide 3. It is a rubric item.

Cut or merge:
- Merge slides 13 and 14 (collapse, then why) into one slide. Re-attribute the collapse to ratchet plus aliasing, and drop "the isolated run is not a controlled comparison" now that real controls exist.
- Move the formula-heavy material and the E6b, E7 and E10 details to backup slides.
- Backup set: threat model and keys, E6b table, E7 budget sweep, E12 full table, CESNET caveats.

Viva guide (demo/build_viva_prep.py) changes:
- Line 108: 365 mW becomes about 385 mW.
- Line 109: 7 mJ becomes "about 10 mJ upper-bound estimate".
- Line 111 ("detectors collapsed first"): replace with "no attack trials yet; time went to calibration controls".
- Line 123 ("not completed a hardware run"): replace with "floor held at 1.0 on the boards".
- Add Q4, Q6, Q7, Q8, Q9, Q11, Q14 and Q20 from section 5.
- The RTTAD answer at line 136 is already accurate.

======================================================================
7. 48-HOUR PRIORITY LIST
======================================================================
These are for the team to do. I made no changes.

Hours 0 to 6 (correctness; no new experiments):
1. Theory text:
   - Minsker lemma "at least (1-alpha)K", in paper/theory.tex and the robust.py docstring;
   - say the theorem covers the exact median;
   - say the spread channel is not covered;
   - say K = 2 on the testbed;
   - give t* in minutes;
   - restate Prop 4(ii) as in Q9.
2. Related work:
   - RTTAD, DriftXpert renaming and TinyML wording;
   - Korycki year 2023;
   - add Nguyen 2020, DIoT, BALANCE, ClippedGossip [preprint], Karimireddy 2021, frog-boiling, ALIE, Bose 2025, RFA, Ieropoulos 2026, Alhelou 2026, Ochiai, TESLA and Garcia DSN 2011;
   - add the positioning table to related.tex.
3. Numeric consistency:
   - one compute figure (about 25 ms on ESP8266, saying it includes batch classification);
   - power 382 to 391 mW;
   - 23,040 vs 23,104 bit flips;
   - ESP32 vs ESP8266 in the keywords and contributions;
   - footprint labelled "ESP32 compile only" next to the measured ESP8266 build.
4. Intro and abstract: lead with security under drift, not E1's FPR. Add the explicit RQ and hypothesis.
5. Revert the deck photo to the blurred file.

Hours 6 to 12 (evidence hygiene; this protects the implementation mark):
6. Commit the rotated-stride, drift and no-peer firmware builds, the raw 27 Nov serial logs and followup_20261127_142002.txt.
7. Rename hardware_attacks.png. Remove the chatgpt.com link from FOA_Demo_Evidence.md.
8. Merge the branch RESEARCH_LOG.md into main's log. Do not overwrite main's log.
9. Rewrite paper/hardware.tex with section 3 of this plan.
10. Add a top-level README.md: setup, `pytest experiments/foa/tests/test_foa.py`, how to regenerate the paper numbers (paper/make_numbers.py) and the deck, and the firmware flashing steps.

Hours 12 to 30 (only if the boards are free; one new experiment class at most):
11. Best value: a GRADUAL shared drift run on the rotated-stride build. For example, step the telemetry period down by about 5% every 2 to 3 minutes rather than halving it at once. Run the no-peers twin with the receive wait kept, to remove the confound. This tests whether FOA tracks drift inside its design envelope, which no board run has shown yet. Report it whatever the result.
12. Repeat the rotated-stride clean baseline twice more, giving 3 runs, so you can quote a range.
13. Stretch, only if a 30-minute rehearsal of firmware/laptop/poisoner.py works: one boundary-poisoner run on one node with an attacker-free twin. If it is shaky, skip it and keep "attacks are simulation-only".
Do NOT change the FOA rule (for example the re-anchoring fix) before the viva. Present it as identified and proposed.

Hours 30 to 40 (cheap analysis wins):
14. Compute 95% Wilson intervals for the E3, E5, E11 and E12 headline percentages from the existing results CSVs. Put them on the headline slides.
15. Optional, simulation only, dev seeds then held-out seeds: a BALANCE baseline (a few lines in fleet.py) on strong shared drift. If there is no time, list it as the first future experiment (Q2).

Hours 40 to 48:
16. Regenerate paper/numbers.tex, the paper, G04_FOA_Final.pptx and G04_Viva_Prep.pdf. Check that no slide still says 15 ms, 365 mW, "not yet run on the boards", "DriftXpert-style" or "no security mechanism".
17. Agree who answers which block (theory, simulation, hardware, related work) and who did what. Do two timed run-throughs with a peer playing examiner and asking Q4, Q6, Q8, Q9 and Q11.

Remaining weaknesses to keep stated in the report and the limits slide:
- no hardware attacks;
- the Byzantine bound is vacuous at K = 2;
- the shared key table;
- abrupt-drift starvation;
- mimicry is not helped;
- device-only drift costs more;
- the Byzantine-plus-poisoner limit (56% at f=3);
- the placeholder basis;
- single hardware runs;
- the planned independent code review (24 Oct) never ran.

Key repo paths:
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/demo/build_final_deck.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/demo/build_viva_prep.py
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/theory.tex
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/related.tex
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/hardware.tex
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/paper/intro.tex
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/firmware/esp8266_foa/foa_config.h
- /Users/rishitkamboj/Collegeactual/Study/SEM5/iot/research project/brainstorming/Research Based Group Project Ideas.pdf (marks scheme)
- Hardware results on the branch: origin/hardware-results-20261127:FOA_floor3/experiments/hardware/RESULTS.md