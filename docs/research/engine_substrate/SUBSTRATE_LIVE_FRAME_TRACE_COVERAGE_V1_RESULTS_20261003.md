# Live frame trace coverage v1 results

Date: 2026-10-03  
Live capture: [frame-interface capture v1](SUBSTRATE_LIVE_FRAME_INTERFACE_CAPTURE_V1_RESULTS_20261003.md)  
Source inventory: [native trace coverage v1.2](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_2_20261003.json)  
Capture crosswalk: [analysis JSON](../../../evaluation/reports/live_frame_trace_coverage_v1_20261003.json)  
Runners: [source audit](../../../scripts/substrate_runtime_access_trace_coverage_audit_v1.py), [capture crosswalk](../../../scripts/analyze_live_frame_trace_coverage_v1.py)

## Source inventory

The refreshed source audit is hashed against six current Rust/Python files and
its own runner. It enumerates all 237 `TermNode` variants, 34 named trace event
kinds, 61 textual note-related sites across Term, rewrite, and JIT source, and
eight coverage findings. The classifications remain source
review, not a sound dependency extractor: selected node and adjacency reads,
population scans, matcher bindings, and effects have concrete instrumentation;
several paths are partial or absent.

The current `NodesWhere` implementation marks both its indexed and fallback
queries and distinguishes scan candidates from returned nodes. `NodesOfType`
records types for returned nodes but has no query marker and does not trace
scanned population candidates. An empty result therefore has no concrete trace
row. Other documented blind spots include rejected matcher edge identities,
`UseTool` callback reads and side effects, unchanged `SetAttrIfDifferent`
old-value reads, and graph-access notes outside an active rule UID. The latter
are discarded by `note()` rather than represented with UID zero.

## Crosswalk on the live capture

The independent join passes all six checks: current source hashes match the
source inventory; both compressed and decompressed raw hashes match the
capture summary; every observed event kind has a source name; all six requests
are present; and no access row has a zero rule UID. Across the six captured
requests there are 1,650,456 weighted concrete access events and 472,347
captured scheduler/work units. Every captured work unit has rule UID zero:
these counters describe operation/scheduler activity outside an entered rule,
not per-rule execution cost. The first prompt accounts for 469,079 access
events and 107,006 work units per worker; the second has 81,073 and 50,443.

The access trace is dominated by term attribute reads (857,271), effect
attribute comparison reads (344,067), and effect type-candidate reads
(322,389). It also records 22,050 successful pattern-edge bindings, but this
does not represent all failed matcher candidates. Typed-population query and
candidate events total 36 and 8,646. Work counters include 177,015 external
poll slots, 177,015 dirty-vector slots, 117,420 selected-rule units, 777
fixed-point probe slots, 75 scheduler passes, and 45 operation-kind markers.
These totals are repeated measurements over the three workers, not unique
nodes or rules.

## Interpretation and next gate

This closes a source-to-capture accounting step for the authored prompt pair
and confirms that the access and scheduler traces cover different work
classes. It does not estimate total access recall: the access stream is
structurally unable to expose rule-UID-zero work, and the work counters do not
record every Python adapter action, tool side effect, native scan, or rejected
candidate. Nor do graph access events establish factor scopes or finite
separator state. Zero recorder drops remain a capacity check only.

The v1 capture initially exported rule definitions only before the first
request, leaving six request-minted RuleUIDs unmapped. The source-locked v1.1
follow-up resolves all six using before/after request exports and reproduces
the original access and work rows exactly. See [request-time scope results](SUBSTRATE_LIVE_FRAME_RULE_SCOPE_CAPTURE_V1_1_RESULTS_20261003.md)
and the [independent v1.1 analysis](../../../evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json).

Next, add explicit query-scan markers and zero-result accounting for
`NodesOfType`, and attribute bounded host callbacks and rejected matcher
candidate work. For the frame-locality claim, reconcile these access classes
with static rule read/write scopes and task-specific operations, then compare
candidate partitions against a monolithic fixed-point oracle with shared-state
and cross-frame mutation controls. Preserve all omissions as unknown until
instrumented or bounded independently.
