# Live frame rule-scope capture v1.1 results

Date: 2026-10-03  
Protocol: [preregistered follow-up](SUBSTRATE_LIVE_FRAME_RULE_SCOPE_CAPTURE_V1_1_PREREG_20261003.md)  
Runner: [capture worker](../../../scripts/substrate_live_frame_rule_scope_capture_v1_1.py)  
Lock: [source lock](../../../evaluation/substrate_capability/live_frame_rule_scope_capture_v1_1_lock_20261003.json)  
Raw data: [compressed worker exports](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_workers_raw_20261003.json.gz)  
Summary: [capture summary](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_20261003.json)  
Independent analysis: [analyzer](../../../scripts/analyze_live_frame_rule_scope_capture_v1_1.py), [analysis output](../../../evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json)

## Result

All nine preregistered gates pass. Three fresh workers each retain rule-store
exports before and after both requests (12 exports total, 28,338 exported rule
rows). The final graph semantic digest matches v1 and reproduces across
workers. The three workers reproduce all v1 access and work rows exactly.
Every access-traced RuleUID resolves to its same-request post-converse native
definition, and definitions for all 798 request-position/UID groups are
stable across workers. Thus 2,394 request-level UID observations map to
definitions.

The v1 crosswalk's six unresolved UIDs (2358–2363) were introduced during the
first request. The exports identify them as:

| RuleUID | Name | Match edges | Observed term forms | Effect shape |
|---:|---|---:|---|---|
| 2358 | `form_intent_conceptualizer_live` | 3 | `Neighbours`, `Attr`, `Exists`, boolean checks | 1 node + 2 edges |
| 2359 | `request_message_shape_conceptualizer_live` | 1 | `Neighbours`, `Exists`, boolean checks | 1 node + 2 edges |
| 2360 | `request_monitor_conceptualizer_live` | 2 | `Neighbours`, `Exists`, boolean checks | 1 node + 3 edges |
| 2361 | `commit_if_recoverable_conceptualizer_live` | 3 | `Neighbours`, `Attr`, `Exists`, boolean checks | 1 node + 2 edges |
| 2362 | `revise_if_not_recoverable_conceptualizer_live` | 2 | `Neighbours`, `Attr`, `Exists`, boolean checks | 1 node + 3 edges |
| 2363 | `conceptualizer_output_candidate_commit` | 1 | `Neighbours`, `Attr`, `Exists`, boolean checks | 1 node + 1 edge |

Across all three workers, these six rules account for 549 weighted access
events. Their exported `where` Terms use local adjacency and attribute checks;
none has a whole-population query Term. Their concrete match/effect shapes
therefore add useful candidate locality evidence for this operation. This
does not prove that all dependencies are represented: native exports do not
include every host read, rejected candidate, or implicit evaluator dependency.

## What is now established

The live trace-to-rule-definition join is closed for this prompt pair and
build. The v1 pre-request export omission is resolved by exporting at request
boundaries; the old v1 capture remains unchanged and its reported gap is
preserved. The consolidated crosswalk covers 401 distinct runtime-traced
definitions: 93 include a `NodesOfType` Term, 124 include local adjacency
Terms, and none include a whole-graph subgraph/reachability or external
callback Term. These are term-presence counts in definitions of rules that
emitted some trace events; they do not prove that every listed Term was
evaluated during the request. `NodesOfType` remains a whole-population
dependency candidate even though its runtime query marker is absent.

This remains an operation-scope audit rather than an inference-factor audit.
The graph's 25,065 nodes and 11,543 edges do not define variable domains or
factor scopes, and local rule match/effect syntax does not prove exact
partitioned-closure parity. `NodesOfType` scans remain a source-known
instrumentation gap, and host/scheduler totals are only partially attributed.

## Next gate

Join the complete request-time definitions to reviewed static read/write
access sets for the runtime-touched rules. Mark population queries, implicit
Term reads, callbacks, and out-of-rule activity as explicit dependencies or
unknowns. Then construct candidate rule/state partitions without using the
protocol-owned task membership and compare partitioned execution against
monolithic fixed-point closure, including shared-state and cross-frame
mutation controls. Include partition discovery, interface, and scheduling
costs before making any cheap-cut or tractability claim.
