# Episodic graph checkpoint and retrieval scale envelope — 2026-09-25

## Result

The pre-locked sweep ran two independent writer/reader process pairs at N=6, 24, 78, and 192 graph-resident Episodes. All 600 post-restart exact-cue queries returned the expected summary with `recalled` provenance and `not_observed` status. Every reader restored the declared Episode count and closed cleanly after the checkpoint cleanup fix. Writer and reader PIDs were distinct for every pair.

| Episodes | Checkpoint bytes | Save median | Load median | Binding closure median | Query tick median | Query p95 | Per-reader total query ticks | Peak RSS max (writer / reader) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 55,326 | 4.47 ms | 6.76 ms | 0.47 ms | 0.168 ms | 0.443 ms | 1.28 ms | 36.7 / 29.9 MiB |
| 24 | 84,310 | 5.83 ms | 7.75 ms | 0.69 ms | 0.371 ms | 0.392 ms | 9.20 ms | 37.2 / 29.7 MiB |
| 78 | 172,138 | 11.54 ms | 10.64 ms | 2.50 ms | 2.190 ms | 2.270 ms | 170.88 ms | 38.4 / 30.7 MiB |
| 192 | 358,238 | 22.51 ms | 16.48 ms | 11.55 ms | 12.004 ms | 12.421 ms | 2,310.83 ms | 42.0 / 34.0 MiB |

These are two-repeat medians over synthetic data; RSS includes interpreter/native import baseline. From 6 to 192 episodes (32×), median query tick rose about 71× and total per-reader query ticks about 1,807×. First-query median and last-query median were similar at each size (at N=192: 12.79 vs 12.29 ms), suggesting the high latency is not only accumulated query bookkeeping. The suite is small and does not identify the exact algorithmic cause. No matcher operation counters, alternative query batching, or graph decomposition were measured here.

Checkpoint bytes grew 6.5× over the same 32× episode increase; save time grew about 5×, and load time about 2.4×. These modest-size observations do not support extrapolation to millions of nodes. The largest run's 384 queries across two replicates each took a median per-query tick of about 12 ms; that is the important current-source warning for the application path, even though persistence and answer quality remained correct.

## Interpretation

This measures `WorldAdapter` full-graph checkpointing and graph-authored episodic retrieval, not the separate LongTermMemory/MemoryFaculty JSON index. It establishes intact restart and exact-key answer quality through N=192 for this authored schema. The sharp query-time growth is a tractability signal requiring larger repeated runs and native candidate/effect attribution before describing a complexity class. It is not proof of quadratic runtime or general CPU performance.

Semantic corruption remains undetected in valid JSON as measured by the checkpoint recovery probe. This scale sweep does not include corrupted checkpoints, semantic cues, or natural-world graphs.

## Reproducibility

- Protocol: [`SUBSTRATE_EPISODIC_CHECKPOINT_SCALE_PREREG_20260925.md`](SUBSTRATE_EPISODIC_CHECKPOINT_SCALE_PREREG_20260925.md)
- Pre-run lock: [`episodic_checkpoint_scale_lock_20260925.json`](../../../evaluation/substrate_capability/episodic_checkpoint_scale_lock_20260925.json)
- Runner: [`substrate_episodic_checkpoint_scale.py`](../../../scripts/substrate_episodic_checkpoint_scale.py)
- Independent analyzer: [`analyze_substrate_episodic_checkpoint_scale.py`](../../../scripts/analyze_substrate_episodic_checkpoint_scale.py)
- Raw records: [`substrate_episodic_checkpoint_scale_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_scale_20260925.json)
- Independent analysis: [`substrate_episodic_checkpoint_scale_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_scale_analysis_20260925.json)

All seven locked input hashes matched. No exploratory worker was run before the lock.
