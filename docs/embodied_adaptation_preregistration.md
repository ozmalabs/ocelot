# Preregistration: from-scratch embodied adaptation

Status: confirmatory follow-up protocol frozen after engineering pilots. This
is not presented as a pre-pilot preregistration. The final engineering pilot
used simulator seed `0`, goal `(2,0,0)`, 120 decisions and two babble samples
per token. Final goal distances were:

| Morphology | Learning | Shuffled model | No learning | Random |
|---|---:|---:|---:|---:|
| R2D2 | 0.271 | 6.149 | 2.156 | 2.258 |
| Husky | 0.153 | 1.656 | 5.503 | 3.121 |
| Racecar | 0.211 | 15.959 | 4.278 | 1.654 |

All three learning pilots crossed the graph-held reach threshold; none of the
shuffled pilots did. These observed numbers are disclosed and remain
descriptive. The new seed, three-goal matrix and thresholds below have not
been run as a batch.

## Claims under test

**H1 — acquisition.** Starting with zero body-specific samples, the graph will
sample every opaque actuator and update a distinct graph-resident forward model
from its observed consequences on R2D2, Husky and Racecar.

**H2 — prediction.** Repeated interventions will reduce pre-update one-step
forward-model error relative to the first intervention with the same actuator.

**H3 — use.** After motor babble, graph-selected actions will make more
open-plane goal progress than a coverage-matched graph-native no-learning
control and graph-native random-like control under the same physics budget.

**H4 — model specificity.** An intact learned actuator/model
association should outperform a shuffled-model control that preserves learned
values and counts but cyclically assigns them to the wrong opaque actuator.
The arm is implemented, but the confirmatory matrix is **not run**. The pilot
result above is not substituted for it.

Collision avoidance and obstacle navigation are not primary hypotheses. The
arena is an open plane; raw contact counts are retained as diagnostics but
include normal ground support.

## Fixed design

Morphologies, in reporting order:

1. `r2d2`
2. `husky`
3. `racecar`

Simulator settings:

- PyBullet `DIRECT`;
- timestep `1/120 s`;
- 24 physics frames per graph action (`0.2 s`);
- gravity `(0, 0, -9.81)`;
- deterministic overlapping pairs enabled;
- 120 unmeasured settling frames after reset;
- initial base pose supplied by the body hardware record;
- flat bundled `plane.urdf`;
- no sensor noise or domain randomisation.

Fixed graph/control seed: `82001`. PyBullet physics is deterministic in this
protocol. Repeating a learning, no-learning, or shuffled run with a different
integer seed but the same goal would therefore be an exact pseudoreplicate.
The seed is retained because it changes the graph-native random-control
schedule; it is not treated as a source of independent physical subjects.

Fixed world-frame goals, metres: `(3, 0, 0)`, `(0, 3, 0)`,
`(3, 3, 0)`. They are executed and reported in that canonical order.

Each `(morphology, seed, goal, arm)` is a completely fresh run:

- new PyBullet client;
- new `WorldAdapter`;
- freshly loaded `embodied_adaptation` seed;
- no checkpoint;
- no copied nodes, action models, counts or policy state;
- every `ActionModel` begins with zero experience and zero effect estimates.

This gives nine fresh starts per arm: three morphologies by three goals. Fresh
means no state transfer, not statistical independence. The three deterministic
goal conditions within a morphology are repeated tasks for that body, not
independent biological subjects. A byte-for-byte repeated run may be used as a
reproducibility check but is never counted as additional evidence.

## Arms

### Learning

The graph first motor-babbles until every one of the nine opaque actuator tokens
has three receipt-backed observations: exactly 27 babble decisions. It then
selects with the learned forward models for 93 navigation decisions. Learning
remains enabled during navigation.

### No-learning control

A fresh graph uses the seed's graph-native, deterministic coverage-matched
round-robin policy for 120 decisions. It receives the same observations but the
control close rule does not update any `ActionModel`. Python does not select an
action. This is the primary implemented control; it is a no-learning control,
not described as statistically random.

### Random control

A fresh graph makes 120 choices using the seed's reproducible graph-native
deterministic hash over epoch, control seed and actuator ordinal. Learning is
disabled. It tests whether a fixed
round-robin schedule is accidentally poor, while retaining graph provenance
for every selected token.

### Shuffled-model control

This secondary arm performs the same 27-decision babble phase as Learning.
Before navigation, a preregistered cyclic permutation associates each opaque
actuator with the next actuator's learned model, wrapping at the final ordinal.
Values and experience counts are unchanged. The permutation is morphology
blind and fixed before outcomes are read. Navigation then runs for 93 decisions
without correcting the shuffled association.

The shipped runner exposes this arm, but H4 remains **not run** until the new
confirmatory matrix is executed. A pilot is not a confirmatory pass.

No arm may call a Python policy as fallback. Missing graph selection is a run
failure.

## Recorded transition

The shipped runner records for every decision:

- morphology, seed, goal, mode and decision index at episode/result level;
- selected opaque token, graph-authored `MotorTrial` token, and a checked
  simulator receipt for the same token;
- graph decision kind and resulting trial status;
- graph-computed pre-update prediction error in learning mode;
- contact count and effort;
- graph-measured goal distance, incremental progress and reached flag;
- initial/final base position and goal position at episode level;
- final `ActionModel` rows with token, ordinal, experience count and learned
  effect attributes.

Raw transition records are the source of truth. Summaries must be reproducible
from them. Failure reporting lists exact morphology, seed, goal and mode, plus
token and epoch whenever action selection had begun; unavailable fields are
explicitly null. A bare failure count is prohibited.

## Metrics

### Non-vacuity

- **Token coverage:** tokens with `experience_count >= 3` divided by nine.
- **Graph provenance:** fraction of applied tokens for which the same token was
  present on an issued graph `MotorTrial`.
- **Model mutation:** number of `ActionModel` nodes whose count and at least one
  of `mean_forward`, `mean_lateral`, `mean_turn`, `contact_ema`, or
  `effort_ema` changed from initialization.
- **Model diversity:** maximum pairwise distance between learned
  `(mean_forward, mean_lateral, mean_turn)` vectors.

### Prediction

For a learning transition, before updating the model, the seed records:

```text
prediction_error =
  sqrt((pred_forward-obs_forward)^2
     + (pred_lateral-obs_lateral)^2
     + (pred_yaw-obs_yaw)^2)
```

This is an explicitly mixed-unit engineering diagnostic (metres and radians),
not a physical norm. The trace retains predicted and observed forward, lateral
and turn components, so translation and yaw changes are also reported
separately. For each token, compare its first and third babble errors. The H2
statistic is the median paired fractional reduction across the nine tokens,
then summarized per morphology. Zero denominators are reported and excluded
from ratios, never replaced with epsilon; absolute change remains reported.

### Navigation

- initial and final planar goal distance;
- normalized progress:
  `(initial_distance - final_distance) / initial_distance`;
- reached: any graph-measured distance `< 0.65 m`;
- path length reconstructed from successive raw pre/post base positions;
- path efficiency for reached runs:
  `initial_distance / max(path_length, initial_distance)`;
- raw contact count and raw-contact decision rate.

The adapter's contact stream includes expected wheel/ground support contacts;
there are no obstacles in the primary arena. It is therefore not a collision
metric. Collision count is **not measured** in this MVP, and no collision
avoidance claim is made.

The runner retains the raw pre/post position for every transition, so path
length and path efficiency are reproducible reporting metrics. They are
descriptive rather than primary gates: a greedy controller may reach by a
long path while still establishing the narrower adaptation claim.

## Primary thresholds

The narrow functional demonstration is supported only if all hold:

1. PyBullet runs all three morphologies; no body is silently skipped.
2. Every learning run has token coverage `1.0`.
3. Graph provenance is `1.0` in every arm.
4. Every learning run mutates all nine model counts, and each morphology has
   model diversity greater than `1e-4`.
5. H2 median prediction-error reduction is positive in each morphology and at
   least `10%` when all token pairs are pooled.
6. Median normalized navigation progress is positive in each morphology.
7. Within each morphology, Learning exceeds both No-learning and Random median
   normalized progress by at least `0.05`.
8. Each of No-learning and Random changes zero `ActionModel` counts or learned
   effect attributes.

Reach rate and path efficiency are reported but are not primary gates: a short
open-loop horizon may show useful adaptation without reaching all three goals.

H4 is supported only if the confirmatory shuffled matrix is run and intact-model
median progress exceeds shuffled-model progress in every morphology, with a
pooled difference of at least `0.05`. Otherwise H4 is refused.

Any failed non-vacuity condition invalidates H2/H3 for that run rather than
being averaged away. Failure of one morphology refuses the cross-morphology
claim; successful morphologies may be reported individually.

## Analysis

Report all nine run rows per arm and morphology-level medians across the three
fixed goal conditions. Compare arms within the same morphology and goal. These
deterministic task conditions do not justify confidence intervals, p-values,
or a population-generalization claim; the analysis is a fixed-case functional
demonstration.

No goal, horizon, actuator lattice, model rate, penalty weight or threshold is
tuned after observing these runs. A necessary engineering correction creates a
new protocol version and reruns every arm.

## Threats to validity

- The URDF actuator wiring is supplied anatomy, not learned actuator anatomy.
- All bodies share the same two-dimensional command lattice.
- PyBullet dynamics and bundled URDFs may favor the fixed policy.
- Deterministic physics limits external validity. Additional integer seeds
  would only vary the graph-native random-control schedule, not create
  independent learning-arm evidence.
- Online sample means assume approximately stationary action effects despite
  velocity and orientation context.
- A one-step greedy forward controller is not a planner, especially for
  Ackermann nonholonomy.
- Body-frame position/yaw omits richer joint-state contingencies.
- Open-plane progress does not demonstrate obstacle navigation.
- The three named mobile bases do not span general body-plan space.
- Hardware configuration contains body-specific joint wiring. The result tests
  learning dynamics and actuator consequences, not discovering joint topology.
- Shared seed rules are a strong inductive prior; “from scratch” refers only to
  body-specific graph state.
