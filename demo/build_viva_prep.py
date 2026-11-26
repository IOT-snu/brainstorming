"""
Builds G04_Viva_Prep.pdf: for every slide of G04_FOA_Final.pptx, what to say, what it means, and the questions
to expect with answers; then a glossary, hard questions and a number sheet. Run: python3 demo/build_viva_prep.py
"""
import os
from pptx import Presentation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
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
say = S_("say", backColor=SOFT, borderPadding=7, leftIndent=7, rightIndent=7, spaceBefore=4, spaceAfter=10)
cell = S_("c", fontSize=8.8, leading=11.8, spaceAfter=0); cellb = S_("cb", fontName="AB", fontSize=8.8, leading=11.8, spaceAfter=0)
P = Paragraph
W = A4[0] - 4 * cm


def table(rows, widths, head=True):
    t = Table([[P(c, cellb if (head and i == 0) or j == 0 else cell) for j, c in enumerate(r)] for i, r in enumerate(rows)], colWidths=widths, repeatRows=int(head))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)] + ([("BACKGROUND", (0, 0), (-1, 0), SOFT)] if head else [])))
    return t


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
   ("Which neighbours are used?", "Devices from other vendors, so a single exploit is unlikely to control many of them.")]),
 ("The loop every device runs.",
  [("What is the detector?", "An online centroid detector: score = distance of a sample from the learned centre divided by the learned spread. Alarm if the score exceeds the 99th percentile of clean calibration data."),
   ("What are the 16 numbers?", "Traffic statistics (Kitsune style: packet sizes, rates, gaps over several time windows) log-scaled, standardised and projected onto 16 shared directions."),
   ("Is it supervised? Do you need attack labels?", "No labels and no attack signatures. It learns from traffic it judges normal."),
   ("Why HMAC?", "So a device without the key cannot forge a neighbour's message; old messages are rejected as stale. In our test, without authentication a keyless forger compromised the victim in every run."),
   ("What is the budget?", "A limit on total device-only movement that grows slowly with time: B0 + B t, in units of the alarm radius. B0 = 0.1, B = 0.005 per cycle.")]),
 ("Four theoretical statements.",
  [("State your main theorem simply.", "An attacker controlling only one device's traffic can move its centre at most (B0 + B t) alarm radii beyond what neighbours back, and the spread is bounded similarly. So there is a minimum time before an attack can hide."),
   ("How is it proved?", "By construction: the device-only part is projected onto a ball whose radius is the budget, after every cycle. The triangle inequality then gives the time to compromise."),
   ("How many bad neighbours can you tolerate?", "Fewer than half only bounds the push per cycle; it is not immunity. In tests, bad neighbours alone never won, but with a traffic poisoner 3 of 7 compromised 56% of victims."),
   ("What is the impossibility?", "If only one device changes, the same observations could come from honest drift or from poisoning, so no rule can separate them.")]),
 ("How we differ from the closest earlier work.",
  [("Isn't this just CIoTA?", "CIoTA uses peers of the same model and discards what they do not agree on. We use other vendors, admit the rest within a budget, and bound attacker movement. Under a one-model botnet, our version of same-model consensus failed and ours held."),
   ("Are you the first?", "We do not claim first. We found no prior work combining these, and several related 2026 works are preprints."),
   ("Did you run the real CIoTA?", "No. We re-implemented its consensus idea around our detector.")]),
 ("What data we used and what is simulated.",
  [("Is your data real?", "Traffic and attacks are real (N-BaIoT, CESNET). The fleet running together, the injected drift on N-BaIoT and the poisoner are simulated. N-BaIoT devices were recorded separately."),
   ("Which attacks?", "Real Mirai and BASHLITE traffic; the poisoner targets scan traffic, the closest to benign."),
   ("How did you avoid tuning on the test?", "Design choices used development seeds 0 and 1; reported results use seeds 2 to 11."),
   ("What does compromised mean?", "Fewer than half of the held-out attack packets raise an alarm, and the same run without the attacker still detects them."),
   ("Did you exclude any device as a victim?", "Yes. A victim's attack must be at least 1.3 alarm radii from benign traffic; Philips and SimpleHome 1002 fail this and stay as neighbours.")]),
 ("The headline: poisoning hidden inside drift.",
  [("Why hide it inside drift?", "During a real change the detector has to move, which gives the poisoner cover."),
   ("Why is single device + floor worse here?", "The floor keeps the normal region wider than a shrunken one, so a few more attacks fit inside it: 43.1% against 39.2%."),
   ("Why is FOA not 0%?", "Stealthy poisoners that hide in the core or imitate drift still win in some runs. The classic boundary poisoner never did.")]),
 ("All rules side by side (without the floor).",
  [("Learn-everything has only 2.6% false alarms. Why not use it?", "It accepts everything, including poison: 35% compromised, and 83% for the classic slow poisoner."),
   ("TOA is safer than FOA. Why drop it?", "It was given the true attack signature, which a real device does not have, and it has 38% false alarms."),
   ("Are those baselines the published systems?", "No, they are our re-implementations of each gating idea around the same detector, so differences come from the update rule.")]),
 ("Botnet, freeze and real drift.",
  [("Explain the botnet test.", "Three cameras of one model are infected and poisoned together. Same-model peers agree with the poison. Other-vendor peers do not."),
   ("Which defence did the freeze attack beat?", "An alarm-rate switch-off: 100% false alarms with decoys at 5% share, 26% without the attacker. The outlier-ratio gate we tested recovered, so not every gate freezes."),
   ("What is CESNET?", "40 weeks of traffic statistics from a national research network. Drift is real; the attack there is modelled.")]),
 ("A photo of the real setup.",
  [("Point to each part.", "The ESP8266 boards, the INA226 sensor and its wiring, the USB hub and cables, and the recording laptop. Practise pointing at them on the photo before the talk."),
   ("Which board is measured?", "Node 1: its 5 V line runs through the INA226. Node 0 reads the sensor over two I2C wires."),
   ("Is the sensor wired in series or parallel?", "In series: only the red 5 V wire of Node 1's cable goes through the 0.1 ohm shunt.")]),
 ("What we measured on hardware.",
  [("Which boards?", "Three ESP8266 NodeMCU boards (single core, about 80 KB RAM; our firmware uses about 51 KB). We also compiled for ESP32."),
   ("Why ESP-NOW?", "Direct short broadcasts between boards without a broker, up to 250 bytes; our message is 92 bytes."),
   ("How did you measure power?", "INA226 across a 0.1 ohm shunt in one board's 5 V line: about 72 mA, 365 mW."),
   ("How much energy does FOA cost?", "We could not detect extra energy at the sensor's 40 ms resolution. From compute time, about 7 mJ per cycle is an estimate, not a measurement."),
   ("What bugs did hardware reveal?", "Calibrating before statistics settled, rejecting frames because boards had different cycle numbers, an unexpected sensor address, and a logger crash on Windows."),
   ("Did you attack the boards?", "No valid attack test: the detectors collapsed first. Attack results are from simulation.")]),
 ("The failure: the normal region shrank until almost everything alarmed.",
  [("What exactly collapsed?", "The spread, so the acceptance region. Connected boards: under 2% in 20 minutes, about 90% false alarms."),
   ("Is the isolated run a fair comparison?", "Not controlled. Wi-Fi was off, which also changes traffic. It supports our explanation but does not prove it."),
   ("Does this break your theorem?", "No. The theorem limits how far an attacker can widen or move the detector. It said nothing about shrinking, which hurts false alarms, not security.")]),
 ("Why it happened.",
  [("Why would core-only learning shrink?", "It estimates spread from the central part of traffic. Repetitive traffic makes that part tight, points drop out, and it tightens again. Growth is gated; shrinking was not."),
   ("Why does agreement make it worse?", "Identical boards shrink in the same way, so the shared channel treats it as real common change."),
   ("What else might contribute?", "The board feature basis is a placeholder not fitted on their traffic, and the detector centre also drifted.")]),
 ("The fix, and the claim we had to correct.",
  [("What is the coverage floor?", "The spread may never go below its calibrated value."),
   ("Can an attacker exploit it?", "It only cancels shrinking, so the budget bounds still hold. It can keep the detector wider than a shrunken one, which cost a single device a few points."),
   ("Did it work on the boards?", "We have not completed a hardware run with it. It is validated in simulation on held-out seeds."),
   ("So is FOA still useful?", "Yes for security under drift: 9.4% compromised against 43.1%. Not for fewer false alarms: a floored single device has 0.8% against 2.5%."),
   ("Why admit this?", "Because the corrected claim is what the data supports.")]),
 ("Open limits and next steps.",
  [("Biggest weakness?", "A device with a large change of its own is learned very slowly, and nothing is verified under attack on hardware."),
   ("What would you do with more time?", "Run the floored firmware, fit the basis on testbed traffic, run flood, freeze and slow-poisoning tests, and use different device types as neighbours.")]),
 ("Close and sources.",
  [("Which paper influenced you most?", "Kloft and Laskov (2012): the same centroid detector, and the result that the attacker's share of traffic bounds poisoning."),
   ("Who did what?", "Answer truthfully for your own team. Agree on this before you walk in.")]),
]

prs = Presentation(os.path.join(ROOT, "G04_FOA_Final.pptx"))
slides = list(prs.slides)
assert len(slides) == len(Q), (len(slides), len(Q))
S = [P("Presentation and viva preparation", title), P("Fleet-Orthogonal Adaptation  ·  Group G-04  ·  Rishit Kamboj and Farhan Naik", small), Spacer(1, 8),
     P("How to use this", h1),
     P("Each slide has: what it means, what to say, and likely questions. Read it once fully, then practise aloud with only the slides. "
       "Aim for about 10 to 12 minutes. A natural split: one person takes slides 1 to 10, the other 11 to 17, and both answer questions.", p),
     P("The 30-second answer", h1),
     P("IoT detectors must keep learning because normal traffic changes, but learning can be poisoned and pausing can be exploited. Our method lets a device "
       "learn in full what neighbours from other vendors also see, and rations what only it sees. In simulation on real IoT traffic it resisted poisoning "
       "hidden in network change far better than a single device. On real boards we found the detectors shrinking until they alarmed on almost everything; "
       "a simple floor fixes this in simulation, and showed that our advantage is security, not fewer false alarms.", say),
     P("Four things never to say", h1),
     table([["Do not say", "Say instead"], ["We are the first", "We found no prior work combining these"],
            ["The fix works on our hardware", "The fix is validated in simulation; the hardware run is still to be done"],
            ["We have fewer false alarms than everyone", "With the floor a single device has fewer; ours is safer under change"],
            ["We tested attacks on the boards", "Attack results are from simulation on real traffic"]], [6.5 * cm, W - 6.5 * cm]), PageBreak()]
for i, (sl, (meaning, qa)) in enumerate(zip(slides, Q), 1):
    texts = [sh.text_frame.text for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    S += [CondPageBreak(7 * cm), P(f"Slide {i}.  {texts[0].replace(chr(10), ' ')}", h1), P("IN SIMPLE WORDS", lab), P(meaning, p),
          P("SAY THIS", lab), P(sl.notes_slide.notes_text_frame.text, say), P("QUESTIONS YOU MAY GET", lab),
          table([[q, a] for q, a in qa], [5.2 * cm, W - 5.2 * cm], head=False)]
S += [PageBreak(), P("Hard questions", h1),
      table([["Question", "Answer"],
             ["Your hardware result is a failure. Why should we accept the project?", "It is a measured limitation with a reproduced cause and a fix tested on held-out simulation runs. The hardware also gave valid timing, communication and power results."],
             ["Your boards are identical. Doesn't that break your diversity assumption?", "Yes. Our design asks for different vendors; three identical boards do not satisfy it, and the collapse shows what happens then."],
             ["Your drift is made by you. Why believe it?", "It is a stress test applied to real traffic statistics with physical meaning, with strength set only by its effect on a static detector. CESNET adds real drift, where FOA was also never compromised."],
             ["Why did you need such large drift?", "These log-scaled features barely move under small changes; 8 times the packet rate only raised static false alarms to 22%."],
             ["What if the gateway is compromised?", "Out of scope: it can change everyone's traffic, so neighbours agree on the attack."],
             ["How are keys distributed?", "Provisioned per device; the testbed uses development keys. Secure provisioning is not part of this work."],
             ["Does it scale?", "Each device sends one 92-byte broadcast per cycle and combines a small peer group, so cost grows with group size, not fleet size. We did not test large fleets."],
             ["What if messages are lost?", "In simulation up to 70% loss changed little; with almost no neighbours it falls back to the budgeted single-device behaviour."],
             ["Why not deep learning or an autoencoder?", "The centroid detector fits a microcontroller, adapts online, and allows a proof. Heavier models are future work."],
             ["Did you use AI tools?", "Answer honestly and follow your course policy. Make sure you can explain every part you present."]], [5.2 * cm, W - 5.2 * cm]),
      PageBreak(), P("Glossary", h1),
      table([["Term", "Meaning"], ["IDS", "Intrusion detection system"], ["Anomaly detector", "Learns normal and flags what differs"], ["Centre, spread, threshold", "Middle of normal, its typical size, and how far is too far"],
             ["False alarm rate", "Share of normal traffic flagged"], ["Compromised", "The target attack mostly goes undetected"], ["Poisoning", "Feeding data that changes what the model learns"],
             ["Peer / neighbour", "Another device whose update is used as a witness"], ["Byzantine peer", "A neighbour that sends anything, with a valid key"], ["Budget", "Maximum allowed movement, growing slowly"],
             ["ESP-NOW", "Espressif's connectionless device-to-device radio protocol"], ["HMAC", "A keyed tag proving who sent a message and that it was not altered"],
             ["Seed", "One random repetition of an experiment"], ["Held-out", "Not used while designing"], ["INA226", "Current and voltage sensor on the I2C bus"]], [4.6 * cm, W - 4.6 * cm]),
      P("Numbers to remember", h1),
      table([["Number", "What it is"], ["9.0% vs 24.6%", "False alarms after strong change, FOA vs single device, without floor"], ["10.8% vs 39.2%", "Compromised under strong change, FOA vs single device"],
             ["2.5% vs 0.8%", "False alarms with floor, FOA vs single device"], ["9.4% vs 43.1%", "Compromised with floor, FOA vs single device"], ["0% vs 100%", "One-model botnet, ours vs same-model consensus"],
             ["100% vs 26%", "Switch-off defence with and without decoys"], ["0% vs 18%", "CESNET, FOA vs single device compromised"], ["11.2 ms, 1.6 ms", "Update and combine time on ESP8266"],
             ["365 mW", "Measured board power"], ["92 bytes", "Message per device per cycle"], ["under 2% vs 61%", "Normal region left: connected 20 min vs isolated 50 min"]], [4.6 * cm, W - 4.6 * cm])]


def foot(c, d):
    c.setFont("A", 8); c.setFillColor(GREY); c.drawString(2 * cm, 1.1 * cm, "G-04  ·  Viva preparation"); c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, str(d.page))


doc = BaseDocTemplate(os.path.join(ROOT, "G04_Viva_Prep.pdf"), pagesize=A4, title="G-04 viva preparation", author="Rishit Kamboj, Farhan Naik")
doc.addPageTemplates([PageTemplate("p", [Frame(2 * cm, 1.7 * cm, W, A4[1] - 3.3 * cm)], onPage=foot)])
doc.build(S); print("wrote G04_Viva_Prep.pdf")
