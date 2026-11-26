"""Builds G04_Project_Explained.pdf: the whole project for a reader who knows nothing about it.
Run: python3 demo/build_explainer.py"""
import os
from PIL import Image as PI
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, Image, CondPageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
F = "/System/Library/Fonts/Supplemental/"
for n, f in (("A", "Arial.ttf"), ("AB", "Arial Bold.ttf"), ("AI", "Arial Italic.ttf")):
    pdfmetrics.registerFont(TTFont(n, F + f))
pdfmetrics.registerFontFamily("A", normal="A", bold="AB", italic="AI", boldItalic="AB")
INK, BLUE, GREY, SOFT, LINE = [colors.HexColor(c) for c in ("#1D1D1F", "#0071E3", "#6E6E73", "#F5F5F7", "#E3E3E8")]
S_ = lambda n, **k: ParagraphStyle(n, **{**dict(fontName="A", fontSize=10.2, leading=15, textColor=INK, spaceAfter=5), **k})
title, sub = S_("t", fontName="AB", fontSize=27, leading=33), S_("s", fontSize=12.5, leading=17, textColor=GREY)
h1 = S_("h1", fontName="AB", fontSize=16.5, leading=21, spaceBefore=16, spaceAfter=7)
h2 = S_("h2", fontName="AB", fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=3)
p, small = S_("p"), S_("sm", fontSize=8.6, leading=11.5, textColor=GREY)
note = S_("n", backColor=SOFT, borderPadding=8, leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=12)
b = S_("b", leftIndent=14, bulletIndent=3, spaceAfter=3)
cell, cellb = S_("c", fontSize=9, leading=12, spaceAfter=0), S_("cb", fontName="AB", fontSize=9, leading=12, spaceAfter=0)
W = A4[0] - 4.2 * cm
S = []
P = lambda t, s=p: S.append(Paragraph(t, s))
H = lambda t: S.extend([CondPageBreak(4.5 * cm), Paragraph(t, h1)])
H2 = lambda t: S.extend([CondPageBreak(2.5 * cm), Paragraph(t, h2)])
B = lambda items: S.extend(Paragraph(i, b, bulletText="•") for i in items)


def T(rows, widths):
    t = Table([[Paragraph(c, cellb if i == 0 or j == 0 else cell) for j, c in enumerate(r)] for i, r in enumerate(rows)], colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, 0), SOFT),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    S.extend([t, Spacer(1, 8)])


def fig(path, caption, w=1.0):
    path = os.path.join(ROOT, path); iw, ih = PI.open(path).size
    S.append(KeepTogether([Image(path, width=W * w, height=W * w * ih / iw), Paragraph(caption, small), Spacer(1, 6)]))


P("Our project, explained from zero", title)
P("A detector for smart devices that keeps learning without being easily fooled", sub)
P("Rishit Kamboj and Farhan Naik  ·  Group G-04  ·  CSD457 Internet of Things  ·  November 2026", small)
P("<b>The whole story in one paragraph.</b> Smart devices need to notice when something attacks them. A program that learns what is normal for a device must keep learning, "
  "because normal changes. But a patient attacker can teach it bad habits. We built a method where each device asks its neighbours: if they see the same change, accept it; "
  "if only this device sees it, accept it slowly. It worked well in computer simulation on real recorded traffic. On real boards we found a flaw, understood it, and designed a "
  "fix that works in simulation but has not yet been confirmed on the boards.", note)

H("1. The background, in plain words")
P("An <b>IoT device</b> is an everyday object with a small computer and a network connection: a camera, a doorbell, a thermostat. They are often weakly protected. "
  "Real malware such as <b>Mirai</b> and <b>BASHLITE</b> takes over many of them and uses them to attack others.")
P("An <b>intrusion detection system</b> watches network traffic and raises an alarm when something looks wrong. Ours is an <b>anomaly detector</b>: it is not told what attacks look like. "
  "It learns what <i>normal</i> looks like and flags anything too far from it. Picture a circle drawn around typical behaviour: inside is normal, outside raises an alarm. "
  "The circle has a <b>centre</b> (typical behaviour) and a <b>size</b> (how much variation is acceptable).")
H("2. The problem")
T([["Choice", "What goes wrong"],
   ["Never update the circle", "Normal behaviour moves (this is called <b>drift</b>), so the device raises alarms all the time. In our test, 78% of normal traffic was flagged."],
   ["Update it from whatever looks normal", "An attacker sends traffic just inside the edge, bit by bit, dragging the circle toward the attack. This is <b>poisoning</b>, nicknamed the boiling frog."],
   ["Stop updating when things look suspicious", "The attacker makes things look suspicious, then leaves. The detector stays stuck. We call this the <b>freeze attack</b>."]], [4.6 * cm, W - 4.6 * cm])
P("Recent research argues that from one device's own traffic, honest change and slow poisoning can be impossible to tell apart.")

H("3. Our idea")
P("Use <b>neighbouring devices as witnesses</b>. A router change affects everyone. A hacker's trick usually affects only the devices it works on. So each device:")
B(["works out how it would like to update its circle;",
   "sends that proposal to its neighbours in a tiny signed message (92 bytes);",
   "finds the <b>robust middle</b> of the neighbours' proposals (the geometric median), which a minority of liars cannot drag far;",
   "applies the <b>shared part</b> in full, and lets its own <b>leftover part</b> through only within a budget that grows slowly."])
P("It never switches learning off, so there is nothing for a freeze attack to trigger. Neighbours should be from <b>different makers</b>, so one trick cannot fool them all. "
  "We named the method <b>Fleet-Orthogonal Adaptation (FOA)</b>.")
fig("paper/fig_system_preview.png", "How the method works: shared change flows through the neighbours; change seen by one device is rationed.")
P("We also proved mathematically that an attacker who controls only one device's traffic can move its circle only a limited amount in a given time. We cannot solve one case: "
  "if only one device changes, nobody can know whether that change is honest.")

H("4. How we got here")
T([["Step", "What we did", "What we learned"],
   ["Reading", "Several rounds of literature search; compiled 36 references", "Poisoning of detectors was known since 2009; peers had been used in 2018 (CIoTA)"],
   ["Version 1", "Slow only the learning that moves toward a known attack", "Needs to know the attack beforehand"],
   ["Version 2", "Learn only from the central, clearly normal traffic", "Fooled when an attack hides inside a large honest change"],
   ["Version 3 (FOA)", "Add neighbours as witnesses", "The version we evaluated"]], [2.8 * cm, 6.4 * cm, W - 9.2 * cm])

H("5. How we tested it on a computer")
H2("The data")
B(["<b>N-BaIoT:</b> real traffic recorded from nine commercial IoT devices, normal and while infected with Mirai and BASHLITE. Each packet is described by 115 statistics.",
   "<b>CESNET-TimeSeries24:</b> 40 weeks of real traffic statistics from a research network, with natural change."])
H2("The simulation")
P("We wrote a program in Python that replays this traffic to a group of virtual devices in learning cycles. We compressed each sample to 16 numbers so devices could compare notes. "
  "We added what the recordings do not contain, and we say so: the devices running together, network changes on N-BaIoT (more packets, extra bytes, jitter), and an attacker who "
  "slips poisoned samples into one device's learning.")
H2("Keeping it fair")
B(["We compared against other approaches built on the same detector: never learn, learn everything, single device, limiting each step, a frozen reference, stopping on alarms, and same-model voting.",
   "Design decisions used two practice runs; reported results use ten different runs.",
   "Every attacked run was paired with the same run without the attacker, so natural change is not counted as a successful attack.",
   "Some devices were excluded as targets because their attack traffic already looked almost normal."])
H2("Results")
T([["Situation", "Our method", "Comparison"],
   ["False alarms after a large network change", "9.0%", "single device 24.6%; never learning 78%"],
   ["Attack hidden inside that change: runs fooled", "10.8%", "single device 39.2%"],
   ["Classic slow poisoner: runs fooled", "0%", "single device up to 84%"],
   ["Most cameras of one model infected: fooled", "0%", "same-model voting 100%"],
   ["Freeze attack", "unaffected", "a stop-on-alarms defence stuck at 100% false alarms"],
   ["40 weeks of real change: fooled", "0%", "single device 18%"]], [7.2 * cm, 2.7 * cm, W - 9.9 * cm])
fig("experiments/foa/figures/fig_headline.png", "Attacks hidden inside network change, before the later fix.")
P("Weaknesses seen in simulation: a device that changes a lot by itself is learned slowly; lying neighbours combined with an attacker can win; careful attackers sometimes succeed.")

H("6. How we built it on real hardware")
T([["Part", "Role"],
   ["Three ESP8266 NodeMCU boards", "Small Wi-Fi microcontrollers that each run the detector"],
   ["Phone hotspot", "The shared network"],
   ["ESP-NOW", "A radio method that lets boards send short messages straight to each other"],
   ["INA226 sensor", "Measures the electricity one board uses, wired into its USB power line"],
   ["Laptop", "Records every board's output and can send attack traffic"]], [5.2 * cm, W - 5.2 * cm])
P("We rewrote the core of the method in the C language for the boards and checked that it gives the same results as the Python version, and that tampered messages are rejected.")
H2("Problems we hit and fixed")
T([["What we saw", "Cause and fix"],
   ["The detector stopped learning immediately", "It judged normal before its traffic statistics had settled. Added a 3 minute warm-up."],
   ["Boards heard each other but rejected messages", "We required identical cycle numbers, impossible when boards start at different times. Now each sender's number only has to increase."],
   ["The power sensor was not found", "It answered at a different address than expected. The program now searches for it."],
   ["Recording failed on Windows", "Odd start-up characters broke the logger. Fixed the text encoding."],
   ["A board kept restarting", "A loose power wire."]], [6 * cm, W - 6 * cm])
H2("What we measured")
B(["Boards heard both neighbours in 97 to 100% of cycles.",
   "Working out an update took about 11 ms and combining it about 1.6 ms, in a cycle of about 7.8 seconds.",
   "A board drew about 365 mW. Any extra energy for learning was too small for the sensor to detect."])

H("7. The surprise: it failed on the boards")
P("Within 20 minutes every board's circle shrank to <b>under 2%</b> of its starting size, and about <b>90%</b> of normal traffic raised alarms.")
fig("experiments/hardware/hardware_results.png", "The recorded board runs: false alarms (top) and circle size (bottom).", 0.92)
P("<b>Why we think it happened.</b> Identical boards send very repetitive traffic. The detector was free to shrink its circle but limited in growing it, because growth is what an attacker wants. "
  "The boards shrank together, and the method read their agreement as real change. When boards could not hear each other, shrinking was far slower (61% of the size left after 50 minutes), "
  "which supports this but was not a controlled comparison. We also reproduced a collapse in simulation. A setup detail (a stand-in way of compressing the traffic) may add to it.")

H("8. The fix and what it changed")
P("One rule: <b>the circle may never become smaller than it was at the start.</b> On fresh simulation runs:")
T([["", "Single device", "Single + fix", "Ours", "Ours + fix"],
   ["False alarms after large change", "24.6%", "0.8%", "9.0%", "2.5%"],
   ["Runs fooled during large change", "39.2%", "43.1%", "10.8%", "9.4%"]], [5.6 * cm] + [(W - 5.6 * cm) / 4] * 4)
P("<b>An honest correction.</b> With the fix, a single device raises <i>fewer</i> false alarms than our method. What remains true is that our method is much harder to fool during a change. "
  "Our attempts to confirm the fix on the boards did not succeed, because the boards ran the older program. So the fix is <b>shown in simulation only</b>.", note)

H("9. What is and is not established")
T([["Established", "Not established"],
   ["Simulation results on real recorded traffic", "Behaviour when real devices of different makers run together"],
   ["The boards communicate and compute within their limits", "Any attack test on the boards"],
   ["The collapse, measured on real boards", "That the fix works on the boards"]], [W / 2, W / 2])
P("Next steps: run the fixed program on the boards, tune the traffic compression to their own data, run attacks on them, and use genuinely different devices as neighbours.")

H("10. Where everything is")
T([["Item", "File or folder"], ["Research paper", "paper/main.pdf"], ["Presentation", "G04_FOA_Final.pptx"], ["Question practice", "G04_Viva_Prep.pdf"],
   ["Simulator and experiments", "experiments/foa (README.md, RESEARCH_LOG.md)"], ["Board recordings", "experiments/hardware"], ["Board programs and wiring", "firmware (build_guide)"],
   ["References", "references.md"], ["Repository", "github.com/IOT-snu/brainstorming"]], [5.2 * cm, W - 5.2 * cm])
H("Word list")
T([["Word", "Meaning"], ["Drift", "Normal behaviour changing over time"], ["Poisoning", "Feeding misleading data to a learning program"], ["False alarm", "Normal traffic flagged as an attack"],
   ["Fooled / compromised", "The attack being tested mostly goes unnoticed"], ["Neighbour / peer", "Another device whose proposal is used as a witness"], ["Budget", "A slowly growing limit on how far one device may move by itself"],
   ["Signed message", "A message with a code proving who sent it and that it was not altered"], ["Simulation", "A computer imitation of the system"], ["Firmware", "The program stored on a board"]], [4.4 * cm, W - 4.4 * cm])


def foot(c, d):
    c.setFont("A", 8); c.setFillColor(GREY); c.drawString(2.1 * cm, 1.1 * cm, "G-04  ·  The project explained"); c.drawRightString(A4[0] - 2.1 * cm, 1.1 * cm, str(d.page))


doc = BaseDocTemplate(os.path.join(ROOT, "G04_Project_Explained.pdf"), pagesize=A4, title="G-04: the project explained", author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2.1 * cm, 1.7 * cm, W, A4[1] - 3.4 * cm)], onPage=foot)])
doc.build(S); print("wrote G04_Project_Explained.pdf")
