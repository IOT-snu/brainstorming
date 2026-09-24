"""Compact 3-panel figure of the synthetic proof of concept, sized for a slide."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sim_toa as S

plt.rcParams.update({"font.family": "Helvetica", "font.size": 12})
cal = np.random.default_rng(99).normal(size=(200000, S.D))
tau = np.quantile(np.linalg.norm(cal, axis=1), 0.99)

POL = [("naive", "Naive adaptive", "#D70015"),
       ("consistency_gate", "Consistency gate", "#FF9F0A"),
       ("budget_freeze", "Freeze budget", "#AF52DE"),
       ("toa", "Threat-Orthogonal (ours)", "#0071E3")]


def avg(policy, until):
    R, F = [], []
    for sd in S.SEEDS:
        rng = np.random.default_rng(sd)
        u, b = S.make_world(rng)
        r, f = S.run(policy, rng, u, b, tau, until)
        R.append(r); F.append(f)
    return np.mean(R, 0) * 100, np.mean(F, 0) * 100


fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
# Draw ours first as a wide translucent band, then the others on top with distinct dash
# patterns, so lines that sit on exactly the same values (all at 100% detection) stay visible.
STYLE = {"toa": dict(lw=7, alpha=0.35, ls="-", z=1),
         "consistency_gate": dict(lw=2.4, alpha=1, ls=(0, (6, 3)), z=3),
         "budget_freeze": dict(lw=2.4, alpha=1, ls=(3, (1.5, 2.5)), z=4),
         "naive": dict(lw=2.2, alpha=1, ls="-", z=5)}
for key, name, c in sorted(POL, key=lambda x: STYLE[x[0]]["z"]):
    rA, fA = avg(key, S.CYCLES)
    _, fB = avg(key, 45)
    k = STYLE[key]
    for a_, y in zip(ax, [rA, fA, fB]):
        a_.plot(y, color=c, lw=k["lw"], alpha=k["alpha"], ls=k["ls"], zorder=k["z"],
                label=name if a_ is ax[0] else None)
ax[0].text(100, 91, "consistency gate, freeze budget\nand ours all stay at 100%", ha="center", va="top",
           fontsize=10.5, color="#424245")
titles = ["Attack still detected (%)", "False alarms (%)", "False alarms (%), attacker leaves at 45"]
for i, a in enumerate(ax):
    a.axvspan(S.DRIFT_START, S.DRIFT_END, color="#F0F0F3", zorder=0)
    a.axvline(S.POISON_START, color="#C7C7CC", ls="--", lw=1)
    a.spines[["top", "right"]].set_visible(False)
    a.spines[["left", "bottom"]].set_color("#C7C7CC")
    a.tick_params(colors="#86868B")
    a.set_title(titles[i], loc="left", fontsize=13, color="#1D1D1F", fontweight="bold")
    a.set_xlabel("adaptation cycle", color="#86868B")
ax[0].set_ylim(-3, 103)
ax[1].set_ylim(-1, 70); ax[2].set_ylim(-1, 70)
h, l = ax[0].get_legend_handles_labels()
order = [l.index(n) for n in ["Naive adaptive", "Consistency gate", "Freeze budget", "Threat-Orthogonal (ours)"]]
ax[0].legend([h[i] for i in order], [l[i] for i in order], loc="center left", bbox_to_anchor=(0.02, 0.42), fontsize=10.5, frameon=False, handlelength=3.2)
fig.tight_layout()
fig.savefig("fig_slide.png", dpi=170, facecolor="white")
print("wrote fig_slide.png")
