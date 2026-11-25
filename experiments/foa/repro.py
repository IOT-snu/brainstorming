"""
Reproduce the testbed collapse: highly repetitive traffic (a periodic device visits a few feature
states) on identical devices. No attacker. Run: python3 repro.py [seed ...]
"""
import sys
import numpy as np
from synth import SynthStream, SynthWorld, D
from fleet import FleetSim, Member, variant, POLICIES


class RepetitiveStream(SynthStream):
    """Benign traffic made of a few repeated states with small jitter, like a node that sends one packet
    type on a timer: k states, unequal weights, identical across devices of one model."""

    def __init__(self, dev, seed=0, k=6, jitter=0.15, **kw):
        super().__init__(dev, seed=seed, **kw)
        r = np.random.default_rng(31 + seed)                       # shared by all devices: same firmware
        self.states = r.normal(size=(k, D)) * r.uniform(0.3, 1.5, size=(k, 1))
        self.w = r.dirichlet(np.ones(k) * 1.5); self.jitter = jitter
        self.cal = self._draw(np.random.default_rng((seed, dev, 1)), 300)

    def _draw(self, r, n):
        return self.center * 0 + self.states[r.choice(len(self.w), n, p=self.w)] + self.jitter * r.normal(size=(n, D))

    def _batch(self, kind, t, prm, n):
        key = (kind, t, prm)
        if key not in self._cache:
            self._cache[key] = self._draw(np.random.default_rng((self.seed, self.dev, t, kind == "te")), 150) + np.asarray(prm)
        return self._cache[key]


def run(pol, seed, n=3, T=200):
    S = [RepetitiveStream(i, seed=seed) for i in range(n)]
    sim = FleetSim([Member("esp", f"v{i}") for i in range(n)], S, SynthWorld(), pol, cycles=T, seed=seed)
    return sim.run()


if __name__ == "__main__":
    seeds = [int(a) for a in sys.argv[1:]] or [0, 1]
    for name, pol in (("static", POLICIES["static"]), ("single device", POLICIES["auto"]), ("FOA", POLICIES["foa"])):
        F, S = [], []
        for s in seeds:
            o = run(pol, s)
            F.append(np.nanmean(o["fpr"][-20:])); S.append(np.nanmean(o["spread"][-1]))
        print(f"{name:14s} false alarms {np.round(F, 3)}   spread ratio {np.round(S, 3)}")
