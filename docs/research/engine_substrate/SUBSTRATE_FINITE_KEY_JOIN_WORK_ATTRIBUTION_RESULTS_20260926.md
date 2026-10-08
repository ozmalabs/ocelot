# Finite-key join work attribution results (2026-09-26)

## Final source-complete evidence

The final v1.3 audit-on capture covers 42 `(topology,N,arity)` configurations,
three fresh substrates per cell, and two fresh processes: 252 native closures.
The independent analyzer passes 2,024 checks, including current source/native
hashes, exact per-case counters across processes, parity with the
uninstrumented terminal graph and independent binding oracle, fixed points,
finite-key bounds, counter identities, and global/per-rule conservation.
Audit-on wall times are intentionally excluded; use the separate
[uninstrumented cost results](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_COST_RESULTS_20260926.md)
for timing.

## N=128 native matcher work

Counts below are medians of three identical integer captures per process; both
processes have the same values.

| Topology | q | Input edges | Complete path bindings (oracle) | Native candidate pairs | Scan | Bound-node local | Binding leaves | Rule enumerations | Term evals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Path | 1 | 127 | 127 | 254 | 254 | 0 | 254 | 2 | 0 |
| Path | 2 | 127 | 126 | 506 | 254 | 252 | 252 | 2 | 0 |
| Path | 3 | 127 | 125 | 756 | 254 | 502 | 250 | 2 | 0 |
| Cycle | 1 | 128 | 128 | 256 | 256 | 0 | 256 | 2 | 0 |
| Cycle | 2 | 128 | 128 | 512 | 256 | 256 | 256 | 2 | 0 |
| Cycle | 3 | 128 | 128 | 768 | 256 | 512 | 256 | 2 | 0 |
| Layered | 1 | 4,095 | 4,095 | 8,190 | 8,190 | 0 | 8,190 | 2 | 0 |
| Layered | 2 | 4,095 | 7,938 | 24,066 | 8,190 | 15,876 | 15,876 | 2 | 0 |
| Layered | 3 | 4,095 | 3,969 | 32,004 | 8,190 | 23,814 | 7,938 | 2 | 0 |

The two- and three-edge joins share an 8,190-candidate full scan across the
first and repeated enumeration. Further expansion is local to already-bound
nodes. The q=3 layered rule produces fewer complete path bindings than q=2, but
more candidate pairs, because the matcher evaluates the larger intermediate
partial-join population before the final edge. This is the concrete work
mechanism behind its slower closure in the earlier timed sweep. `cand_enum` and
`cand_tested` are equal in every captured cell; zero bound-rejection counts and
the full candidate/Term counters remain in the raw reports.

All these match patterns are handled through indexed graph-edge expansion; the
Term evaluator records zero calls and zero work units for them. This does not
mean Terms are free in general—it identifies the specific native path used by
these edge-only joins. The two rule enumerations are stable across N and arity:
one progressing enumeration and the terminal no-progress enumeration.

## Lineage and limits

The first v1.2 counter captures replicated but did not directly hash
`scale_audit.rs`. They are preserved as diagnostic raw data and excluded from
the final claim. The v1.3 amendment added the counter implementation,
independent analyzer, native matcher sources, and protocol to raw provenance;
the source-complete v1.3 pair is the admitted result.

Counters are instrumented site counts, not CPU instructions, and the
independent complete-path binding count is not assumed to equal native
candidate pairs. This remains one finite-key rule/effect schema on authored
topologies. The dense layered graphs vary degree distribution and edge count
together; there is no natural graph sampling or arbitrary rule-program
coverage.

## Reproduction

Run the same counter runner in two fresh processes, then analyze both captures
against the uninstrumented topology capture:

```sh
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_join_work_attribution_v1_3.py --output evaluation/reports/mint_termination_join_work_attribution_v1_3_a_20260926.json
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_finite_key_join_work_attribution_v1_3.py --output evaluation/reports/mint_termination_join_work_attribution_v1_3_b_20260926.json
.venv/bin/python scripts/analyze_substrate_finite_key_join_work_attribution_v1_2.py evaluation/reports/mint_termination_join_work_attribution_v1_3_a_20260926.json evaluation/reports/mint_termination_join_work_attribution_v1_3_b_20260926.json evaluation/reports/mint_termination_join_topology_v1_20260926.json
```

Protocols: [work attribution preregistration](SUBSTRATE_FINITE_KEY_JOIN_WORK_ATTRIBUTION_PREREG_20260926.md), [v1.3 provenance amendment](SUBSTRATE_FINITE_KEY_JOIN_WORK_ATTRIBUTION_V1_3_AMENDMENT_20260926.md), and the [locked topology design](SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_PREREG_20260926.md). Runner/analyzer: [runner](../../../scripts/substrate_finite_key_join_work_attribution_v1_3.py), [independent analyzer](../../../scripts/analyze_substrate_finite_key_join_work_attribution_v1_2.py). Raw evidence: [process A](../../../evaluation/reports/mint_termination_join_work_attribution_v1_3_a_20260926.json), [process B](../../../evaluation/reports/mint_termination_join_work_attribution_v1_3_b_20260926.json), [analysis](../../../evaluation/reports/mint_termination_join_work_attribution_v1_3_analysis_20260926.json). The earlier [v1.2 provenance-limited captures](../../../evaluation/reports/mint_termination_join_work_attribution_v1_2_a_20260926.json) and [analysis](../../../evaluation/reports/mint_termination_join_work_attribution_v1_2_analysis_20260926.json) remain visible but are not used for the final claim.

## Next gate

Use the attributed counters to design edge-count-matched degree controls and
join-order/selectivity controls. Then repeat the counter/timing pair on
runtime-derived task graphs. Preserve the distinction between instrumented
work counts, uninstrumented closure time, and workload prevalence.
