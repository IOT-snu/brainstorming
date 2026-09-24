"""Builds Readup_From_Zero.pdf, a beginner-friendly explanation of the whole project.
Run: python3 concept_figs.py && python3 build_readup.py"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
    "cover": ParagraphStyle("cover", fontName="AB", fontSize=28, leading=33, textColor=INK),
    "sub": ParagraphStyle("sub", fontName="A", fontSize=13, leading=18, textColor=BODY),
    "eye": ParagraphStyle("eye", fontName="AB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="AB", fontSize=20, leading=25, textColor=INK, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="AB", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", fontName="A", fontSize=10.5, leading=15.5, textColor=BODY, spaceAfter=6),
    "b": ParagraphStyle("b", fontName="A", fontSize=10.5, leading=15, textColor=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="AI", fontSize=9, leading=12, textColor=GRAY, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName="A", fontSize=9.5, leading=12.5, textColor=BODY),
    "cellb": ParagraphStyle("cellb", fontName="AB", fontSize=9.5, leading=12.5, textColor=INK),
    "key": ParagraphStyle("key", fontName="A", fontSize=10.5, leading=15, textColor=INK, backColor=CARD,
                          borderPadding=8, spaceBefore=6, spaceAfter=12, leftIndent=8, rightIndent=8),
}
def P(t, s="p"): return Paragraph(t, st[s])
def B(items): return [Paragraph(i, st["b"], bulletText="•") for i in items]
def KEY(t): return P("<b>In short:</b> " + t, "key")
def link(u, t=None): return f'<link href="{u}" color="#0071E3"><u>{t or u}</u></link>'
def img(name, w, folder=HERE):
    from PIL import Image as PI
    path = os.path.join(folder, name)
    iw, ih = PI.open(path).size
    return Image(path, width=w, height=w * ih / iw)
def table(rows, widths):
    data = [[P(c, "cellb" if r == 0 or j == 0 else "cell") for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRID),
                           ("BACKGROUND", (0, 0), (-1, 0), CARD), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t
def footer(c, d):
    c.saveState(); c.setFont("A", 8); c.setFillColor(GRAY)
    c.drawString(2 * cm, 1.2 * cm, "From zero: our IoT security research project  ·  Group G-04")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(d.page)); c.restoreState()

doc = BaseDocTemplate(os.path.join(HERE, "Readup_From_Zero.pdf"), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm, title="From zero: our IoT security research project",
                      author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2.2 * cm, 2 * cm, A4[0] - 4.4 * cm, A4[1] - 4 * cm)], onPage=footer)])
W = A4[0] - 4.4 * cm
S = []

# Cover
S += [Spacer(1, 3.5 * cm), P("CSD457 INTERNET OF THINGS  ·  GROUP G-04", "eye"),
      P("From zero: what our research project is actually about", "cover"), Spacer(1, 10),
      P("A read-up that assumes no background. Start at page one and by the end you will understand the problem, "
        "the research, our idea, and our results.", "sub"), Spacer(1, 0.8 * cm),
      table([["Chapter", "Question it answers"],
             ["1", "What is the Internet of Things, and why is it easy to attack?"],
             ["2", "What does network traffic look like to a computer?"],
             ["3", "What is an intrusion detection system?"],
             ["4", "How does a detector learn what 'normal' looks like?"],
             ["5", "Why must the detector keep learning?"],
             ["6", "What is poisoning, and what is the boiling-frog attack?"],
             ["7", "Why are small IoT devices especially at risk?"],
             ["8", "Why don't existing defenses solve it?"],
             ["9", "Our idea: Threat-Orthogonal Adaptation"],
             ["10", "How we tested it, and what we found (10B: without a list of attacks)"],
             ["11", "What we will do next"],
             ["12", "The five papers, a glossary, and where everything lives"]], [2.2 * cm, W - 2.2 * cm]),
      PageBreak()]

# 1
S += [P("CHAPTER 1", "eye"), P("What is the Internet of Things, and why is it easy to attack?", "h1"),
      P("The <b>Internet of Things (IoT)</b> means everyday objects connected to the internet: smart doorbells, "
        "security cameras, thermostats, baby monitors, smart plugs, fitness bands, factory sensors. Each one is a "
        "tiny computer with a network connection."),
      P("They are easy targets for three reasons:")]
S += B(["<b>They are weak computers.</b> A smart plug has a small chip, very little memory and a tiny power budget. "
        "There is no room for heavy antivirus software.",
        "<b>They are rarely updated or watched.</b> People install them and forget them, often with default passwords.",
        "<b>There are billions of them.</b> Take over enough of them and you have an army."])
S += [P("That army is called a <b>botnet</b>. The best-known one is <b>Mirai</b>, which in 2016 infected large "
        "numbers of cameras and routers using default passwords and used them to flood websites with traffic. "
        "Mirai is also in the dataset we use (N-BaIoT [4])."),
      KEY("IoT devices are small, forgotten and numerous, so attackers love them. They need protection that is "
          "light enough to run on the devices themselves.")]

# 2
S += [P("CHAPTER 2", "eye"), P("What does network traffic look like to a computer?", "h1"),
      P("Devices talk by sending <b>packets</b>: small chunks of data, each with a size and a time it was sent. "
        "A doorbell might send a few packets a second to its cloud server; an infected doorbell running a flood "
        "attack sends thousands."),
      P("A detector does not read the contents of packets. It summarises the <b>pattern</b>: how big packets are, how "
        "many are sent, how regular the timing is, how many different destinations there are, measured over several "
        "time windows (the last 0.1 seconds, 1 second, 1 minute, and so on). Each packet becomes a list of numbers "
        "called <b>features</b>. The dataset we use has 115 features per packet, computed the Kitsune way [3]."),
      P("You can picture every packet as a <b>dot in a space</b>: similar behaviour gives nearby dots. Normal traffic "
        "forms a cloud. Attack traffic forms a different cloud, usually far away."),
      KEY("To the detector, each packet is a point. Normal traffic is one cloud of points; attacks are another.")]

# 3
S += [P("CHAPTER 3", "eye"), P("What is an intrusion detection system?", "h1"),
      P("An <b>intrusion detection system (IDS)</b> watches traffic and raises an alarm when something looks like an "
        "attack. There are two kinds:")]
S.append(table([["Kind", "How it works", "Weakness"],
                ["Signature-based", "Keeps a list of known attack patterns, like an antivirus.", "Misses new attacks that are not on the list."],
                ["Anomaly-based (ours)", "Learns what normal looks like, alarms on anything too different.", "Its idea of normal can go stale, or be manipulated."]],
               [3.6 * cm, 6.4 * cm, W - 10 * cm]))
S += [Spacer(1, 6), P("Two numbers judge a detector:")]
S += B(["<b>Recall (detection rate):</b> of all attacks, what share did it catch? Higher is better.",
        "<b>False-positive rate (false alarms):</b> of all normal traffic, what share did it wrongly flag? Lower is "
        "better. Too many false alarms and people switch the detector off."])
S += [KEY("We build an anomaly-based IDS that runs on the device itself, and we judge it by how many attacks it "
          "catches and how few false alarms it raises."), PageBreak()]

# 4
S += [P("CHAPTER 4", "eye"), P("How does a detector learn what 'normal' looks like?", "h1"),
      P("Our detector keeps just two things about normal traffic:")]
S += B(["the <b>centre</b>: the average point of the normal cloud, and",
        "the <b>spread</b>: how wide the normal cloud is."])
S += [P("Anything within a few spreads of the centre is normal. Anything beyond that boundary raises an alarm. "
        "That's the whole detector, which is why it fits on a microcontroller."),
      img("fig_detector.png", W * 0.78), Spacer(1, 4),
      P("Where do the centre and spread come from? From <b>learning</b>: the detector watches traffic it believes is "
        "normal and sets the centre to its average and the spread to its width. This is the machine learning in our "
        "project. It is simple on purpose: the attack we study exploits exactly this kind of learning [1][2]."),
      KEY("The detector is a circle drawn around normal traffic. Inside the circle means normal; outside means alarm."),
      PageBreak()]

# 5
S += [P("CHAPTER 5", "eye"), P("Why must the detector keep learning?", "h1"),
      P("Normal is not fixed. A new device joins the network, a firmware update changes how a camera talks, people "
        "go on holiday. This slow change is called <b>concept drift</b>."),
      P("Real data shows how large it is. CESNET-TimeSeries24 [5] recorded 40 weeks of traffic from a real internet "
        "provider serving about half a million users. An analysis of it found traffic volume dropped about 52% at the "
        "end of the university semester, with significant shifts in most weeks."),
      P("A detector that learned 'normal' once and never updates will start flagging all this new normal behaviour as "
        "attacks. False alarms climb until the detector is useless. So the detector must <b>keep learning</b>: every "
        "so often it updates its centre and spread from recent traffic."),
      KEY("Normal traffic changes over time, so a useful detector has to keep updating what it thinks normal is.")]

# 6
S += [P("CHAPTER 6", "eye"), P("What is poisoning, and what is the boiling-frog attack?", "h1"),
      P("If the detector learns from recent traffic, an attacker can control part of what it learns from. Feeding a "
        "learning system crafted data so it learns the wrong thing is called <b>poisoning</b>."),
      P("The clever version is the <b>boiling-frog attack</b>, named after the story that a frog in slowly heating water "
        "doesn't notice until it's too late. The attacker never sends anything alarming. Instead, each cycle they send "
        "traffic placed just inside the detector's boundary, nudged toward the attack they want to hide. The detector "
        "sees it as normal and learns it. Its centre moves a little and its spread grows a little. Next cycle the "
        "attacker nudges again. Eventually the real attack sits inside the boundary and passes unnoticed."),
      img("fig_boilingfrog.png", W * 0.66), Spacer(1, 4),
      P("This was shown on real network anomaly detectors in the paper <b>ANTIDOTE</b> [1] (2009), which also proposed "
        "a defense for large server-side systems."),
      KEY("The attacker slowly teaches the detector that attacks are normal, one tiny step at a time, without ever "
          "setting off an alarm."), PageBreak()]

# 7
S += [P("CHAPTER 7", "eye"), P("Why are small IoT devices especially at risk?", "h1"),
      P("Kloft and Laskov [2] proved that how far an attacker can push this kind of detector depends on the "
        "<b>attacker's share</b> of the traffic it learns from. With a small share, honest traffic keeps pulling the "
        "detector back. With a large share, the attacker wins."),
      P("On a big network the attacker is a drop in the ocean. But a smart doorbell or plug sends very little traffic "
        "of its own, so an attacker can easily be a large share of what that device's detector sees."),
      P("Our real-data check (Chapter 10) makes this concrete: on real traffic from a smart doorbell, the naive "
        "self-learning detector was poisoned when the attacker was just <b>10%</b> of the traffic."),
      KEY("The quieter the device, the easier it is to poison. IoT devices are quiet.")]

# 8
S += [P("CHAPTER 8", "eye"), P("Why don't existing defenses solve it?", "h1")]
S.append(table([["Approach", "What it does", "Why it falls short"],
                ["Never learn (static)", "Train once, never update.", "Safe from poisoning, but goes stale under drift and drowns in false alarms."],
                ["Learn everything (naive)", "Update from all traffic judged normal.", "Keeps up with drift, but is poisoned (Chapters 6 and 7)."],
                ["Robust statistics on a server (ANTIDOTE [1])", "Uses outlier-resistant maths, retrains in batches.", "Built for large server-side systems, not continuous learning on a small device."],
                ["Freeze when suspicious", "Stops learning when drift looks too big.", "Can be weaponized: see below."]],
               [4 * cm, 5 * cm, W - 9 * cm]))
S += [P("The freeze attack (our finding)", "h2"),
      P("Suppose a defense stops learning whenever drift looks suspicious. An attacker only has to push hard enough to "
        "trip the freeze, then leave. The detector is now frozen, but normal traffic keeps drifting. False alarms "
        "climb and climb until people switch the detector off. The attacker has turned the defense itself into the "
        "attack. We found no prior paper naming this, and it broke our own first design in testing."),
      KEY("Never learning fails, always learning gets poisoned, and freezing can be abused. We need a detector that "
          "keeps learning but can't be steered."), PageBreak()]

# 9
S += [P("CHAPTER 9", "eye"), P("Our idea: Threat-Orthogonal Adaptation (TOA)", "h1"),
      P("The key observation: <b>honest drift can move in any direction, but poisoning must move toward the attack it "
        "wants to hide.</b> A semester-end traffic drop, for example, moves normal away from flood attacks. An "
        "attacker hiding a flood has to drag normal toward floods."),
      P("So TOA looks at every update the detector wants to make and splits it into two parts:")]
S += B(["<b>The sideways or away part</b> (green below): applied in full, straight away. The detector always keeps up "
        "with honest drift and never freezes, so the freeze attack doesn't work on it.",
        "<b>The part toward a known attack</b> (red below): allowed only up to a small, slow budget learned from clean "
        "traffic. The attacker's only useful direction is rationed."])
S += [img("fig_toa.png", W * 0.72), Spacer(1, 4),
      P("'Orthogonal' is the maths word for 'at right angles to'. The safe part is the part at right angles to the "
        "threat direction, hence the name."),
      P("The guarantee", "h2"),
      P("Because the gap between normal and a known attack can shrink by at most a fixed budget per cycle, we can "
        "compute a <b>minimum number of cycles</b> before that attack could be hidden, however clever the attacker is. "
        "In our simulation that minimum was 678 cycles, while the naive detector fell in 24."),
      P("Why it fits on an ESP32", "h2"),
      P("Splitting an update needs one dot product and one distance per known attack. That's a handful of "
        "multiplications, tiny even for a microcontroller."),
      KEY("Let normal move anywhere except toward known attacks. Honest change is learned freely; the attacker's "
          "only useful move is rationed."), PageBreak()]

# 10
S += [P("CHAPTER 10", "eye"), P("How we tested it, and what we found", "h1"),
      P("Test 1: simulation (synthetic data)", "h2"),
      P("We first built a simulated world with drift and a boiling-frog attacker controlling 40% of traffic, and "
        "compared five detectors over 5 random seeds.")]
S.append(img("fig_slide.png", W, EXP))
S += [Spacer(1, 4), table([["Detector", "Attack still detected", "False alarms"],
                          ["Naive learning", "0% after 24 cycles", "0%"],
                          ["Consistency filter", "100%", "85%"],
                          ["Freeze budget", "100%", "87%, never recovers after the attacker leaves"],
                          ["TOA (ours)", "100%", "0.3%"]], [4.6 * cm, 4 * cm, W - 8.6 * cm]),
      P("Test 2: real IoT traffic (N-BaIoT)", "h2"),
      P("Then we used <b>real data</b> from N-BaIoT [4]: 49,548 packets of normal traffic from a real Danmini smart "
        "doorbell, and real Mirai attack traffic from the same doorbell. The only simulated part is the poisoner, "
        "because no dataset contains poisoning: each poison packet is a mix of a real normal packet and a real attack "
        "packet, placed just inside the boundary.")]
S.append(img("nbaiot_results.png", W, EXP))
S += [Spacer(1, 4), table([["Result on real doorbell traffic", "What it means"],
                          ["Naive learning was poisoned with the attacker at only 10% of traffic (Mirai scan detection fell to about 5%).", "Real IoT traffic is tightly clustered, so it is even easier to poison than our simulation suggested."],
                          ["TOA kept 100% detection at every attacker share from 10% to 50%, for three different Mirai attacks (scan, ack, syn).", "The defense holds on real traffic, not just synthetic."],
                          ["TOA's false alarms stayed about 0.8%, the same as a detector that never learns.", "The protection costs essentially nothing in false alarms."]],
                         [W * 0.55, W * 0.45]),
      P("An honest limit we found", "h2"),
      P("We also let a second real device (an Ecobee thermostat) join the network midway. Every detector, even with no "
        "attacker at all, then showed about 34% false alarms. The reason: a detector that only learns from traffic it "
        "already accepts can never learn a completely different device, whose traffic always looks foreign. This is "
        "not a TOA problem but a detector-design lesson: keep <b>one detector per device</b>, which is also how "
        "N-BaIoT's authors built theirs [4]."),
      KEY("In simulation and on real IoT traffic, TOA keeps attacks visible while naive learning is poisoned, at almost "
          "no false-alarm cost. Next we must handle new devices properly and move to the ESP32."), PageBreak()]

# 11
S += [P("CHAPTER 10B", "eye"), P("Can it work without a list of attacks?", "h1"),
      P("The version above needs a <b>signature</b> for each attack it protects: one reference point, such as the "
        "average of Mirai scan traffic. A fair question is whether that is just hard-coding. So we built a version "
        "that needs no signatures at all. It relies on a footprint that poison cannot avoid:"),
      ]
S += B(["<b>Learn from the dense middle only.</b> Poison has to sit near the boundary to have any pull without "
        "raising alarms. If the detector learns only from the dense core of traffic, that poison is ignored.",
        "<b>Accept a shift only if the whole cloud moves.</b> Honest change moves all of the traffic, including the "
        "outer ring. Poison moves only one part. A shift of the centre that the outer ring does not back up is scaled down.",
        "<b>Widen the boundary only if the outer ring really gets busier.</b> A smart attacker who hides poison inside "
        "the core tries to inflate the spread instead; this check blocks that."])
S += [table([["Test", "Signature-free result"],
             ["Real doorbell traffic, normal attacker, 10 to 50% share", "100% detection of Mirai scan, ack and syn; about 1% false alarms"],
             ["Real doorbell traffic, smart attacker who knows the defense and hides poison in the core", "100% detection; 0.2 to 0.3% false alarms"],
             ["Synthetic: strong honest drift and the attack at the same time", "Still poisoned (2 to 46% detection). Open problem"]],
            [W * 0.55, W * 0.45]),
      KEY("The defense can work without a list of attacks, and it beat both attackers on real IoT traffic. The hard "
          "case left is an attacker hiding inside genuine, large drift. Our plan: signature-free by default, "
          "signatures as an extra safety floor for the most important attacks."), PageBreak()]

S += [P("CHAPTER 11", "eye"), P("What we will do next", "h1")]
S.append(table([["When", "Work"],
                ["Weeks 1 to 3", "Per-device detectors on N-BaIoT; more devices and attacks; attacker share taken from real device traffic rates."],
                ["Week 4 (mid-review)", "Full real-data comparison with all baselines, including ANTIDOTE's robust PCA."],
                ["Weeks 5 to 7", "Port the detector and TOA to the ESP32; measure memory, latency and energy. Study the freeze attack with real long-term drift from CESNET-TimeSeries24 [5]."],
                ["Weeks 8 to 9", "Parameter sweeps, the IEEE-format report, code and a live demo."]],
               [3.6 * cm, W - 3.6 * cm]))
S += [P("Open questions we will be honest about", "h2")]
S += B(["<b>Attacks hidden inside strong drift:</b> the signature-free version is still poisoned when heavy honest "
        "drift and the attack happen together (Chapter 10B). This is the main open research question.",
        "<b>Honest drift toward an attack:</b> TOA then slows learning in that direction; in simulation false alarms "
        "peaked near 7% and recovered.",
        "<b>Realism of the attacker:</b> our poison mixes real normal and real attack packets; a live attacker on real "
        "hardware is a stretch goal."])
S.append(PageBreak())

# 12
S += [P("CHAPTER 12", "eye"), P("The five papers, a glossary, and where everything lives", "h1"),
      P("The five papers, in reading order for a beginner", "h2")]
PAPERS = [
    ("[4] N-BaIoT (IEEE Pervasive Computing, 2018)", "Real traffic from 9 infected IoT devices. Read first: it shows what IoT attacks look like.", "https://arxiv.org/abs/1805.03409"),
    ("[3] Kitsune (NDSS, 2018)", "How to turn packets into features and detect anomalies on small devices.", "https://arxiv.org/abs/1802.09089"),
    ("[1] ANTIDOTE (ACM IMC, 2009)", "The boiling-frog attack on network detectors, and a server-side defense.", "https://people.eecs.berkeley.edu/~tygar/papers/SML/IMC.2009.pdf"),
    ("[2] Kloft and Laskov (JMLR, 2012)", "The maths of how far an attacker can push a learning detector.", "https://jmlr.csail.mit.edu/papers/volume13/kloft12b/kloft12b.pdf"),
    ("[5] CESNET-TimeSeries24 (Scientific Data, 2025)", "40 weeks of real traffic showing how normal drifts.", "https://www.nature.com/articles/s41597-025-04603-x"),
]
for t, why, u in PAPERS:
    S.append(P(f"<b>{t}</b><br/>{why}<br/>{link(u)}", "b"))
S += [P("Glossary", "h2")]
S.append(table([["Term", "Meaning"],
                ["Anomaly detection", "Learning what normal looks like and flagging what is too different."],
                ["Botnet / Mirai", "An army of hijacked devices; Mirai is a famous IoT botnet."],
                ["Concept drift", "Normal behaviour slowly changing over time."],
                ["Poisoning", "Feeding a learning system crafted data so it learns the wrong thing."],
                ["Boiling-frog attack", "Poisoning in tiny steps that never trigger an alarm."],
                ["Attacker's share", "The fraction of the learning data the attacker controls."],
                ["Freeze attack", "Tripping a defense that stops learning, so drift makes it useless (our finding)."],
                ["TOA", "Threat-Orthogonal Adaptation: learn freely except toward known attacks (our method)."],
                ["Recall", "Share of attacks caught."],
                ["False-positive rate", "Share of normal traffic wrongly flagged."],
                ["ESP32", "A cheap, popular microcontroller with Wi-Fi, used in many IoT devices."]],
               [4 * cm, W - 4 * cm]))
S += [P("Where everything lives", "h2")]
S += B(["Repository: " + link("https://github.com/IOT-snu/brainstorming"),
        "<b>topic-proposal.md</b>: the formal proposal.",
        "<b>notes/Presentation_and_Study_Notes.pdf</b>: slide script and Q&A preparation.",
        "<b>experiments/sim_toa.py</b>: the simulation. <b>experiments/nbaiot_check.py</b>: the real-data check.",
        "<b>literature-review.md</b> and <b>research-findings.md</b>: the wider reading and how the design evolved."])

doc.build(S)
print("wrote", os.path.join(HERE, "Readup_From_Zero.pdf"))
