# CSD457 IoT — Research Project Proposal

## Title
**Poison-Resilient On-Device Intrusion Detection for Drifting IoT**
*(A drift-adaptive TinyML detector on an ESP32 that resists attackers who slowly poison its own adaptation.)*

> Group G-04. Rishit Kamboj and Farhan Naik.
> Aligns with the instructor's research areas: **IoT Network Security (attack detection)** and
> **Edge Intelligence for Resource-Constrained Systems**.

---

## 1. Problem Statement
A practical defense for IoT devices is an **anomaly-based intrusion detector that runs on the device
itself** (fast, private, no cloud). To stay accurate, that detector has to **adapt**, because a device's
normal behavior drifts over time (firmware updates, new apps, changing usage). But adaptation opens a
door: if the detector updates itself from live, unlabeled traffic, an attacker can feed it **tiny, slow
changes** that look like ordinary drift, walking the notion of "normal" until a real attack no longer
looks abnormal. This is a **data-poisoning attack on the adaptation itself** (a "boiling-frog" attack).
A static detector avoids it but goes stale; a naive adaptive one stays fresh but is poisonable.

## 2. Existing Work & Research Gap
- On-device anomaly IDS (e.g., **Kitsune**, **N-BaIoT**) are typically **static**: accurate at first,
  then decay as behavior drifts.
- Concept-drift methods (**ADWIN**, **Page-Hinkley**) adapt well, but assume a server's resources and
  **trust their own updates**, so they are exposed to slow poisoning.
- Poisoning / robust-learning work exists mostly for **large offline or server-side** models, not for a
  microcontroller running an **unsupervised, self-adapting** detector under tight memory and energy limits.

**Gap:** There is no **lightweight on-device detector that adapts to *benign* drift while resisting
*adversarial* drift**, and no measured account of what that resilience costs on a real ESP32.

## 3. Research Question
> *Can an unsupervised on-device detector adapt to benign concept drift while resisting slow data-
> poisoning of its own updates, and still fit an ESP32's memory and energy budget?*

## 4. Hypothesis
A **robust update guard** (rate-limited adaptation, trimmed statistics, and an anchor to a trusted
baseline) lets the detector follow benign drift yet **rejects the boiling-frog attack**, keeping
detection high at a small, measurable on-device cost.

## 5. Proposed Approach / Methodology
1. **Detector:** a tiny unsupervised model (int8 autoencoder in TFLite Micro, or streaming Half-Space
   Trees) over lightweight streaming traffic features (packet sizes, inter-arrival times, protocol counts).
2. **Adaptation:** online concept-drift tracking (ADWIN / Page-Hinkley) on the anomaly-score stream.
3. **The attack (what we build):** a boiling-frog poisoning attack that slowly shifts "normal" so a
   target attack evades detection. We quantify how far a naive adaptive detector can be walked.
4. **The defense (the new part):** a robust update guard that separates benign drift from adversarial
   drift (bounded update rate, trimmed/median stats, trusted anchor, anti-collapse checks).
5. **Proof on hardware:** deploy on the ESP32 and measure the real cost of the defense.

## 6. Platform / Tools
- **Hardware:** ESP32 (on-device detector, defense, and measurements).
- **Software:** Python (offline training and attack simulation), TensorFlow Lite Micro (deployment),
  river / scikit-learn (streaming, drift, baselines).

## 7. Datasets (public)
- **CIC-IoT-2023** — large modern IoT attack dataset.
- **N-BaIoT** — per-device benign vs. botnet (Mirai / BASHLITE) traffic.
- **TON_IoT** — telemetry plus network with temporal structure.
- **Drift and attack construction:** compose benign traffic across periods for natural drift, then inject
  the boiling-frog poisoning as slow, attacker-controlled drift. Document the protocol.

## 8. Baselines
1. **Static detector** (no adaptation) — stale but unpoisonable.
2. **Naive adaptive detector** (drift adaptation, no defense) — fresh but poisonable. The key contrast.
3. **Periodic full retrain** — the heavy cloud approach.
4. (Reference) **Kitsune-style** ensemble.

## 9. Evaluation Metrics
- **Detection quality:** recall, precision, F1, AUROC / AUPRC on real attacks.
- **Benign-drift stability:** false-positive rate over time as normal drifts.
- **Attack resilience (primary novelty):** poisoning attack-success rate, decision-boundary shift under
  attack, and detection retained under attack (naive adaptive vs. ours).
- **On-device cost:** RAM footprint, inference and update latency, energy per inference, model size.

## 10. Expected Contribution
1. A demonstration that **self-adapting on-device IDS are poisonable** by slow, drift-shaped attacks.
2. A **lightweight defense** that keeps the benefits of adaptation while resisting the attack, running
   inside an ESP32.
3. The **measured security-vs-cost tradeoff** of this defense on real hardware. This attack-plus-defense
   form is what takes the work to A/A* conference or Q1 level.

---

## Papers to read (target: 5 recent + these anchors — verify each before citing)
- Mirsky et al., *Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection*, NDSS 2018.
- Meidan et al., *N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders*, IEEE Pervasive Computing 2018.
- Gama et al., *A Survey on Concept Drift Adaptation*, ACM Computing Surveys 2014.
- Bifet & Gavalda, *Learning from Time-Changing Data with Adaptive Windowing (ADWIN)*, SDM 2007.
- Neto et al., *CICIoT2023*, Sensors 2023 (dataset paper).

Then add **2-3 recent (2022-2025)** papers on *poisoning / robust online learning* and *on-device or
TinyML intrusion detection*. These pin the exact gap: robust adaptation on a microcontroller.

---

## Risks & Mitigations
- **Attack looks staged** → define a clear, realistic threat model (attacker can inject traffic the
  detector may learn from) and document the boiling-frog schedule honestly.
- **ESP32 too weak for detector plus defense** → run on replayed features, or use lighter models
  (Half-Space Trees); report measured RAM / latency / energy to prove feasibility.
- **Scope creep** → fix 2 datasets, 3 baselines, 1 attack model, 1 defense for the first iteration.

## Deliverable timeline
- **Sep 24 — First Presentation (Proposal):** lit review, research gap, proposed idea.
- **Mid-review:** problem and RQ, literature table, architecture, baselines and attack defined, first results.
- **Final:** full system, IEEE 2-column report, code .zip with README.
