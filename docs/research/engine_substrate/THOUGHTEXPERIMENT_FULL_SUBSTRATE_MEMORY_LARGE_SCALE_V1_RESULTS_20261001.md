# Full Substrate memory large-scale extension v1 — results

**Result:** 18/18 fresh-process rows completed with branch isolation; six size/backend summaries match the pre-run source/native lock.

The panel measures full-process current RSS/PSS around a branch fork from a normally booted Substrate containing the correction fixture and a linked noise graph. The substrate retains its rule/candidate/observation state; it does not execute candidate prediction or closure during this measurement.

| Added noise nodes | Baseline PSS | Eager fork ΔPSS | Shared-record fork ΔPSS | Shared-graph-page fork ΔPSS | Shared-page / eager ratio | Post-drop ΔPSS: eager / records / pages |
|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 69.0 MiB | 26.48 MiB | 10.94 MiB | 0.31 MiB | 84.7× | 26.51 / 10.96 / 0.31 MiB |
| 200,000 | 98.8 MiB | 57.31 MiB | 26.28 MiB | 1.73 MiB | 33.0× | 57.34 / 26.30 / 1.73 MiB |

At 200k nodes, sharing graph pages lowers the live-fork PSS delta by about 33× versus eager copy and 15× versus shared-record pages. Shared graph pages have a larger delta at 200k than at 100k (1.73 versus 0.31 MiB), while eager copy rises from 26.48 to 57.31 MiB. These are two fixture sizes on one host, not a scaling law. A branch-local node insertion changes current PSS by roughly 0–0.03 MiB; this is near smaps granularity and should not be interpreted as zero write allocation. After branch drop plus GC, measured PSS stays close to the fork delta for all backends, so this run does not demonstrate prompt page/allocator reclamation.

This is full-process memory accounting for one synthetic graph fixture. It includes Python, native engine, booted rules, candidate/observation state, and noise graph; it does not run inference or candidate prediction. PSS is current residency, not peak memory. The backends share graph storage, while other Substrate fields still copy eagerly. Independent hosts and natural task graphs remain unmeasured.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_FULL_SUBSTRATE_MEMORY_LARGE_SCALE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_full_substrate_memory_large_scale_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_full_substrate_pss_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_full_substrate_memory_large_scale_v1_raw_20261001.json)
