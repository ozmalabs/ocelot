# GenInfer scoped population trace v1 results

Date: 2026-10-05  
Protocol: [preregistration](SUBSTRATE_GENINFER_SCOPED_POPULATION_TRACE_V1_PREREG_20261005.md)  
Runner: [`substrate_geninfer_scoped_population_trace_v1.py`](../../../evaluation/substrate_capability/substrate_geninfer_scoped_population_trace_v1.py)  
Analyzer: [`analyze_geninfer_scoped_population_trace_v1.py`](../../../evaluation/substrate_capability/analyze_geninfer_scoped_population_trace_v1.py)

## Outcome

All gates pass for nine source-locked production-rule captures: three fresh processes each for unscoped global, explicit shared scope, and per-frame scope at K=2. Source/build inputs remain stable, there are no trace drops, scope receipts are consistent, and both frame transformations match their exact oracle in every capture.

Median helper work over the two-frame closure is:

| Work event | Frame scoped | Explicit global | Unscoped global |
|---|---:|---:|---:|
| Typed population nodes enumerated | 76 | 76 | 76 |
| Selected-node attributes counted | 28 | 56 | 320 |
| Codebook parts parsed | 4 | 8 | 76 |
| Search candidates | 9,600 | 19,200 | 19,200 |

The population scan count is invariant across modes: two GenInfer queries each traverse all 38 `ShapeSignature` population nodes. Exact `scope_id` filtering then reduces attribute inspection, parsing, and search. Per-frame scope halves candidate work relative to a shared scope on this two-frame fixture; explicit scope cuts parsed parts from 38 per query to 2. The `unscoped_global` arm parses 38 parts per query, while its search counter remains 19,200 because not every parsed part enters the measured candidate loop.

## Interpretation

This is direct current-source runtime evidence for both sides of the scoped-GenInfer tradeoff: exact supplied scopes reduce downstream work without changing the tested outputs, while type-index population enumeration remains global. It gives a concrete implementation target: add a scope-aware population index (or equivalent exact index selection) so the loader can avoid visiting unrelated nodes, then repeat this trace with semantic parity and maintenance cost included.

Scope IDs and the correct assignments are authored by the benchmark. The experiment does not discover cheap cuts, validate scope provenance, cover nested/shared interfaces, establish frame-locality prevalence, or measure end-to-end system scaling. The work counters cover the selected loop sites, not all native work. The result is also a two-frame synthetic geometry fixture, not a natural task sample.

## Artifacts

- [Source lock](../../../evaluation/substrate_capability/geninfer_scoped_population_trace_v1_lock_20261005.json)
- [Nine-case capture](../../../evaluation/reports/geninfer_scoped_population_trace_v1_20261005.json)
- [Independent analysis](../../../evaluation/reports/geninfer_scoped_population_trace_v1_analysis_20261005.json)
