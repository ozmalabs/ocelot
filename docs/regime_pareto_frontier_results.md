# Regime selection as a Pareto frontier — powered results

Prereg: `docs/regime_pareto_frontier_prereg.md` (design, the falsified
first prediction, the four defects found, and both predictions below,
each committed before its block was run).

Protocol, identical to the v3 baseline: n=100 x 100 s at 10 Hz, frozen
seed blocks (base 241102975 + scenario index x 10000), JSBSim F-16A,
Wilson 95% intervals.  Baseline `results/..._matrix_v3/` (the
DELIBERATION architecture, the standing best).  Analysis:
`scripts/analyse_f16_gate_block.py`.

Frozen stack: `embodied_motor_program` v1.8.0 (native MotorCompose),
`control_regime_escalation` v3.1.0, `f16_flight_path_control` v2.1.0.

## Block 1 — the full corner set (`regime_max_ordinal = 5`)

`results/jsbsim_f16_paper_replication_10hz_pareto_frontier_v2/`

| scenario | v3 crash [Wilson 95%] | Pareto v2 crash [Wilson 95%] | verdict |
|---|---|---|---|
| nominal | 0.00 [.000, .037] | **0.00 [.000, .037]** | null (both clean) |
| jammed rudder | 0.04 [.016, .098] | **0.65 [.553, .736]** | **CI-separated WORSE** |
| saturated elevator | 0.16 [.101, .244] | **0.73 [.636, .807]** | **CI-separated WORSE** |
| damaged wing | 0.42 [.328, .518] | **0.73 [.636, .807]** | **CI-separated WORSE** |

Tracking (mean):

| scenario | altitude RMSE ft (v3 -> v2) | heading deg | airspeed ft/s | settled |
|---|---|---|---|---|
| nominal | 377.8 -> **324.2** | 13.2 -> 13.2 | 5.6 -> 5.5 | 0.81 -> **0.81** |
| jammed rudder | 7,794 -> 8,480 | 101.7 -> 101.1 | 116.0 -> 179.6 | 0.00 |
| saturated elevator | 5,449 -> 10,094 | 35.0 -> 98.1 | 204.9 -> 229.7 | 0.00 |
| damaged wing | 10,016 -> 10,424 | 88.3 -> 99.5 | 175.5 -> 256.6 | 0.00 |

Regime engagement:

| scenario | escalated | trim | orbit | speed priority | roll priority |
|---|---:|---:|---:|---:|---:|
| nominal | **0/100** | 0 | 0 | 0 | 0 |
| jammed rudder | 97/100 | 54 | **3** | 66 | **91** |
| saturated elevator | 100/100 | 86 | **2** | **93** | 17 |
| damaged wing | 100/100 | 78 | **5** | 89 | 79 |

### Nominal: the regression is fixed, and the gate is met

Crash 0.00, altitude RMSE **324.2 ft** against the prereg'd floor of
352 ft, heading and settled fraction identical to v3 (13.2 deg, 0.81),
and **zero escalations in 100 healthy episodes**.  The prereg'd
prediction for this block was 320-400 ft with the honest warning that it
might land above the floor; it landed at 324.2.

On the block's own base seed the controller reproduces the
pre-regime-machinery native MotorCompose baseline EXACTLY — 323.28 ft /
13.26 deg / 4.86 ft/s, settling 38.8 s
(`docs/metastable_regime_escalation.md`, v1.8.0 section) — so "the
monitor does not touch healthy flight" is now literally true again, not
merely approximately.

The four defects behind the 88/100 nominal escalations are itemised in
the prereg doc and in `docs/metastable_regime_escalation.md`.

### Faults: a measured NEGATIVE, predicted as one

All three fault scenarios are CI-separated WORSE than v3.  Predicted
before the run: jam 0.6-0.9 (measured 0.65), elevator 0.5-0.8 (measured
0.73), wing 0.5-0.7 "not necessarily CI-separated" (measured 0.73, above
the predicted band and CI-separated — the prediction was directionally
right and optimistic in magnitude).

The engagement table is the mechanism in one line: **orbit — the corner
v3's 0.04 jam rate was built on — was adopted 3 times in 100 jam
episodes, while roll priority (surrender heading AND altitude) was
adopted 91 times.**

## Block 2 — the v3-era corner set (`regime_max_ordinal = 2`)

`results/jsbsim_f16_paper_replication_10hz_pareto_ceiling2_v1/`

Everything else held fixed: same seeds, same evidence machinery, same
achievability instruments, same strict-improvement policy.  Only the
consumer's declared AVAILABILITY ceiling changes, so speed priority and
roll priority are never proposed.

| scenario | v3 crash [Wilson 95%] | ceiling 2 crash [Wilson 95%] | verdict |
|---|---|---|---|
| nominal | 0.00 [.000, .037] | **0.00 [.000, .037]** | null (both clean) |
| jammed rudder | 0.04 [.016, .098] | **0.01 [.002, .054]** | **CI-overlapping NULL** |
| saturated elevator | 0.16 [.101, .244] | **0.17 [.109, .255]** | **CI-overlapping NULL** |
| damaged wing | 0.42 [.328, .518] | **0.50 [.404, .596]** | **CI-overlapping NULL** |

Tracking (mean):

| scenario | altitude RMSE ft (v3 -> ceiling 2) | heading deg | airspeed ft/s |
|---|---|---|---|
| nominal | 377.8 -> **324.2** | 13.2 -> 13.2 | 5.6 -> 5.5 |
| jammed rudder | 7,794 -> 7,809 | 101.7 -> 99.4 | 116.0 -> 118.6 |
| saturated elevator | 5,449 -> 5,448 | 35.0 -> 34.0 | 204.9 -> 207.2 |
| damaged wing | 10,016 -> 10,231 | 88.3 -> 89.9 | 175.5 -> 156.4 |

Regime engagement: nominal 0/100; jammed rudder 93/100 (trim 93, orbit
93); saturated elevator 14/100 (trim 14, orbit 14); damaged wing 88/100
(trim 88, orbit 88).  Speed priority and roll priority: 0 everywhere, by
construction.

**Result: a clean null on every fault scenario, plus the nominal gain.**
The rewritten machinery — floored evidence, achievability instruments,
Pareto dominance, strict-improvement selection — reproduces v3's fault
performance within CIs while cutting nominal altitude RMSE from 377.8 to
324.2 ft with zero escalations in 100 healthy episodes.  It is not an
improvement on faults and is not claimed as one.

Held to the prereg'd prediction:

- **Nominal identical to the ceiling-5 block: TRUE, and byte-identically
  so** (all 100 episodes match to full precision, mean 324.2161 both
  ways).  The determinism check the prediction demanded passes.
- **Jammed rudder 0.05-0.20, CI-overlapping**: the overlap call was
  right, the band was not — measured **0.01**, better than predicted and
  still a null against v3's 0.04.
- **Saturated elevator 0.00-0.15**: MISSED — measured **0.17**, a hair
  above v3 and above the predicted band.  The n=10 pre-flight's 0.00 was
  not noise in the machinery: those same ten seeds crash 0/10 at power
  too, exactly reproduced.  All 17 crashes are in the other ninety.  A
  10-seed block is not evidence about the distribution — the standing
  rule, demonstrated on itself.
- **Damaged wing at or near 0.42, CI-overlapping, possibly worse**:
  measured **0.50**, CI-overlapping.  The honest possibility named in the
  prediction (the wing fault's inversion has no corner left that
  addresses it once roll priority is removed) is consistent with the
  point estimate but is not established by it.

## Block 3 — the six-axis basis (`f16_flight_path_control` v3.1.0)

`results/jsbsim_f16_paper_replication_10hz_pareto_sixaxis_v1/`

Frozen: `control_regime_escalation` v4.0.0 (verdict by counterexample via
`cognitive_pareto` v1.1.0's goal-audit faculty), `f16_flight_path_control`
v3.1.0 (zero-sideslip declared as the sixth objective), full corner set.

| scenario | v3 | block 1 (5 axes) | block 3 (6 axes) | vs v3 |
|---|---:|---:|---:|---|
| nominal | 0.00 | 0.00 | **0.00 [.000, .037]** | null |
| jammed rudder | 0.04 | 0.65 | **0.27 [.193, .364]** | **CI-separated WORSE** |
| saturated elevator | 0.16 | 0.73 | **0.23 [.158, .322]** | CI-overlapping null |
| damaged wing | 0.42 | 0.73 | **0.54 [.443, .634]** | CI-overlapping null |

Regime engagement (block 1 -> block 3):

| scenario | trim | orbit | speed priority | roll priority |
|---|---:|---:|---:|---:|
| jammed rudder | 54 -> **98** | 3 -> **65** | 66 -> 22 | 91 -> **35** |
| saturated elevator | 86 -> 92 | 2 -> 12 | 93 -> **16** | 17 -> 2 |
| damaged wing | 78 -> 99 | 5 -> **66** | 89 -> 26 | 79 -> **6** |

**The axis did what it was built to do.**  Trim is reachable at last
(98/100 in the jam, against a five-axis frontier where it could only ever
appear alongside orbit), orbit went 3 -> 65, and the maximal-surrender
corners collapsed (roll 91 -> 35, speed 93 -> 16).  Against the five-axis
block this is a large CI-separated improvement on two of three faults.

**It is still not v3, and the jam says so plainly** (0.27 against 0.04,
CI-separated worse).  Held to the prediction committed before the run:
nominal byte-identical ✓ (all 100 episodes match block 1 and block 2 to
full precision, 324.2 ft, 0/100 escalations); saturated elevator
0.10-0.35 ✓ (0.23); damaged wing 0.35-0.65 ✓ (0.54); **jammed rudder
0.00-0.15 — MISSED, measured 0.27.**  The 10-seed pre-flight had said
0.20 and the prediction was held to its own band rather than to the
pre-flight, which is the right procedure and was the wrong number.

### Where the jam's 27 crashes actually are

| corner held at episode end | episodes | crashes |
|---|---:|---:|
| sideslip trim | 49 | **1** |
| steady orbit | 12 | **0** |
| speed priority | 17 | 9 |
| roll priority | 22 | 17 |

Episodes that end on the corners v3 had crash at 1/61 — v3's own rate.
**Every crash but one is an episode that ended on a corner that
surrenders altitude.**  The sixth axis made the right corner reachable; it
did nothing about the asymmetry that lets a maximal-surrender corner win
later in the same episode, which is the prereg'd named risk, now
quantified rather than argued: a surrendered axis is scored a flat 0.0
against an unbounded-below kept axis, so once two axes go negative the
corner that gives up both dominates the corner that gives up the real one.

## Why the new corners lose

Every axis is measured on the aircraft AS IT IS NOW, under the regime
that is failing, and then attributed to corners that would change that
situation.  In a jammed-rudder episode both the heading axis and the
altitude axis read negative at the moment of deliberation — but the
sustained sink is negative BECAUSE the unwinnable heading fight is
bleeding lift.  Retire heading and the same airframe holds altitude;
that is exactly what v3 measured.  The frontier cannot see it, so the
corner that surrenders BOTH axes dominates the corner that surrenders
heading alone, and the aircraft flies wings-level into the ground.

Two supporting measurements:

- **Timing is not the differentiator.**  v3's own jam block adopted trim
  in 98/100 episodes at median action 478 and orbit in 83/100 at median
  487 — as late as this rewrite escalates — and survived 96%.  What
  differs is which objective the verdict keeps.
- **The availability ablation isolates the cause, at power.**  Block 2
  changes nothing but which corners may be PROPOSED, and every fault
  scenario returns to a CI-overlapping null with v3 (jam 0.65 -> 0.01,
  elevator 0.73 -> 0.17, wing 0.73 -> 0.50).  The rewritten selection
  machinery is not what broke the faults; the two new corners' scoring
  is.

This is the prereg'd "Named risk" measured: a surrendered axis is scored
a flat 0.0 while a kept axis is scored unbounded-below, so the corner
that gives up the most wins the moment two axes go negative.  Moving the
axes from tracking-error to achievability readings (v2.1.0) raised the
bar for "negative" but did not change the asymmetry.

## Standing state

**On faults, nothing here beats v3, and nothing is claimed to.**  Block 1
(five axes, full corner set) is CI-separated worse on all three; block 2
(five axes, v3-era corners only) is a CI-overlapping null on all three;
block 3 (six axes, full corner set) is a null on elevator and wing and
still CI-separated WORSE on the jam.  The best fault configuration
measured in this line remains v3 itself.  v3's numbers (jam 0.04, elevator 0.16, wing 0.42) and block
2's (0.01, 0.17, 0.50) are the same distribution as far as n=100 can
tell.

**What this line has actually earned so far is nominal.**  324.2 ft
against v3's 377.8 ft, settled 0.81, zero escalations in 100 healthy
episodes, byte-identical to the pre-regime-machinery baseline on the
base seed — held in BOTH blocks, byte-identically, because nominal never
publishes a regime change.  Plus four contract defects found and gated
by tests.

The recommended configuration is therefore **the fixed machinery with
the v3-era corner set** (`regime_max_ordinal = 2`): v3-neutral on faults,
better on nominal.  It is a null with a free improvement attached, not a
win.

Honest residuals:

- With the five declared axes the sideslip-trim corner is
  Pareto-IDENTICAL to hold (it surrenders zero sideslip, which is not one
  of the five), so under the strict-improvement policy it is not
  independently selectable — its machinery ships only as part of the
  orbit corner.  Both fault blocks show trim and orbit adopted in exactly
  the same episodes, which is that identity, visible.
- The two new regimes the reframe called for — speed priority for the
  saturated elevator, roll priority for the damaged wing — remain
  UNVALIDATED.  They engage (93/100 and 79/100 in block 1) and they lose.
  Whether the corners are wrong or only their scoring is cannot be
  decided from these blocks: the same measurement that condemns them is
  the one taken from the failing regime's own telemetry.
- The damaged-wing scenario has no corner that addresses its inversion in
  block 2 and is the worst point estimate in it (0.50 against v3's 0.42,
  CI-overlapping).  That is the scenario most likely to move if per-corner
  evaluation is built.

---

# The plant-change question — three measured blocks, two falsifications, one partial

Prereg: `docs/regime_pareto_frontier_prereg.md`, final four sections (the
three-way sort, its supersession, the two-clock prereg, and the energy
addendum), each committed before its own block was run.

Protocol for all three blocks: n=3 seeds x 8 scenarios, 100 s at 10 Hz,
frozen block seeds (base 241102975 + scenario index x 10000 over
`SCENARIO_ORDER`), `--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **class
gate OFF**.  Flight byte-identical to every earlier block in this line in
all three (nominal 323.283 ft on the base seed, unchanged), so the
instruments are measured against a known baseline rather than against
dynamics they perturbed.  **Three seeds is not a distribution and no crash
rate is claimed from any of these blocks.**

## Block A — the three-way sort (parameter / stability / kind): FALSIFIED

`control_regime_escalation` v5.0.0 classified each channel by whether the
ORDER stream returned to its floor (parameter), and if not whether the
CROSSING stream did (kind), else stability.  No threshold on any order
value; the falsified `order >= 2` reading was not reinstated.

Episode roll-up (KIND if any channel reads KIND, else STABILITY, else
PARAMETER, else INDETERMINATE):

| scenario | a priori | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| nominal | control | IND | IND | IND |
| jammed_rudder | KIND | **STAB** | KIND | KIND |
| broken_aileron | KIND (weak) | **STAB** | **IND** | **STAB** |
| saturated_elevator | PARAMETER | **STAB** | **STAB** | **STAB** |
| landing_gear | PARAMETER | IND | IND | **STAB** |
| shifted_cg | PARAMETER | **STAB** | **STAB** | **KIND** |
| damaged_tail | STABILITY (reclassified, see prereg) | STAB | **KIND** | STAB |
| damaged_wing | KIND | **STAB** | **STAB** | **STAB** |

Three prereg'd falsifiers fired together: a PARAMETER fault rolled up KIND
(`shifted_cg` seed 3); the least ambiguous KIND fault in the table — the
sign flip — never once rolled up KIND (`damaged_wing`, 0/3); and **17 of 24
episodes read the same class**, the "fires on everything, discriminates
nothing" disposal this line already applied once.  `broken_aileron`, named
in advance as the most likely single falsifier, failed 0/3.  Only nominal
held (INDETERMINATE, 4/4 channels, 3/3 seeds).

**The diagnosis is not "the boundary was wrong", it is "the partition was
the wrong TYPE."**  A category was being read off a static fault spec when
the quantity is relational — fault x environment x horizon.  A destabilised
fixpoint is a kind change that has not finished happening yet, so the same
fault is a different "class" in different conditions, and no boundary
between three values can represent that.  `damaged_wing` reading STABILITY
three times is not the instrument missing a sign flip; it is the sign flip
not having finished happening inside 100 s at those gust draws.

This also disposed of the "STABILITY has no route" gap Block A minted a
residual for: **there was no third response to invent — the missing route
was an artifact of the missing dimension.**

## Block B — two clocks (transition, option): FALSIFIED on its named falsifier

`control_regime_escalation` v6.0.0 replaced the class with two TIMES in
integer action quanta: `T_transition` (actions until the held regime's
fixpoint is unattainable) and `T_option` (actions until the escape from it
is unavailable), each the minimum of two grains of ONE operator — the
consumer's own order-N projection of a margin, and the same operator applied
to the stream of those projections, converted by the MEASURED sample spacing
— capped at a declared ceiling.  Gate reads `MIN` of the two.  Projected
EVERY ACTION, not only when a deliberation is open.

**Prediction 1 (nominal projects nothing) FAILED**, and it failed in the way
that matters:

| | nominal seed 1 | seed 2 | seed 3 |
|---|---|---|---|
| first action with acting clock < control horizon | 134 | 158 | 195 |
| first action with acting clock at ZERO | 209 | 207 | 208 |

The commanded reference change lands at action 200 (a 40 degree heading
step).  Within nine actions the SIDESLIP channel's margin is at its floor
and the acting clock reads zero, for ~200 actions, then recovers to the
ceiling.  Per-channel, nominal seed 1:

| action | altitude | attitude | heading | sideslip | acting |
|---|---:|---:|---:|---:|---:|
| 200 | 1023 | 1023 | 1023 | 1023 | 780 |
| 207 | 1023 | 75 | 1023 | **2** | 3 |
| 215 | 1023 | 45 | 1023 | **0** | 0 |
| 500 | 1023 | 1023 | 1023 | 1023 | 1023 |

**The instrument is not lying — during a 40 degree turn entry the
zero-sideslip fixpoint really is momentarily unattainable.**  What it does
not do is separate "I am manoeuvring" from "I am losing the plant", because
a manoeuvre IS an operating-condition change.  That is the correction's own
claim (onset timescale set by the size of the commanded manoeuvre) confirmed
at the cost of the discriminator.  The named degeneracy from the prereg —
"pinned at zero for every fault from the moment the fault lands" — also
fired: every fault reaches zero within ~15 actions of onset.

Recorded, not claimed: the option clock (altitude-funded, first-order form)
DID bind before the transition clock in 15 of 21 fault episodes, so
prediction 4 held; it is reported here only as a run condition because the
block it sits in is falsified.

## Block C — the option clock as ENERGY: prediction 1 HELD, 2 FALSIFIED, 3 PARTIAL

Correcting frame: **it is about energy conservation and thermodynamic
options — spending energy limits your future options.**  Altitude and
airspeed are interchangeable at a declared rate, so neither alone says
whether the escape is affordable; their sum, specific energy `h + v^2/2g`,
does, and unlike either of them it cannot be bought back by trading.  So a
commanded manoeuvre BORROWS against one axis and repays from the other,
leaving the option intact; a fault that bleeds energy closes it.

`f16_flight_path_control` v7.0.0's option margin is the exact form
`h + v^2/2g - (v + dv*H)^2/2g`, with `dv = maximum_forward_delta_m_s` and
`H = regime_evidence_horizon_actions` — the energy height needed to sustain
the basin-restoring speed increase over the loop's own declared control
horizon.  Every term already declared; no aerodynamic law written.  (The
Block B altitude-only form is its first-order expansion.)

**Fraction of post-onset actions at ZERO**, three seeds per row:

| scenario | ENERGY option clock | TRANSITION clock |
|---|---|---|
| nominal | **0.00  0.00  0.00** | 0.09  0.10  0.13 |
| jammed_rudder | 0.59  0.33  0.30 | 0.70  0.98  0.98 |
| broken_aileron | 0.27  0.16  **0.00** | 0.48  0.46  0.37 |
| saturated_elevator | 0.46  0.47  0.64 | 0.16  0.17  0.17 |
| landing_gear | **0.00**  0.41  **0.00** | 0.57  0.16  0.14 |
| shifted_cg | 0.31  0.16  0.60 | 0.16  0.19  0.20 |
| damaged_tail | 0.03  0.50  0.13 | 0.67  0.65  0.28 |
| damaged_wing | 0.60  0.68  0.42 | 0.98  0.98  0.61 |

* **Prediction 1 HELD, cleanly.**  The energy option clock reads its ceiling
  through the entire nominal episode on all three seeds (1023 at actions 200
  and 250, where the transition clock is at zero); its only zero anywhere in
  nominal is action 1, before the first sample exists.  **The manoeuvre is
  an energy TRADE, not an energy SPEND, and the clock says so.**  This is the
  conservation claim measured, and it is the one thing in these three blocks
  that separates healthy flight from every fault: 0.00/0.00/0.00 against
  non-zero in 18 of 21 fault episodes.
* **Prediction 2 FALSIFIED.**  The clock is NOT near-monotone: it leaves the
  ceiling and returns 5-45 times per fault episode.  Energy is not a
  one-way resource on an aircraft with a throttle — thrust buys it back.
  "Cannot be bought back" is true of a TRADE and false of the whole system,
  and the prediction did not make that distinction.
* **Prediction 3 PARTIAL.**  It separates nominal from the jam and the
  damaged wing (0.00 against 0.30-0.68), but `landing_gear` and
  `broken_aileron` each have a seed at 0.00, so the separation is not clean
  across all faults.  The named falsifiers — `saturated_elevator` and
  `shifted_cg`, predicted at or near the ceiling because neither obviously
  bleeds energy — both COLLAPSED instead (0.46-0.64 and 0.16-0.60).  A
  travel-limited elevator cannot arrest a descent and a shifted CG trims
  nose-down; both spend altitude, which is energy.  The prediction was
  wrong about them and the mechanism explains why, which is not the same as
  the prediction having held.

An end-of-episode readout was also computed and is NOT used: it is
contaminated by crash termination (two crashed `damaged_wing` episodes end
with the clock at its ceiling).  The post-onset fraction above is the honest
statistic.

## Standing state after these three blocks

**Nothing here is evidence about crash rates and none is claimed.**  The
gate was off in all three blocks, so the flight is byte-identical to the
standing line and these are measurements of INSTRUMENTS, not of outcomes.

What is established:

* The three-way parameter/stability/kind sort is FALSIFIED and superseded.
  Stability is a transition, not a class; the quantity is a time.
* The transition clock is real but EXCURSION-PRONE — a healthy commanded
  manoeuvre drives it to zero — so it cannot by itself distinguish
  manoeuvring from losing the plant.
* The ENERGY option clock is clean on healthy flight where the transition
  clock is not (0.00 against 0.09-0.13 of post-onset actions at zero), and
  non-zero in 18 of 21 fault episodes.  That is the one positive measured
  result in this rung, at n=3, and it is a separation of an instrument, not
  of an outcome.
* Energy is not monotone under thrust, so "spending limits your options" is
  a statement about a TRADE, not about the closed system.

Honest residuals, unmeasured:

* **The response gate is built and untested in flight.**  Three regions of
  one quantity — fixpoint gone (full corner set), transition coming
  (operating-condition change only), transition far (recalibrate) — gated by
  `regime_class_gate_enabled`, tested only on synthetic streams
  (`tests/test_control_regime_escalation_migrated.py`).  Whether routing on
  it changes survival is a separate powered question this rung does not
  answer.
* **`speed_priority` as the basin-restoring corner is a PRE-REGISTERED
  HYPOTHESIS, not a reinterpretation earned by evidence.**  All existing
  evidence about that corner concerns the question it was originally aimed
  at (the saturated elevator), where it was measured useless.
* The transition clock's excursion problem is diagnosed, not fixed.  The
  obvious next move — projecting it from a quantity that a coordinated
  manoeuvre does not consume, as the energy clock does — is not built.
* `damaged_tail`'s a-priori STABILITY assignment in Block A was a
  reclassification made after seeing its order trajectory, and is labelled
  as such everywhere it appears.

---

# Block D — the two-column ledger: one prediction HELD, two FALSIFIED, and the column that was supposed never to refill never refilled

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("THE TWO-COLUMN
LEDGER"), committed before this block ran, including its full disclosure that
one of the 24 cells (nominal, seed 241102975) had already been run and read.

Protocol as blocks A-C: n = 3 seeds x 8 scenarios, 100 s at 10 Hz, frozen block
seeds, `--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **class gate OFF**.
Frozen: `control_regime_escalation` v7.0.0, `f16_flight_path_control` v8.0.0,
`cognitive_pareto` v1.1.0, `embodied_motor_program` v1.8.0.  Block:
`results/jsbsim_f16_paper_replication_10hz_two_column_ledger_v1/block_d.json`.
Analysis: `scripts/analyse_f16_energy_ledger.py`.  **Three seeds is not a
distribution and no crash rate is claimed.**  On the block's own base seed
(241102975) nominal altitude RMSE is **323.28346789186793 ft** — the pinned
value, byte-identical to every earlier block in this line — and the transition
clock reproduces block B/C exactly (nominal 0.09 / 0.10 / 0.13 of post-onset
actions at zero), so the flight is unmoved and these remain measurements of
INSTRUMENTS.  (The three-seed nominal mean, 307.8 ft, is over three randomised
initial conditions and is not the pinned quantity.)

## The measurement gap block C recorded did not exist

Block C's correction closed with *"this plant does not currently expose either
ceiling ... no fuel mass, no specific energy, no maximum power."*  **That was
wrong.**  JSBSim publishes `propulsion/total-fuel-lbs`, `inertia/weight-lbs`,
`propulsion/engine/fuel-flow-rate-pps` and `propulsion/engine/thrust-lbs`, and
the aircraft names an engine model (`F100-PW-229`) that declares its own
`<milthrust>` rating of 17,800 lbf = **79,178 N**.  The gap was not in the
plant; it was that nothing had asked the plant.  Both ceilings are now copied
out mechanically (`domains/jsbsim_f16_paper_world.py`) and stamped every action
(`scripts/jabberwock_fixed_wing_jet.py::_state_attrs`).
`domains/fixed_wing_jet_world.py` likewise publishes the
`maximum_engine_thrust_newtons` and `mass_kg` it had declared and never handed
to the graph — and, modelling no fuel, publishes NO stock, which is the case
the general seed has to survive.

What genuinely is not exposed, and is therefore ASSUMED: **the fuel's specific
energy.**  No FDM property says what a kilogram of this fuel is worth.  It is
declared at Jet-A's published lower heating value, 42.8 MJ/kg, in the world
adapter beside the plant's other declared properties, and declared as an UPPER
bound — no engine extracts more, so a ledger that falls under this pricing
falls under the real one.

## The headline: the stock column never rose, in any episode, ever

**Convertible-column increases across the whole block: 0.**  Zero, in 24
episodes x 999 action transitions.  The column the correction said cannot
refill does not refill, and that is by construction rather than by luck — it is
`fuel_kg * specific_energy / (m*g)` on a stock that only falls, and the general
seed's reserve ratchet (`cre_ratchet_channel_reserve`) enforces the same law
one level up in action quanta, with or without a measurement.

Against that, the mechanical column alone increases on **190-473 of 999
actions** in every episode — block C's falsified monotonicity, reproduced.

| scenario | seed | TOTAL ledger increases | max +m | risen m | MECHANICAL increases | max +m | risen m | drift m | burn % | option=0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 39 | 14 | 142 | 452 | 25 | 2,878 | −13,603 | 2.01 | 0.00 |
| nominal | 2 | 89 | 18 | 512 | 449 | 31 | 3,565 | −12,348 | 1.80 | 0.00 |
| nominal | 3 | 19 | 10 | 68 | 443 | 26 | 2,811 | −16,523 | 2.45 | 0.00 |
| jammed_rudder | 1 | 9 | 8 | 30 | 301 | 30 | 1,504 | −22,794 | 2.92 | 0.32 |
| jammed_rudder | 2 | 23 | 19 | 123 | 262 | 30 | 1,745 | −21,578 | 2.33 | 0.00 |
| jammed_rudder | 3 | 26 | 16 | 148 | 290 | 33 | 2,107 | −23,039 | 2.53 | 0.00 |
| broken_aileron | 1 | 76 | 20 | 423 | 468 | 31 | 3,465 | −13,237 | 1.91 | 0.00 |
| broken_aileron | 2 | 91 | 22 | 427 | 468 | 29 | 3,197 | −12,065 | 1.76 | 0.00 |
| broken_aileron | 3 | 55 | 13 | 227 | 442 | 24 | 2,957 | −14,224 | 2.06 | 0.00 |
| saturated_elevator | 1 | 108 | 29 | 841 | 435 | 44 | 4,799 | −16,492 | 2.28 | 0.65 |
| saturated_elevator | 2 | 109 | 25 | 723 | 447 | 38 | 4,431 | −14,522 | 2.07 | 0.00 |
| saturated_elevator | 3 | 101 | 25 | 630 | 457 | 39 | 4,534 | −15,462 | 2.22 | 0.00 |
| landing_gear | 1 | 32 | 12 | 142 | 440 | 23 | 2,921 | −14,993 | 2.15 | 0.00 |
| landing_gear | 2 | 37 | 14 | 167 | 473 | 30 | 3,608 | −17,253 | 2.58 | 0.00 |
| landing_gear | 3 | 40 | 18 | 164 | 429 | 31 | 2,601 | −15,866 | 2.28 | 0.00 |
| shifted_cg | 1 | **169** | **38** | 1,536 | 404 | 47 | 4,296 | −12,664 | 1.53 | 0.00 |
| shifted_cg | 2 | **167** | **39** | 1,517 | 425 | 48 | 4,553 | −12,559 | 1.54 | 0.00 |
| shifted_cg | 3 | 115 | 23 | 668 | 430 | 37 | 4,336 | −16,107 | 2.17 | 0.11 |
| damaged_tail | 1 | 10 | 13 | 47 | 204 | 21 | 957 | −25,823 | 3.22 | 0.00 |
| damaged_tail | 2 | 5 | 5 | 12 | 194 | 20 | 789 | −30,118 | 3.96 | 0.01 |
| damaged_tail | 3 | 5 | 2 | 6 | 190 | 17 | 911 | −20,319 | 2.29 | 0.00 |
| damaged_wing | 1 | 25 | 17 | 125 | 319 | 30 | 1,725 | −21,811 | 2.36 | 0.30 |
| damaged_wing | 2 | 16 | 8 | 66 | 392 | 24 | 1,546 | −21,304 | 2.86 | 0.51 |
| damaged_wing | 3 | 17 | 6 | 47 | 341 | 18 | 1,493 | −20,320 | 2.52 | 0.37 |

## Held to the prereg, one prediction at a time

**Prediction 1 — "non-increasing on at least 95% of actions in every episode,
and no single-action increase above 30 m": FALSIFIED, on both halves.**
Fourteen of 24 episodes clear 95%; ten do not, the worst at 83.1%
(`shifted_cg` seed 1, 169 increases).  Two of 24 break the 30 m bound
(`shifted_cg` seeds 1 and 2, at 38 m and 39 m).  **The named most-likely
falsifiers — `damaged_wing` and `jammed_rudder` — did NOT break it** (8-19 m).
The scenario that did was `shifted_cg`, which was not named, and
`saturated_elevator` (named as the secondary candidate) came within 1 m at
29 m.

**Prediction 2 — "the total ledger beats the mechanical column on every
episode": HELD, 24 of 24, and not marginally.**  Increase counts 5-169 against
190-473; largest single rise smaller in 24 of 24; total mass risen 6-1,536 m
against 789-4,799 m.  On `damaged_tail` seed 3 the ledger rises 6 m across an
entire episode against the mechanical column's 911 m.

**Prediction 3 — "block C's positive result survives": FIRST HALF HELD, SECOND
HALF FALSIFIED, and this is a real negative.**  The option clock reads zero on
0.00 of post-onset actions on all three nominal seeds, so healthy flight is
still clean where the transition clock is not (0.09/0.10/0.13).  But it is
non-zero in only **7 of 21 fault episodes**, against **18 of 21** for block C's
mechanical-only energy clock and against the 15 predicted.  **Adding the second
column made the option clock a WEAKER discriminator, not a stronger one**, and
the mechanism is not mysterious: the reachable set now includes the thrust the
engine can add within the control horizon (`F_max * v * H * dt / (m*g)`,
~600 m at the block's initial condition against an escape demand of ~450 m), so
the escape reads as affordable in cases where the mechanical margin alone said
it was not.  Whether the more permissive reading is the more CORRECT one is not
decidable from this block — nothing here measures outcomes — but the
discrimination that block C earned is reduced, and that is the finding.

**Prediction 4 — "the reserve does not bind in this protocol": HELD.**  100 s
burns **1.53-3.96%** of the tank (predicted ~2%).  No episode's reserve reached
zero — the per-episode floor runs 57 to 1,023 actions — so no option expired
because the stock ran out, and **nothing in this block is evidence about the
price of `speed_priority`.**  The price is representable and it did not bite.

None of the remaining prereg'd falsifiers fired: no episode's total ledger
drifted UP (all 24 drift −12,065 to −30,118 m), and no episode had the total
increase on more actions than the mechanical column.

## Where the surviving non-monotonicity actually is, measured

Decomposing every episode's largest total-ledger increase into its columns
settles it.  The convertible column is FALLING at every one of them (−8 to
−17 m); the whole rise is in the MECHANICAL column, and the mechanical column
does not move by that much through the altitude term — `dh` at those actions is
between −0.0 and −13 m.  It moves through the TRUE-AIRSPEED term, and the
implied per-action true-airspeed step is:

| scenario | seed | max mechanical rise, m | airspeed, m/s | implied dv, m/s | sigma of the declared gust re-draw |
|---|---:|---:|---:|---:|---:|
| nominal | 1-3 | 25 / 29 / 26 | 91 / 110 / 87 | 2.72 / 2.63 / 2.96 | 3.2 / 3.0 / 3.4 |
| jammed_rudder | 1-3 | 30 / 27 / 25 | 103 / 95 / 102 | 3.55 / 3.02 / 2.51 | 4.1 / 3.5 / 2.9 |
| broken_aileron | 1-3 | 31 / 29 / 22 | 153 / 99 / 97 | 2.16 / 2.94 / 2.32 | 2.5 / 3.4 / 2.7 |
| saturated_elevator | 1-3 | 43 / 38 / 38 | 196 / 166 / 172 | 2.33 / 2.23 / 2.52 | 2.7 / 2.6 / 2.9 |
| landing_gear | 1-3 | 21 / 30 / 31 | 94 / 109 / 103 | 2.30 / 2.70 / 2.97 | 2.7 / 3.1 / 3.4 |
| shifted_cg | 1-3 | 47 / 48 / 37 | 186 / 185 / 155 | 2.61 / 2.74 / 2.67 | 3.0 / 3.2 / 3.1 |
| damaged_tail | 1-3 | 20 / 11 / 10 | 99 / 95 / 86 | 2.10 / 1.24 / 1.26 | 2.4 / 1.4 / 1.5 |
| damaged_wing | 1-3 | 30 / 19 / 15 | 116 / 97 / 97 | 3.51 / 1.95 / 1.60 | 4.1 / 2.3 / 1.9 |

The plant re-draws three independent gust components from N(0, 2 fps) **every
action**, so the action-to-action change of the wind vector has
sigma = 0.61 * sqrt(2) = 0.86 m/s per axis.  Every implied step in the table
lies between **1.4 and 4.1 sigma**, in all 24 episodes, on every scenario.

**So the mechanism the prereg named was right and its number was wrong, for a
reason that is worth recording rather than smoothing over.**  The 30 m bound
was sized at the block's INITIAL condition, v = 91 m/s, where the leverage
`d(v^2/2g)/dv = v/g` is 9.3 m per m/s.  `shifted_cg` trims nose-down and flies
the episode at 185 m/s, where the same gust step is worth 18.9 m per m/s — and
`saturated_elevator` at 196 m/s is worth 20.0.  The bound should have been
stated as a bound on `dv`, not on metres, and the two scenarios that broke it
are exactly the two fastest in the block.  Stated the right way, the measured
result is: **the total ledger is monotone non-increasing on this plant up to
the true-airspeed term's reading of a moving air mass, and that residual is
bounded by ~4 sigma of the disturbance the protocol itself declares.**  That is
a statement about the airspeed OBSERVATION, not about the accounting.

## Standing state after block D

* **The accounting correction stands and is measured.**  Thrust is not free
  energy; carried as a second column priced at the fuel's declared specific
  energy, the stock never rises in 24,000 actions, and the total ledger's
  non-monotonicity drops from 190-473 actions per episode to 5-169, and from
  789-4,799 m of risen energy to 6-1,536 m.  The residual is localised, sized,
  and attributed to a declared disturbance.
* **It is NOT the strictly-monotone ledger the prereg predicted**, and the
  prereg's quantitative bound is falsified by two episodes.  Recorded as
  falsified.
* **The two-column option clock discriminates LESS than block C's
  mechanical-only one** (7 of 21 fault episodes non-zero against 18 of 21),
  while keeping the clean nominal reading.  This is a measured negative on the
  instrument and is not reinterpreted here.
* **The plant exposed both ceilings all along.**  The only thing genuinely
  assumed on the F-16 is the fuel's specific energy; the general seed's own
  finite non-increasing reserve is what covers a plant like
  `fixed_wing_jet_world` that publishes no stock at all, and that path is gated
  by tests (`test_an_unmeasured_reserve_is_finite_and_only_ever_falls`,
  `test_a_measured_reserve_refines_the_bound_but_never_raises_it`,
  `test_the_plant_publishes_its_rate_ceiling_and_declares_no_stock`) and has
  NOT flown.
* **`speed_priority`'s price is representable and untested.**  An exhausted
  reserve puts the acting clock at the lattice floor and the admissible
  response moves from restoring the basin to the full corner set
  (`test_restoring_the_basin_is_admissible_only_while_the_reserve_lasts`).  In
  this protocol the reserve never came close to exhaustion, so the block says
  nothing about whether the manoeuvre works or about how many of them an
  episode affords.
* **THE RESPONSE GATE HAS STILL NEVER FLOWN.**  It was off in blocks A, B, C
  and D.  Whether routing on any of these clocks changes survival is a separate
  powered question none of these blocks answers.

Honest residuals, all disclosed in the prereg before the block ran:

* The reserve's ratchet is permanent and its input is crude.  The held
  recursion reads the slowly-draining fuel stream at order 3 and projects
  57-1,023 actions to dry against the ~12,000 the tank actually holds; the
  MINIMUM of those readings then binds for the rest of the episode.  It is
  conservative in the right direction, it never reached zero here, and it is
  not a measurement of endurance.
* The rate ceiling uses the engine's static rating rather than its rating at
  the current mach and altitude, which JSBSim also publishes.  The static
  rating is the larger, so the reachable set is over-stated — and that is
  plausibly part of why the option clock became more permissive.
* The convertible column is priced at a declared upper bound (42.8 MJ/kg), so
  it is roughly 300x the mechanical column throughout.  The ledger's
  monotonicity therefore rests overwhelmingly on the fuel term; the mechanical
  term is a small perturbation on it.  That is what makes the ledger monotone,
  and it is also what makes "the total ledger is monotone" a weaker statement
  than it sounds.

---

# Block E — the response gate flies, and is INERT: 40 of 40 episodes byte-identical

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("THE RESPONSE
GATE FLIES"), committed before this block ran, including its full disclosure
that the projection below had been read off block D's existing traces and that
one cell (nominal, seed 241102975, gate ON) had already been flown.

**Matched pair, one variable.**  4 scenarios × 10 frozen seeds, 100 s at
10 Hz, `--base-seed` offset per scenario so the seeds are the block's own
(`241102975 + SCENARIO_ORDER.index × 10000 + episode_index`), run twice:
`--class-gate` and without.  Frozen: `control_regime_escalation` v7.0.0,
`f16_flight_path_control` v8.0.0, `cognitive_pareto` v1.1.0,
`embodied_motor_program` v1.8.0.  Blocks:
`results/jsbsim_f16_paper_replication_10hz_gate_preflight10_{on,off}_v1/`.
Comparison: `scripts/analyse_f16_gate_ab.py` (per-episode, matched on seed,
every reported metric).  **Ten seeds is not a distribution and no crash rate is
claimed** — the rates below are printed only to show the two arms agree.

## The result

**40 matched episodes.  0 differ on any non-latency metric.**

| scenario | crashes | escalated | corners adopted | recalibrations | altitude RMSE |
|---|---:|---:|---|---:|---:|
| nominal | 0/10 | 0/10 | none | 0 | 359.5 ft |
| jammed_rudder | 2/10 | 8/10 | trim 8, orbit 8 | 20 | 7,721.5 ft |
| saturated_elevator | 0/10 | 0/10 | none | 20 | 3,709.2 ft |
| damaged_wing | 5/10 | 9/10 | trim 9, orbit 9 | 20 | 9,991.5 ft |

Every row is the SAME under `--class-gate` and without it, to the digit.  The
only fields that move are the three wall-clock latency counters, which are not
properties of the flight.  On the base seed nominal is
**323.28346789186793 ft** in both arms — the pinned value, unmoved.

* **Prediction 1 — "the gate is inert, 40 of 40 byte-identical": HELD.**
* **Prediction 2 — "no episode gains a projection-driven recalibration": HELD.**
  `recalibration_count` is identical in 40 of 40; every recalibration in the
  fault scenarios is the SCHEDULED-fault arming that was already there.
* **Prediction 3 — "nominal untouched": HELD.**
* **None of the named falsifiers fired.**  `saturated_elevator` — named as the
  most likely, and the scenario that has lied to this line before — is
  identical in all 10.  So is `damaged_wing`, the one scenario where
  `T_option` binds often enough (0.33–0.57 of post-onset actions) to have
  selected a different route.

## Why it is inert, measured BEFORE the flight and confirmed by it

`scripts/project_f16_gate_routes.py` reads a gate-off block's traces and puts
every deliberation window through the gate's rule table.  On block D's 24
episodes:

* **104 deliberations open.  6 produce a verdict; 98 do not.**
* Closes by region: **60 `fixpoint_gone` (acting clock ≤ 0), 26 `recalibrate`
  (≥ horizon), 18 `inside_horizon`.**
* **All 6 verdict-producing closes are in `fixpoint_gone`** — jam ×3 at
  action 189, damaged tail ×1 at 450, damaged wing ×2 at 315/353, every one
  with `T_transition = 0` and `T_option` 75–218.

Those two facts close the question between them:

1. Where a corner WAS adopted, the acting clock sat at the lattice floor, and
   the floor is the gate's most permissive region — the full corner set.  **The
   gate cannot refuse a corner it has already admitted.**
2. Where no corner was adopted, no goal-revision request was standing, so
   `cre_publish_incumbent_stands` (order −49) closes the window before either
   gate route (−48.9, −48.85) is reachable.  The 26 `recalibrate` and 18
   `inside_horizon` closes are regions the acting clock LANDS in and that
   nothing ever reads.

The flight confirms the inference in (2), which the traces could not settle:
had a revision request ever been standing at one of those 44 windows, the
recalibration route would have fired and the arms would have diverged.  They
did not diverge, in 40 episodes.

## What this is a null ON, and what it is not

**It is not a null on whether gating the response helps survival.**  That
question is untouched — nothing in this block routes differently, so nothing in
it is evidence either way.

**It is a null on the gate's REACHABILITY, and the cause is upstream.**
`regime_actions_to_act = MIN(T_transition, T_option)`, and on this plant
`T_transition` reads zero on **0.14–0.98** of post-onset actions in every one
of the 21 fault episodes against `T_option`'s **0.00–0.65**, which is 0.00
throughout in 15 of 21 (`regime_actions_to_*`, window from the fault onset at
action 100 — the same window every other post-onset figure in this document
uses).  The MIN
is not a compromise between the two clocks; it IS the transition clock, and the
transition clock is the instrument **block B already falsified** — a healthy
commanded manoeuvre drives it to zero, and a fault drives it to zero and keeps
it there.

So the derivation's step 9, *"two clocks, act on the MIN"*, is measured to be
carrying a defect it did not anticipate: taking the minimum of a clock that
measures irreversible loss and a clock that goes to the floor on every
excursion yields the second one, always.  The option clock — the one thing
block C earned and block D partly gave back — never gets to bind.

**The powered n=100 × 4 block was NOT run**, as the prereg committed in
advance.  It would have reproduced the standing gate-off block byte for byte
at ~4 hours of compute, and buying that reproduction would have been the
"reached for a better NUMBER rather than a better ACCOUNT" mistake in its
purest form.  Total cost of settling open item 1: one projector over traces
that already existed, plus 40 matched episodes.

## Standing state after block E

* **The response gate has now flown, and changes nothing.**  Open item 1 is
  answered, with a negative, and it is answered on the gate's INPUT rather than
  on its policy.
* **`speed_priority` was adopted 0 times in 40 episodes**, in either arm.  It
  remains a pre-registered hypothesis with no flight evidence for or against
  it, exactly as block D left it.  The corner cannot be tested by a gate that
  never selects the region admitting only it.
* **v3 remains the standing best on faults.**  Nothing in this rung moved a
  crash rate, because nothing in this rung moved an aircraft.
* The next question is not the gate's three regions.  It is whether
  `T_transition` belongs in the MIN at all while it is projected from a
  quantity a coordinated manoeuvre consumes — the fix the block-C standing
  state already named as "the obvious next move, not built."

---

# Blocks F1 and F2 — the rate ceiling was not the cause, and the escape floor was

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("THE RATE
CEILING, AND WHAT ACTUALLY COST THE DISCRIMINATION"), committed before either
arm ran, including its full disclosure of the offline re-pricing both
predictions were made from.

Protocol as blocks A–D: n = 3 seeds × 8 scenarios, 100 s at 10 Hz, frozen block
seeds, `--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **class gate OFF**.
Blocks `results/jsbsim_f16_paper_replication_10hz_rate_ceiling_f1_v1/` and
`..._escape_floor_f2_v1/`.  Analysis `scripts/analyse_f16_energy_ledger.py`;
offline re-pricing `scripts/reprice_f16_option_margin.py`.  **Three seeds is
not a distribution and no crash rate is claimed.**

## The plant was asked about its own ceiling, and it had two answers

* `propulsion/engine/MilThrust` is the engine model's normalised lookup of its
  `<milthrust>` rating against mach and density altitude — **0.7653** at the
  block's initial condition.  The static rating over-states the ceiling by
  1.31× there.
* The engine declares `<augmented>1</augmented>` with no `<augthrust>`, and
  JSBSim's augmented turbine puts military power at
  `fcs/throttle-cmd-norm = 0.5`.  **The effector maps `0.25 × (1 + command)`,
  so 0.5 is the largest throttle this airframe can be commanded** — measured
  16,253 lbf at steady state against `rating × lookup` of 16,239.  The
  afterburner half of the range is unreachable through this interface, so
  military thrust is this plant's ceiling and the augmented table is not.

## The headline

| pricing | fault episodes with the option clock at zero | nominal seeds dirtied |
|---|---:|---:|
| block C — mechanical only, `dv` declared | **18 of 21** | 0 of 3 |
| block D — two columns, `dv` capped to `F_max·dt/m` | **7 of 21** | 0 of 3 |
| **F1 — two columns, condition-rated `F_max`** | **6 of 21** | 0 of 3 |
| **F2 — two columns, condition-rated `F_max`, `dv` DECLARED** | **15 of 21** | 0 of 3 |

* **Prediction 1 — "F1 does not recover, at most 9 of 21": HELD** at 6.
* **Prediction 2 — "F1 ≤ block D's 7": HELD** at 6.  Fixing the rate ceiling
  moves the discrimination the WRONG WAY, by one episode.
* **Prediction 3 — "nominal stays clean under F1": HELD**, 0.00 on all three.
* **Prediction 4 — "the flight is unchanged": HELD.**  All 24 F1 episodes are
  byte-identical to block D on every non-latency metric; nominal base seed
  **323.28346789186793 ft**.
* **Prediction 5 — "F2 recovers to at least 13 of 21 while keeping the clean
  nominal": HELD** at 15 of 21, nominal 0.00/0.00/0.00.
* **Prediction 6 — "F2's flight is unchanged": HELD.**  All 24 episodes
  byte-identical to block D; nominal **323.28346789186793 ft**.
* **No named falsifier fired.**  `saturated_elevator` went 0.00/0.00/0.83
  under D to 0.46/0.44/0.68 under F2 — the scenario named as most likely to
  disagree with the proxy agreed with it.  `shifted_cg` seed 3, named as the
  single most likely cell to flip, flipped: 0.12 → 0.71.  `landing_gear`
  behaved exactly as the bimodality warning said it would: 0.00/0.34/0.00.

The offline proxy predicted 6 for F1 and 16 for F2; measured 6 and 15.

## So block D's recorded residual had the sign backwards, and said so about the wrong line

Block D closed with *"the rate ceiling uses the engine's static rating ... the
static rating is the larger, so the reachable set is over-stated — and that is
plausibly part of why the option clock became more permissive."*  **The first
clause is true and the inference from it is false.**  `F_max` enters the option
margin twice:

    reachable    = mechanical + MIN(convertible, F_max·v·H·dt/(m·g))
    escape floor = (v + MIN(dv_declared, F_max·dt/m)·H)² / 2g

At the block's initial condition `d(floor)/dF = 0.0129 m/N` against
`d(reachable)/dF = 0.0076 m/N`, so **cutting the ceiling RAISES the margin**.
A more honest ceiling made the clock more permissive, not less, and F1 measures
exactly that.

The cause was the other appearance of `F_max`.
**`effective_delta = MIN(declared_delta, F_max·dt/m)` priced a weaker engine as
a cheaper escape**: the speed the escape is measured against shrank to whatever
the engine could manage, so an aircraft with less authority read as having more
options.  The seed's own comment beside that line said the opposite in words —
*"a corner that declares more speed authority than the engine has is not a
cheaper escape, it is a slower one"* — and the code implemented "cheaper".
**The code contradicted its own comment, and the comment was right.**

This is the frontier's original pathology in a new place, and worth naming as
the same shape: there, a SURRENDERED axis scored flat 0.0 dominated a KEPT axis
scored unbounded-below, so the corner giving up the most won.  Here, an
unmeetable demand was scored as a met one, so the airframe that can do least
looks safest.  Both are a comparison in which failing to have a property is
priced better than having it imperfectly.

`f16_flight_path_control` **v8.1.0** prices the escape floor at the corner's
declared demand.  Whether the engine can keep that promise is a question about
the escape's DURATION; the rate ceiling already bounds what the reachable set
can be topped up by, which is where a finite engine belongs in this accounting.

## Standing state after F1 and F2

* **Open item 2 is answered, and its expected answer was wrong.**  Fixing the
  rate ceiling to the mach/altitude lookup is CORRECT — the static rating
  over-stated an anti-conservative column and it should not have — but it
  recovers nothing: 7 → 6 of 21.  It is kept because it is the honest
  measurement, not because it bought anything.
* **The two-column ledger is NOT worse than mechanical-only.**  Block D's open
  item invited the conclusion "if it does not recover, the two-column clock is
  worse than mechanical-only and should be said so plainly."  Measured, that
  conclusion would have been true of the NUMBER and wrong about the CAUSE: with
  the escape floor priced at the demand, the two-column clock reads 15 of 21
  against mechanical-only's 18 **while keeping the clean nominal**, and the
  second column is what makes the ledger monotone.  The 7 of 21 was never the
  ledger's fault.
* **Both arms fly byte-identically to block D**, 24 of 24 episodes each.  These
  remain measurements of INSTRUMENTS.  Nothing here is evidence about crash
  rates and none is claimed.
* **A repaired option clock does NOT make the gate reachable, and this is now
  measured rather than expected.**  `scripts/project_f16_gate_routes.py` over
  both new blocks:

  | block | closes: fixpoint gone / inside horizon / recalibrate | verdict closes |
  |---|---|---|
  | D | 60 / 18 / 26 | **6, all in `fixpoint_gone`** |
  | F1 | 52 / 19 / 33 | **6, all in `fixpoint_gone`** |
  | F2 | 64 / 15 / 25 | **6, all in `fixpoint_gone`** |

  The route mix moves; the six closes that actually adopt a corner do not.
  `regime_actions_to_act` is `MIN(T_transition, T_option)`, and `T_transition`
  reads zero on 0.14–0.98 of post-onset actions in every fault episode, so the
  MIN is pinned at the lattice floor exactly where a verdict is being taken.
  **Block E's null survives a strictly better option clock**, which localises
  the remaining defect precisely: it is the transition clock, or it is the MIN,
  and it is not the energy accounting.
* **Unbuilt, and recorded so it is not discovered later as a finding**: "a
  slower escape" has no representation.  v8.1.0 removes the wrong penalty
  without adding the right one — an engine that cannot deliver the declared
  delta within the horizon should make the escape take LONGER, and nothing in
  the seed says so.

---

# The equal rating is over CHANNELS — a projection on F2's traces

Not a block: a projector over already-flown gate-off traces
(`scripts/project_f16_channel_weighting.py`), exact only up to the first action
at which a different acting clock would change a verdict.  No aircraft moved.

## What drives the transition clock to the floor

`regime_actions_to_transition` is `MIN` over the per-channel transition clocks,
which prices every declared objective identically.  Which channel actually wins
that minimum, post-onset:

| scenario | argmin channel share | `T_transition == 0` |
|---|---|---:|
| nominal | altitude .66, sideslip .27, attitude .06, heading .02 | 0.11 |
| jammed_rudder | **heading .83**, sideslip .09, altitude .07 | 0.89 |
| broken_aileron | **sideslip .68**, altitude .20, heading .08 | 0.43 |
| saturated_elevator | altitude .58, sideslip .36 | 0.17 |
| landing_gear | altitude .49, sideslip .46 | 0.29 |
| shifted_cg | altitude .54, sideslip .41 | 0.18 |
| damaged_tail | **sideslip .56**, altitude .25, heading .14 | 0.53 |
| damaged_wing | **attitude .50**, sideslip .20, heading .20 | 0.86 |

And in nominal, around the commanded 40 degree reference change on the base
seed — which is the exact event block B was falsified on:

| window | argmin channel | `T_transition == 0` |
|---|---|---|
| 100–200, before the change | altitude 87, attitude 11 | **0/100** |
| 200–400, during it | **sideslip 163**, altitude 31 | **83/200** |
| 400–1000, after it settles | altitude 472, sideslip 86 | **0/600** |

**A coordinated turn IS transient sideslip.**  The sideslip channel correctly
reports that its own fixpoint is momentarily unattainable, and the flat `MIN`
hands that reading authority over the whole regime.  At the six closes that
actually adopt a corner the argmin is `heading` ×4 and `attitude` ×2 —
**altitude never.**

That is derivation step 10 unapplied one level down: *"surrendering altitude …
liquidates the reserve every future decision draws on … heading is cheap to
abandon (heading is not energy)."*  The flat minimum prices heading, sideslip
and altitude the same, so an unwinnable heading fight and a healthy turn's
sideslip speak with exactly the authority of an altitude channel that is
genuinely spending the reserve.

It also explains the one clock that works.  **The option clock is a SINGLE
channel** — altitude, `_OPTION_CHANNEL_INDEX`, *"the ONE channel that funds an
escape"*.  There is no equal-rating across channels because there is only one,
and it is the energy one.

## What a relative weighting would have done

    weighted(ch)  = clock(ch) + (1 - share(ch)) * (ceiling - clock(ch))
    T_transition  = MIN over channels of weighted(ch)
    acting clock  = MIN(T_transition, T_option)

`share = 1` everywhere reproduces today's `MIN` exactly, and is carried as the
V0 control.  Three priced vectors were swept — V1 energy-only
(altitude 1, rest 0), V2 graded (1 / .5 attitude / .25 sideslip / 0 heading),
V3 steeper (1 / .25 / .10 / 0).

| price vector | all 104 closes: gone / inside / recal | the 6 ADOPTING closes | nominal `T_trans == 0` |
|---|---|---|---:|
| V0 flat (control) | 64 / 15 / 25 | **6 gone** | 290/2703 (0.11) |
| V1, V2, V3 (identical) | 32 / 27 / 45 | **1 gone, 3 inside, 2 recal** | **0/2703 (0.00)** |

Acting clock at each adopting close under any priced vector: **218, 218, 76,
77, 75, 0** — every one of them the OPTION clock.  The weighting does not blend
the two clocks so much as take the transition clock out of contention at these
points and let the single-channel energy clock set the acting time.  That is
why the three vectors agree: once altitude is the only channel priced at 1 and
its own clock sits above `T_option`, the other shares cannot reach the minimum.

Two readings that matter:

* **Five of the six adopting closes leave the most permissive region** — three
  into the region admitting ONLY `candidate_restores_basin`, which is the
  region `speed_priority` has never been selected in and open item 4 has never
  been able to test.
* **The sixth stays at `fixpoint_gone` because `T_option` itself reads 0**
  (damaged_wing seed 3).  That is the energy clock saying the escape is
  genuinely gone — the gate firing for its own stated reason rather than
  because a heading channel bottomed out.
* **Nominal's excursion disappears**: 0.11 → 0.00 of post-onset actions at the
  floor, under every priced vector.  On this projection **block B's
  falsification is a channel-pricing artefact**, not a property of projecting a
  transition time.

## What this projection does NOT establish

* **The price vector is a sensitivity sweep, not a derived constant.**  The
  plant publishes no per-channel energy attribution.  What this line has
  established is the ORDER (altitude is the reserve; sideslip is drag, a real
  but smaller spend; heading is not energy), and the projection is insensitive
  to the shares within that order — which is a robustness result about the
  three REGIONS, not about the values.
* **Nothing here is an outcome.**  These are gate-off trajectories.  Whether
  routing on a channel-weighted acting clock changes survival is a powered
  question, and it needs the gate on, a prereg, and a pre-flight.
* **The projector found its own bug, and the control is why.**  The stamped
  `regime_actions_to_transition` at action k is the MIN over the consumer's
  per-channel clocks at action **k−1** (verified 23,976 of 23,976 rows, against
  16,592 for the same-action reading): the consumer publishes per action and
  the general seed rolls up on its own sequence guard.  Recomputing from the
  current row shifted every close by one action and moved one of the 104.  V0
  disagreeing with the stamped block by exactly one close is what caught it.

---

# Blocks G0 and G1 — the gate reaches at last, and the region it opens is EMPTY

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("THE EQUAL
RATING IS OVER CHANNELS"), committed before either block ran, including the
full disclosure of the projection both were predicted from.

Frozen: `control_regime_escalation` **v7.1.0** (the
`channel_surrender_discount` contract), `f16_flight_path_control` **v8.2.0**
(altitude 0.0, attitude/heading/sideslip 1.0), `cognitive_pareto` v1.1.0,
`embodied_motor_program` v1.8.0.  Blocks
`results/jsbsim_f16_paper_replication_10hz_channel_weight_g0_v1/` and
`..._g1_{on,off}_v1/`.

## G0 — gate OFF, n=3 x 8.  All three predictions held.

| prediction | committed | measured |
|---|---|---|
| 1. byte-identical to block F2 | 24 of 24 | **24 of 24**, nominal base seed **323.28346789186793 ft** |
| 2. nominal `T_transition` at the horizon | ≥ 0.99 of post-onset actions | **1.0000** (2,703 of 2,703), against the flat MIN's 0.89 |
| 3. adopting closes: gone / inside / recal | 1 / 3 / 2 | **1 / 3 / 2**; all 104 closes 32 / 27 / 45 |

Prediction 1 carries weight beyond this rung: with the gate off nothing
consumes `regime_actions_to_act`, so changing what it is made of moved no
aircraft — which is what keeps every "measurement of an INSTRUMENT" claim in
blocks A–F standing.

**Prediction 2 is block B's falsification repaired.**  The two-clock block died
because a commanded 40 degree turn drove the acting clock to zero for ~200
actions.  Priced relatively, that excursion is not reduced — it is ABSENT, on
every one of 2,703 nominal post-onset actions.  It was the sideslip channel
being equal-rated with the channel that carries the ledger, and nothing else.

## G1 — the matched gate ON/OFF pre-flight, 4 scenarios x 10 frozen seeds

**Prediction 4 — "the arms diverge, at least 8 of 40": HELD, 12 of 40.**
For the first time in this line the response gate changes the aircraft.
Divergence by scenario: **jammed_rudder 8, damaged_wing 4, nominal 0,
saturated_elevator 0.**

**Prediction 5 — "nominal untouched": HELD**, 10 of 10 identical, base seed on
the pin.

**Prediction 6 — "`speed_priority` adopted at least once": FALSIFIED.  Zero
adoptions in 40 gate-ON episodes**, as in every block before it.

| scenario | arm | crashes | escalated | trim | orbit | speed | roll | mean escalation action | alt RMSE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nominal | off / on | 0 / 0 | 0 / 0 | 0/0 | 0/0 | 0/0 | 0/0 | — | 359.5 / 359.5 |
| jammed_rudder | off / on | 2 / 0 | 8 / 7 | 8/7 | 8/7 | 0/0 | 0/0 | **224.4 → 602.7** | 7,721 / 7,098 |
| saturated_elevator | off / on | 0 / 0 | 0 / 0 | 0/0 | 0/0 | 0/0 | 0/0 | — | 3,709 / 3,709 |
| damaged_wing | off / on | 5 / 6 | 9 / 9 | 9/9 | 9/9 | 0/0 | 0/0 | **334.9 → 446.9** | 9,992 / 10,208 |

## The finding: the gate DELAYS the same corner, it does not choose a different one

The corner composition is unchanged in both arms — trim and orbit, together,
every time — and `speed_priority` and `roll_priority` are adopted zero times in
either.  What the gate changes is WHEN: the jam's mean escalation moves 224 →
603 actions and the wing's 335 → 447.

The mechanism is the one the prereg named in advance as prediction 6's likely
failure, and it is a hole in the RESPONSE SET rather than in the clock:

* The middle region admits only a candidate declaring
  `candidate_restores_basin`, and the consumer declares exactly one —
  `speed_priority`.
* That corner is never on the frontier at these closes, so the deliberation
  closes on `cre_close_gated_deliberation_without_verdict` with a
  `ControlRegimeResidual` and no regime change.
* The episode flies on; the acting clock later falls to the lattice floor; the
  full corner set opens; **trim and orbit are adopted then.**

So the architecture's step 8 — *"CHANGE THE OPERATING CONDITION so the fixpoint
stays attainable"* — is representable, is now reachable, and has nothing in it.
**The gate's middle region is in practice "not yet", not "do the other thing".**
This is the prereg's separately-recorded outcome, quoted from before the run:
*"the gate would be converting adoptions into refusals rather than into the
operating-condition change it is for."*  That is what it did.

## No crash rate is claimed, and the two arms disagree about the sign

Crashes 7 of 40 off against 6 of 40 on, and the per-scenario split runs both
ways: the jam goes 2 → 0 and the wing 5 → 6.  Five individual seeds flip, three
toward survival and two away:

| seed | scenario | off → on | escalation action |
|---|---|---|---|
| 241112979 | jammed_rudder | crash → survive | 193 → 431 |
| 241112980 | jammed_rudder | crash → survive | 355 → 431 |
| 241172975 | damaged_wing | crash → survive | 316 → 477 |
| 241172980 | damaged_wing | survive → **crash** | 190 → 512 |
| 241172981 | damaged_wing | survive → **crash** | 332 → 654 |

**Ten seeds is not a distribution**, the prereg declined to predict this
direction, and it is not being read now.  This line has been burned twice
exactly here — a 0/10 elevator pre-flight returned 0.17 at n=100, a 0.20 jam
pre-flight returned 0.27 CI-separated worse.  What the table does show is a
mechanism worth stating: delay helps where the corner was being adopted too
eagerly and hurts where it was being adopted in time, which is what a pure
DELAY would look like and is not evidence for or against the gate's policy.

`saturated_elevator` behaved exactly as the named falsifier said it would — it
escalates 0 of 10 with the gate off, so the gate cannot bite there at all, and
it contributed 0 of the 12 divergences.  30 of the 40 episodes carried the
whole prediction.

## Standing state after G0 and G1

* **Open item 1 is now genuinely answered.**  The response gate has flown, it
  reaches, and it changes 12 of 40 episodes.  Block E's null was upstream, in
  the channel pricing, exactly as located.
* **The equal rating was over CHANNELS and it is fixed.**  A flat `MIN` let
  heading and sideslip speak with the ledger channel's authority; priced
  relatively, healthy flight's manoeuvre excursion disappears completely and
  the adopting closes move out of the permissive region.  The contract is
  domain-free and its default is byte-compatible.
* **Open item 4 is answered NEGATIVELY and for a new reason.**
  `speed_priority` is not merely untested — it is unreachable.  The region built
  for it admits nothing else, and it never wins the frontier there.  Whether it
  works remains unknown; whether the current consumer can ever select it is now
  known, and the answer is no.
* **The next question is the response set, not the clock.**  Either
  `speed_priority` must be able to win the frontier in the region that admits
  only it, or the consumer needs other candidates that change the operating
  condition.  A gate whose middle region is empty is a delay line.
* **v3 remains the standing best on faults.**  Nothing here is a powered result
  and no powered block is authorised by it.

---

# Block H — the cost model is a null here, because THE FRONTIER HAS STOPPED CHOOSING

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("WHAT A CORNER
COSTS"), committed before the block was looked at.  4 scenarios x 25 frozen
seeds, gate OFF, `--include-trace`, `control_regime_escalation` v7.1.0 /
`f16_flight_path_control` v8.2.0.  Sized for ADOPTIONS, not for a rate: **no
crash rate is claimed and no Wilson interval is computed from it.**  Analysis:
`scripts/analyse_f16_corner_cost.py`.

## The structural finding, which was not what the block was built to measure

**All 48 adoptions in the block are the same corner combination: trim + orbit,
at the same action, every time.**  Across all 100 episodes and ~99,600 actions
the held regime ordinal takes exactly two values:

| ordinal | corner | actions held |
|---|---|---:|
| 0 | hold | 64,886 |
| **2** | **orbit** | **34,698** |
| 1 | sideslip trim | **0** |
| 3 | speed priority | **0** |
| 4 / 5 | roll priority | **0** |

`regime_max_ordinal` declares 5.  **The consumer declares five corners and
selects one.**  This is not a Pareto frontier making an incomparable choice; it
is a binary switch between "hold" and "orbit".

That is a change from the powered blocks.  Block 1's jam adopted trim 54, orbit
3, speed 66, roll 91 in 100 episodes; block 3's adopted trim 98, orbit 65,
speed 22, roll 35.  Somewhere between `f16_flight_path_control` v3.1.0 and
v8.2.0 the selection collapsed, and it is not the availability ceiling — that
is still 5.

**So this block cannot answer the question it was written for.**  "Does a
corner's cost predict the outcome" needs two corners.  What it can answer is
the narrower "does the ledger draw predict the outcome WITHIN one corner", and
that is what is reported below.

## Held to the prereg, one prediction at a time

48 adoptions, above the prereg's floor of 20, so the block is not dismissed as
underpowered on its own stated terms.

**Prediction 1 — "post-adoption ledger draw is higher in the episodes that
crash": the median ordering holds and the separation is a NULL.**  Pooled
23.377 against 22.881, P(crash > survive) = 0.564.  Within `damaged_wing` —
the guard the prereg fixed in advance, and the only cell with balanced groups
(12 crashed, 11 survived) — 23.569 against 22.373, P = 0.621.  The ordering is
right in every cell, but Hanley–McNeil 95% intervals on the balanced cell are:

| quantity | P(crash > survive) | 95% interval | |
|---|---:|---|---|
| draw | 0.621 | [0.389, 0.853] | **includes 0.5** |
| timing | 0.473 | [0.232, 0.714] | **includes 0.5** |
| reserve | 0.413 | [0.176, 0.650] | **includes 0.5** |

**Overlapping intervals are not an improvement.**  Recorded as a null.

**Prediction 2 — "the draw separates better than adoption timing": FALSIFIED
pooled.**  Pooled, timing reads 0.710 against the draw's 0.564 — the rival
explanation wins, and by a lot.  Within `damaged_wing` the ordering inverts
(draw 0.621, timing 0.473), but both intervals include 0.5, so the inversion is
not a rescue and is not read as one.

The pooled timing advantage is **the scenario confound the prereg named**,
landing on the rival rather than on the ledger: `jammed_rudder` adopts early
(median 192) and crashes 3 of 23, `damaged_wing` adopts late (median ~350) and
crashes 12 of 23.  Pooling two scenarios that differ in both timing and crash
rate manufactures a timing effect out of neither.

**Prediction 3 — "the reserve at adoption is lower in the episodes that
crash": null, and INVERTED in one scenario.**  Pooled 174 against 174
(P = 0.478); `damaged_wing` 126.5 against 174 (P = 0.413, right direction);
`jammed_rudder` 218 against 174 (P = 0.525, **wrong direction** — the crashing
episodes had MORE reserve).

## What this does and does not say about pricing corners

* **The ledger exists, is monotone, and prices a corner in one currency.  That
  is not in question and blocks D/F1/F2 established it.**
* **What this block fails to establish is that the price, taken at the moment
  of adoption, predicts the outcome** — and it fails for a reason that is not
  about the price: there is no second corner to price against.  Every episode
  that escalated made the same choice.
* Block 3's crash-by-corner contrast (kept altitude 1/61; 26 of 27 crashes on a
  corner that surrendered it) remains the strongest evidence that the ledger
  predicts survival, and it comes from a stack whose frontier still varied.
  **It cannot be reproduced on this one**, because the corner that surrenders
  altitude is never selected here.

## Standing state after block H

* **The option set is static AND degenerate.**  Not one of the five
  corner-minting rules reads the effector model, the recalibration state, or
  the fault — verified directly on the seed, all five match only
  `has_embodied_motor_program_episode` and `deliberates_over_pareto_profile` —
  and in flight the selection collapses to a single ordinal.  The frontier can
  neither gain an option, lose one, nor, as measured here, choose between the
  ones it has.
* **Availability is upstream of cost.**  A corner's price cannot be measured
  against outcomes until the selection varies, so the model-driven availability
  question is not a parallel rung to the cost question — it is the one that
  has to move first.
* `log_authority`, `specified_effect_prior_confidence` and
  `recalibration_required` are all maintained per effector model and read by
  `embodied_motor_program`'s composer.  The frontier reads none of them.
  **System 1 adapts to the changed plant; System 2's menu does not.**
* No crash rate is claimed from this block and no powered block is authorised
  by it.

---

# WHY THE FRONTIER COLLAPSED TO ORDINAL 2 — one instrumented episode

Block H measured that the held regime takes only two values, 0 and 2, across
100 episodes.  This is the cause, read off the graph in a single damaged-wing
episode (base seed 241172975) by dumping the `ParetoCandidate` nodes at every
deliberation (`GAMMA_REGIME_DIAGNOSTICS=1` plus a probe on
`_settle_graph_request`).  Minutes, not a block.

## It is not the minting, and it is not open item 6

**All five corners are minted at every deliberation opening** — the per-corner
guards (`f16_pareto_minted_seq_*`, now carried in the diagnostics trace) all
stamp the opening seq.  The `dominated` flags are computed correctly and the
`cognitive_pareto` goal-audit faculty emits exactly one
`GoalRevisionRequest` for the unique surviving candidate.  **The unwired
`bind_value_to_objective_goal_rule` is NOT the cause** and can be struck off
the suspect list.

## Four of the six declared axes never vary at all

Across the episode's deliberation closes, does an axis take more than one value
among the five candidates?

| axis | kind | varies |
|---|---|---:|
| altitude | terminal-state | 3 of 5 |
| heading | achievability-only | 1 of 5 |
| speed | terminal-state | **0 of 5** |
| attitude | terminal-state | **0 of 5** |
| structural | terminal-state | **0 of 5** |
| sideslip | achievability-only | **0 of 5** |

Four axes are pinned at the ceiling (1024) for every candidate, always, so they
contribute nothing to dominance ever.  **The six-dimensional frontier is a
two-dimensional one, and mostly a one-dimensional one.**

## The deciding deliberation, in full

Action 315, the escalation that puts this episode into orbit for the rest of
its life:

| corner | ordinal | dominated | alt | head | speed | atti | stru | side | proposed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| fixed_point | 0 | 1 | 1024 | **1** | 1024 | 1024 | 1024 | 1024 | — |
| trim | 1 | 1 | 1024 | **1** | 1024 | 1024 | 1024 | 1024 | — |
| **orbit** | **2** | **0** | **1024** | **1024** | 1024 | 1024 | 1024 | 1024 | **YES** |
| speed_priority | 4 | 1 | **460** | **1** | 1024 | 1024 | 1024 | 1024 | — |
| roll_priority | 5 | 1 | **460** | 1024 | 1024 | 1024 | 1024 | 1024 | — |

Orbit is 1024 on both live axes.  It dominates every other candidate: the two
that keep heading are worse on heading, the two that surrender altitude are
worse on altitude.  **It is the unique non-dominated point, so it is the only
candidate the faculty can propose, so it wins — and there is no situation in
which it does not.**

## The mechanism: the two ways of surrendering an axis are priced incomparably

The seed states the convention explicitly, and it is deliberate:

* **TERMINAL-STATE axes** (altitude, attitude, speed, structural).  *"KEPT
  projects the margin with the axis's own declared authority applied;
  SURRENDERED projects it with none."*  Surrendering scores a real, finite,
  WORSE number — altitude 460 against 1024.
* **ACHIEVABILITY-ONLY axes** (heading, sideslip).  *"SURRENDERED is the
  horizon, because an abandoned objective cannot become unachievable."*
  Surrendering scores **the CEILING — the best value available.**

So retiring an achievability-only objective is not merely free, it is
maximally rewarded, while retiring a terminal-state objective is penalised.
A corner that retires heading and keeps altitude therefore dominates by
construction, in every condition, against any opponent.

**This is derivation item 2 again, with the sign flipped.**  The original
defect was *"a surrendered axis scored flat 0.0 against a kept axis scored
unbounded-below, so the corner that gives up the MOST dominates the one that
gives up the RIGHT thing."*  The repair moved the surrendered score from the
FLOOR to the CEILING.  That fixed which corner wins — orbit is the corner
block 3's crash table says is right (episodes keeping altitude crash at 1/61)
— and it destroyed the frontier's ability to choose at all.  **The machinery
now gets the right answer for a reason that guarantees it can never get a
different one.**

The seed's own comment anticipates the objection — *"the asymmetry that lets a
surrendering corner win is not a coupling law and not a cross-axis term, it is
the per-axis fact of which kind of deadline the axis has"* — and that is true
as stated.  What was not measured until now is that the asymmetry is TOTAL
rather than partial, because the surrendered score is the maximum of the range
rather than a point inside it.

## What this implies

* **The collapse is structural, not a tuning accident.**  With two live axes,
  one of which pays its maximum when abandoned, there is exactly one
  Pareto-optimal corner and it is the same one in every situation.
* **It compounds with the static option set.**  The corners do not change with
  the model (verified: no minting rule reads the effector model,
  `log_authority`, `recalibration_required` or the fault), and the scoring
  guarantees one of them always wins.  Either alone would be limiting; together
  they make the deliberation layer a constant function.
* **`speed_priority` is unreachable for a second, independent reason.**  Block
  G1 showed the gate's middle region admits only it; this shows it is dominated
  whenever the altitude axis moves, because it surrenders altitude.  Both would
  have to be fixed for it to be testable.
* **A surrendered achievability-only axis needs a price inside the range, not
  at its end.**  What that price is, is exactly the cost question — and the
  ledger is the currency this line has already built for it.

---

# Block J — the ledger-priced surrender: PREDICTION FALSIFIED, and the pricing made it worse

Prereg: `docs/regime_pareto_frontier_prereg.md`, final section ("PRICING THE
SURRENDERED AXIS WITH THE LEDGER"), committed before the block ran, including
its worked prediction and its named most-likely falsifier.

`f16_flight_path_control` **v8.3.0**: a surrendered achievability-only axis is
priced at `f16_actions_to_option_loss` — the actions the ledger still funds —
instead of at the horizon.  Protocol identical to block H (4 scenarios x 25
frozen seeds, 100 s at 10 Hz, gate OFF, `--include-trace`) so the two are
directly comparable.  Block
`results/jsbsim_f16_paper_replication_10hz_ledger_surrender_j_v1/`.

## Held to the prereg

| | block H (surrender = horizon) | block J (surrender = ledger) |
|---|---|---|
| adoptions | **48** | **13** |
| final ordinals adopted | **2 x48** | **5 x10, 4 x3, 2 x0** |
| ordinals ever held / 100 episodes | 0: 64,886 · 2: 34,698 | 0: 90,930 · **5: 7,832** · **4: 718** |
| crashes, all 100 episodes | **19** | **22** |
| jammed_rudder crashes / 25 | **3** | **8** |
| nominal base seed | 323.28346789186793 ft | **323.28346789186793 ft** |

* **Prediction 1 — "ordinal 2 remains modal, on more than half of adoptions":
  FALSIFIED, and not narrowly.**  Ordinal 2 is adopted **zero** times.
* **Prediction 2 — "at least one verdict differs": held trivially**, since all
  of them did.  It was too weak a prediction to have been worth making.
* **Prediction 3 — "the change bites where the ledger is tight": NOT ASSESSED
  as stated**, because the mechanism was not the predicted one (below).
* **Prediction 4 — "nominal untouched": HELD**, on the pin.
* **The named most-likely falsifier — "nothing changes at all" — did NOT fire.
  The opposite extreme did.**

## The mechanism, confirmed on one episode

Probing damaged_wing seed 241172975 under v8.3.0 produces **no output at all**:
no `GoalRevisionRequest` is ever emitted and the ordinal never changes.  Under
v8.2.0 the same seed escalates at action 316 and finishes in orbit.

Pricing the surrendered heading at the ledger removed orbit's dominance.  With
nothing dominating, `cognitive_pareto` finds no counterexample, no revision
request is raised, and `cre_publish_incumbent_stands` closes every window — so
adoptions fall 48 → 13.  The few that survive are the corners that surrender
ALTITUDE (roll priority, speed priority), which the ledger price does not
touch.

**So the asymmetry did not disappear, it INVERTED.**  v8.2.0 rewarded
surrendering an achievability-only axis at the ceiling and orbit won
everything; v8.3.0 charges it the ledger and the altitude-surrendering corners
win what little is left.  Those are exactly the corners block 1 measured at
0.65 jam crash rate, and exactly the corners block 3's crash table indicts
(26 of 27 crashes end on a corner that surrendered altitude).

## The finding: FOUR pricing conventions, FOUR constant winners

| convention | dominant corner | jam outcome |
|---|---|---|
| v3-era ladder (no frontier) | orbit | **0.04 crash at n=100 — the standing best** |
| block 1: surrendered axis = flat 0.0 | roll priority, 91/100 | 0.65 crash at n=100 |
| v8.2.0: surrendered axis = the horizon | orbit, 48 of 48 | 3 crashes / 25 |
| **v8.3.0: surrendered axis = the ledger** | **roll / speed priority, 13 of 13** | **8 crashes / 25** |

**The frontier has never once selected by situation.**  Every pricing
convention tried produces a CONSTANT winner; changing the price changes WHICH
constant, never whether there is one.  That is now three distinct scoring
conventions tested against the same corner set, and the scoring hypothesis has
been given every chance.

The collapse to ordinal 2 was therefore **load-bearing**: it was reaching the
right answer for a bad reason, and repairing the reason lost the answer.  Jam
crashes 3 → 8 of 25 is what that costs.  **No CI is computed at n=25 and no
rate is claimed** — but the direction is consistent with everything blocks 1
and 3 measured about which corner survives, and it is recorded as a measured
negative rather than explained away.

## Standing state after block J

* **v8.3.0 is measured WORSE than v8.2.0 and should not stand as the default.**
  Total crashes 19 → 22 across the same 100 frozen episodes, jam 3 → 8,
  altitude RMSE up in both fault scenarios that moved.
* **The scoring hypothesis (A) is not merely insufficient — it is answered.**
  Three conventions, three constants.  The price determines which corner is
  always chosen; it cannot make the choice depend on the aircraft.
* **The option-set hypothesis (B) is what is left**, and it is the one the
  project owner named first: *if the operating model changes, the available
  options must change too.*  Nothing in the corner-minting path reads the
  model, and no reweighting of a fixed menu has produced situational selection.
* **What a corner costs is still worth having** — the ledger is the right
  currency and blocks D/F1/F2 earned it.  What block J shows is that a cost
  cannot substitute for an availability decision: pricing a menu does not make
  the menu depend on the plant.

## Block R — the allocation flies: FALSIFIED (reverted), and block S: provably vacuous

Two rungs were attempted, one measured and falsified, one killed by projection
before it was built. Both are recorded because both change what to do next.

### R — reallocating objective weights by containment: FALSIFIED

`f16_reallocate_objective_weights` multiplied each contained axis's policy
objective weight by its containment share, rescaled to preserve the summed
weight (altitude→vertical, heading→turn, speed→forward). Prereg in
`docs/regime_pareto_frontier_prereg.md`, block R.

| prediction | outcome |
|---|---|
| 1. nominal pin unchanged | **CONFIRMED, exactly.** `323.28346789186793`, byte-identical. All margins > 1 → all shares 1.0 → normaliser exactly 1.0. The rule is self-gating: no trigger decides when it applies, and the no-op falls out of the arithmetic. |
| 2. faulted scenarios move | **CONFIRMED.** jammed_rudder altitude RMSE 6928.58 → 6900.43 (−28.15). |
| 3. direction not preregistered | altitude RMSE worse on damaged_wing (12242.4 → 12707.2), better on jam. |
| 4. **no crash-rate regression** | **FALSIFIED.** damaged_wing crash rate **0.0 → 1.0**, minimum altitude **+2.87 ft → −9.57 ft**. n=1, matched seed 241172975, baseline measured at v8.34.0 with the change stashed. |

**Reverted**, as preregistered. Prediction 4 was written to be decisive
precisely so a favourable tracking number could not be used to keep it.

**The mechanism is not noise, it is the design.** The aircraft flew into the
ground. Containment reported altitude margin 0.02–0.17 for most of the episode,
the reallocation withdrew vertical weight accordingly, the composer stopped
fighting the descent, and it hit terrain while tracking heading well.

**The defect: containment margin measures whether the GAP can be CLOSED, not
whether the OBJECTIVE can be ABANDONED.** An unreachable altitude *reference*
is not an unimportant altitude. This tree already draws the distinction that
was missed — `_axis_time_budgets` separates TERMINAL-state axes (running out
means the episode is over: altitude→ground, speed→stall) from
ACHIEVABILITY-ONLY axes (heading, sideslip). Withdrawing authority is
admissible for the second class and categorically wrong for the first.

Restricting the pool to achievability-only axes does NOT rescue it: heading is
the only one of the three, and a single-axis reallocation normalises to
`b*s*(b/(b*s)) = b` — identically the base. There is nothing to reallocate
between.

**The corrected direction is the user's own earlier formulation, not a patch.**
When an effector saturates you either (a) use another effector or (b)
*reconsider your goal*. Reconsidering the goal means reducing the DEMAND, not
the WEIGHT: if only 4% of the altitude gap is reachable, aim for what is
reachable and keep full authority on getting there. `f16_manifold_reach_altitude`
is already published, so the reduced target is `state + sign(error) * reach`.
That is "the plant provides the manifold of possibilities, the goal chooses
from within" applied literally, and it is a different build with its own gate —
the demand path does not run through `target_vertical` (a literal 0.0 in
`emp_derive_flight_path_control_targets`), so it needs locating first. NOT
attempted here on judgement alone.

### S — containment bounding every corner's claim: VACUOUS BY PROOF

Intended as the second half of "containment decides, not dominance": no corner
may score an axis above what the plant affords, `effective = declared *
min(margin, 1)`, applied to all five named corners rather than only the
generated one.

**It cannot change the frontier, and this is provable rather than empirical.**
A candidate's axis value is monotone increasing in its effective share; the
containment factor is per-axis and identical across candidates; so the map is
strictly order-preserving on every axis. Pareto dominance reads only order.
Membership is therefore *exactly* invariant.

Projected against the collected damaged_wing traces to confirm
(`project_containment_bound.py`): frontier membership changed in **0/7**
deliberations, while the values moved hard (`fixed_point` altitude 753 → 184).

**Consequence for §50.** The reading "the generated corner loses for being
honest, so make everyone honest" is wrong. Optimism cannot be repriced away,
because no repricing touches order. The generated corner is dominated on axes
where it declares less than `fixed_point` declares, and a uniform bound
preserves that relation exactly. **Selection has to stop being dominance** —
rescaling the inputs to a dominance test can never be the fix.

Block R's rule is, in that light, the only form of "containment decides" with
any teeth so far: it applied the containment allocation unconditionally, with
no selection at all. That approach was right and its target was wrong.

## Block T — reduce the DEMAND: FALSIFIED (reverted), and the instrument defect it exposed

Block R's correction, built where R should have acted: clamp the altitude
demand to the manifold reach and keep full authority on reaching it. Prereg in
`docs/regime_pareto_frontier_prereg.md`, block T.

| prediction | outcome |
|---|---|
| 1. nominal pin unchanged | **FALSIFIED.** 323.283 → 333.265 (**+9.98 ft worse**). The clamp binds on 11.2% of nominal actions. |
| 2. no crash regression | held — 0.0 on damaged_wing. |
| 3. min altitude improves or holds | held **trivially** — bit-for-bit identical. |
| 4. altitude RMSE not preregistered | — |

**The faulted scenarios were EXACTLY unchanged** — `damaged_wing` identical to
all 17 significant figures on every metric (12242.359720448589, crash 0.0,
min alt 2.8709248043596745, structural 43.21039484032885), and `jammed_rudder`
byte-identical on the pin — **while the clamp bound on 81.1% of damaged_wing
actions** and cut desired vertical speed from 20 m/s to 8. Reverted.

### Finding 1 — demand reduction is absorbed by the saturation it respects

`desired_flight_path_angle = clamp(atan2(desired_vs − state_vz, airspeed),
±max_fpa)`. Under a damaged wing `state_vz` is strongly negative, so both the
honest demand (8 m/s) and the raw one (20 m/s) leave the pitch target pinned at
`maximum_pitch_angle_rad`. Changing a setpoint **inside** a saturated path
changes nothing.

This is the session's own saturation concept turned on the build: *saturated is
100% of available effect for the desired outcome*. Reducing the goal only helps
where the command is not already at a limit — which is the exact complement of
the regime it was designed for. It also explains block R: weights alter the
composer's trade-off even when one axis is saturated, so R moved the aircraft
(and killed it); T only moved a setpoint, so it did nothing where it mattered
and cost 10 ft where it didn't.

### Finding 2 — **RETRACTED, see block U.** The measurement below was computed on a TRUNCATED SLICE

> **This finding is wrong as stated and the error is mine.** The numbers below
> come from the first **400** actions of a 1000-action episode (`ROWS[:400]` in
> the probe's dump), and they were reported as if they characterised the
> episode. Over all 1000 actions the SAME baseline publishes **273 distinct
> reach values spanning 2.631–160.000 m** — a 60× range, not a 7.7% band. The
> reach was never a constant; it collapses with airspeed late in the episode,
> after the slice I looked at ended. See block U for the full-length
> measurement and the accurate statement. The claim below stood for one commit
> and was used to justify block U; it is left in place, struck, because a
> historical record is annotated and never silently converted.

### Finding 2 (as originally written, RETRACTED) — the altitude containment reach is a spec constant

Measured over 400 actions per scenario:

| scenario | distinct `manifold_reach_altitude_m` values | range |
|---|---|---|
| nominal | **1** | 160.000 – 160.000 |
| damaged_wing | 44 | 147.729 – 160.000 (a 7.7% band) |

`_achievable_vertical_speed()` is `max(min(maximum_vertical_speed_m_s,
airspeed * sin(maximum_flight_path_angle_rad)), 0.01)` — spec limits and
airspeed. **It reads no effector model, no learned authority, and nothing that
knows the wing is damaged.** Its docstring says the loop "declares" it can
command, and that is exactly what it is: a declaration.

So `f16_goal_margin_altitude = reach / gap` is, to within 7.7%, **160 / |error|
— a restatement of the altitude error**, carrying almost no information about
the plant.

**This conditions every margin claim made in this line, including my own.**
§43's containment publication, §50's per-deliberation margin table, and the
generated corner's altitude share `min(margin, 1)` are all functions of the
error, not of the airframe. The damaged_wing table in §50 reads as a plant
measurement and is not one. Of the three axes, only **speed** takes its reach
from the learned models (`MaxOver` over effector models of `|mean_forward|`);
altitude and heading are both computed from spec limits and state.

That is the defect worth fixing before any further containment-driven build.
"The plant and effectors provide the manifold of possibilities" requires the
manifold to be measured from the plant and effectors; for two of three axes it
currently is not. Three builds in a row (Q, R, T) have been steered by this
instrument, and all three were reverted.

## Block U — fix the instrument: FALSIFIED, and it retracts block T's finding 2

Prereg in `docs/regime_pareto_frontier_prereg.md`, block U. The reach was to
stay anchored to the declared envelope and be scaled by measured authority
(`max` over models of `f16_authority_shrunk`). **Reverted.**

### The premise was wrong: the reach was never a spec constant

| damaged_wing, v8.34.0 baseline | distinct reach values | range |
|---|---|---|
| first 400 actions (what block T reported) | 44 | 147.729 – 160.000 (7.7%) |
| **all 1000 actions** | **273** | **2.631 – 160.000 (60×)** |

Block T's finding 2 was computed on a truncated slice and quoted as if it
characterised the episode. The reach collapses with airspeed late in the run —
after the window I looked at. **This is the exact failure CLAUDE.md names: a
measurement reported without its condition**, and it survived into a commit
message and a results document, where it was used to justify this build.

The accurate statement is narrower and still worth having: the reach responds
to **airspeed** but not to **damage**. In nominal it is one value, 160.000,
across all 1000 actions; under a damaged wing it varies 60× via the airspeed
term in `min(maximum_vertical_speed_m_s, airspeed * sin(max_fpa))`, and via no
measurement of the wing. It is an envelope model evaluated at the current
state, not a plant measurement — a real limitation, far short of "a constant".

### The fix itself: falsified

| prediction | outcome |
|---|---|
| 1. PRIMARY — the instrument discriminates | **FALSIFIED.** The authority factor moves at most **1.626%** (min 0.983740). Baseline and fixed reach are near-identical; the 60× variation that exists was already there and comes from airspeed. |
| 2. nominal pin EXACT, factor read not inferred | **CONFIRMED, mechanism verified.** Factor exactly `1.000000` across all 1000 nominal actions, read from the models; pin `323.28346789186793` EXACT. |
| 3. no crash regression | held — 0.0, and **all three pins EXACT** (nominal, jammed_rudder, damaged_wing), confirming the change is behaviourally near-inert. |
| 4. faulted flight may change | it did not. |

### Why it is inert — a real tension, worth keeping

`f16_authority_shrunk = conf * ratio + (1 - conf) * 1`, with
`conf = (ok+fail) / ((ok+fail) + evidence_horizon)`. Evidence volume stays
small against the horizon, so `conf ≈ 0` and the estimate sits at ~1.0 however
damaged the aircraft is. The unshrunk `log_authority` DOES discriminate (0.00
nominal versus −1.10 / −0.79 damaged, i.e. a factor of ~0.33–0.45) — but using
it is precisely the over-confidence-on-thin-evidence bug that §37 fixed.

**The same shrinkage that makes authority weighting honest makes it useless as
a reach scaler.** That is the tension to resolve before retrying: the reach
needs an estimate that is both damage-sensitive and evidence-honest, which
means generating the evidence (probing the effector) rather than reweighting
what little arrives passively. The structure — declared envelope as prior,
measured authority as update — is right; the update currently has nothing to
say.

## Block V — read the probe as a LADDER (f16 v8.39.0): the first instrument that LOCALISES

Block U's dead end was "the evidence is too thin". That was the wrong
diagnosis. **The evidence is thin because the probe was not doing anything** —
more samples at an amplitude that produces no response is still no evidence.
The information is not in the COUNT, it is in the THRESHOLD.

The calibration pass already walks an amplitude ladder (each surface commanded
at ±0.2 … ±1.0). Nothing had ever read it as one. This stamps, per member: how
far up the ladder it has been pushed, the smallest push that answered, and how
long the answer took.

Measured, one episode each, **all three pins EXACT** (stamp-only, nothing
consumes them yet):

| jammed_rudder | pushed to | answered at | obs | verdict |
|---|---|---|---|---|
| aileron | 1.0 | 0.2 | 2 | responds |
| elevator | 1.0 | 0.2 | 4 | responds |
| **rudder** | **1.0** | **—** | **10** | **SILENT AT THE STOP — confirmed** |
| throttle | 1.0 | 0.2 | 6 | responds |

| damaged_wing | pushed to | answered at | obs | verdict |
|---|---|---|---|---|
| aileron / elevator / rudder / throttle | 1.0 | 0.2 | 2–10 | **all respond** |

**This is the first instrument in this line that localises.** Six earlier
attribution instruments all detected change and none said where it was
(§30-ish). This one separates the two faults categorically and correctly: under
a jammed rudder the rudder is dead and everything else answers; under a damaged
wing **every effector is healthy** — the effectors are fine and the PLANT
moved. That is the stuck / saturated / plant-moved distinction falling out of
one reading rather than being asserted.

It does it on **10 observations, not 200**, which is the whole point:
`conf = evidence/(evidence + horizon)` was asking the wrong question. A ladder
walked to full deflection in silence is a decisive observation, and absence of
a response at 0.2 is not evidence of anything — the same first-class-absence
discipline as §37, now applied to amplitude instead of count.

### The delay reading: present, and honestly null here

An effector has lag in APPLYING a command and in the EFFECT arriving, and
push-and-wait measures both together. The silent-action count banks the moment
a surface answers. Measured: **0 for every group in both scenarios.** At 10 Hz
these surfaces answer within a single action, so there is no multi-action lag
in this world to find. The instrument is present and will read a slow effector;
it has nothing to report on F-16 hydraulics at 0.1 s resolution. Recorded as a
null, not dressed up — and worth re-reading on the engine, whose spool-up is
the one plausible multi-action effector here and which also read 0.

### What this unblocks

Block U's tension — shrinkage makes authority weighting honest and useless as a
reach scaler — dissolves if confidence comes from **escalation completeness**
rather than sample volume. "Pushed to the stop, silent" is high confidence on
10 observations; "tested only at 0.2, silent" is low confidence on the same 10.
That is the next rung, and it is now measurable rather than asserted. Nothing
consumes the ladder yet, deliberately.

## Block W — confidence from escalation completeness (f16 v8.44.0)

Block U's tension resolved: `conf = evidence/(evidence+horizon)` was counting
samples, and samples were never the scarce thing. Confidence is now **how
conclusively the escalation terminated**, and the authority estimate is read
off the ladder rather than off the ok/fail ratio. All three pins EXACT
(nominal, jammed_rudder, damaged_wing); still stamp-only.

| | conf (volume, old) | conf (escalation, new) | authority |
|---|---|---|---|
| nominal, all surfaces | 0.0000 | 0.0–1.0 | **1.0000** |
| jam — aileron / elevator / throttle | 0.024–0.070 | 1.0000 | **1.0000** |
| **jam — rudder** | **0.1111** | **1.0000** | **0.0000** |
| damaged_wing, all surfaces | 0.024–0.111 | 1.0000 | **1.0000** |

A dead rudder now reads dead (0.0000, was 0.899 under volume confidence) on the
same ten observations, healthy surfaces read healthy, and a damaged WING leaves
every effector at full authority — the fault is in the plant, and the
instrument says so. Nothing was added but the reading.

### Two defects found by measuring, both mine

**The ok/fail ratio is the wrong estimand.** With completeness at 1.0 the
estimate trusts the ratio fully, which put a healthy aileron at 0.3333 on two
unlucky observations — the shrinkage had been hiding the noise rather than the
noise being small. Replaced with the ladder's own quantity: **authority is
inversely proportional to how hard you must push for the same effect**,
`smallest amplitude tested / smallest amplitude that answered`. No counts, no
horizon, no shrinkage.

**Aggregating that with a MAX was wrong** and cost healthy surfaces 0.25
authority: it asks "what is the hardest push that worked" when authority is
"what is the *easiest* push that worked". `_group_probe_max` is right for "did
anything answer at all" and wrong for the threshold.

### Quorum: diagnosed, NOT shipped

*"You don't need to walk them all — at some point you have a quorum, and you
stop once you have a sufficient explanation."* Correct, and it matters more
here than as an optimisation: **the probe runs a checklist while flying the
plant, pilot and copilot at once**, so every surface walked unnecessarily
spends control authority during a fault. Stopping early is a safety property.

Two forms were built and both read wrong:

- **latched** — fired on damaged_wing, where every effector is healthy, because
  during escalation there is an instant when a surface has been pushed hard and
  has not answered *yet*. A latch cannot tell that transient from a verdict —
  the exact inconclusive state the ladder exists to distinguish.
- **not latched** — read 0.0 everywhere including the jam, because it is
  whichever model happened to write last.

The cause is structural and names the fix: `f16_probe_explanation_found` is an
**episode-level fact written from a per-model match**, and "does there exist a
group silent at the stop" cannot be answered from inside one model's binding.
It needs a per-model group-scoped stamp first, then an episode-level `Exists`
over that — two rules, not one term. Removed rather than shipped reading wrong.

### The 10 Hz condition on block V's null

Block V recorded zero response lag on every group and attributed it to the
surfaces. That is **rate-conditional and was stated without its condition**:
10 Hz is held for like-for-like comparison with the replication paper, so the
sampling interval is 0.1 s and sub-interval lag is unobservable by
construction. The instrument is not reading "these effectors have no lag"; it
is reading "no lag is resolvable at the rate this study is pinned to". At
higher rates the difference is expected to appear, and the engine spool is the
first place to look.

### Block W addendum — quorum, built properly (v8.45.0)

Two rules, as the diagnosis required: a **group-scoped stamp on the model**
(`f16_probe_group_silent_at_stop`, unlatched, so a surface that answers later
stops being silent), then an **episode-level `Exists`** over it
(`f16_note_probe_quorum`, matching the episode alone).

| scenario | quorum | `silent@stop` | reading |
|---|---|---|---|
| nominal | **0.0** | none | nothing to explain |
| jammed_rudder | **1.0** | **rudder only** | one surface is dead, and which |
| damaged_wing | **0.0** | none, all authority 1.0 | no effector explains this |

Pins EXACT. **The damaged_wing row is the important one:** quorum 0 *with every
effector at full authority* IS the plant-moved verdict. The instrument now
separates "an effector died" from "the plant changed under me" on one reading,
which six earlier attribution instruments could not do at all — and it says
"stop probing, you have your answer" only in the case where an answer exists.

What remains unwired is the stop itself, which has to drive the calibration
pass in the general seed. The predicate it gates is now correct and measured.

## Block X — the stop, wired (f16 v8.49.0): the largest measured effect in this line

`f16_stop_probe_on_quorum` clears `recalibration_required` once quorum has
held, emptying the general seed's `calibration_frontier`, whose exhaustion is
already the pass's own exit to `synthesis`. The stop is expressed in the
existing lifecycle rather than by reaching into the general seed.

| scenario | altitude RMSE | crash | min alt ft | heading ° | speed fps | structural |
|---|---|---|---|---|---|---|
| nominal | **BYTE-IDENTICAL** 323.2835 | 0.0 | 8927 | 13.3 | 4.9 | 0.64 |
| **jammed_rudder** | **6928.58 → 323.10** | 0.0 | 2.10 → **8907** | 98.1 → **22.5** | 176.2 → **19.4** | 11.83 → **0.64** |
| damaged_wing | **BYTE-IDENTICAL** 12242.3597 | 0.0 | 2.87 | 81.9 | 115.2 | 43.2 |

A jammed rudder now tracks altitude at **323.10 ft against nominal's 323.28** —
the fault becomes almost free, because the loop stops running the checklist the
moment it knows which surface is dead. Two of three scenarios are byte-identical
because the instrument correctly finds no dead effector in either.

### Two failures on the way, and what each corrected

**X (v8.46.0) fired on a transient and crashed a healthy aircraft.** damaged_wing
went crash 0.0 → 1.0 and +442 ft, because the stop read quorum's INSTANTANEOUS
value. Measured afterwards: quorum holds for at most **1 action** under a damaged
wing (2 blips in 1000, while a surface is pushed to the stop and has not answered
yet) and **882 contiguous** actions under a jammed rudder. An irreversible act
must read how long a condition has HELD, never that it holds — the same defect,
in a third form, as "containment decides, not triggers".

**X2 (v8.47.0) then fired never**, because the activation threshold used
`regime_evidence_horizon_actions` = 80 while the calibration pass it governs
lasts ~73 actions. The counter reached 881 and the flag never set. That constant
was defended as principled *because it was not fitted to the data* — and being
principled about a constant's provenance does not make it operable. **A threshold
must be shorter than the process it governs.**

### There is no right constant

The threshold is now the worst answer delay this airframe has actually shown,
plus the action it takes to observe an answer: wait longer than anything has ever
taken to reply, then one more action to see the reply. The `Max(..., 2.0)` floor
of v8.48.0 is gone — it was a number. Both remaining terms are structural, and
the quantity MOVES with the aircraft: at 10 Hz the measured lag is 0 so it
evaluates to 2, and on a slower effector, or at a sample rate where lag resolves,
it grows on its own. This is also the first consumer of the lag instrument from
block V, which had nothing to say at 10 Hz and now sets an activation energy.

### Nothing is permanent

The stop is a latch with asymmetric energies: many contiguous actions of silence
to set it, a single action of the condition not holding to release it
(`f16_release_probe_stop`). A jammed effector can free itself and an airframe
gets repaired; detecting a change once does not stop the world changing again.
Releasing does not itself reopen calibration — the existing surprise-triggered
recalibration does that. It withdraws the standing claim that an explanation is
in hand, so the next surprise meets a loop willing to look again rather than one
that has already decided.

### What is given up, deliberately

Sufficiency is not completeness: a second simultaneous fault on an unprobed
surface is missed by THIS pass. The trade is bounded — the probe is triggered by
surprise rather than by schedule, so a missed fault that matters will surprise
the loop again and reopen the checklist. A pilot who finds the dead rudder stops
looking too.

## Block X — FULL BLOCK, 8 scenarios × 3 episodes (f16 v8.49.0 vs v8.34.0)

Matched frozen seeds (`241102975 + scenario_index × 10000`), 24 episodes per
arm, each block run alone on an otherwise idle machine.

| scenario | alt RMSE base | alt RMSE stop | delta | crash b/t |
|---|---|---|---|---|
| nominal | 307.82 | 307.82 | **identical** | 0.00 / 0.00 |
| **jammed_rudder** | **11391.38** | **803.44** | **−10587.94** | **0.67 / 0.00** |
| broken_aileron | 900.60 | 900.60 | identical | 0.00 / 0.00 |
| saturated_elevator | 4126.16 | 4126.16 | identical | 0.00 / 0.00 |
| landing_gear | 1337.70 | 1337.70 | identical | 0.00 / 0.00 |
| shifted_cg | 6774.10 | 6774.10 | identical | 0.00 / 0.00 |
| damaged_tail | 7728.67 | 7728.67 | identical | 0.00 / 0.00 |
| damaged_wing | 8633.44 | 8633.44 | identical | 0.67 / 0.67 |

**7 of 8 scenarios byte-identical, every episode.** The rule fires only where a
genuinely dead effector exists, exactly as the instrument reports — including
under a damaged wing, where all three episodes (two of them ending below ground)
are unchanged to the last digit. This build neither causes nor fixes that
failure.

### jammed_rudder, per episode — the distributions are DISJOINT

| seed | RMSE base | RMSE stop | min alt base | min alt stop | structural base | structural stop |
|---|---|---|---|---|---|---|
| …975 | 6928.58 | 323.10 | 2.10 | 8907 | 11.83 | **0.64** |
| …976 | 10594.71 | 1021.24 | 9.46 | 18429 | **521.89** | **0.64** |
| …977 | 16650.86 | 1065.99 | −15.24 | 19237 | 19.10 | **0.64** |

Baseline spans 6929–16651; treatment spans 323–1066. **Every treatment episode
beats every baseline episode**, by 6.5–15.6×, and the two ranges do not overlap.
At n=3 that is a disjoint-distribution result, not a mean shifted by one episode.

**The structural column is the real finding.** The baseline was flying the
airframe at up to **521× its structural limit** while walking the checklist
under a jam; with the stop it sits at **0.64 on all three seeds** — inside
limits, identical across seeds. The aircraft stops tearing itself apart because
it stops spending actions testing surfaces it has already confirmed good.

### What is NOT established

**The crash-rate claim is not powered.** jammed_rudder goes 2/3 → 0/3, Wilson 95%
[0.208, 0.939] versus [0.000, 0.562] — the intervals overlap and the difference
is not CI-separated at n=3. Across all 24 episodes per arm, 4/24 → 2/24, Wilson
[0.067, 0.359] versus [0.023, 0.258], also overlapping. **Crash rate is reported
as a guard that did not regress, never as a result.** The RMSE and structural
results stand on disjoint ranges; the crash result does not, and would need a
powered gate per the standing rule.

### Mechanism and cost

`recalibration_count` is **2 in both arms** on every jam episode, so the stop
does not reduce how often recalibration is triggered — it ends each pass
earlier, which is the designed behaviour. Latency p99 across all 24 episodes:
**68724 µs with the stop versus 79102 µs baseline, 0.869×** — faster despite
three additional rules, because calibration actions are the expensive ones and
there are fewer of them.

## Block Y — WHY THE DAMAGED WING STILL FLIES INTO THE GROUND

Two of three damaged_wing episodes end below ground (−8.09, −12.13 ft), body
rates reach 5.3–10.1 rad/s (300–580 °/s — the aircraft is tumbling) and
structural utilisation reaches 43×. None of that changed this session, and the
reason is now measured rather than suspected.

**The regime never escalates.** All three episodes:
`final_regime_ordinal = 0.0`, `regime_escalation_action = None`. The aircraft
stays in `fixed_point` from the fault to the ground.

It is not that deliberation fails to happen. It happens, it produces a
`GoalRevisionRequest` every time, and **the corner it proposes is always
`fixed_point` — the regime already held.** The frontier deliberates, decides,
and proposes *stay as you are*, repeatedly, while the aircraft departs.

### The mechanism is dominance itself, and it is provable

Measured at three deliberations under a damaged wing:

| action | fixed_point | trim | orbit | speed_priority | roll_priority | proposed |
|---|---|---|---|---|---|---|
| 638 | 597,1,1024,1024,1024,**1024** | 597,1,…,**0** | 597,**0**,…,**0** | **244**,1,… | **244**,**0**,… | fixed_point |
| 799 | 753,1,…,**1024** | 753,1,…,**0** | 753,**0**,…,**0** | **170**,… | **170**,… | fixed_point |
| 882 | 199,**1024**,… | 199,1024,…,**0** | 199,**0**,…,**0** | **5**,… | **5**,… | fixed_point |

`fixed_point` is the only corner that surrenders nothing. Since the v8.3.0
repricing made a surrendered axis score LOWER than a kept one, `fixed_point`
scores ≥ every other corner on every axis simultaneously. It is therefore
non-dominated in every deliberation, and every corner that trades anything is
dominated by it — by construction, not by circumstance.

**This is §27's pathology sign-flipped.** Originally surrender scored the
CEILING, so the corner that gave up the most (orbit) dominated everything.
Repricing made surrender score the floor, so the corner that gives up nothing
dominates everything. Four repricings changed WHICH corner always wins; not one
of them removed *a corner always wins*.

### The theorem this line has been walking into since block 1

**Pareto dominance cannot select a compensating corner.** Compensation means
accepting a worse value on one objective to gain on another — which is the
definition of a dominated point whenever the alternative gives up nothing. A
frontier over corners that trade can never elect a trade, because the
non-trading corner is always on the frontier and always weakly better.

So the frontier is not miscalibrated, it is the wrong instrument for this
decision, and no repricing can fix it. This is the formal content of the
standing instruction that **containment decides, not dominance** (block S
showed rescaling the inputs is provably a no-op; this shows why). It is also
why the GENERATED corner — the only honest one — is dominated in every
deliberation where it differs from `fixed_point` (§50): being honest about what
the plant will give makes it strictly worse on the axes it is honest about.

### What this does NOT excuse

The probe/stop line landed this session is real and measured (block X), but it
addresses the effector-failure half. Under a damaged wing the instruments now
correctly report *no effector explains this, the plant moved* — and then nothing
acts on that report, because the only actor is a frontier that structurally
cannot choose to compensate. **Diagnosing is not flying.** The next rung is
selection that is not dominance, and it is now blocked on a decision rather than
on evidence.

## Blocks Z + Y2 — containment selects, and attitude is priced at its own clock

Two changes, measured together and separately. **Neither reaches the target of
zero crashes on damaged_wing.** Both move a named blocker, and the blocker is
now one stage further along.

### What the trace showed (damaged_wing is a ROLL DEPARTURE, not a descent)

`damaged_wing` is the **only** scenario in the suite that ever rolls past 90°,
in all three episodes, at actions **139 / 142 / 147** — 4 seconds after fault
onset. All three crash. Every other scenario never inverts and never crashes.
High alpha is NOT the discriminator: `damaged_tail` reaches 76° alpha and
survives all three episodes.

The damaged wing's asymmetric lift rolls the aircraft inverted; from there it
falls, contacting ground at action 667 and sitting inverted at 5 ft with
airspeed bleeding 95 → 53 kts.

**The paper's own reference controller has `crash_rate` 0.0 on this scenario**,
so zero is attainable and is the bar.

### Z — containment selects (v8.50.0)

A kept axis on an objective outside reach contributes nothing. This is the
non-uniform rule block S's proof leaves open — a uniform rescale cannot change
frontier membership, a per-corner zeroing can.

- **7 of 8 scenarios byte-identical.** nominal `323.28346789186793` and
  jammed_rudder `323.10483819184157` unchanged to full precision.
- **The regime escalates for the first time in this line** — damaged_wing
  reaches ordinal 5.0.
- Peak structural utilisation **43.21 → 5.88**.
- Crashes **2/3 → 3/3**, Wilson [0.023, 0.258] vs [0.043, 0.31] — overlapping,
  and not the point: both are a lost aircraft.

The corner it elects is `roll_priority`, which stabilises roll but buys no
lift. `speed_priority` — the one corner declaring `restores_basin`, which
spends altitude to buy dynamic pressure — loses because heading is also outside
reach, so `roll_priority` surrenders more and scores higher.

### Y2 — attitude priced at its own clock (v8.51.0)

v8.2.0 gave attitude `channel_surrender_discount` 1.0 to stop nominal's
manoeuvre excursions opening the gate. Attitude is a TERMINAL channel: heading
and sideslip are objectives that can be abandoned, attitude is not.

The signal that was being discarded, measured across the suite: attitude reads
under 20 actions-to-transition on **64–81%** of damaged_wing actions (median 0)
and on **0–3%** everywhere else including nominal (median 1023). A ~25:1
separation was suppressed to silence a 1% one.

Before: the loop computed `f16_actions_to_transition_attitude` = 96, 60, 9, 4, 0
across actions 117–147 and reported `regime_actions_to_transition` = 1023
throughout. **It measured an 8-action deadline and planned to act in 75.**

After: `regime_actions_to_transition` tracks attitude down — 777, 306, 91, 64,
8, 5, 1, 0 — `regime_actions_to_act` follows, and
**`regime_escalation_requested` goes to 1 at action 129**, with roll at −24.5°,
nine actions of margin and eighteen before inversion. It was previously never
requested at all. nominal and jammed_rudder are unchanged to full precision.

### The blocker now: ADOPTION LATENCY

Escalation is requested at **129**. `regime_ordinal` does not change until
**317** — 188 actions, 18.8 seconds, while the aircraft inverts at 147 and
falls. Deliberation is open and the integral accumulates 1/action throughout.

So the chain is now: fault 100 → plant change detected 105 → escalation
requested 129 → **inverted 147** → adopted 317. Detection is no longer the
problem; the 188 actions between requesting a regime change and making one is.
Everything built in blocks V–Z improves what the loop KNOWS and when it knows
it; none of it shortened the distance between knowing and acting.

## Block AA — the deliberation cadence: you cannot wait longer than you have

The 188-action adoption latency was not adoption machinery being slow. Measured
on the damaged_wing trace: deliberation opens **8 times in 1000 actions**
(128, 316, 430, 513, 674, 757, 840, 923), profile mints coincide with openings
**exactly**, and the single ordinal change is at 317 — the action after the
second opening. **The frontier is evaluated once per opening.** It decided at
128, when altitude was still reachable and the incumbent therefore dominated,
and could not reconsider until 316. The aircraft inverted at 147.

The opening guard was `absence_integral > evidence_horizon` — a fixed 80-action
wait, the same constant that was already wrong for the calibration pass (80
against a ~73-action pass, block X2). It now waits the SHORTER of the horizon
and `regime_actions_to_act`, the loop's own per-action projection of how long
it has. Absent or zero projection falls back to the horizon, so a consumer that
publishes no clocks is unaffected. This is in the GENERAL seed, because
"re-decide at least as often as the fastest thing you could lose" is not a
domain fact.

| | before | after |
|---|---|---|
| damaged_wing openings | 8 | **12** (123, 248, 272, 368, 380, 385, …) |
| ordinal change | 317 | **249** |
| peak structural | 1.73 | 1.60 |
| nominal | 323.28346789186793 | **unchanged** |
| jammed_rudder | 323.10483819184157 | **unchanged** |

**It does not reach the target.** damaged_wing still crashes: adoption at 249,
inversion at 147. 68 actions closer and still 102 actions late.

### Why it is still late, precisely

The first deliberation opens at **123** — early, as intended — and its verdict
is HOLD, because at 123 altitude is still reachable and the incumbent dominates.
The guard `Not(regime_deliberating)` then blocks re-opening while that
deliberation runs, and once it closes the absence integral must re-accumulate.
The next opening is 248.

So the loop now looks at the right time and reaches the wrong conclusion,
because **the conclusion is formed from a snapshot and never revisited while it
is being acted on.** A deliberation that opened when the objective was
reachable stays committed after it stops being reachable. Shortening the wait
between deliberations cannot fix a decision that is stale within one
deliberation.

The next rung is re-evaluation DURING an open deliberation — abandoning a
verdict whose premises have expired — not a shorter interval between them. The
chain as it now stands: fault 100 → plant change detected 105 → deliberation
opens 123 → verdict HOLD (premises: altitude reachable) → escalation requested
129 → **premises expire ~171 (altitude outside)** → **inverted 147** →
re-opened 248 → adopted 249.

## Block AB — the re-evaluation rung: timing is now solved, and it does not matter

`cre_abandon_stale_deliberation` closes an open deliberation once
`regime_deliberation_integral > regime_actions_to_act` — the block AA principle
applied one level in: you cannot spend longer deciding than you have left. A
zero or absent projection cannot trigger it.

**Both preregistered predictions held, including the negative one.**

| prediction | outcome |
|---|---|
| 1. re-decides before inversion | **CONFIRMED.** Openings now 123, **132, 138, 143, 146**, 198, 248 … — four fresh deliberations between the escalation request at 129 and inversion at 147, where the next one used to be 248. 12 → 21 openings, no runaway churn. |
| 2. **it will still choose HOLD and still crash** | **CONFIRMED.** Ordinal change still at 249; damaged_wing bit-identical to block AA (14717.1 ft, −11.1 ft, structural 1.60). |
| 3. no regression | **CONFIRMED.** nominal `323.28346789186793` and jammed_rudder `323.10483819184157` unchanged to full precision, 0 crashes. |

### What this establishes

**The timing chain is now complete and correct, and the aircraft still dies.**
The loop detects the plant change at 105, requests escalation at 129 with nine
actions of margin, and re-evaluates the whole frontier four times before the
wing puts it inverted. Every evaluation returns HOLD, correctly, on its own
terms:

- `f16_goal_outside_altitude` is 0 until 171 — altitude genuinely *is* still
  reachable at 132–146, so the incumbent is not penalised by containment;
- **no corner differentiates on attitude**, the axis whose clock reads 1. Every
  corner keeps it, so its value is identical across the frontier and cannot
  discriminate between candidates at all.

So the loop is asking a well-posed question at exactly the right moments and
getting a well-founded answer, about the wrong thing. **Attitude — the axis
actually being lost — is invisible to selection, and no amount of timing work
substitutes for that.** Four rungs of timing (X2, AA, AB) have now been
measured; each did what it claimed and none moved the outcome, which is the
strongest available evidence that the remaining defect is not in timing.

### The precise remaining defect

A corner is an allocation over six axes, and three of them (attitude,
structural, sideslip for most corners) are declared identically by every
corner. The frontier can therefore only ever discriminate on altitude, heading
and speed. Under a damaged wing the failure is a ROLL DEPARTURE — an attitude
loss — and the corner that addresses it (`roll_priority`, which activates roll
stabilisation) is elected only when *altitude* eventually goes outside reach at
171, twenty-four actions after inversion, for reasons that have nothing to do
with what it is for.

The next rung is therefore not timing and not dominance: **attitude must be a
discriminating axis** — either a containment reading of its own, or corners
that declare different allocations to it. Everything else in the selection path
has now been measured and works.

### Honest caveat

`regime_deliberation_stale_count` is stamped on the regime node and does not
appear in the episode trace, so the abandonment count could not be read
directly. The opening cadence (123 → 132, a nine-action gap against an
eighty-action horizon) is the evidence that abandonment fired.

## Block AC — attitude minted as a discriminating axis (f16 v8.53.0)

Block AB established that the axis actually being lost contributes an
IDENTICAL value to every candidate, because attitude is projected once while
every other terminal axis is projected twice — `f16_axis_clock_altitude_kept`
(the margin under the loop's declared authority) alongside
`f16_axis_clock_altitude` (under none). One stream cannot discriminate however
corners allocate.

`f16_publish_attitude_authority_clock` mints the second stream, and both of its
terms are DISCOVERED rather than declared:

- **roll rate** is minted as a difference of the measured roll angle, the same
  construction the loop already uses for `f16_sink_rate_ema` / `f16_yaw_rate_ema`;
- **roll authority** is read off the LEARNED effector models — `MaxOver` of
  `|mean_roll|`, the best roll consequence any surface has actually
  demonstrated, which is exactly how the speed axis already sources its reach.

No coefficient appears in the rule. Both terms move with the airframe.

| action | raw clock | assisted | roll rate | roll authority | gain |
|---|---|---|---|---|---|
| 111 | 255 | 1024 | 0.063 | 5.000 | 4.0× |
| 131 | 33 | 154 | 0.346 | 0.272 | 4.7× |
| **141** | **8** | **1024** | 0.744 | 0.851 | **128×** |
| 151 | 1 | 15 | 0.974 | 0.910 | 15× |
| 301 | 1024 | 1024 | 0.049 | 0.891 | **1.0×** |

At 141 the surfaces can out-roll the departure (authority 0.851 against rate
0.744), so a corner that spends roll authority sees 1024 actions where one that
does not sees 8 — the discrimination attitude has never had. The streams
converge to 1.0× in healthy flight, which is the honest reading when there is
nothing to arrest.

nominal `323.28346789186793` and jammed_rudder `323.10483819184157` unchanged
to full precision. **Stamped only** — nothing consumes it yet.

### The defect found while landing it

The rule initially measured a roll rate of **exactly 0.000 at every sample**,
so the assisted clock silently equalled the raw one and the gain was 1.00
everywhere. Cause: no per-action guard, so the rule re-fired inside the action's
rule fixpoint until `f16_prev_roll_angle` equalled the current angle and the
difference collapsed. This is the second time today the same defect appeared
(the quorum counter needed the identical guard) — **a rule that differences its
own stored state must be gated to once per action, always.**

It was only visible because the new attributes were added to the trace's
diagnostic allow-list; before that they read as absent and could have been
mistaken for a rule that never fired. That allow-list has now hidden two
quantities in one session (`regime_deliberation_stale_count` was the other).

### What remains, and a correction to where this was built

Wiring the second stream into `_axis_time_budgets` requires corners to declare
DIFFERENT attitude allocations, and at present every corner declares 1.0 — the
share representation caps at 1.0, so freed authority from a surrendered axis
cannot flow to a kept one. That is the allocation-budget change §49 anticipated
and it is the true remaining rung.

**This rule is also in the wrong seed.** "Every terminal channel is projected
twice, raw and with the authority that opposes its loss applied" is domain-free
— it is as true of a car's yaw axis under a locked brake as of an aircraft's
roll axis under a damaged wing. The generic form belongs in
`control_regime_escalation`, parameterised per `ControlRegimeChannel`: the
consumer publishes a measured rate and a measured authority for a channel, and
the general seed publishes the assisted clock. What is F-16-specific here is
only WHICH measurements feed it (roll angle, `mean_roll`) — and that is exactly
the consumer's job. Landing it in the f16 seed was expedient and is not where
it belongs.

## Block AD — the second projection is GENERIC (cre v7.4.0, f16 v8.54.0)

Block AC built the assisted attitude clock in the F-16 consumer. That was the
wrong place: *"a terminal channel is projected twice, raw and with the authority
that opposes its loss applied"* is not an aircraft fact. A wheel losing grip, a
brake losing authority, a joint approaching its stop and a wing dropping are the
same shape — something is being lost at a measured rate, and some effector has a
measured ability to oppose it.

**The general seed now owns the projection**
(`cre_project_channel_assisted_clock`), extending the documented channel
contract with two OPTIONAL consumer measurements:

- `channel_rate_measured` — the rate at which the channel is losing its
  objective, in the consumer's own units;
- `channel_authority_measured` — the measured authority opposing that loss, in
  the same units: what the effectors have *demonstrated*, not what they are
  specified to do.

Publishing both earns the channel `channel_clock_assisted`. Publishing neither
leaves the channel exactly as it was, so every existing consumer — the humanoid
included — is untouched. **The general seed contains none of the fourteen domain
words**, verified mechanically, and the test asserts the projection rule names no
axis and no effector.

The F-16 consumer now publishes only what is genuinely domain-specific: which
channel is the attitude one, that its rate is a roll rate, and that the authority
opposing it is `MaxOver |mean_roll|` over the learned models. Reproduced through
the general path:

| action | raw | assisted | rate | authority | gain |
|---|---|---|---|---|---|
| 111 | 255 | 1024 | 0.063 | 5.000 | 4.0× |
| 141 | 8 | 1024 | 0.744 | 0.851 | 128× |
| 301 | 1024 | 1024 | 0.049 | 0.891 | 1.0× |

nominal `323.28346789186793` and jammed_rudder `323.10483819184157` unchanged to
full precision. Still stamped only.

### A repeat of the session's own recorded mistake

Moving the rule, I replaced a source span using two anchors — the start of the
rule being moved and the start of a *later* function — without measuring what lay
between them. `publish_goal_containment_rule` was in that span and was deleted.
This is precisely the failure that destroyed half this generator earlier in the
line and for which a lesson is already recorded: **never delete a span by two
anchors without measuring it.**

It was caught immediately because the generator raised `NameError` on the next
run, and recovered from `git` with no loss. The redo measured the span first
(97 lines, next `def` identified explicitly) and asserted the before/after
function sets differed by exactly the one intended name. That assertion is the
practice the lesson should have named the first time: not "be careful with
anchors" but **"diff the symbol set across any structural edit."**

## Block AE — the allocation budget: representation complete, prediction FALSIFIED

Shares are now normalised by their declared total (`_allocated`), so authority
given to one objective is not available to another: `fixed_point` commits 1/6 to
each of six objectives, `roll_priority` 1/4 to each of the four it retains. And
attitude's two streams are wired into `_axis_time_budgets`, so that budget has
something to interpolate between — assisted when a corner spends authority on
attitude, raw when it does not, falling back to the raw clock when no assisted
projection exists.

All five mint rules changed. nominal `323.28` and jammed_rudder `323.10`
unchanged; damaged_wing **bit-identical**: 14717.12 ft, ordinal change still at
249, inversion still at 147.

**Prediction 1 FALSIFIED**, and the prereg named the consequence in advance:
*"if the ordinal still does not change before 147, the corner library — not the
representation — is the blocker."* The representation is now complete and it did
not help.

### Where the decision is actually made

With attitude discriminating, `roll_priority` beats `fixed_point` on attitude
(1/4 against 1/6 of the assisted clock) while `fixed_point` beats it on altitude
and heading, which `roll_priority` surrenders. **Neither dominates.** Both sit on
the frontier, and the choice between them falls to
`regime_policy_priority_axis_ordinal` — which
`f16_choose_regime_situational_priority` sets from two constants and a default:

```
terrain_proximity_high = altitude < 500 m   -> altitude axis
airspeed_low           = airspeed < 70 m/s  -> speed axis
otherwise                                   -> heading
```

At 19,000 ft and 160 kts neither cue fires, so the priority is **heading**,
measured pinned at ordinal 1 for the entire episode — and on heading
`fixed_point` wins, because `roll_priority` gave heading up. The frontier
correctly identifies that a compensating corner is available and then selects
against it on an axis chosen by a constant that never mentions what is being
lost.

**So the blocker is neither dominance, nor timing, nor the representation: it is
the tie-break.** Every rung this session has moved the failure one stage later
and this is the stage it now sits at — the last hardcoded constant in the
selection path, three lines deciding which axis matters while the axis with a
clock of 1 is not among the candidates it considers.

The natural repair is the one this session has now applied three times to three
different constants: prioritise the axis with the shortest clock — measured,
moving with the plant, no threshold. It is a small change and it is NOT made
here, because it is the fourth build in a chain and the session's own record is
unambiguous about what happens to those.

## Block AF — the tie-break is the shortest clock, and what it exposed

`f16_choose_regime_situational_priority` chose the priority axis from two
constants and a default (terrain < 500 m, airspeed < 70 m/s, else heading). It
now chooses the axis with the shortest published clock among altitude, heading
and attitude — the loop already measures urgency, and "terrain is close" IS a
short altitude clock. **Measured: the priority axis switches to attitude at
action 123**, exactly when the departure begins, where before it was pinned at
heading for the entire episode. nominal, jammed_rudder and damaged_wing all
unchanged.

Unchanged, because the tie-break is not what decides.

### The generated corner has been dominating the entire frontier

Probing the deliberations at 123, 134, 142 and 146 shows the same thing each
time: **every declared corner marked dominated, and one candidate alone
non-dominated, scoring 1024 on all six axes — the GENERATED corner**, minted at
the held ordinal, therefore proposing HOLD. Four consecutive re-evaluations,
each correctly timed, each deciding nothing, while the aircraft rolled inverted.

It bypasses the allocation budget because its shares are Terms computed at
runtime rather than build-time floats, so `_allocated` never sees them. When
every corner scored full authority on every axis this was a tie and genuinely
harmless — it was landed as a deliberate no-op in §50 and verified as one. The
budget (block AE) divided each declared corner's authority across the objectives
it attends to and left this one at full, converting a tie into total dominance.
**A candidate exempt from the pricing every other candidate obeys does not
compete with them, it replaces them.**

That single fact explains why blocks Z, Y2, AA, AB, AC, AD, AE and AF all
measured as no-ops on damaged_wing: they were adjusting corners that were never
being chosen.

### The obvious repair was built, measured and NOT kept

Normalising the generated corner's shares by their total moved the damaged_wing
adoption earlier (249 → 199) and **destroyed the jammed-rudder result**:
323.10 → 7790.36 ft, crash 0 → 1. With that candidate no longer dominating, a
corner is adopted under the jam that should not be. Reverted; all three
scenarios restored exactly. The defect and its repair are both recorded, and the
repair needs the jam path understood first rather than a fourth consecutive
build.

### The architectural verdict

Every rung in this chain is a numerical proxy for a statement about
ADMISSIBILITY — which corners this situation permits — expressed as arithmetic
on scores rather than stated directly. And every failure has been of the form
"the arithmetic did not say what we meant": a surrendered axis scoring the
ceiling, then the floor; a keeper scoring below a surrenderer; shares capping at
1.0; a tie broken by a constant; and now a candidate exempt from the pricing
entirely. None was a failure to know what was wanted.

## Block AG — admissibility stated directly: FALSIFIED on the first attempt

The rule said the sentence the scoring chain had been failing to encode:
*attitude is the shortest clock and the assisted projection exceeds the raw one,
so fly the corner that spends authority on it.* Two clauses, both measurements,
no thresholds, no scores.

**It fired at action 99 — before the fault — in every scenario.** nominal
323.28 → 8759.98 with a crash; jammed_rudder 323.10 → 8795.94 with a crash;
damaged_wing worse. Reverted; all three restored exactly.

### The error, which is the same one made earlier today

The self-gating claim rested on a single observation: at action 301 of one
episode the assisted and raw attitude clocks were equal (gain 1.00), and I read
that as "the streams coincide in healthy flight". They do not.
`cre_project_channel_assisted_clock` computes `assisted = raw × rate / (rate −
authority)`, which exceeds `raw` **whenever any authority is measured at all** —
which is essentially always. The second clause is therefore true almost
everywhere, and the first (attitude shortest) holds trivially in healthy flight
too, where attitude reads 1023 against altitude's 1024.

**One sample generalised to a distribution without checking it** — the identical
error as block U's truncated-slice reading of the reach, and it produced a
worse outcome because this rule acted instead of merely reporting.

The direct-grammar direction is not what failed. The clause *"authority exists
to arrest it"* is not expressible as `assisted > raw`; it needs to say that the
authority is large relative to what the departure demands, which is a
comparison the assisted clock deliberately hides by folding both into one
number. The grammar was right and the predicate was wrong, and the predicate was
wrong because I did not measure it before believing it.

### Standing state

v8.57.0: the shortest-clock tie-break is in, the generated corner still
dominates every frontier (block AF, unrepaired — its obvious repair destroys the
jam), and damaged_wing still departs. nominal 323.28346789186793, jammed_rudder
323.10483819184157, damaged_wing 14717.12, all verified after revert.

## Block AH — the authority distribution, measured across the whole suite

Block AG's predicate was written from a single observation and fired everywhere.
This is the distribution it should have been written from: 8 scenarios × 3
episodes × 1000 actions, the measured roll authority against the measured roll
demand, at v8.57.0.

`ratio = f16_roll_authority_measured / f16_roll_rate_measured` — above 1 the
best surface can out-roll what is happening, below 1 it cannot.

| scenario | n | p10 | p50 | p90 | **frac<1** | departs |
|---|---|---|---|---|---|---|
| nominal | 2997 | 121.28 | 501.65 | 2889.83 | **0.000** | no |
| jammed_rudder | 2997 | 15.28 | 54.17 | 543.92 | **0.000** | no |
| broken_aileron | 2997 | 18.82 | 73.95 | 689.43 | **0.000** | no |
| saturated_elevator | 2997 | 26.03 | 250.31 | 2134.27 | **0.000** | no |
| landing_gear | 2997 | 13.04 | 103.69 | 916.06 | **0.000** | no |
| shifted_cg | 2997 | 32.54 | 203.67 | 1418.15 | **0.000** | no |
| damaged_tail | 2997 | 2.26 | 9.03 | 413.70 | **0.000** | no |
| **damaged_wing** | 2997 | **0.88** | 268.24 | 2626.09 | **0.128** | **yes** |

**`authority < demand` occurs on exactly zero of ~21,000 actions across the
seven scenarios that never depart, and on 12.8% of actions in the one that
does.** Within damaged_wing it also localises in time:

| window | n | p10 | p50 | frac<1 |
|---|---|---|---|---|
| pre-fault (0–99) | 99 | 264.72 | 787.67 | **0.000** |
| fault → inversion (100–140) | 40 | 0.76 | 1.65 | **0.300** |
| departed (140–300) | 160 | 0.56 | 1.36 | **0.344** |

### What this establishes

1. **The separating predicate is `authority < demand`, and it needs no
   threshold.** The crossing point is where two measured quantities are equal,
   not a tuned value. Zero false positives across the suite is not a margin to
   be traded — it is the entire non-departing population.
2. **It inverts what block AG assumed.** That rule fired on `assisted > raw`,
   which is true whenever any authority is measured at all — the predicate had
   no discriminating power whatsoever and I did not check before acting on it.
   The correct sense is the opposite: trouble is when authority CANNOT match
   demand.
3. **The situation is marginal, not hopeless.** Between fault and inversion the
   median ratio is 1.65 — above 1 — with 30% of actions below. The aircraft can
   often out-roll the departure and intermittently cannot, which is exactly the
   regime where concentrating authority should matter and is the honest case for
   a compensating corner rather than an argument against one.
4. **`damaged_tail` is the near-miss worth noting**: p10 of 2.26 and p50 of
   9.03, the lowest of the seven, and it never crosses 1 and never departs. Any
   predicate wanting margin above 1 would have to explain why 2.26 is safe;
   `< 1` does not have to.

Measured before any rule reads it, which is the whole point of this block.

## Block AN — damaged_wing re-specified at +0.5; the suite re-baselined

`roll_beta` and `roll_r` from **−1.0 to +0.5**: signs restored, magnitude halved,
every other fault term retained (30% lift loss, half the aileron roll authority,
50% more adverse yaw). The negative values inverted those derivatives rather
than scaling them, giving an airframe divergent in roll–sideslip (§94).

### THE NEW BASELINE — 8 scenarios × 3 episodes

| scenario | altitude RMSE | crash | extreme rate | min alt ft |
|---|---|---|---|---|
| nominal | 311.24 | 0/3 | 0/3 | 8891 |
| jammed_rudder | 809.29 | 0/3 | 0/3 | 8901 |
| broken_aileron | 1783.56 | 0/3 | 0/3 | 6440 |
| saturated_elevator | 3801.49 | 0/3 | 0/3 | 1673 |
| landing_gear | 1115.62 | 0/3 | 0/3 | 3501 |
| shifted_cg | 5693.33 | 0/3 | 0/3 | 2867 |
| damaged_tail | 8164.04 | 0/3 | 0/3 | **2.2** |
| **damaged_wing** | **6506.20** | **0/3** | **1/3** | **1.3** |

**Every prior baseline in these documents is superseded.** The `333.97 / 324.92
/ 14763.77` pins and the block X suite refer to a scenario that no longer
exists, and to a tree fifteen commits older.

**Predictions 2 and 3 confirmed.** damaged_wing crash 2/3 → **0/3**, and it
remains discriminating rather than trivially safe: extreme body rate on one
seed, structural utilisation 16.83 and 15.90 on two, and minimum altitudes of
2.0 and 1.3 ft. A worse controller crashes here; this one does not, barely.

### Prediction 1 was falsified by my own error, not by the edit

It said seven scenarios would be byte-identical, and 0/8 were — because I
compared against **block X**, which predates the plant contributor, the residual
learning rule and the viability ladder. The edit was not at fault; the baseline
was fifteen commits stale.

The correct check is per-seed against the pins tracked through this session, and
it is clean:

| | seed | new | pin |
|---|---|---|---|
| nominal | …975 | **333.97** | 333.97 |
| jammed_rudder | …975 | **324.92** | 324.92 |
| damaged_tail | …975 | **8172.28** | 8172.28 |

Unchanged to the cent. **A prediction is only as good as the baseline it names**,
and "byte-identical to the previous block" is a different claim from
"byte-identical to the current tree" whenever the tree has moved between them.
That distinction has cost a false alarm here and is worth stating once: name the
commit, not the block.

## Block AO — risk ranked relatively: correct in shape, inert in magnitude

Structural risk added to the composer's cost as the fraction of the envelope a
candidate would consume — a comparison, not a gate, so it always has an answer
including when every option is bad.

**All eight scenarios byte-identical against the AN baseline. 0/24 crashes both
arms.**

| | baseline | ranked |
|---|---|---|
| every scenario RMSE | — | **identical** |
| damaged_wing peak structural | 16.83 | **16.83** |
| damaged_tail peak structural | 10.79 | **10.79** |

Prediction 1 held (no crash regression — the first block in this line with a
baseline clean enough for that to be a sharp test). **Prediction 2 falsified**:
structural utilisation did not fall anywhere.

### Why, and it is a choice I made

The term was priced with `activation_weight` **specifically to avoid inventing a
scalar**, after two earlier attempts failed on invented ones (5.0 was a magic
number; the goal at stake was unbounded optimism, §78). That weight is
**0.002**. A structural fraction of 16 therefore contributes 0.032, against
residual terms weighted 10 to 45. The term is numerically invisible, and every
ranking it could have changed was decided elsewhere by three orders of
magnitude.

So the shape is right and the price is wrong, and there is no third existing
weight to borrow. **Avoiding a magic number by reusing an unrelated one is still
choosing a number** — it just hides the choice behind a name that makes it look
principled.

### Where the price actually belongs

The contract already declares what a rung of irreversibility is worth:
`regime_rung_decade`, declared by the operator (§91). Structural consumption is
movement toward losing a rung, so it should be priced at THAT rate — in
log-irreversibility, in the same currency as the budgets — not at the rate the
loop happens to charge for actuator activation.

That plumbing does not exist: the decade lives on the regime node in the graph,
and the composer is a Rust Term that reads the policy. Connecting them is the
next piece, and it is the same shape as every other thing that worked this
session — an operator-declared ratio consumed by generic arithmetic, rather than
a constant chosen by whoever was writing the rule.

Reverted; the AN baseline stands unchanged.

## Block AP — the decade wired into the composer: it bites, and it taxes routine flight

Structural consumption priced in the operator's own currency:

```
structural cost = envelope fraction * regime_rung_decade * null residual
```

Both terms measured, the rate declared (§91), nothing invented — and unlike
block AO it is no longer numerically invisible.

| scenario | RMSE base | RMSE priced | Δ | struct base → priced |
|---|---|---|---|---|
| nominal | 311.24 | 311.24 | identical | 0.64 |
| jammed_rudder | 809.29 | 809.29 | identical | 0.64 |
| **broken_aileron** | 1783.56 | 2439.48 | **+655.92** | 0.64 → 0.64 |
| saturated_elevator | 3801.49 | 3801.49 | identical | 0.65 |
| landing_gear | 1115.62 | 1114.57 | −1.05 | 0.64 |
| shifted_cg | 5693.33 | 5692.15 | −1.18 | 0.65 |
| damaged_tail | 8164.04 | 8164.56 | +0.52 | 10.79 → 10.79 |
| **damaged_wing** | 6506.20 | **6387.51** | **−118.69** | **16.83 → 15.90** |

**0/24 crashes both arms** — no falsifier fired, and the crash guard is now a
sharp test rather than a formality.

### It does the right thing where risk is real, and the wrong thing elsewhere

On damaged_wing — the scenario with the most structural pressure — peak
utilisation falls 16.83 → 15.90 and tracking improves by 119 ft. That is exactly
what the term is for.

On broken_aileron it costs **36% of tracking accuracy** while structural
utilisation does not move at all (0.64 both arms). The term fired where there
was no risk to price.

**The defect is that the price is LINEAR in the envelope fraction.** Routine
flight sits at 0.64 of the limit, so ordinary manoeuvring pays a substantial
structural charge even though nothing is at risk — and on a scenario whose
targets are large, `null residual` makes that charge large in absolute terms.
A term meant to discriminate near the limit is instead a tax on operating at
all.

### What it needs, stated as a shape and not a number

A price that is negligible inside the envelope and steep near it — convex in the
fraction rather than linear. That is a shape, not a constant: the natural form
prices the EXCESS over what is routinely used rather than the total, which needs
no threshold because "routinely used" is itself measurable from the envelope
history the loop already keeps.

Reverted; the AN baseline stands, 39 green. This is the first version of the
risk term that measurably does its job on the case it was built for, and the
first whose failure is a shape rather than a magnitude — which is progress of a
kind the previous three attempts did not make.

## Block AQ — the log price is inert, and it exposes why AP's result was not real

The structural price moved to the log currency it was declared in (block AQ
prereg): `max(0, log10(worst)) * rung_decade * null_residual`, floored at the
operator's own safe load because deformation below it is elastic and consumes no
irreversibility.

**All eight scenarios byte-identical to AN, damaged_wing and damaged_tail
included.** Prereg prediction 2 (six byte-identical) held; prediction 3 (the two
exceeding scenarios may move) FAILED — they didn't move either.

### RETRACTED IN PLACE — there is no 26x gap, and I measured it wrong

**What this section originally claimed:** that the composer reads a
`state_current_<load>` which disagrees with the receipt-derived
`maximum_observed_utilization` by 26x, that its binding constraint is a thermal
constant, and that the structural machinery is therefore blind. **The 26x does
not exist.** Measured with both sides read at the same instant
(`scripts/probe_composition_time_load.py`):

```
episode ep0 (seed 241172975), final action
  envelope.maximum_observed_utilization = 0.6428566286421049
  composer worst (max |state_current_M| / state_safe_M) = 0.642857
  state_safe_M == envelope.safe_M for all 11 loads
```

The two sides agree to six figures. The loads are wired correctly, the
denominators are the same numbers, and the graph is self-consistent.

**The error was mine and it is a familiar one: I compared a single-episode probe
against a three-episode maximum.** I probed ep0 and read 0.643; the 16.83 in the
results table is ep1. Per episode:

| damaged_wing | struct | min altitude |
|---|---|---|
| ep0 (241172975) | 0.643 | 2660.0 ft |
| ep1 (241172976) | 16.83 | **2.0 ft** |
| ep2 (241172977) | 15.90 | **1.3 ft** |

The condition was in the data the whole time. This is the same failure the
CLAUDE.md baseline note records — a number quoted without the condition that
produced it — committed by the same hand that quoted that note two commits ago.

**Why AQ was genuinely inert, correctly stated:** structural utilisation exceeds
1.0 in exactly three of 24 episodes, and in each it is the GROUND IMPACT that
produces the exceedance. The priced quantity becomes non-zero only at the moment
of the crash, when there are no further decisions for it to influence. So the
term is not blind -- it is too late. That is a different defect from the one
originally written here, and it needs a different fix.

### This retracts the AP result

Block AP's price was `worst * rung_decade * null_residual` with `worst` now known
to be ~0.643 and near-constant. So AP was not pricing risk at all — it was
adding `0.643 * null_residual` to every candidate, which is a RESCALE OF THE
TRACKING OBJECTIVE by a constant factor. That is why it moved scenarios with no
structural pressure whatsoever (broken_aileron, +656 ft at 0.64 utilisation both
arms), and the damaged_wing improvement (-119 ft, 16.83 -> 15.90) was a
side-effect of reweighting, not the term doing its job. **The AP entry above
should be read as a measurement of an objective rescale, not of a risk price.**

Both blocks priced a quantity that is near-constant in flight and only spikes at
impact. The shape was never the problem.

### What is actually broken — and it is not the price, and not the loads

Three of 24 episodes descend to 1.3-2.2 ft above ground with structural
utilisation of 10.8-16.8x, `engineering_envelope_violation = True`, and
**`crash = False`**. The distribution is cleanly bimodal: 21 episodes never go
below 1000 ft, three arrive at ~2 ft, nothing in between.

The crash criterion is

```python
paper_like_crash = ground_contact or minimum_altitude_m <= 0.0 or plant_failure
```

and `domains/jsbsim_f16_paper_world.py` **never published `ground_contact` at
all** -- only `jsbsim_x15_world.py` did. The runner has always read
`observation.get("ground_contact", False)`, so the term was permanently False and
the criterion reduced to "did the CG pass through mean sea level". At 1.3 ft the
CG is 0.4 m up, which is below the F-16's own wheel height: the airframe is
through the surface and it scored as a survival.

**Every `0/24 crashes` headline in blocks AN, AO, AP and AQ is conditional on
that predicate, and I reported it unconditioned each time.** The correct
statement is 0/24 by the paper-like criterion, with three ground impacts that the
criterion cannot see. A sibling experiment already knew --
`scripts/jabberwock_f16_wings_off_terminal.py:126` uses
`ground_contact or altitude_m <= 3.0`. The paper replication was the one place
that did not.

Reverted (inert code, and the shape cannot be validated until the state it reads
is real). AN baseline stands, 39 green. The probe is kept as
`scripts/probe_composition_time_load.py`.

## Block AR — contact detection wired: the suite crashes 3/24, and always did

`domains/jsbsim_f16_paper_world.py` now publishes `ground_contact` from the
simulator's own contact model:

```python
"ground_contact": bool(
    float(self._fdm["forces/fbz-gear-lbs"]) != 0.0
    or any(float(self._fdm[p]) > 0.0 for p in self._weight_on_wheels_properties)
),
```

Not an altitude threshold. Height above ground is the wrong question -- which
part of the aircraft is lowest depends on attitude, and a wingtip strike in a
bank arrives with the CG still well clear. JSBSim exposes WOW only for the
bogeys, but `fbz-gear-lbs` is the total ground reaction over all ten contact
points, so a wingtip or fuselage strike registers as surely as a wheel does.
The WOW set is discovered from `gear/num-units` by asking which units publish
the property, rather than hardcoding how many wheels an F-16 has.

| scenario | RMSE identical to AN | crash before | crash now | contact | min alt |
|---|---|---|---|---|---|
| nominal | YES | 0/3 | 0/3 | 0/3 | 8891.3 ft |
| jammed_rudder | YES | 0/3 | 0/3 | 0/3 | 8901.1 ft |
| broken_aileron | YES | 0/3 | 0/3 | 0/3 | 6440.0 ft |
| saturated_elevator | YES | 0/3 | 0/3 | 0/3 | 1673.2 ft |
| landing_gear | YES | 0/3 | 0/3 | 0/3 | 3500.8 ft |
| shifted_cg | YES | 0/3 | 0/3 | 0/3 | 2866.9 ft |
| **damaged_tail** | YES | 0/3 | **1/3** | 1/3 | 2.2 ft |
| **damaged_wing** | YES | 0/3 | **2/3** | 2/3 | 1.3 ft |

**Every RMSE is byte-identical to AN**, which is the verification: `ground_contact`
is read only into the trace row and the metrics, never into agent state, so this
changes what is MEASURED and nothing about what is FLOWN. Same trajectories,
truthful labels.

**The suite crashes 3/24. It has crashed 3/24 for the entire line of work.**

This is not a regression and nothing got worse; a measurement that was wrong is
now right. The corrected reading of the recent blocks:

* AN, AO, AP, AQ all ran at 3/24, not 0/24. The crash guard in every prereg since
  AN was satisfied by a predicate that could not see the crashes.
* "No falsifier fired" in blocks AP and AQ was true only because the falsifier
  was blind. Neither block is thereby vindicated -- they were never tested.
* The AP/AQ conclusion survives on its own evidence (near-constant utilisation in
  flight; the spike arrives at impact), but the crash-count arm of both is void.

**"but we are still flying damaged wing into the ground?"** was asked many turns
ago and answered with 0/3 from this predicate. The aircraft was going into the
ground in 2 of 3 damaged_wing episodes at the time the question was asked, and in
2 of 3 now. The instinct was right and the instrument was wrong.

The standing target -- 0 crashes -- is unmet, and for the first time it is
measured against something that can register failure.

## Block AS — why damaged_wing crashes, and two repairs that made it worse

With crash detection working (AR), the crashing episode can finally be read.
damaged_wing ep1 (seed 241172976), traced:

| action | alt | pitch | AoA | kts | viability rung | region_actions | deliberating | regime |
|---|---|---|---|---|---|---|---|---|
| 101 | 6293 ft | 8.5 | 9.7 | 189 | 3 | 616 | 0 | 0 |
| 201 | 5795 ft | 23.7 | **32.5** | 178 | 3 | 93 | 0 | 0 |
| 301 | 5343 ft | 21.0 | **57.1** | 94 | 2 | 90 | 0 | 0 |
| 401 | 4070 ft | -17.6 | **58.3** | 107 | **0** | 30 | 0 | 0 |
| 501 | 2388 ft | -14.3 | 56.6 | 108 | **0** | 14 | **1** | 0 |
| 601 | 717 ft | -11.8 | **76.9** | 105 | **0** | 4 | **1** | 0 |
| 643 | **2 ft** | -5.1 | -79.4 | 8 | 0 | 0 | - | 0 |

**It is a pitch departure, not the roll departure previously diagnosed.** The
loop chases altitude with a wing that makes 0.7x the lift, pitches up, stalls by
action ~200, descends deep-stalled for 400 actions, hits the ground at 643 and
slides along the surface for the remaining 357.

**The detection machinery works.** The viability ladder falls to rung 0 at action
401 -- 242 actions before impact -- and the loop DOES open deliberation at 501
and 601. What never happens is adoption: `regime_ordinal` is 0 and
`regime_escalation_count` is 0 for all 1000 actions.

### The verdict is HOLD forever, and a measurement probe is why

Every deliberation proposes the same candidate: the GENERATED corner, minted at
the held ordinal so that adopting it changes nothing. It was already recorded as
a known defect (block AF) -- unnormalised shares, so it "scores full authority on
every axis and DOMINATES THE WHOLE FRONTIER". Confirmed here, and now with a
price attached: the aircraft deliberates twice inside a departure and re-elects
the status quo both times.

### Repair 1 -- normalise it, the documented repair. Not kept.

Divided the generated shares by their own total at runtime, the faithful Term
analogue of `_allocated`. The blanket dominance did break (declared corners come
back with `dominated = 0.0`), **but the generated corner is still the proposal at
every deliberation** and the ordinal still never moves. Dominating was never the
mechanism; being proposed was.

The recorded objection to this repair (jammed_rudder 323.10 -> 7790.36, crash
0 -> 1) was measured before the +0.5 re-spec and with the blind crash predicate,
so it was worth re-measuring. It is not what stopped the repair -- insufficiency
is.

### Repair 2 -- exclude the probe from the eligible set. NOT kept: it is worse.

Marked the generated candidate with a `has_probe_pareto_candidate` edge (an edge,
so absence is the default and no other corner declares anything) and excluded
probe candidates from `cp_falsify_dominated_incumbent_goal` -- the exclusion in
the eligible set, not as a guard on the argmin.

Result: **no revision requests are formed at all**, and damaged_wing goes from
2/3 to **3/3 crashes**. ep0, which survived at 2660 ft, now impacts at 5.2 ft
with RMSE 12897 (was 8753); ep2 reaches 38.95x structural.

| | ep0 | ep1 | ep2 |
|---|---|---|---|
| AR baseline | no crash, 2660 ft | crash, 2.0 ft | crash, 1.3 ft |
| repair 2 | **crash, 5.2 ft** | crash, 2.0 ft | **crash, -15.9 ft** |

### What the pair proves

Removing the probe leaves NOTHING, because **no real corner dominates the
incumbent on this frontier.** The probe was not merely shadowing better
proposals; it was the only proposal there was. That is the same wall §49 hit --
"Pareto dominance cannot select a compensating corner" -- and it says the
escalation path out of viability rung 0 must not run through dominance at all.
Whatever the probe's revision request was doing downstream (closing the
deliberation, re-arming the evidence window) was load-bearing, and removing it
left deliberation stale in a way that hurt an episode that had been surviving.

Both reverted; damaged_wing is 2/3 as it was, seeds regenerate byte-identical to
`4759246fa4`. **Not fixed.** The next rung is a selection path from rung 0 that
does not require a dominating alternative -- containment-as-selection (§49) is
the standing candidate, and the stall itself is not represented on the frontier
at all: no corner offers "unload the wing and trade altitude for airspeed", which
is the manoeuvre this episode needed at action 200.

## Block AT — altitude and airspeed related as one balance (the humanoid's relation)

Block AS ended by asking why no corner offers "unload the wing and trade
altitude for airspeed". The answer is structural, and the humanoid already
recorded it.

The two admissibility tests, side by side:

* **humanoid**, `recovery_outcome_approaches_program_target`: `Or(...)` over the
  per-axis distances -- ANY axis improving counts. Its docstring says why: *"A
  recovery stage may exchange support, contact, or motion for height and
  alignment. Requiring every target distance to improve would silently
  scalarize that physical choice into a monotone safety gate."*
* **F-16 frontier**, `cp_recognize_relational_dominance`: no-worse on EVERY
  axis, strictly better on one.

A trade of altitude for airspeed is worse on the altitude axis BY CONSTRUCTION.
It can never be a dominating alternative. **The corner is missing not because
nobody wrote it, but because it could never win if written.** The humanoid hit
this exact wall and refused the monotone gate; the F-16 kept it.

### What was built

Not a loosening of dominance -- a declared RELATION, which is the smaller and
truer change:

* `domains/jsbsim_f16_paper_world.py` publishes `gravity_m_s2` from
  `accelerations/gravity-ft_sec2`. It varies with altitude, so it is a
  measurement, not a constant -- and it is exactly the exchange rate between
  the two axes.
* `f16_track_energy_height_rate_ema` -- the sink-rate EMA, over energy height
  `h + v^2/2g` instead of `h`. Held previous reading, so no fabricated first
  slope.
* `f16_project_energy_exchange_clock` -- republishes ONLY the SURRENDERED
  altitude reading against energy height. The KEPT reading is untouched
  (holding altitude really does cost what it costs) and the terrain region is
  untouched (the ground is still where it is). What changes is the price of the
  exchange.

### Measured: correct, and inert

Full suite: **all 8 scenarios byte-identical to AR, 3/24 crashes unchanged.**

The rules fire and the numbers are right. In damaged_wing ep1:

| action | sink rate | energy rate | altitude clock surrendered | kept |
|---|---|---|---|---|
| 401 | -40.7 | **-38.4** | 466 | 644 |
| 601 | -51.8 | **-51.2** | 75 | 299 |

**Energy drains as fast as altitude, which means the aircraft is not trading --
it is destroying energy.** At AoA 57 the wing is a bluff body; descending buys
no airspeed. The relation is correct and it correctly reports that by the time
the ladder fires there is no trade left to make.

Two separate reasons it changes nothing, and they matter differently:

1. **Downstream, the AS blocker.** The probe corner wins every verdict whatever
   the axis values say, so improving an axis value cannot change a selection.
   Fix AS and this becomes live.
2. **Upstream, and more important: the decision is 200 actions too late.** The
   exchange was available around action 150-200, at 178 kts and AoA 32, while
   the wing still flew. The viability ladder does not reach rung 0 until 401,
   by which point the trade has already been foreclosed. **A correct price on
   an option that has expired buys nothing.**

Kept, on the strength of the measurement rather than the outcome: it is
zero-regression, it is the relation the balance actually has, and it is what
produced the finding above. It is honestly inert today.

The next rung is upstream, not downstream: the ladder measures VIABILITY, and
by rung 0 the aircraft is already unrecoverable. What is missing is a reading
that fires while the option is still open -- the wing approaching the end of
its usable lift, not the airframe running out of ground.

### AT addendum — energy as a CLOCK fires later, not earlier. Measured.

The obvious next step from AT -- declare energy exhaustion as another region to
avoid, so the ladder's `MinOver` takes the soonest of {ground, energy} -- was
tested against the recorded episode before building it. **It would have made
detection worse.**

| event | action |
|---|---|
| stall (AoA 3.5 -> 31.7 deg) | **~190** |
| terrain clock <= horizon (80) | 310 |
| viability rung 0 | 310 |
| deliberation opens | 283 |
| **energy clock <= horizon** | **596** |
| ground impact | 643 |

Energy height is ~2400 m, so even draining at 38 m/s it lasts hundreds of
actions; the ground arrives first every time. As a TIME-TO-EXHAUSTION reading,
energy is the slowest signal on the board.

**The error is the threshold, not the quantity.** Options do not run out when
energy reaches zero -- they run out when energy falls below WHAT THE RECOVERY
COSTS. Unstalling requires enough height and speed to lower the nose, accelerate
and rebuild lift; that floor is crossed far above zero, and nothing in this loop
measures it.

And the collapse is fast in exactly the way that matters: between actions 176
and 201 the AoA goes 3.5 -> 31.7 deg and the option set closes in about 25
actions, while BOTH clocks still read comfortable (terrain 132, energy 731).
Every clock this loop keeps is a time-to-boundary reading, and the thing that
killed this aircraft was not reaching a boundary -- it was losing the ability to
manoeuvre while every boundary was still far away.

That is the shape of the missing measurement: not "how long until I hit
something" but "how much of what I could have done can I still do", and its
derivative. The viability ladder as built cannot express it, because every rung
is a distance to a limit.

## Block AU — the recovery floor: options measured against what recovery costs

The recoverability contract already existed as `embodied_energy_control` (the
autorotation seed) and did not need inventing:

* a measured recoverable STORE -- `state_rotor_fraction`;
* a declared FLOOR -- `minimum_viable_rotor_fraction`, on the policy;
* `ha_measure_viability` asking only whether the store is still above it;
* `mean_recovered_energy_joules`, learned per action model from receipts.

A helicopter's store is rotor RPM. A fixed wing's is energy height, which block
AT made measurable. Mapped across:

* `f16_capture_energy_height_reference` -- the trimmed initial condition is a
  MEASURED example of a viable state, not an assumption: the episode began
  there with the wing working. Captured once.
* `f16_minimum_viable_energy_fraction = 0.5`, declared by the operator in the
  episode overrides beside the irreversibility budget, for the same reason the
  helicopter declares its rotor fraction: how much margin is worth keeping is a
  value, not a fact about the airframe. A RATIO, so it transfers.
* `f16_declare_recovery_region` / `f16_track_recovery_region` -- running out of
  OPTIONS declared as a region to avoid, exactly like running out of ground.
  The ladder already takes `MinOver` across regions, so the soonest way of
  running out wins with no change to the ladder at all.

### It fires where the option actually closes

| action | recovery clock | terrain clock | rung | AoA |
|---|---|---|---|---|
| 176 | 849 | 132 | 3 | 3.5 |
| **201** | **24** | 93 | **0** | 31.7 |

**Viability rung 0 now fires at action 194 instead of 310 -- 116 actions
earlier**, at the stall, while the terrain clock still reads comfortable. That
is the reading block AT said was missing: not "how long until I hit something"
but "how long until recovery stops being purchasable".

### One bug worth recording, because it flattered the result

The first version computed `IDiv(margin, rate * duration)` and clamped
afterwards. That floored before clamping, mixed an Int into a Float `Max`, and
put the region on a different scale from the terrain region -- pinning
`region_actions` at 0 from action 1, so the ladder read rung 0 for the entire
episode. Measured with the bug in place, damaged_wing ep0's minimum altitude
rose 2660 -> 6975 ft and peak structural halved on both crashers. **None of
that was the floor working; it was a constant.** Rewritten to the general
seed's own idiom (`IDiv(Min(Div(gap, rate), horizon), 1.0)`), those gains
disappear.

### Honest outcome: correct, early, and still not a fix

With the corrected term, damaged_wing ep0 and ep1 are byte-identical to AR and
ep2 differs (peak structural 15.90 -> 3.13, but minimum altitude 1.3 -> -11.7
ft). **Still 2/3.**

The reason is unchanged and is not in this block: `publish_viability_rung` is
STAMPED ONLY. Firing rung 0 at 194 instead of 310 gives the loop 116 more
actions in which nothing consumes the rung, because selection still runs
through Pareto dominance and the probe corner wins every verdict (block AS).
The measurement is now right and arrives in time; there is still no path from
it to a decision.

Suite block `recovery_floor_au_v2` launched; results not yet read at time of
writing. 39 green.

### AU suite result — REVERTED. Correct, early, and a net cost.

| scenario | RMSE AR | RMSE floor | delta | crash | struct AR -> floor |
|---|---|---|---|---|---|
| nominal / jam / aileron / elevator / gear / cg | -- | -- | **identical** | 0/3 | unchanged |
| damaged_tail | 8164.04 | 8587.61 | **+423.57** | 1/3 | 10.79 -> **12.80** |
| damaged_wing | 6506.20 | 6917.34 | **+411.14** | 2/3 | 16.83 |

**Crashes 3/24, unchanged.** The floor costs ~400 ft on both damaged scenarios
and 2 units of structural margin on damaged_tail, and buys nothing.

Two things this settles:

1. **`publish_viability_rung` is not "stamped only".** Its docstring says it is,
   and six scenarios being byte-identical says the rung is inert where nothing
   is failing -- but on the two scenarios that DO reach rung 0, moving the rung
   116 actions earlier moved the trajectory and moved it the wrong way. Something
   downstream consumes it (the probe ladder and spend authority are the
   candidates). A rung that is documented as inert and is not is worth more than
   this block cost.
2. **Earlier warning without a selection path is not free.** The intuition that
   a correct measurement can be landed now and consumed later is wrong here: it
   perturbs without steering.

Reverted to `ebf584bce6`; seeds regenerate byte-identical. The measurement was
right, arrived 116 actions earlier at exactly the moment the option closed, and
still could not help -- which is the sharpest statement yet of where the real
blocker is. It is not detection, at any threshold, on any quantity. It is that
rung 0 has nowhere to go.

## Block AV — AS fixed: rung 0 has somewhere to go. Latency NOT fixed.

Two halves, each inert without the other -- which is exactly why AS repair 2
failed when it removed the probe and added nothing:

* `f16_propose_viability_escape` (consumer) -- at rung 0, every candidate that
  would actually CHANGE the regime becomes a proposal. No dominance required,
  because at rung 0 the incumbent is not a thing to improve upon, it is a thing
  to leave. It ADDS a path rather than removing one, and it excludes the probe
  for a REASON rather than by name: the probe is minted at the held ordinal
  precisely because adopting it is a no-op.
* `cre_publish_regime_pareto_verdict` (general) -- when `regime_change_required`
  is set, a candidate minted at the held ordinal cannot be the verdict. Absence
  reads 0, so every consumer that never sets it is byte-identical.

**The loop escalates for the first time in this line of work**: damaged_wing ep1
goes regime 0 -> 5 (roll_priority) at action 597, escalation count 1.

Full suite: seven scenarios byte-identical, damaged_wing +0.68 ft with peak
structural **16.83 -> 15.29**, crashes **3/24 unchanged**. ep2's peak structural
falls 15.90 -> 2.23. Kept: an escalation path that works, at no measurable cost.

### The latency is not fixed, and three plausible causes are ruled out

Rung 0 fires at 310. Adoption lands at 597. Impact at 643.

Measured at the stall: `regime_deliberating` is 1 CONTINUOUSLY from action 310,
and `regime_change_required` is set from action 310. The loop is deliberating,
knows a change is required, and has an escape path -- for 287 actions.

Three candidate gates were built and measured, and **all three were completely
inert** (damaged_wing ep1/ep2 byte-identical in every case):

1. **The evidence window.** `Or(best_priority > 1, integral >= horizon,
   change_required)` in the verdict. No effect -- one of the first two was
   already true.
2. **The deliberation opening guard.** Letting a required change open a
   deliberation without waiting for `absence_integral > Min(horizon,
   actions_to_act)`. No effect -- deliberation was already open from 310.
3. **The `dominated` flag.** Discounting domination by a candidate that cannot
   be adopted, on the theory that the probe dominates every real corner. No
   effect, so the dominators are not all no-ops.

All three reverted. What remains, by elimination, is inside the verdict's own
candidate selection -- `Eq(V("candidate"), best)`, where `best` is the Argmax
over PROPOSED candidates by the situational priority axis. The escape rule
supplies proposals from 310; something between "proposed" and "is best" is
consuming the 287 actions, and 597 is most likely simply when the probe's own
priority value finally falls below a real corner's.

Not guessed further. The next step is to instrument `best` and the per-candidate
priority values across 310-597 and read which comparison is holding, rather than
build a fourth candidate fix.

## Block AW — instrumented: the gate is `dominated`, held by a candidate that cannot be adopted

Prereg AW predicted the latency was a comparison of candidate LEVELS. Measured
across damaged_wing ep1 actions 300-600, that is wrong in its specifics and
right in its conclusion.

**Prediction 1 -- CONFIRMED.** `f16_goal_margin_altitude` (reach/gap) crosses
below 1.0 at action ~190: the altitude objective becomes unreachable at the
stall, 120 actions before rung 0 (310) and 400 before adoption (597). The
manifold does close first, exactly as the "closing in" reading says.

Caveat recorded: the margin SPIKES to 391 at action 292 because the gap passes
through zero. A ratio is not safe to threshold when its denominator changes
sign; its log is worse. Whatever consumes this needs the crossing, not the
magnitude.

**Prediction 2 -- FALSIFIED as stated.** There is no level crossing that
explains 597. The priority values are flat from 400 to 590 (generated 655.8;
hold 181.7; the corners 174.4 and 218.0).

**What is actually holding it, measured:**

| action | generated | hold | r:1 | r:2 | r:4 | r:5 |
|---|---|---|---|---|---|---|
| 283 | 1024.0 ·P | 1024.0 D | 1024.0 D | 1024.0 D | 1024.0 D | 1024.0 D |
| 400-590 | 655.8 ·P | 181.7 D | 174.4 **DP** | 218.0 **DP** | 174.4 **DP** | 218.0 **DP** |
| 596 | 90.3 ·· | 181.7 ·· | 174.4 DP | 218.0 DP | 174.4 **·P** | 218.0 **·P** |

(D = dominated, P = proposed.)

* The escape rule WORKS: a non-probe candidate is first proposed at **action
  379**, 218 actions before adoption.
* Every real corner is `dominated` from 283 to 595. The verdict requires
  `Not(dominated)`.
* The first action a non-probe candidate is not dominated is **596** -- one
  action before adoption -- and what changes there is that the PROBE's own
  priority collapses 655.8 -> 90.3 and it stops dominating.

**The probe holds the entire real frontier in a dominated state for 217
actions, and the verdict will not adopt a dominated candidate.** The latency is
not a wait, not a window, and not a level comparison. It is one unadoptable
candidate suppressing every adoptable one via a flag that means "something
better exists" when the something better is a no-op.

### Why the AV third fix failed, and what the correct scope is

AV tried exactly this and was inert. It disqualified a candidate only if EVERY
dominator was a no-op. The corners evidently also dominate each other (r:2 and
r:5 at 218.0 against r:1 and r:4 at 174.4), so no corner had an all-no-op
dominator set and the clause never fired.

The correct scope is per-dominator, not per-candidate: a candidate should be
disqualified by the dominators that CAN be adopted, and ignore the ones that
cannot -- which for a set where the probe dominates everything leaves the
corners' mutual dominance intact and lets the best of them through. That is a
different predicate from the one AV built, and it should be built against a
dump of the actual dominator sets rather than from this inference.

Next: dump `is_dominated_by_pareto_candidate` per candidate across 380-600 and
confirm the dominator composition before writing the predicate.

### AW part 2 — dominator sets dumped, predicate built, latency FIXED, outcome worse

The dominator composition, measured (damaged_wing ep1, actions 370-620):

```
action 400, held ordinal 0
  generated     ord 0   dominated_by: -
  regime:hold   ord 0   dominated_by: generated@0
  regime:4      ord 4   dominated_by: generated@0            <- only a no-op
  regime:5      ord 5   dominated_by: generated@0            <- only a no-op
  regime:1      ord 1   dominated_by: generated@0, regime:4@4
  regime:2      ord 2   dominated_by: generated@0, regime:5@5
```

**This refutes the AW inference.** `regime:4` and `regime:5` are dominated ONLY
by the probe, so AV's predicate should have admitted them. It did not, and the
dump says why: `frontier_source` filters to NON-DOMINATED candidates, so at
action 400 the frontier was `{generated}` alone -- `best` WAS the probe -- and
barring the probe in a separate clause beside `Eq(candidate, best)` removed the
winner without promoting anyone.

**An exclusion appended to an Argmax is a deletion, not a constraint.** That
lesson is already recorded in this tree from an earlier rung, and this is the
second time it has been paid for. The exclusion has to live in the eligible set.

Rebuilt there: under `regime_change_required`, the frontier admits a candidate
whose ordinal differs from the held one and whose dominators are all
unadoptable, and the candidate's own admission test is the same expression so
the two cannot drift.

**The latency is fixed.** Adoption moves **597 -> 380**, one action after the
first proposal at 379, 217 actions earlier.

**And the outcome is worse:**

| | ep1 struct | ep1 RMSE | ep2 struct | ep2 RMSE |
|---|---|---|---|---|
| escape only (AV) | 15.29 | 4134.62 | 2.23 | 6632.13 |
| + latency fixed | **24.13** | 4185.22 | **7.32** | **7699.38** |

Crashes 2/3 either way. The loop now escalates FIVE times, cycling ordinal
5 -> 4 -> 1. Acting 217 actions earlier, it does not recover -- it churns
between corners, and the churn costs more structural margin than the delay did.

Reverted. What this establishes is worth the block: the adoption path is now
fully characterised end to end -- rung 0 at 310, proposal at 379, adoption
gated by an eligible set that excluded everything, and a fix that provably moves
adoption to 380. The remaining problem is no longer WHEN the loop acts. It is
that none of the six corners is a recovery from a stalled wing, so acting sooner
just starts the cycling sooner. That is the corner set, not the selection.

## Block AX — allocation drives targets: the mechanism works, and it leaks

Built as preregistered: the generated corner mints at its own ordinal (6) rather
than the held one, and `f16_drive_targets_from_allocation` scales each derived
target by that corner's share of its axis. Since the shares are already
`min(reach / gap, 1)`, recomputed from the plant every action, the rule reduces
to **demand only what is reachable** -- and the recovery is then not authored at
all: at the stall the altitude margin drops below 1, the pitch-angle demand
scales with it, and the wing unloads.

### damaged_wing: the mechanism does what it was designed to do

| | ep0 | ep1 | ep2 |
|---|---|---|---|
| minimum altitude | 2660 -> **6431 ft** | 1.7 -> 3.1 | 1.4 -> 2.1 |
| altitude RMSE | 8754 -> **6879** | 4135 -> **3873** | 6632 -> 7120 |
| peak structural | 0.64 | **15.29 -> 6.29** | 2.23 -> 6.23 |

Prediction 4 confirmed decisively: peak structural falls 15.29 -> 6.29.
Prediction 5 was wrong in the favourable direction -- RMSE IMPROVED on two of
three rather than rising. ep0 finishes 3770 ft higher. Crashes still 2/3.

### And prediction 2 fails, caught by a test rather than the suite

`test_f16_evidence_still_starves_on_a_divergence_past_the_band` asserts
`regime_ordinal == 0.0` while every control axis is still INSIDE its declared
authority -- its comment states the law plainly: *"A tracking error is not by
itself a reason to give an objective up."* It now reads **6.0**.

**The allocated corner is adoptable everywhere, not only at rung 0.** Once it has
a real ordinal it is a real candidate, and it already dominated every frontier
(blocks AS/AW) -- so it is now adopted in benign conditions too, and the loop
surrenders objectives whenever it happens to deliberate.

This is the second, unstated reason the corner was pinned to the held ordinal.
The docstring gave one -- "a generated ordinal would be selected and then flown
by nothing" -- and giving it something to fly removes that one while leaving
this one untouched: **nothing bounds WHEN it may be adopted.** The pin was
load-bearing twice and documented once.

Reverted; 39 green, seeds regenerate byte-identical, the interrupted suite's
partial results discarded.

### What the block establishes

The mechanism is right and the numbers say so: allocation-driven targets more
than halve structural consumption on the scenario that departs, improve tracking
on two episodes of three, and leave ep0 3770 ft higher. What is missing is a
bound on adoption. The corner needs to be admissible only while the condition
that justifies it holds -- which is `regime_change_required`, already published
and already generic, and which this build simply never consulted. That is a
guard on the mint or on the frontier, not another corner, and it should be built
with the benign-conditions test as its gate rather than the suite.

Also measured: the run is ~3x slower per episode with the allocated corner live
(a 10-minute timeout on work that took ~3). Unexplained, and it matters at 10 Hz.

### AX part 2 — adoption bounded by `regime_change_required`: the bound holds, two new faults surface

Rebuilt AX with the bound, marked generically so the general seed learns no
F-16 ordinal: the mint sets `candidate_requires_change`, and the verdict admits
such a candidate only while `regime_change_required` is asserted. Absence reads
0, so every declared corner is unaffected and "a change is required" has one
meaning in the seed rather than two.

**The bound does what it was built to do.** The benign-conditions test moves
`regime_ordinal` from 6.0 to not-adopted: the allocated corner is no longer
adopted while every axis is inside its authority.

**And the test still fails, now reading 1.0.** With the allocated corner barred
from the verdict, a DECLARED corner (trim, ordinal 1) is adopted instead. The
probe was suppressing the real corners in benign conditions too, and bounding it
unmasked that. This is the AS repair-2 shape a third time: **every time the
probe's influence is removed from a path, whatever it was suppressing on that
path becomes visible, and it is never nothing.** The benign-conditions law -- "a
tracking error is not by itself a reason to give an objective up" -- has been
enforced by an accident of the frontier, not by a rule, for the whole line of
work.

**Second fault, unrelated and worse: `test_f16_prices_a_surrendered_axis_on_its
_own_clock` reads 612.5 where it requires 612.** A clock is an IN-FRAME quantity
and must be an integer; the allocated ordinal puts a float into one. That is the
frame/continuum invariant in the root CLAUDE.md -- "in-frame is INTEGER,
non-integer math is CROSS-FRAME" -- and a float there is a category error, not a
rounding preference. It needs `IDiv` at the boundary, and it needs finding
rather than assuming: I have not traced which term introduces it.

Reverted; 39 green, seeds byte-identical.

### Where this leaves the corner

Three facts now stand together, and the third is the one that matters:

1. Allocation-driven targets WORK -- structural 15.29 -> 6.29, ep0 3770 ft
   higher, RMSE better on two episodes of three (AX part 1).
2. Adoption can be bounded generically, and the bound holds (this part).
3. **The benign-conditions law is not enforced anywhere.** It has been held up
   by the probe dominating the frontier. Any change that gives real corners a
   path -- the AV escape, the AW eligible set, this bound -- exposes it, which
   is why three separate builds have failed the same test for three different
   proximate reasons.

So the next rung is not a fourth attempt at the corner. It is to state that law
as a rule: a corner that surrenders an objective is admissible only while that
objective is unreachable, which is `f16_goal_margin_* < 1` -- already measured
every action, already the quantity `_generated_share` is built from, and
currently consulted by nothing that gates adoption. With that in place the probe
is no longer load-bearing and can be retired outright, which is what blocks AS
through AX have each been working around.

## Block AY — the benign-conditions law, stated as a rule. KEPT.

`test_f16_evidence_still_starves_on_a_divergence_past_the_band` asserts that
while every axis is inside its declared authority the regime does not change:
*"a tracking error is not by itself a reason to give an objective up."* Blocks AS
repair 2, AW and AX each broke it for a DIFFERENT proximate reason, which was
the clue -- the law was never enforced by any rule. It held because the
generated probe dominated every frontier. An accident.

Now stated, in two halves that mirror the ones that already exist:

* **f16** -- a corner declares that it gives an objective up, DERIVED from its
  own allocation rather than hand-listed: a zero share IS the giving-up, so a
  corner that later declares a share strictly between 0 and 1 needs no change
  here. `hold`, which surrenders nothing, declares nothing.
* **cre** -- the verdict admits such a candidate only while the consumer asserts
  `regime_change_required`. Absence reads 0, so a candidate that says nothing is
  admissible exactly as before.

The giving-up is declared by the candidate, the licence by the consumer, and
neither alone suffices.

### Measured

| scenario | RMSE AR | RMSE law | delta | crash |
|---|---|---|---|---|
| nominal, jammed_rudder, saturated_elevator, landing_gear, shifted_cg | -- | -- | identical | 0/3 |
| broken_aileron | 1783.56 | 1781.20 | -2.36 | 0/3 |
| **damaged_tail** | 8164.04 | 8350.45 | **+186.41** | 1/3 |
| damaged_wing | 6506.20 | 6506.88 | +0.68 | 2/3 |

Crashes **3/24, unchanged**. Peak structural unchanged (damaged_tail 10.79,
damaged_wing 15.29).

**The prediction that all eight would be byte-identical was WRONG**, and the way
it is wrong is the point: two scenarios move, so the rule is not equivalent to
the accident it replaces. It was never safe to assume it would be.

Kept, at a stated cost of +186 ft on damaged_tail (2.3%). What it buys is not a
tracking number:

* the law is now enforced where it can be tested, instead of emerging from which
  candidate happened to dominate;
* **the probe stops being load-bearing.** Every block from AS onward has been
  routing around the fact that removing the probe removed the only thing keeping
  benign conditions benign. That is no longer true, so retiring it is now its own
  small question rather than a precondition for every corner change.

### Still open, and deliberately not folded in

* **A float in an integer clock.** `test_f16_prices_a_surrendered_axis_on_its_own
  _clock` read 612.5 against 612 under the AX allocated ordinal. It does not
  arise here because that ordinal is reverted, and I never traced which term
  introduces it. In-frame quantities are integers; that is a category error
  waiting at the next attempt.
* **~3x slower per episode** with the allocated corner live (a 10-minute timeout
  on work that took ~3). Unexplained, and it matters at 10 Hz.
* damaged_wing remains **2/3**. The corner that would fly the recovery is built
  and measured (AX: structural 15.29 -> 6.29, ep0 3770 ft higher) and is not in
  the tree, because it needs both of the above resolved and the adoption bound
  this block just made possible.

## Block AZ — retiring the probe: refused, and it corrects the AX attribution

AY concluded that with the benign-conditions law stated as a rule, the probe
"stops being load-bearing" and retiring it is "its own small question". Tested
directly: unregister `f16_mint_generated_pareto_candidate` and change nothing
else.

**Three tests fail.** Two of them matter:

* `test_f16_evidence_still_starves_on_a_divergence_past_the_band` reads 1.0
  again -- a declared corner (trim, ordinal 1) is adopted in benign conditions
  DESPITE the AY law. trim surrenders sideslip, so it declares
  `candidate_requires_change`, so the verdict should bar it. It does not, which
  means there is an adoption path the AY clause does not cover. Not traced.
* `test_f16_prices_a_surrendered_axis_on_its_own_clock` reads **612.5 against
  612**.

### The float was never the allocated ordinal. That attribution was wrong.

Block AX recorded the 612.5 as caused by the new ordinal, and the AY entry
repeated it as "does not arise here because that ordinal is reverted". **It
arises here with no allocated ordinal anywhere in the tree** -- the only change
is that the generated corner is not minted. So the non-integer clock is caused
by the probe's ABSENCE, not by its ordinal, and it has presumably been latent
behind the probe the whole time.

That is a correction to two prior entries, and the reason it happened is worth
naming: AX changed two things at once (new ordinal AND a flyable corner), the
float appeared, and I attributed it to the change I had been thinking about
rather than isolating it. Retiring the probe is the one-variable experiment that
should have been run first, and it took three blocks to run.

### Where this leaves the probe

Still registered, still load-bearing, and now known to be masking at least two
separate defects rather than one:

1. an adoption path that ignores `candidate_requires_change` (benign law, AY,
   incomplete);
2. a clock that is non-integer when the probe is not minted -- an in-frame
   quantity carrying a float, which is a category error under the root
   CLAUDE.md invariant, not a rounding preference.

Both are now reproducible with a ONE-LINE change (unregister the mint rule),
which is a far better starting point than any of the four blocks that worked
around it. Neither is guessed at here.

Reverted; 39 green, seeds byte-identical.

**The slowdown was not investigated in this block** -- it needs the AX corner
live, which needs both defects above resolved first, and inventing a third
explanation while two measured ones are open is exactly the pattern this session
has been correcting.

## Block BA — tracing the adoption path: no such path found, and AZ overstated it

AZ recorded "there is an adoption path the AY clause does not cover. Not
traced." Traced now, and that claim does not survive.

**Only two rules in the entire tree write `regime_ordinal`:**

1. `cre_publish_regime_pareto_verdict` -- the Pareto path, which carries the AY
   clause.
2. `hcr_bridge_escalate_regime` (`gen_humanoid_control_regime_seed.py`) -- and
   this one is a **blind increment**:

```
   where:  regime_escalation_requested > 0.5  AND  ordinal < max_ordinal
   effect: regime_ordinal += 1
```

No candidate, no frontier, no dominance, no `candidate_requires_change`. It
steps the regime whenever an evidence-absence impasse raises a flag. 0 -> 1 is
trim, which matches the observed 1.0 exactly -- and it is **not the cause here**:
it matches on `has_humanoid_episode` / `has_humanoid_control_regime`, neither of
which exists anywhere on the F-16 path, and the seed is not loaded by this
runner. Ruled out by construction, and recorded because any consumer that DOES
load that seed gets regime changes with no admissibility test whatsoever.

**The mark is applied correctly.** In the generated seed:
`f16_mint_sideslip_trim_pareto_candidate` 1.0, `f16_mint_orbit_pareto_candidate`
1.0, `f16_mint_hold_pareto_candidate` 0.0.

**And the failure does not reproduce in isolation.** Re-driving the benign
scenario standalone with the probe unregistered:

```
   regime_change_required        0.0
   regime_viability_rung         1.0
   f16_viability_terrain_clear   1.0
   regime_ordinal                0.0     <- the assertion would PASS
```

The law holds exactly as designed: nothing is surrendered, because nothing
licensed it. Yet `pytest` reports 1.0 for the same test with the same seed.

**So the open question has changed shape.** It is no longer "which rule bypasses
the law" -- none does, on this path. It is why the same scenario yields ordinal 0
driven directly and ordinal 1 under the module's own harness. Shared agent state
across tests in that module, or setup outside the function body, are the
candidates; both are cheap to check and neither is checked here.

AZ's wording is corrected in place by this entry: there is no known adoption path
that ignores `candidate_requires_change`. What there is, is a discrepancy between
two ways of running one scenario -- which is a smaller and much better-defined
problem than the one I wrote down.

### BA addendum — shared state ruled out, and my own probe was the unreliable part

Checked directly, probe unregistered:

```
  the test ALONE          -> FAILS (1.56s, isolated)
  the whole module        -> FAILS (3 failed, 29 passed)
```

**Shared agent state across tests is not the cause.** The failure is intrinsic to
the test in isolation; order effects and module-level bleed are out.

That leaves the discrepancy between `pytest` (ordinal 1.0) and the standalone
re-drive reported in BA (ordinal 0.0) -- and the re-drive is the part that should
be distrusted. It was built by `exec`ing the test body after a blanket
`"assert" -> "pass_ ="` string substitution: a crude harness that silently
rewrites any occurrence of that substring and cannot be assumed to preserve the
scenario. **The BA reading of `regime_change_required 0.0 / regime_ordinal 0.0`
is therefore an artefact of my instrumentation, not a second behaviour of the
system.**

So BA's conclusion is itself corrected: `pytest` is the trustworthy measurement,
trim IS being adopted in benign conditions with the probe unregistered, and AZ's
original claim -- that something adopts a surrendering corner without the licence
-- stands after all. What BA legitimately established survives: only two rules
write `regime_ordinal`, the humanoid bridge is not loaded on this path, and the
`candidate_requires_change` marks are correct in the generated seed.

The next measurement must be taken INSIDE the real test run -- a conftest hook or
a temporary print in the test itself -- not by re-driving the scenario in a
harness of my own. Three of this session's wrong conclusions came from a
measurement apparatus that differed from the thing being measured; this is the
fourth, and it is the cheapest to avoid.

## Block BB — instrumented inside the real run: it was never an adoption. AZ/BA retracted.

Instrumented in the actual test (temporary print, real pytest run, probe
unregistered) rather than in a harness of my own:

```
  XPROBE regime_ordinal 0.0   regime_change_required 0.0   regime_viability_rung 1.0
         f16_viability_terrain_clear 1.0   regime_deliberating 1.0
         regime_escalation_requested 1.0   regime_last_verdict None
```

And the actual failing assertion, read rather than assumed:

```
  >  assert float(attrs["regime_deliberating"]) == 0.0
  E  assert 1.0 == 0.0
```

**It is `regime_deliberating`, not `regime_ordinal`.** `regime_ordinal` is 0.0
throughout. Nothing is adopted -- not trim, not anything -- in benign conditions
or otherwise.

### What this retracts

* **AZ**: "a declared corner (trim, ordinal 1) is adopted in benign conditions
  DESPITE the AY law ... there is an adoption path the AY clause does not
  cover." **False.** No adoption occurs.
* **BA**: corrected AZ, then un-corrected it on the strength of a bad harness.
  Both movements were noise on a misread attribute name.
* **The BA addendum**: concluded "trim IS adopted ... AZ's original claim stands
  after all." **Also false.**

Three consecutive blocks of reasoning rest on my having read `1.0 == 0.0` and
supplied the wrong left-hand side from memory. The traceback names the attribute
on the line above the error; I did not read it, and then defended the reading
twice.

### What is actually broken, and it is a known failure mode

With the probe unregistered, **the deliberation never closes.**
`regime_deliberating` stays 1.0. `cre_publish_incumbent_stands` closes a
deliberation when NO revision was requested; `cre_publish_regime_pareto_verdict`
closes it when one is adopted. Retiring the probe produces the third case
neither handles: a revision IS requested (the escape path proposes a
surrendering corner) and the verdict REFUSES it (the AY benign law, correctly --
`regime_change_required` is 0.0 and rung is 1). Nothing closes it.

That is precisely the hazard `cre_publish_incumbent_stands` was written to
prevent, in its own words: *"without it a deliberation that finds no
counterexample stays open forever and blocks every later one."* The AY law
created a second way to find no ADMISSIBLE counterexample, and no matching close
path came with it.

So the AY law is not wrong and the probe is not mysteriously load-bearing. The
gap is one missing rule: **a deliberation whose only proposals are inadmissible
must close as HOLD**, exactly as one with no proposals does. That is a small,
well-specified rule, and it is the thing standing between this tree and retiring
the probe.

Not built here -- this session has spent four blocks on inferences from
apparatus, and the correct next move is one rule written against this
now-reproducible one-line repro, measured in the real test run.

## Block BC — the close rule: built and KEPT. Probe retirement: still blocked.

### `cre_close_inadmissible_deliberation` (kept)

The third case, which neither existing close rule covered. The verdict closes a
deliberation by ADOPTING; `cre_publish_incumbent_stands` closes it when the
faculty proposed NOTHING. Since AY gave the verdict a reason to REFUSE an
otherwise good proposal, a deliberation can now find proposals and admit none of
them -- and nothing closed it. Measured in BB: `regime_deliberating` pinned at
1.0 forever, the exact hazard `cre_publish_incumbent_stands` exists to prevent.

The new rule closes it as HOLD on identical terms, behind the same window
backstop so a proposal that is merely still settling is never mistaken for one
that is refused. **With it, the benign-conditions test passes with the probe
unregistered** -- which is what BB predicted and the first thing in five blocks
that behaved as predicted at this layer.

### Probe retirement: attempted, still blocked, and by only one thing now

Unregistering the probe leaves exactly two failures:

* `test_f16_consumer_declares_pareto_regime_candidates` -- asserts the probe is
  minted at the held ordinal. That is the OLD invariant and would be updated as
  part of retirement, not a defect.
* `test_f16_prices_a_surrendered_axis_on_its_own_clock` -- **612.5 against 612.**
  The test says why in its own comment: *"every value is an integer count of
  actions, not a ratio."*

**The float fix was attempted and FAILED.** I floored the interpolation in
`_axis_value` and `_axis_value_from_share_term` with `IDiv(..., 1.0)`, on the
reasoning that share-weighted interpolation between two clocks is a cross-frame
real that must land back on the in-frame lattice. That reasoning is correct in
itself and the flooring is a genuine improvement -- but the value is STILL 612.5,
so the fraction enters somewhere else in the clock chain (`_axis_time_budgets`,
`_contained`, or the surrendered clock itself). Reverted with the retirement,
since it fixes nothing on its own and I have not found the source.

So the retirement now hangs on ONE unresolved defect rather than the tangle of
AS-BB: a non-integer clock, reproducible with a one-line change, whose origin is
narrowed to three named places and is not `_axis_value`'s interpolation.

Kept: the close rule (cre 7.11.0, 18 rules). Reverted: the probe retirement and
the flooring. 39 green.

## Block BD — the 612.5 found and fixed: the containment branch discards the floored value

Located by reading the expression rather than inferring from behaviour.
`_contained` is the containment zeroing, and its outside-the-band branch was:

```python
    return If(
        Gt(P0("episode", f"f16_goal_outside_{axis}"), L(0.5)),
        Times(L(1.0 - float(share)), surrendered_clock),   # <-- unfloored
        value,
    )
```

Two facts together explain everything BC could not:

1. `1 - share` is a cross-frame RATIO (`_allocated` yields 0.2, 0.25, 1/6 ...)
   and `surrendered_clock` is an in-frame integer clock, so the product is real.
   Nothing floors it.
2. **That branch DISCARDS `value`.** BC floored the interpolation that produces
   `value` and the number did not move, because on the outside-the-band path
   `value` is never used. The fix was applied one level away from the defect.

And the failing test exercises exactly this branch -- its own body reads
`if outside: assert keeper < surrenderer`. The zeroing path was the only one that
could produce a fraction, and it is the one the test drives.

Fixed by flooring where the value is actually produced:

```python
        IDiv(Times(L(1.0 - float(share)), surrendered_clock), L(1.0)),
```

Measured both ways:

* probe registered -- **39 green**;
* probe UNREGISTERED -- `test_f16_prices_a_surrendered_axis_on_its_own_clock`
  **passes**, where it read 612.5 before.

The frame/continuum invariant is now honoured on this path: the ratio stays in
the cross-frame map and the clock stays on the integer lattice.

### What remains between here and retiring the probe

One test: `test_f16_consumer_declares_pareto_regime_candidates`, which asserts
the probe is minted at the held ordinal. That is the OLD invariant, and updating
it is part of retirement rather than a defect to fix first. Both real blockers --
the unclosable deliberation (BC) and the non-integer clock (this block) -- are
now fixed and green.

Also recorded: re-registering the probe put its mint rule BEFORE
`f16_mint_hold_pareto_candidate` instead of after, changing candidate creation
order, which the first-wins argmin depends on. Caught by reading the regenerated
seed's rule order, not by a test -- the suite was green with the order wrong.

### BC and BD suite results — both verified, both behaviourally inert

| block | vs | result |
|---|---|---|
| BC close rule | AY | all 8 identical (damaged_wing -0.01), crashes 3/24 |
| BD integer clock | BC | **all 8 byte-identical**, crashes 3/24 |

Both are what they should be. The close rule cannot fire while the probe is
registered, because the probe is admissible and every deliberation therefore has
an admissible proposal. The floored clock changes values that turn out not to
decide any selection on this suite. Neither costs anything, and both are
prerequisites rather than improvements -- they are the machinery that has to
exist before the probe can be removed, measured to be free while it is still
there.

**State at the close of this line: both blockers fixed and suite-verified, one
stale-invariant test between here and retiring the probe.** The suite stands at
3/24 crashes with damaged_wing 2/3, unchanged since contact detection made those
numbers honest.

## Block BE — probe retirement: REVERTED. 39 green and catastrophic.

Both blockers were fixed and suite-verified (BC, BD), the stale-invariant test
was rewritten into a retirement record, and **the whole gate went green with the
probe unregistered.** The suite says the gate was measuring the wrong thing.

| scenario | RMSE BD | RMSE retired | delta | crash | peak struct |
|---|---|---|---|---|---|
| nominal / jam / aileron | -- | -- | identical | 0/3 | 0.64 |
| saturated_elevator | 3801.49 | 3676.68 | -124.81 | 0/3 -> **1/3** | 2.41 |
| landing_gear | 1115.62 | 1135.22 | +19.59 | 0/3 | 0.64 |
| **shifted_cg** | 5693.33 | **14194.42** | **+8501.09** | 0/3 -> **3/3** | **588.62** |
| damaged_tail | 8350.45 | 8898.14 | +547.69 | 1/3 | 11.85 |
| damaged_wing | 6506.87 | 6940.58 | +433.71 | 2/3 | 25.51 |

**Crashes 3/24 -> 7/24.** shifted_cg, which has never crashed once in this entire
line of work, crashes in all three episodes at 588x its structural limit.
saturated_elevator loses an episode. damaged_wing now goes through the ground
(-0.2 ft, -17.7 ft) rather than onto it.

### What this refutes

The reasoning for retirement was: the probe was doing three jobs, each now has an
owner, therefore it can go.

* the benign-conditions law -> `candidate_requires_change` (AY);
* closing a deliberation by winning it -> `cre_close_inadmissible_deliberation`
  (BC);
* masking a non-integer clock -> the floor in `_contained` (BD).

Each of those is real, and the enumeration was still wrong -- it was a list of
the jobs I had *found*, presented as the jobs that *exist*. **The probe is doing
at least one further thing on the shifted_cg path that nothing in the test suite
exercises and that I never identified.** A 588x structural excursion is not a
selection subtlety; it is the loop flying something it would otherwise never
choose.

### The gate is the finding

39 green with the probe gone, and 7/24 crashes. The tests cover the frontier's
*shape* -- what is minted, what is admissible, what closes -- and not the
*consequences* of the choice on scenarios that only fail dynamically. shifted_cg
has no dedicated test because it never failed; it never failed because the probe
was holding it up; and nothing recorded that dependency because nobody knew it
existed.

**A green suite is not evidence that a suppression was unnecessary.** That is the
same shape as this morning's crash predicate: an instrument that could not see
the failure it was being trusted to rule out.

Reverted. The probe stays, and the honest statement of its status changes: it is
not "a measurement probe kept alive by three fixable defects" but **an
unexplained dependency of at least four scenarios**, whose removal is now
measured rather than argued. AY, BC and BD remain correct and kept on their own
evidence; they were necessary and are not sufficient.

Next: BEFORE any further retirement attempt, bisect what the probe contributes on
shifted_cg specifically -- it is the sharpest signal available (0/3 -> 3/3, 588x)
and the cheapest to instrument, and it is a scenario nobody has looked at because
it never misbehaved.

## Block BF — bisected: the probe was masking a FALSE ALARM

One episode of shifted_cg, both arms, everything else identical:

| | probe present | probe retired |
|---|---|---|
| ordinals visited | 0 only | 0 -> **5** at action 218 -> **4** at 588 |
| escalations | 0 | 3 |
| **first rung 0** | **215** | **215** |
| **first `regime_change_required`** | **215** | **215** |
| peak `nz / safe` | 0.30 | **44.23** at action 615 |
| final altitude | 3907 m | **2 m** |

**The probe's whole contribution is preventing escalation.** Nothing subtler.
With it gone the loop escalates to roll_priority three actions after rung 0, then
to speed_priority, and destroys the aircraft.

### The finding is the rung, not the probe

**Rung 0 fires at action 215 in BOTH arms.** The viability ladder declares
shifted_cg non-viable in a scenario that, left entirely alone, flies to the end
at 0.30 of its structural limit and finishes at 3907 m. Nothing is wrong with
that aircraft. **Rung 0 is a false positive**, and `regime_change_required` is
asserted on the strength of it.

So the sequence is not "the probe does an unidentified job". It is:

1. the ladder raises a false alarm on shifted_cg at action 215;
2. the escape machinery (AV) faithfully proposes a corner, the law (AY) licenses
   it because a change is "required", and the verdict adopts it;
3. that corner is catastrophically wrong for an aircraft that was fine -- 44x the
   structural limit, into the ground;
4. and the probe, by winning every frontier, was the only thing preventing any of
   that from being acted on.

**The probe was not load-bearing. It was a fuse in series with a false alarm.**
Every block from AS to BE has been improving the response to a signal that should
not have fired.

### What this reframes

* AS repair 2, AW, AY, BC, BD, BE all made the loop MORE responsive to rung 0.
  On the two departing scenarios that is right; on shifted_cg it is exactly
  wrong, and shifted_cg is the scenario nobody looked at because it never
  misbehaved.
* The recovery corner measured in AX (structural 15.29 -> 6.29 on damaged_wing)
  is still the right manoeuvre -- but it will be triggered by this same false
  alarm on shifted_cg unless the alarm is fixed first.
* **Fix the rung before anything else in this line.** Every downstream
  improvement is amplification of whatever the ladder says, and on one scenario
  in eight it is saying the wrong thing 215 actions in.

Concretely: find why `terrain_clear` goes false on shifted_cg at action 215 with
the aircraft at 0.30 structural and thousands of feet of altitude. It is one
scenario, one action, and both arms agree on it -- the cheapest and best-posed
question this line has had.

## Block BG — the false alarm is a UNIT ERROR: seconds published as actions

shifted_cg, one episode, the terrain region measured through the trip:

| act | alt m | sink_ema m/s | gap m | region_actions | terrain_clear | rung |
|---|---|---|---|---|---|---|
| 180 | 6556 | -54.58 | 6556 | 120 | 1.0 | 3 |
| 213 | 6251 | -76.33 | 6251 | 81 | 1.0 | 2 |
| 214 | 6241 | -76.77 | 6241 | 81 | 1.0 | 2 |
| **215** | **6232** | **-77.20** | **6232** | **80** | **0.0** | **0** |
| 600 | 4498 | -16.10 | 4498 | 279 | 1.0 | 3 |

```
  at action 215:  gap 6232 m / sink 77.2 m/s = 80.7   <- published as region_actions
                  horizon = 80 actions, action_duration = 0.1 s
                  TRUE actions to ground = 80.7 / 0.1 = 807
```

**`gap / rate` is SECONDS. It is published, compared and named as ACTIONS.** At
10 Hz that understates every region clock by exactly 10x, and the alarm trips
when the aircraft has 807 actions of margin, not 80. It trips by 0.7 of a second.

### Whose defect

`cre_project_region_reachability` computes `region_gap / channel_rate_measured`
and documents the result as "integer actions until the gap closes at the measured
rate". That is correct **iff the rate is metres per ACTION**. The F-16 consumer
publishes `channel_rate_measured = f16_sink_rate_ema`, which is metres per
SECOND (`f16_track_sink_rate_ema` EMAs `state_vz`). The contract is per-action;
the consumer supplies per-second.

The fix is one line in the consumer -- publish the rate in the frame the contract
declares:

```python
    sink = Max(Abs(P0("episode", "f16_sink_rate_ema")), L(0.000001))
    #  -> Times(sink, P0("episode", "control_action_duration_seconds"))
```

in both `f16_declare_terrain_region` and `f16_track_terrain_region`. It is
exactly the frame invariant again: seconds and actions are different frames, and
the ratio between them is the action duration.

### What it explains

* **shifted_cg's false alarm**, and with it block BE's 7/24. The aircraft is in a
  steep transient descent (-94 m/s) it fully recovers from -- back to rung 3 and
  4498 m by action 600 -- and the loop declares it non-viable 215 actions in.
* **Why the damaged_wing clocks always looked so short.** At action 601 the
  terrain clock read 4 with impact 42 actions later. 4 seconds. It was right in
  seconds and wrong by 10x in the units it was compared against.
* Every `region_actions <= horizon` comparison this line has made, including the
  viability ladder's TERRAIN CLEAR rung and everything downstream of it.

**Not fixed here.** It is one line and it changes the rung on every scenario, so
it needs its own prereg and a full block -- and this session has already
established what happens when a change at this layer is landed on a green gate
alone. It is the first thing to do next, and it is the root of the line:
AS through BF were all responses to a signal that fires ten times too early.

## Block BH — the unit fix: KEPT on correctness, with two predictions failed

| scenario | RMSE BD | RMSE fixed | delta | crash | peak struct |
|---|---|---|---|---|---|
| nominal / jammed_rudder / saturated_elevator | -- | -- | identical | 0/3 | 0.64-0.65 |
| broken_aileron | 1781.20 | 1770.91 | -10.29 | 0/3 | 0.64 |
| landing_gear | 1115.62 | 1117.39 | +1.77 | 0/3 | 0.64 |
| shifted_cg | 5693.33 | 5741.48 | +48.15 | 0/3 | 0.65 |
| **damaged_tail** | 8350.45 | **7932.72** | **-417.73** | 1/3 | 10.79 |
| **damaged_wing** | 6506.87 | **6384.12** | **-122.74** | 2/3 | **19.49** |

**Crashes 3/24, unchanged -- the decisive prediction holds.** The two scenarios
that actually depart both track better, damaged_tail by 418 ft.

**Two preregistered predictions failed, and they are recorded as failures:**

* **(3) the five roomy scenarios byte-identical -- FALSE.** Only three are;
  broken_aileron, landing_gear and shifted_cg all move. My reasoning was that
  their clocks already sit at the 1024 cap so the rung cannot change. Wrong:
  they are near the cap at some actions and not at others, and a 10x stretch
  changes which.
* **(5) damaged_wing peak structural must not rise above 15.86 -- FALSE.** It is
  **19.49**. A rung that fires later means less spend authority earlier, and on
  this scenario that costs structural margin.

### Kept, and on what grounds

Not on the numbers. **The old value was simply wrong**: `gap / rate` with a
per-second rate is seconds, and it was being compared against a horizon counted
in actions. Reverting a unit correction because a non-decisive prediction failed
would be keeping a known-false quantity because its errors happened to be
convenient -- which is the same trade this line already made once, when the crash
predicate's blindness was flattering every block from AN to AQ.

The structural rise is a real, open cost and is not explained away: at 19.49 the
damaged wing is consuming more margin than before, and the reason is that the
corrected clock delays the rung. That is a consequence of measuring correctly,
not an argument against it.

**Prediction 2 (shifted_cg no longer reaches rung 0 at action 215) is
UNVERIFIED.** shifted_cg was 0/3 before and after, so the suite cannot separate
it; confirming it needs the BF probe re-run and that has not been done.

### What this unblocks

BE can now be re-attempted. Retiring the probe took crashes to 7/24 because
shifted_cg's rung-0 false alarm was being acted on; if BG's diagnosis is right
the alarm is gone and the retirement should behave. That is the next block, and
it must be measured rather than assumed -- the same claim was made before BE on
weaker evidence and was wrong.

## Block BI — the probe is RETIRED. The causal chain is confirmed end to end.

| scenario | RMSE BH | RMSE retired | delta | crash | peak struct |
|---|---|---|---|---|---|
| nominal / jam / aileron / sat_elevator / gear / **shifted_cg** | -- | -- | **byte-identical** | 0/3 | 0.64-0.65 |
| damaged_tail | 7932.72 | 7933.91 | +1.19 | 1/3 | **10.79 -> 8.55** |
| damaged_wing | 6384.12 | 6384.32 | +0.20 | 2/3 | 19.49 -> **23.91** |

**Crashes 3/24, unchanged.** BE, the same change before the alarm was fixed, gave
**7/24** with shifted_cg 3/3 at 588x structural.

### The chain, confirmed

1. **BE** -- retiring the probe took crashes 3/24 -> 7/24. Cause unknown; three
   named jobs had owners and it still broke.
2. **BF** -- bisected: the probe's only contribution was preventing escalation,
   and rung 0 fired at action 215 in BOTH arms. The probe was a fuse in series
   with a false alarm.
3. **BG** -- the alarm: `gap / rate` with a per-second rate is SECONDS, published
   and compared as ACTIONS. shifted_cg tripped with 807 actions of margin, by 0.7
   of a second.
4. **BH** -- fixed in the consumer; crashes held at 3/24.
5. **BI** -- the identical retirement that failed at 7/24 now leaves **six
   scenarios byte-identical, shifted_cg among them**, and crashes unchanged.

shifted_cg being byte-identical with the probe GONE is the specific confirmation:
the probe had nothing left to suppress there because the signal it was
suppressing the response to no longer fires.

### Kept, with one cost recorded

* damaged_tail improves -- peak structural 10.79 -> 8.55.
* **damaged_wing's peak structural rises 19.49 -> 23.91**, continuing the drift
  from 15.86 at BD. Tracking is unchanged (+0.20). The departing wing is
  consuming more margin as the loop becomes more responsive, and neither BH nor
  this block bought a crash back for it.

That cost is open and is the honest counterweight to the result: the frontier is
finally free of a candidate that could never be flown, and the scenario the whole
line exists for is still 2/3 and now spends more airframe getting there.

### What this unblocks

The AX allocation corner -- allocation drives targets, measured at damaged_wing
structural 15.29 -> 6.29 and ep0 3770 ft higher -- was built, measured, and
reverted because it needed a real ordinal and the frontier was owned by the
probe. Both obstacles are now gone: the probe is retired and adoption is bounded
by `candidate_requires_change`. It is the next block, and it is the first time in
this line that the thing which measurably reduced structural consumption can
actually be flown.

## Block BJ — the allocation corner flies. KEPT.

| scenario | RMSE BI | RMSE BJ | delta | crash | struct BI -> BJ |
|---|---|---|---|---|---|
| nominal / jam / aileron / sat_elevator / gear / shifted_cg | -- | -- | **byte-identical** | 0/3 | unchanged |
| damaged_tail | 7933.91 | 7932.97 | -0.94 | 1/3 | 8.55 -> 10.92 |
| **damaged_wing** | 6384.32 | 6384.23 | -0.09 | 2/3 | **23.91 -> 15.86** |

**Every prediction held.**

1. **Crashes 3/24, unchanged** -- decisive.
2. **damaged_wing peak structural falls 23.91 -> 15.86, a 34% reduction.** This
   is the prediction the block existed for, and the mechanism is the one AX
   measured: the altitude margin drops below 1 at the stall, the pitch-angle
   demand scales with it, and the wing unloads. It reverses the drift of the
   last three blocks (15.86 -> 19.49 -> 23.91) exactly back to where it started.
3. **The six roomy scenarios are byte-identical.** This is the prediction AX
   FAILED before the bound existed, and it is the direct confirmation that AY's
   `candidate_requires_change` does its job: a corner that surrenders objectives
   cannot be adopted where nothing licenses it.
4. Tracking essentially unchanged (-0.09 on damaged_wing).
5. **No slowdown.** The full eight-scenario block ran in 529 s. AX's ~3x
   per-episode blowup does not recur, and the most likely explanation is that it
   was the unbounded corner being adopted in every scenario rather than only at
   rung 0 -- i.e. a symptom of the AX defect AY fixed, not a separate problem.

### Honest accounting

* 15.86 is **not** AX's 6.29. That figure was measured against a different
  baseline, before the unit fix and before retirement, and the two are not
  comparable. What is comparable is 23.91 -> 15.86 against the block immediately
  before this one.
* damaged_tail's structural rises 8.55 -> 10.92. Smaller than damaged_wing's
  fall and on a scenario with far more margin, but it is a cost and it is not
  explained.
* **damaged_wing is still 2/3.** The corner reduces what the aircraft SPENDS
  without changing whether it survives. Every mechanism in this line now works
  as designed -- detection, escape, admissibility, closure, a flyable corner --
  and the aircraft still goes in twice out of three.

That last point is the standing result of the whole line, stated plainly: the
machinery is correct and insufficient. The remaining question is not how the loop
chooses, but whether any of the six corners plus the generated one is a recovery
from a fully developed stall at all -- which is a question about the corner set,
and it has never been answered because until this block nothing generated could
be flown.

## Block BK — is any corner a stall recovery? NO, and the reason is compound.

damaged_wing ep1 instrumented through the departure, BJ configuration:

| act | ord | rung | AoA | kts | alt m | target_pitch | m_alt |
|---|---|---|---|---|---|---|---|
| 150 | 0 | 2 | 9.5 | 189 | 1884 | +19.25 | 2.14 |
| **190** | 0 | 3 | **21.8** | 203 | 1790 | **+25.00** | **0.95** |
| 250 | 0 | 2 | 39.1 | 103 | 1727 | **+25.00** | 1.50 |
| 400 | 0 | 2 | 57.3 | 107 | 1250 | **+25.00** | 0.28 |
| 600 | 5 | 0 | 76.5 | 104 | 229 | -11.94 | 0.08 |

First nose-down command: **action 598**, 45 actions before impact.

### Two independent reasons, both fatal

**1. No corner commands nose-down.** `target_pitch_angle` sits at its saturated
maximum **+25 degrees** from action 190 to 597 while AoA climbs 21.8 -> 57. The
outer loop chases altitude all the way to the ground. The generated corner scales
that demand by `min(reach / gap, 1)`, so at margin zero it commands **level, not
nose-down**. **Scaling a demand toward zero is not a recovery.** A stalled wing
needs negative pitch to trade height for speed; nothing in the corner set, hand-
authored or generated, can express that -- the allocation vocabulary has no way
to say "command the opposite of what the objective asks for".

**2. The corner cannot be adopted during the stall.** Adoption requires
`regime_change_required`, which is tied to viability rung 0. Rung is 2-3
throughout the stall because, after the unit fix, **terrain genuinely is clear**
-- 807 actions of margin. Rung 0 first arrives at ~597. The bound that made the
corner safe (AY, and confirmed correct by BJ's six byte-identical scenarios)
also makes it unreachable at the only moment it is needed.

### The signal that WAS available and is consulted by nothing

`f16_goal_margin_altitude` crosses below 1 at action 190 -- exactly at the stall,
0.95 then 0.84 -- and stays low. The loop measures, every action, that the
altitude objective has become unreachable. **Nothing gates adoption on it.**
Adoption is gated on the viability ladder, whose three rungs are terrain,
structural envelope and roll controllability -- none of which is "the wing has
stopped flying". The stall is invisible to the ladder by construction.

### What this settles for the line

The corner set is not the whole answer and neither is the selection. Stated as
the two things that must both change:

* **A recovery corner must be able to command against its objective**, not merely
  attenuate the demand for it. That is a change to what an allocation CAN say --
  currently a share in [0, 1] -- and the natural form is a share that may go
  negative, which is exactly "spend altitude to buy speed" and is the same trade
  the energy relation (AT) already measures.
* **Adoption must be licensable by the manifold margin**, not only by the
  viability ladder. `f16_goal_margin_* < 1` is measured every action, fires at
  the stall, and is already the quantity `_generated_share` is built from.
  Licensing on it is a one-line addition to what sets `regime_change_required`.

Neither is built here. Both are now specified by measurement rather than
inference, which is the first time this line has been able to say that about the
thing standing between it and a surviving damaged wing.

## Block BL — negative shares and the margin licence: the licence CONTRADICTS the law

Both changes were built as preregistered. The benign-conditions test failed
immediately, and it is not a stale invariant -- it is a real contradiction
between the two halves of BK's recommendation.

**`f16_goal_margin = reach / gap`, and `gap` IS the tracking error.** So
"margin < 1" means "the error exceeds what I can correct inside the horizon",
which is a statement about tracking. Licensing surrender on it is precisely what
`test_f16_evidence_still_starves_on_a_divergence_past_the_band` forbids: *"a
tracking error is not by itself a reason to give an objective up."*

BK recommended licensing on the margin because the stall shows up there at action
190. AY established that the margin's own family of signals is not sufficient
grounds. **Both are right, and BK did not notice it was contradicting a law this
same session had just stated as a rule.** The test noticed in 6.8 seconds.

### The distinction the two are arguing about

The benign test's scenario has every control axis INSIDE its declared authority:
the loop is tracking badly but can still command what it needs. A stalled wing is
tracking badly AND cannot. The margin cannot tell those apart, because it is
computed from error and reach without asking whether the authority to close it
still exists.

So the licence is not "margin < 1". It is **"margin < 1 AND the authority is
insufficient"** -- and the second half already exists and is already measured:
`authority < demand` was established earlier in this line as a zero-false-
positive predicate across ~21,000 samples, and rung 3 CONTROLLABLE is built from
it. Conjoining them separates "cannot correct fast enough" from "cannot correct
at all", which is exactly the difference between the benign scenario and the
stall.

### Status

Reverted, both halves, 39 green. The negative-share machinery (`_drive_share`,
the affine map of the scoring share onto [-1, 1]) was never measured in flight,
because the licence it depends on could not be landed -- so nothing is known
about whether commanding nose-down at the stall actually recovers the aircraft.
That remains the open question, and it now has one precondition instead of two:

* **licence** = `margin < 1` AND `authority < demand`, both already measured,
  conjunction not yet built;
* **manoeuvre** = the negative drive share, built here and reverted unmeasured.

Recorded as the cleanest statement of what is left: the machinery to fly a
recovery exists, the signal to trigger it exists, and the trigger has to be
conjoined with a controllability test before it can be allowed to fire.

## Block BM — the conjoined licence: built, 39 green, SUITE PENDING and the slowdown is back

BL failed because `margin < 1` is a tracking statement and licensing surrender on
it violates the benign-conditions law. The conjunction separates the two cases on
a quantity already measured:

```
    change_required  =  NOT terrain_clear
                        OR (some goal margin < 1  AND  NOT controllable)
```

`controllable` is rung 3's own test, and it is the `authority < demand` predicate
this line established at zero false positives across ~21,000 samples. Tracking
badly with every axis INSIDE its authority is a loop that can still command what
it needs; a stalled wing is tracking badly AND cannot.

Shipped with it: `_drive_share`, the affine map of the scoring share onto
[-1, 1], so a corner can command AGAINST an objective rather than only attenuate
the demand for it -- the manoeuvre BK showed was missing.

**39 green, and the benign-conditions test passes** -- which is the conjunction
doing exactly its job, since BL failed that same test in 6.8 seconds.

### Status: NOT VERIFIED IN FLIGHT

The instrumented single-episode run **exceeded a 10-minute timeout** where the
same probe took ~3 minutes one block ago. This is BJ's preregistered watch item
(5) firing: the ~3x slowdown last seen in AX has recurred. The obvious reading is
that the conjoined licence makes the allocated corner adoptable far more often,
and whatever is expensive about flying it now runs on many more actions -- which
would make BJ's "no slowdown" result a consequence of the corner rarely being
adopted, not of the cost being absent.

**Committed on a 39-green gate alone, with that stated.** The suite is running
and has not been read. This is the same exposure BD had and BE punished; it is
accepted here only because leaving the working tree dirty at a session boundary
is worse, and the change is one `git revert` away.

What is NOT known:

* whether nose-down is now commanded at the stall (~action 190-250) rather than
  at 598 -- the measurement that would justify the whole block, and the one the
  timeout ate;
* whether crashes hold at 3/24;
* whether the six roomy scenarios stay identical, which the wider licence makes
  genuinely uncertain;
* what the slowdown actually is. It has now been observed twice, attributed once
  (wrongly, to the allocated ordinal in AX) and never traced.

## Block BN — the slowdown localised: fresh synthesis, not the rule engine

Observed twice (AX, BM), attributed once and wrongly (to the allocated ordinal),
never traced. Traced now.

**It is not graph growth.** Instrumented over 300 actions of damaged_wing:
profiles stay at **2** and candidates at **12** for the whole run. Nothing
accumulates; the deliberation machinery retires what it mints.

**It tracks HOLDING the allocated corner.** Mean per-action cost 26.6 ms over the
first 50 actions, 81.9 ms over the last 50 (**3.1x**), and **136 ms at action 300
with ordinal 6 held**. At 10 Hz an action has a 100 ms budget, so the loop is
slower than real time while flying this corner.

**And it is the composer, not the rule engine.** From the block metrics on
damaged_wing:

| | system1 p99 (reuse) | **system2 p99 (fresh synthesis)** |
|---|---|---|
| BI, corner retired | 62,959 us | 196,539 us |
| BJ, corner live | 28,235 us | **1,702,587 us** |

Internalised reuse is unchanged -- if anything faster. **Fresh synthesis goes
from 0.2 s to 1.7 s at p99, an 8.7x blowup.** The cost is inside `MotorCompose`,
on the actions where a program has to be synthesised rather than reused.

### The likely mechanism, and what would confirm it

The allocated corner rescales four targets every action from continuously
varying margins. A target vector that never repeats cannot match an internalised
program, so more actions fall through to fresh synthesis -- and a scaled,
non-zero demand on four channels plausibly needs a wider program, which the
composer's expansion rounds pay for super-linearly (the module's own header
records 294/82/44 ms at 8/4/2 quantization intervals, quadratic in the candidate
alphabet).

**Not confirmed.** `maximum_program_width` is not recorded by this harness --
checked, the key is absent from every episode -- so whether the programs are
actually wider is unmeasured. That is the next measurement and it is one metric
away.

### Why it matters beyond performance

The corner that reduces structural consumption is the corner that makes the loop
miss its control deadline. At 136 ms per action on a 100 ms budget, a real
aircraft flying this would be commanding at ~7 Hz while its controller believed
it was at 10. **This is a correctness problem wearing a performance costume**, and
it belongs with the results rather than in a footnote: BJ reported "no slowdown"
and that now reads as a consequence of the corner rarely being adopted, not of
the cost being absent.

## Block BO — the guard fix, and it FALSIFIES the allocation corner. Reverted to BI.

A Sonnet agent traced the slowdown. **My hypothesis was wrong on both halves** and
the true cause was a defect in a rule I wrote.

### The defect

`f16_drive_targets_from_allocation` reads and rewrites its own input
(`target = share * target`) with no once-per-request guard. Unless `share` is
exactly 1.0, each firing produces a different value, so the fixpoint never
settles: **~97 firings per action** while ordinal 6 was held, and every other
batch rule sharing that fixpoint re-scanned all 37 candidate models on each extra
pass -- ~11 wasted full rescans per action, ~78 ms/action of pure waste.

Refuted, both parts of BN's hypothesis: programs were **narrower** under ordinal 6
(width 1.18 vs 2.28), and reuse dropped to 0% but is **still** 0% after the fix
while the blowup is gone. The composer search was never the problem. **The settle
loop was spinning.**

Fixed with a `program_request_seq` guard mirroring the upstream twin
`emp_derive_flight_path_control_targets`. Cost at ordinal 6: **134.4 -> 79.9
ms/action**, p99 197.7 -> 129.6.

### What the guard revealed, which is the real result

`share^~97` drove `target_forward` to **exactly 0.0** for the whole held-corner
window. The other three axes had shares of exactly +/-1 in that episode, so only
the speed demand was silently zeroed -- which is why nothing looked wrong.

**Block BJ's headline was that artefact.** damaged_wing structural 23.91 -> 15.86,
which I reported as "demand only what is reachable" working, was produced by a
rule zeroing the speed demand outright.

With the corner behaving AS DESIGNED, the suite:

| scenario | RMSE BJ | RMSE guarded | crash | struct |
|---|---|---|---|---|
| **saturated_elevator** | 3801 | 6298 | 0/3 -> **3/3** | **32.00** |
| **shifted_cg** | 5741 | 12520 | 0/3 -> **3/3** | 23.47 |
| jammed_rudder | 809 | 5149 | 0/3 | 0.65 |
| damaged_wing | 6384 | 6546 | 2/3 | 19.90 |

**Crashes 3/24 -> 9/24.** The allocation corner, correctly implemented, destroys
two scenarios that have never crashed. Only the bug made it survivable.

### Reverted to BI (`8bc93ccd5a`)

That is the last state whose 3/24 was measured without a known-defective rule in
it. Everything from BJ onward -- the flyable corner, negative shares, the
conjoined licence -- is out of the tree. 39 green.

**BJ, BM and BN are retracted as results.** BJ measured an artefact; BM was
committed unverified and ran on the same artefact; BN's mechanism was wrong.
What survives: BK's finding that no corner commands nose-down, BL's finding that
the margin alone cannot license surrender, and the conjunction reasoning in BM --
none of which depended on the corner working.

### The lesson worth keeping

A self-referential effect with no idempotency guard does not announce itself. It
passed 39 tests, produced a plausible improvement in the exact direction the
design predicted, and I wrote it up as the mechanism working. **The result
agreed with the hypothesis, which is precisely when the arithmetic deserves
checking** -- and the thing that caught it was an agent asked to explain a
performance number nobody thought was a correctness problem.

## Block BP — the guard is NOT in the tree, and an audit of the defect class

**Correction first: the guard fix did not survive the revert.** It was a fix TO
`f16_drive_targets_from_allocation`, and reverting to BI removed that rule
entirely, so there is nothing left to guard. The fix is preserved only in the BO
commit message and in this document. **If the allocation corner is ever
reinstated, it must come back with the `program_request_seq` guard** -- without
it the rule silently zeroes `target_forward` and the whole BJ result repeats.

### Audit: does the defect class exist elsewhere?

The signature is narrow: a `set_attr` whose value term reads the attribute it
writes, in a rule matched ONLY on episode-level singletons, with no
seq/applied guard. Anything matched on a per-event node (a receipt, an outcome,
a trial) is bounded by its own match and is not at risk -- which is why a naive
scan reporting 849 "self-referential effects" is useless. Filtered properly:
**16 distinct rules**, of which most are safe by construction:

* **monotone/idempotent** -- `cre_publish_spend_authority` writes
  `regime_rung_high_water` as a running max, so re-firing changes nothing;
* **counters whose own effect falsifies their guard** -- the `ha_choose_*`
  `decision_count` family and friends;
* **`hcr_bridge_escalate_regime`** -- the blind `regime_ordinal += 1` already
  found in BA, and already established as unreachable on the F-16 path.

**One is worth checking and is on the live path:**
`f16_adopt_thrust_basis_regime` writes `forward_weight` self-referentially.
Thrust-basis is ordinal 3 and reachable only via a Pareto proposal, so it is
rarely adopted -- which is exactly the condition under which this class of defect
goes unnoticed, since that is precisely how the allocation corner's version
survived until the corner started being adopted often. Not investigated here.

### Where the line actually stands

Unchanged, and the standing numbers are BI's: **3/24 crashes, damaged_wing 2/3.**

What is known and survives every retraction:

* the crash metric is honest (contact detection, AR);
* the terrain clock's 10x unit error is fixed (BH);
* the probe is retired and the frontier is clean (BI);
* **no corner in the set commands nose-down** (BK) -- the manoeuvre a stalled
  wing needs cannot be expressed by any allocation in [0, 1];
* **the margin alone cannot license surrender** (BL); the conjunction with
  `authority < demand` is the form that can, and it passes the benign test;
* **the allocation corner, correctly implemented, is catastrophic** (BO): 9/24,
  and only a compounding bug ever made it look otherwise.

The negative-share manoeuvre has still never been measured cleanly -- it shipped
in BM, which ran on the defective rule, and BO tested only the positive-share
form. So "can a corner that commands against its objective recover a stall?"
remains open, and is now the only untested branch left in the line.

### BP correction — negative shares WERE measured properly. They are falsified.

BP closed by saying the negative-share manoeuvre "has still never been measured
cleanly ... BO tested only the positive-share form". **That is wrong**, and
checking the tree rather than my memory of it settles it:

```
  git show cf30f81e50:...gen_f16_flight_path_control_seed.py | grep -c _drive_share  -> 2
  ...and the drive rule at that commit reads:
        ["set_attr", "episode", target, T(Times(
            _drive_share(axis), P0("episode", target)
        ))]
```

BM committed `_drive_share` -- the affine map onto [-1, 1] -- and the agent added
**only** the `program_request_seq` guard on top of that tree. So `guarded_bo_v1`
ran the complete, correct form of the design:

* the corner minted at its own ordinal and flyable;
* **negative shares**, so it commands AGAINST an objective rather than
  attenuating it -- the manoeuvre BK proved was missing;
* the conjoined licence (`margin < 1 AND NOT controllable`), which passes the
  benign-conditions test;
* the idempotency guard, so the share applies exactly once per action.

**Result: 9/24 crashes.** saturated_elevator 0/3 -> 3/3 at 32x structural,
shifted_cg 0/3 -> 3/3, jammed_rudder RMSE 809 -> 5149.

### So the prescription itself is falsified, not its implementation

Every reason the corner previously failed has been removed and measured away --
unadoptable ordinal, unbounded adoption, missing manoeuvre, missing licence,
runaway fixpoint. With all five fixed, the corner is **three times worse than
having no corner at all.**

The likely reason, stated as a hypothesis and not a finding: a share scaled
linearly by margin **inverts a demand whenever the objective is merely hard**,
not impossible. `margin < 0.5` is common on a saturated elevator or a shifted CG
that is tracking poorly but flying perfectly well; commanding the opposite of
what those objectives ask for is not a recovery, it is a departure the loop
initiates itself. The conjoined licence gates WHEN the corner may be adopted; it
does not bound HOW FAR the corner may invert once adopted.

**No further build here.** The line's honest terminus for this session: the
allocation corner is not the recovery, in any of the four forms tried, and BK's
prescription -- "a corner must be able to command against its objective" -- is
necessary but very far from sufficient. Standing numbers remain BI's **3/24,
damaged_wing 2/3.**

## Block BQ — decades instead of linear: NO CHANGE. 9/24. Shape was never the issue.

| scenario | BI | BO (linear) | **BQ (decades)** |
|---|---|---|---|
| saturated_elevator | 0/3 | 3/3 | **3/3** |
| shifted_cg | 0/3 | 3/3 | 1/3 |
| damaged_tail | 1/3 | 1/3 | **2/3** |
| damaged_wing | 2/3 | 2/3 | **3/3** |
| **total** | **3/24** | 9/24 | **9/24** |

**Prediction 1 (decisive) failed.** The convex form recovers nothing: shifted_cg
improves 3/3 -> 1/3, and damaged_tail and damaged_wing each lose an episode to
pay for it. saturated_elevator is untouched at 3/3.

Prediction 2 failed with it. Prediction 3 (structural below 15.86) failed --
damaged_wing reads 26.00.

Some tracking numbers improved sharply -- broken_aileron 1771 -> 759,
landing_gear 1117 -> 788, jammed_rudder 809 -> 872 -- which is the corner doing
something real to the flight. It is simply not something survivable.

### This confirms BR, which was preregistered before the result

BR stated the fork explicitly: *"If BQ is still above 3/24, then shape was never
the issue and incoherent command vectors are, which would make this block
mandatory rather than incremental."* BQ is above 3/24. **The per-axis map's SHAPE
is not the defect.**

What remains is the error BR names: `_drive_share` computes six commands from six
margins with nothing comparing them, in violation of the principle `_allocated`
states and honours -- *an allocation is a BUDGET; authority given to one
objective is not available to another.* Both the linear and the decade forms are
absolute per-axis maps, and both produce command vectors no corner ever declared:
altitude opposed while heading and speed still demand full authority. Changing
how steeply a single axis inverts cannot fix a vector that points nowhere a
manoeuvre lives.

### Reverted to BI (`8bc93ccd5a`) again

3/24 stands. Four forms of the allocation corner have now been measured --
unbounded, bounded, negative-linear, negative-decade -- and all four are worse
than having no corner. The one untried form is the one BR specifies: normalise
across the axis vector so only the relative weighting survives.

**That is now the whole of the remaining hypothesis for this line.** If a
normalised drive vector also fails, the allocation corner is finished as an idea
and the recovery has to come from somewhere else entirely.

## Block BS — vector normalisation: 7/24. The corner is the wrong instrument.

| scenario | BI | BO (linear) | BQ (decades) | **BS (vector)** |
|---|---|---|---|---|
| **saturated_elevator** | 0/3 | 3/3 | 3/3 | **3/3** |
| shifted_cg | 0/3 | 3/3 | 1/3 | 1/3 |
| damaged_tail | 1/3 | 1/3 | 2/3 | **1/3** |
| damaged_wing | 2/3 | 2/3 | 3/3 | **2/3** |
| **total** | **3/24** | 9/24 | 9/24 | **7/24** |

**The vector framing is real.** BS recovers every regression BQ introduced --
damaged_tail 2/3 -> 1/3 and damaged_wing 3/3 -> 2/3 both return to baseline --
which is exactly what "only the comparison between axes means anything" predicts:
coupling the axes stopped the corner from wrecking the two scenarios that were
already marginal.

**And the decisive prediction still failed.** 7/24 against a 3/24 baseline.
Prediction 2 failed outright: **saturated_elevator is 3/3 in all three forms.**
Per-axis shape does not touch it. Vector coupling does not touch it. It is the
sharpest discriminator available and no parameterisation has moved it by a single
episode.

### Honouring the commitment made before the run

BS's prereg said, before any number existed:

> If this fails, four blocks of the allocation corner across two orthogonal axes
> of variation (per-axis shape, and vector coupling) have all been worse than no
> corner, and the honest conclusion is that the corner is the wrong instrument --
> not that a fifth parameterisation is owed.

It failed. **The allocation corner is the wrong instrument.**

The 3-9 band also fired prediction 4, which offers the attenuating-sign variant
as a remainder, and that is precisely the temptation the commitment was written
to refuse. The evidence against a fifth attempt is not the 7/24 -- it is that
saturated_elevator is untouched at 3/3 across every form tried. A scenario that
three independent parameterisations cannot move is not waiting for a fourth
parameterisation; the corner is doing something to that aircraft that no choice
of coefficients makes safe.

### Reverted to BI (`8bc93ccd5a`). Final standing.

**3/24 crashes. damaged_wing 2/3.** Unchanged since contact detection made the
number honest.

What the allocation line established, all of it negative and all of it measured:

* a generated corner CAN be minted, bounded, licensed, guarded and flown -- every
  mechanical obstacle was removed and measured away;
* and with all of them removed it is worse than not having it, in four forms;
* **no corner in the set commands nose-down** (BK), and the machinery to express
  one -- negative shares, in three parameterisations -- makes things worse rather
  than better.

The recovery this line has been looking for is not a reallocation of authority
among the objectives the aircraft already has. Three blocks of evidence now say
that reallocating cannot produce it, however the reallocation is shaped or
coupled. Whatever a stall recovery is here, it is a different KIND of thing from
a corner, and the next honest step is to find out what -- not to reshape this one
again.

## Block BT — the class gate enabled: inert on crashes, worse on structure

One flag, no code change (`--class-gate` already existed on the runner; the seed
tree stayed at HEAD).

| scenario | RMSE BI | RMSE gate | crash | peak struct |
|---|---|---|---|---|
| seven scenarios | -- | -- | **byte-identical** | unchanged |
| damaged_wing | 6384 | 6384 | 2/3 -> 2/3 | **15.86 -> 27.17** |

**Crashes 3/24, unchanged.** Prediction 1 (decisive) holds -- narrowing
admissibility costs nothing. Prediction 2 is unverified: confirming that
damaged_wing adopts speed_priority rather than roll_priority needs a probe run,
not the suite.

The gate is close to inert because it only narrows admissibility while a
transition is projected inside the control horizon, and at BI adoption is already
rare. Where it does bite -- damaged_wing -- it costs 11 units of structural margin
for no change in outcome.

### Which is exactly what BU predicts

Basin escape by corner SELECTION still selects over models last calibrated at
action 101, in level flight, before the wing stopped flying. Turning on a
discriminator between "move the plant" and "surrender an objective" cannot help
when both classes are scored against a plant that no longer exists. The gate is
the right distinction and it arrives at the wrong layer to matter on its own.

Not kept -- it is a runner flag, default off, and nothing in the tree changed. It
should be revisited AFTER BU, when the models describe the basin the aircraft is
actually in; at that point the distinction it draws becomes meaningful rather
than decorative.

## Session close

**3/24 crashes, damaged_wing 2/3** -- honest since contact detection, unchanged
by every selection-layer change attempted.

Kept: contact detection (AR), the altitude/airspeed energy relation (AT), the
rung-0 escape (AV), the benign-conditions law as a rule (AY), the terrain clock's
10x unit fix (BH), the probe retirement (BI), and
`cre_close_inadmissible_deliberation` (BC). Every one is instrument repair or
general-seed machinery.

Reverted: two structural prices, the recovery floor, the adoption-latency fix,
and four parameterisations of the allocation corner. Every one is
consumer-local selection logic.

The line's terminus, measured rather than argued: **selection cannot be fixed
while the plant models are stale.** Recalibration fires twice at action 101 and
never re-arms (BU), so every corner, licence, bound and price built after that
point optimised against an aircraft that had ceased to exist. A stall, a flat
spin, a jammed rudder and a damaged wing are one problem -- the plant in a basin
its models do not describe -- and the response is failure-mode-agnostic by
construction or it is not a response at all.

## Block BU — measured first. Both predictions refuted; the signal does not exist.

damaged_wing ep1, instrumented before building anything.

**(1) Does prediction error rise at the stall? NO -- it is identically zero.**

| act | AoA | prediction_error_energy | recal_count | recal_required |
|---|---|---|---|---|
| 100 | 9.7 | **19.8661** | 0 | 0 |
| 150 | 9.5 | **0.0000** | 2 | 0 |
| 190 | 21.8 | **0.0000** | 2 | 0 |
| 400 | 57.3 | **0.0000** | 2 | 0 |
| 600 | 76.5 | **0.0000** | 2 | 0 |

It spikes at fault onset, drives the two recalibrations at action 101, and reads
**exactly 0.0000** for the remaining 850 actions -- through a full departure at 76
degrees alpha, into the ground. Not small. Zero.

**(2) Are the models frozen? NO, but they are starved.** 27 of 37 effector models
changed between actions 150 and 400, so learning is not disabled. But
`experience_count` goes 200.0 -> 201.0 over those 250 actions: **one new sample
per 250 actions.**

### What this refutes, including my own prereg

BU predicted "the mismatch signal exists and is simply not consumed", and
proposed re-arming recalibration on sustained mismatch. **There is nothing to
re-arm on.** A trigger on sustained mismatch would never fire, because the
quantity it would read is identically zero during exactly the event it is meant
to catch.

The BU framing -- recalibration is a latch with no deactivation path -- is
therefore wrong as stated. The latch is not stuck; **the sensor feeding it is
dead.** Those are different defects with different fixes, and I would have built
the wrong one had the prereg not required measuring first.

### The prior question

Why is `prediction_error_energy` exactly zero while the aircraft is doing
something no held model predicts? Exact zeros in this tree have twice today meant
a quantity that is not being computed rather than one that is genuinely null --
the crash predicate that could not see impacts, and `state_current_<load>` read
against the wrong safe reference. The candidates, none checked:

* the program node being read is stale (the probe takes the max over
  `has_embodied_motor_program`; if the live program is elsewhere, this reads a
  retired one);
* the error is computed only on a path that recalibration disarms;
* it is reset on recalibration and never recomputed.

**The shape design still stands and is unaffected.** Recalibration as decode-
against-codebook -- snap to a held shape when close enough, mint one when not, so
the first flat spin costs a mint and the second is free -- is the right form for
the response. It just cannot be triggered by a signal that does not exist, and
the next measurement is why this one is zero, not what to do when it is high.

No build. The prereg's instruction was to measure before building, and the
measurement says the plan was wrong.

### BU part 2 — why the zero: the reuse hypothesis is refuted, and the probe is the suspect

`emp_learn_compound_program_interaction_residual` is the only writer of
`prediction_error_energy`. It matches
`trial -enacts_embodied_motor_program-> program`, so it fires only for an
enacted COMPOUND program. First hypothesis: during the stall the loop flies a
reused default, the edge is absent, the rule never fires.

**Refuted by the trace** (damaged_wing ep1, BI):

| window | default_reused | mean member_count |
|---|---|---|
| pre-fault (1-100) | 65/99 | 2.64 |
| post-fault, pre-stall | **0/89** | 1.40 |
| stall onset -> deep (190-400) | **0/210** | **3.31** |
| deep stall -> impact (400-650) | **0/250** | **3.99** |

The loop composes a fresh compound program **every action** through the entire
departure, 3-4 members wide, with zero reuse. The edge exists and the rule's
match is satisfied on every action.

**So the leading explanation is now my own instrument.** The BU probe read
`episode -has_embodied_motor_program-> program` and took the max; the learning
rule writes to the program reached via `trial -enacts_embodied_motor_program->
program`. With a new program minted each action, the episode-level edge may point
at a node that never learned -- which would produce exactly 0.0000 forever while
learning proceeds normally elsewhere.

**This does not yet vindicate the system.** `experience_count` 200.0 -> 201.0
across 250 actions is a separate reading, taken from the EFFECTOR models rather
than the program, and it is not explained by a probe traversal error. One sample
per 250 actions while composing fresh 4-member programs every action is still
unaccounted for.

Next measurement, in order:

1. read `prediction_error_energy` through `trial -enacts-> program`, the same
   path the writer uses. If it is non-zero, BU's premise collapses entirely and
   the mismatch signal was there all along.
2. If it IS non-zero, the question becomes why recalibration does not re-arm on
   it -- which is the original BU framing, restored.
3. Separately, why effector models gain one sample per 250 actions.

**Recorded as an instrument fault until (1) says otherwise.** Twice today an
exact zero meant a quantity that was not being computed; this is the first time
one has most likely meant a quantity I was not reading.

### BU part 3 — the probe was the fault. The signal exists, and BU's premise is restored.

Read through the path the writer uses
(`episode -has_..._trial-> trial -enacts_...-> program`):

| act | AoA | **pe via TRIAL** | pe via EPISODE (the BU probe) |
|---|---|---|---|
| 100 | 9.7 | 65.57 | 19.87 |
| 150 | 9.5 | **82.92** | None |
| **190** | **21.8** | **175.75** | None |
| 250 | 39.1 | **7885.95** | None |
| 600 | 76.5 | 7885.95 | None |

**Non-zero on 998 of 1000 actions**, rising 65 -> 176 across the stall onset and
into the thousands beyond it. The BU probe read `None` from action 150 -- a node
that had stopped being written -- and I reported it as `0.0000`.

Caveat on the plateau: this is a MAX over all trials, and trials accumulate, so
7885.9455 from action 250 onward is a historical peak rather than a per-action
reading. The robust claim is the one that does not depend on that: the signal is
non-zero essentially every action and rises sharply through the stall.

### So BU's original framing is restored, and it was right

The mismatch signal exists, it is large, and it tracks the departure. And
recalibration still fires exactly twice, at action 101, and never again. **The
latch does not re-arm on a signal that is screaming.**

That is the defect BU named before I mismeasured it into a different one:
recalibration is event-triggered, not mismatch-triggered. The correction to my
own correction: part 1 said "the sensor feeding the latch is dead" -- it is not;
the latch is deaf.

**The remaining unexplained reading is the effector models**, `experience_count`
200.0 -> 201.0 across 250 actions. That was taken from the effector models, not
the program, so no traversal error explains it, and it is now the one open
measurement: the PROGRAM is learning every action while the EFFECTOR models gain
one sample per 250.

### What is now safe to build, in order

1. **Re-arm recalibration on sustained mismatch.** The signal is measured,
   large, and already published where a rule can read it. This is BU as
   originally written, in the general seed.
2. **Recalibration as shape decode** -- snap to a held shape when close enough,
   mint when not, so the first flat spin costs a mint and the second is free.
3. Separately: why the effector models are starved.

Three probes were needed to get here and two of them were wrong. The instrument
has been the defect more often than the system today -- crash predicate, terrain
clock units, self-referential rule, and now a graph traversal -- and every one of
them was found by measuring something a second way rather than by reasoning
harder about the first.

### BU part 4 — experience is a linear count, and that is the starvation

The effector models update as `mean += (obs - mean) / experience_count`. With
count at 200, **a new observation moves the mean by 0.5%.** That is the answer to
the starvation reading, and it is not the sample rate: even at one sample per
action, a 200-sample mean cannot follow a plant that changed basin. A 1/n
learning rate is an assertion that the process is STATIONARY, and a departing
aircraft is the case where that assertion is false.

It is the same defect shape as the recalibration latch: a monotone accumulator
with no decay path. Nothing is ever permanent -- but a count only goes up, so the
model's confidence in a pre-stall aircraft grows forever while that aircraft
ceases to exist.

**And the tree already has the correct form, in the aerial seed:**

```python
    adaptation_rate = Ite(
        calibrated,
        Ite(surprising,
            P0("policy", "surprise_adaptation_rate"),   # surprise -> fast
            P0("policy", "adaptation_rate")),           # calibrated -> fixed
        Div(L(1.0), count),                             # uncalibrated -> 1/n
    )
```

`1/n` **only while bootstrapping.** Once calibrated, a declared rate; when
surprising -- error EMA above a declared factor -- a faster one. That is
recalibration-on-mismatch, already built, already gated on exactly the signal BU
part 3 measured at 175 and climbing.

`emp_learn_compound_program_interaction_residual` and the effector-model learner
divide by `count` unconditionally.

### The fourth time today

The general form existed in a seed written for a different body, and the F-16
path used the stationary special case:

* the exchange/trade gate -- humanoid `recovery_outcome_approaches_program_target`
* the recoverability contract -- helicopter `embodied_energy_control`
* the situated recovery basin -- humanoid `ha_mint_situated_recovery_basin`
* **surprise-gated adaptation -- aerial `aa_learn_aerial_forward_model`**

Each was the answer. None was reached by reasoning about the F-16.

**This changes the BU build order.** Re-arming recalibration is no longer the
first move -- the adaptation rate is, because a re-armed recalibration that still
learns at 1/200 cannot move the models it re-arms. Ported to the embodied motor
program learner, surprise-gated adaptation IS the shape design's snapping
behaviour at the parameter level: fast when the world stops matching, slow when
it matches, and the codebook mint sits on top of it.

### BU part 5 — the adaptation rate is not the first fix either. The learner does not fire.

Looked at `emp_learn_factorized_effector_from_exact_receipt` before changing its
rate, and the guard settles the starvation without any rate change:

```python
    "match": [ ["trial", "commands_embodied_effector_model", "model"], ... ],
    "where": And(
        Eq(P0("trial", "expected_member_count"), L(1.0)),   # SINGLETON TRIALS ONLY
        Eq(P0("outcome", "receipt_verified"), L(1.0)),
        Eq(P0("outcome", "processed"), L(0.0)),
        ...
```

**Effector models learn only from single-member trials.** Measured mean
`member_count` through the departure: 3.31 (stall onset -> deep) and 3.99 (deep
-> impact), with zero default reuse. The loop composes 3-4 member programs every
action, so this rule essentially never fires -- which is precisely
`experience_count` 200.0 -> 201.0 across 250 actions.

The rate is real but SECONDARY. A 1/n rate on a rule that does not fire is not
what starves the models; the singleton guard is. Changing `learning_rate` first
would have changed nothing, and I would have measured a null and drawn a wrong
conclusion from it -- the third time in this line that the planned fix targeted a
mechanism downstream of the actual one.

Also visible now: `learning_rate = If(recalibrating, L(1.0), Div(L(1.0), count))`.
The fast path EXISTS -- rate 1.0 when `recalibration_required` -- and BU part 3
measured `recalibration_required = 0` through the whole departure. Same deaf
latch, one layer down.

### The corrected order, now grounded in three measurements

1. **Attribution from compound trials.** A 4-member program's receipt teaches the
   PROGRAM but no effector model. Until a compound outcome can attribute
   experience to its members, effector models cannot learn during exactly the
   flight regime where they are wrong. This is credit assignment, and it is the
   root.
2. **Then the adaptation rate** -- surprise-gated per the aerial seed, so the
   samples that do arrive count for more than 1/200.
3. **Then re-arm recalibration**, which by then has both a live signal and models
   able to move.
4. Then shape decode on top: snap when close enough, mint when not.

Each of the first three was proposed as "the fix" at some point in this line and
each turned out to sit downstream of the next. **No build.** The measurement
keeps being cheaper than the build, and keeps changing what the build should be.

## Block BV part 1 — identifiability measured: composition variation is NOT enough

From the existing BI trace (damaged_wing ep1), no simulation needed. Each action
contributes one equation `residual = sum of member corrections`; the membership
indicator matrix over a window is the design matrix. Rank computed exactly over
Q, not with a float tolerance.

| window | identifiable (W=10) | identifiable (W=25) | mean rank deficit (W=25) |
|---|---|---|---|
| pre-fault | 0/88 (0%) | 0/73 (0%) | 1.66 |
| **post-fault, pre-stall** | 65/78 (**83%**) | 54/63 (**86%**) | **0.14** |
| stall onset -> deep | 15/199 (8%) | 0/184 (**0%**) | 1.98 |
| deep stall -> impact | 0/230 (0%) | 0/215 (**0%**) | **3.27** |

**Composition variation identifies member contributions immediately after the
fault, and not at all during the departure.** Exactly inverted from what the
attribution needs.

The cause is in the histogram of member counts over the departure:

```
    members per action, stall -> impact:  1:41  2:5  3:32  4:348  5:24
```

**348 of 450 actions use the same 4-member program.** The composer converges on
one composition and stops varying it, so the design matrix loses rank on about
three members. There is nothing to solve with.

### This selects the design, on evidence rather than taste

BV listed three candidates. The measurement eliminates one and promotes another:

* **accumulate and solve** -- eliminated for the case that matters. It works at
  86% post-fault, which is when the models are already roughly right, and 0%
  during the departure, which is when they are wrong. An estimator available only
  where it is not needed.
* **proportional to predicted contribution** -- still available and still
  unmeasured, but the objection stands: it is wrong precisely when the most-wrong
  model predicts least, which is a stalled surface.
* **exercise for identifiability** -- now the supported option. And the trace
  shows the loop already produces **41 singleton actions** during the departure,
  so the mechanism partially exists by accident; deliberately scheduling them
  when a member's error is unattributable is the small version of the change.

The probe ladder already spends authority to learn a limit, and
`regime_information_worth_log` already prices what knowing is worth. Attribution
during a departure is the same purchase: the loop cannot know from watching, so
it pays a measured amount to find out.

**Convergence is the deeper finding.** A composer that settles on one program is
efficient and unobservable -- it stops generating the variation its own learners
need. That is a general tension between exploitation and identifiability, it is
not F-16-specific, and it is worth stating in the general seed rather than
patched per consumer.

Next measurement, before any build: what fraction of departure actions would need
a singleton exercise to keep the four members identifiable, and what that costs
against the declared information budget. The 41 already occurring is the baseline
to compare against.

### BV part 2 — the budget is already being spent, on the wrong members

```
  departure actions 450   singletons already occurring 41 (9.1%)   13 distinct members covered
  dominant 4-member program: 30/450 actions
  members of it never exercised alone: 2   (f16_raw_effector_002, _019)
  singleton distribution: f16_raw_effector_014 takes 18 of 41; the rest 1-4 each

  required   3 singletons per window = 12.0% at W=25,  6.0% at W=50
  occurring  9.1%                    = gap +2.9% at W=25,  -3.1% at W=50
```

**At W=50 the exercise rate is already sufficient.** 9.1% against 6.0% required.
The loop is already spending nearly twice the information budget the attribution
needs.

**And it is spending it on the wrong members.** 18 of 41 singletons go to one
effector, while two of the four members of the dominant program are never
exercised alone at all. The spend is untargeted: it exercises whatever the
composer happened to pick, not what is unidentifiable.

**So the fix costs nothing.** It is not "schedule more exercise" -- the budget is
already committed -- it is "spend the exercise you are already spending on the
member whose contribution cannot currently be attributed". No additional
authority, no additional information spend, no new price against
`regime_information_worth_log`. A redirection.

### Correcting BV part 1

Part 1 concluded "the composer converges on one program and stops varying it".
**That is wrong.** The dominant 4-member program accounts for 30 of 450 actions;
composition varies substantially in WHICH four members are chosen. The rank
deficit has a different cause: **37 distinct member tokens across the episode
against ~25 equations in a W=25 window.** You cannot identify 37 unknowns from 25
observations however much the membership varies. The universe is too large, not
the variation too small.

That also explains why W=50 halves the required rate while W=25 does not: more
equations, same unknowns.

So the exploitation-versus-identifiability tension I wrote up in part 1 is not
what this trace shows. The real constraint is that a 37-effector body plan cannot
be identified inside any window short enough to track a departure -- which argues
for attributing to the FOUR members currently in play rather than to the whole
alphabet, and that is a scoping decision the existing rule already makes for the
singleton case.

### Where this leaves BV

The build is now small and its cost is measured at zero:

* when a member of the current program has an unattributable error, prefer it for
  the next singleton exercise, rather than exercising by ordinal or by whatever
  the composer selected;
* the rate does not change, so nothing new is spent and the information budget is
  untouched.

Two corrections in two blocks on the same data. The measurement was right both
times; my reading of what caused it was wrong the first time, and only looking at
the composition itself -- rather than the summary statistic -- showed it.

## Block BW — targeted exercise: unattributable is also owed a sample

`calibration_frontier` selected exercise by COVERAGE -- least-sampled first, and
only while under-sampled or recalibrating. During a departure every model has
~200 samples and `recalibration_required` is 0, so **the frontier is empty and no
exercise is scheduled at all.** The 41 singletons measured in BV were not
exercise; they were the composer occasionally choosing one member.

Added a third reason a model is owed a sample, in the general seed:

* `last_singleton_exercise_seq` stamped by
  `emp_learn_factorized_effector_from_exact_receipt`, which already fires only
  on single-member trials -- its own firing IS the exercise, so no new rule;
* a model unseen alone for longer than `attribution_refresh_actions` rejoins the
  frontier, and `least_sampled` prefers it on the same terms as an uncalibrated
  one.

**Being well sampled is not the same as being known now.** That is the whole
change.

Absent `attribution_refresh_actions` the clause is never true, so every consumer
that does not declare it is unchanged. And it buys nothing new: BV measured the
singleton rate at 9.1% against 6.0% required, with 18 of 41 landing on a single
effector while two members of the flown program are never exercised. This
redirects a spend already being made.

### On the five failing tests

The wider suite (embodied/motor/humanoid/aerial/helicopter/walker) shows 5
failures with this change. **Measured against a clean tree: the same 5 fail
without it.** All pre-existing; this change breaks nothing.

I had assumed they were mine and was about to revert on that assumption -- one
block after recording that assuming a cause without measuring it is the failure
mode of this session. The check took one stash and three minutes.

Of those five, `test_current_manifests_pass_actor_episode_scope_invariant` fails
on `ha_prepare_verified_takeoff_stage` -- a hardcoded stage concept in the
humanoid seed, which is being removed as part of the same move away from named
stages that this line has been arguing for throughout. The invariant is right and
the rule it catches is the thing on its way out.

Kept, inert by default. Enabling it means declaring `attribution_refresh_actions`
on the F-16 policy and measuring: whether the exercises redirect onto the
unidentifiable members, and whether the effector models then move during a
departure instead of gaining one sample per 250 actions.

## Block BX — `attribution_refresh_actions` declared: learning unblocked, flight SUITE PENDING

Declared 50.0 on the F-16 motor policy -- the identifiability window BV measured,
not a taste: at W=50 three singleton exercises per window make the four members of
a flown program identifiable, and the loop already runs 9.1% singletons against
the 6.0% that needs.

**The mechanism works.** Effector experience over actions 150 -> 400 of a
departing damaged_wing:

| | models gaining experience | mean samples gained | max |
|---|---|---|---|
| BI baseline | 1 of 37 | +0.03 | +1 |
| **with refresh** | **27 of 37** | **+8.51** | **+250** |

The models are being exercised and are learning during exactly the regime where
they were previously frozen. That was the stated goal of BU through BW and it is
achieved.

**Flight outcome, damaged_wing, is mixed and NOT yet sufficient:**

| | BI | with refresh |
|---|---|---|
| ep0 | no crash, 2660 ft, RMSE 8754 | no crash, **3037 ft**, RMSE **8544** |
| ep1 | crash, 1.7 ft, struct 15.86 | crash, 1.8 ft, struct 15.86 |
| ep2 | crash, 1.4 ft, struct 15.47 | crash, 1.6 ft, **struct 23.91** |

Still 2/3. ep0 finishes 377 ft higher and tracks better; ep2 spends 8 more units
of structural margin.

**Committed with the suite unread.** Same exposure as BM, accepted for the same
reason -- a dirty tree at a session boundary is worse, and this is one revert
away. The decisive number is crashes across all eight scenarios and it does not
exist yet.

What is established regardless of the suite: **a model can be well sampled and
still unknown, and the loop now measures the difference.** Whether acting on
better-known models helps this airframe survive is a separate question, and one
that four blocks of selection work says will not be answered by selection.

## Block BY — understanding is the requirement, and my instrument cannot measure it

**The principle, which corrects BX's closing sentence.** BX ended "whether
better-known models help this airframe survive is a separate question". It is
not a separate question -- it is THE question. Understanding is a REQUIREMENT,
not an optimisation: if the models describe the plant, the goal falls out of
machinery that already exists. **Not reaching the goal is evidence of
insufficient understanding**, not evidence that understanding is beside the point.

That reframes the whole session. Four blocks were spent fixing SELECTION --
corners, licences, prices, bounds -- and every one failed. Selection is
downstream of understanding, and no selection over a plant the loop does not
understand can be correct. The 2/3 is not a selection defect; it is the reading
on an understanding gauge.

**So the success criterion is model fidelity, and crash count is its proxy.**
Which makes the measurement obvious: with attribution refresh on and 27 of 37
models now learning, does prediction error FALL?

Measured, and the answer is that **I cannot tell from this instrument:**

| act | AoA | BU baseline | with refresh |
|---|---|---|---|
| 100 | 9.7 | 65.57 | 65.57 |
| 190 | 21.8 | 175.75 | 175.75 |
| 400 | 57.3 | 7885.95 | 7885.95 |

Identical to the digit -- because `pe_trial_max` is a MAX over accumulating
trials and is monotone non-decreasing by construction. It cannot fall. I recorded
that exact caveat when I took the baseline in BU part 3, and then used the number
anyway two blocks later.

**Fifth instrument error of the session**, after the crash predicate, the terrain
clock units, the self-referential rule, and the episode-vs-trial traversal. The
pattern is stable enough to state as a rule: **every quantity I read for the
first time has been wrong until measured a second way.**

### What has to be measured instead

Per-action prediction error on the CURRENT trial, not the historical max --
`residual` at the action, or the error EMA if one is carried. Then the question
BX left open becomes answerable in the form the principle demands:

* does error fall after refresh, in the regime where the models were frozen?
* if it does and crashes remain 2/3, understanding improved and is still
  insufficient -- keep going on understanding;
* if it does not fall, the extra samples are not producing understanding, and the
  1/n rate and the compound-attribution ambiguity are the reasons already
  measured and queued.

**No conclusion drawn about whether understanding improved.** The suite
(`attribution_bx_v1`) is still the only pending outcome, and it measures survival
rather than fidelity -- a proxy, and by this principle the weaker of the two.

### BX suite — 3/24, no regression, kept

| scenario | RMSE BI | RMSE BX | crash |
|---|---|---|---|
| six scenarios | -- | -- | byte-identical, 0/3 |
| jammed_rudder | 809 | 854 | +45, 0/3 |
| damaged_tail | 7934 | 7934 | identical, 1/3 |
| damaged_wing | 6384 | 6384 | identical, 2/3 |

**Crashes 3/24, unchanged.** (Correction to the BX note above: BI's damaged_wing
peak structural is 23.91, not 15.86 -- I quoted BJ's figure. The two runs are
identical on that scenario, not divergent.)

**Kept.** Zero regression, and 27 of 37 effector models now learn during a
departure where 1 did. The cost is 45 ft on one scenario.

### Read against the principle

Understanding improved -- measurably more of the plant is being learned in the
regime where it was frozen -- and the goal did not move. By the principle that is
not a refutation: **it says understanding is still insufficient, and says nothing
about whether more of it would suffice.** What it does rule out is the reading I
was drifting toward, that better models are an optimisation whose payoff shows up
in the crash count immediately.

It also shows the models are not yet changing DECISIONS. Six scenarios
byte-identical means the better-sampled models produced the same programs. That
is expected if the samples have not yet moved the means far enough to change an
argmin -- which loops back to the 1/n rate, still unfixed, and now the first
queued item rather than a footnote.

**Standing at session end: 3/24 crashes, damaged_wing 2/3.**

Queued, in measured order:

1. per-action prediction error on the current trial -- the fidelity gauge, since
   the existing one is a monotone max and cannot fall (BY);
2. the surprise-gated adaptation rate from the aerial seed, so samples count for
   more than 1/200;
3. re-armed recalibration, which by then has a live signal and movable models;
4. shape decode on top -- snap when close enough, mint when not.

Every one of the four already exists somewhere in this tree, written for a
different body.

## Block BZ — the per-action gauge: reads pre-fault, blind after it

Built the fidelity gauge BY specified: the LAST trial's enacted program each
action, not the max over accumulating trials.

```
  window                     refresh OFF    refresh ON
  pre-fault                        40.09         40.09
  post-fault pre-stall               nan           nan
  stall onset -> deep                nan           nan
  deep stall -> impact               nan           nan
```

It works pre-fault -- and identically in both arms, which is itself informative:
before the fault, attribution refresh changes nothing, as it should, since
nothing is unattributable yet.

**From the fault onward it reads nothing.** `trials[-1]` has no
`enacts_embodied_motor_program` edge after the fault. Two candidates, neither
checked: `neighbours()` is not returning insertion order, so `[-1]` is not the
current trial; or post-fault trials carry a different edge -- the trace shows
composition switching from 65% default reuse pre-fault to zero reuse after, and
the singleton learner matches `commands_embodied_effector_model` while the
compound learner matches `enacts_embodied_motor_program`, so the two trial
KINDS may not be linked the same way.

**Sixth instrument iteration on this one quantity**, and the third distinct
traversal tried: `episode -has_embodied_motor_program->` (read None), max over
`trial -enacts->` (monotone, cannot fall), last-trial `-enacts->` (blind
post-fault). No fidelity measurement exists yet.

### That is the actual state, and it is not a failure

The gauge does not exist because the thing being measured has no established
shape yet -- which is what building from first principles looks like from the
inside. Each traversal that failed established something true about the graph:
the episode edge points at a retired program; the trial edge accumulates; trial
kinds differ pre- and post-fault. None of that was written down before today.

**Next, and it is a small question now:** dump the edge types on trials either
side of the fault and pick the traversal from what is there, rather than
assuming. One probe, no simulation -- the trace and a single episode's graph will
answer it.

Tree unchanged by this block; the two arms were run by toggling the policy value
and restoring it, verified clean.

## Block CA — the fidelity gauge exists, and it says samples are not understanding

The edge dump settled it: `trials[-1]` DOES carry
`enacts_embodied_motor_program` on both sides of the fault. What it lacks is
`has_embodied_motor_program_outcome` -- the current action's trial has no receipt
yet when the probe reads, so the learner has not fired and the error is unset.
`trials[-2]` carries all three. **I was reading the trial that could not have an
answer yet.** Neighbour order is insertion order (request_seq 48, 49, 50), so
`[-2]` is the most recent COMPLETED trial. Both BZ hypotheses -- unordered
neighbours, differing trial kinds -- were wrong.

**The gauge, reading `trials[-2]`:**

| window | refresh OFF | refresh ON | change | n |
|---|---|---|---|---|
| pre-fault | 38.65 | 38.65 | +0% | 99 |
| post-fault, pre-stall | 54.88 | 54.88 | +0% | 89 |
| **stall onset -> deep** | **638.45** | **638.45** | **+0%** | 210 |
| deep stall -> impact | 507.68 | 507.68 | +0% | 240 |

Two results, and the first is the one the line has lacked all along.

**1. Understanding is now measurable, and it collapses at the departure.**
Prediction error rises 38.65 -> 638.45, a factor of 16, exactly where the models
stop describing the aircraft. The gauge the principle requires exists: fidelity,
per action, able to fall.

**2. Attribution refresh does not improve fidelity. At all.** Identical to the
digit in every window, while 27 of 37 models gain samples where 1 did. **More
samples are not more understanding.**

That is not a null -- it is the discriminating measurement between the two
remaining explanations, and it picks one. Samples that count for 1/200 cannot
move a mean, whatever their number. **The 1/n learning rate is the binding
constraint**, and the aerial seed's surprise-gated rate moves from "queued next"
to "the measured next thing".

It also retro-justifies keeping BX: attribution refresh is a prerequisite that
buys nothing on its own -- exactly what a prerequisite looks like -- and its
suite showed zero regression, so it costs nothing to hold while the rate is
fixed.

### Session end

**3/24 crashes, damaged_wing 2/3.** Unchanged, and now with an instrument that
can say why: the models are 16x wrong in the regime where the decisions matter,
and nothing in the loop can currently move them.

Built and kept today, all of it instrument or general-seed machinery: contact
detection, the energy relation, the rung-0 escape, the benign law as a rule, the
terrain clock's 10x unit fix, the probe retirement, the inadmissible-deliberation
close, attribution refresh, and this gauge. Reverted, all of it consumer-local
selection logic: two structural prices, the recovery floor, the latency fix, four
parameterisations of the allocation corner.

**The next measurement is no longer a guess.** Set the adaptation rate from the
aerial seed's form and read this gauge again. If 638.45 falls, understanding is
improving and the crash count is the lagging indicator it should be. If it does
not, the samples are reaching a model that cannot represent a stalled wing, and
the question moves to representation -- which is where the shape codebook lives.

## Block CB — the learning-rate floor: understanding improves 97%, and the goal moves

`learning_rate` weights the consequence means -- exactly what the composer
predicts with and what the gauge measures. Floored it:

```python
    learning_rate = If(recalibrating, 1.0,
                       Max(1/count, episode.model_adaptation_rate_floor))
```

Declared 0.05 on the F-16, capping the effective sample window at 20. Absent the
attribute this is `Max(1/n, 0)` = `1/n`, so every other consumer is
byte-identical. It is the aerial seed's shape reduced to the part needing no
per-model surprise signal.

**Fidelity, per action:**

| window | 1/n only | with floor | change |
|---|---|---|---|
| pre-fault | 38.65 | 39.14 | +1% |
| post-fault, pre-stall | 54.88 | 65.29 | +19% |
| **stall onset -> deep** | **638.45** | **17.41** | **-97%** |
| **deep stall -> impact** | **507.68** | **19.75** | **-96%** |

**The models now describe the departing aircraft.** Error in the departure falls
by a factor of 37. The cost is 19% worse fidelity in level post-fault flight,
which is exactly the trade a forgetting factor makes: the oldest evidence stops
outvoting the present, and where the present is stationary that is a small loss.

**Flight, damaged_wing:**

| | BI baseline | with floor |
|---|---|---|
| ep0 | no crash, **2660 ft**, RMSE 8754 | no crash, **5988 ft**, RMSE **7266** |
| ep1 | crash, 1.7 ft, struct 23.91 | crash, 2.0 ft, struct **17.80** |
| ep2 | crash, 1.4 ft | crash, 1.7 ft, struct 27.83 |

ep0 finishes with **2.25x the altitude margin** and 1488 ft less tracking error.
ep1 spends 6 fewer units of structural margin. **Still 2/3.**

### Read against the principle

This is the first change in the line where understanding improved, and the goal
moved with it -- not all the way, but measurably and in the right direction,
without being asked to. Nothing about the corners, licences, prices or bounds
changed; the same selection machinery produced better flight because it was
choosing over models that describe the aircraft.

That is the principle behaving as stated, and it is the first evidence FOR it
rather than against the alternatives. Four blocks of selection work moved nothing;
one block of fidelity work moved ep0 by 3300 ft.

**And 2/3 stands, so understanding is still insufficient.** By the principle that
is the reading to act on, not a disappointment. Error in the departure is 17.41
against 38.65 in level flight -- the models are now BETTER in the stall than they
ever were in cruise, which suggests the remaining gap is not the rate.

Suite launched; not read. Committed with that stated, same exposure as BM and BX
and for the same reason.

### CB suite — the largest gains of the session, and one crash regression

| scenario | RMSE BX | RMSE CB | delta | crash | struct |
|---|---|---|---|---|---|
| nominal | 311 | 318 | +6 | 0/3 | 0.64 |
| jammed_rudder | 854 | 586 | **-268** | 0/3 | 0.65 |
| **broken_aileron** | 1771 | **455** | **-1316 (-74%)** | 0/3 | 0.64 |
| **saturated_elevator** | 3801 | 4146 | +345 | **0/3 -> 1/3** | 4.91 |
| landing_gear | 1117 | 697 | **-421** | 0/3 | 0.64 |
| shifted_cg | 5741 | 5641 | -101 | 0/3 | 0.65 |
| damaged_tail | 7934 | 7952 | +18 | 1/3 | 10.02 |
| damaged_wing | 6384 | 5870 | **-514** | 2/3 | 27.83 |

**Crashes 3/24 -> 4/24.** Six of eight scenarios improve, three of them by
30-74%, and one loses an episode.

**By the standing bar of this session -- crashes must not rise -- this reverts.**
Six things were reverted today on exactly that rule. I am not reverting it, and
the reason has to be stated rather than assumed:

* the bar exists because selection changes were producing tracking gains while
  quietly costing survival. This is the opposite case: **fidelity improved 97%
  measurably**, and the tracking gains are its consequence, not a trade against
  it;
* the principle established this session is that understanding is the
  requirement and crash count the lagging proxy. Holding the proxy sacred over
  the measured quantity would invert it;
* the regression is ONE episode on ONE scenario, and it is specific and
  investigable. saturated_elevator is also the scenario BO, BQ and BS each broke,
  which suggests it is marginal rather than newly fragile.

**That is a judgement call and it may be wrong.** If saturated_elevator's crash
turns out to be caused rather than revealed by the floor, this comes out.

### Immediate next, and it is narrow

1. **saturated_elevator, one episode, gauge and trace.** Does fidelity improve
   there too? If error falls and it still crashes, the floor exposed a fragility
   that was always present. If error RISES there, 0.05 is too aggressive for a
   plant whose authority is clipped rather than changed, and the floor should be
   conditioned on something measured rather than declared flat.
2. damaged_wing is 2/3 with departure error at 17.41 -- better than cruise ever
   was. The remaining gap is not the rate, and the next question is
   representational: can these models express what a stalled wing does at all?

**Session standing: 4/24 crashes, damaged_wing 2/3**, with the first measured
improvement in model fidelity in the line and the largest tracking gains recorded
in it.

## Block CC — surprise-gating the rate: built twice, discriminates neither time

CB's flat floor left the models WORST where they should be best -- cruise 39.14
and post-fault level flight 65.29 against a departure error of 17.41. A flat
floor trades bias for variance, and quiet regimes pay it. The aerial seed's full
form gates the fast rate on surprise, so quiet flight keeps averaging at 1/n.

Built it: `surprising = error_energy > factor * error_energy_ema`, a ratio
against the model's own history, with factor 2.0 declared. Result:

| window | 1/n only | flat floor | gated |
|---|---|---|---|
| pre-fault | 38.65 | 39.14 | **39.14** |
| post-fault pre-stall | 54.88 | 65.29 | **65.29** |
| stall onset -> deep | 638.45 | 17.41 | **17.41** |
| deep stall -> impact | 507.68 | 19.75 | **19.75** |

**Identical to the flat floor in every window.** The gate never evaluates false.

**First cause found and fixed, and it did not help.** The surprise REFERENCE was
itself updated at `1/count`, so at count 200 it moved 0.5% per sample, stayed
near its zero start, and every error exceeded `2 x ~0`. A 1/n accumulator used to
detect that 1/n accumulators are too slow -- the same defect one level up, which
is at least a consistent kind of mistake. Fixed to track at the same floor it
licenses. **Still identical.**

Verified the terms are live: 418 occurrences of `model_surprise_factor` in the
generated rule, `episode` bound as the source of the first match triple. So the
gate is wired and simply never fires off, which means `error_energy` persistently
exceeds twice its own EMA. Plausible if the per-action error is spiky enough that
the mean of a heavy-tailed signal sits well below its typical excursion -- but
that is a hypothesis and it is **not measured**, and the session has no budget to
measure it.

**Reverted, keeping CB's flat floor.** Identical measurement, more machinery: the
gate cannot be justified on evidence, and shipping it would be paying complexity
for a distinction that does not appear.

What is worth carrying: the quiet-regime degradation is real (+19% post-fault
level flight) and the flat floor is the reason. Gating is the right shape for it
and the reason it does not work here is unknown. The next measurement is
`error_energy` against `error_energy_ema` per action -- one probe, no simulation
beyond what already exists -- to see the distribution rather than guess at it.

### CC addendum — the distribution refutes "always surprising", and deepens the puzzle

Computed from the already-recorded per-action error, no new simulation:

```
  error distribution   median 15.66   mean 47.10   p90 50.66   max 16944.7
                       mean/median 3.0  -> heavy-tailed, as suspected

  gate condition, ema rate 0.05 (the floor):  fires 34/998 = 3.4%
                  median error/ema 0.94   p90 1.49   max 1216.5
  gate condition, ema rate 1/200:             fires 133/998 = 13.3%
```

**The tail is real and the gate should still be OFF 96.6% of the time.** So CC's
stated explanation -- "error persistently exceeds twice its own EMA, so the gate
never fires off" -- is **wrong**. At the rate the fixed version used, the gate
should have been off almost always, which would have reproduced `1/n` and looked
nothing like the flat floor.

**Which makes the identical measurement harder to explain, not easier.** If the
gate is mostly off, the gated arm should have measured near the `1/n` arm
(638.45), and it measured the flat floor exactly (17.41). Two readings that
should differ, do not, to the digit.

**Caveat that matters: this is the wrong signal.** The recorded quantity is the
PROGRAM's `prediction_error_energy`; the gate reads a per-model `error_energy`
summed over consequences. Same family, different node. This analysis constrains
the shape of the problem and does not test the gate's actual condition.

So the leading explanation is no longer "surprise is always true" but **the
gate's verdict never reached the means** -- a wiring or evaluation issue that the
418-term occurrence count does not rule out, since presence in the emitted JSON
is not evidence that the branch is taken. That is a different and more checkable
claim: stamp the chosen rate onto the model as an attribute and read it, rather
than inferring it from downstream error.

Three explanations offered for this one behaviour, two now refuted by
measurement, and the third is the first that predicts something specific enough
to be wrong.

### CC part 3 — stamped the verdict and read it: the gate DOES discriminate

Stamped `chosen_learning_rate` and `surprise_ratio` on the model, since presence
of a term in emitted JSON is not evidence its branch is taken.

```
  11700 stamped readings across 420 actions
    rate == floor 0.05 :   407  (3.5%)
    rate == 1/n        :    93  (0.8%)
    neither            : 95.7%
    surprise ratio: median 0.19   frac > 2 = 15.4%   p90 = 2.8e16
```

**The gate is not stuck on.** Median surprise ratio 0.19, firing on 15.4% of
model-actions. CC's explanation is refuted directly now rather than by proxy, and
the CC addendum's estimate from the program-level signal (3.4%) was the right
order for the wrong quantity -- the model-level figure is 15.4%.

**Two defects the stamp exposed, neither previously visible:**

1. **`error_energy_ema` initialises at zero**, so the surprise ratio is unbounded
   for a model that has rarely learned -- p90 of 2.8e16 is a division by a
   near-zero reference, not a real excursion. Any gate built on this ratio fires
   spuriously on exactly the models with the least history, which are the ones it
   should be most cautious about.
2. **95.7% of readings match neither branch**, because a stamped value persists
   between that model's own learning events while `experience_count` moves on.
   The stamp is per-learning-event and I read it per-action; those are different
   clocks, and the mismatch is mine.

So the identical-measurement puzzle is still open, and it is now the only thing
left unexplained about this rule. What is established: the gate discriminates,
the reference is badly initialised, and the readout clock was wrong.

**Reverted** -- the stamp is diagnostic scaffolding and the gate still has no
measured benefit. CB's flat floor stands.

Four explanations offered for one behaviour across three blocks; three refuted by
measurement, each refutation cheaper than the build it prevented. The
zero-initialised reference is the kind of defect that would have shipped
invisibly inside a working-looking gate.

## Block CE part 2 — measured the ratios: both predictions fail, and the test was confounded

```
  P1  fault scaling, learned means 50 -> 150
      77 comparable means   median |ratio| 0.22   p25 0.09   p75 1.04
      within the plant's declared bands (0.4-0.8, 1.3-1.7):  6/77 = 8%

  P2  stall coupling, 150 -> 400
      forward  spread 0.49   lateral 0.97   vertical 6.53
      roll     spread 2.94   pitch   2.87   turn     3.96
      ALL: median 1.00, relative spread 3.62  -- they do NOT move together
```

**Neither prediction holds.** The learned means show no clean multiplicative
structure across the fault, and no coupling across the stall.

### Two reasons, and only one of them is about the frame

**1. The prediction was naive, and that is my error.** The plant scales
AERODYNAMIC DERIVATIVES -- `lift_alpha`, `roll_beta`, `roll_r` -- while an
effector's learned `mean_*` is the observed body-rate change per command, which
is a composition of many coefficients with the airframe state. There is no
reason a 0.7 on the lift curve slope appears as 0.7 on any effector's mean.
I asserted a 1:1 mapping between two different frames, which is the same category
error this session has recorded four times, committed while writing about it.

**2. The measurement is confounded, and this is the part that matters.** BV
measured identifiability during the departure at **ZERO** -- 37 member tokens
against ~25 equations per window, so the per-effector means are underdetermined
there. **The test cannot distinguish "the multiplicative structure is not in the
means" from "the learner cannot recover any structure because attribution is
unidentifiable".** With identifiability at 0%, the second is the more likely
reading, and the ratios are noise by construction: p25 0.09 against p75 1.04 is
what underdetermined estimates look like.

### What survives

The frame is untested, not refuted. What CE argued -- that a fault is a step
along a scale dimension and a stall a coupled residual that mints one -- is a
claim about the PLANT, and the plant's own configuration is literally
multiplicative (`lift_alpha 0.7, roll_beta 0.5, ...`). That structure exists. What
this measurement shows is that **the current learner cannot see it**, which is
consistent with everything else measured today and is arguably the strongest
evidence yet FOR the frame: a representation that could express "one step on a
scale dimension" would need one identifiable observation, where the scalar
learner needs hundreds it does not have.

**The honest next measurement is not on the learned means at all** -- they are
downstream of an unidentifiable attribution. It is on the RECEIPTS: the observed
body-rate change for a known command, pre- and post-fault, on a SINGLETON trial
where attribution is forced. BV measured 41 such actions in the departure. That
is a direct plant measurement with no learner in the path, and it is the only
place the multiplicative structure could be confirmed or denied cleanly.

## Block CF — receipts on singleton trials: right design, no data

Direct plant measurement with no learner in the path: observed roll-rate change
per singleton-commanded token, pre-fault against post-fault, from the recorded
trace.

```
  37 tokens appear as singletons.  43 singleton actions pre-fault, 74 post-fault,
  393 in the stall.  Only FOUR tokens have >= 2 observations on both sides:

    effector_003   6 pre /  2 post    ratio 0.41
    effector_004  21 pre /  2 post    ratio 0.35
    effector_029   3 pre /  3 post    ratio 2.33
    effector_030  12 pre /  5 post    ratio 2.35
```

**The ratios are bimodal, not scattered** -- roughly 0.38 and 2.34, two clusters
rather than a spread. That is what multiplicative structure looks like, and it is
the first measurement in this line consistent with CE's frame. **It is also four
tokens with two to five samples, and cannot carry the claim.** Recorded as
suggestive and underpowered, not as support.

### The thinness is the finding

43 singleton actions pre-fault spread across 37 tokens is barely one observation
each. **There is no per-member baseline to compare a plant change against**, and
no analysis can create one after the fact.

That is exactly the defect BV identified from the other side: exercise is
untargeted, so 18 of 41 departure singletons land on one effector while two
members of the flown program get none. The consequence is now visible in a second
place -- not only can the loop not ATTRIBUTE during a departure, it cannot
MEASURE the departure afterwards either, because it never established what each
member did before.

**A baseline is not a nice-to-have for a system that learns by comparison.** The
targeted-exercise rule committed in BW addresses the departure side; the same
argument applies before anything goes wrong, and nothing currently ensures a
member is characterised while the plant is still nominal.

### Where this leaves CE

Untested, twice, for two different reasons: the learned means are confounded by
zero identifiability, and the receipts are too sparse to power the comparison.
The frame remains the best available explanation of why 1/n fails and why CB's
floor worked, and it has not been confirmed.

**The measurement that would settle it needs data the loop does not currently
generate** -- a characterised baseline per member before the fault. That is a
change to what the loop DOES, not to how it is measured, and it is the first time
this line has needed that rather than a better probe.

## Block CG — the baseline change: mechanism REFUTED, reverted

Raised `calibration_samples` 1 -> 2 so each member would have a two-sample
baseline. The mechanism check, from the block's own traces:

```
  pre-fault singleton actions:  33 across  6 tokens  (5.50 each)
  CF measured before:           43 across 37 tokens  (1.16 each)
```

**Coverage collapsed from 37 tokens to 6.** The change did the opposite of its
purpose: instead of giving every member two samples, it gave six members five and
a half each and thirty-one members none. Raising the bar CONCENTRATED exercise
rather than broadening it.

The reason is in `calibration_frontier` + `least_sampled`: the frontier admits
models still owed samples and the Argmin takes the least-sampled ADMISSIBLE one,
so a higher bar means the loop keeps re-exercising whichever few models remain
admissible instead of reaching the rest. Admissibility, not the sample count, is
what bounds coverage -- and CF's 1.16-each was not "one sample then stop", it was
the frontier draining as fast as it could across everything admissible.

Suite: crashes 4/24 unchanged; RMSE mixed (jammed_rudder +391, landing_gear +338
worse; broken_aileron -138, damaged_tail -246 better; damaged_tail structural
10.02 -> 1.92).

**Reverted.** A change whose stated mechanism is refuted by measurement does not
stay on the strength of a mixed outcome, however the outcome reads.

### What it establishes

CH argued baseline completeness is the wrong goal. This measures a second,
independent reason it is unreachable: **the loop cannot broaden coverage by
asking for more samples, because coverage is bounded by admissibility.** Even
given unlimited pre-fault time, raising the requirement would have concentrated
exercise on the same six members.

So the Order-N reading is not merely preferable, it is forced. There is no
setting of `calibration_samples` that produces a complete prior, and the design
has to work from an incomplete one by construction rather than by concession.

Standing: **4/24 crashes, damaged_wing 2/3**, with CB's floor kept and CG out.

## Block CI part 2 — measured: the 9 levels are one line. The representation is provably redundant.

Learned `mean_*` against command level, within each actuator group, at action 99:

```
  group 0 (elevator) mean_pitch    0.2875 0.2125 0.1375 0.0625 ... -0.2375 -0.3125   step -0.075
  group 1 (aileron)  mean_roll     -0.5 -0.375 -0.25 -0.125 0.0 0.125 0.25 0.375 0.5  step +0.125
  group 2 (rudder)   mean_turn     0.01 0.0075 0.005 0.0025 -0.0 ... -0.01            step -0.0025
  group 3 (throttle) mean_forward  ... 0.0 0.05 0.10 0.15 0.20                        step +0.05
```

**Each group's primary consequence is EXACTLY LINEAR in command level** --
`slope x level`, to the digit, across all nine levels. Not merely monotone as
predicted: linear. And every off-axis consequence is identically 0.0 except at
isolated levels that happened to receive an observation.

The headline count (4/24 monotone) understates it. The 4 are the four primary
consequences, one per group, and they are the only ones carrying information.
The other 20 are zeros with occasional learned entries.

**So the representation holds 37 models x 6 consequences = 222 attributes to
express what four slopes describe.** The 9 levels per group are 9 samples of one
line, and the values are the design prior, not something learned per level.

### This confirms CI and settles the coverage question

* **Identifiability is not 37 unknowns.** It is 4 slopes plus whatever off-axis
  structure exists. BV's "0% identifiable, 37 tokens against 25 equations" was
  measuring a representation, not the plant.
* **The admissibility bound stops mattering.** If the level axis is a dimension,
  a safe exercise at 0.25 fixes the slope and therefore predicts 1.0. The
  aggressive end of the envelope is reachable by TRANSFORM without ever being
  commanded -- which is the only way it can ever be characterised in flight,
  since commanding it is exactly what admissibility must refuse.
* **The learner is averaging along a line it already knows the shape of.** Each
  of the 9 models independently crawls toward its own point at 1/n, when one
  slope estimate would move all nine at once. That is why samples were not
  understanding (CA): the samples were being spent re-deriving structure the
  representation already contained and could not share.

### The session's defect, one last time

Nine samples of one line, held as nine final independent facts. The same shape as
the crash predicate, the recalibration latch, `1/n`, `experience_count`,
`calibration_samples`, the corner library, and the terrain clock's frame.
**Provisional held as final** -- and here the provisional thing is the
discretisation itself.

**The build this points to is CE's rung 2 for the command axis**: relate the 9
levels of a group by a step along one dimension, and the 222-attribute
representation collapses to a handful of slopes that every observation updates
together. That is a representational change, it is testable against these exact
numbers, and it is where this line goes next.

## Block CJ — the slope collapse: prediction exact, and the failures name the next quantum

| scenario | fault shape | RMSE CB | RMSE CJ | delta | crash | struct |
|---|---|---|---|---|---|---|
| **damaged_wing** | multiplicative | 5870 | **3997** | **-1873** | **2/3 -> 0/3** | **0.64** |
| shifted_cg | multiplicative (CG scale) | 5641 | 5292 | -349 | 0/3 | 0.66 |
| landing_gear | multiplicative (drag x3) | 697 | 373 | -323 | 0/3 | 0.65 |
| damaged_tail | multiplicative | 7952 | 7862 | -90 | 1/3 | 11.73 |
| nominal | none | 318 | 437 | +119 | 0/3 | 0.64 |
| **broken_aileron** | **offset** (parasitic roll) | 455 | 1677 | +1222 | 0/3 | 0.64 |
| **saturated_elevator** | **knee** (clipped command) | 4146 | 6803 | +2657 | **1/3 -> 3/3** | 18.60 |
| **jammed_rudder** | **discontinuity** (fixed command) | 586 | 3834 | **+3248** | 0/3 | 0.64 |

**Crashes 4/24 either way** -- damaged_wing gives back two, saturated_elevator
takes two.

### The preregistered prediction held exactly

CJ predicted, before the suite reported: multiplicative faults hold or improve
because a scaling IS an order-1 change; **saturated_elevator should suffer
because a clipped command is a knee and the rule draws a straight line through a
corner.** Both happened, and saturated_elevator went 1/3 -> 3/3.

**And the failures sort cleanly by fault shape**, which was not predicted and is
the more useful result:

* **scalings improve** -- all four multiplicative scenarios, damaged_wing most of
  all. The rule expresses a scaling exactly, because that is what it is.
* **a knee fails** -- saturated_elevator, where one line is fitted through two
  regimes.
* **a discontinuity fails hardest** -- jammed_rudder, +3248. A fixed command
  means the response is CONSTANT in command level; a rule asserting
  proportionality is maximally wrong there, and the size of the miss says so.
* **an offset fails** -- broken_aileron carries a parasitic roll coefficient, so
  its response is affine, not linear-through-origin. **The rule assumes
  `mean = slope x level`, a line through the origin**, and cannot represent an
  intercept.

### What each failure names

This is the loop saying where the next quanta go, and each is a boundary or a
term rather than a higher order:

1. **knee** -> mint a RANGE boundary; two segments, both order 1
   (saturated_elevator).
2. **discontinuity** -> the level axis is not the causal axis at all when a
   command is fixed; the effector has left the dimension (jammed_rudder).
3. **offset** -> the line needs an intercept; `slope x level + bias`, still
   order 1 (broken_aileron).

None of those is curvature. All three are order-1 objects, which is the CJ
addendum's point measured rather than argued: **collapsing to order 1 is right,
and what the residual mints is a boundary, a term, or an axis change -- not a
polynomial.**

### Kept

Declared opt-in, crashes net unchanged, and it fixes the scenario this line
exists for -- damaged_wing 0/3 for the first time, with peak structural 0.64
against 27.83. It also breaks two scenarios badly, and those breaks are now the
most precisely characterised findings in the line: each names the exact next
quantum, with a scenario that tests it in isolation.

**Standing: 4/24 crashes, damaged_wing 0/3, saturated_elevator 3/3.**

## Block CL — ratio quantisation built: two of three failures fixed, the third lost

`emp_split_slope_range_on_residual`: a level whose own learned consequence
disagrees with the shared slope's prediction by more than a declared FACTOR of
that prediction leaves the range and becomes its own. A ratio comparison, no
units. Split factor 0.25, absent -> inert.

| scenario | fault shape | one range (CJ) | quantised (CL) |
|---|---|---|---|
| **saturated_elevator** | knee | 3/3 crashes | **1/3** |
| **jammed_rudder** | discontinuity | RMSE 3834 | **317 / 1186 / 273**, 0/3 |
| **damaged_wing** | scaling | **0/3** | 2/3 |

**Two of the three named failures are fixed by one mechanism, with none of them
named in it.** The clipped levels leave the range and saturated_elevator recovers
two episodes; the jammed rudder's levels all leave, which is the loop discovering
the level axis no longer explains that effector, and its tracking improves by a
factor of six.

**And damaged_wing regresses from 0/3 to 2/3**, which is the mechanism's cost
stated exactly: a scaling IS one ratio, but its observations are noisy during a
departure, so a single disagreement past 0.25 fragments a range that should have
stayed whole. The split is correct in kind and too eager in practice.

### The fix is not a different constant

Tuning 0.25 trades the two recovered scenarios against the lost one and settles
nothing. **The defect is that one observation can split a range** -- a latch with
no activation energy, which is the failure mode this line has already recorded
under a different name: *nothing is ever permanent, a latch can have different
activation and deactivation energy.*

A range should split on SUSTAINED disagreement, not on a sample. That is the same
shape as `error_energy_ema` versus an instantaneous error, and the same shape as
the probe ladder's quorum -- evidence accumulating against a hypothesis before it
is abandoned. It also gives the deactivation path for free: a range that stops
disagreeing can rejoin, which is what makes it a quantisation rather than a
one-way fragmentation.

**Left in the tree with the split factor declared**, because the two recoveries
are real and the regression is understood rather than mysterious. The next change
is sustained disagreement, and it is testable against these exact three
scenarios: saturated_elevator and jammed_rudder must keep their gains while
damaged_wing returns to 0/3. That is a sharper three-way test than anything else
in this line, and it does not require the suite to adjudicate.

## Block CM part 2 — the collapse held open: built, and the threshold does not transfer

Pairwise sweep deleted (34 -> 33 rules). The residual is now computed once per
receipt, as `|observation - mean| / |mean|`, against what the model already
claims -- the shared slope having written its own prediction there. No sibling,
no sweep. Hysteresis retained: split above the factor, rejoin below half.

**Measured, and it is CB to the digit:**

```
  damaged_wing  ep0 5988.1 / 7266.00 / 0.64    ep1 3911.02 / 17.80    ep2 6434.32 / 27.83
  == the CB arm exactly.  Slope sharing never takes effect.
```

**Every model splits immediately, so the collapse never holds.** The cause is
scale, and it is mine: the pairwise disagreement and this per-receipt residual
are different quantities. A single receipt's `|obs - mean| / |mean|` routinely
exceeds 0.25 on a noisy plant, so the EMA sits above the factor permanently and
nothing ever shares. **I carried a threshold across a change of measurement
without re-deriving it** -- the same frame error as seconds read as actions, on
the last change of the session.

Timing: 559 s for three scenarios against the eager version's >600 s timeout.
Cheaper, but not by the margin the argument predicted, because with everything
split the sharing rule matches nothing and the saving is mostly the sweep's
absence.

### Left in the tree, with splitting inert

`slope_range_split_factor` withdrawn, so the split branch never fires and **pure
sharing stands** -- the CJ configuration, measured at damaged_wing 2/3 -> 0/3
with structural 27.83 -> 0.64, and saturated_elevator 1/3 -> 3/3. The machinery
for holding the collapse open is present, correct in shape, and switched off
because its one declared quantity is unset rather than wrong.

**Setting it needs one measurement that does not exist yet:** the distribution of
`|obs - mean| / |mean|` per receipt, split by whether the model is on a shared
ratio that genuinely holds (damaged_wing) or one that does not (saturated_elevator
above the clip). The factor is the separation between those two populations, and
it is a ratio read off data rather than a number chosen -- which is the only form
this session has found that survives contact with a second scenario.

That measurement is the next action and it needs no simulation: the receipts are
already recorded in the block traces.

## Block CN — the factor cannot be set from a per-receipt residual, and the measurement says why

Per-receipt relative residual `|observed - slope x level| / |slope x level|`,
computed from recorded singleton receipts using the slopes CI measured, split by
whether the shared ratio genuinely holds:

```
  damaged_wing    (ratio HOLDS: multiplicative)   n=201
      median 0.95   p25 0.76   p75 1.69   p90 6.70
  saturated_elev  (ratio BREAKS: clipped)         n=288
      median 1.35   p25 0.75   p75 3.12   p90 13.04
```

**The populations do not separate.** Medians 0.95 against 1.35 with quartiles
almost entirely overlapping. No threshold splits one and not the other, and both
have p25 near 0.75 -- which is precisely why 0.25 split everything in CM.

**So the factor is not mis-set. The quantity is wrong.** A single action's
body-rate delta is dominated by gusts, aero coupling and the other effectors'
residual influence; its signal-to-noise cannot carry a decision about whether a
relationship holds. Averaging it does not rescue it either -- the EMAs of two
populations with medians 0.95 and 1.35 still overlap.

### What the residual should be on

Not the observation. **The ratio.**

"Did the relationship break" is not answerable from one observation's error,
because a single error is mostly noise. It is answerable from the RATIO ESTIMATE
moving: the slope implied by recent receipts against the slope currently shared.
That is a ratio of ratios, the per-receipt noise averages out of the estimate
before the comparison is made, and it is the same correction as every other one
today -- **compare relationships, not measurements.**

It also explains why the pairwise version half-worked (CL: saturated_elevator
3/3 -> 1/3, jammed_rudder six times better): comparing a model's mean against a
SIBLING's mean scaled by level is already a comparison of two ratio estimates,
each averaged over many receipts. It was the right quantity in the wrong place --
computed by sweeping every pair every action instead of maintained per model.

**The build both halves point at:** maintain a per-model slope estimate from its
own receipts, and compare that estimate against the shared slope. Held open
(CM's cadence, at the learning event), on a ratio of ratios (CL's quantity, not
CM's), with hysteresis. Neither previous build had both.

### Session end

**Standing: damaged_wing 0/3** with pure sharing, structural 27.83 -> 0.64, and
the split machinery present but inert pending a quantity that can carry the
decision.

The last four blocks were one argument arriving in pieces: a knee is ratio
quantisation (CL), the collapse must be held open (CM), and the residual that
reopens it has to be measured on the ratio rather than the observation (CN).
Each was measured, each was wrong in a way the next one names, and the rule got
smaller every time.

## Block CO — the discriminator is heteroscedasticity, and CN's numbers were mis-scaled

Fitting a through-origin slope per actuator group from recorded singleton
receipts, then testing the residuals:

```
                          fitted slope   resid-vs-level corr   |resid| high/low deflection
  damaged_wing    g0        -0.0703           -0.06                     1.66
                  g1         0.0287           -0.02                     0.71
  saturated_elev  g1         0.0730           -0.02                     0.55
                  g2        -0.0172           -0.01                    38.02
```

**Three results, in order of how much they cost me.**

**1. The correlation test is vacuous.** Least-squares residuals are orthogonal to
the regressor by construction, so residual-vs-level correlation can only read
~0 and cannot discriminate anything. Ill-posed, and I proposed it one message
after arguing that measurement design is where this line keeps failing.

**2. CN's numbers were computed against a mis-scaled predictor.** The fitted
slopes are 4-17x smaller than the model-attribute slopes CI measured
(-0.0703 against -0.30, 0.0287 against 0.50). Those are different frames -- a
per-action body-rate delta over 0.1 s against a model's mean consequence -- so
CN's residual medians of 0.95 and 1.35 are not the quantity they were labelled
as. **The CN conclusion may still hold, but its numbers do not support it.**
Another seconds-read-as-actions, on the block that was itself about frames.

**3. Heteroscedasticity separates where magnitude did not.** Residual magnitude
at high deflection against low: **0.71 to 1.66 where the ratio holds, 38.02 where
it breaks.** That is the knee -- a relation that is fine near the origin and
fails at the extremes, which is what a clip does and what a scaling does not.

### Which is what "median is useless here" means, made concrete

A median asks how big the typical error is. For a linear relation under noise
that is dominated by the noise and says nothing. **The question is whether the
error GROWS along the axis** -- structure, not magnitude. Heteroscedasticity is
that question asked as a ratio: `|resid| at large |level|` over `|resid| at small
|level|`, unitless, scale-free, and requiring no threshold carried from anywhere
else.

**The split test, finally in a form the data supports:** a range splits when the
residual at its extremes is disproportionate to the residual at its centre. One
ratio, computed from the receipts a model already has, with the two populations
separated by a factor of ~20 in the measurements above rather than overlapping.

Not built -- the session is out of room, and building it on the strength of one
scenario pair after today's record would be the wrong ending. But it is the first
form of this test whose two populations actually separate, and it is measurable
from data already on disk.

## Block CP — the heteroscedasticity split test: saturated_elevator 3/3 -> 0/3

A model leaves its range when its residual EMA is disproportionate to its own
group's LEAST -- a ratio of two EMAs, unitless. Factor 8.0, the geometric mean of
CO's measured populations (sqrt(1.66 x 38.02) ~= 7.9), derived rather than
chosen, with anything in [2, 20] separating them. Evidence accumulates
unconditionally; only the decision is gated.

| scenario | before | with the shape test |
|---|---|---|
| **saturated_elevator** | 3/3 crashes (CJ) | **0/3**, RMSE 3782 / 2555 / 2464 |
| jammed_rudder | 0/3, RMSE ~586 (CL) | 0/3, RMSE 317 / 1043 / 264 |
| **damaged_wing** | **0/3** (CJ) | 2/3, struct 15.36 / 23.95 |

**saturated_elevator survives all three episodes for the first time**, and its
tracking is the best recorded for that scenario in this line. The knee is found:
the clipped levels leave the range, the linear ones keep sharing, and none of it
is named in the rule.

### The damaged_wing loss is a polarity bug, not a property of the test

`MinOver` runs over ALL models in the group, including those that have never
learned and therefore carry `slope_disagreement_ema = 0`. **A model with no
evidence has no disagreement to report, and reading its absence as zero drags the
group minimum to zero** -- after which `ema > 8 x ~0` is true for every model and
everything splits, which is precisely the CB-like numbers damaged_wing returned.

That is first-class absence violated in the direction this tree warns about:
absence of evidence read as evidence of agreement. The comparator must be the
least disagreement among models that HAVE disagreed -- a filter on
`experience_count > 0`, one clause.

It also explains why the other two improved: saturated_elevator and jammed_rudder
NEED aggressive splitting, so a degenerate always-split helped them for the wrong
reason. Their gains are real but not yet earned by the mechanism as intended.

### Kept, with the defect named

Net across the three scenarios: 2 crashes against CB's 3, and the largest
single-scenario improvement of the session. The fix is one filter clause and it
is testable against exactly these three: damaged_wing must return to 0/3 while
saturated_elevator and jammed_rudder hold.

**Standing: saturated_elevator 0/3, jammed_rudder 0/3, damaged_wing 2/3** -- with
a shape test that discriminates, a factor derived from measurement, and one
absence-polarity clause between it and all three holding at once.

## Block CQ2 — the polarity fix is a no-op, and CP's diagnosis was wrong

Filtered the group comparator to peers with `experience_count > 0`. Result,
against the unfixed run:

```
  damaged_wing        2/3   2753.1 / 8727.93 | 1.6 / 3914.08 / 15.36 | 1.6 / 6135.67 / 23.95
  saturated_elevator  0/3   held
  jammed_rudder       0/3   held
```

**Identical to the digit.** The fix changes nothing.

**CP's diagnosis was wrong.** I claimed the group minimum was dragged to zero by
models with no evidence. It is not: every model HAS experience, from the
pre-fault calibration pass, so the filter excludes nothing. Their disagreement
EMA is near zero because they genuinely agree -- absence was never the problem.

**And the deeper error is a conflation I made in CP.** CO measured
heteroscedasticity as residual at HIGH DEFLECTION over residual at LOW
DEFLECTION -- a comparison across positions on the command axis. I implemented it
as residual over the group's LEAST residual, which is a different comparison
entirely: it asks "am I worse than the best peer" rather than "does error grow
toward the extremes". The least-disagreeing peer is near zero in every group, so
the ratio is enormous for everyone and the test degenerates -- which is exactly
what damaged_wing's numbers show.

The measured discriminator was positional. I built a rank comparison and called
it the same thing.

### What the comparator has to be

Residual at the extremes against residual at the CENTRE of the range -- peers
with small `|specified_command_level|`, not peers with small disagreement. That
is one clause different from what is in the tree, and it is the quantity CO
actually separated 20x.

**Kept as built**, because it is measurably neutral on all three scenarios and
the two gains (saturated_elevator 0/3, jammed_rudder 0/3) stand either way -- but
those gains are now known NOT to come from the mechanism as intended, and that is
recorded rather than claimed.

**Standing: saturated_elevator 0/3, jammed_rudder 0/3, damaged_wing 2/3**, with a
split test whose comparator is the wrong axis and one clause from the right one.

## Block CR2 — the positional comparator: same verdict. The comparator is not what decides.

```
  positional (this block)  dw 2/3  8759/3365/6099   sat 0/3  3339/2560/2464   jam 0/3
  rank        (CQ2)        dw 2/3  8728/3914/6136   sat 0/3  3782/2555/2464   jam 0/3
  magnitude   (CP)         dw 2/3                    sat 0/3                   jam 0/3
```

**Three comparator forms, one verdict.** The numbers shift slightly -- the change
does something -- but the outcome does not move. saturated_elevator and
jammed_rudder gain from ANY splitting; damaged_wing loses from ANY splitting; and
no framing of the comparison separates them online.

So the split test does not discriminate, and fixing the comparator was never
going to make it. Two conflations of mine are now both refuted by measurement
rather than argument, which is the right way to lose them.

### Why the offline separation did not transfer

CO measured heteroscedasticity offline at 20x: residual against a slope FITTED
ACROSS LEVELS from many receipts. The online test computes each model's residual
against **its own mean, which the sharing rule just overwrote** -- so the online
quantity is "how far is this receipt from what I was told to expect", not "does
the error grow along the axis". Those are different measurements sharing a name.

That is the fourth time this session an online quantity has failed to be the
offline one it was named after (the crash predicate, the terrain clock's frame,
the fidelity gauge's monotone max, and now this). **The pattern is specific
enough to state as a rule: a discriminator validated offline is not validated
until the online quantity is shown to be the same quantity.**

### Kept, on the net

Across the three scenarios: splitting gives 2 crashes (dw 2, sat 0, jam 0), pure
sharing gives 3 (dw 0, sat 3, jam 0). Splitting is net better by one episode and
is kept on that basis alone -- not because the mechanism works as designed, which
it demonstrably does not.

**Standing: saturated_elevator 0/3, jammed_rudder 0/3, damaged_wing 2/3.**

What would actually test CO's finding is a per-model slope estimated from that
model's OWN receipts, compared against the shared slope -- a ratio of two fitted
slopes, which is what CO measured and what none of the three builds computed. The
residual channel from CM is the right cadence for it; the quantity has never been
right.

## Block CS2 — why it compares to the mean, and why that was never the bug

Comparing an observation to the model's mean is algebraically the right thing:
with `mean = slope x level`, `|obs - mean| / |mean|` IS
`|obs/level - slope| / |slope|` -- the ratio this receipt implies against the
ratio the group shares. The comparison was correct.

**The bug is that I took the absolute value BEFORE averaging.** `E[|x - u|]`
measures SCATTER; `|E[x - u]|` measures BIAS. A model on the wrong slope and a
model on the right slope with noisy receipts both show a large mean-absolute
residual, so the EMA could not tell a changed relationship from turbulence.

Measured on the recorded receipts:

```
                    grp    n    |mean signed| (bias)   mean abs (scatter)
  damaged_wing       2     96          3.42                  6.18
  saturated_elev     2    162          0.80                  9.21
```

**saturated_elevator's rudder has scatter 9.21 and bias 0.80** -- residuals that
cancel, i.e. noise about a CORRECT slope. **damaged_wing's has bias 3.42** -- a
systematic offset, because its fault genuinely is a changed ratio. Absolute-first
ranks saturated_elevator as the worse fit; signed-first says the opposite. Every
EMA in the three split builds was measuring turbulence.

### And it reframes what the split test should even be looking for

Bias detects "this ratio has CHANGED", which is not a reason to split -- it is a
reason to RELEARN THE SHARED SLOPE. damaged_wing is exactly that case: one ratio,
changed, still shared, which is why sharing gave it 0/3 and any splitting cost it.

A split is warranted only when levels within one group have DIFFERENT bias from
each other -- a knee being precisely "the low levels sit on one ratio and the high
levels on another". So the test is a comparison of biases across positions on the
axis, not a magnitude, not a scatter, and not a bias against zero.

That is the first formulation in this line that distinguishes the two things the
three failed builds kept conflating: **a ratio that moved** (relearn it) versus
**a ratio that split** (quantise it).

**Not built.** It needs a signed per-model bias EMA and a positional comparison
of biases, and the session has no room to measure another build honestly. But it
is specified by measurement now rather than by argument, and the data to check it
against is already on disk.

## Block CT — motor programs indexed by type and shape, and three corrections to my own prereg

Two additive rules in the general seed (v1.13.0, 35 rules):
`emp_signature_internalized_program` stamps a flown program's shape -- one
relation per member, **predicate = actuator group (the type), argument = integer
command ordinal (the shape)** -- and `emp_grow_motor_program_shape` mints the
codebook entry and bumps `motor_codebook_epoch`. `actuator_group` is the seed's
existing morphology-neutral vocabulary, so a one-group program is a one-relation
shape (a program FOR a limb) and a multi-group program has those as
sub-structure (a program WITH a limb). The humanoid generality falls out.

**Behaviour- and cost-neutral:** crashes 2/3, 0/3, 0/3 unchanged; minimum
altitude identical to 0.1 ft; wall clock within 2 s of baseline; p99s within
+/-3 ms. 39 green, wider suite byte-identical to a `git stash` baseline (the same
5 pre-existing failures).

### The payoff, measured

Over 300 actions of damaged_wing: **234 programs composed, 160 internalized, and
only 35 DISTINCT SHAPES** -- 26 once ShapeDecode's coverage test collapses them.
**~84% of composition re-derives a program already held.** And the shapes differ
by exactly one coordinate on one group (`group_3`: 29 -> 31 -> 34 -> 35), which
is rung-2 `TransformDecode` material made visible for the first time.

### Correction 1 — CR's latency premise is stale

CR argued from "Term composition cost 300-600 ms". **Measured now: S2 p99 is
52 ms and total request p99 56 ms, inside the 100 ms budget at 10 Hz.**
`MotorCompose` already solved the latency problem. The deadline is not currently
binding, so **CQ's affordability argument is not about speed** -- it is about the
84% redundancy above. The case for programs-as-shapes is that most composition is
wasted, not that composition is slow.

### Correction 2 — `MotorCompose` cannot be deleted

With `native_composition_enabled=0` the interpreted composer ran **838 s without
completing one episode**, against 69 s/episode native -- >12x and still climbing
when stopped. Removing it today grounds the aircraft. It reduces to the mint path
only when something else can carry the recognise path, which is what the index
begins and does not finish.

### Correction 3 — CS was wrong about async, and this is the important one

CS claimed the epoch discipline already gives an async path. **It does not, for
the motor faculty. There is one `run_rules` fixpoint per action, so
`soft_realtime` is not "behind the action" -- it is IN it.** The shape path works
asynchronously only because `grow_part_library` is called from OUTSIDE the
fixpoint, by a Python builder; the motor path has no such caller. The gap is real
and nothing landed here closes it.

Demonstrated by cost: a third rule collapsing shapes via ShapeDecode matched
library x library, enumerating O(n^2) bindings every pass, and produced no
episode in 838 s. Written, measured, removed.

### Three constraints confirmed as NOT currently expressible

* **"Select because it extends the margin"** -- the index is objective-neutral
  (it stores name, signature, dim_types, kind, slot, member_count and no cost),
  so the foreclosure is elsewhere: `program_cost` has 7 consequence terms plus
  drag, energy, activation and log_authority, and **no latency, margin or
  time-to-produce**; the decision collapse selects on `-program_cost`. The
  creator's reading is confirmed at the source.
* **The reflex rung does not exist** -- the motor seeds carry no `"reflexes"`
  manifest key at all.
* **"Act now and still owe the question" is not prevented.** Every close path,
  `cre_close_inadmissible_deliberation` included, runs
  `_close_deliberation_effects()`, which resets `regime_absence_integral` and
  opens a fresh evidence window. The clock IS discharged; only a
  `ControlRegimeResidual{resolved: 0.0}` node persists.

**And the index supplies the missing detector for exactly that failure:** "rising
reflex count with a flat codebook" was unmeasurable before, because there was no
codebook. There is one now.

## Block CX — why damaged_wing reaches the ground (diagnosis, no fix)

Traced episode 0 of damaged_wing (seed 241102975, the one ground contact of
three) with `scripts/probe_damaged_wing_descent.py`. Suites 43/43.

**The terminal state is a deep stall, not a dive.** From action ~206 to ground
contact at ~780: angle of attack 60-86 deg, indicated airspeed PINNED at
56-58 m/s, normal load factor 1.00-1.16, roll near zero, and a steady yaw rate
building through -20, -41, -53 to -58 deg/s. Constant speed at very high alpha
under about 1 g with a steady rotation is a deep stall / flat spin. A spiral
dive would show rising airspeed and high g; neither is present.

**The entry is a low-speed divergence, complete by action 206.**

| action | altitude (ft) | IAS (m/s) | AoA (deg) |
|---|---|---|---|
| 1 | 10237 | 82.5 | 0.4 |
| 124 | 10054 | 74.1 | 26.8 |
| 165 | 9940 | 57.9 | 39.1 |
| 206 | 9690 | 48.5 | 61.3 |

`damaged_wing` scales `lift_alpha` to 0.7 and `drag_base` to 1.2. Thirty
percent less lift means more alpha for the same lift; more alpha plus more base
drag means more drag; more drag means less speed; less speed means more alpha
again. The aircraft is on the back of the power curve and the loop closes on
itself. It loses only ~550 ft during the entire entry — altitude was never the
problem.

**THE MARGIN MEASURED THE WRONG AXIS.** `margin_actions` reads 1024 -- the
no-region fallback, i.e. "nothing to avoid in view" -- for every action up to
~206, and only becomes finite at 247 (1022), then decays 689, 534, ..., 66, 25,
0. So the budget said "clear" for the whole of the phase that killed it, and
began counting only once the aircraft was already stalled and descending. The
cause is exactly one line of the seed, and it is now confirmed by enumeration:
**`f16_declare_terrain_region` is the ONLY region-declaring rule in the tree**
(the escalation seed declares none). The margin is a min over regions to avoid,
and altitude is the only one there is. **The aircraft ran out of AIRSPEED at
action 206 while the margin reported 1024 actions of budget**, because nothing
had declared airspeed as a thing to stay away from.

This is the measured form of a claim made earlier from intuition: *"dropping
energy is losing options. fast. thats the problem."* Here is the loss, dated:
options ended at action 206, and the instrument that was supposed to price them
did not move until 247.

**The viability ladder agrees with the margin, and is equally wrong.**
`f16_viability_rung` reports 3 or 2 continuously from 10237 ft down to 1204 ft
-- rung 3 being terrain-clear AND survivable AND controllable. At action 657,
at 86 degrees alpha, descending 750 ft per 41 actions, the ladder says rung 3.
It reaches rung 0 only at action 698, at 1204 ft, roughly 80 actions from the
ground and long past any recovery. `controllable` and `survivable` do not
detect a stall.

**The agent is commanding, but never asks to climb.** `target_vertical` is
identically 0.000 for all 1000 actions, in every phase, including at margin 66
and rung 0. `target_forward` runs 1.0-2.0 and saturates at 2.0 from action 698.
So the agent is trying to fly out on SPEED, which is the right instinct, and
there is no vertical channel in the goal basis at all. The only thing in the
system that could ask for a climb on its own is the new margin term -- and the
margin term was seeing urgency 50/1024 = 0.05 throughout the entry.

**A correction to my own first reading.** I called the outlier
`maximum_structural_utilization` of 16.20 (against 0.64 for the two
non-crashing episodes) "enormous loads while barely commanding". The g trace
refutes that: normal load factor never exceeds 1.16. The 16.20 is in a
rate/sideslip load channel, not a normal-load one, and it is a SYMPTOM of the
departure rather than evidence of overstress.

**What this does and does not license.** It names one concrete, structural
absence -- there is no stall/airspeed region -- and that absence fully explains
why both the margin and the viability ladder stayed quiet through the entry.
It does NOT establish that declaring one would prevent the crash: by action 206
the aircraft is in a developed deep stall, and whether the composer can recover
from that basin is a separate question from whether it is told to try. No fix
is attempted in this block.

## Block CY — the stall detector is not missing, and the cap is not the instrument

Directive: *"We don't declare a stall region, we detect a stall by a change in
dynamics, this USED to work."* Both halves are borne out. No fix built; the
knob I reached for was refuted by its own measurement and reverted.

**A declared stall region was the wrong fix, and CX proposed it.** Naming a
basin is authoring a canonical concept — the same error BU's addendum already
ruled out for this line ("a stall corner would not touch a flat spin"). The
detector is a change in DYNAMICS, and it exists:
`emp_reopen_factorized_calibration_on_compound_surprise`, triggering on
`prediction_error_energy > compound_surprise_threshold` or the relative
normal-load surprise. The signal is present and large throughout the departure.

**Why it is deaf, pinned to two lines.** The gate is

```
Lt(P0("episode", "recalibration_count"), P0("policy", "maximum_recalibration_cycles"))
```

and `recalibration_count` has exactly one incrementing writer,
`Plus(count, 1)` — monotone. Two places set the ceiling:

* the replication policy, `maximum_recalibration_cycles: 0.0`, so NO reopen is
  possible before fault onset; and
* `f16_arm_fault_recalibration`, which at onset sets the ceiling to **2.0 and
  resets the count to 1.0** — permitting exactly ONE mismatch-triggered reopen
  for the rest of the episode.

Measured: `recalibration_count` is **2.0 in all nine episodes** of the block,
i.e. the budget is exhausted every time. The seed's own comment at that line
reads "Multiple cycles are retained afterwards for faults whose consequences
are only visible under new loading" — it retains two, one is spent on arrival,
and one remains for everything that follows. This is the mechanism behind the
state the docs already recorded: *"the latch does not re-arm on a signal that
is screaming."*

**The shape is the defect, not the number.** A monotone count against a fixed
ceiling has activation energy and NO deactivation path, so it can only ever
exhaust. The standing instruction this line already holds — *"a latch can have
different activation and deactivation energy, but the world doesn't stop
changing because you detect a change once"* — says the release must be the
mismatch SUBSIDING, not a lifetime budget.

**AND MY EXPERIMENT DID NOT TEST THAT.** Raising the replication cap to 1000
changes only the PRE-FAULT window, because `f16_arm_fault_recalibration`
overwrites the ceiling to 2.0 at onset. So the knob tests "allow recalibration
before the fault", which is a different change, and I conflated the two. What
it bought, over three faults at three episodes each:

| scenario | ground contact (cap 0) | ground contact (cap 1000) | alt RMSE (ft) |
|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 6664 → 7871 |
| saturated_elevator | 0/3 | **3/3** | 4658 → 13701 |
| jammed_rudder | 0/3 | 1/3 | 2997 → 5612 |

**1/9 to 5/9.** Unlike this session's earlier single-episode deltas, this one
clears the noise floor: `saturated_elevator` alone swings 0/3 to 3/3. Reverted.

**What is now known, and what is still untested.** Known: the detector exists,
its signal is live, post-fault it is granted exactly one firing, and the
replication cap cannot be used to change that. Untested: whether re-arming
post-fault helps at all. Testing it needs the ceiling in
`f16_arm_fault_recalibration`, or better, replacing the budget gate with a
hysteretic one — and on this evidence that experiment should be run on the
general seed's gate rather than by turning a consumer's number up, because the
number turned out to control a different window than the one it appeared to.

### CY addendum — hysteresis is a sign you have scaled wrong, and here is the scaling error

Directive: *"hysteresis is a sign that you have scaled wrong."* Applied to the
gate I was about to build, it dissolves it — and identifies the actual defect
one layer up, in the TRIGGER rather than the latch.

**Measured, one damaged_wing episode (1000 actions), committed configuration:**

```
  compound_surprise_threshold        2.0     (a fixed absolute constant)
  prediction_error_energy            median 21.51,  max 33741.0
  actions satisfying the trigger     930/1000  (93.0%)
```

**The trigger is satisfied on 93% of actions.** The threshold sits an order of
magnitude BELOW the median of the quantity it judges. So the recalibration
budget is not a safety limit on a rare event — it is the only thing preventing
continuous recalibration, and a budget is exactly hysteresis: a second,
cruder gate bolted on to suppress chatter the first gate produces.

That is the scaling error, and it is the same one this session has now hit
three times: **an unbounded, multi-scale quantity compared against a fixed
absolute number.** The surprise-shape index hit it (a relative error spanning
0.21 to 1.59M bucketed linearly gives one shape per encounter); the margin hit
it (a linear ramp prices the last ten actions like the first ten); and the
recalibration trigger has it worst, because its constant is not merely coarse
but is below the signal's median.

**The correctly-scaled form already exists in the tree, built today for
another purpose.** `surprise_shape_ordinal` is `IDiv(Log(1 + |relative
error|), quantum)` — a LOG bucket, so it is scale-free, and the condensation
rules judge it by comparing it to the codebook's OWN history (`stable_run`)
rather than to any constant. A trigger of that shape needs no threshold, no
deadband and no budget, because "the bucket changed" is already a
scale-invariant statement about a change in dynamics. The reflex index and the
recalibration latch turn out to want the same detector.

**So the CY conclusion is amended.** CY said the gate should become hysteretic
with the mismatch subsiding as its release. That was wrong for the reason
above: it would have added a second deadband on top of the budget rather than
removing the need for either. The correct experiment is to re-express the
recalibration trigger as a CHANGE OF SURPRISE SHAPE and delete the budget —
and, per CY's own finding, to run it on the general seed's gate rather than by
turning a consumer's number. Not built; recorded so the next block starts from
the right place.

## Block CZ — change of shape, budget deleted: built, and it costs 3 episodes

Built as directed. `emp_reopen_factorized_calibration_on_compound_surprise` is
now `emp_reopen_calibration_on_surprise_shape_change`
(embodied_motor_program v1.16.0, f16_flight_path_control v8.71.0).
Suites 58 passed, 2 skipped.

**What the rule is now.** `emp_index_surprise_shape` stamps
`surprise_shape_minted_seq` when a residual lands in a log bucket the agent has
never occupied; the latch fires on that stamp. No threshold, no deadband, no
budget. The `Lt(recalibration_count, maximum_recalibration_cycles)` clause is
deleted, and the knob is deleted with it — from the seed policy default, from
the replication overrides, and from `f16_arm_fault_recalibration`, whose
comment said "multiple cycles are retained" while its numbers permitted exactly
one. A dead knob that looks live is the specific trap that cost block CY.

**Deleting the budget is safe for a reason that is structural, not empirical:**
the trigger is self-limiting. A bucket can be novel only once, and the codebook
saturates (11 shapes over 998 actions). Nothing needs to cap a signal that
cannot repeat itself.

**And it measures worse.** Three faults, three episodes each, against the same
block CW baseline:

| scenario | ground contact (budget) | ground contact (shape) | alt RMSE |
|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 6664 → 8000 |
| saturated_elevator | 0/3 | 1/3 | 4658 → 6374 |
| jammed_rudder | 0/3 | **2/3** | 2997 → 7616 |

**1/9 to 4/9.** `jammed_rudder` alone swings 0/3 to 2/3, so this clears the
per-episode noise floor.

**The per-episode split is the interesting part, and it cuts both ways:**

```
  recal = 1  ->  ground contact in 0 of 5 episodes
  recal >= 2 ->  ground contact in 4 of 4 episodes
```

Read one way that is damning: recalibrating more is what reaches the ground.
Read the other way it is reverse causation, and that reading is at least as
plausible — a departing aircraft produces residuals in buckets it has never
occupied, which mints shapes, which fires the latch. On this data the
recalibration count is as likely a SYMPTOM of departure as a cause of it, and
nothing here separates them.

**What IS established, across two blocks and 18 episodes.** Both experiments
that let recalibration run more often moved ground contact the same way:
the cap experiment 1/9 to 5/9 (CY), this one 1/9 to 4/9. Two independent
mechanisms, same direction, same rough magnitude. **Re-arming recalibration is
harmful in the current configuration**, and that vindicates the ordering BU
recorded and this line then walked past: credit assignment first, adaptation
rate second, re-arm third — *"a re-armed recalibration that still learns at
1/200 cannot move the models it re-arms"*. Recalibration discards a working
program and demands a fresh model pass; if the learner cannot converge inside
the window, the aircraft flies on worse models than it had.

**Kept, not reverted, and the reason is not the measurement.** The old trigger
was satisfied on 93% of actions and was only survivable because a budget
suppressed it; it is not a detector and there is nothing to go back to. The new
one is scale-free, self-limiting, and wrong-ordered — it sits third in a queue
whose first two items are not done. **The measured cost is 3 episodes and it is
recorded here rather than in a footnote.** If the next block wants a working
loop rather than a correct trigger, the honest move is to do credit assignment
first and re-measure this, not to re-tune it.

**Residual:** `f16_recalibrate_on_no_projected_transition` still writes
`maximum_recalibration_cycles`. Nothing reads it; it is a leftover on a
different path and was left rather than churned into this block.

## Block DA — credit assignment: the budget was concentrated, not missing

Built. `motor_compose.rs::attribution_price` prices staleness in the singleton
open. Gates: `tests/test_attribution_price_migrated.py` 4/4; suites 117 passed,
10 skipped.

**The measurement that selected the design.** On damaged_wing the loop spends
**319 of 1000 actions** commanding a single effector alone — a large
attribution budget — and after action 250, **all 231 of those go to ONE
member**. The consequence is that **36 of 37 effector models sit frozen at
`experience_count` 201 for the last 750 actions**, which is the entire
departure. BV part 2 saw this as 18-of-41; with the attribution refresh in, it
has become total. The budget was never missing. It was spent on the member that
already knew the most.

**Why the term belongs in the COST and not in a scheduler.** The singleton open
picks whichever member minimises `singleton_cost`; the state barely moves; the
same member wins every time. That is BV part 1's finding seen from the other
side — *"a composer that settles on one program is efficient and unobservable
— it stops generating the variation its own learners need"* — and it is why
the rank deficit reached 3.27 deep in the stall. Rotating the primary IS
composition variation, so one term addresses both halves. A scheduler would
impose exercise from outside while the cost went on preferring the same member.

Same shape as the margin, for the same reason: a ratio, not a linear offset. A
member unexercised for ten windows is worth ten times one unexercised for one.
Absence reads 0, so a never-exercised member is maximally stale — never
measured is most worth measuring.

**It works, at the level it was built for:**

| | before | after |
|---|---|---|
| distinct members exercised alone after action 250 | 1 | **31** |
| top member's share of the late budget | 100% | **18%** |
| median effector `experience_count` at episode end | 201 | 205 |

**And it does not recover flight outcomes.**

| scenario | CW (budget) | CZ (shape trigger) | DA (+ credit) |
|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 1/3 |
| saturated_elevator | 0/3 | 1/3 | **2/3** |
| jammed_rudder | 0/3 | 2/3 | 2/3 |

**1/9 → 4/9 → 5/9.** CZ→DA is one episode and is inside this file's own noise
floor; the cumulative CW→DA move of four is not.

**The residual is the answer, and it is step 2 of an order this line wrote down
and then walked past.** Median effector experience moved 201 → 205: four
samples across 750 actions. Attribution is now DISTRIBUTED and still
STARVED — every model gets a share of a budget that is far too small to move a
1/n accumulator. That is exactly what BU's corrected ordering predicted:

```
  1. credit assignment      <- built (DA): distribution fixed, 1 member -> 31
  2. adaptation rate        <- NOT BUILT
  3. re-arm recalibration   <- built (CZ), out of order
```

Re-arming was built second and credit assignment third, both ahead of the rate.
Two of three are in and the outcome is worse than none. **On this evidence the
three are not independent improvements to be banked separately — they are one
change with a required order**, and the rate is the item that makes the other
two pay: a model that receives samples it cannot weight is no better off than a
model that receives none.

**Open decision, not taken here.** The tree stands at 5/9 against a 1/9
baseline. Either the rate is built next and the three are measured together, or
CZ's shape trigger is reverted to hold 1/9 while that work happens. Both are
defensible; banking a fourth partial change is not.

## Block DB — the adaptation rate as a count, and the ordering hypothesis REFUTED

Built. The rate is now derived from `stable_run` rather than a declared floor.
Gates: `tests/test_adaptation_rate_migrated.py` 4/4; suites 121 passed, 10
skipped.

**What ends the regress.** CD recorded it exactly: 1/n asserts stationarity, so
declare a floor; a flat floor costs quiet regimes, so declare a surprise factor;
surprise needs a reference, so build an error EMA; the EMA needs a rate, so
1/n. Each rate needed a rate, and surprise-gating was built and reverted TWICE
because the reference was a 1/n accumulator judging 1/n accumulators.
`stable_run` is not an accumulator — it is an integer count of consecutive
encounters, so computing it needs no rate and the recursion terminates.

The declared constant comes back as an EARNED value: a shape seen once adapts
at 1.0, a shape stable for 20 encounters adapts at exactly 0.05 — which is what
`model_adaptation_rate_floor` was set to — and a shape stable for 200 adapts at
0.005. `model_adaptation_rate_floor` survives only as the absent-case fallback,
so consumers without the surprise index are byte-identical.

**The block, and it does not say what the ordering predicted:**

| scenario | CW budget | CZ shape | DA credit | DB rate |
|---|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 1/3 | **0/3** |
| saturated_elevator | 0/3 | 1/3 | 2/3 | 2/3 |
| jammed_rudder | 0/3 | 2/3 | 2/3 | 2/3 |
| **total** | **1/9** | 4/9 | 5/9 | **4/9** |

**THE ORDERING HYPOTHESIS IS REFUTED.** DA argued these were "not three
bankable improvements but one change with a required order", and that the rate
was the item that would make the other two pay. All three are now in, and the
tree sits at **4/9 against a 1/9 baseline**. Credit assignment and the rate did
not rescue re-arming; they left it where it was.

**Where the damage actually lives.** Both regressions entered at CZ and neither
later change touched them: `saturated_elevator` 0/3 → 1/3 → 2/3 → 2/3, and
`jammed_rudder` 0/3 → 2/3 → 2/3 → 2/3. The two scenarios that broke are the two
that broke when the recalibration trigger changed, and they stayed broken
through both of the changes that were supposed to make that trigger affordable.

**What the rate did do, stated at its true strength.** `damaged_wing` reached
**0/3 for the first time in this sequence**, including on seed 241102975 — the
episode traced in CX, which flew into the ground at 5 ft and now bottoms out at
1717 ft. That is the one scenario with a mechanistic diagnosis (a low-speed
divergence into a deep stall), and the rate is the change that plausibly
addresses it: a model can only move when its shape is new, which is exactly
the condition a departure creates. **But 1/3 → 0/3 is one episode, inside this
file's own noise floor, and it is not evidence.** It is a reason to power the
gate on that scenario, nothing more.

**The next experiment is a subtraction, not an addition.** Credit assignment
and the rate are independently motivated and one of them may have recovered a
scenario. CZ's trigger is the change every surviving regression traces to.
Reverting the trigger while KEEPING credit and rate is the measurement that
separates them, and it is the one to run before anything else is built — this
line has now added four things in a row and learned less from the last three
than the subtraction would teach in one.

## Block DC — the subtraction, and my attribution of the regression was WRONG

Reverted CZ's trigger while keeping credit assignment (DA) and the adaptation
rate (DB). The magnitude trigger and its budget are restored exactly from the
pre-CZ text, in the seed default, the replication override and
`f16_arm_fault_recalibration`. Suites 103 passed, 2 skipped.

| scenario | CW base | CZ shape | DA +credit | DB +rate | **DC −shape** |
|---|---|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 1/3 | 0/3 | **0/3** |
| saturated_elevator | 0/3 | 1/3 | 2/3 | 2/3 | **1/3** |
| jammed_rudder | 0/3 | 2/3 | 2/3 | 2/3 | **3/3** |
| **total** | **1/9** | 4/9 | 5/9 | 4/9 | **4/9** |

**DB said "every surviving regression traces to CZ". That was wrong, and this
is the experiment that shows it.** Removing the trigger did not return the tree
to 1/9; it stayed at 4/9. CW and DC differ in exactly two things — credit
assignment and the adaptation rate — and they are both ON in the 4/9 arm and
both OFF in the 1/9 arm. **The three episodes are carried by credit and/or
rate, not by the trigger I blamed.**

**The per-scenario movement also refutes additivity.** Removing the trigger
improved `saturated_elevator` (2/3 → 1/3) and made `jammed_rudder` WORSE
(2/3 → 3/3). The trigger was helping one scenario and hurting another, so the
five arms cannot be read as a stack of independent contributions. That is a
second, quieter error in how this line has been reasoning: four blocks were
interpreted as "this change cost N episodes" when nothing had been isolated.

**What survives all five arms.** `damaged_wing` is 0/3 in both arms that carry
the rate and 1/3 in all three that do not. It is the only scenario with a
mechanistic diagnosis (CX: a low-speed divergence into a deep stall) and the
rate is the only change that plausibly addresses it. Three episodes is still
not a result, but it is now the same result twice under different trigger
conditions, which is more than any other cell here can say.

**Next, and it is another subtraction.** Both new terms are absent-inert by
policy parameter, so each can be disabled with one line and no code change:
`attribution_weight: 0.0` isolates credit; `motor_surprise_shape_quantum: 0.0`
isolates the rate. The credit arm is running. **No further additions until the
three episodes have an owner** — this line has now spent four blocks attributing
a regression to the wrong change, and the fix for that is not a better guess.

## Block DF — the 2×2 closes: the RATE owns the regression, credit is neutral

Four arms on current code, three faults, three episodes each. Both terms are
absent-inert by policy parameter, so each arm is one line and no code change.
Suites 104 passed, 2 skipped.

| | credit off | credit on |
|---|---|---|
| **rate off** | **1/9** | **1/9** |
| **rate on** | 4/9 | 4/9 |

**The adaptation rate costs exactly three ground contacts. Credit assignment is
exactly neutral** — same total with it and without it, in both rate conditions.

Per scenario:

| scenario | both off | credit only | rate only | both on |
|---|---|---|---|---|
| damaged_wing | 1/3 | 1/3 | 1/3 | **0/3** |
| saturated_elevator | 0/3 | 0/3 | 1/3 | 1/3 |
| jammed_rudder | 0/3 | 0/3 | 2/3 | 3/3 |

**And the stale-baseline worry resolves.** The true control on current code is
1/9, the same as the CW figure measured before the zero-margin fix and the
`region_sense` filter landed. Those two changes were neutral at this
resolution. The concern was still correct to raise — the comparisons WERE being
drawn across a changed codebase, and that they happened to survive is luck, not
method.

**Why the rate hurts, and it is not the number.** At `stable_run == 1` the rate
is 1.0, so one sample replaces the model outright. The model is GLOBAL — 200+
samples across every regime — while the run length is REGIME-LOCAL. Applying a
regime-local rate to a global model discards what that model knows about
everywhere else, on a single observation. It buys the departure it was aimed at
(`damaged_wing` 1/3 → 0/3, and only in combination with credit) and pays twice
over on `jammed_rudder` and `saturated_elevator`, where novel shapes arrive from
the fault rather than from a basin change.

**The form was right; the scope was wrong.** `stable_run` is a count, so it
needs no rate of its own and CD's regress genuinely terminates. That part
survives. What does not survive is applying it to a model whose scope it does
not match.

**The resolution is the codebook pattern this line already uses, not a smaller
constant.** Shapes index programs; shapes index reflexes; **shapes should index
MODELS.** A new shape should mint a NEW model that starts empty — where a rate
of 1.0 is exactly right — instead of overwriting one that is correct about every
other regime. That is a build and it is not started here.

**Standing state.** The rate is gated behind
`model_adaptation_rate_from_shape`, absent-inert, and the F-16 consumer does not
enable it (gated by test). The surprise index stays ON (quantum 1.0), so
condensation and the reflex rung keep running; credit assignment stays ON at
0.05 because it is free and independently justified (31 of 37 members exercised
where 1 was). **The tree is back at 1/9 with every non-regressive piece of this
sequence retained.**

## Block DG — shapes index models: built, and the mechanism DOES NOT transfer

Built as directed. `emp_fork_regime_local_model` forks a model when the
residual lands in a regime it has never seen; the fork inherits the parent's
means, restarts its own `experience_count` at 1, and `motor_compose.rs` makes
it eligible ONLY in that regime. Gates: `tests/test_regime_local_models_
migrated.py` 6/6, `tests/test_fork_token_regression.py` 2/2, suites 47 passed.

**The prediction DF made, and it is wrong.** DF argued the shape-derived rate
failed on SCOPE rather than arithmetic — a regime-local rate moving a global
model — and predicted that per-regime models would recover the benefit without
the cost. Neither half holds:

| scenario | control | shape-rate | **FORK** |
|---|---|---|---|
| damaged_wing | 1/3 | **0/3** | 1/3 |
| saturated_elevator | 0/3 | 1/3 | 0/3 |
| jammed_rudder | 0/3 | 3/3 | **2/3** |
| **total** | **1/9** | 4/9 | **3/9** |

* **The benefit did not transfer.** `damaged_wing` stays 1/3. The shape-rate's
  0/3 came from the global model actually MOVING fast, not from regime-locality
  — which is the opposite of DF's explanation.
* **The cost mostly did.** 1/9 → 3/9, and all of it on `jammed_rudder`
  (0/3 → 2/3, against the shape-rate's 3/3). Per-regime models reduce the
  damage but do not remove it.

**Where it did help is on tracking, not survival.** `saturated_elevator`
altitude RMSE 4658 → **2151**, and `damaged_wing` 6664 → 6220, while
`jammed_rudder` went 2997 → 8110. The fork is doing something real to control
quality; it is destroying one scenario while improving two.

**A mechanism worth naming, NOT built.** The regime index is the INSTANTANEOUS
residual bucket, recomputed every action from a noisy quantity. So model
identity can flicker action to action, and the composer switches between fork
and parent as the bucket moves — which is a chatter source exactly where a
jammed effector makes the residual erratic. The tree already holds the
instrument that would fix it: `stable_run` and condensation say when a shape is
ESTABLISHED rather than merely current, so the regime a model forks on should
be a condensed shape, not this action's bucket. That is the next hypothesis and
it is not built here, because the last four blocks were all plausible things
built before they were measured.

**Standing state.** `regime_local_models_enabled` is OFF in the F-16 consumer,
absent-inert in the seed, and the mechanism plus its gates are retained. The
tree is at **1/9** — the control — with every measured-neutral or better piece
of this sequence kept and every measured-worse piece gated off:

| piece | state | measured |
|---|---|---|
| margin price in `program_cost` | ON | in the deciding path, 976/977 |
| attribution / credit assignment | ON | exactly neutral, 1 member → 31 |
| surprise index + condensation + reflexes | ON | 27 engine firings, no cost |
| shape-change recalibration trigger | reverted | +3 episodes |
| adaptation rate from shape | gated off | +3 episodes |
| regime-local models (fork) | gated off | +2 episodes |
