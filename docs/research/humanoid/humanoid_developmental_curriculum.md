# Situated child-like motor development

The humanoid starts supported on its back. This is not a canonical pose or a
hidden `home`: it is merely a currently stable relation between this body and
this surface. While the active developmental ecology is the floor, low height
and non-upright orientation are intended conditions. They cannot invoke a
get-up program unless independent material or intervention evidence opens a
viability interrupt.

## Developmental plan

The graph now represents development as an overlapping dependency graph, not
an age clock or a scalar stage score. Its broad progression is:

1. spontaneous whole-body variation, effector consequences, surface contact,
   reversible action, and antigravity segmental control;
2. side lying, rolling between opposed supported body surfaces, prone support,
   reaching, pivoting, and independent sitting;
3. transitions into and out of sitting, belly mobility, quadruped support and
   rocking, and hands-and-knees crawling;
4. kneeling, pulling to stand, cruising, standing alone, controlled lowering,
   assisted stepping, and walking alone;
5. running, jumping, stairs, single-leg balance, and hopping.

This ordering is deliberately a DAG. Several abilities develop concurrently,
and hands-and-knees crawling is an optional route rather than a mandatory gate
to standing. That matches the WHO longitudinal result: achievement windows
overlap, no fixed sequence was assumed, and a minority of typically observed
children did not exhibit hands-and-knees crawling.

The first capability is spontaneous general movement, because useful early
development is not a sequence of commanded poses. Movement variability itself
provides the sensorimotor data from which directed and repeatable action can be
learned. Later labels are human analogues for reporting; graph rules still use
body-plan-neutral goals, structural relations, and receipts, so learned
abilities can warm-start structurally similar bodies.

### Endogenous somatomotor waves

Spontaneous variation now has a graph-native generator rather than depending
on a succession of independent least-used twitches. The discovered mechanical
effector topology becomes an excitable sheet. Homeostatic deprivation ignites
a rested actuator channel, activity travels one mechanical hop per motor epoch,
and a topology-derived active interval makes adjacent bursts overlap. The
overlapping front collapses to one motor program that may command several
effectors. Verified reafference then changes each cell's experience counters;
the field itself has no output authority.

There is one excitable cell per physical command channel, not per opaque token.
Opposing command polarities are possible outputs of the same channel. This
distinction prevents a spontaneous front from treating flexion and extension
of one joint as independent effectors, while retaining both choices during
the program's situated analysis-by-synthesis collapse. The mechanism contains
no anatomy, preferred pose, random host policy, floating-point cognition, or
fixed wave width/duration. Body topology determines connectivity and local
burst persistence.

This is a deliberately conservative engineering analogue of patterned
spontaneous activity in developing sensory circuits and the reafferent value
of sleep twitches and spontaneous general movements. It does not claim that
human spinal or motor-cortical development is literally a retinal-wave copy.
Its testable claim is narrower: endogenous correlated movement provides better
developmental evidence than isolated commands, and receipts should progressively
turn that variation into reusable motor programs.

## What counts as achievement

A joint twitch is not a roll, and one lucky event is not a milestone. The
simulator boundary transduces the body's local axis into a signed
gravity-relative integer class. A side transition changes the dominant axis;
a complete supine/prone transition reaches the opposing class. Multi-action
orientation trajectories are retained in the graph, so a roll may unfold over
several interleaved experiments without Python deciding that it occurred.

For every capability the graph requires:

- causally bound, verified receipts;
- repeated success over a body-derived evidence window;
- more distinct situated contexts than prerequisite abilities; and
- a successful delayed retention probe.

Only then is the ability mastered and stored as an output-null, shape-indexed
memory. Clinical-style milestones are reported separately from precursor
capabilities; failing to reach a later milestone is data, not something hidden
by a collapsed progress score.

## Boundary and transfer

Continuous PyBullet quantities exist only at the mechanical interface.
Developmental evidence, trajectory memory, selection, competence, retention,
and transfer are integer-only graph cognition. Templates and recalled memories
have zero output authority. `ShapeDecode` can use shared kinematic and support
relations to warm-start another body plan, but every transferred ability must
be reverified on the receiving body.

Run the short cold assay with the repository environment:

```bash
/home/matt/ozma/internal/research/.venv/bin/python \
  scripts/jabberwock_humanoid_developmental_curriculum.py \
  --protocol protocols/humanoid_developmental_smoke_v1.json \
  --json-out results/humanoid_child_development_cold_v1.json
```

The full curriculum uses
`protocols/humanoid_developmental_relative_balance_v1.json`. Results report
demonstrated precursor capabilities, demonstrated clinical milestones, the
active human analogue, its ecology, failures, contexts, retention, get-up
attempts, and the complete motor trace. This makes the next developmental
limit auditable rather than inferred from a nominal stage number.

## First cold execution

`results/humanoid_child_development_floor_v1.json` is a completed 160-action
cold run. It retained spontaneous general movement, supine effector-consequence
exploration, and body-surface contact discovery. Reversible action accumulated
the complete competence window and is awaiting its delayed retention probe;
the active frontier has advanced to antigravity head/trunk control. No rolling,
sitting, crawling, standing, or walking milestone was claimed.

The run made one initialization-time get-up attempt and entered no recovery
basin. The earlier pseudo-developmental 720-action result made 630 get-up
attempts, so floor ecology has removed the dominant wrong-basin behavior
without disabling material interrupts.

The 720-action audit was also attempted, but the broader humanoid episode graph
still grows too expensive over long histories and did not finish within the
assay window. Consumed developmental receipts are now archived from the hot
development edge while remaining reachable through their trial for audit; the
remaining long-episode cost is outside this developmental edge and should be
profiled before treating very long wall-clock exposure as useful practice.

## Somatomotor-wave cold assay

`results/humanoid_child_somatomotor_waves_cold_v8.json` is the matching short
cold assay with endogenous waves enabled. Across 81 enacted waves, all 81
received verified reafference, all 21 actuator channels produced a useful
configuration/contact consequence, and 27 programs contained overlapping
effectors (maximum observed width two). It mastered three precursor abilities
in the assay window—spontaneous general movement, effector-consequence survey,
and surface-contact mapping—versus two in the earlier
`humanoid_child_development_cold_v2.json` run. It also made no get-up attempt,
so the gain did not come from returning to the old upright/recovery basin.

That earlier comparison was an integration assay rather than a controlled
efficacy claim. The subsequent same-revision paired ablation is recorded in
`results/somatomotor_wave_same_revision_ablation_v2.json`. Both arms execute in
one process with the same engine, body, initial fixture, seed, calibration,
developmental graph and protocol. The only manipulated input is the integer
`somatomotor_wave_enabled` experimental gate; disabling it removes wave
proposals without unloading the rest of cognition.

The enabled arm mastered three precursor abilities versus two, produced eight
support alternations versus five, made no get-up attempt versus one, and had
slightly less negative directed displacement. Its 81 verified waves included
26 compound fronts. Capability-relative receipts strengthened 12 propagation
couplings and fractionated four; the strongest reached integer strength five.
This establishes a controlled effect for this deterministic fixture and shows
that practice changes future propagation, but it is still one body/fixture
pair. Counterbalanced execution and a preregistered family of fixtures and
body variants are required before generalizing the effect.

## Counterbalanced fixture and mechanical-body family

`results/somatomotor_wave_fixture_body_matrix_v2.json` expands the ablation to
a declared two-by-two family: supported supine versus supported prone initial
relations, crossed with nominal versus three-quarter actuator authority. These
are two mechanical variants of one morphology, not two different anatomical
body plans. Each condition has an independent world for each arm, and arm
order is reversed in two of the four conditions.

The paired wave-minus-ablation results remain separate rather than being
collapsed into one score:

| condition | mastery | support alternations | directed displacement |
|---|---:|---:|---:|
| nominal supine | +1 | +3 | +0.009 m |
| nominal prone | -1 | 0 | +0.063 m |
| reduced-authority supine | +1 | +4 | +0.091 m |
| reduced-authority prone | 0 | +4 | +0.086 m |

Across the family, waves add one net mastered precursor, eleven support
alternations and 0.249 m of directed displacement. Every wave arm avoids the
single get-up attempt made by its matched ablation. The nominal-prone result is
important: better displacement coexists with one fewer mastered precursor.
The wave generator therefore changes the exploration tradeoff rather than
being uniformly better under every developmental measure. Four deterministic
conditions establish robustness to these declared variations, but are not a
population estimate and do not test transfer to a different morphology.

## Immutable retained-rediscovery assay

`results/somatomotor_wave_retained_rediscovery_v3.json` tests practice using a
separate cold source library. Every stored capability records the verified
receipt that caused mastery, is integer-native, and has zero output authority.
The retained run may read this library but cannot update it; its SHA-256 is
checked after execution. Recall merely reopens the verification boundary, so
each ability still needs a fresh successful receipt.

All three cold abilities were re-mastered sooner:

| capability | cold receipt | retained receipt | receipts saved |
|---|---:|---:|---:|
| spontaneous general movement | 106 | 85 | 21 |
| surface-contact mapping | 134 | 95 | 39 |
| effector-consequence survey | 139 | 88 | 51 |

The retained run saves 111 action/receipt opportunities across those three
abilities and masters two further precursors—antigravity segmental control and
prone forelimb support—within the same assay horizon. This operationalizes
practice as a reduced verified trajectory back into a capability basin, not a
larger scalar reward or blind replay of a stored action.

## Cross-morphology transfer

`results/somatomotor_cross_morphology_transfer_v6.json` moves beyond mechanical
variants of one body. The source is the 21-channel MJCF humanoid; the target is
a distinct 17-channel symmetric humanoid with fewer links and a shorter
kinematic chain. Its name-free body signature has 23 relations: 17 are shared
with the source and six remain residual. The target is run twice in independent
worlds; only the presence of the immutable three-capability source library
changes.

The initial result correctly produced no unsafe transfer, but also exposed an
asynchronous eligibility error. Shape recall was classified as background
work while eligibility required zero local attempts. The live developmental
hard sheet could record its first attempt before background recall ran, making
the valid prior permanently unreachable. Shape recall now settles on the
initialization hard sheet. It remains output-null and cannot select an action;
all capability claims still require complete target-body evidence and delayed
retention.

After that fix, ShapeDecode opens three partial-shape capability priors with
overlap 17 and zero exact-body recalls. The v3 assay showed that this was useful
but incomplete: the warm target additionally closed surface-contact mapping,
yet its physical trace was identical to the cold target. Capability knowledge
had transferred; motor exploration had not.

The source library now also retains experienced wave couplings as output-null
integer evidence. A first implementation matched only a generic adjacent-link
motif. All 18 memories therefore collapsed to the same rank, and the target
again followed an identical trajectory. The corrected representation records
name-free local structure for both ends of a coupling: kinematic depth, local
degree and integer actuator-axis class. Sixteen distinct local motifs remain
in the 18-memory source library. Whole-body ShapeDecode still establishes that
the source is relevant, while local relation matching decides where a hint may
apply.

Coupling evidence now affects two graph-native degrees of freedom. At a branch
it ranks competing propagation paths. On a chain, where refractoriness often
leaves only one possible successor, it biases the endogenous ignition site.
This is not an actuator mapping or a recalled command. It is a one-shot
excitability prior; the receiving body's first verified reafferent receipt
clears it and updates local coupling strength.

The v6 cold/warm assay demonstrates physical transfer under that design:

| measure | cold target | warm target |
|---|---:|---:|
| spontaneous-general-movement mastery receipt | 90 | 86 |
| effector-consequence-survey mastery receipt | 118 | 113 |
| surface-contact mapping | not mastered | receipt 135 |
| support alternations | 11 | 12 |
| directed displacement | -0.0236 m | -0.0176 m |

The compound program and physical trajectory both diverge from action zero and
remain different at all 80 measured actions. Twelve local coupling hints are
used, all twelve receive target-body verification, and zero remain pending at
the end. The immutable source library's SHA-256 remains unchanged. These are
separate tradeoffs rather than a single success score: common capabilities save
nine receipts in total, a third capability becomes reachable, support changes,
and displacement is less negative. This deterministic paired fixture establishes
a causal mechanism and a concrete cross-morphology result; broader body families
are still required before claiming population-level generality.

## Passive caregiver scaffolding

Human development does not begin with isolated self-authored twitches. A
caregiver commonly cycles an infant's limbs and supplies repeated whole-body
load and vestibular waves through carrying and bouncing. These observations
separate two learning problems: discovering how the body can move, and
discovering which changes the child caused.

The general somatomotor field now represents that distinction explicitly. When
scaffolding is available, the graph requests the least passively exposed
effector channel. The mechanical boundary cycles that channel in both
directions and returns an integer trajectory: positive and negative excursion,
return residual, and the number of other channels that moved. Each channel has
a separate output-null `SomatomotorPassiveBodyModel` that accumulates its
passive envelope, repeatability, residual and observed mechanical coupling.
This is not the action model. After every channel has contingent evidence,
the graph requests one body-scaled external load wave. Every passive receipt is
marked exafferent, has no efference copy, consumes no child motor energy, and has
zero output authority. It can change body-map familiarity and wave
excitability, but cannot count as self-authored competence.

Only after passive coverage and the load wave are complete does the graph open
a new active attempt. That attempt receives normal motor-babble agency only if
its own physical receipt closes and confirms a fresh efference copy. The
passive model then records active reverification and agency disambiguation as
separate counts. If an unfamiliar or moving body has no stable fixation, both
its reference and efference copy are situated in the current sensed
configuration rather than an invented fixed posture.

The original caregiver experiment incorrectly made passive handoff a
permission gate: without it Walker2D could not emit action one. That result is
superseded. Development is not intrinsically safe; a caregiver changes the
consequence and recovery ecology in which development occurs.

`results/caregiver_safety_ontology_ablation_v7.json` replaces that ontology.
Absent, scrambled and contingent arms all complete 108 self-authored actions
and master the same two early capabilities. The absent arm retains 108
unbuffered receipts. Both caregiver-present arms receive 14 protected actions;
only the contingent arm receives seven-channel passive body-map credit. The
scrambled arm records its eight mismatches and continues cold rather than
halting. A separate matched physics assay in
`results/caregiver_protection_physics_v1.json` confirms that graph-authorized
external support changes the physical consequence while leaving the child
command identical. Full gates and limitations are in
`DEVELOPMENTAL_SAFETY_ONTOLOGY_RESULTS.md`.

`results/somatomotor_cross_morphology_family_v2.json` combines this scaffold
with the transfer assay and counterbalances arm order across three bodies:

| target body | shared / target relations | transferred hints | cold/warm result |
|---|---:|---:|---|
| symmetric articulated | 17 / 23 | 12 | physical divergence; 9 common receipts saved; one warm-only capability |
| radial articulated | 5 / 14 | 0 | identical 80-action trajectories |
| planar articulated | 3 / 14 | 0 | identical 80-action trajectories |

All bodies receive the same untuned scaffold procedure. The low-overlap bodies
therefore test specificity rather than merely adding more positive examples:
ShapeDecode withholds both capability and coupling priors, while the generic
passive-to-active developmental mechanism still lets the planar body acquire
its own calibration from scratch.

## Directed floor mobility

`results/humanoid_floor_mobility_v8.json` returns the 21-channel humanoid to a
cold, supported floor start for 480 self-authored actions. The previous exact
two-action pose reversal was replaced by return through coarse proprioceptive
regions. This is still situated: the regions are sensed sign relations for the
current joints, not a stored home configuration. Compound somatomotor programs
now retain integer developmental affordances from their verified receipts:
reversal, signed vestibular escape, support gain and translation.

The run mastered eight capabilities:

- spontaneous general movement;
- effector-consequence and surface-contact surveys;
- reversible configuration control;
- antigravity segmental control;
- prone forelimb support;
- prone reach and pivot; and
- belly crawling, including its delayed retention receipt.

It produced 30 support alternations, positive directed displacement, and no
get-up attempt. This is a real progression from the earlier three mastered
precursors: the body now discovers prone support and closes a retained
translated support cycle rather than merely wobbling in place.

Rolling remains unresolved and is reported as a failure, not inferred from
translation. The graph made 228 side-lying attempts without a gravity-axis
class transition. The investigation nevertheless established useful negative
results. Repeating the compound program with the largest unsigned orientation
change merely oscillated within one support basin. Signed vestibular escape
improved selection but still required programs to be scoped by support phase.
The final system synthesized three independently grounded, five-member bundles
for three support phases and scaled their hold time by discovered bundle width;
none crossed the side-lying boundary. The next rolling mechanism therefore
needs sequence learning over changing intermediate gravity vectors, not a
stronger preference for any single repeated compound action.

## Arbitrary-order developmental program trajectories

The programming-tree and budgeting work now supplies that missing sequence
representation as a general faculty, not a rolling special case. A situated
capability holds a graph budget, a current grounded program and a reusable
inventory of verified program transitions. Rules construct arbitrary-order
simple prefixes from that current program. Orientation span, boundary crossing,
energy and peak load remain separate Pareto coordinates; curiosity only breaks
ties among the non-refuted frontier. The selected path has no direct actuator
authority. The hard-real-time humanoid bridge releases exactly its next
grounded compound program and waits for the ordinary physical receipt.

`results/humanoid_floor_mobility_v11.json` verifies that this is active rather
than decorative: 98 developmental transition edges produced prefixes through
depth nine and one selected path. It did not complete a replay or add a ninth
milestone, so side-lying remains an open developmental failure. The run also
exposed scheduling and retention costs; the final rules isolate trajectory
construction from unrelated Pareto sweeps and bound retained candidates. Full
registered gates, failed intermediate designs and the remaining functional-
equivalence residual are recorded in
`PROGRAM_TRAJECTORY_BUDGET_RESULTS.md`.
