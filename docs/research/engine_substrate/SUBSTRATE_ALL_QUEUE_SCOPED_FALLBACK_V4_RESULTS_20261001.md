# Direct matcher-order consumer v4 results

Date: 2026-10-01

## Outcome

The source/native-locked 27-worker factorial yields the same last-match `selected_mid` under direct full and scoped-plus-fallback closure in all 27 workers. Every selected value follows the actual rule-matcher consumption result. This does not follow from comparing with the final item in `graph_to_dict()`'s edge array: that persistence order is the edge slab order, not the matcher index order.

The preregistered strict analyzer reports 330/354 checks. Eighteen exact graph-wire parity checks fail, consistent with v2/v3: node arrays and canonical edge-fact multisets match in 27/27, but graph edge-vector ordering matches in 9/27. Six additional diagnostic checks fail because direct-full `selected_mid` does not equal the last `handled_mid` edge in the persisted slab order. The scoped-plus-fallback selection does match that slab tail in 27/27; nevertheless, full and fallback matcher-selected NodeIDs agree in 27/27. The discrepancy identifies a protocol mistake: the edge vector used by `graph_to_dict()` was treated as though it exposed `edges_by_type` enumeration order. These are distinct orderings.

All queue-family counts, handled/verified edges, fixed-point reports, and order-sensitive selections pass their independent checks. No checker or runner sorts edges. The result shows no observable difference for this direct matcher continuation despite graph serialization order differences. It does not establish equivalence for arbitrary iteration APIs or consumers.

## Source ordering facts

The source audit confirms:

- `TypedGraph::insert_edge` appends edge indices to `edges_by_type` and adjacency vectors; deletion removes entries with stable `retain` operations.
- The both-unbound matcher branch enumerates `edges_by_type` directly.
- `TypedGraph::iter_edges`, used by `persist::graph_to_value` and Python `graph_to_dict`, enumerates the edge slab by slot index.
- Freelist reuse can therefore change serialized edge order without changing edge-type-index or per-node adjacency order.

The matcher-level selected node is the relevant behavioral observation here; the persisted final array cannot serve as its expected order oracle.

## Artifacts

- [Preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V4_PREREG_20261001.md)
- [Protocol correction amendment](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V4_1_AMENDMENT_20261001.md)
- [Runner](../../../scripts/substrate_all_queue_scoped_fallback_v4.py)
- [Strict analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v4.py) — retains the exact wire and mistaken slab-tail gates, hence the nonzero result.
- [Post-hoc state/order analysis](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v4_state_order.py)
- [Source/native lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v4_lock_20261001.json)
- [Raw workers](../../../evaluation/reports/all_queue_scoped_fallback_v4_workers_20261001.json)
- [Strict analysis](../../../evaluation/reports/all_queue_scoped_fallback_v4_analysis_20261001.json)
- [State/order analysis](../../../evaluation/reports/all_queue_scoped_fallback_v4_state_order_20261001.json)

All worker fingerprints are stable before and after execution. The preregistered wire-order failure remains disclosed rather than normalized away.

## Next gate

Use an API that explicitly returns `edges_by_type` or adjacency order if one is added for diagnostics, or infer it through additional matched bindings whose last-match outputs encode the sequence at several prefixes. Separately test scoped/full behavior where an earlier effect removes a later binding's unique match edge; the current shared trigger deletion invalidates a common edge but leaves each join path intact.
