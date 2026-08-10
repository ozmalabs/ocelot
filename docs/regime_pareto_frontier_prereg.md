# Regime selection is a Pareto frontier, not a ladder — prereg + handoff

## The measured negative that motivates this

Four architectures were measured at n=100 x 100 s (10 Hz), same seeds,
same plant.  Crash rate [Wilson 95%]:

| scenario | v1 absolute | v2 urgency | v3 deliberation | arch4 trend-gate |
|---|---:|---:|---:|---:|
| nominal | 0.00 | 0.00 | 0.00 | 0.00 [0, .037] |
| jammed rudder | **0.00** | 0.11 | 0.04 | 0.08 [.041, .150] |
| saturated elevator | 0.21 | 0.18 | **0.16** | 0.22 [.150, .311] |
| damaged wing | 0.47 | 0.49 | **0.42** | 0.51 [.413, .606] |

Results dirs: `..._matrix_v1`, `..._matrix_v2`, `..._matrix_v3` (v3 holds
the DELIBERATION architecture despite the name), and
`..._arch4_terminaldescent`.

**arch4 is a null-to-negative result and is recorded as one.**  It was
tuned against the four seeds that crashed under v3; all four flipped to
survival, and none of it generalised.  This is the standing rule
(POWER THE GATE BEFORE THE ENDGAME) reproduced exactly: four rescued
anecdotes were never evidence about the distribution.  Its one real
gain — nominal altitude RMSE 352+-313 -> 324+-44, from no longer
mistaking ordinary transients for regime failure — is worth keeping
independently of everything else here.

**v3 (deliberation, fixed window) is the current best and the baseline
any redesign must beat.**

## What the failures actually say

Orbit adoption across architectures: jam 82/100 -> 51, elevator 23 ->
11, wing 100 -> 2.  Earlier triggering spends the decisive escalation on
a HOLD verdict, because at that moment NO rung's precondition is
satisfied.  Three of four measured failure modes have no rung whose
precondition describes them at all:

- **damaged wing** — rolls inverted ~2.5 s after onset; no rung's
  precondition mentions roll authority.
- **saturated elevator** — 205 ft/s airspeed RMSE with +-5% pitch
  travel; no rung hands speed to the throttle.
- **jammed-rudder residual** — seeds that DO adopt orbit still crash, so
  orbit is one corner, not the corner every flight condition needs.

Four architectures iterated on WHEN TO DECIDE.  The binding constraint
is WHAT THERE IS TO DECIDE BETWEEN.

## The reframe

`docs/embodied_pareto_profiles.md` already states the law this design
broke:

> There are no weights, sums, or hidden winner-selection constants in
> the core. ... A separate context-sensitive policy can choose among
> frontier members; that choice must remain explicit and must not be
> smuggled into the Pareto substrate as a scalar score.

`cre_publish_regime_deliberation` publishes an **Argmax over per-rung
supports** — precisely the smuggled scalar.  And the rung ladder
(0 -> 1 -> 2 -> 3) imposes a TOTAL ORDER on regimes that are
Pareto-INCOMPARABLE.  Each surrenders a different objective:

| regime | surrenders | keeps |
|---|---|---|
| fixed point (0) | nothing | all |
| sideslip trim (1) | zero sideslip | heading, altitude, speed |
| steady orbit (2) | absolute heading | altitude, speed, wings level |
| **speed priority (new)** | altitude tracking | airspeed, control authority |
| **roll priority (new)** | heading + altitude | attitude, structural margin |
| thrust basis (3) | flight | impact state |

None is above another.  They are corners of a frontier over WHICH
OBJECTIVES REMAIN ACHIEVABLE.

## Design to implement

1. **Regimes as Pareto candidates.**  Each declared regime is a
   candidate on an `embodied_pareto_profile` whose dimensions are the
   measured achievable margins per axis: altitude-hold, heading-hold,
   speed-hold, attitude-hold, structural margin.  Reuse the existing
   primitive and its `dominates_embodied_pareto_candidate` edges; do NOT
   re-implement dominance.
2. **Deliberation computes the frontier** (the doc already specifies
   dominance evaluation as a bounded, asynchronous System-2 task — which
   matches the standing architectural finding that escalation is a
   TRIGGER for a higher-order collapse, never an immediate switch, and
   that reflex and deliberation are ONE process at different depths:
   an unambiguous field settles at order 0, an ambiguous one deepens).
3. **An explicit, declared policy selects among frontier members** from
   the situation (e.g. terrain proximity favours altitude-hold; low
   airspeed favours speed-hold).  It must be visible graph data, not a
   scalar folded into the candidates.
4. `regime_ordinal` becomes an IDENTIFIER, not a ladder position;
   `regime_max_ordinal` becomes "which regimes are declared available".
   Keep the general seed domain-free (the existing test asserts no
   domain vocabulary in `control_regime_escalation`).
5. **Two new regimes**, whose absence is measured above: speed-priority
   (altitude surrendered, throttle owns speed — for saturated elevator)
   and roll-priority (heading + altitude surrendered, attitude and
   structural margin kept — for damaged wing).

## Gates (must all be met before any claim)

- Migrated tests green: `tests/test_control_regime_escalation_migrated.py`,
  `tests/test_jsbsim_f16_paper_replication_migrated.py`,
  `tests/test_jsbsim_f16_coupled_migrated.py`,
  `tests/test_fixed_wing_jet_control_migrated.py`.
- Nominal n=100 crash 0.00 and altitude RMSE no worse than 352 ft.
- Fault scenarios compared against **v3** with Wilson 95% CIs, n=100,
  the frozen seed blocks (base 241102975 + scenario index x 10000).
- No tuning against individually named failing seeds.  Prereg the
  prediction, then run the full block.  Report nulls as nulls.

## Frozen stack for the comparison

`embodied_motor_program` v1.8.0 (native MotorCompose),
`control_regime_escalation` (v2.1.0 at handoff),
`f16_flight_path_control` (v1.10.0 at handoff — arch4; revert the
evidence gate to v3 semantics or keep it only if measured neutral).
Engine binary: `runners/dsl/python/substrate_rs/_native.abi3.so` built
from this tree (includes the `MotorCompose` term).

## Prediction (prereg'd before the n=100x4 powered run)

Implementation notes below record what actually landed
(`control_regime_escalation` v3.0.0, `f16_flight_path_control` v2.0.0 —
the terminal-descent evidence gate from arch4/v1.10.0 was KEPT, measured
neutral-to-positive independently of the ladder-vs-Pareto question, see
"What shipped" below). Before running the n=100x4 block this prediction
is committed from the mechanism's design alone — a small number of n=1,
30 s smoke probes were run first to catch runtime errors (crashes,
exceptions), never to compare outcomes or adjust any formula; no formula
or threshold in the shipped code was changed after looking at a probe's
selected regime or metric.

- **Nominal**: BYTE-IDENTICAL to v3, 0.00 crash. Nominal flight never
  starves evidence past the horizon, so it never opens a deliberation and
  never touches any of the new machinery — the same structural argument
  that made v4's metastable probe and the v1.6.0 render path both leave
  nominal untouched.
- **Jammed rudder** (v3: 0.04 [.041 CI not double-checked here, see
  table above]): CI-overlapping neutral. Trim and orbit already existed
  and already covered this fault reasonably (v3 held the DELIBERATION
  architecture at 0.04); the redesign changes WHICH mechanism selects
  between them (frontier + policy vs. Argmax-over-support) but does not
  hand jammed rudder a genuinely new corner the way saturated elevator
  and damaged wing get one.
- **Saturated elevator** (v3: 0.16) and **damaged wing** (v3: 0.42):
  these are the two failure modes the doc's own "what the failures
  actually say" section identifies as having NO rung whose precondition
  describes them — no rung ever handed speed to the throttle, no rung's
  precondition mentioned roll authority. The prediction is that crash
  rate is CI-separated LOWER for at least one of these two, since the
  new speed-priority and roll-priority corners are the first candidates
  ever proposed that surrender exactly the axis each fault makes
  unwinnable while explicitly keeping the axis that matters for not
  crashing (airspeed/control authority; attitude/structural margin).
- **Named risk, not tuned against**: candidates that SURRENDER an axis
  are scored a flat, un-penalised 0.0 on it regardless of how good or
  bad that axis currently is, while candidates that KEEP an axis are
  scored the live, unbounded-below achievable-margin formula. This is a
  structural asymmetry (surrendering is "free" the moment any kept axis
  goes even mildly negative) that smoke probes showed pushing selection
  toward the more-surrendering corners (speed/roll priority) rather
  faster than the qualitative "corner per fault" story above suggests.
  If it holds at n=100 the plausible signature is: crash rate flat or
  improved (the selected corners are still real, validated protective
  behaviours — full-throttle authority, wings-level with neutral pitch)
  but altitude/heading RMSE on fault scenarios WORSE than v3 even when
  crash rate does not regress, because tracking objectives are given up
  more readily than a tuned design would. This paragraph is written
  before the n=100 numbers exist specifically so a worse-RMSE, flat-
  crash-rate outcome cannot later be read as a surprise discovery.

---

## The nominal prediction was FALSIFIED, and why (measured, 2026-08-02)

The n=100 nominal block
(`results/jsbsim_f16_paper_replication_10hz_pareto_frontier_v1/nominal.json`)
against the prediction committed above:

| | predicted | v3 baseline | Pareto v1 (measured) |
|---|---|---:|---:|
| crash rate | 0.00 | 0.00 | **0.01** |
| escalations | 0 | 3/100 | **88/100** |
| altitude RMSE | byte-identical | 378 ft | **778 +- 445 ft** |
| airspeed RMSE | byte-identical | — | **252 +- 155 ft/s** |
| settled fraction | — | 0.81 | **0.25** |

82 of the 100 healthy episodes ended holding the SPEED-PRIORITY corner —
the one that surrenders altitude tracking.  The prediction's argument
("nominal never starves evidence, so it never opens a deliberation") was
sound as an argument; the premise was false in the shipped code.

### The measured cause: the evidence RATCHET lost its settling-band floor

Instrumented single-episode trace (nominal, seed 241102975, 100 s, the
gate protocol, regime attrs read straight off the episode node —
`GAMMA_REGIME_DIAGNOSTICS=1` in `scripts/jabberwock_fixed_wing_jet.py`):

```
seq  joint_err  best_err  err_ema  absence  deliberating  ordinal
  1     0.000     0.000     0.000      0.0        0          0
  2     0.058     0.000     0.001      0.0        0          0
  3     0.905     0.000     0.012      1.0        0          0
 ...   (absence integral climbs 1.0 per action, evidence never fires)
 82     1.36      0.000     1.36      80.0        1          0
162     1.87      0.000     1.868      0.0        0          4   <- speed priority
```

Evidence has two arms and both are ratios of the regime's OWN best,
floored at the joint published settling band (one unit per counted axis,
3.0 here) precisely so a best tighter than the band cannot sharpen the
monitor below the band.  The Pareto rewrite computed that floor
(`reference_scale`) and wired it into the band-RESIDENCE arm only; the
RATCHET arm kept comparing against the raw `regime_best_error`.

Every episode starts AT its reference, so the first action's joint error
is identically 0.0 and the ratchet latches `regime_best_error = 0.0` on
tick 1.  From tick 2 "a new best" means `error < 0.9 * 0.0` —
unsatisfiable for the rest of the episode.  That left the residence arm
alone carrying evidence, and its (correct, arch4) trend test rejects any
sample above the regime's own lagging EMA — which a healthy episode
drifting slowly off its initial altitude is on nearly every sample.  So
evidence starved from the SECOND ACTION of ordinary healthy flight, at
~1.9 band units of joint error, well inside the published band.

This is the same failure the floor was introduced for, one step more
extreme: the v1.4.0 note records "a 0.3-band initial capture escalated
EVERY scenario pre-fault"; a 0.0-band capture starves every episode from
tick 2.

**The starvation precondition, not the frontier, is what nominal lost.**
Once a deliberation opens, the frontier does behave as the "Named risk"
paragraph above predicted — a mildly negative kept axis (altitude at
1.9 band units scores -0.84) loses to a surrendered axis's flat 0.0, so
speed priority dominates every other corner and wins.  That asymmetry is
REAL, and the 10-seed pre-flight below measured it costing the gate even
after healthy flight stopped starving.


### Fix 1 (`f16_flight_path_control` v2.0.1): floor the ratchet arm

One change: the ratchet arm compares against the floored
`reference_scale`, exactly as the residence arm already did.  No
threshold, formula or constant was altered.

### The 10-seed pre-flight caught the SECOND cause

The pre-flight is the standing practice in this line (the
`..._preflight_10seed_v1` precedent caught two problems single seeds had
hidden).  With fix 1 alone, nominal n=10 (the block's own first ten
seeds):

| | v3 baseline | Pareto v1 | + fix 1 |
|---|---:|---:|---:|
| escalations | 3/100 | 88/100 | 3/10 |
| altitude RMSE | 378 ft | 778 ft | **521 +- 452 ft** |

The seven episodes that never escalated sit at 318-346 ft — the healthy
number, comfortably inside the 352 ft gate floor.  The three that did
escalate went to speed priority and blew out to 760 / 1820 ft with
airspeed RMSE of 400 ft/s.  Two of the three published at actions
209-213, i.e. a deliberation opened before the commanded reference
change and published its verdict 80 actions later, when the commanded
transient made the status quo look worst.

**Why a healthy aircraft can still open a deliberation** (and should):
the F-16's honest nominal steady-state altitude offset is ~300 ft, which
is 3 settling-band units on its own — right at the joint band, so a slow
drift outside it genuinely stops producing evidence.  v3 escalated 3/100
for exactly the same reason.  The difference is what the verdict then
DOES, and there the frontier had two defects:

1. **The same declared dimension was measured with two different
   instruments depending on the candidate.**  Heading was already an
   achievability ratio (bank-steering authority vs the sustained turn
   rate the airframe is actually producing) with the reason written into
   the seed; altitude and speed were raw tracking errors in settling-band
   units, and the "hold" candidate alone was scored on raw tracking error
   where every alternative was scored structurally.  A ~300 ft altitude
   offset therefore read -9 on an aircraft with its entire pitch envelope
   untouched, so surrendering altitude (flat 0.0) dominated the status
   quo in ordinary cruise.  A tracking error outside the band is not an
   unachievable objective; a demand past the loop's own declared
   authority is.
2. **A tie was broken by whatever order the frontier iterated in.**  Two
   Pareto-equal candidates with equal priority readings left the Argmax
   free to abandon the regime being flown on no measured preference —
   the HOLD verdict the ladder architecture had, silently lost in the
   rewrite.

### Fix 2 (`f16_flight_path_control` v2.1.0): one instrument per dimension

Altitude and speed become achievability ratios read straight off the
outer loop's own clamps (`emp_derive_flight_path_control_targets`),
against the same 1.5x operating-point margin the heading axis already
declares — a commanded reference change demands exactly the clamped
authority, so a criterion sitting ON the authority would call every
commanded manoeuvre unachievable:

| axis | measured against | authority |
|---|---|---|
| altitude | sustained vertical rate (`f16_sink_rate_ema`) | min(max vertical speed, V sin(max flight-path angle)) |
| heading | sustained body yaw rate (`f16_yaw_rate_ema`) | g tan(max bank) / V *(unchanged)* |
| speed | \|speed error\| x dt / airspeed tau | max forward delta |

and the "hold" candidate reads the same five formulas as every other
candidate; what stays its own is only WHICH axes it is still attempting.
No new constant is introduced: every term is a declaration the
controller already flies by.

**The altitude axis is DISTURBANCE-vs-authority, and the second
pre-flight round is why.**  Read as demand-vs-authority
(`|altitude error| / altitude tau`) it is SELF-FULFILLING, and the
10-seed jammed-rudder pre-flight measured the cost: **0.80 crash against
v3's 0.04**, with the roll-priority corner (which surrenders heading AND
altitude) selected in 9 of 10 episodes at ~44 s and altitude RMSE of
7,700 ft.  A jam's altitude error is large BECAUSE the unwinnable
heading fight is bleeding lift; scoring altitude by that error declares
altitude unachievable, which hands the frontier to the corner that gives
up the most, which then flies wings-level into the ground.  Retire the
heading fight and the same aircraft holds altitude.  The honest question
for the axis is therefore the one the heading axis already asks: is the
rate the airframe is SUSTAINING inside what the loop can command?  The
speed axis keeps its demand reading because no declared corner surrenders
speed -- it never discriminates between candidates, only feeds the
situational-priority readout.

### Fix 3 (`control_regime_escalation` v3.1.0): the burden of proof is on the change

Leaving the currently-held regime requires a STRICT improvement on the
declared priority axis over the frontier's own status-quo candidate; a
tie publishes the status quo, closing the deliberation and opening a
fresh evidence window without touching what System 1 is flying.  This is
not a scalar smuggled into dominance — dominance has already run and left
both candidates on the frontier; it is the explicit, declared policy step
choosing between them.  (Also fixed there: `regime_escalation_count`
compared the verdict against an ordinal the preceding effect had already
overwritten, so the telemetry counted 0 through every real change.)

### What fixes 2 and 3 mean for the fault scenarios

Not neutral, and prereg'd as such.  Under one honest achievability
instrument the corners separate by which axis has genuinely run out of
authority: a jam's sustained turn rate exceeds the bank-steering
authority (heading negative -> orbit), a saturated elevator's altitude
demand exceeds the commandable vertical speed while its speed demand
exceeds the forward-delta authority (-> speed priority), a damaged wing
loses both heading and altitude while attitude is what is left (-> roll
priority).  That is the design the reframe describes, now actually
implemented — but it is a DIFFERENT selection rule from the one the
n=100 x 4 block was going to measure, and it is measured, not assumed.

Honest residual, recorded before the run: with the five declared axes the
sideslip-trim corner is Pareto-IDENTICAL to hold (it surrenders zero
sideslip, which is not one of the five), so under fix 3 it can never be
selected on its own.  Its machinery still ships as part of the orbit
corner, which is where the measured history put its value.  A sixth
(lateral/sideslip) axis is what would make it a distinguishable corner;
that is not being added here.

### Disclosure of what was looked at

Diagnosis used ONE nominal episode (seed 241102975, the block's own base
seed) instrumented at the attr level, one 100 s re-run of that seed, and
two 10-seed nominal pre-flights.  No formula, threshold or constant was
chosen by looking at an outcome: fix 1 restores an invariant the code's
own comment already declared, fix 2 applies to two axes the reason the
seed already wrote down for the third, and fix 3 restores a verdict the
previous architecture had.  Nothing was tuned against a named failing
seed.  The pre-flight numbers are reported above rather than hidden, and
the powered block is what the prediction is held to.

## The four-scenario pre-flight (n=10, committed before the powered block)

With all four fixes in, the same 10-seed protocol on all four gate
scenarios, against v3's n=100 crash rates:

| scenario | v3 (n=100) | Pareto v2 (n=10) | altitude RMSE | corners adopted |
|---|---:|---:|---:|---|
| nominal | 0.00 | **0.00** | 359 ft | none — 0/10 escalations |
| jammed rudder | 0.04 | **0.80** | 8,039 ft | roll priority 9/10, orbit 0/10 |
| saturated elevator | 0.16 | **0.70** | 7,453 ft | speed priority 10/10 |
| damaged wing | 0.42 | **0.60** | 9,914 ft | roll priority 7/10 |

Nominal is fixed and holds: zero escalations, zero crashes, and the seven
to ten episodes that never engage the machinery sit at 318-346 ft.  (The
359 ft mean is one non-escalating outlier at 718 ft; the median is
326 ft.  v3's own nominal mean was 378 ft.)

**The fault side is a large measured regression, and it is predicted to
stay one at power.**  Two of the three are already CI-separated worse at
n=10 (8/10 against 4/100; 7/10 against 16/100); damaged wing is not
(0.60 [0.31, 0.83] against 0.42).

### Why — the mechanism, stated before the powered run

1. **Status-quo measurements cannot score a hypothetical corner.**  Every
   axis is measured on the aircraft as it is NOW, under the regime that
   is failing, and then attributed to corners that would change that
   situation.  In the jam the sustained sink is large because the
   unwinnable heading fight is bleeding lift — retire heading and the
   sink goes away — but the altitude axis cannot know that, so it reads
   "altitude unachievable" and the corner that surrenders BOTH heading
   and altitude (roll priority) dominates the corner that surrenders
   heading alone (orbit).  Orbit — the corner v3's 0.04 was built on —
   was adopted in 0 of 10 jam episodes.  Moving the axis from
   demand-driven to disturbance-driven (fix 2b) narrowed this but did not
   remove it: the disturbance is a status-quo measurement too.
2. **Escalation is far too late.**  The published verdict lands at ~44 s
   in the jam block, ~34 s after fault onset; v3's trim/orbit landed at
   ~16 s / ~27 s.  By then the airframe is in an established spiral, and
   no corner recovers it.  This is inherited from the v2.0.0 evidence
   rule, not from the fixes here (the settling-band floor is inert
   whenever the error is far outside the band, which is every fault).

The Pareto reframe's own argument — regimes are incomparable corners, so
select by dominance over declared axes — is not what is being falsified
here.  What the measurement falsifies is scoring those axes from the
failing regime's own telemetry.

## Prediction for the powered re-run (committed before the n=100 x 4 block)

Frozen: `control_regime_escalation` v3.1.0, `f16_flight_path_control`
v2.1.0, `embodied_motor_program` v1.8.0, base seed 241102975 + scenario
index x 10000, n=100, 100 s, 10 Hz, results in
`results/jsbsim_f16_paper_replication_10hz_pareto_frontier_v2/`.

- **Nominal**: crash 0.00.  Altitude RMSE between 320 and 400 ft, i.e.
  possibly ABOVE the prereg'd 352 ft floor on the mean while every
  non-escalating episode sits at 318-350 ft, because that floor was set
  from a pre-arch4 nominal and one bad-transient outlier moves a mean of
  this spread.  Escalations at most 5/100.
- **Jammed rudder**: crash CI-separated WORSE than v3's 0.04 — expected
  around 0.6-0.9.
- **Saturated elevator**: crash CI-separated WORSE than v3's 0.16 —
  expected around 0.5-0.8.
- **Damaged wing**: crash worse than or equal to v3's 0.42, expected
  0.5-0.7, and NOT necessarily CI-separated.
- Every fault scenario's altitude RMSE far worse than v3, because the
  selected corners surrender altitude.
- **This is prereg'd as a NEGATIVE.**  If it lands as predicted, v3
  (deliberation architecture, `results/..._matrix_v3/`) remains the
  standing best and this run is recorded as the second measured null in
  this line, alongside arch4.  It is being run at power rather than
  called from the pre-flight because the standing rule cuts both ways: a
  10-seed block is not evidence about the distribution, whichever
  direction it points.

## Availability ablation, and a second powered block (prereg'd before running)

`regime_max_ordinal` is the consumer's declared AVAILABILITY ceiling: a
candidate above it is never proposed at all.  Holding EVERYTHING else
fixed (same seeds, same evidence machinery, same achievability
instruments, same strict-improvement policy) and declaring only the
v3-era corners available (ceiling 2: sideslip trim, steady orbit),
n=10:

| scenario | v3 (n=100) | ceiling 5 (n=10) | ceiling 2 (n=10) |
|---|---:|---:|---:|
| jammed rudder | 0.04 | 0.80 | **0.10** — orbit adopted 9/10 |
| saturated elevator | 0.16 | 0.70 | **0.00** — 0/10 escalations |

This isolates the regression cleanly: **it is the two new corners, not
the rewritten selection machinery.**  With them unavailable the same
machinery adopts orbit in the jam and survives 9/10; with them available
the frontier hands the jam to roll priority (surrender heading AND
altitude) in 9/10 and the aircraft flies wings-level into the ground.
It is the prereg'd "Named risk" measured with a clean ablation: a
surrendered axis is scored a flat 0.0 while a kept one is scored
unbounded-below, so the corner that gives up the most wins as soon as
two axes are negative — and in a jam BOTH are, because the sustained
sink is a consequence of the heading fight the orbit corner would end.

The v3 block itself says the same thing from the other side: 98/100 of
its jam episodes adopted trim (median action 478) and 83/100 orbit
(median 487) — v3 escalated just as LATE as this rewrite does.  Timing is
not the differentiator; keeping the altitude objective is.

**Second powered block, prereg'd here before it is run.** Same protocol,
same frozen seeds, `regime_max_ordinal = 2`, results in
`results/jsbsim_f16_paper_replication_10hz_pareto_ceiling2_v1/`.

- **Nominal**: identical to the ceiling-5 nominal block.  Nominal never
  publishes a regime change, so the ceiling cannot matter; if the two
  nominal blocks differ at all, something else is non-deterministic and
  every comparison in this document needs re-examining.
- **Jammed rudder**: crash 0.05-0.20, CI-OVERLAPPING with v3's 0.04.
  Predicted a null, not an improvement.
- **Saturated elevator**: crash 0.00-0.15, i.e. equal or better than
  v3's 0.16; CI-separated better only if it lands at or below ~0.06.
- **Damaged wing**: no ablation data exists for this scenario, and the
  corner the design analysis assigns it (roll priority) is exactly what
  the ceiling removes.  Predicted at or near v3's 0.42, CI-overlapping,
  with the honest possibility that it is worse because the wing fault's
  inversion has no corner left that addresses it.

---

## The sixth axis (2026-08-05) — the residual this line kept recording

Both powered blocks recorded the same honest residual: with five declared
axes the sideslip-trim corner is Pareto-IDENTICAL to "hold", because the
objective it surrenders -- zero sideslip -- is not one of the five.  The
blocks show it directly: trim and orbit are adopted in exactly the same
episodes (93/93 in the ceiling-2 jam block, 88/88 for the damaged wing),
never trim alone.  v3's measured jam survival went trim FIRST (98/100,
median action 478) and orbit after: a corner this frontier could not
represent at all.

`f16_flight_path_control` v3.1.0 declares it.  The margin is the same
disturbance-vs-authority shape every other axis uses -- the sustained
lateral body velocity the yaw drive is failing to null, against the only
lateral quantum this protocol declares (the published airspeed settling
band), at the same 1.5x operating-point margin.  The trim corner
surrenders it; the orbit corner surrenders it too (orbit is trim's
machinery plus a wings-level roll override); every other corner keeps it.
The six objectives are now held as `Goal` nodes
(`episode -holds_flight_objective->`), so the basis is inspectable graph
data rather than a hand-typed count.

**A measured hazard, recorded and NOT shipped.**  `cognitive_pareto`
v1.1.0 lets a value identify its axis by graph identity (`measures_goal`)
or by `dimension_ordinal`, and `same_dimension` picks the branch from
whether BOTH values carry the edge.  Binding those edges from a separate
rule is a mid-fixpoint race: while they land, some pairs compare by
identity and others by ordinal.  Measured on the sink probe -- with the
binding rule installed ALL FIVE corners were flagged `dominated` at once
(empty frontier, no verdict, four spurious GoalRevisionRequests); without
it, speed priority is the unique survivor and one request is minted,
which is correct.  The fix is not rule ordering: a value must never be
OBSERVED unbound, so the edge belongs in the effect list that mints the
value.  Deferred, with the rule left unwired in the file.

### Single-seed probe, disclosed (NOT a result)

Jammed rudder, base seed 241112975, five axes -> six: crash -> no crash,
minimum altitude -15 ft -> 3,753 ft, altitude RMSE 7,248 -> 4,526 ft, and
the corner sequence changes from roll priority (447) + speed priority
(845) to **trim (268) then orbit (446)** -- v3's own measured sequence,
and 18 s earlier, because the jam's signature is lateral and there is
finally an axis that sees it.  Nominal on its base seed is byte-identical
(323.283 ft, no escalation, no corner adopted).

One seed is not evidence about the distribution.  This document already
records that rule being demonstrated on itself: a 0/10 saturated-elevator
pre-flight came back 0.17 at n=100, with all seventeen crashes in the
ninety seeds the pre-flight never ran.

## Prediction for the six-axis powered block (committed before it runs)

Frozen: `control_regime_escalation` v4.0.0 (verdict by counterexample via
`cognitive_pareto`'s goal-audit faculty), `f16_flight_path_control`
v3.1.0 (six axes), `cognitive_pareto` v1.1.0, `embodied_motor_program`
v1.8.0.  Same protocol, same frozen seeds, n=100 x 4, results in
`results/jsbsim_f16_paper_replication_10hz_pareto_sixaxis_v1/`.

- **Nominal**: crash 0.00 and altitude RMSE 324.2 ft, BYTE-IDENTICAL to
  both previous blocks.  Nominal never publishes a regime change, and the
  sixth axis cannot change that -- in healthy flight lateral velocity is
  near zero, so surrendering zero sideslip is a pure Pareto cost.  If
  nominal moves at all, the sixth axis is firing in healthy flight and
  the fault blocks are uninterpretable.
- **Jammed rudder** (v3: 0.04; five-axis ceiling-5: 0.65): the corner
  sequence the probe shows is v3's, so the honest prediction is a return
  toward v3 -- crash 0.00-0.15, CI-separated BETTER than the five-axis
  0.65 and CI-OVERLAPPING with v3's 0.04.  A CI-separated improvement on
  v3 itself is NOT predicted.
- **Saturated elevator** (v3: 0.16; five-axis: 0.73): improvement over
  the five-axis block, but this fault is not lateral and the sixth axis
  should barely engage -- predicted 0.10-0.35, CI-overlapping with v3.
- **Damaged wing** (v3: 0.42; five-axis: 0.73): least confident.  The
  wing fault has a lateral signature, so trim may now be reachable where
  it was not; predicted 0.35-0.65, CI-overlapping with v3.
- **The named risk is unchanged and still unmeasured against**: a
  surrendered axis is scored a flat 0.0 against an unbounded-below kept
  axis.  Adding a sixth axis gives the maximal-surrender corner one more
  thing to give up, so it is not obvious a priori that this helps the
  wing at all.
- **Reported as a null if it is one.**  v3 remains the standing best
  until something is CI-separated better than it.

---

## Order as a PLANT-KIND-CHANGE detector — prereg (2026-08-06)

Not a gate.  This predicts a STRUCTURE and is falsifiable independently of
whether any aircraft survives.

The distinction, from the project owner: a saturated elevator does not
change the KIND of the plant -- same equations, smaller coefficient.  A
jammed rudder and a damaged wing do.  Changing WHICH OBJECTIVES you
pursue is the right response to a kind change and the wrong response to a
parameter change, which wants the recalibration path that already exists.
This explains, without reference to any score, why the speed-priority
corner was never selected in 40 episodes and why selecting it in blocks 1
and 3 caused crashes rather than preventing them: it was built for the
saturated elevator, a fault that never asked for a different objective
set.

### Classification, committed BEFORE the run, from the declared fault spec

The criterion is structural, not outcome-derived: **a fault is a KIND
change iff it introduces a persistent uncommanded forcing term or FLIPS
THE SIGN of a stability derivative** (the closed loop's equilibrium
structure changes, so an objective becomes unattainable rather than
merely harder).  Scaling a coefficient, limiting travel, adding drag or
moving mass is a PARAMETER change.

| scenario | declared modification | class |
|---|---|---|
| nominal | none | control |
| jammed_rudder | `fixed_command` yaw = 0.500 — persistent uncommanded moment | **KIND** |
| broken_aileron | roll authority 0.5 **+ `parasitic_roll_coefficient` 0.01** — a new forcing term, but a small one | **KIND (weak)** |
| saturated_elevator | `command_limit` pitch 0.05 | PARAMETER |
| landing_gear | `gear_drag` x3, gear deployed | PARAMETER |
| shifted_cg | `cg_scale` (1.2, 1.4, 0.7) | PARAMETER |
| damaged_tail | `lift_elevator` 0.5, `pitch_q` 0.5, `pitch_alpha` 0.5, drag up — all positive scalings | PARAMETER |
| damaged_wing | **`roll_beta` -1.0, `roll_r` -1.0** — dihedral effect REVERSED, a sign flip | **KIND** |

### Prediction

Sustained measured order (`f16_axis_order_*`, the held finite-difference
recursion's own verdict, read across deliberations rather than at one
sample):

- **KIND faults hold order >= 2 on the axis whose structure the fault
  changed**, sustained across deliberations: jammed rudder and damaged
  wing on the lateral axes (sideslip / heading / attitude), broken
  aileron on roll.
- **PARAMETER faults settle to order <= 1** after their commanded
  transient, on every axis.
- **nominal** never engages the mechanism.

Already observed at n=1 and NOT part of the test: jammed rudder held
sideslip 3 / attitude 3 / heading 2; damaged wing held sideslip 4 /
heading 3 / attitude 3; saturated elevator settled to 0-1 and never
escalated.  **The prediction is therefore genuinely at risk on four
scenarios I have not looked at: broken_aileron, landing_gear, shifted_cg
and damaged_tail.**  Three of those are predicted PARAMETER and must
settle to <= 1; broken_aileron is predicted KIND on a forcing term two
orders of magnitude smaller than the jam's, and is the most likely single
falsifier.

### What would falsify it

A parameter fault holding order >= 2 sustained on any axis, or a kind
fault settling to <= 1 on the axis its own spec structurally altered.
Either kills the reading that order distinguishes kind from degree.  An
honest third outcome is that order tracks EXCITATION rather than kind --
visible as high order on whichever axis is merely most disturbed,
regardless of class -- and the damaged-tail case is the discriminator
there, being a large parameter change on the pitch axis.

n = 3 seeds per scenario, 100 s, frozen block seeds (base 241102975 +
scenario index x 10000).  Three seeds is not a distribution and no crash
rate is claimed from this run; the claim is about the ORDER SIGNAL only.

### RESULT — the strong prediction is FALSIFIED (n=3 per scenario)

Sustained order = median across every deliberation-opening projection in
an episode, pooled over 3 seeds.

| scenario | class | alt | head | side | atti | esc |
|---|---|---:|---:|---:|---:|---:|
| nominal | control | 0.0 | 0.0 | 1.0 | 1.0 | 0/3 |
| jammed_rudder | KIND | 1.0 | **2.0** | **3.0** | **3.0** | 3/3 |
| broken_aileron | KIND(weak) | 0.5 | 0.0 | **2.0** | **2.0** | 0/3 |
| saturated_elevator | param | 1.0 | 0.0 | **2.0** | 0.0 | 0/3 |
| landing_gear | param | 0.0 | 0.0 | **2.0** | 1.0 | 0/3 |
| shifted_cg | param | 1.0 | 1.0 | 1.0 | 0.5 | 0/3 |
| damaged_tail | param | 1.0 | 1.0 | **2.0** | **2.0** | 1/3 |
| damaged_wing | KIND | 1.5 | 1.5 | **2.5** | **2.0** | 2/3 |

**Three of four PARAMETER faults hold order >= 2**, so "parameter settles
to <= 1 on every axis" is dead.  All three kind faults held, but that half
of the prediction is worthless on its own -- a rule that fires on 6 of 7
faults discriminates nothing.

**The falsifier is the same axis every time: sideslip.**  It reads >= 2
for every fault regardless of class, which is the EXCITATION reading this
prereg named as its honest third outcome -- order tracking how disturbed
an axis is rather than what kind of change occurred.

The excitation reading does not survive intact either, and the
discriminator this prereg nominated is why: **damaged_tail is a large
parameter change on the PITCH axis, and its high orders are on SIDESLIP
and ATTITUDE while its altitude axis sits at 1.0.**  Pure excitation
would have put the signal where the fault was.  So sideslip's order is
measuring something common to being in a disturbed lateral state, not the
fault's own axis, and not its class.

What is left, stated as a HYPOTHESIS FOR A SEPARATE PREREG and not as a
result of this one -- it is a post-hoc reading of a falsified prediction
on three seeds:

- **heading order separates the classes in this sample**: KIND 1.5-2.0
  (jam 2.0, wing 1.5) against PARAMETER <= 1.0 (elevator 0.0, gear 0.0,
  cg 1.0, tail 1.0) and nominal 0.0.  Broken aileron reads 0.0 and would
  falsify it immediately, which is exactly why it must be prereg'd and
  run before being believed.
- **sideslip MAGNITUDE** may separate where its threshold does not: KIND
  2.5-3.0 against PARAMETER 2.0.  Three seeds cannot support a threshold
  between 2.0 and 2.5.

`shifted_cg` is the one clean parameter case (<= 1.0 on every axis).
No crash rate is claimed from n=3; the two damaged-wing crashes and the
zero elsewhere are recorded only as run conditions.

---

## WHAT KIND OF CHANGE WAS IT? — prereg (2026-08-06)

Not a gate, and not a crash-rate claim.  This predicts a STRUCTURE, and it
is the successor to the FALSIFIED order-as-detector prediction above.  It is
committed before any fault scenario has been run through the mechanism it
describes; the only run made before writing it was **nominal**, as a smoke
test that the machinery fires and does not change the flight (altitude RMSE
323.283 ft on the base seed, byte-identical to the pre-regime-machinery
baseline, and every channel INDETERMINATE).

### What is being claimed, and what is NOT

A fault changes a controlled plant in one of three ways.  This is a generic
statement about controlled systems with nothing aircraft-specific in it:

1. **PARAMETER** — the fixpoint still exists and still attracts; only where
   it sits, or how much authority reaches it, changed.
2. **STABILITY** — the fixpoint still exists but stops attracting properly
   (reduced restoring stiffness and/or damping).
3. **KIND** — the fixpoint is gone, or a new forcing term / sign flip
   replaced it.

Only class 3 warrants changing WHICH OBJECTIVES are pursued.  Class 1 wants
recalibration, which already exists and already works.  Class 2 wants
re-stabilisation — the objective is still attainable, the loop just cannot
hold it — and **there is no re-stabilisation path in this tree**, so the
build mints a residual and says so rather than inventing one.

Measured consequence of confusing them (`docs/regime_pareto_frontier_results.md`
block 3): 26 of 27 jammed-rudder crashes ended on a corner that surrendered
altitude, because the frontier was being asked parameter and stability
questions and could only answer by giving up objectives.

### The instrument, stated before it is pointed at anything

`control_regime_escalation` v5.0.0 classifies; `f16_flight_path_control`
v6.0.0 only publishes integers to it.  The general seed contains no domain
vocabulary (gated by
`tests/test_control_regime_escalation_migrated.py::test_seed_is_general_and_declares_the_contract`).

The consumer already runs the held order-N recursion (`TimeInfer`, the same
`diff_pyramid` / `robust_order_min` / `steps_to_origin` machinery
`GENERIC_ORDER_N_RESULTS.md` gated) on each axis's own margin stream once
per deliberation, and it publishes the TWO readings that fit produced:

* `channel_order` — the ORDER it fitted;
* `channel_crossing` — the STEPS-TO-FLOOR it projected, shifted by one so
  that ZERO means "this channel's floor has been reached" (`steps_to_origin`
  counts steps and is bounded below by 1; the operator's own contract says a
  caller whose terminal state is elsewhere shifts its own coordinate).

**The general seed runs THE SAME recursion on THOSE streams** — the operator
one level up, the move this substrate makes repeatedly (strokes to
characters, regimes to cognition).  Exactly one test is used, twice:

> *does this stream's own fitted generator carry it to its floor inside the
> evidence it was fitted from?* — `crossing < Count(history)`

and the classification is:

| order stream | crossing stream | class |
|---|---|---|
| returns to its floor | — | **PARAMETER** |
| does not return | returns to its floor | **KIND** |
| does not return | does not return | **STABILITY** |
| fewer than 4 samples | — | **INDETERMINATE** |

**THERE IS NO THRESHOLD ON THE ORDER VALUE ANYWHERE.**  The falsified
prediction above thresholded it (`order >= 2`) and died; the level is
deliberately never consulted here, and that is gated by a test
(`test_the_order_level_itself_is_never_thresholded`: a stream pinned at 4
and a stream pinned at 2 must read the same class).

Two declared quantities are used, and both are the operator's own, not
picked to make scenarios come out right:

* **`crossing < Count`** — believe a projection only as far as the evidence
  it was fitted from.  That is the identifiability guard `CLAUDE.md` already
  declares (pin a continuous parameter only to observational resolution).
  It is also why this test needs no constant.
* **four samples** — the shortest stream from which the recursion's robust
  witness can produce a fit at all (`robust_order_min` needs `min_order + 2`
  = three difference samples).  Below it, "no fit" is a statement about the
  evidence, not about the stream.  `max_steps` is set to 1024 and is INERT:
  the comparison is against `Count`, which is always far smaller.

### Classification from the DECLARED fault spec, committed before the run

Structural criterion, refined from the two-class one above to have a
stability category: a fault is **KIND** iff it introduces a persistent
uncommanded forcing term or FLIPS THE SIGN of a stability derivative;
**STABILITY** iff it reduces a restoring-stiffness or damping derivative
without flipping its sign; **PARAMETER** otherwise (scaling authority,
limiting travel, adding drag, moving mass).

| scenario | declared modification | a priori class |
|---|---|---|
| nominal | none | control |
| jammed_rudder | `fixed_command` yaw = 0.500 — persistent uncommanded moment | **KIND** |
| broken_aileron | roll authority 0.5 + `parasitic_roll_coefficient` +0.01 — a new forcing term, two orders of magnitude smaller than the jam's | **KIND (weak)** |
| saturated_elevator | `command_limit` pitch 0.05 — travel limited, no derivative touched | PARAMETER |
| landing_gear | `gear_drag` x3, gear deployed | PARAMETER |
| shifted_cg | `cg_scale` (1.20, 1.40, 0.70) | PARAMETER |
| damaged_tail | `pitch_q` 0.5 **and** `pitch_alpha` 0.5 — pitch damping AND pitch stiffness halved, signs unchanged (plus `lift_elevator`/`pitch_elevator` 0.5 authority and drag up) | **STABILITY** |
| damaged_wing | `roll_beta` -1.0, `roll_r` -1.0 — dihedral effect REVERSED, a sign flip | **KIND** |

**`damaged_tail` IS A RECLASSIFICATION AND MUST BE READ AS ONE.**  The
two-class table above assigned it PARAMETER, because that criterion had no
stability category and PARAMETER was the only non-KIND option.  The
three-class criterion assigns it STABILITY from the SAME declared spec — but
**the criterion was written after its measured order trajectory had been
seen** (it holds 2-3 across deliberations and never decays), so this row is
not an independent a-priori assignment and no confirmation of it counts for
much.  Every other row is unchanged from the earlier, already-committed
table.

### Prediction

Per channel the classifier emits one of the four classes.  The EPISODE
roll-up — what the gate acts on — is: KIND if any channel reads KIND, else
STABILITY if any reads STABILITY, else PARAMETER if any reads PARAMETER,
else INDETERMINATE.

1. **The three KIND faults roll up KIND** on at least one channel, in a
   majority of seeds: jammed_rudder, damaged_wing, broken_aileron.
2. **The three PARAMETER faults never roll up KIND**: saturated_elevator,
   landing_gear, shifted_cg read PARAMETER or INDETERMINATE.
3. **damaged_tail rolls up STABILITY** — neither KIND nor PARAMETER.
   (Reclassified row; see above.)
4. **nominal rolls up INDETERMINATE on every channel and every seed.**  It
   opens two deliberations in a 100 s episode, which is below the
   recursion's own evidence requirement, and there is nothing to classify.

### What would falsify it

* Any PARAMETER-classified fault rolling up **KIND** on a majority of seeds.
* Any KIND-classified fault rolling up **PARAMETER**.
* **nominal** reading anything but INDETERMINATE.
* **Every scenario reading the same class.**  A classifier that fires on 7
  of 7 faults discriminates nothing — that is exactly how the previous
  prediction died, and the same disposal applies here.
* **Everything reading INDETERMINATE.**  The instrument would then be
  degenerate at this episode length rather than wrong, and that is a null,
  reported as a null.

### Named in advance: the most likely falsifiers

**`broken_aileron` is the most likely single falsifier**, for the same
reason it was last time and one more.  Its forcing term is two orders of
magnitude smaller than the jam's; it escalated 0 of 3 times in the recorded
block, so its deliberation streams are short and may not clear the
four-sample evidence requirement at all; and a small parasitic roll is
unlikely to consume any channel's projected room, so the honest expectation
is that it reads STABILITY or INDETERMINATE where the a-priori class says
KIND.

**The most likely DEGENERATE outcome is the sideslip channel reading KIND
everywhere.**  The falsified prediction above recorded that sideslip holds
order >= 2 for every fault regardless of class, and in the recorded jam
block `f16_axis_clock_sideslip` sits at 1 — the floor — at every
deliberation.  If every fault's sideslip margin is pinned at its floor, its
crossing stream trivially "returns", every fault rolls up KIND, and the
instrument discriminates nothing.  This is named here so that it cannot be
reported afterwards as anything but the falsification it would be.

**A third, quieter risk:** a noisy crossing stream can fit at order 3 and
project AWAY from its floor even while falling (measured on a synthetic
stream, `[900, 700, 500, 380, 240, 120]` → `order_fit = 3`, `crossing`
saturated).  That turns a KIND reading into a STABILITY reading, so the KIND
test is conservative in the presence of noise, and a STABILITY result on a
KIND fault is weaker evidence against the reading than a KIND result on a
PARAMETER fault is.

### Protocol

n = 3 seeds per scenario x 8 scenarios, 100 s, 10 Hz, frozen block seeds
(base 241102975 + scenario index x 10000 over `SCENARIO_ORDER`),
`--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`.  **The class gate is OFF**
(`regime_class_gate_enabled = 0`), so the flight is byte-identical to the
block the order streams were read from and the classifier is measured
against a known baseline rather than against dynamics it has itself
perturbed.  Verified on nominal: 323.283 ft, unchanged.

Frozen: `control_regime_escalation` v5.0.0, `f16_flight_path_control`
v6.0.0, `cognitive_pareto` v1.1.0, `embodied_motor_program` v1.8.0.

**Three seeds is not a distribution.**  No crash rate is claimed from this
run, and nothing here is evidence that gating the response helps or harms
survival — the gate ships built, tested on synthetic streams, and MEASURED
ONLY AS A CLASSIFIER.  Whether routing on the class changes flight outcomes
is a separate powered question and is not answered here.

### SUPERSEDED 2026-08-06 — the three-way sort above was the WRONG TYPE, and it was measured wrong

The prereg immediately above ("WHAT KIND OF CHANGE WAS IT?") is superseded,
not deleted: the superseded prediction and its reason are part of the
record.  It was run first, and it FAILED, and the way it failed is the
evidence for the correction that replaced it.

**Measured, n=3 x 8, `control_regime_escalation` v5.0.0 /
`f16_flight_path_control` v6.0.0, gate off, flight byte-identical
(nominal 323.283 ft).**  Episode roll-up (KIND if any channel reads KIND,
else STABILITY, else PARAMETER, else INDETERMINATE):

| scenario | a priori | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| nominal | control | IND | IND | IND |
| jammed_rudder | KIND | **STAB** | KIND | KIND |
| broken_aileron | KIND (weak) | **STAB** | **IND** | **STAB** |
| saturated_elevator | PARAMETER | **STAB** | **STAB** | **STAB** |
| landing_gear | PARAMETER | IND | IND | **STAB** |
| shifted_cg | PARAMETER | **STAB** | **STAB** | **KIND** |
| damaged_tail | STABILITY (reclassified) | STAB | **KIND** | STAB |
| damaged_wing | KIND | **STAB** | **STAB** | **STAB** |

**Three named falsifiers fired at once.**  A PARAMETER fault rolled up KIND
(`shifted_cg` seed 3).  A KIND fault never once rolled up KIND
(`damaged_wing`, 0/3 — and it is the sign-flip case, the least ambiguous
KIND in the table).  And **17 of 24 episodes read the same class**, which is
the "a rule that fires on everything discriminates nothing" disposal this
document already applied to the order-threshold reading.  `broken_aileron`,
named in advance as the most likely single falsifier, duly failed 0/3.
Only nominal held (4/4 channels INDETERMINATE on all three seeds).

**The corrected diagnosis, from the project owner, and it is deeper than
"the boundary was wrong":**

> STABILITY IS NOT A THIRD CLASS.  It is a TRANSITION.  A destabilised
> fixpoint is a kind change that has not finished happening yet, its onset
> timescale set by the environment — gust energy, the size of the commanded
> manoeuvre, how long the episode runs — not by the fault alone.  Perturb a
> marginally-stable plant enough, or wait long enough, and the trajectory
> leaves the shrinking basin, at which point the fixpoint is gone FOR THAT
> TRAJECTORY.

So the partition was the wrong TYPE, not merely the wrong boundary.  A
category was being read off a STATIC FAULT SPEC when the quantity is
RELATIONAL — fault x environment x horizon — and **the same fault is a
different "class" in different conditions.**  The measured table is exactly
what that predicts: `damaged_wing` reading STABILITY on three seeds is not
the instrument failing to see a sign flip, it is the sign flip not having
finished happening inside a 100 s episode at these gust draws; `shifted_cg`
reading KIND on one seed of three is the same fault in a rougher condition.
A three-valued attr cannot represent that, and no boundary between three
values would have.

It also disposes of the "STABILITY has no route" gap the superseded build
minted a residual for.  **There was no third response to invent — the
missing route was an artifact of the missing dimension.**

Two further corrections arrived with it and are folded into the successor:

* **The response set is not {recalibrate, change objectives}.**  It includes
  CHANGE THE OPERATING CONDITION so the fixpoint stays attainable.  A
  damaged tail halved pitch stiffness and damping; aerodynamic moments scale
  with dynamic pressure, so flying faster multiplies them back up — the same
  fault has an attainable fixpoint at a higher speed and a collapsing one at
  a lower speed.  Excitation matters as much as authority: a shrinking basin
  that is not probed hard does not get left.
* **A transition time is only actionable while the ESCAPE from the regime
  survives.**  Fifty metres further down the storm drain the projection that
  the pond is coming is just as accurate and completely useless, because
  reversing is no longer possible.  Two clocks, and the second expires
  first.

---

## TWO CLOCKS — prereg (2026-08-06, supersedes the three-way sort)

`control_regime_escalation` v6.0.0 mints TIMES, not classes:

  `T_transition`  actions until the held regime's fixpoint is no longer
                  attainable.
  `T_option`      actions until the ESCAPE from that regime is no longer
                  available.

Both in the integer action quanta everything else in this line uses, with
the consumer's declared horizon as an honest ceiling for "beyond what I can
see"; both projected FROM THE TRAJECTORY by the same held order-N recursion
the consumer runs on its own margins, applied one level up to the streams of
what that recursion measured; both computed EVERY ACTION whether or not a
deliberation is open.  The gate reads
`regime_actions_to_act = MIN(T_transition, T_option)`.

Each per-channel clock is the minimum of two grains of one operator, and
there is no threshold in it: the POINT reading is the consumer's own
order-N projection of that channel's margin over its whole sample window,
and the SAMPLE reading is the same operator applied to the stream of those
projections (how many samples until the deadline itself reaches zero),
converted to actions by the MEASURED spacing between samples rather than a
declared constant.  Below the recursion's own evidence requirement the fit
floors, the sample reading saturates, and the minimum falls back to the
point reading — the honest behaviour, and no evidence guard is written.

The response set is three REGIONS OF ONE QUANTITY, and both boundaries are
declared quantities already in this contract: ZERO (the integer lattice's
origin the operator projects to) and `regime_evidence_horizon_actions` (the
loop's own slow time constant).

| acting clock | response |
|---|---|
| `<= 0` — the fixpoint is gone | the full corner set; surrendering an objective is honest when the objective no longer exists |
| `0 < t <` control horizon | ONLY a candidate declaring `candidate_restores_basin` — move the plant to where the basin is bigger, while the authority to move it still exists |
| `>=` control horizon | recalibrate.  "Never" and "beyond anything I can plan over" are the same response; which it was is in the minted time |

### A HYPOTHESIS, pre-registered and NOT established

`speed_priority` is the one corner declaring `candidate_restores_basin`, and
the declaration is a hypothesis.  That corner was built for the saturated
elevator and measured **useless** there — 0 adoptions in 40 pre-flight
episodes, and crashes when it fired in block 3.  The saturated elevator is a
limited-travel fault that never asked for anything but recalibration.  Under
the corrected reading the corner answers a DIFFERENT question: commanding
speed multiplies control moments back up with dynamic pressure, which
restores the very stiffness and damping a fault removed.  Same corner, right
question.  **The evidence so far speaks only to the old question, and this
run does not test the new one** — the gate is off.

Also recorded, from the same source and not tested here: the metastable
regime was the VEHICLE for the escape, not a holding pattern (the youth
reversed the jumping, he did not stop — stopping was falling in).  So the
response to a projected transition is not necessarily to leave the current
corner; re-aiming it may be the manoeuvre.  `f16_speed_priority_on_authority_loss`
is already that shape — it re-aims the forward axis inside trim and roll
priority rather than replacing them.

### Prediction

1. **nominal: both clocks at the ceiling on every channel and every seed.**
   No transition is projected in healthy flight.  (Observed on the base seed
   already and disclosed: 1023 on every clock, 323.283 ft.)
2. **Every fault scenario projects a FINITE acting clock at some point in
   the episode** — the quantity is not degenerate at the ceiling for faults.
3. **The acting clock is CONDITION-DEPENDENT within a scenario.**  For at
   least one scenario, the three seeds' minimum acting clocks straddle the
   declared control horizon (80 actions): the same fault reads "act now" in
   one condition and "not yet" in another.  This is the direct test of the
   correction's own central claim.
4. **The option clock binds before the transition clock somewhere.**  In at
   least one fault scenario, `regime_actions_to_option_loss <
   regime_actions_to_transition` at some action.  If it never binds, the
   second clock bought nothing in this domain and that is a null on it.
5. **`damaged_tail`'s acting clock is finite and not pinned at zero** — the
   "transitioning at a rate this environment sets" reading, and the scenario
   the corrected diagnosis names.

### What would falsify it

* nominal projecting a finite acting clock.
* A fault whose acting clock never leaves the ceiling.
* Every seed of every scenario landing on the SAME side of the control
  horizon — the quantity would be fault-determined and the relational claim
  unsupported by this measurement.
* The acting clock pinned at ZERO for every fault from the first sample —
  see below.

### Named in advance: the most likely falsifier, and the disclosure it rests on

**FULL DISCLOSURE: this prediction is NOT blind.**  The superseded block
above was run before it was written, and its sideslip order and clock
streams for all eight scenarios are in this document.  What I have seen is
that `f16_axis_clock_sideslip` reads 1 — its floor — at the first
deliberation in the jam, the saturated elevator, the damaged tail and the
damaged wing.  I have not computed the new quantity on any fault scenario.

That seen data names the falsifier directly: **the acting clock may be
pinned at 0 for every fault from the moment the fault lands**, because the
lateral margins reach their floor almost immediately.  If so, every fault
reads "fixpoint already gone", the transition region is empty, the option
clock never gets a chance to bind, and the instrument is measuring fault
ONSET rather than a transition.  **`saturated_elevator` is the most likely
single falsifier** — an a-priori parameter fault whose sideslip clock hit
its floor immediately in the superseded block, so it is predicted to read
"fixpoint gone" from the start, which under this build would admit the full
corner set for a fault that wants recalibration.

### Protocol

n = 3 seeds per scenario x 8 scenarios, 100 s, 10 Hz, frozen block seeds
(base 241102975 + scenario index x 10000 over `SCENARIO_ORDER`),
`--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **gate OFF**
(`regime_class_gate_enabled = 0`) so the flight is byte-identical to every
earlier block in this line and the clocks are measured against a known
baseline rather than against dynamics they have themselves perturbed.
Verified: nominal 323.283 ft under v6.0.0/v7.0.0, unchanged.

Frozen: `control_regime_escalation` v6.0.0, `f16_flight_path_control`
v7.0.0, `cognitive_pareto` v1.1.0, `embodied_motor_program` v1.8.0.

**Three seeds is not a distribution.**  No crash rate is claimed.  Nothing
here is evidence that gating the response helps or harms survival; the gate
ships built and tested on synthetic streams, and is MEASURED ONLY AS A
PROJECTOR.

### ADDENDUM 2026-08-06 — the option clock is ENERGY, and this is prereg'd before its block

The two-clock block above ran and is falsified (see the results document).
The diagnosis is that the TRANSITION clock is EXCURSION-PRONE: a commanded
manoeuvre in a HEALTHY aircraft drives the sideslip channel's margin to its
floor and the acting clock reads zero for ~200 actions, then recovers.  The
instrument is not lying — during a 40 degree turn entry the zero-sideslip
fixpoint really is momentarily unattainable — but it does not separate "I am
manoeuvring" from "I am losing the plant", because a manoeuvre IS an
operating-condition change.  That is the correction's own claim (the onset
timescale is set by the size of the commanded manoeuvre) confirmed at the
cost of the discriminator.

The correcting frame, from the project owner: **it is about energy
conservation and thermodynamic options.  SPENDING ENERGY LIMITS YOUR FUTURE
OPTIONS.**  That names exactly the property the transition clock lacks and
the option clock should have:

* Altitude and airspeed are interchangeable at a declared rate, so neither
  alone says whether the escape is affordable.  Their SUM — specific energy
  `h + v^2/2g` — does, and unlike either of them **it cannot be bought
  back.**  Drag only ever removes it.
* So a commanded manoeuvre BORROWS against one axis and repays it from the
  other, leaving the option intact; a fault that bleeds energy closes the
  option for good.  The reversible excursion and the irreversible loss are
  different quantities, and the option clock should be projected from the
  irreversible one.

`f16_flight_path_control` v7.0.0's option margin is now the exact specific-
energy form: `h + v^2/2g - (v + dv*H)^2/2g`, where `dv` is
`maximum_forward_delta_m_s` and `H` is `regime_evidence_horizon_actions` —
the energy height needed to sustain, over the loop's own declared control
horizon, the speed increase that restores the basin.  Every term is already
declared by this loop and no aerodynamic law is written.  (The altitude-only
form the falsified block used, `v*dv*H/g`, is the first-order expansion of
exactly this expression.)

**Prediction, committed before the energy block runs.**

1. **In nominal the ENERGY option clock stays at its ceiling through the
   commanded reference change**, while the transition clock still goes to
   zero there.  This is the direct test of the conservation claim: the
   manoeuvre is an energy TRADE, not an energy SPEND.
2. **The energy option clock is near-monotone within an episode** — it falls
   and does not recover to the ceiling once a fault is bleeding energy,
   whereas the transition clock recovers after every excursion.  Measured as:
   for each episode, the number of actions on which the option clock
   INCREASES back to the ceiling after leaving it.
3. **It discriminates where the transition clock did not**: at the end of a
   100 s episode the option clock separates nominal (ceiling) from at least
   the two energy-bleeding faults (`jammed_rudder`, whose unwinnable heading
   fight bleeds lift, and `damaged_wing`, whose drag is up).

**What would falsify it.** The energy clock also collapsing in nominal
during the manoeuvre (same degeneracy, nothing gained); or the energy clock
sitting at its ceiling for every fault too (inert); or its final value
overlapping nominal's across all faults (no discrimination).

**Named most likely falsifier:** `saturated_elevator` and `shifted_cg` — a
travel limit and a mass shift neither of which obviously bleeds energy, so
they are predicted to sit at or near the ceiling.  If they instead collapse,
the clock is measuring the manoeuvre again rather than the energy.

Protocol unchanged: n=3 x 8, gate off, same frozen seeds, same versions
except `f16_flight_path_control` v7.0.0's energy option margin.

### Correction to block C's falsified monotonicity — THRUST IS NOT FREE ENERGY

Block C predicted the option clock's energy would fall monotonically and
measured 5-45 recoveries per fault episode.  Recorded as falsified, and
it stays falsified: the prediction as written is dead.

But the diagnosis is not "energy is the wrong quantity".  It is that the
WRONG STOCK was tracked.  Mechanical energy (`h + v^2/2g`) is not
monotone because thrust adds to it -- and thrust is bounded twice, in
ways the block ignored:

- a RATE ceiling: maximum power in, so the ledger cannot be refilled
  arbitrarily fast;
- an AMOUNT ceiling: fuel is a finite stock, so the total that can ever
  be added is bounded.

With both columns carried, the ledger is monotone again and the
thermodynamic reading survives intact:

    TOTAL admissible energy  =  mechanical + remaining convertible fuel
                             (monotone NON-INCREASING; fuel only falls)

    reachable within horizon H  =  mechanical + min(remaining fuel,
                                   max power x H)

That is the quantity a next prereg should test, and it is a STRICTLY
STRONGER claim than block C's: not merely that a fault spends energy
while a manoeuvre trades it, but that the total ledger never refills and
every basin-restoring manoeuvre is drawn against a finite budget.

Two consequences, both unmeasured and both to be prereg'd rather than
assumed:

- `speed_priority`-as-basin-restoration HAS A PRICE.  Commanding thrust
  to restore stability spends the one column that cannot be recovered,
  so there is a finite number of such manoeuvres in an episode.  The
  hypothesis is not "restore the basin" but "restore the basin while the
  fuel to do it exists", which is a different and testable claim.
- It explains the standing `f16_speed_priority_on_authority_loss` note
  (the 1983 Negev F-15 recovery, full afterburner until fuselage lift
  and surface authority returned): that manoeuvre converts the
  irreplaceable stock into the recoverable one at the maximum rate.  It
  works BECAUSE the ledger has two columns with different reversibility.

MEASUREMENT GAP, stated plainly: this plant does not currently expose
either ceiling.  `domains/fixed_wing_jet_world.py` publishes
`engine_power_state` and nothing else -- no fuel mass, no specific
energy, no maximum power.  So the monotone total-energy ledger is NOT
computable from what is observed today, and any test of it needs the
plant to publish fuel and a thrust ceiling first.  Until then the
mechanical-energy clock is what exists, its non-monotonicity is EXPECTED
rather than anomalous, and it must not be read as the admissible set
growing.

### THE TWO-COLUMN LEDGER — prereg (2026-08-06, committed before block D runs)

Block C's monotonicity prediction is falsified and stays falsified.  This is
not its rescue; it is a DIFFERENT and strictly stronger claim, on a quantity
block C did not compute because the plant was never asked for it.

#### What is EXPOSED, and what is ASSUMED

The previous section closed with a stated measurement gap: *"this plant does
not currently expose either ceiling."*  That was wrong, and finding out how
wrong is most of this rung.  JSBSim publishes both.

**Exposed — copied out of the plant, no decision, no derivation**
(`domains/jsbsim_f16_paper_world.py` -> `observe()` ->
`scripts/jabberwock_fixed_wing_jet.py::_state_attrs` -> the episode):

| column | property | value at the block's initial condition |
|---|---|---|
| the AMOUNT: remaining stock | `propulsion/total-fuel-lbs` | 1814.4 kg |
| the RATE: engine rating | `<milthrust>` in the engine model the aircraft names (`F100-PW-229`, 17,800 lbf) | 79,178 N |
| mass the ledger is per-unit-weight of | `inertia/weight-lbs` | 9,811.2 kg |
| burn and thrust, diagnostic | `propulsion/engine/fuel-flow-rate-pps`, `propulsion/engine/thrust-lbs` | measured per action |

JSBSim's runtime `propulsion/engine/MilThrust` property is the NORMALISED
thrust-table lookup at the current flight condition (0.765 at the initial
condition), not the rating, so the rating is read from the engine model that
declares it.  A plant whose model cannot be read publishes no rating at all
and the absence is first-class.

`domains/fixed_wing_jet_world.py` now publishes the
`maximum_engine_thrust_newtons` and `mass_kg` it has declared since it was
written and never handed to the graph.  It models no fuel, so it publishes no
stock — the opposite half of the same split, and the case the general seed has
to survive.

**Assumed — and stated as an assumption, in two places, for two reasons**

1. **The fuel's specific energy: 42.8 MJ/kg, declared in the world adapter.**
   JSBSim publishes the tank CONTENTS and the engine's thrust-specific fuel
   consumption but no energy content — there is no property anywhere in the FDM
   that says what a kilogram of this fuel is worth.  So it is DECLARED, as
   Jet-A's published lower heating value, and it is declared as an UPPER bound:
   no engine extracts more work than that from a kilogram, so a ledger that
   falls under this pricing falls under the real one.  This is a plant property
   sitting beside the plant's other declared properties, not a tuning constant.
2. **A finite, monotone non-increasing RESERVE in the general seed, in action
   quanta, whenever a consumer publishes no stock at all**
   (`control_regime_escalation` v7.0.0, `cre_ratchet_channel_reserve`).  This
   is the part that is not optional.  The general seed must not require a plant
   to publish fuel or a thrust ceiling, and absent a measurement it holds a
   finite bound that falls by the measured sample spacing — one action of
   reserve per action of flight — starting from the channel's own declared
   horizon.  Two branches, one law: with a measurement the bound refines by
   MINIMUM, so a plant reporting MORE stock than before never returns an option
   already spent; with no measurement the bound still falls.  **An unmeasured
   tank treated as infinite is an assertion, not a withheld judgement.**  This
   is the frontier's first-class-absence discipline at the opposite corner:
   there the graph stores that the sequence does not end, here that it DOES,
   even when it cannot see where.

#### The rebuilt option clock

`f16_flight_path_control` v8.0.0 (`f16_sample_axis_margins`), in metres of
energy height, every term declared or published:

    mechanical    = h + v^2/2g
    convertible   = fuel_kg * fuel_specific_energy / (m*g)
    rate ceiling  = F_max * v * H * dt / (m*g)            [absent a rating,
                                                           no rate applies]
    reachable     = mechanical + MIN(convertible, rate ceiling)
    escape floor  = (v + dv_eff * H)^2 / 2g
    option margin = reachable - escape floor

and `dv_eff = MIN(maximum_forward_delta_m_s, F_max*dt/m)` — a corner that
declares more speed authority than the engine has is not a cheaper escape, it
is a slower one.  The general seed then takes
`channel_actions_to_option_loss = MIN(trajectory projection, held reserve)`,
so the option expires at the earlier of the escape's own margin reaching its
floor and the stock that funds it running out.

The LEDGER stamped for measurement is `f16_energy_total_m = mechanical +
convertible`, in integer metres.  That is the quantity the prediction is about.

**`speed_priority`'s price is representable and is not asserted.**  No new
clause was needed: `regime_actions_to_act` is the MINIMUM of the transition and
option clocks, the option clock is bounded by the reserve, so an exhausted
reserve puts the acting clock at the lattice floor — and at the floor the
admissible response stops being "restore the basin" and becomes the full corner
set.  The hypothesis is therefore "restore the basin WHILE THE FUEL TO DO IT
EXISTS".  Gated on synthetic streams
(`test_restoring_the_basin_is_admissible_only_while_the_reserve_lasts`).
Nothing here claims the manoeuvre works.

#### FULL DISCLOSURE: this prediction is NOT blind

One of the 24 cells has already been run and read: **nominal, seed 241102975**
— which is scenario index 0, seed 1 of the block below.  What it showed, and
all of it is quoted here because the prediction was written after seeing it:

* Nominal altitude RMSE **323.28346789 ft**, byte-identical to every earlier
  block in this line.  The ledger changes no flight (the gate is off and no
  candidate reads the option clock).
* **Total-ledger increases: 39 of 999 actions, largest +14 m, summing to
  142 m.  Mechanical-column increases: 452 of 999, largest +25 m, summing to
  2,878 m.**  So the two-column ledger is not monotone, but it is ~11.6x less
  non-monotone by count and ~20x by mass.
* The convertible column ran 807,098 -> 793,810 m over the episode; **2.0% of
  the tank burns in 100 s.**  The stock does not bind in this protocol and was
  not expected to.
* The reserve clock is **pinned at 218 actions from action 18 onwards.**  The
  held recursion reads the fuel stream at order 3 and projects ~220 actions to
  dry — badly conservative against the ~12,000 actions the tank actually holds
  — and the ratchet then makes the lowest such reading permanent.  This is the
  ratchet behaving exactly as specified on a crude reading; it is disclosed, not
  fixed, and is named as a residual below.

#### Prediction, committed before block D

1. **The total ledger is non-increasing on at least 95% of actions in every
   one of the 24 episodes, and its residual increases are BOUNDED BY THE
   DECLARED GUST.**  The mechanism claimed: the surviving increases are not
   energy gains at all, they are the true-airspeed term reading a moving air
   mass.  `d(v^2/2g)/dv = v/g ~ 9.3 m per m/s` at the block's initial
   condition, and the declared gust is 2 fps = 0.61 m/s, so one sigma is
   ~5.7 m and three sigma ~17 m.  **Quantitative form: no single-action
   increase exceeds 30 m in any episode.**
2. **The total ledger is CI-cleanly better than the mechanical column on every
   scenario**: per episode, total-ledger increase COUNT is lower than
   mechanical-column increase count, 24 of 24.
3. **Block C's one positive result survives.**  The fraction of post-onset
   actions at which the option clock reads zero is 0.00 on all three nominal
   seeds and non-zero on at least 15 of the 21 fault episodes.  The clock's
   ceiling is now the reserve rather than 1023, so this is stated as "never
   zero in nominal", not "at the horizon".
4. **The reserve does not bind in this protocol.**  100 s burns ~2% of the
   tank on every scenario, so no episode's option clock expires because the
   stock ran out.  The price of `speed_priority` is representable and does not
   bite here, and saying otherwise from this block would be unsupported.

#### What would falsify it

* A single-action total-ledger increase above 30 m — the surviving
  non-monotonicity would then be something other than gust noise on the
  airspeed term, and the accounting would be wrong somewhere else.
* Any episode where the total ledger increases on MORE actions than the
  mechanical column: the second column would be adding non-monotonicity rather
  than removing it.
* The option clock reading zero anywhere in nominal, or at the reserve ceiling
  for every fault: the discrimination block C earned would be gone.
* The total ledger DRIFTING UP over an episode (last > first) in any episode.

#### Named in advance: the most likely falsifier

**`damaged_wing` and `jammed_rudder`.**  Both spend the episode at large
sideslip with the airframe well off its trimmed condition, so the true-airspeed
measurement swings hardest there and prediction 1's 30 m bound is a bound on a
quantity driven by exactly that.  If any episode breaks the bound it will be
one of those two, and the reading will be that the mechanical column's AIRSPEED
term — not the fuel column — is what makes the ledger non-monotone.  A second,
independent candidate: **`saturated_elevator`**, whose sustained descent
converts altitude to airspeed at high rate, which is the trade the ledger is
supposed to be neutral to and is the cleanest test that it actually is.

#### Protocol

Unchanged from blocks A-C: n = 3 seeds x 8 scenarios, 100 s at 10 Hz, frozen
block seeds (base 241102975 + scenario index x 10000 over `SCENARIO_ORDER`),
`--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **class gate OFF** so the
flight is byte-identical to every earlier block and these remain measurements
of INSTRUMENTS, not of outcomes.  Frozen: `control_regime_escalation` v7.0.0,
`f16_flight_path_control` v8.0.0, `cognitive_pareto` v1.1.0,
`embodied_motor_program` v1.8.0.  **Three seeds is not a distribution and no
crash rate is claimed.**

#### Residuals recorded in advance, so they cannot be discovered as findings

* The reserve's ratchet is permanent and its input is crude: an order-3 fit to
  a slowly-draining tank projects ~220 actions to dry against ~12,000 actual,
  and the MINIMUM of such readings binds for the rest of the episode.  It is
  conservative in the right direction and it is not a measurement of endurance.
  Fixing it needs either an evidence guard (a threshold, which this line
  refuses) or an order cap (which it also refuses), so it stands.
* The rate ceiling uses the engine's static rating, not its rating at the
  current mach and altitude, which JSBSim also publishes as a lookup.  The
  static rating is the larger, so the reachable set is over-stated, which is
  the anti-conservative direction and is not defended — it is simply the
  ceiling the engine model declares.
* The response gate has still never flown.

### THE RESPONSE GATE FLIES — prereg (2026-08-06, committed before the gate's first flight)

Four blocks of instrumentation and zero flights.  This rung turns
`regime_class_gate_enabled` on and measures what routing on the acting clock
does to the aircraft.  Nothing below is an outcome claim; the pre-flight is
n=10 and **a pre-flight is not evidence about the distribution** — this line
has been burned by that twice (a 0/10 saturated-elevator pre-flight returned
0.17 at n=100; a 0.20 jam pre-flight returned 0.27 CI-separated worse).

#### What actually changes when the gate is on

Three rules read `regime_class_gate_enabled`, and their firing ORDER is what
decides whether the gate is reachable at all:

| order | rule | condition (gate on) | effect |
|---|---|---|---|
| −49 | `cre_publish_incumbent_stands` | window ran out AND **no goal-revision request** | close, change nothing.  **Does not consult the gate.** |
| −48.9x | `cre_publish_regime_pareto_verdict` | acting clock `<= 0` (full corner set) OR (`0 < t <` H AND `candidate_restores_basin`) | adopt the corner |
| −48.9 | `cre_route_no_projected_transition_to_recalibration` | window ran out AND acting clock `>= H` | `regime_recalibration_requested` → the consumer's `f16_recalibrate_on_no_projected_transition` forces a fresh model pass (`program_mode = recalibration_marking`, trust epoch bumped, default reuse zeroed) |
| −48.85 | `cre_close_gated_deliberation_without_verdict` | window ran out AND acting clock `< H` | mint a `ControlRegimeResidual`, close |

So the gate can only bite in two places: a deliberation where the projection
REFUSES a corner the ungated frontier would have adopted, and a deliberation
that reaches its window with a revision request still standing.  Where no
revision request exists, `cre_publish_incumbent_stands` closes it first and
the gate is unreachable.

#### FULL DISCLOSURE: this prediction is NOT blind

Block D's 24 episodes were re-read before this was written — no new flight,
just the traces that already existed — and every deliberation window in them
was projected through the table above.  All of it is quoted:

* **104 deliberations open across the 24 gate-off episodes.  6 produce a
  verdict; 98 close without one.**
* At the close action of each, the acting clock lands: **60 `<= 0`
  (fixpoint gone → full corner set), 26 `>= H` (recalibrate), 18 strictly
  inside the horizon (only `speed_priority` admissible).**
* **At all 6 of the closes that actually produced a verdict, the acting
  clock reads 0** (jam ×3 at action 189, damaged tail ×1 at 450, damaged
  wing ×2 at 315/353 — every one `T_transition = 0`, with `T_option`
  75–218).  The gate's most permissive region is the one the verdicts sat
  in, so the gate would have admitted every corner the ungated run adopted.
* The MIN is the transition clock almost everywhere: `T_transition` reads
  zero on **0.14–0.98** of post-onset actions in EVERY ONE of the 21 fault
  episodes, against `T_option` at **0.00–0.65**, which is 0.00 throughout in
  15 of 21.  (Corrected after the block ran: these two ranges were first
  written from a window starting at action 200, the reference change, while
  every other "post-onset" figure in this document starts at action 100, the
  fault onset — `scripts/analyse_f16_energy_ledger.py`'s own default.  Same
  fields, same block, one window; the counts and every route figure below are
  unaffected, and the prediction was not restated.)

**That is the block-B falsification arriving one level up.**  The transition
clock is excursion-prone — a healthy commanded manoeuvre drives it to zero —
and `regime_actions_to_act = MIN(T_transition, T_option)` inherits that in
full.  The acting clock is not a compromise between the two clocks; on this
plant it IS the falsified one.

#### Prediction

1. **The gate is INERT on this plant: gate-on metrics are byte-identical to
   gate-off on all 40 matched pre-flight episodes** (4 scenarios × 10 frozen
   seeds), on every reported metric including `recalibration_count`,
   `regime_escalation_action` and the corner-adoption actions.  Mechanism, as
   projected above: the verdict points sit at the lattice floor where the
   full corner set is admissible, and every other window closes on
   `cre_publish_incumbent_stands` before a gate route can fire.
2. **No episode gains a projection-driven recalibration.**
   `recalibration_count` is unchanged in 40 of 40.
3. **Nominal is untouched**: 323.28346789186793 ft on the base seed, zero
   escalations.  (Already run and disclosed — see below.)

This is a prediction that the rung's headline move buys NOTHING, made before
it ran, because that is what the existing traces project.  If it holds, the
finding is not "the gate is bad" but **"the gate cannot be evaluated while
its input is the clock this line already falsified"**, and open item 1 is
superseded by open item 2 rather than answered.

#### What would falsify it

* Any of the 40 matched episode metric sets differing between gate on and
  gate off.
* A recalibration appearing in a gate-on episode and not its gate-off twin.
* A corner adopted under the gate that the ungated twin did not adopt, or
  vice versa.
* Nominal moving off 323.28346789186793 ft on the base seed.

#### Named in advance: the most likely falsifier

**`saturated_elevator` and `shifted_cg`.**  They are the two scenarios whose
deliberation closes land OUTSIDE the "fixpoint gone" region most often in
block D — the elevator 5 of 15 closes at `>= H` and the CG 7 of 16 — so if a
revision request is ever standing at one of those windows, the recalibration
route fires there first.  `saturated_elevator` is also the scenario whose
pre-flight has lied to this line before.  A second, independent candidate:
**`damaged_wing`**, the one powered scenario where `T_option` is non-zero
often enough (0.33–0.57 of post-onset actions) to be the binding clock, which
is the only way a route other than "fixpoint gone" gets selected at a verdict.

#### Already run and disclosed, not blind

One cell: **nominal, seed 241102975, gate ON, 100 s.**  Altitude RMSE
**323.28346789186793 ft**, heading 13.2596741442958 deg, settling 38.8 s,
zero escalations, zero recalibrations — byte-identical to the gate-off pin.
The gate changes nothing in healthy flight on that seed, which is prediction
3 already observed on one of the 40 cells.

#### Protocol

**Matched pair, same frozen seeds, one variable.**  4 scenarios
(`nominal`, `jammed_rudder`, `saturated_elevator`, `damaged_wing`), 10
episodes each, 100 s at 10 Hz, seeds `241102975 + SCENARIO_ORDER.index ×
10000 + episode_index` (so `--base-seed` is offset per scenario and each
scenario runs in its own process, as every earlier block in this line did).
Run twice: `--class-gate` and without it.  No trace (the comparison is on
metrics).  Frozen: `control_regime_escalation` v7.0.0,
`f16_flight_path_control` v8.0.0, `cognitive_pareto` v1.1.0,
`embodied_motor_program` v1.8.0.

**The powered n=100 × 4 block runs only if the pre-flight shows the gate
doing something.**  Spending 4 hours of compute to reproduce a byte-identical
block is the "reached for a better number rather than a better account"
mistake in its purest form.  If the pre-flight is byte-identical, this rung's
result is the projection above plus its confirmation, and the next rung is
the acting clock's input, not its consumer.

### THE RATE CEILING, AND WHAT ACTUALLY COST THE DISCRIMINATION — prereg (2026-08-06, committed before blocks F1 and F2)

Block D left an anti-conservative residual on the record: *"the rate ceiling
uses the engine's static rating rather than its rating at the current mach and
altitude ... the static rating is the larger, so the reachable set is
over-stated — and that is plausibly part of why the option clock became more
permissive."*  This rung fixes it and measures whether the discrimination
block C earned (18 of 21 fault episodes) comes back from block D's 7 of 21.

**It also predicts, before running, that it will NOT come back, and names a
different cause.**

#### What the plant was asked, and what it said

The same discipline block D learned the hard way — ASK THE SIMULATOR — applied
to the ceiling itself.  Measured, not assumed:

* `propulsion/engine/MilThrust` is the engine model's own normalised lookup of
  its `<milthrust>` rating against mach and density altitude.  It reads
  **0.7653** at this block's initial condition, so the static rating
  over-states the ceiling there by **1/0.7653 = 1.31x**.
* The engine model declares `<augmented>1</augmented>` but no `<augthrust>`,
  and JSBSim's augmented turbine puts military power at
  `fcs/throttle-cmd-norm = 0.5` and full afterburner at 1.0.  **The effector
  maps `0.25 * (1 + command)`, so the largest throttle this airframe can be
  commanded is 0.5** — exactly military.  Measured at steady state: 16,253 lbf
  at throttle 0.5 against `rating x lookup` of 16,239 lbf.  The afterburner
  half of the range is not reachable through this interface, so the augmented
  table is not this plant's ceiling and military thrust is the right rating to
  scale.

`domains/jsbsim_f16_paper_world.py` now publishes
`maximum_engine_thrust_newtons = rating x MilThrust_lookup`, per action.  No
seed changes for arm F1.

#### FULL DISCLOSURE: this prediction is NOT blind

The option margin was re-priced OFFLINE on block D's existing traces
(`scripts/reprice_f16_option_margin.py`), under four pricings, counting the
fault episodes with any post-onset action at `option_margin <= 0`.  The
instrument reproduces BOTH published results exactly, which is why it is
trusted enough to predict from:

| pricing | fault episodes with margin <= 0 |
|---|---:|
| block C: mechanical only, declared `dv = 2.0` | **18 of 21** — matches block C's published 18 of 21 |
| block D: two columns, `dv` capped to `F_max*dt/m` | **7 of 21** — matches block D's published 7 of 21 |
| **F1: two columns, condition-rated `F_max`** | **6 of 21** |
| **F2: two columns, condition-rated `F_max`, `dv` UNCAPPED** | **16 of 21** |

It is a proxy and it is stated as one: the stamped clock is an order-N
projection OF this margin's stream, not the margin's sign, and the proxy
disagrees with the stamped clock on one nominal seed (0.42 by proxy against
0.00 stamped).  It over-reports zeros.  That is why F1 and F2 are FLOWN.

#### The mechanism, stated before the runs

`F_max` enters the option margin TWICE, with opposite signs:

    reachable    = mechanical + MIN(convertible, F_max * v * H * dt / (m*g))
    escape floor = (v + MIN(dv_declared, F_max*dt/m) * H)^2 / 2g
    margin       = reachable - escape floor

Lowering `F_max` lowers the reachable set — and lowers the escape floor too,
faster.  At the block's initial condition `d(floor)/dF = 0.0129 m/N` against
`d(reachable)/dF = 0.0076 m/N`, so **cutting the ceiling RAISES the margin**
and makes the option clock MORE permissive, not less.  The residual block D
recorded had the sign backwards.

And that exposes the real defect, which is not the ceiling at all:
**`effective_delta = MIN(declared_delta, F_max*dt/m)` prices a weaker engine as
a CHEAPER escape.**  An aircraft that cannot accelerate reads as having more
options, because the speed it is asked to reach shrinks to whatever it can
manage.  The seed's own comment beside that line says the opposite in words —
*"a corner that declares more speed authority than the engine has is not a
cheaper escape, it is a slower one"* — and the code implements "cheaper".
This is the frontier's original pathology in a new place: there, a surrendered
axis scored flat 0.0 dominated a kept axis scored unbounded-below; here, an
unmeetable demand is scored as a met one.

#### Prediction

**Arm F1 (rate ceiling fixed, nothing else).**

1. **The discrimination does NOT recover**: the option clock reads zero in
   **at most 9 of 21** fault episodes, against block D's 7 and block C's 18.
   Stated as a range because the projection layer is not the margin's sign.
2. **It does not get better than block D**: F1's count is `<=` block D's 7,
   not above it.  The direction is the claim; the exact number is not.
3. **Nominal stays clean**: the option clock reads zero on 0.00 of post-onset
   actions on all three nominal seeds.
4. **The flight is unchanged.**  Nominal altitude RMSE on the base seed is
   323.28346789186793 ft.  The gate is off and no candidate reads the option
   clock, so a repriced ceiling must not move an aircraft.

**Arm F2 (rate ceiling fixed AND the escape floor priced at the DECLARED
delta).**

5. **The discrimination substantially recovers: the option clock reads zero in
   at least 13 of 21 fault episodes**, against block D's 7, while nominal
   stays at 0.00 on all three seeds — i.e. it recovers most of block C's 18
   WITHOUT giving back the clean nominal reading that was block C's one
   earned result.
6. **The flight is still unchanged** (323.28346789186793 ft), for the same
   reason.

#### What would falsify it

* F1 recovering to 13 or more — the ceiling would have been the cause after
  all and the offline instrument would be wrong about the sign.
* F1 or F2 moving nominal off 0.00, or off 323.28346789186793 ft.
* F2 failing to reach 13 — the delta cap would not be the dominant cause
  either, and the block-C-to-block-D loss would be unexplained by both
  candidates.
* F2 recovering all the way to 18 of 21 AND losing the clean nominal — that
  would be block C reproduced rather than repaired, and the two-column ledger
  would have bought nothing.

#### Named in advance: the most likely falsifiers

**`saturated_elevator` and `damaged_wing`.**  They are the two scenarios where
the proxy already reads a large at-zero fraction under block D's own pricing
(0.83 and 0.34–0.81), so they are the episodes with the least headroom between
the two arms and the most room for the projection layer to disagree with the
margin's sign.  `shifted_cg` seed 3 is the single most likely individual cell
to flip: its proxy reads 0.12 under D and 1.00 under F2, the largest swing in
the block.

Second, independent: **`landing_gear`**, whose proxy is 0.00 in two of three
seeds under every pricing and 1.00 in the third.  If a scenario is bimodal
across seeds at n=3, the count it contributes is a coin toss and both arms'
totals inherit that noise.  **Three seeds is not a distribution** and no crash
rate is claimed from either arm.

#### Protocol

Unchanged from blocks A–D: n = 3 seeds x 8 scenarios, 100 s at 10 Hz, frozen
block seeds (base 241102975 + scenario index x 10000 over `SCENARIO_ORDER`),
`--include-trace`, `GAMMA_REGIME_DIAGNOSTICS=1`, **class gate OFF** so both
arms remain measurements of INSTRUMENTS and the flight stays byte-identical to
every earlier block.  F1 changes only `domains/jsbsim_f16_paper_world.py`; F2
additionally bumps `f16_flight_path_control` to v8.1.0 for the escape-floor
pricing, with its pin updated in
`tests/test_jsbsim_f16_paper_replication_migrated.py`.  Analysis:
`scripts/analyse_f16_energy_ledger.py`.

**Neither arm is an adoption.**  F2 is a candidate repair being MEASURED; if it
recovers the discrimination that is evidence about an instrument, not about
whether routing on it helps an aircraft, and the gate has still never usefully
flown (block E).

### THE EQUAL RATING IS OVER CHANNELS — prereg (2026-08-06, committed before blocks G0 and G1)

Block E measured the response gate to be inert: at all six deliberation closes
that adopted a corner the acting clock read 0, which is the gate's most
PERMISSIVE region (fixpoint gone → the full corner set).  Blocks F1/F2 showed
that a strictly better option clock does not change that.  This rung changes
what the acting clock is made of.

#### The defect, measured

`regime_actions_to_transition` was `MIN` over the per-channel transition
clocks — a flat minimum, which prices every declared objective identically.
Which channel actually wins it (F2's traces, post-onset):

| scenario | argmin channel | `T_transition == 0` |
|---|---|---:|
| nominal | altitude .66, sideslip .27 | 0.11 |
| jammed_rudder | **heading .83** | 0.89 |
| broken_aileron | **sideslip .68** | 0.43 |
| damaged_tail | **sideslip .56** | 0.53 |
| damaged_wing | **attitude .50** | 0.86 |

and on the base seed through the commanded 40 degree reference change — the
event the two-clock block was falsified on — the argmin flips to **sideslip
(163 of 200 actions)** and `T_transition` reads zero on **83 of 200**, against
0 of 100 before it and 0 of 600 after it settles.  **A coordinated turn IS
transient sideslip.**  At the six closes that adopted a corner the argmin is
`heading` ×4 and `attitude` ×2 — altitude at none of them.

That is derivation step 10 unapplied one level down: altitude liquidates the
reserve every future decision draws on; heading is not energy at all.  The flat
minimum let the cheap objective speak with the expensive one's authority.  It
also explains the one clock that works: the option clock is a SINGLE channel,
the funding one, so it was never equal-rated.

#### The contract

`control_regime_escalation` **v7.1.0**.  A channel declares
`channel_surrender_discount` in [0, 1] — how much of its own loss is ALREADY
PAID FOR in another channel's ledger — and the transition roll-up becomes

    weighted(channel) = clock + discount * (horizon - clock)
    T_transition      = MIN over channels of weighted(channel)

minted back onto the integer lattice (the clocks are in-frame integers, the
discount is a cross-frame ratio).  **`P0` reads an absent attribute as zero and
zero is "priced in full", so a consumer that declares nothing gets the flat MIN
byte-identically** — gated by
`test_a_channel_that_declares_no_discount_is_priced_in_full`.  The OPTION
roll-up is left flat, deliberately: its channels declare an expiry only where
they fund an escape, so its minimum is already over the channels that have a
price.

`f16_flight_path_control` **v8.2.0** declares altitude 0.0 (priced in full — it
carries the ledger the option clock is projected from) and attitude, heading,
sideslip 1.0.  **The discount is not "this objective does not matter."** It is
that sideslip's drag and an attitude excursion's energy both come off the
mechanical column the altitude channel already reads, and counting them again
in the roll-up lets one spend force action twice; heading costs no energy at
all.  A genuine departure is `f16_departure_pitch_priority_override`'s job, not
the regime clock's.

#### FULL DISCLOSURE: this prediction is NOT blind

`scripts/project_f16_channel_weighting.py` was run on F2's traces before any of
this was built, and all of it is quoted:

| price vector | 104 closes: gone / inside / recal | the 6 ADOPTING closes | nominal `T_trans==0` |
|---|---|---|---:|
| V0 flat (control) | 64 / 15 / 25 | **6 gone** | 290/2703 (0.11) |
| V1 energy-only (what ships) | 32 / 27 / 45 | **1 gone, 3 inside, 2 recal** | **0/2703 (0.00)** |
| V2, V3 graded | identical regions to V1 | identical | 0.00 |

Acting clock at each adopting close under V1: **218, 218, 76, 77, 75, 0** —
every one of them the OPTION clock.  The weighting does not blend the clocks;
it takes the transition clock out of contention and lets the single-channel
energy clock set the time.  The sixth close stays at `fixpoint_gone` because
`T_option` itself reads 0 there (damaged_wing seed 3).

The projector is exact only up to the first action at which a different acting
clock changes a verdict.  It also found its own bug and the V0 control is why:
the stamped `regime_actions_to_transition` at action k is the MIN over the
consumer's channels at action **k−1** (23,976 of 23,976 rows, against 16,592
same-action), so recomputing from the current row shifts every close by one.

#### Prediction

**Block G0 — gate OFF, n=3 × 8, the block-D protocol.**

1. **Byte-identical to block F2 on all 24 episodes**, every non-latency metric,
   nominal base seed **323.28346789186793 ft**.  With the gate off nothing
   reads `regime_actions_to_act`, so a changed acting clock must not move an
   aircraft.  If it does, the clock has a consumer nobody has accounted for and
   every "measurement of an instrument" claim in blocks A–F is weakened.
2. **`regime_actions_to_transition` reads the horizon on ≥ 0.99 of nominal
   post-onset actions**, against the flat MIN's 0.89.  The manoeuvre excursion
   is gone.
3. **The six adopting closes land 1 `fixpoint_gone` / 3 `inside_horizon` /
   2 `recalibrate`**, reproducing the projection exactly, since G0's
   trajectories are F2's.

**Block G1 — the matched gate ON/OFF pre-flight, 4 scenarios × 10 frozen
seeds**, the block-E protocol.

4. **THE ARMS DIVERGE.  At least 8 of the 40 matched episodes differ on a
   non-latency metric.**  This is the claim block E could not make.  Sizing: 17
   of the 40 gate-off episodes adopt a corner (jam 8/10, wing 9/10) and the
   projection moves ~5 of every 6 adopting closes out of the permissive region.
5. **Nominal is untouched**: 10/10 identical in both arms,
   **323.28346789186793 ft** on the base seed.  Healthy flight never escalates,
   so the gate cannot bite there whatever the clock says.
6. **`speed_priority` is adopted in at least 1 of the 40 gate-ON episodes** —
   the first time in this line, against 0 in 40 under block E's gate and 0 in
   both arms of every block since.  This is the direct test of open item 4 and
   it is the RISKIEST prediction here.

**NOT predicted: the direction on crash rate.**  Ten seeds is not a
distribution, this line has been burned twice by reading one as if it were
(a 0/10 elevator pre-flight returned 0.17 at n=100; a 0.20 jam pre-flight
returned 0.27 CI-separated worse), and there is a real mechanism pointing each
way — refusing the altitude-surrendering corners should help (block 3: episodes
ending on a corner that KEPT altitude crash at 1/61, and 26 of 27 crashes end
on one that surrendered it), while refusing ORBIT is refusing the corner v3's
0.04 jam rate was built on.  **No crash rate is claimed from G1 and no powered
block is authorised by it.**

#### What would falsify it

* G0 differing from F2 on any non-latency metric.
* G1's arms identical again, or fewer than 8 of 40 diverging — the weighting
  would not have reached the gate and the projection would be wrong.
* Nominal moving off 323.28346789186793 ft in any arm.
* `speed_priority` adopted 0 times in 40 gate-on episodes while the arms still
  diverge — the `inside_horizon` region would be admitting only a corner that
  is never on the frontier, so the gate would be converting adoptions into
  refusals rather than into the operating-condition change it is for.  That is
  a DIFFERENT result from prediction 4 failing and is recorded separately.

#### Named in advance: the most likely falsifiers

**`saturated_elevator`.**  It escalates 0 of 10 times under the gate-off arm,
so it can contribute NOTHING to prediction 4's divergence count and drags it
toward the floor — 30 of the 40 episodes carry the whole prediction.  It is
also the scenario whose pre-flight has misled this line before.

**Prediction 6 is the one most likely to fail**, and its named mechanism is
dominance rather than the gate: `speed_priority` has been adopted 0 times in
every block measured here, and in block 3 it was adopted 16/100 in the elevator
and crashed when it fired.  If it is dominated on the frontier at the three
`inside_horizon` closes, the deliberation closes with a
`ControlRegimeResidual` and no adoption — prediction 4 holds, 6 fails, and the
reading is that the gate can refuse but the consumer has nothing to offer in
the region where refusal bites.

Second, independent: **`damaged_wing`**, whose sixth close stays in
`fixpoint_gone` on `T_option`'s own zero.  If more of its closes do that at
n=10 than the n=3 projection suggests, the divergence count falls.

#### Protocol

G0: n = 3 × 8, 100 s at 10 Hz, frozen block seeds, `--include-trace`,
`GAMMA_REGIME_DIAGNOSTICS=1`, gate OFF.  G1: 4 scenarios
(`nominal`, `jammed_rudder`, `saturated_elevator`, `damaged_wing`) × 10 frozen
seeds, run twice with and without `--class-gate`, no trace, compared per
episode on seed by `scripts/analyse_f16_gate_ab.py`.  Frozen:
`control_regime_escalation` v7.1.0, `f16_flight_path_control` v8.2.0,
`cognitive_pareto` v1.1.0, `embodied_motor_program` v1.8.0.

**Ten seeds is not a distribution.**  G1 answers "does the gate now do
anything, and what", not "is it better".

### WHAT A CORNER COSTS — prereg (2026-08-06, committed before block H)

Block 1 added two corners with no price attached and they were CI-separated
worse on all three faults.  The derivation's item 2 says why: a surrendered
axis scored flat 0.0 against a kept axis scored unbounded-below, so the corner
that gives up the MOST dominated the one that gives up the RIGHT thing.  Three
repricings failed because each priced a STATE comparison.

What exists now and did not then is a STOCK-AND-FLOW price: the two-column
ledger (`f16_energy_total_m`, monotone non-increasing across 24 episodes x 999
transitions), the option margin, and a finite reserve.  **A corner's cost is
its draw on that ledger**, in metres of energy height, and every corner is
priced in the same currency.

There is already indirect evidence, from a POWERED block, that the price
predicts outcomes: block 3's crash-by-corner table — episodes ending on a
corner that KEPT altitude crash at 1/61, while 26 of 27 crashes end on a corner
that SURRENDERED it.  Altitude is the ledger.  That is the cost model
retro-predicting survival at n=100, and it was not read as one at the time.
But block 3 ran `f16_flight_path_control` v3.1.0 and **the ledger did not exist
yet**, so the draw was never measured — only its altitude proxy.

#### Prediction, committed before block H is looked at

Block H: 4 scenarios x 25 frozen seeds, gate OFF, `--include-trace`, current
stack.  Not a protocol this line has run before (n=25 rather than 10 or 100);
it is sized for ADOPTIONS, not for a rate — n=10 yields ~17 adoptions and n=25
should yield ~40.  **No crash rate is claimed and no Wilson interval will be
computed from it.**

1. **The ledger draw after adoption separates outcome.**  Among episodes that
   adopt a corner, the mean per-action draw on `f16_energy_total_m` over the
   actions AFTER adoption is higher in the episodes that crash than in those
   that do not, and the two distributions do not merely overlap in mean — the
   crashing episodes' median draw exceeds the surviving episodes' median.
2. **The draw is a better separator than the adoption ACTION.**  Adoption
   timing alone (early vs late) does not separate crash from survival as
   cleanly as the draw does, measured as the gap between group medians relative
   to within-group spread.  If timing separates equally well, the ledger adds
   nothing over "it escalated early", which G1 already showed moves outcomes.
3. **The surviving reserve at adoption is LOWER in the episodes that crash.**
   `regime_reserve_actions` at the adoption action, which is the stock the
   escape draws on.

#### What would falsify it

* The crashing and surviving episodes' post-adoption draw distributions having
  the same or inverted median ordering.
* Adoption timing separating outcome at least as well as the draw — the
  ledger would be redundant with something already measured.
* Fewer than 20 adoptions in the block, in which case NOTHING is concluded and
  the block is reported as underpowered rather than squinted at.

#### Named in advance: the most likely falsifier

**`damaged_wing`.**  It adopts in 9 of 10 episodes and crashes in 5 of 10, so
it dominates both groups and its within-scenario variation will drive the
medians; if the draw separates outcome only because scenarios differ in both
draw and crash rate, that is a scenario confound and not a cost model.  **The
guard against it is stated in advance: the comparison must hold WITHIN
`damaged_wing` alone, not only pooled.**  If it holds only pooled, the finding
is a scenario effect and is reported as one.

Second: **`jammed_rudder`** under the current stack crashes 0 of 10 with the
gate off in G1's own arm, so it may contribute adoptions to only one group.

### PRICING THE SURRENDERED AXIS WITH THE LEDGER — prereg (2026-08-06, committed before block J)

The frontier collapsed to ordinal 2 because a surrendered achievability-only
axis scored **the horizon — the maximum of the range** — so retiring heading
was not merely free but maximally rewarded, and orbit (retire heading, keep
altitude) dominated every other candidate by construction.

`f16_flight_path_control` **v8.3.0** prices a surrendered achievability-only
axis at `f16_actions_to_option_loss` — the actions the LEDGER still funds —
instead of the horizon.  An abandoned objective still cannot expire; what can
expire is the ability to go on flying the corner that abandoned it, and that is
funded from mechanical + convertible energy bounded by the reserve.  Both kinds
of axis are then priced in one currency, which is the point: they stop being
incomparable.

#### This is a DISCRIMINATING experiment, and the prediction is that it FAILS

Two hypotheses have been on the table for why the deliberation layer is a
constant function:

* **(A) the scoring** — surrender priced at the end of the range rather than
  inside it;
* **(B) the option set** — corners that do not change with the model, among
  which one is dominant in every condition.

Pricing by the ledger tests (A) alone, and **the prediction is that (A) is not
sufficient**, worked through on the deciding deliberation already dumped
(damaged_wing seed 241172975, action 315, where `f16_actions_to_option_loss`
reads 75):

| corner | alt | head | under v8.3.0 |
|---|---:|---:|---|
| fixed_point | 1024 | 1 (kept, unachievable) | dominated by orbit |
| trim | 1024 | 1 | dominated (also loses sideslip 1024 → 75) |
| **orbit** | 1024 | **75** (was 1024) | **still dominates all four** |
| speed_priority | 460 | 1 | dominated |
| roll_priority | 460 | 75 | dominated on altitude |

The asymmetry that actually decides is not ceiling-versus-real.  It is that a
KEPT objective which has become unachievable scores its FLOOR (1), so
surrendering it wins on that axis at any price above 1.  Orbit surrenders
exactly the axis that has gone unachievable and nothing else, so it wins
whatever the surrendered price is — until the ledger falls below the kept
clock.

**Prediction, committed before block J** (4 scenarios x 25 frozen seeds, gate
OFF, `--include-trace`, the block-H protocol so it is directly comparable):

1. **The collapse is REDUCED but NOT ELIMINATED.**  Ordinal 2 remains the
   modal adopted regime, on more than half of all adoptions.
2. **But the frontier stops being a constant function**: at least one
   deliberation in the block reaches a verdict other than ordinal 2, OR at
   least one adoption that block H made does not happen.  Block H's count was
   48 adoptions, 48 of them ordinal 2, 0 of anything else.
3. **The change bites where the ledger is tight.**  Any deliberation whose
   verdict differs from block H's has `f16_actions_to_option_loss` below the
   kept clock of the axis the winning corner surrenders.
4. **Nominal is untouched**: 323.28346789186793 ft on the base seed, 0
   escalations, because healthy flight never opens a deliberation that reaches
   a verdict.

#### What would falsify it

* **Ordinal 2 winning 100% of adoptions again, with the same count as block H
  (48).**  Then the ledger price changed nothing at all, hypothesis (A) is
  dead outright rather than merely insufficient, and the whole cause is (B).
* Ordinal 2 falling BELOW half of adoptions — the scoring would have been more
  of the cause than predicted, and prediction 1 is wrong.
* Nominal moving off the pin — the pricing would have reached healthy flight,
  which it must not.

#### Named in advance: the most likely falsifier

**The first falsifier is the likely one** — that nothing changes at all.
`f16_actions_to_option_loss` reads at or near its ceiling on most post-onset
actions in most scenarios (block D measured the option clock non-zero in only 7
of 21 fault episodes, and F2's repair took it to 15 of 21 but still 0.00 for
long stretches), so on most deliberations the surrendered price will be large
and the ordering will be exactly as before.  **`saturated_elevator` is the most
likely single scenario to show a change**, since its option clock reads zero on
the largest fraction of post-onset actions (0.46-0.68 under F2) — but it
adopted only 2 of block H's 48, so it can move very little of the total.

**Either outcome is informative and neither is a rescue.**  If the collapse
survives, that is positive evidence for the option-set hypothesis, which is the
one the project owner named first.

### CONTAINMENT AS THE DELIBERATION TRIGGER — prereg (committed before block M)

`control_regime_escalation` v7.2.0 adds `cre_open_on_goal_outside_manifold`:
a deliberation opens when the consumer publishes
`regime_goal_outside_manifold`.  ADDITIVE — the evidence-absence trigger is
untouched, so any change is attributable to this alone.
`f16_flight_path_control` v8.27.0 publishes it when any declared objective's
gap exceeds its reach, guarded on `calibration_complete` because an unlearned
map has zero reach and would fire on every action of every episode (caught by
two gate tests, not by inspection).

#### FULL DISCLOSURE: not blind

The containment margins were measured before this was wired
(`docs/decision_making_spike.md` §43).  Post-onset fraction of actions with the
want outside reach: **nominal altitude 0.12**, heading 0.00, speed 0.00;
jam 0.82/0.38/0.84; elevator 0.91/0.09/0.86; wing 0.90/0.52/0.00.

#### Prediction

1. **NOMINAL WILL NOW ESCALATE, and this is a REGRESSION.**  Nominal reads
   altitude outside on 0.12 of post-onset actions, so the trigger fires in
   healthy flight and breaks `0/100 nominal escalations` — the invariant this
   line has guarded since the v3.0.0 regression (88/100 healthy escalations,
   altitude RMSE 378 → 778 ft).  I expect nominal escalation in the majority of
   episodes and nominal altitude RMSE to rise above 323.28346789186793 ft.
2. **Faults will escalate far earlier and far more often** — containment fails
   on 0.82-0.91 of post-onset actions against an absence integral that
   currently yields ~2 deliberations per episode.
3. **Outcomes are NOT predicted.**  Ten episodes is not a distribution.

#### What would falsify it

* Nominal not escalating at all — the 0.12 would have to be transient enough
  that the request is always closed before it fires.
* Nominal escalating but altitude RMSE staying on the pin.

#### The point of running a prediction of failure

Containment is the RIGHT condition (a corner surrenders an objective; the
reason to surrender one is that it cannot be had) and an INSTANTANEOUS reading
of it is the wrong trigger.  The evidence path has an urgency-weighted integral
precisely so a transient does not open a deliberation.  If this fires in
nominal, the finding is that containment must feed that integral rather than
bypass it — which is a smaller and better-founded change than either.

## Block R — the allocation flies (f16 v8.35.0)

`f16_reallocate_objective_weights` multiplies each contained axis's policy
objective weight by its containment share `min(margin, 1)`, rescaled to
preserve the summed weight of the three:

    w_i = b_i * s_i * (sum_j b_j) / (sum_j b_j * s_j)

for (altitude→vertical_weight, heading→turn_weight, speed→forward_weight).
This is the first time an allocation reaches the aircraft rather than only the
frontier score. Base weights are captured once (`f16_capture_base_objective_weights`)
so the rule is idempotent; it is scoped to the held ordinal so it can never
fight `f16_adopt_thrust_basis_regime`'s own `forward_weight` override.

**PREDICTIONS, recorded before the run:**

1. **Nominal pin UNCHANGED at `323.28346789186793`.** If every objective is
   contained, all shares are 1.0, the normaliser is exactly 1.0, and the
   weights are byte-identically the base. The rule is self-gating by
   construction — no trigger decides when it applies. A moved nominal pin
   therefore does NOT falsify the arithmetic; it falsifies the assumption that
   nominal is fully contained, which is worth knowing either way.
2. **Faulted scenarios move.** damaged_wing runs with altitude margin 0.005–0.17
   for most of the episode (§50), so its vertical weight should fall hard and
   turn/forward should absorb it.
3. **Direction is NOT preregistered.** Reallocating away from an unreachable
   objective could help (authority spent where it buys something) or hurt
   (altitude RMSE is the scored metric, and this deliberately stops chasing
   altitude when altitude is unreachable). The honest prediction is that
   altitude RMSE gets WORSE where altitude was already unrecoverable and the
   other axes improve — i.e. the metric may punish the correct behaviour.
   Record both; do not adopt on the altitude number alone.
4. **No crash-rate regression.** Any increase in crash rate falsifies the build
   outright, regardless of tracking numbers.

## Block T — reduce the DEMAND, not the weight (f16 v8.36.0)

Block R's correction, built where R should have acted. When the altitude
demand exceeds what the airframe can reach in its own projection window, the
outer loop asks for what is REACHABLE and keeps **full** authority on getting
there:

    demanded_altitude_error = clamp(altitude_error, -reach, +reach)

in `derive_flight_path_control_targets_rule`, feeding `desired_vertical_speed`
and so the pitch chain. Two invariants hold it honest:

- The PUBLISHED `flight_path_altitude_error_m` stays **raw**. Clamping it would
  feed the clamp back into the containment measurement that produced the reach,
  and the margin would read 1.0 forever.
- **Absent reach means no clamp**, not a zero demand, so a consumer that
  declares no manifold is byte-identical. `seeds/embodied_motor_program.json`
  regenerates byte-identical, confirming no other domain is touched; exactly
  two f16 rules change.

**PREDICTIONS, recorded before the run:**

1. **Nominal pin unchanged at `323.28346789186793`.** Block R established that
   every nominal margin exceeds 1, i.e. reach > |error| throughout, so the
   clamp is inert. Self-gating again, by the same arithmetic — no trigger.
2. **No crash-rate regression on damaged_wing** (baseline 0.0, measured at
   v8.34.0). Same decisive falsifier as block R. This is the prediction the
   build exists to satisfy: R crashed by removing authority, T removes only
   the impossible part of the demand.
3. **Minimum altitude improves or holds** on damaged_wing (baseline +2.87 ft).
   The aircraft should stop commanding a pitch attitude it cannot sustain in
   pursuit of an altitude it cannot reach.
4. **Altitude RMSE direction NOT preregistered.** Aiming at a reachable
   altitude rather than the reference can raise the RMSE against that
   reference while flying better. Do not adopt or reject on that number.

## Block U — fix the instrument (f16 v8.37.0)

Block T finding 2: the altitude and heading reaches were spec constants, so
`f16_goal_margin_*` restated the error rather than measuring the plant. The
reach now stays anchored to the DECLARED envelope and is SCALED by measured
authority — `max` over effector models of `f16_authority_shrunk`, which shrinks
toward 1.0 as evidence thins, so **no evidence reads full authority**.

Sourcing the reach directly from `mean_vertical` was measured and rejected
first: in nominal it is 0.0000 on nearly every model (a trimmed aircraft
produces no vertical excursion to observe) versus 2–3.7 under a damaged wing.
It records what happened, not what the effector can do.

**PREDICTIONS, recorded before the run:**

1. **PRIMARY — the instrument discriminates.** `f16_manifold_reach_altitude`
   must separate the plants: baseline was 1 distinct value in nominal and 44
   spanning 7.7% in damaged_wing. Under the fix, damaged_wing's reach must fall
   well below nominal's 160.0 m. `log_authority` is 0.00 in nominal and −1.10 /
   −0.79 under damage, so the expected factor is ~0.45 → reach ~72 m. **If
   damaged_wing's reach stays within 10% of nominal's, the fix has failed and
   this is falsified regardless of any tracking number.**
2. **Nominal pin EXACT at `323.28346789186793`** — *conditional on the factor
   being exactly 1.0*, i.e. nominal producing zero failure evidence. **The
   factor will be read directly and reported, not inferred from the pin.**
   Block R claimed a confirmed mechanism it had not verified; that is not
   repeated here. A nominal factor below 1.0 means the pin moves and the
   prediction is falsified, not reinterpreted.
3. **No crash-rate regression on damaged_wing** (baseline 0.0). Same decisive
   falsifier as R and T.
4. **Faulted flight MAY change** — the altitude clocks feed four mint rules, so
   candidate scores move. Direction not preregistered. This is an instrument
   fix and is to be judged on prediction 1, not on RMSE.

## Block X — wire the stop to the calibration pass (f16 v8.46.0)

`f16_stop_probe_on_quorum` clears `recalibration_required` once quorum holds,
emptying the general seed's `calibration_frontier`, whose exhaustion is already
the pass's own exit to `synthesis`. The stop is expressed in the existing
lifecycle rather than by reaching into the general seed.

**PREDICTIONS, recorded before the run:**

1. **nominal byte-identical** — quorum is false (nothing to explain), so the
   rule cannot fire. Self-gating.
2. **damaged_wing byte-identical** — quorum is false (every effector answers;
   the plant moved and no effector-level explanation exists), so the rule
   cannot fire. **This is the sharp one:** a fault scenario that must come back
   EXACTLY unchanged, because the instrument correctly finds no dead effector.
3. **jammed_rudder changes** — the only scenario with a genuinely dead
   effector. Calibration actions should fall and control actions rise.
   Direction of the tracking metric NOT preregistered.
4. **No crash-rate regression on jammed_rudder** (baseline 0.0). Decisive
   falsifier, as in blocks R, T and U.

### Block X2 — hysteresis on the stop (f16 v8.47.0)

Block X fired on a transient and crashed a healthy aircraft. The stop now reads
how long quorum has HELD (`f16_probe_quorum_actions`, reset the moment it stops
holding) and activates only past the loop's own `regime_evidence_horizon_actions`.
A separate `f16_release_probe_stop` clears the flag on a single action of the
condition not holding — deliberately asymmetric activation and deactivation
energy, because nothing is permanent: a jammed effector can free itself and an
airframe gets repaired.

Measured basis: quorum holds for **1 action** at most under a damaged wing (2
blips in 1000) and **882 contiguous** under a jammed rudder.

**PREDICTIONS:**

1. **nominal byte-identical** (quorum never holds).
2. **damaged_wing byte-identical to the v8.45.0 baseline** — the transient is
   1 action, far below the horizon, so the stop must not fire. This is the
   prediction block X failed.
3. **jammed_rudder keeps block X's improvement** — quorum holds 882 actions, so
   the stop still fires, only later by the horizon.
4. **No crash regression anywhere.** damaged_wing must return to crash 0.0.

## Block Z — containment SELECTS (f16 v8.50.0)

Block Y's defect: `fixed_point` surrenders nothing, so after v8.3.0 it scores
≥ every corner on every axis and dominance can never elect a trade. Block S
proved a uniform rescale cannot change membership. This is the non-uniform
rule: **an axis a corner KEEPS, on an objective containment reports outside
reach, contributes nothing** — only the kept portion is zeroed, the surrendered
portion is untouched.

**PREDICTIONS:**

1. **nominal byte-identical** — nothing is ever outside reach, so nothing is
   zeroed. Self-gating, no trigger.
2. **damaged_wing: the regime ESCALATES.** `final_regime_ordinal` must leave
   0.0 and `regime_escalation_action` must stop being None on at least one
   episode. This is the direct test: corners that keep an unreachable altitude
   lose it, corners that surrender it do not, so a trade can win for the first
   time. **If the ordinal stays 0.0 the build has failed**, whatever the
   tracking numbers do.
3. **No crash regression anywhere**, and specifically jammed_rudder must not
   lose block X's result (803.44 mean, 0.00 crash). It is the standing risk:
   the jam now flies well and this changes what its frontier may elect.
4. **Tracking direction NOT preregistered.** Escalating into a compensating
   regime under a departure may cost altitude RMSE while saving the aircraft.
   Judge on prediction 2 and the crash/structural guards, not on RMSE.

## Block Y2 — un-discount the attitude channel (f16 v8.51.0)

The loop measures `f16_actions_to_transition_attitude` = 96 → 60 → 9 → 4 → 0 as
the damaged wing rolls it inverted, and reports `regime_actions_to_transition`
= 1023 throughout, because v8.2.0 gave attitude `channel_surrender_discount`
1.0 — replacing its clock with the horizon before the MIN over channels. It
measured an 8-action deadline and planned to act in 75.

Attitude is a TERMINAL channel: heading and sideslip are objectives that can be
abandoned, attitude is not. Discount set to 0.0, joining altitude.

**PREDICTIONS:**

1. **damaged_wing acts in time.** `regime_actions_to_transition` must fall to
   attitude's clock during the departure, and escalation must occur before the
   roll passes 90° (actions 139/142/147), instead of at 317 / never.
2. **The target is 0 crashes on damaged_wing**, not fewer. The reference
   controller in the paper achieves crash_rate 0.0 on this scenario, so zero is
   attainable and is the bar.
3. **nominal must not regress.** Attitude reads urgent on ~1% of nominal
   actions, so some extra deliberation is expected; crash must stay 0/3 and
   altitude RMSE must not materially worsen. This is the cost the v8.2.0
   discount was introduced to avoid, now paid deliberately.
4. **No crash regression on any other scenario.**

## Block AA — you cannot wait longer than you have (cre v7.2.0)

Measured: deliberation opens 8 times in 1000 actions, profile mints coincide
exactly, and the single ordinal change is the action after the second opening.
The frontier is evaluated ONCE per opening. Under a damaged wing it opened at
128 — altitude still reachable, so the incumbent dominated and the verdict was
HOLD — and could not reconsider until 316, because the opening guard is
`absence_integral > evidence_horizon` and the horizon is 80 actions. The
aircraft inverted at 147.

The guard now waits the SHORTER of the evidence horizon and
`regime_actions_to_act`, the loop's own projection of actions remaining. Absent
or zero projection falls back to the horizon.

**PREDICTIONS:**

1. **damaged_wing re-decides in time.** A deliberation must open between
   action 129 (escalation requested, 9 actions of margin) and 147 (inversion),
   instead of the next opening being 316.
2. **The target is 0 crashes on damaged_wing**, the bar the paper's reference
   controller meets.
3. **nominal and jammed_rudder must not regress.** Both currently sit at
   323.28346789186793 and 323.10483819184157 with 0 crashes. `actions_to_act`
   is 75 in healthy flight against a horizon of 80, so a modest increase in
   deliberation frequency is expected there — this is the cost, and crash must
   stay 0.
4. **Watch for deliberation churn**, the failure mode already diagnosed in this
   line: if openings become very frequent, the loop re-decides faster than
   evidence arrives and the verdict oscillates.

## Block AB — abandon a stale deliberation (cre v7.3.0)

`cre_abandon_stale_deliberation` closes an open deliberation once
`regime_deliberation_integral > regime_actions_to_act` — you cannot spend
longer deciding than you have left — so a fresh one can open against current
evidence. A zero or absent projection cannot trigger it.

**PREDICTIONS, including a deliberate NEGATIVE one:**

1. **damaged_wing re-decides before inversion.** At action 129 the integral is
   2 against 8 actions remaining; by ~135 it is 8 against 7. A fresh
   deliberation must open between roughly 135 and 147.
2. **AND IT WILL STILL CHOOSE HOLD, AND STILL CRASH.** This is the prediction
   worth making, because it tests the model rather than the build. At 135
   `f16_goal_outside_altitude` is still 0 — it does not turn on until 171 — so
   the incumbent is not penalised, and **no corner differentiates on attitude**,
   the axis actually being lost (every corner keeps it, so its value is
   identical across the frontier and cannot discriminate). Re-evaluating at the
   right moment cannot help when the criterion cannot see the failure.
   **If this holds, it establishes that attitude must enter the selection
   criterion, and that no amount of timing work will substitute.**
   If it fails and the aircraft recovers, my model of the selection path is
   wrong and that is more valuable still.
3. **nominal and jammed_rudder must not regress** from
   `323.28346789186793` / `323.10483819184157`, 0 crashes.
4. **Watch for churn**: abandoning and re-opening every action would be the
   failure mode. `regime_deliberation_stale_count` is stamped to measure it.

## Block AE — the allocation is a budget (f16 v8.55.0)

Shares are normalised by their declared total, so authority given to one
objective is not available to another. `fixed_point` commits 1/6 to each of six
objectives; `roll_priority`, having surrendered altitude and heading, commits
1/4 to each of four — a longer assisted attitude clock than the corner that
kept everything. This is the first time a corner's surrender changes what it
gets on the objectives it keeps.

**PREDICTIONS:**

1. **damaged_wing elects a compensating corner BEFORE inversion (action 147).**
   The attitude streams diverge 4×–128× there, so the budget difference (1/4
   against 1/6) is now a real difference on the axis being lost. Previously the
   first non-HOLD verdict was 249. **If the ordinal still does not change before
   147, the corner library — not the representation — is the blocker.**
2. **nominal WILL change**, and this is the honest cost: altitude's kept and
   surrendered streams differ in healthy flight, so every corner's altitude
   value moves. Crash must stay 0/3 and RMSE must not materially worsen.
3. **jammed_rudder must not lose block X's result** (323.10, 0 crashes).
4. **Target remains 0 crashes on damaged_wing.**

## Block AF — the tie-break is the shortest clock (f16 v8.57.0)

`f16_choose_regime_situational_priority` chose the priority axis from two
constants and a default (terrain < 500 m, airspeed < 70 m/s, else heading). It
now chooses the axis with the SHORTEST published clock among altitude, heading
and attitude. Both constants were proxies for urgency the loop already measures
directly; a short altitude clock IS terrain proximity, and no altitude or
airspeed threshold can ever notice an attitude clock of 1 at 19,000 ft.

**PREDICTIONS:**

1. **damaged_wing selects a compensating corner before inversion (147).** The
   attitude clock reads 61 / 24 / 8 across actions 123–141 while altitude reads
   1024 and heading 683+, so the priority becomes attitude, and on attitude
   `roll_priority` beats `fixed_point` (1/4 against 1/6 of the assisted clock).
   The ordinal must change before 147, against 249 today.
2. **Target 0 crashes on damaged_wing.** Everything upstream is now measured
   and correct; if the aircraft still departs with the right corner adopted
   before inversion, the corner itself is insufficient and the library is the
   answer.
3. **nominal must not regress.** Its clocks are long, so the priority may move
   off heading; crash must stay 0 and RMSE must not materially worsen.
4. **jammed_rudder must not lose block X's result** (323.10, 0 crashes).

## Block AG — admissibility stated directly (f16 v8.58.0)

`f16_admit_roll_priority_on_attitude_loss` says the sentence the whole scoring
chain was trying to encode: **attitude is the shortest clock, and the assisted
projection exceeds the raw one, so fly the corner that spends authority on it.**
Two clauses, both measurements, no thresholds, no scores, no dominance.

Self-gating by construction: in healthy flight the assisted and raw attitude
clocks are equal (measured gain 1.00), so the second clause is false.

**PREDICTIONS:**

1. **damaged_wing adopts roll_priority before inversion (147).** The clauses are
   both true from ~action 111, where attitude reads 255 raw against 1024
   assisted while altitude reads 1024 and heading 683+.
2. **nominal and jammed_rudder unchanged** — the assisted and raw clocks
   coincide in both, so the rule cannot fire. If either moves, the self-gating
   claim is wrong.
3. **Target 0 crashes on damaged_wing.** If the corner is adopted before
   inversion and the aircraft still departs, `roll_priority` itself is
   insufficient and the answer is the corner library, not the selection path.
4. **Watch for oscillation**: the rule sets `regime_ordinal` directly and only
   from `fixed_point`, so it cannot cycle, but the adoption action is stamped
   to confirm it fires once rather than repeatedly.

## Block AI — selection is cost per unit benefit (emp v1.13.0)

`singleton_cost` summed a benefit term (weighted squared residual to the target)
with resource terms (drag, energy, activation, authority) and minimised the
total. Summing makes them exchangeable, so when the target is small and no
candidate reduces the residual much, the resource terms decide and **the
cheapest option wins — doing nothing is always cheapest.** Measured (§72): the
zero-effect airframe was selected on 25.9% of nominal actions against 0.1%
before it was learned.

It is now `resource / benefit`, where benefit is the reduction in weighted
squared residual relative to commanding nothing. A candidate that does not
improve on the null action has benefit <= 0 and is inadmissible at any price —
compared against the null action, not a tuned floor.

**This changes EVERY selection in the motor-program seed**, so every scenario is
expected to move. Baseline is the same tree with the previous `singleton_cost`.

**PREDICTIONS:**

1. **The zero-effect airframe stops being selected**: plant-in-trial on nominal
   falls from 25.9% toward 0%. This is the direct test of the mechanism; if it
   does not fall, the diagnosis in §72 is wrong.
2. **Nominal improves or holds** (333.97 with dense learning). A quarter of its
   actions were being spent on a null command; recovering them should not cost
   tracking.
3. **No crash-rate regression across the 8-scenario block.** Decisive, as in
   every prior block.
4. **Direction on damaged_wing NOT preregistered.** It is the scenario where
   commanding *something* least reliably helps, and a criterion that refuses
   null actions may drive more control input into a departure. Judge on the
   crash guard, not the RMSE.
5. **Watch for "no admissible candidate"**: if every candidate has benefit <= 0
   the Argmin sees only sentinels. That state was previously expressible as
   "pick the cheapest"; it is now a real possibility and would show as a stall.

## Block AJ — admissibility is causal (emp v1.13.0)

A candidate is admissible only if its COMMAND can change something:
`specified_maximum_position_change_per_action > 0`, the world's own declaration
of causal capability, applied at the three candidate filters. Measured on this
airframe: 0.667 aileron/elevator/throttle, 0.500 rudder, **0.000 the airframe**.

Block AI established that no ranking over PREDICTIONS can exclude the airframe:
its learned means predict the target and it costs nothing, so cost/benefit made
it win harder. Correlation with the end is what a good predictor offers; causing
the end is a different property.

**PREDICTIONS:**

1. **Plant selection falls to 0%** from 25.9% on nominal. Direct test.
2. **Nominal improves toward 326.65** (its value when the plant was effectively
   never selected) from 333.97. A quarter of its actions were null commands.
3. **No crash-rate regression** across the block. Decisive.
4. **jammed_rudder holds** near 324.92.
5. **damaged_wing direction NOT preregistered.**

## Block AK — the surprise-reduction term (emp v1.14.0)

Benefit is furtherance of goals OR reduction of surprise; both ranking functions
computed only the first. Measured (§75): in steady cruise every real effector
has NEGATIVE goal benefit (−0.0070) while the null option has 0.0000, so doing
nothing is optimal whenever the goal limb is flat — 25.9% of nominal actions.

Added: `surprise_benefit = surprise_weight / (1 + experience_count)`, the loop's
own learning rate, subtracted from the cost being minimised. **Absent
`surprise_weight` reads zero**, so every consumer that does not declare one is
byte-identical. The F-16 policy declares 5.0, sized from the measurement above
(real effectors trail by 0.0070 in goal benefit and lead by ~0.004 in learning
rate, so a weight above ~1.75 flips it).

**PREDICTIONS:**

1. **Plant selection falls sharply** from 25.9% on nominal. With ~998
   observations its learning rate is ~0.001 against ~0.005 for the surfaces, so
   it now loses on both limbs. If it does not fall, the diagnosis in §75 is
   wrong.
2. **Nominal improves toward 326.65** from 333.97 — the actions currently spent
   on a null command are returned to control.
3. **No crash-rate regression.** Decisive, as in every block.
4. **Watch for over-exploration**: a large surprise weight makes the loop prefer
   unexercised effectors, which is desirable on a fault and wasteful in cruise.
   Any degradation in nominal tracking is that trade appearing, and 5.0 is the
   first value tried, not a tuned one.

## Block AL — the viability ladder as the selection criterion (motor_compose.rs)

Structural admissibility was an ABSOLUTE gate: when every `state_safe_*` reaches
zero — what a departing airframe does — no candidate is admissible and the
composer returns an empty plan. It stops choosing exactly when choosing matters.

It is now a RUNG: prefer any candidate that keeps the structure intact; if none
does, still choose the cheapest of those that do not. Least-worst, never
"acceptable".

**PREDICTIONS:**

1. **nominal and jammed_rudder unchanged.** Their envelopes never collapse
   (measured: `state_safe_normal_load` never reaches 0 in either), so every
   candidate sits on the same rung and the criterion reduces to the existing
   cost. If either moves, the rung is firing where no rung was needed.
2. **damaged_wing changes**, because its envelope collapses from ~action 413
   and the composer currently stops choosing there.
3. **Direction on damaged_wing NOT preregistered.** §81 established the
   scenario is beyond control — extreme body rate in 3/3 episodes, roll
   authority below demand 12.8% of the time, departure with full aileron
   restored — so "still crashes" does NOT falsify the criterion. What is being
   tested is whether the loop keeps choosing, not whether it survives.
4. **No crash regression on the other seven scenarios.** Decisive.
5. **Watch structural utilisation**: the rung permits exceeding the envelope
   when nothing else is possible, so the utilisation may rise. Anything
   approaching §78's 169× means the rung is being used where an admissible
   option existed.

## Block AM — selection spends against the budget (cre v7.8.0, f16 v8.63.0)

Two changes. The floor is now measured from the HIGH-WATER rung rather than the
current one — `rung - worth` tracked the descent and could never be violated,
which is a ratchet, not a budget. And the probe stop gains a second trigger:
the checklist also stops when `regime_budget_exhausted`, i.e. when viability has
fallen below the authorised floor.

Probing is the one thing this loop does deliberately at a cost, so it is the
first consumer of the budget. With `regime_goal_worth_log` 0.0 the floor is the
high-water rung and ANY viability loss exhausts the budget.

**PREDICTIONS:**

1. **nominal unchanged** — rung 3 on 1000/1000 actions, so the budget is never
   exhausted and the new trigger cannot fire.
2. **damaged_wing changes**: rung drops below 3 early, so the checklist stops
   almost immediately instead of running its passes.
3. **jammed_rudder is the risk.** Its rung dips to 2 on 43 actions, which now
   exhausts the budget and stops the checklist early — possibly BEFORE quorum
   identifies the dead rudder. If the jam result (324.92) degrades toward the
   pre-stop baseline of 6928, the budget is firing where the quorum should have.
4. **No crash-rate regression.** Decisive.

## Block AN — damaged_wing re-specified, whole suite re-baselined

`roll_beta` and `roll_r` change from **−1.0 to +0.5**. The negative values did
not scale those derivatives, they INVERTED them: the dihedral effect and the
yaw–roll coupling reversed sign, which is a divergent airframe rather than a
damaged one. Measured (§94): at −1.0 the controller crashes 3/3 with extreme
body rate 3/3 and no change can pass; at +0.5, with 30% lift loss, half the
aileron roll authority and 50% more adverse yaw all retained, it survives 0/3
with extreme rate on one seed and two episodes ending within 2 ft of the ground.

**Every baseline in this document is invalidated by this change.** The
`333.97 / 324.92 / 14763.77` pins and the block X full-suite numbers refer to a
scenario that no longer exists. This block establishes the replacement.

**PREDICTIONS:**

1. **Seven scenarios byte-identical.** Only `damaged_wing`'s aero scales change,
   so nominal, jammed_rudder, broken_aileron, saturated_elevator, landing_gear,
   shifted_cg and damaged_tail must reproduce their block X values exactly. Any
   movement means the edit touched more than intended.
2. **damaged_wing crash rate falls from 2/3.** §94 measured 0/3 at this
   configuration on these seeds.
3. **damaged_wing remains discriminating**: extreme body rate on at least one
   seed, and minimum altitudes low enough that a worse controller would crash.
   If it becomes trivially safe, the scenario has been made useless in the other
   direction.
4. The new numbers become the baseline for every subsequent block, and every
   earlier comparison in this document is superseded rather than corrected.

## Block AO — risk ranked relatively (motor_compose.rs), against the AN baseline

Structural risk enters the composer's cost as the fraction of the envelope a
candidate would consume, worst key, priced with the existing
`activation_weight`. It is a COMPARISON, not a gate: with a roomy envelope every
candidate scores near zero, and as it tightens the differences grow and the
structurally cheapest wins among equals. Always has an answer, including when
every option is bad — which is what §80 required and §83's gate could not do.

No new weight and no threshold. Limits disabled or no envelope published gives
zero.

**Baseline is block AN**, commit `97c8be7315`, the re-specified suite:
nominal 311.24, jammed_rudder 809.29, broken_aileron 1783.56,
saturated_elevator 3801.49, landing_gear 1115.62, shifted_cg 5693.33,
damaged_tail 8164.04, damaged_wing 6506.20, all 0/3 crashes.

**PREDICTIONS:**

1. **No crash-rate regression anywhere.** All eight are at 0/3 now, so any
   crash is a decisive falsification — this is the first block in this line with
   a baseline clean enough for that to be a sharp test.
2. **Peak structural utilisation falls on the scenarios that have any**:
   damaged_wing (16.83, 15.90 on two seeds), saturated_elevator (4.92),
   damaged_tail (13.35 historically). The term exists to make a candidate that
   consumes the envelope lose to one that does not.
3. **Scenarios with a roomy envelope are near-unchanged** — nominal, jam,
   broken_aileron, landing_gear all sit at 0.64–0.65 utilisation, so the term is
   ~0 for every candidate and cannot discriminate.
4. **Tracking direction NOT preregistered.** Spending less structure may cost
   altitude tracking; that is the trade being measured, and RMSE alone does not
   decide it.

## Block AQ — the structural price in the log currency it was declared in

Block AP priced structural consumption LINEARLY in the envelope fraction, so
routine flight at 0.64 of the limit paid a substantial charge with nothing at
risk (broken_aileron, +656 ft, structural unmoved at 0.64 both arms).  The
decade dimension is a LOG dimension; pricing it linearly threw away the reason
for expressing it in decades.

Changed, one variable only:

```
    AP:  worst_fraction            * rung_decade * null_residual
    AQ:  max(0, log10(worst_frac)) * rung_decade * null_residual
```

The floor is not a chosen threshold.  Below the certified limit deformation is
ELASTIC and the airframe returns to where it started, so no irreversibility is
consumed and there are no decades to charge.  Above it the deformation is
plastic and log10(load/safe) counts the decades past the operator's own declared
safe load.  The composer already carries authority as `-log_authority`; this
puts structure in the same currency.

Baseline: block AN, `results/rebaseline_damaged_wing_plus05_v1`, commit
`97c8be7315` (HEAD `427d458538` touches only docs/results).

**Predictions, in falsification order:**

1. **DECISIVE — crashes stay 0/24.**  Any crash kills the term outright.
2. **SHARP — six scenarios byte-identical.**  nominal (0.64), jammed_rudder
   (0.64), broken_aileron (0.64), saturated_elevator (0.65), landing_gear (0.64)
   and shifted_cg (0.65) never exceed the limit, so the price is EXACTLY zero at
   every action and their trajectories must reproduce AN bit for bit.  Any drift
   on these six means the term is firing inside the envelope and the log form
   has failed the same way the linear one did.
3. Only damaged_wing (16.83) and damaged_tail (10.79) may move, being the only
   two that go past the limit at all.
4. Peak structural utilisation on those two should not RISE.  Tracking direction
   is not preregistered — buying structural margin with tracking error is the
   trade the term exists to make, and AP already showed damaged_wing can get
   both at once.

Prediction 2 is the real test: it is the difference between a risk price and a
tax on operating.

## Block AW (next) — the latency is a LEVEL comparison of a CLOSING quantity

Block AV eliminated three candidate gates for the 287-action adoption latency
(evidence window, deliberation opening guard, `dominated` flag -- all measured
inert, all reverted). What remains is `Eq(V("candidate"), best)` in
`cre_publish_regime_pareto_verdict`, where `best` is the Argmax over proposed
candidates by the situational priority axis VALUE.

That is a comparison of LEVELS. The quantity that is actually moving is the
manifold: `f16_publish_goal_manifold` already computes `reach / gap` per axis as
`f16_goal_margin_*`, and says in its own docstring that "THE MARGIN IS A RATIO
because its LOG is the decision quantity" -- and then, in the last line,
"DECIDES NOTHING."

The hypothesis: **adoption is late because the loop compares where the
candidates ARE, not how fast the manifold is closing.** Levels do not cross
until 597 -- which is simply when the probe's own reading finally falls -- while
the manifold has been contracting since the stall at ~190. A level comparison
defers by construction; a rate cannot.

Predictions, to be measured before anything is built:

1. `f16_goal_margin_altitude` and its log begin falling at the stall (~190),
   not at 310 and not at 597.
2. The per-candidate priority values do NOT cross until ~597, confirming the
   level comparison is what is holding.
3. If (1) and (2) both hold, the adoption trigger belongs on the margin's rate
   of change, not on the level -- and the existing manifold quantity, which
   currently decides nothing, is what should carry it.

Instrument first: dump `best`, every candidate's `regime_situational_priority_
value`, and `f16_goal_margin_*` across actions 300-600 of damaged_wing ep1.
Do not build a fourth fix before reading which comparison is holding.

## Block AX — the allocation drives the targets, so a minted corner can fly

Every corner today has a hand-coded twin: `f16_adopt_metastable_trim`,
`adopt_orbit_regime_rule`, `adopt_speed_priority_regime_rule`, each keyed on one
ordinal and each writing `target_*` itself. That is why the generated corner is
minted at the HELD ordinal -- a new ordinal would be selected and then flown by
nothing -- and that no-op is the root of blocks AS, AV and AW.

**The change: a corner's allocation writes the targets, so minting is flying.**

A corner's allocation is a per-axis share of what it will attend to. The general
statement of "flying" it is then one line: **demand of each axis only the share
of it you are keeping.**

```
    target_<axis> := share_<axis> * target_<axis>
```

For the generated corner the shares are already computed from the plant --
`_generated_share = min(reach / gap, 1)` -- so this says: demand only what is
REACHABLE. At the stall the altitude margin falls below 1, the vertical demand
scales down, and the wing unloads. **The recovery corner is not a named
manoeuvre that someone has to author; it is what "demand only what you can
reach" does when the wing has stopped reaching.** That is why this belongs in
the machinery and not in a sixth hand-written corner.

Scoped narrowly so the five declared corners are untouched:

* only the generated corner is minted with `share_<axis>` attributes; absence of
  those attributes means the new rule does not match, so every declared corner
  flies through its existing hand-coded twin exactly as now;
* the generated corner moves to a NEW ordinal, so adopting it is no longer a
  no-op and it stops being the frontier-suppressing probe of block AW.

Baseline: `results/ground_truth_ar_v1` at commit `9ecc10c2f1` (AR numbers with
the AV escape in place: 7 scenarios byte-identical, damaged_wing peak structural
15.29, crashes 3/24).

**Predictions, in falsification order:**

1. **DECISIVE -- crashes must not rise above 3/24.** The AV escape path plus a
   flyable corner is the whole point; a regression here kills it.
2. The six roomy scenarios (nominal, jammed_rudder, broken_aileron,
   saturated_elevator, landing_gear, shifted_cg) should be BYTE-IDENTICAL. They
   never reach rung 0, the generated corner is never adopted, and no declared
   corner carries shares. Any drift means the mint change leaked.
3. damaged_wing adopts the generated ordinal rather than 5/4/1, and does so
   once rather than the five-way cycling AW measured -- because the allocation
   tracks the plant continuously instead of switching between fixed corners.
4. Peak structural on damaged_wing should FALL below 15.29: unloading is what
   the scaled vertical demand does.
5. Altitude RMSE on damaged_wing will RISE, and that is not a falsifier --
   surrendering unreachable altitude is the manoeuvre, and tracking error is
   what it costs.

Not preregistered: whether 2/3 becomes 1/3 or 0/3. The mechanism being right
does not make the corner sufficient, and AW showed acting earlier can churn.

## Block BH — the unit fix: publish the closing rate per ACTION

`cre_project_region_reachability` computes `region_gap / channel_rate_measured`
and documents it as "integer actions until the gap closes". That holds only if
the rate is metres per ACTION. `f16_declare_terrain_region` and
`f16_track_terrain_region` publish `f16_sink_rate_ema`, metres per SECOND, so at
10 Hz every region clock reads 10x shorter than the truth (block BG: shifted_cg
tripped rung 0 at action 215 with 807 actions of margin, by 0.7 of a second).

Fix, in the consumer, both rules:

```
    sink = Max(Abs(f16_sink_rate_ema), eps)
      ->  Times(sink, control_action_duration_seconds)
```

Nothing in the general seed changes: the contract was always per-action and the
consumer was always the thing that knew which measured quantity to supply.

Baseline: `results/integer_clock_bd_v1` at commit `13a26072b5` (3/24 crashes;
damaged_tail 1/3, damaged_wing 2/3).

**Predictions, in falsification order:**

1. **DECISIVE -- crashes must not exceed 3/24.** A rung that fires later must not
   cost an episode anywhere.
2. **shifted_cg no longer reaches rung 0 at action 215**, and ideally not at all:
   its terrain clock becomes ~807 against a horizon of 80.
3. The five roomy scenarios should be BYTE-IDENTICAL. Their clocks already sit at
   or near the 1024 cap (nominal reads 651 at action 100 and caps at 1024 once
   multiplied), so the rung never moves and nothing downstream sees a change.
4. damaged_tail and damaged_wing MAY move. Their clocks stretch 10x, so rung 0
   arrives much later or not at all, which means less escalation and less spend
   authority. Direction is not preregistered: later escalation was good in AW
   (the churn cost more than the delay) and bad in principle for a real
   departure, and this line has been wrong about that sign twice.
5. Peak structural on damaged_wing should not RISE above 15.86.

Note what this block does NOT test: the probe still wins every frontier, so
almost nothing can be adopted regardless of the rung. This measures whether the
CORRECTED signal is safe, not whether acting on it is. Retirement stays reverted
and BE is re-run only after this lands.

## Block BJ — the allocation corner, flyable at last

AX built it and reverted it: the generated corner minted at its OWN ordinal, with
`f16_drive_targets_from_allocation` scaling each derived target by that corner's
share of its axis. Because the shares are `min(reach / gap, 1)` recomputed every
action, the rule says DEMAND ONLY WHAT IS REACHABLE -- and the recovery is not
authored: at the stall the altitude margin falls below 1, the pitch-angle demand
scales with it, and the wing unloads.

It was reverted because it needed a real ordinal on a frontier the probe owned,
and because with a real ordinal it was adoptable in benign conditions. Both are
resolved: the probe is retired (BI) and adoption is bounded by
`candidate_requires_change` (AY). This re-applies it with the bound in place.

Note what changes about the corner's identity: BI retired it AS A PROBE -- an
unadoptable candidate minted at the held ordinal. It returns as a flyable corner
at its own ordinal. The test is updated to assert that, not its absence.

Measured previously (AX, before the unit fix and before retirement):
damaged_wing peak structural **15.29 -> 6.29**, ep0 minimum altitude 2660 ->
6431 ft, RMSE better on two episodes of three.

Baseline: `results/probe_retired_bi_v1` at commit `8bc93ccd5a` -- 3/24 crashes,
damaged_tail 1/3 struct 8.55, damaged_wing 2/3 struct 23.91.

**Predictions, in falsification order:**

1. **DECISIVE -- crashes must not exceed 3/24.**
2. **damaged_wing peak structural must FALL well below 23.91.** This is the one
   change measured to reduce it, and unloading an over-stressed wing is the
   mechanism. If structural does not fall, the corner is not doing what AX
   measured and the whole rationale is void.
3. The six roomy scenarios should be BYTE-IDENTICAL: they never reach rung 0, and
   the corner declares `candidate_requires_change`, so it cannot be adopted
   there. This is the AX prediction that FAILED before the bound existed; it is
   the direct test of whether AY actually fixed that.
4. Altitude RMSE on damaged_wing may rise. Not a falsifier -- surrendering
   unreachable altitude is the manoeuvre and tracking error is its price.
5. **Watch the wall clock.** AX ran ~3x slower per episode with this corner live
   and the cause was never found. If it recurs it is a result in its own right:
   a 10 Hz loop cannot afford it, and it must be explained before the corner is
   kept on tracking grounds alone.

## Block BL — negative shares, and licensing on the margin

BK established the two reasons no corner recovers a stall, both measured:

1. an allocation share lives in [0, 1], so a corner can only ATTENUATE a demand,
   never oppose it -- at margin zero the generated corner commands level, and a
   stalled wing needs nose-down;
2. adoption is licensed only by viability rung 0, which is terrain/structural/
   roll -- none of which is "the wing has stopped flying" -- so the corner is
   unreachable during the stall (rung 2-3 until action ~597).

Both are addressed here.

**Negative shares.** The scoring share stays in [0, 1]; the frontier
interpolation depends on that. A separate DRIVE share is used for targets:

```
    drive = 2 * min(margin, 1) - 1        margin >= 1 -> +1  (demand it fully)
                                          margin = 0.5 ->  0  (stop asking)
                                          margin = 0   -> -1  (command the opposite)
```

The canonical affine map from [0, 1] onto [-1, 1]; no constant beyond the two
that define that map. It makes "spend altitude to buy speed" expressible for the
first time -- the same trade the energy relation (AT) already measures.

**Licensing on the margin.** `regime_change_required` becomes true when terrain
is not clear OR any goal margin is below 1. The margin is measured every action,
crosses at the stall (action 190 on damaged_wing ep1), and is already the
quantity `_generated_share` is built from.

Baseline: `results/alloc_corner_bj_v1` at commit `84dba29336` -- 3/24 crashes,
damaged_wing 2/3 struct 15.86, damaged_tail 1/3 struct 10.92.

**Predictions, in falsification order:**

1. **DECISIVE -- crashes must not exceed 3/24.**
2. **damaged_wing must command nose-down near the stall (~action 190-250), not
   at 598.** If `target_pitch_angle` does not go negative early, the negative
   share is not reaching the aircraft and the block is void whatever the
   tracking says.
3. **The six roomy scenarios will NOT be byte-identical, and that is expected.**
   Licensing on the margin is a strictly wider licence: any transient dip below
   1 on any axis now permits adoption. This is the risk of the block, and
   prediction 1 is what bounds it.
4. damaged_wing peak structural should not rise above 15.86.
5. Not preregistered: whether 2/3 becomes 1/3 or 0/3. Commanding nose-down at
   the stall is necessary for recovery and may still not be sufficient at 0.7x
   lift.

## Block BQ — the drive share in decades, not linear

BO measured the linear drive share at 9/24 crashes. The diagnosis: linear crosses
zero at margin 0.5, so an objective that is merely HARD gets its demand inverted
and the loop departs an aircraft that was flying.

**The margin is a ratio, so its log is the decision quantity** --
`f16_publish_goal_manifold` says so in its own docstring, and the linear form
threw that away. Same correction the structural price needed (AP -> AQ).

```
    drive = clamp(1 + log10(margin), -1, +1)

    margin  0.5  ->  +0.70   (linear:  0.00)
    margin  0.3  ->  +0.48   (linear: -0.40)   <- linear already inverting
    margin  0.1  ->   0.00   (linear: -0.80)
    margin  0.01 ->  -1.00   (linear: -0.98)
```

One decade short of reachable to stop asking, two to oppose. Everything else is
unchanged from BO: flyable ordinal, conjoined licence, and the idempotency guard
-- written BEFORE the rule this time, not discovered afterwards.

Baseline: `results/probe_retired_bi_v1` at `8bc93ccd5a` -- 3/24, damaged_wing 2/3
struct 15.86, damaged_tail 1/3 struct 8.55. (BO's 9/24 is the arm being repaired,
not the baseline.)

**Predictions:**

1. **DECISIVE -- crashes must not exceed 3/24.** BO's 9/24 must be recovered in
   full; anything above 3/24 means convexity was not the defect.
2. **saturated_elevator and shifted_cg must return to 0/3.** They are the two the
   linear form destroyed, and both fly with margins in the 0.3-0.5 band where
   the two forms differ most.
3. damaged_wing peak structural should fall below 15.86 -- the actual claim of
   the whole allocation line, and never yet observed except as the BJ artefact.
4. `target_forward` must never be identically 0 across a held-corner window --
   the BJ artefact's signature, now explicitly watched.
5. Wall clock comparable to BI's ~580 s; the guard is in from the start.

## Block BR (next) — the drive share is a VECTOR, not six scalars

BQ fixes the SHAPE of the per-axis map (linear -> decades). It does not fix a
deeper error that both forms share: **each axis maps its own margin to its own
command, independently, as an absolute scalar.**

The tree already states the correct principle, in `_allocated`'s own docstring:

> **AN ALLOCATION IS A BUDGET: authority given to one objective is not
> available to another.**

`_allocated` honours it -- declared shares are divided by their total, so they
mean something only relative to each other. `_drive_share` does not: it computes
six numbers from six margins with nothing comparing them.

**That is why inverting one axis is so destructive.** Commanding -0.4 on altitude
while heading and speed still demand +1.0 is not a manoeuvre; it is an incoherent
command vector. A recovery is a DIRECTION in target space -- nose down AND
accept the heading loss AND spend the altitude for speed, together -- and a
per-axis absolute map cannot express a direction, only six unrelated magnitudes.
It can produce command vectors no pilot would ever fly and no corner ever
declared.

The correction, to be built after BQ reports:

* compute the per-axis drive terms as now (decades of unreachability);
* then **normalise across the axis vector**, exactly as `_allocated` normalises
  declared shares, so only the RELATIVE weighting survives;
* the vector's direction is the manoeuvre; its magnitude is set by how much
  authority the corner has, not by six independent margins.

This also predicts something falsifiable about BQ. If BQ recovers 3/24, the
convexity fix was sufficient for SAFETY and the vector error costs only
effectiveness -- damaged_wing stays 2/3. If BQ is still above 3/24, then shape
was never the issue and incoherent command vectors are, which would make this
block mandatory rather than incremental.

## Block BS — the vector-normalised drive (BR built)

`_normalised_drive` holds the sum of the drive magnitudes at the axis count, the
faithful analogue of `_allocated`'s divide-by-total. Scale-invariant, so a
saturated vector is unchanged; it redistributes only where an axis has slack.

**A concern recorded BEFORE the run, because it may be the wrong sign.** When an
axis has slack the freed budget goes to the OTHERS, so at a stall the altitude
opposition GROWS (-1.00 -> -1.15). The budget reading that motivated this block
was "authority spent opposing one objective is not available to the others" --
that would ATTENUATE the opposition, not amplify it. `_allocated`'s arithmetic
gives the amplifying form. Both are defensible readings of a budget and they
differ in sign, so this measures the one the tree already implements, and the
other becomes the next candidate if this fails.

Baseline `results/probe_retired_bi_v1` (`8bc93ccd5a`): 3/24, damaged_wing 2/3.
The arm being repaired is BO/BQ's 9/24.

**Predictions:**

1. **DECISIVE -- crashes must not exceed 3/24.** BO and BQ both returned 9/24
   with per-axis absolute maps; if normalising the vector does not recover that,
   then the vector framing is not the defect either.
2. saturated_elevator back to 0/3 -- untouched at 3/3 by both previous forms, so
   it is the sharpest discriminator.
3. damaged_wing structural below 15.86.
4. If crashes land BETWEEN 3 and 9, the vector framing is partially right and the
   sign concern above is the likely remainder.

If this fails, four blocks of the allocation corner across two orthogonal axes of
variation (per-axis shape, and vector coupling) have all been worse than no
corner, and the honest conclusion is that the corner is the wrong instrument --
not that a fifth parameterisation is owed.

## Block BT (next) — a stall recovery is BASIN ESCAPE, and the machinery is already here, switched off

BS closed the allocation line: a corner is a reallocation of authority among the
objectives the aircraft already has, and four parameterisations of that are all
worse than no corner. The reframing that explains why: **a stall is a different
attractor.** No redistribution of demand within the deep-stall basin escapes the
deep-stall basin. The aircraft has to be moved to where the basin is bigger.

**The tree already draws this exact distinction and it has been off all session.**

* `_mint_candidate_effects` carries `candidate_restores_basin`, documented as
  *"does this candidate change the OPERATING CONDITION so the fixpoint stays
  attainable, rather than surrendering an objective?"*
* Measured in the current seed: **`speed_priority` is the ONLY corner declaring
  `restores_basin = 1.0`.** hold, trim, orbit and roll_priority all declare 0.0.
* `cre_publish_regime_pareto_verdict` consumes it, and its own comment is the
  thesis verbatim: *"A transition that has not happened is not a reason to give
  up an objective -- it is a reason to move the plant to where the basin is
  bigger, while the authority to move it still exists."*
* That clause is gated on `regime_class_gate_enabled`, **OPT-IN, and
  `class_gate_enabled: bool = False` in the runner.** No block in this session
  set it. Every measurement today ran with basin-restoring candidates treated
  identically to surrender candidates.

So the selection has never once distinguished "move the plant" from "give up an
objective". The one corner that IS a basin escape has been competing on the same
terms as four corners that are not, and losing to them on clocks.

**The next block is one flag**, not a new mechanism: run the suite with
`class_gate_enabled=True` against the BI baseline (3/24). Predictions:

1. **DECISIVE -- crashes must not exceed 3/24.** The gate narrows what is
   admissible mid-transition; narrowing must not cost an episode.
2. damaged_wing should adopt **speed_priority (ordinal 4)** during the departure
   rather than roll_priority (5), because with the gate on it is the only
   admissible class while a transition is projected inside the horizon.
3. If damaged_wing improves at all, basin escape is the right frame and the whole
   allocation line was the wrong instrument for a reason now understood.
4. If it does not, the gate is necessary but the F-16's single basin-restoring
   corner is insufficient -- and the question becomes what a SECOND basin escape
   would be for this airframe, which is a question about the plant rather than
   about selection.

Note this is the cheapest untried thing in the entire line: no new rule, no new
parameterisation, one boolean that the general seed has been waiting on.

## Block BU (next) — a stall IS a plant failure, and recalibration is one-shot

Reframing: a stall is not a control problem distinct from a fault. It is the
plant entering a different basin relative to the environment -- which is exactly
what a damaged wing or a jammed rudder is. The difference between "the plant
changed" and "the plant changed AGAIN, aerodynamically, at high alpha" is a
distinction the loop should not be making, and the tree already has the faculty
for the first: recalibration on model mismatch.

**Measured, BI baseline, and it settles the question:**

```
  damaged_wing   ep0/1/2   recalibration_count = 2.0   post_fault_action = 101
  jammed_rudder            recalibration_count = 2.0   post_fault_action = 101
  broken_aileron           recalibration_count = 2.0   post_fault_action = 101
  damaged_tail             recalibration_count = 2.0   post_fault_action = 101
  nominal                  recalibration_count = 0.0   post_fault_action = None
```

Fault onset is action 100. **Recalibration fires twice, at action 101, and never
again** -- in every scenario, including the ones that go on to depart and hit the
ground 540 actions later. The stall at ~190 produces no recalibration whatsoever.

So recalibration is **event-triggered, not mismatch-triggered**: it responds to
the scheduled fault transient and then considers the plant known. When the plant
enters a new basin mid-flight -- which is what a stall IS -- the faculty that
exists to relearn the plant does not re-arm.

**That is why the selection layer could never solve this.** Blocks AS through BS
asked the frontier to choose a corner for an aircraft whose effector models were
last calibrated at action 101, in level flight, before the wing stopped flying.
No selection over stale models can be correct, however the corners are shaped,
coupled, licensed or guarded -- which retrospectively explains four
parameterisations all being worse than none.

It also matches a standing instruction in this line: *"nothing is ever permanent
-- a latch can have different activation and deactivation energy, but the world
doesn't stop changing because you detect a change once."* Recalibration is
exactly such a latch, and it currently has no deactivation path.

**Predictions for BU, to be measured before anything is built:**

1. Effector-model prediction error rises sharply at the stall (~action 190) and
   stays high -- the mismatch signal exists and is simply not consumed.
   `prediction_error_energy` is already on the trace row.
2. The learned `mean_*` consequences on the effector models at action 400 still
   describe the pre-stall aircraft, not the stalled one.
3. If both hold, the fix is to re-arm recalibration on sustained mismatch rather
   than on the onset event -- a change to WHEN the existing faculty fires, not a
   new mechanism, and squarely in the general seed rather than the F-16 consumer.

Do not build before measuring (1) and (2). This line has spent four blocks on a
mechanism whose premise was never checked.

### BU addendum — flat spin, stall, damaged wing: one solution type, and the humanoid already has it

A flat spin is an entirely different basin from a deep stall, with different
physics and a different exit. It is the same PROBLEM SHAPE: the plant has moved
to a basin its held models do not describe. So is a jammed rudder. So is a
damaged wing. The response type does not vary with the name of the failure --
detect the mismatch, relearn the plant where it now is, re-derive what is
reachable, select on that.

**This rules out the entire class of fix this line kept reaching for.** A "stall
recovery corner" is a canonical posture for one named failure; it would not touch
a flat spin, and a flat-spin corner would not touch the next basin. BK prescribed
exactly that and BS falsified it in four parameterisations. The failure was not
the parameterisation -- it was authoring a canonical response per named basin at
all.

**The humanoid already implements the general form, and the F-16 does not:**

```
  ha_mint_situated_recovery_basin
    "On entry to fallen-body recovery, anchor a temporary basin to the sensed
     configuration and dimensionless body state.
     The basin is a situated search frame, NOT A CANONICAL POSTURE."
```

The F-16 mentions "basin" nine times and every one is the `restores_basin`
boolean on a hand-authored corner. **It mints no basin.** Its five corners ARE
canonical postures -- the thing the humanoid's own docstring says a recovery
basin must not be. The humanoid, on falling, anchors a search frame to where the
body actually is; the F-16, on departing, picks from a fixed library authored for
an aircraft that was flying.

So the two prescriptions compose, and they are ordered:

1. **BU** -- re-arm recalibration on sustained mismatch, so the plant models
   describe the basin the aircraft is actually in. Nothing downstream can be
   correct before this.
2. **then** -- mint a situated recovery basin from the sensed state, the F-16
   analogue of `ha_mint_situated_recovery_basin`, so the search frame is anchored
   to where the aircraft IS rather than to five postures authored in advance.

Neither is a stall fix. Both are failure-mode-agnostic by construction, which is
the test the F-16 corner set fails and the humanoid's basin machinery passes.

## Block BV (next) — credit assignment from compound trials: the honest scoping

`emp_learn_uncommanded_contributor_from_residual` already IS credit assignment
from compound action:

```
    residual = observed change - sum of the commanded members' predictions
```

averaged incrementally into the same `mean_*` columns every effector carries.
Fifth instance of the general form already existing in this tree.

**But it is scoped to the unambiguous case, and that scoping is correct.** A
never-commanded contributor is the ONLY possible owner of the residual, so
attribution is forced. With four commanded members the residual has four possible
owners and no single receipt distinguishes them -- which is exactly why
`emp_learn_factorized_effector_from_exact_receipt` guards on
`expected_member_count == 1`. That guard is not an oversight; it is the
identifiability condition.

So this is a DESIGN decision, not a port, and it should not be made by analogy.
The candidates, none measured:

* **proportional to predicted contribution** -- distribute the residual by each
  member's share of the predicted effect. Cheap, and wrong whenever the model
  that is most wrong is also the one predicting least.
* **accumulate and solve** -- treat each compound receipt as one equation in the
  members' corrections and solve across a window. Identifiable when the
  composition varies (it does: widths 1-5, changing group membership), and this
  is the form that actually earns the attribution.
* **exercise for identifiability** -- when a member's error is unattributable,
  command it alone. The probe ladder already exists to do exactly this, and the
  cost is one action of authority spent on knowing, which the operator's
  information budget (`regime_information_worth_log`) already prices.

**The third is most in keeping with the tree**: it does not invent an attribution
rule, it recognises that the loop cannot know and spends a measured amount to
find out -- the same move the probe ladder makes for limits.

Measure before building, per BU's own lesson repeated three times:

1. how often is a member's contribution identifiable from composition variation
   alone, over a departure? (widths and group membership are already in the
   trace);
2. what fraction of actions would need a singleton exercise to close the gap;
3. what that costs against the declared information budget.

**Not started.** This is a core general seed with humanoid, aerial and helicopter
consumers, and the session has no budget left to measure a change of that blast
radius. Beginning it now would repeat the exact failure this line has recorded
five times: building the plausible thing before measuring whether it is the
thing.

## Block CD — learning is a DIMENSION the tree does not represent

Stepping back from three blocks of rate patching. The observation that explains
all of them: **the Jabberwock is not missing an understanding of learning, it is
missing the REPRESENTATION of learning as a frame.** Effectors got representations
because they are easy to measure; learning never did.

**The regress is the evidence, and it is today's own record:**

```
  1/n asserts stationarity          -> declare a floor            0.05
  a flat floor costs quiet regimes  -> declare a surprise factor  2.0
  surprise needs a reference        -> an error EMA
  the EMA needs a rate              -> ... 1/n
```

I used a 1/n accumulator to detect that 1/n accumulators are too slow, then
declared two constants to repair the first constant. **Each rate needs a rate.**
That regress does not terminate by adding another parameter, and it is the
signature of a quantity being represented as a scalar knob when it should be a
coordinate.

**What the tree does everywhere else and not here.** Shapes are decoded against a
codebook and minted when the residual will not fit. Dimensions themselves are
minted -- `DimInfer` finds a LATENT dimension when a residual is coupled across
observed ones, and `scale2` established that A BASE IS A DIMENSION rather than
per-frame config. Space is quantised per body shape with per-dimension
resolution. Transformation is a quantum step along one dimension.

Learning has none of this. `experience_count` is a monotone scalar;
`learning_rate` is a scalar branch; `model_adaptation_rate_floor` and
`model_surprise_factor` are declared constants I wrote today. Nothing about how
this agent learns is decodable, transformable, mintable, or comparable across
frames -- so it cannot be inferred from residual the way every other
representation in this tree is.

**Consequences that follow directly, and each is checkable:**

* **"How fast to forget" is a ratio between frames** -- evidence-age against
  plant-change-rate -- which by the frame/continuum invariant makes it a
  CROSS-FRAME map, not an in-frame constant. Declaring 0.05 puts a real number
  where a map belongs, the same category error as the terrain clock's seconds
  read as actions.
* **Surprise is a residual that does not fit the held model** -- which is
  precisely what `sd_mint_quantum` already responds to. The stall should mint a
  learning quantum, not trip a threshold I chose.
* **The first flat spin costing a mint and the second being free** is the same
  statement one level up: it is only true if learning itself is quantised.

**Nothing to build yet, and deliberately.** The next step is not a fifth rate
parameter but establishing what the dimension IS: what its coordinate measures,
what a quantum on it means, and what residual mints one. The sd loop is the
machinery and `DimInfer` is the precedent -- a latent dimension inferred from a
residual coupled across observed ones is exactly the shape of "these models are
all wrong together, in a way none of their individual errors expresses".

CB's flat floor stays in the meantime: measured, honest about what it is -- a
constant standing in for a dimension -- and worth its 97% until the dimension
exists.

### CD addendum — measured scope: 60 rules, 8 seeds, and a clean dividing line

Static scan of every seed for count-divided incremental learning (a `Div` whose
denominator is a count-like attribute, writing a `mean_*` or `*_ema`):

```
  60 rules across 8 seeds
    humanoid_adaptation            22     humanoid_kinematics_study   12
    embodied_motor_program          8     embodied_motor_priors        6
    humanoid_coordination_curriculum 6    aerial_adaptation            2
    embodied_adaptation             2     helicopter_autorotation      2

  seeds carrying any explicit rate concept at all: 5 of 8
```

**This is not a motor-program defect.** It is 60 rules across every embodied
faculty in the tree -- humanoid balance, kinematics, coordination curriculum,
aerial, helicopter, motor priors -- each independently reimplementing "average
what I have seen, weighted 1/n".

**And the dividing line is exact.** Not one sd-loop, shape-codebook,
spatial-quanta or conversation rule appears in the scan. Those faculties do not
average: they DECODE against a held codebook and MINT when the residual will not
fit. They have a representation, so they never needed a rate.

So the claim is measurable and it holds: **the defect appears in precisely the
faculties that lack a minted representation and fell back on a scalar.** The sd
loop is not one instance among many -- it is the only place in this tree where
learning is represented rather than approximated, and 60 rules are what its
absence looks like elsewhere.

That reframes the build target one more time. It is not "add a learning
dimension to the motor program seed", nor even "to the embodied seeds". It is
that the sd loop's decode-recognise-transform-infer-mint ladder is the general
form of learning, the embodied faculties are 60 special cases that predate it,
and the question is what a learning quantum means when the thing being decoded is
a MODEL rather than a shape.

The F-16 measurements stand as the sharp instance: 638 -> 17 by putting a
constant where a coordinate belongs, and a regress of rates-needing-rates that
only terminates when the quantity becomes a dimension.

## Block CE — what a learning quantum means for a MODEL

Worked out from the sd loop's own ladder, which already answers this for shapes.
A model's signature is its consequence vector -- `mean_forward`, `mean_lateral`,
`mean_roll`, ... -- what commanding it does. Decoding an outcome against held
models is the same operation as decoding an observation against held shapes, and
the same Occam ladder applies:

```
  rung 1  RECOGNISE   the outcome matches a held model's signature
                      -> nothing to learn.  THIS IS "the second flat spin is free".

  rung 2  TRANSFORM   the outcome is a held signature stepped k along ONE
                      dimension -- uniform delta, integer k
                      -> learn a step, not a model.

  rung 3  INFER       the residual is COUPLED across consequences in a way no
                      held dimension expresses
                      -> mint a LATENT DIMENSION.  Expensive, once.

  rung 4  MINT        genuinely novel
                      -> a new model.
```

**A learning quantum is a step along a dimension of the model's own consequence
space.** Not a nudge toward a new mean -- a decision about which rung explains
what just happened.

### The F-16 faults are literally rung 2 and rung 3

`damaged_wing` in the plant is a set of MULTIPLICATIVE scalings:

```python
    ("lift_alpha", 0.7), ("roll_beta", 0.5), ("roll_r", 0.5),
    ("roll_aileron", 0.5), ("yaw_aileron", 1.5)
```

The aircraft is not a new aircraft. It is the same aircraft scaled along several
coefficient dimensions -- and `scale2` established that **a multiplicative base
IS a dimension**, with the ratio living cross-frame and the step `k` staying an
in-frame integer. A damaged wing is a handful of integer steps on scale
dimensions the loop could already represent.

A STALL is the rung above: every lifting-surface consequence collapses together,
which is a residual coupled across observed dimensions that no per-effector
scaling expresses. That is `DimInfer`'s exact trigger -- "rotating a flat 2D
rectangle in Z gives an XY change you cannot replicate without Z" is the same
sentence as "the wing stalling gives a coupled change across every surface you
cannot replicate by scaling any of them".

### Why 1/n fails, stated precisely

**Averaging is rung-4 behaviour applied to a rung-2 situation.** A 200-sample
mean crawling toward a 0.5x coefficient is the loop slowly BECOMING a new model
when the honest reading is "same model, one step down a scale dimension". It is
not too slow by accident -- it is answering the wrong question, and no rate fixes
that. Which is why every rate patch regressed into another constant.

It also explains the measurement that has stood unexplained all session:
CB's floor bought 638 -> 17 not by learning faster but by letting recent evidence
dominate, which APPROXIMATES a step. A step is what was needed; a fast average is
the nearest thing a scalar representation can express.

### What this predicts, and how it is falsifiable

1. The residuals under `damaged_wing` should be well explained by a small number
   of multiplicative steps -- a per-consequence ratio between post-fault and
   pre-fault means clustering near the plant's own 0.7/0.5/1.5, not scattered.
2. Under a stall the same ratios should NOT separate per effector: they should
   move together, which is the coupling that mints a dimension rather than steps
   an existing one.
3. If (1) holds, a rung-2 learner would converge in ONE observation where the 1/n
   learner needs hundreds -- and the crash count is downstream of that.

Both are measurable from data already recorded, with no new simulation: the
effector `mean_*` snapshots at actions 150 and 400 that BU already dumps. **That
is the next measurement, and it tests the whole frame rather than another
parameter.**

## Block CH — Order-N, and why the baseline fix is still the wrong kind

CG raised `calibration_samples` 1 -> 2 so each member has a baseline. It measured
better and it is still the wrong SHAPE of answer, for a reason CG itself
surfaced: 37 members x 2 samples is 74 actions against a fault at 100. At x3 the
baseline never finishes. **Characterise-then-act does not scale in the dimension
that matters, because the world breaks when it breaks.**

The tree's answer to this already has a name. `Order-N growth is DYNAMIC
QUANTIZATION as graph rules`: decode against the codebook you have, and let the
RESIDUAL mint the next quantum, with `codebook_epoch` re-arming decode when the
codebook grows. **You never hold a complete prior. You hold one that grows where
it is wrong.**

Applied to models, that is CE: a learning quantum minted on residual. The first
flat spin mints, the second is free. No complete characterisation is required at
any point -- which is the only formulation that survives a fault arriving before
the baseline finishes, i.e. every real one.

### The single defect behind everything measured today

**The loop treats provisional representations as final.** Every distinct bug this
session is an instance:

| what | how it treats itself as final |
|---|---|
| crash predicate | one criterion, could not see a new failure mode |
| recalibration | fires twice at action 101, never re-arms |
| `1/n` | stationarity IS the assertion that the prior is done |
| `experience_count` | monotone; confidence in a dead aircraft grows forever |
| `calibration_samples` | "calibrated" means finished |
| the corner set | five hand-authored postures, a fixed library |
| the probe at the held ordinal | the frontier as a fixed set |
| terrain clock units | one frame, never reconciled with another |

Eight defects, one shape. That is why fixing them individually kept producing the
next one, and why every fix that stuck was a representation gaining a degree of
freedom rather than a parameter gaining a better value.

### What follows

* **Acting on incompletely adapted priors is the requirement, not the
  degradation.** A loop that can only act once characterised cannot fly, because
  characterisation is never finished. The measure of the design is what it does
  at action 101 with a two-sample prior -- not how good the prior eventually gets.
* **CG stays** -- a better baseline is strictly better and costs nothing measured
  so far -- **but it is not the fix, and the prereg should stop treating baseline
  completeness as the goal.**
* **The next build is CE's ladder for models**, and its value is precisely that
  it never needs the baseline to be complete: rung 1 recognises, rung 2 steps,
  rung 3 mints a dimension, rung 4 mints a model, and a two-sample prior is
  enough to enter at rung 2 instead of averaging from scratch.

The F-16 has been a good instrument for this because a departing aircraft is the
case where waiting to be sure is indistinguishable from doing nothing.

## Block CI — the admissibility bound is not the defect; the missing dimension is

`structural_model_admissible` rejects a model whose predicted load added to the
current load would exceed safe. In flight that excludes the high-deflection
models, so **the aggressive end of the envelope can never be characterised --
exactly the end a departure needs.** Loosening it means exercising commands that
would break the airframe, which is not a fix.

**But the bound is only crippling because of how the models are shaped.**
Measured:

```
  actuator group 0: 9 models     group 2: 9 models
  actuator group 1: 9 models     group 3: 9 models     group 4: 1 (plant)
                                                       -> 37 total
```

**The 37 members are 4 effectors x 9 command levels, held as 37 UNRELATED
models.** Command level is a dimension -- quantised, ordered, with a smooth
response along it -- and the tree represents it as an index into independent
codebook entries. `scale2` established that a base is a dimension; the command
axis never got the same treatment.

### Every coverage symptom measured today follows from that

* **Identifiability zero** (BV): 37 unknowns against ~25 equations per window.
  But it is not 37 unknowns -- it is 4 effectors with a response curve each,
  perhaps 8-12 parameters. Identifiable with the observations already available.
* **Coverage bounded at 6 tokens** (CG): admissibility excludes high-deflection
  models. If level were a dimension, exercising 0.25 would inform 1.0 by
  TRANSFORM -- rung 2 of CE's ladder -- and the safe end would characterise the
  unsafe end without commanding it.
* **Attribution ambiguity** (BV/BW): a 4-member program is 4 effectors at
  particular levels, not 4 arbitrary draws from 37.

**And it is the session's single defect again**: 9 samples of one continuous
response treated as 9 final independent facts. Provisional held as final, in the
representation rather than the parameter.

### What this makes the fix

Not "loosen admissibility" and not "exercise more". **Relate the levels.** A
model at command level c and the same effector at level c' differ by a step along
the command dimension, which is precisely what `TransformDecode` reads and
`DimInfer` mints. Then:

* what can be safely exercised constrains what cannot;
* the unknown count drops from 37 to the number of effectors times the order of
  their response;
* and a departure that pushes into never-exercised deflections is decoded as a
  step on a known axis rather than an unmodelled member.

Falsifiable cheaply and with data already recorded: **the 9 learned `mean_*`
vectors within one actuator group should be monotone and smooth in command
level.** If they are, the 9 independent models are 9 samples of one curve and the
representation is provably redundant. If they are not, the levels are genuinely
independent and this whole line is wrong.

That is the next measurement, it needs no simulation, and it tests the
representation rather than a parameter.

## Block CJ prediction — "four slopes" is four slopes AT ORDER 1

Recorded BEFORE the slope suite reports, because the correction predicts where it
should fail.

CI part 2 measured the response as exactly linear in command level and I wrote
"222 attributes collapse to four slopes". That is wrong as stated. It is **four
slopes AT ORDER 1** -- the first-order fit of a response measured only where it
happens to be linear.

**And `emp_share_slope_across_command_levels` as built asserts order 1 forever.**
It overwrites every sibling with `source_mean x level_ratio` on each learning
event, so a genuinely non-linear response cannot survive contact with it. That is
the session's defect a tenth time, in the change I just made: an order-1 fit,
provisional, held as final.

Order-N is the correction. The tree's own form -- decode against the order you
hold, and let the RESIDUAL mint the next -- means linearity is rung 1, curvature
is a minted quantum when the line stops fitting, and saturation is another. The
rule should propagate at the order currently justified and stop propagating where
the residual says the order is insufficient.

**Falsifiable, on the suite already running:**

1. **saturated_elevator should SUFFER.** It is literally a clipped command: the
   response saturates, so it is not linear in command level, and the rule will
   propagate a straight line through a knee. If it loses episodes or tracking
   against the CB arm, that is order-1 being forced through an order-2 reality.
2. Scenarios whose faults are multiplicative -- damaged_wing, damaged_tail,
   broken_aileron -- should hold or improve, because a scaling IS an order-1
   change and the rule expresses it exactly.
3. If saturated_elevator holds too, the responses are linear across the whole
   commanded envelope in this plant, and the order-1 assertion is safe HERE while
   remaining wrong in general.

Whatever the suite says, the rule needs an order guard before it can be trusted
beyond this airframe: propagate only while the residual at the propagated levels
stays within what the current order explains, and mint the next order when it
does not.

### CJ addendum — order 1 is not the compromise, it is the PRODUCT

Correcting the correction. CJ framed order-1 as a defect to be replaced by
order-N. That is backwards.

**Most things are close enough to linear, or linear WITHIN RANGES, that order 1
is the cheap path -- and collapsing order N to order 1 is what System 1 IS.**
Higher order is expensive at first and the whole point of internalising is that
you stop paying for it.

This tree already measures exactly that split, and today's numbers are the cost
of not having collapsed:

```
  system1 p99 (internalised reuse)   ~28 ms
  system2 p99 (fresh synthesis)      196,539 us .. 1,702,587 us
```

**System 2 does the order-N work. System 1 is the collapsed order-1 result.**
Every action spent in fresh synthesis is an action where the collapse has not
happened yet.

So `emp_share_slope_across_command_levels` is not a shortcut that will need
replacing -- **it is System 1 for the command axis**, and the first thing in this
line to move work from S2 to S1 rather than making S2 smarter. That is why it
produced the result it did: damaged_wing 2/3 -> 0/3 with structural 27.83 -> 0.64
is what happens when the loop stops re-deriving a line it already knows.

### Which changes the order guard from "add curvature" to "mint a range"

The guard is not a higher-order fit. It is a BOUNDARY:

* propagate order 1 while the residual at the propagated levels stays within what
  the line explains;
* where it does not, **mint a range boundary** and keep order 1 inside each
  segment;
* saturation is then not a curve to model but a knee to find -- one boundary, two
  lines, both order 1.

That is cheaper than curvature, it is falsifiable per-segment, and it is the same
machinery `space_quantize` already uses: a residual mints a refinement, per
dimension, at the grain where it is needed and nowhere else. Piecewise-linear is
order-N collapsed to order-1 with the collapse points recorded -- which is the
literal definition of a quantised dimension.

**And it predicts saturated_elevator precisely.** A clipped command is one knee:
linear below it, flat above. Under a global order-1 rule that is a straight line
through a corner and should hurt. Under a range-minting rule it is two segments
and should be exact. If the running suite shows saturated_elevator suffering,
that is not evidence against the collapse -- it is the loop telling us where the
first boundary goes.

## Block CK — what is being minted is a RELATIONSHIP, and the ledger says so

The slope is not a measurement of the response at nine levels. **It is one
ratio** -- `mean / level` -- and it needed no absolute calibration, no time base,
and no complete sample set. One observation fixes a proportion, and the
proportion carries to every level including the ones that can never be safely
commanded. That is why a two-sample prior sufficed where a two-hundred-sample
average did not.

**Today's failures were absolutes standing where ratios belonged. Every one.**

| defect | the absolute | the ratio it should have been |
|---|---|---|
| terrain clock (BG) | seconds read as actions | the action duration between the frames |
| structural price (AP/AQ) | linear in an envelope fraction | log of a ratio -- decades |
| `1/n` (CA) | a count of samples | evidence age against plant change rate |
| drive share (BO/BS) | six per-axis magnitudes | the comparison BETWEEN axes |
| 9 command levels (CI) | nine independent facts | one slope |
| `experience_count` | monotone total | proportion of evidence still valid |

**And every fix that worked was a ratio.** The slope (`mean / level`). The
manifold margin (`reach / gap`, whose docstring already says its LOG is the
decision quantity). Surprise (`error` against its own history). The
irreversibility budget (decades -- a log of a ratio). The one measured success of
the whole line, damaged_wing 2/3 -> 0/3, came from replacing 222 absolute
attributes with four proportions.

This is the frame/continuum invariant read forward rather than as a constraint:
**a ratio is a CROSS-FRAME map, never an in-frame coordinate.** Minting a ratio
is minting a map between frames. Minting a measurement is recording a coordinate,
which is why measurements go stale the instant the frame moves -- a stalled wing,
a jammed surface, an aircraft that is no longer the one that was calibrated.

### It reframes the three named quanta as relations, not corrections

CJ's failures each name a relational object, and none needs a measurement:

* **knee** (saturated_elevator) -- not "the response saturates at value X" but
  **the ratio holds up to here and a different ratio holds beyond**. Two
  proportions and the point they exchange.
* **offset** (broken_aileron) -- not "add a bias of Y" but **the ratio is to a
  shifted origin**. A relation between where zero is claimed to be and where it
  is.
* **discontinuity** (jammed_rudder) -- not "the response is 0.3 regardless" but
  **the ratio is to a different quantity entirely**. The effector has left the
  command dimension; its relation is now to nothing the level axis expresses.

None requires a scale, a unit, or a time base. Each is a comparison, and each can
be minted from a residual that fails to fit an existing comparison -- which is
what the sd loop already does for shapes.

**The design consequence:** stop trying to characterise the plant and start
minting the relations that hold within it. The plant is never fully measured, the
world breaks before characterisation finishes (CH), coverage is bounded by
admissibility (CG) -- and none of that matters to a proportion, which one
admissible observation establishes and which transfers to the levels admissibility
forbids.

## Block CL — the knee is ratio quantisation, and that collapses all three quanta into one

CJ named three failures and CK reframed them as relations. They are not three
things. **The ratio is a quantised dimension, and every one of them is a step
along it.**

A knee is not a boundary object plus two slopes. It is **the ratio being
quantised**: one quantum of ratio holds over one range of command level, the next
holds over the next, and the "knee" is nothing but where one ends. There is no
knee to detect -- there is a residual that does not fit the current quantum, and
`sd_mint_quantum` already knows what to do with that.

**All three CJ failures are the same statement:**

| CJ called it | what it actually is |
|---|---|
| knee (saturated_elevator) | the ratio takes a different quantum beyond a level |
| offset (broken_aileron) | `mean/level` VARIES across the axis, because the response is affine -- so the ratio is not one quantum |
| discontinuity (jammed_rudder) | the response is constant, so `mean/level` goes as `1/level` -- a ratio varying strongly, quantised finely or recognised as a ratio to something else |

**One mechanism, not three.** Not a boundary detector, an intercept term and an
axis-change rule -- a slope that is itself quantised, refined per range where the
residual demands it and nowhere else.

### Which is machinery this tree already has, for a different dimension

`space_quantize` quantises space per body shape, N-dimensionally, with
**per-dimension resolution and per-dimension residual splits** -- "flood does not
occur per pixel, it occurs at quanta; a remainder goes to more detail; quanta are
dynamic PER DIMENSION". `scale2` established a multiplicative base as a
dimension. `qf_refine_residual` is the refinement rung.

The command axis needs exactly that and has none of it: one global slope, no
resolution, no refinement, no per-range quanta. **The fix is the space ladder
applied to a response curve** -- and that is why the failures sorted so cleanly
by fault shape: each is a different demand for refinement on the same axis.

### The build, stated once

Hold the slope as a quantised function of command level: one ratio per range,
initialised as a single range spanning the axis (which is exactly the rule
already committed and measured at damaged_wing 2/3 -> 0/3), and split a range
when the residual inside it exceeds what one ratio explains.

* saturated_elevator splits once, at the clip.
* broken_aileron splits until the affine response is covered, or gains an origin
  shift if that is cheaper -- and WHICH IS CHEAPER IS MEASURABLE, not a design
  choice to be argued.
* jammed_rudder splits without converging, which is the loop discovering that
  the level axis no longer explains this effector -- the honest signal that the
  effector has left the dimension, arrived at rather than asserted.

Order 1 everywhere, refined where measured, with the cost of refinement paid only
where the residual demands it. **Nothing needs a measurement, a unit, or a time
base -- only comparisons and the points at which they stop holding.**

## Block CM — hold the collapse open

The rule as built re-decides the collapse every action: for every source/target
pair in a group, recompute the disagreement and re-derive whether the range still
holds. That is ~288 pairs x 19 consequences per action, and it is why three
scenario runs blew a ten-minute budget that normally fits them.

**But the cost is a symptom.** Re-deriving the collapse every action is not
expensive-but-correct, it is the wrong relationship to the collapse. A collapse
that must be re-established continuously was never a collapse -- it is System 2
wearing System 1's clothes, which is precisely the thing the collapse exists to
stop paying for.

**Hold it open instead.** The collapse stands. It is applied continuously and for
free -- one slope, one multiply. What stays open is the RESIDUAL against it: a
channel that accumulates evidence as evidence arrives, and can reopen the collapse
when there is enough of it. Not re-decided, not sealed. Held open.

Concretely, and it is a smaller rule than the one it replaces:

* the shared slope applies as now (System 1, free);
* the disagreement EMA updates **at the learning event**, where a receipt already
  arrives for that model and the prediction for it already exists -- ONE
  comparison per receipt, not a pairwise sweep per action;
* crossing the factor reopens the collapse for that model and it splits;
  falling below half rejoins it.

That is cheaper by the ratio of receipts to pairs, and it is more correct for a
reason that has nothing to do with cost: **the residual is evidence, and evidence
arrives with receipts.** Accumulating it on a schedule of its own invents
observations that were never made -- the same error as a latch with no
deactivation energy, and as an EMA that tracks nothing because it updates at 1/n.

### Why this is the general form

Every kept change in this session has this shape, and I did not see it until now:

* `cre_close_inadmissible_deliberation` -- a deliberation is not sealed by
  finding no counterexample; it closes and can reopen on new evidence;
* the rung-0 escape -- the frontier is not a fixed set, it admits what the
  situation licenses;
* the learning-rate floor -- the mean is not final, recent evidence can move it;
* the slope collapse -- 222 attributes become four, and the four are not final.

**Held open is the difference between a collapse and an assumption.** The session
found ten instances of provisional-held-as-final; the cure is not to stop
collapsing, it is to leave the residual channel attached to every collapse so it
can be undone by the same evidence that would have prevented it.

The run in flight measures the eager version. Whatever it says about hysteresis
is still worth having -- but the rule it measures should be replaced by the one
above regardless of the number, because a collapse that costs per-action is not
one.

## Measurement discipline — a statistic is only a statistic in comparison

Standing rule, arrived at the hard way and applying to this tree's diagnostics as
much as to its rules.

**A single statistic is an in-frame coordinate. It carries no information until
it is compared to something.** A median alone says how big a thing typically is,
which is unanswerable without knowing how big it could be. A median WITH a spread
is a ratio, and a ratio is a cross-frame map -- the same invariant this tree
already applies to physical quantities, applied to the measurements OF them.

Today's own record is the proof, on one dataset:

```
  reported as a median        0.95 vs 1.35        populations overlap, no decision
  reported as a ratio         0.71-1.66 vs 38.02  populations separate ~20x
```

**Same receipts. Same residuals. One framing decides and the other cannot.** The
first was two medians read as absolutes; the second was a median compared to
another median from the same data.

### The failures this explains, all of them from today

* CN's per-receipt medians -- reported bare, concluded "cannot discriminate",
  when the data could discriminate and the framing could not.
* AP's structural price -- a fraction reported and priced as a magnitude, when
  the decision quantity was its log, a ratio.
* CA's "samples are not understanding" -- prediction error reported as a level,
  when what mattered was the level against its own history.
* BU part 3's monotone max -- a statistic that cannot fall, compared to nothing,
  and therefore incapable of showing improvement.
* CO's correlation test -- worse than uninformative, structurally zero.

**Six instrument failures in one session, and this is their single shape.** Not
carelessness in each case -- a missing comparison in every case.

### The rule, stated for reuse

Every measurement reported in this line must carry its comparator:

* a median carries a spread, or a second median from a contrasting population;
* a residual carries the scale it is a residual OF;
* a rate carries the rate it is faster or slower THAN;
* a clock carries the frame it is counted in;
* an error carries its own history.

**If a number cannot be written as a ratio, it is not yet a measurement -- it is
a reading.** That distinction has cost this session four reverted builds and two
invalidated analyses, and it is the same distinction the agent itself needs:
minting relationships rather than recording values.

## The session in one line — match SHAPES, not numbers

Every number I chose today was wrong. Every shape I found was right. That is not
a coincidence and it is not luck; it is the same statement the architecture makes
in its own naming -- `ShapeDecode`, `ShapeSignature`, `sd_recognize`,
`sd_mint_quantum`. **The tree is a shape matcher, and every defect found today was
somewhere a number had been put where a shape belonged.**

**The numbers, all chosen, all wrong:**

| number | what it was standing in for |
|---|---|
| `minimum_altitude_m <= 0.0` | the shape of contact -- any part of the airframe reaching the ground |
| horizon 80 against `gap/rate` | the shape of two frames, seconds against actions |
| structural price linear in a fraction | the shape of irreversibility, which is logarithmic |
| `1/n` | the shape of stationarity, asserted where the plant was changing |
| `calibration_samples = 1` | the shape of "characterised" |
| drive share `2m - 1` | the shape of a trade between axes |
| `slope_range_split_factor = 0.25` | the shape of a relationship breaking |
| `model_surprise_factor = 2.0` | the shape of surprise |

**The shapes, all found, all right:**

* nine levels are ONE LINE -- proportionality, not nine facts (damaged_wing 0/3)
* a fault is a SCALING -- one step on a dimension, not a new model
* a stall is a COUPLED residual -- the signature `DimInfer` already mints on
* a knee is RATIO QUANTISATION -- two shapes and where they exchange
* a broken relationship is HETEROSCEDASTIC -- error growing toward the extremes,
  separating 20x where medians overlapped
* a collapse must be HELD OPEN -- the shape of a hypothesis, not a conclusion

### Why this is the rule and not an observation

A number is an in-frame coordinate: true in one frame, silently false in the
next. That is exactly how each one failed -- the crash predicate was true until
the aircraft touched down at 1.3 ft; `1/n` was true until the plant changed
basin; 0.25 was true for a pairwise comparison and false for a per-receipt one,
the same session, two hours apart.

**A shape is a relationship, and relationships transfer between frames.** That is
what made the slope work at command levels it had never been safe to command,
and what makes "the first flat spin mints, the second is free" possible at all.

**So: when the work reaches for a threshold, the question has been mis-framed.**
The question is never "what value separates these" -- it is "which held shape
does this match, and if none, what does the residual mint". Six instrument
failures, four reverted builds, and one result that worked, all agree on it.

CD measured the corollary without my seeing it at the time: 60 count-divided
learners across 8 embodied seeds, and **not one in the sd-loop, shape-codebook,
spatial-quanta or conversation faculties.** The faculties that match shapes never
needed a number. The ones that match numbers are where every defect lives.

### The reframe — shape matching is CHEAP, and that is the point

The rule is not only about correctness. **Matching shapes costs almost nothing;
matching numbers is what has been expensive.** Today's timings measure the gap:

```
  fresh synthesis p99 (search over an alphabet)   196,539 - 1,702,587 us
  internalised reuse p99 (a held shape applied)             ~28,000 us
  eager pairwise disagreement (288 pairs x 19)     three scenarios, 600 s timeout
  the slope collapse (one proportion, applied)     damaged_wing 2/3 -> 0/3
```

**The best result of the session cost one multiply.** Nine levels are one line,
so a receipt at 0.25 fixes the response at 1.0 -- no search, no optimisation, no
two hundred samples. Against that, everything expensive today either failed or
was reverted: the composer's quadratic search, the pairwise sweep, the
200-sample averages that produced no understanding (CA), the four
parameterisations of a corner.

At 10 Hz an action has 100 ms. **A departing aircraft cannot afford expensive
math, and does not need it** -- it needs to recognise that this is the same wing
it had, scaled. That recognition is a comparison, and comparisons are free.

### Which puts the expensive machinery in its proper place

The composer search, the Rust primitives, the numerical work -- **these are the
residual path, not the main one.** They are what runs when shape matching fails,
which by construction should be rare and, after a mint, rarer. `MotorCompose`
exists in Rust because the Term-tree composer cost 300-600 ms per request; the
deeper answer is not a faster search but fewer searches, because the shape is
already held.

That is the whole of System 1 and System 2 restated as an economics: **System 2
pays once, in full; System 1 pays nothing, forever after.** Every block today that
tried to make System 2 smarter was reverted. The one block that moved work into
System 1 -- the slope collapse -- is the one still standing, and it is also the
cheapest thing in the tree.

**So the design target is not a better optimiser.** It is a codebook rich enough
that the optimiser is rarely reached, minted from residuals as they arrive, held
open so it can be corrected. Cheap, incremental, and wrong only in ways that
announce themselves.

## Block CQ — a motor program is a program, and it is not a Term-tree

`MotorCompose { episode, policy, candidate }` is already a Term -- but one that
answers "is this candidate a member" by running an opaque native search. **The
program it yields is graph edges (`trial -commands_embodied_effector_model->
model`), not a Term-tree.** The module header states the split plainly: the graph
decides WHEN to compose, Rust answers the membership question.

So the program is data, the search is native, and neither is a structure the sd
loop can operate on. That is the gap, and it explains a lot of today:

* **A program cannot be RECOGNISED.** Reuse is a separate mechanism
  (`default_program_reuse`, measured at 0% during a departure) rather than
  `sd_recognize` matching a held shape.
* **A program cannot be TRANSFORMED.** "Same program, one step along a
  dimension" has no representation -- which is why the slope collapse had to be
  written by hand for effector models, as a bespoke rule, when it is rung 2 of a
  ladder that already exists.
* **A program cannot be MINTED.** Novelty is re-searched from the alphabet every
  time, at 196,539-1,702,587 us, instead of minting a quantum once and
  recognising it thereafter.

Everything the sd loop gives shapes for free -- recognise, transform, infer,
mint -- the motor path reimplements or does without.

### The objection, and why it inverts

`MotorCompose` exists BECAUSE Term-tree composition cost 300-600 ms per request
(294/82/44 ms at 8/4/2 quantization intervals, quadratic in the alphabet). Making
programs Terms appears to walk straight back into that.

**It does not, and the reason is this session's central measurement.** The
expensive part is the SEARCH, not the representation. A recognised program needs
no search -- it is evaluated, and evaluation is the cheap direction. Term-as-
program costs the old price only when something must be composed for the first
time, which is exactly System 2 paying once, and costs nothing on every
subsequent recognition, which is exactly System 1. The native search stops being
the main path and becomes the residual one.

Put the other way: `MotorCompose` optimised the wrong thing. It made the search
fast, when the win was in not searching.

### What would have to be true

* a Term that evaluates to a set of `(model, command level)` pairs -- the Term
  vocabulary already has `Vec`, `MapList`, `Filter`, `Append`;
* programs held as ShapeSignatures over that structure, so `sd_recognize` and
  `TransformDecode` apply unchanged;
* `MotorCompose` retained as the mint path -- what runs when decode finds no
  match and a new quantum is required.

**Not started, and it is a larger change than anything attempted today** -- it
touches the composer, the trial representation and the reuse path together. But
it is the first proposal in this line that would make the motor faculty a
consumer of the sd loop rather than a parallel implementation of it, and CD
already measured what that difference is worth: 60 count-divided learners in the
faculties without a minted representation, and none in the faculties with one.

## Block CR — make Term-trees cheaper, which is a win for everyone

CQ concluded that a motor program should be a Term-tree, and immediately met the
objection that Term-tree composition cost 300-600 ms, which is why `MotorCompose`
exists. **The answer is not to special-case the hot path again. It is to make the
evaluator cheap, once, for every faculty.**

`MotorCompose`'s own header names the mechanism it hardcoded:

> All per-model predictions are plan-independent, so they are computed ONCE into
> a matrix and every cost is pure arithmetic over it -- **the property the
> Term-tree composer cannot express, and the whole speedup.**

That is loop-invariant hoisting, written by hand, for one Term. **It is a general
evaluator optimisation and the tree has 8397 places that would take it:**

```
  Filter / Argmin / Argmax terms across all seeds   6308
  MaxOver / MinOver / Sum terms                     2089
```

At each of those, the body is re-evaluated per element, including subterms that
do not reference the bound variable. The evaluator carries a `shape_cache` and a
`derivations` cache but no general subterm memoisation and no hoisting.

### Why this is the higher-leverage move

* **It is mechanical and safe.** A subterm that does not reference the loop
  variable is loop-invariant by inspection of the Term tree; hoisting it changes
  no semantics. No heuristics, no thresholds -- the analysis is structural.
* **It pays everywhere at once.** Every consumer -- humanoid, aerial, helicopter,
  conversation, the sd loop itself -- iterates sets in rules. `MotorCompose` sped
  up one path for one body plan; hoisting speeds up all 8397 sites for all of
  them.
* **It removes the reason to write native special cases at all.** The precedent
  set by `MotorCompose` is "when a Term path is hot, replace it with Rust". That
  precedent scales badly: each such replacement is a faculty that leaves the
  graph and stops being decodable, transformable and mintable -- which is exactly
  the deficit CQ measured in the motor path.
* **It makes CQ affordable.** Programs-as-Terms is only sensible if evaluating a
  Term is cheap. This is the prerequisite, not a parallel idea.

### The measurement that would justify it, before any code

1. instrument the evaluator to count subterm evaluations per set-iterating Term,
   and the fraction whose subtree does not reference the bound variable;
2. that fraction IS the available speedup, per site, measured rather than
   assumed;
3. the composer's own numbers give the expected shape -- 294/82/44 ms at 8/4/2
   quantization intervals is quadratic in the alphabet, and hoisting the
   plan-independent part is what flattened it to the native version's cost.

**Not built. This is a Rust evaluator change and it needs a benchmark before a
line of it is written** -- but it is the first proposal in this session whose
benefit is not confined to the F-16, and it is the correct response to a hot path
in a graph-resident system: make the graph faster, not the path native.

## Block CS — the wider search is an ASYNC background process

The S1/S2 economics recorded earlier had a hole I did not see: "System 2 pays
once, in full" -- but *in full* meant blocking a 10 Hz control loop for up to
1.7 seconds. A deadline missed by 17x is not a payment, it is a crash with extra
steps.

**The resolution is that the wider search does not run in the action.** React
now, with whatever shape is held -- 28 ms, order 1, possibly wrong at the edges.
The order-N search runs BEHIND that, over accumulated residuals, on its own
clock. When it finds something, the codebook grows and the next reaction is
better. **"Oh, this is like that" arrives late, and late is fine, because the
aircraft did not wait for it.**

This is how the deadline stops binding at all. Today's numbers stop being a
problem to optimise and become a scheduling statement:

```
  react   ~28 ms   inside a 100 ms budget, always
  search  196,539 - 1,702,587 us   behind it, never in it
```

### The machinery is already there and this is what it is for

`codebook_epoch` re-arms decode when the codebook grows -- `sd_decode` /
`sd_recognize` / `sd_mint_quantum` / `sd_redecode`, with the epoch bump as the
signal that what was unrecognisable a moment ago may be recognisable now.
**That is precisely an async-mint hook**: it does not require the mint to have
happened in the same fixpoint as the decode that failed. The loop can decode,
fail, act on the residual anyway, and re-decode later when the epoch moves.

What is missing is not the hook but the discipline of using it: today's motor
path composes synchronously and blocks, because `MotorCompose` was built to make
the blocking call fast rather than to remove it from the action.

### What follows for the three open proposals

* **CQ (programs as Term-trees)** -- recognition is the fast path and lives in the
  action; composition is the mint and belongs behind the epoch. The split falls
  out naturally once programs are shapes.
* **CR (cheaper Term evaluation)** -- still worth it, and its priority drops. If
  the search is off the critical path, making it 3x faster matters less than
  making the reaction correct. **Hoisting helps the async worker; it is no longer
  the thing standing between the loop and its deadline.**
* **The residual channel** built today (CM/CP) is exactly the queue such a worker
  would consume: per-model disagreement, accumulating unconditionally, already
  held open.

### The honest caveat

This tree runs one `run_rules` fixpoint per action; there is no worker, no queue,
no epoch scheduler. **Async here means "not in this action's fixpoint", which is
a real architectural change and not a flag.** The pieces -- residual
accumulation, `codebook_epoch`, mint-on-residual -- exist and were built for it.
Nothing yet drives them from outside the action, and that is the gap.

### CS addendum — the async hook is not hypothetical, it is already how shapes work

Checked the sd loop's own description rather than inferring it:

> codebook growth (**`grow_part_library` bumping `agent.codebook_epoch`, Python
> builder**) re-arms decoded/recognized-transformed observations via
> `sd_redecode`

**The epoch is bumped from OUTSIDE the rule fixpoint, by a builder, and decode
re-arms on the next pass.** That is the async pattern in production for shapes
today -- react on what is held, grow the codebook on another clock, re-decode
when it grows. v1.8.0 extends it: `GenInfer` discovers a new linear generator,
mints it as graph data, bumps the epoch, and the orbit collapses to one generator
on re-decode.

So CS overstates the gap. The tree does not lack the mechanism; **the motor path
is the faculty that does not use it.** Shapes react-then-recognise-later already.
Motor programs block on a synchronous search because `MotorCompose` was written
to make that search fast rather than to move it off the action.

That makes the change smaller than CS implied and more clearly correct: not
"build an async architecture" but "give the motor path the same epoch discipline
the shape path already has". The residual channel from CM/CP is the queue, the
epoch is the signal, `sd_redecode` is the re-arm, and `MotorCompose` becomes what
the builder calls when a residual needs a new program -- behind the loop, not
inside it.

## Reflexes are ORDER 0 — and that makes the whole ladder one axis

The rungs are not three different mechanisms chosen by a clock. **They are one
mechanism at different ORDERS**, and the time available selects which order you
can afford:

```
  order N   SEARCH      compose from the alphabet          expensive, needs time
  order 1   RATIO       apply a held slope, one multiply    cheap, needs a match
  order 0   REFLEX      observation -> program, directly    free, needs nothing
```

**Order 0 is the terminal collapse.** Order N collapses to order 1 -- that is
what System 1 IS, and it is what the slope collapse did, measured at
damaged_wing 2/3 -> 0/3 for the cost of one multiply. Order 1 collapses to
order 0 when the mapping is so well established that no relationship needs
computing at all: not "apply the ratio", just "this, then that".

### Three things follow immediately, and they are not stylistic

**1. A reflex has no parameters, so it cannot be mis-fit.** Every defect this
session came from a relationship being wrong -- a slope shared too widely, a
threshold carried across frames, a rate asserting stationarity, an order-1 fit
forced through a knee. Order 0 has no relationship to get wrong. That is why it
is safe to fire without confidence, and why "no time to think" is not a
degradation but a rung.

**2. The time ladder and the order ladder are the same ladder.** Earlier this was
recorded as "orders and confidence" selecting a rung; the sharper statement is
that the margin in orders of magnitude selects the ORDER OF MODEL you can afford
to evaluate. `regime_actions_to_act` does not choose between mechanisms -- it
reads off which order fits in the time.

**3. It explains why the reflex must not resolve the concern.** An order-0 mapping
carries no model of WHY it worked. Catching the arrow teaches nothing about the
archer. So a reflex firing cannot discharge the question -- there is nothing in
an order-0 response that could have answered it. The held-open discipline is not
an extra rule bolted on; it is what order 0 means.

### And it names the missing collapse

The tree collapses order N to order 1 (the slope, once shared). **Nothing
collapses order 1 to order 0.** There is no mechanism by which a ratio applied
often enough, always with the same outcome, becomes a direct mapping that skips
the multiply. That is the reflex-formation path, and its absence is why the seed
now has a reflex rung with nothing to put in it: reflexes here would have to be
authored as seeded priors, when the interesting ones are the ones that CONDENSE
from repeated order-1 success.

The motor codebook landed today is the prerequisite for measuring that -- 35
shapes over 300 actions, ~84% redundancy. A shape recognised over and over with
an unchanging outcome is exactly a candidate for order-0 condensation, and until
today there was no codebook in which to notice it.

### Correction — order 0 is INVOLUNTARY, so it is not on the time axis at all

The previous entry said the time margin selects the order. That is wrong at the
bottom rung. From the creator: **"order 0 reflexes are involuntary and driven by
specific surprise shapes."**

Two corrections, and the second is the substantive one.

**1. Involuntary means not selected.** There is no decision point where the loop
weighs order 0 against order 1 and picks it because the clock is short. A reflex
fires because its stimulus matched. It is not the cheapest option chosen under
pressure; it is not an option. That is what "fires automatically" was reaching
for and this states it exactly -- and it is why putting `fire_reflexes` behind a
method the consumer must call is not merely inconvenient but wrong in kind.

**2. The trigger is a SURPRISE SHAPE, not a shortage of time.** The stimulus is
not "any observation" and not "the margin is small" -- it is *this particular
shape of mismatch*. So order 0 is not the bottom of the time ladder. It sits
beside it:

```
  INVOLUNTARY   order 0   fires on a matched SURPRISE SHAPE, whatever the clock says
  VOLUNTARY     order 1   apply a held ratio          } the time margin selects
                order N   compose from the alphabet   } between THESE
```

The clock chooses how much thinking you can afford. It does not choose whether
you flinch.

### What this makes the reflex index

A reflex is `surprise shape -> program`, so the thing it is keyed on is the shape
of the RESIDUAL, not the shape of the observation. That lands on machinery this
session already built and measured:

* the residual channel (CM/CP) accumulates per-model disagreement unconditionally
  and is already held open -- it is the surprise signal;
* CS2 measured that its SIGNED form carries bias where the absolute form carries
  only scatter, so "a specific surprise shape" is distinguishable from noise, at
  3.42 against 0.80 on the two populations tested;
* the motor codebook (CT) gives the response side -- 35 held shapes over 300
  actions -- so both halves of `surprise shape -> program` now have an index.

**What is missing is the mapping between them**, and it should CONDENSE rather
than be authored: a surprise shape that has repeatedly been followed by the same
program, with the same outcome, is an order-0 candidate. That is the order-1 ->
order-0 collapse named in the previous entry, now with its trigger identified --
not "a ratio applied often enough" in the abstract, but a surprise shape whose
response never varies.

Nothing here is built. But the two indexes exist as of today, the surprise signal
is measured and signed, and the collapse has a definition sharp enough to test.

### Reflexes are TRAINED — which settles that condensation is the mechanism, not a nicety

Human lived experience proves it: you can train your reflexes. A block, a
catch, a recovery — deliberate first, skilled later, involuntary in the end. That
progression is not an analogy for the order ladder, it IS the order ladder,
traversed downward by practice:

```
  order N   think it through          deliberate, slow, correct
  order 1   apply the pattern         skilled, fast, still computed
  order 0   it happens without you    involuntary
```

**So order-0 content is overwhelmingly LEARNED, not seeded.** Innate reflexes
exist and are real, but they are the small set. The ones that matter to a
competent agent are the ones it condensed from its own repeated success — which
means a reflex codebook that can only be authored is the wrong shape, in exactly
the way a motor codebook that could only be authored was (CT: 35 shapes minted
from flight, none of them written by hand).

Three things this fixes in what was recorded above:

* **The condensation path is not speculative.** The previous entry called
  order-1 -> order-0 "a missing collapse". Training is the existence proof that
  it is the normal case, not an optimisation.
* **The reflex index must GROW, like every other index here.** `motor_reflex_
  buy_time` shipped today as a seeded prior with an absent stimulus, which is the
  authored kind. The trained kind needs the same mint-on-evidence treatment the
  motor codebook just received.
* **And it must be able to decay.** A trained reflex that is no longer right has
  to be untrainable, or the agent is welded to its own history — the same
  activation/deactivation asymmetry recorded for latches, and the same held-open
  discipline. A condensed reflex is a collapse, and collapses stay open.

The measurable form, with both indexes now in place: **a surprise shape whose
response has not varied over N encounters is a candidate for condensation; a
condensed reflex whose outcome starts varying is a candidate for release.** Both
are ratios over the codebook's own history, which is the only form this session
found that survives contact with a second scenario.

## Block CU — condensation: the order-1 -> order-0 collapse, built and measured

Five rules in `embodied_motor_program` v1.14.0 (40 rules), the mechanism the
previous three entries specified. Gates: `tests/test_reflex_condensation_
migrated.py` 6/6; standing suite 39/39; neighbouring motor suites 63 passed,
10 skipped.

**What was built.** A surprise-shape index keyed on the SHAPE OF THE RESIDUAL —
the join between the residual channel and the motor codebook that the reflex
entry named. `emp_index_surprise_shape` mints a bucket the first time it is
seen; `emp_count_stable_surprise_response` and `emp_vary_surprise_response`
carry its whole history in one integer, `stable_run`;
`emp_condense_surprise_reflex` collapses order 1 to order 0 at N unvarying
encounters; `emp_release_condensed_reflex` puts it back when the response
starts varying. Both parameters are absent-inert, so the faculty is off for any
agent that does not declare them.

**Measured on one nominal episode (998 actions):**

| | |
|---|---|
| surprise shapes | 11 |
| stable-run length | max 27, mean 6.7, singletons 1/11 |
| condensed at end | 1/11 (ordinal 1, run 27) |
| released at end | 2/11 |
| order-boundary transitions | 7 |

The cycle runs unprompted in flight: shapes condense, vary, release, and
re-condense, seven times over one episode. That is the trained reflex with
decay, which is what "you can train your reflexes" asks for.

**Honest reading.** Only one shape is condensed at the end, because N=20 is
high against a mean run of 6.7 — most shapes never reach the threshold. N was
declared before the run and is NOT retuned here; it is a measurement, and the
distribution it produced is the thing to tune against next.

**FOUR DEFECTS, ALL FOUND BY MEASUREMENT, NONE BY READING THE SEED.** Each is
now asserted directly in the gate, because each was invisible in a green tree:

1. **The ordinal was linear.** `relative_normal_load_error` runs 0.21 to
   1_591_707 over one episode — it divides by a predicted load that passes
   through zero. Quartering that gives ~6.4M buckets: one shape per encounter,
   an index that has learned nothing. This is the failure the session's own
   rule names — it was matching a NUMBER. The log collapses seven orders of
   magnitude into ~15 buckets that recur, and the invariant holds exactly as
   written: the log is the cross-frame map, the integer `k` is the in-frame
   coordinate.
2. **A Float attr recompared against an Int never matched.** Stored ordinals
   read back as Floats; `IDiv(x, 1)` is the coercion, and it is the same idiom
   `motor_program_member_relation` already documents.
3. **The response identity was a serial number.** `motor_program_shape_name` is
   `emp_program_<internalized_epoch>_<member_count>`, so a fresh instance of an
   identical program gets a different name and every re-encounter read as
   varied. Symptom: 16 shapes, every run 1, epoch 0 — a faculty that had
   installed cleanly and could never fire. The comparison is now over the
   program's SIGNATURE.
4. **`P0` cannot compare a String.** `P0` is `Plus(Attr, 0.0)` — the
   first-class-absence idiom for NUMBERS. On a String it never compares equal,
   which silently forced the vary branch on a byte-identical program. `A` is
   correct here, and its absence polarity is right too: an unset response is
   equal to nothing, so it restarts the run rather than extending it.

**And one design defect the bench caught that flight had hidden.** The
encounter chain bound every past trial of the episode, so when a new residual
bucket first appeared, every binding passed the mint guard against the same
pre-pass graph: the index gained three or four entries for one shape (flight
showed this at ordinals 1, 12 and 14). It cannot be cleaned up afterwards —
duplicates share an ordinal, so the recur rules increment all of them in
lockstep and no attribute ever separates them. The fix is at the mint:
outcomes carry the episode's `program_request_seq`, so requiring equality binds
the current action alone. Shapes went 16 (fragmented) -> 11 (clean).

**A refuted hypothesis, recorded because it cost a run.** I predicted that an
edge type must be a declared production to be matchable, and that this was why
the recur rules never fired. Adding the production changed the output
byte-for-byte. The production is kept as correct hygiene; it was not the bug.

**Residuals, named.** `MapList` preserves neighbour order, so two programs with
the same relation system enumerated differently serialise differently and read
as varied — conservative (it can miss a condensation, never invent one), but
real. The three gaps from the reflex entry are untouched: no response executor
for `motor_reflex_buy_time`, reflexes still do not fire automatically in the
engine cycle, and `program_cost` still cannot express "select because it
extends the margin". Condensation grows the index; it does not yet make the
index fire.

## Block CV — make them fire: order 0 in the engine cycle, response as a rule

The reflex rung had three named gaps. Two are closed here. Gates:
`tests/test_reflex_condensation_migrated.py` 11/11; flight suites 46/46;
motor/adaptation suites 104 passed, 8 skipped.

**The gap was structural, not a missing call.** A Reflex carried a response
NAME, and the host looked that name up in a Python dict of callables. So a
reflex could only fire where Python chose to call `fire_reflexes` — which the
flight loop never does, because `tick()` is `run_cycle("default")`. The reflex
shipped installed and unreachable. Worse, the response being a callable is the
architecture rule's own failure case: **an order-0 response the agent cannot
see is one it can never learn to change**, which is exactly what the training
argument says it must be able to do.

**What was built, in the engine.** A reflex marked `autonomous` fires inside
`cognitive_cycle::execute`, at the TOP of the cycle, before a single rule is
matched — on every plan, because involuntary cannot mean "on the plans the host
picked". The two dispatch paths are made totally disjoint in Rust: the host
loop skips autonomous reflexes and the engine pass skips host-dispatched ones,
so nothing fires twice and absent `autonomous` reads 0. The engine links
`agent -has_fired_reflex-> reflex` once, because a rule cannot match a node no
edge reaches.

**And the response is a rule.** `next_ready` already stamped `fire_count`
before returning — that stamp IS the response channel. The engine does not need
to know what a reflex MEANS, only that it fired;
`emp_enact_motor_reflex_buy_time` reads the stamp and supplies the meaning.
Nothing outside the graph is involved in firing or in responding.

**Arming is the surprise shape.** `motor_reflex_armed` was always the right
hook; it shipped inert because nothing set it, and nothing COULD, because there
was no index of surprise shapes to set it from. `emp_arm_condensed_reflex` arms
when the residual this action falls into a bucket the agent has already
condensed. Arming is a rule in the settle; firing is the engine at the top of
the next cycle. The one-action gap is the point: the reflex acts at the START
of the next action on what the last one told it, instead of waiting for the
fixpoint it exists to pre-empt.

**Measured on one nominal episode (998 actions):**

| | |
|---|---|
| reflex fires (engine) | 27 |
| enactments (the response rule) | 27 |
| host calls involved | 0 |

The two numbers matching is the end-to-end check: every engine firing was
picked up and enacted by the graph.

**What the index refused to condense is as interesting as what it did.** With
the log ordinal corrected, the bucket histogram over the episode is
`{0:59, 1:155, 2:414, 3:35, 4:9, 5:18, 6:3, 11:1, 12:2, 13:275, 14:27}`.
Bucket 2 is the most common surprise in the episode by far — 414 encounters —
and its stable run never exceeded 3, so it never condensed. Frequency is not
stability, and the index does not confuse them. Bucket 1, at 155 encounters,
reached a run of 27 and condensed.

**Residuals, named and measured.**

* **A 50% duty cycle.** The arm rule and the enact rule both run in the same
  settle, so arm-then-disarm and fire alternate: the reflex fires on every
  OTHER action while a condensed surprise persists. Measured, not inferred.
  Fixing it means gating the stimulus on arm freshness rather than disarming,
  which needs the stimulus to compare against the episode's current action seq
  — a change to the stimulus Term, not to the mechanism.
* **The third gap is still open, and it is the one that matters.** Nothing
  consumes `motor_reflex_held_seq`. The reflex fires, and the time it buys is
  not yet spent, because `program_cost` still cannot express "select because it
  extends the margin". Firing is real, involuntary, graph-native and measured;
  ACTING on it is the next rung.

## Block CW — the price of time: program_cost expresses the margin

Gates: `tests/test_margin_price_migrated.py` 4/4; flight + reflex suites 54/54.

**The instrument was checked first, and this time it is the right one.**
`probe_selection_attribution.py` on nominal: **976 of 977 admissions by
`native(MotorCompose)`**, 1 by calibration. Unlike the allocation corner, the
composer's cost really is the deciding path.

**What was missing.** Every term in `program_cost` prices the STATE a program
produces — goal residual, drag, energy, activation, authority. None can say
"take this one because it buys more time", so a candidate worse on the goal
could never win however short the budget got. A reflex buys time and the
composer had no way to spend it.

**The shape is a ratio, deliberately not a linear ramp.** Urgency is
`margin_reference_actions / margin_actions`: ~0 when the budget is long,
growing without bound as it closes — a hyperbola in time-to-go, which is the
actual shape of closing in. A linear penalty prices the last ten actions like
the first ten, and the last ten are the only ones that matter. In-frame the
margin is an integer count of actions; the ratio is the cross-frame map that
turns it into a weight, exactly as the invariant requires.

**Measured on damaged_wing (1000 actions):** 4.9% of actions at margin 0,
24.6% at the 1024 no-region fallback, **705 with a live budget** (median 163),
of which **204 sit inside the horizon at urgency > 1**. The term is live and
bites on about a fifth of the episode.

**THERE IS NO MARGIN OF ZERO.** An earlier version floored the divisor at one
action so that zero became maximum urgency. That is a category error, corrected
in place: at zero it is too late, which is a different STATE and not a larger
weight. The escape path answers there (`authority_escape` /
`f16_propose_viability_escape`, via viability rung 0). Pricing it would also be
actively harmful — it would keep the composer choosing between programs at the
exact moment its job is to stop choosing and go. Fixing this also fixed the
real defect the floor was hiding: absent and zero read identically through
`P0`, so the faculty is now gated on the POLICY declaring it, and the episode
only supplies the value.

**"BAD" IS NOT A PROPERTY OF THE OUTCOME.** If you are a plane, crashing into
the ground is bad; if you are a kinetic payload, it is your entire reason to
exist. The physics is identical and only the declared sense differs. The region
contract already carried this (`region_sense`: +1 reach, −1 avoid) and states
it outright — *"reaching a goal and being reached BY a threat are the same
closure"* — but `margin_actions` shipped as an UNFILTERED `MinOver`, which
reads every region as a threat. Correct for this airframe today only because
terrain is the only region declared, so the bug was LATENT rather than absent:
the first `region_sense: +1` goal region would have made the composer price
arriving at its own objective as an emergency and climb away from it. The
margin is now a min over avoid-regions only. Time until something you must
reach is progress, and the goal residual already prices that.

**The block, reported as a pair and ranked by nothing.** Tracking error and
margin are incomparable objectives; `cognitive_pareto` refuses to scalarize
exactly this, so a verdict here would be doing by hand what the faculty
declines to do. Whether a trade is worth making is a decision against a
declared objective basis.

| scenario | ground contact | alt RMSE (ft) | hdg RMSE (deg) | spd RMSE (fps) |
|---|---|---|---|---|
| damaged_wing | 1/3 | 6664.4 | 116.54 | 137.27 |
| saturated_elevator | 0/3 | 4657.9 | 12.79 | 150.99 |
| jammed_rudder | 0/3 | 2996.9 | 53.66 | 64.29 |

**And the delta is NOT a result.** Ground contact on damaged_wing moved 2/3 to
1/3 — that is ONE episode at n=3, and this file's own standing rule says deltas
within ~3× the per-episode step are not results. It is recorded as a
measurement, not as an improvement, and it is not evidence the term helps. A
powered gate is what would settle it.

**Residual, named.** `terrain_clear` still reads the UNFILTERED MinOver. It is
the same latent hardcoding, it is pre-existing, and changing the viability
ladder's input needs its own measurement rather than being bundled into this
one.
