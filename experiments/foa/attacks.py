"""
Attackers. All are white-box on the algorithm and read the victim's live state (worst case).

Traffic poisoners control a share p of one victim's training traffic (Kloft and Laskov's attacker
share) and craft feature vectors; they cannot touch the device's code or keys. Modes:
  boundary  real benign points pulled toward real attack traffic until just inside the alarm radius
            (the classic boiling frog).
  core      the same, but kept just inside the core radius, to slip past core-only learning.
  mimicry   copies of real benign points translated toward the attack, so the whole cloud appears
            to move: indistinguishable, for one device on its own, from honest drift.
  multidir  mimicry that rotates through several directions that all lead to the attack, to defeat
            any budget kept along a single direction.
  aligned   mimicry along the fleet consensus direction whenever that direction leads toward the
            attack (tries to ride the common channel).
  decoy     loud traffic far outside the boundary. Never learned from; it exists only to trip a
            stop-learning gate (the freeze attack).
Schedules: continuous, or pulsing (on for `on` cycles, off for `off` cycles).

Gossip attackers:
  Byzantine  f fleet members whose keys were stolen: they send whatever frame maximises the bias of
             the consensus toward one victim's attack.
  Sybil      no key: forges frames (wrong tags) or replays genuine frames from earlier cycles.
"""
import numpy as np


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


class TrafficAttacker:
    def __init__(self, victim, target, mode="boundary", p=0.3, t0=40, t1=10**9, on=0, off=0, v_frac=0.5, k_dirs=4):
        self.victim, self.target, self.mode, self.p = victim, target, mode, p
        self.t0, self.t1, self.on, self.off = t0, t1, on, off
        self.v_frac, self.k_dirs = v_frac, k_dirs
        self._basis = None

    def active(self, t):
        if not (self.t0 <= t < self.t1):
            return False
        if self.on and self.off:
            return ((t - self.t0) % (self.on + self.off)) < self.on
        return True

    def _directions(self, a_hat, rng):
        if self._basis is None:
            Q = np.linalg.qr(np.column_stack([a_hat, np.random.default_rng(3).normal(size=(len(a_hat), self.k_dirs))]))[0]
            self._basis = Q[:, 1:]
        return self._basis

    def inject(self, t, det, B, pool, rng, ctx=None):
        """Returns the poisoned batch and the poison points alone."""
        k = int(round(len(B) * self.p / (1.0 - self.p)))
        if k <= 0:
            return B, B[:0]
        base = B[rng.integers(0, len(B), k)]
        if self.mode == "decoy":
            # Real attack packets, pushed out to at least twice the alarm radius: loud traffic that every
            # rule rejects from learning, so its only possible effect is on a stop-learning gate.
            P = pool[rng.integers(0, len(pool), k)]
            off = P - det.mu
            n = np.linalg.norm(off, axis=1, keepdims=True) / det.s
            P = det.mu + off * np.maximum(1.0, 2.0 * det.tau / np.maximum(n, 1e-9))
            return np.vstack([B, P]), P
        tgt = pool[rng.integers(0, len(pool), k)]
        a_hat = _unit(pool.mean(0) - det.mu)
        if self.mode in ("boundary", "core"):
            V = tgt - base
            limit = det.tau - 0.3 if self.mode == "boundary" else det.c - 0.15
        else:
            if self.mode == "multidir":
                E = self._directions(a_hat, rng)
                e = E[:, (t // 3) % E.shape[1]]
                d = _unit(a_hat + 0.8 * e)
            elif self.mode == "aligned" and ctx is not None and ctx.get("m") is not None and ctx["m"] @ a_hat > 0:
                d = _unit(ctx["m"])
            else:
                d = a_hat
            # Re-centre copies of real benign points on the detector's current centre and move the
            # whole copy ahead toward the attack: to this device alone it looks like the cloud drifting.
            V = (det.mu - B.mean(0)) + self.v_frac * det.c * det.s * d
            V = np.tile(V, (k, 1))
            limit = det.tau - 0.3
        lo, hi = np.zeros(k), np.ones(k)
        for _ in range(20):
            mid = (lo + hi) / 2
            ok = det.score(base + mid[:, None] * V) <= limit
            lo = np.where(ok, mid, lo); hi = np.where(ok, hi, mid)
        P = base + lo[:, None] * V
        return np.vstack([B, P]), P


class Byzantine:
    """f compromised fleet members (valid keys) biasing the consensus toward one victim's attack."""

    def __init__(self, nodes, victim, target, t0=40, t1=10**9, scale=10.0, style="aim"):
        self.nodes, self.victim, self.target = list(nodes), victim, target
        self.t0, self.t1, self.scale, self.style = t0, t1, scale, style

    def active(self, t):
        return self.t0 <= t < self.t1

    def frame_vector(self, t, victim_det, pool, rng, D):
        if self.style == "inflate":
            return rng.normal(size=D) * self.scale * victim_det.s0, 0.0
        a_hat = _unit(pool.mean(0) - victim_det.mu)
        return self.scale * victim_det.s0 * a_hat, 0.05


class Sybil:
    """Keyless injector: forged frames claiming real sender ids, plus replays of last cycle's frames."""

    def __init__(self, n_forged=8, replay=True, victim=0, target=None, t0=40, t1=10**9, scale=10.0):
        self.n_forged, self.replay, self.victim, self.target = n_forged, replay, victim, target
        self.t0, self.t1, self.scale = t0, t1, scale

    def active(self, t):
        return self.t0 <= t < self.t1
