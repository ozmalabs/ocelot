# LLM taxonomy traversal scaling v1.1 results

## Result

Three fresh workers completed 9,640 queries each over the 6,445-concept, 5,772-edge harvested `isa` graph. The independent analyzer passes all gates. Every answer agrees with the registered six-hop operating envelope; against full graph closure, accuracy is 99.969% (9,637/9,640), positive recall is 99.938%, and negative specificity is 100%. The three misses are the only positive pairs at shortest-path distances 7 and 8, which exceed the traversal default of six hops. The shuffled-graph balanced accuracy is 50.47%, near chance.

Median graph build time is 97.72 ms, query-batch time for 9,640 pairs is 27.89 ms (345,671 queries/s), and worker peak RSS is 109.39 MiB. Per-query median latency follows path length: 2.30 μs at distance 2, 2.70 μs at distance 3, 3.40 μs at distance 4, 4.14 μs at distance 5, and 4.79 μs at distance 6. These are measurements of native graph construction and bounded traversal on one harvested graph, not a general scaling law.

## Interpretation and limits

This supports the substrate's ability to apply held relation structure efficiently on this workload. The graph has at most one outgoing `isa` edge per concept, so this is a sparse, nearly functional traversal case; it does not establish bounded treewidth or infer that useful frames can be discovered automatically. The oracle is the graph's own transitive closure, not external taxonomy truth. A separate harvest audit reports only 27.2% valid-ancestor yield, so answer correctness relative to the stored graph should not be read as semantic correctness. No downstream task utility or end-to-end learning cost was measured.

The next locality gate should use connected task-derived factor graphs with independently established outcomes, compare monolithic execution against automatically proposed and controlled partitions, and charge partition discovery and verification. Retain graph size, degree, separator size, width, domain cardinality, utility, and full runtime/memory costs so the cheap-cut hypothesis can be evaluated rather than assumed.

## Reproducibility artifacts

- Protocol: [v1 preregistration](LLM_TAXONOMY_TRAVERSAL_SCALING_V1_PREREG_20261002.md) and [v1.1 amendment](LLM_TAXONOMY_TRAVERSAL_SCALING_V1_1_AMENDMENT_20261002.md)
- Runner: [source-locked experiment](../../../evaluation/substrate_capability/llm_taxonomy_traversal_scaling_v1.py)
- Lock: [v1.1 source lock](../../../evaluation/substrate_capability/llm_taxonomy_traversal_scaling_v1_1_lock_20261002.json)
- Capture: [three-worker raw data](../../../evaluation/reports/llm_taxonomy_traversal_scaling_v1_1_20261002.json)
- Analysis: [independent analysis](../../../evaluation/reports/llm_taxonomy_traversal_scaling_v1_1_analysis_20261002.json)
