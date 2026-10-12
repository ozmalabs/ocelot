# GenInfer frame selection source audit (2026-10-03)

## Finding

The substrate has a scoped GenInfer consumer, but source inspection found no
substrate-side producer or validator for its frame scopes. In
[`load_parts_with_scope`](../../../runners/dsl/src/shape_decode.rs#L266), the
native loader reads an observation-provided `scope_id` and filters
`ShapeSignature` parts by exact attribute equality before parsing. The
[`GenInfer` Term evaluator](../../../runners/dsl/src/term.rs#L10268) passes the
scope expression and boolean `require_scope` to that loader. When scope is
required but absent, [`eval_gen_infer`](../../../runners/dsl/src/shape_decode.rs#L3029)
returns an empty parts list.

The 2026-10-05 runtime counter probe refines the cost claim: filtering happens
inside iteration over `nodes_of_type(codebook_type)`, so an explicit scope does
not avoid enumerating the typed population. In a locked K=2 production-rule
fixture, both scoped and global modes enumerate all 38 typed nodes per query
(76 total), while per-frame scope parses 4 parts and evaluates 9,600 search
candidates across two frames, versus 76 parts and 19,200 candidates for
unscoped global mode. Exact outputs pass in all conditions. Thus scope reduces
downstream candidate work here, while population discovery remains graph-wide.
See [runtime trace v1](SUBSTRATE_GENINFER_SCOPED_POPULATION_TRACE_V1_RESULTS_20261005.md).

The native loader now also uses the existing graph attribute index when
`(codebook_type, scope_id)` is explicitly declared. A v2.1 source-locked probe
shows the indexed K=2 arm performs zero full-population node visits and returns
four scoped members over four production calls, with the same four parsed
parts and 9,600 candidates as scan-based frame scope. The index was supplied
by the harness, is not automatically admitted or rebuilt by GenInfer, and did
not produce a closure-time win on this small fixture (38.03 ms indexed vs.
28.49 ms scanned). Index maintenance, cloning, restore, and large-population
costs remain unmeasured. See [index trace v2.1](SUBSTRATE_GENINFER_SCOPE_INDEX_TRACE_V2_1_RESULTS_20261005.md).

The `GenInfer` Term carries optional scope children through its arena and
JSON/reflection codecs ([codec](../../../runners/dsl/src/jsonio.rs#L1227),
[reflection](../../../runners/dsl/src/reflect.rs#L2889)); this is parameter
plumbing, not scope production. The engine does not read `frame_id`, inspect
`FrameScope` records, calculate connected components or separators for this
route, infer dependency membership, or generate `scope_id` values. A repository search for `FrameScope`,
`gen_infer_scope_required`, and `scope_id` under `domains/`, `substrate/`,
`runners/dsl/`, and `seeds/` found the native filtering in `shape_decode.rs`,
Term plumbing in `term.rs` and its serialization/reflect support, and seeded
rule reads in `seeds/shape_decode_loop.json`. The source audit searched with `rg -n 'FrameScope|gen_infer_scope_required|scope_id'
domains substrate runners/dsl seeds` and then inspected GenInfer-related scope
hits. The remaining `scope_id` occurrences in `runners/dsl/src/py.rs` belong to
work-accounting telemetry, not frame selection. No scope-discovery writer or
provenance validator is present in those paths. `FrameScope` records in the
recent experiments are constructed by evaluation harnesses.

The task-graph structural census profiles graph components and articulation
points, but uses evaluator-supplied owner labels and a deliberately projected
undirected graph; it does not discover operational GenInfer scopes. Its
results explicitly leave factor-scope preservation and semantic parity open.
See [structural census v1.3](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_RESULTS_20261003.md).

## Capability classification

| Capability | Status | Evidence |
|---|---|---|
| Apply an explicitly supplied scope token to GenInfer codebook selection | Measured | [scope v1.3](SUBSTRATE_GENINFER_EXPLICIT_SCOPE_V1_3_RESULTS_20261003.md) |
| Fail closed when required token is missing or does not match a part | Measured | [scope v1.3 controls](SUBSTRATE_GENINFER_EXPLICIT_SCOPE_V1_3_RESULTS_20261003.md) |
| Validate scope provenance records | Absent in native path | [provenance probe](SUBSTRATE_GENINFER_SCOPE_PROVENANCE_V1_RESULTS_20261003.md) |
| Discover frame boundaries or scope tokens from graph structure | No producer found | This source audit |
| Discover cross-frame dependencies and preserve them under partitioning | Not implemented/measured | [cross-frame result](SUBSTRATE_GENINFER_CROSS_FRAME_V1_RESULTS_20261003.md) |
| Validate task semantics after applying a discovered partition | Open | Structural census and scoped closure parity audits |

## Next measurement and implementation gate

Do not treat the existing speedup as an end-to-end substrate capability. A
candidate scope-discovery mechanism must be evaluated against held-out oracle
boundaries and dependency edges, including high-coupling and ambiguous graphs.
Measure boundary recall/precision, dependency coverage, false split rate,
missed explanations, scope-generation cost, and the cost of a conservative
global retry when scoped inference has no explanation. Only after exact or
explicitly bounded semantic parity should those measured partitions feed the
production GenInfer path and larger graph scaling runs.
