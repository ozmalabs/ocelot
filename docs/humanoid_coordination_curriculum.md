# Graph-native humanoid coordination curriculum

This experiment adds an active balance curriculum to the graph-native
humanoid controller. It does not provide named joints, motion clips, inverse
kinematics, a gait controller, or a Python curriculum policy.

The graph owns nine dimensionless whole-body challenge directions, selects
among unresolved challenge frontiers with the shared curiosity term, and
expresses the selected impulse in body weights. The PyBullet boundary only
converts that request to newtons and returns an action-time receipt.

## What counts as safe

Postural survival was not enough. An early implementation promoted a challenge
when the body was upright and outside recovery after one evidence window. That
accepted perturbations while the controller was airborne and reduced directed
progress from `0.327 m` in an earlier run to `0.019 m`.

The graph now records directed progress and support-cycle count at challenge
issue. It promotes a frontier only after all of the following are observed:

- the body is upright;
- explicit recovery mode has ended;
- directed progress has returned to at least its pre-challenge value; and
- a new locomotor support cycle has completed.

The earliest success verdict uses the morphology-derived support evidence
window. An unsafe verdict waits for that window multiplied by the sensed
support count, giving the gait an opportunity to re-form. Resolution also
starts a fresh rest interval before another challenge can be issued.

## Curiosity and locomotor bootstrap

Removing the early perturbation uncovered a stable standing attractor: the
unperturbed cold controller completed no support alternations. Perturbation was
therefore doing two jobs—testing balance and supplying an exploratory kick.

The graph now learns the locomotor consequence of every safely recovered
challenge:

- mean post-challenge support-cycle gain; and
- mean morphology-normalized directed-progress gain.

At a zero-cycle start, a shape-matched challenge with demonstrated recovery
utility receives a temporary curiosity bonus and is replayed at its known-safe
scale. After locomotion begins, ordinary learning-progress curiosity again
selects unresolved frontiers. This is causal scaffolding learned from receipts,
not a hard-coded choice of direction.

## Five-lifetime result

The canonical fresh-library run is split across:

- `results/humanoid_coordination_causal_bootstrap_epochs_v1.json`
- `results/humanoid_coordination_causal_bootstrap_epochs4_5_v1.json`
- `results/humanoid_coordination_causal_bootstrap_library_v1.json`

The first lifetime discovered that the forward challenge safely produced three
new support cycles. Every later lifetime selected it as the initial bootstrap,
while later challenges continued exploring other directions.

| Lifetime | Directed progress | Support alternations | Peak tilt | Falls |
|---:|---:|---:|---:|---:|
| 1 | `0.252 m` | 29 | `0.049 rad` | 0 |
| 2 | `0.213 m` | 40 | `0.105 rad` | 0 |
| 3 | `0.257 m` | 37 | `0.073 rad` | 0 |
| 4 | `0.211 m` | 25 | `0.059 rad` | 0 |
| 5 | `0.285 m` | 44 | `0.133 rad` | 0 |

More experience therefore increased the best observed progress by about 13%
and support alternation count by about 52%. It did not monotonically optimize
every measure: the most active lifetime used a larger tilt envelope. That is a
real speed/agility/stability tradeoff, not a suppressed fault.

By lifetime five the graph had tight two-sided brackets for forward,
left, forward-right and rearward-right challenges, and one-sided safe
frontiers for rearward-left and unload. The remaining broad or one-sided
frontiers are explicit curriculum targets rather than hidden tuning gaps.

## Architectural boundary

All selection, challenge intensity, delayed task verdicts, bracket updates,
causal bootstrap utility, and shape-indexed retention are graph rules and graph
facts evaluated by the Rust substrate. Python performs simulator transduction,
observation serialization, and graph-memory persistence only.

This is no longer only a reactive-balance foundation. The next retained
curriculum layer unlocks ballistic landing from the mastered `unload`
frontier. It transfers the graph-measured safe impulse rather than introducing
an authored jump magnitude, and it only accepts a landing receipt after the
support topology has gone to zero and subsequently returned. Vertical landing
then unlocks forward, left and right landing challenges from the same learned
envelope.

The first retained ballistic epoch,
`results/humanoid_coordination_epoch24_ballistic_landing_v1.json`, sampled all
11 then-present challenges. It completed three vertical landing trials and two
forward landing trials. Both directions recorded real airborne and touchdown
facts; two vertical receipts and one forward receipt recovered safely, one
forward trial established an unsafe upper boundary, and the humanoid did not
fall. It made `0.180 m` directed progress with 14 support alternations.

The directional extension,
`results/humanoid_coordination_epoch25_directional_landing_v1.json`, retained
`0.273 m` progress, 27 support alternations and no fall. Right landing acquired
a safe receipt and an unsafe ceiling. Left landing exposed an important
curriculum error: a stable pulse that failed to leave the ground was being
recorded as unsafe. The graph now distinguishes task insufficiency from safety
failure. A grounded, upright, locomotion-recovered receipt remains eligible
and expands by the support-derived evidence fraction; an airborne trial which
cannot recover still contracts the safety frontier.

The corrected warm-start run,
`results/humanoid_coordination_epoch26_directional_landing_v2.json`, then made
the left trial airborne, observed touchdown and promoted it safely. That run
fell later at action 140, so it is evidence for repaired directional
acquisition, not a clean whole-episode parkour result.

Because that evolving library already contained an impossible historical
bracket from the old semantics, it remains a diagnostic artifact rather than
the canonical warm start. The clean corrected run is
`results/humanoid_coordination_epoch27_corrected_directional_landing_v1.json`
with `results/humanoid_parkour_landing_library_v2.json`. Starting again from
the established balance library, it made `0.246 m` progress and 13 support
alternations with no fall. It recovered safely from two vertical landings and
one forward landing. Left and right both genuinely became airborne and
touched down but did not regain the locomotor task, so they correctly became
unsafe upper bounds at `0.856`, with no inverted safe/unsafe frontier.

At that point the remaining architectural boundary was self-generated takeoff. These landing
challenges apply simulator-transduced external impulses so the graph can learn
flight, touchdown and recovery before being asked to produce launch. A proper
takeoff stage must add vertical centre-of-mass velocity to the learned motor
consequence model and let the existing analysis-by-synthesis composer discover
a coordinated extension program. Obstacle affordances, reach/vault coupling
and repeated jump sequences remain later curriculum stages.

## Self-generated takeoff

That boundary is now crossed. Humanoid action models, support-local experts,
synergies, arbitrary motor programs, prediction errors and consolidated motor
rates all carry the learned change in vertical centre-of-mass velocity
(`dvz`). Native `MotorCompose` includes the same dimension in forward synthesis.
When a takeoff challenge is active, the graph opens a normalized upward
velocity residual; ordinary posture, locomotion and support-preview costs remain
active, so upward motion is not selected independently of viability.

The takeoff request explicitly has zero environmental impulse authority. The
world boundary acknowledges it without applying force or advancing an external
force frame. The graph holds the motor residual open across actions until it
observes both zero support and positive whole-body vertical momentum. Negative
vertical momentum during an aerial gait interval is rejected as falling, not
misreported as takeoff. Touchdown and resumed locomotion are still required for
a safe receipt.

The canonical retained result is
`results/humanoid_coordination_epoch32_self_takeoff_causal_v1.json`, with the
shape-indexed frontier in `results/humanoid_parkour_takeoff_library_v4.json`.
It completed `0.256 m` directed progress and 41 support alternations without a
fall. The graph issued two takeoff tasks. The first remained grounded or lost
support with downward momentum and was retained as insufficient task evidence.
During the second, the zero-force request was recorded at action 136; the
vertical motor drive remained open while the composer selected learned opaque
actions. At action 146 the body had zero support and `+2.04 kg m/s` whole-body
vertical momentum, after which the drive closed, contact returned and the
locomotor task recovered. The resulting frontier has one safe self-generated
takeoff at scale `0.952` and no unsafe ceiling in that clean run.

This is a real but small hop, not yet a parkour-height jump. The next curriculum
steps are to expand the flight-time/height envelope, consolidate the successful
multi-action launch trajectory as a reusable shape-indexed motor program, then
couple launch to directional landing and obstacle affordances.

The flight-envelope stage now makes that first claim stricter. A self-takeoff
receipt must raise the measured whole-body centre of mass by a graph-derived
ballistic target and remain aerial for at least as many distinct sensor
receipts as the morphology has load-bearing supports. The height target is
`difficulty² * standing_height / (support_count * support_prior²)`, the
ballistic `v²/(2g)` consequence of the graph's existing takeoff velocity
target. A state-sequence guard ensures repeated rule fixpoints cannot invent
flight time.

Applying that evidence invalidated the old tiny-hop safe floor, as intended.
Epochs 33 and 34 recorded no qualifying flight and contracted the frontier.
The cause was not a lack of useful single-joint models: the ordinary composer
correctly refused combinations whose pair interactions had never been
learned, but the finite synergy-probe budget could not cover the humanoid's
cross-joint product space. During an explicit self-takeoff drive only, native
analysis by synthesis may now propose a novel cross-actuator additive program
from those learned local consequences. Missing interactions contribute no
invented residual; observed execution still supplies the causal receipt.
Ordinary locomotion retains the learned-synergy requirement.

The retained sequence in
`results/humanoid_coordination_epoch35_novel_takeoff_composition_v1.json`
through
`results/humanoid_coordination_epoch37_retained_takeoff_recovery_v1.json`
shows the distinction between producing flight and mastering it. Epoch 36
raised whole-body centre of mass by `0.00541 m` against a `0.00332 m` target,
recorded two aerial receipts and touchdown, and did not fall, but failed to
regain the locomotor task inside the recovery window. It was therefore not
promoted. On the next retained epoch the graph again produced two aerial
receipts, raised centre of mass by `0.00361 m` against a `0.00262 m` target,
touched down, resumed locomotion, and promoted a safe floor at scale `0.594`
below the learned unsafe ceiling `0.668`. That run completed 33 support
alternations without a fall. The launch remains broad—the exploratory program
used up to 19 distinct actuator groups—so energetic/program compression is
the next optimization before obstacle coupling.

## Takeoff efficiency frontier

Launch composition now prices two biological costs in addition to task error:
measured actuator work normalized by body gravitational potential energy, and
motor-unit recruitment normalized by the morphology's available effector
groups and support prior. These costs are active only during an explicit
self-takeoff efficiency probe; acquisition and ordinary walking retain their
previous objectives. The native composition cache also keys the takeoff drive,
compression scale and compression authority, preventing a cached motor answer
from crossing a changed motivational state or a newly allocated graph.

A resolved takeoff remains curiosity-eligible for a support-prior-sized
efficiency evidence window. The graph starts at one support-prior fraction and
then bisects a separate compression safe/unsafe frontier. Every proposed point
must still satisfy the same centre-of-mass height, distinct aerial receipt,
touchdown and locomotor recovery requirements. Compression failure updates the
compression ceiling without erasing the underlying physical-skill frontier.
Both frontiers persist in the shape library.

The diagnostic full-pressure trial
`results/humanoid_coordination_epoch40_takeoff_efficiency_probe_v1.json`
reduced peak width from 19 to 6 but made flight too brief, demonstrating why
width alone is not a valid optimization verdict. The retained Pareto search in
epochs 42–44 converged to a safe compression pressure of `0.03125` and an
unsafe ceiling of `0.031684`. The safe receipt completed flight, touchdown and
locomotor recovery without a fall. Across its 12 launch-drive actions it used
44 actuator-group recruitments versus 46 in the uncompressed epoch-37 receipt,
a `4.35%` structural reduction; its measured supplied work was `89.91 J`.
Peak instantaneous width remained 19, while the later wide action contracted
from 16 members to 14. This is a modest but causally retained compression, not
a claim that the launch has become a compact primitive. The narrow boundary
also shows the next architectural need: consolidate and prune the successful
multi-action launch trajectory as a unit, rather than asking only a myopic
per-action composer to discover temporal redundancy.

## Developmental jump chunks

The motor graph now learns that unit as a support-topology sequence. Every
grounded program carries both a task context and a receipt-derived phase:
preparation (support retained), launch (support lost), flight (support absent),
or landing (support regained). Support loss in any task is neither a fault nor
a safety verdict: its learned probability and missing-load magnitude are
weighted against progress, energy, attitude, capture geometry, and the active
gait's expected topology. It may be deliberate, incidental, useful, or costly.
Walking and self-takeoff predecessors are kept in separate temporal
contexts, so an incidental gait transition cannot seed a jump schema.

Local safety is still insufficient for replay. A self-takeoff transition is
marked trajectory-verified only after the graph observes the complete flight
envelope, touchdown, upright recovery, renewed directed progress, and a new
support cycle. Only then may an uncompressed task use the phase-conditioned
sequence as a top-down prior. A compression probe deliberately returns to
analysis by synthesis: the existing takeoff energy/recruitment Pareto pressure
can remove redundant recruitment within a phase, and the resulting replacement
sequence earns reuse only if the whole trajectory succeeds again. This is the
developmental pattern suggested by jumping in children: stabilize the large
temporal chunks first, then improve coordination inside them.

Verified transitions are stored alongside their endpoint programs in the
body-shape library. Restoration is mechanical; graph rules reactivate an edge
only after shape decoding has rebound both endpoint programs to the current
body. The migrated tests cover deliberate support-loss retention, whole-jump
verification, shape-library round-trip, and ordinary receipt-driven sequence
advance. The 360-action retained physics probe
`results/humanoid_coordination_epoch46_developmental_chunks_v1.json` remained
upright without a fall, but curiosity did not select a challenge in that
lifetime, so it is a locomotion-regression result rather than evidence of
physical jump replay.

The follow-up support-tradeoff regression removes the last Boolean contact
vetoes from compound authority, recovery entry, primitive learning, synergy
approval, and motor-memory retention. In
`results/humanoid_coordination_epoch47_support_tradeoff_v1.json`, the body
completed 180 actions and 36 support alternations without a fall. Eighteen of
20 aerial samples remained outside recovery, and four aerial samples executed
compound actions. Thus unsupported motion is now an ordinary controllable
region of state space; its learned topology and load deficit affect ranking,
but do not determine the verdict.

Epochs 48–62 then exercised acquisition rather than replay. Deliberate takeoff
now owns its controller while the body remains inside its material/upright
envelope, so a generic gait-surprise reflex cannot fragment preparation,
launch, flight, and landing. The native composer also closes from its
graph-visible attachment snapshot; it no longer waits forever for candidates
that became dynamically ineligible after attachment. This produced repeated
unassisted flight envelopes and, in epoch 62, a complete safe receipt: two
distinct aerial observations, a `0.00380 m` height gain against a `0.00244 m`
target, touchdown, renewed locomotion, 35 support alternations, and no fall.

That receipt exposed why a developmental schema cannot be retained by local
chunk quality alone. Its four endpoint programs included two singletons and
all four had locally negative directed advance, yet together they formed a
successful recovered trajectory. Whole-trajectory verification now stamps the
transition and both endpoint programs with one schema identity. The familiar
body-shape library admits those endpoints despite their local score, exempts
them from the isolated-habit withdrawal heuristic, and persists the edge only
after both endpoints are present. The epoch-62 disk library consequently holds
four verified programs and two verified transitions for schema `304`; this is
a lifetime-boundary result, not merely an in-memory trace.

Acquisition evidence and refinement evidence are now separate. Attempts made
before a reusable schema exists do not consume the bounded phase-compression
budget. When the first verified transition becomes active, a graph rule opens
a fresh compression safe/unsafe frontier; only trials with nonzero compression
pressure increment its evidence count. This permits later lifetimes to warm
retrieve the coarse movement and use analysis by synthesis to prune it without
confusing discovery attempts with evidence about temporal redundancy.

The first warm refinement lifetime,
`results/humanoid_coordination_epoch63_warm_schema_refinement_v1.json`, opened
that frontier at compression pressure `1/9` and accepted it as safe. It minted
schema `437` with four retained endpoint programs of widths `[4, 1, 1, 1]` and
three verified transitions. The coarse schema had broad preparation chunks of
widths 11 and 10. This is the desired developmental improvement loop: restore
an embodied prior, synthesize a different realization under a resource cost,
verify the complete physical consequence, and retain the new realization by
shape. The lifetime also records an earlier ordinary-locomotion fall at action
98, 43 unsuccessful get-up attempts, and one simulator body reset; the later
safe takeoff receipts do not erase that negative evidence.

The later F-16 metastable-control work exposed a retrieval mismatch in this
loop. A verified jump was still dispatched as a walking-token match or an
ordinal transition chain, while the flight controller lets every learned rung
compete from its own currently supported physical precondition. Humanoid
takeoff now follows the same graph-native contract: a whole-trajectory-verified
stage is eligible from its current support topology, independent of the
walking selector's token. Its preparation remains output-null until the
thalamic release rule fires, and compression pressure disables replay so a new
analysis-by-synthesis realization can compete.

Restored schemas also distinguish relational endpoints from executable motor
events. Some compound roots were persisted with zero local duration because
their measured timing lives on the verified outgoing temporal edge. Stage
firing derives its horizon from either receipt without a host default. The
schema's declared primary token is authoritative, and an output-potent trial
enacts the complete arbitrary member set rather than silently collapsing to a
primary/secondary pair.

The diagnostic sequence records each boundary. Epoch 65 restored eight warm
programs but recalled none. Epoch 66 recalled 216 phase-matched singleton
endpoints without falling, proving asynchronous support-conditioned dispatch
but not compound launch. Epoch 67 selected compound roots, yet the trial
boundary still reduced them to pairs. The corrected epoch 68 fired one intact
width-11 program, immediately entered flight, gained `0.01014 m`, touched down,
and continued without a fall; it correctly failed the current `0.02765 m`
height target. Epoch 69 then replayed an actual topology sequence—widths 4, 10,
and phase-conditioned singleton stages—again observing flight and touchdown
without a fall. Its `0.00834 m` peak remained below the `0.02184 m` target, so
the graph retained unsafe evidence and reduced the next difficulty scale from
`1.714` to `1.523`. The curriculum is therefore adapting again, although this
frontier has not yet produced a new safe receipt.

## Escaping a learned standing fixed point

Later retained-memory epochs exposed a second learning problem: epochs 16–18
selected running but produced the same `-0.00423 m` motion and zero support
alternations. Because every ordinary learning receipt required a support
cycle, the absence of locomotion generated no evidence with which to revise
the choice.

The shared control-regime escalation contract now makes that absence itself a
graph residual. For a biped, four action requests without a new support cycle
or new best progress demote the attractor to walking; a further absence opens
recovery, invalidates the stale motor default, and re-kicks graph learning.
The ordinary gait selector cannot promote over an escalated episode, so the
fallback is persistent rather than a one-tick suggestion.

The canonical migrated probe is
`results/humanoid_coordination_epoch22_fast_regime_v2.json`: `0.193 m`
directed progress, 37 support alternations, no fall, and a final walking
attractor. This is less progress than the best early lifetime, but it turns an
otherwise permanent standing fixed point into safe gait evidence from which
the curriculum can continue learning.

The subsequent native-System-2 probe replaces the interpreted compound search
with the F-16 work's `MotorCompose` primitive while preserving the humanoid
schema's support-local models and learned pair residuals. It produced `0.253 m`,
21 support alternations, width-2 simultaneous actions, no fall, and a final
walking attractor (`humanoid_coordination_epoch23_native_system2_v2.json`).
This is native analysis by synthesis, not a simplified local gate: the same
whole-plan cost and synergy constraints select the arbitrary motor bundle.

The first reach substage is now live through the accompanying kinematics
study. The graph selects a topology-inferred non-support terminal point,
constructs a target from the learned affordance closest to an abstract reach
direction, and inverts its endpoint model by analysis by synthesis. The
canonical pass closed a `0.0254 m` target in one opaque action with zero
measured residual and left locomotion unchanged. A harder free-direction
negative control exposed the next gate: multi-step reach needs endpoint
consequences conditioned on changing joint configuration.

That gate has a historical positive result, but the corrected repeat exposes
the remaining ceiling. The boundary mirrors an opaque actuator ordinal, while
the graph learns command-specific pre/post anchors and scales predicted
endpoint effects over the physical servo interval. It also remembers
goal-scoped worsening receipts. The v15 run closed `0.0287 m` to `0.0037 m` in
five actions, below a `0.0062 m` learned-basis tolerance, while preserving
`0.252 m` walking progress, 29 support alternations and no fall. Corrected
v20/v21 runs did not reproduce the closure. v22 adds a support-prior-shrunk
context residual learned incrementally from measured single-reach transitions;
the graph then selected a causal compound and closed the composed target in
three attempts while preserving the walking gate. Arbitrary-direction reach
remains the next frontier. The new arbitrary-direction mode now requires a
causal spanning compound when available, but its first withheld-direction
probe exhausted the morphology-derived horizon. Directional coefficients and
momentum-conditioned local reachability are still required.
