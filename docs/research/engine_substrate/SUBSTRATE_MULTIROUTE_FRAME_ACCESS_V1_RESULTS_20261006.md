# Multi-route frame and native access capture v1 results

Date: 2026-10-06  
Status: integrity gates passed; cheap-cut evidence remains open and currently unsupported by this operational frame.

## Result

Ten source-locked fresh workers replayed the five live-conversation routes twice. Each worker produced exactly one outcome-blind checkpoint and one post-checkpoint native trace; sources remained stable, with zero dropped trace rows and zero unmapped RuleUIDs. Corresponding replicates were identical on the reported counts.

| Route | Ingress frame | Direct boundary | State-graph width upper bound | Native trace events | Distinct outside-cut nodes | Task utility |
|---|---:|---:|---:|---:|---:|---:|
| Scene description | 7 | 5 nodes / 8 incidences | 2 | 1,771,713 | 7,311 | 0/2 |
| Held self-knowledge answer | 7 | 6 / 9 | 2 | 418,244 | 11,787 | 2/2 |
| Self-report action | 6 | 5 / 8 | 2 | 481,197 | 11,796 | 2/2 |
| Unknown-word clarification | 6 | 5 / 8 | 2 | 425,170 | 11,783 | 2/2 |
| Concern authoring | 16 | 5 / 8 | 2 | 444,651 | 11,782 | 0/2 |

The same selected-authored panel therefore reproduces the earlier shape: the fixed ingress projection is small and has a low induced state-graph width, while each native trace touches 7,311–11,796 distinct nodes outside the frame and its direct boundary. Read and write instrumentation shows this is not just a frame-count artifact: recurring term attribute/edge reads, type-population candidate reads, and effect comparisons/writes reference nodes well beyond the ingress cut. Scene description has a distinct high-volume out-of-frame `term_attr_read` population. A separately locked static metadata supplement then resolved all observed RuleUIDs/names and found zero resource-key mismatches or concrete dependency pairs outside the conservative static projection. The projection nevertheless contains 59,227–77,001 possible rule pairs versus 195–237 dynamically witnessed pairs, and 9,000–42,000 weighted events per route are not statically checkable because their trace kind has no key. This is a measured execution footprint, not proof that those accesses are semantically required or avoidable; see the [static reconciliation results](SUBSTRATE_MULTIROUTE_STATIC_DEPENDENCY_RECONCILIATION_V1_RESULTS_20261006.md).

The existing task utility profile remains 6/10: self-report, held-answer, and clarification pass both replicates; scene description and concern authoring fail both. Scene description retains the known faculty/receipt discrepancy discussed in the cross-family comparison, so its utility failure is reported against the existing baseline oracle and does not explain the locality trace. During analysis, the harvest runner's `task_ok` helper exposed its known self-report bug (calling `.get()` on route-name strings); analysis uses the corrected independent `task_oracle` plus the existing scene-faculty-build contract. No worker was rerun or excluded.

## Interpretation and limits

This is negative evidence for the claim that the currently declared ingress frame predicts the native operating footprint across these routes. It is not a falsification of all task locality: Concepts, lexicon populations, ShapeDecode work, prior context, and other resident state may form a compact but currently unmeasured interface. The trace omits host-side reads and cannot separate necessary semantic dependency from avoidable global scans. Width is measured on the projected state graph, not the inference primal graph. The panel is five selected authored routes with repeated workers, on one engine/build and host; it estimates neither natural-task prevalence nor general asymptotic scaling. Instrumentation is enabled, so these counts are not timing estimates.

## Next gate

Observed resource keys now reconcile with static declarations, but the conservative static graph is too broad to serve as a useful interface. The next gate is exact-parity candidate-generation and cache/index invalidation experiments on the lexicon Concept scan, curiosity's resident Concept reads, and ShapeDecode/recognition populations; include population growth and mutation controls. Account for these shared populations as explicit interfaces. Then define a dependency-backed frame blind to task outcomes and run monolithic-versus-partitioned closure with exact task-state parity and negative locality controls. Do not advance the cheap-cut tractability claim until shared-interface and discovery costs are measured on independently authored task families.

## Artifacts

- [Prospective protocol](SUBSTRATE_MULTIROUTE_FRAME_ACCESS_V1_PREREG_20261006.md)
- [Capture runner](../../../scripts/substrate_multiroute_frame_access_v1_20261006.py)
- [Analyzer](../../../scripts/analyze_substrate_multiroute_frame_access_v1_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/multiroute_frame_access_v1_20261006_lock.json)
- [Compressed capture](../../../evaluation/reports/multiroute_frame_access_v1_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/multiroute_frame_access_v1_20261006/analysis.json)
- [Static dependency reconciliation](SUBSTRATE_MULTIROUTE_STATIC_DEPENDENCY_RECONCILIATION_V1_RESULTS_20261006.md)
