# Treewidth analysis cost envelope — 2026-09-25

## Question and method

How does the current reusable treewidth implementation's own analysis cost grow with graph size and topology, before any exact inference is attempted?

[`scripts/graph_treewidth_cost_envelope.py`](../../../scripts/graph_treewidth_cost_envelope.py) measured `domains.graph_treewidth.exact_treewidth` three times per graph for four deterministic families at n=8/9/10, and `min_fill_upper_bound` five times per graph for paths, width-2 bands, sparse-random graphs through n=512, and complete graphs through n=80. Random edges use `p=min(1,3/(n-1))` and seed `1701+n`. Each returned elimination order was independently replayed by a separate local validator; the induced width had to match the reported value. The exact search is factorial with pruning and refuses above n=10 by default; min-fill is heuristic and always returns an upper bound.

The raw report contains all 131 timings, graph sizes, widths, environment and source hashes: [`evaluation/reports/graph_treewidth_cost_envelope_20260925.json`](../../../evaluation/reports/graph_treewidth_cost_envelope_20260925.json).

## Results

All 36 exact orders and 95 min-fill orders reconciled to the independently replayed width. Width was stable across repeats. Exact-search median wall time:

| Family | n=8 | n=9 | n=10 | Exact width at n=10 |
|---|---:|---:|---:|---:|
| Path | 34.3 ms | 341 ms | 3.60 s | 1 |
| Banded-2 | 34.7 ms | 352 ms | 3.69 s | 2 |
| Complete | 46.9 ms | 462 ms | 4.90 s | 9 |
| Sparse random | 44.8 ms | 360 ms | 3.85 s | 2 |

The n=8→9 and n=9→10 exact-search cost grows by about an order of magnitude even on path inputs where the true width remains 1. The measured n=10 complete control was the slowest at 5.04 s maximum over three repeats. These timings support keeping the current n=10 exact cap conservative for synchronous callers; they do not establish worst-case runtime beyond the measured points.

Min-fill median wall time and returned width:

| Family | n : width / median time |
|---|---|
| Path | 32: 1 / 0.32 ms; 64: 1 / 1.21 ms; 128: 1 / 4.63 ms; 256: 1 / 18.6 ms; 512: 1 / 72.9 ms |
| Banded-2 | 32: 2 / 0.52 ms; 64: 2 / 2.04 ms; 128: 2 / 7.92 ms; 256: 2 / 31.3 ms; 512: 2 / 132 ms |
| Sparse random | 32: 6 / 0.69 ms; 64: 9 / 2.79 ms; 128: 19 / 17.2 ms; 256: 30 / 62.6 ms; 512: 65 / 572 ms |
| Complete | 32: 31 / 6.52 ms; 48: 47 / 30.2 ms; 64: 63 / 89.7 ms; 80: 79 / 210 ms |

For a fixed family and stable width (path/banded), doubling n costs about 4×, consistent with this implementation repeatedly scanning candidate vertices and neighbor pairs. Sparse-random analysis grows faster as both n and the produced width rise. The complete family reaches width n−1 and costs 210 ms at n=80. Width is a key input to later exponential inference cost, while width computation itself has a distinct, measurable cost.

## Claim boundary and next gate

This is a synthetic algorithm microbenchmark for the current Python source. It does not measure junction-tree message passing, belief-propagation quality, substrate graph extraction, allocations, or real workload topology. Exact widths are produced by the algorithm's permutation search; this run independently validates the returned orders' widths, not the minimum over all possible orders with a second exact implementation. No treewidth result here establishes cheap cuts or frame-semantic validity.

Next, pair width-analysis cost with exact inference cost and output quality on identical fixed CAN graphs: compare exhaustive ground truth, junction-tree exact results/refusals, and explicitly labelled approximate or heuristic solvers. Include decomposition/extraction cost and memory, and retain high-width controls. Audit all results against the current source/build before making claims about the substrate's inference envelope.
