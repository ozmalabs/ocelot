# Typed frame-interaction census v1 results (2026-10-03)

## Outcome

The source-locked census covers 78 snapshots and independently validates every
edge occurrence, relation type, frame-membership classification, graph digest,
and aggregate count with zero errors. It preserves direction and parallel
relation types. The labels are source-captured owner/shared-boundary
annotations, not inferred by the census.

| Family | Graphs | Edge occurrences | Common-frame edges | Disjoint-frame edges | Unassigned-endpoint edges | Shared-boundary incident edges |
|---|---:|---:|---:|---:|---:|---:|
| Bigville dynamic-link | 63 | 108,558 | 63,000 | 7,758 | 37,800 | 0 |
| Connected conversation | 12 | 3,399 | 1,236 | 90 | 2,073 | 966 |
| Discourse connected task | 3 | 729 | 210 | 6 | 513 | 177 |

Every disjoint-frame edge in the two conversation families is `follows_event`
(90/90 conversation edges; 6/6 discourse edges). In Bigville, all 7,758
cross-owner edges are `causal_influence`; 63,000 more `causal_influence` edges
are common-frame. Conversation and discourse also show substantial typed
incidence through shared boundary nodes: `has_event`, `from_speaker`,
`to_addressee`, and `contributes_to_common_ground` are among the relations
that touch those shared nodes. These interface edges would be hidden by a
method that only removes articulation vertices: multi-frame nodes can connect
many task scopes without themselves being a one-vertex cut.

The high unassigned-endpoint counts are material: 37,800/108,558 Bigville,
2,073/3,399 conversation, and 513/729 discourse edge occurrences have at least
one endpoint without a frame membership annotation. This limits any claim
about the full interaction boundary and signals that annotation coverage must
be measured alongside sparsity.

## Interpretation and limits

Typed graph relations expose real cross-frame routes that the earlier
undirected profile could not name. The conversation relation `follows_event`
provides an explicit sequential dependency; shared boundary nodes mediate
additional common-frame incidences. This is a useful target list for rule-level
factor-scope audit. It is not that audit: rules can bind several graph edges,
read scalar attributes, or produce effects that are not represented by one
edge. The census cannot certify independent partitioned closure or exact
inference.

The captures are selected workloads, labels are source runtime annotations,
and the relation projection does not recover edge-generation semantics. Next
trace actual rule binding/effect dependencies against these typed interfaces,
then run monolithic-versus-partitioned semantic-parity cases with shared-node,
`follows_event`, and high-coupling controls. Include unassigned nodes in the
boundary risk analysis.

## Artifacts

- [Preregistration](SUBSTRATE_TYPED_FRAME_INTERACTION_CENSUS_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_typed_frame_interaction_census_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_typed_frame_interaction_census_v1_analysis_20261003.json)

Reproduce from the repository root:

```sh
python3 evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1.py --run
python3 evaluation/substrate_capability/analyze_substrate_typed_frame_interaction_census_v1.py
```
