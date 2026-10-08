# Varied-topology transport solver v1.3 amendment

Date: 2026-10-03

The v1.2 full-grid capture completed, but exactness failed. Independent analysis found 237/960 conditioned states whose direct energy disagrees with the reported conditioned energy; the failures occur on repeated topologies, especially the dense fan-in-8 graph. The component-preparation cache accidentally retained per-case factor weights along with topology and reused those weights for later held-out rows. The minimum-separator proposals, topology joins, monolithic baseline, source stability, state domain, and mutation checks passed. V1.2 timing ratios are invalid for solver comparison and are retained only as diagnostic evidence.

V1.3 keeps the same workload and local exact component solvers. The topology cache now holds only graph-derived separator/component structure and elimination orders. Each case binds its current unary and pairwise factor values to that cached structure; this per-case binding cost is measured and charged. The independent analyzer continues to rescore both returned states from captured anonymous factors and checks signs from captured node IDs. A fresh three-worker source-locked run is required; v1.2 results cannot serve as confirmatory observations.
