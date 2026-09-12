# CSD457 IoT — Research Project Proposal

## Title
**Drift-Aware On-Device Intrusion Detection for Resource-Constrained IoT Devices**
*(Keeping false alarms low as "normal" behavior changes over time — entirely on an ESP32)*

> Maps to suggested Topic #4. Aligns with the instructor's research areas: **IoT Network Security
> (attack detection)** and **Edge Intelligence for Resource-Constrained Systems**.

---

## 1. Problem Statement
IoT devices are attractive attack targets (Mirai-style botnets, etc.). A practical defense is an
**anomaly-based intrusion detector that runs on the device itself** (no cloud dependency, low latency,
privacy-preserving). But an IoT device's *normal* behavior is **not static** — it drifts over time
(firmware updates, new legitimate apps/devices on the network, seasonal/usage changes, changing network
conditions). A detector trained once and frozen sees this drift as "anomalous," so its **false-positive
rate (FPR) climbs over time → alarm fatigue → the IDS gets ignored.** Continuously retraining in the
cloud is expensive, privacy-invasive, and too heavy for a microcontroller.

## 2. Existing Work & Research Gap
- On-device / lightweight IoT anomaly IDS (e.g., autoencoder-based like **Kitsune**, **N-BaIoT**)
  are typically **trained once and static** — they don't adapt to concept drift.
- The **concept-drift** literature (ADWIN, Page-Hinkley, adaptive windowing) handles drift well, but
  those methods are usually studied on servers and are **too heavy (memory/compute) for an ESP32**.
- Most IoT-IDS papers optimize **detection accuracy**, and under-report **FPR stability under drift**
  and **real on-device cost** (RAM, latency, energy).

**Gap:** There is no well-characterized **lightweight, label-free, drift-aware anomaly IDS that keeps
FPR low and stable under concept drift *within* ESP32 memory/energy limits.**

## 3. Research Question
> *Can an unsupervised, on-device detector keep its false-positive rate low as normal IoT behavior
> drifts over time, within an ESP32's memory and energy limit — without cloud retraining or labels?*

## 4. Hypothesis
A **lightweight drift-adaptation layer** (a concept-drift signal on the anomaly-score stream +
adaptive decision threshold + guarded incremental update on confidently-benign samples) will maintain
**lower and more stable FPR under drift** than a static detector, at **comparable detection rate**,
while **fitting ESP32 RAM/energy budgets**.

## 5. Proposed Approach / Methodology
1. **Features (ESP32-feasible):** incremental per-flow/packet statistics (packet-size stats,
   inter-arrival times, protocol counts) — Kitsune-style streaming features.
2. **Base detector (tiny, unsupervised):** small int8 autoencoder (TFLite Micro) **or** a lighter
   streaming method (Half-Space Trees / streaming iForest) — chosen to fit ESP32.
3. **Drift-adaptation layer (the novelty):** run a drift detector (Page-Hinkley / ADWIN-lite) on the
   anomaly-score stream; when drift in *benign* behavior is detected, **adapt the threshold** and do a
   **small, guarded incremental update** on high-confidence-benign samples (with anti-poisoning guards).
4. **Deploy on ESP32** and measure real cost (RAM, latency, energy).

## 6. Platform / Tools
- **Hardware:** ESP32 (on-device detector + measurements).
- **Software:** Python (offline training/eval), TensorFlow Lite Micro (deployment), scikit-learn /
  river (streaming/drift) for baselines.
- Optional: Wokwi / real traffic replay for the on-device demo.

## 7. Datasets (public)
- **CIC-IoT-2023** — large modern IoT attack dataset.
- **N-BaIoT** — per-device benign vs. botnet (Mirai/BASHLITE) — great for per-device on-device modeling.
- **TON_IoT** — telemetry + network with temporal structure.
- **Kitsune / Mirai** capture — natural reference for the autoencoder baseline.
- **Drift construction:** compose benign traffic from different periods/conditions to create controlled
  concept drift, then measure FPR over time (standard practice in the drift literature — document it).

## 8. Baselines
1. **Static autoencoder / one-class detector** (no adaptation) — the standard on-device approach.
2. **Periodic full retrain** — approximates the cloud/oracle upper bound.
3. **Fixed-threshold** naive detector.
4. (Reference) **Kitsune-style** ensemble.

## 9. Evaluation Metrics
- **Primary:** FPR over time / **FPR stability under drift** (the core claim).
- **Detection:** TPR/recall, precision, F1, AUROC / AUPRC on attacks.
- **Systems (on ESP32):** RAM footprint (KB), inference latency (ms), **energy per inference (mJ)**,
  model size (KB), adaptation overhead.
- **Robustness:** performance across drift rates; resistance of the incremental update to poisoning.

## 10. Expected Contribution
A **lightweight, label-free, drift-aware on-device IDS** that keeps FPR **low and stable under concept
drift** within ESP32 limits — shown to beat static on-device detectors on FPR-under-drift at comparable
detection, and an **empirical characterization of the accuracy–memory–energy–drift trade-off on real
hardware.** This is the shape/level of an IoT-J / IoTDI / SenSys-workshop contribution.

---

## Papers to read (target: 5 recent + these anchors — verify each before citing)
Anchors (classics — confirm details):
- Mirsky et al., *Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection*, NDSS 2018.
- Meidan et al., *N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders*, IEEE Pervasive Computing 2018.
- Gama et al., *A Survey on Concept Drift Adaptation*, ACM Computing Surveys 2014.
- Bifet & Gavaldà, *Learning from Time-Changing Data with Adaptive Windowing (ADWIN)*, SDM 2007.
- Neto et al., *CICIoT2023*, Sensors 2023 (dataset paper).

Then add **2–3 recent (2022–2025)** papers on *on-device / TinyML IDS* and *drift-aware IDS for IoT*
(IEEE IoT-J, IoTDI, SenSys/EWSN, ACM). These pin down the exact gap you're filling.

---

## Risks & Mitigations
- **ESP32 too weak for live model + drift** → run detector on replayed features on-device; or use a
  lighter model (Half-Space Trees); report measured latency/RAM/energy to prove feasibility.
- **No naturally-drifting labeled data** → construct controlled drift by mixing benign distributions
  over time; document the protocol.
- **Scope creep** → freeze 1–2 datasets, 3 baselines, 1 drift mechanism for the first iteration.

## Deliverable timeline
- **Sep 24 — First Presentation (Proposal):** lit review + research gap + proposed idea (this doc → slides).
- **Mid-Review:** problem/RQ, literature table, architecture, baselines defined, initial results/plan.
- **Final:** implementation, results, IEEE 2-column report + code .zip + README.
