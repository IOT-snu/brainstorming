# FOA reality check: how useful is it, really? (27 Nov 2026)

A blunt follow-up to `00_RESEARCH_LOG.md`. It uses our own run files
(`experiments/foa/results/E3.csv`, `E12.txt`, the paper's CESNET numbers, and the 27 Nov board runs
on branch `origin/hardware-results-20261127`) plus a targeted search for practical alternatives that
the academic sweeps did not cover.

## 1. Verdict in five lines

1. **Not revolutionary.** FOA is a sensible, new combination of known pieces (robust consensus,
   bounded updates, a shared versus device-only split) aimed at one narrow threat: slow poisoning
   hidden inside honest drift. Each piece has prior art, and so does the core intuition (see section 4).
2. **Real, but narrow, win in simulation.** Under strong injected shared drift it is compromised far
   less often than a device learning alone (9.4% vs 43.1% with the floor), mostly because the classic
   boundary poisoner never beats it (0% vs 75.4%).
3. **It loses or ties on most other axes.** With the floor a lone device has fewer false alarms
   (0.8% vs 2.5%), handles its own drift far better (0.9% vs 24.6% false alarms), and mimicry attacks
   hurt both the same (17.1% vs 16.4%).
4. **On the only real drift we have (CESNET), not adapting at all was best**: the static detector had
   5.9% false alarms against FOA's 9.1%, and it cannot be poisoned.
5. **Hardware shows feasibility, not security.** The boards run it (about 25 ms of computing per
   cycle, 26% of flash, 93% of instruction RAM), the floor holds, but no attack has been run on them, and
   an abrupt traffic change stalled every adaptive rule at about 99% false alarms.

Technology readiness: about TRL 3 to 4 (proof of concept, components checked in the lab). As a course
project it is strong. As a product it is not deployable as it stands.

## 2. Our runs, read without spin

### Simulation (N-BaIoT traffic, injected drift and poisoner, held-out seeds 2 to 11)

With the coverage floor (E12, 7,310 runs):

| | Single device + floor | FOA + floor | Who wins |
|---|---|---|---|
| False alarms, moderate drift | 0.9% | 1.4% | single device |
| False alarms, strong drift | 0.8% | 2.5% | single device |
| False alarms, device-only drift | 0.9% | 24.6% | single device, by a lot |
| Compromised, no drift | 7.6% | 4.3% | FOA, slightly |
| Compromised, strong drift, all attackers | 43.1% | 9.4% | **FOA, clearly** |
| ... boundary attacker | 75.4% | 0.0% | **FOA** |
| ... core-hiding attacker | 36.8% | 11.8% | FOA |
| ... mimicry attacker | 17.1% | 16.4% | tie |
| Monoculture botnet, 1 to 3 cameras infected | 100% | 0% | FOA (by construction: diverse peers) |

Without the floor (E3, 6,720 runs), when FOA was compromised it happened at a median of cycle 104
(the attack starts at cycle 40), the fastest at cycle 49. Its final detection of the attack was 0.89
against 0.67 for a lone device; TOA with an oracle attack signature did better than FOA (5.5%
compromised, 0.96 detection), which shows what knowing the attack is worth.

Caveats that matter:
- The drift, the poisoner and the fleet's concurrency are synthetic. "Strong drift" was set so that a
  static detector reaches about 78% false alarms; that is a stress test we chose, not an observed
  network.
- False alarms are per sample. On the boards a sample is taken every 50 ms, so even 1.5% means roughly
  26,000 flagged samples per device per day. Nobody would run that as an alerting system without
  aggregating to per-device alerts, which we have not evaluated.
- The time-to-compromise bound is a delay, not a wall. With our defaults a target 2 alarm radii away
  needs at least about 130 cycles: about 17 minutes at the boards' 7.8 s cycle, or about five and a
  half days at one cycle per hour. A patient attacker on one device always wins eventually, and the same
  budget makes FOA equally slow to accept a device's own honest change.

### Real drift (CESNET-TimeSeries24, 12 addresses, 40 weeks, modelled attack)

| | Static | Naive | Single device | FOA | Frozen reserve |
|---|---|---|---|---|---|
| False alarms | 5.9% | 5.2% | 11.6% | 9.1% | 11.6% |
| Compromised | 0% (cannot learn) | 91% | 18% | 0% | 0% |

Plainly: on this real drift, adaptation was not needed. FOA is safe here, but a detector that never
learns is at least as good. The case for FOA rests on drift large enough to break a static detector,
which we have only injected.

### Boards (3 ESP8266, single runs, 27 Nov)

- Works: Wi-Fi and gossip (both peers heard in 88 to 97% of cycles), floor held (spread ratio never
  below 1.0000), HMAC frames, power 382 to 391 mW (radio dominated), about 25 ms of computing per cycle.
- Found: calibration aliasing (fixed-stride calibration matched the 200 ms telemetry period; rotating
  the stride took false alarms from 25% to 1.5 to 1.7%).
- Failed: an abrupt halving of the telemetry periods left no accepted traffic (zero core samples in
  78 of 79 cycles) and false alarms stayed near 99% with or without peers.
- Not done: any attack, a static control with the rotated calibration, repeats, committed raw logs.
- Threat-model gap we noticed while reading the firmware: the board features summarise *all*
  incoming packets together, so an attacker's traffic shifts every sample instead of adding separate
  samples. That breaks the simulation's assumption behind the freeze result (decoys as separate
  samples) and the "attacker holds under half the batch" argument for the agreement median. On the
  boards only the budget argument survives unchanged. Keying statistics per source would fix this.

## 3. The real use case, and where it does not apply

**Where it does not help (be honest about these in the viva):**
- **Single-purpose IoT devices.** An allow-list of the endpoints a maker intends, the IETF
  Manufacturer Usage Description standard (RFC 8520, 2019), cannot be poisoned and stops the scanning
  and flooding in N-BaIoT without any learning. Even a static detector catches most of that traffic.
- **Mirai-style attackers.** They are loud, not slow, and once inside a device Mirai kills processes
  holding the remote-access ports and competing malware (Antonakakis et al., USENIX Security 2017). A
  detector on the infected device dies with it.
- **The ESP8266 as both protected device and detector.** If its firmware is replaced, the detector
  is gone; if it is not, an outside attacker can only shape the traffic it receives. Either way, no
  one receives its alarms today.
- **Tiny fleets.** Our 3-board testbed gives each device 2 peers, where the Byzantine theorem says
  nothing (one key-holding peer moves a two-point median without bound).
- **Frequent device-only changes** (firmware updates, new usage): FOA rations them, so false alarms
  stay high until the budget catches up (24.6% in simulation).

**Where the idea fits (plausible, none of it tested by us):**
1. **Per-device baselines on a gateway, edge box or ISP**: one FOA detector per device on a router or
   Raspberry Pi with per-source features, peers drawn from other devices and sites, alarms feeding a
   quarantine rule. This avoids "the infected device kills its detector" and gives more peers.
2. **Industrial (OT) monitoring.** Commercial OT sensors learn a baseline and then stop: Microsoft
   Defender for IoT runs a learning mode of days to weeks, after which deviations alert and humans
   triage what to add to the baseline. That is the static or learn-then-freeze approach FOA argues
   against; an FOA-like rule could absorb fleet-wide changes automatically and leave only
   device-specific changes for human triage.
3. **Per-entity analytics beyond IoT** (UEBA, NDR): Microsoft Sentinel's UEBA already scores each
   entity against its own history, its peers and the organisation. FOA's contribution there would be
   a principled rule for when a baseline may *move*, not just how to score.
4. **Sensor fleets with shared environmental drift** (for example smart meters, where weather and
   season move every meter together, and tampering is local). Our search found no work on slow
   tampering specifically, so this is a hypothesis.

## 4. Better or already-existing things we found

| Thing | What it does | Better than FOA at | Worse than FOA at |
|---|---|---|---|
| MUD allow-lists (RFC 8520) | Network enforces maker-declared endpoints | Cannot be poisoned; no learning; catches scans and floods | Only fits single-purpose devices; needs maker files; adoption data is thin |
| Learn-then-freeze plus human triage (Defender for IoT learning mode) | Baseline for days to weeks, then alert on deviations | No automatic poisoning path | Drift becomes alerts; needs people |
| Darktrace patent US 10,986,121 B2 (2021) | Continually updated per-entity models compared with own history and with peers, so compromised entities are not learned as normal | Same core intuition, from a commercial vendor; built for enterprise scale | No public bound on poisoning speed, no freeze analysis (as far as the text we read goes) |
| Sentinel UEBA peer analytics | Each entity scored against history, peers, organisation | Production scale, peers chosen from group membership | Scoring only; no stated rule for safe baseline movement |
| Chen, Kar, Moura SIU (arXiv 1709.06156, preprint) | Consensus plus norm-limited local innovation, robust below one half | Convergence guarantee | Fixed target, tolerance shrinks, no drift |
| BALANCE (ACM CCS 2024) | Accept neighbour models within a shrinking distance | Convergence proofs, decentralised FL | Shrinking radius rejects late honest drift (our untested claim) |
| ClippedGossip (arXiv 2202.01545, preprint) | Clip neighbours' updates in gossip | Arbitrary graphs, proofs | Same: static optimum |
| Kloft and Laskov (JMLR 2012) | Poisoning bounds for exactly our centroid detector | Tight single-learner analysis | No drift, no peers |
| Our own TOA (oracle signature) | Rations movement toward a known attack | Fewer compromises (5.5% vs 10.8%) | Needs the attack signature |
| Static detector | Never learns | Best false alarms on real CESNET drift; unpoisonable | Breaks under large drift (78% in our stress test) |

What remains ours, stated safely: we found no prior work that splits each device's update into a
peer-backed part and a device-only part with a growing budget and a stated minimum time to compromise,
together with an analysis of freeze attacks on stop-learning gates, implemented on microcontrollers.

## 5. What would make it genuinely useful (ranked)

1. **Run attacks on the boards** (slow ramp vs a lone device, loud decoys, forged and replayed frames),
   with attacker-free twins and repeats. Without this the hardware says nothing about security.
2. **Move the detector to a gateway** (router or Raspberry Pi), one detector per device, statistics
   keyed per source. This matches the simulation's threat model and the realistic deployment.
3. **Evaluate alerts, not samples**: alerts per device per day at a fixed detection rate, and attach
   an action (quarantine through a firewall or MUD rule).
4. **Recover from abrupt change safely** (re-anchor only when a quorum of peers stalls at the same
   time, with its own budget), and test steps of 1, 2 and 4 alarm radii.
5. **Fair baselines**: static and lone device with the rotated calibration on the boards; BALANCE and
   ClippedGossip in simulation.
6. **Find one domain where slow manipulation is real** (OT sensors, meters) and test there; injected
   drift on N-BaIoT cannot carry the argument alone.
7. **Fix the firmware threat model**: per-pair keys (today every board holds every key) and close the
   60 s replay window after a peer goes quiet.

## 6. Sources checked for this note (27 Nov 2026)

- RFC 8520, Manufacturer Usage Description Specification: https://www.rfc-editor.org/rfc/rfc8520.html
- Microsoft Defender for IoT, learned baseline of OT alerts: https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/create-learned-baseline
- Microsoft Sentinel UEBA: https://learn.microsoft.com/azure/sentinel/identify-threats-with-entity-behavior-analytics
- Darktrace patent US 10,986,121 B2 (read in part): https://patents.google.com/patent/US10986121
- Antonakakis et al., Understanding the Mirai Botnet, USENIX Security 2017: https://faculty.cc.gatech.edu/~mbailey/publications/usesec17_mirai.pdf
- Chen, Kar, Moura, Resilient Distributed Estimation: Sensor Attacks (preprint): https://arxiv.org/abs/1709.06156
- Fang et al., Byzantine-Robust Decentralized Federated Learning (BALANCE), CCS 2024: https://arxiv.org/abs/2406.10416
- He, Karimireddy, Jaggi, ClippedGossip (preprint): https://arxiv.org/abs/2202.01545
- Korycki and Krawczyk, Machine Learning 112 (2023): https://link.springer.com/article/10.1007/s10994-022-06177-w
- Pavan et al., TinyML on-device learning survey (preprint): https://arxiv.org/abs/2605.31226
- Poisoning surveys (no documented in-the-wild case against a deployed anomaly detector found): https://arxiv.org/abs/2205.01992

Search for in-the-wild poisoning of deployed anomaly detectors found surveys and lab attacks
(for example SpamBayes, Nelson et al. 2008), not a documented field incident. Slow poisoning of IoT
detectors remains a research threat model.
