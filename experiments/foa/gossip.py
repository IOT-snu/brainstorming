"""
Authenticated gossip of proposed updates, byte for byte what an ESP32 would put in an ESP-NOW frame.

Frame (little-endian, 92 bytes, well under ESP-NOW's 250-byte payload):
    u8  version
    u8  sender id
    u16 learning points used (n_core)
    u32 cycle number                      (freshness: replays of old frames are rejected)
    f32 dmu[16]                           proposed centre shift in the shared space
    f32 dls                               proposed change of log spread
    u8  tag[16]                           HMAC-SHA256 over everything above, truncated to 128 bits

Each device has its own provisioned key; receivers hold the keyring of their peer group.
"""
import hashlib, hmac, struct
import numpy as np

VERSION = 1
HEAD = struct.Struct("<BBHI16ff")
TAG = 16
FRAME_BYTES = HEAD.size + TAG


def pack(sender, cycle, dmu, dls, n_core, key):
    body = HEAD.pack(VERSION, sender, min(int(n_core), 65535), cycle, *np.asarray(dmu, dtype=np.float32).tolist(), float(dls))
    return body + hmac.new(key, body, hashlib.sha256).digest()[:TAG]


def verify(frame, keyring, cycle):
    """Returns (sender, dmu, dls, n_core) or (None, reason)."""
    if len(frame) != FRAME_BYTES:
        return None, "length"
    body, tag = frame[:-TAG], frame[-TAG:]
    f = HEAD.unpack(body)
    if f[0] != VERSION:
        return None, "version"
    sender, n_core, cyc = f[1], f[2], f[3]
    key = keyring.get(sender)
    if key is None:
        return None, "unknown sender"
    if not hmac.compare_digest(hmac.new(key, body, hashlib.sha256).digest()[:TAG], tag):
        return None, "bad tag"
    if cyc != cycle:
        return None, "stale"
    return (sender, np.array(f[4:20], dtype=np.float64), float(f[20]), n_core), "ok"


def keys(n, seed=0):
    rng = np.random.default_rng(seed)
    return {i: rng.integers(0, 256, 32, dtype=np.uint8).tobytes() for i in range(n)}
