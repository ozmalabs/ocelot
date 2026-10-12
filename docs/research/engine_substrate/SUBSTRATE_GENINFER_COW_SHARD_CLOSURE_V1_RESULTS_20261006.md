# GenInfer full-seed closure by COW shard count — results

The paired gate passed across 15 cases and 30 fresh worker processes. The capture names and hashes each loaded temporary native binary; every worker's source manifest was stable before and after execution. The independent analyzer confirmed paired closure-work counts, statuses, residuals, transformation receipts, acquisition decisions, and exact training/held-out/corruption outcomes. The active extension was not replaced.

## Observed cost

At the fixed bound of 5, the positive training closure median grows with relation count in both variants:

| Relation count | 64 shards | 512 shards | 512/64 |
|---:|---:|---:|---:|
| 4 | 52.469 ms | 52.531 ms | 1.001× |
| 16 | 211.641 ms | 216.731 ms | 1.024× |
| 64 | 873.071 ms | 865.018 ms | 0.991× |

Held-out closure medians were 0.729/0.754 ms (4 relations), 1.458/1.437 ms (16), and 4.495/4.496 ms (64), for 64/512 shards respectively. The disabled control training median was 1.280/1.230 ms; predicate-corrupt training was 20.515/19.464 ms, while its held-out phase was 1,275.156/1,279.551 ms. Peak-RSS deltas were 764–952 KiB, too coarse to resolve a useful memory difference in this workload.

The positive training medians differ by −0.9% to +2.4% between variants, which does not show a meaningful closure speedup from 512 shards. Positive training cost rises by about 16.6× from 4 to 64 relations while relation count rises 16×, but three sizes and three repetitions do not establish asymptotic behavior. The expensive phase is the bounded GenInfer training path; held-out transforms are much cheaper once the generator is present, except for the intentionally mismatching predicate-corrupt tail control. This is a useful workload decomposition, not a general tractability result.

## Decision and next work

Keep the production default at 64. The larger shard count's first-write advantage in graph mutation did not translate into a measurable GenInfer closure gain here. Next profile the positive training closure by native phase and graph access/mutation class, then run the same paired variants on a representative live route that forks, mutates, and closes a whole `Substrate`. Keep candidate-count scaling separate from graph-size scaling. The `predicate_corrupt` held-out stage is intentionally adversarial and can take around 1.3 seconds; it should remain a separate tail-cost control rather than be averaged into ordinary operating cost.

The results support only this source-matched build and synthetic full-seed shape transformation task. They do not establish natural-task frame locality, rare minting, general learning capability, or CPU scale.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_COW_SHARD_CLOSURE_V1_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_cow_shard_closure_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_cow_shard_closure_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_cow_shard_closure_v1_20261006.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_cow_shard_closure_v1_analysis_20261006.json)
