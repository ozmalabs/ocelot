# Thoughtexperiment epistemic commit v1 results

**Status:** source-locked mechanism probe passes all 16 checks across five fresh workers.

## Contract exercised

The low-level `apply_experiment_graph_delta` primitive is a structural graph merge. It does not classify beliefs, reground conclusions, or invoke the commitment gate. The user-facing Thoughtexperiment route instead returns a detached branch plus a primary-graph audit trace. The trace now stores the full injected hypothesis specification. Injected assumption nodes/edges and derived edges that depend directly on assumption nodes are classified as noncommittable records; the detached `conclusions` receipt still preserves them for inspection and replay.

Ordinary changed-edge conclusions carry sparse before/after attributes. `reground` accepts them only when the live edge still matches the changed keys' before-image or already matches the proposed result. `commit_imagination` repeats the edge check immediately before the gate and refuses stale edge changes. An explicitly approved commit applies the sparse update while preserving unrelated live edge attributes. Added-edge records retain their attributes and are checked for collisions before commit.

## Measurement

Five independent workers run a graph rule that changes attributes on one existing edge only in the detached branch, under an explicit injected hypothesis. Each worker checks: exact hypothesis persistence; assumption-node/edge classification; pending changed-edge before/after record; no live edge mutation during imagination; successful regrounding; preservation of a concurrent edge update by stale-commit refusal; default gate refusal without edge write; and approved, exact edge-attribute writeback. All 16 checks pass.

This is a constructed mechanism fixture, not a natural-task measure, and it does not validate all writeback kinds or concurrent commits. Deletion receipts remain reportable branch residuals but do not become writeback proposals in this path. The structural graph-delta API remains available for controlled branch/state merges; callers must apply epistemic policy before using it against an authoritative live graph.

## Artifacts

- Runner: [thoughtexperiment_epistemic_commit_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_epistemic_commit_v1.py)
- Capture: [thoughtexperiment_epistemic_commit_v1.json](../../../evaluation/reports/thoughtexperiment_epistemic_commit_v1.json)
- Edge-delta mechanism result: [residual adoption results](THOUGHTEXPERIMENT_RESIDUAL_ADOPTION_V1_RESULTS_20261001.md)
