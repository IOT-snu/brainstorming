"""
Live demo (about one minute): FOA against the other rules, on real N-BaIoT traffic, run in front of you.

Scene 1  Poisoning hidden inside honest drift.
         Nine devices, strong network-wide drift from cycle 40 to 160, and an attacker controlling 30% of
         one camera's (SimpleHome XCS7-1003) traffic, slowly pulling its detector toward Mirai scan
         traffic. Each rule runs on exactly the same traffic.
Scene 2  The freeze attack.
         The attacker only sends loud decoy traffic (5% share) from cycle 40 to 100, then leaves.

Prints a table per scene and writes demo/demo_scene1.png and demo/demo_scene2.png.
Run from the repository root:  python3 demo/live_demo.py
"""
import os, sys, time, warnings
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments", "foa"))
warnings.filterwarnings("ignore")

import experiments as E
from fleet import FleetSim, POLICIES
from data import World
from attacks import TrafficAttacker
import style
import matplotlib.pyplot as plt

SEED, VICTIM = 2, 8
RULES = ["static", "auto", "kl", "frozen", "foa"]


def run(rule, attackers, drift="strong"):
    members = E.fleet_members("F9")
    streams = E.build_streams(members, SEED)
    sim = FleetSim(members, streams, World(E.DRIFT[drift]), POLICIES[rule], cycles=E.CYCLES, seed=SEED, attackers=attackers)
    return sim.run(eval_target={i: s.target_name("scan") for i, s in enumerate(streams)}), streams


def main():
    t0 = time.time()
    print("Loading real N-BaIoT traffic for nine devices ...", flush=True)
    E.space()
    members = E.fleet_members("F9")
    tgt = E.build_streams(members, SEED)[VICTIM].target_name("scan")
    print(f"Victim: {members[VICTIM].short} (camera), target attack: {tgt}\n")
    style.setup()

    # ---------------- scene 1
    print("SCENE 1  poisoning hidden inside strong honest drift (attacker share 30%)")
    print(f"{'rule':34s} {'scan detected at end':>21s} {'victim false alarms':>20s} {'fleet false alarms':>19s}")
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    for r in RULES:
        out, _ = run(r, [TrafficAttacker(VICTIM, tgt, "boundary", 0.3, t0=40)])
        rec, fpr = out["rec"][:, VICTIM], out["fpr"]
        others = [i for i in range(9) if i != VICTIM]
        print(f"{style.NAME[r]:34s} {100 * np.mean(rec[-10:]):20.0f}% {100 * np.mean(fpr[160:, VICTIM]):19.1f}% "
              f"{100 * np.nanmean(fpr[160:, others]):18.1f}%", flush=True)
        style.line(ax[0], np.arange(len(rec)), 100 * rec, r)
        style.line(ax[1], np.arange(len(rec)), 100 * np.nanmean(fpr[:, others], 1), r)
    for a, title, yl in ((ax[0], "Victim: scan attack detected", "%"), (ax[1], "Rest of fleet: false alarms", "%")):
        a.axvspan(40, 160, color="#f3f2ee", zorder=0); a.set_title(title); a.set_xlabel("learning cycle"); a.set_ylabel(yl)
        a.set_ylim(-3, 103)
    ax[0].legend(fontsize=6.5, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "demo_scene1.png"), dpi=160, facecolor="white"); plt.close(fig)

    # ---------------- scene 2
    print("\nSCENE 2  freeze attack: 5% loud decoys from cycle 40 to 100, honest drift 40 to 160")
    print(f"{'rule':34s} {'false alarms at end, no attacker':>33s} {'with attacker':>15s}")
    fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.2))
    for r in ["kl", "foa"]:
        clean, _ = run(r, [])
        dec, _ = run(r, [TrafficAttacker(VICTIM, "mirai_udp", "decoy", 0.05, t0=40, t1=100)])
        c, d = clean["fpr"][:, VICTIM], dec["fpr"][:, VICTIM]
        print(f"{style.NAME[r]:34s} {100 * np.mean(c[-40:]):32.1f}% {100 * np.mean(d[-40:]):14.1f}%", flush=True)
        style.line(ax, np.arange(len(d)), 100 * d, r, label=f"{style.NAME[r]}, attacked")
        ax.plot(np.arange(len(c)), 100 * c, color=style.COLOR[r], lw=0.9, ls=(0, (2, 1.5)), label=f"{style.NAME[r]}, no attacker")
        if r == "foa":
            print(f"{'':34s} FOA trajectory identical with and without decoys: {np.array_equal(c, d)}")
    ax.axvspan(40, 100, color="#fdecec", zorder=0); ax.set_title("Freeze attack on the victim"); ax.set_xlabel("learning cycle")
    ax.set_ylabel("false alarms (%)"); ax.set_ylim(-3, 103); ax.legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "demo_scene2.png"), dpi=160, facecolor="white"); plt.close(fig)
    print(f"\nPlots: demo/demo_scene1.png, demo/demo_scene2.png   ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
