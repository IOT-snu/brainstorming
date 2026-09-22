# Literature Review: Poison-Resilient On-Device IDS for Drifting IoT

Built from a 10-topic search (78 papers found, 28 deep-read from full text where accessible).
Venues were checked against the fetched pages. **Preprints are marked**; prefer peer-reviewed
entries when choosing the 5 papers for the presentation.

**Suggested 5 for the proposal slides:** [1] Kitsune, [5] AOC-IDS, [14] Can't Boil This Frog,
[16] ONLAD poisoning, [21] Krum. Together they cover detector, adaptation, attack, attack on MCU-style learning, and defense.

## A. On-device / lightweight IDS (static, no adaptation)

| # | Paper | Venue | Takeaway for us |
|---|---|---|---|
| 1 | Mirsky et al., *Kitsune: An Ensemble of Autoencoders for Online NIDS* | NDSS 2018 | Source of our incremental features; the detector freezes after training |
| 2 | Meidan et al., *N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders* | IEEE Pervasive Computing 2018 | Primary dataset; 9 real devices, so device heterogeneity gives natural drift |
| 7 | *Intrusion Detection on Resource-Constrained IoT Devices with Hardware-Aware ML and DL* | IEEE ETECOM 2025 (arXiv 2512.02272) | ESP32 measurement protocol for RAM, latency, and power |
| 8 | *Empowering IoT Security: On-Device Intrusion Detection in Resource Constrained Devices* | arXiv 2605.13159 **(preprint)** | ESP32 nested-if codegen + micros() timing harness |
| 9 | *Network Intrusion Detection System in a Light Bulb* | ITNAC 2022 | NIDS on a smart-bulb MCU: shows feasibility, no adaptation |

## B. Concept-drift detection and adaptation

| # | Paper | Venue | Takeaway |
|---|---|---|---|
| 4 | Bifet & Gavaldà, *Learning from Time-Changing Data with Adaptive Windowing (ADWIN)* | SDM 2007 | Our drift trigger; its own theory shows slow drift is detected late, which is exactly what the attacker exploits |
| 12 | Gama et al., *Learning with Drift Detection (DDM)* | SBIA 2004, LNAI 3171 | Classic sequential drift test |
| 10 | Yang & Shami, *A Lightweight Concept Drift Detection and Adaptation Framework for IoT Data Streams (OASW)* | IEEE IoT Magazine 2021 | Threshold-gated retrain; commits updates unchecked (baseline B1) |
| 11 | *LE3D: A Lightweight Ensemble Framework of Data Drift Detectors for Resource-Constrained Devices* | IEEE CCNC 2023 | Cheap drift ensemble on constrained devices; no poisoning defense |
| 5 | Zhang et al., *AOC-IDS: Autonomous Online Framework with Contrastive Learning for IDS* | IEEE INFOCOM 2024 | Frozen trusted anchor (baseline B2) |
| 6 | *CND-IDS: Continual Novelty Detection for IDS* | DAC 2025 | Continual IDS with clean-subset refit; no adversarial vetting |
| 23 | *Learn to Adapt: Robust Drift Detection in Security Domain* | Computers & Electrical Engineering 2022 (Q1) | Robust drift detection for security data |
| 24 | *Hybrid IDS with Real-Time Concept Drift Detection for Enhanced IoT Security* | Sensors 2026 | Drift monitoring only, no retraining |

## C. Poisoning of adaptive / online detectors (attack side, already demonstrated)

| # | Paper | Venue | Takeaway |
|---|---|---|---|
| 13 | Kravchik et al., *Poisoning Attacks on Cyber Attack Detectors for ICS* | ACM SAC 2021; extended in Computers & Security 2022 | Interpolation-based gradual poisoning; we port the construction |
| 14 | *Can't Boil This Frog: Robustness of Online-Trained Autoencoder Anomaly Detectors to Adversarial Poisoning* | arXiv 2002.02741 **(preprint)** | Boiling-frog attack on online autoencoders |
| 15 | Korycki & Krawczyk, *Adversarial Concept Drift Detection under Poisoning Attacks* | Machine Learning (Springer) 2023 | Robust drift *detection*; desktop RBM, not an adaptation gate |
| 16 | *Data Poisoning Attack against NN-Based On-Device Learning Anomaly Detector by Physical Attacks on Sensors* | Sensors 2024 | 100% success against ONLAD (our detector family); **proposes no defense** |
| 17 | *PACOL: Poisoning Attacks Against Continual Learners* | arXiv 2311.10919 **(preprint)** | Poisoning continual learners |
| 25 | *Robustness Analysis of ML Models for IoT IDS Under Data Poisoning* | arXiv 2604.14444 **(preprint)** | Offline poisoning of IoT IDS |
| n/a | UMass Dartmouth thesis talk, *Frog-Boiling Poisoning Against Drift-Aware Continual Learners* (Aug 2026) | Thesis (not published) | **Closest prior work:** same attack on an SSF-adaptive IDS autoencoder. Attack-focused, not an MCU defense. We cite it to position our work |

## D. Poisoning defenses (all cross-client or offline)

| # | Paper | Venue | Takeaway |
|---|---|---|---|
| 21 | Blanchard et al., *Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent (Krum)* | NeurIPS 2017 | Basis of TimeKrum; needs n peers, we use our own history instead |
| 19 | Yin et al., *Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates* | ICML 2018 | Coordinate-wise median / trimmed mean (ablation variant) |
| 18 | Nelson et al., *Exploiting Machine Learning to Subvert Your Spam Filter* (RONI) | USENIX LEET 2008 | Impact-based defense; blind to low-impact distributed poison (baseline B3) |
| 20 | Zhang et al., *Poisoning Attacks on Federated Learning-based IoT IDS* | DISS workshop @ NDSS 2020 | Cross-client defenses fail against slow attackers **even with peers**, which motivates Layer 2 |

## E. Datasets

| # | Paper | Venue |
|---|---|---|
| 22 | Neto et al., *CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT* | Sensors 2023 |
| 3 | Alsaedi et al., *TON_IoT Telemetry Dataset* | IEEE Access 2020 |

## How it fits together

```
 static on-device IDS [1,2,7,8,9]  --- stale ---->  drift adaptation [4,5,6,10,11,12]
                                                            |
                                                  commits updates unchecked
                                                            v
                                     boiling-frog poisoning works [13,14,16, thesis]
                                                            |
                               existing defenses need peers [18,19,20,21]
                                                            v
                   GAP: peer-free defense on one MCU  -->  TimeGuard (ours)
```
