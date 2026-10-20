# Research Round 3: 2024 to 2026 Literature and the Next Direction

Third research round, 20 Oct 2026. A multi-agent sweep: 10 search angles, 80 papers found, 24 of the most
recent (2024 to 2026) read in full, 4 candidate directions, adversarial prior-art searches on each, and 3
independent judges. Full machine output: `research/round3.json`.

## Plain-language summary

**1. The newest papers moved the bar.** Three 2026 preprints (WARDEN/CDC, "Theory of Continual Learning
Against Data Poisoning", CAPTURE) prove that a self-learning detector watching a single stream of data
*cannot* reliably tell honest drift from slow poisoning. So our open problem ("an attack hidden inside
genuine drift beats us") is not a bug we can patch. It is a proven limit, and the only escape is extra
information from outside that one stream.

**2. What is still ours:**
- **TOA** (rationing only the part of an update that moves toward an attack). No paper does this; the
  nearest relatives slow all directions equally, clamp to a fixed box, or freeze.
- **The freeze attack.** No paper treats "stop learning when suspicious" as something an attacker can
  trip on purpose, even though many published defences (T2T rollback, DriftXpert, OWAD, RTTAD) work that way.
- **A safety plus liveness guarantee:** a minimum time to compromise *and* bounded false alarms under
  honest drift. Nobody states the second half.
- **Anything on an ESP32.** A 2026 survey of about 70 microcontroller on-device learning papers found
  no security mechanism at all.

**3. What we must concede:** the self-poisoning theory itself (WARDEN owns it), gradual poisoning of
self-updating IDS as a threat (CCS 2025 poster, ANTIDOTE), and most parts of the core/outer-ring rule
(DriftXpert's outlier ratio is a close cousin).

**4. The chosen direction: Fleet-Orthogonal Adaptation (FOA).** Every device keeps its own detector, and
neighbouring devices act as witnesses. Drift the peers also see (network-wide change) is learned in full;
drift only one device sees goes through TOA's slow budget. Because peers give a second stream of evidence,
this escapes the single-stream impossibility results. It also fixes our new-device problem: a joining
device starts from its peers' median and learns under the budget. Peers are chosen to be
**vulnerability-diverse** (same role, different vendor or firmware), so one botnet exploit cannot fake
agreement. The freeze attack, run against real published defences, becomes the evaluation section.

**5. Honest novelty:** every candidate came back *partially covered*. FOA's closest prior work is CIoTA
(NDSS DISS 2018 / JPDC 2020), where same-firmware devices must agree before learning. FOA differs by
using vulnerability-diverse peers and by admitting the disagreeing part slowly instead of discarding it.
We must beat CIoTA head-to-head in a "monoculture botnet" test to earn the claim.

## Candidates, verdicts and judge scores

| Candidate | Prior-art verdict | Closest prior work | Judge total (of 120) |
|---|---|---|---|
| Fleet-Orthogonal Adaptation | partially covered | CIoTA: Collaborative IoT Anomaly Detection via Blockchain | 81 |
| Gate-Tripping and Calibration-Blinding | partially covered | For the theorem: CAPTURE | 84 |
| Rejected-Mode Subspace Budget | partially covered | Kloft & Laskov, "Security Analysis of Online Centroid Anomaly Detection", JMLR 13 | 80 |
| Event-Licensed Adaptation | partially covered | Cisco US Patent US9923911B2, "Anomaly detection supporting new application deployments" | 54 |

Judge picks: the security-reviewer judge picked the freeze-attack paper; the IoT-systems and pragmatic judges
picked FOA. The final design uses FOA as the method and the freeze attack on published defences as its
evaluation. Fallback if multi-device plumbing slips: the rejected-mode subspace budget (TOA with threat
directions learned from the detector's own alarms, no signatures).

## Must-read before claiming anything

`The Price of Self-Calibration` (arXiv 2609.23254), Pasikhani et al. (TDSC 2026) and the full AHA text
(CCS 2025) were not read in full and could pre-empt parts of the freeze-attack framing. Several 2026 papers
are un-reviewed preprints, and most numbers came through a summarising fetch tool: check every number
against the PDF before citing it.

---

# Full report from the research workflow

> Scope note. This is defensive research: the aim is a detector that keeps protecting constrained IoT devices while an adversary tries to corrupt its self-learning. Attack descriptions are kept at the level a security paper needs to justify a defense, not as operational recipes. All numbers taken from papers read through a summarizing fetch tool are flagged "verify"; check them against the source PDFs before citing.

---

## 1. What the newest research does (2024-2026)

### Theme A: the field now has impossibility theory for self-poisoning

Three 2026 preprints turned "a self-labelling detector slowly poisons itself" from a demo into a proved limit.

- **WARDEN / CDC** (arXiv:2607.21673, 2026, verify) models impurity of a self-updating bank as a generalized Polya urn. The admission-kernel slope `b` behaves like a reproduction number: below 1 impurity settles benign, at or above 1 it goes to full compromise, with a critical contamination rate. Its **Theorem 15** is a two-world construction on a one-dimensional score: honest drift and tail-mimicking contamination can produce the identical unlabelled stream, so any label-free threshold rule that holds a false-alarm rate under drift has detection power capped at `kappa = alpha / (pi + alpha(1-pi))`. A labelled oracle escapes; a single-stream label-free rule cannot.
- **Theory of CL Against Poisoning** (arXiv:2606.29841, ICML 2026, verify) proves no regularized learner converges under frequent shifted poison. Its one-dimensional proof is literally an EMA mean dragged by a persistent bias, which is our centroid. It also contributes the **T2T** rollback defense (flag a task when its score exceeds 2.5x the mean of the last five, then roll back to `w_{t-2}`).
- **CAPTURE** (arXiv:2609.02265, 2026, verify), Theorem 2, gives the static single-statistic dilemma in Le Cam two-point form: any rule reading one statistic has `FUR + RRL >= 1 - delta`, meaning it must either accept injected claims or reject genuine revisions.
- **The Price of Self-Calibration** (arXiv:2609.23254, 2026, verify) gives the non-adversarial version of the same trade-off (Remark 4, "no free tuning"): slowing adaptation narrows the blind set only at the cost of longer miscalibration after legitimate change, and no setting removes both costs. Its blind set for speed-bounded drift is the `2v` class.

Together these say our open problem 1 (an attack hidden inside genuine drift beats the signature-free rule) is **a known impossibility for single-stream label-free learners**, not a bug we can patch within one stream.

### Theme B: published adaptive NIDS and TTA detectors that we can study

- **ACORN-IDS** (arXiv:2602.07291, 2026, verify): continual novelty IDS, PCA reconstruction scorer, threshold `mean + 2*sigma` recomputed per task on a **clean held-out split**. No adversarial analysis. Important correction to our plan: its threshold is not refreshed from stream traffic, so a stream-inflation attack applies only if the clean split or the pseudo-labels can be influenced.
- **DriftXpert** (arXiv:2609.08623, 2026, verify): latent-manifold NIDS with a label-free Outlier Ratio `OR > T` retrain trigger plus selective freezing and weight interpolation. Public code reportedly incomplete (GitHub issue #1). Its OR statistic is essentially our "outer ring gets busier" test, used as a retrain trigger rather than an evidence gate.
- **OWAD** (NDSS 2023, background): calibrator + permutation-test shift detection + explainer + EWC-style consolidated fine-tune. Human labels the selected samples. Public KitNET-on-Kyoto demo. The most natural published defense to attack; its authors list robustness to adversarial attack as future work.
- **CB-RBM / Feature-Context Consistency** (arXiv:2610.16694, NeurIPS 2026, verify): a drift-stable graph fraud detector. Deliberately freezes a drift-invariant score and argues freezing is safe under smooth drift. A frozen plain-RBM baseline there rises to 89-100% false positives under drift, the same effect we measured.
- **RTTAD** (arXiv:2605.10242, 2026, verify) and **Su et al.** (arXiv:2410.04682, ICLR 2025): test-time adaptation that updates only on confident pseudo-normal samples. Su et al. show high-entropy poison is filtered by EATA and design a balanced low-entropy attack to pass the filter; nobody trips the filter to stall adaptation.

### Theme C: attacks on adaptation have matured, but only on the "absorb" side

- **AHA** (CCS 2025 poster, abstract only, verify): reframes boiling-frog with habituation, sensitization, creeping normality, alert fatigue. Conceptual, one VAE/Suricata demo, no measured defense.
- **Korycki & Krawczyk** (Machine Learning 2022): already names, in prose, "impairing the adaptation process" up to "complete nullification", forcing false adaptation, and draining the label budget. Mechanism is masking drift, not tripping a refusal gate; no theorem or contract.
- **Adversarial Attacks for Drift Detection** (ESANN 2025): constructs streams provably invisible to window-based monitors (`W_n v = 0`).
- **Su et al.**, **SuSS 2026** contrastive multi-agent drift induction, and **NDSS 2026** learned pulsing attackers time-boxed to a monitor's refresh windows: all on the absorb or evasion side.

### Theme D: robust statistics and certified updates, all batch or freezing

Online geometric median + Median Covariation Matrix (arXiv:2601.03957, 2026, verify) gives bounded per-point influence but unbounded influence for mean shift and variance inflation (the slow-poison directions), and freezes on long streams (decaying step size, no forgetting). **RPS** (ICLR 2025, arXiv:2410.09878) and **LID / Provably Safe Model Updates** (SaTML 2026, arXiv:2512.01899, verify) certify robustness but assume exchangeability or stop updating when the certified box empties.

### Theme E: TinyML on-device learning has no security at all

The ODL survey (arXiv:2605.31226, 2026, verify), about 70 MCU works, contains no poisoning, no adversarial triggering, no IDS, and never mentions ESP32. This is the clearest standing gap.

---

## 2. Honest check: covered versus still new

**Already covered (concede and cite, do not claim):**

| Our element | Covered by | What survives |
|---|---|---|
| Self-poisoning theory (urn, `b` as reproduction number, critical rate) | WARDEN 2026 | We can **measure** `q(rho)` and show `b >= 1` naive, `b < 1` ours; we cannot claim to theorize it first. |
| Open problem 1 (poison inside drift) | WARDEN Thm 15; 2606.29841 Thm 3.1; CAPTURE Thm 2 | Becomes a **corollary**; the contribution must be the side information that escapes the single-stream theorem. |
| "Gradual poisoning of a self-updating NIDS" | AHA (CCS 2025), ANTIDOTE, Kloft & Laskov | Not novel by itself. |
| Core/outer-ring parts | DriftXpert OR (retrain trigger); OWAD/NetSight permutation KL | The assembly and its use as an evidence gate is the thin new part. |
| Adaptive-attacker evaluation | Su et al., ESANN 2025, SuSS 2026, NDSS 2026 | A hand-built "hide in the core" attacker will not satisfy an A/A* reviewer; we need a learned or provably-blind attacker. |

**Still new (defensible):**

1. **TOA as threat-aware rate limiting**: split each update into a signature-direction component (rationed by a slow cumulative budget, giving a provable minimum time to compromise) and the rest (applied in full, never freezes). The nearest relatives restrict updates for other reasons: 2606.29841 penalizes data-covariance eigendirections with no cumulative budget and freezes at `lambda = infinity`; OWAD's consolidation guards forgetting; LID clamps to a static box; EMA and beta-interpolation slow every direction equally. Name it and contrast all four.
2. **The freeze attack as a stated attack surface**: no corpus paper treats a stop-learning, rollback, or gate rule as something an attacker trips on purpose to profit after leaving. Many published defenses have the vulnerable stop-start structure (T2T rollback, DriftXpert/OWAD gates, RTTAD stop rule, EATA filter). This is our most defensible first claim, pending a full read of 2609.23254 and the AHA text.
3. **A joint safety-plus-liveness contract** (minimum time to compromise AND bounded false alarms under honest drift, including after the attacker leaves). No paper states a liveness property for adaptive detectors.
4. **IoT / ESP32 / per-device lifecycle**: no corpus paper runs on an MCU, does per-device self-learning with a safe bootstrap, or treats device churn as an attack vector.
5. **Fleet peers as the side information that escapes the single-stream theorem** (the core of the chosen direction below).

---

## 3. The new direction

### In one paragraph

Keep a per-device centroid detector on every node. The impossibility results all assume **one** score stream, so give each device a second stream: its vulnerability-diverse peers. Each cycle a device proposes an update; the part that a robust peer consensus (geometric median of peers' proposed shifts) backs is applied in full, and only the peer-unexplained residual goes through TOA's slow cumulative budget. Common-mode drift (ISP, gateway, diurnal, campus calendar, a firmware push shared by peers) is applied freely; a single-exploit poisoning campaign, which peers do not share, is rationed. A new device bootstraps from the peer median under the residual budget only, which bounds join-time poisoning and fixes the 34% false-alarm result. We call it **Fleet-Orthogonal Adaptation (FOA)**. The freeze attack, generalized from our own baselines to verified published gates, is the evaluation section: it shows why gating on a single statistic is what FOA avoids.

This is the decisive call. Two of three judges picked FOA over the pure Gate-Tripping paper because FOA makes the ESP32 fleet the contribution (per-device detectors are the natural MCU shape), addresses three of four open problems in one mechanism, and reuses nearly all existing code. Gate-Tripping is the stronger pure-security paper but its theorem core is already published (CAPTURE + 2609.23254) and faithfully reimplementing six defenses in seven weeks is too risky; its strongest piece (freeze attacks on verified gates) folds into FOA's evaluation.

### Exact mechanism (pseudocode)

```
# Per device i, fixed PCA-10 basis frozen after a clean warm-up.
# State: centre c_i (R^10), spread s_i (scalar or per-axis).
# Budget: B0 (initial), B (per-cycle slope). Cumulative residual applied <= B0 + B*t.

for each cycle t:
    x_window = accepted_traffic(i, t)

    # 1. Local proposal via the signature-free core/ring pre-filter
    core      = dense_core(x_window)                 # trimmed inner mass
    ring      = outer_ring(x_window)                 # the periphery
    Delta_i   = proposed_shift(core)                 # centre move from the core only
    dS_i      = proposed_spread_growth(core)

    # 2. Gossip: send Delta_i (10 float32) + HMAC(key_provision) over ESP-NOW / gateway
    broadcast(i, Delta_i, dS_i, hmac=HMAC(key_i, Delta_i || dS_i || t))

    # 3. Peer consensus over the VULNERABILITY-DIVERSE peer group P(i)
    #    (same role + gateway, different vendor/firmware -> a monoculture botnet
    #     cannot fake consensus; network-wide drift is common-mode)
    peers   = verified_peer_shifts(P(i), t)          # drop any failing HMAC
    m_t     = geometric_median(peers, iters=10)      # Weiszfeld; breakdown point 1/2
    mS_t    = geometric_median([dS_j for j in peers])

    # 4. Split into common part + residual
    a_i     = g_i * m_t                              # g_i = per-device gain (warm-up)
    r_i     = Delta_i - a_i

    # 5. Update: common part in full, residual rationed by TWO cumulative budgets
    #    (budget #2 on the consensus channel closes the g*C*sigma leak in T1)
    c_i    += a_i + budget_apply(r_i,  cum_residual,  B0, B)
    c_i    += budget_apply_consensus(a_i, cum_common, B0c, Bc)   # cap on common channel
    # Spread: peer-backed growth in full; device-specific excess budgeted; growth
    # along the signature direction gets a direction-weighted radius budget
    s_i    += peer_backed(mS_t) + budget_apply(excess_spread, cum_spread, ...)

    # 6. Accept/flag using updated (c_i, s_i); self-label accepted traffic as normal

# JOIN: a new device starts from (median peer c, median peer s) and runs its first
# K cycles under the RESIDUAL budget only -> join-time poisoning bounded by B0 + K*B.
```

TOA (the signature-direction budget) is the special case where `P(i)` is empty and the rationed component is the known-signature projection. The signature-free rule is the local pre-filter (`core`, `ring`) that produces `Delta_i`. The freeze attack is what we deliberately avoid: there is no stop-learning gate anywhere, so there is no refusal region for honest drift to trip.

### Why it is different from every recent paper

- **Escapes the impossibility theorems** (WARDEN Thm 15, 2606.29841 Thm 3.1, CAPTURE Thm 2): all are single-stream. FOA's second stream (peers) changes the observation model. In the two-world construction, World-A honest drift is common-mode across peers while World-B contamination reaches at most `f < |P|/2` streams, so a peer-aware rule can hold the false-alarm rate in A and keep detection in B. This must be proved as its **own** multi-stream theorem with fixed `f` (not as a corollary), plus the matching negative result: victim-only drift is still indistinguishable up to rate `B`.
- **Not CIoTA / LE3D** (NDSS DISS 2018, CCNC 2023, the nearest prior art): CIoTA uses same-firmware peers and element-wise consensus and simply **discards** anything without consensus; LE3D only labels common drift natural. FOA (a) uses **vulnerability-diverse** peers so a monoculture botnet cannot manufacture consensus, and (b) **admits the residual slowly through a budget** instead of discarding it, which keeps liveness for device-specific benign drift.
- **Not robust federated aggregation** (R-DPFL 2026, BALANCE CCS 2024): those aggregate one shared model and clip the remainder to zero. FOA keeps per-device models and rations rather than clips, inside a time-to-compromise and freeze analysis.
- **Not T2T / DriftXpert / OWAD / RTTAD / EATA**: all gate adaptation on a statistic, which is exactly the freeze surface; FOA never stops learning.

### How it builds on TOA, the signature-free rule, and the freeze attack

TOA's budget code and minimum-time-to-compromise proof carry over with the signature projector replaced by "residual after consensus". The signature-free core/ring rule becomes the local pre-filter. The freeze attack graduates from our own baselines to published gates and becomes the evaluation that justifies the no-gate design: we show CIoTA-style discard and the gated defenses fail under a tripped-then-left attacker while FOA holds.

---

## 4. Threat model (including an adaptive attacker who knows the defense)

- **Attacker capability**: controls its own traffic on one device and up to `f` peer streams; no gradients, no parameters, no provisioning key (so it cannot forge HMACs or mint peers). Attacker share `rho` of a victim's accepted traffic is the main axis (Kloft & Laskov 2012).
- **Knowledge**: white-box on the algorithm, grey-box on live state. A **surrogate-by-query** attacker rebuilds an approximate centroid from observed accept/flag decisions (Su et al. style), then steers poison.
- **Adaptive attackers to run, each known to the literature**:
  1. Contrastive multi-direction poisoner (SuSS 2026 reward): spreads displacement over mutually dissimilar directions to beat a single budget.
  2. Core-hiding poisoner: matches first and second moments of clean traffic (Su et al. feature-consistency).
  3. Window-blind schedule (ESANN 2025, `W_n v = 0`): provably invisible to our ring windows.
  4. Learned pulsing (NDSS 2026): times bursts to the budget refill.
  5. Monoculture botnet: compromises same-vendor peers to fake consensus (the test that separates FOA from CIoTA).
  6. Omission: withholds attack traffic until after compromise.
- **Failure boundary, reported honestly**: correlated compromise of a majority of the peer group (`f >= |P|/2`), gateway/relay compromise, and cross-vendor credential botnets. State these as the limits where the escape does not hold.

---

## 5. Experiments

### Datasets

- **N-BaIoT (synthesised concurrency)**: Danmini, Ecobee, Philips as vendor-diverse peers, plus the four cameras (Provision PT-737E/PT-838, SimpleHome XCS7-1002/1003). Build time-aligned benign streams; inject (a) common-mode drift (rate/size ramps, gradual mix-in of a second benign profile) and (b) idiosyncratic drift on one device; poison one device toward Mirai scan/ack/syn at `rho` from 5-40%. **Label the concurrency as synthetic**: N-BaIoT captures are per-device and not concurrent (confirmed by the NID dataset survey, Computers & Security 2025, which notes no documented public concept-drift NID dataset existed through 2023).
- **CESNET-TimeSeries24 (real common-mode drift)**: per-IP hourly series, cluster IPs into behavioural peer groups, exploit the real semester-start/holiday shifts as drift speed `v`, inject a boiling-frog ramp toward a scanning profile into one IP. Report detection against WARDEN's `kappa` for single-stream vs FOA to show the ceiling lifts. **Stretch goal**, not on the critical path.
- **ESP32 fleet of 4 (6 if time)**: identical telemetry firmware plus 1-2 different firmwares for diversity, a real router/endpoint change as genuine common-mode drift, a laptop poisoner on one board.

### Baselines (including the newest published defenses)

Naive self-labeller; our freezing baselines; **CIoTA-style same-firmware consensus** (the head-to-head that proves vulnerability diversity); **R-DPFL-style clipped robust aggregation**; **WARDEN frozen reserve + conformal p-values + e-BH**; **Kloft & Laskov switch-off gate** (the classic FPR-triggered freeze, our freeze-attack target); **T2T rollback** and **OWAD** (KitNET public demo) as verified published gates for the freeze section; TOA with a true signature; the signature-free core/ring rule. Drop the unverified LID box and CB-RBM re-implementations and the ACORN stream-inflation claim unless the clean-split threat model is justified.

### Metrics

Time to compromise; FPR during and after the attack plus the half-life of elevated FPR (the liveness metric nobody measures); FPR under honest drift; detection TPR vs WARDEN `kappa`; alerts per device per hour; measured `q(rho)` and `b` per detector (the urn lens); for the freeze section, freeze duty cycle per attacker packet and post-departure FPR validated against the predicted `1 - Phi(z_alpha - v*tau/s)`.

### The one headline figure

A two-panel figure. **Left**: under a monoculture-botnet scenario, CIoTA same-firmware consensus absorbs the campaign (compromise) while FOA's vulnerability-diverse peers hold (100% detection, low FPR). **Right**: post-attacker-departure FPR under honest drift, showing the freezing/gated defenses at the 85-87% false-alarm plateau and FOA flat near its nominal rate. One picture, both the safety win and the liveness win.

### ESP32 measurements

Per-cycle latency; peak RAM including the gossip buffer; ESP-NOW bytes per learning event; energy per learning event via INA219; HMAC verification time. A 10-dimensional geometric median (Weiszfeld, 10 iterations) and a 40-byte gossip packet are cheap enough to measure and defend. Report compute-only power separately from Wi-Fi transmit power (the latter can exceed the TinyML survey's 500 mW class figure).

---

## 6. Runner-up directions worth mentioning

- **Gate-Tripping and Calibration-Blinding** (judge 1's pick): formalize the freeze attack and its dual (blinding a label-free calibrator) as attacks on any suspicion-gated self-learner, with the safety-plus-liveness contract, and break verified published gates on IoT traffic. Strongest pure-security paper, but the theorem core is pre-empted by CAPTURE Thm 2 and 2609.23254 Remark 4, and reproducing six defenses in seven weeks is high-risk. **Use its best piece (freeze attacks on verified gates) as FOA's attack section.**
- **RMSB (Rejected-Mode Subspace Budget)**: TOA whose threat directions are learned from the detector's own alarms (persistent, stationary rejected modes). Cheapest to build (rank-1 projector becomes rank-r), but every part has prior art (Kloft & Laskov alarm-driven protection, MINAS persistence, GPM/SafeGrad projection). **Use as the low-risk fallback and as the learned subspace inside FOA's residual channel.**
- **Event-Licensed Adaptation**: signed firmware/provisioning events unlock a time-boxed fast-learning budget. Headline pre-empted by Cisco US9923911B2, HADES-IoT, and Defender for IoT; secure-boot eFuse burns are irreversible and risky on our only boards. **Borrow only the licensed-join idea as a small extension to FOA's join rule.**

---

## 7. Risks and honest limits

1. **Novelty is partial.** FOA's "peers as witness" headline is CIoTA/LE3D. The paper must be pitched as "the first budgeted common-versus-residual update split for label-free detector adaptation, with a multi-stream escape from the drift/contamination ceiling", citing CIoTA, LE3D, R-DPFL up front, and must beat CIoTA in the monoculture-botnet head-to-head to earn the framing.
2. **Synthetic concurrency on N-BaIoT.** The devices were captured separately, so common-mode drift is injected by us; reviewers discount this. The ESP32 fleet's real router change and CESNET's real calendar drift have to carry the "the drift is real" claim.
3. **Theorem risk.** T2 is almost true by assumption; it must be a standalone multi-stream theorem with fixed `f` plus the victim-only negative result, or reviewers call it a corollary. T1 has an unbudgeted consensus-channel leak (`g*C*sigma_idio`), the exact frog-boiling surface; close it with the second cumulative budget (budget #2 in the pseudocode).
4. **Liveness gap from diversity.** Vulnerability-diverse peers push benign vendor-specific drift (a single-vendor firmware push) into the budgeted residual, which can slow legitimate adaptation. Measure this explicitly.
5. **Must-read-before-writing caveats.** `2609.23254` (manufactured blind sets), Pasikhani et al. TDSC 2026, and the AHA full text are unread and could partly pre-empt framing. Most corpus numbers came through a summarizing fetch tool; verify against PDFs. Several 2026 hits are single-author un-reviewed preprints.
6. **Unsearched kill zones.** Byzantine multi-sensor change detection, federated "framing honest clients" attacks, and classic IDS alert flooding (squealing, Stick/Snot) were not searched and could hide a direct precedent for the freeze section.

---

## 8. Seven-week plan

- **W1**: Multi-stream N-BaIoT harness (cameras + Danmini/Ecobee/Philips) with synthetic common-mode and vendor-specific drift; label synthetic clearly. Read `2609.23254` and the AHA full text.
- **W2**: FOA implemented (geometric median, HMAC gossip, two cumulative budgets to close the T1 leak). Reuse TOA budget code and the core/ring filter unchanged except the projector.
- **W3**: Baselines, CIoTA same-firmware consensus, R-DPFL clipping, WARDEN frozen reserve, the Kloft & Laskov switch-off gate (freeze attack demonstrated on it, closing open problem 4), TOA, signature-free.
- **W4**: Attacker matrix: `f` sweep, Sybil gossip without the key, monoculture botnet, core-hiding, window-blind schedule, a small PPO pulsing attacker, attack-hidden-in-drift. Build the headline figure.
- **W5**: ESP32 fleet of 4 over ESP-NOW: one real router/endpoint change, laptop poisoner, measure latency/RAM/bytes/energy/HMAC time.
- **W6**: T1 and T2 proofs (T2 standalone with its negative result); ablations (plain vs geometric median, peer-group size, `B`, random vs vulnerability-diverse peers, correlated-compromise boundary); measure `q(rho)` and `b`.
- **W7**: Writing. CESNET is a stretch goal only.

**Fallbacks**: if the multi-stream plumbing slips, RMSB is the low-risk core and its learned subspace stands in for the signature in FOA's residual channel. The freeze results on published gates make a strong section regardless of which core ships.

---

### References (10-15 most recent, with role)

1. **WARDEN / CDC** - Self-Poisoning in Adaptive OOD Detection (arXiv:2607.21673, 2026, verify). Role: the impossibility ceiling (Theorem 15, `kappa`) FOA must escape; the urn/`b`-as-reproduction-number lens we measure.
2. **Theory of CL Against Poisoning** (arXiv:2606.29841, ICML 2026, verify). Role: EMA-mean-dragged-by-bias impossibility = our centroid; source of the T2T rollback gate we freeze-attack.
3. **CAPTURE** (arXiv:2609.02265, 2026, verify). Role: static single-statistic dilemma (Thm 2) that our safety-plus-liveness contract extends adversarially; cite, do not restate.
4. **The Price of Self-Calibration** (arXiv:2609.23254, 2026, verify). Role: non-adversarial "no free tuning" trade-off and the `2v` blind set; must read before claiming the freeze framing.
5. **ACORN-IDS** (arXiv:2602.07291, 2026, verify). Role: closest published continual novelty IDS; baseline and attack target; corrects our clean-split assumption.
6. **DriftXpert** (arXiv:2609.08623, 2026, verify). Role: published OR-gated adaptive NIDS; its OR is our ring test; a freeze target with (incomplete) public code.
7. **OWAD** (NDSS 2023). Role: the most natural published defense to freeze-attack; KitNET public demo; evidence that per-device detectors are the practical unit.
8. **CB-RBM / Feature-Context Consistency** (arXiv:2610.16694, NeurIPS 2026, verify). Role: a 2026 "freeze and make the score drift-invariant" design that leaves strategic drift open; contrast for FOA's peer-context idea.
9. **Su et al.** - Adversarial Risk of Test-Time Adaptation (arXiv:2410.04682, ICLR 2025). Role: realistic grey-box/surrogate threat model and the EATA entropy-filter baseline; precedent for our adaptive attacker.
10. **RTTAD** (arXiv:2605.10242, 2026, verify). Role: confident-pseudo-normal TTA with a stop rule; a gated-defense target.
11. **Korycki & Krawczyk** - Adversarial Concept Drift under Poisoning (Machine Learning 2022). Role: prior prose for "impair/nullify adaptation" and label-queue drain; concede that the ideas are not new, draw the distinction.
12. **Kloft & Laskov** - Security Analysis of Online Centroid Anomaly Detection (JMLR 2012). Role: foundation for attacker-share and minimum-time-to-compromise; the classic FPR-triggered switch-off gate we freeze-attack; warns a learned radius invites poisoning.
13. **AHA** - Adversarial Habituation Attack (CCS 2025 poster, verify). Role: newest top-venue naming of boiling-frog / alert fatigue; must read full text before claiming the freeze framing.
14. **CIoTA** - Collaborative IoT Anomaly Detection via Blockchain (NDSS DISS 2018 / JPDC 2020). Role: the closest prior art for peers-as-witness; the head-to-head baseline (same-firmware consensus) FOA must beat with vulnerability diversity.
15. **RPS** - Reliable Prediction Sets under Data Poisoning (ICLR 2025, arXiv:2410.09878). Role: two-sided (coverage + size) reliability framing that models our detection-plus-false-alarm contract; background for certified robustness.