"""
Signature-free ("auto") Threat-Orthogonal Adaptation, tested on real N-BaIoT traffic and on
synthetic drift.

Idea: to move the detector without raising alarms, poison must sit inside the boundary, and it
cannot look like a genuine shift of the whole traffic cloud. Honest drift moves the whole cloud.
  Step 1 (core learning): learn centre and spread only from the dense core of accepted traffic
          (points within the clean-data 80th-percentile radius). Poison parked near the boundary
          then has no pull. Honest drift still moves the core.
  Step 2 (whole-cloud support): a real shift of the cloud also shifts its outer ring. If the core
          moves but the outer ring does not follow, the move is not supported and is scaled down.
No attack signatures, no labels.

Attackers:
  boundary  poison just inside the alarm boundary (classic boiling frog)
  core      adaptive: knows the defense and hides poison just inside the core radius

Run: python3 auto_toa.py /path/to/nbaiot_data     (see nbaiot_check.py for the data layout)
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ETA = 0.5
SEEDS = [0, 1, 2, 3, 4]
Q_CORE = 0.8


class Detector:
    """Centre + spread detector with a pluggable update policy."""

    def __init__(self, cal, tau_q=0.99):
        self.mu0 = cal.mean(0)
        self.D = cal.shape[1]
        self.s0 = np.sqrt(np.mean(np.sum((cal - self.mu0) ** 2, 1)) / self.D)
        r = np.linalg.norm(cal - self.mu0, axis=1) / self.s0
        self.tau = np.quantile(r, tau_q)
        self.c = np.quantile(r, Q_CORE)                       # core radius, in spreads
        core = cal[r <= self.c]
        self.kappa = np.sqrt(np.mean(np.sum((core - self.mu0) ** 2, 1)) / self.D) / self.s0
        # Whole-cloud support calibration: shift clean data by small steps and record how much the
        # outer ring's mean moves along the shift compared with the core's.
        rng = np.random.default_rng(7)
        ratios = []
        for _ in range(40):
            d = rng.normal(size=self.D); d /= np.linalg.norm(d)
            X = cal + 0.3 * self.s0 * d
            rr = np.linalg.norm(X - self.mu0, axis=1) / self.s0
            acc = X[rr <= self.tau]; ra = rr[rr <= self.tau]
            dc = (acc[ra <= self.c].mean(0) - self.mu0) @ d
            ds = (acc[ra > self.c].mean(0) - self.mu0) @ d
            ratios.append(ds / max(dc, 1e-9))
        self.beta = float(np.median(ratios))
        ra_cal = r[r <= self.tau]
        self.f0 = float(np.mean(ra_cal > self.c))              # clean share of accepted traffic in the outer ring

    def reset(self):
        self.mu, self.s = self.mu0.copy(), self.s0

    def score(self, X):
        return np.linalg.norm(X - self.mu, axis=1) / self.s

    def update(self, B, policy):
        r = self.score(B)
        acc, ra = B[r <= self.tau], r[r <= self.tau]
        if len(acc) == 0 or policy == "static":
            return
        if policy == "naive":
            mu_p = self.mu + ETA * (acc.mean(0) - self.mu)
            self.s = self.s + ETA * (np.sqrt(np.mean(np.sum((acc - mu_p) ** 2, 1)) / self.D) - self.s)
            self.mu = mu_p
            return
        core, shell = acc[ra <= self.c], acc[ra > self.c]
        if len(core) < 5:
            return
        d_core = core.mean(0) - self.mu
        step = ETA * d_core
        if policy == "auto" and len(shell) >= 5 and np.linalg.norm(d_core) > 1e-9:
            u = d_core / np.linalg.norm(d_core)
            d_shell = (shell.mean(0) - self.mu) @ u
            support = np.clip(d_shell / (self.beta * np.linalg.norm(d_core)), 0.0, 1.0)
            step = step * support
        mu_p = self.mu + step
        s_core = np.sqrt(np.mean(np.sum((core - mu_p) ** 2, 1)) / self.D) / self.kappa
        s_step = ETA * (s_core - self.s)
        if policy == "auto" and s_step > 0:
            # A genuinely wider cloud also puts more traffic in the outer ring. Poison hidden in the
            # core does not, so spread growth is only allowed in proportion to outer-ring backing.
            frac = len(shell) / len(acc)
            s_step *= np.clip((frac - self.f0) / (0.25 * self.f0) + 1.0, 0.0, 1.0)
        self.s = self.s + s_step
        self.mu = mu_p


def poison(det, B, target, p, mode, rng):
    """Mix real benign and real attack points, pushed as far toward the attack as the mode allows."""
    k = int(len(B) * p / (1 - p))
    b = B[rng.integers(0, len(B), k)]
    z = target[rng.integers(0, len(target), k)]
    limit = (det.tau - 0.3) if mode == "boundary" else (det.c - 0.15)
    lo, hi = np.zeros(k), np.ones(k)
    for _ in range(25):
        mid = (lo + hi) / 2
        ok = det.score(b + mid[:, None] * (z - b)) <= limit
        lo = np.where(ok, mid, lo); hi = np.where(ok, hi, mid)
    return np.vstack([B, b + lo[:, None] * (z - b)])


def experiment(det, batches, tests, atk_test, policy, p, mode, poison_start, seed):
    rng = np.random.default_rng(seed)
    det.reset()
    rec, fpr = [], []
    for t, B in enumerate(batches(rng)):
        if t >= poison_start and p > 0:
            B = poison(det, B, atk_pool, p, mode, rng)
        det.update(B, policy)
        rec.append(np.mean(det.score(atk_test) > det.tau))
        fpr.append(np.mean(det.score(tests[t]) > det.tau))
    return np.array(rec), np.array(fpr)


def real_nbaiot(data_dir):
    global atk_pool
    sl = lambda X: np.sign(X) * np.log1p(np.abs(X))
    ld = lambda f, n=None, r=None: np.loadtxt(os.path.join(data_dir, f), delimiter=",", skiprows=1)
    rng0 = np.random.default_rng(123)
    benign = sl(ld("benign.csv"))
    n_cal = int(0.2 * len(benign)); cal = benign[:n_cal]
    mz, sz = cal.mean(0), cal.std(0) + 1e-6
    Vt = np.linalg.svd((cal - mz) / sz - ((cal - mz) / sz).mean(0), full_matrices=False)[2]
    proj = lambda X: np.clip(((X - mz) / sz) @ Vt[:10].T, -1e3, 1e3)
    det = Detector(proj(cal))
    stream = proj(benign[n_cal:])
    train, test = stream[0::2], stream[1::2]
    per = 250; cyc = len(train) // per
    results = {}
    for target in ["scan", "ack", "syn"]:
        A = sl(ld(os.path.join("mirai", target + ".csv")))
        A = proj(A[rng0.choice(len(A), 6000, replace=False)])
        atk_pool, atk_test = A[:3000], A[3000:]
        batches = lambda rng: (train[t * per:(t + 1) * per] for t in range(cyc))
        tests = [test[t * per:(t + 1) * per] for t in range(cyc)]
        for mode in ["boundary", "core"]:
            for p in [0.1, 0.2, 0.3, 0.4, 0.5]:
                for pol in ["naive", "core_only", "auto"]:
                    R, F = zip(*[experiment(det, batches, tests, atk_test, pol, p, mode, 15, s) for s in SEEDS])
                    results[(target, mode, p, pol)] = (np.mean(R, 0), np.mean(F, 0))
    return results, det


def synthetic_drift():
    """Synthetic world with strong benign drift: checks the defense still learns honest change."""
    global atk_pool
    D, N, CY = 12, 500, 200
    res = {}
    for toward in [False, True]:
        for pol in ["static", "naive", "core_only", "auto"]:
            for mode in ["boundary", "core"]:
                R, F = [], []
                for sd in SEEDS:
                    rng = np.random.default_rng(sd)
                    u = rng.normal(size=D); u /= np.linalg.norm(u)
                    w = rng.normal(size=D); w -= (w @ u) * u; w /= np.linalg.norm(w)
                    b = (0.6 * u + 0.8 * w) if toward else (-0.3 * u + np.sqrt(0.91) * w)
                    det = Detector(np.random.default_rng(99).normal(size=(20000, D)))
                    a = 9.0 * u
                    atk_pool = a + 0.6 * rng.normal(size=(2000, D))
                    atk_test = a + 0.6 * rng.normal(size=(300, D))
                    shift = np.zeros((CY, D))
                    for t in range(CY):
                        shift[t] = shift[t - 1] + (5.0 / 80 * b if 60 <= t < 140 else 0) if t else 0
                    batches = lambda r: (shift[t] + r.normal(size=(int(N * 0.6), D)) for t in range(CY))
                    tests = [shift[t] + np.random.default_rng(1000 + t).normal(size=(1000, D)) for t in range(CY)]
                    r_, f_ = experiment(det, batches, tests, atk_test, pol, 0.4, mode, 20, sd)
                    R.append(r_); F.append(f_)
                res[(toward, pol, mode)] = (np.mean(R, 0), np.mean(F, 0))
    return res


def main():
    data = sys.argv[1] if len(sys.argv) > 1 else "nbaiot_data"
    out_dir = os.path.dirname(os.path.abspath(__file__))
    lines = []
    real, det = real_nbaiot(data)
    lines.append(f"REAL N-BaIoT doorbell. core radius {det.c:.2f}, alarm radius {det.tau:.2f} (in spreads), support beta {det.beta:.2f}")
    lines.append("final recall on target / mean false alarms over last 30% of cycles, 5 seeds")
    for target in ["scan", "ack", "syn"]:
        for mode in ["boundary", "core"]:
            for p in [0.1, 0.2, 0.3, 0.4, 0.5]:
                row = []
                for pol in ["naive", "core_only", "auto"]:
                    r, f = real[(target, mode, p, pol)]
                    tail = max(1, int(0.3 * len(f)))
                    row.append(f"{pol} {r[-1]:.2f}/{f[-tail:].mean():.3f}")
                lines.append(f"{target:5s} {mode:8s} p={p:.1f}  " + " | ".join(row))
    syn = synthetic_drift()
    lines.append("\nSYNTHETIC with benign drift, attacker 40%: final recall / false alarms last 50 cycles")
    for toward in [False, True]:
        for mode in ["boundary", "core"]:
            row = []
            for pol in ["static", "naive", "core_only", "auto"]:
                r, f = syn[(toward, pol, mode)]
                row.append(f"{pol} {r[-1]:.2f}/{f[-50:].mean():.3f}")
            lines.append(f"drift {'toward' if toward else 'away  '} attacker {mode:8s} " + " | ".join(row))
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(out_dir, "auto_toa_results.txt"), "w").write(txt + "\n")

    colors = {"naive": "#D70015", "core_only": "#FF9F0A", "auto": "#0071E3"}
    names = {"naive": "Naive adaptive", "core_only": "Core learning only", "auto": "Auto TOA (no signatures)"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    for pol in ["naive", "core_only", "auto"]:
        ax[0].plot(real[("scan", "boundary", 0.3, pol)][0] * 100, color=colors[pol], lw=3 if pol == "auto" else 1.8, label=names[pol])
        ax[1].plot(real[("scan", "core", 0.3, pol)][0] * 100, color=colors[pol], lw=3 if pol == "auto" else 1.8)
        ax[2].plot(syn[(False, pol, "core")][1] * 100, color=colors[pol], lw=3 if pol == "auto" else 1.8)
    ax[2].plot(syn[(False, "static", "core")][1] * 100, color="#86868B", lw=1.6, label="Static (never adapts)")
    t = ["Real N-BaIoT: detected (%), classic attacker", "Real N-BaIoT: detected (%), attacker hides in core", "Synthetic drift: false alarms (%)"]
    for i, a in enumerate(ax):
        a.set_title(t[i], loc="left", fontweight="bold", fontsize=11.5)
        a.spines[["top", "right"]].set_visible(False); a.set_xlabel("adaptation cycle")
    ax[0].set_ylim(-3, 103); ax[1].set_ylim(-3, 103); ax[2].set_ylim(-1, 60)
    ax[0].legend(loc="lower left", fontsize=9, frameon=False); ax[2].legend(loc="upper left", fontsize=9, frameon=False)
    fig.suptitle("Signature-free defense. Real doorbell and Mirai scan traffic with a modelled poisoner at 30% share; right panel synthetic, 40%. 5 seeds.",
                 fontsize=10, color="#86868B", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "auto_toa_results.png"), dpi=160, facecolor="white")
    print("wrote auto_toa_results.png")


if __name__ == "__main__":
    main()
