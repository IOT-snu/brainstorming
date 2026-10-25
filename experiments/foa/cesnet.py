"""
Real drift: CESNET-TimeSeries24 (Koumar et al., Scientific Data 2025), 40 weeks of traffic statistics
per IP address from a national research network, with real calendar drift (semester, holidays).

A fleet is the most active IP addresses of one institution: they sit behind the same network, so they
share its common-mode drift, while each has its own behaviour. One learning cycle is one day; its
batch is that day's 10-minute aggregates (up to 144 points). Even slots train, odd slots test.
Nothing about the drift is injected here. The poisoner and the attack class are modelled: the attack
profile is the IP's own traffic turned into a scanner (many destinations and ports, short flows,
small packets), because CESNET-TimeSeries24 has no attack labels.

Same interface as data.Stream, so fleet.FleetSim runs on it unchanged.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CESNET_DIR", os.path.join(HERE, "..", "data", "cesnet"))
SAMPLE = os.path.join(ROOT, "ip_addresses_sample", "agg_10_minutes")
FEATS = ["n_flows", "n_packets", "n_bytes", "n_dest_asn", "n_dest_ports", "n_dest_ip",
         "tcp_udp_ratio_packets", "tcp_udp_ratio_bytes", "dir_ratio_packets", "dir_ratio_bytes", "avg_duration", "avg_ttl"]
SLOTS = 144                      # 10-minute slots per day
CAL_DAYS = 28


def signlog(X):
    return np.sign(X) * np.log1p(np.abs(X))


def load_ip(ip):
    path = os.path.join(SAMPLE, f"{ip}.csv")
    head = open(path).readline().strip().split(",")
    A = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    cols = [head.index(f) for f in FEATS]
    return A[:, 0].astype(int), A[:, cols]


def scanner(X):
    """The same hours, but behaving like a scanner: many destinations, ports and short flows."""
    Y = np.array(X, dtype=float, copy=True)
    f = {k: i for i, k in enumerate(FEATS)}
    Y[:, f["n_flows"]] *= 20
    Y[:, f["n_packets"]] *= 4
    Y[:, f["n_bytes"]] *= 1.5
    Y[:, f["n_dest_ip"]] = Y[:, f["n_dest_ip"]] * 30 + 50
    Y[:, f["n_dest_ports"]] = Y[:, f["n_dest_ports"]] * 10 + 20
    Y[:, f["n_dest_asn"]] = Y[:, f["n_dest_asn"]] * 5 + 5
    Y[:, f["avg_duration"]] *= 0.05
    Y[:, f["dir_ratio_packets"]] = 0.95
    return Y


def pick_fleet(n=9, min_days=250):
    """The institution with the most IPs active on at least min_days days; its n most active IPs."""
    import csv
    rel = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "ids_relationship.csv"))):
        rel[int(r["id_ip"])] = int(r["id_institution"])
    activity = {}
    for fn in os.listdir(SAMPLE):
        ip = int(fn[:-4])
        t, _ = load_ip(ip)
        days = np.bincount(t // SLOTS)
        activity[ip] = int(np.sum(days >= 72))         # days with at least half the slots active
    by_inst = {}
    for ip, a in activity.items():
        if a >= min_days and ip in rel:
            by_inst.setdefault(rel[ip], []).append((a, ip))
    inst = max(by_inst, key=lambda k: len(by_inst[k]))
    ips = [ip for _, ip in sorted(by_inst[inst], reverse=True)[:n]]
    return inst, ips, {k: len(v) for k, v in by_inst.items()}


class CesnetSpace:
    """Fleet-shared space as for N-BaIoT: sign-log, within-IP standardisation, whitened PCA. All 12
    components are kept; the projection is padded with zero columns to the 16 numbers of the gossip
    frame (constant coordinates, so distances are unchanged)."""

    def __init__(self, ips, D=16, floor=0.05):
        T = []
        for ip in ips:
            t, X = load_ip(ip)
            T.append(signlog(X[t < CAL_DAYS * SLOTS]))
        cent = np.vstack([x - x.mean(0) for x in T])
        self.mean = np.vstack(T).mean(0)
        self.std = np.maximum(cent.std(0), floor)
        Z = cent / self.std
        _, sv, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
        k = min(D, len(sv))
        self.W = np.zeros((Z.shape[1], D))
        self.W[:, :k] = Vt[:k].T / (sv[:k] / np.sqrt(len(Z)))
        self.explained = float(np.sum(sv[:k] ** 2) / np.sum(sv ** 2))

    def project(self, X):
        return np.clip(((signlog(np.asarray(X, dtype=float)) - self.mean) / self.std) @ self.W, -1e3, 1e3)


class CesnetStream:
    def __init__(self, ip, space, cycles=None, seed=0):
        self.short, self.instance, self.ip = f"ip{ip}", 0, ip
        t, X = load_ip(ip)
        self.t, self.X, self.space = t, X, space
        day = t // SLOTS
        self.days = int(day.max()) + 1
        self.cycles = cycles or self.days - CAL_DAYS
        self.cal = space.project(X[day < CAL_DAYS])
        self.by_day = {}
        for d in range(CAL_DAYS, self.days):
            idx = np.where(day == d)[0]
            self.by_day[d - CAL_DAYS] = (idx[t[idx] % 2 == 0], idx[t[idx] % 2 == 1])
        self.attack_names = ["scan"]
        self._cache = {}

    def _get(self, kind, t):
        key = (kind, t)
        if key not in self._cache:
            tr, te = self.by_day.get(t, (np.array([], int), np.array([], int)))
            idx = tr if kind == "tr" else te
            X = self.X[idx]
            if kind in ("ae", "ap"):
                X = scanner(self.X[np.concatenate([tr, te])])
            self._cache[key] = self.space.project(X) if len(X) else np.zeros((0, self.space.W.shape[1]))
        return self._cache[key]

    def train(self, t, prm):
        return self._get("tr", t)

    def test(self, t, prm):
        return self._get("te", t)

    def attack_eval(self, name, prm):
        return self._get("ae", self._t_now)

    def attack_pool(self, name, prm):
        return self._get("ap", self._t_now)

    def target_name(self, family):
        return "scan"


class CesnetWorld:
    """Real drift is in the data. params() only tells each stream which day it is, so the scanner
    profile follows the IP's own current behaviour."""

    def __init__(self, streams):
        self.streams = streams

    def params(self, t, dev):
        self.streams[dev]._t_now = t
        return (1.0, 0.0, 1.0)
