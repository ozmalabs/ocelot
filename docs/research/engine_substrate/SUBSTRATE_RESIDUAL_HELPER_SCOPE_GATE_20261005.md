# Residual helper scope gate — 2026-10-05

## Decision from source inspection

The 2026-10-05 GenInfer residual-work analysis attributes 75% of typed-population visits to ShapeDecode, TransformDecode, and DimInfer. That is a count of visits, not a measured share of CPU time. The next useful question is whether those visits can be bounded by a valid, pre-existing frame assignment while preserving each helper's current semantics.

The current APIs are not interchangeable:

| Helper | Current population behavior | Existing scope contract | Implication |
|---|---|---|---|
| ShapeDecode | Loads typed parts and, on some paths, relation-cue nodes | `codebook_scope` collects part names and filters after loading | Preserve it as a name aperture; add any graph-frame filter as a separate optional input. |
| TransformDecode | Calls `load_parts`, then applies name-based `exclude` | No graph-frame parameter | A new frame filter can be applied before parsing, while retaining exclusion and candidate ordering. |
| DimInfer | Calls `load_parts`, applies exclusion, and loads typed generators | No graph-frame parameter; generators are currently global to the helper | Scope parts first; keep generators global for the initial experiment and count their load/work separately. |
| GenInfer | `load_parts_with_scope` filters `scope_id` before parsing; optional attribute index can avoid population visits | Optional graph-data scope ID | This is the established implementation pattern, but does not prove frame IDs are sound. |

Source anchors: `runners/dsl/src/shape_decode.rs::{load_parts,load_parts_with_scope,apply_scope,eval_transform_decode,eval_dim_infer}`; `runners/dsl/src/term.rs::TermNode::{ShapeDecode,TransformDecode,DimInfer,GenInfer}` and the corresponding `evaluate` arms; `runners/dsl/src/jsonio.rs` serialization/deserialization arms; `runners/dsl/src/reflect.rs` reflection/copy arms. The GenInfer scope parameter filters `codebook_type` nodes by their `scope_id` attribute. ShapeDecode's `codebook_scope` instead evaluates to names and has deliberate absent-versus-empty semantics. Reusing that field for frame identity would be a contract bug.

The shipped `seeds/shape_decode_loop.json` passes `obs.scope_id` to GenInfer, including the minting and validation calls. A reproducible static audit finds 44 scoped GenInfer Term occurrences, versus 3 global ShapeDecode, 7 global TransformDecode, and 17 global DimInfer occurrences in the same 17-rule seed ([runner](../../../evaluation/substrate_capability/audit_shape_decode_seed_scope_v1.py), [machine report](../../../evaluation/reports/shape_decode_seed_scope_audit_v1_20261005.json)). This established only that the observation carries a lookup key. The source-locked v1.4 live capture now resolves the runtime side: three workers reproduce one 25,065-node graph, and all 410 ShapeSignature nodes lack both `scope_id` and `frame_id` ([analyzer](../../../evaluation/substrate_capability/analyze_live_codebook_frame_provenance_v1.py), [analysis](../../../evaluation/reports/live_codebook_frame_provenance_v1_analysis_20261005.json)). The existing `obs.scope_id` therefore does not identify members in this codebook; applying it to the earlier helpers would return zero parts. This route has no valid codebook frame scope to propagate as captured. The next provenance gate must use another independently authored route whose codebook members are assigned before inference, or add and validate actual part ownership as a separate semantic change before rerunning parity and cost measurements.

## Implementation proposal, gated on provenance

If a production call site can supply a frame identity that was assigned before helper execution, add an independent optional `frame_scope` argument to ShapeDecode, TransformDecode, and DimInfer. It should have the same graph-data meaning as GenInfer's scope: only codebook nodes with the exact `scope_id` value are eligible. `None` preserves current global behavior; a present empty/missing frame population must fail closed to zero candidates. ShapeDecode's name-based `codebook_scope` and `exclude` are applied after this population restriction. Initially keep DimInfer's generator population global; measure it separately and only scope it in a later change if generators have valid frame ownership.

Before changing the API, trace production rule arguments and graph writes to establish how codebook parts receive `scope_id`, whether duplicate names cross frame boundaries, and whether ShapeDecode relation cues and any auxiliary graph reads are frame-local. If the production route has no predeclared frame identity, do not synthesize one from the winning answer or outcome; first run a separately preregistered frame-discovery gate. Harness-authored scopes may validate mechanics but cannot establish natural locality.

## Required experiment

Run a paired scan/index × global/frame-scoped panel on at least two independently authored task families. Freeze frame assignments before outcomes. Include a scan reference and indexed lookup where the graph has the scope index; compare exact helper outputs, candidate identities/order, graph digest, task outcome, and all non-helper work. Negative controls include absent scope, empty scope, mismatched scope, duplicated part names across scopes, mutation that changes `scope_id`, graph fork/restore followed by index rebuild, and a frame whose helper needs a global codebook part. Any omitted required part or changed answer rejects the proposed scope contract.

Record per helper: population nodes visited, attributes read, parts parsed, relation cues visited, candidates evaluated/rejected, generator records read, and elapsed helper time. Also record end-to-end closure wall time, CPU time, peak RSS, graph size, frame count, boundary population, and index build/update/fork/restore costs. Use separate traced and untraced workers, source hashes, unique worker PIDs, at least 10 paired repetitions per cell, randomized arm order, and a larger population series. Report distributions and confidence intervals; operation-count reduction alone is not a speedup claim.

## Advancement criteria

1. **Provenance:** production scopes are available before execution and independently justified; no outcome-derived partitioning.
2. **Semantic parity:** all positive and negative controls preserve the reference behavior, or a deliberately scoped call is rejected explicitly rather than silently broadened.
3. **Work reduction:** scoped/indexed helpers reduce the intended population work and do not move equivalent whole-population work into another helper.
4. **Cost benefit:** end-to-end time or memory improves on representative workloads after index and mutation costs; otherwise retain the result as a mechanism-only finding.
5. **Generality:** replicate on distinct task families and independently produced graphs before updating the natural-locality or tractability claim.

This gate advances engine measurement. It does not resolve rung 3/4 induction, establish cheap-cut prevalence, or demonstrate self-improvement.

## Separate engine opportunity: indexed name aperture

The failed frame-provenance path does not remove all scope-related optimization opportunities. ShapeDecode's existing name aperture is semantically valid and appears in `seeds/vision_crossframe_identity.json`: the rule scores one named `ShapeSignature` at a time. However, `eval_shape_decode` currently calls `load_parts` before `apply_scope`, so even a singleton name scope parses the whole typed codebook before retaining one candidate. The live capture's 410-part codebook and per-helper population counters make this measurable, but they do not yet quantify an end-to-end name-index benefit.

`Graph::nodes_where` can return indexed IDs in ascending NodeID order, which could preserve the loader's first-name order and later-duplicate overwrite behavior if IDs from multiple queried names are merged and sorted. The index is exact-`Value` keyed, while `collect_part_names` lowercases names and accepts both interned strings and `Surface(Text)`. Therefore a direct `name` index lookup is not generally semantics-preserving. The experiment must either add a maintained case-folded string index with full graph mutation/fork/restore coverage, or explicitly test a constrained canonical-name path and retain scan fallback whenever the invariant is not proven. It must test duplicate names, uppercase/mixed-case names, `Str` and `Surface(Text)`, empty versus absent scope, and malformed out-of-scope records; those malformed records currently may panic during full loading and cannot silently disappear under an indexed path.

The next implementation gate is a baseline and candidate-paired ShapeDecode benchmark using the cross-frame identity's candidate-at-a-time rule shape. Cross codebook sizes and aperture cardinalities, include both canonical and adversarial names, and report population visits, parts parsed, helper time, total rule-closure time, CPU, RSS, index build/update/fork/restore costs, and exact output/order/graph parity. Run the scan implementation as the oracle. Proceed to an optimized implementation only after the protocol fixes malformed-record semantics and establishes an index lifecycle contract; report operation-count savings separately from end-to-end benefit.
