"""
Download the N-BaIoT files our experiments need, without keeping the whole archive.

The UCI server does not support partial downloads, so this streams the zip from the start,
reads each member header, keeps the members we want and skips the rest.

Two modes.

  python3 get_nbaiot.py [output_dir]
      Danmini doorbell only (about 200 MB downloaded), used by the single-device experiments:
        benign.csv                              Danmini_Doorbell/benign_traffic.csv
        mirai/{scan,ack,syn,udp,udpplain}.csv   unpacked from Danmini_Doorbell/mirai_attacks.rar

  python3 get_nbaiot.py --fleet [output_dir]
      All nine devices, used by the fleet experiments. Reads the whole archive once and writes
      compact float32 arrays (feature order as in the CSV header, saved to features.txt):
        fleet/<Device>/benign.npy                 every benign row, in capture order
        fleet/<Device>/<family>_<attack>.npy      a seeded random sample of ATTACK_ROWS rows
      family is mirai or gafgyt (gafgyt is the dataset's name for BASHLITE).

Needs bsdtar (macOS has it) or unrar to read the .rar members.
"""
import io, os, shutil, struct, subprocess, sys, urllib.request, zlib
import numpy as np

URL = "https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip"
WANT = {"Danmini_Doorbell/benign_traffic.csv": "benign.csv",
        "Danmini_Doorbell/mirai_attacks.rar": "mirai.rar"}
ATTACK_ROWS = 20000


class Stream:
    def __init__(self, resp):
        self.r, self.buf, self.total = resp, b"", 0

    def read(self, n):
        while len(self.buf) < n:
            chunk = self.r.read(1 << 20)
            if not chunk:
                break
            self.buf += chunk
            self.total += len(chunk)
        out, self.buf = self.buf[:n], self.buf[n:]
        return out


def members(s):
    """Yield (name, write_to) for each local file header; write_to(path) saves it, else it is skipped."""
    while True:
        hdr = s.read(30)
        if len(hdr) < 30 or hdr[:4] != b"PK\x03\x04":
            return
        _, flag, meth, _, _, crc, csize, usize, nlen, elen = struct.unpack("<HHHHHIIIHH", hdr[4:])
        if flag & 8:
            sys.exit("Archive uses data descriptors; this simple reader does not support that.")
        name = s.read(nlen).decode(); s.read(elen)
        saved = []

        def save(dest, meth=meth, crc=crc, csize=csize):
            d = zlib.decompressobj(-15) if meth == 8 else None
            c, left = 0, csize
            with open(dest, "wb") as f:
                while left:
                    blk = s.read(min(left, 1 << 20)); left -= len(blk)
                    data = d.decompress(blk) if d else blk
                    c = zlib.crc32(data, c); f.write(data)
            if c & 0xFFFFFFFF != crc:
                sys.exit("CRC mismatch for " + name)
            saved.append(dest)

        yield name, save
        if not saved:
            left = csize
            while left:
                left -= len(s.read(min(left, 1 << 20)))


def unpack_rar(rar, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for cmd in (["bsdtar", "-xf", rar, "-C", dest_dir], ["unrar", "x", "-o+", rar, dest_dir + "/"]):
        try:
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                return
        except FileNotFoundError:
            continue
    sys.exit("Could not unpack " + rar + ". Install bsdtar or unrar.")


def csv_to_array(path):
    raw = open(path, "rb").read()
    header, body = raw[:raw.index(b"\n")].decode().strip(), raw[raw.index(b"\n") + 1:]
    a = np.array(body.replace(b"\n", b",").decode().rstrip(",").split(","), dtype=np.float64)
    cols = header.split(",")
    return a.reshape(-1, len(cols)).astype(np.float32), cols


def danmini(out_dir):
    need = set(WANT)
    s = Stream(urllib.request.urlopen(URL))
    for name, save in members(s):
        if name in need:
            save(os.path.join(out_dir, WANT[name])); need.discard(name)
            print(f"saved {WANT[name]}  ({s.total/1e6:.0f} MB downloaded so far)", flush=True)
        if not need:
            break
    if need:
        sys.exit("Archive ended before all files were found: " + ", ".join(sorted(need)))
    unpack_rar(os.path.join(out_dir, "mirai.rar"), os.path.join(out_dir, "mirai"))
    print("done:", sorted(os.listdir(os.path.join(out_dir, "mirai"))))


def fleet(out_dir, attempts=12):
    """The server sometimes drops the connection and cannot resume mid-file, so on failure we
    reconnect and skip every member already converted (marked done)."""
    for k in range(attempts):
        try:
            if fleet_pass(out_dir):
                return
        except Exception as e:                      # dropped connection: start the stream again
            print(f"attempt {k + 1} failed ({type(e).__name__}); reconnecting", flush=True)
    sys.exit("gave up after repeated connection failures")


def fleet_pass(out_dir):
    root = os.path.join(out_dir, "fleet")
    tmp = os.path.join(out_dir, "fleet_tmp")
    os.makedirs(root, exist_ok=True); os.makedirs(tmp, exist_ok=True)
    s = Stream(urllib.request.urlopen(URL, timeout=120))
    for name, save in members(s):
        dev, _, base = name.rpartition("/")
        if not dev or base not in ("benign_traffic.csv", "mirai_attacks.rar", "gafgyt_attacks.rar"):
            continue
        dev = dev.split("/")[-1]
        ddir = os.path.join(root, dev); os.makedirs(ddir, exist_ok=True)
        mark = os.path.join(ddir, "." + base + ".done")
        if os.path.exists(mark):
            continue
        rng = np.random.default_rng(zlib.crc32((dev + base).encode()))
        part = os.path.join(tmp, base); save(part)
        if base == "benign_traffic.csv":
            X, cols = csv_to_array(part)
            np.save(os.path.join(ddir, "benign.npy"), X)
            open(os.path.join(root, "features.txt"), "w").write("\n".join(cols) + "\n")
            print(f"{dev}: benign {X.shape}  ({s.total/1e6:.0f} MB downloaded)", flush=True)
        else:
            family = base.split("_")[0]
            udir = os.path.join(tmp, family); shutil.rmtree(udir, ignore_errors=True)
            unpack_rar(part, udir)
            for f in sorted(os.listdir(udir)):
                if f.endswith(".csv"):
                    X, _ = csv_to_array(os.path.join(udir, f))
                    keep = np.sort(rng.choice(len(X), min(ATTACK_ROWS, len(X)), replace=False))
                    np.save(os.path.join(ddir, f"{family}_{f[:-4]}.npy"), X[keep])
                    print(f"{dev}: {family}_{f[:-4]} {len(X)} rows, kept {len(keep)}", flush=True)
            shutil.rmtree(udir, ignore_errors=True)
        os.remove(part)
        open(mark, "w").close()
    shutil.rmtree(tmp, ignore_errors=True)
    print("done:", sorted(os.listdir(root)), flush=True)
    return True


def main():
    args = [a for a in sys.argv[1:] if a != "--fleet"]
    out_dir = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "nbaiot")
    os.makedirs(out_dir, exist_ok=True)
    fleet(out_dir) if "--fleet" in sys.argv else danmini(out_dir)


if __name__ == "__main__":
    main()
