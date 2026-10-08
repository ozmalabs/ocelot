# Term external-dependency probe v1.1 results

Date: 2026-09-28

## Results

Three fresh workers completed all six cells. The independent analyzer passes 14 gates for source/native lock equality, child command/stream hashes, unique PIDs, exact graph replication, read-set scope, callback/fire/trace conservation, and zero trace drops.

| Matches (M) | Tool effect position | Callback calls per settle | Progress reported | Median elapsed time |
|---:|---|---:|---:|---:|
| 1 | first | 2 | 1 | 63,990 ns |
| 1 | last | 2 | 1 | 13,540 ns |
| 2 | first | 4 | 1 | 21,290 ns |
| 2 | last | 4 | 1 | 16,130 ns |
| 4 | first | 8 | 1 | 22,500 ns |
| 4 | last | 8 | 1 | 22,450 ns |

For each M and effect position, all three workers agree exactly. Callback calls, native fire-counter deltas, and `term_tool_dispatch` events conserve exactly; every target receives the fixed result and marker. `reads_any=true` and `edge:trigger` are stable across all cells. Effect order does not change the final graph or callback count in this fixture.

Callback work is exactly `2M` for this family while the reported progress remains one at M=1/2/4. This is consistent with each binding being evaluated in the progress-producing settle pass and again during the final no-progress pass. It shows why a settle/progress count is insufficient as a general cost proxy when Terms can call external handlers. The first-position M=1 timing has a large cold-start difference; all timings are descriptive and this panel makes no latency claim.

## Scope and limits

This establishes a cardinality slope only for one authored edge rule, a fixed idempotent result, and a local callback counter. It does not establish a bound for other schedulers, nested expressions, matching predicates, multiple rules, callbacks that mutate external state, or natural workloads. The callback's observable side effect in this panel is its invocation count; repeated effectful callbacks could duplicate host actions.

## Reproduction

See [preregistration](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_1_PREREG_20260928.md), [source/native lock](../../../evaluation/substrate_capability/term_external_dependency_probe_v1_1_lock_20260928.json), [runner](../../../scripts/substrate_term_external_dependency_probe_v1_1.py), [raw capture](../../../evaluation/reports/term_external_dependency_probe_v1_1_20260928.json), [independent analyzer](../../../scripts/analyze_term_external_dependency_probe_v1_1.py), and [analysis](../../../evaluation/reports/term_external_dependency_probe_v1_1_analysis_20260928.json).
