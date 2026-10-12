# Interacting-tree construction cost v1 results

**Evidence grade:** post-hoc analysis of the source-locked 36-worker interacting-tree closure panel. The additional 10-million-node star pilot was started with the existing worker and interrupted after more than nine minutes without a row; it contributes no timing, memory, or correctness result.

## Finding

The original panel recorded graph construction separately from closure. In the three uninstrumented replicates at N=1,000,000, median `add_edge_unchecked` construction took 456.86 s for the star and 1.674 s for the balanced tree. Closure took 1.678 s and 6.112 s respectively. At N=100,000, star edge construction took 2.799 s and balanced-tree construction 0.152 s. Thus, for a tenfold increase in N, measured star edge construction grew 163.2×, while balanced construction grew 11.0×. At one million nodes the star's measured edge-build time was 272.5× its closure time.

At the time of the original capture, `graph.rs` implemented `edge_idx` by scanning the `(source, edge type)` adjacency bucket, and `insert_edge` used it to detect duplicates. In the star fixture, every `child` edge shares one source/type bucket, so duplicate detection scans an increasingly large bucket on each insertion. The raw run lock preserves the original source hash; the current source has since changed. The later [v1.2 indexed replay](SUBSTRATE_INTERACTING_TREE_EDGE_INDEX_V1_2_RESULTS_20260928.md) supplies the causal intervention: edge construction falls 275.6× at 1M star while balanced construction remains unchanged. The balanced tree distributes outgoing `child` edges across source nodes and does not exhibit the original superlinear growth over the measured decade.

This changes the scale interpretation: closure can be inexpensive while preparing the graph is the dominant and topology-sensitive cost. A ten-million-node closure panel using this fixture builder is not currently a useful next measurement. The engine needs an indexed duplicate check for high-degree source/type buckets, or the harness needs a semantically equivalent bulk builder, before a meaningful high-fanout scale claim can be made. Any optimization must preserve duplicate-edge attribute replacement, deletion, and adjacency-query behavior.

## Reproduction and limits

This is a post-hoc phase decomposition, not a new runtime capture. Run `python3 scripts/analyze_substrate_interacting_tree_construction_cost_v1.py`; it checks the original raw capture against its source lock and the original independent analysis, then recomputes phase medians and ratios. The derived machine-readable record is [`substrate_interacting_tree_construction_cost_v1_analysis_20260928.json`](../../../evaluation/reports/substrate_interacting_tree_construction_cost_v1_analysis_20260928.json). The underlying panel's runner, lock, raw capture, and result are linked in [`the v1 closure results`](SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_RESULTS_20260928.md).

The interrupted 10M star attempt is disclosed only to explain why no larger point is claimed; it emitted no row and is not included in the analysis. The derived timing ratios describe one builder, one star/tree pair, and three workers per cell. They do not prove an asymptotic bound or establish a performance regression across all graph workloads.
