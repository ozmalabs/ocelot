# Stable-order batch edge deletion v1 preregistration

**Question:** can deleting a known edge batch compact each affected adjacency vector once, preserving sequential deletion outcomes and stable iteration order while reducing high-degree deletion cost?

## Paired mutation workload

At N=5,000/20,000/80,000, run three fresh-process pairs per size. Each arm builds the same root, N attributed leaves, and one homogeneous `hub_child` edge per leaf. One arm calls `remove_edge` once per edge; the other calls the new `remove_edges_batch` once with the ordered triples. Alternate arm order across replicates. Time node construction, edge construction, deletion, and full post-delete graph readback separately. Compare with the existing source-locked sequential deletion capture.

## Semantic controls

On a separate small mixed-edge graph, compare sequential and batch outcome booleans for interleaved edge types, duplicate requests, and a missing edge. Capture `edge_deleted` hook events and require identical order/count. Require byte-equivalent canonical graph snapshots before and after deletion, exact edge/node counts, stable `out_edges_idx` and type-index iteration order, and no missing or stale target lookup. For the scale graph require every delete success, zero final edges, exact nodes, and equal sequential/batch post-delete digests.

## Implementation conditions and limits

The batch core collects unique live EdgeIdx values, deletes them, and stable-filters each affected vector once. Per-edge deletion generations increment once per removed edge; dirty marking and cursor invalidation coalesce by edge type. Compare wall time descriptively and verify all raw worker results independently. This measures one high-degree bucket and a new public batch API; it does not show that arbitrary callers can be transparently switched from individual mutations or measure concurrent execution.
