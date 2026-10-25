"""
E0: the data and the shared space, before any adaptation.
  - variance kept by the fleet-shared 10-D basis
  - per device: calibration spread, alarm radius, clean false-alarm rate, detection of every attack
    type by the calibrated (static) detector, and attack distance in calibration spreads
  - what the honest drift does: how far it moves each device's benign traffic (in spreads), the
    static detector's false alarms under it, and its angle to the attack directions
Writes results/E0.json and prints a table.
"""
import json, os
import numpy as np

import data
from data import Stream
from detector import Detector
from experiments import DRIFT, IDIO, space, CYCLES

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    sp = space()
    out = dict(explained=sp.explained, devices={})
    print(f"shared basis keeps {sp.explained * 100:.1f}% of within-device variance (10 of 115 dims)")
    for s in data.available():
        st = Stream(s, sp, cycles=CYCLES, seed=0)
        det = Detector(st.cal)
        none = (1.0, 0.0, 1.0)
        te = np.vstack([st.test(t, none) for t in range(0, CYCLES, 4)])
        fpr = float(np.mean(det.score(te) > det.tau))
        atk = {}
        for a in st.attack_names:
            A = st.attack_eval(a, none)
            r = det.score(A)
            atk[a] = dict(recall=float(np.mean(r > det.tau)), median_dist=float(np.median(r)))
        dr = {}
        mu_benign = te.mean(0)
        for name in ("moderate", "strong"):
            d = DRIFT[name]
            prm = (d["g"], d["b"], d["h"])
            X = np.vstack([st.test(t, prm) for t in range(0, CYCLES, 4)])
            shift = X.mean(0) - mu_benign
            cos = {}
            for a in st.attack_names:
                ad = st.attack_eval(a, none).mean(0) - det.mu0
                cos[a] = float(shift @ ad / (np.linalg.norm(shift) * np.linalg.norm(ad) + 1e-12))
            dr[name] = dict(shift_spreads=float(np.linalg.norm(shift) / det.s0), static_fpr=float(np.mean(det.score(X) > det.tau)),
                            cos_to_attacks=cos)
        prm = (IDIO["g"], IDIO["b"], IDIO["h"])
        X = np.vstack([st.test(t, prm) for t in range(0, CYCLES, 4)])
        idio = dict(shift_spreads=float(np.linalg.norm(X.mean(0) - mu_benign) / det.s0), static_fpr=float(np.mean(det.score(X) > det.tau)))
        out["devices"][s] = dict(n_benign=len(data.raw(s).benign), s0=det.s0, tau=det.tau, c=det.c, beta=det.beta, f0=det.f0,
                                 clean_fpr=fpr, attacks=atk, drift=dr, idio=idio)
        if not atk:
            print(f"{s:8s} (no attack files yet)"); continue
        worst = min(atk.items(), key=lambda kv: kv[1]["median_dist"])
        print(f"{s:8s} n={len(data.raw(s).benign):6d} tau={det.tau:4.2f} clean FPR={fpr*100:4.1f}%  min recall={min(v['recall'] for v in atk.values())*100:5.1f}%"
              f"  closest attack {worst[0]} at {worst[1]['median_dist']:.1f} spreads | strong drift moves {dr['strong']['shift_spreads']:.1f} spreads,"
              f" static FPR {dr['strong']['static_fpr']*100:.0f}% | idio {idio['shift_spreads']:.1f} spreads, FPR {idio['static_fpr']*100:.0f}%")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "results", "E0.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
