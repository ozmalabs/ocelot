# Positive join multiplicity × clause attribution v1.1 results (2026-09-26)

## Result

The source/native-locked evaluation covered 60 fresh-process cells: `R={1,8}` writer/target pairs, `M={1,4,16,32,64}` two-edge join multiplicities, two authored match orders, and three replications. The independent analyzer passed **545/545 checks**, including readback of the installed match order via `export_rules()`. Audit-on/off final graphs and reports match; queue conservation and per-writer attribution hold; clause candidate counts sum to the per-writer candidate total.

For each writer, queue items in both measured families equal `M` under either authored order. Candidate tests also depend strongly on authoring order, but the engine reorders match edges during installation. The runner now reads back `export_rules()` so the positions are labeled by the actual installed edge type. It installs trigger then game first; the remaining equal-cardinality path edges are ordered by the reorderer's deterministic tie behavior:

| `M` | Authored order → installed order | Writer tests by installed edge | Paired-workload total per writer/target |
|---:|---|---|---:|
| 1 | trigger,left,right,game → trigger,game,right,left | trigger 1, game 1, right 1, left 1 | 6 |
| 1 | trigger,right,left,game → trigger,game,left,right | trigger 1, game 1, left 1, right 1 | 6 |
| 4 | trigger,left,right,game → trigger,game,right,left | trigger 1, game 1, right 4, left 16 | 24 |
| 4 | trigger,right,left,game → trigger,game,left,right | trigger 1, game 1, left 4, right 4 | 12 |
| 16 | trigger,left,right,game → trigger,game,right,left | trigger 1, game 1, right 16, left 256 | 276 |
| 16 | trigger,right,left,game → trigger,game,left,right | trigger 1, game 1, left 16, right 16 | 36 |
| 32 | trigger,left,right,game → trigger,game,right,left | trigger 1, game 1, right 32, left 1,024 | 1,060 |
| 32 | trigger,right,left,game → trigger,game,left,right | trigger 1, game 1, left 32, right 32 | 68 |
| 64 | trigger,left,right,game → trigger,game,right,left | trigger 1, game 1, right 64, left 4,096 | 4,164 |
| 64 | trigger,right,left,game → trigger,game,left,right | trigger 1, game 1, left 64, right 64 | 132 |

The paired-workload total includes two fixed target-rule candidate tests per writer/target; the writer-edge counts omit those. At `M=64`, the engine's tie-resolved installed order determines whether the final path edge incurs 4,096 or 64 tests. This is authoring-order sensitivity **through the existing install-time cost-based reorderer**, not a raw matcher comparison with reordering disabled. The counter localizes the work to the final path edge; it does not establish every internal cause or total runtime.

## Interpretation and limits

This is direct evidence that the current install-time reorderer's tie resolution can make matcher work depend materially on authored order for this regular two-edge schema, without changing its result. The current cardinality heuristic puts singleton edges first but cannot distinguish equal-cardinality path relations; the tie-break then decides which edge is last. This is a target for a richer selectivity estimate, not an evaluation of such an optimizer. It is not a general complexity exponent or evidence about natural-task frequency. Scheduler planning nanoseconds remain distinct from matching and end-to-end closure time; total CPU/wall time and memory were not measured here.

Next evaluate controlled degree skew and data distributions at fixed output cardinality under the existing install-time reorderer; then compare it with a semantics-preserving selectivity-aware ordering policy. Record installed order, candidate tests by installed edge, end-to-end CPU/wall time, peak memory, exact graph parity, and instrumentation overhead separately.

## Artifacts

- [Preregistration](SUBSTRATE_JOIN_MULTIPLICITY_CLAUSE_ATTRIBUTION_V1_1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_join_multiplicity_clause_attribution_v1_1.py)
- [Analyzer](../../../scripts/analyze_substrate_join_multiplicity_clause_attribution_v1_1.py)
- [Raw workers](../../../evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/join_multiplicity_clause_attribution_v1_1_lock_20260926.json)
