# Indexed `AddNodeIfAbsent` lookup v1 preregistration

Date: 2026-10-06  
Status: prospective mechanism comparison; an opt-in-by-existing-index fast path is implemented, but no measurement result is yet available.

## Question

Can a selective attribute index reduce the large first-pass `AddNodeIfAbsent` population scan while preserving its exact current semantics and remaining compatible with thoughtexperiment copy-on-write branches?

## Source facts and semantic invariant

The current effect implementation resolves the requested attributes, walks `nodes_of_type(type)` in its existing order, and returns the first node whose attributes contain every requested `(key, value)` pair. Extra candidate attributes are allowed. The `Concept.name` use in `slang_variant_bind_denotes` is a high-value target. The graph already has declared `(node_type, attr_key, value)` RoaringBitmap indexes, maintained across insertion, deletion, attribute change, and type change.

An index fast path is exact for a fully indexed nonempty key only if it returns the same first witness as the current typed-node sequence. A bitmap's numeric NodeID iteration order is not itself a proof of this: deleting a node and reusing its ID can place it at the end of the typed-node sequence. Candidate retrieval must therefore use this protocol:

1. For each requested attribute key, require a declared index; otherwise use the reference scan.
2. Intersect indexed candidate sets for every requested pair. A conflicting repeated key/value pair correctly yields no candidate; matching repeated pairs are redundant.
3. On zero candidates, return the current scan's no-match result. On exactly one candidate, return it directly.
4. On multiple candidates, use the reference typed-node scan to choose the first witness. This preserves duplicate-witness ordering until an order-preserving index is independently proven.
5. Empty attribute maps always use the reference scan. Candidate attribute subset semantics and native `Value` equality remain authoritative.

This exact version may leave duplicate-heavy cases O(N); record how often that fallback occurs. Any later optimization of that path requires a separately specified order-preserving index.

## Workload and arms

Use two stages. First, isolate the exact `AddNodeIfAbsent` rule shape from `slang_variant_bind_denotes` on a native graph with candidate populations `N ∈ {512, 4,096, 7,164, 16,384}` and requested variant counts `M ∈ {1, 15, 64}`. Put matching Concept witnesses at the end of the type bucket, use unique distractor names, and preserve the real route's 15-key composition at `N=7,164` (12 hits and 3 misses). Use five fresh timing workers per cell, counterbalanced arm execution, and one separate trace diagnostic worker per cell. Second, replay the actual full-seed `unknown_word_clarification` route on five fresh workers per arm with the `Concept.name` index declared before conversation. Require the existing task oracle, exact final graph digest, exact reply, and source/build provenance. The isolated ladder estimates mechanism scaling; the full-seed route establishes applicability on this one live route only.

- **Reference:** current typed-node scan, unchanged.
- **Indexed-warm:** declare `Concept.name` before the lookup batch and use the exact candidate algorithm above.
- **Indexed-cold:** include index declaration/backfill in the measured first-use cost.
- **Branch:** create a Thoughtexperiment CoW fork before and after index construction; measure fork wall/CPU/peak memory, then run indexed and reference arms on isolated branches. Include index state in the semantic branch fingerprint.

Measure separately: index build time and memory, lookup time, candidate nodes and attribute comparisons, index maintenance under writes, graph fork cost, full closure cost, and returned witness IDs. Do not pool those phases into one speedup number. Timings require tracing disabled; operation counters are collected in separate diagnostic workers.

## Semantic and mutation controls

Before population scaling, exercise deterministic controls through the same native API and compare witness IDs and final graph state between reference and indexed paths:

- missing key, exact match, case-varied string, and multiple requested keys;
- existing candidates with extra attributes (subset semantics);
- no match, one match, multiple equal matches, and two distinct matches with different creation order;
- delete the earliest match, insert a later match, delete and reuse a NodeID, and retype a candidate;
- mutate indexed attributes from match to nonmatch and nonmatch to match;
- duplicate requested keys with equal and conflicting values;
- empty requested attributes and heterogeneous `Value` cases including boolean/integer equality as implemented by native `Value`.

The multiple-match/reuse controls must demonstrate that the indexed path returns the same first node or take the specified reference fallback. Insert/delete/retype/attribute-change controls must prove that index maintenance prevents stale witnesses. Copy-on-write arms must show isolation: branch-local mutation cannot change the parent or sibling lookup result.

## Gates and decision

- Source lock covers this protocol, runner/analyzer, seed inputs, native extension/build manifest, relevant Rust graph/effect sources, and thoughtexperiment branch implementation.
- All control cases match reference witnesses, semantic graph, and final route outcome; all workers pass current source/build provenance; no indexed lookup uses undeclared keys.
- Report candidate-count/counter parity and index staleness checks before any performance interpretation.
- Promote the path only if full-route parity passes and the warm/first-use cost profile shows a useful gain after index build, mutation maintenance, and CoW fork costs are charged. If warm wins but cold or branch costs dominate, keep it scoped to amortized long-lived sessions and state that limit. If any semantic control fails, do not promote.

This is a selected engine mechanism study. It cannot establish that the resident Concept population is a small frame boundary, natural-task prevalence, or general tractability. After this gate, apply the same explicit population accounting to curiosity and ShapeDecode, then compare full monolithic and dependency-backed partitioned execution.

## Source and prior evidence

- [`AddNodeIfAbsent` current scan](../../../runners/dsl/src/rewrite.rs#L2385)
- [Graph attribute index and indexed intersections](../../../runners/dsl/src/graph.rs#L947)
- [`slang_variant_bind_denotes`](../../../seeds/slang_lexicon.json#L314)
- [Source-linked hotspot audit](SUBSTRATE_PREOUTCOME_TASK_FRAME_HOTSPOT_AUDIT_V1_RESULTS_20261005.md)
- [Describe-rule Concept scaling v1](SUBSTRATE_DESCRIBE_RULE_CONCEPT_CANDIDATE_SCALE_V1_RESULTS_20260927.md)
- [Multi-route static dependency reconciliation](SUBSTRATE_MULTIROUTE_STATIC_DEPENDENCY_RECONCILIATION_V1_RESULTS_20261006.md)
