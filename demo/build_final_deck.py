"""
Builds G04_FOA_Final.pptx (and PNG previews of every slide). Run: python3 demo/build_final_deck.py [preview_dir]
Native PowerPoint text, shapes and charts, so everything stays editable. Numbers come from the paper and the logs.
"""
import os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PREV = sys.argv[1] if len(sys.argv) > 1 else None
FONT = "Arial"
INK, GREY, SOFT, LINE = "1D1D1F", "6E6E73", "F5F5F7", "D2D2D7"
BLUE, RED, WHITE, PALE = "0071E3", "D70015", "FFFFFF", "C7C7CC"
rgb = lambda h: RGBColor.from_string(h)
F = "/System/Library/Fonts/Supplemental/"
PX = 120                                                    # preview pixels per inch

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
previews = []


class Slide:
    def __init__(self, notes, bg=WHITE):
        self.s = prs.slides.add_slide(prs.slide_layouts[6])
        self.s.background.fill.solid(); self.s.background.fill.fore_color.rgb = rgb(bg)
        self.s.notes_slide.notes_text_frame.text = notes
        self.im = Image.new("RGB", (1600, 900), "#" + bg); self.d = ImageDraw.Draw(self.im)
        previews.append(self.im)

    def text(self, x, y, w, h, t, size=18, color=INK, bold=False, align="l", anchor="t", spacing=1.12, track=None):
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame; tf.word_wrap = True
        for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(tf, m, 0)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        if track is None:
            track = -0.018 if size >= 30 else 0.0
        for i, line in enumerate(t.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.line_spacing = spacing
            r = p.add_run(); r.text = line
            f = r.font; f.name = FONT; f.size = Pt(size); f.bold = bold; f.color.rgb = rgb(color)
            r._r.get_or_add_rPr().set("spc", str(int(track * size * 100)))
        # preview
        font = ImageFont.truetype(F + ("Arial Bold.ttf" if bold else "Arial.ttf"), int(size * PX / 72))
        lines = []
        for para in t.split("\n"):
            cur = ""
            for word in para.split(" "):
                nxt = (cur + " " + word).strip()
                if self.d.textlength(nxt, font=font) > w * PX and cur:
                    lines.append(cur); cur = word
                else:
                    cur = nxt
            lines.append(cur)
        lh = size * PX / 72 * 1.17 * spacing
        total = lh * len(lines)
        if total > h * PX + lh * 0.35:
            print("OVERFLOW", len(previews), t[:50])
        yy = y * PX + {"t": 0, "m": (h * PX - total) / 2, "b": h * PX - total}[anchor]
        for ln in lines:
            lw = self.d.textlength(ln, font=font)
            xx = x * PX + {"l": 0, "c": (w * PX - lw) / 2, "r": w * PX - lw}[align]
            self.d.text((xx, yy), ln, font=font, fill="#" + color); yy += lh

    def box(self, x, y, w, h, fill=SOFT, line=None, radius=0.12):
        sh = self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        if radius:
            sh.adjustments[0] = min(0.5, radius / min(w, h))
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill); sh.shadow.inherit = False
        if line:
            sh.line.color.rgb = rgb(line); sh.line.width = Pt(1.25)
        else:
            sh.line.fill.background()
        self.d.rounded_rectangle([x * PX, y * PX, (x + w) * PX, (y + h) * PX], radius * PX, fill="#" + fill, outline="#" + line if line else None, width=2)

    def line(self, x1, y1, x2, y2, color=LINE, width=1.25, arrow=False):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = rgb(color); c.line.width = Pt(width)
        if arrow:
            from pptx.oxml.ns import qn
            ln = c.line._get_or_add_ln(); e = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}); ln.append(e)
        self.d.line([x1 * PX, y1 * PX, x2 * PX, y2 * PX], fill="#" + color, width=max(1, int(width * 1.6)))
        if arrow:
            import math
            a = math.atan2(y2 - y1, x2 - x1)
            self.d.polygon([(x2 * PX, y2 * PX)] + [(x2 * PX - 13 * math.cos(a + s), y2 * PX - 13 * math.sin(a + s)) for s in (0.45, -0.45)], fill="#" + color)

    def dot(self, cx, cy, r, fill=BLUE, line=None):
        sh = self.s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - r), Inches(cy - r), Inches(2 * r), Inches(2 * r))
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill); sh.shadow.inherit = False
        if line:
            sh.line.color.rgb = rgb(line); sh.line.width = Pt(1.5)
        else:
            sh.line.fill.background()
        self.d.ellipse([(cx - r) * PX, (cy - r) * PX, (cx + r) * PX, (cy + r) * PX], fill="#" + fill, outline="#" + line if line else None, width=2)

    def head(self, title, sub=None):
        self.text(0.9, 0.62, 11.6, 0.8, title, 34, bold=True)
        if sub:
            self.text(0.9, 1.42, 11.4, 0.5, sub, 17, GREY)

    def bars(self, x, y, w, h, cats, vals, hi, fmt='0.0"%"', top=None):
        cd = CategoryChartData(); cd.categories = cats; cd.add_series("value", vals)
        gf = self.s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
        ch = gf.chart; ch.has_legend = False; ch.has_title = False
        ch.font.name = FONT; ch.font.size = Pt(13); ch.font.color.rgb = rgb(GREY)
        pl = ch.plots[0]; pl.gap_width = 55; pl.has_data_labels = True
        dl = pl.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
        dl.font.size = Pt(18); dl.font.bold = True; dl.font.color.rgb = rgb(INK); dl.font.name = FONT
        va = ch.value_axis; va.visible = False; va.has_major_gridlines = False; va.minimum_scale = 0; va.maximum_scale = top or max(vals) * 1.18
        ca = ch.category_axis; ca.format.line.color.rgb = rgb(LINE); ca.tick_labels.font.size = Pt(13)
        for i in range(len(vals)):
            pt = pl.series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(BLUE if i in hi else PALE)
        base, m = y + h - 0.65, top or max(vals) * 1.18
        bw = w / len(vals)
        for i, v in enumerate(vals):
            bh = (h - 0.9) * v / m
            self.d.rectangle([(x + i * bw + bw * 0.22) * PX, (base - bh) * PX, (x + i * bw + bw * 0.78) * PX, base * PX], fill="#" + (BLUE if i in hi else PALE))
            f = ImageFont.truetype(F + "Arial Bold.ttf", 28)
            self.d.text(((x + i * bw + bw / 2) * PX, (base - bh) * PX - 18), f"{v:g}%", font=f, fill="#" + INK, anchor="mm")
            f2 = ImageFont.truetype(F + "Arial.ttf", 20)
            self.d.multiline_text(((x + i * bw + bw / 2) * PX, base * PX + 30), cats[i], font=f2, fill="#" + GREY, anchor="mm", align="center")


def spread_series():
    out = []
    for path in ("experiments/hardware/IDLE4/COM10.log", "experiments/hardware/nowifi/COM10.log"):
        rows = []
        for l in open(os.path.join(ROOT, path), errors="replace"):
            ts, _, r = l.partition(" "); v = r.strip().split(",")
            if v[0] == "FOA" and len(v) == 18:
                rows.append((float(ts), float(v[11])))
        out.append([((t - rows[0][0]) / 60, 100 * s) for t, s in rows if (t - rows[0][0]) / 60 <= 20.2])
    return out


# 1 ---------------------------------------------------------------- title
s = Slide("Good afternoon. We are Group G-04. Our project is an IoT intrusion detector that keeps learning as normal traffic changes, while staying hard to poison. We will show the idea, the guarantees, the results on real IoT traffic, and the system running on real boards.")
s.text(0.9, 1.85, 11.5, 2.0, "Learning from the\nneighbours", 60, bold=True, spacing=1.0)
s.text(0.9, 4.15, 9.5, 0.9, "Poison-resilient intrusion detection on drifting IoT devices", 22, GREY)
s.text(0.9, 6.15, 8, 0.35, "Rishit Kamboj and Farhan Naik", 15, INK, True)
s.text(0.9, 6.5, 9, 0.35, "CSD457 Internet of Things  ·  Group G-04", 13, GREY)

# 2 ---------------------------------------------------------------- problem
s = Slide("A detector learns what normal traffic looks like. Normal changes, so it has to keep learning. If it trusts itself, an attacker can walk it slowly toward the attack. If it stops learning when things look suspicious, the attacker can trigger that stop and leave, and it floods with false alarms. If it never learns, ordinary change sets off alarms everywhere. Every current option fails one of these.")
s.head("A detector that learns can be fooled", "Normal traffic keeps changing, so standing still is not an option either.")
for x, t, b in ((0.9, "Trust yourself", "An attacker feeds slightly unusual traffic, little by little, until the attack itself looks normal.\nThe boiling frog."),
                (4.95, "Stop when suspicious", "An attacker trips the stop switch with loud junk and leaves. Honest change continues and the detector never catches up.\nThe freeze attack."),
                (9.0, "Never learn", "Safe from poisoning, but after a network change most normal traffic raises an alarm.\n78% false alarms in our test.")):
    s.line(x, 2.55, x + 3.4, 2.55, INK, 1.75)
    s.text(x, 2.82, 3.4, 0.5, t, 21, bold=True)
    s.text(x, 3.55, 3.3, 2.4, b, 17, GREY, spacing=1.2)

# 3 ---------------------------------------------------------------- idea
s = Slide("Our idea is to use neighbouring devices as a second witness. Picture a hospital ward: an infusion pump, a patient monitor and a smart bed, each from a different maker. When the hospital moves to a new network gateway, every device's traffic changes together, so the neighbours back that change and it is learned, as far as each device's own traffic agrees. If only the infusion pump starts behaving differently, no neighbour backs it, so it is allowed only slowly, within a small budget. Each device sends one signed 92-byte message per cycle. We call this Fleet-Orthogonal Adaptation, FOA.")
s.head("Ask the neighbours", "A hospital ward: three devices from three different makers.")
for y, n, v in ((2.45, "Infusion pump", "Maker A"), (3.75, "Patient monitor", "Maker B"), (5.05, "Smart hospital bed", "Maker C")):
    s.box(0.9, y, 2.6, 1.0)
    s.text(1.1, y + 0.17, 2.3, 0.4, n, 16, INK, True); s.text(1.1, y + 0.55, 2.3, 0.35, v, 13, GREY)
    s.line(3.55, y + 0.5, 4.55, 4.25, GREY, 1.25, True)
s.box(4.6, 3.6, 2.5, 1.3, WHITE, BLUE); s.text(4.7, 3.6, 2.3, 1.3, "Robust middle of the neighbours' updates", 15, BLUE, True, "c", "m")
s.line(7.15, 3.95, 8.5, 3.2, GREY, 1.25, True); s.line(7.15, 4.55, 8.5, 5.3, GREY, 1.25, True)
s.box(8.55, 2.3, 3.9, 1.85, BLUE)
s.text(8.8, 2.45, 3.5, 0.4, "Neighbours see it too", 17, WHITE, True)
s.text(8.8, 2.85, 3.5, 0.75, "The hospital switches to a new network gateway. Every device changes.", 14, WHITE)
s.text(8.8, 3.65, 3.5, 0.4, "Learn it, as far as my traffic agrees", 14, WHITE, True)
s.box(8.55, 4.5, 3.9, 1.85)
s.text(8.8, 4.65, 3.5, 0.4, "Only I see it", 17, INK, True)
s.text(8.8, 5.05, 3.5, 0.75, "Only the infusion pump starts sending unusual traffic.", 14, GREY)
s.text(8.8, 5.85, 3.5, 0.4, "Allow it slowly, within a budget", 14, INK, True)

# 4 ---------------------------------------------------------------- one cycle (flowchart)
s = Slide("Here is one learning cycle. Each traffic sample gets a score. Samples that raise an alarm are never learned from. From the most normal samples, the device proposes an update, signs it and shares it with its neighbours. It combines its neighbours' updates, keeps the part they agree on, rations the part only it sees, and updates its idea of normal. Then the next cycle starts. Nothing in this loop switches learning off.")
s.head("One learning cycle", "The same loop runs on every device.")
BW, BH, r1, r2 = 2.3, 1.0, 2.45, 4.85
def node(x, y, t):
    s.box(x, y, BW, BH, SOFT); s.text(x + 0.12, y, BW - 0.24, BH, t, 16, INK, True, "c", "m")
X1 = (0.9, 3.55, 7.3, 10.13)
for x, t in zip(X1, ("Traffic", "Score it", "Propose an update", "Sign and share")):
    node(x, r1, t)
s.line(X1[0] + BW + 0.04, r1 + BH / 2, X1[1] - 0.06, r1 + BH / 2, GREY, 1.5, True)
s.line(X1[1] + BW + 0.04, r1 + BH / 2, X1[2] - 0.06, r1 + BH / 2, GREY, 1.5, True)
s.text(X1[1] + BW + 0.05, r1 - 0.2, X1[2] - X1[1] - BW - 0.1, 0.55, "most normal samples", 13, GREY, False, "c", "b")
s.line(X1[2] + BW + 0.04, r1 + BH / 2, X1[3] - 0.06, r1 + BH / 2, GREY, 1.5, True)
s.line(X1[1] + BW / 2, r1 + BH + 0.04, X1[1] + BW / 2, r1 + BH + 0.5, GREY, 1.5, True)
s.text(X1[1] - 0.3, r1 + BH + 0.55, BW + 0.6, 0.35, "alarms are never learned", 13, GREY, False, "c")
X2 = (10.13, 5.5, 0.9)
for x, t in zip(X2, ("Combine with neighbours", "Keep what they agree on", "Update normal")):
    node(x, r2, t)
s.line(X1[3] + BW / 2, r1 + BH + 0.04, X1[3] + BW / 2, r2 - 0.06, GREY, 1.5, True)
s.line(X2[0] - 0.04, r2 + BH / 2, X2[1] + BW + 0.06, r2 + BH / 2, GREY, 1.5, True)
s.line(X2[1] - 0.04, r2 + BH / 2, X2[2] + BW + 0.06, r2 + BH / 2, GREY, 1.5, True)
s.line(X2[2] + BW / 2, r2 - 0.04, X2[2] + BW / 2, r1 + BH + 0.06, GREY, 1.5, True)
s.text(X2[2] + BW / 2 + 0.12, r1 + BH + 0.55, 1.4, 0.35, "next cycle", 13, GREY)
s.line(X2[0] + BW / 2, 6.55, X2[0] + BW / 2, r2 + BH + 0.06, GREY, 1.5, True)
s.text(X2[0] - 0.3, 6.6, BW + 0.6, 0.35, "updates from neighbours", 13, GREY, False, "c")

# 5 ---------------------------------------------------------------- guarantees
s = Slide("We guarantee four things. First, an attacker on one device can only move its detector by a fixed amount plus a slow rate beyond what the neighbours back, so poisoning needs a guaranteed minimum time. Second, fewer than half malicious neighbours can only add a limited push each cycle. Third, there is no switch an attacker can trip to stop learning, and alarmed decoys never enter the update. Fourth, every message is signed, so a device without the key cannot pretend to be a neighbour.")
s.head("What we guarantee")
for i, (t, b) in enumerate((("Bounded", "One attacked device moves only a set amount beyond what neighbours back. Poisoning needs a guaranteed minimum time."),
                            ("Resistant to bad peers", "Fewer than half malicious neighbours add only a limited push each cycle."),
                            ("Cannot be frozen", "No step switches learning off, and alarmed decoys never enter the update."),
                            ("Unforgeable", "Every message carries an HMAC tag. Without the key, no one can speak for a neighbour."))):
    y = 1.95 + i * 1.22
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.33, 3.6, 0.5, t, 21, BLUE, True)
    s.text(4.8, y + 0.34, 7.5, 0.75, b, 18, INK)

# 5b ---------------------------------------------------------------- safer across conditions (grouped bars)
s = Slide("This chart puts FOA next to a device learning on its own, both with the floor, across five conditions. With no network change, FOA halves the compromise rate. Under a strong network change it falls from forty-three percent to about nine. The classic slow poisoner, which beats a lone device three times out of four, never beat FOA. An attacker hiding inside the clean core is cut from thirty-seven percent to twelve. And when a botnet takes over devices of one model, a lone device is always compromised and FOA never is.")
s.head("Safer across attacks and conditions", "Share of attacked runs compromised. Lower is better. Both rules with the floor.")
G = (("No network\nchange", 7.6, 4.3), ("Strong network\nchange", 43.1, 9.4), ("Classic slow\npoisoner", 75.4, 0.0),
     ("Hiding in the\nclean core", 36.8, 11.8), ("One-model\nbotnet", 100.0, 0.0))
gx0, gw, base, top = 0.9, 11.53 / 5, 6.05, 2.95
sc = lambda v: (base - top) * v / 100
s.line(0.9, base, 12.43, base, LINE, 1.25)
for i, (n, a, f) in enumerate(G):
    cx = gx0 + gw * (i + 0.5)
    for j, (v, col) in enumerate(((a, PALE), (f, BLUE))):
        x = cx - 0.78 + j * 0.82
        h = max(sc(v), 0.03)
        s.box(x, base - h, 0.72, h, col, None, 0)
        s.text(x - 0.25, base - h - 0.42, 1.22, 0.38, f"{v:g}%", 17, BLUE if j else GREY, True, "c")
    s.text(cx - gw / 2 + 0.05, base + 0.12, gw - 0.1, 0.7, n, 14, INK, False, "c", spacing=1.05)
s.box(9.0, 1.98, 0.28, 0.28, PALE, None, 0); s.text(9.38, 1.95, 1.6, 0.35, "Lone device", 14, GREY)
s.box(10.95, 1.98, 0.28, 0.28, BLUE, None, 0); s.text(11.33, 1.95, 1.1, 0.35, "FOA", 14, BLUE, True)

# 6 ---------------------------------------------------------------- novelty
s = Slide("The closest earlier system is CIoTA. It uses devices of the same model as peers and discards what they do not agree on. We use devices from other vendors, we admit the rest within a budget instead of discarding it, and we prove a bound on how far an attacker can move the detector. When a botnet infects most devices of one model, same-model voting is fully compromised and ours is not. We found no prior work that combines these.")
s.head("What is new here", "What FOA adds over the closest earlier system, CIoTA.")
s.text(4.6, 2.2, 3.6, 0.4, "CIoTA", 18, GREY, True); s.text(8.5, 2.2, 3.9, 0.4, "FOA (ours)", 18, BLUE, True)
for i, (k, a, b) in enumerate((("Who are the peers", "Same device model", "Other vendors"),
                               ("What neighbours do not back", "Discarded", "Admitted slowly, within a budget"),
                               ("Limit on an attacker", "Agreement of the group", "Proven bound on movement"),
                               ("Can it be frozen", "Not analysed", "No stop switch to trip"),
                               ("One-model botnet in our test", "100% compromised", "0% compromised"))):
    y = 2.75 + i * 0.8
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.22, 3.6, 0.5, k, 16, INK, True); s.text(4.6, y + 0.22, 3.7, 0.5, a, 16, GREY); s.text(8.5, y + 0.22, 3.9, 0.5, b, 16, INK, i == 4)

# 7 ---------------------------------------------------------------- evaluation setup
s = Slide("We tested on real traffic from nine IoT devices with real Mirai and BASHLITE attacks, and on forty weeks of real traffic from a national research network. Across more than twenty-six thousand fleet runs we compared FOA with eight other update rules. Every design choice was made on separate runs from the ones we report.")
s.head("How we tested it", "Real IoT traffic, real botnet attacks, real network change.")
for x, big, small in ((0.9, "9", "real IoT devices with real Mirai and BASHLITE traffic (N-BaIoT)"),
                      (5.0, "40", "weeks of real network traffic (CESNET)"),
                      (9.1, "26k+", "fleet runs, compared with eight other rules")):
    s.text(x, 2.5, 3.6, 1.5, big, 88, INK, True, anchor="b")
    s.text(x, 4.2, 3.2, 1.2, small, 17, GREY)
s.text(0.9, 6.3, 11.4, 0.4, "Every reported result comes from test runs that played no part in any design decision.", 16, INK, True)

# 8 ---------------------------------------------------------------- main result
s = Slide("This is the main result. During a strong network change, an attacker hides poisoning inside it. A detector learning on its own is compromised in about forty percent of runs. FOA brings that to about ten percent, about four times fewer. Against the classic slow poisoner, FOA was never compromised.")
s.head("About 4× fewer compromised devices", "Poisoning hidden inside a strong network change. Share of attacked runs where the attack went undetected.")
s.bars(1.4, 2.1, 10.5, 4.4, ["Single device", "Single device\n+ floor", "FOA", "FOA\n+ floor"], [39.2, 43.1, 10.8, 9.4], {2, 3})
s.text(0.9, 6.7, 11.5, 0.4, "Against the classic slow poisoner: 0% for FOA, 63% for a single device.", 17, INK, True)

# 9 ---------------------------------------------------------------- all rules (trade-off chart)
s = Slide("Here every rule is one dot, under strong network change. Left is fewer false alarms, down is fewer compromised devices, so the bottom-left corner is best. Rules that stop or restrict learning sit to the right: safer, but noisy. Learning everything is quiet but easy to poison. TOA is safe only because it is told the attack in advance. FOA sits closest to the corner without knowing the attack: nine percent false alarms and about eleven percent compromised.")
s.head("The only rule low on both", "Each dot is one rule under strong network change. Closer to the bottom-left is better.")
gx0, gx1, gy0, gy1 = 1.7, 9.4, 6.3, 2.3            # x: false alarms 0..80 %, y: compromised 0..45 %
tx = lambda v: gx0 + (gx1 - gx0) * v / 80
ty = lambda v: gy0 - (gy0 - gy1) * v / 45
s.line(gx0, gy0, gx1, gy0, INK, 1.25); s.line(gx0, gy0, gx0, gy1, INK, 1.25)
for v in (0, 20, 40, 60, 80):
    s.text(tx(v) - 0.4, gy0 + 0.08, 0.8, 0.3, f"{v}%", 12, GREY, align="c")
for v in (15, 30, 45):
    s.line(gx0, ty(v), gx1, ty(v), "E8E8ED", 0.75); s.text(gx0 - 0.75, ty(v) - 0.15, 0.65, 0.3, f"{v}%", 12, GREY, align="r")
s.text(gx0, gy0 + 0.4, gx1 - gx0, 0.3, "false alarms", 13, GREY, align="c")
s.text(0.9, gy1 - 0.45, 4, 0.3, "compromised", 13, GREY)
for n, x, y, dx, dy in (("Never learn", 78.3, 0, -1.75, -0.45), ("Learn everything", 2.6, 35, 0.15, -0.42), ("Single device", 24.6, 39, 0.15, -0.42),
                        ("Limit each step", 55.9, 30, 0.12, -0.42), ("Frozen reference", 59.3, 27, 0.15, 0.05), ("Stop on many alarms", 45.0, 30, -2.15, 0.08),
                        ("TOA, knows the attack", 38.3, 5.5, 0.15, -0.42)):
    s.dot(tx(x), ty(y), 0.09, PALE, GREY); s.text(tx(x) + dx, ty(y) + dy, 2.3, 0.35, n, 13, GREY)
s.dot(tx(9.0), ty(10.8), 0.15, BLUE)
s.text(tx(9.0) + 0.25, ty(10.8) - 0.2, 1.0, 0.4, "FOA", 18, BLUE, True)
s.text(9.9, 2.5, 2.6, 0.5, "FOA", 26, BLUE, True)
s.text(9.9, 3.15, 2.6, 0.4, "9.0% false alarms", 17, INK, True)
s.text(9.9, 3.6, 2.6, 0.4, "10.8% compromised", 17, INK, True)
s.text(9.9, 4.25, 2.55, 1.6, "Closest to the corner, and the only rule near it that does not need the attack known in advance.", 15, GREY, spacing=1.18)

# 10 ---------------------------------------------------------------- other attacks
s = Slide("Three more tests that break other defences. When a botnet infects most cameras of one model, same-model voting fails completely, while neighbours from other vendors hold. Five percent decoy traffic permanently locks a stop-learning defence, and FOA is unaffected. Over forty weeks of real network change, FOA was never compromised, against eighteen percent for a single device.")
s.head("Three attacks that break other defences")
for x, big, t, b in ((0.9, "0%", "One-model botnet", "FOA compromised. Same-model voting: 100% once two of three cameras are infected."),
                     (5.0, "100%", "Freeze attack", "False alarms for a stop-learning defence after 5% decoys. FOA is unaffected."),
                     (9.1, "0%", "40 weeks of real change", "FOA compromised on real national-network traffic. Single device: 18%.")):
    s.text(x, 2.1, 3.7, 1.4, big, 72, BLUE if big == "0%" else RED, True, anchor="b")
    s.line(x, 3.85, x + 3.35, 3.85)
    s.text(x, 4.12, 3.35, 0.5, t, 20, bold=True)
    s.text(x, 4.75, 3.2, 1.6, b, 16, GREY, spacing=1.2)

# 11 ---------------------------------------------------------------- testbed photo
s = Slide("This is our testbed. Three ESP8266 boards and an INA226 power sensor in the supply line of one of them, connected over USB to the laptop that records their output. The boards talk to each other directly over ESP-NOW.")
s.head("Our testbed", "Three ESP8266 boards, an INA226 power sensor, and a laptop recording every board.")
photo = os.path.join(ROOT, "research.jpeg")
if not os.path.exists(photo) or "--blurred" in sys.argv:
    photo = os.path.join(HERE, "testbed_photo.jpg")
pw, ph = Image.open(photo).size
w_in = 5.2 * pw / ph
s.s.shapes.add_picture(photo, Inches((13.333 - w_in) / 2), Inches(2.05), Inches(w_in), Inches(5.2))
s.im.paste(Image.open(photo).resize((int(w_in * PX), int(5.2 * PX))), (int((13.333 - w_in) / 2 * PX), int(2.05 * PX)))

# 12 ---------------------------------------------------------------- hardware
s = Slide("And it runs on real boards. Three ESP8266 boards talk directly over ESP-NOW and hear both neighbours in nearly every cycle. Computing an update takes tens of milliseconds, combining neighbours under two milliseconds, and signing a message under a millisecond. The board draws under 400 milliwatts, almost all of it the radio, and the extra energy for learning was too small for our sensor to detect.")
s.head("It runs on a tiny board", "Three ESP8266 boards talking directly over ESP-NOW, one INA226 power sensor.")
for i, (k, v) in enumerate((("Cycles hearing both neighbours", "88 to 100%"), ("Compute an update", "11 to 24 ms"), ("Combine with neighbours", "1.2 to 1.9 ms"),
                            ("Sign one message, check two", "0.6 ms and about 1 ms"), ("Board power", "365 to 391 mW"), ("Extra energy for learning", "Too small to detect"))):
    y = 2.35 + i * 0.7
    s.text(0.9, y + 0.15, 6, 0.4, k, 18, GREY); s.text(6.9, y + 0.15, 5.5, 0.4, v, 20, INK, True, "r")
    s.line(0.9, y + 0.68, 12.43, y + 0.68)

# 13 ---------------------------------------------------------------- found and fixed on hardware
s = Slide("Real hardware showed us something no simulation had. Identical boards sending repetitive traffic agreed with each other on shrinking their idea of normal, until it was under two percent of its starting size. We traced the cause, reproduced it, and fixed it with one rule: normal never shrinks below its calibrated size. On the boards the normal region then held its full size in every run. We also found and fixed a calibration timing bug, and false alarms on the boards came down to about one and a half percent.")
s.head("Hardware showed what simulation could not", "We found a hidden failure on the boards, explained it, and fixed it.")
for x, big, col, t, b in ((0.9, "<2%", RED, "Before the fix", "Identical boards agreed on shrinking “normal” until almost everything alarmed."),
                          (5.0, "1.0", BLUE, "The floor held", "With one new rule, the normal region kept its full size on every board."),
                          (9.1, "1.6%", BLUE, "False alarms now", "On the boards, after we also fixed calibration timing. Down from 25%.")):
    s.text(x, 2.1, 3.9, 1.4, big, 72, col, True, anchor="b")
    s.line(x, 3.85, x + 3.35, 3.85)
    s.text(x, 4.12, 3.35, 0.5, t, 20, bold=True)
    s.text(x, 4.75, 3.2, 1.6, b, 16, GREY, spacing=1.2)
s.text(0.9, 6.55, 11.5, 0.5, "The rule: “normal” never shrinks below its calibrated size.", 18, INK, True)

# 14 ---------------------------------------------------------------- strengths
s = Slide("What makes FOA practical. It needs no labels or attack signatures. Each device sends one small signed message per cycle, with no server or cloud. Combining neighbours takes a millisecond or two on a tiny board. Neighbours come from different makers, so one exploit cannot easily fake agreement. There is no switch to freeze it, and the damage one compromised device can do is provably bounded.")
s.head("Built for real deployments", "What makes FOA practical on small IoT devices.")
for i, (t, b) in enumerate((("No labels", "Learns from its own traffic. Needs no attack signatures or labelled data."),
                            ("Tiny messages", "One signed 92-byte broadcast per cycle. No server, no cloud."),
                            ("Fast", "1.2 to 1.9 ms to combine neighbours on an ESP8266."),
                            ("Cross-vendor", "Neighbours from different makers, so one exploit cannot easily fake agreement."),
                            ("Cannot be frozen", "No switch an attacker can trip to stop learning."),
                            ("Proven limits", "A guaranteed bound on how far one compromised device can be moved."))):
    x, y = 0.9 + (i % 3) * 3.98, 2.35 + (i // 3) * 2.15
    s.line(x, y, x + 3.55, y, INK, 1.5)
    s.text(x, y + 0.22, 3.5, 0.45, t, 22, BLUE, True)
    s.text(x, y + 0.82, 3.4, 1.0, b, 16, GREY, spacing=1.2)

# 15 ---------------------------------------------------------------- use cases
s = Slide("Where FOA fits. Anywhere a fleet of IoT devices shares a network that keeps changing. In smart buildings and campuses, a gateway can run one detector per device, with hundreds of neighbours. In industrial networks, monitoring tools often learn a baseline once and then stop; FOA keeps the baseline current without opening it to slow poisoning. Hospitals mix many device makers on one network. And commercial platforms that already compare devices with their peers can use FOA as the rule for when a baseline may move.")
s.head("Where FOA fits", "Fleets of IoT devices that share a network and keep changing.")
for i, (t, b) in enumerate((("Smart buildings and campuses", "A gateway runs one detector per device. Hundreds of devices share every network change, so neighbours are plentiful."),
                            ("Industrial and OT networks", "Monitoring tools often learn a baseline once and then stop. FOA keeps it current without opening it to slow poisoning."),
                            ("Hospitals and clinics", "Many device makers on one network, frequent updates, and attacks that must not hide inside routine change."),
                            ("Security platforms", "Products already compare devices with their peers. FOA adds a proven rule for when a baseline may move."))):
    x, y = 0.9 + (i % 2) * 5.85, 2.2 + (i // 2) * 2.25
    s.box(x, y, 5.6, 2.0)
    s.text(x + 0.35, y + 0.3, 5.0, 0.45, t, 20, INK, True)
    s.text(x + 0.35, y + 0.88, 4.95, 1.0, b, 15, GREY, spacing=1.18)

# 15b ---------------------------------------------------------------- how we got here (idea sequence)
s = Slide("This is the path of ideas that led to FOA. We started with a single detector that learns on its own, which is easy to poison slowly. Pausing when things look suspicious is safer, but an attacker can freeze it. Our first method, TOA, was very safe, but it needed to know the attack in advance. FOA replaces that knowledge with neighbours as witnesses. Testing on real boards then led us to the coverage floor, and the final system runs on ESP8266 boards with 92-byte messages.")
s.head("How we got here", "Each idea fixed the weakness of the one before.")
steps = (("Learn alone", "Easy to poison, little by little."),
         ("Pause when suspicious", "Safer, but an attacker can freeze it."),
         ("TOA", "Very safe, but needs the attack known in advance."),
         ("FOA", "Neighbours as witnesses. No attack knowledge needed."),
         ("Coverage floor", "Found on real boards. One rule fixed it."),
         ("On the boards", "92-byte messages, about 1 ms to combine."))
cw = 11.53 / 6
s.line(0.9 + cw / 2, 2.75, 0.9 + cw * 5.5, 2.75, LINE, 2)
for i, (t, b) in enumerate(steps):
    cx = 0.9 + cw * (i + 0.5); hi = i >= 3
    s.dot(cx, 2.75, 0.32, BLUE if hi else WHITE, None if hi else GREY)
    s.text(cx - 0.32, 2.43, 0.64, 0.64, str(i + 1), 18, WHITE if hi else GREY, True, "c", "m")
    s.text(cx - cw / 2 + 0.08, 3.4, cw - 0.16, 0.8, t, 18, BLUE if hi else INK, True, "c")
    s.text(cx - cw / 2 + 0.12, 4.25, cw - 0.24, 1.6, b, 14, GREY, align="c", spacing=1.18)
    if i < 5:
        s.line(cx + 0.36, 2.75, cx + cw - 0.4, 2.75, GREY if i < 2 else BLUE, 1.5, True)
s.box(0.9, 6.05, 11.53, 0.75, SOFT)
s.text(1.2, 6.05, 11.0, 0.75, "Result: a detector that keeps learning, needs no attack signatures, and limits what one compromised device can do.", 16, INK, True, anchor="m")

# 16 ---------------------------------------------------------------- recent research
s = Slide("These are six recent papers behind our work. From DriftXpert we took its outlier-ratio statistic, which our baseline uses to pause learning. RTTAD adapts only on samples it is confident about and reports that unguarded adaptation hurts. WARDEN argues that one stream cannot tell drift from poisoning, which is exactly why we add neighbours. Su and others, and Rapid Poison, show that systems which adapt can be poisoned, which shapes our threat model. The TinyML survey reviews about seventy on-device learning works and does not discuss security, which is the gap we work in.")
s.head("Recent research we build on", "Six recent papers, and what each gave us.")
s.text(0.9, 2.1, 5.6, 0.35, "Paper", 13, GREY, True); s.text(7.0, 2.1, 5.4, 0.35, "What we took from it", 13, BLUE, True)
for i, (t, v, b) in enumerate((
        ("DriftXpert: drift adaptation for intrusion detection", "arXiv preprint",
         "Its outlier-ratio statistic, used in our baseline as a stop gate."),
        ("RTTAD: risk-aware test-time adaptation", "arXiv preprint",
         "Adapt only on samples you are confident about. Unguarded adaptation hurts."),
        ("WARDEN: self-poisoning in adaptive detection", "arXiv preprint",
         "One stream cannot separate drift from poisoning, so we add neighbours."),
        ("Su et al.: poisoning test-time adaptation", "ICLR",
         "A realistic attacker with limited knowledge, for our threat model."),
        ("Rapid Poison: attacks on a rapid response framework", "ICML",
         "Evidence that adaptation itself is an attack surface."),
        ("Survey: on-device learning in TinyML", "arXiv preprint",
         "About 70 on-device learning works, and no discussion of security."))):
    y = 2.5 + i * 0.75
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.1, 5.8, 0.3, t, 15, INK, True); s.text(0.9, y + 0.42, 5.8, 0.28, v, 12, GREY)
    s.text(7.0, y + 0.1, 5.4, 0.62, b, 14, INK, anchor="m")

# 17 ---------------------------------------------------------------- close
s = Slide("To sum up: learn freely what the neighbours also see, ration what only you see. We tested this on real IoT traffic, real botnet attacks, forty weeks of real network change, and real boards. These are the foundations we build on.")
s.text(0.9, 0.85, 11.5, 1.7, "Learn what neighbours see.\nRation what only you see.", 40, bold=True, spacing=1.05)
s.text(0.9, 2.85, 11, 0.45, "Tested on real IoT traffic, real botnet attacks and real boards.", 18, GREY)
s.line(0.9, 3.75, 12.43, 3.75)
s.text(0.9, 3.98, 4, 0.4, "Built on", 15, INK, True)
for i, r in enumerate(("Rubinstein et al., ANTIDOTE: poisoning of anomaly detectors, ACM IMC",
                       "Kloft and Laskov, Security analysis of online centroid anomaly detection, JMLR",
                       "Golomb, Mirsky, Elovici, CIoTA: collaborative IoT anomaly detection, NDSS DISS",
                       "Meidan et al., N-BaIoT, IEEE Pervasive Computing",
                       "Koumar et al., CESNET-TimeSeries24, Scientific Data")):
    s.text(0.9, 4.45 + i * 0.4, 11.5, 0.35, r, 15, GREY)

# 17b ---------------------------------------------------------------- research questions and answers
s = Slide("We asked two research questions. First: can a fleet of self-learning detectors keep following honest change, while limiting how fast an attacker on one device can poison its detector, without a stop switch an attacker could trip? Second: does this hold up against the attacks that defeat existing defences, a botnet that takes over most devices of one model, and a freeze attack? Our four hypotheses are all supported. Safety: about eleven percent compromised against thirty-nine for a single device. Tracking: false alarms within two points of a single device. Cost: under two milliseconds to combine on an ESP8266. Robustness: zero percent compromised under a one-model botnet, and unaffected by decoys.")
s.head("Our research questions")
for x, k, q in ((0.9, "RQ1", "Can a fleet of self-learning detectors keep following honest change, while limiting how fast an attacker on one device can poison its detector, without a stop switch an attacker could trip?"),
                (6.79, "RQ2", "Does it hold up against the attacks that defeat existing defences: a botnet that takes over most devices of one model, and a freeze attack?")):
    s.box(x, 1.7, 5.64, 1.75, BLUE)
    s.text(x + 0.3, 1.85, 1.0, 0.4, k, 16, WHITE, True)
    s.text(x + 0.3, 2.25, 5.05, 1.15, q, 14, WHITE, True, spacing=1.12)
for i, (h, t, r) in enumerate((("H1  Safety", "RQ1. Under shared change, FOA is compromised less often than a lone device and gated defences.", "10.8% vs 39.2% (lone) and 27 to 30% (gated)"),
                               ("H2  Tracking", "RQ1. FOA follows shared change with false alarms close to a lone device.", "2.5% vs 0.8%, both with the floor"),
                               ("H3  Cost", "RQ1. FOA fits a few-dollar microcontroller.", "1.2 to 1.9 ms to combine, 92-byte messages"),
                               ("H4  Robustness", "RQ2. FOA resists a one-model botnet and is not frozen by decoys.", "0% vs 100% for same-model voting; decoys have no effect"))):
    y = 3.75 + i * 0.9
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.17, 2.2, 0.4, h, 16, BLUE, True)
    s.text(3.1, y + 0.17, 5.1, 0.7, t, 14, INK)
    s.text(8.4, y + 0.17, 2.85, 0.7, r, 13, GREY)
    s.text(11.25, y + 0.17, 1.18, 0.4, "Supported", 13, BLUE, True, "r")

# 18 ---------------------------------------------------------------- limits and next (last)
s = Slide("Finally, what is still open and what we do next. A large change on one device alone is learned slowly, because no neighbour backs it. Malicious neighbours combined with a poisoner can beat devices whose attack is close to normal. A sudden jump outside the normal region leaves nothing to learn from. And three boards is still a small fleet. Thank you, we are happy to take questions.")
s.head("What is still open")
s.text(0.9, 1.9, 5.3, 0.45, "Current limits", 21, bold=True)
s.text(7.1, 1.9, 5.3, 0.45, "What we do next", 21, bold=True)
for i, (a, b) in enumerate((("A big change on one device alone is learned slowly.", "Larger board fleets with mixed device makers."),
                            ("Bad neighbours plus a poisoner can beat borderline devices.", "Recover safely from a sudden jump."),
                            ("A sudden jump outside the normal region stalls learning.", "Run one detector per device on a gateway, with per-source statistics."),
                            ("Three boards is still a small fleet.", "Compare with BALANCE and ClippedGossip."))):
    y = 2.6 + i * 0.98
    s.line(0.9, y, 6.2, y); s.line(7.1, y, 12.43, y)
    s.text(0.9, y + 0.18, 5.2, 0.75, a, 17, GREY); s.text(7.1, y + 0.18, 5.2, 0.75, b, 17)
s.text(0.9, 6.6, 6, 0.45, "Thank you. Questions?", 22, BLUE, True)


out = os.path.join(ROOT, "G04_FOA_Final.pptx")
prs.save(out); print("wrote", out, len(prs.slides), "slides")
if PREV:
    os.makedirs(PREV, exist_ok=True)
    for i, im in enumerate(previews, 1):
        im.save(os.path.join(PREV, f"s{i}.png"))
    sheet = Image.new("RGB", (1600 * 3 + 40, 920 * ((len(previews) + 2) // 3) + 20), "#555555")
    for i, im in enumerate(previews):
        sheet.paste(im, (i % 3 * 1620, i // 3 * 920))
    sheet.resize((sheet.width // 3, sheet.height // 3)).save(os.path.join(PREV, "sheet.png"))
