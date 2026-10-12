# Substrate matcher prefix-work v1 results

Date: 2026-10-01  
Status: complete; all 9 analyzer gates pass.

## Result

The source-locked panel completed 108 fresh workers across three four-clause patterns (path, four-edge star, cycle), three graph shapes (directed path, center-out star, ring), N={16,32}, two input clause orders, and three repeats. In every worker, the independently replayed install order matched the exported native order, and an independent adjacency-based join enumerator reproduced the exact candidate-test count at every clause position. The prefix sums matched global `cand_tested`; per-rule totals reconciled; the effect-free rules left graph facts unchanged; source hashes remained stable.

| Pattern / graph | N | Candidate tests by installed prefix | Total candidate tests |
|---|---:|---:|---:|
| path4 / path | 16 | 15, 14, 13, 12 | 54 |
| path4 / path | 32 | 31, 30, 29, 28 | 118 |
| star4 / star | 16 | 15, 225, 3,375, 50,625 | 54,240 |
| star4 / star | 32 | 31, 961, 29,791, 923,521 | 954,304 |
| cycle4 / ring | 16 | 16, 16, 16, 16 | 64 |
| cycle4 / ring | 32 | 32, 32, 32, 32 | 128 |

The star4-on-star fixture's total work rises 17.6× when N doubles, while path4-on-path and cycle4-on-ring roughly double. The star prefix counts expose the multiplicative join growth directly: at N=32, the fourth prefix alone visits 923,521 candidates. When a pattern is tested against a topology with no continuation, later prefixes are zero; for example path4-on-star takes only 31 candidate tests at N=32. Reversing the clause list did not change total work in these same-relation fixtures (all 18 paired pattern/topology/size cells have ratio 1.0), even though the installed clause order was reversed. This is a useful counterexample to assuming every syntactic order change helps.

## Interpretation and limits

This validates the native per-clause audit as an exact measure of candidate enumeration for these simple patterns and shows that prefix work depends strongly on pattern/graph structure. It does not test mixed relation cardinalities, where the CAN heuristic failure occurs; natural rule families; productive effects; or scalability beyond 32 Concepts. The work supports a next panel with mixed edge types and independently varied relation counts. A practical selector should be judged against these prefix profiles while accounting for the cost of collecting any statistics it uses.

## Reproduction and artifacts

- Protocol: [preregistration](SUBSTRATE_MATCHER_PREFIX_WORK_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/substrate_matcher_prefix_work_v1.py)
- Analyzer: [independent ordering and join simulator](../../../scripts/analyze_substrate_matcher_prefix_work_v1.py)
- Lock: [source/input lock](../../../evaluation/substrate_capability/substrate_matcher_prefix_work_v1_lock_20261001.json)
- Raw data: [108 worker records](../../../evaluation/reports/substrate_matcher_prefix_work_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/substrate_matcher_prefix_work_v1_analysis_20261001.json)

Reproduce with `python3 evaluation/substrate_capability/substrate_matcher_prefix_work_v1.py`; this checks the lock, runs every worker, and invokes the independent analyzer.
