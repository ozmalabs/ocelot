# Graph-resident edge identity site materialization scaling v1

This locked measurement isolates graph-site materialization. Each cell starts from a fresh Rust substrate created by `boot_core(seeds=())`, inserts a controlled number of unrelated nodes, then times `_ensure_edge_identity_sites` for a synthetic rule whose fresh node has direct bound `Attr` values. The timed interval includes extraction, existing-site lookup, and insertion of typed `EditSite` nodes. Substrate boot and unrelated-node construction are outside the timed interval.

The preregistered grid crosses unrelated graph sizes 0, 1,000, and 10,000 with target attribute widths 8, 32, and 64. Each cell has one warmup and five fresh-substrate trials. The expected site total is one relation-only site plus all singletons and pairs, with one full signature when width exceeds two. The lock captures relevant Python/native source hashes and host/runtime metadata. This is a one-host synthetic scaling diagnostic; it does not measure complete proposal composition, native selection, concurrent frames, or task quality.

- Runner: [measure_graph_site_materialization_scaling_v1.py](../../../evaluation/substrate_capability/measure_graph_site_materialization_scaling_v1.py)
- Analyzer: [analyze_graph_site_materialization_scaling_v1.py](../../../evaluation/substrate_capability/analyze_graph_site_materialization_scaling_v1.py)
- Lock: [graph_site_materialization_scaling_v1_lock_20261002.json](../../../evaluation/substrate_capability/graph_site_materialization_scaling_v1_lock_20261002.json)
- Results: [graph_site_materialization_scaling_v1_20261002.json](../../../evaluation/reports/graph_site_materialization_scaling_v1_20261002.json)
