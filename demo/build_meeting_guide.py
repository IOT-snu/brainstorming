"""Builds demo/Meeting_Guide.pdf: what to show the instructor, in what order, and what to say.
Numbers are read from paper/numbers.tex so they match the paper. Run: python3 demo/build_meeting_guide.py"""
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("A", F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("AB", F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("AI", F + "Arial Italic.ttf"))
pdfmetrics.registerFontFamily("A", normal="A", bold="AB", italic="AI", boldItalic="AB")
INK = colors.HexColor("#1D1D1F"); BLUE = colors.HexColor("#0071E3"); GRAY = colors.HexColor("#86868B")
BODY = colors.HexColor("#424245"); CARD = colors.HexColor("#F5F5F7"); GRID = colors.HexColor("#E8E8ED")
st = {
    "cover": ParagraphStyle("cover", fontName="AB", fontSize=21, leading=26, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="A", fontSize=11, leading=15, textColor=BODY, spaceAfter=4),
    "eye": ParagraphStyle("eye", fontName="AB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h2": ParagraphStyle("h2", fontName="AB", fontSize=12, leading=15.5, textColor=INK, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="A", fontSize=9.6, leading=13.6, textColor=BODY, spaceAfter=4),
    "b": ParagraphStyle("b", fontName="A", fontSize=9.6, leading=13.2, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.6, leading=11.5, textColor=INK, backColor=CARD,
                           borderPadding=5, spaceBefore=3, spaceAfter=7, leftIndent=6),
    "cell": ParagraphStyle("cell", fontName="A", fontSize=8.5, leading=11, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="AB", fontSize=8.5, leading=11, textColor=INK),
    "small": ParagraphStyle("small", fontName="AI", fontSize=8.3, leading=11, textColor=GRAY, spaceAfter=3),
    "key": ParagraphStyle("key", fontName="A", fontSize=10, leading=14.2, textColor=INK, backColor=CARD,
                          borderPadding=7, spaceBefore=4, spaceAfter=9, leftIndent=8, rightIndent=8),
}
P = lambda t, s="p": Paragraph(t, st[s])
B = lambda items: [Paragraph(i, st["b"], bulletText="•") for i in items]
N = {k: v.replace("\\%", "%").replace("\\,", " ").replace("{,}", ",")
     for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", open(os.path.join(ROOT, "paper", "numbers.tex")).read())}


def table(rows, widths):
    data = [[P(c, "cellb" if r == 0 or j == 0 else "cell") for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("BACKGROUND", (0, 0), (-1, 0), CARD)]))
    return t


def img(path, w):
    iw, ih = PI.open(path).size
    return Image(path, width=w, height=w * ih / iw)


def footer(c, d):
    c.saveState(); c.setFont("A", 8); c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, "Group G-04  ·  Meeting guide  ·  Fleet-Orthogonal Adaptation")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(d.page)); c.restoreState()


doc = BaseDocTemplate(os.path.join(HERE, "Meeting_Guide.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.7 * cm, bottomMargin=1.8 * cm, title="G-04 meeting guide", author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 1.8 * cm, A4[0] - 4 * cm, A4[1] - 3.5 * cm)], onPage=footer)])
W = A4[0] - 4 * cm
S = []

S += [P("CSD457 · GROUP G-04 · PROGRESS MEETING", "eye"),
      P("Meeting guide: what to show, in what order", "cover"),
      P("Everything done before the ESP32 boards arrived. About 15 minutes; the live part takes 2.", "sub"),
      P("Open with this (30 seconds)", "h2"),
      P("An IoT device that keeps learning can be slowly taught that attacks are normal, and a defence that stops "
        "learning when traffic looks odd can be frozen by an attacker. From one device's traffic alone these cannot be "
        "told apart. <b>Our method, Fleet-Orthogonal Adaptation, uses the neighbouring devices as a second witness:</b> "
        "change that devices of other vendors also see is learned in full; change only this device sees is let in through "
        "a slow budget that never closes. We built it, proved its guarantees, tested it on real IoT traffic, wrote the paper, "
        "and wrote the ESP32 firmware, which is waiting for the boards.", "key"),
      P("Show in this order", "h2")]
S += [table([["#", "Open", "What to point at", "Time"],
             ["1", "paper/main.pdf, page 2", "Figure 1, the system diagram: shared drift, peers, common part vs rationed residual", "2 min"],
             ["2", "paper/main.pdf, Fig. 3 (headline)", "(a) the classic poisoner never beats FOA; (b) FOA alone is low on both compromise and false alarms", "2 min"],
             ["3", "Terminal: <b>bash demo/run_demo.sh</b>", "Tests pass, C firmware matches Python, then the live simulation on real traffic (see next page)", "2 min"],
             ["4", "demo/demo_scene1.png, demo_scene2.png", "Scene 1: poisoning inside drift. Scene 2: the freeze attack locks a published-style gate; FOA unchanged", "2 min"],
             ["5", "paper/main.pdf, Section IV", "Theorem 1 (bounded movement, minimum time to compromise) and Proposition 1 (what no rule can do)", "2 min"],
             ["6", "paper/main.pdf, Discussion: Limits we measured", "Be upfront: three results go against us", "1 min"],
             ["7", "firmware/README.md and circuit/", "ESP32 firmware compiles; 0 mismatches against Python; INA219 wiring; hardware-day steps", "2 min"],
             ["8", "notes/Progress_Report.pdf", "Leave with her: one-page status, results, next steps", "1 min"]],
            [0.6 * cm, 4.6 * cm, W - 6.6 * cm, 1.4 * cm])]
S += [P("Numbers to remember", "h2")]
S += B([f"Strong network-wide drift, no attacker: fleet false alarms <b>FOA {N['FOAFleetFPR']}</b>, single device {N['AutoFleetFPR']}, "
        f"pause-learning defences {N['GateFleetFPR']}, never-learning detector {N['StrongStaticFPR']}.",
        f"Poisoning hidden inside drift (6,720 runs): compromised <b>FOA {N['FOAComp']}</b> vs single device {N['AutoComp']}; "
        f"the classic slow poisoner never beat FOA ({N['FOABoundaryComp']}).",
        f"Monoculture botnet: same-model consensus (CIoTA style) {N['MonoCiotaThree']} compromised; FOA with diverse peers {N['MonoFOAThree']}.",
        f"Freeze attack: 5% decoys lock an alarm-rate switch-off at {N['KLFrozenFPR']} false alarms; FOA bit-for-bit unchanged.",
        f"Real drift (40 weeks of CESNET): FOA {N['CesFOAComp']} compromised, single device {N['CesAutoComp']}.",
        "Proven bound held in every attacked FOA run (0 violations in 3,630). ESP32: 0 mismatches in 480 cycles, "
        "0 of 23,104 tampered messages accepted, about 22 KB of flash for FOA."])
S.append(PageBreak())

S += [P("THE LIVE DEMO", "eye"), P("One command, about two minutes", "h2"),
      P("cd \"research project/brainstorming\"<br/>bash demo/run_demo.sh --esp32", "code"),
      P("Run it once before the meeting so the data is cached. It prints four blocks:", "p")]
S += B(["<b>Tests.</b> 16 unit and property tests: geometric median robustness, budget never exceeded, forged and replayed "
        "messages rejected, decoys leave FOA unchanged.",
        "<b>Firmware check.</b> The ESP32 C code is fed the same inputs as the Python version on 480 recorded cycles: "
        "0 mismatches, every tampered message rejected, HMAC matches the official test vector.",
        "<b>Live simulation.</b> Real traffic of nine IoT devices. Scene 1: strong drift plus an attacker on one camera. "
        "Scene 2: the freeze attack.",
        "<b>ESP32 compile</b> (with --esp32): flash and RAM with and without FOA."])
S += [img(os.path.join(HERE, "demo_scene1.png"), W),
      P("Scene 1 as it prints: the single-device rule and the alarm switch-off lose the scan attack completely (their lines "
        "overlap at 0%); the frozen reserve and the static detector keep it but raise 60 to 76% false alarms on the rest of "
        "the fleet; FOA keeps detecting with about 6% false alarms.", "small"),
      img(os.path.join(HERE, "demo_scene2.png"), W * 0.62),
      P("Scene 2: decoys sent only between cycles 40 and 100 lock the alarm-rate switch-off at 100% false alarms for good. "
        "FOA's run with and without the attacker is identical.", "small"),
      PageBreak()]

S += [P("BE READY FOR", "eye"), P("Likely questions", "h2")]
S += [table([["Question", "Answer"],
             ["Is the data real?", "The traffic and the attacks are real (N-BaIoT: nine devices, real Mirai and BASHLITE). The "
              "concurrency of the fleet, the drift on N-BaIoT and the poisoner are simulated by us, and we say so. CESNET gives 40 weeks of real drift."],
             ["Is this new? What about CIoTA?", "CIoTA (2018) also uses peers, but same-model peers and it discards disagreement. "
              "We use peers from other vendors and ration rather than discard. Head to head under a monoculture botnet: CIoTA-style 100% compromised, FOA 0%. We say 'we found no prior work that', never 'first'."],
             ["Did you tune on the test data?", "No. All design choices were made on development seeds 0 and 1; every reported "
              "number uses seeds 2 to 11. The victim rule (attack at least 1.3 alarm radii out) was fixed before the main runs."],
             ["How do you count a compromise?", "Each attacked run is paired with the same run without the attacker. Only "
              "detection lost that the attacker-free twin keeps counts, because honest drift alone can hide an attack."],
             ["What does it cost on the device?", "One 92-byte message per device per learning cycle and about 22 KB of flash; "
              "about 2 ms of computing per 10 s cycle is an estimate until we measure it on the boards."],
             ["Where does it fail?", "A device with a big change of its own on top of network-wide drift is lost; malicious "
              "peers alone never win, but together with a traffic poisoner they beat borderline devices; stealthier poisoners "
              "at 40% share still win about a third of the time."],
             ["What is the theory?", "Theorem 1: an attacker on one device gains at most B0 + Bt alarm radii, giving a "
              "minimum time to compromise (checked in every run). Proposition 1: a device's own change and an attack on it look "
              "identical to everyone else, so no rule can avoid the trade-off; FOA makes it one number, B."]],
            [4.3 * cm, W - 4.3 * cm])]
S += [P("What we need from her", "h2")]
S += B(["When the ESP32 boards and INA219 modules will be available, and how many.",
        "The mid-review and final submission dates, and whether the IEEE paper format is acceptable for the report.",
        "Whether the affiliation line on the paper is right."])
S += [P("Files", "h2"),
      table([["What", "Where"],
             ["Paper (IEEE, 11 pages)", "paper/main.pdf"],
             ["Progress report", "notes/Progress_Report.pdf"],
             ["First presentation deck", "CSD457_First_Presentation.pptx"],
             ["Study notes and read-up", "notes/Presentation_and_Study_Notes.pdf, notes/Readup_From_Zero.pdf"],
             ["Simulator and all experiments", "experiments/foa (README.md, RESEARCH_LOG.md)"],
             ["ESP32 firmware and tools", "firmware (README.md)"],
             ["Power-measurement circuit", "circuit (KiCad schematic, CircuitLab sheet)"],
             ["Demo", "demo/run_demo.sh, demo/live_demo.py"]],
            [5.5 * cm, W - 5.5 * cm])]
doc.build(S)
print("wrote", os.path.join(HERE, "Meeting_Guide.pdf"))
