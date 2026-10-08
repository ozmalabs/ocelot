# ShapeDecode verdict-comparator cache v1 — results

The source-locked 80-worker replay of the existing `vision_verdict_comparator` seed's V0 `hamming` arm passed all 11 checks. Workers ran in unique fresh processes over four codebook sizes, five replicates, scan/cache modes, and traced/untraced conditions. Every graph-produced readback selected `r00`; paired readbacks and closure work matched, traces were complete, and source hashes were stable.

| VdSignature parts | Population visits, scan → cache | Cache hits / misses | Median untraced closure, scan → cache | Median wall speedup |
|---:|---:|---:|---:|---:|
| 16 | 512 → 32 | 30 / 2 | 8.11 → 2.86 ms | 2.83× |
| 32 | 2,048 → 64 | 62 / 2 | 26.04 → 5.51 ms | 4.72× |
| 64 | 8,192 → 128 | 126 / 2 | 95.43 → 12.35 ms | 7.73× |
| 128 | 32,768 → 256 | 254 / 2 | 367.80 → 31.14 ms | 11.81× |

Scan visits follow `2P²`; cache visits follow `2P`, matching one full parse per nested Term evaluation plus candidate selection. CPU and wall times track closely. Median peak RSS spans 54.5–56.1 MiB in cached workers and 54.3–56.3 MiB in scan workers, with no clear difference at this measurement resolution.

## Interpretation and limits

This result replicates the earlier cache effect in a second codebook type and in the existing seed-defined comparator rules, whose ShapeDecode Terms sit under `MaxOver` and `Argmax`. The work reduction and speedup grow over 16–128 codebook parts in this one-probe workload. It is stronger evidence for the candidate-at-a-time mechanism than a second hand-built Term, but remains an authored evaluation seed and controlled fixture. It does not establish activation or frequency in ordinary operation, nor natural-task prevalence, general tractability, or a universal complexity bound.

Only the V0 hamming arm, one probe orbit, one 6×6 region resolution, and one host were measured. This replay does not cover `Surface(Text)`, malformed codebook entries, exclusion filters, multi-probe cache lifetime, mutation lifecycle, or tasks outside the comparator seed. No claim is made about cache effectiveness on direct one-shot ShapeDecode calls, where there may be no nested reuse to amortize the first full parse.

## Artifacts

- [Preregistration](SHAPEDECODE_VERDICT_COMPARATOR_CACHE_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/shapedecode_verdict_comparator_cache_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_shapedecode_verdict_comparator_cache_v1.py)
- [Raw capture](../../../evaluation/reports/shapedecode_verdict_comparator_cache_v1_20261005.json)
- [Analysis](../../../evaluation/reports/shapedecode_verdict_comparator_cache_v1_analysis_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/shapedecode_verdict_comparator_cache_v1_lock_20261005.json)
