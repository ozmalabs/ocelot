# Bigville controlled cross-boundary exact MAP results

## Result

The preregistered 24-case replay passed all nine independent analysis gates across three fresh workers, N=10/25 authored Bigville resident CANs, and explicit boundary dimensions k=0/2/4/6. BFS over the extracted graph found interior components without using resident labels. Every interior pairwise factor remained within one component or touched the declared boundary. Conditional exhaustive MAP matched global min-fill/junction-tree MAP in whole-model energy in all cases, with complete domain-valid states and independently reconstructed enumeration counts.

At N=25, the conditional solver examined 6,075 local assignments at k=0 and 3,582,306 at k=6. Median conditional discovery+MAP time rose from 10.35 ms to 6.02 s; global width+MAP stayed around 7–9 ms, with reported width 2 throughout. At N=10, k=6 required 925,101 local assignments and a 1.50 s median. This confirms exact conditional factorization for these controlled bounded-size interiors while showing the exponential boundary cost directly. It does not show a speed advantage over the global solver in this low-width model.

## Interpretation and limits

The experiment establishes a correctness and cost envelope for explicit boundaries in the Python exact-inference path. It also exposes a practical implementation issue: the straightforward conditional oracle repeatedly solves each interior assignment for every boundary assignment, so its work scales as `d^k Σ_C d^|C|`; this is the preregistered direct algorithm, not optimized message reuse. Width-2 global junction-tree inference is much cheaper here. The result therefore supports the bounded-separator proposition but does not establish that native partitioned inference is useful or faster.

Added cross-resident factors are controlled perturbations to deterministic authored simulation models. The run does not measure natural boundary prevalence, automatic boundary discovery quality beyond this simple graph BFS, native frame messages/scheduling, larger boundary widths, or end-to-end substrate cost. Phase C remains open.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_BIGVILLE_CROSS_BOUNDARY_MAP_PREREG_20260926.md)
- Runner: [`substrate_bigville_cross_boundary_map_v1.py`](../../../scripts/substrate_bigville_cross_boundary_map_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_cross_boundary_map_v1.py`](../../../scripts/analyze_substrate_bigville_cross_boundary_map_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/bigville_cross_boundary_map_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_bigville_cross_boundary_map_v1_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_bigville_cross_boundary_map_v1_analysis_20260926.json)
