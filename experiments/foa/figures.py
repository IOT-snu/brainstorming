"""
All paper figures, from the pickled results. Run: python3 figures.py [names...]  -> figures/*.pdf|png
"""
import os, pickle, sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import style
from style import COLOR, NAME, INK, INK2, MUTED

HERE = os.path.dirname(os.path.abspath(__file__))
RES, FIG = os.path.join(HERE, "results"), os.path.join(HERE, "figures")
style.setup()
W1, W2 = 3.45, 7.1          # IEEE column and page widths, inches


def load(name):
    p = os.path.join(RES, name + ".pkl")
    return pickle.load(open(p, "rb")) if os.path.exists(p) else None


def ci(x):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], dtype=float)
    if len(x) < 2:
        return (float(np.mean(x)) if len(x) else np.nan), 0.0
    return float(np.mean(x)), float(1.96 * np.std(x, ddof=1) / np.sqrt(len(x)))


# ---------------------------------------------------------------- theory (synthetic)
def fig_theory():
    S = load("S")
    if S is None:
        return
    fig, ax = plt.subplots(1, 3, figsize=(W2, 2.15))
    Bs = sorted({r["B"] for r in S["S1"]})
    T = 500
    for drift, key, lab, mk in ((False, "foa", "no drift", "o"), (True, "auto", "with honest drift", "s")):
        med, lo = [], []
        for B in Bs:
            t = [r["ttc"] if r["ttc"] is not None else np.inf for r in S["S1"] if r["B"] == B and r["drift"] == drift]
            lo.append(min(t)); med.append(np.median(t))
        y = [min(v, T) for v in lo]
        ax[0].plot(Bs, y, marker=mk, ms=4, color=COLOR[key], label=f"earliest compromise, {lab}", lw=1.3)
        for B, v in zip(Bs, lo):
            if not np.isfinite(v):
                ax[0].annotate("", (B, T + 30), (B, T), arrowprops=dict(arrowstyle="-|>", color=COLOR[key], lw=0.8))
    tb = [min(r["t_closed"] for r in S["S1"] if r["B"] == B) for B in Bs]
    ax[0].plot(Bs, tb, color=INK, lw=1.0, label="Theorem 1 lower bound")
    ax[0].set_xscale("log"); ax[0].set_ylim(0, T + 60)
    ax[0].set_xlabel("residual budget slope B (spreads per cycle)"); ax[0].set_ylabel("cycles until detection < 50%")
    ax[0].set_title("a. Time to compromise vs budget"); ax[0].legend(loc="upper right", fontsize=6)
    ax[0].text(Bs[0], T + 45, "never within 500 cycles", fontsize=6, color=MUTED, va="bottom")

    vs = sorted({r["v"] for r in S["S2"]})
    M = np.array([[np.mean([r["lost"] for r in S["S2"] if r["B"] == B and r["v"] == v]) for v in vs] for B in Bs])
    cmap = LinearSegmentedColormap.from_list("b", ["#ffffff", "#cde2fb", "#3987e5", "#104281"])
    ax[1].imshow(M, origin="lower", cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax[1].set_xticks(range(len(vs))); ax[1].set_xticklabels([f"{v:g}" for v in vs], rotation=45)
    ax[1].set_yticks(range(len(Bs))); ax[1].set_yticklabels([f"{b:g}" for b in Bs])
    ax[1].grid(False)
    ax[1].set_xlabel("device-only honest drift rate v"); ax[1].set_ylabel("budget slope B")
    ax[1].set_title("b. Liveness: drift the device loses")
    for i in range(len(Bs)):
        for j in range(len(vs)):
            if M[i, j] > 0:
                ax[1].text(j, i, "lost", ha="center", va="center", fontsize=5.5, color="white" if M[i, j] > 0.5 else INK)

    alphas = sorted({r["alpha"] for r in S["S3"]})
    mx = [max(r["bias_over_r"] for r in S["S3"] if r["alpha"] == a) for a in alphas]
    aa = np.linspace(0, 0.48, 100)
    from robust import minsker_constant
    ax[2].plot(aa, [minsker_constant(a) for a in aa], color=INK, lw=1.0, label="bound $C_\\alpha$ (Minsker 2015)")
    ax[2].plot(alphas, mx, marker="o", ms=4, color=COLOR["foa"], lw=1.6, label="worst observed, 400 trials")
    ax[2].set_xlabel("fraction of Byzantine peers $\\alpha$"); ax[2].set_ylabel("consensus bias / honest radius")
    ax[2].set_title("c. Byzantine peers move the median little"); ax[2].legend(loc="upper left", fontsize=6)
    ax[2].set_ylim(0, 2.2)
    fig.tight_layout(w_pad=1.2)
    style.save(fig, os.path.join(FIG, "fig_theory"))


def rows_of(name, **filt):
    R = load(name) or []
    out = []
    for r, tr in R:
        if all((r.get(k) == v) if not callable(v) else v(r.get(k)) for k, v in filt.items()):
            out.append((r, tr))
    return out


def mean_trace(rows, key):
    xs = [tr[key] for _, tr in rows if tr is not None and tr.get(key) is not None]
    return np.nanmean(np.vstack(xs), 0) if xs else None


def drift_band(ax, a=40, b=160, label="honest drift ramps"):
    ax.axvspan(a, b, color="#f3f2ee", zorder=0, lw=0)
    if label:
        ax.text((a + b) / 2, 0.985, label, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=6, color=MUTED)


LIVE = ["static", "frozen", "kl", "auto", "naive", "foa"]


def fig_liveness():
    fig, ax = plt.subplots(1, 3, figsize=(W2, 2.2), sharey=True)
    panels = [("common_moderate", "fpr", "a. Moderate shared drift (fleet)"), ("common_strong", "fpr", "b. Strong shared drift (fleet)"),
              ("idio", "fpr", "c. Device-only drift (that device)")]
    for a, (sc, key, title) in zip(ax, panels):
        for p in LIVE:
            tr = mean_trace(rows_of("E1", scenario=sc, policy=p), key)
            if tr is not None:
                style.line(a, np.arange(len(tr)), 100 * tr, p)
        drift_band(a, *((60, 120) if sc == "idio" else (40, 160)))
        a.set_title(title); a.set_xlabel("learning cycle"); a.set_xlim(0, 239)
    ax[0].set_ylabel("false alarms (%)"); ax[0].set_ylim(0, 100)
    h, l = ax[1].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.06), fontsize=6.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    style.save(fig, os.path.join(FIG, "fig_liveness"))


def rate_ci(xs):
    xs = np.asarray([x for x in xs if x is not None and np.isfinite(x)], float)
    if not len(xs):
        return np.nan, 0.0
    m = xs.mean()
    return 100 * m, 100 * 1.96 * np.sqrt(max(m * (1 - m), 1e-9) / len(xs))


ATT = ["naive", "auto", "or", "kl", "clip", "frozen", "toa", "foa"]


def fig_headline():
    """E3: attack hidden in strong honest drift. a) attack-attributable compromise vs share;
    b) safety vs liveness plane; c) victim detection over time at share 0.3."""
    fig, ax = plt.subplots(1, 3, figsize=(W2, 2.35))
    ps = [0.1, 0.2, 0.3, 0.4]
    for pol in ATT:
        ys, es = zip(*[rate_ci([r["compromised_attr"] for r, _ in rows_of("E3", policy=pol, p=p, mode="boundary")]) for p in ps])
        style.line(ax[0], ps, ys, pol, marker="o", ms=3)
    ax[0].set_xlabel("attacker share of the victim's traffic"); ax[0].set_ylabel("victims compromised (%)")
    ax[0].set_title("a. Boundary attacker under drift"); ax[0].set_ylim(-3, 103); ax[0].set_xticks(ps)
    for pol in ATT + ["static"]:
        R = [r for r, _ in rows_of("E3", policy=pol)]
        L = [r for r, _ in rows_of("E1", policy=pol, scenario="common_strong")]
        if not R and pol != "static":
            continue
        y = 100 * np.mean([r["compromised_attr"] for r in R]) if R else 0.0
        x = 100 * np.mean([r["fpr_fleet_after"] for r in L])
        ax[1].scatter([x], [y], s=46 if pol == "foa" else 26, color=COLOR[pol], zorder=5, edgecolor="white", linewidth=0.8)
        lab = {"auto": "single device", "or": "outlier-ratio gate", "kl": "alarm switch-off", "clip": "clipping",
               "frozen": "frozen reserve", "naive": "naive", "toa": "TOA (oracle)", "static": "static", "foa": "FOA"}[pol]
        off = {"auto": (4, 4), "or": (4, -8), "kl": (-46, 7), "clip": (-6, 8), "frozen": (4, -10), "naive": (4, 3),
               "toa": (4, 3), "static": (-8, 8), "foa": (5, -2)}[pol]
        if pol in ("foa", "static"):      # every other point is identified by the shared legend
            ax[1].annotate(lab, (x, y), xytext=(5, -2) if pol == "foa" else (-10, 8), textcoords="offset points", fontsize=6.5,
                           color=INK if pol == "foa" else INK2, fontweight="bold" if pol == "foa" else "normal")
    ax[1].set_xlabel("false alarms after honest drift (%)"); ax[1].set_ylabel("victims compromised (%)")
    ax[1].set_title("b. Safety and liveness together"); ax[1].set_xlim(-3, 85); ax[1].set_ylim(-5, 105)
    for pol in ["auto", "kl", "frozen", "foa"]:
        tr = mean_trace(rows_of("E3", policy=pol, p=0.3, mode="boundary"), "rec")
        if tr is not None:
            style.line(ax[2], np.arange(len(tr)), 100 * tr, pol)
    drift_band(ax[2], label="")
    ax[2].axvline(40, color=COLOR["naive"], lw=0.8); ax[2].text(42, 5, "poisoning starts", fontsize=6, color=COLOR["naive"])
    ax[2].set_xlabel("learning cycle"); ax[2].set_ylabel("target attack detected (%)"); ax[2].set_ylim(-3, 103)
    ax[2].set_title("c. Detection over time, share 0.3"); ax[2].set_xlim(0, 239)
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=8, bbox_to_anchor=(0.5, -0.07), fontsize=6)
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.0)
    style.save(fig, os.path.join(FIG, "fig_headline"))


def bars(ax, groups, series, value, colors, labels, width=0.8):
    n = len(series)
    for j, sname in enumerate(series):
        xs = np.arange(len(groups)) + (j - (n - 1) / 2) * width / n
        vals, errs = zip(*[value(g, sname) for g in groups])
        ax.bar(xs, vals, width / n - 0.02, yerr=errs, color=colors[j], label=labels[j], error_kw=dict(lw=0.6, capsize=1.5, ecolor=INK2))
    ax.set_xticks(np.arange(len(groups)))


def fig_monoculture():
    """E4: a botnet compromises k of the three instances of one camera model and poisons them together."""
    pols = ["auto", "ciota", "foa_same", "foa", "foa_all"]
    fig, ax = plt.subplots(1, 1, figsize=(W1, 2.3))
    val = lambda k, p: rate_ci([r["compromised_attr"] for r, _ in rows_of("E4", policy=p, infected=k, drift="strong")])
    bars(ax, [1, 2, 3], pols, val, [COLOR[p] for p in pols], [NAME[p] for p in pols])
    n = len(pols)
    for i, k in enumerate([1, 2, 3]):
        for j, p in enumerate(pols):
            v = val(k, p)[0]
            if v < 1:
                ax.text(i + (j - (n - 1) / 2) * 0.8 / n, 2, "0", ha="center", va="bottom", fontsize=6, color=COLOR[p], fontweight="bold")
    ax.set_xticklabels(["1 of 3", "2 of 3", "3 of 3"]); ax.set_xlabel("same-model cameras infected (strong drift)")
    ax.set_ylabel("infected cameras compromised (%)"); ax.set_ylim(0, 112)
    ax.legend(fontsize=5.5, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.25))
    fig.tight_layout()
    style.save(fig, os.path.join(FIG, "fig_monoculture"))


def fig_freeze():
    """E5: decoys trip stop-learning gates during drift; the attacker leaves at cycle 100."""
    pols = ["kl", "or", "frozen", "auto", "foa"]
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.15), gridspec_kw=dict(width_ratios=[1.5, 1]))
    for p in pols:
        tr = mean_trace(rows_of("E5", policy=p, attacker=True, p=0.1), "fpr")
        if tr is not None:
            style.line(ax[0], np.arange(len(tr)), 100 * tr, p)
        trc = mean_trace(rows_of("E5", policy=p, attacker=False), "fpr")
        if trc is not None and p in ("kl", "foa"):
            ax[0].plot(np.arange(len(trc)), 100 * trc, color=COLOR[p], lw=0.9, ls=(0, (2, 1.5)), alpha=0.8)
    ax[0].axvspan(40, 100, color="#fdecec", zorder=0, lw=0)
    ax[0].text(70, 0.985, "decoys (10%)", transform=ax[0].get_xaxis_transform(), ha="center", va="top", fontsize=6, color=COLOR["naive"])
    ax[0].set_xlabel("learning cycle"); ax[0].set_ylabel("victim false alarms (%)"); ax[0].set_xlim(0, 239); ax[0].set_ylim(0, 100)
    ax[0].set_title("a. Freeze attack, then honest drift (dotted: no attacker)")
    ax[0].legend(loc="upper left", fontsize=6, bbox_to_anchor=(0.0, 0.92))
    shares = [0.05, 0.1, 0.2]
    bars(ax[1], shares, pols, lambda q, p: ci([r["fpr_v_tail"] * 100 for r, _ in rows_of("E5", policy=p, attacker=True, p=q)]),
         [COLOR[p] for p in pols], [NAME[p] for p in pols])
    ax[1].set_xticklabels([f"{int(q * 100)}%" for q in shares]); ax[1].set_xlabel("decoy share of the victim's traffic")
    ax[1].set_ylabel("false alarms, last 40 cycles (%)"); ax[1].set_title("b. Lasting damage"); ax[1].set_ylim(0, 100)
    fig.tight_layout(w_pad=1.2)
    style.save(fig, os.path.join(FIG, "fig_freeze"))


def fig_gossip():
    """E6: Byzantine peers with stolen keys, and frame loss."""
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.1))
    fs = [0, 1, 2, 3, 4, 5]
    for d, ls, lab in (("strong", "-", "with strong shared drift"), ("none", (0, (3, 2)), "no drift")):
        ys, es = zip(*[rate_ci([r["compromised_attr"] for r, _ in rows_of("E6", kind="byzantine", f=f, drift=d, policy="foa")]) for f in fs])
        ax[0].plot(fs, ys, marker="o", ms=3, lw=2.0 if d == "strong" else 1.3, ls=ls, color=COLOR["foa"], label=f"FOA, {lab}")
    ax[0].text(0.1, 62, "mean-based and no-common-budget\nvariants give identical curves", fontsize=5.5, color=MUTED)
    ax[0].axvline(3.5, color=MUTED, lw=0.8); ax[0].text(3.6, 50, "half of the\n7 peers", fontsize=6, color=MUTED)
    ax[0].set_xlabel("Byzantine peers (of 7)"); ax[0].set_ylabel("victim compromised (%)"); ax[0].set_ylim(-3, 103)
    ax[0].set_title("a. Peers with stolen keys"); ax[0].legend(fontsize=6, loc="upper left")
    losses = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
    y1 = [ci([100 * r["fpr_fleet_after"] for r, _ in rows_of("E6", kind="loss", loss=l)])[0] for l in losses]
    y2 = [rate_ci([r["compromised_attr"] for r, _ in rows_of("E6", kind="loss", loss=l)])[0] for l in losses]
    ax[1].plot([100 * l for l in losses], y1, marker="o", ms=3, color=COLOR["foa"], label="fleet false alarms after drift")
    ax[1].plot([100 * l for l in losses], y2, marker="s", ms=3, color=COLOR["naive"], label="victim compromised")
    ax[1].set_xlabel("frames lost (%)"); ax[1].set_ylabel("%"); ax[1].set_ylim(-3, 103); ax[1].legend(fontsize=6)
    ax[1].set_title("b. Lossy radio")
    fig.tight_layout(w_pad=1.2)
    style.save(fig, os.path.join(FIG, "fig_gossip"))


def fig_frontier():
    """E7: one knob, B. Safety (compromise under drift) against liveness (device-only drift false alarms)."""
    import experiments as E
    fig, ax = plt.subplots(1, 1, figsize=(W1, 2.4))
    xs, ys = [], []
    for b in E.BSWEEP:
        n = f"foa_B{b}"
        y = rate_ci([r["compromised_attr"] for r, _ in rows_of("E7", kind="safety", drift="strong", policy=n)])[0]
        x = ci([100 * r["fpr_v_after"] for r, _ in rows_of("E7", kind="liveness", policy=n)])[0]
        xs.append(x); ys.append(y)
        ax.annotate(f"{b:g}", (x, y), xytext=(-4, -10) if y < 5 else (3, 3), textcoords="offset points", fontsize=5.5, color=INK2)
    ax.plot(xs, ys, marker="o", ms=4, color=COLOR["foa"], lw=1.8, label="FOA, labelled by budget slope B")
    for pol in ["auto", "frozen", "kl", "static"]:
        y = rate_ci([r["compromised_attr"] for r, _ in rows_of("E7", kind="safety", drift="strong", policy=pol)])[0] if pol == "auto" else np.nan
        if pol != "auto":
            y = rate_ci([r["compromised_attr"] for r, _ in rows_of("E3", policy=pol, mode="boundary", p=0.4, victim=lambda v: v in (0, 1, 4, 8))])[0] if pol != "static" else 0.0
        x = ci([100 * r["fpr_v_after"] for r, _ in rows_of("E7", kind="liveness", policy=pol)])[0]
        ax.scatter([x], [y], color=COLOR[pol], s=22, zorder=5, label=NAME[pol])
    ax.set_xlabel("device-only drift: false alarms after (%)"); ax.set_ylabel("victims compromised (%)")
    ax.set_title("Safety and liveness trade-off"); ax.legend(fontsize=5.5, loc="upper right")
    ax.set_xlim(-3, 85); ax.set_ylim(-5, 105)
    fig.tight_layout()
    style.save(fig, os.path.join(FIG, "fig_frontier"))


def fig_cesnet():
    """E11: 40 weeks of real CESNET traffic, one cycle per day."""
    fig, ax = plt.subplots(1, 2, figsize=(W2, 2.1), gridspec_kw=dict(width_ratios=[1.6, 1]))
    for p in ["static", "frozen", "kl", "auto", "naive", "foa"]:
        tr = mean_trace(rows_of("E11", victim=-1, policy=p), "fpr_fleet")
        if tr is not None:
            k = 7
            sm = np.convolve(np.nan_to_num(tr), np.ones(k) / k, mode="same")
            style.line(ax[0], np.arange(len(tr)), 100 * sm, p)
    ax[0].set_xlabel("day (after 28 days of calibration)"); ax[0].set_ylabel("fleet false alarms (%, 7-day mean)")
    ax[0].set_title("a. Real drift, no attacker"); ax[0].legend(fontsize=5.5, ncol=2)
    pols = ["naive", "auto", "kl", "frozen", "foa"]
    bars(ax[1], [0.2, 0.4], pols, lambda q, p: rate_ci([r["compromised_attr"] for r, _ in rows_of("E11", p=q, policy=p)]),
         [COLOR[p] for p in pols], [NAME[p] for p in pols])
    ax[1].set_xticklabels(["20%", "40%"]); ax[1].set_xlabel("attacker share"); ax[1].set_ylabel("victims compromised (%)")
    ax[1].set_title("b. Boiling frog on real drift"); ax[1].set_ylim(0, 105)
    fig.tight_layout(w_pad=1.2)
    style.save(fig, os.path.join(FIG, "fig_cesnet"))


FIGS = {"theory": fig_theory, "liveness": fig_liveness, "headline": fig_headline, "monoculture": fig_monoculture,
        "freeze": fig_freeze, "gossip": fig_gossip, "frontier": fig_frontier, "cesnet": fig_cesnet}


def main():
    os.makedirs(FIG, exist_ok=True)
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        try:
            FIGS[n]()
            print("figure", n)
        except Exception as e:                       # a missing result file skips its figure
            print("skipped", n, type(e).__name__, e)


if __name__ == "__main__":
    main()
