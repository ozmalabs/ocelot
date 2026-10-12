# Batched contract-query partial-domain and operator coverage v1.1 — results

**Result:** all seven analyzer gates pass across 32 fresh workers (eight targets × two repetitions × two arms). Uncached and lazy-matrix arms produce identical queries, entropy, partition sizes, ordered predictions, labels, terminal conditions, and final target. The independent Python oracle matches native results for all eight Term families over complete and partial inputs. The matrix path refuses `Holds` hypotheses before calling the evaluator.

The input grid mixes `{x}` with `{x,y}` for 44 candidate rows; 12 selected queries omit `y`, showing that both routes can use a discriminating partial record. Four target cases are already singletons after the initial observation and make zero queries. The lazy matrix evaluates only evidence-relevant survivor/input pairs: it uses 8 calls in those zero-query cases, 96 for two of the one-query cases, and 184 for the other one-query cases. Corresponding uncached counts are 8, 106, and 196. Both arms identify every target in the finite supplied pool.

## Cost boundary and interpretation

Across these tiny H=8 cases, median measured selector time is 0.634 ms uncached and 0.832 ms with the lazy matrix. This supports the intended reduction in redundant evaluations but shows that matrix bookkeeping can cost more than the saved native calls when only zero or one query is needed. The performance gain previously measured at H=32–512 and 5–9 sequential queries does not imply a gain for small, already-resolved tasks. These timings are one-host descriptive evidence; the confirmatory purpose here is semantic behavior across mixed operators and partial inputs.

The lazy update fixes eager matrix population: it first applies existing observations, returns immediately if fewer than two hypotheses survive, and only evaluates candidate inputs for current survivors. `Holds` remains outside the allowed matrix path. The implementation remains opt-in. Next measure the crossover over query depth and survivor fraction, then repeat with task-generated Terms and partial domains before any default integration.

## Artifacts

- [Base preregistration](SUBSTRATE_CONTRACT_QUERY_BATCHED_PARTIAL_DOMAIN_V1_PREREG_20261002.md)
- [Lazy-matrix amendment](SUBSTRATE_CONTRACT_QUERY_BATCHED_PARTIAL_DOMAIN_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_batched_partial_domain_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_contract_query_batched_partial_domain_v1_1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_batched_partial_domain_v1_1_analysis_20261002.json)
