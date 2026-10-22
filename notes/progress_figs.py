"""System and wiring diagrams for the progress report. Run: python3 progress_figs.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
from matplotlib.path import Path
from matplotlib.patches import PathPatch

INK, BLUE, GRAY, RED, GREEN, ORANGE = "#1D1D1F", "#0071E3", "#86868B", "#D70015", "#248A3D", "#FF9F0A"
CARD, EDGE = "#F5F5F7", "#C7C7CC"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 11})


def box(ax, x, y, w, h, title, lines=(), fill=CARD, edge=EDGE, tcolor=INK, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fill, ec=edge, lw=lw))
    ax.text(x + 0.18, y + h - 0.28, title, fontsize=11.5, fontweight="bold", color=tcolor, va="top")
    for i, l in enumerate(lines):
        ax.text(x + 0.18, y + h - 0.7 - i * 0.34, l, fontsize=9.5, color=GRAY, va="top")


def wire(ax, pts, color=INK, lw=2, ls="-", z=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=z)


def dot(ax, x, y, color=INK):
    ax.add_patch(Circle((x, y), 0.07, fc=color, ec=color, zorder=5))


# ------------------------------------------------------------------ 1. System diagram
fig, ax = plt.subplots(figsize=(12.4, 6.8))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 6.8); ax.axis("off")
ax.text(0.2, 6.5, "Fleet of vulnerability-diverse ESP32 detectors", fontsize=14, fontweight="bold", color=INK, va="center")
ax.text(0.2, 6.1, "Every node runs its own detector and learns from its own traffic. Peers share only a small update.", fontsize=10, color=GRAY, va="center")

box(ax, 0.2, 2.6, 3.0, 2.8, "Laptop", ["MQTT broker (Mosquitto)", "Poisoner script (attacker)", "Experiment control, logger", "N-BaIoT replay feeder"])
box(ax, 3.9, 3.2, 2.0, 1.4, "Wi-Fi router", ["one fixed channel"])

nodes = [(7.6, 4.85, "Node A", "firmware profile 1"), (7.6, 3.4, "Node B", "firmware profile 2"),
         (7.6, 1.95, "Node C", "firmware profile 3"), (7.6, 0.5, "Node D", "firmware profile 1 (spare)")]
for x, y, t_, s_ in nodes:
    box(ax, x, y, 2.9, 1.15, f"ESP32 {t_}", [s_ + " + sensor"], fill="#FFFFFF", edge=BLUE, lw=1.6)

# Wi-Fi: router -> vertical bus -> each node
BUS = 6.7
wire(ax, [(3.2, 3.9), (3.9, 3.9)], color=GRAY, lw=1.8)
wire(ax, [(5.9, 3.9), (BUS, 3.9)], color=GRAY, lw=1.8)
wire(ax, [(BUS, 5.2), (BUS, 0.85)], color=GRAY, lw=1.8)
for x, y, t_, s_ in nodes:
    wire(ax, [(BUS, y + 0.35), (x, y + 0.35)], color=GRAY, lw=1.8)
    dot(ax, BUS, y + 0.35, GRAY)

# ESP-NOW gossip: every node joins one shared dashed line on the right
GX = 11.1
wire(ax, [(GX, 1.08), (GX, 5.43)], color=BLUE, lw=2.0, ls=(0, (4, 2)))
for x, y, t_, s_ in nodes:
    wire(ax, [(x + 2.9, y + 0.58), (GX, y + 0.58)], color=BLUE, lw=2.0, ls=(0, (4, 2)))
    dot(ax, GX, y + 0.58, BLUE)
ax.text(GX + 0.2, 3.5, "ESP-NOW\ngossip\n(72 bytes)", fontsize=9.5, color=BLUE, va="center")

# attacker path into Node A only
wire(ax, [(3.2, 5.05), (BUS - 0.4, 5.05), (BUS - 0.4, 5.75), (7.6, 5.75)], color=RED, lw=2.2, ls=(0, (5, 3)))
ax.annotate("", xy=(7.6, 5.75), xytext=(7.2, 5.75), arrowprops=dict(arrowstyle="-|>", color=RED, lw=2.2))
ax.text(3.35, 5.15, "poison traffic aimed at Node A", fontsize=10, color=RED, va="bottom")

# power monitor
box(ax, 3.4, 0.5, 2.9, 1.5, "Power monitor", ["ESP32 + INA219 on Node A", "serial cable to laptop"], fill="#FFFFFF", edge=ORANGE, lw=1.6)
wire(ax, [(1.7, 2.6), (1.7, 1.25), (3.4, 1.25)], color=ORANGE, lw=2.0)

# legend
y0 = 0.1
for i, (col, ls_, lab) in enumerate([(GRAY, "-", "Wi-Fi telemetry"), (BLUE, "--", "ESP-NOW peer gossip"), (RED, "--", "attacker traffic"), (ORANGE, "-", "energy monitoring (serial)")]):
    x0 = 0.2 + i * 2.6
    wire(ax, [(x0, y0), (x0 + 0.5, y0)], color=col, lw=2.2, ls=(0, (4, 2)) if ls_ == "--" else "-")
    ax.text(x0 + 0.6, y0, lab, fontsize=9.5, color=INK, va="center")
fig.tight_layout()
fig.savefig("fig_system.png", dpi=170, facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ 2. Wiring diagram
fig, ax = plt.subplots(figsize=(11.5, 6.8))
ax.set_xlim(0, 11.5); ax.set_ylim(-1.9, 6.6); ax.axis("off")
ax.text(0.2, 6.3, "Measuring one node's energy with an INA219 current sensor", fontsize=14, fontweight="bold", color=INK)
ax.text(0.2, 5.9, "The sensor sits in series with the node's 5 V supply. A second ESP32 reads it over I2C.", fontsize=10, color=GRAY)

box(ax, 0.2, 4.0, 2.1, 1.5, "5 V supply", ["USB breakout", "or bench supply"])
box(ax, 4.6, 2.0, 2.6, 3.5, "INA219 module", [])
ax.add_patch(Rectangle((5.1, 3.0), 0.3, 1.6, fc="#FFFFFF", ec=INK, lw=1.4)); ax.text(5.55, 3.8, "0.1 ohm\nshunt", fontsize=9, color=GRAY, va="center")
box(ax, 1.0, 1.2, 2.6, 1.9, "Node under test", ["ESP32, powered only", "through the sensor"])
box(ax, 8.9, 2.0, 2.4, 3.5, "Monitor ESP32", [])

def pin(x, y, label, side, color=INK, dx=0.12):
    ax.add_patch(Circle((x, y), 0.07, fc=color, ec=color, zorder=5))
    ax.text(x + (dx if side == "r" else -dx), y, label, fontsize=9.5, color=INK, va="center", ha="left" if side == "r" else "right")

Y1, Y2, Y3, Y4 = 4.55, 3.95, 3.35, 2.4
pin(2.3, Y1, "+5V", "l", RED)
pin(4.6, Y1, "VIN+", "r", RED)
pin(4.6, 3.0, "VIN-", "r", RED)
pin(3.6, 2.45, "VIN (5V)", "l", RED)
pin(7.2, Y1, "VCC", "l", ORANGE)
pin(7.2, Y2, "SDA", "l", BLUE)
pin(7.2, Y3, "SCL", "l", GREEN)
pin(7.2, Y4, "GND", "l", INK)
pin(8.9, Y1, "3V3", "r", ORANGE)
pin(8.9, Y2, "GPIO21 (SDA)", "r", BLUE)
pin(8.9, Y3, "GPIO22 (SCL)", "r", GREEN)
pin(8.9, Y4, "GND", "r", INK)
pin(0.5, 4.0, "GND", "r", INK, dx=0.15)
pin(2.0, 1.2, "GND", "r", INK)

wire(ax, [(2.3, Y1), (4.6, Y1)], RED, 2.4)
wire(ax, [(4.6, 3.0), (4.1, 3.0), (4.1, 2.45), (3.6, 2.45)], RED, 2.4)
wire(ax, [(7.2, Y1), (8.9, Y1)], ORANGE, 2.0)
wire(ax, [(7.2, Y2), (8.9, Y2)], BLUE, 2.0)
wire(ax, [(7.2, Y3), (8.9, Y3)], GREEN, 2.0)
RAIL = 0.4
wire(ax, [(0.5, 4.0), (0.5, RAIL), (8.8, RAIL)], INK, 2.2)
wire(ax, [(2.0, 1.2), (2.0, RAIL)], INK, 2.2); dot(ax, 2.0, RAIL)
wire(ax, [(7.2, Y4), (7.7, Y4), (7.7, RAIL)], INK, 2.2); dot(ax, 7.7, RAIL)
wire(ax, [(8.9, Y4), (8.4, Y4), (8.4, RAIL)], INK, 2.2); dot(ax, 8.4, RAIL)
ax.text(0.7, RAIL - 0.15, "common ground rail (all grounds joined)", fontsize=9.5, color=INK, va="top")

ax.annotate("", xy=(10.1, 1.45), xytext=(10.1, 2.0), arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.8))
ax.text(10.1, 1.35, "USB to laptop\n(serial log)", fontsize=9.5, color=GRAY, ha="center", va="top")

ax.text(0.2, -0.6,
        "Build notes (check before wiring):\n"
        "1. Add 4.7 kohm pull-ups from SDA and SCL to 3V3 if the INA219 module has none.\n"
        "2. Flash the node first, then power it only through this path. Do not also plug in its USB at the same time.\n"
        "3. INA219 samples about every 0.5 ms, so measure energy over many cycles and average. Do not trust single short bursts.",
        fontsize=9.5, color=INK, va="top", linespacing=1.5)
fig.tight_layout()
fig.savefig("fig_circuit.png", dpi=170, facecolor="white")
plt.close(fig)
print("wrote fig_system.png fig_circuit.png")
