"""
Real-data check of Threat-Orthogonal Adaptation (TOA) on N-BaIoT.

What is real:   benign traffic from a real Danmini smart doorbell and real Mirai attack traffic
                (N-BaIoT, Meidan et al. 2018), with the 115 Kitsune-style features from the dataset.
                Optional: benign traffic from a second real device, which "joins the network" midway
                and causes real drift.
What is modelled: the poisoning. N-BaIoT contains no poisoning, so the attacker is simulated: each
                poison sample is a mix of a real benign packet and a real attack packet, pushed just
                inside the detector's boundary (the boiling-frog strategy of ANTIDOTE, IMC 2009).

Data layout (from the UCI N-BaIoT archive):
  DATA/benign.csv            Danmini_Doorbell/benign_traffic.csv
  DATA/mirai/{scan,ack,syn,udp,udpplain}.csv   unpacked from Danmini_Doorbell/mirai_attacks.rar
  DATA/second_benign.csv     optional, another device's benign_traffic.csv
Run:  python3 nbaiot_check.py /path/to/DATA
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = sys.argv[1] if len(sys.argv) > 1 else "nbaiot_data"
TARGET = os.environ.get("TARGET", "scan")       # attack the poisoner wants to hide
D = 10                                           # PCA dimensions
PER_CYCLE = 250                                  # benign training packets per cycle
ETA = 0.5
POISON_START = 15
SEEDS = [0, 1, 2, 3, 4]
TOA_B0, TOA_RHO = 0.5, 0.005
BUDGET_B0, BUDGET_RHO = 1.0, 0.08
GATE_K = 3.0


def load(path, n=None, rng=None):
    X = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.float64)
    if n is not None and len(X) > n:
        X = X[rng.choice(len(X), n, replace=False)] if rng is not None else X[:n]
    return X


def slog(X):
    return np.sign(X) * np.log1p(np.abs(X))


def main():
    rng0 = np.random.default_rng(123)
    benign = slog(load(os.path.join(DATA, "benign.csv")))            # time-ordered
    second_path = os.path.join(DATA, "second_benign.csv")
    second = slog(load(second_path)) if (os.path.exists(second_path) and not os.environ.get("NO_SECOND")) else None
    attacks = {a: slog(load(os.path.join(DATA, "mirai", a + ".csv"), 6000, rng0))
               for a in ["scan", "ack", "syn", "udp", "udpplain"]}

    # Calibration = first 20% of the doorbell's benign traffic, in time order.
    n_cal = int(0.2 * len(benign))
    cal, stream = benign[:n_cal], benign[n_cal:]
    mu_z, sd_z = cal.mean(0), cal.std(0) + 1e-6
    Z = lambda X: (X - mu_z) / sd_z
    U_, S_, Vt = np.linalg.svd(Z(cal) - Z(cal).mean(0), full_matrices=False)
    P = Vt[:D].T
    proj = lambda X: np.clip(Z(X) @ P, -1e3, 1e3)
    calp = proj(cal)
    mu0 = calp.mean(0)
    s0 = np.sqrt(np.mean(np.sum((calp - mu0) ** 2, 1)) / D)
    tau = np.quantile(np.linalg.norm(calp - mu0, axis=1) / s0, 0.99)

    streamp = proj(stream)
    secondp = proj(second) if second is not None else None
    A = {k: proj(v) for k, v in attacks.items()}
    sig_idx = rng0.choice(len(A[TARGET]), 1000, replace=False)
    a_sig = A[TARGET][sig_idx].mean(0)                     # the known signature TOA protects
    test_mask = np.ones(len(A[TARGET]), bool); test_mask[sig_idx] = False
    atk_test = A[TARGET][test_mask][:3000]

    train_b, test_b = streamp[0::2], streamp[1::2]          # interleaved: same time window
    cycles = len(train_b) // PER_CYCLE
    drift_start, drift_end = int(cycles * 0.35), int(cycles * 0.75)

    def batch(t, arr_train, rng):
        own = arr_train[t * PER_CYCLE:(t + 1) * PER_CYCLE]
        if secondp is None or t < drift_start:
            return own
        frac = min(0.5, 0.5 * (t - drift_start) / max(1, drift_end - drift_start))   # new device ramps to 50%
        k = int(PER_CYCLE * frac)
        idx = rng.choice(len(secondp), k, replace=False)
        return np.vstack([own[k:], secondp[idx]])

    def run(policy, p, seed):
        rng = np.random.default_rng(seed)
        mu, s = mu0.copy(), s0
        M0 = np.linalg.norm(a_sig - mu0) - tau * s0
        hist, frozen, used = [], False, 0.0
        rec, fpr = [], []
        for t in range(cycles):
            B = batch(t, train_b, rng)
            if t >= POISON_START and p > 0:
                k = int(len(B) * p / (1 - p))
                b = B[rng.integers(0, len(B), k)]
                z = A[TARGET][rng.integers(0, len(A[TARGET]), k)]
                lo, hi = np.zeros(k), np.ones(k)
                for _ in range(25):                                  # largest mix still accepted
                    mid = (lo + hi) / 2
                    x = b + mid[:, None] * (z - b)
                    ok = np.linalg.norm(x - mu, axis=1) / s <= tau - 0.3
                    lo = np.where(ok, mid, lo); hi = np.where(ok, hi, mid)
                B = np.vstack([B, b + lo[:, None] * (z - b)])
            acc = B[np.linalg.norm(B - mu, axis=1) / s <= tau]
            if len(acc):
                mu_p = mu + ETA * (acc.mean(0) - mu)
                s_p = s + ETA * (np.sqrt(np.mean(np.sum((acc - mu_p) ** 2, 1)) / D) - s)
            else:
                mu_p, s_p = mu, s
            if policy == "static":
                mu_p, s_p = mu, s
            elif policy == "budget_freeze":
                if frozen or np.linalg.norm(mu_p - mu0) + tau * abs(s_p - s0) > (BUDGET_B0 + BUDGET_RHO * t) * s0:
                    frozen, mu_p, s_p = True, mu, s
            elif policy == "consistency_gate":
                dv = np.append(mu_p - mu, tau * (s_p - s))
                if len(hist) >= 8:
                    H = np.array(hist[-16:]); med = np.median(H, 0)
                    mad = np.median(np.linalg.norm(H - med, axis=1)) + 1e-9
                    if np.linalg.norm(dv - med) > GATE_K * mad:
                        mu_p, s_p = mu, s
                if mu_p is not mu:
                    hist.append(dv)
            elif policy == "toa":
                allowed = (TOA_B0 + TOA_RHO * t) * s0
                margin = lambda m, sc: np.linalg.norm(a_sig - m) - tau * sc
                if M0 - margin(mu_p, s_p) > allowed:
                    th = (a_sig - mu) / np.linalg.norm(a_sig - mu)
                    along = (mu_p - mu) @ th
                    if along > 0:
                        mu_p = mu_p - along * th
                    s_cap = (np.linalg.norm(a_sig - mu_p) - (M0 - allowed)) / tau
                    s_p = max(0.3 * s0, min(s_p, s_cap))
            mu, s = mu_p, s_p
            rec.append(np.mean(np.linalg.norm(atk_test - mu, axis=1) / s > tau))
            tb = test_b[t * PER_CYCLE:(t + 1) * PER_CYCLE]
            if secondp is not None and t >= drift_start:
                tb = np.vstack([tb, secondp[rng.integers(0, len(secondp), len(tb) // 2)]])
            fpr.append(np.mean(np.linalg.norm(tb - mu, axis=1) / s > tau))
        return np.array(rec), np.array(fpr)

    pols = [("static", "Static (never adapts)", "#86868B"), ("naive", "Naive adaptive", "#D70015"),
            ("consistency_gate", "Consistency gate", "#FF9F0A"), ("budget_freeze", "Freeze budget", "#AF52DE"),
            ("toa", "Threat-Orthogonal (ours)", "#0071E3")]

    print(f"N-BaIoT Danmini doorbell: {len(benign)} benign packets, calibration {n_cal}, {cycles} cycles of {PER_CYCLE}")
    print(f"second device drift: {'yes' if secondp is not None else 'no (within-device drift only)'}; target attack: mirai {TARGET}")
    print(f"clean recall on each Mirai attack: " + ", ".join(
        f"{k}={np.mean(np.linalg.norm(v - mu0, axis=1) / s0 > tau):.2f}" for k, v in A.items()))
    print(f"initial margin to target = {(np.linalg.norm(a_sig - mu0) - tau * s0) / s0:.2f} (in units of spread)\n")

    print("Attacker share sweep (mean of 5 seeds): final recall on target / mean FPR over last 30% of cycles")
    sweep = {}
    for p in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        row = []
        for key, name, _ in pols:
            R, F = zip(*[run(key, p, sd) for sd in SEEDS])
            r, f = np.mean(R, 0), np.mean(F, 0)
            sweep[(p, key)] = (r, f)
            tail = int(0.3 * cycles)
            row.append(f"{key[:6]} {r[-1]:.2f}/{f[-tail:].mean():.3f}")
        print(f"p={p:.1f}  " + " | ".join(row))

    P_MAIN = float(os.environ.get("P_MAIN", 0.4))
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.4))
    for key, name, c in pols:
        r, f = sweep[(P_MAIN, key)]
        lw = 3 if key == "toa" else 1.8
        ax[0].plot(r * 100, color=c, lw=lw, label=name)
        ax[1].plot(f * 100, color=c, lw=lw)
    for a_ in ax:
        if secondp is not None:
            a_.axvspan(drift_start, drift_end, color="#F0F0F3", zorder=0)
        a_.axvline(POISON_START, color="#C7C7CC", ls="--", lw=1)
        a_.spines[["top", "right"]].set_visible(False)
        a_.set_xlabel("adaptation cycle")
    ax[0].set_title(f"Real N-BaIoT: Mirai {TARGET} still detected (%)", loc="left", fontweight="bold")
    ax[1].set_title("False alarms on real benign traffic (%)", loc="left", fontweight="bold")
    ax[0].set_ylim(-3, 103); ax[0].legend(loc="lower left", fontsize=9, frameon=False)
    fig.suptitle(f"Real benign and Mirai traffic (N-BaIoT, Danmini doorbell), modelled poisoner at {int(P_MAIN*100)}% share, 5 seeds",
                 fontsize=10, color="#86868B", x=0.01, ha="left")
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get("OUT", "nbaiot_results.png"))
    fig.savefig(out, dpi=160, facecolor="white")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
