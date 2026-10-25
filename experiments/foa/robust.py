"""
Robust aggregation and budget primitives. Kept tiny and dependency-free so the same arithmetic
can be mirrored line by line in the ESP32 C implementation (firmware/foa_core.c).
"""
import numpy as np


def geometric_median(X, iters=10, eps=1e-9):
    """Weiszfeld iterations from the coordinate-wise median. Breakdown point 1/2: fewer than half
    the inputs, however extreme, cannot move it arbitrarily far (Lopuhaa and Rousseeuw 1991)."""
    X = np.asarray(X, dtype=np.float64)
    if len(X) == 1:
        return X[0].copy()
    y = np.median(X, axis=0)
    for _ in range(iters):
        d = np.linalg.norm(X - y, axis=1)
        w = 1.0 / np.maximum(d, eps)
        y_new = (w[:, None] * X).sum(0) / w.sum()
        if np.linalg.norm(y_new - y) < 1e-12:
            break
        y = y_new
    return y


def aggregate(X, how):
    if how == "gm":
        return geometric_median(X)
    if how == "mean":
        return np.mean(X, axis=0)
    if how == "cwmed":
        return np.median(X, axis=0)
    raise ValueError(how)


def project_ball(v, radius):
    """Closest point to v with norm <= radius."""
    n = np.linalg.norm(v)
    return v if n <= radius else v * (radius / n)


def minsker_constant(alpha):
    """C_alpha from Minsker (2015, Lemma 2.1): if more than (1 - alpha) of the points lie within r
    of z, the geometric median lies within C_alpha * r of z. Valid for alpha < 1/2."""
    if alpha >= 0.5:
        return np.inf
    return (1.0 - alpha) * np.sqrt(1.0 / (1.0 - 2.0 * alpha))
