# Edge-matched width-q topology comparison v1 preregistration (2026-09-29)

## Question

Does min-fill's width overestimate on rectangular grids persist when compared with an irregular graph of exactly the same node count, edge count, and known treewidth?

## Paired graph construction

For q∈{4,5,6}, use N=120 and 12 deterministic ID/edge-order relabellings. One graph is the q×(120/q) rectangular grid. Its paired `sparse_partial_qtree` begins with a retained (q+1)-clique, then adds every remaining vertex with at least one edge to a q-clique in a seeded random q-tree completion. Randomly distribute the remaining attachment edges, subject to 1≤degree≤q, until the edge count exactly equals the paired grid. The partial graph is connected, has a width-q elimination certificate inherited from the completion, and has a clique lower bound q; hence its exact treewidth is q. The grid has known treewidth q.

## Measurements and gates

Record min-fill width, production `treewidth_bound_check` outcome at bound q, ordering time, bag-size histogram, degree summary, and a maximum-cardinality-search chordality diagnostic. Require exact paired node/edge counts; width-q certificate for both graphs; the partial q-tree's retained clique lower bound; min-fill width no lower than q; gate outcome agrees with its upper bound; and source lock match. The chordality diagnostic is descriptive and is not used as a correctness gate.

## Claim boundary

This paired synthetic family isolates node/edge count and certified treewidth but does not match degree sequence or all separator profiles. Results do not estimate natural graph frequencies or learned-frame quality.

```sh
python3 evaluation/substrate_capability/can_edge_matched_width_topology_v1.py --lock
python3 evaluation/substrate_capability/can_edge_matched_width_topology_v1.py
python3 evaluation/substrate_capability/analyze_can_edge_matched_width_topology_v1.py
```

