# Dynamic helper work counters: implementation note

Date: 2026-10-05

## Purpose

The v1.3 live frame/rule capture reproduced rule identity and operation work, but it could not quantify the internal work of dynamic helper Terms. This source change adds opt-in work events to that trace so helper traversals can be counted by current rule UID and operation. It is instrumentation only; it does not bound helper scope or establish that natural tasks have small separators.

## Counter contract

The counters use the existing bounded `WorkEvent` trace. With tracing disabled, helper scopes do not emit work events. Each helper invocation emits kind `dynamic_helper_invocation` (46), with its helper family as subject. Detailed work rows use that helper subject and these kind IDs:

| ID | Event | Counted unit |
|---:|---|---|
| 47 | `helper_codebook_population_node` | Each node returned by the codebook type population query, before an optional GenInfer scope filter |
| 48 | `helper_node_attribute_examined` | Number of attributes on a node whose attributes are iterated after filtering |
| 49 | `helper_codebook_part_parsed` | Each successfully parsed nonempty codebook part |
| 50 | `helper_relation_cue_population_node` | Each relation-cue node returned by its type population query |
| 51 | `helper_search_candidate` | A helper-specific candidate or search work unit at the instrumented loop site |
| 52 | `helper_candidate_part_scored` | Each unused ShapeDecode part scored in a search state |
| 53 | `helper_graph_term_node_decoded` | Each graph node recursively visited while decoding a graph-resident Term |
| 54 | `helper_render_rule_candidate` | Each Join render-rule neighbor examined |
| 55 | `helper_auxiliary_population_node` | Each generator population node enumerated |
| 56 | `helper_scope_population_index_query` | A GenInfer scoped lookup using a declared `(codebook type, scope_id)` graph attribute index |
| 57 | `helper_scope_population_index_member` | Each matching node returned by that indexed lookup |

Helper family subjects are stable constants in `runners/dsl/src/access_trace.rs`: ShapeDecode 1, TransformDecode 2, DimInfer 3, GenInfer 4, TimeInfer 5, DepthInfer 6, BlinkBridge 7, GapAbduce 8, GapVerify 9, ProgEval decode 10, Join render 11, RatioInduce 12, SupportInfer 13. Subject zero on a row remains the rule UID in `WorkEvent`, not the helper family. The Python API exposes event names and subjects; analysis must retain the six-field all-scope tuple so operation ID, rule UID, kind, and helper subject are not conflated.

## Coverage and limits

The helper guards cover the eleven dynamic-helper variants from the v1.3 audit plus RatioInduce and SupportInfer where the evaluator shares the same population loader. ShapeDecode/TransformDecode/DimInfer/GenInfer/RatioInduce/TimeInfer/SupportInfer/BlinkBridge/GapAbduce/GapVerify/DepthInfer are guarded at evaluator entry. ProgEval's scope covers only graph-to-Term decoding, and Join's scope covers render-source resolution. GenInfer's population count deliberately occurs before its scope filter, exposing the full population traversal even when later candidate evaluation is scoped.

If GenInfer has a declared graph attribute index on the codebook type and
`scope_id`, the loader instead records kinds 56/57 and visits only indexed
members. The fallback continues to use kind 47 for every typed population
node visited before filtering. Index declaration remains opt-in; these events
do not establish automatic index admission or safe scope discovery.

Kind 51 is not a uniform complexity unit across helpers: it records the named loop iterations, not elapsed time or equivalent computational effort. It currently does not count all matcher enumeration/rejections, all graph reads, or each arithmetic operation. The normal access trace separately records selected graph reads when enabled. Neither trace is a proof of locality. Counters must be paired with exact output/graph parity and uninstrumented timing before drawing cost conclusions.

## Validation state

`rustfmt --check` passes for the edited modules. `cargo check --manifest-path runners/dsl/Cargo.toml` completed successfully on 2026-10-05 with warnings elsewhere in the crate. The provenance-aware release build ran the three-worker live helper capture and the four-arm GenInfer index trace. The latter confirms zero typed-population visits in the indexed arm with exact parity to scan-based scoped candidates; the small fixture shows no closure-time improvement. No test suite was run. Scope discovery, automatic index admission, scale-dependent maintenance/clone/restore cost, broader helper-family coverage, and natural-task prevalence remain open; see [v1.4 helper results](SUBSTRATE_LIVE_HELPER_WORK_CAPTURE_V1_4_RESULTS_20261005.md) and [index results](SUBSTRATE_GENINFER_SCOPE_INDEX_TRACE_V2_1_RESULTS_20261005.md).
