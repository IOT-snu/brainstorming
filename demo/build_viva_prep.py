"""
Builds G04_Viva_Prep.pdf: for every slide of G04_FOA_Final.pptx, what to say, what it means, and the questions
to expect with answers; then the maths, hard questions, a glossary and a number sheet. Run: python3 demo/build_viva_prep.py [preview_dir]
preview_dir: slide PNGs written by build_final_deck.py (use --blurred, this PDF is shared).
"""
import os, sys
from pptx import Presentation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PREV = sys.argv[1] if len(sys.argv) > 1 else None
F = "/System/Library/Fonts/Supplemental/"
for n, f in (("A", "Arial.ttf"), ("AB", "Arial Bold.ttf"), ("AI", "Arial Italic.ttf")):
    pdfmetrics.registerFont(TTFont(n, F + f))
pdfmetrics.registerFontFamily("A", normal="A", bold="AB", italic="AI", boldItalic="AB")
INK, BLUE, GREY, SOFT, LINE = [colors.HexColor(c) for c in ("#1D1D1F", "#0071E3", "#6E6E73", "#F5F5F7", "#E3E3E8")]
S_ = lambda n, **k: ParagraphStyle(n, **{**dict(fontName="A", fontSize=9.8, leading=13.8, textColor=INK, spaceAfter=3), **k})
title = S_("t", fontName="AB", fontSize=22, leading=27)
h1 = S_("h1", fontName="AB", fontSize=14, leading=18, spaceBefore=12, spaceAfter=6)
lab = S_("l", fontName="AB", fontSize=8.5, textColor=BLUE, spaceBefore=4, spaceAfter=1)
p = S_("p"); small = S_("s", fontSize=8.8, textColor=GREY)
eq = S_("eq", fontName="AB", fontSize=10.2, leading=15, spaceAfter=2)
say = S_("say", backColor=SOFT, borderPadding=7, leftIndent=7, rightIndent=7, spaceBefore=4, spaceAfter=10)
spk = S_("spk", fontName="AB", fontSize=10, textColor=colors.HexColor("#D70015"), spaceAfter=6)
cell = S_("c", fontSize=8.8, leading=11.8, spaceAfter=0); cellb = S_("cb", fontName="AB", fontSize=8.8, leading=11.8, spaceAfter=0)
P = Paragraph
W = A4[0] - 4 * cm


def table(rows, widths, head=True):
    t = Table([[P(c, cellb if (head and i == 0) or j == 0 else cell) for j, c in enumerate(r)] for i, r in enumerate(rows)], colWidths=widths, repeatRows=int(head))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)] + ([("BACKGROUND", (0, 0), (-1, 0), SOFT)] if head else [])))
    return t


def formulas(i):
    if i not in FORM:
        return []
    rows = [[P(n, cellb), [P(f, eq), P("<b>where</b>  " + v, small)]] for n, f, v in FORM[i]]
    t = Table(rows, colWidths=[4.0 * cm, W - 4.0 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return [P("FORMULAS, WITH VARIABLES", lab), t, Spacer(1, 6)]


# per slide: (meaning in simple words, [(question, answer), ...])
Q = [
 ("The one-line project: a detector that keeps learning but is hard to fool.",
  [("What is your project in one sentence?", "An on-device intrusion detector for IoT that keeps learning from changing traffic while limiting how far an attacker can poison it, using other devices as witnesses."),
   ("Why is it an IoT project and not just ML?", "It runs on microcontrollers, learns from each device's own network traffic, shares updates over ESP-NOW, and we measured time, memory and power on real boards.")]),
 ("Three bad choices: trust yourself (poisoned), stop when suspicious (frozen), never learn (false alarms).",
  [("What is drift?", "Normal traffic changing over time: a router or tunnel change, new polling rates, firmware updates."),
   ("What is the boiling-frog attack?", "Poisoning in tiny steps. Each step is accepted as normal, moves the boundary, and lets the next step sit further out until the real attack is accepted. Studied by ANTIDOTE (2009)."),
   ("What is the freeze attack?", "Send loud junk so a defence that pauses on suspicion stops learning. Leave. Honest drift continues and the paused detector keeps raising false alarms."),
   ("Where does 78% come from?", "A detector that never learns, after our strong simulated network change on N-BaIoT traffic.")]),
 ("Honest change hits many devices, an exploit hits few. So neighbours help tell them apart.",
  [("Why would neighbours see the same change?", "They share the gateway, tunnel and services. That is an assumption: change affecting only one device is not covered."),
   ("What is a geometric median and why not an average?", "The point with the smallest total distance to all inputs. One extreme value can drag an average anywhere; fewer than half bad inputs cannot drag the geometric median far."),
   ("Which neighbours are used?", "Devices from other vendors, so a single exploit is unlikely to control many of them."),
   ("Why a hospital example?", "Hospitals mix many device makers on one network and change it often (gateways, updates), and an attack there must not hide inside routine change. The example is illustrative; our tests used N-BaIoT, CESNET and our boards.")]),
 ("The loop every device runs, as a flowchart: score, drop alarmed samples, propose from the clean core, sign and share, take the neighbours' middle, check w and λ, split, cap with budgets, move normal.",
  [("What is the detector?", "An online centroid detector: score = distance of a sample from the learned centre divided by the learned spread. Alarm if the score exceeds the 99th percentile of clean calibration data."),
   ("What are the 16 numbers?", "Traffic statistics (Kitsune style: packet sizes, rates, gaps over several time windows) log-scaled, standardised and projected onto 16 shared directions."),
   ("Is it supervised? Do you need attack labels?", "No labels and no attack signatures. It learns from traffic it judges normal."),
   ("What does 'as far as my traffic agrees' mean?", "The backed part is scaled by w (is the neighbours' change real?) and lambda (does my own core traffic move the same way?), and it is kept within a larger common budget, 0.75 + 0.06 t alarm radii."),
   ("Why HMAC?", "So a device without the key cannot forge a neighbour's message; old messages are rejected as stale. In our test, without authentication a keyless forger compromised the victim in every run."),
   ("What is the budget?", "A limit on total device-only movement that grows slowly with time: B0 + B t, in units of the alarm radius. B0 = 0.1, B = 0.005 per cycle."),
   ("Why do alarmed samples never get learned?", "Because an attacker's loud traffic would otherwise pull the detector. Only accepted samples, and for the update only the clean core, are used.")]),
 ("Four guarantees: bounded movement, limited push from bad peers, no stop switch, unforgeable messages.",
  [("State your main theorem simply.", "An attacker controlling only one device's traffic can move its centre at most (B0 + B t) alarm radii beyond what neighbours back, and the spread is bounded similarly. So there is a minimum time before an attack can hide."),
   ("How is it proved?", "By construction: the device-only part is projected onto a ball whose radius is the budget, after every cycle. The triangle inequality then gives the time to compromise."),
   ("How many bad neighbours can you tolerate?", "Fewer than half only bounds the push per cycle; it is not immunity. In tests, bad neighbours alone never won, but with a traffic poisoner 3 of 7 compromised 56% of victims. The bound also needs at least 3 peers: on our 3 boards each device has 2, so the theorem says nothing there."),
   ("Is the time bound strong?", "It is a delay, not a wall. With our defaults an attack 2 alarm radii away needs at least about 130 cycles: about 17 minutes at the boards' 7.8 s cycle, or about 5.5 days at one cycle per hour. A patient attacker on one device always wins eventually, which our impossibility result says no rule can avoid."),
   ("So FOA never stops learning?", "No gate stops it. But it learns only from accepted traffic, so if all traffic suddenly lands outside the alarm radius there is nothing to learn from. The boards showed this when their traffic rate doubled at once."),
   ("What does unforgeable mean exactly?", "Each frame carries a 16-byte HMAC-SHA256 tag. A device without the key cannot forge a neighbour's update, and stale frames are rejected. In simulation, without authentication a keyless forger compromised the victim in every run."),
   ("Is there anything no rule can do?", "If only one device changes, the same observations could come from honest drift or from poisoning, so no rule can separate them.")]),
 ("Safer across attacks and conditions: FOA against a device learning alone, both with the floor, in five settings.",
  [("What does each bar mean?", "The share of attacked runs where the target attack went undetected (compromised). Grey: a device learning alone. Blue: FOA. Lower is better."),
   ("What is the classic slow poisoner?", "An attacker who places poison just inside the edge of the normal zone and pushes it outward a little each cycle (the boiling frog). FOA's budget stopped it every time."),
   ("What is hiding in the clean core?", "An attacker who places poison inside the central part of normal traffic, so it is used for learning. Harder to stop; FOA still cuts it from 36.8% to 11.8%."),
   ("Why 100% vs 0% for the botnet?", "Most devices of one model are infected and push the same way. A lone device learns the poison; FOA's neighbours come from other vendors and do not back it."),
   ("Is there any attack where FOA is not better?", "An attacker who imitates the shared network change: about 16% for both. Not on this slide; say it plainly if asked."),
   ("Where do the numbers come from?", "Simulation on real N-BaIoT traffic and attacks, held-out seeds 2 to 11, 7,310 runs (experiment E12).")]),
 ("How we differ from the closest earlier work.",
  [("Isn't this just CIoTA?", "CIoTA uses peers of the same model and discards what they do not agree on. We use other vendors, admit the rest within a budget, and bound attacker movement. Under a one-model botnet, our version of same-model consensus failed and ours held."),
   ("Are you the first?", "We do not claim first. We found no prior work combining these, and several related 2026 works are preprints."),
   ("What does 'Not analysed' mean for CIoTA freezing?", "The CIoTA paper does not study a freeze attack. We do, and FOA has no switch an attacker can trip."),
   ("Did you run the real CIoTA?", "No. We re-implemented its consensus idea around our detector."),
   ("What is the closest work you found?", "Structurally, a consensus method with a norm-limited local step by Chen, Kar and Moura (a preprint), BALANCE (CCS 2024) and ClippedGossip. They aim at a fixed target with a shrinking tolerance, so they would reject honest change that arrives late; we have not tested them. A Darktrace patent already compares devices with their peers so compromised ones are not learned as normal. We found no prior work combining a peer-backed split, a growing budget with a time-to-compromise bound and a freeze analysis.")]),
 ("What data we used and what is simulated.",
  [("Is your data real?", "N-BaIoT has real traffic and real attacks. CESNET has real traffic and drift, but the attack on it is modelled by us. The fleet running together, the injected drift on N-BaIoT and the poisoner are simulated. N-BaIoT devices were recorded separately."),
   ("Which attacks?", "Real Mirai and BASHLITE traffic; the poisoner targets scan traffic, the closest to benign."),
   ("How did you avoid tuning on the test?", "Design choices used development seeds 0 and 1; reported results use seeds 2 to 11."),
   ("What does compromised mean?", "Fewer than half of the held-out attack packets raise an alarm, and the same run without the attacker still detects them."),
   ("Did you exclude any device as a victim?", "Yes. A victim's attack must be at least 1.3 alarm radii from benign traffic; Philips and SimpleHome 1002 fail this and stay as neighbours.")]),
 ("The headline: about 4 times fewer compromises when poisoning hides inside network change.",
  [("Why hide it inside drift?", "During a real change the detector has to move, which gives the poisoner cover."),
   ("Why is single device + floor worse here?", "The floor keeps the normal region wider than a shrunken one, so a few more attacks fit inside it: 43.1% against 39.2%."),
   ("Is this simulation?", "Yes: real N-BaIoT traffic and attacks, with the fleet, drift and poisoner simulated, on held-out seeds."),
   ("Why 4 times?", "39.2% / 10.8% is about 3.6, and 43.1% / 9.4% about 4.6."),
   ("Why is FOA not 0%?", "Stealthy poisoners that hide in the core or imitate drift still win in some runs. The classic boundary poisoner never did.")]),
 ("Every rule as a dot: left is fewer false alarms, down is fewer compromised. FOA is closest to the bottom-left without knowing the attack. These numbers are without the floor.",
  [("Learn-everything has only 2.6% false alarms. Why not use it?", "It accepts everything, including poison: 35% compromised, and 83% for the classic slow poisoner."),
   ("TOA is safer than FOA. Why drop it?", "It was given the true attack signature, which a real device does not have, and it has 38% false alarms."),
   ("Why n/a for never learn?", "A detector that never learns cannot be poisoned, so compromise does not apply."),
   ("Are those baselines the published systems?", "No, they are our re-implementations of each gating idea around the same detector, so differences come from the update rule."),
   ("Why is never learn at 0% compromised?", "It cannot be poisoned because it never learns, but it raises 78% false alarms after a network change, so it is unusable.")]),
 ("Three attacks that break other defences: one-model botnet, freeze, and 40 weeks of real change.",
  [("Are these numbers good or bad?", "0% is compromise of our method, so good. The red 100% is the false alarm rate of the alarm-rate switch-off defence, so bad for that defence."),
   ("What does 'run without the floor' mean?", "These tests used the original rule, before we added the minimum limit on the spread. We have not re-run them with it."),
   ("Explain the botnet test.", "Three cameras of one model are infected and poisoned together. Same-model peers agree with the poison. Other-vendor peers do not."),
   ("Which defence did the freeze attack beat?", "An alarm-rate switch-off: 100% false alarms with decoys at 5% share, 26% without the attacker. The outlier-ratio gate we tested recovered, so not every gate freezes."),
   ("What is CESNET?", "40 weeks of traffic statistics from a national research network. Drift is real; the attack there is modelled."),
   ("Was FOA the best on CESNET?", "Not on false alarms: a detector that never learns had 5.9% against FOA's 9.1%, and it cannot be poisoned. That drift was mild, so adapting was not needed. CESNET shows FOA is safe on real drift, not that it is needed there.")]),
 ("A photo of the real setup.",
  [("Point to each part.", "The ESP8266 boards, the INA226 sensor and its wiring, the USB hub and cables, and the recording laptop. Practise pointing at them on the photo before the talk."),
   ("Which board is measured?", "Node 1: its 5 V line runs through the INA226. Node 0 reads the sensor over two I2C wires."),
   ("Is the sensor wired in series or parallel?", "In series: only the red 5 V wire of Node 1's cable goes through the 0.1 ohm shunt.")]),
 ("It runs on a tiny board: timing, communication and power measured on ESP8266.",
  [("Which boards?", "Three ESP8266 NodeMCU boards (single core, about 80 KB RAM; our firmware uses about 51 KB). We also compiled for ESP32."),
   ("Why ESP-NOW?", "Direct short broadcasts between boards without a broker, up to 250 bytes; our message is 92 bytes."),
   ("How did you measure power?", "INA226 across a 0.1 ohm shunt in one board's 5 V line: about 72 mA, 365 mW in the first session and 382 to 391 mW in the later runs. Almost all of it is the radio and the board's normal draw."),
   ("How much energy does FOA cost?", "We could not detect extra energy at the sensor's 40 ms resolution. Computing takes about 14 ms per cycle in the first runs and about 25 ms in the later ones; at full board power that is at most about 5 to 10 mJ per cycle, an upper bound, not a measurement."),
   ("What bugs did hardware reveal?", "Calibrating before statistics settled, rejecting frames because boards had different cycle numbers, an unexpected sensor address, and a logger crash on Windows."),
   ("Did you attack the boards?", "The boards were used to measure cost and behaviour under real traffic; the attack results come from simulation on real IoT traffic. Board attack trials (slow poisoning, decoys, forged frames) are the next step. Say this plainly if asked.")]),
 ("Hardware showed what simulation could not: identical boards agreed on shrinking normal; one rule (the floor) fixed it; a calibration timing fix brought board false alarms to about 1.6%.",
  [("What exactly collapsed?", "The spread, so the acceptance region. Connected boards: under 2% in 20 minutes, about 90% false alarms."),
   ("Does this break your theorem?", "No. The theorem limits how far an attacker can widen or move the detector. It said nothing about shrinking, which hurts false alarms, not security."),
   ("Why would core-only learning shrink?", "It estimates spread from the central part of traffic. Repetitive traffic makes that part tight, points drop out, and it tightens again. Growth is gated; shrinking was not."),
   ("Why does agreement make it worse?", "Identical boards shrink in the same way, so the shared channel treats it as real common change."),
   ("What else might contribute?", "The board feature basis is a placeholder not fitted on their traffic, and the detector centre also drifted. Later runs found calibration aliasing: calibration kept every 10th 50 ms sample, in step with the 200 ms telemetry, so it saw only some phases of the traffic."),
   ("What is the coverage floor?", "The spread may never go below its calibrated value."),
   ("Can an attacker exploit it?", "It only cancels shrinking, so the budget bounds still hold. It can keep the detector wider than a shrunken one, which cost a single device a few points."),
   ("Did it work on the boards?", "For the spread, yes: in the 27 November runs it never fell below its calibrated value. False alarms stayed near 25% until we fixed a calibration bug; then they were 1.5 to 1.7%. The bars on this slide are simulation."),
   ("What changed since the collapse?", "The firmware now has the floor, Wi-Fi connects properly so both peers are heard in most cycles, and calibration samples are spaced unevenly."),
   ("What is calibration aliasing?", "Calibration kept every 10th sample, one every 500 ms. The telemetry repeats every 200 ms, so calibration only ever saw two of its four phases and the others looked abnormal. Gaps of 9, 9, 9 and 13 samples cover all four."),
   ("Why did the sudden jump break everything?", "Doubling the rate moved all traffic outside the alarm radius, so nothing was accepted and nothing could be learned, with or without peers. Any rule that learns only from accepted traffic is stuck then. FOA follows gradual change; a sudden large step needs a separate, safe recovery rule."),
   ("How reliable are these numbers?", "Single runs, each with its own calibration, so descriptive. A never-learning detector was not rerun with the fixed calibration, so we cannot yet say what adaptation itself adds on the boards."),
   ("Is finding a failure a bad thing?", "No. It is a measured problem with a reproduced cause and a fix that held on every board. Simulation alone would never have shown it."),
   ("Does the floor hurt anything?", "It only cancels shrinking, so the attack bounds still hold. With the floor, a single device has slightly fewer false alarms than FOA in simulation (0.8% vs 2.5%); FOA's advantage is safety: 9.4% vs 43.1% compromised.")]),
 ("What makes FOA practical: no labels, tiny messages, fast, cross-vendor, cannot be frozen, proven limits.",
  [("Why no labels?", "It learns from traffic it judges normal; no attack signatures or labelled data are needed."),
   ("Is 92 bytes per cycle a lot?", "No. ESP-NOW allows 250 bytes; one broadcast per cycle per device, no server or cloud."),
   ("Why does cross-vendor matter?", "One exploit usually targets one device model, so it is unlikely to control neighbours from other makers. Same-model voting failed completely under a one-model botnet; ours held."),
   ("What exactly is proven?", "That one compromised device can move its detector at most (B0 + B t) alarm radii beyond what neighbours back, and that fewer than half bad peers add only a limited push per cycle.")]),
 ("Where FOA fits: smart buildings and campuses, industrial networks, hospitals, and security platforms that already compare devices with peers.",
  [("Is this revolutionary?", "It changes how a fleet of detectors can keep learning safely: it uses the fleet itself as a witness, with a proven limit on what one compromised device can do. We found no prior work combining these. Avoid the word first."),
   ("Why not just use an allow-list?", "For single-purpose devices an allow-list such as MUD (RFC 8520) is better: it cannot be poisoned. Anomaly detection matters where normal behaviour is too varied or changes too often to list."),
   ("Have you tested these settings?", "Not yet; they are the target deployments. Our evidence is real IoT and network traffic plus the boards."),
   ("Where would you deploy it?", "On a gateway or edge box, one detector per device, so an infected device cannot switch it off, with many peers and someone acting on the alarms."),
   ("Do companies already do something like this?", "Peer comparison, yes: Microsoft Sentinel's UEBA compares entities with their peers, and a Darktrace patent uses peers so that compromised devices are not learned as normal. What we add is a rule for when a baseline may move, with a bound."),
   ("Your false alarms are 1 to 2.5%. Is that usable?", "Not as raw per-sample alarms: at 20 samples a second that is thousands per day. A deployment would raise one alert per device when a cycle's alarm share is high; we have not evaluated alert rates yet.")]),
 ("How we got here: learn alone, pause when suspicious, TOA, FOA, coverage floor, on the boards. Each idea fixed the weakness of the one before.",
  [("What was TOA?", "Threat-Orthogonal Adaptation, our first method. It refused to move toward known attack directions. Very safe (5.5% compromised) but it needed the attack signature in advance, which a real device does not have."),
   ("Why did you move from TOA to FOA?", "To remove the need to know the attack. FOA uses neighbours as witnesses instead of attack knowledge."),
   ("What did the boards add?", "They exposed the shrinking problem that led to the coverage floor, and gave real timing, communication and power numbers.")]),
 ("Six recent papers and what each gave us.",
  [("Did you copy their methods?", "We implemented simplified versions of two ideas as baselines: a gate using DriftXpert's outlier-ratio statistic (DriftXpert itself uses it to trigger retraining, not to pause) and WARDEN-style frozen-reserve screening. The others shaped motivation, threat model or design reasoning."),
   ("Are all of these peer reviewed?", "No. Su et al. (ICLR 2025) and Rapid Poison (ICML 2026) are; the other four are preprints, marked on the slide."),
   ("Which are the core foundations?", "The older works on the previous slide: ANTIDOTE, Kloft and Laskov, CIoTA, N-BaIoT and CESNET."),
   ("How is RTTAD different from you?", "It adapts a batch of test data in rounds, using confidently normal and confidently abnormal samples, with no attacker. Its rounds end when too few confident samples remain, which the paper does not define precisely. We work on a stream, learn only from accepted traffic, assume an attacker and limit movement with budgets.")]),
 ("Close and sources.",
  [("Which paper influenced you most?", "Kloft and Laskov (2012): the same centroid detector, and the result that the attacker's share of traffic bounds poisoning."),
   ("Why no years in the citations on the slide?", "Only for a clean slide; full references with years are in the report."),
   ("Who did what?", "Answer truthfully for your own team. Agree on this before you walk in.")]),
 ("Two research questions and four hypotheses, each with the result that supports it.",
  [("Say the research question.", "Can a fleet of self-learning detectors keep following honest change while limiting how fast an attacker on one device can poison its detector, without a stop switch an attacker could trip?"),
   ("Say RQ2.", "Does FOA hold up against the attacks that defeat existing defences: a botnet that takes over most devices of one model, and a freeze attack?"),
   ("What supports H4?", "Under a one-model botnet FOA was compromised in 0% of runs against 100% for same-model voting once two of three cameras were infected; 5% decoy traffic locked a stop-learning defence at 100% false alarms, while FOA's behaviour was unchanged because alarmed samples never enter its update."),
   ("Why is H2 supported if FOA has more false alarms than a lone device?", "H2 asks whether FOA follows change closely, not whether it beats a lone device on false alarms: 2.5% against 0.8% is within 2 points, while FOA is far safer (9.4% vs 43.1% compromised with the floor)."),
   ("Which gated defences are the 27 to 30%?", "Frozen reference 27%, limit each step 30%, stop on many alarms 30%, all under strong shared change."),
   ("Is H3 about energy too?", "Yes: the extra energy for learning was too small for our INA226 to detect; the board drew 365 to 391 mW, mostly the radio."),
   ("Were the hypotheses set before the results?", "Answer truthfully: they state what the method was designed to achieve; the numbers come from held-out runs not used in design.")]),
 ("Open limits and next steps.",
  [("Biggest weakness?", "A device with a large change of its own is learned slowly, and a sudden jump outside the normal region leaves nothing to learn from."),
   ("Why does a sudden jump stall learning?", "FOA learns only from accepted traffic. If all traffic jumps outside the alarm radius at once, nothing is accepted. On the boards this happened when every board doubled its traffic rate together. A safe recovery rule is next."),
   ("Why is three boards a limit?", "The bad-peer bound needs at least 3 peers; with 3 boards each has 2."),
   ("What would you do with more time?", "Attack the boards (slow poisoning, decoys, forged and replayed messages) with attacker-free twins and repeats; add a safe way to recover from sudden jumps; move the detector to a gateway with per-source statistics; compare with BALANCE and ClippedGossip; and use different device types as neighbours.")]),
]

# per slide: [(name, formula, labelled variables), ...]
SCORE = ("Anomaly score and alarm", "score(x) = ||x − μ|| / s<br/>alarm if score(x) &gt; τ",
         "x: one traffic sample (16 numbers). μ: learned centre of normal. s: learned spread. ||·||: length of a vector. τ: threshold, the 99th percentile of clean calibration scores.")
FPR = ("False alarm rate", "FPR = benign samples that raise an alarm / all benign samples",
       "Measured on benign traffic the detector did not learn from. Lower is better.")
COMP = ("Compromised", "detection = attack packets flagged / all attack packets<br/>compromised if detection &lt; 0.5",
        "Measured on held-out target attack packets, and only counted if the same run without the attacker still detects them.")
FLOOR = ("Coverage floor", "s(t) ≥ s<super>0</super>",
         "s(t): spread at cycle t. s<super>0</super>: spread at calibration. Only shrinking is cancelled.")
RES = ("Residual budget", "r = d − a<br/>||R(t)|| ≤ (B<sub>0</sub> + B·t)·ρ",
       "d: my proposed centre shift. a: accepted common part. r: residual, mine alone. R: all residual movement added up. t: cycle number. B<sub>0</sub> = 0.1: starting allowance. B = 0.005: growth per cycle. ρ = τ·s<super>0</super>: calibrated alarm radius.")
FORM = {
 2: [SCORE, ("Learning step (single device)", "μ ← μ + d", "d: the centre shift the device proposes from traffic it did not alarm on. Poisoning works by steering d a little each cycle."), FPR],
 3: [("Geometric median of neighbours", "m = argmin<sub>y</sub> Σ<sub>j</sub> ||y − d<sub>j</sub>||",
      "d<sub>j</sub>: update sent by neighbour j. y: candidate point. m: the point with the smallest total distance to all d<sub>j</sub> (found with 10 Weiszfeld iterations)."),
     ("Split of my update", "d = a + r", "a: part neighbours and my traffic support (large budget). r: the rest (small budget).")],
 4: [SCORE,
     ("Propose (from core traffic)", "core: accepted samples with score ≤ c<br/>d = η·(mean(core) − μ)·support<br/>e = change in log s",
      "c: 80th-percentile clean score. η = 0.5: step size. support: 0 to 1, how far the outer ring moves with the core. d: centre shift. e: log-spread change (growth allowed only if the outer ring backs it)."),
     ("Share", "tag = first 16 bytes of HMAC-SHA256(key, message)", "key: the sender's secret key. message: header, 16 values of d, and e. Whole frame: 92 bytes."),
     ("Agree: smoothed consensus", "m<sub>avg</sub> ← (1 − α)·m<sub>avg</sub> + α·m", "m: geometric median this cycle. m<sub>avg</sub>: its running average. α = 0.2."),
     ("Is it real? weight w", "σ = median<sub>j</sub> ||d<sub>j</sub> − m|| / √K<br/>z = ||m<sub>avg</sub>|| / (σ<sub>avg</sub>·√(α/(2 − α)))<br/>w = clip((z − 2) / 2, 0, 1)",
      "K: number of neighbours. σ: noise this cycle. σ<sub>avg</sub>: σ smoothed like m<sub>avg</sub>. z: signal divided by noise. w: 0 below z = 2, 1 above z = 4."),
     ("Do I see it too? agreement λ", "g = η·median<sub>x in core</sub> (x − μ)·u,  u = m<sub>avg</sub> / ||m<sub>avg</sub>||<br/>λ = clip(g<sub>avg</sub> / ||m<sub>avg</sub>||, 0, 1)",
      "u: direction of the consensus. g: how far my core traffic moved along it. g<sub>avg</sub>: g smoothed."),
     ("Split and apply", "a = w·λ·m<sub>avg</sub>, kept within ||C|| ≤ (0.75 + 0.06·t)·ρ<br/>r = d − a, kept within ||R|| ≤ (0.1 + 0.005·t)·ρ<br/>μ ← μ + a + r",
      "C: all common movement added up. R: all residual movement added up. If fewer than 2 neighbours are heard, a = 0.")],
 5: [("What the detector contains", "μ(t) = μ<super>0</super> + C(t) + R(t)<br/>log(s(t)/s<super>0</super>) = C<sub>s</sub>(t) + R<sub>s</sub>(t)",
      "μ<super>0</super>, s<super>0</super>: calibrated centre and spread. C, C<sub>s</sub>: common movement and spread change. R, R<sub>s</sub>: residual movement and spread change."),
     RES, ("Spread budget", "|R<sub>s</sub>(t)| ≤ 0.1 + 0.001·t", "Limit on my own spread change, in log units."),
     ("Earliest compromise (approximate, no common movement)", "t* ≈ (M − 1 − B<sub>0</sub> − B<sub>0</sub><super>s</super>) / (B + B<super>s</super>)",
      "M: distance of the attack in alarm radii. B<sub>0</sub><super>s</super> = 0.1 and B<super>s</super> = 0.001: spread budget start and growth. Valid for small budgets."),
     ("Bad neighbours", "||m − m<super>H</super>|| ≤ C<sub>f/K</sub>·r,  C<sub>β</sub> = (1 − β)·√(1/(1 − 2β))",
      "m<super>H</super>: median of the honest neighbours alone. r: how far honest updates lie from it. f: bad neighbours out of K, with f &lt; K/2. β = f/K. It bounds the push per cycle; it is not immunity.")],
 7: [("Same-model consensus (CIoTA style)", "update = element-wise median of same-model devices' d; the rest is discarded", "If most of that model is infected, the median is the attacker's update."),
     ("Ours", "update = a + r,  with r budgeted", "a: backed by other vendors. r: the rest, limited and not discarded.")],
 8: [FPR, COMP, ("Victim rule", "M = median distance of target attack from benign centre / ρ ≥ 1.3", "M: attack distance in alarm radii. ρ: alarm radius. Closer attacks cannot be protected by a centroid detector."),
     ("Poisoner share", "p = poisoned samples / learning batch,  p = 0.1 to 0.4", "p: fraction of the victim's learning traffic controlled by the attacker.")],
 9: [COMP, ("Compromise percentage", "compromised % = compromised attacked runs / all attacked runs × 100", "Runs cover victims, attacker shares, poisoning styles and random seeds.")],
 10: [FPR, COMP, ("Alarm-rate switch-off", "skip learning if alarm rate &gt; 5 × clean rate", "clean rate: alarm rate on calibration traffic."),
     ("Outlier-ratio gate", "skip learning if alarm rate &gt; 3 × its own moving average", "The moving average rises with the alarms, so this gate can reopen.")],
 11: [("Freeze condition", "alarm rate &gt; limit  ⇒  learning stops", "Decoys raise the alarm rate. FOA has no such condition, and alarmed samples never enter its update."), FPR, COMP],
 13: [("Current through the shunt", "I = V<sub>shunt</sub> / R<sub>shunt</sub>", "V<sub>shunt</sub>: voltage across the shunt. R<sub>shunt</sub> = 0.1 ohm. I: board current."),
      ("Power and energy", "P = V × I<br/>E = ∫ P dt (summed by the trapezoid rule)", "V: supply voltage (5.04 V). P: power (365.4 mW). E: energy. Over one 7.77 s cycle E is about 2.84 J, almost all of it the board's normal draw.")],
 14: [FLOOR, ("Normal region left", "ratio = s(t) / s<super>0</super> × 100%", "Under 2% after 20 minutes on identical boards, before the floor; 1.0 with the floor."),
      ("Why shrinking raises alarms", "alarm if ||x − μ|| &gt; τ·s", "If s shrinks, the radius τ·s shrinks, so ordinary traffic falls outside it."),
      ("Floor in log form", "C<sub>s</sub> + R<sub>s</sub> ≥ 0", "The excess shrinking is removed from this cycle's residual first, then from the common part, so budgets still hold."),
      ("Calibration spacing", "old: keep every 10th sample (one per 500 ms)<br/>new: gaps of 9, 9, 9 and 13 samples",
       "Samples are 50 ms apart and the telemetry repeats every 200 ms, so a fixed 500 ms spacing sees only two of its four phases; the uneven gaps see all four.")],
 15: [("Combine cost", "geometric median of K updates: 10 Weiszfeld iterations", "K: neighbours heard. 1.2 to 1.9 ms on an ESP8266 with K = 2."), RES],
 21: [("Starvation", "accepted = samples with score ≤ τ<br/>if fewer than 5 core samples: d = 0",
       "After a sudden jump every sample scores above τ, so nothing is accepted and the detector cannot move.")],
 6: [COMP],
}

# new slide -> (old slide in the 20-slide deck, speaker). Old odd slides were Rishit's, even were Farhan's.
OWN = {1: (1, "Rishit"), 2: (2, "Farhan"), 3: (3, "Rishit"), 4: (4, "Farhan"), 5: (5, "Rishit"), 6: (None, "New"),
       7: (6, "Farhan"), 8: (7, "Rishit"), 9: (8, "Farhan"), 10: (9, "Rishit"), 11: (10, "Farhan"), 12: (11, "Rishit"),
       13: (12, "Farhan"), 14: ("13 to 16", "Mixed"), 15: (None, "New"), 16: (18, "Farhan"), 17: (None, "New"),
       18: (20, "Farhan"), 19: (19, "Rishit"), 20: (None, "New"), 21: (17, "Rishit")}
NOTE = {3: "same idea, new hospital example", 4: "same content, now a flowchart", 5: "rows reworded",
        10: "same numbers, now a chart", 14: "merges old 13 and 15 (Rishit) with 14 and 16 (Farhan)",
        16: "rewritten as positive use cases", 21: "trimmed"}


def owner_line(i):
    old, who = OWN[i]
    if who == "New":
        return "SPEAKER: NEW SLIDE, decide who presents it"
    if who == "Mixed":
        return f"SPEAKER: MIXED, was slides {old} ({NOTE[i]})"
    return f"SPEAKER: {who.upper()}, was slide {old}" + (f" ({NOTE[i]})" if i in NOTE else "")


prs = Presentation(os.path.join(ROOT, "G04_FOA_Final.pptx"))
slides = list(prs.slides)
assert len(slides) == len(Q), (len(slides), len(Q))
S = [P("Presentation and viva preparation", title), P("Fleet-Orthogonal Adaptation  ·  Group G-04  ·  Rishit Kamboj and Farhan Naik", small), Spacer(1, 8),
     P("How to use this", h1),
     P("Each slide has: a picture, formulas with labelled variables where they apply, what it means, what to say, and likely questions. Read it once fully, then practise aloud with only the slides. "
       "Aim for about 12 to 14 minutes. Each slide is labelled with who prepared it in the earlier 20-slide deck (odd slides Rishit, even slides Farhan). NEW slides still need a speaker.", p),
     P("Who presents which slide", h1),
     table([["Slide now", "Was slide", "Speaker"]] + [[str(k), str(v[0]) if v[0] else "none", v[1] if v[1] != "Mixed" else "Mixed: Rishit 13, 15 and Farhan 14, 16"] for k, v in OWN.items()], [3 * cm, 3 * cm, W - 6 * cm]),
     P("The 30-second answer", h1),
     P("IoT detectors must keep learning because normal traffic changes, but learning can be poisoned and pausing can be exploited. Our method lets a device "
       "learn more freely what neighbours from other vendors also see, and rations what only it sees. In simulation on real IoT traffic it resisted poisoning "
       "hidden in network change far better than a single device. On real boards we found the detectors shrinking until they alarmed on almost everything; "
       "a simple floor fixed this, and on the boards it held, with false alarms near 1.6% after a calibration fix. Our main advantage is security under change.", say),
     P("Five things never to say", h1),
     table([["Do not say", "Say instead"], ["We are the first", "We found no prior work combining these"],
            ["The hardware shows it is secure", "The floor held on the boards; every attack result is from simulation"],
            ["We have fewer false alarms than everyone", "With the floor a single device has fewer; ours is safer under change"],
            ["We tested attacks on the boards", "Attack results are from simulation on real traffic"],
            ["It never stops learning / it is revolutionary", "No gate stops it, but a sudden jump can starve it; it is a new combination for one narrow threat"]], [6.5 * cm, W - 6.5 * cm]), PageBreak()]
for i, (sl, (meaning, qa)) in enumerate(zip(slides, Q), 1):
    texts = [sh.text_frame.text for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    said = sl.notes_slide.notes_text_frame.text
    pic = [Image(os.path.join(PREV, f"s{i}.png"), 10.5 * cm, 10.5 * cm * 9 / 16, hAlign="LEFT")] if PREV else []
    if pic:
        pic = [Table([pic], style=[("BOX", (0, 0), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                   ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)], hAlign="LEFT")]
    S += ([PageBreak()] if i > 1 else []) + [P(f"Slide {i}.  {texts[0].replace(chr(10), ' ')}", h1), P(owner_line(i), spk)] + pic + [P("IN SIMPLE WORDS", lab), P(meaning, p),
          P("SAY THIS", lab), P(said, say)] + formulas(i) + [ P("QUESTIONS YOU MAY GET", lab),
          table([[q, a] for q, a in qa], [5.2 * cm, W - 5.2 * cm], head=False)]
S += [PageBreak(), P("The maths, if asked", h1),
      table([["Symbol or question", "Answer"],
             ["x, mu, s", "x: one traffic sample (16 numbers). mu: centre of normal. s: spread, the typical distance from the centre."],
             ["Score and alarm", "score = ||x - mu|| / s. Alarm if score > tau, the 99th percentile on clean data."],
             ["Alarm radius rho", "tau x starting spread. Budgets are measured in this unit."],
             ["d, m, a, r", "d: my proposed update. m: geometric median of neighbours' updates. a: the common part accepted. r = d - a: the residual, mine alone."],
             ["Smoothed consensus", "m_avg = 0.8 x old m_avg + 0.2 x m, so random jumps cancel and real change persists."],
             ["w: are neighbours' changes real?", "z = size of m_avg divided by (noise x sqrt(a / (2 - a))), a = 0.2; noise is the median disagreement over sqrt(number of peers), smoothed. w = (z - 2) / 2, clipped to 0..1."],
             ["Why 2 and 4?", "Below twice the noise it may be chance, above four it very likely is not. Design choices. Without w, false alarms rose from 7.0% to 10.1%; no victim fooled either way."],
             ["lambda: does my traffic agree?", "Median movement of my core points along the neighbours' direction, divided by the size of m_avg, clipped to 0..1. Median, so under half the batch cannot fake or cancel it."],
             ["Accepted change", "a = w x lambda x m_avg, then limited by the common budget."],
             ["Residual budget", "total residual movement <= (0.1 + 0.005 t) rho. At t = 0, 100, 200 this is 0.1, 0.6, 1.1 radii."],
             ["Common budget", "total common movement <= (0.75 + 0.06 t) rho."],
             ["Spread budgets", "Residual 0.1 + 0.001 t, common 0.7 + 0.02 t, in log units."],
             ["How were budgets chosen?", "Design choices: unverified change gets little, neighbour-backed change gets more. Only the residual spread budget was tightened on development seeds (0.2 to 0.1, 0.002 to 0.001)."],
             ["Was B tested?", "A sweep on held-out seeds, 4 victims: 0.005 is the largest tested slope with no victim compromised (31% false alarms under device-only drift). It shows the trade-off; B was not tuned with it. B0 was not swept."],
             ["Coverage floor", "s >= starting spread."]], [5.2 * cm, W - 5.2 * cm]),
      PageBreak(), P("Hard questions", h1),
      table([["Question", "Answer"],
             ["Your hardware result is a failure. Why should we accept the project?", "It is a measured limitation with a reproduced cause and a fix tested on held-out simulation runs and then on the boards, where the floor held. The hardware also gave valid timing, communication and power results, and found a calibration bug and the sudden-jump stall."],
             ["Your boards are identical. Doesn't that break your diversity assumption?", "Yes. Our design asks for different vendors; three identical boards do not satisfy it, and the collapse shows what happens then."],
             ["Your drift is made by you. Why believe it?", "It is a stress test applied to real traffic statistics with physical meaning, with strength set only by its effect on a static detector. CESNET adds real drift, where FOA was also never compromised; there, though, a never-learning detector had fewer false alarms."],
             ["Why did you need such large drift?", "These log-scaled features barely move under small changes; 8 times the packet rate only raised static false alarms to 22%."],
             ["What if the gateway is compromised?", "Out of scope: it can change everyone's traffic, so neighbours agree on the attack."],
             ["How are keys distributed?", "Provisioned per device; the testbed uses development keys. Today every board holds every node's key, so capturing one board gives all identities; per-pair keys are planned. Secure provisioning is not part of this work."],
             ["Does it scale?", "Each device sends one 92-byte broadcast per cycle and combines a small peer group, so cost grows with group size, not fleet size. We did not test large fleets."],
             ["What if messages are lost?", "In simulation up to 70% loss changed little; with almost no neighbours it falls back to the budgeted single-device behaviour."],
             ["Why not deep learning or an autoencoder?", "The centroid detector fits a microcontroller, adapts online, and allows a proof. Heavier models are future work."],
             ["Is this useful in practice?", "In a narrow setting: one detector per device on a gateway, many peers, shared change plus slow local tampering. For single-purpose devices an allow-list is better, and loud botnets are caught without learning."],
             ["Why not just use an allow-list (MUD)?", "Where a device's traffic can be listed, yes. Anomaly detection matters where normal behaviour is too varied or changes too often to list."],
             ["Did you use AI tools?", "Answer honestly and follow your course policy. Make sure you can explain every part you present."]], [5.2 * cm, W - 5.2 * cm]),
      PageBreak(), P("Glossary", h1),
      table([["Term", "Meaning"], ["IDS", "Intrusion detection system"], ["Anomaly detector", "Learns normal and flags what differs"], ["Centre, spread, threshold", "Middle of normal, its typical size, and how far is too far"],
             ["False alarm rate", "Share of normal traffic flagged"], ["Compromised", "The target attack mostly goes undetected"], ["Poisoning", "Feeding data that changes what the model learns"],
             ["Peer / neighbour", "Another device whose update is used as a witness"], ["Byzantine peer", "A neighbour that sends anything, with a valid key"], ["Budget", "Maximum allowed movement, growing slowly"],
             ["ESP-NOW", "Espressif's connectionless device-to-device radio protocol"], ["HMAC", "A keyed tag proving who sent a message and that it was not altered"],
             ["Seed", "One random repetition of an experiment"], ["Held-out", "Not used while designing"], ["INA226", "Current and voltage sensor on the I2C bus"],
             ["Calibration aliasing", "Calibration samples taken in step with a repeating traffic pattern, so some phases are never seen"],
             ["Starvation", "No accepted traffic left to learn from"]], [4.6 * cm, W - 4.6 * cm]),
      P("Numbers to remember", h1),
      table([["Number", "What it is"], ["9.0% vs 24.6%", "False alarms after strong change, FOA vs single device, without floor"], ["10.8% vs 39.2%", "Compromised under strong change, FOA vs single device"],
             ["2.5% vs 0.8%", "False alarms with floor, FOA vs single device"], ["9.4% vs 43.1%", "Compromised with floor, FOA vs single device"], ["0% vs 100%", "One-model botnet, ours vs same-model consensus"],
             ["100% vs 26%", "Switch-off defence with and without decoys"], ["0% vs 18%", "CESNET, FOA vs single device compromised"], ["11 to 24 ms, 1.2 to 1.9 ms", "Update and combine time on ESP8266, first and later runs"],
             ["365 to 391 mW", "Measured board power, mostly the radio"], ["1.5 to 1.7%", "Board false alarms with the floor and fixed calibration"],
             ["about 99%", "Board false alarms after a sudden doubling of the traffic rate"], ["5.9% vs 9.1%", "CESNET false alarms, never-learning detector vs FOA"],
             ["about 17 min", "Minimum time to compromise on the boards, attack 2 alarm radii away"], ["92 bytes", "Message per device per cycle"], ["under 2% vs 61%", "Normal region left: connected 20 min vs isolated 50 min"]], [4.6 * cm, W - 4.6 * cm])]


def foot(c, d):
    c.setFont("A", 8); c.setFillColor(GREY); c.drawString(2 * cm, 1.1 * cm, "G-04  ·  Viva preparation"); c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, str(d.page))


doc = BaseDocTemplate(os.path.join(ROOT, "G04_Viva_Prep.pdf"), pagesize=A4, title="G-04 viva preparation", author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 1.7 * cm, W, A4[1] - 3.3 * cm)], onPage=foot)])
doc.build(S); print("wrote G04_Viva_Prep.pdf")
