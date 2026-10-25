"""
Fleet simulator and every adaptation rule we compare.

Each cycle, every device:
  1. receives a batch of its own traffic (plus any poison aimed at it),
  2. proposes an update with its local rule (detector.propose),
  3. broadcasts the proposal as an authenticated 92-byte frame (gossip.py),
  4. applies some part of its proposal according to the rule under test,
  5. is scored on held-out benign traffic (false alarms) and real attack traffic (detection).

Rules ("mode"):
  static    never adapts.
  self      applies its own proposal in full (naive or signature-free auto, set by `rule`).
  clip      own proposal clipped per cycle (robust-aggregation style clipping, no memory).
  frozen    learns only from points a frozen copy of the calibrated detector accepts
            (frozen-reserve screening, WARDEN style).
  kl        alarm-rate switch-off: skips the update while the batch alarm rate is above
            kl_factor times the clean rate (Kloft and Laskov style).
  or        outlier-ratio gate: skips the update while the alarm rate exceeds 3x its own slow
            moving average (DriftXpert style).
  toa       our earlier Threat-Orthogonal Adaptation with an oracle attack signature.
  ciota     element-wise median of the proposals of same-model devices, residual discarded
            (CIoTA style consensus).
  foa       Fleet-Orthogonal Adaptation (this paper), see apply_foa.
"""
from dataclasses import dataclass, field, replace
import copy
import numpy as np

from detector import Detector
from robust import aggregate, project_ball
from foa_rule import FoaState, foa_step, consensus_direction
import gossip

CLEAN_ALARM = 0.01


def calibrated(stream):
    """Calibration depends only on the stream, so it is done once and copied into each run."""
    if getattr(stream, "_det", None) is None:
        stream._det = Detector(stream.cal)
    return copy.deepcopy(stream._det)


@dataclass(frozen=True)
class Policy:
    name: str
    mode: str = "self"
    rule: str = "auto"
    # FOA
    agg: str = "gm"
    peers: str = "diverse"
    k_peers: int = 0
    lam_gate: bool = True
    signif: bool = True
    alpha: float = 0.2
    z0: float = 2.0
    z1: float = 4.0
    residual: str = "budget"
    robust_lam: bool = True     # agreement from the median projection of own core points
    joint: bool = False         # one budget for centre and spread residuals (ablation)
    common_dir: str = "consensus"   # "own": doubly robust common channel (direction from own median shift)
    B0: float = 0.1             # residual budget, in alarm radii (tau * s0)
    B: float = 0.005
    B0s: float = 0.1            # residual log-spread budget (spread was the attackers' lever; see paper)
    Bs: float = 0.001
    common_budget: bool = True
    B0c: float = 0.75           # common-channel budget, in alarm radii
    Bc: float = 0.06
    B0cs: float = 0.7
    Bcs: float = 0.02
    k_min: int = 2
    hmac: bool = True
    # baselines
    clip: float = 0.1
    kl_factor: float = 5.0


def P(name, **kw):
    return Policy(name=name, **kw)


POLICIES = {
    "static": P("static", mode="static"),
    "naive": P("naive", mode="self", rule="naive"),
    "auto": P("auto", mode="self", rule="auto"),
    "clip": P("clip", mode="clip"),
    "frozen": P("frozen", mode="frozen"),
    "kl": P("kl", mode="kl"),
    "or": P("or", mode="or"),
    "toa": P("toa", mode="toa"),
    "ciota": P("ciota", mode="ciota", peers="same", agg="cwmed"),
    "foa": P("foa", mode="foa"),
}


def variant(base, name, **kw):
    return replace(POLICIES[base], name=name, **kw)


@dataclass
class Member:
    short: str
    vendor: str
    instance: int = 0
    join: int = 0
    byzantine: bool = False


class DevState(FoaState):
    """FOA state plus what the baselines need."""

    def __init__(self, D):
        super().__init__(D)
        self.or_hist = CLEAN_ALARM


def select_peers(members, i, how, k, seed):
    me = members[i]
    others = [j for j in range(len(members)) if j != i]
    if how == "none":
        return []
    if how == "same":
        cand = [j for j in others if members[j].short == me.short]
    elif how == "diverse":
        cand = [j for j in others if members[j].vendor != me.vendor]
    elif how in ("all", "random"):
        cand = others
    else:
        raise ValueError(how)
    if how == "random" or (k and len(cand) > k):
        rng = np.random.default_rng(seed * 7919 + i)
        cand = list(rng.permutation(cand))
    return sorted(cand[:k]) if k else sorted(cand)


class FleetSim:
    def __init__(self, members, streams, world, policy, cycles=240, attackers=(), byzantine=None, sybil=None,
                 loss=0.0, seed=0, join_mode="self", record_state=False, trace_device=None):
        self.members, self.streams, self.world, self.pol = members, streams, world, policy
        self.T, self.attackers, self.byz, self.sybil = cycles, list(attackers), byzantine, sybil
        self.loss, self.seed, self.join_mode, self.record_state = loss, seed, join_mode, record_state
        self.trace_device, self.trace = trace_device, []
        self.n = len(members)
        self.rng = np.random.default_rng(10007 * seed + 13)
        self.keys = gossip.keys(self.n, seed)
        self.dets = [calibrated(s) for s in streams]
        D = self.dets[0].D
        self.st = [DevState(D) for _ in range(self.n)]
        self.peers = [select_peers(members, i, policy.peers, policy.k_peers, seed) for i in range(self.n)]
        self.keyring = [{j: self.keys[j] for j in self.peers[i]} for i in range(self.n)]
        self.joined = [m.join == 0 for m in members]
        self.frames_prev = []
        self.stats = dict(rejected={}, accepted=0, bytes_sent=0)

    # ------------------------------------------------------------------ helpers
    def _join(self, i, t):
        """A device joining mid-run. self: calibrate on its own first window (which an attacker may
        already be poisoning). warm: start from the geometric median of same-model peers' detector
        state and run under the residual budget only."""
        s = self.streams[i]
        prm = self.world.params(t, i)
        X = np.vstack([s.train(t + k, prm) for k in range(5)])
        for a in self.attackers:
            if a.victim == i and a.active(t):
                X, _ = a.inject(t, self.dets[i], X, s.attack_pool(a.target, prm), self.rng)
        det = Detector(X)
        if self.join_mode == "warm":
            same = [j for j in range(self.n) if j != i and self.members[j].short == self.members[i].short and self.joined[j]]
            if same:
                from robust import geometric_median
                det.mu0 = geometric_median(np.array([self.dets[j].mu for j in same]))
                det.s0 = float(np.median([self.dets[j].s for j in same]))
                for a in ("tau", "c", "kappa", "beta", "f0"):
                    setattr(det, a, float(np.median([getattr(self.dets[j], a) for j in same])))
                det.reset()
        self.dets[i] = det
        self.joined[i] = True

    # ------------------------------------------------------------------ FOA
    def apply_foa(self, i, t, prop, inbox):
        det, st = self.dets[i], self.st[i]
        if i == self.trace_device:
            rec = dict(t=t, tj=t - self.members[i].join, mu=det.mu.copy(), s=det.s, prop=prop, batch=self._last_batch,
                       peers=[(f[1].copy(), f[2]) for f in inbox], st_in={k: copy.deepcopy(v) for k, v in vars(st).items() if k != "log"})
        dmu, dls = foa_step(st, self.pol, det.tau * det.s0, t - self.members[i].join, prop.dmu, prop.dls,
                            [f[1] for f in inbox], [f[2] for f in inbox], prop.along, prop.dmed, prop.dmed_noise)
        if i == self.trace_device:
            rec.update(out_dmu=dmu.copy(), out_dls=dls, st_out={k: copy.deepcopy(v) for k, v in vars(st).items() if k != "log"})
            self.trace.append(rec)
        det.apply(dmu, dls)

    # ------------------------------------------------------------------ main loop
    def run(self, eval_target=None):
        T, n, pol = self.T, self.n, self.pol
        D = self.dets[0].D
        uses_gossip = pol.mode in ("foa", "ciota")
        out = dict(fpr=np.full((T, n), np.nan), rec=np.full((T, n), np.nan), disp=np.full((T, n), np.nan),
                   spread=np.full((T, n), np.nan), q_acc=np.full((T, n), np.nan), q_core=np.full((T, n), np.nan),
                   applied=np.zeros((T, n), dtype=bool))
        for key in ("lam", "w", "a", "r_app", "R", "C", "m_norm", "d50", "reach"):
            out[key] = np.full((T, n), np.nan)
        if self.record_state:
            out["mu"] = np.full((T, n, D), np.nan); out["s"] = np.full((T, n), np.nan)
        targets = {}
        for i in range(n):
            ts = [a.target for a in self.attackers if a.victim == i]
            targets[i] = ts[0] if ts else (eval_target or {}).get(i)
        for t in range(T):
            props, poison = [None] * n, [None] * n
            for i in range(n):
                m = self.members[i]
                if not self.joined[i]:
                    if t == m.join:
                        self._join(i, t)
                    else:
                        continue
                if m.byzantine:
                    continue
                det, s = self.dets[i], self.streams[i]
                prm = self.world.params(t, i)
                B = s.train(t, prm)
                Pn = []
                for a in self.attackers:
                    if a.victim == i and a.active(t):
                        ctx = {"m": self.st[i].m_ema if pol.mode == "foa" else None}
                        B, Pp = a.inject(t, det, B, s.attack_pool(a.target, prm), self.rng, ctx)
                        Pn.append(Pp)
                if Pn:
                    PP = np.vstack(Pn)
                    rp = det.score(PP)
                    out["q_acc"][t, i] = float(np.mean(rp <= det.tau))
                    out["q_core"][t, i] = float(np.mean(rp <= det.c))
                if pol.mode == "frozen":
                    B = B[np.linalg.norm(B - det.mu0, axis=1) / det.s0 <= det.tau]
                u = consensus_direction(self.st[i]) if pol.mode == "foa" else None
                props[i] = det.propose(B, "naive" if pol.rule == "naive" else "auto", u)
                if i == self.trace_device:
                    self._last_batch = B.copy()

            inboxes = [[] for _ in range(n)]
            if uses_gossip:
                inboxes = self._gossip(t, props)

            for i in range(n):
                if props[i] is None:
                    continue
                det, st, prop = self.dets[i], self.st[i], props[i]
                applied = True
                if pol.mode == "static":
                    applied = False
                elif pol.mode in ("self", "frozen"):
                    det.apply(prop.dmu, prop.dls)
                elif pol.mode == "clip":
                    det.apply(project_ball(prop.dmu, pol.clip * det.s0), float(np.clip(prop.dls, -0.05, 0.05)))
                elif pol.mode == "kl":
                    if prop.alarm <= pol.kl_factor * CLEAN_ALARM:
                        det.apply(prop.dmu, prop.dls)
                    else:
                        applied = False
                elif pol.mode == "or":
                    if prop.alarm / max(st.or_hist, CLEAN_ALARM) <= 3.0:
                        det.apply(prop.dmu, prop.dls)
                    else:
                        applied = False
                    st.or_hist = 0.9 * st.or_hist + 0.1 * prop.alarm
                elif pol.mode == "toa":
                    self._apply_toa(i, t, prop, targets.get(i))
                elif pol.mode == "ciota":
                    group = [prop] + [f for f in inboxes[i]]
                    if len(group) >= 3:
                        M = np.array([prop.dmu] + [f[1] for f in inboxes[i]])
                        S = np.array([prop.dls] + [f[2] for f in inboxes[i]])
                        det.apply(np.median(M, axis=0), float(np.median(S)))
                    else:
                        det.apply(prop.dmu, prop.dls)
                elif pol.mode == "foa":
                    self.apply_foa(i, t, prop, inboxes[i])
                out["applied"][t, i] = applied

            for i in range(n):
                if not self.joined[i] or self.members[i].byzantine:
                    continue
                det, s, st = self.dets[i], self.streams[i], self.st[i]
                prm = self.world.params(t, i)
                out["fpr"][t, i] = float(np.mean(det.score(s.test(t, prm)) > det.tau))
                if targets.get(i):
                    Ae = s.attack_eval(targets[i], prm)
                    out["rec"][t, i] = float(np.mean(det.score(Ae) > det.tau))
                    if pol.mode == "foa":
                        # Theorem 1 check: half the attack must lie within tau*s of mu, and mu can be at
                        # most the residual budget away from the consensus-backed path mu0 + C.
                        tj = t - self.members[i].join
                        out["d50"][t, i] = float(np.median(np.linalg.norm(Ae - det.mu0 - st.C, axis=1)) / det.s0)
                        L = pol.B0 + pol.B * tj
                        if pol.joint:     # ||R||/rho + |Rs| <= L: the reachable radius is largest at one end of the split
                            out["reach"][t, i] = det.tau * max(np.exp(st.Cs + L), np.exp(st.Cs) + L)
                        else:             # ||R|| <= L rho and |Rs| <= B0s + Bs t
                            out["reach"][t, i] = det.tau * np.exp(st.Cs + pol.B0s + pol.Bs * tj) + L * det.tau
                out["disp"][t, i] = float(np.linalg.norm(det.mu - det.mu0) / det.s0)
                out["spread"][t, i] = det.s / det.s0
                for key in ("lam", "w", "a", "r_app", "R", "C", "m_norm"):
                    if key in st.log:
                        out[key][t, i] = st.log[key]
                if self.record_state:
                    out["mu"][t, i] = det.mu; out["s"][t, i] = det.s
        out["stats"] = self.stats
        out["targets"] = targets
        return out

    def _apply_toa(self, i, t, prop, target):
        """TOA with an oracle signature: the shift toward the known attack is rationed by a cumulative
        budget, everything else is applied in full."""
        det, st, pol = self.dets[i], self.st[i], self.pol
        if target is None:
            det.apply(prop.dmu, prop.dls); return
        pool = self.streams[i].attack_pool(target, self.world.params(t, i))
        u = pool.mean(0) - det.mu0; u /= np.linalg.norm(u)
        along = float(prop.dmu @ u)
        cap = (pol.B0 + pol.B * t) * det.tau * det.s0
        used = float(st.R @ u) if st.R is not None else 0.0
        allowed = min(along, max(cap - used, 0.0)) if along > 0 else along
        step = prop.dmu - along * u + allowed * u
        st.R = st.R + allowed * u
        det.apply(step, min(prop.dls, pol.Bs) if prop.dls > 0 else prop.dls)

    def _gossip(self, t, props):
        n, pol = self.n, self.pol
        frames = []
        for j in range(n):
            if not self.joined[j]:
                continue
            m = self.members[j]
            if m.byzantine and self.byz is not None and self.byz.active(t):
                v = self.byz.victim
                vec, dls = self.byz.frame_vector(t, self.dets[v], self.streams[v].attack_pool(self.byz.target, self.world.params(t, v)), self.rng, self.dets[v].D)
                frames.append(gossip.pack(j, t, vec, dls, 200, self.keys[j]))
            elif m.byzantine:
                frames.append(gossip.pack(j, t, np.zeros(self.dets[j].D), 0.0, 200, self.keys[j]))
            elif props[j] is not None:
                frames.append(gossip.pack(j, t, props[j].dmu, props[j].dls, props[j].n_core, self.keys[j]))
        self.stats["bytes_sent"] += len(frames) * gossip.FRAME_BYTES
        if self.sybil is not None and self.sybil.active(t):
            v = self.sybil.victim
            pool = self.streams[v].attack_pool(self.sybil.target, self.world.params(t, v))
            u = pool.mean(0) - self.dets[v].mu; u = u / np.linalg.norm(u) * self.sybil.scale * self.dets[v].s0
            fake_key = b"\x00" * 32
            for k in range(self.sybil.n_forged):
                frames.append(gossip.pack(k % n, t, u, 0.05, 200, fake_key))
            if self.sybil.replay:
                frames += self.frames_prev
        self.frames_prev = [f for f in frames[:n]]
        inboxes = [[] for _ in range(n)]
        for i in range(n):
            if not self.joined[i] or self.members[i].byzantine:
                continue
            peers = set(self.peers[i]) if pol.mode == "foa" else {j for j in range(n) if j != i and self.members[j].short == self.members[i].short}
            keyring = {j: self.keys[j] for j in peers}
            seen = set()
            for f in frames:
                if self.loss and self.rng.random() < self.loss:
                    continue
                if pol.hmac:
                    res, why = gossip.verify(f, keyring, t)
                else:
                    h = gossip.HEAD.unpack(f[:-gossip.TAG])
                    res, why = ((h[1], np.array(h[4:20], dtype=np.float64), float(h[20]), h[2]), "ok") if h[1] in peers or h[1] >= n else (None, "not a peer")
                if res is None:
                    self.stats["rejected"][why] = self.stats["rejected"].get(why, 0) + 1
                    continue
                if pol.hmac and res[0] in seen:
                    continue
                seen.add(res[0])
                inboxes[i].append(res)
                self.stats["accepted"] += 1
        return inboxes
