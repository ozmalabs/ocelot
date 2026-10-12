# Finite-key recursive closure scale-cost results (2026-09-26)

## Design and admission

The registered v1 sweep holds the one-edge recursive `add_node_if_absent` plus
`add_edge` rule family fixed while varying initial directed-cycle size
`N=16…1024` and mint-signature count `M=1/2/4`. Each of 21 cells has seven
fresh-substrate timed replicates and a separate warm-up. Engine construction,
graph/rule setup, and closure are timed separately. A preregistered v1.1 run
repeats the complete matrix in a fresh process using the same native artifact
and runtime source. The independent comparison finds exact semantic replication
for all 147 case IDs: fixed-point status, progress/pass counters, node/edge
counts, conservative bound, and a normalized terminal-graph digest matching an
independently reconstructed oracle. All per-run checks pass in both processes.

## Timing results

Median closure milliseconds, by process:

| M | N=16 | N=32 | N=64 | N=128 | N=256 | N=512 | N=1024 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1, v1 | 0.049 | 0.079 | 0.113 | 0.202 | 0.385 | 0.781 | 1.404 |
| 1, v1.1 | 0.047 | 0.071 | 0.108 | 0.192 | 0.367 | 0.681 | 1.419 |
| 2, v1 | 0.103 | 0.161 | 0.288 | 0.560 | 1.071 | 2.076 | 4.234 |
| 2, v1.1 | 0.106 | 0.155 | 0.282 | 0.528 | 0.996 | 1.971 | 3.975 |
| 4, v1 | 0.281 | 0.517 | 0.976 | 1.778 | 3.631 | 6.920 | 13.777 |
| 4, v1.1 | 0.271 | 0.482 | 0.907 | 1.733 | 3.313 | 6.675 | 17.031 |

At `N=1024`, median setup is 1.30–1.34 ms for M=1, 1.34–1.41 ms for M=2,
and 1.59–1.60 ms for M=4. Closure grows from N=16 to N=1024 by 28.8–30.2×
(M=1), 37.4–41.2× (M=2), and 49.0–62.8× (M=4). Terminal edges grow from
`N + M(N+M)`, near 64× for each fixed M. The M=4, N=1024 closure maximum
across both processes is 25.53 ms, against process medians of 13.78 and
17.03 ms; retain this timing spread as tail evidence.

All cells reach fixed point in three passes. Progress steps are 2/4/8 for
M=1/2/4 and remain constant across N in this fixture. The result therefore
isolates increasing match/effect work inside a fixed pass count. It does not
measure native allocation or detailed candidate/Term counts.

## Interpretation and limits

The captured closure medians scale roughly with the linearly growing final edge
population for each fixed M over these sizes. This is consistent with the
single-edge positive matcher on a cycle plus witness closure; it is not a fitted
complexity theorem or an estimate for arbitrary rule bodies, topology, dynamic
boundaries, or production seed closures. The finite-key proof bounds possible
progressing facts and rounds; this timing sweep measures one engine execution
path and does not turn that fact bound into a general CPU-time bound.

## Reproduction

Run both commands in separate processes from the repository root:

```sh
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_closure_scale_cost_v1.py
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_closure_scale_cost_v1_1.py
.venv/bin/python scripts/analyze_substrate_finite_key_closure_scale_cost_v1.py evaluation/reports/mint_termination_scale_cost_v1_20260926.json
.venv/bin/python scripts/analyze_substrate_finite_key_closure_scale_cost_v1_1.py evaluation/reports/mint_termination_scale_cost_v1_20260926.json evaluation/reports/mint_termination_scale_cost_v1_1_20260926.json
```

Protocol: [v1 preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_COST_PREREG_20260926.md); [v1.1 confirmation amendment](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_COST_V1_1_AMENDMENT_20260926.md). Runners: [v1](../../../scripts/substrate_finite_key_closure_scale_cost_v1.py), [v1.1](../../../scripts/substrate_finite_key_closure_scale_cost_v1_1.py). Independent analyzers: [per-capture oracle](../../../scripts/analyze_substrate_finite_key_closure_scale_cost_v1.py), [cross-process comparison](../../../scripts/analyze_substrate_finite_key_closure_scale_cost_v1_1.py). Raw captures: [v1](../../../evaluation/reports/mint_termination_scale_cost_v1_20260926.json), [v1.1](../../../evaluation/reports/mint_termination_scale_cost_v1_1_20260926.json); [independent analysis](../../../evaluation/reports/mint_termination_scale_cost_v1_1_analysis_20260926.json).

## Next gate

Vary topology and positive-match arity while retaining exact terminal-state
oracles; collect native candidate and Term-work counts if available, and profile
allocation separately. Keep the current finite-key fragment and its exclusions
explicit when comparing with broader seed closure.
