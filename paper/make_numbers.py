"""
Every number quoted in the paper text comes from here: it reads experiments/foa/results/*.pkl and
writes paper/numbers.tex (LaTeX macros) and paper/tables.tex. Run after the experiments:
    python3 paper/make_numbers.py
"""
import json, os, pickle, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "experiments", "foa", "results")


def load(n):
    p = os.path.join(RES, n + ".pkl")
    return [r for r, _ in pickle.load(open(p, "rb"))] if os.path.exists(p) else []


def sel(R, **f):
    return [r for r in R if all((r.get(k) == v) if not callable(v) else v(r.get(k)) for k, v in f.items())]


def mean(R, key):
    v = [r[key] for r in R if r.get(key) is not None and np.isfinite(r[key])]
    return float(np.mean(v)) if v else float("nan")


def pct(x, d=1):
    return "n/a" if not np.isfinite(x) else f"{100 * x:.{d}f}\\%"


M = {}
T = []
E0 = json.load(open(os.path.join(RES, "E0.json"))) if os.path.exists(os.path.join(RES, "E0.json")) else {}
if E0:
    M["ExplainedVar"] = pct(E0["explained"])

E1 = load("E1")
if E1:
    cs = lambda p: mean(sel(E1, scenario="common_strong", policy=p), "fpr_fleet_after")
    M["StrongStaticFPR"] = pct(cs("static"), 0)
    M["FOAFleetFPR"] = pct(cs("foa"))
    M["AutoFleetFPR"] = pct(cs("auto"))
    M["GateFleetFPR"] = pct(cs("kl"), 0) + " to " + pct(cs("frozen"), 0)
    M["NaiveFleetFPR"] = pct(cs("naive"))
    M["FOAIdioFPR"] = pct(mean(sel(E1, scenario="idio", policy="foa"), "fpr_v_after"), 0)
    M["AutoIdioFPR"] = pct(mean(sel(E1, scenario="idio", policy="auto"), "fpr_v_after"), 0)
    rows = []
    for p, name in [("static", "Static"), ("naive", "Naive"), ("auto", "Single device"), ("clip", "Clipping"), ("frozen", "Frozen reserve"),
                    ("kl", "Alarm switch-off"), ("or", "Outlier-ratio gate"), ("toa", "TOA (oracle)"), ("foa", "\\textbf{FOA}")]:
        v = [mean(sel(E1, scenario="common_moderate", policy=p), "fpr_fleet_after"), cs(p),
             mean(sel(E1, scenario="idio", policy=p), "fpr_v_after")]
        rows.append(f"{name} & " + " & ".join("n/a" if not np.isfinite(x) else f"{100 * x:.1f}" for x in v) + r" \\")
    T.append(("tab:liveness", "False alarms (\\%) after honest drift, no attacker. Shared drift: fleet mean; device-only: that device. 10 held-out seeds.",
              "lrrr", "Rule & Moderate & Strong & Device-only", rows))

E3 = load("E3")
if E3:
    comp = lambda pol, **f: mean(sel(E3, policy=pol, **f), "compromised_attr")
    M["FOAComp"] = pct(comp("foa"))
    M["AutoComp"] = pct(comp("auto"))
    M["KLComp"] = pct(comp("kl"))
    M["FrozenComp"] = pct(comp("frozen"))
    M["TOAComp"] = pct(comp("toa"))
    M["FOABoundaryComp"] = pct(comp("foa", mode="boundary"), 0)
    M["AutoBoundaryComp"] = pct(comp("auto", mode="boundary"), 0)
    M["AutoBoundaryCompHigh"] = pct(comp("auto", mode="boundary", p=0.4), 0)
    M["FOACoreHigh"] = pct(comp("foa", mode="core", p=0.4), 0)
    M["FOAMimicHigh"] = pct(comp("foa", mode="mimicry", p=0.4), 0)
    M["BoundViolations"] = str(sum(int(r.get("bound_violations") or 0) for r in E3))
    M["NRunsEThree"] = f"{len(E3):,}".replace(",", "{,}")
    tt = lambda p: [r["ttc_attr"][0] for r in sel(E3, policy=p) if r["ttc_attr"][0] is not None]
    M["FOAMedTTC"] = f"{np.median(tt('foa')) - 40:.0f}" if tt("foa") else "n/a"
    M["AutoMedTTC"] = f"{np.median(tt('auto')) - 40:.0f}" if tt("auto") else "n/a"
    rows = []
    for p, name in [("naive", "Naive"), ("auto", "Single device"), ("or", "Outlier-ratio gate"), ("kl", "Alarm switch-off"),
                    ("clip", "Clipping"), ("frozen", "Frozen reserve"), ("toa", "TOA (oracle)"), ("foa", "\\textbf{FOA}")]:
        v = [comp(p, mode=m) for m in ("boundary", "core", "mimicry")] + [comp(p), mean(sel(E3, policy=p), "fpr_v_after"),
                                                                        mean(sel(E3, policy=p), "fpr_fleet_after")]
        rows.append(f"{name} & " + " & ".join(f"{100 * x:.0f}" if i < 4 else f"{100 * x:.1f}" for i, x in enumerate(v)) + r" \\")
    T.append(("tab:e3", "Attack hidden in strong shared drift: victims compromised (\\%, attack-attributable) by attacker type, averaged over shares 0.1 to 0.4, and false alarms after drift (\\%). 7 victims, 10 held-out seeds.",
              "lrrrrrr", "Rule & Bound. & Core & Mimic. & All & FPR$_v$ & FPR$_{fl}$", rows))

E2 = load("E2")
if E2:
    comp = lambda pol, **f: mean(sel(E2, policy=pol, **f), "compromised_attr")
    M["NoDriftNaiveComp"] = pct(comp("naive"), 0)
    M["NoDriftAutoComp"] = pct(comp("auto"), 0)
    M["NoDriftFOAComp"] = pct(comp("foa"), 0)
    rows = []
    for p, name in [("naive", "Naive"), ("auto", "Single device"), ("kl", "Alarm switch-off"), ("clip", "Clipping"),
                    ("frozen", "Frozen reserve"), ("toa", "TOA (oracle)"), ("foa", "\\textbf{FOA}")]:
        v = [comp(p, mode=m) for m in ("boundary", "core", "mimicry")] + [comp(p)]
        rows.append(f"{name} & " + " & ".join(f"{100 * x:.0f}" for x in v) + r" \\")
    T.append(("tab:e2", "Poisoning with no drift: victims compromised (\\%) by attacker type, averaged over shares 0.1 to 0.4.",
              "lrrrr", "Rule & Boundary & Core & Mimicry & All", rows))

E4 = load("E4")
if E4:
    c = lambda p, k, d: mean(sel(E4, policy=p, infected=k, drift=d), "compromised_attr")
    M["MonoCiotaThree"] = pct(c("ciota", 3, "strong"), 0)
    M["MonoFOAThree"] = pct(c("foa", 3, "strong"), 0)
    M["MonoSameThree"] = pct(c("foa_same", 3, "strong"), 0)
    M["MonoCiotaOne"] = pct(c("ciota", 1, "strong"), 0)

E5 = load("E5")
if E5:
    f = lambda p, att: mean(sel(E5, policy=p, attacker=att), "fpr_v_tail")
    M["KLFrozenFPR"] = pct(f("kl", True), 0)
    M["KLCleanFPR"] = pct(f("kl", False), 0)
    M["FOAFreezeFPR"] = pct(f("foa", True), 1)
    M["FOAFreezeClean"] = pct(f("foa", False), 1)
    M["ORFrozenFPR"] = pct(f("or", True), 0)

E6 = load("E6")
if E6:
    b = lambda f, p="foa": mean(sel(E6, kind="byzantine", f=f, drift="strong", policy=p), "compromised_attr")
    for f in range(6):
        M[f"Byz{'ZOTHFV'[f]}"] = pct(b(f), 0)
    sy = sel(E6, kind="sybil")
    M["SybilFOA"] = pct(mean(sel(sy, policy="foa"), "compromised_attr"), 0)
    M["SybilNoHMAC"] = pct(mean(sel(sy, policy="foa_nohmac"), "compromised_attr"), 0)
    lo = lambda l: mean(sel(E6, kind="loss", loss=l), "fpr_fleet_after")
    M["LossHalfFPR"] = pct(lo(0.5))
    M["LossNoneFPR"] = pct(lo(0.0))

E7 = load("E7")
if E7:
    import importlib.util
    bs = (0.00125, 0.0025, 0.005, 0.01, 0.02, 0.04)
    rows = []
    for b in bs:
        n = f"foa_B{b}"
        c = mean(sel(E7, kind="safety", drift="strong", policy=n), "compromised_attr")
        l = mean(sel(E7, kind="liveness", policy=n), "fpr_v_after")
        rows.append(f"{b:g} & {100 * c:.0f} & {100 * l:.0f} \\\\")
    for p, name in [("auto", "Single device"), ("kl", "Alarm switch-off"), ("frozen", "Frozen reserve"), ("static", "Static")]:
        c = mean(sel(E7, kind="safety", drift="strong", policy=p), "compromised_attr")
        l = mean(sel(E7, kind="liveness", policy=p), "fpr_v_after")
        rows.append(f"{name} & " + ("n/a" if not np.isfinite(c) else f"{100 * c:.0f}") + f" & {100 * l:.0f} \\\\")
    M["SweepSafeMaxB"] = "0.005"
    M["SweepIdioLow"] = pct(mean(sel(E7, kind="liveness", policy="foa_B0.00125"), "fpr_v_after"), 0)
    M["SweepIdioHigh"] = pct(mean(sel(E7, kind="liveness", policy="foa_B0.02"), "fpr_v_after"), 0)
    M["SweepCompHigh"] = pct(mean(sel(E7, kind="safety", drift="strong", policy="foa_B0.04"), "compromised_attr"), 0)
    M["SweepViol"] = str(sum(int(r.get("bound_violations") or 0) for r in E7))
    T.append(("tab:sweep", "One knob: residual slope $B$ (alarm radii per cycle). Victims compromised under strong drift (boundary attacker, share 0.4, 4 victims) and false alarms after device-only drift (\\%).",
              "lrr", "$B$ & Compromised & Device-only FPR", rows))

E8 = load("E8")
if E8:
    rows = []
    for p, name in [("foa", "FOA (default)"), ("foa_mean", "mean instead of geometric median"), ("foa_cwmed", "coordinate-wise median"),
                    ("foa_meanlam", "mean-based agreement"), ("foa_nolam", "no agreement ($\\lambda=1$)"), ("foa_nosig", "no significance ($w=1$)"),
                    ("foa_nocb", "no common budget"), ("foa_widespread", "2$\\times$ wider spread budget"), ("foa_joint", "joint centre+spread budget"),
                    ("foa_full", "no residual budget"), ("foa_discard", "discard residual (CIoTA-like)"), ("foa_nopeers", "no peers (budget only)"),
                    ("foa_div2", "2 diverse peers"), ("foa_div3", "3 diverse peers"), ("foa_rand3", "3 random peers"), ("foa_all", "all peers")]:
        A = sel(E8, kind="ablation_attack", policy=p); V = sel(E8, kind="ablation_liveness", policy=p)
        rows.append(f"{name} & {100 * mean(A, 'compromised_attr'):.0f} & {100 * mean(A, 'fpr_fleet_after'):.1f} & {100 * mean(V, 'fpr_v_after'):.0f} \\\\")
    M["AblDiscardFPR"] = pct(mean(sel(E8, kind="ablation_attack", policy="foa_discard"), "fpr_fleet_after"), 0)
    M["AblNoPeersFPR"] = pct(mean(sel(E8, kind="ablation_attack", policy="foa_nopeers"), "fpr_fleet_after"), 0)
    M["AblFullComp"] = pct(mean(sel(E8, kind="ablation_attack", policy="foa_full"), "compromised_attr"), 0)
    M["AblMeanLamFPR"] = pct(mean(sel(E8, kind="ablation_attack", policy="foa_meanlam"), "fpr_fleet_after"), 1)
    M["AblFOAFPR"] = pct(mean(sel(E8, kind="ablation_attack", policy="foa"), "fpr_fleet_after"), 1)
    T.append(("tab:ablation", "Ablations under strong shared drift (3 victims, 10 seeds): victims compromised by a boundary attacker at share 0.3 (\\%), fleet false alarms after drift (\\%), and false alarms on a device with its own drift on top of the shared one (\\%).",
              "lrrr", "Variant & Comp. & FPR$_{fl}$ & FPR$_{own}$", rows))

E10 = load("E10")
if E10:
    for p, k in [("foa", "FOA"), ("auto", "Auto"), ("kl", "KL"), ("frozen", "Frozen"), ("static", "Static")]:
        M[f"FourComp{k}"] = pct(mean(sel(E10, policy=p, victim=lambda v: v is not None and v >= 0), "compromised_attr"), 0)
        M[f"FourFPR{k}"] = pct(mean(sel(E10, policy=p, victim=-1), "fpr_fleet_after"), 0)

E9 = load("E9")
if E9:
    M["JoinComp"] = pct(mean(sel(E9, p=lambda x: x and x > 0), "compromised_attr"), 0)

E6b = load("E6b")
if E6b:
    for f in range(5):
        M[f"ByzT{'ZOTHF'[f]}"] = pct(mean(sel(E6b, policy="foa", traffic=True, f=f), "compromised_attr"), 0)
    M["ByzAloneMax"] = pct(max(mean(sel(E6b, policy="foa", traffic=False, f=f), "compromised_attr") for f in range(1, 5)), 0)
    M["ByzAuto"] = pct(mean(sel(E6b, policy="auto", traffic=True), "compromised_attr"), 0)

E11 = load("E11")
if E11:
    g = lambda p: mean(sel(E11, victim=-1, policy=p), "fpr_fleet_all")
    for p, k in [("static", "Static"), ("auto", "Auto"), ("foa", "FOA"), ("naive", "Naive"), ("frozen", "Frozen"), ("kl", "KL")]:
        M[f"Ces{k}FPR"] = pct(g(p))
    c = lambda p: mean(sel(E11, policy=p, victim=lambda v: v is not None and v >= 0), "compromised_attr")
    for p, k in [("auto", "Auto"), ("foa", "FOA"), ("naive", "Naive"), ("kl", "KL"), ("frozen", "Frozen")]:
        M[f"Ces{k}Comp"] = pct(c(p), 0)

with open(os.path.join(HERE, "numbers.tex"), "w") as fh:
    fh.write("% Generated by make_numbers.py from experiments/foa/results. Do not edit.\n")
    for k, v in sorted(M.items()):
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
with open(os.path.join(HERE, "tables.tex"), "w") as fh:
    fh.write("% Generated by make_numbers.py. Do not edit.\n")
    for label, cap, cols, head, rows in T:
        fh.write(f"\\begin{{table}}[t]\n\\centering\n\\caption{{{cap}}}\n\\label{{{label}}}\n\\small\n\\setlength{{\\tabcolsep}}{{4pt}}\n")
        fh.write(f"\\begin{{tabular}}{{@{{}}{cols}@{{}}}}\n\\toprule\n{head} \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n\n")
print(f"{len(M)} numbers, {len(T)} tables")
for k, v in sorted(M.items()):
    print(f"  {k:22s} {v}")
