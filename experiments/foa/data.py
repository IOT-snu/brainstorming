"""
Real N-BaIoT traffic for a simulated fleet.

Every N-BaIoT row is the 115 Kitsune statistics of one packet. We use, per device:
  - its benign capture, in time order: first 20% calibrates the detector, the rest streams;
  - samples of its real Mirai and BASHLITE (gafgyt) attack traffic, split into a pool the
    poisoner draws from and a held-out pool we measure detection on.

The nine devices were captured separately. The concurrency of the fleet, the honest drift and
the poisoning are ours and are synthesised (stated in the paper). The drift is applied to the raw
Kitsune statistics with physically meaningful transforms (packet rate, packet size overhead,
network jitter), not as an arbitrary vector in feature space.

All devices share one feature space: sign-log transform, fleet-wide standardisation, and a
16-dimensional whitened PCA basis fitted on the pooled calibration traffic of all devices, with each
device centred on itself. A shared basis is what lets devices compare their updates, and sixteen
numbers fit an ESP-NOW frame. Whitening (each component scaled to unit pooled variance) matters:
with the isotropic detector, an unwhitened basis lets the top components drown low-variance attack
directions (static scan recall 0% on four devices with 10 unwhitened components, at least 80% on
every device with 16 whitened ones; see analysis_e0.py).
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("NBAIOT_FLEET", os.path.join(HERE, "..", "data", "nbaiot", "fleet"))

# short name, folder prefix, device kind, vendor, Mirai capture available
DEVICES = [
    ("danmini", "Danmini_Doorbell", "doorbell", "Danmini", True),
    ("ecobee", "Ecobee_Thermostat", "thermostat", "Ecobee", True),
    ("ennio", "Ennio_Doorbell", "doorbell", "Ennio", False),
    ("philips", "Philips_B120N10_Baby_Monitor", "baby monitor", "Philips", True),
    ("prov737", "Provision_PT_737E_Security_Camera", "camera", "Provision", True),
    ("prov838", "Provision_PT_838_Security_Camera", "camera", "Provision", True),
    ("samsung", "Samsung_SNH_1011_N_Webcam", "webcam", "Samsung", False),
    ("sh1002", "SimpleHome_XCS7_1002_WHT_Security_Camera", "camera", "SimpleHome", True),
    ("sh1003", "SimpleHome_XCS7_1003_WHT_Security_Camera", "camera", "SimpleHome", True),
]
SHORT = [d[0] for d in DEVICES]
INFO = {d[0]: dict(folder=d[1], kind=d[2], vendor=d[3], mirai=d[4]) for d in DEVICES}
D_PCA = 16


def signlog(X):
    return np.sign(X) * np.log1p(np.abs(X))


def feature_names():
    return open(os.path.join(DATA, "features.txt")).read().split()


class Groups:
    """Column indices of the Kitsune statistics that each drift mechanism touches."""

    def __init__(self, names):
        idx = lambda f: np.array([i for i, n in enumerate(names) if f(n)], dtype=int)
        jit = lambda n: n.startswith("HH_jit")
        self.weight = idx(lambda n: n.endswith("_weight"))                        # decayed packet counts
        self.size_mean = idx(lambda n: n.endswith("_mean") and not jit(n))        # mean packet size
        self.jit_mean = idx(lambda n: jit(n) and n.endswith("_mean"))             # mean inter-packet gap
        self.jit_var = idx(lambda n: jit(n) and n.endswith("_variance"))
        self.magnitude = idx(lambda n: n.endswith("_magnitude"))                  # sqrt(mu_in^2 + mu_out^2)


def drift_raw(X, G, g=1.0, b=0.0, h=1.0):
    """Physically meaningful drift on raw Kitsune statistics.
    g: packet-rate factor (counts scale by g, inter-packet gaps by 1/g),
    b: bytes of per-packet overhead added in both directions (e.g. a new tunnel or TLS record layer),
    h: network jitter factor on inter-packet gaps (e.g. a route or gateway change)."""
    if g == 1.0 and b == 0.0 and h == 1.0:
        return X
    Y = np.array(X, dtype=np.float64, copy=True)
    if g != 1.0:
        Y[:, G.weight] *= g
    gap = h / g
    if gap != 1.0:
        Y[:, G.jit_mean] *= gap
        Y[:, G.jit_var] *= gap * gap
    if b:
        Y[:, G.size_mean] += b
        Y[:, G.magnitude] += b * np.sqrt(2.0)
    return Y


class Raw:
    """One N-BaIoT device: benign rows in capture order and sampled attack rows."""

    def __init__(self, short):
        folder = INFO[short]["folder"]
        d = os.path.join(DATA, folder)
        if not os.path.exists(os.path.join(d, "benign.npy")):
            raise FileNotFoundError(f"{folder} not under {DATA}; run get_nbaiot.py --fleet")
        self.short = short
        self.benign = np.load(os.path.join(d, "benign.npy"))
        self.attacks = {f[:-4]: np.load(os.path.join(d, f)) for f in sorted(os.listdir(d))
                        if f.endswith(".npy") and f != "benign.npy"}


_RAW = {}


def raw(short):
    if short not in _RAW:
        _RAW[short] = Raw(short)
    return _RAW[short]


def available():
    return [s for s in SHORT if os.path.exists(os.path.join(DATA, INFO[s]["folder"], "benign.npy"))]


class Space:
    """Fleet-shared feature space: sign-log, fleet standardisation, whitened PCA of within-device variation."""

    def __init__(self, devices, cal_frac=0.2, rows_per_device=4000, floor=0.05, seed=0):
        rng = np.random.default_rng(seed)
        T = []
        for s in devices:
            B = raw(s).benign
            cal = B[: int(cal_frac * len(B))]
            cal = cal[rng.choice(len(cal), min(rows_per_device, len(cal)), replace=False)]
            T.append(signlog(cal.astype(np.float64)))
        cent = np.vstack([t - t.mean(0) for t in T])
        self.mean = np.vstack(T).mean(0)
        self.std = np.maximum(cent.std(0), floor)
        Z = cent / self.std
        _, sv, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
        self.W = Vt[:D_PCA].T / (sv[:D_PCA] / np.sqrt(len(Z)))
        self.explained = float(np.sum(sv[:D_PCA] ** 2) / np.sum(sv ** 2))
        self.groups = Groups(feature_names())

    def project(self, X):
        return np.clip(((signlog(np.asarray(X, dtype=np.float64)) - self.mean) / self.std) @ self.W, -1e3, 1e3)


class Stream:
    """One device instance over time. Several instances of one model (different homes) are made
    by giving each its own calibration subsample, its own position in the capture, and its own seed.

    Batches depend only on (instance, cycle, world), never on the policy under test, so every
    policy sees exactly the same traffic and the projections can be cached."""

    def __init__(self, short, space, instance=0, cycles=240, n_train=200, n_test=200, n_eval_atk=150,
                 cal_frac=0.2, window=0.25, cal_sub=1.0, seed=0):
        self.short, self.space, self.instance, self.cycles = short, space, instance, cycles
        self.n_train, self.n_test, self.window = n_train, n_test, window
        R = raw(short)
        rng = np.random.default_rng(1000 * seed + 17 * instance + SHORT.index(short))
        n = len(R.benign); nc = int(cal_frac * n)
        cal = R.benign[:nc]
        if cal_sub < 1.0:
            cal = cal[np.sort(rng.choice(nc, int(cal_sub * nc), replace=False))]
        self.cal_raw = cal
        self.cal = space.project(cal)
        post = R.benign[nc:]
        self.train_raw, self.test_raw = post[0::2], post[1::2]
        self.phase = 0.0 if instance == 0 else float(rng.uniform(0, 1))
        self.seed = int(rng.integers(1 << 30))
        self.attack_names = sorted(R.attacks)
        self.n_eval_atk = n_eval_atk
        self.pool_raw, self.eval_raw = {}, {}
        self._cache = {}

    def _split(self, a):
        """Lazily split one attack type into a poison pool and a disjoint held-out evaluation set."""
        if a not in self.pool_raw:
            X = raw(self.short).attacks[a]
            p = np.random.default_rng(SHORT.index(self.short) * 100 + len(a)).permutation(len(X))
            self.pool_raw[a] = X[p[:2000]]
            self.eval_raw[a] = X[p[len(X) // 2:len(X) // 2 + self.n_eval_atk]]

    def target_name(self, family):
        """'scan' -> mirai_scan when the device has Mirai captures, else gafgyt_scan."""
        if family in self.attack_names:
            return family
        for pre in ("mirai_", "gafgyt_"):
            if pre + family in self.attack_names:
                return pre + family
        raise KeyError(family)

    def _window(self, pool, t, k, salt):
        w = max(k, int(self.window * len(pool)))
        frac = (self.phase + t / max(self.cycles, 1)) % 1.0
        start = int(frac * (len(pool) - w))
        r = np.random.default_rng((self.seed, t, salt))
        return pool[start + r.integers(0, w, k)]

    def train(self, t, prm):
        key = ("tr", t, prm)
        if key not in self._cache:
            X = self._window(self.train_raw, t, self.n_train, 1)
            self._cache[key] = self.space.project(drift_raw(X, self.space.groups, *prm))
        return self._cache[key]

    def test(self, t, prm):
        key = ("te", t, prm)
        if key not in self._cache:
            X = self._window(self.test_raw, t, self.n_test, 2)
            self._cache[key] = self.space.project(drift_raw(X, self.space.groups, *prm))
        return self._cache[key]

    def attack_eval(self, name, prm):
        """Held-out attack traffic as seen through the network path (overhead and jitter apply,
        the benign packet-rate factor does not: the attacker sets its own rate)."""
        key = ("ae", name, prm[1], prm[2])
        if key not in self._cache:
            self._split(name)
            self._cache[key] = self.space.project(drift_raw(self.eval_raw[name], self.space.groups, 1.0, prm[1], prm[2]))
        return self._cache[key]

    def attack_pool(self, name, prm):
        key = ("ap", name, prm[1], prm[2])
        if key not in self._cache:
            self._split(name)
            self._cache[key] = self.space.project(drift_raw(self.pool_raw[name], self.space.groups, 1.0, prm[1], prm[2]))
        return self._cache[key]


def ramp(t, t0, t1):
    if t1 <= t0:
        return float(t >= t0)
    return float(min(max((t - t0) / (t1 - t0), 0.0), 1.0))


class World:
    """Honest drift schedule. `common` applies to every device (shared network change);
    `idio` maps a device index to its own drift (e.g. a firmware update on that device only).
    Each drift is dict(g=final rate factor, b=final overhead bytes, h=final jitter factor, t0, t1)."""

    def __init__(self, common=None, idio=None):
        self.common, self.idio = common, dict(idio or {})

    @staticmethod
    def _one(d, t):
        if not d:
            return 1.0, 0.0, 1.0
        f = ramp(t, d["t0"], d["t1"])
        return 1.0 + (d.get("g", 1.0) - 1.0) * f, d.get("b", 0.0) * f, 1.0 + (d.get("h", 1.0) - 1.0) * f

    def params(self, t, dev):
        g1, b1, h1 = self._one(self.common, t)
        g2, b2, h2 = self._one(self.idio.get(dev), t)
        return (round(g1 * g2, 6), round(b1 + b2, 4), round(h1 * h2, 6))
