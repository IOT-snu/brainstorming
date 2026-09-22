"""
Proof-of-concept simulation: Threat-Orthogonal Adaptation (TOA) vs. existing
update policies for a self-adapting anomaly detector under a boiling-frog
poisoning attack and realistic benign drift.

SYNTHETIC DATA. This checks whether the mechanism behaves as claimed before we
spend weeks on N-BaIoT and the ESP32. It is not a result on real traffic.

Detector (mean + spread, the same model family as rolling avg/stddev baselines):
  state      mu_hat (centre), s_hat (scale)
  score      ||x - mu_hat|| / s_hat, alarm if score > TAU (TAU = 99th pct, about 1% FPR)
  adaptation each cycle, self-label the batch (score <= TAU means "normal") and propose
             mu' = mu + eta (mean(accepted) - mu)
             s'  = s  + eta (rms spread of accepted around mu' - s)
The attacker's poison sits just inside the boundary. Because it is accepted, it both drags
the centre toward the attack and inflates the learned spread, so the envelope grows every
cycle until it swallows the attack. Policies differ only in what they do with (mu', s').

Run:  python3 sim_toa.py        (writes toa_results.png, prints a table)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = 12
N = 500
CYCLES = 200
ETA = 0.5
P_POISON = 0.40          # low-traffic IoT device: attacker can be a large share of what it learns from
ATTACK_DIST = 9.0
ATTACK_SPREAD = 0.6
POISON_START = 20
DRIFT_START, DRIFT_END, DRIFT_TOTAL = 60, 140, 5.0
SEEDS = [0, 1, 2, 3, 4]

BUDGET_B0, BUDGET_RHO = 1.0, 0.08    # old Layer 2: total parameter displacement budget, rho > benign drift rate
TOA_B0, TOA_RHO = 0.5, 0.005         # TOA: budget only for LOSS OF MARGIN to known attack signatures
GATE_K = 3.0


def make_world(rng, toward=False):
    u = rng.normal(size=D); u /= np.linalg.norm(u)
    w = rng.normal(size=D); w -= (w @ u) * u; w /= np.linalg.norm(w)
    if toward:
        b = 0.6 * u + 0.8 * w        # worst case: benign drift partly TOWARD the attack
    else:
        b = -0.3 * u + np.sqrt(0.91) * w   # realistic: mostly orthogonal, slightly away (e.g. a volume drop)
    return u, b


def margin(a, mu, s, tau):
    """How far the attack signature sits outside the detection envelope."""
    return np.linalg.norm(a - mu) - tau * s


def run(policy, rng, u, b, tau, poison_until=CYCLES):
    a = ATTACK_DIST * u
    anchor_mu, anchor_s = np.zeros(D), 1.0
    M0 = margin(a, anchor_mu, anchor_s, tau)
    mu, s = np.zeros(D), 1.0
    mu_true = np.zeros(D)
    hist, frozen = [], False
    atk = a + ATTACK_SPREAD * rng.normal(size=(300, D))
    step = DRIFT_TOTAL / (DRIFT_END - DRIFT_START)
    rec, fpr = [], []
    for t in range(CYCLES):
        if DRIFT_START <= t < DRIFT_END:
            mu_true = mu_true + step * b
        batch = mu_true + rng.normal(size=(int(N * (1 - P_POISON)), D))
        if POISON_START <= t < poison_until:
            d = (a - mu) / np.linalg.norm(a - mu)
            k = int(N * P_POISON)
            poison = mu + (tau - 0.3) * s * d + 0.15 * s * rng.normal(size=(k, D))
            batch = np.vstack([batch, poison])

        acc = batch[np.linalg.norm(batch - mu, axis=1) / s <= tau]
        if len(acc):
            mu_p = mu + ETA * (acc.mean(0) - mu)
            s_acc = np.sqrt(np.mean(np.sum((acc - mu_p) ** 2, axis=1)) / D)
            s_p = s + ETA * (s_acc - s)
        else:
            mu_p, s_p = mu, s

        if policy == "static":
            mu_p, s_p = mu, s
        elif policy == "naive":
            pass
        elif policy == "budget_freeze":
            disp = np.linalg.norm(mu_p - anchor_mu) + tau * abs(s_p - anchor_s)
            if frozen or disp > BUDGET_B0 + BUDGET_RHO * t:
                frozen = True
                mu_p, s_p = mu, s
        elif policy == "consistency_gate":
            dv = np.append(mu_p - mu, tau * (s_p - s))
            if len(hist) >= 8:
                H = np.array(hist[-16:])
                med = np.median(H, axis=0)
                mad = np.median(np.linalg.norm(H - med, axis=1)) + 1e-9
                if np.linalg.norm(dv - med) > GATE_K * mad:
                    mu_p, s_p = mu, s
            if not (mu_p is mu):
                hist.append(dv)
        elif policy == "toa":
            allowed_loss = TOA_B0 + TOA_RHO * t
            if M0 - margin(a, mu_p, s_p, tau) > allowed_loss:
                # 1) keep every part of the centre update that does NOT move toward the attack
                t_hat = (a - mu) / np.linalg.norm(a - mu)
                dmu = mu_p - mu
                along = dmu @ t_hat
                if along > 0:
                    mu_p = mu + dmu - along * t_hat
                # 2) grow the spread only as far as the remaining margin budget allows
                s_cap = (np.linalg.norm(a - mu_p) - (M0 - allowed_loss)) / tau
                s_p = max(0.5, min(s_p, s_cap))
            # never freeze: the orthogonal / away part of every update is always applied

        mu, s = mu_p, s_p
        rec.append(np.mean(np.linalg.norm(atk - mu, axis=1) / s > tau))
        test = mu_true + rng.normal(size=(1000, D))
        fpr.append(np.mean(np.linalg.norm(test - mu, axis=1) / s > tau))
    return np.array(rec), np.array(fpr)


POLICIES = [
    ("static", "Static (never adapts)"),
    ("naive", "Naive adaptive"),
    ("consistency_gate", "Consistency gate (Layer 1 only)"),
    ("budget_freeze", "Drift budget with freeze"),
    ("toa", "Threat-Orthogonal Adaptation (ours)"),
]
SCENARIOS = {
    "A": dict(until=CYCLES, toward=False, title="A: attacker never stops"),
    "B": dict(until=45, toward=False, title="B: attacker trips the freeze, then leaves"),
    "C": dict(until=CYCLES, toward=True, title="C: worst case, benign drift heads toward the attack"),
}


def main():
    cal = np.random.default_rng(99).normal(size=(200000, D))
    tau = np.quantile(np.linalg.norm(cal, axis=1), 0.99)
    res = {}
    for sc, cfg in SCENARIOS.items():
        for key, _ in POLICIES:
            R, F = [], []
            for sd in SEEDS:
                rng = np.random.default_rng(sd)
                u, b = make_world(rng, cfg["toward"])
                r, f = run(key, rng, u, b, tau, cfg["until"])
                R.append(r); F.append(f)
            res[(sc, key)] = (np.mean(R, 0), np.mean(F, 0))

    M0 = ATTACK_DIST - tau
    t_star = (M0 - TOA_B0) / TOA_RHO
    print(f"threshold tau = {tau:.2f} (1% FPR clean).  initial margin to attack = {M0:.2f}")
    print(f"TOA certificate: margin(t) >= M0 - (B0 + rho t), so the attack centre stays detected for at least t* = {t_star:.0f} cycles\n")
    hdr = f"{'':<3}{'policy':<38}{'recall@end':>11}{'min recall':>11}{'FPR last 50':>12}{'cycles to <50% recall':>23}"
    print(hdr); print("-" * len(hdr))
    for sc in SCENARIOS:
        for key, name in POLICIES:
            r, f = res[(sc, key)]
            below = np.where(r < 0.5)[0]
            print(f"{sc:<3}{name:<38}{r[-1]:>11.2f}{r.min():>11.2f}{f[-50:].mean():>12.3f}{(str(below[0]) if len(below) else 'never'):>23}")
        print()

    colors = {"static": "#86868B", "naive": "#D70015", "consistency_gate": "#FF9F0A", "budget_freeze": "#AF52DE", "toa": "#0071E3"}
    fig, ax = plt.subplots(2, 3, figsize=(16, 7.4), sharex=True)
    for j, (sc, cfg) in enumerate(SCENARIOS.items()):
        for key, name in POLICIES:
            r, f = res[(sc, key)]
            lw = 2.8 if key == "toa" else 1.6
            ax[0, j].plot(r * 100, color=colors[key], lw=lw, label=name)
            ax[1, j].plot(f * 100, color=colors[key], lw=lw)
        for row in range(2):
            ax[row, j].axvspan(DRIFT_START, DRIFT_END, color="#F0F0F3", zorder=0)
            ax[row, j].axvline(POISON_START, color="#C7C7CC", ls="--", lw=1)
            ax[row, j].spines[["top", "right"]].set_visible(False)
        ax[0, j].set_ylim(-3, 103); ax[1, j].set_ylim(-1, 70)
        ax[0, j].set_title(cfg["title"], loc="left", fontsize=11.5)
        ax[1, j].set_xlabel("adaptation cycle")
    ax[0, 0].set_ylabel("target-attack recall (%)")
    ax[1, 0].set_ylabel("false-positive rate (%)")
    ax[0, 0].legend(loc="lower left", fontsize=8.5, frameon=False)
    fig.suptitle("Synthetic proof of concept, 5 seeds. Grey band = benign drift, dashed line = poisoning starts. Not real-traffic results.",
                 fontsize=10.5, color="#86868B", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig("toa_results.png", dpi=160)
    print("wrote toa_results.png")


if __name__ == "__main__":
    main()
