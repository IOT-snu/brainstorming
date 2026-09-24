"""Explanatory diagrams for the beginner read-up. Run: python3 concept_figs.py"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

BLUE, RED, GRAY, INK, GREEN = "#0071E3", "#D70015", "#86868B", "#1D1D1F", "#248A3D"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 11})
rng = np.random.default_rng(3)


def base(ax, title):
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK)


# 1. How an anomaly detector sees traffic
fig, ax = plt.subplots(figsize=(6.2, 4.2))
base(ax, "How our detector sees traffic")
n = rng.normal(0, 0.6, (250, 2))
a = rng.normal([4.2, 1.4], 0.35, (60, 2))
ax.scatter(*n.T, s=8, color=BLUE, alpha=0.5, label="normal packets")
ax.scatter(*a.T, s=10, color=RED, alpha=0.7, label="attack packets")
ax.add_patch(Circle((0, 0), 1.9, fill=False, lw=2, ls="--", color=INK))
ax.plot(0, 0, "k+", ms=14, mew=2)
ax.annotate("centre", (0, 0), (-1.3, -2.6), arrowprops=dict(arrowstyle="->", color=GRAY), color=GRAY)
ax.annotate("boundary = centre + spread\ninside: normal, outside: alarm", (1.35, 1.35), (-2.8, 2.5),
            arrowprops=dict(arrowstyle="->", color=GRAY), color=GRAY, fontsize=9.5)
ax.annotate("attack: far outside\nso it raises an alarm", (4.2, 1.4), (2.3, -2.4),
            arrowprops=dict(arrowstyle="->", color=RED), color=RED, fontsize=9.5)
ax.set_xlim(-3.3, 5.6); ax.set_ylim(-3.1, 3.2)
ax.legend(loc="upper right", fontsize=9, frameon=False)
fig.tight_layout(); fig.savefig("fig_detector.png", dpi=180); plt.close(fig)

# 2. Boiling frog: the boundary is walked toward the attack
fig, ax = plt.subplots(figsize=(6.2, 5.2))
base(ax, "Boiling-frog poisoning, step by step")
ax.scatter(*a.T, s=10, color=RED, alpha=0.7)
for k, (cx, r) in enumerate([(0, 1.9), (0.8, 2.3), (1.6, 2.8), (2.4, 3.3)]):
    ax.add_patch(Circle((cx, 0.28 * cx), r, fill=False, lw=1.8, color=INK, alpha=0.25 + 0.25 * k,
                        ls="--" if k < 3 else "-"))
    ax.plot(cx, 0.28 * cx, "+", color=INK, ms=10, alpha=0.3 + 0.23 * k)
for k in range(3):
    p = np.array([1.5 + 0.8 * k, 0.4 + 0.25 * k])
    ax.plot(*p, "o", color="#FF9F0A", ms=7)
ax.text(-3.0, -5.3, "orange = poison packets placed just inside the edge.\nEach cycle the detector learns them as normal, so its\ncentre moves and its edge grows, until the attack is inside.",
        fontsize=9.5, color=GRAY)
ax.set_xlim(-3.3, 6.2); ax.set_ylim(-5.6, 4.4)
fig.tight_layout(); fig.savefig("fig_boilingfrog.png", dpi=180); plt.close(fig)

# 3. TOA: split every update
fig, ax = plt.subplots(figsize=(6.2, 4.2))
base(ax, "Threat-Orthogonal Adaptation: split every update")
ax.scatter(*a.T, s=10, color=RED, alpha=0.7)
ax.add_patch(Circle((0, 0), 1.9, fill=False, lw=2, color=INK))
o = np.array([0, 0]); prop = np.array([1.2, 1.4])
t_hat = np.array([4.2, 1.4]); t_hat = t_hat / np.linalg.norm(t_hat)
toward = (prop @ t_hat) * t_hat; side = prop - toward
def arr(p0, p1, c, lw=2.4, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=16, color=c, lw=lw, ls=ls))
arr(o, prop, GRAY, 2, "--"); arr(o, side, GREEN); arr(o, toward, RED)
ax.text(prop[0] + 0.1, prop[1] + 0.1, "update the detector\nwants to make", color=GRAY, fontsize=9.5)
ax.text(side[0] - 2.4, side[1] + 0.25, "sideways part:\napplied in full", color=GREEN, fontsize=9.5)
ax.text(toward[0] + 0.15, toward[1] - 0.75, "part toward the attack:\nonly a small budget allowed", color=RED, fontsize=9.5)
ax.text(3.35, 2.2, "known attack", color=RED, fontsize=9.5)
ax.set_xlim(-3.3, 5.8); ax.set_ylim(-2.6, 3.0)
fig.tight_layout(); fig.savefig("fig_toa.png", dpi=180); plt.close(fig)
print("wrote fig_detector.png, fig_boilingfrog.png, fig_toa.png")
