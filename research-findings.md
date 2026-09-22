# Research Findings: From TimeGuard to Threat-Orthogonal Adaptation

Second research round, 23 Sep 2026. Targeted searches, source checks, and a simulation.
This document explains **why the design changed** and what is genuinely new.

## 1. A correction: peer-free defenses already exist

**ANTIDOTE** (Rubinstein, Nelson, Huang, Joseph et al., ACM IMC 2009) studied boiling-frog poisoning of
the PCA-subspace anomaly detector on backbone networks and defended it with robust PCA on a single model.
So "a peer-free defense against boiling-frog poisoning" is **not new**. Our first 78-paper sweep missed it.
The deck's earlier novelty claim was removed.

What ANTIDOTE does not cover: continuous adaptation to honest drift, microcontroller constraints, and
defenses that must keep learning without freezing. That is where we now aim.

## 2. Three findings that shaped the new design

### Finding 1: honest drift is directional too
CESNET-TimeSeries24 (Koumar et al., *Scientific Data* 2025) gives 40 weeks of real ISP traffic from 50
institutions. An analysis of it ([drift-aware-nids](https://github.com/Amirikiarash/drift-aware-nids))
shows systematic drift around the academic calendar, with **mean volume down 52% at semester end** and
significant shifts in 33 of 39 weeks. So a rule like "steady, one-directional drift means an attack"
would flag normal life. **Direction alone cannot separate honest drift from poisoning. Direction relative
to a known attack can:** poisoning must move "normal" toward the attack it wants to hide, while honest
drift can go anywhere.

### Finding 2: defenses that freeze can be weaponized (new, as far as we found)
Many defenses stop adapting when drift looks suspicious (our own earlier Layer 2 did). An attacker can
trip that freeze and leave. Honest drift continues, the frozen detector's false alarms climb, and
operators eventually turn it off. Searches for this attack on drift adaptation found no prior naming or
study. It also broke our own earlier TimeGuard design in simulation.

### Finding 3: small IoT devices are easier to poison
Kloft and Laskov (*JMLR* 2012, "Security Analysis of Online Centroid Anomaly Detection") show the
attacker's displacement of an online centroid detector is bounded by their share of the training
stream. Our simulation matches: at 10 to 20% of traffic the honest majority pulls the detector back; at
**30% or more, naive adaptation is compromised in 22 to 27 cycles**. Backbone detectors (ANTIDOTE's
setting) see huge volumes, but a smart plug sends little, so an attacker can easily be a large share.
Open-source ESP32 intrusion detectors already relearn a rolling mean-plus-stddev baseline with no
poisoning protection (e.g. [MashhudFarah/WIDS](https://github.com/MashhudFarah/WIDS), 20-sample
rolling window).

## 3. The method: Threat-Orthogonal Adaptation (TOA)

Each proposed update to the detector (centre and spread) is split in two:

- **Safe part:** everything that moves the envelope sideways or away from known attack signatures.
  Always applied, so the detector keeps up with honest drift and **never freezes**.
- **Threat part:** anything that shrinks the margin between the normal envelope and a known attack.
  Allowed only up to a slow budget `B0 + rho * t`, with `rho` learned from clean data.

```
margin(mu, s)   = ||a - mu|| - tau * s          # distance from attack signature a to the envelope
allowed_loss(t) = B0 + rho * t
propose (mu', s') from the self-labelled batch
if margin0 - margin(mu', s') > allowed_loss(t):
    remove the component of (mu' - mu) pointing toward a      # keep sideways/away movement
    cap s' so margin0 - margin(mu', s') <= allowed_loss(t)    # spread may not swallow the attack
apply (mu', s')                                               # never freeze
```

**Certificate.** By construction `margin(t) >= margin0 - (B0 + rho t)`, so a known attack's centre stays
outside the envelope for at least `t* = (margin0 - B0) / rho` cycles (678 in the simulation), whatever
the attacker does. Related theory: Bose et al., "Keeping up with dynamic attackers: certifying robustness
to adaptive online data poisoning", AISTATS 2025 (mean estimation and classification, not IDS).

**Cost on an ESP32:** one dot product and one norm per known attack signature per update.

## 4. Simulation (synthetic, 5 seeds): `experiments/sim_toa.py`

Detector: centre + spread (the rolling mean/stddev family). Attacker: 40% of traffic, poison placed just
inside the boundary toward the attack. Honest drift: 5 units over cycles 60 to 140.

| Scenario | Policy | Attack recall at end | False alarms (last 50 cycles) |
|---|---|---|---|
| A: attacker never stops | Naive adaptive | **0%** (compromised at cycle 24) | 0.0% |
| | Consistency gate (Krum-style over own history) | 100% | **84.7%** |
| | Freeze budget | 100% | **86.8%** |
| | **TOA** | **100%** | **0.3%** |
| B: attacker trips the freeze, leaves at 45 | Freeze budget | 100% | **86.8%, never recovers** |
| | **TOA** | **100%** | **1.3%** |
| C: honest drift heads toward the attack (worst case) | Freeze budget | 100% | 41.3% |
| | **TOA** | **100%** | **1.2%** (peaks near 7% during drift) |

Figures: `experiments/toa_results.png` (all scenarios), `experiments/fig_slide.png` (deck).

**Honest limits**
- Synthetic data. The real test is N-BaIoT (with real per-device packet rates) and CESNET drift.
- TOA needs a signature (direction) for the attacks it protects. Zero-day protection is open; we will try
  directions learned from the detector's own alarms.
- If honest drift really does move toward an attack, TOA slows adaptation along that direction (scenario C).

## 5. What is new, stated carefully

1. **TOA:** rationing only the threat-aligned component of a continuously adapting on-device detector,
   with a closed-form minimum time to compromise. Not found in our searches; ANTIDOTE (robust PCA, server,
   batch) and robust aggregation (peers) are different mechanisms.
2. **The freeze attack** on defenses that stop adapting. Not found named or studied.
3. **IoT-specific exposure:** measuring how poisonable real low-traffic devices are, using real rates.

## Sources
- Rubinstein et al., ANTIDOTE, ACM IMC 2009: https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf
- Kloft and Laskov, Security Analysis of Online Centroid Anomaly Detection, JMLR 2012
- Koumar et al., CESNET-TimeSeries24, Scientific Data 2025; analysis: https://github.com/Amirikiarash/drift-aware-nids
- Bose et al., AISTATS 2025: https://openreview.net/pdf?id=HF8PmUAaFu
- Open-source ESP32 WIDS: https://github.com/MashhudFarah/WIDS
- "When Adversarial Perturbations meet Concept Drift", ACM AISec 2024: https://dl.acm.org/doi/10.1145/3689932.3694757
- UMass Dartmouth frog-boiling thesis talk, 2026: https://www.umassd.edu/events/cms/20260811-demonstrating-and-characterizing-frog-boiling-poisoning.php
