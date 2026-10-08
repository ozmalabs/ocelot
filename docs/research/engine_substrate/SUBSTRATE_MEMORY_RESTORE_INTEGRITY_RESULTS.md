# Long-term memory restore integrity probe

**Date:** 2026-09-25. This probe sets a deterministic recovery policy for duplicate durable keys and checks malformed-record handling in a fresh process.

## Policy and protocol

During first-bind restore, each valid record key is indexed once. If a second valid JSON record declares the same key, the adapter removes that key from every native shape cluster, marks it ambiguous, and skips any further files with that key. `findable` is false and exact-key recall returns `None` for that key. A valid unique key remains indexed and recallable. Malformed JSON or a JSON object missing required `key`, `round`, or `attrs` fields is skipped and counted. Duplicate contents are treated as ambiguous even if they appear equivalent; no last-writer-wins rule is inferred from filename order.

[`substrate_memory_restore_integrity_probe.py`](../../../scripts/substrate_memory_restore_integrity_probe.py) uses a writer process to create two valid native records, a second file with a conflicting copy of one key but different shape/attrs, malformed JSON, and a JSON object missing attrs. A fresh reader process binds, probes both keys, reads restoration counters and validates the unique record's attributes. Inputs and the expected policy were locked before the run in [`memory_restore_integrity_lock_20260925.json`](../../../evaluation/substrate_capability/memory_restore_integrity_lock_20260925.json). The result is [`substrate_memory_restore_integrity_20260925.json`](../../../evaluation/reports/substrate_memory_restore_integrity_20260925.json). One writer/reader pair was run; this is a deterministic mechanism probe, not a reliability-rate estimate.

## Result

The reader reported one indexed unique record, one ambiguous duplicate key, and two skipped malformed records. The duplicate key was not findable and exact-key recall returned `None`; the unique key was findable and its attributes matched. The restored index contained one cluster and the reader graph contained one node and no edges. Different writer and reader PIDs confirm this was a process restart.

This prevents nondeterministic duplicate-key recall across clusters and makes basic malformed-file skipping observable. It does not validate checksums, truncated-but-valid semantic content, concurrent writers, crash consistency, same-key repair, or whether first-bind skipping should be surfaced as a hard error in production. The current decision favors refusing ambiguous recall while allowing the rest of the store to load.
