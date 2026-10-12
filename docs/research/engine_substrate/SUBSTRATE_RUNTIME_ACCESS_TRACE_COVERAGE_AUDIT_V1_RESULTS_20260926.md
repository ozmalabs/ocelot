# Native runtime access-trace coverage audit v1 (2026-09-26)

## Purpose and scope

This source audit enumerates what the current native rule access trace records and identifies concrete omitted access paths before using traces to argue about frame dependencies. It is not a dynamic recall test. The current implementation defines 16 event kinds and the Term arena contains 236 variants; most variants are pure value transforms, so that count is not a coverage percentage.

## Instrumented families

- Interpreted `Attr`/`TypeOf` and selected JIT attribute/type reads emit concrete node/resource IDs.
- Typed adjacency Terms record returned outgoing/incoming edges; `ReachableFrom`, `SlideNeighbours`, `Edges`, `EdgeAttr`, and Render child/template traversal have selected concrete edge/attribute events.
- `NodesWhere` records an index-query marker and returned/fallback rows; `NodesOfType` records returned rows; `ScalarAttrTriples` records the whole iteration.
- The rule matcher records successful pattern-edge bindings. Selected effect events cover edge insertion/deletion/replacement, node mint/deletion, attribute writes, type queries, and candidates checked by `AddNodeIfAbsent`.

These are instrumented code paths, not a claim that every call or read within each operation is represented. The trace records only while a stable current `RuleUid` is entered and ignores events with UID 0. It is bounded to 250,000 distinct event keys; overflow is reported as dropped rows.

## Concrete gaps found

1. **Shape-decode cache fingerprints:** this gap is now instrumented. `sd_cache_key` emits a typed-population query marker and type/attribute reads for each node fingerprinted ([`term.rs`](../../../runners/dsl/src/term.rs:3369), [node fingerprint](../../../runners/dsl/src/term.rs:3385)); decoder scans separately call `trace_scanned_node` on cache misses ([helper](../../../runners/dsl/src/shape_decode.rs:55)). A paired current-engine probe with one versus two identical computed DimInfer effects records 2 versus 4 query markers per codebook type, while the traced/untraced semantics match. This confirms the repeated key construction is represented in the trace; it does not identify hit/miss directly or count work outside a current RuleUID. See [probe results](SUBSTRATE_SD_CACHE_KEY_TRACE_PROBE_V1_RESULTS_20260926.md), [preregistration](SUBSTRATE_SD_CACHE_KEY_TRACE_PROBE_V1_PREREG_20260926.md), and [raw report](../../../evaluation/reports/substrate_sd_cache_key_trace_probe_v1_20260926.json).
2. **External tool calls:** `UseTool` crosses into a registered Python callback ([`Term arm`](../../../runners/dsl/src/term.rs:3776), [`dispatch`](../../../runners/dsl/src/term.rs:6901)); callback graph access and external side effects have no native event family.
3. **Attribute effect read detail:** `SetAttrIfDifferent` reads the old value to decide whether it writes, while the trace reports an effect-attribute write only on the changed branch ([old-value read](../../../runners/dsl/src/rewrite.rs:2377), [write event](../../../runners/dsl/src/rewrite.rs:2384)). This omits a concrete read and all unchanged-branch read counts.
4. **Matcher work:** only successful pattern-edge bindings are emitted ([`rewrite.rs`](../../../runners/dsl/src/rewrite.rs:1511)); failed candidates and much scheduler/index work remain outside the trace.
5. **Outside-rule work:** `note()` returns immediately when no rule UID is active ([UID guard](../../../runners/dsl/src/access_trace.rs:117)). Host adapter mutations, post-rule queue draining, and other operations outside an entered rule cannot be attributed by this stream.

Static scheduler access sets remain a separate conservative declaration and do not fill these dynamic trace gaps. The scene v2.1 capture's zero dropped rows therefore means the event-key cap did not overflow; it does not mean every access was traced.

## Next coverage gate

Diagnostic probes now exercise four boundaries, but do not estimate overall recall. The cache-key fingerprint path now has source instrumentation and paired current-engine confirmation: repeated key queries are visible, though hit/miss is not labeled and work outside a RuleUID remains silent. A preregistered matcher probe increased candidate tests from 1 to 9 while successful `pattern_edge` events stayed at 1; predicate attribute reads were visible for every candidate, but rejected edge identities were omitted ([matcher results](SUBSTRATE_MATCHER_REJECTED_CANDIDATE_TRACE_V1_RESULTS_20260926.md), [preregistration](SUBSTRATE_MATCHER_REJECTED_CANDIDATE_TRACE_V1_PREREG_20260926.md), [raw report](../../../evaluation/reports/substrate_matcher_rejected_candidate_trace_v1_20260926.json)). A separate preregistered paired probe independently confirmed one `UseTool` callback in each arm with no corresponding trace event; for `SetAttrIfDifferent`, changed and unchanged arms preserve semantics, while only the changed arm emits the target write event. See [cache-key results](SUBSTRATE_SD_CACHE_KEY_TRACE_PROBE_V1_RESULTS_20260926.md), [other blind-spot results](SUBSTRATE_ACCESS_TRACE_BLINDSPOT_PROBE_V1_RESULTS_20260926.md), and [raw report](../../../evaluation/reports/substrate_access_trace_blindspot_probe_v1_20260926.json). Post-rule work remains to be measured with explicit operation counters and attribution.

Next, add explicit cache hit/miss labels if useful for cost attribution, then add task/operation attribution for scheduler and host work outside a RuleUID. Continue testing matcher join orderings and larger candidate populations, then repeat the live task capture and report expanded coverage with overhead.

## Reproduction and provenance

Run `python3 scripts/substrate_runtime_access_trace_coverage_audit_v1.py` to regenerate the source-hashed matrix at [`coverage audit JSON`](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_20260926.json). It records SHA-256 values for `access_trace.rs`, `term.rs`, `shape_decode.rs`, `rewrite.rs`, `jit.rs`, and the current `world_adapter.py`, plus event names, note callsite counts, source anchors, and next-probe requirements. The amended source inventory does not retroactively turn the scratch probes into a locked dynamic recall result.
