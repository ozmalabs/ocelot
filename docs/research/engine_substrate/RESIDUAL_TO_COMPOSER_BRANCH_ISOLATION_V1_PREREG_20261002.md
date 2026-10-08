# Residual-to-composer branch isolation v1 preregistration

## Question

Can the measured cue-derivation path run inside an isolated snapshot branch, produce the same bounded held-operator proposal, and return only a useful residual artifact to the primary graph?

## Candidate mechanism

This follows cue-derivation v1 without changing its action-vector decoder or task/control panel. The task fault and observed actual/expected outcome are established in the primary fixture. A public immutable snapshot is forked; `induce_concern` and `ground_concern` run against a branch-bound Agent. The extracted candidate is scored on held-out navigation in an independent context. The primary receives one `ExperimentResidual` node containing the observation, derived cue, selected target/operator/site, serialized candidate rule when present, and held-out pass flag.

## Gated panel

Reuse the 13 locked cases: four cardinal inversions, four valid non-inversions, four malformed/underdetermined observations, and one absent-target control. Require source stability; branch state changes on every induction path; no primary graph/rule/revision changes during branch work; exactly one new primary node on return, with every prior primary node and edge unchanged; no primary rule-store changes; positive proposals select `flip_comparison` for `hop_descend_gradient`, are present in the returned residual, and pass held-outs; all non-inversion and malformed cases abstain; and the absent-target case does not propose. Preserve zero-proposal controls.

The harness must report full primary node/edge/rule snapshots and branch node/edge/rule deltas, not only target-rule equality or object counts. The successful isolated branch proves mutation containment and return-path utility for this authored mechanism. It does not prove that the substrate learned the cue decoder: action geometry and cue mapping remain host-authored. No speed claim is gated; snapshot fork time is reported descriptively.

## Reproduction

Build and provenance-check the current release engine, run `measure_residual_to_composer_branch_isolation_v1.py --lock`, run the locked worker panel with `--run`, then execute the independent analyzer. The lock binds the task adapters, navigation fault, composer bridge, reflective faculty, seed closure, native sources, protocol, runner, analyzer, and loaded extension.
