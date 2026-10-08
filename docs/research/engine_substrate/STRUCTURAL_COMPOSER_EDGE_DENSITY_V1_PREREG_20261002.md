# Structural composer edge-density scaling v1 preregistration

This panel measures whether full prompted structural composition depends on unrelated edge density at a fixed graph size. It crosses recurrence, repeated reply, actor-recipient relation-only, and actor-recipient actor+verb proposals with 100,000 unrelated nodes and 0, 1, or 4 directed unrelated edges per node. Each worker runs two same-family untimed composer warmups, constructs fresh graph noise, records node and edge insertion time and RSS, then measures one composer call and its RSS delta. Three fresh-process replicates are captured per cell in deterministic shuffled order (seed 61007).

Noise edges connect cyclically offset nodes and use distinct edge types by offset. They are inserted through `add_edge_unchecked`, matching the native seed/reflection path while avoiding grammar-check cost. Expected target/operator/site and primary-rule isolation are inherited from earlier locked transfer experiments. The measurement tests one synthetic sparse graph family; it does not isolate clustering, high-degree hubs, typed production density, or inference cost. Current RSS is sampled from `/proc/self/statm` and is page-granular.

- Runner: [measure_structural_composer_edge_density_v1.py](../../../evaluation/substrate_capability/measure_structural_composer_edge_density_v1.py)
- Analyzer: [analyze_structural_composer_edge_density_v1.py](../../../evaluation/substrate_capability/analyze_structural_composer_edge_density_v1.py)
- Lock: [structural_composer_edge_density_v1_lock_20261002.json](../../../evaluation/substrate_capability/structural_composer_edge_density_v1_lock_20261002.json)
- Results: [structural_composer_edge_density_v1_20261002.json](../../../evaluation/reports/structural_composer_edge_density_v1_20261002.json)
