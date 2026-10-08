# Typed frame-interaction census v1 preregistration (2026-10-03)

## Question

The prior task-graph census discarded direction, edge type, and shared frame
membership. This source-locked reanalysis tests whether actual typed graph
relations cross the annotated frame interfaces, and which relation types carry
those interactions. It is an interaction census, not a factor-scope audit:
rule matches and effect dependencies can involve more than the recorded graph
edge endpoints.

## Inputs and classification

Use the same 78 snapshots from Bigville dynamic-link (63), connected
conversation (12), and discourse connected-task (3), with source identities and
node/frame annotations from the upstream captures. Preserve every raw edge's
source, target, relation type, and attributes. Bigville node membership comes
from `runtime_node_frame`; conversation and discourse use `frame_owner`,
expanded by `boundary_nodes_by_frames` so shared nodes carry all annotated
frames.

Classify each edge occurrence deterministically:

- `unassigned_endpoint`: either endpoint has no frame membership;
- `common_frame`: both endpoints are members of at least one same frame;
- `disjoint_frames`: both are annotated but have no frame in common.

Independently flag edges touching any node assigned to multiple frames. Report
all counts by task family and relation type. Do not collapse edge direction,
parallel typed edges, or repeated graph snapshots. The labels are held-out
annotations; the profile computation must not use them to alter graph structure.

## Gates and claim scope

1. Bind all raw captures, upstream locks, source extraction code, protocol,
   runner, and analyzer in a fresh source lock.
2. Reconstruct all 78 graph identities and edge occurrences with stable graph
   digests; independently recalculate every classification and per-type count.
3. Report family-level and per-relation profiles, including unassigned and
   shared-boundary incidences; retain every graph in the output.

Pass means only that the typed interaction profile was measured reproducibly.
A concentrated set of disjoint-frame relation types may guide factor-scope
review; it does not prove those edges are complete factor scopes or that
partitioned execution is semantically equivalent. Inputs remain three selected
task families with runtime-generated frame labels. Next step is rule-match and
effect-access scope attribution, then semantic-parity trials with shared and
high-coupling controls.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_typed_frame_interaction_census_v1.py`
- Lock: `evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1_lock_20261003.json`
- Capture: `evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_typed_frame_interaction_census_v1_analysis_20261003.json`
