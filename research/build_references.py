"""Builds references.md (compiled, newest first) and references.json. Run: python3 build_references.py"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
# (year, month for sorting, short title, authors/venue, status, read, role, url)
R = [
 # ---------------- 2026
 (2026, 10, "Feature-Context Consistency: Unsupervised Adversarial Detection with Drift Stability on Attributed Graphs (CB-RBM)", "arXiv 2610.16694 (journal-ref field says NeurIPS 2026)", "preprint, venue to verify", "full text", "Freezes a drift-invariant score instead of adapting; its frozen baseline shows the false-alarm blow-up under drift that we measured", "https://arxiv.org/abs/2610.16694"),
 (2026, 9, "The Price of Self-Calibration: Exact Evidence Budgets and Manufactured Blind Sets in Adaptive Monitoring", "arXiv 2609.23254", "preprint", "seen in search, not read", "Closest to our freeze-attack framing (non-adversarial trade-off between safety and recalibration). Must read before claiming the freeze attack", "https://arxiv.org/abs/2609.23254"),
 (2026, 9, "Navigating the Latent Manifold: Proactive Concept Drift Adaptation for Resilient NIDS (DriftXpert)", "arXiv 2609.08623", "preprint", "full text", "Outlier-ratio gate for adaptation: a published gate we tested in the freeze study", "https://arxiv.org/abs/2609.08623"),
 (2026, 9, "CAPTURE: Disentangling Preference Drift from Memory Poisoning in Personalized LLM Agents", "arXiv 2609.02265", "preprint", "seen in search, not read", "States a single-statistic dilemma (accept injected claims or reject genuine revisions) that our safety-plus-liveness goal extends", "https://arxiv.org/abs/2609.02265"),
 (2026, 9, "Candidate Comparability Before Promotion: Conditional Validation in Adaptive Network Intrusion Detection", "Fernandez-Barrios et al., arXiv 2609.04388", "preprint", "abstract", "Server-side study of when an adaptive NIDS should accept a retrained model; no poisoning. A hold-back-until-evidence design to compare against", "https://arxiv.org/abs/2609.04388"),
 (2026, 8, "Empirical Analysis of Evasion and Poisoning Against Malware Data Drift Detection", "arXiv 2608.03642", "preprint", "full text", "Recent evidence that drift detectors themselves can be attacked", "https://arxiv.org/abs/2608.03642"),
 (2026, 7, "Self-Poisoning in Adaptive Out-of-Distribution Detection: A Sharp-Threshold Theory and Certified Label-Free Calibration (WARDEN, CDC)", "arXiv 2607.21673", "preprint", "full text", "Theory of self-poisoning; proves a single label-free stream cannot separate honest drift from contamination. The ceiling we must escape", "https://arxiv.org/abs/2607.21673"),
 (2026, 6, "Theory of Continual Learning Against Data Poisoning Attacks", "arXiv 2606.29841 (ICML 2026 template, venue to verify)", "preprint", "full text", "No regularised learner converges under frequent shifted poison; source of the T2T rollback gate; nearest to TOA's direction damping", "https://arxiv.org/abs/2606.29841"),
 (2026, 6, "Rapid Poison: Practical Poisoning Attacks Against the Rapid Response Framework", "ICML 2026 (arXiv 2606.16242)", "peer-reviewed", "full text", "Poisoning of an adaptation pipeline, including induced false positives; shows signatures themselves can be shaped by an attacker", "https://arxiv.org/abs/2606.16242"),
 (2026, 5, "What changes after deployment? A survey on On-device Learning in TinyML", "arXiv 2605.31226", "preprint", "full text", "About 70 microcontroller learning works and no security mechanism: the standing gap we fill", "https://arxiv.org/abs/2605.31226"),
 (2026, 5, "When Normality Shifts: Risk-Aware Test-Time Adaptation for Unsupervised Tabular Anomaly Detection (RTTAD)", "arXiv 2605.10242", "preprint", "full text", "Confident-normal-only adaptation with a stop rule; unguarded adaptation is worse than none, matching our naive result", "https://arxiv.org/abs/2605.10242"),
 (2026, 3, "The Boiling Frog Threshold: Criticality and Blindness in World Model-Based Anomaly Detection Under Gradual Drift", "arXiv 2603.08455", "preprint", "full text", "Gradual-drift blindness in anomaly detection; related threat model", "https://arxiv.org/abs/2603.08455"),
 (2026, 2, "ACORN-IDS: Adaptive Continual Novelty Detection for Intrusion Detection Systems", "arXiv 2602.07291", "preprint", "full text", "Closest recent continual IDS to our setting (PCA scorer, normal-only stream); no adversarial analysis", "https://arxiv.org/abs/2602.07291"),
 (2026, 1, "Online robust covariance matrix estimation and outlier detection", "arXiv 2601.03957", "preprint", "full text", "Bounded per-point influence but unbounded influence for mean shift; no forgetting. Shows why plain robust statistics are not enough", "https://arxiv.org/abs/2601.03957"),
 (2026, 1, "Contrastive Adversarial Agents for Intentional Drift Induction in Network Intrusion Detection Systems", "AAAI Summer Symposium Series (SuSS) 2026", "peer-reviewed (symposium)", "full text", "Attacker induces drift to steer a retrained NIDS; supports our adaptive-attacker model; no defence", "https://ojs.aaai.org/index.php/AAAI-SS/"),
 (2026, 1, "Strategic Games and Zero Shot Attacks on Heavy-Hitter Network Flow Monitoring", "NDSS 2026", "peer-reviewed", "full text", "Learned attackers timed to a monitor's refresh windows; basis for our pulsing-attacker test", "https://www.ndss-symposium.org/"),
 # ---------------- 2025
 (2025, 12, "Provably Safe Model Updates (LID)", "arXiv 2512.01899 (SaTML 2026 per paper notes, to verify)", "preprint, venue to verify", "full text", "Certified box around a model's parameters; stops updating when the box empties (another stop-style design)", "https://arxiv.org/abs/2512.01899"),
 (2025, 8, "Shift Detection and Adaptation for Network Intrusion Detection (NetSight)", "arXiv 2508.15100", "preprint", "full text", "Self-labelling drift-adaptive NIDS with permutation-test gates", "https://arxiv.org/abs/2508.15100"),
 (2025, 8, "CITADEL: Continual Anomaly Detection for Enhanced Learning in IoT Intrusion Detection", "arXiv 2508.19450", "preprint", "seen in search, not read", "Recent continual IoT IDS; check whether it defends its own adaptation", "https://arxiv.org/abs/2508.19450"),
 (2025, 10, "Adversarial Habituation Attack: A Psychological Extension and Re-framing of Boiling Frog Attack", "ACM CCS 2025 (poster)", "peer-reviewed (poster)", "abstract only", "Newest top-venue naming of boiling-frog and alert fatigue; read the full text before claiming the freeze framing", "https://dl.acm.org/doi/10.1145/3719027.3760741"),
 (2025, 4, "On the Adversarial Risk of Test Time Adaptation: An Investigation into Realistic Test-Time Data Poisoning", "ICLR 2025 (arXiv 2410.04682)", "peer-reviewed", "full text", "Realistic grey-box poisoning of adaptation and the entropy-filter defence; our threat-model precedent", "https://arxiv.org/abs/2410.04682"),
 (2025, 4, "Provably Reliable Conformal Prediction Sets in the Presence of Data Poisoning", "ICLR 2025 spotlight (arXiv 2410.09878)", "peer-reviewed", "abstract and method", "Two-sided reliability (coverage and size) that models our detection-plus-false-alarm contract", "https://arxiv.org/abs/2410.09878"),
 (2025, 4, "Adversarial Attacks for Drift Detection", "ESANN 2025 (arXiv 2411.16591)", "peer-reviewed", "abstract and method", "Streams provably invisible to window-based drift monitors", "https://arxiv.org/abs/2411.16591"),
 (2025, 2, "Network Intrusion Datasets: A Survey, Limitations, and Recommendations", "Computers & Security 156 (2025), arXiv 2502.06688", "peer-reviewed", "abstract and key sections", "Notes there is no documented public NID dataset with concept drift: why we inject drift and add CESNET", "https://arxiv.org/abs/2502.06688"),
 (2025, 6, "CND-IDS: Continual Novelty Detection for Intrusion Detection Systems", "DAC 2025 (arXiv 2502.14094)", "peer-reviewed", "full text", "Continual IDS that refits on a held-out clean subset", "https://arxiv.org/abs/2502.14094"),
 (2025, 3, "CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting", "Koumar et al., Scientific Data 12 (2025)", "peer-reviewed", "dataset paper", "Core: 40 weeks of real traffic drift", "https://www.nature.com/articles/s41597-025-04603-x"),
 # ---------------- 2024
 (2024, 10, "Data Poisoning Attack against Neural Network-Based On-Device Learning Anomaly Detector by Physical Attacks on Sensors", "MDPI Sensors 24(19):6416 (2024)", "peer-reviewed", "full text", "100% poisoning success on an on-device learner; proposes no defence", "https://doi.org/10.3390/s24196416"),
 (2024, 5, "AOC-IDS: Autonomous Online Framework with Contrastive Learning for Intrusion Detection", "IEEE INFOCOM 2024 (arXiv 2402.01807)", "peer-reviewed", "full text", "Online IDS with a frozen trusted anchor", "https://arxiv.org/abs/2402.01807"),
 # ---------------- Foundations and core
 (2023, 3, "Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation (OWAD)", "NDSS 2023", "peer-reviewed", "full text", "Per-device shift detection with a permutation-test gate; public demo; a published gate to test", "https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/"),
 (2022, 1, "Adversarial concept drift detection under poisoning attacks for robust data stream mining", "Korycki and Krawczyk, Machine Learning (Springer) 2022", "peer-reviewed", "full text", "Prose precedent for attacks that impair the adaptation process", "https://arxiv.org/abs/2009.09497"),
 (2018, 7, "CIoTA: Collaborative IoT Anomaly Detection via Blockchain", "Golomb, Mirsky, Elovici. NDSS DISS 2018; JPDC 2020", "peer-reviewed", "found in prior-art check", "Closest prior art for peers as witnesses: same-firmware devices must agree before learning", "https://arxiv.org/abs/1803.03807"),
 (2018, 2, "N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders", "Meidan et al., IEEE Pervasive Computing 2018", "peer-reviewed", "dataset paper", "Core: real IoT traffic and Mirai/BASHLITE attacks; our data", "https://arxiv.org/abs/1805.03409"),
 (2018, 2, "Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection", "Mirsky et al., NDSS 2018", "peer-reviewed", "full text", "Core: our feature extraction and the online IDS idea", "https://arxiv.org/abs/1802.09089"),
 (2017, 12, "Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent (Krum)", "Blanchard et al., NeurIPS 2017", "peer-reviewed", "full text", "Robust filtering that needs many peers; why peer-free is hard", "https://papers.nips.cc/paper/6617-machine-learning-with-adversaries-byzantine-tolerant-gradient-descent"),
 (2012, 1, "Security Analysis of Online Centroid Anomaly Detection", "Kloft and Laskov, JMLR 13 (2012)", "peer-reviewed", "full text", "Core: attacker share bounds poisoning; source of the alarm-rate switch-off idea", "https://jmlr.csail.mit.edu/papers/volume13/kloft12b/kloft12b.pdf"),
 (2009, 11, "ANTIDOTE: Understanding and Defending against Poisoning of Anomaly Detectors", "Rubinstein et al., ACM IMC 2009", "peer-reviewed", "full text", "Core: the boiling-frog attack on network detectors and a robust-PCA defence", "https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf"),
]
R.sort(key=lambda r: (r[0], r[1]), reverse=True)
CORE = {"ANTIDOTE", "Security Analysis of Online Centroid", "Kitsune", "N-BaIoT", "CESNET"}
rows = [dict(year=r[0], title=r[2], venue=r[3], status=r[4], read=r[5], role=r[6], url=r[7],
             core=any(r[2].startswith(c) for c in CORE)) for r in R]
json.dump(rows, open(os.path.join(HERE, "references.json"), "w"), indent=1)

recent = [r for r in rows if r["year"] >= 2025]
md = ["# Compiled references, newest first", "",
      f"{len(rows)} references; **{len(recent)} are from 2025 and 2026**. Built from the papers we searched for and read across three research rounds.",
      "", "**How to use this list**",
      "- *Read* shows how much of the paper we actually read. Anything marked \"seen in search, not read\" or \"abstract\" must be read before it is cited for a specific claim.",
      "- Many 2026 entries are **preprints** (not yet peer-reviewed). Check numbers against the PDF, not against our summaries.",
      "- The five **core** papers (cited in the proposal deck) are marked CORE.", ""]
cur = None
for r in rows:
    y = r["year"] if r["year"] >= 2024 else "Earlier and core"
    if y != cur:
        md += ["", f"## {y}", "", "| Reference | Venue | Status | Read | Why it matters to us |", "|---|---|---|---|---|"]
        cur = y
    t = ("**CORE** " if r["core"] else "") + f"[{r['title']}]({r['url']})"
    md.append(f"| {t} | {r['venue']} | {r['status']} | {r['read']} | {r['role']} |")
md += ["", "## Not yet searched", "",
       "Byzantine multi-sensor change detection, federated learning attacks that frame honest clients, and classic IDS alert-flooding "
       "attacks (the old Stick and Snot tools) were not searched and could hold direct precedents for the freeze attack."]
open(os.path.join(HERE, "..", "references.md"), "w").write("\n".join(md).replace("—", ", ") + "\n")
print(len(rows), "references;", len(recent), "from 2025-2026")
