# Long-term memory restart recall probe

**Date:** 2026-09-25. This direct probe measures a narrow implementation repair: rebuilding the native long-term shape index from durable JSON record files when a fresh Python adapter binds to a new substrate, then retrieving by exact key or shape.

## Method

[`substrate_memory_restart_probe.py`](../../../scripts/substrate_memory_restart_probe.py) starts three separate Python processes against one temporary record directory: a writer, an exact-key reader, and a shape reader. The writer consolidates one typed record, links it to an anchor, forces its cluster cold, and exits. Each reader creates a fresh `Substrate` and `LongTermMemory`, binds (triggering the disk scan), checks `findable`, and pages the record into the new graph. The shape arm also invokes native shape descent. The probe checks the durable attributes, process IDs, index cluster count, node count, and edge count. The unique temporary directory is removed at process completion.

The pre-run lock is [`memory_restart_probe_lock_20260925.json`](../../../evaluation/substrate_capability/memory_restart_probe_lock_20260925.json); it records SHA-256 hashes for the harness, adapter, Rust sources, extension, and build manifest. Two harness amendments are recorded in the lock after initial diagnostic failures: use unchecked edge insertion for the fixture relation, serialize only attrs from the native record view, and bind before checking the adapter's lazy-restored name set. Outcome definitions did not change after the first execution. The raw final measurement is [`substrate_memory_restart_probe_20260925.json`](../../../evaluation/reports/substrate_memory_restart_probe_20260925.json). The extension was built through `scripts/engine_build.sh`; no test suite was run.

## Results

| Measure | Observation |
|---|---|
| Process separation | Writer, exact-key reader, and shape reader used distinct PIDs. |
| Disk index recovery | Both readers reconstructed one cluster and reported the record findable after binding. |
| Exact-key recall | Returned the stored attrs (`label`, `new_signs`, `utts`, `round`) into the fresh substrate. |
| Shape recall | Shape descent also paged the record into the fresh substrate with the same attrs. |
| Wall time | 0.146 s total for the three child processes, about 0.046–0.050 s each including Python import/startup. This is a one-record functional probe, not a scaling estimate. |
| Relationship preservation | Reader edge count was 0. The durable file stores attributes only; anchor/chain structure is not persisted. |

This resolves the prior empty-index and stubbed exact-key path for this single-record case. The adapter reconstructs one index entry per file at first bind, and native lookup pages the containing shape cluster. It does not restore node identity across restart or incident edges, and the index is rebuilt by a linear directory scan.

## Remaining work

Next memory gates are: (1) scale the restart scan and recall across record and cluster counts, recording bind latency/RSS and exact-key correctness; (2) define duplicate-key, malformed-file, and concurrent-writer policies; (3) decide whether durable records should include stable IDs and incident edges or whether memory records are intentionally attribute snapshots; (4) exercise retrieval quality and interference on task-linked records; and (5) measure scan amortization and impose a practical bound or persistent index if it dominates startup. Do not claim relationship-preserving persistence until the edge/identity model is implemented and measured.
