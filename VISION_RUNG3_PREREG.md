# RUNG 3 — the dorsal/motion stream: DIRECTION SELECTIVITY

*Everything above the OUTCOME section was written and committed BEFORE the
confirmatory run. Binding: `VISION_PROTOCOL.md`.*

## Why this rung is a DIFFERENTIAL prediction, not a repeat of rung 1

The verified research (105-agent adversarial pass) established 3-0 that the
**dorsal stream is EARLY and PARALLEL**, not a rung stacked above V1: V1 and MT
are co-earliest; marmoset layer-4 CB+ is dense in V1 AND MT/MST/FST at E130
(prenatal); PV peaks PD14 dorsal vs PD28 ventral; a retina→inferior-pulvinar→MT
route **BYPASSES V1**; and neonatal MT ablation permanently degrades
reach-to-grasp for MOVING targets (Atapour & Bourne 2021).

And it issued an explicit warning, which is the whole point of this rung:

> Do NOT generalise from orientation to DIRECTION selectivity — direction is
> absent at eye opening and DOES require experience (Li 2006) — the opposite
> case.

So rungs 1-2 and rung 3 must come apart:

| | orientation (BUILT) | direction (this rung) |
|---|---|---|
| from waves alone | **emerges** (0.195 vs 0.000) | should be **~ABSENT** |
| from experience | refines it (0.402 > 0.363 > 0.216) | should be **REQUIRED** |

A model that produced direction selectivity from waves would contradict Li 2006.
A model that produced it from neither would fail to reproduce development at all.
Both are reportable outcomes and both are stated in advance below.

## The mechanism (`seeds/vision_dorsal.json`, `dorsal=0` by default)

A **parallel** population — `DUnit` / `DSynapse` / `has_dunit` off the SAME
Retina, never downstream of the ventral `Unit`s — because the research says
parallel. It also leaves `seeds/vision_waves.json` byte-untouched, so every
committed rung-1/rung-2 result reproduces.

The direction mechanism is a **delay-line coincidence detector**
(`dv_unit_activate`): each DSynapse carries its own conduction `delay` and
contributes only when its pre cell's transient fired exactly `delay` steps ago.
Inputs that were SEQUENTIAL at the retina arrive SIMULTANEOUSLY at the unit iff
the sequence matches the delay gradient (`delay + position = const`).

**Why the ventral rule cannot do this, structurally:** `wv_unit_activate` counts
ANY pre-burst inside a window `[0, window_steps]` that is SHARED across all of a
unit's synapses. `a→b` and `b→a` deliver the identical set of in-window bursts,
so **no weight assignment on that rule can ever prefer one over the other**.
Order-blindness is a property of the rule, not of its parameters. That is why
rung 3 needs a new rule rather than more training.

`dv_oja_learn` is Oja's rule on the delay-gated input — Oja because the rung-2
convergence work established it is the only rule in this tree with a stable
non-zero fixed point (fixed-sign Butts never converges; BCM converges to
annihilation), and nine attempts failed purely because they were measured on a
transient.

### THE PARADIGM-CRITICAL LINE, and it is one line

A delay-line direction detector is **trivial to build**: set `delay = k − proj`
and you have direction selectivity with no learning at all. That would be
`preprocess_patches` at the motion grain. **The adapter draws every delay
UNIFORMLY AT RANDOM from {0..3}** — every direction symmetric a priori, expected
delay gradient zero along every axis. Random delays are to direction what random
ignition is to waves. Gated by
`test_the_adapter_hands_the_agent_no_direction_gradient` (max |corr(delay, pos)|
< 0.5 across units).

## The measure — CALIBRATED FIRST (PROTOCOL §1), and it needed two real fixes

**DSI** = `(R_pref − R_null)/(R_pref + R_null)`, null = pref + 180°, from
peak responses to bars drifting in 8 directions, **cross-validated** (pref chosen
on half the reps, DSI scored on the held-out half) so the argmax selection bias
does not inflate it.

Two defects were found by calibrating before measuring, not after:

1. **Independent per-direction sweeps were a pixel-quantisation artifact.** The
   first cut gave tuning curves identical for 45/135/225/315 and all 10 units the
   same DSI of 0.026 — the "direction" signal was the bar geometry landing on the
   sampling grid differently per angle. **Fix:** a direction and its opposite now
   present the EXACT same frames in reversed order (`sweep_frames`), so the only
   thing that can separate them is ORDER. The probe is thereby a per-direction
   temporal-shuffle control.
2. **A mean readout is MATHEMATICALLY INCAPABLE of measuring direction here.** A
   DUnit is linear in its arriving inputs, and over one sweep every cell fires
   exactly one transient and so contributes to exactly one step — so `sum(dact)`
   over a sweep is the sum of the unit's weights, **identical for every
   direction**. Measured on a mirrored pair: sum 48.75 vs 48.76, peak 11.07 vs
   8.95. The mean scored the hand-built IDEAL unit at **0.004**. **Fix:** the
   readout is the PEAK. Direction lives in the temporal CONCENTRATION of the
   drive, which is also what the unit's own threshold/burst rule reads.

Neither is metric surgery (PROTOCOL §5): no gate had failed, and the ideal
exemplar is precisely the instrument built to catch this.

### Calibration table (burned seeds 0-7, before any arm)

| check | result | verdict |
|---|---|---|
| **random / untrained units** | **+0.1115** (SD 0.021 across seeds) | **NOT zero — see below** |
| **ideal hand-built DS unit** (θ=0) | **+0.6000** | PASS — 4× the floor |
| **ideal hand-built DS unit** (θ=90°) | **+0.6000** | PASS |
| **duration** (waves, 0→3200 steps) | 0.1164 → 0.1298 | nearly flat (+0.013) |

**THE FLOOR IS 0.111, NOT 0, AND THAT IS A FACT ABOUT THE MODEL.**
Cross-validation removes the selection bias but not this, because it is not
noise: a unit whose delays are drawn at random has, by chance, a better delay
gradient along some direction than along its opposite, and that preference
REPLICATES because the delays are fixed. **Random wiring confers weak direction
bias for free.**

**Consequence, binding on every claim below:** an arm's absolute DSI is
meaningless and `DSI > 0` is NOT evidence of learned direction selectivity. Only
PAIRED comparisons are interpretable — arms share a seed and therefore share
their delays, so the innate bias is identical in each and cancels. The floor is
measured per-seed by an `untrained` arm.

**Dynamic range = 0.111 (floor) → 0.600 (ideal) = 0.489.** Every effect below is
also reported as a fraction of it, because a statistically significant 0.009 is
1.9% of the range and calling that "direction selectivity" would be a lie told
with a correct p-value.

## CONVERGENCE (PROTOCOL §2) — run FIRST, before any arm

Waves only, n=8 seeds, drift = ‖w(t) − w(t−50)‖/‖w(t)‖ (FIXED window).

| steps | mean DSI | weight std | drift | NaN |
|---|---|---|---|---|
| 0 | +0.1115 | 0.0495 | — | 0 |
| 200 | +0.1162 | 0.0231 | 0.1337 | 0 |
| 800 | +0.1161 | 0.0138 | 0.0267 | 0 |
| 1600 | +0.1165 | 0.0134 | 0.0105 | 0 |
| 3200 | +0.1277 | 0.0167 | **0.0044** | 0 |

**CONVERGENT** — drift falls monotonically to 0.004 and the weights settle. This
is the property fixed-sign (drift 0.49-0.75) and BCM (converges to 0.004
structure) both lacked, and it is why an arm comparison is meaningful at all.

**And re-run at the rate actually used (η=2e-3), because changing η invalidates a
convergence check made at another rate. The arms were NOT run until this passed:**

| steps | mean DSI | weight std | drift | NaN |
|---|---|---|---|---|
| 0 | +0.1115 | 0.0495 | — | 0 |
| 50 | +0.1100 | 0.0303 | 1.2412 | 0 |
| 200 | +0.1190 | 0.0151 | 0.1419 | 0 |
| 800 | +0.1266 | 0.0178 | 0.0195 | 0 |
| 1600 | +0.1255 | 0.0251 | 0.0123 | 0 |
| 3200 | +0.1299 | 0.0347 | **0.0115** | 0 |

**CONVERGENT + non-zero structure, PASS.** Drift falls monotonically over more
than two orders of magnitude (1.24 → 0.0115; rung 2's Oja scaffold was accepted
at 0.107). Weight std bottoms at 0.014 and then GROWS to 0.035 while the norm
contracts, i.e. structure is being built, not dissolved — this is neither
fixed-sign's never-settling decay nor BCM's convergence-to-annihilation. **0 NaN
at every checkpoint** confirms the stability the positive control indicated.

Note what this table ALREADY shows, before any arm: **waves move DSI by +0.018
over 3200 steps** (0.1115 → 0.1299) — 3.7% of the dynamic range. That is the H1b
question, and it is why H1b is tested as EQUIVALENCE against a SESOI rather than
as a bare null: at n=100 an effect this size will very likely be "significant"
while being negligible.

## THE POSITIVE CONTROL — which changed the design, before any arm was tested

**The question a null cannot answer: can `dv_oja_learn` produce direction
selectivity AT ALL?** If it cannot, every arm is a null instrument and three
pre-registered nulls would be worthless. So: train on the most direction-
structured input that exists — bars drifting in ONE consistent direction (this is
an INSTRUMENT check on burned seeds, **never an experimental arm**; it trains on
the probe stimulus, which is exactly why it can only calibrate, never confirm).

| η | 0 | 400 | 1600 | 6400 | NaN |
|---|---|---|---|---|---|
| 5e-4 | 0.111 | 0.111 | 0.122 | 0.213 | 0 |
| **2e-3** | 0.111 | 0.124 | **0.215** | 0.351 | 0 |
| 1e-2 | 0.111 | 0.239 | 0.351 | — | 0 |

**This invalidated the original design (η=5e-4, P2=400), which the pilot had
already run: at that setting the rule moves DSI by 0.000 even on a PERFECT
single-direction stimulus.** The pilot's arm differences (all |d| < 0.01) were
therefore measuring nothing, and reporting them as "direction does not emerge"
would have been the wrong-instrument error.

**FIXED IN ADVANCE, on positive-control grounds only:** **η = 2e-3, P1 = 1600,
P2 = 1600.** η=2e-3 is the smallest tested rate at which the mechanism expresses
a meaningful fraction of its dynamic range within a feasible run (0.215 = 21% at
1600 steps), and the dorsal population is **measurably stable** there (0 NaN in
every cell of the table — unlike the ventral population, which diverges at 2e-3
because its shared window makes `y` up to 49 where the dorsal delay-gating keeps
it small). P2 = P1 = 1600, the wave fixed-point length from rung 2.

This is instrument calibration, not a parameter search over outcomes: the choice
is made on a control that contains no arm and no hypothesis, and is frozen here
before the confirmatory run. η and P2 are **not swept again**.

## THE ARMS — what each corresponds to IN THE ANIMAL (PROTOCOL §6)

A wrong control arm cost two pre-registrations in this tree (`dark` = "no input",
when dark-reared animals **keep their waves**). Each arm is checked against a
real experiment:

| arm | phase 2 (400→**1600** steps, EQUAL in every arm) | the animal |
|---|---|---|
| `untrained` | no training at all | the FLOOR: what random wiring alone gives |
| `dark` | **waves continue** (`propagate=1`) | dark-reared: spontaneous activity, no vision. **Li 2006: no DS.** |
| `normal` | real video through a **drifting eye**, waves cease | normal rearing |
| `strobe` | the SAME retinal frames, **order permuted**, waves cease | **strobe-reared** (Cynader & Chernenko 1976): stroboscopic rearing destroys motion continuity while preserving spatial form, and **abolishes direction selectivity while sparing orientation selectivity** |

Phase 1 (1600 steps of waves) is **bit-identical in every arm** — same seed, same
RNG draws — so every arm enters phase 2 with the same receptive fields and the
same delays.

### The `normal` arm needed a fix too, and it is biology, not convenience

**Measured before running: real video at 16×16 is nearly STATIC.** At native
frame rate consecutive frames differ by 0.005, and the median-split drive gives a
burst ONSET rate of **0.6%** against a 50% duty cycle — 99% of the drive is a
standing pattern. Worse, `dv_unit_activate` reads `last_burst`, which is
overwritten every step a cell stays on, so **a sustained cell's latency is
permanently 0 and only delay-0 synapses can ever match**: on that drive the delay
line is STRUCTURALLY BLIND to video. A null would have meant "there was no motion
in the moving-experience arm", not anything about development.

Two fixes, both asserted biology:

1. **The transient (magnocellular) channel** (`dv_transient`, a RULE): the dorsal
   output fires on burst ONSET, not level. The dorsal stream is fed by transient
   M/Y-type retinal ganglion cells which adapt away static input, while the
   ventral stream's sustained P/X cells carry level — the two streams read
   different channels off the same cells, which is the parallel anatomy the
   research established. The adapter records only the FACT (`prev_burst`); the
   RULE decides what an onset is. Measured: fires exactly once per burst episode.
2. **The drifting eye** (`gaze_walk`): no animal has a stabilised retina, and a
   stabilised image **fades from perception entirely** (Ditchburn & Ginsborg
   1952; Riggs & Ratliff 1952; Troxler). The perfectly-stabilised retina is the
   unphysical model. Drift is piecewise-constant velocity, direction-**isotropic**
   by construction — the adapter hands the agent no preferred direction, exactly
   as wave ignition hands it no spatial structure.

**Measured drive per arm** (descriptive, never tested — reported so the reader
knows what each arm was):

| arm | onset rate | burst duty |
|---|---|---|
| `dark` | 0.066 | 0.131 |
| `normal` | 0.053 | 0.500 |
| `strobe` | 0.235 | 0.500 |

`normal` and `strobe` have **identical duty cycle by construction** (same frames,
permuted) and differ ONLY in order. `strobe` nonetheless delivers **4.4× the
onsets** of `normal` — that is not a confound to be removed but the manipulation
itself (temporal continuity IS what motion is), and it is named here so the
result is read with it in view.

## Hypotheses — CONJUNCTIVE, so the rung cannot pass by being inert

Per seed *i*, each arm's value is the mean cross-validated DSI over its 10 DUnits.

- **H1a (primary):** `d_normal = DSI(normal) − DSI(dark)`, two-sided.
  Predicted **> 0** — direction REQUIRES moving visual experience.
- **H1b (co-primary):** `d_dark = DSI(dark) − DSI(untrained)`, two-sided.
  Predicted **≈ 0** — direction is NOT innate and NOT built by waves (Li 2006);
  the opposite case to orientation.
- **H1c (co-primary):** `d_strobe = DSI(normal) − DSI(strobe)`, two-sided.
  Predicted **> 0** — it is MOTION, not spatial structure. Isolates order:
  identical frames, identical duty cycle, permuted.

**Bonferroni α = 0.05/3 = 0.0167 each, fixed now.**

**SESOI = 0.049** = 10% of the calibrated dynamic range (0.489). Fixed now, from
burned-seed calibration only. H1b's "≈ 0" is tested as **equivalence**: the 95%
CI of `d_dark` must lie entirely inside ±0.049. A null that is merely
non-significant is not evidence of absence; an interval inside the SESOI is.

### RUNG 3 IS BUILT iff ALL THREE hold

1. `d_normal > 0` ∧ `p < 0.0167`, **and**
2. `|d_dark|` 95% CI ⊂ (−0.049, +0.049) (equivalence to the floor), **and**
3. `d_strobe > 0` ∧ `p < 0.0167`.

H1a and H1c both require a POSITIVE effect, so the conjunction cannot be passed
by making the mechanism inert — the failure mode attempt 2 of rung 2 fell into
("removed the harm" by removing the effect). H1b's equivalence is only meaningful
because the same n detects H1a; that is stated as a condition, not assumed.

## n / seeds / statistic

- **Paired within seed. SEED IS THE UNIT OF ANALYSIS** (PROTOCOL §4) — the 10
  DUnits in a run share input and compete under winner-take-all, so they are not
  independent. Counting units inflated every early p-value in this tree.
- One-sample **two-sided sign-flip randomisation test**, 20,000 permutations, per
  hypothesis; bootstrap 95% CIs.
- **n = 100 seeds, FIXED IN ADVANCE.** Pilot on **burned seeds 0-9** (variance
  only) gave per-seed SD 0.0052 / 0.0099 / 0.0076 for d_normal / d_dark /
  d_strobe. Those SDs are from the η=5e-4 setting the positive control then
  invalidated, so they are treated as a LOWER bound; n=100 gives ≥80% power at
  α=0.0167 for |δ| ≈ 0.005 even at 3× the pilot SD, i.e. far inside the SESOI.
  n=100 is chosen to make an equivalence verdict on H1b possible, not to detect
  the smallest effect.
- **Confirmatory seeds: 4000-4099** — never used for anything (ledger appended in
  `VISION_PROTOCOL.md`). Burned here: 0-13 (calibration, positive control,
  pilot).

**Exactly three hypothesis tests. No sweeps. No re-runs.** A further attempt
needs a NEW pre-registration with a NEW mechanism-level hypothesis — never a
parameter search over η, P2, `max_delay` or `delay_tol`.

## MY PREDICTION, STATED IN ADVANCE, WITH ITS PROVISOS

**I predict the conjunction FAILS, on H1a.**

The pilot (η=5e-4, P2=400 — the invalidated setting, so this is a weak prior, not
data about the real design) put d_normal at **−0.004** and d_strobe at **−0.004**:
both the OPPOSITE of the predicted sign, and both ≈ 0.

The mechanistic reason I expect H1a to fail, and it is the proviso to watch:
**Oja converges to the leading principal component of whatever it is shown, and
`dark`'s waves ARE coherent motion.** A travelling wave sweeping a receptive
field is exactly the input a delay line reads; the positive control proves the
rule learns direction from coherent motion. So `dark` is NOT a no-motion control
in this model the way it is in the animal — the animal's waves are far slower
than visual motion and do not drive the transient M pathway the way a moving edge
does, but nothing in this model implements that separation. If `dark` and
`normal` both deliver coherent motion at ~1 px/step, H1a should be ≈ 0 and **H1b
should FAIL its equivalence** (waves should build DS).

Against that: the measured wave duration curve is nearly flat (0.111 → 0.128 over
3200 steps at η=5e-4), i.e. waves empirically build almost no DS — plausibly
because wave direction at a given RF is ISOTROPIC across ignitions, so the
covariance has no dominant direction and Oja's leading PC is the DC component.
If that is what dominates, **H1b passes** and the differential prediction survives
its hardest test.

**H1c is my best hope and I am genuinely uncertain**: `strobe` has no coherent
motion at all, so it should not build DS — but it delivers 4.4× the onsets, and
under Oja more unstructured drive actively DISSOLVES structure (rung 2's
`sutured`: −0.147). If `strobe` dissolves the innate delay bias, d_strobe > 0
would be **passing for the wrong reason** — destruction, not construction. The
`untrained` arm is what makes that diagnosable: if `strobe` < `untrained`, the
effect is dissolution.

**What would make me wrong in the interesting direction:** H1a passing would mean
real visual motion carries direction structure that isotropic waves do not, which
is precisely Li 2006's claim, and would be the first thing in this tree to
reproduce it.

**A negative here is a result** and will be reported exactly as observed. The
mechanism is proven to work (positive control, 0.111 → 0.351); if development's
own inputs do not drive it, that is a fact about the inputs and the rule, not a
bug to be tuned away.

---

# OUTCOME (run 2026-07-17, exactly as specified — n=100, seeds 4000-4099)

```
H1a d_normal  (normal - dark)      -0.0035  95% CI [-0.0077, +0.0005]  p=0.0922   (predicted > 0)
H1b d_dark    (dark - untrained)   +0.0096  95% CI [+0.0048, +0.0144]  p=0.0001   (predicted ~ 0)
H1c d_strobe  (normal - strobe)    +0.0114  95% CI [+0.0073, +0.0156]  p=0.0001   (predicted > 0)

  H1a (experience produces direction)  : FAIL
  H1b (waves do NOT, equivalence +-0.049): PASS
  H1c (motion, not spatial structure)  : PASS
```

# **DECISION: NOT BUILT** — the conjunction fails on H1a.

| arm | mean DSI | vs floor | reading |
|---|---|---|---|
| `dark` (waves continue) | 0.1125 | +0.0096 | waves build ~nothing |
| `normal` (video + drifting eye) | 0.1089 | +0.0061 | **experience builds ~nothing** |
| `untrained` (the floor) | 0.1028 | — | what random delays alone give |
| `strobe` (same frames, permuted) | 0.0975 | **−0.0054** | **below the floor — dissolution** |

## EVERY EFFECT IS INSIDE THE SESOI. Two are "significant" and none is real.

Held to the standard this document fixed in advance (0.049 = 10% of the 0.489
dynamic range; observed floor 0.1028 ⇒ range 0.497):

| | effect | % of dynamic range |
|---|---|---|
| H1a | −0.0035 | **−0.7%** |
| H1b | +0.0096 | **+2.0%** |
| H1c | +0.0114 | **+2.3%** |

**Three tests, two p=0.0001, zero meaningful effects.** H1b and H1c are
statistically bulletproof and scientifically negligible. This is exactly the trap
the pre-registration named — *"a statistically significant 0.009 is 1.9% of the
range and calling that 'direction selectivity' would be a lie told with a correct
p-value"* — and it is why H1b was specified as an EQUIVALENCE test rather than a
bare null. That choice paid: H1b's p=0.0001 would have "refuted" the null while
its CI [+0.0048, +0.0144] sits entirely inside ±0.049 and **establishes
equivalence to the floor**. A bare null test would have reported the opposite
conclusion from the same numbers.

**H1c passes the pre-registered rule on a technicality** (`d > 0 ∧ p < 0.0167`;
no SESOI was attached to H1a/H1c). It is recorded as a PASS because that is what
was written down, and simultaneously as meaningless at 2.3% of range. The
conjunction fails on H1a regardless.

## MY PREDICTION HELD — and it is the proviso that tells us what is going on

The pre-registration said: **"I predict the conjunction FAILS, on H1a."** It does.

But being right about the outcome is cheap; the pre-registration staked two
COMPETING mechanisms on H1b, and that is where the information is:

> **(1)** if `dark`'s waves ARE coherent motion driving DS ⇒ H1a ≈ 0 **and H1b
> should FAIL its equivalence** (waves should build DS).
> **(2)** against that: wave direction at an RF is ISOTROPIC across ignitions, so
> the covariance has no dominant direction and Oja's leading PC is the DC
> component ⇒ **H1b passes**.

**Proviso (2) is what held. H1b PASSED equivalence (+2.0% of range).** So the
reason I gave for expecting H1a to fail — "`dark`'s waves are coherent motion, so
`dark` is not a no-motion control" — is **WRONG, and the data say so**: waves
build essentially no direction selectivity, exactly as Li 2006 requires.

**And that makes the real finding worse than the one I predicted.** H1b passing
means waves don't build DS. H1a failing means `normal` doesn't beat `dark`.
Together: **NEITHER waves NOR moving visual experience build direction
selectivity in this model.** `normal` sits +0.0061 (1.2% of range) above the
untrained floor. The rung does not fail because waves stole the effect; it fails
because **there is no effect in either arm.**

## THE DIAGNOSIS — and the defect is MY DESIGN, not the biology

The positive control proves the rule CAN learn direction (0.111 → 0.351, 49% of
range) — but only from a stimulus with ONE consistent direction. Both
experimental arms are **direction-ISOTROPIC**, and one of them is isotropic
*because I made it so*: `gaze_walk` redraws its drift direction uniformly every
20 steps, deliberately, so the adapter would hand the agent no preferred
direction (the paradigm rule — and it is still the right call; a drift with a
built-in direction bias would have been `preprocess_patches` at the motion
grain).

So the mechanism-level statement, which is a fact about the RULE:

> **Oja's fixed point is the leading principal component of the TIME-AVERAGED
> input covariance. Averaged over a training distribution whose motion is
> isotropic, there is no dominant direction to find — however much coherent
> motion each individual epoch contains.** The rule cannot develop direction
> selectivity from input that is isotropic *on average*, and natural visual
> experience IS isotropic on average.

Real animals develop DS from natural input anyway. They therefore do not do it
this way: a neuron must lock onto a *locally* consistent direction and keep it —
symmetry-breaking faster than the averaging timescale — rather than converge to
the average. Oja's stability, the very property that rescued rung 2 from nine
failed attempts on a transient, is what forbids it here: **a contraction to the
mean of an isotropic distribution is the mean.**

## Was H1c a pass for the wrong reason? YES — and the `untrained` arm proves it

The pre-registration flagged this in advance: *"if `strobe` dissolves the innate
delay bias, d_strobe > 0 would be passing for the wrong reason — destruction, not
construction. The `untrained` arm is what makes that diagnosable."*

It is diagnosable, and the answer is that **roughly half of H1c is destruction**:

```
strobe - untrained = -0.0054   (BELOW the floor — strobe DISSOLVES the innate bias)
normal - untrained = +0.0061   (barely above the floor)
                     -------
H1c = normal - strobe = +0.0114
```

`strobe` delivers 4.4× the onsets (0.2534 vs 0.0496) with an identical duty
cycle, and under Oja unstructured drive actively dissolves structure — the same
mechanism that produced rung 2's `sutured` −0.147. So H1c's "motion beats
scrambled" is ~47% *scrambled destroying what random wiring gave* and ~53%
*motion adding a negligible amount*. **It is not evidence that motion builds
direction selectivity.** Without the `untrained` arm this would have been
reported as H1c passing and the rung as one-third built.

## What is CLAIMED

1. **The dorsal population is a working, convergent, parallel mechanism.** Drift
   1.24 → 0.0115 over 3200 steps at the rate used, 0 NaN, weight structure
   growing 0.014 → 0.035. Neither fixed-sign's never-settling decay nor BCM's
   annihilation.
2. **The mechanism can learn direction** — positive control, 0.111 → 0.351 (49%
   of range), from a single-direction stimulus.
3. **Waves do not build direction selectivity** (H1b, equivalence to the floor
   within ±0.049, n=100, fresh seeds). This reproduces the research's
   differential warning — direction is NOT innate, unlike orientation — but see
   below for why it is weak evidence.

## What is NOT claimed

- **NOT that direction selectivity requires experience.** H1a FAILED. Moving
  experience produced +1.2% of dynamic range over the floor. The differential
  prediction's *positive* half is unreproduced.
- **NOT that H1b vindicates Li 2006.** Waves build nothing — but so does
  everything else in this model, so "waves specifically do not" is not evidence
  about waves. A null that is a special case of a universal null is not a
  finding about its subject. This is the honest reading and it demotes claim 3
  above.
- **NOT that motion beats scrambled input.** H1c passes as written and ~half of
  it is `strobe` dissolving the innate bias below the floor.
- **NOT that the delay-line account of direction selectivity is wrong.** What is
  measured is that *this rule* on *this input* does not develop it. The research
  refuted 0-3 the Hebbian-vs-sparsity question; this licenses nothing about which
  biological mechanism is correct.
- **NOT anything about absolute DSI.** The floor is 0.103, not 0 — random delays
  confer a real replicating direction bias — so only the paired differences above
  mean anything.
- **NOT that the arms delivered equal drive.** `strobe` has 4.4× `normal`'s
  onsets (0.2534 vs 0.0496); identical duty cycle, but the onset gap is named,
  not removed.

## THE NAMED NEXT HYPOTHESIS (NOT run, NOT built here)

**A rule whose attractor is not the average.** Oja converges to the leading PC of
the time-averaged covariance, which is direction-isotropic for any natural input
— so no drive, schedule, aperture or η fixes this, and **no parameter of the
present rule is worth sweeping** (η, P2, `max_delay`, `delay_tol` are all frozen
and stay frozen). The required property is *symmetry-breaking faster than the
averaging timescale*: a unit that locks onto a locally-consistent direction and
keeps it — e.g. a rule with bistable/hysteretic weights, or an anti-Hebbian
lateral term between DUnits so that once a unit claims a direction its neighbours
are pushed off it (the model has NO lateral interactions at all, which is also
why orientation MAPS are unbuilt). That is a mechanism-level hypothesis and it
requires its own pre-registration.

**A second, cheaper thing to settle first:** whether natural visual motion is
anisotropic at the RF/epoch grain in a way waves are not. My `normal` arm cannot
answer it — `gaze_walk`'s drift is isotropic by construction — so the
experience-dependence of direction is currently **untested**, not refuted. That
distinction is the honest status of this rung.

## Honest status

**Rung 3: NOT BUILT.** The mechanism is real, convergent and demonstrably capable
(positive control); the arms are valid (checked against dark-rearing and strobe
rearing, equal duration, correct control, paired delays); the measure is
calibrated (ideal 0.600, floor 0.103, duration flat) and cost two real fixes
found before the run. The rule simply does not develop direction selectivity from
development's own inputs, and the reason is now measured rather than inferred:
**its attractor is the average, and the average has no direction.**

Rungs 1 and 2 are untouched: `dorsal=0` by default, `vision_waves.json`
byte-unchanged, vision suite green.
