"""
Download only the N-BaIoT files our experiments need, without fetching the whole ~1 GB archive.

The UCI server does not support partial downloads, so this streams the zip from the start,
reads each member header, saves the members we want, skips the rest, and stops as soon as
everything wanted has been saved (about 200 MB for the Danmini doorbell).

Output (default experiments/data/nbaiot):
  benign.csv                    Danmini_Doorbell/benign_traffic.csv
  mirai/{scan,ack,syn,udp,udpplain}.csv   unpacked from Danmini_Doorbell/mirai_attacks.rar
Needs bsdtar (macOS has it) or unrar to unpack the .rar.

Run: python3 get_nbaiot.py [output_dir]
"""
import os, struct, subprocess, sys, urllib.request, zlib

URL = "https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip"
WANT = {"Danmini_Doorbell/benign_traffic.csv": "benign.csv",
        "Danmini_Doorbell/mirai_attacks.rar": "mirai.rar"}


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


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "nbaiot")
    os.makedirs(out_dir, exist_ok=True)
    need = set(WANT)
    s = Stream(urllib.request.urlopen(URL))
    while need:
        hdr = s.read(30)
        if len(hdr) < 30 or hdr[:4] != b"PK\x03\x04":
            sys.exit("Unexpected end of archive before all files were found: " + ", ".join(sorted(need)))
        _, flag, meth, _, _, crc, csize, usize, nlen, elen = struct.unpack("<HHHHHIIIHH", hdr[4:])
        if flag & 8:
            sys.exit("Archive uses data descriptors; this simple reader does not support that.")
        name = s.read(nlen).decode(); s.read(elen)
        if name in need:
            dest = os.path.join(out_dir, WANT[name])
            d = zlib.decompressobj(-15) if meth == 8 else None
            c, left = 0, csize
            with open(dest, "wb") as f:
                while left:
                    blk = s.read(min(left, 1 << 20)); left -= len(blk)
                    data = d.decompress(blk) if d else blk
                    c = zlib.crc32(data, c); f.write(data)
            if c & 0xFFFFFFFF != crc:
                sys.exit("CRC mismatch for " + name)
            need.discard(name)
            print(f"saved {dest}  ({s.total/1e6:.0f} MB downloaded so far)", flush=True)
        else:
            left = csize
            while left:
                left -= len(s.read(min(left, 1 << 20)))
    rar = os.path.join(out_dir, "mirai.rar"); mdir = os.path.join(out_dir, "mirai")
    os.makedirs(mdir, exist_ok=True)
    for cmd in (["bsdtar", "-xf", rar, "-C", mdir], ["unrar", "x", "-o+", rar, mdir + "/"]):
        try:
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                break
        except FileNotFoundError:
            continue
    else:
        sys.exit("Could not unpack mirai.rar. Install bsdtar or unrar and unpack it into " + mdir)
    print("done:", sorted(os.listdir(mdir)))


if __name__ == "__main__":
    main()
