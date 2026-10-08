# Bounded-width exact inference scale check

**Run date:** 2026-09-25  
**Runner:** [can_bounded_width_scale.py](../../../scripts/can_bounded_width_scale.py)  
**Preregistration:** [CAN_BOUNDED_WIDTH_SCALE_PREREG_20260925.md](CAN_BOUNDED_WIDTH_SCALE_PREREG_20260925.md)  
**Pre-run lock:** [can_bounded_width_scale_lock_20260925.json](../../../evaluation/substrate_capability/can_bounded_width_scale_lock_20260925.json)  
**Raw report:** [can_bounded_width_scale_20260925.json](../../../evaluation/reports/can_bounded_width_scale_20260925.json)

## Method and result

Twenty-one fresh worker processes measured exact binary MAP on path graphs of 32–2,048 concepts, three seeds at each size. Each graph was constructed in a native substrate, extracted through can_network_from_mt, then ordered by current min-fill and solved by junction_tree_map. An independent two-state dynamic program and an independent energy rescore supplied the exact oracle.

All 21 extracted factor models matched the generated inputs; all had min-fill upper bound 1 and maximum bag size 2; and all junction-tree energies matched the independent oracle. There were no timeouts or correctness failures.

| Nodes | Edges | Median extraction | Median min-fill | Median junction-tree MAP | Traced MAP peak | Max worker RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 31 | 0.50 ms | 0.48 ms | 2.49 ms | 37 KiB | 25.1 MiB |
| 64 | 63 | 0.88 ms | 1.27 ms | 4.98 ms | 68 KiB | 25.1 MiB |
| 128 | 127 | 1.80 ms | 4.55 ms | 11.51 ms | 136 KiB | 25.3 MiB |
| 256 | 255 | 3.36 ms | 17.60 ms | 20.30 ms | 273 KiB | 26.3 MiB |
| 512 | 511 | 6.38 ms | 72.46 ms | 41.82 ms | 561 KiB | 27.2 MiB |
| 1,024 | 1,023 | 14.45 ms | 288.22 ms | 84.31 ms | 1.11 MiB | 30.0 MiB |
| 2,048 | 2,047 | 26.82 ms | 1,170.02 ms | 173.40 ms | 2.29 MiB | 34.9 MiB |

The exact message-passing time approximately doubles as node count doubles, consistent with the expected linear cost for this width-one family. The current min-fill ordering does not: it grows about 2,460× from 32 to 2,048 nodes (64× the input size), and takes 6.7× the MAP time at the largest point. Thus the bounded-width inference algorithm itself scales well on this path, while ordering is already the measured bottleneck at 2,048 variables. Extraction remains cheaper than either at the largest point.

## Scope and next measurement

This is a synthetic two-state path family. It supports a measured exactness and cost envelope for one runtime-extracted width-one graph shape; it does not establish natural-task prevalence, automatic frame discovery, marginal inference, higher-width costs, concurrent throughput, or native allocation totals. Worker RSS includes the interpreter/import floor; Python traced peak covers only allocations during MAP.

Next measure an ordering strategy specialized for forests or bounded-width graphs against min-fill, with exactly the same graph/order validity checks and MAP oracle. Then extend to width-two ladders and a fixed-boundary modular family, where cost should scale linearly in frame count and exponentially in the declared width. Preserve the current min-fill result as baseline; do not claim a general linear inference envelope from paths alone.

The first unscored worker failed because the benchmark adapter supplied tuple factor keys where the solver expects frozenset; this harness-only issue and the pre-scored-run lock amendment are documented in the preregistration. It did not contribute a scored data point.
