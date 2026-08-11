# Biology-derived motor-control upgrade

## Scope

This upgrade addresses the next motor-control gaps identified after temporal
program chaining. It uses biological findings as computational constraints,
not as claims that graph nodes reproduce named brain structures.

The implementation preserves the project boundary: motor state, predictions,
uncertainty, preparation, release, timing, and learning are graph data and
Rust-executed rules. Python mirrors simulator receipts, mechanically enacts
the graph-authored command, and reports results.

## Research-to-build plan

| Evidence | Computational implication | Graph implementation | Status |
|---|---|---|---|
| Cerebellar Purkinje activity carries both predictive and feedback-related signals used to form sensory prediction error ([Streng et al., 2018](https://doi.org/10.1038/s41467-018-03541-0)) | A forward model needs both a predicted consequence and receipt-specific error, not only a running mean | Each exact program and temporal edge stores whole-body and lateral prediction-error energy; uncertainty of its mean falls with verified experience | Implemented |
| Preparatory cortical states can remain output-null before becoming output-potent ([Kaufman et al., 2014](https://doi.org/10.1038/nn.3643)); basal-ganglia circuits can adjust an action-release threshold ([Lo and Wang, 2006](https://doi.org/10.1038/nn1722)) | Selection and release should be separate causal events, with evidence for and against release | `HumanoidMotorPreparation` nodes carry direct task cost and indirect uncertainty cost; a later graph rule disinhibits the exact program or transition | Implemented |
| The largest motor-cortical population component reflects movement timing independently of movement type ([Kaufman et al., 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5069299/)); trajectory and traversal speed can be independently represented ([a 2023 motor-population study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10246015/)) | Program geometry must not be conflated with duration | Consequences are learned per physics frame and reconstructed at the selected horizon; timing contracts or relaxes from prediction receipts | Implemented |
| The nervous system combines efference-copy predictions with delayed sensory feedback to estimate current body state ([Miall et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6010151/)) | Delayed sensing requires a predictive belief state rather than raw-observation control | A shared `EmbodiedBodyBelief` advances a kinematic prior and precision-weights delayed proprioceptive, vestibular, and tactile receipts with explicit variance | Implemented |

## Implemented mechanisms

### Cerebellar-style conditional uncertainty

For each exact motor memory and temporal transition, the graph maintains:

- a mean consequence rate for body-axis orientation, angular velocity, and
  horizontal velocity;
- mean dimensionless sensory-prediction-error energy;
- separate lateral-channel prediction-error energy;
- exact experience count; and
- uncertainty of the learned mean, computed as error energy divided by
  experience count.

Only the exact causal model receives its receipt. Wider-program residuals are
not assigned to arbitrary members.

### Output-null preparation and release

An eligible candidate no longer jumps directly from selection to a trial. The
graph first creates an output-null preparation containing:

- direct predicted task cost;
- indirect uncertainty cost;
- uncertainty-adjusted cost;
- competing primitive cost;
- lateral capture cost; and
- lateral uncertainty and competing lateral cost.

A separate release rule makes the preparation output-potent. Release requires
the candidate's uncertainty-adjusted interval to beat the primitive both
globally and in the lateral control channel. The subsequent trial links back
to the preparation, preserving the entire causal path.

The mechanism resembles direct/indirect action gating and thalamic
disinhibition. It does not encode dopamine, nuclei, or anatomical connectivity.

### Independent timing coordinate

The first attempt adapted `response_frames` while retaining a fixed-horizon
consequence. That was invalid: a six-frame observation was being treated as
the prediction for seven or eight frames.

The corrected model learns consequence per physics frame. Candidate evaluation
and efference copy multiply that rate by the candidate's current timing
coordinate. Prediction surprise contracts the horizon by one physical frame;
a stable receipt relaxes it by one frame toward the graph's existing body
horizon. No command rate is declared.

## Falsification and correction record

The development sequence was deliberately not hidden:

1. Uncertainty plus unconstrained adaptive timing travelled `0.863 m` but
   drifted `0.247 m`, failing the unchanged `0.2 m` limit.
2. Requiring raw predicted lateral improvement travelled `1.008 m` but still
   drifted `0.244 m`. A point estimate was not a sufficient safety argument.
3. Normalizing consequences by time reproduced the same failure. This fixed a
   real representation error but showed that it was not the drift's cause.
4. Requiring channel-specific uncertainty to fit inside the predicted lateral
   advantage passed: `0.683 m` travel, `0.167 m` drift, 197 support
   alternations, zero aerial samples, and no fall.

No evaluation threshold, body configuration, cadence constant, or actuator
semantics changed during these corrections.

## Final simulator results

The PyBullet controller creates two output-null preparations and releases both.
The matched tonic controller creates none. One exact two-motor memory is
recalled twice and reaches three experiences. Six safe temporal transitions
are learned, but all remain at one experience and none is released as a
sequence. This is the intended effect of uncertainty: graph structure may be
retained without automatically receiving actuator authority.

Official HumanoidBench H1 remains unchanged. It falls at decision 65 versus
64 for tonic control, grounds no safe compound memory, creates no preparation
or transition, and performs no recall. The new gate does not manufacture
competence from an inadequate local forward model.

## Sensor-delay follow-on

The shared implementation is described in
[Embodied sensorimotor architecture](embodied_sensorimotor_architecture.md).
All three PyBullet boundaries now expose configurable sensor noise and
sample-delay queues. The graph creates an uncertain body belief, associates
each receipt with its exact causal trial, and reuses the existing efference,
eligibility, adaptive-credit, allostatic, generative-world-model, dual-process,
and default-mode cores.

The previous warning still applies: having an estimator is not evidence that it
improves control. That requires a matched delayed/noisy protocol against a
privileged-state arm.

## Next experiments

The next biology-derived steps should be separately preregistered:

1. Run measured latency, jitter, and dropped-receipt arms. Compare raw-state
   control against the implemented graph belief state under identical physics.
2. Give transition uncertainty repeated evidence through multiple seeds and
   perturbation schedules; test whether safe sequence recall emerges rather
   than weakening the gate.
3. Represent longer context only if first-order transitions are empirically
   aliased. A second-order context should be justified by different outcomes
   for the same transition under different predecessors.
4. Split reward/vigor from kinematic safety only when the graph receives a
   genuine effort or energy receipt. A named dopamine scalar without such a
   signal would add metaphor, not capability.
