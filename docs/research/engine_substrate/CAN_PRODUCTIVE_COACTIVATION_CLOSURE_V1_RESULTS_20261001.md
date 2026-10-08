# Productive coactivation closure v1 results

Date: 2026-10-01  
Status: complete; all 10 analyzer gates pass.

## Result

The source-locked capture ran 45 fresh workers over N={32,64,128}, five coactivation populations per size, and three replicates per cell. Only `can_native_hebbian_mint` and `can_native_hebbian_reweight` were active. Each input coactivation had `can_tick=1` and stale observation/evidence ticks. Half, rounded down, had a pre-existing causal edge to exercise reweighting; the rest exercised minting.

All 90 audited order arms terminated below the cap, and their terminal probe made no further progress. All 90 arms met the pair-level oracle: each supplied pair had a causal link, `evidence_tick=1`, one confirmation, and zero disconfirmations. Final node/edge counts matched the exact growth oracle. Authored and sparse-first results had identical canonical graph facts in all 45 paired workers. Audited and uninstrumented closure also agreed on progress, final graph, and terminal state. Per-rule candidate counts reconciled with the global total in every arm, and all worker inputs matched the source lock.

| N | Q | Authored candidate tests | Sparse-first candidate tests | Reduction | Audited closure ms, authored → sparse-first |
|---:|---:|---:|---:|---:|---:|
| 32 | 0 | 2,112 | 0 | 100.00% | 3.4 → <0.1 |
| 32 | 32 | 10,800 | 2,944 | 72.74% | 14.6 → 1.2 |
| 32 | 128 | 61,056 | 11,776 | 80.71% | 22.8 → 5.1 |
| 32 | 248 | 188,272 | 22,816 | 87.88% | 56.8 → 6.3 |
| 32 | 992 | 2,574,000 | 91,264 | 96.45% | 321.2 → 53.0 |
| 64 | 0 | 8,320 | 0 | 100.00% | 13.0 → <0.1 |
| 64 | 64 | 43,104 | 11,008 | 74.46% | 32.3 → 1.8 |
| 64 | 256 | 244,992 | 44,032 | 82.03% | 85.3 → 8.6 |
| 64 | 1,008 | 2,804,896 | 173,376 | 93.82% | 501.0 → 50.4 |
| 64 | 4,032 | 41,556,320 | 693,504 | 98.33% | 4,256.5 → 301.1 |
| 128 | 0 | 33,024 | 0 | 100.00% | 29.0 → <0.1 |
| 128 | 128 | 172,224 | 42,496 | 75.33% | 130.6 → 6.5 |
| 128 | 512 | 981,504 | 169,984 | 82.68% | 372.6 → 22.8 |
| 128 | 4,064 | 43,364,416 | 1,349,248 | 96.89% | 5,344.5 → 248.8 |
| 128 | 16,256 | 667,968,192 | 5,396,992 | 99.19% | 57,319.0 → 2,369.3 |

For each nonempty population, sparse-first reduces candidate tests by 72.74–99.19%. The speedup is large because the authored pattern order begins with broad Microtheory membership joins, while sparse-first begins with observed coactivation records. At N=128,Q=16,256, candidate work is about 124× lower and audited closure wall time about 24× lower. At N=128,Q=0, sparse-first performs no candidate tests, while authored order still performs 33,024. This shows that population and join order jointly determine the realized closure cost in this fixture; it does not establish that sparse-first wins on other relation distributions or rule sets.

## Claim boundary

This is productive closure evidence for two production CAN rules on synthetic graphs with supplied ledgers and deliberately balanced mint/reweight eligibility. It is stronger than a read-only matcher probe because the intended effects occur and are independently checked. It remains finite-size evidence for one source revision, host, pair layout, and rule family. It does not demonstrate natural-task tractability, a general asymptotic bound, full CAN closure behavior, or CPU-scale capacity beyond N=128. The timing values are from instrumented runs and are diagnostic; separate uninstrumented arms were used to verify semantic parity, not to make an uninstrumented timing claim.

## Reproduction and artifacts

- Protocol: [preregistration](CAN_PRODUCTIVE_COACTIVATION_CLOSURE_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/can_productive_coactivation_closure_v1.py)
- Analyzer: [gate and summary script](../../../scripts/analyze_can_productive_coactivation_closure_v1.py)
- Lock: [source/input lock](../../../evaluation/substrate_capability/can_productive_coactivation_closure_v1_lock_20261001.json)
- Raw data: [45 worker records](../../../evaluation/reports/can_productive_coactivation_closure_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/can_productive_coactivation_closure_v1_analysis_20261001.json)

Reproduce with `python3 evaluation/substrate_capability/can_productive_coactivation_closure_v1.py`; the runner checks the lock, executes all workers, and invokes the analyzer.
