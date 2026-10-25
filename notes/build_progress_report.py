"""Builds Progress_Report.pdf (short version). Run: python3 progress_figs.py && python3 build_progress_report.py"""
import json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PI

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..", "experiments")
F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("A", F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("AB", F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("AI", F + "Arial Italic.ttf"))
pdfmetrics.registerFontFamily("A", normal="A", bold="AB", italic="AI", boldItalic="AB")

INK = colors.HexColor("#1D1D1F"); BLUE = colors.HexColor("#0071E3"); GRAY = colors.HexColor("#86868B")
BODY = colors.HexColor("#424245"); CARD = colors.HexColor("#F5F5F7"); GRID = colors.HexColor("#E8E8ED")

st = {
    "cover": ParagraphStyle("cover", fontName="AB", fontSize=24, leading=29, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="A", fontSize=12, leading=16.5, textColor=BODY),
    "eye": ParagraphStyle("eye", fontName="AB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="AB", fontSize=17, leading=22, textColor=INK, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="AB", fontSize=12, leading=15.5, textColor=INK, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="A", fontSize=9.8, leading=14, textColor=BODY, spaceAfter=4),
    "b": ParagraphStyle("b", fontName="A", fontSize=9.8, leading=13.5, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "small": ParagraphStyle("small", fontName="AI", fontSize=8.5, leading=11.5, textColor=GRAY, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="A", fontSize=8.6, leading=11.2, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="AB", fontSize=8.6, leading=11.2, textColor=INK),
    "ref": ParagraphStyle("ref", fontName="A", fontSize=7.8, leading=9.6, textColor=BODY),
    "refb": ParagraphStyle("refb", fontName="AB", fontSize=7.8, leading=9.6, textColor=INK),
    "key": ParagraphStyle("key", fontName="A", fontSize=9.8, leading=14, textColor=INK, backColor=CARD,
                          borderPadding=7, spaceBefore=4, spaceAfter=9, leftIndent=8, rightIndent=8),
}
def P(t, s="p"): return Paragraph(t, st[s])
def B(items): return [Paragraph(i, st["b"], bulletText="•") for i in items]
def KEY(t): return P("<b>In short:</b> " + t, "key")
def img(path, w):
    iw, ih = PI.open(path).size
    return Image(path, width=w, height=w * ih / iw)
def ok(t="Done"): return f'<font color="#248A3D"><b>{t}</b></font>'
def part(t="Partly"): return f'<font color="#B26A00"><b>{t}</b></font>'
def todo(t="Not yet"): return f'<font color="#D70015"><b>{t}</b></font>'

def table(rows, widths, head=True, ps=("cell", "cellb")):
    data = [[P(c, ps[1] if (head and r == 0) or j == 0 else ps[0]) if isinstance(c, str) else c
             for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    sty = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID),
           ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2)]
    if head: sty.append(("BACKGROUND", (0, 0), (-1, 0), CARD))
    t.setStyle(TableStyle(sty))
    return t

def footer(c, d):
    c.saveState(); c.setFont("A", 8); c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, "Group G-04  ·  Progress report  ·  Poison-Resilient On-Device Intrusion Detection for Drifting IoT")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(d.page)); c.restoreState()

doc = BaseDocTemplate(os.path.join(HERE, "Progress_Report.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.7 * cm, bottomMargin=1.8 * cm, title="G-04 Progress report",
                      author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 1.8 * cm, A4[0] - 4 * cm, A4[1] - 3.5 * cm)], onPage=footer)])
W = A4[0] - 4 * cm
S = []

# numbers come from the paper's generated macros, so report and paper always agree
import re
NUM = {k: v.replace("\\%", "%").replace("\\,", " ").replace("{,}", ",")
       for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(HERE, "..", "paper", "numbers.tex")).read())}
FIGS = os.path.join(EXP, "foa", "figures")

# ============================================================ PAGE 1
S += [P("CSD457 INTERNET OF THINGS  ·  GROUP G-04  ·  OCTOBER 2026", "eye"),
      P('Progress report: <font color="#0071E3">Fleet-Orthogonal Adaptation</font>, poison-resilient on-device intrusion detection for drifting IoT', "cover"),
      Spacer(1, 4), P("Rishit Kamboj and Farhan Naik  ·  What we built and measured, what it shows, and what the hardware will add.", "sub"),
      P("The project in one paragraph", "h2"),
      P("An IoT device that learns what normal traffic looks like can be taught, slowly, that attacks are normal; and a defence that "
        "stops learning when traffic looks suspicious can be frozen. From one device's traffic alone, honest change and slow "
        "poisoning cannot be told apart. Our method, <b>Fleet-Orthogonal Adaptation (FOA)</b>, uses the device's neighbours as a "
        "second witness: the part of an update that vulnerability-diverse peers also see is learned in full, the device-only rest "
        "is admitted through a budget that never closes. It is implemented, tested on all nine N-BaIoT devices and on 40 weeks of "
        "real CESNET traffic, written up as an IEEE-format paper, and ported to ESP32 firmware that is waiting for the boards."),
      P("Where we stand", "h2")]
S.append(table([["Area", "Status", "One line"],
                ["Method (FOA) and theory", ok(), "Algorithm, four results with proofs (containment, Byzantine bound, frontier, no freeze state)"],
                ["Simulation on real traffic", ok(), "All 9 N-BaIoT devices, 8 baselines, 12 attacker types, about 19,500 fleet runs, held-out seeds"],
                ["Real drift", ok(), "40 weeks of CESNET traffic, 12 addresses of one institution"],
                ["Freeze attack", ok(), "Shown on the alarm-rate switch-off; FOA provably and measurably immune"],
                ["Paper", ok(), "paper/main.pdf, 11 pages, every number generated from the results"],
                ["ESP32 firmware", part("Built, not run"), "Compiles; matches the Python reference on every recorded cycle; adds about 22 KB flash"],
                ["ESP32 measurements", todo(), "Latency, energy and radio loss need the boards"]],
               [5.0 * cm, 2.4 * cm, W - 7.4 * cm]))
S += [P("Main results", "h2")]
S += B([f"<b>Following honest drift.</b> Under strong network-wide drift FOA ends at <b>{NUM['FOAFleetFPR']}</b> false alarms; a single "
        f"device learning alone {NUM['AutoFleetFPR']}, defences that pause learning {NUM['GateFleetFPR']}, a detector that never learns {NUM['StrongStaticFPR']}.",
        f"<b>Poisoning hidden inside drift.</b> Compromised overall: FOA <b>{NUM['FOAComp']}</b>, single device {NUM['AutoComp']}. "
        f"The classic slow poisoner never beat FOA ({NUM['FOABoundaryComp']}).",
        f"<b>Monoculture botnet.</b> Same-model consensus (CIoTA style) {NUM['MonoCiotaThree']} compromised once most cameras of a model are "
        f"infected; FOA with diverse peers {NUM['MonoFOAThree']}.",
        f"<b>Freeze attack.</b> 5% decoy traffic locks an alarm-rate switch-off at <b>{NUM['KLFrozenFPR']}</b> false alarms for good; FOA unchanged.",
        f"<b>Real CESNET drift.</b> FOA compromised in {NUM['CesFOAComp']} of runs, single device {NUM['CesAutoComp']}.",
        f"<b>Bound.</b> The proven minimum time to compromise held in every attacked FOA run ({NUM['BoundViolations']} violations)."])
S.append(PageBreak())

# ============================================================ PAGE 2
S += [P("RESULTS", "eye"), P("Two figures that carry the story", "h1"),
      img(os.path.join(FIGS, "fig_headline.png"), W),
      P("Poisoning hidden inside strong shared drift, 7 victims, 10 held-out seeds. (a) Boundary poisoner: FOA is never compromised. "
        "(b) FOA alone is low on both compromise and false alarms. (c) Detection of the target attack over time.", "small"),
      Spacer(1, 6), img(os.path.join(FIGS, "fig_liveness.png"), W),
      P("False alarms with no attacker. Shared drift is followed through the peers; drift on one device only is admitted at the "
        "budget rate, the trade-off the theory says no rule can avoid.", "small"),
      P("What goes against us (reported in the paper)", "h2")]
S += B([f"A device whose own traffic changes a lot, on top of shared drift, is lost by FOA (single-device adaptation keeps it): device-only drift "
        f"ends at {NUM['FOAIdioFPR']} false alarms for FOA against {NUM['AutoIdioFPR']}.",
        f"Malicious peers alone never compromised anyone, but helping a traffic poisoner they beat borderline victims: {NUM['ByzTH']} with "
        f"three of seven peers.",
        f"Core-hiding and mimicry poisoners at 40% share still win about a third of the time ({NUM['FOACoreHigh']}, {NUM['FOAMimicHigh']}).",
        "Fleet concurrency, the N-BaIoT drift and the poisoner are simulated; hardware numbers are estimates."])
S.append(PageBreak())

# ============================================================ PAGE 3
S += [P("METHOD AND FIRMWARE", "eye"), P("How FOA works and what is ready for the boards", "h1"),
      KEY("Learn freely what the neighbours also see; ration what only this device sees; never stop learning."),
      img(os.path.join(HERE, "..", "paper", "fig_system_preview.png"), W) if os.path.exists(os.path.join(HERE, "..", "paper", "fig_system_preview.png")) else Spacer(1, 1),
      P("Firmware status", "h2")]
S += [table([["Check", "Result"],
                ["C core vs Python reference, 480 recorded cycles", "0 mismatches"],
                ["Tampered gossip frames accepted (bit flips, wrong keys, replays)", "0 of 23,104"],
                ["HMAC-SHA256, RFC 4231 test vector", "pass"],
                ["Node firmware for ESP32 (Arduino core 3.3.12)", "915 KB flash, 69 KB RAM; FOA's own share about 22 KB / 20 KB"],
                ["Power monitor (INA219, no library)", "compiles; about 1 kHz samples"],
                ["Laptop tools", "poisoner (boiling frog, pulse, decoy, flood) and collector (latency, peers, mJ per cycle)"]],
               [8.0 * cm, W - 8.0 * cm]),
      P("Hardware-day steps are in firmware/README.md: wire the INA219, fix the router channel, flash four nodes, record 20 minutes "
        "of clean traffic to fit the shared space, then run idle, drift, poisoning and freeze sessions.", "small"),
      PageBreak()]

# ============================================================ PAGE 4: hardware diagrams
S += [P("HARDWARE", "eye"), P("IoT set-up and wiring", "h1"),
      img(os.path.join(HERE, "fig_system.png"), W * 0.84),
      P("Four ESP32 nodes with different firmware share a Wi-Fi network and gossip small signed updates over ESP-NOW. The laptop runs the "
        "MQTT broker, the poisoner and the logger. A separate ESP32 reads the INA219 on Node A.", "small"),
      Spacer(1, 4), img(os.path.join(HERE, "fig_circuit.png"), W * 0.84),
      P("Proposed wiring, not yet built. Check every pin against your module's datasheet before powering it. Default I2C pins on "
        "the ESP32 DevKitC are GPIO21 (SDA) and GPIO22 (SCL).", "small"), PageBreak()]

# ============================================================ PAGE 5: parts and plan
S += [P("PARTS AND PLAN", "eye"), P("What we need, and what comes next", "h1")]
S += [table([["Item", "Qty", "Why"],
                ["ESP32 development boards (for example ESP32-DevKitC)", "4, plus 1 for monitoring", "Fleet nodes A to D and the power monitor"],
                ["INA219 current-sensor module, 5 V supply or USB breakout", "1 to 2", "Measures a node's power and energy"],
                ["BME280 or DHT22 sensor (optional)", "1 per node", "Gives each node real telemetry to send"],
                ["Breadboard, jumpers, 4.7 kohm resistors, USB cables and hub", "1 set", "Wiring, I2C pull-ups, flashing, serial logs"],
                ["Wi-Fi router on a fixed channel; laptop", "1 each", "ESP-NOW and Wi-Fi share one channel; laptop runs broker, poisoner, logger"]],
               [8.2 * cm, 3.0 * cm, W - 11.2 * cm]),
      P("Software: ESP-IDF or the Arduino core (ESP-NOW and mbedTLS HMAC are standard), Python and NumPy, Mosquitto, and our experiment "
        "scripts. Two run modes: <b>replay</b> (N-BaIoT features fed over serial, for reliable cost numbers) and <b>live</b> (the "
        "board's own telemetry). Measured on the board: peak RAM and flash, latency per update and per signed message, ESP-NOW bytes "
        "per learning event, and energy per update from the INA219. The firmware already logs the time of every stage; our current "
        "figure (about 2 ms of compute per 10 s learning cycle) is an estimate until we measure it.", "p"),
      P("Next steps", "h2")]
S += [table([["When", "Work", "Output"],
                ["Boards arrive", "Flash four nodes and the monitor; fit the shared basis on clean testbed traffic; idle baseline", "Real latency, RAM, bytes, energy per cycle"],
                ["Week after", "Real shared drift (a router or telemetry change on every node); laptop poisoner; decoy freeze test", "FOA on real hardware with real drift"],
                ["Before submission", "Independent code review; read the three unread preprints; replace estimates in the paper with measurements", "Final paper and demo"]],
               [2.6 * cm, W - 7.1 * cm, 4.5 * cm]),
      P("Risks and fallbacks", "h2")]
S += [table([["Risk", "Fallback"],
                ["Novelty is partial (CIoTA is close); several 2026 papers are preprints", "We beat CIoTA-style consensus head to head; claims say 'we found no prior work', never 'first'"],
                ["Simulated concurrency and drift on N-BaIoT", "CESNET supplies real drift; the testbed supplies a real shared change"],
                ["ESP-NOW and Wi-Fi on one channel misbehave", "Fall back to UDP gossip through the router (same frames, same HMAC)"]],
               [6.2 * cm, W - 6.2 * cm]),
      PageBreak()]

# ============================================================ PAGE 6: references
refs = json.load(open(os.path.join(HERE, "..", "research", "references.json")))
def short(t):
    t = t.split(" (")[0]
    t = t.split(": ")[0] if len(t.split(": ")[0]) > 22 else t
    return t if len(t) <= 78 else t[:75] + "..."
S += [P("REFERENCES", "eye"), P("Compiled references, newest first", "h1"),
      P("36 references, 26 from 2025 to 2026. Full list with links, reading status and one line on why each matters: "
        "<b>references.md</b> in the repository. <b>Read</b> says how much we actually read; preprints are not peer-reviewed, so check "
        "numbers against the PDF.", "small")]
rows = [["Year", "Paper", "Type", "Read"]]
for r in refs:
    name = ("<b>CORE</b> " if r["core"] else "") + short(r["title"])
    rd = {"full text": "full", "abstract": "abstract", "abstract only": "abstract", "abstract and method": "partial",
          "abstract and key sections": "partial", "dataset paper": "dataset", "found in prior-art check": "partial"}.get(r["read"], "not read")
    rows.append([str(r["year"]), name, "peer-reviewed" if r["status"].startswith("peer") else "preprint", rd])
data = [[Paragraph(c, st["refb" if (i == 0 or j == 0) else "ref"]) for j, c in enumerate(row)] for i, row in enumerate(rows)]
t = Table(data, colWidths=[1.2 * cm, W - 5.6 * cm, 2.4 * cm, 2.0 * cm], repeatRows=1)
t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, GRID),
                       ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
                       ("BACKGROUND", (0, 0), (-1, 0), CARD)]))
S.append(t)

doc.build(S)
print("wrote", os.path.join(HERE, "Progress_Report.pdf"))
