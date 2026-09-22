# Poison-Resilient On-Device Intrusion Detection for Drifting IoT

**Group G-04: Rishit Kamboj, Farhan Naik** · CSD457 Internet of Things · Monsoon 2026

---

## What we will research

We will build an **IoT intrusion detector that keeps learning on an ESP32 but cannot be taught to ignore
attacks**. Concretely, we will:

1. **Measure the risk.** Show how easily real, low-traffic IoT devices can be poisoned when their
   detector learns on the fly [2][4].
2. **Build the defense.** *Threat-Orthogonal Adaptation (TOA)*: the detector learns honest change freely,
   and rations only the change that moves it toward a known attack [1][5].
3. **Prove it for real.** Test on real IoT traffic and real long-term drift, then run it on an ESP32 and
   measure memory, latency and energy [3][4][5].

**Deliverables:** a working ESP32 detector, a new attack on existing defenses (the *freeze attack*), and
results on real data.

Everything below explains why, and how.

---

## 1. Problem

- **Detection belongs on the device.** Online anomaly detectors can run on small, cheap hardware close to
  the traffic they protect [3].
- **Normal traffic keeps changing.** Real networks drift for weeks; in 40 weeks of ISP traffic, volume
  fell 52% at semester end [5]. A frozen detector goes stale, so it must keep learning.
- **Learning is the weak point.** An attacker can feed slow, harmless-looking changes until an attack
  looks normal, the boiling-frog attack [1]. The larger the attacker's share of the traffic the detector
  learns from, the further they can push it [2].

## 2. The 5 papers we build on

| # | Paper | What it shows | What it leaves open |
|---|---|---|---|
| [1] | ANTIDOTE (ACM IMC 2009) | Boiling-frog poisoning works on network anomaly detectors; robust PCA resists it | Server-side, batch retraining, not on a device |
| [2] | Kloft & Laskov (JMLR 2012) | Poisoning power is bounded by the attacker's traffic share | Theory only; never tested on low-traffic IoT |
| [3] | Kitsune (NDSS 2018) | Online anomaly IDS light enough for small devices | Stops learning after training; no poisoning defense |
| [4] | N-BaIoT (IEEE Pervasive Computing 2018) | Real traffic from 9 IoT devices, including Mirai and BASHLITE | Offline detection; no drift, no poisoning |
| [5] | CESNET-TimeSeries24 (Scientific Data 2025) | 40 weeks of real traffic drift from 50 institutions | A dataset; not yet used to test poisoning defenses |

## 3. Research gap

On-device detectors stop learning [3], real traffic makes learning necessary [5], and the only existing
defense against boiling-frog poisoning runs on a server with batch retraining [1].
**No detector keeps adapting on a device, never freezes, and still cannot be walked toward an attack.**

## 4. Three findings that shaped the design

1. **Honest drift is directional too** [5]. "Steady drift means attack" would flag normal life. What
   separates poisoning is drift **toward an attack**, because poisoning must move "normal" toward the
   attack it wants to hide [1].
2. **Defenses that freeze can be weaponized (new).** If a defense stops learning when drift looks
   suspicious, an attacker can trip it and leave. Honest drift continues and the frozen detector drowns in
   false alarms. Our simulation (Section 8) shows this, and it broke our own earlier design.
3. **Small IoT devices are easier to poison** [2][4]. Poisoning succeeds only when the attacker is a large
   share of the training stream [2]. A smart plug sends little traffic, so matching it is easy.

## 5. Research questions

- **RQ1.** Can a detector keep learning honest drift while refusing only the part of each update that
  moves it toward a known attack?
- **RQ2.** Can an attacker turn a freezing defense into a denial of service, and does never-freezing
  adaptation prevent that?
- **RQ3.** How exposed are real low-traffic IoT devices [2][4], and what does protection cost on an ESP32?

**Hypothesis:** rationing only the threat-aligned part of each update keeps attacks visible without the
false-alarm cost of freezing.

## 6. Method: Threat-Orthogonal Adaptation

**Features.** Kitsune's damped incremental traffic statistics [3], computable in O(1) memory per stream.

**Detector.** A centre-plus-spread anomaly detector: score = distance from the learned centre divided by
the learned spread; alarm above a threshold set on clean data. It adapts both centre and spread each
cycle from the traffic it judges normal. This is the model family that poisoning exploits [1][2].

**TOA update rule.** Each proposed update is split in two:

- **Safe part** (sideways or away from known attacks): always applied, so the detector never freezes.
- **Threat part** (shrinks the margin between normal and a known attack signature): capped by a slow
  budget learned from clean data.

```
margin(mu, s)   = ||a - mu|| - tau * s          # gap between attack signature a and the envelope
allowed_loss(t) = B0 + rho * t                   # rho learned from clean drift
propose (mu', s') from the self-labelled batch
if margin0 - margin(mu', s') > allowed_loss(t):
    remove the part of (mu' - mu) pointing toward a       # keep sideways and away movement
    cap s' so the margin loss stays within allowed_loss(t)
apply (mu', s')                                          # never freeze
```

**Guarantee.** By construction the margin never falls below `margin0 - (B0 + rho t)`, so a known attack
stays detected for at least `t* = (margin0 - B0) / rho` cycles, whatever the attacker does.

**ESP32 cost.** One dot product and one norm per known attack signature per update.

## 7. Threat model, data and protocol

- **Attacker:** controls a share p of the traffic the detector learns from (swept from 10% to 60%),
  knows the features, and places poison just inside the boundary, toward the target attack [1].
- **Target attacks and IoT traffic:** N-BaIoT [4], using each device's real traffic rate to set a
  realistic p.
- **Real benign drift:** CESNET-TimeSeries24 [5], replayed as the drift the detector must follow.
- **Freeze attack (RQ2):** the attacker pushes until a freezing defense trips, then leaves.
- **Protocol:** calibrate on clean data, stream drift plus poisoning, measure every cycle, 5 seeds.

## 8. Baselines and metrics

**Baselines:** static detector [3]; naive adaptive (commits every update, the setting poisoned in [1]);
freeze budget; robust outlier filter [1]; ANTIDOTE robust PCA [1].

**Metrics:** attack recall and cycles to compromise (headline); false-alarm rate under drift; F1 and
AUROC; ESP32 memory, per-packet latency, per-update latency and energy.

**Preliminary result (our synthetic simulation, `experiments/sim_toa.py`, 5 seeds, attacker at 40%):**

| Policy | Attack recall at end | False alarms (last 50 cycles) |
|---|---|---|
| Naive adaptive | 0% (compromised at cycle 24) | 0.0% |
| Robust consistency filter | 100% | 84.7% |
| Freeze budget | 100% | 86.8% (never recovers after the attacker leaves) |
| **TOA (ours)** | **100%** | **0.3%** |

At a 10 to 20% attacker share, even naive adaptation survives, consistent with [2]. This is synthetic data;
the real test is Section 7.

## 9. Expected contribution

1. **Threat-Orthogonal Adaptation:** an on-device update rule that never freezes, rations only
   threat-aligned drift, and gives a provable minimum time to compromise.
2. **The freeze attack:** a new attack on defenses that stop learning under suspicion, and evidence that
   never-freezing adaptation is immune.
3. **Real exposure and cost:** how poisonable real low-traffic IoT devices are [4], and what protection
   costs on an ESP32.

## 10. Honest limits

- TOA protects attacks with a known signature. Zero-day protection is open; we will test directions
  learned from the detector's own alarms.
- If honest drift really moves toward an attack, TOA slows learning in that direction (in simulation,
  false alarms peaked near 7% and recovered).
- Results so far are synthetic.

## 11. Plan

| Weeks | Work |
|---|---|
| 1 to 3 | N-BaIoT pipeline, attack, baselines |
| 4 (mid-review) | Real-data version of the preliminary result |
| 5 to 7 | ESP32 port; freeze attack study; CESNET drift |
| 8 to 9 | Sweeps, IEEE 2-column report, code and demo |

## References

1. B. I. P. Rubinstein, B. Nelson, L. Huang, A. D. Joseph et al., "ANTIDOTE: Understanding and Defending
   against Poisoning of Anomaly Detectors," *ACM Internet Measurement Conference (IMC)*, 2009.
2. M. Kloft and P. Laskov, "Security Analysis of Online Centroid Anomaly Detection," *Journal of Machine
   Learning Research*, 2012.
3. Y. Mirsky, T. Doitshman, Y. Elovici and A. Shabtai, "Kitsune: An Ensemble of Autoencoders for Online
   Network Intrusion Detection," *NDSS*, 2018.
4. Y. Meidan, M. Bohadana, Y. Mathov et al., "N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using
   Deep Autoencoders," *IEEE Pervasive Computing*, 2018.
5. J. Koumar, K. Hynek, T. Čejka and P. Šiška, "CESNET-TimeSeries24: Time Series Dataset for Network
   Traffic Anomaly Detection and Forecasting," *Scientific Data*, 2025.

*Wider reading (28 papers) is in `literature-review.md`; the reasoning behind the design change is in
`research-findings.md`.*
