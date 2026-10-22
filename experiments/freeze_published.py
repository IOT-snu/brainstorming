"""
Freeze attack on the gating mechanisms of published adaptive defences.

WHAT THIS IS: our own simplified re-implementations of the *update-gating rule* of four published
defence families, wrapped around the same centre-and-spread detector used elsewhere in this
project. It tests the mechanism class, not the full published systems. Rule details were taken
from paper summaries and must be checked against the PDFs before citing (see literature notes).

Gates (all decide whether to apply the cycle's update; parameters fixed in advance, not tuned):
  kl      Kloft and Laskov (JMLR 2012) style switch-off: freeze while the alarm rate exceeds
          5x the clean rate.
  or      DriftXpert (arXiv 2026) style outlier-ratio gate: freeze while the current alarm rate
          exceeds 3x its own slowly-moving history (EWMA 0.1).
  rttad   RTTAD (arXiv 2026) style confident-sample rule: update only from confidently normal
          samples (inside the clean 80th-percentile radius) and stop when fewer than half the
          batch qualify.
  t2t     T2T rollback (arXiv 2606.29841) style: if the batch's mean anomaly score exceeds 2.5x
          the mean of the last five, roll the detector back to its state two cycles ago.
Comparators: naive (no gate) and auto (our signature-free rule, no gate).

ATTACKER: sends loud decoy traffic (far from normal, so it never poisons anything: every
detector simply rejects it from learning). It is active only for a window that starts when honest
drift starts. The decoys exist only to make a gate close at the wrong time.
  - kl, or, rttad: sustained decoys for a window (cost reported), then the attacker LEAVES.
  - t2t: a decoy burst every 6th cycle (just after the 5-cycle score window forgets the last
    burst), for the same window, then leaves.

HONEST DRIFT: ramps the normal traffic away from where the detector was calibrated. Naive
learning can follow it (control run without attacker). A frozen detector cannot.

OUTPUT: false alarms on honest traffic at the end of the run (after drift stopped and after the
attacker left), with and without the attacker; share of cycles the update was withheld; and the
attacker's cost in decoy packets.

Run: python3 freeze_published.py [path to nbaiot data dir]   (real-packet part runs only if data exists)
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import auto_toa as A

SEEDS = [0, 1, 2, 3, 4]
GATES = ["naive", "auto", "kl", "or", "rttad", "t2t"]
NAMES = {"naive": "Naive (no gate)", "auto": "Signature-free (no gate)", "kl": "Alarm-rate switch-off (Kloft and Laskov style)",
         "or": "Outlier-ratio gate (DriftXpert style)", "rttad": "Confident-sample stop (RTTAD style)",
         "t2t": "Score-spike rollback (T2T style)"}
DECOY_SHARE = {"kl": 0.10, "or": 0.20, "rttad": 0.50, "t2t": 0.20, "naive": 0.20, "auto": 0.20}


class World:
    def __init__(self, cal, honest, test, decoy, cycles, d0, d1, win, tail, drift):
        self.cal, self.honest, self.test, self.decoy = cal, honest, test, decoy
        self.cycles, self.d0, self.d1, self.win, self.tail, self.drift = cycles, d0, d1, win, tail, drift


def run(world, gate, attacker, seed):
    rng = np.random.default_rng(seed)
    det = A.Detector(world.cal)
    det.reset()
    tau, c = det.tau, det.c
    a0 = 1 - 0.99
    hist_or, scores, states = a0, [], []
    skipped, decoys_sent = 0, 0
    fa = []
    for t in range(world.cycles):
        B = world.honest(t, rng)
        share = DECOY_SHARE[gate]
        active = attacker and world.d0 <= t < world.d0 + world.win
        if active and (gate != "t2t" or (t - world.d0) % 6 == 0):
            k = int(len(B) * share / (1 - share))
            B = np.vstack([B, world.decoy(k, rng)]); decoys_sent += k
        r = det.score(B)
        alarm = float(np.mean(r > tau))
        score = float(np.mean(r))
        apply = True
        if gate == "kl":
            apply = alarm <= 5 * a0
        elif gate == "or":
            apply = (alarm / max(hist_or, a0)) <= 3.0
            hist_or = 0.9 * hist_or + 0.1 * alarm
        elif gate == "rttad":
            conf = B[r <= c]
            apply = len(conf) >= 0.5 * len(B)
            B = conf
        elif gate == "t2t":
            if len(scores) >= 5 and score > 2.5 * np.mean(scores[-5:]) and len(states) >= 2:
                det.mu, det.s = states[-2][0].copy(), states[-2][1]
                apply = False
            scores.append(score)
        if apply and len(B):
            det.update(B, "auto" if gate == "auto" else "naive")
        elif not apply:
            skipped += 1
        states.append((det.mu.copy(), det.s))
        fa.append(float(np.mean(det.score(world.test(t, rng)) > tau)))
    fa = np.array(fa)
    return fa, skipped / world.cycles, decoys_sent


def evaluate(world, label):
    out = {}
    for g in GATES:
        res = {}
        for att in (False, True):
            runs = [run(world, g, att, s) for s in SEEDS]
            fa = np.mean([r[0] for r in runs], 0)
            res[att] = dict(fa=fa, tail=float(np.mean(fa[-world.tail:])), skip=float(np.mean([r[1] for r in runs])),
                            decoys=float(np.mean([r[2] for r in runs])))
        out[g] = res
    print(f"\n{label}")
    print(f"{'defence':<48}{'FA no attacker':>15}{'FA after attack':>16}{'updates withheld':>18}{'decoy packets':>15}")
    for g in GATES:
        n, a = out[g][False], out[g][True]
        print(f"{NAMES[g]:<48}{n['tail']*100:>14.1f}%{a['tail']*100:>15.1f}%{a['skip']*100:>17.0f}%{a['decoys']:>15.0f}")
    return out


def synthetic():
    D, CY = 12, 200
    cal = np.random.default_rng(99).normal(size=(20000, D))
    state = {}

    def honest(t, rng):
        return shift(t) + rng.normal(size=(300, D))

    def test(t, rng):
        return shift(t) + rng.normal(size=(1000, D))

    rngw = np.random.default_rng(5)
    b = rngw.normal(size=D); b /= np.linalg.norm(b)
    u = rngw.normal(size=D); u /= np.linalg.norm(u)

    def shift(t):
        f = min(max((t - 60) / 80, 0.0), 1.0)
        return 5.0 * f * b

    def decoy(k, rng):
        return 9.0 * u + 0.6 * rng.normal(size=(k, D))

    return World(cal, honest, test, decoy, CY, 60, 140, 30, 50, shift)


def real(data_dir):
    sl = lambda X: np.sign(X) * np.log1p(np.abs(X))
    ld = lambda f: np.loadtxt(os.path.join(data_dir, f), delimiter=",", skiprows=1)
    rng0 = np.random.default_rng(123)
    benign = sl(ld("benign.csv"))
    n_cal = int(0.2 * len(benign)); cal_raw = benign[:n_cal]
    mz, sz = cal_raw.mean(0), cal_raw.std(0) + 1e-6
    Vt = np.linalg.svd((cal_raw - mz) / sz - ((cal_raw - mz) / sz).mean(0), full_matrices=False)[2]
    proj = lambda X: np.clip(((X - mz) / sz) @ Vt[:10].T, -1e3, 1e3)
    cal = proj(cal_raw)
    stream = proj(benign[n_cal:])
    train, test_b = stream[0::2], stream[1::2]
    U = sl(ld(os.path.join("mirai", "udp.csv")))
    U = proj(U[rng0.choice(len(U), 8000, replace=False)])
    per = 250; CY = len(train) // per
    s0 = np.sqrt(np.mean(np.sum((cal - cal.mean(0)) ** 2, 1)) / cal.shape[1])
    d = rng0.normal(size=cal.shape[1]); d /= np.linalg.norm(d)
    M = float(os.environ.get("DRIFT_MAG", 10.0))   # chosen so a never-learning detector fails (98% FA) while plain learning follows (2.7%)
    d0, d1 = int(CY * 0.30), int(CY * 0.60)

    def shift(t):
        f = min(max((t - d0) / max(1, d1 - d0), 0.0), 1.0)
        return M * s0 * f * d

    honest = lambda t, rng: train[t * per:(t + 1) * per] + shift(t)
    test = lambda t, rng: test_b[t * per:(t + 1) * per] + shift(t)
    decoy = lambda k, rng: U[rng.integers(0, len(U), k)]
    return World(cal, honest, test, decoy, CY, d0, d1, int(CY * 0.2), int(CY * 0.25), shift)


def cost_sweep(world, label, windows=(10, 20, 25, 30, 40, 60), seeds=tuple(range(10))):
    """How little attacking locks the alarm-rate switch-off gate? A run counts as LOCKED OUT if its
    false alarms at the end exceed 20% (the detector stayed frozen after the attacker left)."""
    print(f"\n{label}: runs locked out (false alarms > 20% at the end, attacker long gone), out of {len(seeds)}")
    print(f"{'attack window (cycles)':<26}" + "".join(f"{'decoys '+str(int(s*100))+'%':>16}" for s in (0.05, 0.10, 0.20)))
    rows = {}
    for w in windows:
        row = []
        for sh in (0.05, 0.10, 0.20):
            world.win = w; DECOY_SHARE["kl"] = sh
            runs = [run(world, "kl", True, s) for s in seeds]
            locked = sum(np.mean(r[0][-world.tail:]) > 0.20 for r in runs)
            row.append((locked, float(np.mean([r[2] for r in runs]))))
        rows[w] = row
        print(f"{w:<26}" + "".join(f"{lk:>6}/{len(seeds)} ({int(n):>5})" for lk, n in row))
    DECOY_SHARE["kl"] = 0.10; world.win = int(world.cycles * 0.15) if world.cycles < 150 else 30
    print("(brackets: total decoy packets the attacker sent)")
    return rows


def plot(results, path, title):
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), sharey=True)
    cols = {"naive": "#86868B", "kl": "#AF52DE", "or": "#FF9F0A", "rttad": "#D70015", "t2t": "#248A3D", "auto": "#0071E3"}
    for j, g in enumerate(["kl", "or", "t2t"]):
        ax[j].plot(results[g][False]["fa"] * 100, color="#C7C7CC", lw=2, label="same defence, no attacker")
        ax[j].plot(results[g][True]["fa"] * 100, color=cols[g], lw=2.6, label="same defence, attacker present then leaves")
        ax[j].plot(results["auto"][True]["fa"] * 100, color=cols["auto"], lw=2.2, ls="--", label="ours (no gate), same attacker")
        ax[j].set_title(NAMES[g], loc="left", fontsize=10.5, fontweight="bold")
        ax[j].spines[["top", "right"]].set_visible(False); ax[j].set_xlabel("adaptation cycle")
    ax[0].set_ylabel("false alarms on honest traffic (%)"); ax[0].set_ylim(-1, 100)
    ax[0].legend(loc="upper left", fontsize=8.5, frameon=False)
    fig.suptitle(title, fontsize=10, color="#86868B", x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(path, dpi=160, facecolor="white"); plt.close(fig)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    lines = []
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        syn = evaluate(synthetic(), "SYNTHETIC drift world (5 seeds). FA = false alarms over the last 50 cycles")
        cost_sweep(synthetic(), "SYNTHETIC, alarm-rate switch-off gate")
    print(buf.getvalue(), end=""); lines.append(buf.getvalue())
    plot(syn, os.path.join(here, "freeze_published_synthetic.png"), "Synthetic drift world, 5 seeds. Attacker sends loud decoy traffic only; it never poisons.")
    data = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "data", "nbaiot")
    if os.path.exists(os.path.join(data, "benign.csv")) and os.path.isdir(os.path.join(data, "mirai")):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rl = evaluate(real(data), "REAL N-BaIoT doorbell packets with an injected gradual drift; decoys are real Mirai udp packets (5 seeds, last 25% of cycles)")
            cost_sweep(real(data), "REAL packets, alarm-rate switch-off gate", windows=(3, 5, 8, 12, 15, 20))
        print(buf.getvalue(), end=""); lines.append(buf.getvalue())
        plot(rl, os.path.join(here, "freeze_published_real.png"), "Real N-BaIoT doorbell packets plus injected gradual drift; decoys are real Mirai udp packets. 5 seeds.")
    else:
        print("\n(real-packet part skipped: no data at", data, ")")
    open(os.path.join(here, "freeze_published_results.txt"), "w").write("".join(lines))


if __name__ == "__main__":
    main()
