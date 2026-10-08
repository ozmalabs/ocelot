# CAN matched-width topology envelope v1 preregistration (2026-09-29)

## Question

At matched node count and known treewidth q, how do topology and relabelling affect min-fill width, bag-size profile, and the production treewidth-bound decision?

## Graph families

For q∈{4,5,6}, create N=120 vertex graphs from four families: q×m rectangular grids (m=120/q, using exact divisibility); a sliding q-tree path; a q-tree whose new vertices all attach to one shared q-clique; and a random q-tree whose new vertices attach to seeded existing q-cliques. A q-tree starts with a (q+1)-clique and each later vertex attaches to an existing q-clique, so its known treewidth is q. Grid treewidth is q for the chosen dimensions. Cross each topology with 12 deterministic relabellings that randomize vertex IDs and edge order: 144 fresh graph cases.

## Measurements and gates

Use `min_fill_upper_bound` and the production `treewidth_bound_check` at bound q. Construct and independently replay a known width-q elimination certificate for every family. Record min-fill width, bag-size histogram, width overhead, production accept/refuse decision, and ordering time. Require exact graph/node/edge counts, valid certificates, min-fill decomposition bags consistent with its reported upper bound, 12 replicates per cell, no underestimation below q, and source-lock agreement. A refusal at bound q is classified as a conservative false refusal because the supplied certificate and family lower bound establish exact width q.

## Lock and limitations

Lock this protocol, runner, `graph_treewidth.py`, and the production caller `can_junction_tree.py`. This is a topology/heuristic envelope, not a natural-task distribution or a proof of learned frame locality. The four constructed families do not cover arbitrary graph classes. The grid-family exact width relies on the standard grid treewidth result; q-tree families have an explicit q+1 clique lower bound and width-q elimination certificate.

```sh
python3 evaluation/substrate_capability/can_matched_width_topology_envelope_v1.py --lock
python3 evaluation/substrate_capability/can_matched_width_topology_envelope_v1.py
python3 evaluation/substrate_capability/analyze_can_matched_width_topology_envelope_v1.py
```

The v1 capture exposed a generator error in the random q-tree family: it attached to q+1 vertices. The failed capture is retained, and the corrected q-subset construction plus fresh-run requirement are documented in the [v1.1 amendment](CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_1_AMENDMENT_20260929.md).
