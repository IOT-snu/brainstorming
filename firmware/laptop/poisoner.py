"""
Testbed attacker, run from the laptop. It only sends UDP packets to one node (it never touches
the node's code or keys), which is exactly the traffic-share attacker of the simulations.

The node's features are damped statistics of packet sizes and inter-packet gaps (foa_features.c),
so the attacker steers them by choosing sizes and timing. Modes:
  boiling   share p of the node's incoming traffic, starting benign-looking and ramping packet size
            and rate toward a flood profile over --ramp seconds (the boundary attacker)
  pulse     the same, on for --on seconds and off for --off seconds
  decoy     loud bursts (max size, high rate) for --duration seconds: trips stop-learning gates
            (the freeze attack); FOA should ignore it
  flood     the actual attack after poisoning, to test whether it is still detected

  python3 poisoner.py --node 192.168.1.51 --mode boiling --share 0.3 --ramp 1800
"""
import argparse, socket, time

NODE_PORT = 5006


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--mode", choices=["boiling", "pulse", "decoy", "flood"], default="boiling")
    ap.add_argument("--share", type=float, default=0.3, help="attacker share of the node's incoming packets")
    ap.add_argument("--base-rate", type=float, default=5.0, help="node's benign packet rate (packets/s)")
    ap.add_argument("--ramp", type=float, default=1800.0, help="seconds to reach the flood profile")
    ap.add_argument("--on", type=float, default=60.0)
    ap.add_argument("--off", type=float, default=60.0)
    ap.add_argument("--duration", type=float, default=3600.0)
    a = ap.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t0 = time.time()
    sent = 0
    while (now := time.time() - t0) < a.duration:
        if a.mode == "decoy" or a.mode == "flood":
            size, rate = 1400, 200.0 if a.mode == "flood" else 50.0
        else:
            f = min(now / a.ramp, 1.0)
            if a.mode == "pulse" and (now % (a.on + a.off)) >= a.on:
                time.sleep(0.05); continue
            size = int(80 + f * (1400 - 80))                      # benign-looking -> flood-sized
            rate = a.base_rate * a.share / (1 - a.share) * (1 + 9 * f)
        sock.sendto(b"\x00" * max(size - 42, 1), (a.node, NODE_PORT))
        sent += 1
        if sent % 500 == 0:
            print(f"t={now:7.1f}s sent={sent} size={size} rate={rate:.1f}/s", flush=True)
        time.sleep(1.0 / rate)


if __name__ == "__main__":
    main()
