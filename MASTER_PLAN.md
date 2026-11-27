# FOA master plan (28 Nov 2026)

## 1. The target, and why it decides everything

The course plan says a project taken to the level of a paper suitable for an A/A* conference or a
Q1 journal earns an A grade regardless of exams, provided it has a clear problem, novelty, proper
evaluation and a significant contribution. That is the prize. The 30 project marks (survey,
presentations and report 10; implementation and results 5; novelty 5; faculty assessment 10) follow
from the same work. So every item below is ranked by one question: how much does it move a careful
reviewer from "interesting student project" to "credible submission to a top security or IoT venue",
per hour of work?

## 2. Where we honestly stand

- **Strong:** a clear dilemma (poisoning vs freezing vs false alarms), a clean mechanism, a
  by-construction speed limit on poisoning, 26k+ simulated runs on held-out seeds with attacker-free
  twins, honest negative results, a C implementation running on three ESP8266 boards.
- **Weak (what a top-venue reviewer would reject us for today):**

| # | Weakness | Fix in this plan | Effort |
|---|---|---|---|
| W1 | Drift and poisoner are injected; on real CESNET drift a never-learning detector wins | Calibrate the speed limit on real drift (D3); hardware with real induced drift and real attack traffic (D2) | 1 to 3 days |
| W2 | Closest decentralised robust methods (BALANCE, ClippedGossip, SIU-style) not compared | Add them as baselines on E1, E3, E12, E11 | 1 day |
| W3 | Theory is one-sided (safety only) and "by construction" | Add a tracking (liveness) proposition and a tightness experiment (D4) | 1 to 1.5 days |
| W4 | Per-sample false alarms; no alert-level number; unclear where it runs | Alert-level metric; gateway framing; deployment guidance section | 1 day |
| W5 | Hardware: no attacks, single runs, identical boards, K = 2 | 2x3 hardware trial with repeats (D2); optional 2 more boards | 2 to 3 days |
| W6 | Abrupt change stalls learning | Quorum re-anchoring with its own budget, if time (D6) | 2 days |
| W7 | Significance: a narrow threat on toy devices | Reframe around fleets of self-learning detectors, which ship commercially (D1) | half a day |

## 3. Six strategic decisions (the thinking behind the plan)

**D1. Reframe the contribution.** Not "a detector on an ESP8266" but "a gate-free, poison-bounded
update rule for fleets of self-learning detectors, instantiated for IoT, cheap enough to run on a
microcontroller". Why: commercial detectors already keep per-entity baselines that update
continuously and compare entities with peers (Darktrace patent US 10,986,121; Microsoft Sentinel
UEBA), and OT tools learn a baseline once and then stop (Defender for IoT learning mode). That makes
slow poisoning and freezing real concerns, and gives FOA a home: one detector per device on a gateway
or edge box. The ESP8266 result becomes evidence of cost, not the deployment claim. This answers
"why does it matter" and "where does it run" in one move.

**D2. Redesign the hardware trial as a 2x3 experiment.** We found that the firmware has no
single-device baseline: with fewer than 2 peers FOA sets the common part to zero and still budgets
the rest, so "ignore peers" is the budget-only ablation, not a lone device. The trial needs three
builds: lone device (apply the proposal in full, new flag `RULE_SINGLE`), budget only (`NO_PEERS`),
and FOA. Run each under two conditions:
- *Device-only slow poisoning on node 0*: expect lone device pulled along, budget-only and FOA held
  to the budget line (B0 + Bt) rho. This is Theorem 1 on real hardware.
- *Gradual shared drift on all boards* (telemetry period ramped over 30 to 60 minutes, not halved at
  once): expect lone device and FOA to follow, budget-only to fall behind and raise false alarms.
Together the two rows show the paper's core claim on boards: only FOA gets both safety and tracking.
Three repeats per cell, in a balanced order, each paired with an attacker-free twin. Measure the
attack profile's distance M first and predict FOA's earliest compromise t* = (M - 1.2) / 0.006
cycles before running, so the result can confirm or refute a stated prediction.
Also note: the board features summarise all incoming packets together, so an attacker shifts every
sample. That makes the poisoning trial a clean test of the budget, but the decoy (freeze) trial will
likely show starvation during the flood. Run it anyway and report it; a per-source statistics build
(`PER_SOURCE`) is the follow-up that matches the simulation's threat model.

**D3. Put a real-world number on the speed limit.** Use CESNET's real 40 weeks to measure how fast
honest traffic drifts per day, split into the fleet-shared part and the device-only part. Choose B so
that, say, 95% of real device-only change is still followed, then state the resulting minimum time
for one host to be moved 2 alarm radii. That turns Proposition 3 (the unavoidable trade-off) and
Corollary 1 into a deployment sentence: "on real network traffic, following 95% of honest host-only
change still forces an attacker to spend at least N days". Cheap, uses existing code and data, and it
answers "is the bound useful?" with data instead of argument.

**D4. Make the theory two-sided.** Add a tracking proposition: with honest peers, shared drift of
speed v per cycle is followed with a bounded lag (the EMA lag is absorbed by the residual), as long as
v stays below what the core can see each cycle and below the common budget slope (0.06 + 0.005 alarm
radii per cycle). Above that speed every rule that learns only from accepted traffic starves, which
is exactly what the boards showed. One proposition then explains both the liveness result and the
hardware stall. Add a greedy budget-saturating attacker to show the time-to-compromise bound is
nearly tight (not just never violated).

**D5. Pre-register before running anything new.** Commit a short file with hypotheses, metrics,
success criteria and the compromise definition before the new runs, so the git timestamp proves we
did not move the goalposts. One hour, large credibility gain with faculty and reviewers.

**D6. One method addition at most, with a kill switch.** The only new mechanism worth adding is
recovery from a step larger than the alarm radius: re-anchor only when the device and a majority of
its peers are starved in the same cycles, with its own budget. Security cost: an attacker must starve
a majority of a peer group at once, which is the fleet-level case Proposition 3 already concedes.
Build it only if Phase 1 finishes by day 3, and drop it if its own attack test (flooding m of N
devices) beats the baseline.

## 4. The plan, in order

### Phase 0: today (2 to 3 hours)
1. Commit the corrected paper, slides, guides and research logs (done with this plan).
2. Preregister (D5): Codex writes and commits the hardware part (see the trial brief); Rishit adds the
   simulation part (baselines, alert metric, CESNET calibration, greedy attacker) before running them.
3. Hand `CODEX_ROBUSTNESS_TRIALS.md` to Codex on the Windows laptop (Farhan supervises).
4. Ask Farhan to turn branch `hardware-results-20261127` into a pull request with the raw logs and
   the rotated-calibration firmware flag, files in `experiments/hardware/` and `firmware/`, and
   without the chatgpt.com link.

### Phase 1: evidence (days 1 to 3), two streams in parallel
**Hardware stream (Farhan + Codex):**
1. Builds: `CAL_ROTATE`, `RULE_SINGLE`, `NO_PEERS`, replay-window fix; host tests still pass.
2. Static control with rotated calibration (closes the unfair 46% comparison).
3. The 2x3 trial of D2, 3 repeats per cell, twins, predictions written down first.
4. Forged and replayed frames (expect 0 accepted; also test a replay after 61 s of silence before and
   after the fix).
5. Decoy trial on the aggregate build (expect starvation; report it).

**Simulation and theory stream (Rishit + Claude):**
1. BALANCE and ClippedGossip baselines (re-implemented on updates, like our other baselines) on E1,
   E3, E12 and CESNET, with twins and held-out seeds.
2. Alert-level metric: alerts per device per day at a fixed detection rate, from per-cycle alarm shares.
3. D3 calibration on CESNET.
4. Greedy budget-saturating attacker; time to compromise against t*.
5. Tracking proposition (D4) with a simulated speed sweep that checks it.
6. Seeds 2 to 31 for the headline experiments, with bootstrap confidence intervals.

### Phase 2: the method gap (days 3 to 5, only if Phase 1 is on time)
1. Quorum re-anchoring (D6) in Python, with experiment E13 (steps of 1, 2 and 4 radii) and E13b
   (flooding m of N devices to trigger it).
2. Same rule in C behind a flag; rerun the abrupt-step test on the boards.
3. Optional: `PER_SOURCE` build and a second decoy trial.

### Phase 3: write (days 5 to 7)
1. Paper: reframe (D1), research question and hypotheses in the introduction, a related-work
   comparison table, new results, the tracking proposition, a deployment-guidance section (gateway
   placement, cycles clocked by time not by packet count so an attacker cannot speed up the budget,
   per-source statistics, per-pair keys), honest limits.
2. Top-level `README.md` and the code `.zip` the course requires (no data, pickles, photos or keys).
3. Slides: 13 or 14 core slides plus backup slides; the new hardware 2x3 figure becomes the climax.
   Rebuild the viva guide and explainer.
4. A 60 to 90 second video of the hardware trial (live plot of node 0's centre against its budget
   line, lone device beside it) as a demo fallback.

### Phase 4: rehearse (days 7 to 9)
1. Two timed run-throughs (10 to 12 minutes), each speaker on their half.
2. Mock viva: the other person asks the 20 hardest questions from `G04_Viva_Prep.pdf` and the
   objections in `research/multi_agent_review_2026-11-27/03_adversarial_judge.md`.
3. Day 9 is buffer.

### If the presentation is in 3 days
Day 1: prereg, `RULE_SINGLE`, device-only poisoning trial (lone device vs FOA, 2 repeats),
BALANCE baseline on E3. Day 2: forgery trial, alert-level metric, CESNET calibration, update paper and
slides. Day 3: README and zip, two rehearsals. Skip D4 proof, D6, per-source, extra boards.

### Stretch (two weeks or more)
- Two more boards (K = 4 tolerates one bad peer) with different traffic profiles, and a Byzantine
  test on hardware.
- A real multi-device dataset with concurrency and attacks, for example UNSW's IoT traces
  (Sivanathan et al., TMC 2019) and the labelled benign and attack traces of Hamza et al. (SOSR 2019);
  check availability first.
- Byzantine spread-channel fix; per-pair keys.
- After faculty feedback, and only if you both agree: arXiv, then IEEE Internet of Things Journal or
  Computers & Security (both IEEE-format friendly).

## 5. Who does what

| Person | Owns |
|---|---|
| Rishit (+ Claude) | Simulation baselines, metrics, theory, paper, slides, README and zip |
| Farhan (+ Codex) | Firmware flags, all board trials, raw logs, the demo video |
| Both | Prereg, results review at each gate, rehearsals, the "who did what" answer |

## 6. Decision gates (what we do when results go against us)

| Gate | If good | If bad |
|---|---|---|
| G1 BALANCE/ClippedGossip (day 2) | Positioning figure: they reject late honest drift | Novelty narrows to the growing budget, the bound and the freeze analysis; say so |
| G2 hardware poisoning (day 3) | Headline hardware figure | Check the budget code path on the board, then report as found |
| G3 shared-drift trial (day 3) | Hardware shows safety and tracking together | Report the tracking limit; it supports D4 |
| G4 re-anchoring (day 5) | New contribution | Drop it; keep as future work |

## 7. What not to do
- No new mechanisms beyond D6. No tuning on held-out seeds or on attacked runs.
- No new datasets before Phase 1 is done.
- No hardware security claims until the 2x3 trial is repeated.
- Never commit the unblurred photo, the unblurred deck, zips of course material, data, pickles or keys.
- No "first", no "revolutionary"; mark preprints.

## 8. Ready-to-use text

**Research question.** Can a fleet of self-learning detectors keep following honest drift while
bounding how fast an attacker on one device can poison its detector, without a stop-learning gate an
attacker could trip?

**Hypotheses.**
H1 (safety): under shared drift, FOA is compromised less often than single-device adaptation and
gated defences.
H2 (tracking): FOA follows gradual shared drift with false alarms within a few points of
single-device adaptation.
H3 (cost): FOA fits the memory, time and energy budget of a few-dollar microcontroller.

**Pitch.** Self-learning detectors can be slowly poisoned or frozen. FOA lets each device learn what
diverse peers confirm and rations the rest, giving a gate-free rule with a provable speed limit on
poisoning, measured on real traffic and running on ESP8266 boards.
