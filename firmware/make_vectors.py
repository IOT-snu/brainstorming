"""
Record test vectors from the Python reference so host_test.c can check the C implementation.

Each case is one cycle of one device: detector state, its batch, its verified peer proposals, and
what Python computed (proposal, FOA output, FOA state after). Cases come from synthetic fleets with
honest drift, a boundary poisoner on the traced device, and heavy packet loss (so the peer count
varies and sometimes falls below k_min). Also records gossip frames for byte-level comparison.

Run from the repo root:  python3 firmware/make_vectors.py  ->  firmware/vectors.bin
"""
import os, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments", "foa"))
from synth import SynthStream, SynthWorld, D
from fleet import FleetSim, Member, POLICIES
from attacks import TrafficAttacker
import gossip

F = lambda xs: struct.pack(f"<{len(xs)}f", *[float(x) for x in xs])
I = lambda *xs: struct.pack(f"<{len(xs)}i", *xs)
ST = ("C", "R", "m_ema", "p_ema")
SC = ("Cs", "Rs", "ms_ema", "ps_ema", "pa_ema", "sig_ema", "sigs_ema")


def state_bytes(st):
    return b"".join(F(np.asarray(st[k])) for k in ST) + F([st[k] for k in SC])


def record(seed, loss, n=7, cycles=160):
    v = np.random.default_rng(seed).normal(size=D); v = v / np.linalg.norm(v) * 6
    streams = [SynthStream(i, seed=seed) for i in range(n)]
    members = [Member(s.short, f"v{i}") for i, s in enumerate(streams)]
    sim = FleetSim(members, streams, SynthWorld(common=(v, 30, 130)), POLICIES["foa"], cycles=cycles,
                   attackers=[TrafficAttacker(0, "atk", "boundary", 0.3, t0=30)], loss=loss, seed=seed, trace_device=0)
    sim.run()
    return sim.dets[0], sim.trace


def main():
    pol = POLICIES["foa"]
    cases, det = [], None
    for seed, loss in ((0, 0.0), (1, 0.0), (2, 0.85)):
        det, tr = record(seed, loss)
        cases += [(det, c) for c in tr]
    out = bytearray(b"FOAV1\0\0\0")
    out += I(len(cases))
    d0 = cases[0][0]
    out += F(list(d0.mu0) + [d0.s0, d0.tau, d0.c, d0.kappa, d0.beta, d0.f0, d0.eta])
    out += F([pol.B0, pol.B, pol.B0s, pol.Bs, pol.B0c, pol.Bc, pol.B0cs, pol.Bcs, pol.alpha, pol.z0, pol.z1])
    out += I(pol.k_min, int(pol.lam_gate), int(pol.signif), int(pol.common_budget), int(pol.robust_lam))
    for det, c in cases:
        X, peers = c["batch"], c["peers"]
        out += I(c["tj"], len(X), len(peers))
        out += F(list(det.mu0) + [det.s0, det.tau, det.c, det.kappa, det.beta, det.f0, det.eta])
        out += F(list(c["mu"]) + [c["s"]])
        out += state_bytes(c["st_in"])
        out += F(X.ravel())
        out += F(np.array([p[0] for p in peers]).ravel()) + F([p[1] for p in peers])
        p = c["prop"]
        out += F(list(p.dmu) + [p.dls, p.along]) + I(p.n_core)
        out += F(list(c["out_dmu"]) + [c["out_dls"]])
        out += state_bytes(c["st_out"])
    keys = gossip.keys(4, seed=9)
    rng = np.random.default_rng(5)
    frames = []
    for k in range(32):
        snd, cyc = k % 4, int(rng.integers(0, 1 << 31))
        dmu = rng.normal(size=D).astype(np.float32); dls = float(np.float32(rng.normal() * 0.01)); nc = int(rng.integers(0, 300))
        frames.append((snd, cyc, dmu, dls, nc, keys[snd], gossip.pack(snd, cyc, dmu, dls, nc, keys[snd])))
    out += I(len(frames))
    for snd, cyc, dmu, dls, nc, key, fr in frames:
        out += struct.pack("<BI", snd, cyc) + F(dmu) + F([dls]) + struct.pack("<H", nc) + key + fr
    path = os.path.join(HERE, "vectors.bin")
    open(path, "wb").write(bytes(out))
    print(f"wrote {path}: {len(cases)} cycles, {len(frames)} frames, {len(out)} bytes")


if __name__ == "__main__":
    main()
