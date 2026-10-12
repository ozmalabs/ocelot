# Anaphora boundary analysis v1.3 correction

Date: 2026-09-29. This amendment changes analysis only; v1.2 raw captures and
their preregistration are immutable.

## Detected measurement error

V1.2's analyzer interprets every trace row with a missing `peer` as an
unresolved pair or a global-boundary pair. The locked native event schema uses
`NO_ID` for the peer on unary accesses such as `term_attr_read`,
`term_type_read`, and `effect_attr_write`. These rows describe one node and an
attribute/type key; `peer=None` does not assert a graph edge to an external
node. The v1.2 fields `cross_frame_trace_count`,
`global_boundary_trace_count`, and `unresolved_trace_endpoint_count` therefore
mix unlike event semantics and are not valid boundary-pair measurements.

## Source-based correction

Reanalyze the immutable v1.2 raw graphs/traces with the event definitions in
the source-locked `runners/dsl/src/access_trace.rs`:

- Pair events (`pattern_edge`, edge effects, `term_edge_read`, and
  `term_edge_attr_read`) count as concrete cross-boundary accesses only when
  both node endpoints are present. A pair crossing owned frames is a
  cross-frame access; one owned endpoint and one unassigned endpoint is a
  global-boundary access. Missing endpoints on a pair event are reported as
  unresolved/partial queries.
- Unary node/attribute/type events (`term_attr_read`, `term_type_read`, JIT
  equivalents, attribute writes/comparisons, node mint/delete, and typed
  candidate access) are classified by the traced node's ownership: local
  owned-node access or access to an explicit global node. They are not counted
  as pair crossings.
- Index/type queries without a concrete node endpoint and host tool dispatch
  are counted in separate global-query/host categories. They do not invent
  graph-node endpoints.
- Unknown event kinds remain separately counted; trace rows remain partial
  evidence and never establish access completeness.

Keep all input tasks, ownership labels, graphs, trace records, partition
algorithms, and task oracles unchanged. Preserve the v1.2 analysis output as a
known metric-definition failure. V1.3 is a source-audited retrospective
reanalysis, not a new confirmatory capture. Report exact source and raw hashes,
corrected interface/resource sets, and all original task/trace parity checks.
Do not claim safe partitioned execution; the generic message-frame scope
remains unsupported and wildcard rule access remains explicit.
