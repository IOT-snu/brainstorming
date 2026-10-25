"""
One visual system for every figure in the paper. Colour follows the method, never its rank, and is
the same in every figure (validated categorical palette, fixed order). FOA is the hero series:
thicker line, drawn last.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8985", "#e8e7e3", "#ffffff"
COLOR = {
    "foa": "#2a78d6", "auto": "#eb6834", "frozen": "#1baf7a", "ciota": "#eda100", "or": "#e87ba4",
    "clip": "#008300", "kl": "#6250d6", "naive": "#e34948", "static": "#a3a29c", "toa": "#52514e",
    "foa_same": "#86b6ef", "foa_all": "#1c5cab",
}
NAME = {
    "foa": "FOA (ours)", "auto": "Signature-free, single device", "frozen": "Frozen-reserve screen",
    "ciota": "Same-model consensus (CIoTA style)", "or": "Outlier-ratio gate", "clip": "Per-cycle clipping",
    "kl": "Alarm-rate switch-off", "naive": "Naive self-labelling", "static": "Static (never adapts)",
    "toa": "TOA, oracle signature", "foa_same": "FOA, same-model peers", "foa_all": "FOA, all peers",
}


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-", "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "lines.linewidth": 1.4,
        "legend.frameon": False, "figure.dpi": 200, "savefig.dpi": 300, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlecolor": INK,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def line(ax, x, y, key, label=None, **kw):
    hero = key == "foa"
    kw.setdefault("lw", 2.0 if hero else 1.3)
    kw.setdefault("zorder", 5 if hero else 3)
    return ax.plot(x, y, color=COLOR.get(key, INK2), label=label if label is not None else NAME.get(key, key), **kw)


def shade(ax, a, b, text=None, y=None):
    ax.axvspan(a, b, color="#f3f2ee", zorder=0, lw=0)
    if text:
        ax.text((a + b) / 2, y if y is not None else ax.get_ylim()[1], text, ha="center", va="top", fontsize=6.5, color=MUTED)


def save(fig, path):
    fig.savefig(path + ".pdf")
    fig.savefig(path + ".png", facecolor=SURFACE)
    plt.close(fig)
