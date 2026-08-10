# Embodied capability bootstrap

The bootstrap layer supplies compact relation systems that tell analysis by
synthesis where useful motor basins are likely to exist. It does not ship
joint trajectories or actuator commands. Every hint has zero output authority;
the current body must still discover a local program and ground it with a
physical receipt before that program can act.

This preserves the project's central constraints:

- there is no canonical pose or canonical forward direction;
- a prior describes topology, such as support → impulse → flight → contact,
  rather than a timed trajectory;
- body-part identities and command magnitudes remain local discoveries;
- ShapeDecode binds a hint stage to a situated, receipt-grounded program;
- capability residuals, not the presence of a hint, decide whether cognition
  must deepen;
- all new cognitive seed values are integers. Floating point remains confined
  to the simulator/interface boundary.

## Shipped basin families

`embodied_capability_bootstrap` currently supplies ten morphology-neutral
families: supported range discovery, righting/get-up, protected descent and
rolling, disturbance response, cyclic contact locomotion, coordinate-frame
discovery, whole-body compound outcomes, reach/contact/release, hybrid
effector-regime transitions, and ballistic takeoff/landing.

Each family has four topological stages. Four is descriptive here—not a fixed
controller depth or timing constant. The order-N capability fabric may refine,
compose, omit, or extend those stages from receipts.

The coordinate-frame prior is deliberately explicit: repeatable displacement
in either sign is locomotor capability. Alignment between a learned body-frame
movement and a situated task-frame goal is a separate residual. “Backward” is
not a failed gait; it is forward under the opposite orientation relation.

## External seed sources considered

The CMU Graphics Lab Motion Capture Database is the best first raw-motion
harvest source. Its use terms permit research and commercial use (but not
resale of the database), and it contains walking, running, jumping, rolling,
obstacle traversal, acrobatics, and dedicated ground get-up sessions. We use
those clips as evidence from which to extract contact and energy topology; raw
poses must never be treated as actuator authority.

Other strong sources are not suitable as a repository dependency:

- AMASS is broad, but its dataset license is personal, non-transferable, and
  restricted to non-commercial uses.
- LaFAN1 contains useful walk, obstacle, crawl, fall, and get-up sequences, but
  is CC BY-NC-ND 4.0 and therefore unsuitable for derived redistributable
  bootstrap assets.
- MoCapAct includes physical actions as well as kinematics, but its smallest
  rollout bundle is about 46 GB, targets a particular dm_control humanoid, and
  would encourage copying controller outputs rather than learning local causal
  effects.

The built-in seeds therefore encode only published, morphology-neutral
relations with provenance URLs. A later CMU harvester can extract candidate
contact sequences into the same output-null format and let ShapeDecode decide
whether they add a genuinely new basin.

## Cold-start integration

The humanoid seed now depends on `embodied_capability_bootstrap`. At episode
start, task-shape matching makes relevant hints cheap defaults without opening
System 2. As a synthesized motor program earns its first receipt, the graph
mints a mechanical name and minimal task/phase signature for it. This fixes a
previous asymmetry where restored library programs were ShapeDecode entries but
programs learned during the current episode were anonymous and therefore could
not be reached by bootstrap hints.

Each grounded program enters a graph-held task/phase routing shape by exact
relation equality. The routing node is already the decoded shape; running
ShapeDecode again through non-unique situated program names was both ambiguous
and quadratic. Built-in stages point to the same routing nodes, so
stage-to-program basins are graph paths rather than a materialized Cartesian
set of every hint stage and every learned program.

The built-in broad matcher uses batch-atomic rules on the hard sensorimotor
sheet and creates a search index, not an active preference. Demonstration
stages that require an observed consequence are excluded from that generic
matcher. The native composer resolves those stages through current support,
the demonstrated successor topology, and an exactly matching locally observed
consequence shape. This avoids both one-step-per-program escalation and the
stage-by-program Cartesian product.

The native composer treats a basin hint as a tie-break between candidates with
equal predicted improvement. Receipt-backed situated evidence remains primary.
An earlier hinted-first comparator allowed a broad prior to select a worse,
though still improving, combination; in the humanoid protocol that changed a
stable trajectory into a fall. A prior that can overrule better evidence has
silently acquired output authority. The corrected ordering prevents that.

All bootstrap and integration rule constants are integers. The PyBullet state,
forces, and commands remain floating point only at the simulator interface.
Actual motor authority remains behind the existing receipt, viability,
material-envelope, and collapse gates.

## Evaluation contract

Do not collapse humanoid competence into signed progress. Report at least:

- path length and displacement vector;
- task-frame alignment separately from locomotor displacement;
- support transitions/contact-cycle evidence;
- falls, tilt, height, and load-envelope receipts;
- hint recruitment and unique basin bindings;
- compound outcome width and residual closure;
- energy and reversals as trade-offs, not universal faults.

The primary regression is an identical cold protocol before and after the
bootstrap dependency. A useful seed must be recruited, bind locally grounded
programs, preserve zero output authority, and avoid increasing cognitive
escalations merely because the seed exists.

## Measured cold humanoid result

The developmental-chunks protocol was run for one 360-action epoch from the
same cold initial condition. Before the evidence-primary tie-break, the broad
basin prior caused a fall despite having nominally zero output authority. With
the corrected composer, the recruited run reproduces the no-bootstrap control
trajectory exactly on every reported locomotor and stability measure:

| Measure | Cold control | Recruited bootstrap |
|---|---:|---:|
| Recognized hints | 0 | 7 |
| Broad task/phase search-index programs | 0 | 156 |
| Hint-triggered System 2 escalations | 0 | 0 |
| Support alternations | 39 | 39 |
| Locomotor path length | 0.494533 m | 0.494533 m |
| Minimum body height | 1.197743 m | 1.197743 m |
| Peak tilt | 0.091354 | 0.091354 |
| Signed task-frame progress | -0.136567 m | -0.136567 m |

The last row is not a locomotion score. The body generated stable displacement
and contact cycling in the orientation opposite the requested task vector.
That is the remaining frame-alignment problem; mechanically, backwards is
forwards under the opposite orientation relation.

This result establishes safe recruitment rather than an immediate gait
improvement. The subsequent CMU harvest adds consequence-specific routing:
the observed context/phase/height-energy alphabet narrows those 156 indexed
programs to 18 relevant programs while preserving the exact cold trajectory.
The controlled native composition test shows that compatible observed topology
can select an equally predicted demonstrated basin without selecting a worse
one. See `docs/cmu_motion_topology_bootstrap.md` for the extraction method,
licence boundary, performance measurements, and remaining practice gap.
