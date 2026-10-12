# Bigville CAN runtime partition replay — diagnostic v3.1

**Run:** 2026-09-25. **Evidence grade:** post-amendment diagnostic on project-authored task data. **Runner:** [`substrate_bigville_can_runtime_partition_replay_v3_1.py`](../../../scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py). **Independent analyzer:** [`analyze_substrate_bigville_can_runtime_partition_replay_v3_1.py`](../../../scripts/analyze_substrate_bigville_can_runtime_partition_replay_v3_1.py).

## Preserved discovery history

The first authored replay, preregistered under [`SUBSTRATE_BIGVILLE_CAN_RUNTIME_PARTITION_REPLAY_PREREG_20260925.md`](SUBSTRATE_BIGVILLE_CAN_RUNTIME_PARTITION_REPLAY_PREREG_20260925.md), reapplied the scenario evidence after it was already present in the baseline. State parity passed, but the first omitted-notification control was a no-op. Its raw record and lock are preserved at [`v1 raw JSON`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_20260925.json) and [`v1 lock`](../../../evaluation/substrate_capability/bigville_can_runtime_partition_replay_lock_20260925.json).

Diagnostic v2 started from priors and applied the authored two-item scenario evidence once to ten residents. Its 10 event/full checkpoints passed, but the omitted-notification control checked state immediately after the field write, before settlement. The analyzer therefore fails its sensitivity check; the record is preserved at [`v2 raw JSON`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_v2_20260925.json), [`v2 analysis`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_v2_analysis_20260925.json), and [`v2 lock`](../../../evaluation/substrate_capability/bigville_can_runtime_partition_replay_v2_lock_20260925.json).

Diagnostic v3 corrected that control but compared all ten omitted updates to the event arm after only the first update, then exited on a stale field name. Its lock and partial raw output are preserved at [`v3 raw JSON`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_20260925.json) and [`v3 lock`](../../../evaluation/substrate_capability/bigville_can_runtime_partition_replay_v3_lock_20260925.json). The exact v3.1 repair is recorded in [`v3.1 amendment`](SUBSTRATE_BIGVILLE_CAN_RUNTIME_PARTITION_REPLAY_V3_1_AMENDMENT_20260925.md); v3.1 is still diagnostic, not a confirmatory rerun.

## v3.1 protocol and results

The current-source runner loads all 100 residents from [`bigville_cast100.json`](../../../seeds/bigville_cast100.json), constructs their individual CANs with [`bigville_can_beliefs.py`](../../../worlds/bigville_can_beliefs.py), applies the authored scenario evidence once per resident in a ten-step sequence, and runs only `can_native_update_3state`. Runtime `causal_influence` adjacency produced 100 connected components, each of five Concepts, mapped through live `has_concept` membership to the 100 Microtheories. No causal edge crossed components.

All ten sequential caller-notified checkpoints matched full round-robin rescans and had independently recomputed zero residual. The no-notification control applied all ten evidence updates without settlement; it differed from the notified terminal projection and had five residual Concept updates. Provenance checks confirmed current-source native engine, no stale Rust files, and matching hashes for protocol, runner, analyzer, cast, seed, builder, native extension and Rust sources. Details are in the [`v3.1 preregistration amendment`](SUBSTRATE_BIGVILLE_CAN_RUNTIME_PARTITION_REPLAY_V3_1_AMENDMENT_20260925.md), [`run lock`](../../../evaluation/substrate_capability/bigville_can_runtime_partition_replay_v3_1_lock_20260925.json), [`raw output`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_1_20260925.json), and [`independent analysis`](../../../evaluation/reports/substrate_bigville_can_runtime_partition_replay_v3_1_analysis_20260925.json).

| Accumulated over ten evidence updates | Caller-notified components | Full rescans |
|---|---:|---:|
| Scoped frame turns | 10 | 1,500 |
| Candidate pairs enumerated | 95 | 7,545 |
| Term evaluations | 4,461 | 336,039 |
| Progress applications | Equal at every checkpoint | Equal at every checkpoint |

The candidate-pair count is 79.4× lower and Term evaluations 75.3× lower in the caller-notified arm. These are deterministic instrumented operation counts on this workload; they are not elapsed time, allocation, native-memory, or CPU-scaling measurements. The reduction is enabled by the authored cast's actual disconnected resident networks, not by a learned hierarchy. Both arms use the same native scoped settlement implementation.

## Claim boundary and next gate

This establishes useful locality evidence for one authored project workload: 100 independent resident CANs with five Concepts each. It is not an external or natural-world sample. There are no cross-resident causal edges, so this result does not exercise propagation across connected frames or quantify boundary width. Caller notification is still supplied by the Python runner; the run does not measure native effect-to-frame notification, node birth/deletion, AddNode idempotence, wall time, memory, or production GALS.

Next confirmation should use an independently specified authored workload with connected frame dependencies or varying resident topology, preserve an independent full-graph oracle, and include repeated mutation sequences. In parallel, implement a native notification prototype only after its effect-to-frame mapping has a frozen semantic contract, then compare native and caller-notified schedules against full rescans while recording the same counters plus partition maintenance and memory. Test mint idempotence separately on full CAN closure rules containing `can_native_note_coactivation` (`AddNode`).
