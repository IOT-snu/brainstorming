"""
What-if simulation of the three-board testbed: three identical devices with repetitive traffic (repro.py),
240 cycles (about 31 min), connected (FOA) or isolated, with and without the coverage floor, with no attacker
or a boundary poisoner (share 0.3, from cycle 40) on node 1. 20 seeds. Synthetic traffic, not board data.
Run: python3 testbed_sim.py -> results/testbed_sim.txt
"""
import warnings
import numpy as np
from repro import RepetitiveStream
from synth import SynthWorld
from fleet import FleetSim, Member, POLICIES, variant
from attacks import TrafficAttacker

warnings.filterwarnings("ignore")
RULES = [("connected, old firmware", POLICIES["foa"]), ("connected, with floor", variant("foa", "f", s_floor=1.0)),
         ("isolated, old firmware", POLICIES["auto"]), ("isolated, with floor", variant("auto", "af", s_floor=1.0))]
lines = [f"{'condition':26s} | no attack: false alarms mean (worst), spread end | poisoned: detected before -> end, compromised runs"]
for name, pol in RULES:
    fa, sp, r0, r1, comp = [], [], [], [], []
    for seed in range(8, 28):
        for att in (False, True):
            S = [RepetitiveStream(i, seed=seed) for i in range(3)]
            A = [TrafficAttacker(1, "atk", "boundary", 0.3, t0=40)] if att else []
            o = FleetSim([Member("esp", f"v{i}") for i in range(3)], S, SynthWorld(), pol, cycles=240, attackers=A, seed=seed).run(eval_target={i: "atk" for i in range(3)})
            if att:
                r = o["rec"][:, 1]; r0.append(r[35:40].mean()); r1.append(r[-10:].mean()); comp.append(r[35:40].mean() >= 0.5 and r[-10:].mean() < 0.5)
            else:
                fa.append(np.nanmean(o["fpr"][-20:])); sp.append(np.nanmean(o["spread"][-1]))
    lines.append(f"{name:26s} | {100*np.mean(fa):5.1f}% ({100*max(fa):5.1f}%), {np.mean(sp):.2f} | {100*np.mean(r0):5.1f}% -> {100*np.mean(r1):5.1f}%, {sum(comp)}/20")
open("results/testbed_sim.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
