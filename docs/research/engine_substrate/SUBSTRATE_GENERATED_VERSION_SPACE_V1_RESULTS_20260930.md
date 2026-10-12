# Generated Version Space and Label Blind Query Selection v1 Results

**Result:** the bounded generator completed on all five preregistered triangular-number anchors. Entropy ranking found the held-out-correct behavior after one query on all anchors, but fixed-first and seeded-random did too. There is no measured selector advantage on this task family.

| Training anchor | Pool size | Terms explored | Generation wall time | Entropy query | Entropy survivors |
|---:|---:|---:|---:|---|---:|
| 6 | 2 | 7,905 | 0.603 s | n=2 | 1 |
| 7 | 3 | 7,905 | 0.621 s | n=2 | 1 |
| 8 | 3 | 7,905 | 0.647 s | n=2 | 1 |
| 9 | 3 | 7,905 | 0.666 s | n=2 | 1 |
| 10 | 1 | 7,905 | 0.647 s | n=2 | 1 |

Every bounded search reached `max_size`; each pool contained a hypothesis matching the grounded slow summation oracle on all eight held-out inputs (`n=13..20`). Entropy, fixed-first, and seeded-random each uniquely identified that held-out behavior in 5/5 anchor conditions and 50/50 random draws. All selected `n=2` for fixed-first and entropy. The oracle-best upper bound also selected `n=2`, while inspecting all 10 candidates (10 oracle calls per anchor versus one for the other policies). The generated pools were so small and so easily separated that this is a negative comparison for the value of entropy ranking here.

The generator ran about 0.65 seconds and 7,905 candidate evaluations per anchor on this host. This measures a narrow symbolic grammar with fixed literals, size cap 7, one labeled row, and an explicit unlabeled query pool. It does not measure generation over open-ended grammars, show an advantage over a competent fixed query order, or establish cross-task capability. An exploratory population-variance run exceeded a 20-second cap after 102,703 explored terms and returned a partial pool, documenting a materially harder search regime.

## Reproduction and evidence

- [Preregistration](SUBSTRATE_GENERATED_VERSION_SPACE_V1_PREREG_20260930.md)
- [Source-locked runner](../../../scripts/substrate_generated_version_space_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_generated_version_space_v1.py)
- [Source and engine lock](../../../evaluation/substrate_capability/substrate_generated_version_space_v1_20260930_lock.json)
- [Raw capture](../../../evaluation/reports/substrate_generated_version_space_v1_20260930_raw.json)
- [Analysis capture](../../../evaluation/reports/substrate_generated_version_space_v1_20260930_analysis.json): 214 checks passed, zero failed.

Next work should target an independently authored task where fixed-first does not already identify the correct hypothesis, and must report pool completeness and generation cost alongside query outcomes. Population variance is a candidate, but requires a deliberately bounded or more efficient synthesis regime; timeout-returned pools must not be described as exhaustive.
