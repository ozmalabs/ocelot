# Structural composer million-node scaling v1.3 preregistration

This checkpoint extends the four-family prompted composer benchmark to one million unrelated graph nodes. It reuses the v1.2 fresh-process harness, two same-family warmups, three replicates per family, locked expected target/operator/site, primary-rule isolation check, and RSS snapshots around graph insertion and composition. Each family is measured at 1,000,000 unrelated nodes; this is an extension point, not a full curve.

The capture is split into one-million-node workers so each process releases its graph before the next replicate. Three replicates per family are preregistered. The prior 0–100,000-node v1.2 curve remains the low/mid-scale reference. RSS remains page-level and not exact graph-object accounting. A successful result supports only these four prompted composer paths at this node count.

- Runner: [measure_structural_composer_family_scaling_v1_3.py](../../../evaluation/substrate_capability/measure_structural_composer_family_scaling_v1_3.py)
- Analyzer: [analyze_structural_composer_family_scaling_v1_3.py](../../../evaluation/substrate_capability/analyze_structural_composer_family_scaling_v1_3.py)
- Lock: [structural_composer_family_scaling_v1_3_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_family_scaling_v1_3_lock_20261002.json)
- Results: [structural_composer_family_scaling_v1_3_20261002.json](../../../evaluation/reports/structural_composer_family_scaling_v1_3_20261002.json)
