# Structural composer family and graph scaling v1.1 preregistration

This amendment retains the v1 36-trial latency/proposal record and fixes the RSS scope. V1's snapshots bracketed composition after the unrelated graph had already been built, so they estimate only the composer-phase resident-page change and do not expose the graph-size memory cost. V1.1 records current RSS at three points in each fresh worker: before adding unrelated nodes, after adding the nodes, and after the measured composition. It derives separate node-insertion and composer-phase deltas.

The design remains four families (recurrence, repeated reply, actor-recipient relation-only, actor-recipient actor+verb), three graph sizes (0/1,000/10,000 unrelated nodes), three replicates per cell, deterministic shuffled order (seed 61003), and two family-specific warmups per isolated worker. Proposal target/operator/site and primary-rule isolation gates are unchanged. RSS is sampled from Linux `/proc/self/statm`; page-level deltas may be noisy or negative for the short composer phase and should be treated as coarse process measurements, not allocator attribution. Lock provenance captures the base composer harness and native binary hashes.

- Runner: [measure_structural_composer_family_scaling_v1_1.py](../../../evaluation/substrate_capability/measure_structural_composer_family_scaling_v1_1.py)
- Analyzer: [analyze_structural_composer_family_scaling_v1_1.py](../../../evaluation/substrate_capability/analyze_structural_composer_family_scaling_v1_1.py)
- Lock: [structural_composer_family_scaling_v1_1_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_family_scaling_v1_1_lock_20261002.json)
- Results: [structural_composer_family_scaling_v1_1_20261002.json](../../../evaluation/reports/structural_composer_family_scaling_v1_1_20261002.json)
