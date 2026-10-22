"""Builds Progress_Report.pdf. Run: python3 progress_figs.py && python3 build_progress_report.py"""
import os
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
GREEN = colors.HexColor("#248A3D"); RED = colors.HexColor("#D70015"); AMBER = colors.HexColor("#B26A00")

st = {
    "cover": ParagraphStyle("cover", fontName="AB", fontSize=26, leading=31, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="A", fontSize=12.5, leading=17, textColor=BODY),
    "eye": ParagraphStyle("eye", fontName="AB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="AB", fontSize=18, leading=23, textColor=INK, spaceAfter=7),
    "h2": ParagraphStyle("h2", fontName="AB", fontSize=12.5, leading=16, textColor=INK, spaceBefore=9, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="A", fontSize=10, leading=14.5, textColor=BODY, spaceAfter=5),
    "b": ParagraphStyle("b", fontName="A", fontSize=10, leading=14, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "small": ParagraphStyle("small", fontName="AI", fontSize=8.5, leading=11.5, textColor=GRAY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="A", fontSize=8.8, leading=11.5, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="AB", fontSize=8.8, leading=11.5, textColor=INK),
    "key": ParagraphStyle("key", fontName="A", fontSize=10, leading=14.5, textColor=INK, backColor=CARD,
                          borderPadding=8, spaceBefore=5, spaceAfter=11, leftIndent=8, rightIndent=8),
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

def table(rows, widths, head=True):
    data = [[P(c, "cellb" if (head and r == 0) or j == 0 else "cell") if isinstance(c, str) else c
             for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    sty = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID),
           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if head: sty.append(("BACKGROUND", (0, 0), (-1, 0), CARD))
    t.setStyle(TableStyle(sty))
    return t

def footer(c, d):
    c.saveState(); c.setFont("A", 8); c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, "Group G-04  ·  Progress report  ·  Poison-Resilient On-Device Intrusion Detection for Drifting IoT")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(d.page)); c.restoreState()

doc = BaseDocTemplate(os.path.join(HERE, "Progress_Report.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.9 * cm, title="G-04 Progress report",
                      author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 1.9 * cm, A4[0] - 4 * cm, A4[1] - 3.7 * cm)], onPage=footer)])
W = A4[0] - 4 * cm
S = []

# ------------------------------------------------------------------ Page 1: summary
S += [P("CSD457 INTERNET OF THINGS  ·  GROUP G-04  ·  OCTOBER 2026", "eye"),
      P('Progress report: <font color="#0071E3">Poison-Resilient</font> On-Device Intrusion Detection for Drifting IoT', "cover"),
      Spacer(1, 6), P("Rishit Kamboj and Farhan Naik  ·  What has changed since the proposal deck, what is done, "
                      "and exactly what we will build, test and measure next.", "sub"), Spacer(1, 8),
      P("The project in one paragraph", "h2"),
      P("An IoT device that learns what normal traffic looks like can be taught, slowly, that attacks are normal. "
        "We are building a detector that <b>keeps learning on an ESP32</b> and cannot be steered that way. Our "
        "first method rationed only the part of each update that moves toward a known attack. New 2026 papers "
        "prove that a detector watching a single stream cannot reliably separate honest change from slow "
        "poisoning, so our next step gives each device a <b>second source of evidence: its neighbours</b>. "
        "Devices that share the same network see the same honest drift; an attacker usually reaches only one."),
      P("Where we stand", "h2")]
S.append(table([["Area", "Status", "One line"],
                ["Idea and literature", ok(), "3 research rounds; 2024 to 2026 papers read; novelty checked against prior work"],
                ["Method v1: Threat-Orthogonal Adaptation (TOA)", ok(), "Works on synthetic and on real N-BaIoT traffic"],
                ["Method v2: signature-free version", ok(), "Beats a normal and a smart attacker on real traffic; fails when the attack hides inside strong honest drift"],
                ["Method v3: peer-witnessed adaptation (FOA)", part("Designed"), "Mechanism and plan written; not yet implemented or tested"],
                ["Freeze attack on published defences", part("Partly"), "Shown on our own baselines; not yet on published ones"],
                ["ESP32 hardware", todo(), "No measurements yet. Parts list and wiring are in this report"],
                ["Report and code package", part("Partly"), "Repository, notes and figures exist; IEEE report not started"]],
               [5.4 * cm, 2.2 * cm, W - 7.6 * cm]))
S += [Spacer(1, 6), KEY("The core idea is proven in simulation and on one real device's traffic. What remains is the part "
                        "that makes it a research result: the peer mechanism, comparison with published defences, and "
                        "real ESP32 measurements.")]
S += [P("Decisions we need from you", "h2")]
S += B(["How many ESP32 boards and INA219 modules we actually have, and whether we buy more.",
        "The real mid-review and final dates, so the weeks above can be pinned to them.",
        "Whether to keep the title or add the method name."])

S.append(PageBreak())

# ------------------------------------------------------------------ Page 2: changes since proposal deck
S += [P("PART 1", "eye"), P("What changed since the proposal deck", "h1"),
      P("The proposal deck (24 September) presented one method, TOA, backed by a synthetic simulation.")]
S.append(table([["", "Proposal deck", "Now"],
                ["Method", "TOA: ration movement toward a <i>known attack signature</i>", "Signature-free version added (learns from the dense core of traffic; accepts a shift only if the outer ring backs it). Next: peer-witnessed version (FOA)"],
                ["Evidence", "Synthetic simulation only", "Plus real N-BaIoT doorbell traffic and real Mirai attacks (scan, ack, syn); attacker is modelled"],
                ["Poisoning risk", "Estimated from the theory of attacker share", "Measured on real traffic: naive learning fails at 10% attacker share (scan) or 20% (ack, syn)"],
                ["Main weakness", "Needs a signature for each attack", "Removed by the signature-free version. New weakness: an attack hidden inside strong honest drift is still not stopped"],
                ["Understanding of that weakness", "Open question", "Three 2026 papers prove it is a <b>limit for any single-stream detector</b>. The way out is extra evidence from outside the stream"],
                ["New devices", "Not considered", "A device joining mid-stream gave about 34% false alarms for every detector. Fix: one detector per device that starts from its peers"],
                ["Novelty claim", "Peer-free defence", "Corrected: ANTIDOTE (2009) already defends a server-side detector. Our claim is now narrower and defensible (see Part 3)"],
                ["Literature", "5 core papers", "5 core plus 24 papers from 2024 to 2026, with prior-art checks on each candidate direction"]],
               [3.2 * cm, 5.0 * cm, W - 8.2 * cm]))
S += [Spacer(1, 6), P("Corrections we made along the way", "h2")]
S += B(["The claim that naive learning is poisoned at 10% attacker share held only for the Mirai scan attack. For ack and "
        "syn it takes 20%. All documents now say 10 to 20%.",
        "A claim that traffic fell 52% at semester end came from an outside analysis of the CESNET data, not from the "
        "CESNET paper itself. It should be worded accordingly or dropped.",
        "The novelty claim was narrowed after we found ANTIDOTE, and again after the 2026 impossibility papers."])
S.append(PageBreak())

# ------------------------------------------------------------------ Page 3: progress and results
S += [P("PART 2", "eye"), P("Progress and results so far", "h1"),
      P("What we built", "h2")]
S += B(["<b>Detector:</b> unsupervised online centroid detector (centre and spread) on PCA-compressed Kitsune-style features. "
        "It labels its own traffic and updates every cycle.",
        "<b>Attacker:</b> boiling-frog poisoner that places poison just inside the alarm boundary toward a target attack. "
        "On real data each poison packet mixes a real normal packet with a real attack packet.",
        "<b>Defences compared:</b> static, naive adaptive, consistency gate, freeze budget, TOA, signature-free TOA.",
        "<b>Code:</b> <font name='AB'>experiments/sim_toa.py</font>, <font name='AB'>nbaiot_check.py</font>, "
        "<font name='AB'>auto_toa.py</font> in the repository."])
S += [P("Key results", "h2")]
S.append(table([["Test", "Result"],
                ["Synthetic, attacker at 40% of traffic", "Naive: attack hidden after 24 cycles. Freezing defences: 85 to 87% false alarms. TOA: 100% detection, 0.3% false alarms"],
                ["Real doorbell traffic, boundary attacker", "Naive fails at 10% share (scan) and 20% (ack, syn). TOA and signature-free: 100% detection, about 0.8% to 1.5% false alarms, at 10 to 50% share"],
                ["Real traffic, smart attacker hiding poison in the core", "Signature-free version: 100% detection, 0.2% to 0.7% false alarms. A first attempt failed here; adding the outer-ring check on spread growth fixed it"],
                ["Synthetic, strong honest drift and attack together", "Signature-free version is still poisoned in three of the four settings tried (2% to 46% detection). This is the open problem"],
                ["New device joins (real thermostat traffic)", "All detectors about 34% false alarms even with no attacker: one shared self-learning detector cannot absorb a new device"]],
               [5.3 * cm, W - 5.3 * cm]))
S += [Spacer(1, 5), img(os.path.join(EXP, "nbaiot_results.png"), W * 0.92),
      P("Real N-BaIoT Danmini doorbell and Mirai scan traffic, modelled poisoner at 10% share, 5 seeds. The thick blue line "
        "(ours) stays at 100% detection while naive learning (red) loses the attack.", "small"),
      P("What the results do not show yet", "h2")]
S += B(["Anything on a microcontroller. All runs so far are Python on a laptop.",
        "The freeze attack on real long-term drift or on published defences.",
        "More than one device's traffic as peers. The peer mechanism has not been implemented.",
        "A real attacker. The poisoner is modelled because no public dataset contains poisoning."])
S.append(PageBreak())

# ------------------------------------------------------------------ Page 4: what the research is
S += [P("PART 3", "eye"), P("What our research is now about", "h1"),
      KEY("Make a fleet of ESP32 detectors that keep learning honest change but cannot be steered by an attacker, by "
          "letting neighbouring devices act as witnesses, and measure what that costs on real hardware."),
      P("Research questions", "h2")]
S += B(["<b>RQ1.</b> Can peer witnesses let a device keep learning honest drift while resisting poisoning, in cases where "
        "a single-stream detector provably cannot?",
        "<b>RQ2.</b> Do published defences that stop or gate learning fall to a freeze attack, and does never-stopping "
        "adaptation avoid it?",
        "<b>RQ3.</b> What does it cost on an ESP32 in memory, latency, radio bytes and energy, and how much does it slow "
        "legitimate adaptation?"])
S += [P("The method: Fleet-Orthogonal Adaptation (FOA)", "h2"),
      P("Each device keeps its own centre-and-spread detector. Every cycle it proposes an update from the dense core of its "
        "own traffic and shares that small proposal (10 numbers, signed) with its peers over ESP-NOW. The peers' "
        "robust consensus (their geometric median) is the <b>common part</b>: network-wide drift such as a router "
        "change or a daily cycle. The rest is the <b>residual</b>."),
      ]
S += B(["The common part is applied in full, so honest drift is learned and the detector never freezes.",
        "The residual goes through TOA's slow budget, so a campaign that only one device sees is rationed.",
        "Peers are chosen to differ in vendor or firmware, so one exploit cannot make several devices agree.",
        "A new device starts from its peers' median and learns under the residual budget only, which bounds how much "
        "an attacker can poison it while it joins."])
S += [P("Why this is different from published work", "h2")]
S.append(table([["Closest work", "What it does", "How we differ"],
                ["CIoTA (NDSS DISS 2018, JPDC 2020)", "Same-firmware devices must agree before learning; disagreement is discarded", "Our peers differ in firmware, so a one-exploit botnet cannot fake agreement; we admit the disagreeing part slowly instead of discarding it"],
                ["ANTIDOTE (IMC 2009)", "Robust PCA on a server, retrained in batches", "Continuous learning on a microcontroller, with peers"],
                ["WARDEN/CDC, 2026 papers on poisoning theory", "Prove single-stream limits", "We use a second stream to escape them, and must prove that as our own theorem"],
                ["DriftXpert, OWAD, T2T rollback (2023 to 2026)", "Stop or gate learning on a statistic", "These are the freeze-attack targets; FOA has no stop gate"]],
               [4.3 * cm, 5.2 * cm, W - 9.5 * cm]))
S += [Spacer(1, 4), P("Every candidate direction came back <i>partially covered</i> in our prior-art checks, so we claim a "
                      "specific combination rather than a first: a budgeted split between peer-explained and "
                      "unexplained updates, tested against a monoculture-botnet attacker, with a freeze-attack study "
                      "on published defences and ESP32 measurements.", "small"), PageBreak()]

# ------------------------------------------------------------------ Page 5-6: hardware
S += [P("PART 4", "eye"), P("IoT components and set-up", "h1"),
      P("The experiment needs a small fleet of real ESP32 devices on one network, an attacker, and a way to measure energy.")]
S.append(table([["Item", "Qty", "Why we need it"],
                ["ESP32 development board (for example ESP32-DevKitC)", "4 minimum, 5 with a spare", "Fleet nodes A to D and the power monitor. You said you have at least one; please check the count"],
                ["Temperature or humidity sensor (BME280 or DHT22)", "1 per node (optional)", "Gives each node real telemetry to send, so its traffic is genuine"],
                ["INA219 current-sensor module", "1 or 2", "Measures a node's power and energy"],
                ["5 V USB supply or breakout board", "1", "Feeds the node through the INA219"],
                ["Breadboard, jumper wires, 4.7 kohm resistors", "a set", "Wiring and I2C pull-ups"],
                ["USB cables and a powered USB hub", "5", "Flashing and serial logs"],
                ["Wi-Fi router or phone hotspot on a fixed channel", "1", "ESP-NOW and Wi-Fi must share one channel"],
                ["Laptop", "1", "MQTT broker (Mosquitto), poisoner script, N-BaIoT replay, data logging"]],
               [6.0 * cm, 3.0 * cm, W - 9.0 * cm]))
S += [P("Software and tools", "h2")]
S += B(["ESP-IDF or Arduino core for ESP32, with ESP-NOW and mbedTLS (HMAC) from the standard SDK.",
        "Python with NumPy for experiments; Mosquitto for MQTT telemetry; the existing N-BaIoT experiment scripts.",
        "Two run modes: <b>replay mode</b> (features from N-BaIoT are fed to the board over serial, to measure compute "
        "cost reliably) and <b>live mode</b> (the board's own telemetry traffic)."])
S += [P("What we will measure on the boards", "h2")]
S += B(["Memory: peak RAM and flash used by the detector, the peer step and the gossip buffer.",
        "Time: latency per update cycle, and time to verify one signed gossip message.",
        "Radio: bytes sent per learning event over ESP-NOW (about 72 bytes: 10 numbers plus a signature).",
        "Energy: millijoules per update cycle, from the INA219, reported separately for compute and for Wi-Fi."])
S += [P("Why we expect it to fit", "h2"),
      P("An ESP32 has two 240 MHz cores and about 520 KB of RAM. Per packet our detector needs about a thousand "
        "multiply-adds and under 10 KB of state; the peer step is a 10-dimensional median over a few neighbours. "
        "These are estimates, not measurements. Measuring them is research question RQ3.")]
S.append(KeepTogether([P("System layout", "h2"), img(os.path.join(HERE, "fig_system.png"), W * 0.86),
      P("Four ESP32 nodes with different firmware share a Wi-Fi network and gossip small signed updates over ESP-NOW. "
        "The laptop runs the MQTT broker, the poisoner and the logger. A separate ESP32 reads the INA219 on Node A.", "small")]))
S += [Spacer(1, 6), P("Wiring for energy measurement", "h2"), img(os.path.join(HERE, "fig_circuit.png"), W * 0.94),
      P("Proposed wiring, not yet built. Check each pin against your module's datasheet before powering it. The INA219 "
        "is wired in series with the node's 5 V supply (high-side). Default I2C pins on the ESP32 DevKitC are GPIO21 (SDA) "
        "and GPIO22 (SCL).", "small"), PageBreak()]

# ------------------------------------------------------------------ Page 7: tests
S += [P("PART 5", "eye"), P("What we will test", "h1"),
      P("Each test answers one claim. The headline result is the first two together.")]
S.append(table([["#", "Test", "Compare against", "Measure", "We win if"],
                ["1", "Attack hidden inside strong honest drift (the open problem)", "Signature-free single-stream; naive; WARDEN-style frozen reserve", "Detection and false alarms as drift and attacker share vary", "FOA keeps detection where single-stream fails"],
                ["2", "Monoculture botnet: the attacker reaches several same-firmware peers", "CIoTA-style same-firmware consensus", "Time to compromise; detection", "Diverse peers hold while same-firmware consensus is fooled"],
                ["3", "Freeze attack on published gated defences", "Kloft and Laskov switch-off rule; T2T rollback; OWAD demo", "False alarms after the attacker leaves; freeze duty cycle", "Gated defences end near 85% false alarms; FOA stays near nominal"],
                ["4", "New device joins", "One shared detector (34% false alarms earlier)", "False alarms after join; join-time poisoning", "False alarms near nominal"],
                ["5", "Cost of caution: vendor-specific honest drift", "Naive; TOA alone", "Adaptation lag; false alarms", "Lag is small and measured"],
                ["6", "Adaptive attackers", "Core-hiding, window-blind schedule, pulsing, omission", "Time to compromise", "No attacker beats the budget bound"],
                ["7", "ESP32 cost", "Naive detector on the same board", "RAM, latency, radio bytes, energy", "Overhead small enough to justify"],
                ["8", "Real long-term drift (stretch)", "As above", "Detection against the theory ceiling", "Ceiling lifted on real calendar drift"]],
               [0.6 * cm, 4.2 * cm, 3.7 * cm, 3.5 * cm, W - 12.0 * cm]))
S += [Spacer(1, 6), P("Data", "h2")]
S += B(["<b>N-BaIoT:</b> Danmini, Ecobee, Philips and the four cameras as peers. The devices were recorded separately, so "
        "shared drift is injected by us and labelled synthetic.",
        "<b>The ESP32 fleet:</b> a real router change gives genuine shared drift; a laptop script poisons one board.",
        "<b>CESNET-TimeSeries24:</b> real calendar drift. A stretch goal, not on the critical path."])
S += [P("The one headline figure", "h2"),
      P("Two panels. Left: under a monoculture botnet, same-firmware consensus is compromised while our diverse peers hold. "
        "Right: false alarms after the attacker leaves, with gated defences high and ours flat.")]
S.append(PageBreak())

# ------------------------------------------------------------------ Page 8: plan
S += [P("PART 6", "eye"), P("Plan of action", "h1"),
      P("Seven working weeks. Adjust the start to the real mid-review and final dates, which we should confirm with Dr. Tapadar.")]
S.append(table([["Wk", "Work", "Output"],
                ["1", "Rebuild the N-BaIoT download as a script (the earlier files were temporary). Build the multi-device harness with shared and vendor-specific drift. Read the three unread papers", "Reproducible data and harness"],
                ["2", "Implement FOA: geometric median, signed gossip, two cumulative budgets, join rule. Reuse the TOA code", "FOA in simulation"],
                ["3", "Implement baselines: CIoTA-style, clipped robust aggregation, WARDEN-style, Kloft and Laskov rule, T2T. Run the freeze attack on them", "Tests 3 and 4"],
                ["4", "Attacker matrix and the headline figure. Tests 1, 2, 5, 6. Prepare the mid-review pack", "First real results"],
                ["5", "Build the ESP32 fleet. Port the detector and FOA. Wire the INA219. First measurements", "Test 7, hardware demo"],
                ["6", "Write the proofs (a standalone multi-device theorem with its negative case). Ablations: peer count, budget, diverse vs random peers", "Theory and ablations"],
                ["7", "IEEE report, code package with README, live demo", "Final deliverables"]],
               [1.2 * cm, W - 5.2 * cm, 4.0 * cm]))
S += [P("Mid-review checklist (from the course brief)", "h2")]
S.append(table([["Required", "Status"],
                ["Clear problem statement and research question", ok() + " (RQs updated above)"],
                ["Literature table of recent papers", part("Partly") + ": 2024 to 2026 list exists; one merged table still to build"],
                ["Research gap and proposed contribution", ok()],
                ["System architecture and workflow", part("Draft") + ": diagram in this report"],
                ["Baselines implemented or clearly defined", part("Partly") + ": four built; published ones defined, not built"],
                ["Experimental setup, data plan and evaluation metrics", ok() + " (Part 4 and 5)"],
                ["Initial results or a clear plan", ok() + " (synthetic and real-doorbell results)"]],
               [8.0 * cm, W - 8.0 * cm]))
S += [P("Risks and fallbacks", "h2")]
S.append(table([["Risk", "Fallback"],
                ["Peer concurrency on N-BaIoT is synthetic", "Let the real ESP32 router change and CESNET carry the real-drift claim"],
                ["The multi-device proof is harder than it looks", "Present it as a stated assumption plus the matching negative result"],
                ["Multi-device plumbing, ESP-NOW channel clashes, or slow on-board features", "Ship the simpler variant that learns threat directions from the detector's own alarms; use replay mode for cost; keep the freeze-attack study, which stands alone"],
                ["Novelty is partial; some 2026 papers are preprints", "Pitch the specific combination and win test 2; verify numbers against PDFs before citing"]],
               [6.0 * cm, W - 6.0 * cm]))
doc.build(S)
print("wrote", os.path.join(HERE, "Progress_Report.pdf"))
