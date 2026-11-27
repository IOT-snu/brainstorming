### Sweep collab-iot
LITERATURE SWEEP: collaborative, federated and peer-to-peer anomaly and intrusion detection for IoT, compared with FOA
(Read only. Nothing in the repo was modified. Every paper below came up in a web search or fetch during this run. "Read" says how deeply I checked each one.)

Axes: (a) multi-device consensus, (b) poisoning/Byzantine robustness, (c) drift adaptation, (d) bounded or budgeted updates with time-to-compromise guarantees, (e) shared-vs-device-only decomposition, (f) freeze-attack resistance, (g) MCU hardware. Ratings: H = high, M = medium, L = low, 0 = none.

== A. Works found (19) ==

1. Mirsky, Golomb, Elovici. "Lightweight Collaborative Anomaly Detection for the IoT using Blockchain." Journal of Parallel and Distributed Computing, 2020. Workshop version: Golomb, Mirsky, Elovici, "CIoTA: Collaborative IoT Anomaly Detection via Blockchain," NDSS DISS 2018. https://arxiv.org/abs/2006.10587 , https://arxiv.org/abs/1803.03807 . Read: full text of the journal version (pdftotext).
What it does: same-type devices each train a control-flow Markov model. Partial blocks of peer models are merged only if (1) a device's own model is within distance alpha of the merge ("model attestation") and (2) the transition was seen by at least pa% of the models ("abnormality filtration"). It uses "proof of cumulative majority", runs on 48 Raspberry Pis, and keeps learning after the grace period.
Overlap: a H, b M (benign majority assumed; with L=20 and pa=75% an attacker must poison 15 of 20 models), c M (says collaboration handles "future concept drifts (e.g., software updates)", but this was not evaluated), d L (proposes a merge interval T(m) that grows with chain length; no bound), e L (local model vs global model, but no split of the update into components), f L (rate-limits chain processing against DoS only), g L (Raspberry Pi, not an MCU).

2. Fang, Zhang, Hairi et al. "Byzantine-Robust Decentralized Federated Learning" (BALANCE). ACM CCS 2024. https://arxiv.org/abs/2406.10416 . Read: method section, HTML v4.
What it does: each client accepts neighbour j only if ||w_i - w_j|| <= gamma * exp(-kappa * t/T) * ||w_i||. That is a radius around its own model that shrinks over time. It then mixes: w_i <- alpha*w_i + (1-alpha)*mean(accepted). Convergence is proven under poisoning.
Overlap: a H, b H, c 0 (static objective; the shrinking radius would actually block late drift), d M (per-round influence is capped by the radius, but there is no time-to-compromise statement), e L (self-reference only), f 0 (not studied; the shrinking radius invites a freeze), g 0. The paper does not say what happens when no neighbour is accepted.

3. Ieropoulos, Anthi, Spyridopoulos, Burnap, Carnelli, Khan. "Federated Detection at the Edge: Collaborative Anomaly Detection for Resource-Limited IoT." IEEE Internet of Things Journal 13(11):24205-24218, 2026, DOI 10.1109/JIOT.2026.3674644. https://orca.cardiff.ac.uk/179135/ . Read: abstract and search excerpts only. The PDF returned 403 to me, so verify the details before citing.
What it does: ESP32 boards run inference with a model trained centrally (autoencoder-based labelling). They multicast predictions over UDP, run cross-device consistency checks against a trust threshold to isolate faulty or compromised nodes, and use MD5 hashes to check that all boards run the same model. The authors say on-device training is infeasible on ESP32.
Overlap: a H (consensus on outputs, not on models), b M, c 0 (no on-device adaptation), d 0, e 0, f 0, g H.

4. Alhelou, Singh, Wang. "Adaptive Federated Learning Defense Against Byzantine Attacks and Concept Drift in IIoT." IEEE ISCAS 2026 (accepted, in press). https://repository.essex.ac.uk/42630/ . Read: full text.
What it does: a star-topology FL autoencoder. The server runs an L2-deviation outlier test on updates and switches from FedAvg to Krum when it fires. A PSI test monitors drift. Evaluated on Edge-IIoTset with 5 Raspberry Pi 3B clients: F1=0.828 at 40% malicious clients. The authors say the outlier test flags updates "regardless of whether they originated from Byzantine attacks or concept drift" and call the resulting removal of drifted clients by Krum "implicit drift mitigation".
Overlap: a M (central server), b M, c M, d 0, e 0 (it explicitly conflates drift with attack, which is the opposite of FOA's decomposition), f 0, g L.

5. Nguyen, Rieger, Miettinen, Sadeghi. "Poisoning Attacks on Federated Learning-based IoT Intrusion Detection System." NDSS DISS 2020. https://www.ndss-symposium.org/wp-content/uploads/2020/04/diss2020-23003-paper.pdf . Read: abstract and introduction.
What it does: compromised IoT devices gradually inject malicious traffic into a gateway's training data, slowly planting a backdoor in the federated model (DIoT). The attacker never compromises the FL client.
Overlap: a M, b H (attack side), c L, d 0, e 0, f 0, g 0. This is essentially FOA's threat model for accepted-sample poisoning.

6. Nguyen, Marchal, Miettinen, Fereidooni, Asokan, Sadeghi. "DIoT: A Federated Self-learning Anomaly Detection System for IoT." IEEE ICDCS 2019. https://arxiv.org/abs/1804.07474 . Read: abstract and summaries.
What it does: gateways identify each device's type and train per-type models, which a server aggregates. Reported 95.6% detection of Mirai at about 257 ms.
Overlap: a M, b L, c L, d 0, e L (per-type grouping), f 0, g 0.

7. Nguyen et al. "FLAME: Taming Backdoors in Federated Learning." USENIX Security 2022. https://www.usenix.org/conference/usenixsecurity22/presentation/nguyen . Read: abstract and summary.
What it does: server-side clustering, norm clipping and calibrated noise. The evaluation includes an IoT NIDS with 13 Mirai backdoors across 24 device types.
Overlap: a M, b H, c 0, d M (norm clipping bounds each round's update, but gives no bound over time), e 0, f 0, g 0.

8. Rey, Sanchez Sanchez, Huertas Celdran, Bovet, Jaggi. "Federated Learning for Malware Detection in IoT Devices." Computer Networks 2022, DOI 10.1016/j.comnet.2021.108693. https://arxiv.org/abs/2104.09994 . Read: abstract.
What it does: supervised and unsupervised federated detectors on N-BaIoT with malicious participants. FedAvg breaks "even with a single adversary"; robust aggregators help but do not solve the problem.
Overlap: a M, b M, c 0, d 0, e 0, f 0, g 0. It uses the same dataset as FOA, so it is a direct baseline source.

9. Karimireddy, He, Jaggi. "Learning from History for Byzantine Robust Optimization." ICML 2021, PMLR 139:5311-5319. https://proceedings.mlr.press/v139/karimireddy21a.html . Read: abstract and slides.
What it does: proves that any aggregation rule which ignores history can be driven to diverge by attacks spread across rounds ("time-coupled" attacks). The fix is centered clipping around the previous aggregate plus worker momentum.
Overlap: a M, b H, c 0, d M (gives the theoretical reason a multi-round budget is needed), e 0, f 0, g 0.

10. He, Karimireddy, Jaggi. "Byzantine-Robust Decentralized Learning via ClippedGossip." arXiv 2202.01545 [preprint; no venue listed on the arXiv page]. https://arxiv.org/abs/2202.01545 . Read: abstract.
What it does: each node clips each neighbour's difference to a ball around its own parameters. Converges to a neighbourhood of a stationary point on arbitrary graphs.
Overlap: a H, b H, c 0, d M (per-step clip), e L, f 0, g 0.

11. Gaucher, Dieuleveut, Hendrikx. "Byzantine-Robust Gossip: Insights from a Dual Approach." arXiv 2405.03449 [preprint]. https://arxiv.org/abs/2405.03449 . Read: abstract.
What it does: reads robust gossip as clipped dual gradient descent, with guarantees for average consensus.
Overlap: a H, b H, c 0, d L, e 0, f 0, g 0.

12. Baruch, Baruch, Goldberg. "A Little Is Enough: Circumventing Defenses For Distributed Learning." NeurIPS 2019. https://arxiv.org/abs/1902.06156 . Read: abstract and reviews.
What it does: colluding workers (under 25%) shift every coordinate by a small multiple of the honest standard deviation. This stays inside the variance and defeats median, trimmed-mean and Krum.
Overlap: b H (attack side). This is the natural colluding-peer attack against FOA's geometric median plus z gate.

13. Chan-Tin, Feldman, Hopper, Kim. "The Frog-Boiling Attack: Limitations of Anomaly Detection for Secure Network Coordinate Systems." SecureComm 2009 (Springer LNICST, 2009). Extended version: ACM TISSEC 2011 (with Heorhiadi). https://www-users.cs.umn.edu/~hopper/frogBoiling.pdf . Read: search abstract only (fetch failed on a certificate error).
What it does: in a decentralized gossip system (Vivaldi), attackers lie just under the rejection threshold every round. With 5% attackers this defeats Mahalanobis, Kalman and witness-based (Veracity) filters. The authors conclude that outlier detection alone cannot secure such systems.
Overlap: a H, b H, c L, d 0, e 0, f 0, g 0. This is the clearest prior statement of the problem FOA's growing budget is designed to answer.

14. Kailkhura, Brahma, Varshney. "Consensus based Detection in the Presence of Data Falsification Attacks." arXiv 1504.03413. The DOI prefix suggests IEEE TSIPN 2016 [venue to verify]. https://arxiv.org/abs/1504.03413 . Read: abstract.
What it does: Byzantine-robust weighted-average consensus for distributed detection with no fusion centre. When attacker statistics are unknown, the fusion weights are learned.
Overlap: a H, b H, c L, d 0, e 0, f 0, g 0.

15. Fung, Zhang, Aib, Boutaba. "Dirichlet-Based Trust Management for Effective Collaborative Intrusion Detection Networks." IEEE TNSM, June 2011. https://personal.ntu.edu.sg/zhangj/paper/tnsm10.pdf . Read: search summary.
What it does: each IDS keeps a Bayesian (Dirichlet) trust score per collaborator from its own experience. Related work by the same group uses "honey" challenges with known answers to catch lying insiders.
Overlap: a H, b M, c 0, d 0, e 0, f 0, g 0.

16. Meidan, Avraham, Libhaber, Shabtai. "CADeSH: Collaborative Anomaly Detection for Smart Homes." IEEE Internet of Things Journal 2022. https://arxiv.org/abs/2303.01021 . Read: abstract.
What it does: features pooled across identical devices; autoencoder plus clustering. Claims "model poisoning mitigation" without giving a mechanism in the abstract.
Overlap: a M, b L, c 0, d 0, e L, f 0, g 0.

17. Garcia, Bessani, Gashi, Neves, Obelheiro. "OS diversity for intrusion tolerance: Myth or reality?" IEEE/IFIP DSN 2011. Journal version: Software: Practice and Experience 2013. https://openaccess.city.ac.uk/id/eprint/526/ . Read: search summary.
What it does: about 15 years of NVD data across 11 operating systems. Common vulnerabilities are rare for most OS pairs, so diverse replicas reduce shared compromise.
Overlap: not a detector. It is the empirical basis for FOA's "vulnerability-diverse peers" assumption, which matters for (b).

18. Pillutla, Kakade, Harchaoui. "Robust Aggregation for Federated Learning" (RFA). IEEE Transactions on Signal Processing 70:1142-1154, 2022. https://arxiv.org/abs/1912.13445 . Read: abstract.
What it does: approximate geometric median by smoothed Weiszfeld iterations, robust up to half of devices corrupted, at 1 to 3 times the communication of averaging.
Overlap: b H. It should be cited next to Minsker for FOA's geomedian step.

19. Recent preprints with weak evidence, listed so they are not missed:
- SecureDyn-FL, Soomro et al., arXiv 2601.06466, comment says accepted to IEEE TNSM. Server-based FL IDS on N-BaIoT with GMM/Mahalanobis "temporal gradient auditing". Overlap b M, rest low. https://arxiv.org/abs/2601.06466
- PenTiDef, Duy et al., arXiv 2602.17973 [preprint]. Blockchain-coordinated, serverless FL IDS with a latent-space (CKA plus K-Means) poisoning filter. Overlap a M, b M. https://arxiv.org/abs/2602.17973
- Sentinel, Feng, Martinez Beltran et al., arXiv 2310.08097 [preprint, venue not verified]. Decentralized FL aggregation using cosine filtering plus bootstrap validation loss. Overlap a H, b H. https://arxiv.org/abs/2310.08097
- DMAS, Singh, Roy, Agrawal, arXiv 2601.17303 [preprint, submitted to SoutheastCon 2026]. P2P agent voting on threats. The abstract gives no BFT details, dataset or attack model. https://arxiv.org/abs/2601.17303
- Vakhnovskyi, arXiv 2604.13308 [preprint]. CEA threat model naming "baseline drift poisoning", where legitimate drift gives cover for malicious drift. No defence. https://arxiv.org/abs/2604.13308

== B. Overall picture ==

- We found no prior work that combines all of: on-device adaptation from accepted samples only, peer gossip used as a reference for drift, a split of the update into a shared part and a device-only part, a growing per-cycle budget with a time-to-compromise statement, and a freeze-attack analysis. The novelty claim rests on that combination, not on any single piece.
- Consensus plus Byzantine robustness is crowded: CIoTA, BALANCE, ClippedGossip, Sentinel, Kailkhura, Fung. FOA should not claim novelty there.
- Drift plus Byzantine in the same system is thin. Alhelou 2026 is the only one we found, and it treats drifted clients as outliers to drop.
- Bounded or budgeted influence over time: per-round bounds are common (FLAME clipping, BALANCE radius, ClippedGossip). Karimireddy 2021 proves per-round bounds are not enough. We found no prior work giving an explicit time-to-compromise bound for a peer-collaborative detector.
- Freeze or availability attacks on collaborative adaptation: none of these works studies them. CIoTA only rate-limits incoming chains.
- MCU hardware: Ieropoulos 2026 (ESP32, inference only, and it argues on-device training is infeasible). FOA's centroid update is cheap enough to adapt on an ESP8266, which is a real contrast. However, see weakness W2.

== C. The 3 closest works ==

1. CIoTA / Mirsky et al. JPDC 2020
- Has, FOA lacks: a scale demonstration (48 devices). Per-device-model chains. An acceptance rule that needs a supermajority (pa%) of peers to have seen a behaviour, so a single peer cannot introduce anything new. A manufacturer-signed bootstrap block for cold start. A TrustZone discussion for key protection. A worked count of how many models an attacker must poison.
- FOA has, CIoTA lacks: tracking drift that is deliberately device-specific (CIoTA filters out anything the majority has not seen, so honest device-only drift is erased, the same problem as Alhelou). A per-cycle budget with time-to-compromise. A freeze analysis. Real network traffic with real drift (CESNET). An MCU implementation. CIoTA's own text admits it needs a large homogeneous population ("If the homogeneous population is not large enough, then consensus will never be reached"). That cuts against FOA's vulnerability-diverse setting, where peers are deliberately not identical.

2. BALANCE / Fang et al. CCS 2024
- Has, FOA lacks: a convergence proof under poisoning in convex and non-convex settings. A clean one-line acceptance rule relative to the node's own state. Peer review at a top venue.
- FOA has, BALANCE lacks: any drift handling (its radius shrinks over time, so a real shift late in deployment is rejected, which is effectively a self-inflicted freeze). The shared-vs-residual split. A growing budget (BALANCE's tolerance moves in the opposite direction). An anomaly-detection framing. Hardware.
- BALANCE is the most important baseline to add to the simulations, because reviewers will ask why FOA is needed instead of it.

3. Ieropoulos et al. IEEE IoTJ 2026
- Has, FOA lacks: more boards (count not verified), cross-device trust thresholds that isolate a bad node, and a model-hash consistency check.
- FOA has, Ieropoulos lacks: any on-device adaptation (their model is frozen after central training, so drift is not addressed at all), poisoning theory, time-to-compromise, and freeze analysis.

Runner-up: Alhelou et al. ISCAS 2026. It is the only one handling Byzantine clients and drift together, but it is server-based, has no budget, and removes drifted clients.

== D. Ideas and techniques to borrow ==

1. ALIE-style colluding attack (Baruch 2019) as the main Byzantine-peer attack in FOA's evaluation: each cycle, colluding peers propose shifts at just under z standard deviations, in a consistent direction. This is the strongest per-round attack against median plus significance gating. FOA's budget should be the reason it fails over time. Report time-to-compromise under it.
2. Frog-boiling (Chan-Tin 2009) and time-coupled attacks (Karimireddy 2021) as the motivating lineage. Karimireddy's result that "any aggregation that ignores history can be made to diverge" is the formal reason FOA's growing budget is needed. Cite both in the paper's motivation.
3. BALANCE and ClippedGossip as baselines in the existing sim harness, with paired attacker-free twins. Both are a few lines on a centroid: accept a peer if the distance is within gamma*exp(-kappa*t/T)*||mu||; clip the peer delta to a ball. Expected result to test: BALANCE fails on shared drift late in deployment.
4. Alhelou-style "drop the drifted" baseline: run Krum or outlier removal on peer proposals. This makes FOA's decomposition argument concrete: show the false-alarm cost on CESNET when honest device-only drift is treated as attack.
5. CIoTA's supermajority filter, used as an extra gate on the shared component: require the shared direction to be supported by at least pa% of peers, not just their geometric median. Also borrow its grouping idea (keep the shared reference per device class) and a signed factory bootstrap centre for cold start.
6. Reputation per peer over time (Fung 2011, Dirichlet trust; Kailkhura learned fusion weights). FOA currently treats peers symmetrically each cycle. A slow-moving trust score that down-weights peers whose proposals keep getting rejected costs a few bytes per peer on an ESP8266.
7. Honey challenges (Fung): occasionally gossip a known-benign reference vector and check that peers score it below tau. This can detect a peer whose centre has been dragged.
8. Model or firmware hash in the HMAC frame (Ieropoulos MD5 check): add a firmware/config digest to each ESP-NOW frame so peers running different detector settings are not averaged together.
9. Measure vulnerability diversity instead of assuming it (Garcia DSN 2011): for the paper, count shared NVD CVEs across the device types used (N-BaIoT device firmware families) to justify "fewer than half of peers share an exploit". This is the honest way to support the geometric-median breakdown assumption against monoculture botnets like Mirai.
10. Smoothed Weiszfeld from RFA (Pillutla 2022) for the on-board geometric median, with a fixed iteration cap, so ESP8266 timing is bounded.
11. CIoTA's growing merge interval T(m) = (1 - 2^(-lambda*m))(tmax - tmin) + tmin: a design for a growing budget that FOA can cite as a related form, while noting that CIoTA gives no bound.
12. Nguyen DISS 2020: a gateway poisoned through traffic from compromised devices. Name it explicitly as the attack FOA's accepted-sample model covers, and reproduce its gradual-injection schedule on N-BaIoT.

== E. Honest weaknesses this sweep exposes for FOA ==

W1. With 3 boards, each node has 2 peers. The geometric median of 2 points is not unique (any point on the segment between them), and its breakdown point gives no protection if 1 of the 2 peers is Byzantine. The Byzantine bound from the Minsker lemma therefore says nothing about the 3-board testbed. Say so plainly, and keep Byzantine claims to the simulations with larger N.
W2. Hardware evidence is thin compared with CIoTA (48 RPis). The latest branch RESULTS.md states "No live poisoning, decoy, or forgery trials were run". The diverse_shared_drift runs show 100% false alarms in the last 5 minutes on all three nodes, with or without peers. So hardware does not yet show FOA following shared drift. This should not be presented as hardware validation of drift tracking.
W3. Theory is "by construction" (the budget caps movement). BALANCE and ClippedGossip prove convergence or accuracy, not just safety. A reviewer will ask about liveness: how fast FOA tracks honest drift as a function of B. FOA should report time-to-track alongside time-to-compromise.
W4. The consensus plus Byzantine part is not novel. Present FOA's contribution as the decomposition, the budget and the freeze analysis on top of known robust aggregation.
W5. Ieropoulos's view that ESP32-class boards cannot train on-device is about neural networks. FOA's centroid update is much simpler, so claims should make clear the detector is a centroid, not a learned model, to avoid overclaiming "on-device learning".

Not found or unverified in this run: the MDPI IoT 2026 paper "Adaptive Federated Baseline K-Means for Lightweight IoT Intrusion Detection" (doi 10.3390/iot7030067) appeared as a search title but returned 403 and could not be confirmed. Since it is a centroid method, it is worth checking by hand. I found no V2X collaborative misbehaviour paper with a clear Byzantine-robust consensus and drift story worth including.

Local scratch (text extractions used for reading, not deliverables): /private/tmp/claude-501/-Users-rishitkamboj-Collegeactual-Study-SEM5-iot-research-project-brainstorming/4d8240d3-c477-4b31-a868-b4b7306e3e48/scratchpad/ciota/c.txt and /private/tmp/claude-501/-Users-rishitkamboj-Collegeactual-Study-SEM5-iot-research-project-brainstorming/4d8240d3-c477-4b31-a868-b4b7306e3e48/scratchpad/essex/e.txt

### Sweep drift-poison
LITERATURE SWEEP: drift adaptation and test-time adaptation under poisoning, budgeted updates, freeze attacks, shared/local decomposition, geometric-median aggregation
(Read only. Nothing in the repo was modified. Every paper below was found by web search or fetch in this run. "Abstract" means only the abstract or a summary was read. Overlap axes: a = multi-device consensus, b = poisoning or Byzantine robustness, c = drift adaptation, d = bounded or budgeted updates with time-to-compromise style guarantees, e = shared vs device-only decomposition, f = freeze-attack resistance, g = MCU hardware. Ratings are H, M, L or "-" for none.)

== A. Relevant works ==

1. Kloft, Laskov. "Security Analysis of Online Centroid Anomaly Detection." JMLR 13:3681-3724, 2012. Earlier version at AISTATS 2010. https://jmlr.org/papers/v13/kloft12b.html (arXiv 1003.0078)
What it does: bounds how far a poisoning attacker can drag an online centroid detector, for finite and infinite windows, with full or partial traffic control and a false-positive-rate constraint. Unconstrained, the attack works with a linear amount of data. With external constraints, the attacker's gain has a strict upper bound.
Overlap: a -, b H, c L (sliding-window retraining, not drift), d H, e -, f -, g -.
Already in paper/bib.tex as "kloft".

2. Bose, Lessard, Fazel, Dvijotham. "Keeping up with dynamic attackers: Certifying robustness to adaptive online data poisoning." AISTATS 2025, PMLR 258. https://arxiv.org/abs/2502.16737 (HTML read in part)
What it does: online learner theta_{t+1} = (1-eta)theta_t + eta z_t, plus a noise defense. An adaptive adversary poisons each step with probability eps, within ||z - mu||^2 <= r. A duality certificate gives an upper bound on the long-run average adversarial loss, solved as a convex program for mean estimation and hinge-loss SGD. The certificate is then used to tune eta and the defense (meta-objective: benign loss + kappa * certificate).
Overlap: a -, b H, c - (assumes a stationary distribution, no drift), d H (certified, adaptive attacker, but infinite-horizon average, not time-to-compromise), e -, f -, g -.
NOT in the current bib. This is the most important new find.

3. Rubinstein et al. "ANTIDOTE: Understanding and Defending against Poisoning of Anomaly Detectors." ACM IMC 2009. https://dblp.org/rec/conf/imc/RubinsteinNHJLRTT09 (PDF: https://ptolemy.berkeley.edu/projects/truststc/pubs/725/IMC.2009.pdf). Companion: "Stealthy poisoning attacks on PCA-based anomaly detectors," Berkeley tech report EECS-2008-73.
What it does: a boiling-frog poisoning attack on a PCA-subspace backbone detector. In the stealthy version, about 5% more volume per week over 3 weeks matched the effect of an 18% one-shot increase. Defence: robust PCA-GRID (MAD) plus a Laplace-based robust cutoff.
Overlap: a - (centralised), b H, c L, d L, e -, f -, g -. Already cited.

4. Chan-Tin, Feldman, Hopper, Kim. "The Frog-Boiling Attack: Limitations of Anomaly Detection for Secure Network Coordinate Systems." SecureComm 2009 (Springer LNICST). Extended in ACM TISSEC 2011 with Heorhiadi. https://www-users.cs.umn.edu/~hopper/frogBoiling.pdf (search snippets only)
What it does: attackers in decentralised Vivaldi stay below every outlier threshold while lying a little at a time. With 5% attackers, the median relative error reached 0.28 on PlanetLab. The journal version shows that statistical rejection of "bad" inputs fails, and so does vouching by witnesses (Veracity).
Overlap: a M (peer-to-peer coordinate consensus), b H (attack only), c -, d -, e -, f -, g -.
NOT in the bib, though it is listed in research/round3.json. The direct reviewer objection is "peer checks plus outlier gating were already shown to fail against frog-boiling." FOA's answer has to be its cumulative budget, not its per-step gating.

5. Korycki, Krawczyk. "Adversarial concept drift detection under poisoning attacks for robust data stream mining." Machine Learning 112:4013-4048 (2023; correction in vol. 113, 2024). https://arxiv.org/abs/2009.09497
What it does: a taxonomy of fake-drift poisoning (instance-based and concept-based). Fake drift can trigger needless adaptation, or slow or fully cancel real adaptation. Proposes an RBM drift detector that is robust to such poisoning, and a "relative loss of robustness" metric.
Overlap: a -, b H, c H, d -, e -, f M (states that heavy poisoning can nullify adaptation; no stop-gate analysis), g -. Already cited.

6. Balachandran. "Self-Poisoning in Adaptive Out-of-Distribution Detection: A Sharp-Threshold Theory and Certified Label-Free Calibration" (WARDEN, CDC). arXiv 2607.21673, July 2026 [preprint]. https://arxiv.org/abs/2607.21673
What it does: models memory-bank impurity as a generalised Polya urn with a sharp reproduction-number threshold. Beyond the threshold the bank is fully poisoned. A certified admission gate that reads only a frozen reserve removes the transition. A "two-world" theorem proves that one unlabelled stream cannot tell drift from contamination.
Overlap: a -, b H (self-poisoning, not strategic), c H, d M (certified gate, no time bound), e -, f M (a frozen reserve is itself a stop-style design), g -. Already cited. The abstract does not say what breaks the impossibility. FOA's claim that peers are the missing side channel is ours, not theirs.

7. Atarmla. "The Price of Self-Calibration: Exact Evidence Budgets and Manufactured Blind Sets in Adaptive Monitoring." arXiv 2609.23254, Sept 2026 [preprint]. https://arxiv.org/abs/2609.23254 (abstract)
What it does: for an online quantile tracker with gain eta, a step of height delta costs about delta/eta excess alarms, and a ramp of slope c costs c/eta. A monitor built to tolerate drift class D is blind to every fault in D minus D. For speed-bounded classes, that blind set is exactly the doubled-speed class. The windowed alarm rate fluctuates on the 1/L scale, not the binomial 1/sqrt(L). The abstract names no adversary.
Overlap: a -, b L, c H, d H (exact budget accounting), e -, f L, g -. Already cited as "selfcal". It implies FOA's B = 0.005 alarm radii/cycle defines a speed class that FOA absorbs by design.

8. Huang, Qiao, Zhang, Ye, Shang, Fu. "When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection" (RTTAD). arXiv 2605.10242, May 2026 [preprint]. https://arxiv.org/abs/2605.10242 (abstract)
What it does: test-time contrastive updates driven mainly by high-confidence pseudo-normal samples, with anomalous samples constrained. 15 tabular datasets. Contamination is accidental, not adversarial.
Overlap: a -, b L, c H, d L, e -, f -, g -. Already cited.

9. Zha, Kang, Liu, Shen, Zhang. "Navigating the Latent Manifold: Proactive Concept Drift Adaptation for Resilient NIDS" (DriftXpert). arXiv 2609.08623, Sept 2026 [preprint]. https://arxiv.org/abs/2609.08623 (abstract)
What it does: latent-manifold outlier analysis detects drift, then alignment plus selective freezing adapts without forgetting. Latency was tested on a low-end PC. No poisoning model.
Overlap: a -, b -, c H, d -, e -, f -, g L. Already cited.

10. Cong, He, Shen, Zhang. "Test-Time Poisoning Attacks Against Test-Time Adaptation Models." IEEE S&P 2024. https://arxiv.org/abs/2308.08505
What it does: surrogate-crafted poisoned test samples against TTT, DUA, TENT and RPL. With 10 poisoned samples, one model fell from 76.20% to 41.83% accuracy. No defence.
Related: Su et al., "On the Adversarial Risk of Test Time Adaptation," arXiv 2410.04682 [preprint]. Under a grey-box attacker, TTA is more robust than earlier work claimed. Already cited as su2025tta.
Overlap: a -, b H, c M, d -, e -, f -, g -. Cong et al. is NOT in the bib.

11. Golomb, Mirsky, Elovici. "CIoTA: Collaborative IoT Anomaly Detection via Blockchain." arXiv 1803.03807 (NDSS 2018 DISS workshop). Extended as Mirsky, Golomb, Elovici, "Lightweight collaborative anomaly detection for the IoT using blockchain," JPDC 145, 2020 (arXiv 2006.10587).
What it does: devices of the same type continuously train local anomaly models and share them. A new merged model is accepted only by consensus, with blockchain bookkeeping. Evaluated on 48 Raspberry Pis.
Overlap: a H, b M (consensus filters bad updates, but local training assumes benign data), c M, d -, e -, f -, g M (Raspberry Pi, not an MCU). Already cited.

12. Le, Moothedath. "Byzantine Resilient Federated Multi-Task Representation Learning" (BR-MTRL). arXiv 2503.19209, v3 Oct 2025 [preprint, venue not verified]. https://arxiv.org/abs/2503.19209
What it does: the shared representation is aggregated at a server with geometric median or Krum, while each client keeps a personal head trained locally. Tested on CIFAR-10 and FEMNIST.
Paired with: Toso, Anderson, Pinot, Gupta. "Byzantine-Robust Federated Representation Learning." arXiv 2609.36660, Sept 2026 [preprint] (abstract). Proves non-asymptotic recovery with no irreducible model-heterogeneity bias when shared and client-specific parts are separated.
Overlap: a M (server-based), b H, c -, d -, e H, f -, g -. Neither is in the bib.

13. Gaucher, Dieuleveut, Hendrikx. "Unified Breakdown Analysis for Byzantine Robust Gossip." ICML 2025, PMLR 267. https://arxiv.org/abs/2410.10418
What it does: a general framework (F-RG) for gossip with robust aggregation rules, an upper bound on the number of tolerable adversaries, and a new rule, CS+, with near-optimal breakdown. Includes a new attack tailored to decentralised communication.
Background: He, Karimireddy, Jaggi, "Byzantine-Robust Decentralized Learning via ClippedGossip," arXiv 2202.01545 [preprint]. It identifies a "dissensus" attack that exploits topology bottlenecks.
Overlap: a H, b H, c -, d L (clipping bounds per-step influence), e -, f -, g -. Not in the bib.

14. Baruch, Baruch, Goldberg. "A Little Is Enough: Circumventing Defenses For Distributed Learning." NeurIPS 2019. https://arxiv.org/abs/1902.06156
What it does: colluding workers shift their updates by a small amount within the honest spread. Krum, trimmed mean and similar rules then keep the Byzantine updates and discard honest ones. Under 25% colluders cut accuracy by 50%.
Overlap: a M, b H (attack), others -. Not in the bib. This is the aggregation-level boiling frog. FOA's geometric median has not been tested against it, as far as the repo shows.

15. Tripathi, Sharma, Mishra, Maiti. "SpectralKrum: A Spectral-Geometric Defense Against Byzantine Attacks in Federated Learning." arXiv 2512.11760, Dec 2025 [preprint]. https://arxiv.org/abs/2512.11760
What it does: estimates a benign subspace from a rolling buffer of past aggregates, runs Krum inside that subspace, and rejects candidates whose orthogonal residual energy is too high. The authors report limited benefit when attacks stay inside the subspace.
Overlap: a M (server), b H, c L, d -, e M (subspace vs orthogonal residual), f -, g -. Not in the bib.

16. Ino, Yoshida, Matsutani, Fujino. "Data Poisoning Attack against Neural Network-Based On-Device Learning Anomaly Detector by Physical Attacks on Sensors." Sensors 24(19):6416, 2024. https://pmc.ncbi.nlm.nih.gov/articles/PMC11479347/
What it does: an acoustic tone near an ADXL345 accelerometer fakes a drift. The ONLAD/OS-ELM multi-instance detector's centroid drift detector then spawns a poisoned instance, so real faults later score as normal. Hardware: Raspberry Pi Pico and Pi 4. No defence; the authors call for anti-poisoning methods for on-device learning.
Overlap: a -, b H (attack), c M (the drift mechanism is the attack vector), d -, e -, f -, g H. Probably the "sensors2024" bib key; please check.

17. Asadi, Bengu, Wulfert, Wohrle, Kellerer. "Gist: Optimizing Segmentation for Decentralized Federated Learning on Tiny Devices." FLEdge-AI '25 (MobiCom 2025 workshop), DOI 10.1145/3737899.3768527. PDF read: https://asadi.io/files/papers/NavidrezaAsadi_MobiCom2025-FLEdgeAI_Gist.pdf
What it does: decentralised FL on a physical cluster of ESP32-S3 boards, sharing parameter segments probabilistically and weighting peers by success. No Byzantine, poisoning or drift terms appear in the text.
Overlap: a H, b -, c -, d -, e L, f -, g H. Not in the bib. It is the nearest MCU-hardware precedent for gossip on boards like ours.

18. Hu, Duan. "Theory of Continual Learning Against Data Poisoning Attacks." arXiv 2606.29841, June 2026 [preprint]. https://arxiv.org/abs/2606.29841 (abstract)
What it does: models attacker and defender as an online zero-sum game. No defence succeeds when a linear fraction of tasks is poisoned with unbounded noise. Task-to-task verification works when attacks are infrequent, and a sensitivity-minimising defence works when per-attack noise is bounded.
Overlap: a -, b H, c M, d M, e -, f -, g -. Already cited as "clpoison".

Also found, lower relevance:
- Belal, Maouche, Ben Mokhtar, "GRANITE: a Byzantine-Resilient Dynamic Gossip Learning Framework," arXiv 2504.17471 [preprint]. Adapts aggregation thresholds to the estimated Byzantine density in each neighbourhood. Overlap a H, b H.
- Kravchik et al., "Can't Boil This Frog," arXiv 2002.02741 [preprint], and "Poisoning Attacks on Cyber Attack Detectors for ICS," ACM SAC 2021 (arXiv 2012.15740). Online-retrained autoencoders largely resisted poisoning. Overlap b H, c M.
- Hinder, Vaquet, Hammer, "Adversarial Attacks for Drift Detection," arXiv 2411.16591 [preprint]. Builds streams that drift without triggering common drift detectors. Overlap c H, f L.
- Hong, "The Boiling Frog Threshold," arXiv 2603.08455 [preprint]. Non-adversarial, gradual-drift blindness thresholds. Already cited in references.md.
- Seibert, Becker, Nita-Rotaru, State, "Newton Meets Vivaldi: Securing Virtual Coordinates by Enforcing Physical Laws." Only the CERIAS 2012 poster was verified (https://www.cerias.purdue.edu/symposium/posters/year/2012/CED-ACB). It defends against frog-boiling with invariants that are not learned, reporting resilience with 30% attackers.
- Takruri et al., "Online drift correction in WSNs using spatio-temporal modeling" (Univ. Melbourne record). Assumes drift is uncorrelated across neighbouring sensors, the opposite of FOA's assumption that drift is shared.
- Li, Hu, Beirami, Smith, "Ditto," ICML 2021, PMLR 139. Personal plus global models, for both robustness and fairness. Overlap e M.
- Minsker, "Geometric median and robust estimation in Banach spaces," Bernoulli 21(4), 2015. The foundation lemma; already cited.

== B. The 3 closest works ==

1. Kloft and Laskov 2012 (single-device centroid poisoning theory)
- They have and FOA lacks: an attack-optimal (greedy) analysis against the exact update rule, with the tightness of the bounds checked on real HTTP traces, and a false-positive-rate constraint on the attacker built into the bound.
- FOA has and they lack: drift tracking, peers, a shared/residual split, freeze analysis and hardware. Their model assumes the normal distribution does not move.

2. Bose et al. 2025 (certified adaptive online poisoning)
- They have and FOA lacks: a computable certificate against a fully adaptive attacker who watches the trajectory, and a principled way to pick eta and the defence strength by trading benign loss against the certificate. FOA's guarantees are "by construction" (budget times cycles) rather than a tight worst-case loss.
- FOA has and they lack: non-stationarity, multiple devices, a finite-horizon time-to-compromise view, and the freeze/liveness side.

3. CIoTA / Mirsky et al. 2020 (fleet-level collaborative IoT anomaly detection)
- They have and FOA lacks: a larger physical deployment (48 Pis versus our 3 ESP8266 boards) and a full merge-on-consensus protocol.
- FOA has and they lack: Byzantine-robust geometric-median aggregation instead of all-or-nothing consensus, budgeted device-only residuals, drift-vs-poison reasoning, explicit bounds, and MCU-class hardware.
- Close runners-up: WARDEN (2607.21673), for the drift/contamination impossibility and the certified gate, and Toso et al. / BR-MTRL, for shared-vs-local robust decomposition.

Combined verdict: we found no prior work that combines multi-device consensus, Byzantine robustness, drift adaptation, budgeted updates with time-to-compromise, a shared/device-only split and freeze resistance on MCUs. Each single ingredient has clear prior art: bounded attacker gain (Kloft), certified adaptive poisoning (Bose), robust shared-part aggregation (BR-MTRL, Toso), robust gossip (Gaucher), collaborative IoT detection (CIoTA) and MCU gossip FL (Gist). The novelty claim should be the combination and the freeze/liveness analysis, not any single component.

== C. Weaknesses this literature exposes in FOA ==

1. Three-board Byzantine bound may be vacuous. foa_rule.py and firmware/esp8266_foa/foa_core.h take the geometric median of PEER shifts only. With 3 boards each node sees K=2 peers. The geometric median of 2 points is not unique (any point on the segment between them qualifies), and with one Byzantine peer the honest share is 1/2, so Minsker's honest-majority condition fails. On the testbed, safety then rests on lambda (own-traffic agreement), the "own" common-direction mode and the budgets, not on the median lemma. Either include the device's own proposal in the median (3 points, 1 Byzantine) or state this limit plainly.

2. Small-shift (ALIE) attacks are untested. Baruch et al. show colluders that stay within the honest spread beat median-type rules. That is the aggregation-level version of frog-boiling, and the repo has no evaluation of it.

3. Frog-boiling precedent. Chan-Tin et al. showed that outlier rejection and witness vouching both fail. FOA's significance gate z and its peer agreement are of the same kind, so the defence must rest on the cumulative budget, and the paper should say so explicitly.

4. Blind set by design. Following Atarmla, any drift FOA absorbs at or below its budget speed is undetectable. The time-to-compromise bound grows linearly in distance/B, so a patient attacker still succeeds after that time. The bound is a delay, not prevention.

5. Common-mode attacks. WARDEN's two-world theorem means FOA escapes the single-stream ceiling only if attacks are not shared by an honest majority. A botnet that hits all devices at once looks like shared drift. Takruri-style WSN work assumes the reverse correlation structure, which shows the assumption is a modelling choice that needs defending.

6. Hardware evidence is thin (origin/hardware-results-20261127, FOA_floor3/experiments/hardware/RESULTS.md).
- No live poisoning, decoy or forgery trials were run.
- In both diverse_shared_drift runs (with and without peers), every node had 100% false alarms over the last 5 minutes, so the hardware does not yet show any fleet benefit.
- The "no_peers" run still logs 99.32% "both peers" on nodes 1 and 2, which should be checked.

== D. Ideas and techniques to borrow ==

1. From Bose et al.: write FOA's per-cycle update as a stochastic map and compute a duality certificate on the worst-case long-run centre offset as a function of (B, lambda, z, s0). Tune B by benign false alarms + kappa * certificate instead of by hand.
2. From Kloft and Laskov: implement the greedy optimal attack against FOA's exact rule, plot it against the time-to-compromise bound to show how tight the bound is, and consider coupling the budget to the observed alarm rate, as their false-positive constraint does.
3. From Atarmla: report FOA's "tolerated class" and blind set explicitly (speed at or below B per cycle on the residual; shared drift capped by lambda), and calibrate windowed alarm-rate checks on the 1/L scale.
4. From WARDEN and Newton: keep a small frozen reserve of calibration samples, or a fixed anchor region from invariants that are not learned. The centre may never leave it, which turns "eventual compromise" into "never beyond R_max".
5. From Gaucher et al. (CS+), ClippedGossip and GRANITE: test clipped gossip or CS+ instead of, or alongside, the geometric median, especially at small K. Adapt aggregation strength to the estimated Byzantine density among neighbours.
6. From SpectralKrum: estimate the "shared" subspace from the history of accepted consensus shifts, and use orthogonal residual energy as an extra gate before rationing the residual.
7. From Toso et al. / BR-MTRL: cite their result that separating shared and client-specific parts removes the heterogeneity bias, as theoretical support for FOA's split, and borrow the structure of their bound.
8. From Korycki and Krawczyk: report "relative loss of robustness" as a standard metric for the freeze and drift experiments.
9. From Ino et al.: add a physical, realistic attack on the boards (signal injection that fakes drift through the sensing path). Their explicit call for on-device anti-poisoning defences is a citable gap FOA can address, with honest scope.
10. From Cong et al. and Su et al.: define attacker-knowledge levels (white-box live state, grey-box initial state only) for the FOA evaluation matrix.

== E. Citations to add to paper/bib.tex (currently missing) ==
Bose et al. 2025; Chan-Tin et al. 2009/2011; Baruch et al. 2019; Gaucher et al. 2025 (plus ClippedGossip); Toso et al. 2026 [preprint] and Le and Moothedath 2025 [preprint]; Cong et al. 2024; SpectralKrum 2025 [preprint]; Gist 2025. Check that "sensors2024" is Ino et al. 2024.

### Sweep tinyml-hw
LITERATURE SWEEP: on-device learning and TinyML anomaly detection on MCUs, gossip over ESP-NOW/BLE, energy, hardware IDS testbeds, authenticated frames on MCUs
(Read only. Nothing in the repo was modified. Every item below was found by web search or fetch in this run. "Read" says how much I actually saw. Several full texts were blocked with HTTP 403, so I relied on abstracts or search snippets for those, and I say so.)

Overlap axes: (a) multi-device consensus, (b) poisoning/Byzantine robustness, (c) drift adaptation, (d) bounded/budgeted updates with time-to-compromise, (e) shared vs device-only decomposition, (f) freeze resistance, (g) MCU hardware. H/M/L = high/medium/low. "-" = none.

=== 1. WORKS FOUND ===

1. Ieropoulos, Anthi, Spyridopoulos, Burnap, Carnelli, Khan. "Federated Detection at the Edge: Collaborative Anomaly Detection for Resource-Limited IoT." IEEE Internet of Things Journal 13(11):24205-24218, 2026. DOI 10.1109/JIOT.2026.3674644. https://orca.cardiff.ac.uk/179135/ (PDF: https://orca.cardiff.ac.uk/id/eprint/179135/1/Federated_Detection_at_the_Edge__Collaborative_Anomaly_Detection_for_Resource_Limited_IoT.pdf). Peer reviewed. Read: listing and search snippets only (full text returned 403).
What it does: an autoencoder is trained centrally. Five ESP32 boards on Wi-Fi each run local inference and multicast their predictions over UDP. MD5 hashes check that all boards run the same model. A trust threshold on cross-device consistency isolates faulty or compromised nodes, with no coordinator. Snippets report 98.5% F-score, 3 ms inference and 12.7 KB memory. The authors say they are deliberately not doing federated learning, because on-device backprop does not fit an ESP32.
Overlap: a M (decision-level agreement, not model consensus), b M (flags inconsistent nodes, but MD5 is unkeyed), c -, d -, e -, f -, g H. Overall: MEDIUM-HIGH.

2. Ieropoulos, Anthi, Spyridopoulos, Burnap, Khan, Carnelli. "Empowering IoT Security: On-Device Intrusion Detection in Resource Constrained Devices." arXiv 2605.13159, 2026 [preprint]. https://arxiv.org/abs/2605.13159. Read: most of the full text.
What it does: a feasibility study on one bare-metal ESP32. It captures 24 h of the board's own MQTT traffic with scripted attacks, labels it by hand, and trains offline a decision tree (99% F1) and a small NN (96% F1). Adaptive models are listed only as future work.
Overlap: a -, b -, c -, d -, e -, f -, g H. Overall: LOW. It does show how weak the usual MCU IDS baseline is: supervised, static and single-device.

3. Manocchio, Layeghy, Portmann. "Network Intrusion Detection System in a Light Bulb." arXiv 2210.03254, 2022 [preprint]. https://arxiv.org/abs/2210.03254. Read: full text (method sections).
What it does: replaces the chip in a consumer smart bulb with an ESP8266 running an optimised decision tree. It is supervised and trained offline on ToN-IoT, BoT-IoT, MQTT-IoT-IDS2020, UNSW-NB15 and CSE-CIC-IDS2018. It notes that a previous ESP8266 deep model used nearly 100% of memory.
Overlap: g H (same chip as ours), everything else -. Overall: LOW-MEDIUM. It is the nearest ESP8266 IDS precedent, and it neither learns nor collaborates.

4. Ito, Tsukada, Matsutani. "An On-Device Federated Learning Approach for Cooperative Model Update between Edge Devices." IEEE Access, 2021 (DOI 10.1109/ACCESS.2021.3093382). arXiv 2002.12301. https://arxiv.org/abs/2002.12301. Peer reviewed. Read: full text (ar5iv).
What it does: each device runs an OS-ELM autoencoder anomaly detector and learns sequentially. Devices exchange the intermediate matrices U=H^T H and V=H^T T, add them up and recompute beta. Drift is the stated motivation. Experiments ran on a desktop with forgetting turned off (alpha=1). Exchange goes through a server. Security and poisoning are not addressed.
Overlap: a H (merges anomaly detectors across devices), b -, c M, d -, e -, f -, g L. Overall: MEDIUM.

5. Yamada, Matsutani. "A Sequential Concept Drift Detection Method for On-Device Learning on Low-End Edge Devices." arXiv 2212.09637 [preprint]. The workshop version, "A Lightweight Concept Drift Detection Method for On-Device Learning on Resource-Limited Edge Devices," appeared at PAISE 2023 according to the authors' page (https://www.arc.ics.keio.ac.jp/~matutani/papers/yamada_paise2023.pdf). An IEICE 2024 journal extension exists (Sunaga, Yamada, Matsutani). https://arxiv.org/abs/2212.09637. Read: abstract.
What it does: fully sequential drift detection paired with OS-ELM on-device learning, on a Raspberry Pi Pico (264 kB). Compared with batch detectors it uses 88.9-96.4% less memory and loses 3.8-4.3% accuracy.
Overlap: c H, g M-H, the rest -. Overall: MEDIUM.

6. Ochiai, Nishihata, Tomiyama, Sun, Esaki. "Detection of Global Anomalies on Distributed IoT Edges with Device-to-Device Communication" (WAFL-Autoencoder). ACM MobiHoc 2023 AIoT workshop. arXiv 2407.11308. https://arxiv.org/abs/2407.11308. Peer reviewed (workshop). Read: full text (HTML).
What it does: on each encounter a device pulls its weights toward its neighbours', W <- W + lambda*sum(Wk - Wn)/(|nbr|+1) with lambda=0.1, then trains locally. Thresholds are gossiped and averaged with a self-weight gamma=0.01. The paper separates "local" anomalies (rare on one device, common elsewhere) from "global" ones (rare on every device). Evaluation is simulation only (MNIST family, random-waypoint contacts). It has no adversary (only 1% dirty data) and no drift.
Overlap: a H, b L, c -, d L (lambda is a fixed step, not a budget), e M (the local/global split is conceptually close to our shared/device-only split), f -, g -. Overall: MEDIUM-HIGH conceptually.

7. Nguyen, Rieger, Miettinen, Sadeghi. "Poisoning Attacks on Federated Learning-based IoT Intrusion Detection System." NDSS DISS workshop, 2020. https://www.ndss-symposium.org/wp-content/uploads/2020/04/diss2020-23003-paper.pdf. Peer reviewed (workshop). Read: full text (sections).
What it does: attacks DIoT, an FL IDS that runs on security gateways. Compromised IoT devices, not the gateways, gradually inject malicious traffic into local training and plant a backdoor that gets past existing FL defences. The attack is parameterised by poisoned data rate (PDR), about 36.7% +/- 6.5% in one setting, and by the fraction of affected gateways (PMR). Evaluated on 46 real devices.
Overlap: a M (server aggregation), b H (it is our threat model: the attacker controls device traffic, not the learner), c L, d -, e -, f -, g -. Overall: MEDIUM.

8. Mirsky, Golomb, Elovici. "Lightweight Collaborative Anomaly Detection for the IoT using Blockchain." Journal of Parallel and Distributed Computing, 2020. arXiv 2006.10587. https://arxiv.org/abs/2006.10587. Peer reviewed. Read: abstract. This is the journal version of CIoTA, which references.md already lists.
What it does: devices update a shared model incrementally through self-attestation plus blockchain consensus. Tested on 48 Raspberry Pis.
Overlap: a H, b M, c L, d -, e -, f -, g M (Raspberry Pi, not MCU). Overall: HIGH, but already known to us.

9. Tanovic, Mezei. "Lightweight Anomaly Detection in Digit Recognition Using Federated Learning." Future Internet 17(8):343, 2025. https://www.mdpi.com/1999-5903/17/8/343 (abstract via https://econpapers.repec.org/RePEc:gam:jftint:v:17:y:2025:i:8:p:343-:d:1713577). Peer reviewed. Read: abstract.
What it does: autoencoders are trained and run on ESP32-CAM (about 12 min to train, 9 ms per inference). FL across 10 boards over Wi-Fi. When 1 to 5 of the 10 clients train on corrupted data, aggregation stays robust. The corruption is benign and there is no defence mechanism.
Overlap: a M, b L-M, c -, d -, e -, f -, g H. Overall: MEDIUM.

10. da Silva, Peixoto, Figueiredo, Prazeres. "TinyFed: Lightweight Federated Learning for Constrained IoT Devices." Internet Technology Letters 8(4), 2025. DOI 10.1002/itl2.70061. https://onlinelibrary.wiley.com/doi/full/10.1002/itl2.70061. Peer reviewed. Read: search snippets only (403).
What it does: a full FL cycle on ESP32 boards with a 4-input NN for temperature, humidity, light and voltage anomalies.
Overlap: a M (server), g H, the rest -. Overall: LOW-MEDIUM.

11. Bao, Kanjo, Banerjee, Rashid, Mohsenin. "Decentralised Resource Sharing in TinyML: Wireless Bilayer Gossip Parallel SGD for Collaborative Learning." arXiv 2501.04817 (journal-ref IEEE Pervasive Computing 2026). https://arxiv.org/abs/2501.04817. Read: full text (HTML).
What it does: two-layer gossip D-PSGD for MCUs. The paper's framing is "TinyML", but everything ran in simulation on an RTX 3070 Ti with MQTT. Its own limitations section says it lacks real edge-device tests. No Byzantine handling, no authentication, no energy.
Overlap: a M, g L. Overall: LOW-MEDIUM. Useful as a sign of how thin real MCU gossip work is.

12. Kargar, Zorbas, Gaffney, O'Flynn, Tedesco. "Concept Drift Mitigation on Resource-Constrained IoT Devices via Self-Learning." IEEE Sensors Applications Symposium (SAS), 2025. https://research.ucc.ie/en/publications/concept-drift-mitigation-on-resource-constrained-iot-devices-via-/. Peer reviewed. Read: abstract.
What it does: DL features plus K-means that self-updates from unlabelled incoming data on an MCU. Model 610 KB, under 0.6 s per sample, under 0.7 J per analysis-plus-update. Security is not mentioned, so unguarded self-learning is exactly the surface we attack.
Overlap: c H, g H, b -. Overall: MEDIUM.

13. Zewail, Ehab, Ali, Mahrous, Awad, Mokhtar. "On-Edge Acoustic Continual Anomaly Detection: A Cross-Platform Comparative Study." Accepted at JAC-ECC 2026. arXiv 2611.15465. https://arxiv.org/abs/2611.15465. Peer reviewed (conference). Read: abstract.
What it does: a TFLM encoder on ESP32-S3 and Nicla Vision, with on-device prototype learning updated by an exponential moving average. In form this is the same idea as an adapting centroid detector. No gate or guard on updates is described.
Overlap: c H, g H, the rest -. Overall: MEDIUM (closest in detector form).

14. Alsalem. "Securing AI-Driven Systems for Environmental Sustainability in IoT Applications: A Lightweight Message-Authentication Scheme Against Telemetry Poisoning." Sensors 26(19):6276, 2026. DOI 10.3390/s26196276. https://pmc.ncbi.nlm.nih.gov/articles/PMC13667637. Peer reviewed. Read: most of the full text.
What it does: HMAC-SHA256 over device ID, timestamp, monotonic counter and value, with per-device keys, on an ESP32-S3 LoRa node. A counter high-water mark gives replay protection. The paper states plainly that a sender holding a valid key cannot be told apart from the real device, so forged traffic is bounded only by the compromised devices' traffic share. The HMAC CPU time was not measured on hardware.
Overlap: b M (outsider forgery only, which is the gap FOA fills), g H. Overall: MEDIUM on the authentication axis.

15. Pearson, Luo, Zhang, Dey, Ling, Bassiouni, Fu. "On Misconception of Hardware and Cost in IoT Security and Privacy." IEEE ICC 2019. https://www.cs.uml.edu/~xinwenfu/paper/Conferences/19_ICC_OnMisconceptionofHardwareandCostinIoTSecurityandPrivacy.pdf. Peer reviewed. Read: full text, Table II.
Measured HMAC-SHA256: 182 us on ESP8266 (160 MHz) and 154 us on ESP32. ECC signature generation on ESP8266 took 2.48e5 us (about 248 ms). This is a benchmark, not a learning paper. Overall: LOW overlap, HIGH use as a reference number.

Supporting items (fewer axes, still useful):
- Nozomi Networks, "ESP-NOW Protocol Analysis and Vulnerability Research," white paper (grey literature, not peer reviewed, about 2024-2025). https://cdn.prod.website-files.com/645a4534705010e2cb244f50/67e3ab1eec0b2be8f630f641_Nozomi-Networks-WP-ESP-NOW.pdf. Read: key sections. Broadcast and multicast ESP-NOW frames carry no encryption or authentication. Built-in anti-replay is a 16-bit random "magic" value plus a cache, and they show it is exploitable. This supports FOA's choice of its own HMAC plus counter.
- Jenhani, Bensalem, Dizdarevic, Jukan. "Optimizing Split Learning Latency in TinyML-Based IoT Systems." arXiv 2507.16594 [preprint]. https://arxiv.org/abs/2507.16594. Read: abstract. On ESP32-S3, ESP-NOW gave the best end-to-end RTT of UDP, TCP, BLE and ESP-NOW, but its small payloads hurt large transfers. FOA's 92-byte frame avoids that problem.
- Ren, Anicic, Runkler. "TinyOL: TinyML with Online-Learning on Microcontrollers." IJCNN 2021. https://arxiv.org/abs/2103.08295. Read: abstract. Incremental on-device training on streams, autoencoder experiments. No attack discussion. c M, g H.
- Marinova, Pandey, Shiraishi, Vejling, Rakovic, Popovski. "Online Continual Learning for Anomaly Detection in IoT under Data Distribution Shifts" (OCLADS). arXiv 2603.07507 [preprint, submitted to EUSIPCO 2026]. https://arxiv.org/abs/2603.07507. Read: abstract. An edge server detects shift and gates updates to the on-device model, needing far fewer updates. c H, server-side, no poisoning.
- Huckelberry, Zhang, Sansone, Mickens, Beerel, Janapa Reddi. "TinyML Security: Exploring Vulnerabilities in Resource-Constrained Machine Learning Systems." arXiv 2411.07114 [preprint, submitted to Proc. IEEE]. https://arxiv.org/abs/2411.07114. Read: abstract. The abstract covers side channels, leakage and query interfaces. I did not see training-time poisoning in the abstract.
- Ochiai, Sun, Jin, Wongwiwatchai, Esaki. "Wireless Ad Hoc Federated Learning." arXiv 2205.11779 [preprint]. https://arxiv.org/abs/2205.11779. The parent of item 6. No security.
- Perrig, Szewczyk, Wen, Culler, Tygar. "SPINS: Security Protocols for Sensor Networks" (muTESLA). Wireless Networks 8, 2002. https://www.doi.org/10.1023/A:1016598314198. Outside the 2015-2026 window. I list it only as a technique: broadcast authentication from symmetric primitives with delayed key disclosure. I did not read the key-chain details in this run.

=== 2. THE THREE CLOSEST WORKS ===

A. Ieropoulos et al., IEEE IoTJ 2026 (item 1)
- What they have that FOA lacks:
  - Live attacks on real ESP32 hardware with a reported F-score. FOA's hardware branch says "No live poisoning, decoy, or forgery trials were run."
  - Five boards, against our three.
  - A decision-level peer check: devices compare predictions and isolate disagreeing nodes. FOA only exchanges centre shifts.
  - A model-consistency hash.
  - Peer-reviewed placement in a top IoT journal.
- What FOA has that they lack:
  - On-device adaptation to drift (their model is trained centrally and frozen).
  - Keyed authentication (their check is unkeyed MD5).
  - A bound on poisoning damage per cycle and a time-to-compromise.
  - Geometric-median aggregation with a Byzantine lemma.
  - The shared vs device-only split.
  - Freeze resistance (a coverage floor).

B. Ochiai et al., WAFL-Autoencoder, MobiHoc AIoT 2023 (item 6)
- What they have that FOA lacks:
  - An explicit threshold-gossip algorithm (gamma-weighted averaging of quantile thresholds).
  - A crisp local vs global anomaly definition that could sharpen how we explain our decomposition.
  - Mobility and encounter-based topologies.
- What FOA has that they lack:
  - A robust aggregator (they use a mean pull, so one Byzantine neighbour moves everyone by lambda/(|nbr|+1) of its offset per encounter, without limit).
  - A significance gate and a growing budget.
  - Any adversary model or drift.
  - Real MCUs and radios.

C. The Keio (Matsutani) line: Ito et al., IEEE Access 2021 (item 4), Yamada and Matsutani 2022/2023 (item 5), and the Sensors 2024 physical poisoning of an on-device-learning detector already in references.md
- Together this is the closest research programme to FOA's problem: cooperative on-device anomaly detectors, sequential drift detection on a Pico-class MCU, and then a demonstrated physical-sensor poisoning of that kind of learner, with the authors saying a defence specific to on-device learning is still needed.
- What they have that FOA lacks:
  - A cheap, MCU-validated sequential drift detector with measured memory savings.
  - A physical attack channel (acoustic injection into MEMS sensors), shown on real hardware.
- What FOA has that they lack:
  - Any defence. Their cooperative merge simply sums U and V, so a poisoned device's matrices enter in full.
  - Bounded updates, Byzantine-robust merging, a freeze analysis, and authenticated exchange.

Runners-up: Zewail et al. (item 13: an EMA prototype, the same detector family as ours, unguarded, on ESP32-S3) and Kargar et al. (item 12: self-learning on an MCU with measured J per update, unguarded).

=== 3. WHAT WE DID NOT FIND (in this run's searches) ===
- We found no prior work that runs Byzantine-robust aggregation (geometric median, trimmed mean or median) on MCU-class boards in a real deployment. Robust-gossip papers found (ClippedGossip arXiv 2202.01545, GRANITE arXiv 2504.17471) are simulation only.
- We found no prior work that uses ESP-NOW to exchange model or centre updates for gossip learning. Searches returned only ESP-NOW chat and sensing demos, plus the split-learning latency benchmark.
- We found no MCU learning work with budgeted or rate-limited updates and a time-to-compromise argument, and none on freeze or availability attacks against on-device adaptation.
- We found no MCU work that splits a learned update into a fleet-shared part and a device-only part. Ochiai's local/global anomaly split is the nearest idea, and it classifies anomalies rather than decomposing updates.
- Most "TinyML FL" papers use a server (TinyFed, Tanovic) or are simulated (Bao et al.).

=== 4. WEAKNESSES IN FOA EXPOSED BY THIS ANGLE (checked in the repo) ===
1. Shared key table. firmware/esp8266_foa/foa_config.h defines FOA_KEYS[N_NODES][32], and every board is flashed with all three keys so it can verify the others. So capturing one board gives the attacker every identity. The Byzantine bound counts compromised identities, so physical compromise of 1 board can become N bad peers. Alsalem (item 14) states the same limit for per-device keys. Either fix this (see 5.1) or state it in the threat model.
2. Replay window after reset. firmware/esp8266_foa/esp8266_foa.ino:48-50 accepts a lower cycle number from a sender that has been silent for PEER_RESET_MS = 60 s. An attacker who jams or out-shouts a node for 60 s can then replay its old, validly signed frames. The ESP-NOW white paper shows the built-in replay defence is weak, so this check is the only one.
3. The hardware drift result does not show tracking. On origin/hardware-results-20261127 (FOA_floor3/experiments/hardware/RESULTS.md), under shared drift, false alarms in the 10 min after the change rise to about 99-100% on all nodes, both with and without peers. Ignore-peers minus receive-peers is -2.37 pp on node 0. continued_clean also logs 100% false alarms. So the peer channel gave no measurable benefit on hardware in these short runs. This is consistent with a slow budget (B=0.005 alarm radii per cycle over about 290 cycles), but it needs to be reported as such, not as evidence that FOA adapts.
4. Energy is not separable. Board power is about 382-391 mW and dominated by Wi-Fi. FOA's per-cycle compute (step about 1.6-1.9 ms, signing about 0.6 ms, verify about 1 ms, proposal about 21.5 ms) cannot be resolved at whole-board level. Kargar et al. report J per update. We can only give an estimate (power x time) unless we add phase markers.
5. Signing cost. We measure about 596 us per frame. Pearson et al. measured 182 us per HMAC-SHA256 on an ESP8266 with a short message. Our 92-byte frame plus the portable C SHA-256 explains part of the gap. It is worth a sentence, since pairwise tags (5.1) would multiply this cost.

=== 5. IDEAS AND TECHNIQUES TO BORROW ===
1. Per-pair keys (from item 14's per-device-key reasoning, plus muTESLA as an alternative). With N=3, give each ordered pair its own key and have each frame carry N-1 truncated tags. Then a captured board can only speak as itself. Cost is about (N-1) x 0.2-0.6 ms per cycle. ECDSA is not an option on ESP8266 (about 248 ms per signature, Pearson Table II). For larger fleets, muTESLA-style delayed key disclosure gives broadcast authentication with symmetric primitives only.
2. Persistent freshness (Alsalem's high-water mark; the ESP-NOW white paper). Store an epoch counter in flash every k cycles and send epoch||cycle, so a reboot never lowers the sequence. Then remove the 60 s reset exception.
3. Decision-level peer cross-check (Ieropoulos). Add per-cycle alarm-rate or score summaries to the gossip frame. Downweight a peer whose proposed shift disagrees with its own alarm statistics. Also add a SHA-256 of the config and basis to the frame so mismatched firmware is excluded.
4. Threshold and spread gossip (Ochiai). Gossip spread and quantile estimates through the same geometric median and a gamma self-weight. Compare against our spread budget.
5. A cheap sequential drift trigger (Yamada and Matsutani; OCLADS). Use a sequential detector to decide when to open the budget faster. This targets weakness 3 without giving up the bound in the quiet state. Report the number of updates, as OCLADS does.
6. A gradual-injection attacker parameterised by PDR (Nguyen et al.). Add a PDR sweep to the simulations so our bound can be compared directly with the DIoT backdoor numbers.
7. Physical-channel poisoning as a hardware attack (Sensors 2024 line). The boards already read temperature and humidity. A heat-gun "shared drift" against a single-board "device-only poison" would be a cheap, convincing live demo, and it fills the "no live poisoning trials" gap.
8. Energy reporting. Toggle a GPIO around each FOA phase and log it next to the INA226 stream. Then report mJ per cycle for proposal, step, sign and verify separately, the way Kargar et al. give J per update. Keep the 384 mW board baseline as context.
9. Transport justification (Jenhani et al.). Cite ESP-NOW's low RTT and the fact that the 92-byte frame fits its payload limit, to justify the radio choice.

=== 6. HONESTY NOTES ===
- Read depth: full text for items 3, 4, 6, 7, 11, 15 and much of 2 and 14. Abstract or listing only for 1, 5, 8, 9, 12, 13. Snippets only for 10. Item 1's numbers (98.5%, 3 ms, 12.7 KB, five boards) come from search snippets of the paper and must be checked against the PDF before citing.
- Items 2, 3, 5 (arXiv version), 11 (arXiv version), and the OCLADS, TinyML-security and split-learning papers are preprints. The Nozomi document is a vendor white paper.
- I could not verify a claimed ACM Computing Surveys "TinyML Security" paper (DOI 10.1145/3793197) or its "fewer than 5% of TinyML papers address security" figure, so I did not use them.
- A Scientific Reports "Federated TinyML ... ICU" paper with Byzantine filtering showed up in a search, but I could not confirm its title or content, so I left it out.