# Native memory page-out and restart probe

**Date:** 2026-09-25. This mechanism and small-scale cost probe uses the current native extension to distinguish same-process page-in from restart recovery and check graph relationship preservation.

## Method

[`substrate_memory_lifecycle_probe.py`](../../../scripts/substrate_memory_lifecycle_probe.py) runs three replicates at 1, 8, 32, and 64 records. Records share one category-shape cluster. Each is linked from an external anchor, and adjacent records have a chain edge. After native consolidation, the probe forces the cluster cold with `hot_window=0`, allocates one unrelated node per record to consume freed NodeIDs, and shape-recalls the cluster on the same substrate. It also runs a writer subprocess that exits after consolidation, then a reader subprocess with a new substrate against the same temporary directory. Each cell uses a unique `TemporaryDirectory`, removed automatically; the fixed store used by the legacy demo is untouched.

The raw output, source hashes, build-manifest hash, and native-extension hash are in [`substrate_memory_lifecycle_20260925.json`](../../../evaluation/reports/substrate_memory_lifecycle_20260925.json). The extension hash matches its build manifest. No Rust rebuild was needed.

## Observations

| Check | Observation |
|---|---|
| Page-out | All records leave the live graph and all incident anchor edges are removed; the cluster is reported evicted. |
| Same-substrate shape page-in | All 1/8/32/64 attributes are decoded in every replicate. Median page-in ranges from 0.018 ms (1 record) to 0.4536 ms (64 records); median consolidation ranges from 0.0585 ms to 1.7795 ms. |
| Node IDs | With interleaved allocations, 0 of 1/8/32/64 record IDs were restored in every replicate. The paired one-record no-interleaving control reuses its ID (1/1). ID behavior depends on allocation conditions. |
| Relationship restoration | 0 anchor edges and 0 chain edges are restored in every replicate. The durable JSON contains record attributes, not incident edges. |
| Storage size | Median-equivalent observed file totals are 159, 1,272, 5,111, and 10,231 bytes for 1, 8, 32, and 64 records respectively (the three replicate values match within each size). |
| Actual process restart | Writer and reader used different PIDs. The reader found `process-restart-probe.json`, but its new substrate had zero indexed clusters and shape recall returned `None`. The per-size sweep independently found the same empty-index condition in every fresh-substrate instance. |
| Exact-key adapter recall | `LongTermMemory.recall(key, ...)` returns `None`. |

These measurements establish same-process attribute round-trip over one synthetic cluster, with observed page-in and consolidation time increasing with record count over this small range. The no-interleaving control reproduces single-record ID reuse; the interleaved-allocation sweep reuses no IDs. They do not establish a general asymptotic envelope. Edge restoration failed throughout, contradicting the historical online-plan description. The historical transparent page-in installer `domains/paged_memory.py` is absent from the current checkout, and no installer for `substrate.graph`'s optional recall-on-miss hook was found.

## Limits and next gate

The scale sweep uses one synthetic cluster, three replicates per size, and same-process substrate instances. The separate actual process restart check covers one record. Conflicting keys, malformed files, concurrent readers/writers, and realistic retrieval cues remain untested. Before long-term memory can count as relationship-preserving persistence, implement or restore index reconstruction and edge-aware records, install a bounded recall-on-miss path, and run multi-process corruption and task-level retrieval measurements. Episodic graph-rule behavior is separate and is not evaluated by this probe.
