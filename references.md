# Compiled references, newest first

36 references; **26 are from 2025 and 2026**. Built from the papers we searched for and read across three research rounds.

**How to use this list**
- *Read* shows how much of the paper we actually read. Anything marked "seen in search, not read" or "abstract" must be read before it is cited for a specific claim.
- Many 2026 entries are **preprints** (not yet peer-reviewed). Check numbers against the PDF, not against our summaries.
- The five **core** papers (cited in the proposal deck) are marked CORE.


## 2026

| Reference | Venue | Status | Read | Why it matters to us |
|---|---|---|---|---|
| [Feature-Context Consistency: Unsupervised Adversarial Detection with Drift Stability on Attributed Graphs (CB-RBM)](https://arxiv.org/abs/2610.16694) | arXiv 2610.16694 (journal-ref field says NeurIPS 2026) | preprint, venue to verify | full text | Freezes a drift-invariant score instead of adapting; its frozen baseline shows the false-alarm blow-up under drift that we measured |
| [The Price of Self-Calibration: Exact Evidence Budgets and Manufactured Blind Sets in Adaptive Monitoring](https://arxiv.org/abs/2609.23254) | arXiv 2609.23254 | preprint | seen in search, not read | Closest to our freeze-attack framing (non-adversarial trade-off between safety and recalibration). Must read before claiming the freeze attack |
| [Navigating the Latent Manifold: Proactive Concept Drift Adaptation for Resilient NIDS (DriftXpert)](https://arxiv.org/abs/2609.08623) | arXiv 2609.08623 | preprint | full text | Outlier-ratio gate for adaptation: a published gate we tested in the freeze study |
| [CAPTURE: Disentangling Preference Drift from Memory Poisoning in Personalized LLM Agents](https://arxiv.org/abs/2609.02265) | arXiv 2609.02265 | preprint | seen in search, not read | States a single-statistic dilemma (accept injected claims or reject genuine revisions) that our safety-plus-liveness goal extends |
| [Candidate Comparability Before Promotion: Conditional Validation in Adaptive Network Intrusion Detection](https://arxiv.org/abs/2609.04388) | Fernandez-Barrios et al., arXiv 2609.04388 | preprint | abstract | Server-side study of when an adaptive NIDS should accept a retrained model; no poisoning. A hold-back-until-evidence design to compare against |
| [Empirical Analysis of Evasion and Poisoning Against Malware Data Drift Detection](https://arxiv.org/abs/2608.03642) | arXiv 2608.03642 | preprint | full text | Recent evidence that drift detectors themselves can be attacked |
| [Self-Poisoning in Adaptive Out-of-Distribution Detection: A Sharp-Threshold Theory and Certified Label-Free Calibration (WARDEN, CDC)](https://arxiv.org/abs/2607.21673) | arXiv 2607.21673 | preprint | full text | Theory of self-poisoning; proves a single label-free stream cannot separate honest drift from contamination. The ceiling we must escape |
| [Theory of Continual Learning Against Data Poisoning Attacks](https://arxiv.org/abs/2606.29841) | arXiv 2606.29841 (ICML 2026 template, venue to verify) | preprint | full text | No regularised learner converges under frequent shifted poison; source of the T2T rollback gate; nearest to TOA's direction damping |
| [Rapid Poison: Practical Poisoning Attacks Against the Rapid Response Framework](https://arxiv.org/abs/2606.16242) | ICML 2026 (arXiv 2606.16242) | peer-reviewed | full text | Poisoning of an adaptation pipeline, including induced false positives; shows signatures themselves can be shaped by an attacker |
| [What changes after deployment? A survey on On-device Learning in TinyML](https://arxiv.org/abs/2605.31226) | arXiv 2605.31226 | preprint | full text | About 70 microcontroller learning works and no security mechanism: the standing gap we fill |
| [When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection (RTTAD)](https://arxiv.org/abs/2605.10242) | arXiv 2605.10242 | preprint | full text | Confident-normal-only adaptation with a stop rule; unguarded adaptation is worse than none, matching our naive result |
| [The Boiling Frog Threshold: Criticality and Blindness in World Model-Based Anomaly Detection Under Gradual Drift](https://arxiv.org/abs/2603.08455) | arXiv 2603.08455 | preprint | full text | Gradual-drift blindness in anomaly detection; related threat model |
| [ACORN-IDS: Adaptive Continual Novelty Detection for Intrusion Detection Systems](https://arxiv.org/abs/2602.07291) | arXiv 2602.07291 | preprint | full text | Closest recent continual IDS to our setting (PCA scorer, normal-only stream); no adversarial analysis |
| [Online robust covariance matrix estimation and outlier detection](https://arxiv.org/abs/2601.03957) | arXiv 2601.03957 | preprint | full text | Bounded per-point influence but unbounded influence for mean shift; no forgetting. Shows why plain robust statistics are not enough |
| [Contrastive Adversarial Agents for Intentional Drift Induction in Network Intrusion Detection Systems](https://ojs.aaai.org/index.php/AAAI-SS/) | AAAI Summer Symposium Series (SuSS) 2026 | peer-reviewed (symposium) | full text | Attacker induces drift to steer a retrained NIDS; supports our adaptive-attacker model; no defence |
| [Strategic Games and Zero Shot Attacks on Heavy-Hitter Network Flow Monitoring](https://www.ndss-symposium.org/) | NDSS 2026 | peer-reviewed | full text | Learned attackers timed to a monitor's refresh windows; basis for our pulsing-attacker test |

## 2025

| Reference | Venue | Status | Read | Why it matters to us |
|---|---|---|---|---|
| [Provably Safe Model Updates (LID)](https://arxiv.org/abs/2512.01899) | arXiv 2512.01899 (SaTML 2026 per paper notes, to verify) | preprint, venue to verify | full text | Certified box around a model's parameters; stops updating when the box empties (another stop-style design) |
| [Adversarial Habituation Attack: A Psychological Extension and Re-framing of Boiling Frog Attack](https://dl.acm.org/doi/10.1145/3719027.3760741) | ACM CCS 2025 (poster) | peer-reviewed (poster) | abstract only | Newest top-venue naming of boiling-frog and alert fatigue; read the full text before claiming the freeze framing |
| [Shift Detection and Adaptation for Network Intrusion Detection (NetSight)](https://arxiv.org/abs/2508.15100) | arXiv 2508.15100 | preprint | full text | Self-labelling drift-adaptive NIDS with permutation-test gates |
| [CITADEL: Continual Anomaly Detection for Enhanced Learning in IoT Intrusion Detection](https://arxiv.org/abs/2508.19450) | arXiv 2508.19450 | preprint | seen in search, not read | Recent continual IoT IDS; check whether it defends its own adaptation |
| [CND-IDS: Continual Novelty Detection for Intrusion Detection Systems](https://arxiv.org/abs/2502.14094) | DAC 2025 (arXiv 2502.14094) | peer-reviewed | full text | Continual IDS that refits on a held-out clean subset |
| [On the Adversarial Risk of Test Time Adaptation: An Investigation into Realistic Test-Time Data Poisoning](https://arxiv.org/abs/2410.04682) | ICLR 2025 (arXiv 2410.04682) | peer-reviewed | full text | Realistic grey-box poisoning of adaptation and the entropy-filter defence; our threat-model precedent |
| [Provably Reliable Conformal Prediction Sets in the Presence of Data Poisoning](https://arxiv.org/abs/2410.09878) | ICLR 2025 spotlight (arXiv 2410.09878) | peer-reviewed | abstract and method | Two-sided reliability (coverage and size) that models our detection-plus-false-alarm contract |
| [Adversarial Attacks for Drift Detection](https://arxiv.org/abs/2411.16591) | ESANN 2025 (arXiv 2411.16591) | peer-reviewed | abstract and method | Streams provably invisible to window-based drift monitors |
| **CORE** [CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting](https://www.nature.com/articles/s41597-025-04603-x) | Koumar et al., Scientific Data 12 (2025) | peer-reviewed | dataset paper | Core: 40 weeks of real traffic drift |
| [Network Intrusion Datasets: A Survey, Limitations, and Recommendations](https://arxiv.org/abs/2502.06688) | Computers & Security 156 (2025), arXiv 2502.06688 | peer-reviewed | abstract and key sections | Notes there is no documented public NID dataset with concept drift: why we inject drift and add CESNET |

## 2024

| Reference | Venue | Status | Read | Why it matters to us |
|---|---|---|---|---|
| [Data Poisoning Attack against Neural Network-Based On-Device Learning Anomaly Detector by Physical Attacks on Sensors](https://doi.org/10.3390/s24196416) | MDPI Sensors 24(19):6416 (2024) | peer-reviewed | full text | 100% poisoning success on an on-device learner; proposes no defence |
| [AOC-IDS: Autonomous Online Framework with Contrastive Learning for Intrusion Detection](https://arxiv.org/abs/2402.01807) | IEEE INFOCOM 2024 (arXiv 2402.01807) | peer-reviewed | full text | Online IDS with a frozen trusted anchor |

## Earlier and core

| Reference | Venue | Status | Read | Why it matters to us |
|---|---|---|---|---|
| [Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation (OWAD)](https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/) | NDSS 2023 | peer-reviewed | full text | Per-device shift detection with a permutation-test gate; public demo; a published gate to test |
| [Adversarial concept drift detection under poisoning attacks for robust data stream mining](https://arxiv.org/abs/2009.09497) | Korycki and Krawczyk, Machine Learning (Springer) 2022 | peer-reviewed | full text | Prose precedent for attacks that impair the adaptation process |
| [CIoTA: Collaborative IoT Anomaly Detection via Blockchain](https://arxiv.org/abs/1803.03807) | Golomb, Mirsky, Elovici. NDSS DISS 2018; JPDC 2020 | peer-reviewed | found in prior-art check | Closest prior art for peers as witnesses: same-firmware devices must agree before learning |
| **CORE** [N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders](https://arxiv.org/abs/1805.03409) | Meidan et al., IEEE Pervasive Computing 2018 | peer-reviewed | dataset paper | Core: real IoT traffic and Mirai/BASHLITE attacks; our data |
| **CORE** [Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection](https://arxiv.org/abs/1802.09089) | Mirsky et al., NDSS 2018 | peer-reviewed | full text | Core: our feature extraction and the online IDS idea |
| [Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent (Krum)](https://papers.nips.cc/paper/6617-machine-learning-with-adversaries-byzantine-tolerant-gradient-descent) | Blanchard et al., NeurIPS 2017 | peer-reviewed | full text | Robust filtering that needs many peers; why peer-free is hard |
| **CORE** [Security Analysis of Online Centroid Anomaly Detection](https://jmlr.csail.mit.edu/papers/volume13/kloft12b/kloft12b.pdf) | Kloft and Laskov, JMLR 13 (2012) | peer-reviewed | full text | Core: attacker share bounds poisoning; source of the alarm-rate switch-off idea |
| **CORE** [ANTIDOTE: Understanding and Defending against Poisoning of Anomaly Detectors](https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf) | Rubinstein et al., ACM IMC 2009 | peer-reviewed | full text | Core: the boiling-frog attack on network detectors and a robust-PCA defence |

## Not yet searched

Byzantine multi-sensor change detection, federated learning attacks that frame honest clients, and classic IDS alert-flooding attacks (the old Stick and Snot tools) were not searched and could hold direct precedents for the freeze attack.
