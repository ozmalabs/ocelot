# Articulation-based frame-discovery baseline v1 results (2026-10-03)

## Outcome

The retrospective source-locked panel covers 78 graph snapshots and 16 unique
topologies across three source families. The independent analyzer reproduces
all articulation sets, cut components, and owner-based scores with zero errors.
The proposal uses topology only; owner annotations are accessed only after
partitioning for scoring.

| Family | Graphs | Labeled-node coverage (median; range) | Component purity (median; range) | Pairwise precision / recall / F1 (median) | Cross-owner edges incident to cut (median) | Same-owner edges incident to cut (median) |
|---|---:|---:|---:|---:|---:|---:|
| Bigville dynamic-link | 63 | 0.802 (0.800–1.000) | 1.000 (1.000–1.000) | 1.000 / 0.508 / 0.674 | 1.000 | 0.396 |
| Connected conversation | 12 | 1.000 (1.000–1.000) | 0.333 (0.125–0.500) | 0.257 / 1.000 / 0.406 | 0.000 | 0.000 |
| Discourse connected task | 3 | 1.000 (1.000–1.000) | 0.500 (0.500–0.500) | 0.379 / 1.000 / 0.549 | 0.000 | 0.000 |

On Bigville, articulation removal yields pure components and cuts all annotated
cross-owner edges, but often splits same-owner nodes across components: median
pairwise recall is 0.508, and 39.6% of same-owner annotated edges touch a cut
vertex. Coverage is 0.8–1.0 because labeled articulation nodes are treated as
boundaries rather than assigned to one frame.

On the connected conversation and discourse families, deleting all articulation
vertices leaves the annotated owners in one scored component. Pairwise recall
is 1.0 because no same-owner pairs are split, but pairwise precision is low
(0.257 and 0.379) because different owners are joined. None of the annotated
cross-owner edges touches a removed articulation node. Thus articulation
points are a useful separator signal in one selected family, but fail to
recover the annotated task owners in the other two.

## Interpretation and limits

This is a topology-only baseline reanalysis, not a substrate-native learning
result. The graph inputs are simple undirected projections; direction, relation
types, edge attributes, and factor scopes are discarded. The frame-owner labels
are existing runtime/task annotations, not independent semantic adjudications.
The three families are selected captures and do not estimate natural-task
prevalence. The result rejects articulation removal as a sufficient universal
frame-discovery method on these captures. It does not reject other separator,
community, typed-hypergraph, or learned-boundary methods.

The next gate should use typed interaction/factor scopes and include nested,
shared-interface, and high-coupling controls. Any proposed partition must be
scored on held-out owner labels, then checked by exact semantic parity against
monolithic inference or closure. Discovery, dependency coverage, updates,
message exchange, and fallback costs must be included before calling the
partition operationally tractable.

## Artifacts

- [Preregistration](SUBSTRATE_ARTICULATION_FRAME_DISCOVERY_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_articulation_frame_discovery_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_articulation_frame_discovery_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_articulation_frame_discovery_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/substrate_articulation_frame_discovery_v1_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_articulation_frame_discovery_v1_analysis_20261003.json)

Reproduce from the repository root:

```sh
python3 evaluation/substrate_capability/substrate_articulation_frame_discovery_v1.py --run
python3 evaluation/substrate_capability/analyze_substrate_articulation_frame_discovery_v1.py
```
