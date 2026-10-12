# GenInfer scope index trace v2.1 results

Date: 2026-10-05  
Correction history: [v2.1 amendment](SUBSTRATE_GENINFER_SCOPE_INDEX_TRACE_V2_1_AMENDMENT_20261005.md)  
Runner: [`substrate_geninfer_scope_index_trace_v2_1.py`](../../../evaluation/substrate_capability/substrate_geninfer_scope_index_trace_v2_1.py)

## Outcome

The corrected v2.1 capture passes all gates across twelve fresh workers (four K=2 conditions × three replicates). Exact output oracles and scope membership pass; worker inputs remain source stable and work traces have no drops. The existing `(node type, attr key, value)` index can serve scoped GenInfer's codebook lookup when explicitly declared. In the indexed arm, the trace contains four scope-index queries and four returned members per worker, zero full typed-population node visits, and the same four parsed parts and 9,600 search candidates as scan-based per-frame scope. The index is declared before task codebook insertion, so its existing insertion-maintenance path supplies the two scoped parts.

| Work/cost (median per worker) | Unscoped global | Explicit global | Frame scope, scan | Frame scope, index |
|---|---:|---:|---:|---:|
| Typed population nodes visited | 76 | 76 | 76 | 0 |
| Scope-index queries / returned members | 0 / 0 | 0 / 0 | 0 / 0 | 4 / 4 |
| Selected attributes counted | 320 | 56 | 28 | 28 |
| Parts parsed | 76 | 8 | 4 | 4 |
| Search candidates | 19,200 | 19,200 | 9,600 | 9,600 |
| Index declaration/backfill | — | — | — | 6.36 µs |
| Production closure wall time | 42.94 ms | 39.35 ms | 28.49 ms | 38.03 ms |

The optional index removes the typed-population traversal while preserving the frame-scoped parse/search workload. It does not improve observed closure time in this small fixture: indexed median is 38.03 ms versus 28.49 ms for scan-based scope. This is one three-replicate micro-workload with substantial fixed closure work; it does not prove the index caused the difference or that index lookup pays off at larger populations. The result supports an operation-count change, not a speedup claim.

## Corrections retained

The first v2 protocol expected two index calls per worker; the captured production route performs four. That capture and failed analysis are retained in the v2 artifacts. V2.1 amends the expected count using that finding and reruns all arms in fresh processes. The original v2.1 analyzer then mishandled absent work-event kinds, treating an omitted zero count as `-1`; its failed output is retained. The separate corrected analyzer reads the same v2.1 lock/capture and treats an absent sparse counter as zero. All preregistered v2.1 checks then pass. These corrections are part of the evidence trail, not hidden retries.

## Limits and next gate

Scope IDs are harness-authored. Only the `(ShapeSignature, scope_id)` index was enabled; index lookup is optional and falls back to the scan unless a caller declares it. This panel does not measure index mutation under attribute reassignment/type changes, snapshot cloning, persistence/restore, admission policy, frame discovery, or natural-task prevalence. Next measure index construction/update/clone costs over population size and scope selectivity, then test a safe source-side admission/rebuild path and exact parity after mutations and restore. Keep the index disabled where no evidence shows that its ongoing maintenance pays for itself.

## Artifacts

- [Amendment](SUBSTRATE_GENINFER_SCOPE_INDEX_TRACE_V2_1_AMENDMENT_20261005.md)
- [Lock](../../../evaluation/substrate_capability/geninfer_scope_index_trace_v2_1_lock_20261005.json)
- [Capture](../../../evaluation/reports/geninfer_scope_index_trace_v2_1_20261005.json)
- [Original analysis with its checker defect](../../../evaluation/reports/geninfer_scope_index_trace_v2_1_analysis_20261005.json)
- [Corrected independent analysis](../../../evaluation/reports/geninfer_scope_index_trace_v2_1_corrected_analysis_20261005.json)
- [Original v2 capture with the wrong expected call count](../../../evaluation/reports/geninfer_scope_index_trace_v2_20261005.json)
