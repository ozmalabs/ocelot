# Metastable regime escalation

## The gap, observed twice in one week

A controller relates to a metastable condition only through evidence
events that occur inside it, so it cannot see that it is outside:

- **F-16 jammed rudder** (`jsbsim_f16_paper_replication`): the outer loop
  encodes a fixed point — zero sideslip, yaw at the reference heading —
  that does not exist once the rudder is held at +15 degrees.  All three
  authority-model probes (`jam_authority`, `jam_prior_invalidation`,
  `jam_authority_receipt`) completed their recalibration cycles and still
  crashed at the 100 s horizon: the effector model was never the problem;
  the objective re-aimed every cycle at an infeasible attractor.
- **Humanoid coordination epochs 16–18**: the graph selected the running
  gait attractor with a freshly minted residual regime and produced three
  byte-identical inert episodes (directed progress −0.00423 m to full
  precision, zero support alternations).  Every learning channel —
  window samples, verdicts, q-updates, curriculum receipts — is gated on
  support-cycle events, which only occur inside the gait limit cycle.
  Trapped in the standing fixed point outside the basin, the runs
  generated no receipts, so nothing ever changed.

The two are mirror images of one missing capability: the F-16 seeks a
fixed point that does not exist; the humanoid sits in a fixed point that
exists but is not the goal.  In both, the absence of expected evidence
was invisible to every channel that could have escalated.

## The general process (`seeds/control_regime_escalation.json`)

Two rules, mirroring `impasse_escalation`'s order-N ladder at the
control grain, matched on `agent -holds_control_regime-> regime`:

1. `cre_note_regime_evidence_absence` — **expected-evidence absence is a
   first-class residual**.  When the regime's clock outruns its evidence
   seq by more than the declared horizon, a `ControlRegimeImpasse`
   {kind: evidence_absence} is minted and escalation is requested.
2. `cre_escalate_regime` — the residual climbs exactly one rung of the
   consumer-declared ladder (`regime_ordinal` up to
   `regime_max_ordinal`), opening a fresh evidence window for the new
   rung.

Per the arc5 exact-first precedent (program-synthesis worktree,
`ec41d3001c`: propose from a held shape, never search), escalation is an
O(1) rung selection on a ladder held as data; the alternative regime is
proposed from held structure — the opposite of re-running the same
calibration/synthesis search against an infeasible target.

The domain declares what counts as evidence (bumping
`regime_evidence_seq`), what each rung means, and the horizon.  The
general seed decides only absence and climb.  The mechanism is opt-in
(`regime_monitor_enabled`), and the contract attrs are documented in the
seed generator (`scripts/gen_control_regime_escalation_seed.py`).

## The F-16 consumer (`f16_flight_path_control` v1.2.0)

Evidence: a progress RATCHET (a new best joint tracking error in
settling-band units) or band residence, reset at every reference change.
An oscillating-but-diverging controller stops producing evidence once
its early-transient best is reached — exactly the jammed-rudder
signature.  Horizon: 5 s.

The ladder:

- **Rung 1 — metastable steady-sideslip trim.**  The yaw-attitude drive
  is retired (heading via bank alone), the lateral objective becomes a
  slow follower of the observed lateral flow (the trim tracks the
  emergent equilibrium rather than fighting it), and the validated
  departure-protection machinery from `jsbsim_f16_departure_recovery` is
  armed (yaw-rate entry raised above the jam-orbit's steady ~0.4 rad/s
  so the orbit is not misclassified as a spin).
- **Rung 2 — the steady orbit.**  Measured on the rung-1 probe: the
  jam-induced turn rate (~20 deg/s) exceeds the bank-clamp steering
  authority (~5 deg/s), so absolute heading is uncontrollable — the
  error sweeps the circle and chasing the wrap at maximum bank bleeds
  lift into a descent.  Rung 2 honestly retires absolute heading:
  wings-level roll target, altitude and airspeed kept, evidence
  re-scoped to what the rung still promises.

One further finding en route (`f16_departure_pitch_priority_override`):
the departure-recovery benchmark's own lesson — *body pitch is not angle
of attack when the flight path itself is falling* — recurs one level up.
With the flight-path loop running above it, the growing altitude error
demanded pitch-up and overpowered the alpha-recovery, holding the
airframe in a quasi-stable alpha≈35° spiral descent.  While departed,
the distal pitch pull is neutralised so alpha recovery owns the pitch
axis; the altitude loop resumes at departure exit.

## Measured result (seed 241102975, 10 Hz, 100 s, the probe protocol)

| Probe | Crash | Extreme rates | Max |rate| rad/s | Max structural util | Min altitude ft |
|---|---|---|---:|---:|---:|
| jam_authority (pre) | yes | yes | ~8.9 | — | — |
| jam_prior_invalidation (pre) | yes (ground) | yes | ~8.9 | — | — |
| jam_authority_receipt (pre) | yes | yes | ~8.9 | — | — |
| **metastable_probe_v4** | **no** | **no** | **0.65** | **0.64** | **2,025** |

Timeline of v4: fault 10 s → escalation + trim at 15.9 s → orbit at
26.6 s → departure-protected descent transient → descent arrests at
617 m (~86 s) → wings toward level, alpha 13°, climbing back toward the
altitude reference at episode end.  Heading RMSE (99°) is the honest
price of rung 2: heading was retired, not failed.  Nominal 100 s is
byte-identical to the pre-change controller (324.33 ft / 13.30° /
4.79 ft/s, settling 39.1 s) with zero escalations — the monitor does not
touch healthy flight.

Intermediate probes preserved: `..._jam_metastable_probe_v1.json`
(rung 1 only: yaw windup fixed, killed by heading-chase descent),
`..._v2.json` (rung 2 without departure protection: deep-stall entry
during the transition), `..._v3.json` (departure protection without
pitch priority: the altitude loop held it in the stall).  Each variant's
failure is what motivated the next rule; none is dead code.

## Eight-scenario 40 s gate (one seed each,
`results/jsbsim_f16_paper_replication_10hz_metastable_gate_v1.json`)

All eight scenarios remain crash-free and nominal is byte-identical with
zero escalations.  Every faulted scenario escalated to rung 2 inside the
40 s window (escalation actions 97-173).  Deltas vs the pre-change gate
are mixed at this horizon: damaged-tail heading RMSE 80.6 -> 30.6 deg
and damaged-wing peak rates 2.71 -> 1.93 rad/s improve; shifted-CG
(2,984 -> 4,210 ft alt, 21.4 -> 42.3 deg heading) and
saturated-elevator altitude worsen; jammed-rudder is similar at 40 s and
only shows its win at 100 s.  The 40 s window prices the rung
transitions but not the long-horizon recovery they buy.

## Rung-2 uncontrollability guard (`f16_flight_path_control` v1.3.0)

The eager-escalation residual, resolved before the full matrix: orbit
adoption is now gated on the MEASURED uncontrollability criterion — a
4 s-followed body yaw rate (`f16_track_yaw_rate_ema`) exceeding 1.5x the
bank-clamp steering authority g*tan(phi_max)/V.  The margin matters: a
commanded turn at the bank clamp realises EXACTLY the achievable rate,
so the bare criterion sits on the normal turning operating point.
Evidence re-scoping keys on actual adoption
(`flight_path_orbit_active`), not ladder position, and the
`orbit_regime_action` metric was corrected to read adoption rather than
`regime_ordinal` (the earlier gate tables' "orbit" column overcounted).

The 10-seed pre-flight (jammed_rudder + nominal, 100 s,
`..._preflight_10seed_v1.json`) then caught two problems single seeds
had hidden, each fixed and re-gated:

- **Nominal escalated on 9/10 seeds** (37–100 s): the in-band evidence
  arm (3.0 band-units) was tighter than the controller's honest cruise
  steady state, so once each reference-change ratchet exhausted,
  evidence starved on healthy flight.  Band residence now means
  BOUNDED-AND-STABLE: 8.0 units (6.0 under orbit); divergent fault
  regimes sit at 20+ units and still starve.
- **Jam seed 241102984 passed 4 ft off the floor**: its flight condition
  kept the yaw-rate EMA under threshold for 20 s of rung-1
  heading-chase descent.  Orbit adoption gained a BEHAVIOURAL fallback:
  heading evidence still starving 2x the horizon after reaching rung 2,
  with the heading error itself large (>0.35 rad) — so an
  altitude-transient starve (saturated elevator, shifted CG, whose
  headings sit near band) does not trigger it.

Final guarded 40 s gate (`..._metastable_native_gate_v7.json`, all
crash-free): nominal never escalates; orbit adopts ONLY for jammed
rudder (354) and damaged wing (311); vs the pre-ladder controller,
damaged-tail 80.6 -> 29.6, broken-aileron 10.0 -> 8.0,
saturated-elevator 24.2 -> 23.5, shifted-CG 21.4 -> 22.3, landing-gear
28.3 -> 32.7 (the rung-1 yaw-attitude retirement's residual cost),
damaged-wing 46.7 -> 81.4 buying peak rates 2.71 -> 1.68 rad/s.

## No magic numbers, only relative ones (`control_regime_escalation`
v1.1.0, `f16_flight_path_control` v1.4.0)

The powered matrix's failures traced to absolute constants, so the
contract was rebuilt on ratios of each regime's own dynamics:

- **Absence is an urgency-weighted integral, engine-general.**
  `cre_integrate_evidence_absence`: each evidence-less tick adds
  `regime_urgency` — the consumer's dimensionless divergence (current
  error over its own band-floored best; absent -> 1.0, exactly the old
  fixed-horizon semantics for every other consumer).  A regime
  diverging at 10x its best escalates in a tenth of the window; the
  damaged wing (inverted in half the old fixed window) escalates 3.7 s
  after onset instead of 7.7.  The integrator's reset is
  order-independent across areas (evidence credited against its own
  previous clock — measured: same-tick comparison silently never reset
  because the area scheduler runs the general seed before the consumer).
- **The window derives from the loop it monitors**: heading tau
  (8 s -> 80 actions at urgency 1), never a bare duration.  The yaw-EMA
  and trim-follower taus are ratios of the same constant.
- **Evidence arms are ratios of the regime's own best** (new best =
  0.9x itself; holding = within 2x itself), floored at the JOINT
  PUBLISHED SETTLING BAND in the metric's own construction (one unit
  per counted axis: 3.0, or 2.0 under orbit) — a best tighter than the
  band must not sharpen the monitor below the band (measured: a
  0.3-band initial capture escalated every scenario pre-fault without
  the floor).
- **The Negev F-15 move** (`f16_speed_priority_on_authority_loss`):
  control authority scales with dynamic pressure, and past 90 degrees
  of bank the lift vector no longer supports the aircraft — geometry,
  not tuning.  While departed or rolled past that boundary under an
  escalated regime, the forward axis demands its full declared
  acceleration authority (the 1983 single-wing F-15 recovery: full
  afterburner until fuselage lift and restored surface authority made
  attitude recovery possible).  Condition-scoped, not one-way.

40 s gate v10 under the relative machinery: all crash-free, nominal
never escalates, broken-aileron and landing-gear recover without even
using the ladder (urgency-patience), escalations are strictly
post-fault (137-167), orbit only for jam (221) and wing (160).

## Render-first System 2 (`embodied_motor_program` v1.6.0, opt-in)

The arc5 exact-first move applied to the motor composer itself.  Premise
measured before building: search-path System-2 p99 scales ~quadratically
with the candidate alphabet (294 / 82 / 44 ms at 8 / 4 / 2 quantization
intervals) — the cost is per-binding re-evaluation of global Argmins
whose `program_cost` is itself O(models).

The render path (`render_first_composition_enabled` policy flag; four
rules: mark → open → attach → close, one fixpoint pass): each actuator
group independently selects the command level whose own receipt-learned
consequence best matches the target, via the O(1) `singleton_cost` —
propose from the held linear models, never search compositions.  The
program lands in the existing decision-collapse / trial / learning /
internalisation machinery unchanged.

Measured (nominal, 20 s, 10 Hz):

| quantization intervals | search p99 | render p99 |
|---:|---:|---:|
| 8 | 294 ms | **27 ms** |
| 4 | 82 ms | 57 ms* |
| 2 | 44 ms | 28 ms |

(*run-to-run noise; render is alphabet-flat — the quadratic scaling is
gone, which is the property the 100 Hz roadmap items need.)

Nominal 100 s under render: 321 ft / 13.2 deg / 4.9 ft/s, settling
38.8 s — within noise of the search controller (324 / 13.3 / 4.8,
39.1 s), zero escalations.

**The regime decides its System-2 mode.**  Render-composed programs
degraded the jammed-rudder fault case (min altitude 2,025 ft -> 4 ft):
per-group proposal ignores cross-group coupling exactly where coupling
matters most and the models were just re-identified.  The fix is the
suspension contract: `f16_adopt_metastable_trim` sets
`render_first_suspended`, so the escalated regime falls back to the
plan-aware search composer ("bins propose, continuous decides" applied
to composer selection).  With suspension, the 100 s jam probe survives
with margin better than the search-only v4 (min altitude 2,348 ft, max
rates 0.68 rad/s, structural utilization 0.68, envelope clean —
`..._jam_metastable_render_probe_v2.json`; the v1 render probe preserves
the unsuspended failure).  The jam episode's p99 (669 ms) sits in its
post-escalation search phase — the honest price of the fallback; async
System-2 publication (improvement-order item 2) is the follow-up that
removes it.

Known flake, not from this work: `test_jsbsim_f16_coupled...
system1_reuse_latency p99 < 1000 us` measured 1,227 us on the EXACT
pre-change state that had passed earlier the same day — the bound is
environmentally borderline on this machine.

## Asynchronous System-2 publication (v1.7.0, opt-in, measured NEGATIVE
on wall-clock — disabled by the F-16 runner)

Improvement-order item 2 implemented at the seed layer:
`emp_async_release_trusted_default` serves the action at System-1 cost
from an epoch-trusted default (trust epoch raised at fault arm AND at
regime suspension, so neither pre-fault nor calm-phase-render defaults
are ever served into a fault window), the search build proceeds across
requests on the existing yield/resume protocol with one plan in flight,
and a completed background build publishes by atomic default swap
(`emp_async_close_background_plan`).  Getting it correct surfaced three
real mechanism bugs, each measured then fixed: unverified async-published
defaults were unservable (experience-count guard); a build completing
into an unserved request armed with a stale request_seq and was retired
in the same tick, deadlocking an armed decision with zero options; the
fault-onset trust epoch admitted calm-phase render defaults for 15
actions of the fault window.

The honest headline measurement: **on a single-threaded rule engine this
does not reduce wall-clock latency.**  The background build's passes run
inside the action's own settle ticks, so jam-probe p99 was unchanged
(641 vs 668 ms — the "System-1" requests simply inherit the build pass),
while serving programs 1-2 actions stale cost real margin (min altitude
2,348 -> 793 ft).  The flag is therefore OFF in the replication runner
(flag-off reproduces the render-suspended result byte-identically), and
the machinery waits on the engine-level prerequisite: scheduling the
synthesis areas off the action boundary (the async cognitive core's
`CognitiveTask`/area-scheduler path — a Rust-side project, out of
seed-rule reach).  Within the serial engine, the realised latency lever
remains the render-first proposer (alphabet-flat ~27 ms).

## Honest residuals

- **Escalation is eager.**  The 5 s evidence horizon fires during the
  ordinary post-fault/reference-change transient for every fault,
  including ones (broken aileron) whose heading tracking was fine —
  rung 2 then retires heading unnecessarily.  The horizon, the ratchet
  margin, and a rung-2 entry condition keyed on required-vs-achievable
  heading rate (the measured uncontrollability criterion) are the
  obvious levers; none is tuned yet.

- The v4 transient loses ~2,500 m of altitude before the regime
  stabilises; rung timing/thresholds are untuned (first-working values).
- The ladder is declared by `regime_max_ordinal` + consumer keying, not
  first-class Rung nodes; migrate to `escalation_rungs.json`-style data
  when a third rung appears.
- The 100-episode matrix gate still applies: this is one seed, one
  scenario, the probe protocol.  The other seven scenarios must hold the
  40 s gate before any full-matrix run (see the replication doc).
- Escalation is one-way within an episode; no de-escalation rung yet
  (rung 2 keeps the orbit even after conditions improve).
- Pre-existing red, not introduced here (verified by re-running with this
  work's `_run` additions stripped): `test_jsbsim_f16_departure_recovery
  ::test_graph_recovers_deep_stall...` fails its 30 m altitude-loss bound
  at 72.2 m in this worktree's current uncommitted state.

## Humanoid consumer (`humanoid_control_regime` v1.0.0)

The directed-walk path now holds the same regime contract in the graph.
New support cycles or a new best directed-progress value are evidence.  The
absence horizon is the sensed support count squared: four action requests for
the biped, derived from morphology rather than a tuned duration.

The consumer uses a hard-realtime bridge for the two generic escalation
transitions because loading the soft-realtime generic rules alongside the
humanoid adaptation schedule currently suppresses them.  The bridge preserves
the generic contract and semantics while the schedule interaction is isolated;
the humanoid-specific rungs remain graph rules:

- **Rung 1 — attractor demotion.** Pin the active gait and residual regime to
  walking, clear the stale evidence window, suspend render-first composition,
  and invalidate earlier System-1 defaults by advancing the async trust epoch.
- **Rung 2 — locomotor bootstrap.** Re-arm recovery and online adaptation,
  reset the stale prior, clear surprise, and request a fresh bootstrap under
  the new trust epoch.

Epochs 16–18 were byte-identical standing fixed points: `-0.00423 m`, zero
support alternations.  The first migrated probe escaped (`1.284 m`, 29
alternations) but the ordinary residual selector promoted it back to running
and it fell at action 175.  Making escalation a one-way episode invariant in
the normal selector removed that conflict.  The final probe
(`results/humanoid_coordination_epoch22_fast_regime_v2.json`) reached
`0.193 m`, completed 37 support alternations, did not fall, and ended in the
walking attractor.  It therefore clears the curriculum's `0.1 m` locomotion
gate without hiding the speed/stability tradeoff.

This imports both useful F-16 results. Absence of expected evidence changes the
control regime, and the full plan-aware System-2 composition now runs through
the same native `MotorCompose` term as the aircraft rather than through the
humanoid's interpreted open/Argmin/yield cascade. The term dispatches on the
held motor schema: generic effector consequences for aircraft and
support-context phase consequences plus learned pair synergies for humanoids.
The graph still decides when composition is required and assembles the selected
program; the native primitive only returns exact membership.

The retained-memory native probe
(`results/humanoid_coordination_epoch23_native_system2_v2.json`) reached
`0.253 m`, completed 21 support alternations, retained width-2 simultaneous
programs, did not fall, and ended walking. The native membership result is
cached only within the current `(request_seq, state_seq)` because the humanoid
population contains many context-local versions of each primitive; any new
observation or learning receipt invalidates it mechanically.

## Native MotorCompose (`embodied_motor_program` v1.8.0 + engine term)

The engine-level resolution of the System-2 latency problem, and it
dissolves rather than schedules it: the ~300-600 ms was never the search
itself, it was Term-tree INTERPRETATION of the search's arithmetic.  The
new Rust term `MotorCompose` (runners/dsl/src/motor_compose.rs; enum /
eval / copy / reflect / jsonio wiring plus the regenerated variant
table) implements the search composer's exact selection — open best
singleton, snapshot-parallel per-group expansion rounds, strict
improvement close — as one pure function over a precomputed
model-prediction matrix.  Parity is structural, not hoped-for: P0
attr-or-zero defaults, ordinal-ascending first-wins argmin (the engine
Argmin's NodeID-sorted-set order), and batch bind-all-then-apply round
semantics are each mirrored explicitly.

Seed side (v1.8.0, `native_composition_enabled` policy flag):
`emp_native_mark_composition_choice` marks the composed members via one
MotorCompose evaluation per binding and feeds the same mark → open →
attach → close assembly pipeline the render path built; term-tree
search opening is guarded off under the flag.  Because the term IS the
search, it needs no regime suspension — full search fidelity in calm
AND fault windows; the F-16 runner now sets native on, render off.

Measured:

- nominal 20 s: tracking IDENTICAL to the term-tree search (alt 143.6 /
  hdg 0.14 / spd 4.71) — the parity gate;
- nominal 100 s: 323.28 / 13.26 / 4.86, settling 38.8 s (search:
  324.33 / 13.30 / 4.79, 39.1 s), zero escalations, System-2 p99
  26.8 ms;
- jammed rudder 100 s
  (`..._jam_metastable_native_probe_v1.json`): survives with the best
  margins of any run — min altitude 2,487 ft, max rates 0.69 rad/s,
  structural utilization 0.65, escalation/orbit timeline matching the
  search run (159 / 266) — at **fault-window p99 43.7 ms vs 668 ms**
  under the term-tree search (~15×).

This supersedes both prior latency levers where enabled: render-first
(approximate semantics, needed suspension) and the async publication
machinery (kept, opt-in, still awaiting an engine scheduler for genuine
background execution — but with composition at ~tens of ms synchronous,
the case for it is now confined to the 100 Hz arm).  The bench sweep
including engine-heavy suites (dimension inference, quanta navigation)
is green on the rebuilt binary; the one red is the pre-existing
environmentally-borderline System-1 p99 bound.

## The Pareto rewrite's nominal regression, found and fixed (2026-08-02)

`control_regime_escalation` v3.0.0 + `f16_flight_path_control` v2.0.0
replaced the rung ladder with a Pareto frontier
(`docs/regime_pareto_frontier_prereg.md`).  Its n=100 nominal block
falsified its own prereg'd prediction: 88/100 healthy episodes escalated,
82 of them ending on the corner that surrenders altitude, altitude RMSE
378 -> 778 ft and one crash.  Four defects, all found by instrumenting a
single episode's own contract attrs and then re-gating at n=10:

1. **The evidence ratchet lost its settling-band floor** (v2.0.1).  Every
   episode starts AT its reference, so the ratchet latched
   `regime_best_error = 0.0` on tick 1 and "a new best" became
   `error < 0.0` forever after; the residence arm's (correct) trend test
   then rejected any slow drift, so evidence starved from the SECOND
   action of healthy flight.  The floor the v1.4.0 note describes was
   computed but wired into the residence arm only.
2. **The same declared dimension was measured with two different
   instruments** (v2.1.0).  Heading was an achievability ratio; altitude
   and speed were raw tracking errors, and "hold" alone was scored on raw
   error where every alternative was scored structurally.  The F-16's
   honest ~300 ft nominal altitude offset therefore read -9 on a healthy
   aircraft, and surrendering altitude (flat 0.0) dominated the status
   quo in cruise.
3. **A Pareto tie was broken by frontier iteration order** (v3.1.0).  The
   HOLD verdict the ladder architecture had was lost: two Pareto-equal
   candidates left the Argmax free to abandon the regime being flown on
   no measured preference.  Leaving the held regime now requires a STRICT
   improvement on the declared priority axis.
4. **`regime_escalation_count` never counted** (v3.1.0): its effect read
   `regime_ordinal` after the preceding effect had already overwritten it
   with the verdict.

Nominal is restored: on the block's base seed the fixed controller
reproduces the pre-regime-machinery native baseline EXACTLY (323.28 ft /
13.26 deg / 4.86 ft/s, settling 38.8 s) with zero escalations, and the
10-seed pre-flight escalates 0/10 with 0 crashes.

**The fault side is a different story and is recorded as a measured
negative** — see `docs/regime_pareto_frontier_prereg.md` for the powered
block and the mechanism.  The short version: axis margins are measured on
the aircraft as it is NOW, under the regime that is failing, and then
attributed to corners that would change that situation.  In a jam the
sustained sink is large BECAUSE the unwinnable heading fight is bleeding
lift, so the altitude axis reads "unachievable" and the frontier picks
the corner that surrenders altitude too — which then flies wings-level
into the ground.  v3's measured survival came from the opposite move:
retire heading, KEEP fighting for altitude.  A frontier scored from the
failing regime's own telemetry cannot express that, and the trim corner
(which surrenders zero sideslip, not one of the five declared axes) is
not even representable in it.
