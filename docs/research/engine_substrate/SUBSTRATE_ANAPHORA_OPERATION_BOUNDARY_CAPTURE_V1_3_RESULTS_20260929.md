# Anaphora operation boundary capture v1.3 results

**Status:** source-audited retrospective reanalysis of the immutable v1.2 capture; not a new capture or a confirmatory task-distribution sample.

## Result

The v1.2 run captured 11 independently authored anaphora tasks in 10 fresh worker processes. The v1.3 analyzer passes all 12 integrity checks: worker/process count, input/source locks, full case order, graph digest, plain-versus-traced graph and checkpoint parity, task oracles, zero dropped trace events, complete/disjoint message-turn ownership, and parity with the historical v1.1 task graphs after seed warmup. The analyzer reclassifies native access events using the event-kind definitions in `runners/dsl/src/access_trace.rs`.

After warming the idempotent intent seeds before ownership attribution, message-turn ownership is 6–8 nodes on the first turn, 12–15 on the second, and 20 on the three-turn examples. The combined owned-node graph (state edges plus concrete pairwise trace dependencies) has min-fill induced width 2 in these examples. These are small, deliberately constructed tasks on one assistant-authored anaphora family.

For authored turn boundaries, the first turn has no cross-frame state or pairwise trace edges. The second turn has 2 cross-frame state edges and 1–2 pairwise trace accesses; the third turn has 4 state edges and 2 pairwise trace accesses. Separately, each turn's graph is incident on five global nodes in this fixture (one Agent, three Concepts, one Interlocutor). Trace analysis finds 17–31 pairwise accesses to external/global nodes and 23–42 unary reads of global nodes across the measured checkpoints. Static access summaries expose 6 wildcard readers and 22 wildcard writers. These accesses show why the small induced width alone does not prove a closed, safely executable frame.

## Partition comparison

Balanced contiguous stable-ID partitions reproduce the authored-turn metrics in this capture because node IDs are allocated in turn order. This baseline is therefore confounded and supplies no independent evidence that the authored cut is uniquely cheap. Dependency-minfill partitions of the same owned nodes split authored turns: median same-frame recall is 0.526 for two-turn tasks and 0.356 for the three-turn tasks. In turn 1, they induce 10–11 cross-frame state edges and 8–12 pairwise trace crossings; in turn 2 of the three-turn cases, they induce 18 state crossings and 13 pairwise trace crossings. The fixture's authored ownership is visibly better than this particular blind partition, but it is supplied by the protocol rather than learned by the substrate.

## Claim boundary and corrections

This result measures protocol-owned turn nodes and a partial operation-boundary graph for a small, deliberately authored family. It does not establish that natural tasks have cheap cuts, that the engine discovers the cuts, that exact inference factors over them, or that partitioned execution preserves behavior. Generic message-scoped execution remains unsupported. The trace covers comprehension only; receive-time effects, Python parsing and host callbacks, scheduler work outside the trace, omitted native accesses, and factor scopes/inference domains remain unmeasured.

Earlier iterations remain preserved with their limitations: v1 failed its native NodeID harness; v1.1 attributed lazy-loaded seed nodes to the first turn; v1.2 fixed ownership by warming seeds but its analyzer misclassified unary events without peers as unresolved pair boundaries. V1.3 corrects only the analysis of the immutable v1.2 raw capture, audited against native trace source. Do not cite v1.2 boundary counts as valid pair-boundary metrics.

## Next gate

Capture operation boundaries on a held-out task family with ownership labels independent of node allocation order. Instrument ingress, host callbacks, scheduler/rule work, and native accesses; add a typed dynamic dependency graph plus static rule read/write domains. Compare authored/annotated ownership with blind partitions using exact graph parity, held-out cut cost, separator cardinality, induced width, and discovery/maintenance cost. Then add a scoped-execution intervention with omission and contamination controls. A natural-task sample is still required before estimating cheap-cut prevalence.

## Artifacts

- Protocol: [v1 preregistration](SUBSTRATE_ANAPHORA_OPERATION_BOUNDARY_CAPTURE_V1_PREREG_20260929.md), [v1.1 ownership correction](SUBSTRATE_ANAPHORA_OPERATION_BOUNDARY_CAPTURE_V1_1_AMENDMENT_20260929.md), [v1.2 seed-warmup correction](SUBSTRATE_ANAPHORA_OPERATION_BOUNDARY_CAPTURE_V1_2_AMENDMENT_20260929.md), [v1.3 trace analysis correction](SUBSTRATE_ANAPHORA_OPERATION_BOUNDARY_CAPTURE_V1_3_ANALYSIS_AMENDMENT_20260929.md).
- Runner: [v1.2 capture runner](../../../scripts/substrate_anaphora_operation_boundary_capture_v1_2.py); analyzer: [v1.3 source-audited analysis](../../../scripts/analyze_substrate_anaphora_operation_boundary_capture_v1_3.py).
- Frozen task suite: [JSON](../../../evaluation/substrate_capability/anaphora_independent_task_suite_v1.json); capture lock: [v1.2 lock](../../../evaluation/substrate_capability/anaphora_operation_boundary_capture_v1_2_lock_20260929.json).
- Raw capture: [v1.2 workers](../../../evaluation/reports/anaphora_operation_boundary_capture_v1_2_raw_20260929.json); analysis: [v1.3 analysis JSON](../../../evaluation/reports/anaphora_operation_boundary_capture_v1_3_analysis_20260929.json).
