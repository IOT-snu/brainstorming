"""
Testbed collector, run from the laptop.

  python3 collector.py logs/run1 --serial /dev/cu.usbserial-0001 /dev/cu.usbserial-0002 ...
      Saves every node's Serial output (FOA cycle lines, RAW calibration lines, PWR samples from the
      monitor node) to logs/run1/<port>.log with a laptop receive timestamp, and counts the UDP
      telemetry each node sends to port 5005.

  python3 collector.py logs/run1 --summarise
      Turns the logs into the hardware table of the paper: per node, learning-cycle latency
      (propose, FOA step, HMAC sign, verify), peers heard per cycle, bytes gossiped per cycle, and,
      with a monitor log, energy per learning cycle (integrated INA219 power over the cycle window
      minus the idle baseline).

Needs pyserial for live capture (pip install pyserial); summarising needs only numpy.
"""
import argparse, glob, os, socket, threading, time
import numpy as np

FRAME_BYTES = 68


def capture(out_dir, ports, baud):
    import serial
    os.makedirs(out_dir, exist_ok=True)

    def pump(port):
        s = serial.Serial(port, baud, timeout=1)
        with open(os.path.join(out_dir, os.path.basename(port) + ".log"), "a") as f:
            while True:
                line = s.readline().decode(errors="replace").strip()
                if line:
                    f.write(f"{time.time():.6f} {line}\n"); f.flush()

    for p in ports:
        threading.Thread(target=pump, args=(p,), daemon=True).start()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 5005))
    with open(os.path.join(out_dir, "telemetry.log"), "a") as f:
        while True:
            data, addr = udp.recvfrom(2048)
            f.write(f"{time.time():.6f} {addr[0]} {len(data)} {data[:120].decode(errors='replace')}\n"); f.flush()


def summarise(out_dir):
    rows, pwr = {}, []
    for p in glob.glob(os.path.join(out_dir, "*.log")):
        for line in open(p):
            ts, _, rest = line.partition(" ")
            if rest.startswith("FOA,"):
                v = rest.strip().split(",")
                rows.setdefault(v[1], []).append([float(ts)] + [float(x) for x in v[2:]])
            elif rest.startswith("PWR,"):
                v = rest.strip().split(",")
                pwr.append([float(ts), float(v[5])])
    pwr = np.array(pwr) if pwr else None
    print(f"{'node':>4} {'cycles':>6} {'peers':>5} {'propose us':>11} {'step us':>8} {'sign us':>8} {'verify us':>9} {'mJ/cycle':>9}")
    for node, r in sorted(rows.items()):
        r = np.array(r)
        # columns after ts: cycle,n,alarm,n_core,peers,lam,w,R,C,s_ratio,disp,us_propose,us_step,us_mac,us_verify,rejected
        e = float("nan")
        if pwr is not None and len(r) > 2:
            base = np.percentile(pwr[:, 1], 10)
            ej = []
            for k in range(1, len(r)):
                m = (pwr[:, 0] >= r[k - 1, 0]) & (pwr[:, 0] < r[k, 0])
                if m.sum() > 2:
                    ej.append(np.trapz(np.maximum(pwr[m, 1] - base, 0), pwr[m, 0]))
            e = float(np.median(ej)) if ej else e
        print(f"{node:>4} {len(r):6d} {np.mean(r[:, 5]):5.2f} {np.median(r[:, 12]):11.0f} {np.median(r[:, 13]):8.0f}"
              f" {np.median(r[:, 14]):8.0f} {np.median(r[:, 15]):9.0f} {e:9.3f}")
    print(f"gossip per node per cycle: one {FRAME_BYTES}-byte ESP-NOW broadcast")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--serial", nargs="*", default=[])
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--summarise", action="store_true")
    a = ap.parse_args()
    summarise(a.out_dir) if a.summarise else capture(a.out_dir, a.serial, a.baud)


if __name__ == "__main__":
    main()
