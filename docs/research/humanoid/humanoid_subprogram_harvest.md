# Humanoid subprogram harvesting

Existing motor experience can warm-start a body without copying a named gait
policy or granting old commands immediate authority. The harvested unit is a
shape-indexed motor subprogram already minted by graph learning.

`scripts/harvest_humanoid_subprograms.py` mechanically unions program facts
from compatible libraries beneath the existing order-N body-shape identity
and gives imported graph objects fresh local ordinals. It does not deduplicate,
score, or decide which programs are useful. Each restored program is exposed
as a relation-system signature. The graph's native `ShapeDecode` recognizes
programs already covered by an earlier codebook entry and relates duplicates
to their canonical program before activation.

At load time the normal graph path still applies:

1. ShapeDecode must exactly recognize the name-free body relation system and
   controller dynamics.
2. ShapeDecode must resolve program identity inside that body codebook.
3. Every opaque member must rebind to a current effector model.
4. Imported programs remain output-null and require a local receipt.
5. Viability and structural gates remain authoritative.
6. Only successful local evidence permits consolidation into the new
   repertoire.

In the first harvested run, 34 distinct historical programs were added to the
11-program base library. The graph admitted eight, recalled and locally
verified two, and retained twelve additional programs. Directed progress rose
from 0.378 m to 0.530 m while tilt and bundle width also rose, so the result is
kept as a Pareto tradeoff rather than called a scalar improvement.

This implementation harvests exact-shape humanoid programs. Cross-body reuse
should harvest consequence templates rather than tokens: body-frame effect,
temporal shape, energy, uncertainty, support transition, and structural load.
A novel body can then use analysis by synthesis to reproduce that consequence
with its own effectors before the same receipt gate grants authority.

## Long plans are hints, not macros

A locally verified short chunk may eventually earn normal motor authority. A
long transition chain has a different representation: an
`EmbodiedMotorPlanHint` containing ordered, output-null stage shapes. The
immediate graph sheet uses `ShapeDecode` only to recognize that a hint covers
the active task. That recognition creates a `SystemTwoEscalation`; the
interruptible integration sheet can then associate exact stage shapes with
grounded local programs as candidate search basins.

Neither a hint nor one of its stages can select an effector, set
`action_ready`, or enact a program. The hint says where analysis by synthesis
might usefully begin. Normal body grounding, consequence prediction, Pareto
tradeoffs, envelope constraints, and physical receipts still decide what is
executed.

The seed library includes morphology-neutral relation systems distilled from:

- spinal phase generation and descending modulation;
- developmental synergy refinement and bilateral symmetrization;
- predictive, reactive, and biomechanical control;
- sequential-contact whole-body control (WoCoCo);
- centroidal MPC plus hierarchical whole-body realization; and
- vision-conditioned parkour planning.

Named manoeuvres are represented the same way. The forward-roll prior encodes
entry momentum, excluded head contact, a distributed contact chain, energy
redirection, and support reacquisition. The dynamic high-angle-of-attack Cobra
encodes its energy/control-authority precondition, coupled-axis and structural
constraints, dynamic pitch-up, and a recoverable exit envelope. Neither
contains joint names, fixed timings, torques, or control-surface commands.

`results/humanoid_motor_plan_hint_library_v1.json` is the first version-5
artifact. It holds 10 plan hints and 52 stage shapes alongside mechanically
harvested exact-body programs. Provenance URLs stay on the hint nodes so later
experiments can measure which prior narrowed search, failed to transfer, or
was contradicted by receipts.

Abstract priors and exact programs expose a deliberately small shared routing
alphabet: motor-task context and motor-task phase. ShapeDecode can therefore
route a conceptual stage such as load acceptance or landing preparation toward
locally grounded chunks without pretending that the prior knows the body's
joint identities. The native composer treats those chunks lexicographically:
among candidate additions that already improve forward synthesis, members of a
hinted basin are explored first. A hint cannot admit a non-improving candidate.

The first routed runs show the distinction in practice. Epoch 89 recognized
four locomotion hints but, before the shared routing alphabet, produced no
local basins. Epoch 90 produced ten stage-to-program basin bindings, stayed
upright, and shifted from 0.184 m to 0.318 m directed progress while reducing
recovery actions from 82 to 62. The next warm lifetime traded some displacement
(0.245 m) for lower peak tilt (0.070 versus 0.110), more support alternations
(49 versus 46), 133 learned-walk actions, and only 46 recovery actions. These
are retained as different Pareto outcomes, not ranked by a collapsed reward.

Native MotorCompose caching now fingerprints every state, policy, model,
synergy, expansion, and basin input that its search reads. This prevents a
composition cached in one lifetime—or before a learned-model update—from being
mistaken for the same search problem in another graph.

## Task-dependent recruitment and proprioceptive focus

The task query is now graph state rather than a runner-selected constant.
Ordinary locomotion asks the hint library for locomotion shapes; an active
self-takeoff drive changes the query to `self_takeoff`, and closing that drive
restores locomotion. Native composition reads the resulting basin relations
but restricts them to the graph's active task context. This prevents a useful
takeoff basin from silently becoming a walking default.

Epoch 92 verified recruitment: considered hints increased from four to six
and the graph made 52 stage bindings to nine local programs. It also exposed a
temporal-resolution failure. The controller produced upward momentum and lost
support, but long motor holds sampled the body only after vertical momentum
had become negative. The curriculum correctly rejected those intervals as
self-authored takeoff.

The response horizon therefore gains a graph-native proprioceptive focus.
While a ballistic drive is active and support remains, the graph divides the
chosen hold by the discovered actuator dimensionality, down to the irreducible
one-physics-receipt floor. It scales the episode and trial predictions by the
same ratio; the underlying learned program duration remains intact. This is a
generic change of sensory-control resolution near a contact transition, not a
fixed control frequency or a host-side jump command.

Epoch 93 then recorded the previously missing causal sequence: positive
whole-body vertical momentum at zero support, two aerial receipts, and
subsequent touchdown. Peak upward momentum was 8.29 kg·m/s; the body remained
upright and reached 0.217 m directed progress. Peak ballistic height gain was
only 5.5 mm against a 20.3 mm target, so the evidence establishes takeoff and
landing but does not claim mastery of the jump. That distinction is preserved
in `results/humanoid_coordination_epoch93_topology_focused_takeoff_v1.json`.
