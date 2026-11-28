"""
Figures for the extended edition (main_full.tex). Run from the repo root: python3 paper/make_full_figs.py
fig_frog.pdf    : the boiling frog in action (E3 traces, classic boundary poisoner, p = 0.3, strong drift)
fig_compare.pdf : compromise across attacks and conditions for every rule (E3, E3_ciota, E4)
"""
import os, pickle, re
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "experiments/foa/results"; OUT = "paper/figures"
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
NAME = {"naive": "Learn everything", "auto": "Lone device", "clip": "Limit each step", "frozen": "WARDEN-style screening",
        "kl": "Kloft-Laskov switch-off", "or": "DriftXpert-style gate", "toa": "TOA (oracle)", "ciota": "CIoTA (same-model)", "foa": "FOA (ours)"}
COL = {"auto": "#7f7f7f", "or": "#ED7D31", "frozen": "#C9A000", "kl": "#5B9BD5", "ciota": "#70AD47", "foa": "#264478", "naive": "#B05050", "clip": "#9467bd", "toa": "#aaaaaa"}

# ---- fig_frog: mean detection of the target attack and false alarms over time
o = pickle.load(open(f"{R}/E3.pkl", "rb"))
pols = ["auto", "or", "kl", "frozen", "foa"]
rec = {p: [] for p in pols}; fpr = {p: [] for p in pols}
for r, tr in o:
    if tr and r["mode"] == "boundary" and abs(r["p"] - 0.3) < 1e-9 and r["policy"] in pols:
        rec[r["policy"]].append(np.asarray(tr["rec"], float)); fpr[r["policy"]].append(np.asarray(tr["fpr"], float))
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.2))
for p in pols:
    if not rec[p]: continue
    ax[0].plot(100 * np.mean(rec[p], 0), color=COL[p], lw=1.6 if p == "foa" else 1.1, ls="--" if p == "auto" else "-", label=NAME[p] + (" (same as gate)" if p == "auto" else ""), zorder=4 if p == "auto" else 3)
    ax[1].plot(100 * np.mean(fpr[p], 0), color=COL[p], lw=1.6 if p == "foa" else 1.1, ls="--" if p == "auto" else "-")
for a in ax:
    a.axvspan(40, 160, color="#f0f0f0", zorder=0); a.set_xlabel("learning cycle")
ax[0].set_ylabel("target attack detected (%)"); ax[1].set_ylabel("victim false alarms (%)")
ax[0].text(100, 103, "drift ramps, poisoner active", fontsize=6.5, ha="center")
ax[0].legend(fontsize=6.5, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.08))
n = len(rec["foa"]); fig.tight_layout(); fig.savefig(f"{OUT}/fig_frog.pdf"); print("frog runs per rule:", n)

# ---- fig_compare: compromise across conditions
e3 = pd.read_csv(f"{R}/E3.csv"); e4 = pd.read_csv(f"{R}/E4.csv")
tab = (e3.pivot_table(index="policy", columns="mode", values="compromised_attr", aggfunc="mean") * 100)
allc = e3.groupby("policy")["compromised_attr"].mean() * 100
txt = open(f"{R}/E3_ciota.txt").read()
cio = [float(x) for x in re.search(r"^ciota\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", txt, re.M).groups()]
bot = e4[(e4.drift == "strong") & (e4.infected == 2)].groupby("policy")["compromised_attr"].mean() * 100
conds = ["Strong drift,\nall attacks", "Classic boundary\npoisoner", "Hiding in the\nclean core", "One-model botnet\n(2 of 3 infected)"]
rows = {}
for p in ["auto", "or", "frozen", "kl", "foa"]:
    rows[p] = [allc[p], tab.loc[p, "boundary"], tab.loc[p, "core"], bot.get(p, np.nan)]
rows["ciota"] = [cio[3], cio[0], cio[1], bot["ciota"]]
order = ["auto", "or", "frozen", "kl", "ciota", "foa"]
fig, ax = plt.subplots(figsize=(7.0, 2.4)); x = np.arange(4); bw = 0.13
for k, p in enumerate(order):
    v = np.array(rows[p], float); xx = x + (k - 2.5) * bw
    m = ~np.isnan(v); ax.bar(xx[m], v[m], bw * 0.92, color=COL[p], label=NAME[p], zorder=3)
    for xi, vi in zip(xx[m], v[m]):
        ax.text(xi, vi + 1.5, f"{vi:.0f}", ha="center", fontsize=5.8)
ax.set_xticks(x); ax.set_xticklabels(conds); ax.set_ylabel("compromised runs (%)"); ax.set_ylim(0, 110)
ax.yaxis.grid(True, color="#e0e0e0", zorder=0); ax.legend(ncol=6, fontsize=6.3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.16))
fig.tight_layout(); fig.savefig(f"{OUT}/fig_compare.pdf")
pd.DataFrame(rows, index=["all", "boundary", "core", "botnet"]).round(1).to_csv(f"{OUT}/fig_compare.csv")
print(pd.DataFrame(rows, index=["all", "boundary", "core", "botnet"]).round(1))
