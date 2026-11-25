"""
E12: the coverage floor (spread never below its calibrated value) on held-out seeds 2-11, same traffic for
all rules. gamma = 1.0 was chosen on development seeds (dev_floor.py). Also repetitive-traffic seeds 8-27.
Run: python3 floor_eval.py  -> results/E12.pkl, results/E12.txt
"""
import multiprocessing as mp, pickle, warnings
import numpy as np
import experiments as E
from fleet import variant
from repro import run

E.VARIANTS["foa_floor"] = variant("foa", "foa_floor", s_floor=1.0)
E.VARIANTS["auto_floor"] = variant("auto", "auto_floor", s_floor=1.0)
E.VARIANTS["foa_same_floor"] = variant("foa", "foa_same_floor", peers="same", s_floor=1.0)
P = ["auto", "auto_floor", "foa", "foa_floor"]
NAMES = dict(auto="Single device", auto_floor="Single device + floor", foa="FOA", foa_floor="FOA + floor")


def tasks():
    T = []
    for s in range(2, 12):
        for d in ("moderate", "strong"):
            T.append(dict(exp="E12", fleet="F9", seed=s, drift=d, policies=P, tags=dict(k=d)))
        for v in range(9):
            T.append(dict(exp="E12", fleet="F9", seed=s, idio={v: E.IDIO}, policies=P, tags=dict(k="idio")))
        for v in E.SCAN_VICTIMS:
            for m in ("boundary", "core", "mimicry"):
                for p in (0.1, 0.2, 0.3, 0.4):
                    for d in ("none", "strong"):
                        T.append(dict(exp="E12", fleet="F9", seed=s, drift=d, attackers=[E.att(v, m, p)], policies=P,
                                      traces=False, tags=dict(k="atk_" + d, mode=m, p=p)))
        for k in (1, 2, 3):
            T.append(dict(exp="E12", fleet="F12", seed=s, drift="strong", attackers=[E.att(v, "boundary", 0.3) for v in range(k)],
                          policies=P + ["foa_same_floor"], tags=dict(k="mono", infected=k)))
    return T


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    E.space()
    for n in E.data.SHORT: E.data.raw(n)
    with mp.get_context("fork").Pool(9) as pool:
        R = [r for rs in pool.map(E.run_task, tasks()) for r, _ in rs]
    pickle.dump(R, open("results/E12.pkl", "wb"))
    m = lambda key, **f: 100 * np.nanmean([r[key] for r in R if all(r.get(a) == b for a, b in f.items()) and r.get(key) is not None])
    L = [f"{len(R)} runs", f"{'rule':24s} mod FPR  strong FPR  idio FPR | comp no-drift (bnd core mim all) | comp strong drift (bnd core mim all) | attacked fleet FPR"]
    for p in P:
        L.append(f"{NAMES[p]:24s} {m('fpr_fleet_after',policy=p,k='moderate'):7.1f} {m('fpr_fleet_after',policy=p,k='strong'):11.1f} {m('fpr_v_after',policy=p,k='idio'):9.1f} | "
                 + " | ".join(" ".join(f"{m('compromised_attr',policy=p,k=k,mode=md):5.1f}" for md in ("boundary", "core", "mimicry")) + f" {m('compromised_attr',policy=p,k=k):5.1f}" for k in ("atk_none", "atk_strong"))
                 + f" | {m('fpr_fleet_after',policy=p,k='atk_strong'):5.1f}")
    for p in P + ["foa_same_floor"]:
        L.append(f"monoculture {p:15s} compromised for 1/2/3 infected: " + " ".join(f"{m('compromised_attr',policy=p,k='mono',infected=k):5.1f}" for k in (1, 2, 3)))
    for p in P:
        o = [run(E.policy(p), s) for s in range(8, 28)]
        f = [100 * np.nanmean(x["fpr"][-20:]) for x in o]
        L.append(f"repetitive traffic {NAMES[p]:24s} mean FPR {np.mean(f):5.1f}  worst {max(f):5.1f}  runs above 10%: {sum(v > 10 for v in f)}/20")
    open("results/E12.txt", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
