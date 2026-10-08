# Unprofiled full seed boot repeat results

Date: 2026-09-25  
Status: six fresh processes; full boot-state parity passed

## Startup envelope

The probe ran three cold and three warm processes in the preregistered order. Each timer includes `WorldAdapter(seeds=())` construction and `load_all_seeds`, excluding interpreter/module imports and any domain task. All six processes used the same 833-manifest snapshot, yielded 24,784 nodes and 11,090 edges, and matched full graph, grammar, rule store, access sets, rule order, and load report. All six PIDs were distinct. Each warm load preserved the cache bytes.

| Cache state | Wall time, seconds | Median | CPU time, seconds | Median |
|---|---|---:|---|---:|
| Cold (n=3) | 30.57, 33.32, 32.18 | 32.18 | 31.32, 33.99, 32.84 | 32.84 |
| Warm (n=3) | 26.13, 26.75, 27.96 | 26.75 | 26.80, 27.34, 28.65 | 27.34 |

The warm median is 5.43 seconds lower in this six-process run. This is a descriptive difference on one host and corpus, not a general cache-speedup claim; n=3 per state is small and the earlier workload probe showed noisy per-process variation. The result confirms that warm cache does not make full boot cheap: the same fixed corpus still takes about 27 seconds at the median.

## Interpretation

Together with the profiled stage results, this suggests the seed index is only one startup cost. Cache validation/build accounts for part of the cold/warm gap, while manifest installation, JSON handling, rule export, and boot-time self-model provenance persist in warm mode. The mirror has multiple downstream consumers, including self-query, reflective rule selection/editing, conversation response, and frozen-core provenance checks. No deferral or removal was tested or proposed.

Next separate startup imports, manifest installation, and self-model mirror cost on more than one corpus size. For any eager/lazy mirror design, first lock consumer-level semantic gates and test complete rule/program/provenance coverage; a timing reduction without those gates is not an acceptable result.

## Artifacts

- Protocol: [`preregistration`](SUBSTRATE_SEED_BOOT_UNPROFILED_REPEATS_PREREG_20260925.md)
- Source/corpus lock: [`lock JSON`](../../../evaluation/substrate_capability/seed_boot_unprofiled_repeats_lock_20260925.json)
- Runner: [`unprofiled startup probe`](../../../scripts/substrate_seed_boot_unprofiled_repeats_v1.py)
- Raw data: [`six boot records`](../../../evaluation/reports/substrate_seed_boot_unprofiled_repeats_v1_20260925.json)
- Self-model consumers: [`consumer audit`](SUBSTRATE_SELF_MODEL_BOOT_CONSUMER_AUDIT.md)
- Stage attribution: [`cProfile results`](SUBSTRATE_SEED_BOOT_PROFILE_RESULTS.md)
