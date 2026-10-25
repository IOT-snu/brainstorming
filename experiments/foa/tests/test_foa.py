"""
Unit and property tests. Run from experiments/foa:  python3 -m pytest -q tests
They use the synthetic fleet, so they need no dataset.
"""
import os, sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from robust import geometric_median, project_ball, minsker_constant, aggregate
from detector import Detector
import gossip
from synth import SynthStream, SynthWorld, D
from fleet import FleetSim, Member, POLICIES, variant, select_peers
from attacks import TrafficAttacker, Byzantine, Sybil


def fleet(n=7, seed=0, model=None):
    streams = [SynthStream(i, seed=seed) for i in range(n)]
    members = [Member(s.short, f"vendor{i}") for i, s in enumerate(streams)]
    return members, streams


# ---------------------------------------------------------------- robust primitives
def test_geometric_median_matches_numerical_minimum():
    from scipy.optimize import minimize
    rng = np.random.default_rng(0)
    for _ in range(20):
        X = rng.normal(size=(9, D)) * rng.uniform(0.1, 5)
        y = geometric_median(X, iters=200)
        f = lambda z: np.linalg.norm(X - z, axis=1).sum()
        ref = minimize(f, np.median(X, 0), method="Nelder-Mead", options=dict(maxiter=20000, xatol=1e-10, fatol=1e-12)).x
        assert f(y) <= f(ref) + 1e-6


def test_geometric_median_breakdown_below_half():
    rng = np.random.default_rng(1)
    honest = rng.normal(size=(5, D)) * 0.1
    for far in (1e2, 1e4, 1e6):
        bad = np.tile(far * np.ones(D) / np.sqrt(D), (4, 1))
        y = geometric_median(np.vstack([honest, bad]), iters=50)
        r = np.max(np.linalg.norm(honest, axis=1))
        assert np.linalg.norm(y) <= minsker_constant(4 / 9) * r + 1e-9   # Minsker Lemma 2.1
    # at half or more, the median follows the attackers
    y = geometric_median(np.vstack([honest[:4], np.tile(1e3 * np.ones(D), (4, 1))]), iters=50)
    assert np.linalg.norm(y) > 1.0


def test_project_ball():
    v = np.ones(D) * 3
    assert np.isclose(np.linalg.norm(project_ball(v, 2.0)), 2.0)
    assert np.allclose(project_ball(v, 100.0), v)


def test_aggregators():
    X = np.arange(12, dtype=float).reshape(4, 3)
    assert np.allclose(aggregate(X, "mean"), X.mean(0))
    assert np.allclose(aggregate(X, "cwmed"), np.median(X, 0))


# ---------------------------------------------------------------- detector
def test_detector_clean_false_alarm_rate_near_one_percent():
    s = SynthStream(0)
    det = Detector(s.cal)
    fpr = np.mean([np.mean(det.score(s.test(t, tuple(np.zeros(D)))) > det.tau) for t in range(50)])
    assert 0.003 < fpr < 0.025
    assert np.mean(det.score(s.attack_eval("atk", None)) > det.tau) > 0.99


def test_proposal_zero_on_empty_and_follows_shift():
    s = SynthStream(1)
    det = Detector(s.cal)
    assert np.allclose(det.propose(np.zeros((0, D))).dmu, 0)
    shift = np.zeros(D); shift[0] = 0.5
    p = det.propose(s.train(0, tuple(shift)), "auto")
    assert p.dmu[0] > 0.05 and abs(p.dmu[1:]).max() < 0.1


# ---------------------------------------------------------------- gossip
def test_frame_size_and_roundtrip():
    k = gossip.keys(3)
    f = gossip.pack(1, 77, np.arange(D) * 0.1, -0.02, 150, k[1])
    assert len(f) == gossip.FRAME_BYTES == 92
    res, why = gossip.verify(f, {1: k[1]}, 77)
    assert why == "ok" and res[0] == 1 and np.allclose(res[1], np.arange(D) * 0.1, atol=1e-6)


def test_frame_rejections():
    k = gossip.keys(3)
    f = gossip.pack(1, 77, np.zeros(D), 0.0, 150, k[1])
    assert gossip.verify(f, {1: k[1]}, 78)[1] == "stale"                     # replay
    assert gossip.verify(f, {2: k[2]}, 77)[1] == "unknown sender"            # not a peer
    forged = gossip.pack(1, 77, np.ones(D), 0.0, 150, b"\x00" * 32)
    assert gossip.verify(forged, {1: k[1]}, 77)[1] == "bad tag"              # no key
    tampered = bytearray(f); tampered[10] ^= 1
    assert gossip.verify(bytes(tampered), {1: k[1]}, 77)[1] == "bad tag"     # bit flip


# ---------------------------------------------------------------- FOA invariants
def run(policy, attackers=(), world=None, n=7, seed=0, cycles=200, **kw):
    members, streams = fleet(n, seed)
    sim = FleetSim(members, streams, world or SynthWorld(), policy, cycles=cycles, attackers=attackers, seed=seed, **kw)
    return sim, sim.run(eval_target={i: "atk" for i in range(n)})


def test_residual_never_exceeds_budget():
    pol = POLICIES["foa"]
    A = [TrafficAttacker(0, "atk", "boundary", 0.4, t0=20)]
    v = np.ones(D) / np.sqrt(D) * 6
    sim, out = run(pol, A, SynthWorld(common=(v, 30, 150)))
    t = np.arange(200)
    cap = pol.B0 + pol.B * t
    assert np.all(out["R"][:, 0] <= cap + 1e-9)
    assert np.all(out["C"][:, 0] <= pol.B0c + pol.Bc * t + 1e-9)
    lam = out["lam"][:, 0]
    assert np.nanmin(lam) >= 0 and np.nanmax(lam) <= 1


def test_foa_no_peers_is_budget_only():
    pol = variant("foa", "foa_nopeers", peers="none")
    sim, out = run(pol, [TrafficAttacker(0, "atk", "boundary", 0.4, t0=20)])
    assert np.nanmax(out["a"][:, 0]) == 0 or np.all(np.isnan(out["a"][:, 0]))
    assert np.all(out["disp"][:, 0] <= (pol.B0 + pol.B * np.arange(200)) * sim.dets[0].tau + 1e-6)


def test_foa_follows_common_drift_without_false_alarms():
    v = np.ones(D) / np.sqrt(D) * 6
    _, out = run(POLICIES["foa"], world=SynthWorld(common=(v, 30, 150)))
    _, st = run(POLICIES["static"], world=SynthWorld(common=(v, 30, 150)))
    assert np.mean(out["fpr"][160:]) < 0.03 < np.mean(st["fpr"][160:])


def test_foa_bounds_attack_hidden_in_drift_where_single_stream_fails():
    v = np.random.default_rng(1).normal(size=D); v = v / np.linalg.norm(v) * 7.6
    w = SynthWorld(common=(v, 40, 160))
    A = [TrafficAttacker(0, "atk", "boundary", 0.4, t0=40)]
    _, auto = run(POLICIES["auto"], A, w, cycles=240)
    _, foa = run(POLICIES["foa"], A, w, cycles=240)
    assert auto["rec"][-1, 0] < 0.5 and foa["rec"][-1, 0] > 0.7


def test_sybil_and_replay_frames_are_rejected():
    sy = Sybil(n_forged=20, replay=True, victim=0, target="atk", t0=10)
    sim, out = run(POLICIES["foa"], sybil=sy, cycles=40)
    rej = sim.stats["rejected"]
    assert rej.get("bad tag", 0) > 0 and rej.get("stale", 0) > 0
    # every accepted frame came from a genuine peer: at most n-1 per device per cycle
    assert sim.stats["accepted"] <= 40 * 7 * 6


def test_determinism():
    A = [TrafficAttacker(0, "atk", "boundary", 0.3, t0=20)]
    _, a = run(POLICIES["foa"], A, cycles=60)
    _, b = run(POLICIES["foa"], A, cycles=60)
    assert np.allclose(np.nan_to_num(a["disp"]), np.nan_to_num(b["disp"]))


def test_peer_selection():
    members = [Member("a", "v1"), Member("a", "v1"), Member("b", "v2"), Member("c", "v3")]
    assert select_peers(members, 0, "same", 0, 0) == [1]
    assert select_peers(members, 0, "diverse", 0, 0) == [2, 3]
    assert select_peers(members, 0, "all", 0, 0) == [1, 2, 3]
    assert len(select_peers(members, 0, "random", 2, 0)) == 2


def test_decoys_leave_foa_trajectory_unchanged():
    """Proposition 4 (i): traffic outside the alarm radius never enters FOA's update."""
    v = np.ones(D) / np.sqrt(D) * 7.6
    w = SynthWorld(common=(v, 30, 150))
    A = [TrafficAttacker(0, "atk", "decoy", 0.3, t0=30, t1=120)]
    _, clean = run(POLICIES["foa"], (), w, cycles=200)
    _, dec = run(POLICIES["foa"], A, w, cycles=200)
    assert np.array_equal(np.nan_to_num(clean["disp"]), np.nan_to_num(dec["disp"]))
    assert np.array_equal(np.nan_to_num(clean["spread"]), np.nan_to_num(dec["spread"]))
    # a stop-learning gate is frozen by the same decoys
    _, kl_clean = run(POLICIES["kl"], (), w, cycles=200)
    _, kl_dec = run(POLICIES["kl"], A, w, cycles=200)
    assert np.mean(kl_dec["fpr"][150:, 0]) > np.mean(kl_clean["fpr"][150:, 0]) + 0.2
