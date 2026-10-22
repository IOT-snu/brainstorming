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

# ============================================================ PAGE 1
S += [P("CSD457 INTERNET OF THINGS  ·  GROUP G-04  ·  OCTOBER 2026", "eye"),
      P('Progress report: <font color="#0071E3">Poison-Resilient</font> On-Device Intrusion Detection for Drifting IoT', "cover"),
      Spacer(1, 4), P("Rishit Kamboj and Farhan Naik  ·  Changes since the proposal deck, progress, and what we will build and test next.", "sub"),
      P("The project in one paragraph", "h2"),
      P("An IoT device that learns what normal traffic looks like can be taught, slowly, that attacks are normal. We are "
        "building a detector that <b>keeps learning on an ESP32</b> and cannot be steered that way. Our first method "
        "rationed the part of each update that moves toward a known attack. New 2026 papers prove that a detector "
        "watching one stream cannot reliably tell honest change from slow poisoning, so the next step gives each device "
        "a <b>second source of evidence: its neighbours</b>. Devices on the same network see the same honest drift; an "
        "attacker usually reaches only one."),
      P("Where we stand", "h2")]
S.append(table([["Area", "Status", "One line"],
                ["Idea and literature", ok(), "3 research rounds; 36 references compiled, 26 from 2025 to 2026 (last page)"],
                ["Method v1: Threat-Orthogonal Adaptation (TOA)", ok(), "Works on synthetic and real N-BaIoT traffic"],
                ["Method v2: signature-free version", ok(), "Beats a normal and a smart attacker on real traffic; fails if the attack hides inside strong honest drift"],
                ["Freeze attack on published defence designs", ok(), "Tested on three published gate mechanisms (simplified re-implementations): one is lockable (page 2)"],
                ["Method v3: peer-witnessed adaptation (FOA)", part("Designed"), "Mechanism and tests written; not yet implemented"],
                ["Reproducible real data", ok(), "get_nbaiot.py downloads just the files we need"],
                ["ESP32 hardware", todo(), "No measurements yet; parts list and wiring on pages 4 to 5"]],
               [5.6 * cm, 1.9 * cm, W - 7.5 * cm]))
S += [P("What changed since the proposal deck (24 September)", "h2")]
S += B(["<b>Real traffic.</b> Real N-BaIoT doorbell and Mirai packets added. Naive learning is poisoned at 10 to 20% attacker share.",
        "<b>Signature-free method</b> added, so TOA no longer needs a known attack signature. Its weakness (an attack hidden in strong "
        "honest drift) is, per three 2026 papers, a proven limit of any single-stream detector; the way out is outside evidence.",
        "<b>Novelty narrowed honestly:</b> ANTIDOTE (2009) already defends a server-side detector, and every direction we checked was "
        "only partly new, so we claim a specific combination (page 3).",
        "<b>Freeze attack now tested on published defence designs,</b> not just our own baselines."])
S += [P("Corrections and decisions", "h2"),
      P("The 10% figure holds only for the scan attack (20% for ack and syn). The 52% traffic-drop figure came from an outside analysis "
        "of the CESNET data, not from the CESNET paper. <b>We need:</b> how many ESP32 boards and INA219 modules we have, and the real "
        "mid-review and final dates.", "p")]
S.append(PageBreak())

# ============================================================ PAGE 2
S += [P("RESULTS", "eye"), P("What we have shown so far", "h1")]
S += [table([["Test", "Result"],
                ["Synthetic, attacker at 40% of traffic", "Naive: attack hidden after 24 cycles. Freeze-style defences: 85 to 87% false alarms. TOA: 100% detection, 0.3% false alarms"],
                ["Real doorbell, boundary attacker, 10 to 50% share", "Naive fails at 10% (scan) or 20% (ack, syn). TOA and signature-free: 100% detection, 0.8% to 1.5% false alarms"],
                ["Real traffic, smart attacker hiding poison in the core", "Signature-free: 100% detection, 0.2% to 0.7% false alarms"],
                ["Strong honest drift and attack together (synthetic)", "Signature-free still poisoned in 3 of 4 settings (2% to 46% detection): the open problem"],
                ["New device joins (real thermostat traffic)", "All detectors about 34% false alarms: one shared detector cannot absorb a new device"]],
               [5.6 * cm, W - 5.6 * cm]),
      P("New: the freeze attack on published defence mechanisms", "h2"),
      P("Many published defences protect themselves by <b>withholding updates when something looks suspicious</b>. We "
        "re-implemented the gating rule of three of them around our detector (simplified versions of the mechanism, not the "
        "full systems; rule details to be checked against the PDFs). The attacker sends only <b>loud decoy traffic that "
        "never poisons anything</b>. It holds a gate closed while honest drift begins, then leaves. If the detector "
        "cannot follow the drift, its own false alarms keep the gate shut."),
      ]
S += [table([["Defence mechanism", "No attacker, false alarms at the end (synthetic / real)", "After the attacker left (synthetic)", "After the attacker left (real packets)", "Verdict"],
                ["Alarm-rate switch-off (Kloft and Laskov, JMLR 2012, style)", "1.3% / 2.7%", "52%", "100%", "<b>Locked out</b>"],
                ["Outlier-ratio gate (DriftXpert, 2026, style)", "1.3% / 2.7%", "1.2%", "2.7%", "Recovers"],
                ["Score-spike rollback (T2T, 2026, style)", "1.3% / 2.7%", "1.2%", "2.7%", "Recovers"],
                ["Ours (no gate)", "1.1% / 0.8%", "1.1%", "0.8%", "Unaffected"]],
               [5.2 * cm, 2.9 * cm, 2.9 * cm, 2.9 * cm, W - 13.9 * cm]),
      Spacer(1, 3),
      P("<b>How much attacking it takes.</b> Against the alarm-rate gate, the lock-in is a threshold effect: too short a push "
        "and the gate reopens and the detector catches up. Holding the gate for about 40 cycles (synthetic) or 15 cycles "
        "(real, faster drift) locked it in <b>10 of 10 runs</b>, with decoys as low as 5% of traffic (about 200 to 600 packets). "
        "Gates whose baseline moves with the traffic (outlier ratio) or that only roll back two cycles (T2T) were not vulnerable "
        "as modelled. A fourth, confident-sample stop rule (RTTAD style), broke even with no attacker, so our simplified version "
        "says nothing about the attack and is excluded.", "p"),
      img(os.path.join(EXP, "freeze_published_real.png"), W * 0.92),
      P("Real N-BaIoT doorbell packets with an injected gradual drift; decoys are real Mirai udp packets; 5 seeds. Purple: attacker "
        "present then leaves. Grey: same gate, no attacker. Blue dashed: ours.", "small"),
      PageBreak()]

# ============================================================ PAGE 3
S += [P("DIRECTION", "eye"), P("What our research is now about", "h1"),
      KEY("Fleet of ESP32 detectors that keep learning honest change but cannot be steered, using neighbouring devices as "
          "witnesses, and measure what it costs on real hardware."),
      P("Research questions", "h2")]
S += B(["<b>RQ1.</b> Can peer witnesses let a device keep learning honest drift while resisting poisoning, where a single-stream "
        "detector provably cannot?",
        "<b>RQ2.</b> Which published defences fall to a freeze attack, and does never-stopping adaptation avoid it? "
        "(Answered in simulation; to repeat on the ESP32.)",
        "<b>RQ3.</b> What does it cost on an ESP32 in memory, latency, radio bytes and energy?"])
S += [P("Method: Fleet-Orthogonal Adaptation (FOA)", "h2"),
      P("Each device keeps its own centre-and-spread detector. Every cycle it proposes an update from the dense core of its own "
        "traffic and shares it (10 numbers, signed, about 72 bytes) with peers over ESP-NOW. The peers' geometric median is the "
        "<b>common part</b> (network-wide drift); the rest is the <b>residual</b>.")]
S += B(["Common part: applied in full, so honest drift is learned and the detector never freezes.",
        "Residual: goes through TOA's slow budget, so a campaign only one device sees is rationed.",
        "Peers differ in vendor or firmware, so one exploit cannot make several devices agree.",
        "A new device starts from its peers' median and learns under the residual budget, bounding join-time poisoning."])
S += [table([["Closest published work", "How we differ"],
                ["CIoTA (NDSS DISS 2018, JPDC 2020): same-firmware devices must agree; disagreement is discarded", "Diverse peers, so a one-exploit botnet cannot fake agreement; the disagreeing part is admitted slowly, not discarded"],
                ["WARDEN/CDC and two other 2026 theory papers: single-stream limits", "A second stream escapes them; we must prove that as our own theorem"],
                ["Gate-based defences (Kloft and Laskov, DriftXpert, T2T, OWAD)", "FOA has no stop gate; the freeze-attack study above shows why that matters"]],
               [8.4 * cm, W - 8.4 * cm]),
      P("Every candidate direction was only partly new in our prior-art checks, so the claim is a specific combination, not a first.", "small"),
      P("What we will test", "h2")]
S += [table([["#", "Test", "Against", "We win if", "Status"],
                ["1", "Attack hidden inside strong honest drift", "Signature-free single stream; WARDEN-style frozen reserve", "FOA keeps detection where single-stream fails", todo("Week 1")],
                ["2", "Monoculture botnet reaches several same-firmware peers", "CIoTA-style same-firmware consensus", "Diverse peers hold; same-firmware consensus is fooled", todo("Week 1")],
                ["3", "Freeze attack on published gates", "Kloft and Laskov, DriftXpert, T2T styles", "Gated defences lock out; FOA does not", ok("Done in sim")],
                ["4", "New device joins; adaptive attackers (core-hiding, pulsing, omission)", "One shared detector; naive", "False alarms near nominal; no attacker beats the budget", todo("Week 2")],
                ["5", "ESP32 cost: RAM, latency, radio bytes, energy", "Naive detector on the same board", "Overhead small enough to justify", todo("Week 3")]],
               [0.6 * cm, 4.6 * cm, 4.0 * cm, 4.6 * cm, W - 13.8 * cm]),
      P("Data: N-BaIoT doorbell, thermostat and cameras as peers (devices were recorded separately, so shared drift is injected and "
        "labelled synthetic); the real ESP32 fleet with a router change supplies genuine shared drift. Headline figure: under a "
        "monoculture botnet, same-firmware consensus is compromised while diverse peers hold; plus false alarms after the attacker "
        "leaves.", "small"), PageBreak()]

# ============================================================ PAGE 4: hardware diagrams
S += [P("HARDWARE", "eye"), P("IoT set-up and wiring", "h1"),
      img(os.path.join(HERE, "fig_system.png"), W * 0.84),
      P("Four ESP32 nodes with different firmware share a Wi-Fi network and gossip small signed updates over ESP-NOW. The laptop runs the "
        "MQTT broker, the poisoner and the logger. A separate ESP32 reads the INA219 on Node A.", "small"),
      Spacer(1, 4), img(os.path.join(HERE, "fig_circuit.png"), W * 0.84),
      P("Proposed wiring, not yet built. Check every pin against your module's datasheet before powering it. Default I2C pins on "
        "the ESP32 DevKitC are GPIO21 (SDA) and GPIO22 (SCL).", "small"), PageBreak()]

# ============================================================ PAGE 5: parts and plan
S += [P("PARTS AND PLAN", "eye"), P("What we need, and the next four weeks", "h1")]
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
        "per learning event, and energy per update from the INA219. Our estimate is about 1,000 multiply-adds and under 10 KB per "
        "packet on a 240 MHz, 520 KB part; that is an estimate until we measure it.", "p"),
      P("Four-week plan", "h2")]
S += [table([["Week", "Work", "Output"],
                ["1", "Implement FOA in simulation: geometric median, signed gossip, two cumulative budgets, join rule. Add the CIoTA-style baseline. Run tests 1 and 2. Read the three unread papers. Order or check parts", "FOA results in simulation"],
                ["2", "Attacker matrix and test 4. Build the headline figure and the mid-review pack. Port the detector to the ESP32 in replay mode. Wire the INA219", "First real results; board running"],
                ["3", "Bring up the ESP32 fleet with FOA over ESP-NOW. Router change as real shared drift. Measure RAM, latency, bytes and energy (test 5)", "Hardware demo and cost numbers"],
                ["4", "Proofs as a stated assumption plus the matching negative case; ablations (peer count, budget, diverse vs random peers); IEEE report, code package with README, demo", "Final deliverables"]],
               [1.3 * cm, W - 5.8 * cm, 4.5 * cm]),
      P("To fit four weeks we drop the CESNET real-drift test and a separate vendor-specific-drift test, and keep the proof minimal.", "small"),
      P("Risks and fallbacks", "h2")]
S += [table([["Risk", "Fallback"],
                ["Novelty is partial (CIoTA is close); some 2026 papers are preprints", "Claim the specific combination and win test 2; verify numbers against the PDFs before citing"],
                ["Peer concurrency on N-BaIoT is synthetic", "Let the real ESP32 router change carry the real-drift claim"],
                ["Multi-device plumbing or on-board features slip", "Ship the simpler variant that learns threat directions from its own alarms; use replay mode for cost; the freeze-attack study stands alone"],
                ["The multi-device proof is harder than it looks", "State it as an assumption plus the matching negative result"]],
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
