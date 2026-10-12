# Thoughtexperiment residual adoption v1 preregistration

## Question

Can the native substrate atomically adopt an isolated branch's graph-diff receipt when the primary still has the exact branch-base revision, preserve exact graph identity and attributes, and reject stale or conflicting receipts without a partial write?

## Contract under evaluation

`Substrate.apply_experiment_graph_delta(expected_revision, delta)` accepts the `graph_diff` wire format returned by the experiment journal. It checks the `(graph mutation version, Γ epoch, rule-slot count)` token before applying. It checks removed identities, edge presence, added identity availability, and changed-node attribute/type before-images. It applies against a staged CoW graph/interner and publishes only after validation. Edge additions in the current wire format carry no edge attributes. Revisions are strict: any primary semantic mutation since branch creation rejects adoption.

The `conclusions` receipt includes injected hypothesis structure and all branch effects. `derived_only` intentionally omits the injected structure; it is not necessarily a closed graph delta because derived edges can refer to hypothesis nodes. The probe records that dependency explicitly and does not treat `derived_only` as independently adoptable.

## Fixture and arms

Use the productive rule fixture from `thoughtexperiment_productive_residual_snapshot_v1.py`, with unrelated path sizes 0, 10,000, and 50,000. Five fresh worker processes per size; each worker runs:

1. **Adopt:** capture a reusable snapshot and its source revision; run one productive imagination with trace recording disabled; apply `conclusions`; compare the complete primary graph with the detached branch graph.
2. **Stale reject:** from an equivalent fresh base, produce a receipt, mutate primary once, then apply against the old revision. Require a stale-revision error and exact primary graph equality before/after the rejected call.
3. **Conflict reject:** from an equivalent fresh base, corrupt one changed-node before-image and apply against the still-current revision. Require a before-image error and exact graph equality before/after.

Randomize arm order by worker parity. Record fork/collapse/readout/adoption timings separately, graph sizes, revisions, rejection strings, graph SHA-256 values, source fingerprint, binary hash, and worker PID.

## Gates

- All 15 workers complete and source/build identity is recorded.
- Every successful arm has a nonempty `conclusions` receipt and exact full-graph equality after adoption, including preserved NodeIDs and graph structure.
- Every stale arm rejects specifically for revision mismatch and leaves the pre-call graph digest unchanged.
- Every conflict arm rejects before publication and leaves the pre-call graph digest unchanged.
- Primary graph remains unchanged during branch execution before adoption.
- Report timings descriptively by size; do not infer asymptotic behavior or general throughput from this single authored family.

## Evidence and limits

The raw capture and analyzer are stored under `evaluation/reports/`; the source-locked runner is under `evaluation/substrate_capability/`. This evaluates API atomicity and adoption cost on one residual family. It does not establish conflict-free concurrent adoption, arbitrary graph-diff validity, merge semantics, or general Thoughtexperiment utility.
