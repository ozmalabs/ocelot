# Structural composer family and graph scaling v1 preregistration

This panel broadens full prompted composition beyond actor-recipient identity and records resident-memory snapshots. It crosses four previously exercised rule families—recurrence, repeated conversation reply, actor-recipient relation-only, and actor-recipient actor+verb identity—with 0, 1,000, and 10,000 unrelated graph nodes. Three replicates are captured per cell, in deterministic shuffled order (seed 61003). Every isolated worker runs two untimed same-family composer warmups, then starts from a fresh family context, inserts its assigned unrelated nodes, adds the family's externally supplied cue, samples current RSS, runs the full composer once, and samples RSS again.

Expected target/operator/site outputs are locked from prior held-out structural experiments. The active primary rule store must remain unchanged. RSS is the resident-page count in `/proc/self/statm` multiplied by page size; per-trial deltas are noisy process snapshots and are not allocator-level attribution. The lock captures the base composer harness's native/source provenance and the runner/protocol hashes. This measures prompted proposal construction, not independent residual detection or end-to-end task success.

- Runner: [measure_structural_composer_family_scaling_v1.py](../../../evaluation/substrate_capability/measure_structural_composer_family_scaling_v1.py)
- Analyzer: [analyze_structural_composer_family_scaling_v1.py](../../../evaluation/substrate_capability/analyze_structural_composer_family_scaling_v1.py)
- Lock: [structural_composer_family_scaling_v1_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_family_scaling_v1_lock_20261002.json)
- Results: [structural_composer_family_scaling_v1_20261002.json](../../../evaluation/reports/structural_composer_family_scaling_v1_20261002.json)
