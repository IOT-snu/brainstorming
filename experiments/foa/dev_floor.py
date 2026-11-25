"""Development-seed comparison for the coverage floor (seeds 0 and 1 for N-BaIoT; repetitive traffic seeds 0-7)."""
import multiprocessing as mp, numpy as np
import experiments as E
from fleet import variant
from repro import run
G = (0.8, 0.9, 1.0)
for g in G:
    E.VARIANTS[f"foa_f{g}"] = variant("foa", f"foa_f{g}", s_floor=g)
    E.VARIANTS[f"auto_f{g}"] = variant("auto", f"auto_f{g}", s_floor=g)
P = ["auto", "foa"] + [f"auto_f{g}" for g in G] + [f"foa_f{g}" for g in G]

if __name__ == "__main__":
    import warnings; warnings.filterwarnings("ignore")
    for p in P:
        o = [run(E.policy(p), s) for s in range(8)]
        print(f"repetitive {p:10s} FPR {100*np.mean([np.nanmean(x['fpr'][-20:]) for x in o]):5.1f}%  worst {100*max(np.nanmean(x['fpr'][-20:]) for x in o):5.1f}%")
    T = []
    for s in (0, 1):
        T.append(dict(exp="D", fleet="F9", seed=s, drift="strong", policies=P, tags=dict(k="live")))
        for v in E.SCAN_VICTIMS:
            T.append(dict(exp="D", fleet="F9", seed=s, idio={v: E.IDIO}, policies=P, tags=dict(k="idio")))
            for m in ("boundary", "core", "mimicry"):
                for d in ("none", "strong"):
                    T.append(dict(exp="D", fleet="F9", seed=s, drift=d, attackers=[E.att(v, m, 0.4)], policies=P, tags=dict(k="atk" + d, mode=m)))
    E.space()
    for n in E.data.SHORT: E.data.raw(n)
    with mp.get_context("fork").Pool(9) as pool:
        R = [r for rs in pool.map(E.run_task, T) for r, _ in rs]
    m = lambda p, k, key: 100 * np.nanmean([r[key] for r in R if r["policy"] == p and r["k"] == k])
    for p in P:
        print(f"{p:10s} drift FPR {m(p,'live','fpr_fleet_after'):5.1f}  idio FPR {m(p,'idio','fpr_v_after'):5.1f}  compromised: no drift {m(p,'atknone','compromised_attr'):5.1f}  strong drift {m(p,'atkstrong','compromised_attr'):5.1f}")
