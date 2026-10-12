# Runtime counter semantics audit v1

Date: 2026-09-28  
Status: source-linked semantics inventory; dynamic calibration remains open.

## Finding

The substrate has separate counters for matcher candidate enumeration, candidate-loop iterations, bound-endpoint rejects, where evaluation, successful match leaves, scheduler slot work, and deferred queue work. These counters describe distinct stages and should not be collapsed into one “operation count.” In particular, candidate enumeration includes pairs that are later rejected by bound checks; candidate tests increment before those checks; successful `pattern_edge` trace rows are emitted only after a complete successful match leaf. There is no exact equality between those quantities.

Scheduler work has an independent path: `scheduler_plan_completed` records external-poll slots, fixed-point probe slots, dirty-vector slots, and selected rules as work events outside the active rule identity. Queue enqueue and drain records also have separate meanings; drained counts include stale or rejected items. This makes the existing instrumentation capable of representing some costs beyond active-rule traces, but it does not establish that every scheduler or post-rule operation is covered.

## Counter distinctions

| Counter class | Source-defined meaning | Do not treat it as |
|---|---|---|
| Candidate pairs enumerated | Pairs materialized by a match-edge expansion, classified as local, hinted, or full scan | Candidate tests, successful bindings, or unique graph edges |
| Candidate tests | Iterations of the candidate loop, before bound endpoint rejection | Successful `pattern_edge` rows or all graph reads |
| Bound rejects | Candidate-loop pairs rejected by bound source/target equality | All failed matches or where-clause rejects |
| Where evaluations | Whole where/JIT calls or remaining unpruned conjunct evaluations | Candidate tests or pushdown evaluations |
| Successful match leaves | Bindings passing distinct-variable and where checks and reaching the visitor | Candidate tests, rule firings, or committed effects |
| Scheduler slots | External polling, fixed-point probe, dirty-vector scan, and selected-rule counts | Matcher work or all process/adapter scheduling |
| Deferred queue work | Recognized enqueues, drain batches, and dequeued records | Successful mutations or host callbacks |
| Concrete access trace | Selected concrete graph reads, successful match footprints, and effects | A complete dynamic dependency set or matcher count |
| Host callback work | `UseTool` callback dispatch and behavior | Native graph trace rows or graph progress |

The machine-readable crosswalk records source anchors and SHA-256 digests for five implementation files: [counter semantics JSON](../../../evaluation/reports/substrate_counter_semantics_v1_20260928.json). Reproduce it with `python3 scripts/audit_substrate_counter_semantics_v1.py`.

## Limits and next calibration gate

This is a source audit, not a dynamic calibration. It does not measure counter overhead, establish complete event coverage, or prove that the concrete access trace includes every dependency. Known omissions include callback-internal accesses, some specialized Term/helper reads, failed matcher identities, unchanged `SetAttrIfDifferent` reads, adapter/boot work, and post-rule work without a recognized queue hook.

The next dynamic gate should use controlled graphs with independently known counts for candidate enumeration, candidate-loop iterations, bound rejects, where calls, successful leaves, scheduler slot classes, queue enqueues/drains, and host callback invocations. Include no-op and negative controls, check semantic parity in uninstrumented arms, and report host/scheduler totals separately from RuleUID-attributed trace events. Only after these equations reconcile should trace projections be used to estimate frame interfaces or operation cost.

## Reproduction boundary

The generator fails if any declared source anchor disappears. Its source hashes and line references are recorded in the JSON output. The artifact does not execute the native engine and therefore makes no runtime calibration claim.
