# Learning kinematics through the active humanoid curriculum

## Question

What representation should an embodied learner use when it must discover its
own kinematics from action receipts rather than receiving a URDF-derived
Jacobian, inverse-kinematics solver, named anatomy or gradient-trained policy?

The coordination curriculum now doubles as an experimental instrument for that
question. PyBullet retains ground truth only as the physical world and
evaluator. Jabberwock receives ordinary whole-body position, proprioceptive and
contact observations.

## Graph models compared

Four approaches receive the same action sequence and are scored on every
receipt before updating:

1. **Global additive:** an opaque action's mean body-relative displacement at
   each distal point.
2. **Support-conditioned hierarchy:** a support-regime sheet initialized from
   the global model with morphology-derived prior strength.
3. **Interaction residual:** the support-conditioned sum plus the measured
   non-additive residual of an actuator pair. Residual authority is
   `n / (n + support-prior-strength)`, so one observation cannot override the
   reusable primitive model.
4. **Context arbitration:** a graph-held track record selects global,
   conditioned or interaction prediction separately by distal point, support
   regime and primitive/compound class. Selection happens before the current
   receipt updates the track record.

The graph infers four terminal points from opaque parent-child relations. The
mechanical boundary does not identify hands, feet, arms or legs.

External balance challenges are excluded from motor-kinematics learning because
their receipts correctly fail the motor-only verification gate.

## Curriculum extension

The ordinary synergy stage provided only one observation per actuator pair.
The first study pass showed that giving a one-shot interaction residual full
authority made held-out compound prediction worse.

The graph now adds an active kinematic-reprobe stage. It:

- considers only actuator pairs already established by causal probing;
- prioritizes the pair with the largest unresolved endpoint residual;
- contracts the action horizon using sensed support count; and
- stops when every observed pair has one receipt per support channel.

For this body that produced 42 additional compound probes. The host loop has a
body-derived safety bound but does not select pairs, endpoints or sample counts.

### Inverse-use reach gate

Forward prediction is now used for action, not only scored after the fact.
After reprobe, the graph:

- considers only inferred terminal points that are not support sensors;
- projects their learned endpoint consequences onto an abstract body-relative
  reach direction;
- chooses the closest consequence on the experienced affordance manifold;
- hides the originating action behind that endpoint target;
- compares eligible primitive and causally verified compound predictions by
  expected residual; and
- closes success only from the selected point's measured receipt.

The graph selected terminal point 27 and opaque actuator
`humanoid_actuator_034`. Its predicted and measured displacement were both
`(-0.021413, -0.009679, -0.009751) m`, reducing endpoint error from
`0.025441 m` to zero in one attempt. No joint name, endpoint label, host-side
target scale or inverse solver entered selection.

The deliberately harder development pass in
`results/humanoid_kinematics_study_v10.json` targeted a free direction outside
the experienced one-action affordance manifold. Its first action reduced
error, but repeated commands reused reset-local consequences after the joint
configuration had changed and final error grew from `0.0254 m` to `0.0470 m`.

The graph now contains one opaque coordinate node per sensed actuator group.
Single-action receipts anchor the selected command's pre/post coordinate.
During analysis by synthesis, the learned endpoint consequence is scaled by
the remaining distance to that post-coordinate. This is a relational
configuration context: Python mirrors raw joint position but never supplies a
joint name, direction, Jacobian or inverse.

The same arbitrary-direction control then diversified its action sequence and
reduced final error to `0.0276 m` in v12, but still failed the `0.0127 m`
criterion. A body-relative constant-velocity prediction was also tested in
v13; it produced some accurate late predictions but worsened aggregate
action-level prediction and was removed. These negative results show that a
free direction can lie outside the locally reachable set and that transient
momentum needs learned persistence rather than undamped extrapolation.

The next positive curriculum gate therefore constructs a target by summing
two distinct learned endpoint affordances. The target is outside the
single-action training set but inside the graph's demonstrated local
capability. In v15 the graph selected opaque basis actions
`humanoid_actuator_034` and `humanoid_actuator_032`, alternated between them as
configuration changed, and reduced error from `0.028684 m` to `0.003695 m` in
five receipt-backed attempts. The tolerance, `0.006208 m`, is half the smaller
learned basis consequence, so completing only one component cannot pass.

The nested two-affordance search initially expanded to an `844 MB` generated
seed. Materializing per-model projections and then selecting primary and
secondary bases in separate graph rules reduced it to `1.19 MB`; the focused
test runtime fell from `73.6 s` to `1.1 s`. Selection remains graph-native.

Corrected follow-up runs made the actuator-ordinal boundary explicit and
constrained remaining-effect scale to the physical servo interval `[0, 1]`.
The graph also records goal-scoped negative outcomes so a worsening candidate
is temporarily avoided. A separate, support-prior-shrunk context residual is
learned only from receipt-verified single-reach transitions and applied to
later predictions. In v22 this state-transition model selected a causal
compound and reduced error from `0.028684 m` to `0.006185 m` in three attempts,
just below the `0.006208 m` criterion. v20/v21 remain negative controls.

## Canonical result

The canonical paired-prequential result remains
`results/humanoid_kinematics_study_v11.json`. The historical sequential
composition result is `results/humanoid_kinematics_study_v15.json`; the latest
corrected frontier is `results/humanoid_kinematics_study_v22.json`, with v21
recording the preceding extended-horizon exhaustion as a negative control.
The compact record is
`results/humanoid_kinematics_study_summary_v1.json`.

The run contains 2,048 prequential point receipts across four inferred terminal
points. Locomotion remained intact: `0.252 m`, 29 support alternations, no fall.

| Evaluation stratum | Receipts | Conditioned vs global | Interaction vs global | Arbitration vs global |
|---|---:|---:|---:|---:|
| All | 2,048 | 0.88% better | 2.08% better | 1.90% better |
| Single actions | 1,696 | 1.16% better | 1.16% better | 1.01% better |
| Compound actions | 352 | no change | 4.91% better | 4.62% better |
| Previously seen pairs | 180 | no change | 9.87% better | 9.28% better |
| Unseen pairs | 172 | no change | no change | no change |
| Unilateral support regime 2 | 292 | 5.98% better | 5.97% better | 4.63% better |

Abstention on unseen pairs is important: the interaction model contributes
exactly zero without causal evidence, recovering the additive prediction rather
than guessing a correction.

## What the data currently says

The best current approach is hierarchical:

1. retain global primitive structure as the low-variance default;
2. specialize by support context when receipts support it;
3. represent measured composition failures as residuals, not replacement
   policies;
4. shrink sparse residual evidence toward zero; and
5. learn which representation to trust in each embodied context.

No fixed representation won all three preliminary lifetimes. Context
arbitration nearly matches the best fixed arm overall and learns substantial
support-specific preferences, but sparse pair identity remains important.
The active reprobe stage supplies the missing reliability evidence and raises
seen-compound improvement from an unstable one-shot result to 9.28% under
prequential arbitration. The inverse gates show reliable one-step inversion
and a corrected two-affordance composition pass. The new
`body_direction_at_learned_scale` mode forces a causal compound whenever a
spanning affordance exists. Its first withheld-direction probe exhausted the
morphology-derived horizon, an honest reachability negative control. The next
requirement is directional coefficient learning and momentum-conditioned local
reachability, rather than selecting a fixed two-action sum. The planner now
computes and enacts graph-derived per-token coefficients, and reach-only
receipts update momentum gains. The momentum rule is phase-gated so it is not
evaluated during calibration or walking; the full 180-action integration
remains the performance gate for this expanded graph.

## Limits and next experiments

This is a deterministic developmental experiment on one morphology, not yet a
population result. Point receipts within a trajectory are not independent
replicates. The study should next add:

- independent morphology families and withheld shapes;
- relational context over the wider joint configuration, not only the
  commanded actuator coordinate;
- goal-scoped transition models that predict incremental endpoint change after
  prior commands, including action duration and body momentum;
- active sequential probes that learn momentum persistence and discriminate
  local linear correction from reusable motor chunks;
- held-out actuator pairs to measure relational generalization;
- changed link lengths and locked joints;
- mid-episode damage to compare local revision with full relearning; and
- energy/sample Pareto curves for active versus uniform probing.

Those experiments can use the same prequential instrument. Simulator
kinematics should remain evaluator-only throughout.
