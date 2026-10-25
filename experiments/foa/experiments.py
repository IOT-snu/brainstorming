"""
Experiment runner. Every experiment of the paper is a list of tasks; a task fixes the fleet, the
honest drift, the attackers and the seed, and runs every rule in its policy list on exactly the same
traffic. Results go to results/<EXP>.pkl (rows of metrics plus victim-averaged traces) and a
human-readable results/<EXP>.csv.

Run:  python3 experiments.py E1 E2 ...   (or `all`)     options: --seeds N  --jobs N  --quick
"""
import argparse, csv, multiprocessing as mp, os, pickle, sys, time
import numpy as np

import data
from data import Stream, World, INFO
from fleet import FleetSim, Member, POLICIES, variant
from attacks import TrafficAttacker, Byzantine, Sybil

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
CYCLES = 240
T_ATT, T_D0, T_D1 = 40, 40, 160
W = dict(pre=(0, 40), drift=(40, 160), after=(160, 240), tail=(200, 240))

# Honest drift. Kitsune's per-packet log statistics barely move under small changes (packet rate x8
# raises the static detector's false alarms only to 22%), so strength is set, before any adaptive
# rule is run, by the static detector's fleet-mean false-alarm rate under the full change:
#   moderate  rate x16, +160 B overhead, jitter x5      static FPR about 34%
#   strong    rate x64, +240 B overhead, jitter x11.4   static FPR about 78%
# These are stress tests of a large shared change; CESNET (cesnet.py) supplies real drift.
DRIFT = {
    "none": None,
    "moderate": dict(g=16.0, b=160.0, h=5.0625, t0=T_D0, t1=T_D1),
    "strong": dict(g=64.0, b=240.0, h=11.3906, t0=T_D0, t1=T_D1),
}
IDIO = dict(g=32.0, b=200.0, h=7.5938, t0=60, t1=120)      # one device's own large change (static FPR about 59%)

VARIANTS = {
    "foa_mean": variant("foa", "foa_mean", agg="mean"),
    "foa_cwmed": variant("foa", "foa_cwmed", agg="cwmed"),
    "foa_nolam": variant("foa", "foa_nolam", lam_gate=False),
    "foa_nosig": variant("foa", "foa_nosig", signif=False),
    "foa_nocb": variant("foa", "foa_nocb", common_budget=False),
    "foa_discard": variant("foa", "foa_discard", residual="discard"),
    "foa_full": variant("foa", "foa_full", residual="full"),
    "foa_nopeers": variant("foa", "foa_nopeers", peers="none"),
    "foa_same": variant("foa", "foa_same", peers="same"),
    "foa_all": variant("foa", "foa_all", peers="all"),
    "foa_rand3": variant("foa", "foa_rand3", peers="random", k_peers=3),
    "foa_div3": variant("foa", "foa_div3", peers="diverse", k_peers=3),
    "foa_div2": variant("foa", "foa_div2", peers="diverse", k_peers=2),
    "foa_div5": variant("foa", "foa_div5", peers="diverse", k_peers=5),
    "foa_nohmac": variant("foa", "foa_nohmac", hmac=False),
}
BSWEEP = (0.00125, 0.0025, 0.005, 0.01, 0.02, 0.04)      # alarm radii per cycle; spread slope 0.2 B
for b in BSWEEP:
    VARIANTS[f"foa_B{b}"] = variant("foa", f"foa_B{b}", B=b, Bs=0.2 * b)
VARIANTS["foa_meanlam"] = variant("foa", "foa_meanlam", robust_lam=False)
VARIANTS["foa_own"] = variant("foa", "foa_own", common_dir="own")
VARIANTS["foa_tcs"] = variant("foa", "foa_tcs", B0cs=0.1, Bcs=0.001)
VARIANTS["foa_own_tcs"] = variant("foa", "foa_own_tcs", common_dir="own", B0cs=0.1, Bcs=0.001)
VARIANTS["foa_joint"] = variant("foa", "foa_joint", joint=True)
VARIANTS["foa_widespread"] = variant("foa", "foa_widespread", B0s=0.2, Bs=0.002)

# Development seeds 0 and 1 were used for every design choice (robust agreement, spread budget,
# drift strength, victim criterion). Every reported number uses the held-out seeds below.
SEED0 = 2


def policy(name):
    return POLICIES.get(name) or VARIANTS[name]


# ------------------------------------------------------------------------ fleets
def fleet_members(name):
    if name == "F9":
        return [Member(s, INFO[s]["vendor"]) for s in data.SHORT]
    if name == "F12":
        return [Member(s, INFO[s]["vendor"], instance=k) for s in ("sh1003", "prov737", "danmini", "ecobee") for k in range(3)]
    if name == "AV":   # whatever devices are downloaded (pilot runs only)
        return [Member(s, INFO[s]["vendor"]) for s in data.available()]
    if name == "F4":   # the hardware testbed size: four nodes, four vendors
        return [Member(s, INFO[s]["vendor"]) for s in ("danmini", "ecobee", "prov838", "sh1003")]
    raise ValueError(name)


SPACE = None


def space():
    global SPACE
    if SPACE is None:
        SPACE = data.Space(data.SHORT)
    return SPACE


def build_streams(members, seed):
    sp = space()
    return [Stream(m.short, sp, instance=m.instance, cycles=CYCLES, seed=seed, cal_sub=1.0 if m.instance == 0 else 0.7)
            for m in members]


# ------------------------------------------------------------------------ one task
_CONTROL = {}


def control_recall(task, members, streams, world, pname, eval_target):
    """Recall of the same rule on the same traffic with no attacker. Honest drift can by itself carry
    benign traffic toward an attack class; only recall lost beyond this control counts as poisoning."""
    key = (task["fleet"], task["seed"], task.get("drift", "none"), repr(sorted(task.get("idio", {}).items())),
           task.get("loss", 0.0), repr(sorted(task.get("joins", {}).items())), task.get("join_mode", "self"),
           tuple(task.get("byz_nodes", [])), pname)
    if key not in _CONTROL:
        if len(_CONTROL) > 400:
            _CONTROL.clear()
        from dataclasses import replace as _r
        honest = [_r(m, byzantine=False) for m in members]       # in the twin, every node is honest
        sim = FleetSim(honest, streams, world, policy(pname), cycles=CYCLES, seed=task["seed"],
                       loss=task.get("loss", 0.0), join_mode=task.get("join_mode", "self"))
        _CONTROL[key] = sim.run(eval_target=eval_target)["rec"]
    return _CONTROL[key]

def window_mean(x, w):
    a, b = W[w]
    v = x[a:b]
    return float(np.nanmean(v)) if np.isfinite(v).any() else float("nan")


def summarize(out, victims, focus, others, t_att, ctrl=None):
    r = {}
    if victims:
        rec = out["rec"][:, victims]
        if ctrl is not None:
            rc = ctrl[:, victims]
            lost = (rec < 0.5) & (rc >= 0.5)            # attack-attributable loss of detection
            ta = []
            for k in range(len(victims)):
                hit = np.where(lost[t_att:, k])[0]
                ta.append(int(t_att + hit[0]) if len(hit) else None)
            r["ttc_attr"] = ta
            r["compromised_attr"] = float(np.mean([x is not None for x in ta]))
            r["rec_gap"] = float(np.nanmean(rc[t_att:] - rec[t_att:]))
            r["rec_ctrl_final"] = float(np.nanmean(rc[-10:]))
        ttcs = []
        for k in range(len(victims)):
            hit = np.where(rec[t_att:, k] < 0.5)[0]
            ttcs.append(int(t_att + hit[0]) if len(hit) else None)
        r["ttc"] = ttcs
        r["compromised"] = float(np.mean([x is not None for x in ttcs]))
        r["rec_final"] = float(np.nanmean(rec[-10:]))
        r["rec_attack"] = float(np.nanmean(rec[t_att:]))
        q = out["q_acc"][:, victims]; qc = out["q_core"][:, victims]
        r["q_acc"] = float(np.nanmean(q)) if np.isfinite(q).any() else float("nan")
        r["q_core"] = float(np.nanmean(qc)) if np.isfinite(qc).any() else float("nan")
        d50, reach = out["d50"][:, victims], out["reach"][:, victims]
        if np.isfinite(d50).any():
            viol = (rec < 0.5) & (d50 > reach + 1e-9)
            r["bound_violations"] = int(np.sum(viol))
            tb = []
            for k in range(len(victims)):
                hit = np.where(d50[t_att:, k] <= reach[t_att:, k])[0]
                tb.append(int(t_att + hit[0]) if len(hit) else None)
            r["t_bound"] = tb
    if focus:
        f = np.nanmean(out["fpr"][:, focus], 1)
        for w in W:
            r[f"fpr_v_{w}"] = window_mean(f, w)
    if others:
        f = np.nanmean(out["fpr"][:, others], 1)
        for w in W:
            r[f"fpr_fleet_{w}"] = window_mean(f, w)
        ro = out["rec"][:, others]
        if np.isfinite(ro).any():
            r["rec_fleet_final"] = float(np.nanmean(ro[-10:]))
    r["applied_frac"] = float(np.mean(out["applied"][:, focus or others])) if (focus or others) else float("nan")
    r["bytes_sent"] = out["stats"]["bytes_sent"]
    r["rejected"] = dict(out["stats"]["rejected"])
    tr = {}
    idx = focus or others
    for k in ("rec", "fpr", "disp", "spread", "R", "C", "lam", "w", "d50", "reach", "q_acc"):
        v = out[k][:, idx]
        tr[k] = np.nanmean(v, 1).astype(np.float32) if np.isfinite(v).any() else None
    tr["fpr_fleet"] = np.nanmean(out["fpr"][:, others], 1).astype(np.float32) if others else None
    return r, tr


def run_task(task):
    import warnings
    warnings.filterwarnings("ignore")
    members = fleet_members(task["fleet"])
    for b in task.get("byz_nodes", []):
        members[b].byzantine = True
    for j in task.get("joins", {}):
        members[int(j)].join = task["joins"][j]
    seed = task["seed"]
    streams = build_streams(members, seed)
    world = World(DRIFT[task.get("drift", "none")],
                  {int(k): v for k, v in task.get("idio", {}).items()})
    attackers = []
    for a in task.get("attackers", []):
        tgt = streams[a["victim"]].target_name(a.get("target", "scan"))
        attackers.append(TrafficAttacker(a["victim"], tgt, a.get("mode", "boundary"), a.get("p", 0.3),
                                         a.get("t0", T_ATT), a.get("t1", 10**9), a.get("on", 0), a.get("off", 0)))
    victims = sorted({a.victim for a in attackers})
    byz = None
    if task.get("byz"):
        b = task["byz"]
        byz = Byzantine(task["byz_nodes"], b["victim"], streams[b["victim"]].target_name(b.get("target", "scan")),
                        b.get("t0", T_ATT), scale=b.get("scale", 10.0), style=b.get("style", "aim"))
        victims = sorted(set(victims) | {b["victim"]})
    syb = None
    if task.get("sybil"):
        s = task["sybil"]
        syb = Sybil(s.get("n", 8), s.get("replay", True), s["victim"], streams[s["victim"]].target_name("scan"), s.get("t0", T_ATT))
        victims = sorted(set(victims) | {s["victim"]})
    focus = victims or [int(k) for k in task.get("idio", {})]
    others = [i for i in range(len(members)) if i not in focus and not members[i].byzantine]
    eval_target = {i: streams[i].target_name("scan") for i in range(len(members))}
    t_att = min([a.t0 for a in attackers] + ([byz.t0] if byz else []) + ([syb.t0] if syb else [])) \
        if (attackers or byz or syb) else T_ATT
    rows = []
    for pname in task["policies"]:
        t0 = time.time()
        sim = FleetSim(members, streams, world, policy(pname), cycles=CYCLES, attackers=attackers, byzantine=byz,
                       sybil=syb, loss=task.get("loss", 0.0), seed=seed, join_mode=task.get("join_mode", "self"))
        out = sim.run(eval_target=eval_target)
        ctrl = None
        if (attackers or byz or syb) and task.get("control", True):
            ctrl = control_recall(task, members, streams, world, pname, eval_target)
        r, tr = summarize(out, victims, focus, others, t_att, ctrl)
        row = dict(task.get("tags", {}), exp=task["exp"], policy=pname, seed=seed, secs=time.time() - t0, **r)
        rows.append((row, tr if task.get("traces", True) else None))
    return rows


# ------------------------------------------------------------------------ experiment grids
BASE = ["static", "naive", "auto", "clip", "frozen", "kl", "or", "foa"]
# Victims: devices whose target (scan) traffic lies at least 1.3 alarm radii out (median score / tau)
# under the calibrated static detector, measured before any adaptive run (analysis_e0.py). Philips
# (1.04) and SimpleHome 1002 (1.16) are too close to their own benign traffic for a centroid detector
# to protect; they stay in the fleet as peers.
SCAN_VICTIMS = [0, 1, 2, 4, 5, 6, 8]


def att(v, mode="boundary", p=0.3, **kw):
    return dict(victim=v, mode=mode, p=p, **kw)


def grid(exp, seeds, quick=False):
    S = range(SEED0, SEED0 + seeds)
    T = []
    if exp == "E1":     # liveness: honest drift only
        for s in S:
            for d in ("moderate", "strong"):
                T.append(dict(exp=exp, fleet="F9", seed=s, drift=d, policies=BASE + ["toa"], tags=dict(scenario=f"common_{d}")))
            for v in SCAN_VICTIMS:
                T.append(dict(exp=exp, fleet="F9", seed=s, idio={v: IDIO}, policies=BASE, tags=dict(scenario="idio", device=v)))
            T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", idio={1: IDIO}, policies=BASE, tags=dict(scenario="both", device=1)))
    elif exp == "E2":   # poisoning, no drift
        for s in S:
            for v in SCAN_VICTIMS:
                for mode in ("boundary", "core", "mimicry"):
                    for p in (0.1, 0.2, 0.3, 0.4):
                        T.append(dict(exp=exp, fleet="F9", seed=s, attackers=[att(v, mode, p)],
                                      policies=["naive", "auto", "clip", "frozen", "kl", "toa", "foa"], traces=False,
                                      tags=dict(victim=v, mode=mode, p=p)))
    elif exp == "E3":   # attack hidden in strong honest drift (headline 1)
        for s in S:
            for v in SCAN_VICTIMS:
                for mode in ("boundary", "core", "mimicry"):
                    for p in (0.1, 0.2, 0.3, 0.4):
                        T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", attackers=[att(v, mode, p)],
                                      policies=["naive", "auto", "clip", "frozen", "kl", "or", "toa", "foa"],
                                      traces=(p == 0.3), tags=dict(victim=v, mode=mode, p=p)))
    elif exp == "E4":   # monoculture botnet vs same-model consensus (headline 2)
        for s in S:
            for d in ("none", "strong"):
                for k in (1, 2, 3):
                    T.append(dict(exp=exp, fleet="F12", seed=s, drift=d, attackers=[att(v, "boundary", 0.3) for v in range(k)],
                                  policies=["auto", "ciota", "foa_same", "foa", "foa_all"], tags=dict(infected=k, drift=d)))
    elif exp == "E5":   # freeze attack (decoys) then honest drift; attacker leaves at 100
        for s in S:
            for v in (0, 1, 4, 8):
                for p in (0.05, 0.1, 0.2):
                    T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong",
                                  attackers=[dict(victim=v, mode="decoy", p=p, t0=T_D0, t1=100, target="udp")],
                                  policies=["naive", "auto", "kl", "or", "frozen", "foa"], tags=dict(victim=v, p=p, attacker=True)))
                T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", idio={v: dict(g=1.0, b=0.0, t0=0, t1=0)},
                              policies=["naive", "auto", "kl", "or", "frozen", "foa"], tags=dict(victim=v, p=0.0, attacker=False)))
    elif exp == "E6":   # gossip attacks: Byzantine peers, Sybil, packet loss
        for s in S:
            for f in (0, 1, 2, 3, 4, 5):           # f = 4 of 7 is past the geometric median's breakdown
                nodes = [2, 4, 5, 6, 0, 1, 3][:f]          # peers of the victim (sh1003, index 8): K = 7
                for drift in ("none", "strong"):
                    T.append(dict(exp=exp, fleet="F9", seed=s, drift=drift, byz_nodes=nodes, byz=dict(victim=8) if f else None,
                                  attackers=[att(8, "boundary", 0.3)], policies=["foa", "foa_nocb", "foa_mean"],
                                  tags=dict(kind="byzantine", f=f, drift=drift)))
            for hm in ("foa", "foa_nohmac"):
                T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", sybil=dict(victim=8, n=12), attackers=[att(8, "boundary", 0.3)],
                              policies=[hm], tags=dict(kind="sybil")))
            for loss in (0.0, 0.1, 0.3, 0.5, 0.7, 0.9):
                T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", loss=loss, attackers=[att(8, "boundary", 0.3)],
                              policies=["foa"], tags=dict(kind="loss", loss=loss)))
    elif exp == "E6b":  # Byzantine peers alone vs together with a traffic poisoner, every qualifying victim
        for s in S:
            for v in (0, 1, 2, 5, 8):
                vend = INFO[data.SHORT[v]]["vendor"]
                peers = [j for j in range(9) if j != v and INFO[data.SHORT[j]]["vendor"] != vend]
                for f in (0, 1, 2, 3, 4):
                    nodes = peers[:f]
                    for traffic in (False, True):
                        T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", byz_nodes=nodes,
                                      byz=dict(victim=v) if f else None,
                                      attackers=[att(v, "boundary", 0.3)] if traffic else [],
                                      policies=["auto", "foa"], tags=dict(victim=v, f=f, K=len(peers), traffic=traffic)))
    elif exp == "E7":   # theory: budget sweep (safety) and liveness (idiosyncratic drift)
        Bs = [f"foa_B{b}" for b in BSWEEP]
        for s in S:
            for v in (0, 1, 4, 8):
                for d in ("none", "strong"):
                    T.append(dict(exp=exp, fleet="F9", seed=s, drift=d, attackers=[att(v, "boundary", 0.4)], policies=Bs + ["auto"],
                                  tags=dict(kind="safety", victim=v, drift=d)))
                T.append(dict(exp=exp, fleet="F9", seed=s, idio={v: IDIO}, policies=Bs + ["auto", "frozen", "kl", "static"],
                              tags=dict(kind="liveness", victim=v)))
    elif exp == "E8":   # ablations and adaptive attackers
        abl = ["foa", "foa_mean", "foa_cwmed", "foa_nolam", "foa_meanlam", "foa_nosig", "foa_nocb", "foa_discard", "foa_full",
               "foa_nopeers", "foa_joint", "foa_widespread", "foa_all", "foa_rand3", "foa_div3", "foa_div2", "foa_div5"]
        for s in S:
            for v in (0, 4, 8):
                T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", attackers=[att(v, "boundary", 0.3)], policies=abl,
                              tags=dict(kind="ablation_attack", victim=v)))
                T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", idio={v: IDIO}, policies=abl,
                              tags=dict(kind="ablation_liveness", victim=v)))
                for mode, extra in (("multidir", {}), ("aligned", {}), ("boundary", dict(on=5, off=5)), ("core", {}), ("mimicry", {})):
                    T.append(dict(exp=exp, fleet="F9", seed=s, drift="strong", attackers=[att(v, mode, 0.3, **extra)],
                                  policies=["auto", "foa"], tags=dict(kind="adaptive", victim=v, mode=mode + ("_pulse" if extra else ""))))
    elif exp == "E9":   # join: a new camera joins at cycle 60 while its first window is poisoned
        for s in S:
            for p in (0.0, 0.1, 0.2, 0.3):
                for jm in ("self", "warm"):
                    A = [att(2, "boundary", p, t0=55)] if p else []
                    T.append(dict(exp=exp, fleet="F12", seed=s, joins={2: 60}, join_mode=jm, drift="none", attackers=A,
                                  policies=["auto", "foa"], tags=dict(p=p, join=jm)))
    elif exp == "E10":  # hardware-size fleet: four nodes
        for s in S:
            for v in range(4):
                T.append(dict(exp=exp, fleet="F4", seed=s, drift="strong", attackers=[att(v, "boundary", 0.3)],
                              policies=["auto", "kl", "frozen", "foa"], tags=dict(victim=v)))
            T.append(dict(exp=exp, fleet="F4", seed=s, drift="strong", policies=["static", "auto", "kl", "frozen", "foa"], tags=dict(victim=-1)))
    if quick:
        T = T[:: max(1, len(T) // 12)]
    return T


EXPS = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exps", nargs="+")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--jobs", type=int, default=max(1, os.cpu_count() - 1))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    exps = EXPS if a.exps == ["all"] else a.exps
    os.makedirs(RES, exist_ok=True)
    for name in data.available():
        data.raw(name)
    space()
    ctx = mp.get_context("fork")
    for e in exps:
        if e == "E11":
            run_cesnet(min(a.seeds, 5), a.jobs)
            continue
        tasks = grid(e, a.seeds, a.quick)
        t0 = time.time()
        rows = []
        with ctx.Pool(a.jobs) as pool:
            for k, rs in enumerate(pool.imap_unordered(run_task, tasks, chunksize=1)):
                rows += rs
                if (k + 1) % max(1, len(tasks) // 20) == 0:
                    print(f"{e}: {k + 1}/{len(tasks)} tasks, {time.time() - t0:.0f}s", flush=True)
        suffix = "_quick" if a.quick else ""
        pickle.dump(rows, open(os.path.join(RES, f"{e}{suffix}.pkl"), "wb"))
        keys = []
        for r, _ in rows:
            keys += [k for k in r if k not in keys]
        with open(os.path.join(RES, f"{e}{suffix}.csv"), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=keys)
            wr.writeheader()
            for r, _ in rows:
                wr.writerow({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()})
        print(f"{e}: {len(tasks)} tasks, {len(rows)} runs in {time.time() - t0:.0f}s", flush=True)



# ------------------------------------------------------------------------ E11: real drift (CESNET)
CESNET_IPS = [259860, 195100, 171452, 78471, 10396, 3271, 41990, 190, 565727, 381279, 612150, 483796]
CESNET_VICTIMS = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]      # 195100 (index 1) has scan margin 0.79 < 1.3


def run_cesnet_task(task):
    import warnings
    warnings.filterwarnings("ignore")
    import cesnet
    global _CSPACE
    if "_CSPACE" not in globals():
        _CSPACE = cesnet.CesnetSpace(CESNET_IPS)
    streams = [cesnet.CesnetStream(ip, _CSPACE) for ip in CESNET_IPS]
    members = [Member(s.short, s.short) for s in streams]
    world = cesnet.CesnetWorld(streams)
    T = min(s.cycles for s in streams)
    attackers = [TrafficAttacker(a["victim"], "scan", a.get("mode", "boundary"), a.get("p", 0.3), a.get("t0", 30))
                 for a in task.get("attackers", [])]
    victims = sorted({a.victim for a in attackers})
    others = [i for i in range(len(members)) if i not in victims]
    ev = {i: "scan" for i in range(len(members))}
    q = T // 4
    rows = []
    for pname in task["policies"]:
        out = FleetSim(members, streams, world, policy(pname), cycles=T, attackers=attackers, seed=task["seed"]).run(eval_target=ev)
        r = dict(task.get("tags", {}), exp=task["exp"], policy=pname, seed=task["seed"])
        f = out["fpr"]
        for k in range(4):
            r[f"fpr_fleet_q{k + 1}"] = float(np.nanmean(f[k * q:(k + 1) * q][:, others]))
        r["fpr_fleet_all"] = float(np.nanmean(f[:, others]))
        r["fpr_ip10396_q4"] = float(np.nanmean(f[3 * q:, 4])) if 4 in others else float("nan")
        tr = dict(fpr_fleet=np.nanmean(f[:, others], 1).astype(np.float32))
        if victims:
            ctrl = FleetSim(members, streams, world, policy(pname), cycles=T, seed=task["seed"]).run(eval_target=ev)["rec"]
            rec, rc = out["rec"][:, victims], ctrl[:, victims]
            t0 = attackers[0].t0
            lost = (rec < 0.5) & (rc >= 0.5)
            hit = np.where(lost[t0:, 0])[0]
            r["ttc_attr"] = [int(t0 + hit[0]) if len(hit) else None]
            r["compromised_attr"] = float(len(hit) > 0)
            r["rec_gap"] = float(np.nanmean(rc[t0:] - rec[t0:]))
            r["fpr_v_all"] = float(np.nanmean(out["fpr"][:, victims]))
            tr["rec"] = rec[:, 0].astype(np.float32)
        rows.append((r, tr))
    return rows


def run_cesnet(seeds, jobs):
    # The shared space needs an SVD; do it before forking (LAPACK in a forked child can hang on macOS).
    import cesnet
    global _CSPACE
    _CSPACE = cesnet.CesnetSpace(CESNET_IPS)
    tasks = []
    for s in range(SEED0, SEED0 + seeds):
        tasks.append(dict(exp="E11", seed=s, policies=["static", "naive", "auto", "frozen", "kl", "or", "foa"], tags=dict(victim=-1)))
        for v in CESNET_VICTIMS:
            for p in (0.2, 0.4):
                tasks.append(dict(exp="E11", seed=s, attackers=[dict(victim=v, p=p)], policies=["naive", "auto", "frozen", "kl", "or", "foa"],
                                  tags=dict(victim=v, p=p)))
    with mp.get_context("fork").Pool(jobs) as pool:
        rows = [r for rs in pool.imap_unordered(run_cesnet_task, tasks) for r in rs]
    pickle.dump(rows, open(os.path.join(RES, "E11.pkl"), "wb"))
    print(f"E11: {len(tasks)} tasks, {len(rows)} runs", flush=True)


if __name__ == "__main__":
    main()
