"""
The per-device detector: an online centre-and-spread anomaly detector (Kloft and Laskov 2012 style).

    score(x) = ||x - mu|| / s,     alarm if score > tau (99th percentile of clean calibration scores)

Each cycle the device self-labels its accepted (non-alarmed) traffic and proposes an update.
Proposal and application are separate so that fleet rules can decide how much of each proposal
to apply. Two local proposal rules:

  naive  move toward the mean of all accepted traffic, spread to its RMS radius.
  auto   our signature-free rule: learn only from the dense core (inside the clean 80th-percentile
         radius), scale a centre move by how well the outer ring follows it (whole-cloud support),
         and allow spread growth only in proportion to outer-ring backing.

The update applied is (dmu, dls): centre shift and change of log spread.
"""
from dataclasses import dataclass
import numpy as np

ETA = 0.5
Q_CORE = 0.8


@dataclass
class Proposal:
    dmu: np.ndarray        # proposed centre shift
    dls: float             # proposed change of log spread
    n_acc: int             # accepted points
    n_core: int            # points used for learning
    alarm: float           # alarm fraction of the batch
    mscore: float          # mean score of the batch
    along: float = 0.0     # eta * median projection of core points on a given direction (FOA agreement)
    dmed: np.ndarray = None  # eta * (coordinate-wise median of core points - mu): robust own shift
    dmed_noise: float = 0.0  # standard error of ||dmed|| under no shift (from the core's own MAD)


class Detector:
    def __init__(self, cal, tau_q=0.99, q_core=Q_CORE, eta=ETA, beta_seed=7):
        cal = np.asarray(cal, dtype=np.float64)
        self.eta = eta
        self.D = cal.shape[1]
        self.mu0 = cal.mean(0)
        self.s0 = float(np.sqrt(np.mean(np.sum((cal - self.mu0) ** 2, 1)) / self.D))
        r = np.linalg.norm(cal - self.mu0, axis=1) / self.s0
        self.tau = float(np.quantile(r, tau_q))
        self.c = float(np.quantile(r, q_core))
        core = cal[r <= self.c]
        self.kappa = float(np.sqrt(np.mean(np.sum((core - self.mu0) ** 2, 1)) / self.D) / self.s0)
        # Whole-cloud support calibration: shift clean data by small steps along random directions and
        # record how far the accepted outer ring's mean moves compared with the core's.
        rng = np.random.default_rng(beta_seed)
        ratios = []
        for _ in range(40):
            d = rng.normal(size=self.D); d /= np.linalg.norm(d)
            X = cal + 0.3 * self.s0 * d
            rr = np.linalg.norm(X - self.mu0, axis=1) / self.s0
            acc, ra = X[rr <= self.tau], rr[rr <= self.tau]
            dc = (acc[ra <= self.c].mean(0) - self.mu0) @ d
            ds = (acc[ra > self.c].mean(0) - self.mu0) @ d
            ratios.append(ds / max(dc, 1e-9))
        self.beta = float(np.median(ratios))
        self.f0 = float(np.mean(r[r <= self.tau] > self.c))
        self.reset()

    def reset(self):
        self.mu, self.s = self.mu0.copy(), self.s0

    def state(self):
        return self.mu.copy(), self.s

    def set_state(self, st):
        self.mu, self.s = st[0].copy(), st[1]

    def score(self, X):
        return np.linalg.norm(X - self.mu, axis=1) / self.s

    def propose(self, B, rule="auto", u=None):
        if len(B) == 0:
            return Proposal(np.zeros(self.D), 0.0, 0, 0, 0.0, 0.0)
        r = self.score(B)
        ok = r <= self.tau
        acc, ra = B[ok], r[ok]
        alarm, ms = float(1.0 - ok.mean()), float(r.mean())
        zero = Proposal(np.zeros(self.D), 0.0, int(ok.sum()), 0, alarm, ms)
        if len(acc) == 0:
            return zero
        if rule == "naive":
            mu_p = self.mu + self.eta * (acc.mean(0) - self.mu)
            s_new = self.s + self.eta * (np.sqrt(np.mean(np.sum((acc - mu_p) ** 2, 1)) / self.D) - self.s)
            return Proposal(mu_p - self.mu, float(np.log(s_new / self.s)), len(acc), len(acc), alarm, ms)
        core, shell = acc[ra <= self.c], acc[ra > self.c]
        if len(core) < 5:
            return zero
        along = float(self.eta * np.median((core - self.mu) @ u)) if u is not None else 0.0
        med = np.median(core, axis=0)
        dmed = self.eta * (med - self.mu)
        mad = 1.4826 * np.median(np.abs(core - med), axis=0)
        dmed_noise = float(self.eta * 1.2533 * np.sqrt(np.sum(mad ** 2) / len(core)))
        d_core = core.mean(0) - self.mu
        step = self.eta * d_core
        nd = np.linalg.norm(d_core)
        if len(shell) >= 5 and nd > 1e-9:
            u = d_core / nd
            d_shell = (shell.mean(0) - self.mu) @ u
            step = step * float(np.clip(d_shell / (self.beta * nd), 0.0, 1.0))
        mu_p = self.mu + step
        s_core = np.sqrt(np.mean(np.sum((core - mu_p) ** 2, 1)) / self.D) / self.kappa
        s_step = self.eta * (s_core - self.s)
        if s_step > 0:
            frac = len(shell) / len(acc)
            s_step *= float(np.clip((frac - self.f0) / (0.25 * self.f0) + 1.0, 0.0, 1.0))
        return Proposal(step, float(np.log((self.s + s_step) / self.s)), len(acc), len(core), alarm, ms, along, dmed, dmed_noise)

    def apply(self, dmu, dls):
        self.mu = self.mu + dmu
        self.s = float(self.s * np.exp(dls))
