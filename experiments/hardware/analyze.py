"""
Analysis of the ESP8266 testbed logs (25 Nov 2026). Run: python3 analyze.py  -> prints the tables and
writes hardware_results.png. COM14 is the monitor node (Node 0, carries the INA226 PWR lines, which
measure Node 1), COM10 is Node 1, COM15 is Node 2.
"""
import glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    foa, pwr = [], []
    for line in open(path, errors="replace"):
        ts, _, r = line.partition(" ")
        v = r.strip().split(",")
        try:
            if v[0] == "FOA" and len(v) == 18:
                foa.append([float(ts)] + [float(x) for x in v[1:]])
            elif v[0] == "PWR" and len(v) == 6:
                pwr.append([float(ts)] + [float(x) for x in v[1:]])
        except ValueError:
            pass
    return np.array(foa), np.array(pwr)


def main():
    fig, ax = plt.subplots(2, 2, figsize=(9, 5), sharex="col")
    for col, run in enumerate(("IDLE4", "energy1")):
        pwr, node1 = None, None
        print(f"== {run}")
        print("node cycles minutes both-peers  propose step sign verify(2) ms   alarms(last10)  spread(last)")
        for p in sorted(glob.glob(os.path.join(HERE, run, "COM*.log"))):
            f, w = load(p)
            if len(w):
                pwr = w
            n = int(f[0, 1])
            if n == 1:
                node1 = f
            ver = f[f[:, 6] == 2, 16]
            print(f"{n:4d} {len(f):6d} {(f[-1, 0] - f[0, 0]) / 60:7.1f} {100 * np.mean(f[:, 6] == 2):9.1f}%  "
                  f"{np.median(f[:, 13]) / 1000:6.2f} {np.median(f[:, 14]) / 1000:5.2f} {np.median(f[:, 15]) / 1000:4.2f} "
                  f"{np.median(ver) / 1000:6.2f}      {100 * f[-10:, 4].mean():6.1f}%        {f[-1, 11]:.3f}")
            t = (f[:, 0] - f[0, 0]) / 60
            ax[0, col].plot(t, 100 * f[:, 4], label=f"node {n}", lw=1.4)
            ax[1, col].plot(t, f[:, 11], lw=1.4)
        if pwr is not None:
            t, mw = pwr[:, 0], pwr[:, 5]
            print(f"power (Node 1): {len(mw)} samples, {pwr[:, 2].mean() / 1000:.3f} V, {pwr[:, 4].mean():.2f} mA, "
                  f"{mw.mean():.1f} mW, {mw.mean() * 7.77 / 1000:.2f} J per 7.77 s cycle")
            excess = []
            for e in node1[:, 0]:
                i, j = np.searchsorted(t, [e - 3.8, e + 3.8])
                rel, q = t[i:j] - e, mw[i:j]
                win = (rel >= -0.5) & (rel < 0.1)
                if len(q) > 100 and win.any():
                    excess.append((q[win].mean() - np.median(q[np.abs(rel) > 1.5])) * 0.6)
            ex = np.array(excess)
            print(f"energy in the 0.6 s learning window minus normal running: {ex.mean():.2f} +- {1.96 * ex.std(ddof=1) / np.sqrt(len(ex)):.2f} mJ")
    ax[0, 0].set_title("Run IDLE4: all three started together", loc="left", fontsize=10)
    ax[0, 1].set_title("Run energy1: node 2 already collapsed", loc="left", fontsize=10)
    ax[0, 0].set_ylabel("false alarms (%)"); ax[1, 0].set_ylabel("spread / calibrated")
    for a in ax.ravel():
        a.spines[["top", "right"]].set_visible(False); a.grid(color="#e8e7e3")
    for a in ax[0]:
        a.set_ylim(0, 105)
    for a in ax[1]:
        a.set_xlabel("minutes after first learning cycle shown"); a.set_ylim(0, 1)
    ax[0, 0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "hardware_results.png"), dpi=200, facecolor="white")


if __name__ == "__main__":
    main()
