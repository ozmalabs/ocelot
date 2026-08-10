# CMU motion-topology bootstrap

This bootstrap distils observed human movement into output-null graph topology.
It does not imitate poses, replay trajectories, name target actuators, or retain
floating-point kinematics. Its purpose is to give analysis by synthesis better
places to look for locally realizable motor programs.

## Evidence subset and licence

The checksum-pinned subset contains nine trials from the CMU Graphics Lab
Motion Capture Database:

- walk, turn, and return along the opposed direction;
- backwards walking and running;
- jumping;
- run-to-roll and dive-to-roll transitions;
- getting up from prone, side-lying, and supine configurations.

The database permits research and commercial use but prohibits resale of the
source data, including converted source data. Raw ASF/AMC files are therefore
downloaded into the ignored `data/cmu_mocap/raw/` directory and are never
redistributed. The checked-in topology is a derived experimental result: it
contains no angles, poses, root positions, joint names, numerical kinematics,
or commands.

The data used in this project was obtained from mocap.cs.cmu.edu. The database
was created with funding from NSF EIA-0196217.

## Reproducible pipeline

1. `scripts/download_cmu_mocap_subset.py` downloads only files declared in
   `data/cmu_mocap/manifest.json` and verifies every ASF and AMC SHA-256.
2. `scripts/harvest_cmu_motion_topology.py` performs offline forward kinematics.
   Euler channel order follows CMU's reference viewer implementation: each
   channel rotation is prepended, and a bone's local rotation is
   `axis_basis × motion × inverse(axis_basis)`.
3. Contact thresholds come from the held skeleton, not tuned distances. A toe
   segment supplies definite-contact clearance, a foot segment supplies
   definite-flight clearance, and the lower effector resolves the anatomical
   ambiguity band.
4. Continuous interface measurements collapse into categorical relations:
   support topology, contact dimension, mass-height energy trend, kinetic
   energy trend, and translation trend.
5. Repeated frames collapse into recurrent topology states and counted graph
   transitions. They are not unrolled into a long trajectory.
6. `scripts/gen_cmu_motion_topology_seed.py` serializes the categorical result
   as an integer-only seed.

The raw/interface side is allowed to use floating point because ASF/AMC files
contain continuous measurements. The cognition-side topology and seed contain
no floating-point values.

## Graph representation

The current nine clips yield:

- 6,800 observed frames;
- 73 distinct contact/height-energy basin states;
- 178 recurrent transitions;
- nine output-null motor-plan hints.

Every evidence clip points to observed topology states and transitions. Every
plan-hint stage abstracts one state, while
`can_transition_to_embodied_motor_plan_hint_stage` edges preserve the recurrent
transition graph and its integer observation counts. This representation can
branch and cycle; stage ordinal records first observation rather than imposing
a fixed controller depth.

Each stage also targets an `EmbodiedMotorConsequenceRoutingShape` keyed by
task context, phase, and categorical height-energy relation. A locally grounded
program reaches that shape only after its own receipt has established the same
consequence. At composition time the native graph traversal is therefore:

`current support topology -> observed successor stage -> consequence shape <- locally grounded program`.

The broad task/phase match remains a search index. It is not an active motor
preference. This distinction prevents a motion clip from granting authority to
an unobserved action or materializing the stage-by-program Cartesian product.

“Forward” is deliberately absent from stage signatures. Translation is an
orientation-relative `increasing`, `decreasing`, or `held` relation. Subject
47's walk-turn-return trial explicitly records opposed translation without
asserting that one sign is the canonical movement direction.

## Authority and evaluation

The seed has no rules and every evidence, state, transition, hint, and stage has
zero output authority. Humanoid integration uses the existing hint pipeline:
task-shape matching may expose a search basin, but receipt-backed predicted
improvement remains primary and a hint can only break an exact tie.

Evaluation must report recruitment separately from movement. Loading a motion
topology is successful only if it:

- adds no System 2 escalation merely by existing;
- does not destabilize the cold controller;
- never selects a worse predicted program over better situated evidence;
- eventually reduces search or practice needed for an equally good or better
  locally grounded program.

## Measured integration result

The controlled native test constructs two equally predicted local program
combinations. Without compatible topology the ordinary deterministic choice is
retained. With a compatible locomotion support transition, the demonstrated
consequence basin wins the tie. A context-mismatched take-off topology has no
effect. A topology hint still cannot make a worse predicted candidate win.

The full cold humanoid run provides a deliberately less flattering but more
useful result:

| Measurement | Existing integer bootstrap | CMU consequence routing |
|---|---:|---:|
| Broad task/phase search-index programs | 156 | 156 |
| Programs matching the observed consequence alphabet | — | 18 |
| Directed progress | -0.1365668874 | -0.1365668874 |
| Support alternations | 39 | 39 |
| Peak tilt | 0.0913538010 | 0.0913538010 |
| Minimum height | 1.1977431326 | 1.1977431326 |
| System 2 escalations caused by hints | 0 | 0 |
| Wall time | 150.52 s | 156.06 s |

Thus the demonstration-derived consequence alphabet narrows the relevant
program set from 156 to 18 (88.46%) without changing the cold trajectory or
destabilizing the controller. It does **not** yet improve that trajectory, and
the current end-to-end Python/PyBullet experiment is about 3.7% slower. The
benefit demonstrated here is deterministic search specificity, not a gait win.

The same seed and native composer were then run on the official HumanoidBench
H1 body at revision `cb1189039151c8aadaaa987b442da54383c87fab`. This is a
second unseen morphology with 19 joints and 39 opaque actuator choices. Its 61
locally grounded task/phase programs narrowed to nine consequence-compatible
programs (85.25%). The controller still failed the walking task and first fell
at action 17, so this is cross-morphology routing evidence, not a transfer-
walking claim. The run also exposed and fixed drift in the simulator boundary:
H1 now accepts weighted graph bundles and situated references and reports the
same sensor, energy, power, and contact receipts as the current embodied loop.

An intentionally ungated first integration materialized generic stage matches.
It preserved the same trajectory but took 189.40 seconds. Excluding
consequence-requiring stages from the generic matcher and resolving them in the
native composer removed that Cartesian scan; the rejected result is retained
as evidence for the architectural boundary.

## Practice check

A two-epoch curriculum check restored one recognized body shape in epoch two,
but the saved library contained no mature motor program to recall. The second
epoch improved directed progress from -0.0190 m to 0.2727 m and added two
support alternations, while peak tilt rose from 0.0914 to 0.1565. Because
`warm_start_program_count` and `warm_start_memory_recall_count` both remained
zero, those changes cannot honestly be attributed to program warm-start. They
show that the shape-memory path is live and that the current short curriculum
does not yet mint a reusable program. Closing that receipt-to-library gap is
the next learning task; it is not papered over by calling epoch variance
practice.
