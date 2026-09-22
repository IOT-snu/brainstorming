# Poison-Resilient On-Device Intrusion Detection for Drifting IoT

**Group G-04: Rishit Kamboj, Farhan Naik** · CSD457 Internet of Things · Monsoon 2026

**Method:** Threat-Orthogonal Adaptation (TOA). **Update 23 Sep:** a second research round replaced the earlier
"TimeGuard" design, which failed in simulation. See `research-findings.md` for the reasons, the new method,
and simulation results. Sections below that mention TimeGuard are kept for history.

> **One line:** An on-device IoT intrusion detector adapts to benign drift. TimeGuard checks every proposed
> update against the device's own past updates and a bounded drift budget, so a slow poisoning attacker
> cannot walk it off course. All of it runs on an ESP32 with no peers and no cloud.

---

## 1. Problem

Lightweight intrusion detectors can run on ESP32-class hardware with high accuracy [7][8][9]. But every one
of them is **trained once and frozen**, so it goes stale as normal IoT traffic drifts. Drift-adaptation
frameworks fix staleness [4][5][10][11][12], but they **commit every update without checking it**. That makes the
adaptation step an attack surface. An attacker who controls a small share of traffic can nudge "normal" a
little each cycle until a real attack looks benign. This is the boiling-frog poisoning attack, and it has
been demonstrated repeatedly [13][14][15][16].

## 2. What the literature says (28 papers deep-read; table in `literature-review.md`)

| Body of work | What it shows | What it lacks |
|---|---|---|
| On-device IDS [1][2][7][8][9] | 96-99% accuracy at KB-scale footprints, measured on ESP32 | Zero post-deployment adaptation |
| Drift adaptation [4][5][10][11][12] | ADWIN, DDM, and LE3D-style ensembles track benign drift cheaply | Updates are committed unconditionally, with no adversarial vetting |
| Poisoning of adaptation [13][14][15][16][17] | Gradual poisoning of online-retrained detectors works, even at 100% success on ONLAD | Attacks only; the ONLAD paper proposes no defense |
| Poisoning defenses [18][19][20][21] | Krum and trimmed-mean are provably robust | **Cross-client only.** They need many peer updates, and they fail against slow attackers even with peers [20] |

**The gap:** no work combines (a) single-device drift adaptation with (b) a poisoning defense that needs
**no peers**, under (c) real **microcontroller** RAM, latency, and energy limits, evaluated against (d) a
**sustained multi-cycle** attack. The attack side is covered (recent frog-boiling thesis work, [13][14]).
**Our contribution is the defense.**

## 3. Key insight (why it is not just "apply Krum")

Robust aggregation catches updates that look **inconsistent**. A well-built boiling-frog attack is
**consistent by design**: each step is tiny and smooth. The literature confirms that small, temporally
consistent deviations bypass robust aggregation. So one layer is not enough:

- **Layer 1 (TimeKrum)** catches **abrupt** poisoning: updates inconsistent with the device's own recent history.
- **Layer 2 (Drift Budget)** catches **patient** poisoning: steps that are each consistent but sum to too much displacement.

Showing that each layer fails alone and the pair holds is the core experimental result.

## 4. Research questions

- **RQ1.** Can a single device vet its own adaptation updates with no peers, using robust statistics over its own update history?
- **RQ2.** Does a cumulative drift budget stop an adaptive attacker who keeps every step within the robust gate?
- **RQ3.** What does this protection cost on an ESP32 in RAM, latency, energy, and slower adaptation to real benign drift?

**Hypothesis:** TimeGuard (L1 + L2) keeps detection of the target attack high over many poisoning cycles,
where naive adaptation collapses. It stays within ESP32 budgets and adds only a small adaptation lag on benign drift.

## 5. Method

**Features.** Kitsune/N-BaIoT damped incremental statistics [1][2]: a 23-feature subset (one decay window)
computable in O(1) memory per packet stream.

**Detector.** An OS-ELM autoencoder (ONLAD-style), chosen because it supports **cheap on-device sequential
updates** on microcontrollers. This is the same detector family the acoustic-injection attack broke [16].
Anomaly score = reconstruction error; threshold = mu + k*sigma from calibration.

**Adaptation loop.** ADWIN [4] on the anomaly-score stream. On drift, samples scored benign form a buffer,
and the device computes a **proposed update** Delta_t (OS-ELM output-weight delta plus threshold shift).
This is where poison enters.

**TimeGuard (the contribution):**
```
history H = ring buffer of last k accepted updates        (k = 8..16)
anchor A  = trusted parameters from clean calibration
budget    B(t) = B0 + rho*t   (rho = benign drift rate measured in calibration)

on proposed update Delta_t:
  # Layer 1: TimeKrum, robust consistency with own history
  s = sum of squared distances from Delta_t to its (k - f - 2) nearest in H
  if s > tau_krum: reject; flag("abrupt")        # tau from calibration percentile
  # Layer 2: Drift Budget, bounded cumulative displacement
  if ||theta + Delta_t - A|| > B(t): freeze; flag("suspected adversarial drift")
  else: commit Delta_t; push Delta_t to H
  # anchor refresh: A moves only after W consecutive clean, in-budget windows
```
Variant for the ablation: coordinate-wise trimmed mean over H instead of Krum [19].

## 6. Threat model and attack construction

- **Attacker:** controls a fraction p (1-10%) of the monitored traffic. Knows the feature extractor.
  Two variants: **oblivious** (does not know TimeGuard) and **adaptive** (knows tau_krum and keeps every step under it).
- **Goal:** make a chosen attack class (e.g. Mirai scan/flood from N-BaIoT) score as benign.
- **Construction (per cycle):** inject samples on the line from the current benign centroid toward the
  target attack, stepping by epsilon, each scored below threshold. This is the interpolation strategy
  of [13][14], ported to network-traffic features and run for N = 50-200 adaptation cycles.

## 7. Data and protocol

- **N-BaIoT** [2] (primary): 9 real IoT devices, benign plus Mirai/BASHLITE. **Natural benign drift** = a new
  device type joining the network (train on devices 1-3, stream in 4-6).
- **CICIoT2023** [22] (second): 105 devices, 33 attacks. Checks that results generalize.
- Protocol: calibrate on clean data, then stream benign drift with a poisoning campaign at rate p, and
  measure every cycle. 5 seeds, mean +/- std.

## 8. Baselines

| ID | System | Role |
|---|---|---|
| B0 | Static OS-ELM AE, no adaptation | Safe but stale |
| B1 | Naive adaptive (ADWIN + commit all), OASW/LE3D-style [10][11] | Fresh but poisonable (key contrast) |
| B2 | Frozen trusted anchor, AOC-IDS-style [5] | Existing anchor defense |
| B3 | RONI-lite (retrain with/without the batch) [18] | Classic impact-based defense |
| Ours | L1 only / L2 only / **L1+L2 (TimeGuard)** | Ablation |

## 9. Metrics

- **Primary (the headline figure):** target-attack recall and **attack success rate vs. poisoning cycles**,
  plus **cycles-to-compromise**. Expected: B1 collapses, L1 falls to the adaptive attacker, L1+L2 holds.
- **Benign drift cost:** FPR after the new-device drift, and adaptation lag (cycles to recover FPR).
- **Detection:** F1, AUROC, TPR at 1% FPR.
- **On ESP32** (micros() timing, current measurement as in [7]): RAM, flash, per-packet inference us,
  per-adaptation-cycle ms, mJ per cycle, and TimeGuard's overhead vs. B1.

## 10. Expected contribution

1. **TimeGuard:** the first peer-free poisoning defense for drift-adaptive IDS. It moves Byzantine-robust
   aggregation onto a single device's time axis and pairs it with a bounded drift budget.
2. **Evidence that one layer is not enough:** robust consistency checks miss patient, consistent poisoning.
3. **Measured ESP32 cost** of securing on-device adaptation, which no prior work reports.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| On-device OS-ELM training too heavy | Run inference + guard on ESP32; replay-feed features over serial; report both |
| Budget too tight, benign drift blocked | Sweep rho; report the security vs. adaptation-lag trade-off curve (a result in itself) |
| Attack looks staged | Follow [13][14]'s published construction; release code; test adaptive attacker |
| Scope creep | MVP = N-BaIoT + B0/B1 + L1+L2. CICIoT2023, B3, and the energy meter are stretch goals |

## 12. Plan (about 9 weeks)

| Week | Work |
|---|---|
| 1 (Sep 24) | Proposal presentation. Download N-BaIoT, build feature pipeline |
| 2 | OS-ELM AE + ADWIN loop in Python; B0 and B1 working |
| 3 | Boiling-frog attack (oblivious); show B1 collapses **(first headline result)** |
| 4 (mid-review) | Layer 1 + adaptive attacker; lit table, architecture, first plots |
| 5 | Layer 2 + ablation (L1, L2, L1+L2) |
| 6 | Port detector + TimeGuard to ESP32 (int8 / fixed point); timing |
| 7 | ESP32 RAM/latency/energy; B2, B3; CICIoT2023 if time allows |
| 8 | Seeds, sweeps (p, rho, k); final figures |
| 9 | IEEE 2-column report, code zip + README, final demo |

## What changed from the earlier framing, and why

The earlier plan claimed the **attack** as novel. A live search found it has already been demonstrated
(frog-boiling thesis work on drift-adaptive IDS, 2026; [13][14][16]). The claim now rests on the
**defense**: peer-free, two-layer, measured on an MCU. The literature shows that space is empty.
