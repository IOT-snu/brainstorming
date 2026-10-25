"""
Theory checks on the controlled synthetic fleet (exact geometry known), complementing the real-data
experiments in experiments.py.

  S1  time to compromise vs residual budget slope B, measured against the Theorem 1 bound
      (boundary poisoner, share 40%, with and without common honest drift).
  S2  safety-liveness frontier: a device-specific honest drift of rate v is tracked iff v is
      below about B, the same rate the budget grants an attacker (Proposition 2).
  S3  consensus bias under f Byzantine peers vs the geometric-median bound C_alpha * r (Lemma).

Run: python3 synth_experiments.py   -> results/S*.pkl
"""
import multiprocessing as mp, os, pickle, sys, time
import numpy as np

from synth import SynthStream, SynthWorld, D
from fleet import FleetSim, Member, variant
from attacks import TrafficAttacker
from robust import geometric_median, minsker_constant

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
N = 9
BS = (0.00125, 0.0025, 0.005, 0.01, 0.02, 0.04)        # alarm radii per cycle


def fleet(seed):
    streams = [SynthStream(i, seed=seed) for i in range(N)]
    return [Member(s.short, f"v{i}") for i, s in enumerate(streams)], streams


def drift_vec(seed, norm=7.6):
    v = np.random.default_rng(100 + seed).normal(size=D)
    return v / np.linalg.norm(v) * norm


def s1_task(args):
    seed, B, drift = args
    members, streams = fleet(seed)
    world = SynthWorld(common=(drift_vec(seed), 40, 160)) if drift else SynthWorld()
    pol = variant("foa", f"foa_B{B}", B=B, Bs=0.2 * B)
    T = 500
    sim = FleetSim(members, streams, world, pol, cycles=T, attackers=[TrafficAttacker(0, "atk", "boundary", 0.4, t0=40)], seed=seed)
    out = sim.run(eval_target={i: "atk" for i in range(N)})
    rec, d50, reach = out["rec"][:, 0], out["d50"][:, 0], out["reach"][:, 0]
    hit = np.where(rec[40:] < 0.5)[0]
    hb = np.where(d50[40:] <= reach[40:])[0]
    det = sim.dets[0]
    # closed-form bound with no common movement: d50(0) <= tau*exp(B0s+Bs t) + (B0 + B t) tau  (spreads)
    d0 = float(np.median(np.linalg.norm(streams[0].attack_eval("atk", None) - det.mu0, axis=1)) / det.s0)
    ts = np.arange(T)
    cf = np.where(d0 <= det.tau * np.exp(pol.B0s + pol.Bs * ts) + (pol.B0 + pol.B * ts) * det.tau)[0]   # separate budgets
    return dict(seed=seed, B=B, drift=drift, ttc=int(40 + hit[0]) if len(hit) else None,
                t_bound=int(40 + hb[0]) if len(hb) else None, t_closed=int(cf[0]) if len(cf) else None,
                violations=int(np.sum((rec < 0.5) & (d50 > reach + 1e-9))), rec=rec.astype(np.float32),
                fpr=np.nanmean(out["fpr"][:, 1:], 1).astype(np.float32), d0=d0, tau=det.tau)


def s2_task(args):
    seed, B, v = args
    members, streams = fleet(seed)
    u = np.random.default_rng(200 + seed).normal(size=D); u /= np.linalg.norm(u)
    ramp = 120
    world = SynthWorld(idio={0: (u * v * ramp, 40, 40 + ramp)})
    pol = variant("foa", f"foa_B{B}", B=B, Bs=0.2 * B)
    out = FleetSim(members, streams, world, pol, cycles=260, seed=seed).run()
    f = out["fpr"][:, 0]
    return dict(seed=seed, B=B, v=v, fpr_drift=float(np.mean(f[40:160])), fpr_tail=float(np.mean(f[220:])),
                lost=bool(np.mean(f[220:]) > 0.5), fpr=f.astype(np.float32))


def s3():
    rng = np.random.default_rng(0)
    rows = []
    K = 9
    for f in range(0, 5):
        alpha = f / K
        for trial in range(400):
            H = rng.normal(size=(K - f, D)) * 0.05 + 0.02          # honest proposals (shared drift + noise)
            z = geometric_median(H, iters=100)
            r = float(np.max(np.linalg.norm(H - z, axis=1)))
            direction = rng.normal(size=D); direction /= np.linalg.norm(direction)
            far = rng.uniform(1, 1000)
            A = np.tile(z + far * r * direction, (f, 1))
            m = geometric_median(np.vstack([H, A]), iters=100) if f else z
            rows.append(dict(f=f, alpha=alpha, bias_over_r=float(np.linalg.norm(m - z) / r), bound=minsker_constant(alpha)))
    return rows


def main():
    os.makedirs(RES, exist_ok=True)
    ctx = mp.get_context("fork")
    seeds = range(10)
    with ctx.Pool(max(1, os.cpu_count() - 1)) as pool:
        t0 = time.time()
        s1 = pool.map(s1_task, [(s, B, d) for s in seeds for B in BS for d in (False, True)])
        print(f"S1 {len(s1)} runs {time.time() - t0:.0f}s, bound violations {sum(r['violations'] for r in s1)}", flush=True)
        t0 = time.time()
        vs = (0.0025, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16)
        s2 = pool.map(s2_task, [(s, B, v) for s in range(5) for B in BS for v in vs])
        print(f"S2 {len(s2)} runs {time.time() - t0:.0f}s", flush=True)
    s3r = s3()
    pickle.dump(dict(S1=s1, S2=s2, S3=s3r), open(os.path.join(RES, "S.pkl"), "wb"))
    for B in BS:
        for d in (False, True):
            rs = [r for r in s1 if r["B"] == B and r["drift"] == d]
            ttc = [r["ttc"] for r in rs]
            print(f"B={B:<6} drift={d!s:5}  ttc={['>500' if x is None else x for x in ttc]}  bound={rs[0]['t_bound']} closed={rs[0]['t_closed']}")
    for B in BS:
        print(f"B={B:<6} lost at v=" + " ".join(f"{v}:{np.mean([r['lost'] for r in s2 if r['B'] == B and r['v'] == v]):.1f}" for v in vs))
    for f in range(5):
        b = [r["bias_over_r"] for r in s3r if r["f"] == f]
        print(f"f={f}/9 bias/r max {max(b):.3f}  bound {minsker_constant(f / 9):.3f}")


if __name__ == "__main__":
    main()
