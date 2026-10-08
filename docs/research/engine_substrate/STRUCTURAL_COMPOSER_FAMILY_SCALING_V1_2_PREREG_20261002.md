# Structural composer family and graph scaling v1.2 preregistration

V1.2 extends the four-family full-composer panel from 10,000 to 100,000 unrelated graph nodes. The earlier v1.1 panel is retained unchanged as the comparison through 10,000. The design uses the same four prompted proposal families, three fresh-process replicates per family/size cell, deterministic shuffled order (seed 61004), two family-specific warmups per worker, and three RSS checkpoints (before unrelated-node insertion, after insertion, after composition). The size grid is 0, 1,000, 10,000, and 100,000.

Expected target/operator/site choices and primary-rule isolation are unchanged from v1.1. RSS is a `/proc/self/statm` process snapshot, quantized to resident pages; it is suitable for coarse changes, not object-level accounting. The 100,000-node point tests a one-order-of-magnitude extension and is not a proxy for million-node or production-scale behavior.

- Runner: [measure_structural_composer_family_scaling_v1_2.py](../../../evaluation/substrate_capability/measure_structural_composer_family_scaling_v1_2.py)
- Analyzer: [analyze_structural_composer_family_scaling_v1_2.py](../../../evaluation/substrate_capability/analyze_structural_composer_family_scaling_v1_2.py)
- Lock: [structural_composer_family_scaling_v1_2_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_family_scaling_v1_2_lock_20261002.json)
- Results: [structural_composer_family_scaling_v1_2_20261002.json](../../../evaluation/reports/structural_composer_family_scaling_v1_2_20261002.json)
