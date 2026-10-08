# Productive Thoughtexperiment residual over reusable snapshots v1 results

## Gates

The corrected confirmatory capture has **15 fresh workers**, five per size, and **225 branch executions** across eager full-copy, direct shared-graph-page, and reusable-snapshot backends. All branches execute one productive graph-rule step within a two-step budget, report convergence, and pass a separate zero-progress terminal probe. Each derived residual is nonempty and includes one added node, one changed node, one deleted node, one added edge, and one deleted edge. Full conclusions and derived-only residuals match exactly across all backends for each branch ordinal. The primary graph and rule store remain unchanged, and a later snapshot fork reproduces the base graph.

The v1 one-step and first orchestration captures are retained only as pilots. The final data uses the amendments that fix analyzer import resolution and add the terminal convergence gate.

## Cost

Five branch alternatives are evaluated per backend per worker. Batch wall medians and reusable snapshot capture costs (milliseconds) are:

| Unrelated nodes | Eager full copy batch | Direct shared pages batch | Reusable batch | Snapshot capture | Reusable batch + capture |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.611 | 0.509 | 0.541 | 0.017 | 0.557 |
| 10,000 | 13.000 | 0.892 | 0.675 | 0.037 | 0.714 |
| 50,000 | 60.072 | 2.445 | 0.987 | 0.074 | 1.061 |

At 50,000 unrelated nodes, reusable snapshots reduce measured five-branch batch time by about 57× versus eager full copies when capture is included. Shared-page branch setup medians are about 0.034 ms direct and 0.033 ms reusable, compared with 10.67 ms eager. The reusable route wins 3/5 paired blocks against direct shared pages at both 10k and 50k; the 50k paired median direct/reusable wall-time ratio is 2.64. The small sample and one-host synthetic fixture make this directional evidence. At baseline size, direct pages are slightly faster and the branches are sub-millisecond.

Collapse and sparse residual-readout phase medians remain small across scales: at 50k, collapse is 0.020/0.047/0.047 ms and journal readout is 0.067/0.050/0.047 ms for eager/direct/reusable. This workload's cost is branch preparation over the large base, not the one-rule inference or the returned residual serialization.

## Residual shape and adoption boundary

Each complete `conclusions` result contains 2 added nodes, 1 changed node, 1 removed node, 2 added edges, and 1 removed edge. The `derived_only` result excludes the injected hypothesis and contains exactly 1 added, 1 changed, and 1 removed node plus 1 added and 1 removed edge. The caller receives the branch residual and the primary remains unchanged. This confirms residual return from a productive isolated branch.

The experiment does **not** merge the residual into the primary. Source review found no guarded graph-delta adoption API; applying node IDs and deletes requires a revision check and conflict policy. Snapshot isolation and residual production are now demonstrated together, while acceptance/adoption remains a distinct unimplemented capability. The next gate is a revision-checked explicit adoption operation with exact expected graph state, stale-revision rejection, and no implicit merge on branch completion.

## Scope and artifacts

One authored hypothesis rule, one focus pattern, one host, and five sequential branches per backend are measured. The experiment does not establish natural-task performance, concurrent write safety, cancellation/reclamation bounds, or vLLM integration. Changed-object counts are the returned semantic delta, not all attempted mutations or touched memory pages.

- [Base preregistration](THOUGHTEXPERIMENT_PRODUCTIVE_RESIDUAL_SNAPSHOT_V1_PREREG_20261001.md)
- [Analyzer-import amendment](THOUGHTEXPERIMENT_PRODUCTIVE_RESIDUAL_SNAPSHOT_V1_1_AMENDMENT_20261001.md)
- [Closure amendment](THOUGHTEXPERIMENT_PRODUCTIVE_RESIDUAL_SNAPSHOT_V1_2_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_productive_residual_snapshot_v1.py)
- [Analyzer](../../../scripts/analyze_thoughtexperiment_productive_residual_snapshot_v1.py)
- [Source-captured workers](../../../evaluation/reports/thoughtexperiment_productive_residual_snapshot_v1.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_productive_residual_snapshot_v1_analysis.json)
