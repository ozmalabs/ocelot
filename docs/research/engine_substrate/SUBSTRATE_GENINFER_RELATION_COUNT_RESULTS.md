# GenInfer relation-count scaling results

**Run date:** 2026-09-26  
**Protocol:** [`SUBSTRATE_GENINFER_RELATION_COUNT_PREREG_20260926.md`](SUBSTRATE_GENINFER_RELATION_COUNT_PREREG_20260926.md)  
**Engine:** `24073a9be843`  
**Evidence grade:** fixed-bound direct evaluator timing; five repetitions per relation count; all outcome and provenance checks pass

## Result

All 25 direct calls return `[2,1,1,1]` and independently report 6,560 enumerated matrices. The bound stays at B=4 while relation count increases through predicate-distinguished copies of the same asymmetric L motif.

| Relations | Candidates/call | Median time | Min–max | Median candidates/s | Median ratio vs 4 |
|---:|---:|---:|---:|---:|---:|
| 4 | 6,560 | 7.676 ms | 7.461–10.947 ms | 854,591 | 1.00× |
| 8 | 6,560 | 14.692 ms | 14.391–20.671 ms | 446,505 | 1.91× |
| 16 | 6,560 | 28.183 ms | 27.668–32.464 ms | 232,765 | 3.67× |
| 32 | 6,560 | 56.450 ms | 54.641–57.581 ms | 116,209 | 7.35× |
| 64 | 6,560 | 119.592 ms | 118.493–124.206 ms | 54,853 | 15.58× |

The 16× relation increase produces a 15.58× median-time increase. This is consistent with approximately linear relation-count cost for the repeated motif at fixed B and candidate count. It does not identify which internal suboperation accounts for that cost.

## Interpretation and limits

The measured quantity is direct evaluator wall time on one graph per condition, with graph construction and process startup excluded. Each relation-count condition repeats the same four coordinate positions under distinct predicate labels; this holds geometric search difficulty fixed while increasing the signature data processed by each candidate. The result is therefore a controlled size curve, not a representative sample of shapes.

Together with the B=4/8/12 search-bound sweep, these measurements begin to separate two dimensions of GenInfer cost: candidate enumeration grows as `(2B+1)^4−1`, while fixed-bound time grows approximately linearly with relation count on this fixture. Five repeats and one motif do not establish a universal cost model, diverse-shape behavior, natural-task tractability, full seed closure cost, or higher-dimensional behavior.

## Reproduction artifacts

- Preregistration: [`SUBSTRATE_GENINFER_RELATION_COUNT_PREREG_20260926.md`](SUBSTRATE_GENINFER_RELATION_COUNT_PREREG_20260926.md)
- Runner: [`geninfer_relation_count_probe_v1.py`](../../../scripts/geninfer_relation_count_probe_v1.py)
- Independent analyzer: [`analyze_substrate_geninfer_relation_count_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_relation_count_probe_v1.py)
- Raw capture: [`substrate_geninfer_relation_count_probe_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_relation_count_probe_v1_20260926.json)
- Analysis: [`substrate_geninfer_relation_count_probe_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_relation_count_probe_v1_analysis_20260926.json)
