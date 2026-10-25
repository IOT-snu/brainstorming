"""
Fleet-Orthogonal Adaptation: the per-device update rule (Algorithm 1 in the paper), as a pure
function of the device's own proposal, its verified peer frames and its FOA state. The ESP32 C
implementation (firmware/esp32_foa/foa_core.c) mirrors this function line by line and is tested
against it.

Given own proposal (d, e) = (centre shift, log-spread change) and peer proposals {(d_j, e_j)}:
  m   = geometric median of peer shifts              (honest-majority robust)
  w   = significance of the smoothed consensus       (no common step while peers only see noise)
  lam = agreement of the device's own traffic with it, measured robustly: the median projection of
        its own core points on the consensus direction (an attacker holding under half the batch can
        neither cancel nor fake it), smoothed, divided by the consensus size, clipped to [0, 1]
  a   = w * lam * m_smoothed                          common part, applied in full
        projected so that ||C + a|| <= (B0c + Bc t) rho  (common-channel budget)
  r   = d - a                                         residual, device-specific, for centre and log spread
        one joint budget: ||R||/rho + |R_s| <= B0 + B t   (the residual can enlarge the acceptance
        region by at most B0 + B t alarm radii, through the centre and the spread together)
  mu += a + r_applied ; log s += a_s + r_s_applied.
Invariant (Theorem 1): mu(t) = mu0 + C(t) + R(t), log s(t)/s0 = Cs(t) + Rs(t),
                       ||R(t)||/rho + |Rs(t)| <= B0 + B t.
Budgets are in units of the device's calibrated alarm radius rho = tau * s0, so the same B means
the same fraction of the detector's acceptance region on every device, whatever its traffic shape.
"""
from dataclasses import dataclass, field
import numpy as np

from robust import aggregate, project_ball


@dataclass
class FoaState:
    D: int
    C: np.ndarray = None
    R: np.ndarray = None
    Cs: float = 0.0
    Rs: float = 0.0
    m_ema: np.ndarray = None
    p_ema: np.ndarray = None
    ms_ema: float = 0.0
    ps_ema: float = 0.0
    pa_ema: float = 0.0
    sig_ema: float = 0.0
    sigs_ema: float = 0.0
    log: dict = field(default_factory=dict)

    def __post_init__(self):
        z = lambda: np.zeros(self.D)
        self.C, self.R, self.m_ema, self.p_ema = z(), z(), z(), z()


def _weight(z, z0, z1):
    return float(np.clip((z - z0) / (z1 - z0), 0.0, 1.0))


def consensus_direction(st):
    """Unit direction of the smoothed consensus, used by the device to measure its own robust agreement."""
    n = float(np.linalg.norm(st.m_ema))
    return st.m_ema / n if n > 0 else None


def foa_step(st, pol, rho, tj, dmu, dls, peer_dmu, peer_dls, own_along=0.0):
    """Returns (applied centre shift, applied log-spread change) and updates st in place.
    rho: calibrated alarm radius tau*s0; tj: cycles since the device joined; peer_*: verified peer proposals;
    own_along: eta * median projection of the device's core points on consensus_direction(st) (taken
    before this call), i.e. how far its own traffic moved along the fleet's drift."""
    al = pol.alpha
    D = st.D
    a, a_s, lam, w, ws = np.zeros(D), 0.0, 0.0, 0.0, 0.0
    K = len(peer_dmu)
    if K >= pol.k_min:
        M = np.asarray(peer_dmu, dtype=np.float64); S = np.asarray(peer_dls, dtype=np.float64)
        m = aggregate(M, pol.agg)
        ms = float(np.median(S))
        sig = float(np.median(np.linalg.norm(M - m, axis=1))) / np.sqrt(K)
        sig_s = 1.25 * 1.4826 * float(np.median(np.abs(S - ms))) / np.sqrt(K)
        st.m_ema = (1 - al) * st.m_ema + al * m
        st.ms_ema = (1 - al) * st.ms_ema + al * ms
        st.sig_ema = (1 - al) * st.sig_ema + al * sig
        st.sigs_ema = (1 - al) * st.sigs_ema + al * sig_s
        shrink = np.sqrt(al / (2 - al))                     # noise of an EMA relative to one sample
        if pol.signif:
            w = _weight(np.linalg.norm(st.m_ema) / max(st.sig_ema * shrink, 1e-12), pol.z0, pol.z1)
            ws = _weight(abs(st.ms_ema) / max(st.sigs_ema * shrink, 1e-12), pol.z0, pol.z1)
        else:
            w = ws = 1.0
        st.p_ema = (1 - al) * st.p_ema + al * np.asarray(dmu)
        st.ps_ema = (1 - al) * st.ps_ema + al * dls
        st.pa_ema = (1 - al) * st.pa_ema + al * own_along
        nm2 = float(st.m_ema @ st.m_ema)
        if nm2 > 0:
            if not pol.lam_gate:
                lam = 1.0
            elif pol.robust_lam:
                lam = float(np.clip(st.pa_ema / np.sqrt(nm2), 0.0, 1.0))
            else:
                lam = float(np.clip(st.p_ema @ st.m_ema / nm2, 0.0, 1.0))
        lam_s = 0.0
        if st.ms_ema != 0:
            lam_s = float(np.clip(st.ps_ema / st.ms_ema, 0.0, 1.0)) if pol.lam_gate else 1.0
        a, a_s = w * lam * st.m_ema, ws * lam_s * st.ms_ema
        if pol.common_budget:
            a = project_ball(st.C + a, (pol.B0c + pol.Bc * tj) * rho) - st.C
            lim = pol.B0cs + pol.Bcs * tj
            a_s = float(np.clip(st.Cs + a_s, -lim, lim)) - st.Cs
        st.log["m_norm"] = float(np.linalg.norm(m) / rho)
    r, r_s = np.asarray(dmu) - a, dls - a_s
    if pol.residual == "budget" and pol.joint:
        L = pol.B0 + pol.B * tj
        Rn, Rsn = st.R + r, st.Rs + r_s
        used = float(np.linalg.norm(Rn)) / rho + abs(Rsn)
        k = min(1.0, L / used) if used > 0 else 1.0       # shrink the accumulated residual until it fits
        r_app, r_s_app = k * Rn - st.R, k * Rsn - st.Rs
    elif pol.residual == "budget":
        r_app = project_ball(st.R + r, (pol.B0 + pol.B * tj) * rho) - st.R
        lim = pol.B0s + pol.Bs * tj
        r_s_app = float(np.clip(st.Rs + r_s, -lim, lim)) - st.Rs
    elif pol.residual == "discard":
        r_app, r_s_app = np.zeros(D), 0.0
    else:
        r_app, r_s_app = r, r_s
    st.C, st.Cs = st.C + a, st.Cs + a_s
    st.R, st.Rs = st.R + r_app, st.Rs + r_s_app
    st.log.update(lam=lam, w=w, ws=ws, a=float(np.linalg.norm(a) / rho), r_app=float(np.linalg.norm(r_app) / rho),
                  R=float(np.linalg.norm(st.R) / rho), C=float(np.linalg.norm(st.C) / rho), Rs=st.Rs, Cs=st.Cs)
    return a + r_app, a_s + r_s_app
