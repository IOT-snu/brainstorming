"""Builds Presentation_and_Study_Notes.pdf. Run: python3 build_notes.py"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

HERE = os.path.dirname(os.path.abspath(__file__))
F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("A", F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("AB", F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("AI", F + "Arial Italic.ttf"))
pdfmetrics.registerFontFamily("A", normal="A", bold="AB", italic="AI", boldItalic="AB")

INK = colors.HexColor("#1D1D1F"); BLUE = colors.HexColor("#0071E3"); GRAY = colors.HexColor("#86868B")
BODY = colors.HexColor("#424245"); CARD = colors.HexColor("#F5F5F7"); GRID = colors.HexColor("#E8E8ED")
RED = colors.HexColor("#D70015"); GREEN = colors.HexColor("#248A3D")

st = {
    "cover": ParagraphStyle("cover", fontName="AB", fontSize=26, leading=31, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="A", fontSize=13, leading=18, textColor=BODY),
    "eye": ParagraphStyle("eye", fontName="AB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="AB", fontSize=19, leading=24, textColor=INK, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="AB", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="AB", fontSize=11, leading=14, textColor=BLUE, spaceBefore=6, spaceAfter=2),
    "p": ParagraphStyle("p", fontName="A", fontSize=10, leading=14.5, textColor=BODY, spaceAfter=5),
    "b": ParagraphStyle("b", fontName="A", fontSize=10, leading=14, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2),
    "small": ParagraphStyle("small", fontName="AI", fontSize=8.5, leading=11, textColor=GRAY),
    "cell": ParagraphStyle("cell", fontName="A", fontSize=9, leading=12, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="AB", fontSize=9, leading=12, textColor=INK),
    "say": ParagraphStyle("say", fontName="A", fontSize=10, leading=14.5, textColor=INK, leftIndent=10,
                          borderColor=BLUE, borderWidth=0, backColor=CARD, borderPadding=7, spaceBefore=3, spaceAfter=8),
}


def P(t, s="p"): return Paragraph(t, st[s])
def B(items): return [Paragraph(i, st["b"], bulletText="•") for i in items]
def link(url, text=None): return f'<link href="{url}" color="#0071E3"><u>{text or url}</u></link>'


def table(rows, widths, head=True):
    data = [[P(c, "cellb" if (head and r == 0) or c0 == 0 else "cell") if isinstance(c, str) else c
             for c0, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if head:
        style += [("BACKGROUND", (0, 0), (-1, 0), CARD)]
    t.setStyle(TableStyle(style))
    return t


def footer(c, d):
    c.saveState()
    c.setFont("A", 8); c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, "CSD457 Group G-04  ·  Poison-Resilient On-Device Intrusion Detection for Drifting IoT")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(d.page))
    c.restoreState()


doc = BaseDocTemplate(os.path.join(HERE, "Presentation_and_Study_Notes.pdf"), pagesize=A4,
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                      title="G-04 Presentation and Study Notes", author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 2 * cm, A4[0] - 4 * cm, A4[1] - 4 * cm, id="f")], onPage=footer)])
W = A4[0] - 4 * cm
S = []

# ------------------------------------------------------------------ Cover
S += [Spacer(1, 4 * cm), P("CSD457 INTERNET OF THINGS  ·  GROUP G-04", "eye"),
      P('<font color="#0071E3">Poison-Resilient</font> On-Device Intrusion Detection for Drifting IoT', "cover"),
      Spacer(1, 10), P("Presentation notes and study guide", "sub"),
      P("Rishit Kamboj and Farhan Naik  ·  First presentation, 24 September 2026", "sub"),
      Spacer(1, 1.2 * cm)]
S.append(table([["Part", "What is inside"],
                ["1", "The whole project on one page"],
                ["2", "Key ideas explained simply"],
                ["3", "The 5 papers: the crux of each, and links to read them"],
                ["4", "Our simulation: what it shows and how to explain it"],
                ["5", "Slide-by-slide presentation script with timing"],
                ["6", "Question and answer preparation"],
                ["7", "What happens after the presentation"]], [2 * cm, W - 2 * cm]))
S += [Spacer(1, 1 * cm), P("How to use this: read Parts 1 to 3 to understand the project. Rehearse with Part 5. "
                           "Each of you should be able to answer every question in Part 6 alone.", "small"), PageBreak()]

# ------------------------------------------------------------------ Part 1
S += [P("PART 1", "eye"), P("The whole project on one page", "h1"),
      P("<b>In one sentence:</b> we are building an IoT intrusion detector that keeps learning on an ESP32 "
        "but cannot be taught to ignore attacks.", "say"),
      P("The problem in three steps", "h2")]
S += B(["<b>Detection should run on the device.</b> A small anomaly detector can sit on cheap hardware next to "
        "the traffic it protects [3].",
        "<b>But normal traffic keeps changing</b> (called <i>concept drift</i>). Real networks drift for weeks; "
        "traffic volume fell 52% at semester end in real ISP data [5]. So the detector must keep learning.",
        "<b>Learning is the weak point.</b> An attacker can feed it slow, harmless-looking changes until an attack "
        "looks normal. This is the <i>boiling-frog</i> poisoning attack [1]. The bigger the attacker's share of "
        "the traffic, the further they can push it [2]."])
S += [P("What we will do", "h2")]
S += B(["<b>Measure the risk:</b> show how easily real, low-traffic IoT devices can be poisoned [2][4].",
        "<b>Build the defense, Threat-Orthogonal Adaptation (TOA):</b> split every update the detector wants to make. "
        "The part that moves sideways or away from known attacks is applied freely. Only the part that moves toward "
        "a known attack is rationed.",
        "<b>Prove it for real:</b> test on real IoT traffic [4] and real drift [5], then run it on an ESP32 and "
        "measure memory, speed and energy."])
S += [P("Why it is new", "h2")]
S += B(["The closest existing defense against boiling-frog poisoning (ANTIDOTE [1]) runs on a server with batch "
        "retraining. Ours learns continuously on a microcontroller.",
        "We found a <b>new attack</b>: defenses that <i>freeze</i> when drift looks suspicious can be tripped on "
        "purpose, leaving the detector stale and flooding operators with false alarms.",
        "TOA never freezes, and gives a <b>provable minimum time</b> before a known attack can be hidden."])
S += [P("Evidence so far", "h2"),
      P("In our synthetic simulation with the attacker at 40% of traffic: naive learning loses the attack in 24 "
        "cycles; freezing defenses keep the attack visible but reach 85 to 87% false alarms; TOA keeps 100% of "
        "the attack detected with 0.3% false alarms. Real-data results come by mid-review."), PageBreak()]

# ------------------------------------------------------------------ Part 2
S += [P("PART 2", "eye"), P("Key ideas explained simply", "h1")]
S.append(table([
    ["Term", "Plain meaning", "Why it matters here"],
    ["Intrusion detection system (IDS)", "Software that watches network traffic and raises an alarm on attacks.", "What we are building, on an ESP32."],
    ["Anomaly detection", "Learn what normal looks like; alarm on anything too different. Can catch unseen attacks.", "Our detector type [3]. It needs a model of normal, which is what an attacker targets."],
    ["Centre and spread", "Our detector keeps the average of normal traffic (centre) and how spread out it is. Far from the centre means alarm.", "Both can be poisoned: drag the centre, or inflate the spread."],
    ["Concept drift", "Normal behaviour slowly changes: new devices, firmware, seasons, semesters.", "Forces the detector to keep learning [5]."],
    ["Data poisoning", "Feeding a learning system crafted data so it learns the wrong thing.", "The attack we defend against."],
    ["Boiling-frog attack", "Poison in tiny steps, each too small to alarm, until an attack looks normal.", "Demonstrated on network detectors in [1]."],
    ["Attacker's share", "What fraction of the learning data the attacker controls.", "Bounds how far they can push [2]; small IoT devices make it large."],
    ["Freeze attack (ours)", "Trip a defense that stops learning, then leave; drift makes the frozen detector useless.", "Our new finding; TOA is immune because it never freezes."],
    ["Threat-Orthogonal Adaptation", "Split each update into toward-attack and everything else; only ration toward-attack.", "Our method."],
    ["Margin", "Distance between a known attack and the edge of what counts as normal.", "TOA guarantees it shrinks slowly, which gives the proof."],
    ["Recall / false-positive rate", "Share of attacks caught / share of normal traffic wrongly flagged.", "Our two headline numbers."],
], [3.6 * cm, 6.8 * cm, W - 10.4 * cm]))
S += [Spacer(1, 10), P("The key intuition behind TOA", "h2"),
      P("Honest drift can move in any direction. A semester-end traffic drop, for example, moves away from flood "
        "attacks. Poisoning has no such freedom: to hide an attack it <b>must</b> move normal toward that attack. "
        "So instead of blocking all drift (which freezes the detector), we block only drift in the one direction "
        "an attacker needs. On an ESP32 that costs one dot product per known attack per update."), PageBreak()]

# ------------------------------------------------------------------ Part 3
PAPERS = [
    ("[1]", "ANTIDOTE: Understanding and Defending against Poisoning of Anomaly Detectors",
     "B. I. P. Rubinstein, B. Nelson, L. Huang, A. D. Joseph et al.  ·  ACM Internet Measurement Conference (IMC), 2009",
     "Network operators use a PCA-based detector to spot anomalies in backbone traffic, and they retrain it on recent traffic. Can an attacker poison that retraining?",
     "Yes. The paper introduces the <b>boiling-frog</b> strategy: add a little malicious traffic ('chaff') over several weeks so the detector slowly accepts it, then launch the real attack unnoticed. As a defense it proposes <b>ANTIDOTE</b>, a robust version of PCA (PCA-GRID) that is less influenced by outliers, and shows it sharply reduces the attacker's success.",
     "It proves our threat is real on network detectors, and it is the closest existing defense, which we cite honestly as prior work.",
     "Server-side, batch retraining on large backbone traffic. Not continuous learning, not on a small device, and it does not study defenses that freeze.",
     "Abstract, the Boiling Frog section, and the ANTIDOTE results.",
     "https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf", None),
    ("[2]", "Security Analysis of Online Centroid Anomaly Detection",
     "M. Kloft and P. Laskov  ·  Journal of Machine Learning Research (JMLR), vol. 13, 2012",
     "An online centroid detector keeps updating its centre as new data arrives. How much can an attacker move it?",
     "A formal analysis: it derives the optimal attack and proves that how far the attacker can shift the centre is <b>bounded by the fraction of the traffic they control</b>. With a small share, the attack stalls; with a large share, it succeeds.",
     "This is the theory behind our finding that small IoT devices are easier to poison: a smart plug sends little traffic, so the attacker's share can be large. Our simulation matches it: at 10 to 20% share even naive learning survives; at 30%+ it breaks.",
     "Pure theory. Nobody has measured attacker share on real low-traffic IoT devices, or built an on-device defense from it.",
     "Introduction and the results on attack efficiency versus attacker fraction.",
     "https://jmlr.csail.mit.edu/papers/volume13/kloft12b/kloft12b.pdf", "https://arxiv.org/abs/1003.0078"),
    ("[3]", "Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection",
     "Y. Mirsky, T. Doitshman, Y. Elovici and A. Shabtai  ·  NDSS, 2018",
     "Can an intrusion detector learn normal traffic by itself, online, cheaply enough for small devices?",
     "Kitsune extracts compact statistics from each packet stream in constant memory, then scores anomalies with a small ensemble of autoencoders. It runs on a Raspberry Pi and detects real attacks, including the Mirai botnet.",
     "Source of our feature extraction, and proof that on-device anomaly detection is practical. Serves as our static baseline.",
     "After its training phase it stops learning, so it goes stale under drift, and it has no protection against poisoning.",
     "Sections on the feature extractor (why it is cheap) and the evaluation.",
     "https://arxiv.org/abs/1802.09089", None),
    ("[4]", "N-BaIoT: Network-Based Detection of IoT Botnet Attacks Using Deep Autoencoders",
     "Y. Meidan, M. Bohadana, Y. Mathov et al.  ·  IEEE Pervasive Computing, 2018",
     "How do real IoT devices behave on the network when infected by botnets?",
     "Captured traffic from <b>9 real commercial IoT devices</b> (cameras, doorbells, thermostats, a baby monitor) in normal operation and while infected with <b>Mirai and BASHLITE</b>. Trained one autoencoder per device and detected the attacks accurately.",
     "Our main dataset: real IoT traffic and real attacks, with realistic per-device traffic rates that tell us how large an attacker's share could be.",
     "Detection is offline; no drift over time and no poisoning of the detector.",
     "The dataset description and the list of devices and attacks.",
     "https://arxiv.org/abs/1805.03409", None),
    ("[5]", "CESNET-TimeSeries24: Time Series Dataset for Network Traffic Anomaly Detection and Forecasting",
     "J. Koumar, K. Hynek, T. Čejka and P. Šiška  ·  Scientific Data, vol. 12, 2025",
     "Researchers lack long, real network traffic datasets to study how traffic changes over time.",
     "Released <b>40 weeks</b> of traffic statistics from an ISP network serving about half a million users: 275,000 IP addresses, 66 billion flows, at IP, institution and subnet level.",
     "Our source of <b>real benign drift</b>. It showed us that honest drift is steady and directional too (volume down 52% at semester end, from an analysis of this data), which is why direction alone cannot reveal an attack.",
     "A dataset. It has not been used to test poisoning defenses for adaptive detectors.",
     "The dataset overview and the figures of traffic over time.",
     "https://www.nature.com/articles/s41597-025-04603-x", "https://arxiv.org/abs/2409.18874"),
]
S += [P("PART 3", "eye"), P("The 5 papers: the crux of each", "h1"),
      P("Chosen from 78 papers found and 28 read in full. Each one gives us one piece; together they show the gap. "
        "Read each 'Start with' section before the presentation.")]
for num, title_, cite, q, crux, us, gap, start, url, alt in PAPERS:
    block = [Spacer(1, 6), P(f"{num}  {title_}", "h2"), P(cite, "small"), Spacer(1, 3),
             table([["Question it asks", q], ["The crux", crux], ["Why it matters to us", us],
                    ["What it leaves open", f'<font color="#D70015">{gap}</font>'], ["Start with", start],
                    ["Read it", link(url) + (("<br/>Also: " + link(alt)) if alt else "")]],
                   [3.6 * cm, W - 3.6 * cm], head=False)]
    S.append(KeepTogether(block))
S += [Spacer(1, 8), P("How the five fit together", "h2"),
      P("Kitsune [3] shows detection can live on a device, but it stops learning. CESNET-TS24 [5] shows real "
        "traffic drifts, so it must keep learning. ANTIDOTE [1] shows learning can be poisoned and defends only on "
        "a server. Kloft and Laskov [2] explain when poisoning succeeds, and N-BaIoT [4] gives real IoT devices to "
        "test that on. The missing piece, a detector that learns safely on the device, is our project."),
      PageBreak()]

# ------------------------------------------------------------------ Part 4
S += [P("PART 4", "eye"), P("Our simulation: what it shows", "h1"),
      P("We tested the idea before presenting it, in <b>experiments/sim_toa.py</b> (synthetic data, 5 random "
        "seeds). A centre-and-spread detector learns each cycle from traffic it judges normal. The attacker controls "
        "40% of traffic and places poison just inside the boundary, toward the attack it wants to hide. Honest drift "
        "happens during cycles 60 to 140 (grey band).")]
fig = os.path.join(HERE, "..", "experiments", "fig_slide.png")
if os.path.exists(fig):
    S += [Image(fig, width=W, height=W / 3.265), Spacer(1, 6)]
S.append(table([["Policy", "Attack still detected", "False alarms", "What happened"],
                ["Naive learning", "0% after cycle 24", "0%", "Poisoned: the attack now looks normal."],
                ["Robust consistency filter", "100%", "85%", "Stops learning, then drowns in false alarms once drift starts."],
                ["Freeze budget", "100%", "87%", "Freezes. In the right panel the attacker leaves at cycle 45 and it never recovers: the freeze attack."],
                ["TOA (ours)", "100%", "0.3%", "Keeps learning honest drift; the attacker cannot move it toward the attack."]],
               [3.6 * cm, 3.1 * cm, 2.2 * cm, W - 8.9 * cm]))
S += [P("Honest limits to say out loud", "h2")]
S += B(["The chart is synthetic, but a real check on N-BaIoT doorbell traffic agrees: naive learning poisoned at 10% share, ours 100% detection with 0.8% false alarms (experiments/nbaiot_check.py).",
        "The slide version uses attack signatures. A signature-free version also works on real N-BaIoT (both attackers, 100% detection), but an attack hidden inside strong genuine drift still beats it in synthetic tests.",
        "If honest drift moves toward an attack, TOA slows learning in that direction; false alarms peaked near 7% "
        "in our worst-case test, then recovered.",
        "At a 10 to 20% attacker share even naive learning survived, consistent with Kloft and Laskov [2]."])
S.append(PageBreak())

# ------------------------------------------------------------------ Part 5
SCRIPT = [
    ("1", "Title", "20 s", "Rishit", "We are Group G-04. Our project is about intrusion detection that runs on a small IoT device and keeps learning, without an attacker being able to abuse that learning."),
    ("2", "What we will research", "40 s", "Rishit", "In one line: an IoT intrusion detector that keeps learning on an ESP32 and cannot be taught to ignore attacks. We will do three things: measure how easily real IoT devices get poisoned, build our defense called Threat-Orthogonal Adaptation, and prove it on real data and real hardware."),
    ("3", "Problem", "45 s", "Rishit", "Detection belongs on the device [3]. But normal traffic keeps changing, as real data shows [5], so the detector must keep learning. And that learning is the weak point: an attacker can feed slow, harmless-looking changes until an attack looks normal [1], and the bigger their share of traffic, the easier it is [2]."),
    ("4", "The 5 papers", "70 s", "Rishit", "We read 28 papers in full and built on these five. Walk the rows, and read the red column: server only, theory only, no defense, no drift, never used for this. That red column is our research gap."),
    ("5", "Research gap", "40 s", "Farhan", "Detectors on devices stop learning, real drift means learning cannot stop, and the one existing defense runs on a server. So nothing learns safely on a device. Credit where due: the attack and a server defense both come from ANTIDOTE."),
    ("6", "Research questions", "35 s", "Farhan", "RQ1 is our method. RQ2 is a new attack we found. RQ3 is real exposure and cost on the ESP32."),
    ("7", "Approach", "60 s", "Farhan", "Every update the detector wants to make is split in two. Anything sideways or away from known attacks is applied immediately, so it never freezes. Only the part moving toward an attack is rationed. That gives a provable minimum time before an attack can be hidden, for the cost of a few dot products."),
    ("8", "Three findings", "50 s", "Farhan", "One: honest drift is directional too, so direction toward an attack is what matters. Two: defenses that freeze can be weaponized, which broke our own first design. Three: small IoT devices are easier to poison because the attacker can be a large share of their traffic."),
    ("9", "Platform and baselines", "40 s", "Rishit", "ESP32 hardware, Python for experiments, N-BaIoT for real IoT attacks and CESNET for real drift. We compare against five baselines, including the classic ANTIDOTE defense."),
    ("10", "Preliminary result", "60 s", "Rishit", "This is synthetic, to test the idea. Left: naive learning is poisoned in 24 cycles. Middle: freezing defenses keep the attack visible but false alarms explode once drift starts. Right: the attacker leaves at cycle 45 and the frozen defense never recovers. Blue is ours in every panel."),
    ("11", "Contribution and plan", "40 s", "Farhan", "Three contributions: the method, the freeze attack, and real exposure and cost measurements. Real-data results by mid-review, the ESP32 port after that. Thank you, we are happy to take questions."),
    ("12", "References", "Q&A", "Both", "Leave this slide up during questions."),
]
S += [P("PART 5", "eye"), P("Slide-by-slide script", "h1"),
      P("About 7 minutes of talking, leaving 3 for questions. The speaker split is a suggestion; swap slides so "
        "each of you presents the part you understand best. Speak naturally; do not read these word for word.")]
S.append(table([["#", "Slide", "Time", "Speaker", "What to say"]] +
               [[a, b, c, d, e] for a, b, c, d, e in SCRIPT],
               [0.8 * cm, 2.7 * cm, 1.2 * cm, 1.9 * cm, W - 6.6 * cm]))
S += [P("Delivery tips", "h2")]
S += B(["Open with slide 2's sentence. If the audience remembers one thing, it should be that.",
        "Point at the red column on slide 4 and the blue line on slide 10. Those two moments carry the talk.",
        "Say 'synthetic' clearly on slide 10. Honesty about limits earns more credit than overclaiming.",
        "Credit ANTIDOTE out loud on slide 5. It shows you read deeply and makes your novelty claim safe.",
        "Rehearse once with a timer. If you run long, shorten slide 4 first."])
S.append(PageBreak())

# ------------------------------------------------------------------ Part 6
QA = [
    ("Isn't this just ANTIDOTE?", "No. ANTIDOTE [1] retrains a robust PCA model in batches on a server with lots of traffic. We learn continuously on a microcontroller, never freeze, and handle drift. ANTIDOTE is one of our baselines."),
    ("Is the boiling-frog attack your idea?", "No, it is from ANTIDOTE [1]. Our contributions are the defense (TOA), the freeze attack, and measurements on real IoT data and hardware."),
    ("What is the freeze attack exactly?", "Many defenses stop learning when drift looks suspicious. An attacker can trigger that on purpose and leave. Normal traffic keeps drifting, so the frozen detector raises more and more false alarms until someone switches it off. TOA never freezes, so it cannot be tricked this way."),
    ("Why would an attacker control 40% of traffic?", "Kloft and Laskov [2] show poisoning only works with a large share. Small IoT devices like smart plugs send very little traffic [4], so an attacker easily matches it. At 10 to 20% even naive learning survived in our simulation, which agrees with [2]."),
    ("Doesn't TOA need attack signatures? That sounds like hard-coding.", "The version on the slides uses signatures for known attacks. We also built a signature-free version: it learns only from the dense core of traffic, and accepts a shift or a wider boundary only if the whole traffic cloud backs it up, because honest drift moves everything while poison moves one part. On real N-BaIoT doorbell traffic it kept 100% detection of Mirai scan, ack and syn against both a normal attacker and a smart attacker who knows the defense, at 10 to 50% attacker share, with 0.2 to 1.5% false alarms."),
    ("So what is still unsolved?", "An attack hidden inside strong genuine drift. In synthetic tests where heavy honest drift and the attack coincide, the signature-free version was still poisoned. Our plan combines both: signature-free by default, with signatures as a guaranteed floor for the most important attacks such as Mirai. Closing that gap is the research question for the rest of the semester."),
    ("What if normal traffic drifts toward an attack?", "Then TOA slows learning in that direction. In our worst-case test false alarms peaked near 7% and recovered, far better than freezing defenses."),
    ("Is the simulation real data?", "The chart is synthetic. We also ran a real check on N-BaIoT: real doorbell traffic and real Mirai attacks, with a modelled poisoner. Naive learning was poisoned at just 10% attacker share; ours kept 100% detection with 0.8% false alarms across three Mirai attacks. Full real-data comparison comes by mid-review."),
    ("Why an ESP32?", "It is cheap, common in IoT, and small enough that memory and energy really matter. That is exactly where continuous, safe learning is hardest and where no existing defense runs."),
    ("What is the guarantee?", "TOA only lets the gap between normal and a known attack shrink by a fixed budget per cycle, so the attack stays detected for at least a computable number of cycles, whatever the attacker does."),
    ("What does it cost on the ESP32?", "One dot product and one distance per known attack per update. Measuring the real memory, latency and energy is part of RQ3."),
]
S += [P("PART 6", "eye"), P("Question and answer preparation", "h1")]
for q, a in QA:
    S.append(KeepTogether([P(q, "h3"), P(a)]))
S.append(PageBreak())

# ------------------------------------------------------------------ Part 7
S += [P("PART 7", "eye"), P("What happens after the presentation", "h1")]
S.append(table([["When", "Goal", "Output"],
                ["Weeks 1 to 3", "N-BaIoT pipeline with Kitsune-style features; naive, static and freeze baselines; the boiling-frog attack", "Naive detector poisoned on real data"],
                ["Week 4 (mid-review)", "TOA on real data; literature table; architecture", "Real-data version of slide 10"],
                ["Weeks 5 to 7", "ESP32 port; freeze attack study; CESNET drift replay", "Memory, latency, energy numbers"],
                ["Weeks 8 to 9", "Sweeps over attacker share and budget; IEEE report; demo", "Final report and code"]],
               [3.2 * cm, 8.2 * cm, W - 11.4 * cm]))
S += [P("Files in our repository", "h2")]
S += B(["<b>topic-proposal.md</b>: the full proposal.",
        "<b>research-findings.md</b>: why the design changed and the evidence.",
        "<b>literature-review.md</b>: all 28 papers read, with notes.",
        "<b>experiments/sim_toa.py</b>: the simulation (run: python3 sim_toa.py).",
        "Repository: " + link("https://github.com/IOT-snu/brainstorming")])
S += [P("All five papers, one list", "h2")]
for num, title_, cite, *_rest, url, alt in PAPERS:
    S.append(P(f"<b>{num}</b> {title_}. {cite}.<br/>{link(url)}" + (f"<br/>{link(alt)}" if alt else ""), "b"))

doc.build(S)
print("wrote", os.path.join(HERE, "Presentation_and_Study_Notes.pdf"))
