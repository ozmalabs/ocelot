# Edge-only deletion where-reader cursor invalidation v1 results

**Evidence grade:** nine fresh source-locked workers; all 9 runner gates and 7 independent analysis checks pass across N=8/32/128, three workers per size.

The rule matches stable `Root -slot-> Slot` edges and reads `Root -block-> *` only in its where condition. Removing the block edge through public `remove_edge` leaves node state unchanged, avoiding `remove_node`'s generic where-rule cursor clearing. Full rescan and sound incremental matching reopen all N slots and produce byte-identical graph snapshots. The unsound falsifier reopens zero slots at every size, proving the type-local where-reader cursor clear is necessary for this edge-only mutation path.

Sound incremental candidate counts equal N (8/32/128), with one reader enumeration. This is a linear full rematch for the where-flip shape, not an incremental candidate-work reduction. The unsound arm has zero candidate pairs because the stale cursor suppresses the stable match bindings. Median N=128 settle time is 86.4 μs full-rescan, 69.7 μs sound incremental, and 8.3 μs unsound; the latter is incorrect and all timings are fixture-specific.

This validates one `Count(Edges)` where-reader and public edge deletion. It does not prove all where-Term families, multiple dependent rules, or concurrent mutation semantics.

Artifacts: [preregistration](SUBSTRATE_DELETE_EDGE_WHERE_CURSOR_INVALIDATION_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_delete_edge_where_cursor_invalidation_v1.py), [raw capture](../../../evaluation/reports/substrate_delete_edge_where_cursor_invalidation_v1_20260928.json), [analysis](../../../evaluation/reports/substrate_delete_edge_where_cursor_invalidation_v1_analysis_20260928.json), and [source lock](../../../evaluation/substrate_capability/delete_edge_where_cursor_invalidation_v1_lock_20260928.json). The companion [node-deletion panel](SUBSTRATE_DELETE_WHERE_CURSOR_INVALIDATION_V1_1_RESULTS_20260928.md) documents why that route did not isolate this invalidator.
