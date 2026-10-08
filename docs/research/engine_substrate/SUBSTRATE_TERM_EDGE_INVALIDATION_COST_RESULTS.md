# Term-edge invalidation cost pilot

**Status:** exploratory, 50 isolated workers; descriptive cost curve, not a scheduler-overhead estimate or complexity result.

## Workload

Each worker builds `n` stable `anchor` edges and `n` `seed` edges from one source. A reader rule matches all anchors and writes `Count(Edges(source, key))` to each anchor target. A writer rule matches the seeds and adds `n` `changed` edges.

- **Control:** the reader counts an untouched edge type. The writer's changes do not invalidate the reader.
- **Treatment:** the reader counts the `changed` edge type. The write dirties the reader and requires a rematch so every existing anchor output reaches the final count `n`.

Both conditions have identical graph size, match counts, and writer effects. Setup is outside the timed interval; each measurement runs in a fresh worker process. Five workers were run per condition at `n = 4, 8, 16, 32, 64`. Every worker's output was compared with the expected value and final edge count. Raw records, per-worker source and extension hashes, CPU/wall time, and RSS are in [`substrate_term_edge_invalidation_cost_20260924.json`](../../../evaluation/reports/substrate_term_edge_invalidation_cost_20260924.json). The harness is [`substrate_term_edge_invalidation_cost.py`](../../../scripts/substrate_term_edge_invalidation_cost.py).

## Results

| Bindings per rule | Control median wall | Treatment median wall | Wall ratio | CPU ratio | Control progress | Treatment progress |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 68.6 µs | 80.2 µs | 1.17× | 1.17× | 2 | 3 |
| 8 | 67.0 µs | 77.3 µs | 1.15× | 1.15× | 2 | 3 |
| 16 | 78.5 µs | 104.5 µs | 1.33× | 1.36× | 2 | 3 |
| 32 | 83.4 µs | 166.7 µs | 2.00× | 2.04× | 2 | 3 |
| 64 | 103.2 µs | 438.8 µs | 4.25× | 4.32× | 2 | 3 |

All 50 workers settled correctly. The added treatment pass accounts for one extra progressing rule step; the widening time gap reflects recomputing the edge count for every anchor against the final edge set. Wall and CPU ratios track closely in this small run. The computation is intentionally fan-out-heavy and can dominate the cost. These numbers therefore measure a concrete workload's cost of maintaining term-derived outputs, not the cursor-clear branch in isolation.

## Limits and next gate

Five repetitions are descriptive and provide no confidence interval. The graph sizes are small, use one source and one edge type, and do not include frame decomposition, concurrent execution, deletions, or host orchestration. Next compare cached/shared aggregation or incremental term maintenance against this baseline only if such a mechanism is within the substrate's intended model; retain exact semantic checks and report its memory/setup costs. Also measure ordinary closure rules with no term-edge reads to bound the unaffected fast path. No general tractability or commodity-scale claim follows.
