"""
Controlled synthetic fleet with the same interface as data.Stream / data.World. Used for unit tests
and for checking the theory where the true drift and attack geometry must be known exactly.

Each device: benign ~ N(c_i + shift_i(t), I) in D dimensions, attack cluster at c_i + dist * u_i.
World parameters are shift vectors (common plus per-device), passed around as rounded tuples so
that batches can be cached exactly like the real streams.
"""
import numpy as np

D = 16


class SynthStream:
    def __init__(self, dev, n_train=200, n_test=200, seed=0, attack_dist=10.5, attack_dir=None, n_cal=5000, model=None):
        rng = np.random.default_rng(1000 * seed + dev)
        self.dev, self.seed = dev, seed
        self.short = model or f"syn{dev}"
        self.center = np.random.default_rng(500 + (dev if model is None else hash(model) % 997)).normal(size=D) * 3.0
        u = np.asarray(attack_dir, dtype=float) if attack_dir is not None else np.random.default_rng(900 + dev).normal(size=D)
        self.u = u / np.linalg.norm(u)
        self.attack_dist = attack_dist
        self.cal = self.center + np.random.default_rng(77 + dev + 1000 * seed).normal(size=(n_cal, D))
        self.n_train, self.n_test = n_train, n_test
        self.attack_names = ["atk"]
        self._cache = {}

    def _batch(self, kind, t, prm, k):
        key = (kind, t, prm)
        if key not in self._cache:
            r = np.random.default_rng((self.seed, self.dev, t, kind == "te"))
            self._cache[key] = self.center + np.asarray(prm) + r.normal(size=(k, D))
        return self._cache[key]

    def train(self, t, prm):
        return self._batch("tr", t, prm, self.n_train)

    def test(self, t, prm):
        return self._batch("te", t, prm, self.n_test)

    def attack_eval(self, name, prm):
        key = ("ae",)
        if key not in self._cache:
            r = np.random.default_rng(4242 + self.dev)
            self._cache[key] = self.center + self.attack_dist * self.u + 0.6 * r.normal(size=(300, D))
        return self._cache[key]

    def attack_pool(self, name, prm):
        key = ("ap",)
        if key not in self._cache:
            r = np.random.default_rng(4343 + self.dev)
            self._cache[key] = self.center + self.attack_dist * self.u + 0.6 * r.normal(size=(2000, D))
        return self._cache[key]


class SynthWorld:
    """common: (vector, t0, t1) ramped linearly; idio: {dev: (vector, t0, t1)}."""

    def __init__(self, common=None, idio=None):
        self.common, self.idio = common, dict(idio or {})

    @staticmethod
    def _one(d, t):
        if d is None:
            return np.zeros(D)
        v, t0, t1 = d
        f = min(max((t - t0) / max(t1 - t0, 1e-9), 0.0), 1.0)
        return np.asarray(v, dtype=float) * f

    def params(self, t, dev):
        return tuple(np.round(self._one(self.common, t) + self._one(self.idio.get(dev), t), 6))
