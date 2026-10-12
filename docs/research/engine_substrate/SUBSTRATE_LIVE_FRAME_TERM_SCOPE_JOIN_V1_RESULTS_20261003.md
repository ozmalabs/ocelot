# Live frame Term-scope crosswalk v1 results

Date: 2026-10-03  
Source inventory: [current Term access crosswalk](../../../evaluation/reports/term_access_dependency_coverage_v1_1_20261003.json)  
Runtime definitions: [request-time rule-scope analysis](../../../evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json)  
Joined analysis: [runner](../../../scripts/analyze_live_frame_term_scope_join_v1.py), [machine-readable result](../../../evaluation/reports/live_frame_term_scope_join_v1_20261003.json)

## Result

The current-source Term inventory passes all five checks. It covers all 237
Term variants, with evaluator arms and `children()` cases present for every
variant; hashes of `term.rs`, `rewrite.rs`, and `access_trace.rs` match the
current working tree. The runtime join passes all five of its checks and
maps the Term syntax from all 401 request-traced rule definitions to the
source inventory, covering 67 distinct Term variants and 15,417 syntactic
Term occurrences across those unique definitions. The corresponding live
trace has 1,650,456 weighted access events.

| Source access class | Live Term variants | Rule definitions containing one or more | Syntax occurrences |
|---|---:|---:|---:|
| finite resource keys | 2 | 395 | 3,748 |
| conditional finite key or wildcard | 2 | 124 | 259 |
| wildcard `reads_any` | 12 | 56 | 202 |
| generic child-walk fallback | 51 | 401 | 11,208 |

The class counts overlap at the rule level. The generic-fallback total is
dominated by ordinary expression and value constructors; it is not a count
of hidden graph reads. The generator detects no direct graph-reading Term or
qualified graph-reader helper left in its generic-fallback class, but its
lexical, depth-limited helper scan is not a sound call-graph proof. These 51
variants remain without individual source review.

## Structural implications

The source inventory classifies `Attr` and `NodesOfType` as finite resource
keys. For frame partitioning, these have different shapes: `Attr` names a
finite attribute resource, while a `NodesOfType` evaluation scans the graph's
population of the requested type. Ninety-three traced rule definitions
contain `NodesOfType` syntax. The runtime tracer currently records the types
of returned nodes but does not mark the query or scan population, so empty
queries and their graph-wide population dependency are not visible in the
live access rows. This is a global dependency candidate despite its finite
type key.

The conditional class comprises `Neighbours` and `InNeighbours`; its source
declaration is finite when the edge type is fixed and wildcard when the
operation traverses all edge types. The wildcard class contributes only 202
syntactic occurrences, but includes 11 reviewed dynamic-helper Term variants
among the 67 live variants, such as shape/depth/time inference and program
evaluation. These helpers may scan typed populations, decode graph-resident
structures, or select runtime-dependent data. Their source declaration is
therefore a better signal of broad dependency than the small count of
concrete trace rows.

No `UseTool`, `ReadFile`, or `ProgCallExtern` syntax appears in the 401
definitions that emitted access rows. This says nothing about host callbacks
that leave no trace row, untraced rule paths, or Python adapter work. The
exported edge matches, attribute keys, and effect kinds provide useful
candidate operation scopes, but they are not factor scopes or proofs of
complete read/write behavior.

## Next gate

Promote runtime-touched source rows into a reviewed operation-scope manifest:
resolve finite edge/attribute keys, enumerate `NodesOfType` populations,
record the any-edge branch of adjacency Terms, and mark each dynamic helper's
implicit graph scope. Add source/runtime checks for empty population queries
and rejected matcher candidates. Then use the manifest to propose partitions
without the protocol-owned task membership and compare partitioned closure
with the monolithic fixed point, including shared-state and cross-frame
mutations, discovery cost, interface traffic, and scheduler overhead. Do not
interpret this one prompt pair as an estimate of natural-task cheap-cut
prevalence.
