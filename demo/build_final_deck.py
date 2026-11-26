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
s = Slide("Good afternoon. We are Group G-04. Our project is about an IoT intrusion detector that keeps learning without being taught to ignore attacks. We will show the idea, what worked in simulation, and what broke on real boards.")
s.text(0.9, 1.85, 11.5, 2.0, "Learning from the\nneighbours", 60, bold=True, spacing=1.0)
s.text(0.9, 4.15, 9.5, 0.9, "Poison-resilient intrusion detection on drifting IoT devices", 22, GREY)
s.text(0.9, 6.15, 8, 0.35, "Rishit Kamboj and Farhan Naik", 15, INK, True)
s.text(0.9, 6.5, 9, 0.35, "CSD457 Internet of Things  ·  Group G-04  ·  November 2026", 13, GREY)

# 2 ---------------------------------------------------------------- problem
s = Slide("A detector learns what normal traffic looks like. Normal changes, so it has to keep learning. If it trusts itself, an attacker can walk it slowly toward the attack. If it stops learning when things look suspicious, the attacker can trigger that stop and leave, and it floods with false alarms. From one device's traffic these cases look alike.")
s.head("A detector that learns can be fooled", "Normal traffic keeps changing, so standing still is not an option either.")
for x, t, b in ((0.9, "Trust yourself", "An attacker feeds slightly unusual traffic, little by little, until the attack itself looks normal.\nThe boiling frog."),
                (4.95, "Stop when suspicious", "An attacker trips the stop switch with loud junk and leaves. Honest change continues and the detector never catches up.\nThe freeze attack."),
                (9.0, "Never learn", "Safe from poisoning, but after a network change most normal traffic raises an alarm.\n78% false alarms in our test.")):
    s.line(x, 2.55, x + 3.4, 2.55, INK, 1.75)
    s.text(x, 2.82, 3.4, 0.5, t, 21, bold=True)
    s.text(x, 3.55, 3.3, 2.4, b, 17, GREY, spacing=1.2)

# 3 ---------------------------------------------------------------- idea
s = Slide("Our idea is to use neighbouring devices as a second witness. A router change reaches everyone. An exploit usually reaches one device. So the part of an update that neighbours also see is applied in full, and the part only this device sees goes through a small budget that grows slowly and never closes.")
s.head("Ask the neighbours", "Honest change reaches everyone. An attack usually reaches one.")
for y, n in ((2.55, "Doorbell"), (3.75, "Thermostat"), (4.95, "Baby monitor")):
    s.box(0.9, y, 2.4, 0.85); s.text(0.9, y, 2.4, 0.85, n, 16, align="c", anchor="m")
    s.line(3.35, y + 0.42, 4.55, 4.17, GREY, 1.25, True)
s.box(4.6, 3.55, 2.5, 1.25, WHITE, BLUE); s.text(4.7, 3.55, 2.3, 1.25, "Robust middle of the neighbours' updates", 15, BLUE, True, "c", "m")
s.line(7.15, 3.9, 8.5, 3.15, GREY, 1.25, True); s.line(7.15, 4.45, 8.5, 5.2, GREY, 1.25, True)
s.box(8.55, 2.55, 3.9, 1.3, BLUE); s.text(8.8, 2.55, 3.5, 1.3, "Neighbours see it too\nLearn it in full", 17, WHITE, True, anchor="m")
s.box(8.55, 4.65, 3.9, 1.3); s.text(8.8, 4.65, 3.5, 1.3, "Only I see it\nAllow it slowly, within a budget", 17, INK, True, anchor="m")
s.text(0.9, 6.45, 11.5, 0.4, "Each device sends one signed 92-byte message per learning cycle. We call this Fleet-Orthogonal Adaptation (FOA).", 14, GREY)

# 3b ---------------------------------------------------------------- one cycle
s = Slide("Here is one learning cycle. The device looks at a batch of its own traffic, proposes an update from the part that looks clearly normal, signs it and broadcasts it, takes the robust middle of its neighbours' updates, and splits its own update into the shared part and its own part. Nothing in this loop ever switches learning off.")
s.head("One learning cycle", "The same six steps run on every device. No step can switch learning off.")
for i, (t, b) in enumerate((("Look", "Summarise recent traffic as 16 numbers per sample."),
                            ("Propose", "Work out an update from the clearly normal core of the batch."),
                            ("Share", "Sign it with HMAC and broadcast 92 bytes."),
                            ("Agree", "Take the geometric median of verified neighbour updates."),
                            ("Split", "Part the neighbours back is learned in full. The rest is budgeted."),
                            ("Check", "Score new traffic. Alarm if it falls outside the threshold."))):
    x, y = 0.9 + (i % 3) * 3.98, 2.35 + (i // 3) * 2.15
    s.line(x, y, x + 3.55, y, INK if i < 5 else INK, 1.5)
    s.text(x, y + 0.22, 3.5, 0.45, f"{i + 1}  {t}", 21, BLUE, True)
    s.text(x, y + 0.82, 3.4, 1.0, b, 16, GREY, spacing=1.2)

# 4 ---------------------------------------------------------------- guarantees
s = Slide("We proved four things. The main one: an attacker on one device can only move its detector by a fixed amount plus a slow rate, so there is a minimum time before an attack can hide. We also state the limit honestly: if only one device changes, no method can know whether it is honest.")
s.head("What we can prove")
for i, (t, b) in enumerate((("Bounded", "An attacker on one device moves its detector by at most B0 + Bt alarm radii beyond what neighbours back."),
                            ("Resistant to bad peers", "Fewer than half malicious neighbours add only a limited push each cycle."),
                            ("No freeze switch", "Loud decoy traffic never enters learning, and learning never stops."),
                            ("An honest limit", "If only one device changes, no rule can tell its own change from an attack."))):
    y = 1.95 + i * 1.22
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.33, 3.6, 0.5, t, 21, BLUE if i < 3 else INK, True)
    s.text(4.8, y + 0.34, 7.5, 0.75, b, 18, INK)

# 4b ---------------------------------------------------------------- novelty
s = Slide("Using peers is not new. CIoTA did it with devices of the same model, and it discards what they do not agree on. We use devices from other vendors, we ration the rest instead of discarding it, and we bound how far an attacker can move the detector. We say we found no prior work that combines these, not that we are first.")
s.head("What is new here", "Closest earlier work: CIoTA (2018), which also learns with peers.")
s.text(4.6, 2.2, 3.6, 0.4, "CIoTA", 18, GREY, True); s.text(8.5, 2.2, 3.9, 0.4, "Ours", 18, BLUE, True)
for i, (k, a, b) in enumerate((("Who are the peers", "Same device model", "Other vendors"),
                               ("What neighbours do not back", "Discarded", "Admitted slowly, within a budget"),
                               ("Limit on an attacker", "Agreement of the group", "Proven bound on movement"),
                               ("One-model botnet in our test", "100% compromised (2 or 3 of 3)", "0% compromised"))):
    y = 2.75 + i * 0.86
    s.line(0.9, y, 12.43, y)
    s.text(0.9, y + 0.24, 3.6, 0.5, k, 16, INK, True); s.text(4.6, y + 0.24, 3.7, 0.5, a, 16, GREY); s.text(8.5, y + 0.24, 3.9, 0.5, b, 16, INK)
s.line(0.9, 6.2, 12.43, 6.2)
s.text(0.9, 6.45, 11.5, 0.4, "CIoTA column: our re-implementation of its consensus idea, not the full published system.", 13, GREY)

# 5 ---------------------------------------------------------------- evaluation setup
s = Slide("We tested on real traffic from nine IoT devices with real botnet attacks, and on forty weeks of real network traffic. The drift on the nine devices and the poisoner are simulated by us, and we say so. Design choices were made on separate runs from the ones we report.")
s.head("How we tested it", "Real traffic and real attacks. Simulated fleet, drift on N-BaIoT, and poisoner.")
for x, big, small in ((0.9, "9", "real IoT devices with real Mirai and BASHLITE traffic (N-BaIoT)"),
                      (5.0, "40", "weeks of real network traffic (CESNET)"),
                      (9.1, "26k+", "simulated fleet runs, compared with eight other rules")):
    s.text(x, 2.5, 3.6, 1.5, big, 88, INK, True, anchor="b")
    s.text(x, 4.2, 3.2, 1.2, small, 17, GREY)
s.text(0.9, 6.3, 11.4, 0.4, "Reported simulation results use test runs that played no part in any design decision.", 15, INK, True)

# 6 ---------------------------------------------------------------- main result
s = Slide("This is the main result. During a strong network change, an attacker hides poisoning inside it. A single device is compromised in about forty percent of runs. FOA brings that to about ten percent, and the classic slow poisoner never beats it.")
s.head("Poisoning hidden inside network change", "Share of attacked runs where the target attack went undetected. Lower is better.")
s.bars(1.4, 2.1, 10.5, 4.4, ["Single device", "Single device\n+ floor", "FOA", "FOA\n+ floor"], [39.2, 43.1, 10.8, 9.4], {2, 3})
s.text(0.9, 6.75, 11.5, 0.35, "The classic slow poisoner under the same change: 63% and 75% for a single device, 0% for FOA.", 14, INK)

# 6b ---------------------------------------------------------------- all rules
s = Slide("Here is every rule side by side under strong network change. Rules that stop or restrict learning keep some safety but raise many false alarms. The naive rule is quiet but easy to poison. TOA is very safe but needs to know the attack in advance. FOA is low on both. These numbers are without the floor.")
s.head("Eight rules, side by side", "Strong network change. Lower is better in both columns. Without the floor.")
s.text(7.0, 1.98, 2.4, 0.35, "False alarms", 14, GREY, True, "r"); s.text(9.8, 1.98, 2.6, 0.35, "Compromised", 14, GREY, True, "r")
for i, (n, w, a, c) in enumerate((("Never learn", "cannot follow change", "78.3%", "not attacked"), ("Learn everything", "easy to poison", "2.6%", "35%"),
                                  ("Single device", "shrinks, and drift hides attacks", "24.6%", "39%"), ("Limit each step", "patient attackers get through", "55.9%", "30%"),
                                  ("Frozen reference", "cannot follow large change", "59.3%", "27%"), ("Stop on many alarms", "can be frozen", "45.0%", "30%"),
                                  ("TOA, knows the attack", "needs the signature in advance", "38.3%", "5.5%"), ("FOA", "shares what neighbours see", "9.0%", "10.8%"))):
    y = 2.4 + i * 0.55
    s.line(0.9, y, 12.43, y)
    hi = BLUE if n == "FOA" else INK
    s.text(0.9, y + 0.12, 3.0, 0.35, n, 15, hi, True); s.text(3.95, y + 0.13, 3.7, 0.35, w, 14, GREY)
    s.text(7.0, y + 0.12, 2.4, 0.35, a, 16, hi, n == "FOA", "r"); s.text(9.8, y + 0.12, 2.6, 0.35, c, 16, hi, n == "FOA", "r")

# 7 ---------------------------------------------------------------- other attacks
s = Slide("Three more tests. When a botnet infects most cameras of one model, same-model voting fails completely, while neighbours from other vendors hold. Five percent decoy traffic permanently locks a stop-learning defence. On forty weeks of real drift, FOA was never compromised. These three were run without the floor.")
s.head("Three more tests", "Run without the floor.")
for x, big, t, b in ((0.9, "0%", "One-model botnet", "FOA compromised. Same-model voting: 100% once two of three cameras are infected."),
                     (5.0, "100%", "Freeze attack", "False alarms for a stop-learning defence after 5% decoys. FOA's behaviour is unchanged by them."),
                     (9.1, "0%", "40 weeks of real change", "FOA compromised. Single device: 18%.")):
    s.text(x, 2.1, 3.7, 1.4, big, 72, BLUE if big == "0%" else RED, True, anchor="b")
    s.line(x, 3.85, x + 3.35, 3.85)
    s.text(x, 4.12, 3.35, 0.5, t, 20, bold=True)
    s.text(x, 4.75, 3.2, 1.6, b, 16, GREY, spacing=1.2)

# 7b ---------------------------------------------------------------- testbed photo
s = Slide("This is our actual testbed. Three ESP8266 boards and an INA226 power sensor in the supply line of one of them, connected over USB to the laptop that records their output. The boards talk to each other directly over ESP-NOW.")
s.head("Our testbed", "Three ESP8266 boards, an INA226 power sensor, and a laptop recording every board.")
photo = os.path.join(HERE, "testbed_photo.jpg")
pw, ph = Image.open(photo).size
w_in = 5.2 * pw / ph
s.s.shapes.add_picture(photo, Inches((13.333 - w_in) / 2), Inches(2.05), Inches(w_in), Inches(5.2))
s.im.paste(Image.open(photo).resize((int(w_in * PX), int(5.2 * PX))), (int((13.333 - w_in) / 2 * PX), int(2.05 * PX)))

# 8 ---------------------------------------------------------------- hardware
s = Slide("Then we built it. Three ESP8266 boards on a phone hotspot talk over ESP-NOW, and an INA226 measures one board's power. Each learning cycle needs about fifteen milliseconds of computing. We could not detect any extra energy for learning with this sensor.")
s.head("Then we put it on real boards", "Three ESP8266 boards, a phone hotspot, one INA226 power sensor.")
for i, (k, v) in enumerate((("Cycles hearing both neighbours", "97 to 100%"), ("Compute an update", "11.2 ms"), ("Combine with neighbours", "1.6 ms"),
                            ("Sign one message, check two", "0.6 ms and 0.95 ms"), ("Board power", "365 mW"), ("Extra energy for learning", "Too small to detect"))):
    y = 2.35 + i * 0.7
    s.text(0.9, y + 0.15, 6, 0.4, k, 18, GREY); s.text(6.9, y + 0.15, 5.5, 0.4, v, 20, INK, True, "r")
    s.line(0.9, y + 0.68, 12.43, y + 0.68)
s.text(0.9, 6.75, 11.5, 0.35, "Measured on hardware. No attacks were run on the boards.", 13, GREY)

# 9 ---------------------------------------------------------------- failure
con, iso = spread_series()
s = Slide("This is what simulation had missed. With the three boards listening to each other, each detector's idea of normal shrank to under two percent in twenty minutes, and false alarms reached about ninety percent. In another run where Wi-Fi was not connected, so boards could not hear each other, it shrank far more slowly. That second run is not a controlled comparison.")
s.head("On the boards, “normal” collapsed", "Size of the normal region, as a share of its starting size (node 1, first 20 minutes).")
cd = XyChartData()
for name, pts in (("Hearing neighbours", con), ("Isolated, no Wi-Fi", iso)):
    se = cd.add_series(name)
    for x_, y_ in pts:
        se.add_data_point(round(x_, 2), round(y_, 2))
ch = s.s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(0.9), Inches(2.05), Inches(8.4), Inches(4.8), cd).chart
ch.has_title = False; ch.font.name = FONT; ch.font.size = Pt(12); ch.font.color.rgb = rgb(GREY)
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
for se, col in zip(ch.plots[0].series, (RED, GREY)):
    se.format.line.color.rgb = rgb(col); se.format.line.width = Pt(3); se.smooth = False
va, ca = ch.value_axis, ch.category_axis
va.minimum_scale, va.maximum_scale, va.major_unit = 0, 100, 25; va.major_gridlines.format.line.color.rgb = rgb("E8E8ED"); va.format.line.fill.background()
va.tick_labels.number_format = '0"%"'; va.tick_labels.number_format_is_linked = False
ca.minimum_scale, ca.maximum_scale, ca.major_unit = 0, 20, 5; ca.format.line.color.rgb = rgb(LINE); ca.has_major_gridlines = False
ca.has_title = True; ca.axis_title.text_frame.text = "minutes"
for pts, col in ((con, RED), (iso, GREY)):
    s.d.line([((1.5 + 7.6 * a / 20) * PX, (6.1 - 3.8 * b / 100) * PX) for a, b in pts], fill="#" + col, width=5)
s.text(9.8, 2.35, 2.7, 0.9, "under 2%", 40, RED, True)
s.text(9.8, 3.15, 2.6, 0.9, "left after 20 minutes together. About 90% false alarms.", 15, GREY)
s.text(9.8, 4.5, 2.7, 0.9, "61%", 40, INK, True)
s.text(9.8, 5.3, 2.6, 1.2, "left after 50 minutes isolated. About 50% false alarms.", 15, GREY)

# 10 ---------------------------------------------------------------- why
s = Slide("Our best explanation. The boards send very repetitive traffic. The detector was free to shrink its normal region but limited in growing it, because growth is what an attacker wants. Identical boards agree on the shrink, and our method treats agreement as a real shared change. We reproduced it in simulation with no attacker.")
s.head("Why it happened", "A guard in one direction, nothing in the other.")
for i, t in enumerate(("Traffic from identical boards is very repetitive.", "The detector may shrink “normal” freely. Growth is limited, to stop attackers.",
                       "The neighbours shrink too, so they agree.", "FOA reads agreement as real change and applies it.")):
    y = 2.35 + i * 0.95
    s.text(0.9, y, 0.7, 0.6, str(i + 1), 30, BLUE, True); s.text(1.75, y + 0.07, 10.4, 0.5, t, 22)
s.text(0.9, 6.45, 11.4, 0.4, "We reproduced the collapse in simulation, with no attacker. The placeholder feature basis may also contribute.", 15, GREY)

# 11 ---------------------------------------------------------------- fix
s = Slide("The fix is one rule: the normal region may never become smaller than it was at calibration. It cuts false alarms sharply on unseen test runs. It also showed us that most of our earlier false-alarm advantage over a single device came from the same flaw. What remains is the safety advantage. The fix has not yet been run successfully on the boards.")
s.head("One rule fixes it, and corrects our claim", "False alarms after a strong network change, on unseen test runs. Lower is better.")
s.bars(0.9, 2.1, 7.9, 4.4, ["Single device", "Single device\n+ floor", "FOA", "FOA\n+ floor"], [24.6, 0.8, 9.0, 2.5], {1, 3})
s.text(9.3, 2.4, 3.2, 0.45, "The rule", 20, bold=True)
s.text(9.3, 2.95, 3.1, 1.1, "“Normal” never shrinks below its calibrated size.", 17, GREY)
s.text(9.3, 4.35, 3.2, 0.45, "The correction", 20, bold=True)
s.text(9.3, 4.9, 3.1, 1.6, "With the floor, a single device raises fewer false alarms than FOA. FOA's real advantage is safety under change.", 17, GREY)
s.text(0.9, 6.75, 11.5, 0.35, "Validated in simulation only. A hardware run with the floor has not been completed.", 14, INK)

# 12 ---------------------------------------------------------------- limits and next
s = Slide("Where we stand honestly, and what is next. We have not attacked the physical boards, and the fix is not yet tested on them. FOA is also weak when one device changes a lot on its own, and malicious neighbours combined with a poisoner can beat borderline devices.")
s.head("What is still open")
s.text(0.9, 1.9, 5.3, 0.45, "Where it falls short", 21, bold=True)
s.text(7.1, 1.9, 5.3, 0.45, "What we do next", 21, bold=True)
for i, (a, b) in enumerate((("A big change on one device alone is learned very slowly.", "Run the floored firmware on the boards."),
                            ("Bad neighbours plus a poisoner beat borderline devices.", "Fit the feature basis on the boards' own traffic."),
                            ("Stealthy poisoners still win in some runs.", "Attack the boards: flood, freeze, slow poisoning."),
                            ("No attack has been run on hardware yet.", "Use devices that really differ as neighbours."))):
    y = 2.6 + i * 0.98
    s.line(0.9, y, 6.2, y); s.line(7.1, y, 12.43, y)
    s.text(0.9, y + 0.18, 5.2, 0.75, a, 17, GREY); s.text(7.1, y + 0.18, 5.2, 0.75, b, 17)

# 13 ---------------------------------------------------------------- close
s = Slide("To close: learn freely what the neighbours also see, ration what only you see, and test on real hardware early, because that is where we learned the most. These are the five works we build on most. Thank you, we are happy to take questions.")
s.text(0.9, 0.85, 11.5, 1.7, "Learn what neighbours see.\nRation what only you see.", 40, bold=True, spacing=1.05)
s.text(0.9, 2.85, 11, 0.45, "And test on real hardware early. That is where we learned the most.", 18, GREY)
s.line(0.9, 3.75, 12.43, 3.75)
s.text(0.9, 3.98, 4, 0.4, "Built on", 15, INK, True)
for i, r in enumerate(("Rubinstein et al., ANTIDOTE: poisoning of anomaly detectors, ACM IMC 2009",
                       "Kloft and Laskov, Security analysis of online centroid anomaly detection, JMLR 2012",
                       "Golomb, Mirsky, Elovici, CIoTA: collaborative IoT anomaly detection, NDSS DISS 2018",
                       "Meidan et al., N-BaIoT, IEEE Pervasive Computing 2018",
                       "Koumar et al., CESNET-TimeSeries24, Scientific Data 2025")):
    s.text(0.9, 4.45 + i * 0.37, 11.5, 0.35, r, 13, GREY)
s.text(0.9, 6.7, 6, 0.4, "Thank you. Questions?", 18, BLUE, True)

out = os.path.join(ROOT, "G04_FOA_Final.pptx")
prs.save(out); print("wrote", out, len(prs.slides), "slides")
if PREV:
    os.makedirs(PREV, exist_ok=True)
    sheet = Image.new("RGB", (1600 * 3 + 40, 900 * 5 + 80), "#555555")
    for i, im in enumerate(previews):
        sheet.paste(im, (i % 3 * 1620, i // 3 * 920))
    sheet.resize((sheet.width // 3, sheet.height // 3)).save(os.path.join(PREV, "sheet.png"))
