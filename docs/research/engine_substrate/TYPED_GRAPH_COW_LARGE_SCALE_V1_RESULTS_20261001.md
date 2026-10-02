# TypedGraph CoW large-scale extension v1 — results

**Result:** 6/6 size/topology cells pass query parity and sibling-isolation checks; all six have five measured repeats and match the pre-run source/binary lock.

The probe extends the shared-slab clone path to 100k and 200k nodes without rebuilding the locked release binary. Each cell compares eager clone with shared node/edge slab clone; mutation timings include clone plus the stated attribute writes.

| Nodes | Topology | Edges | Clone eager/shared (ms) | Clone ratio | One write eager/shared (ms) | 1% writes eager/shared (ms) |
|---:|---|---:|---:|---:|---:|---:|
| 100,000 | path | 99,999 | 29.92 / 19.60 | 1.53× | 27.40 / 21.71 | 28.27 / 19.75 |
| 100,000 | star | 99,999 | 25.89 / 16.67 | 1.55× | 22.91 / 13.15 | 25.12 / 17.04 |
| 100,000 | grid | 199,367 | 37.24 / 21.65 | 1.72× | 35.58 / 19.75 | 30.34 / 19.42 |
| 200,000 | path | 199,999 | 60.94 / 38.57 | 1.58× | 65.30 / 40.66 | 64.29 / 48.19 |
| 200,000 | star | 199,999 | 48.61 / 28.98 | 1.68× | 51.03 / 34.66 | 51.62 / 36.88 |
| 200,000 | grid | 399,105 | 69.09 / 34.97 | 1.98× | 63.70 / 35.65 | 69.56 / 43.60 |

Shared-slab clone is faster in all six cells, by 1.53–1.98×. Clone-plus-one-write is faster by 1.26–1.80×, and clone-plus-spaced-1%-writes by 1.33–1.59×. Eager and shared clone medians rise by roughly 1.5–2.0× from 100k to 200k depending on topology; this finite two-point observation is descriptive, not a complexity estimate. At 200k, shared clone-plus-1%-writes still costs 36.9–48.2 ms, so page sharing does not make mutation free.

This is TypedGraph-only evidence for one node type and empty node/edge attribute maps. The probe reuses its locked release binary, does not include the full Substrate indexes or rule closure, and does not measure RSS/PSS or process-wide memory. Historical 50,771-node measurements are not pooled because their Rust source hashes differ from this run.

## Artifacts

- [Preregistration](TYPED_GRAPH_COW_LARGE_SCALE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/typed_graph_cow_large_scale_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/typed_graph_cow_probe_v2.py)
- [Raw capture](../../../evaluation/reports/typed_graph_cow_large_scale_v1_raw_20261001.json)
