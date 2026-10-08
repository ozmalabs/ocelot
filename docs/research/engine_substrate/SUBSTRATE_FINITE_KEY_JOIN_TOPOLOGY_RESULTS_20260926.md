# Finite-key join-arity and topology closure envelope (2026-09-26)

## Design and replication

The locked matrix has 42 configurations across one-, two-, and three-edge
positive path joins; path and directed-cycle graphs at N=32/64/128/256/512; and
four-level complete-adjacent-layer graphs at N=16/32/64/128. Each configuration
has five fresh-substrate timed replicates, with setup and closure timed
separately. One rule mints one fixed witness and adds a result edge from the
terminal matched node; it matches only the original `link` type.

Both fresh processes complete 210 timed cases with all native and independent
checks passing. Per-capture analysis independently enumerates match bindings,
reconstructs terminal nodes and edges, and confirms exact normalized graph
digests, the finite-key progress bound, and fixed-point status (1,895 checks
per process). The cross-process comparison confirms exact semantic agreement
for all 210 case IDs, with the same native artifact and relevant engine source.

## Matched N=128 results

Closure medians in milliseconds are shown as `v1 / v1.1`:

| Topology | Input edges | Join arity q | Enumerated bindings | Distinct terminal nodes | Closure ms |
|---|---:|---:|---:|---:|---:|
| Path | 127 | 1 | 127 | 127 | 0.096 / 0.095 |
| Path | 127 | 2 | 126 | 126 | 0.121 / 0.119 |
| Path | 127 | 3 | 125 | 125 | 0.195 / 0.137 |
| Cycle | 128 | 1 | 128 | 128 | 0.099 / 0.097 |
| Cycle | 128 | 2 | 128 | 128 | 0.131 / 0.128 |
| Cycle | 128 | 3 | 128 | 128 | 0.137 / 0.139 |
| Layered | 4,095 | 1 | 4,095 | 127 | 2.076 / 2.091 |
| Layered | 4,095 | 2 | 7,938 | 64 | 6.140 / 6.075 |
| Layered | 4,095 | 3 | 3,969 | 1 | 3.704 / 3.548 |

All cases settle in two passes. On sparse path/cycle inputs, increasing arity
adds modest matching overhead for this shape. The layered family is much more
expensive, with the two-edge join producing the largest binding count and
closure time. The topology change also raises input edge count from about 128
to 4,095, so this is a combined branching/density stress, not a topology-only
causal comparison. At the same layered N, q=2 has twice q=3's bindings and
about 1.7× its median closure time across processes.

## Interpretation and limits

This supports a narrow claim: positive join closure cost depends materially on
the graph/match population even when the finite-key fragment remains bounded
and pass count is constant. The recorded path-binding count is an independent
workload descriptor, not a native candidate-counter measurement. A larger
closure time is not itself a complexity class, and the bounded fixtures do not
estimate natural graph frequency, arbitrary rule plans, typed selectivity,
negative conditions, attribute predicates, memory, or production seed closure.

## Reproduction

Run v1 and v1.1 in separate processes from the repository root, then run the
independent analyzer on each capture and the paired analyzer:

```sh
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_join_topology_v1.py
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_join_topology_v1_1.py
.venv/bin/python scripts/analyze_substrate_finite_key_join_topology_v1.py evaluation/reports/mint_termination_join_topology_v1_20260926.json
.venv/bin/python scripts/analyze_substrate_finite_key_join_topology_v1.py evaluation/reports/mint_termination_join_topology_v1_1_20260926.json
.venv/bin/python scripts/analyze_substrate_finite_key_join_topology_v1_1.py evaluation/reports/mint_termination_join_topology_v1_20260926.json evaluation/reports/mint_termination_join_topology_v1_1_20260926.json
```

Protocol: [v1 preregistration](SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_PREREG_20260926.md), [v1.1 amendment](SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_V1_1_AMENDMENT_20260926.md). Runners: [v1](../../../scripts/substrate_finite_key_join_topology_v1.py), [v1.1](../../../scripts/substrate_finite_key_join_topology_v1_1.py). Analyzers: [per-capture oracle](../../../scripts/analyze_substrate_finite_key_join_topology_v1.py), [cross-process comparison](../../../scripts/analyze_substrate_finite_key_join_topology_v1_1.py). Raw captures: [v1](../../../evaluation/reports/mint_termination_join_topology_v1_20260926.json), [v1.1](../../../evaluation/reports/mint_termination_join_topology_v1_1_20260926.json); [paired analysis](../../../evaluation/reports/mint_termination_join_topology_v1_1_pair_analysis_20260926.json).

## Next gate

Add candidate/Term-level instrumentation or native profiler attribution for the
same locked cells, then vary one factor at a time: hold input edge count fixed
while changing degree distribution, and hold degree distribution fixed while
changing join arity. Only after that should these results be connected to
representative frame or task graphs.
