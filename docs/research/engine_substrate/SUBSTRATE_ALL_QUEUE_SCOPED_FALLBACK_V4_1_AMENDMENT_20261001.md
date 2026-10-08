# Direct matcher-order consumer v4.1 protocol correction

Date: 2026-10-01

## Correction

The preregistered v4 analysis required `selected_mid` to equal the last `handled_mid` edge in the graph dictionary. Source review after capture shows this is the wrong oracle for matcher order:

- `TypedGraph::edges_by_type()` returns the per-type `Vec<EdgeIdx>` used by the matcher's both-unbound scan.
- `TypedGraph::iter_edges()` enumerates live slots in the edge slab; `persist::graph_to_value()` serializes edges through this iterator.
- Edge deletion retains the per-type index order, while freed slab slots can be reused by later insertions.

Thus graph serialization order is not the index order being queried by the matcher. The v4 primary behavioral comparison remains valid: the one-shot matcher continuation's final selected NodeID matches across full and scoped-plus-fallback execution in all 27 workers. The failed selected-versus-slab-tail checks are disclosed as a bad diagnostic oracle, not recast as a substrate behavior failure.

## Captured result retained

The v4 protocol, raw capture, and strict analysis remain immutable. The strict analyzer records 330/354 checks because 18 exact wire-order gates fail and six direct-full selected values differ from the final serialized slab-order edge. Post-hoc analysis finds equal matcher selections in all 27 workers, equal canonical graph facts in all 27, and exact wire equality in 9/27. The correction and source evidence are recorded in the [v4 result](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V4_RESULTS_20261001.md).

No rerun is needed for this correction: it changes interpretation of an existing capture, not fixture execution. A future confirmatory protocol should expose or measure the actual matcher-index ordering instead of using `graph_to_dict()` edge order as a proxy.
