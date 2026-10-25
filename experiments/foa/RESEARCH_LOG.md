# Research log: Fleet-Orthogonal Adaptation

What we did, in order, including what did not work. Dates are 2026.

## 24 Oct: build

- Downloaded all nine N-BaIoT devices (UCI, streamed; the server dropped the connection once, so the
  downloader now resumes by skipping finished devices) and a 1,000-IP sample of CESNET-TimeSeries24.
- Wrote the fleet simulator, the FOA rule, eight baselines and the attackers; unit tests on a synthetic
  fleet with known geometry.
- Wrote the ESP32 C core and checked it against Python on recorded cycles (equivalence, frames,
  tamper rejection, RFC 4231). Compiled the node sketch, the INA219 monitor and a no-FOA baseline for
  the ESP32 to measure FOA's own flash and RAM.

## Design changes forced by the data (development seeds 0 and 1 only)

1. **Budget units.** Budgets were first in calibration spreads. Real devices are heavy-tailed (alarm
   radius 7 to 15 spreads against about 4 for Gaussian data), so budgets are now in alarm radii
   (tau * s0), which makes the time-to-compromise bound scale-free.
2. **Shared space.** A 10-D unwhitened PCA basis lost low-variance attack directions: the static
   detector caught 0% of scans on four devices. A 16-D whitened basis catches at least 80% on every
   device. Frames grew from 68 to 92 bytes.
3. **Agreement.** The first agreement lambda used the mean of the device's own proposals. An attacker
   pushing against the drift cancelled it (lambda went to 0), the victim stopped following the fleet,
   and its spread inflated. Lambda now uses the median projection of the device's core points on the
   consensus direction: an attacker holding under half the batch can neither cancel nor fake it.
   Fleet false alarms after drift fell from about 12% to 10%.
4. **Spread budget.** In every traced compromise the attacker inflated the spread, not the centre.
   Tightening the residual spread budget (B0s 0.2 to 0.1, Bs 0.002 to 0.001) removed all compromises in
   the pilot and lowered false alarms. A joint centre-and-spread budget was tried and rejected: it hurt
   liveness (it is kept as an ablation).
5. **Drift strength.** Small physical changes barely move Kitsune's log statistics (rate x8 gives a
   static detector 22% false alarms). Strength was set only by the static detector's false-alarm rate:
   moderate about 34%, strong about 78%. These are stress tests; CESNET supplies real drift.
6. **Victims.** Philips and SimpleHome 1002 have their scan traffic at 1.04 and 1.16 alarm radii from
   benign: no centroid detector protects that. Rule fixed before the main run: victims need 1.3 radii.
7. **Paired controls.** Honest drift alone made one camera's scan traffic undetectable for every
   core-learning rule. Every attacked run is now paired with its attacker-free twin, and only loss of
   detection that the twin keeps counts.
8. **Decoys.** Real flood packets sometimes fell inside the alarm radius on some devices, so "decoys"
   could poison. Decoys are now pushed to at least twice the alarm radius; E5 was rerun.

## 25 Oct: results (held-out seeds 2 to 11)

- E1 liveness, strong shared drift, fleet false alarms after drift: FOA 9.0%, single device 24.6%,
  alarm switch-off 45%, frozen reserve 59%, static 78%. Device-only drift: FOA 36%, single device 26%
  (the cost the frontier proposition predicts).
- E3 poisoning hidden in strong drift: compromised overall FOA 10.8%, single device 39.2%, switch-off
  29.9%, frozen reserve 27.4%, TOA with an oracle signature 5.5%. Boundary attacker: FOA 0% at every
  share. Core-hiding and mimicry at share 0.4: FOA 34% and 29%, mostly the Provision cameras.
- E4 monoculture: same-model consensus 0% with one of three cameras infected, 100% with two or three;
  FOA with diverse peers 0% throughout.
- E5 freeze: decoys at 5% lock the alarm-rate switch-off at 100% false alarms (26% without attacker);
  FOA identical with and without decoys (unit test: bit-for-bit). The outlier-ratio gate is not frozen.
- E6: HMAC rejects all forged and replayed frames (without it, 100% compromised). Frame loss up to 70%
  is harmless. **Three of seven Byzantine peers compromise the victim during drift**, below the
  breakdown point: the common budget is too generous. Open problem.
- E7: B up to 0.005 alarm radii per cycle: no compromise; larger B tracks device-only drift faster and
  is compromised more often.
- E8: discarding the residual (CIoTA-like) or removing peers wrecks liveness (54%, 43% fleet false
  alarms); removing the residual budget gives the attack back (67%) and is the only variant that ever
  violated the bound.
- E10 four nodes: FOA 0% compromised, 11% false alarms.
- E11 CESNET real drift: FOA 0% compromised (single device 18%, naive 91%); false alarms FOA 9.1%,
  single device 11.6%, static 5.9% (real drift here is mild).
- Bound of Corollary 1: 0 violations in 3,630 attacked runs of FOA and its budgeted variants and in the
  synthetic runs.

## Known gaps

- Fleet concurrency, drift (on N-BaIoT) and the poisoner are synthetic; hardware numbers are estimates.
- A device with large own drift on top of shared drift is lost by FOA.
- Byzantine minorities can win during drift; a tighter or drift-aware common budget is future work.
- The independent multi-agent code review planned for 24 Oct did not run (usage limit); the C core is
  verified against Python, and the Python is covered by unit tests, but a second reviewer is still owed.
