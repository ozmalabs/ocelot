# Pre-outcome task-frame hotspot audit v1

Date: 2026-10-05  
Status: source-linked read-only attribution of the v1 capture; no engine behavior changed.

## Result

The v1 access trace is reproducible at rule and operation level: each of the seven per-prompt event profiles is identical across its three workers. The analyzer independently joins observed RuleUID names to the seed definitions and the effect/Term implementations. Every seed hash matches the capture's Python/seed source closure, and the Rust files match the native build manifest named by the capture. The result is an attribution of recorded native accesses, not a timing or causal ablation experiment.

Most accesses outside the ingress cut come from three broad resident operations plus a one-turn ShapeDecode burst:

| Route stage | Rule(s) | Outside-cut accesses / observed work | Source-level behavior |
|---|---|---:|---|
| First “What do you know about copper?” turn | `slang_variant_bind_denotes` | 215,073 accesses (49.4% of 435,616 outside-cut accesses). Fifteen match edges cause 107,460 typed Concept candidates and the same number of `name` comparisons, or 7,164 candidates per match. The rule mints 3 Concept nodes and upserts 15 `denotes` edges. | The rule is not request-anchored: it matches each `agent knows_variant v` with no `denotes` edge. Its `add_node_if_absent` effect scans `graph.nodes_of_type(Concept)` and compares the requested attributes candidate by candidate. On each later turn, this rule has only 90 `denotes` edge reads and no typed candidate scan or attribute comparisons. The measured initialization cost is therefore concentrated in this first pass for the captured session. |
| Every held-topic turn | `curiosity_targets_ambivalent_nodes` | 63,230–107,491 accesses per turn. First turn: 6,323 `has_concept` match edges, 44,261 reads each of `state` and `is_ambivalent`, plus 6,323 flag comparisons and writes. Subsequent turns retain 63,230–75,876 reads of those attributes. | A global microtheory-to-Concept recognition rule classifies ambivalent Concepts, independently of the inbound Message. The separate live self-report scale study already shows its candidate work grows by eight tests and 88 Term evaluations per added membership on that workload; the new trace confirms it is active during held-topic turns. |
| Every held-topic turn | `gr_condition_lapse` | 19,806–26,408 accesses per turn, including 4,920–6,560 ShapeSignature typed-candidate visits. | The generic residual-condition rule contains `Count(Filter(NodesOfType("ShapeSignature"), ...))` branches. It evaluates the current shape population from each applicable condition, outside the message-root input projection. |
| First held-topic turn only | `sd_decode`, `sd_transform_decode`, `sd_infer_dimension` | 57,057 combined accesses outside the cut, including ShapeSignature codebook candidates and attributes. Later turns show only 10–11 status reads per rule. | The first captured turn settles a pending Observation through the shape-decoding ladder. This is reported as first-turn work; the capture does not establish whether it is startup overhead or a request-triggered operation. |

The first three named rules contribute 345,701 outside-cut accesses. Adding the first-turn ShapeDecode family yields 402,758 of 435,616 outside-cut accesses (92.5%). In the six later turns, `curiosity_targets_ambivalent_nodes` plus `gr_condition_lapse` account for 89,638–95,682 outside-cut accesses per turn. The full per-prompt breakdown, event profiles, source hashes, and capture/lock digests are in the [machine analysis](../../../evaluation/reports/preoutcome_task_frame_hotspots_v1_analysis_20261005.json).

## What this changes

The earlier “small ingress frame, broad outside access” result now has a more precise explanation: much of its outside work is independent of the request and comes from resident whole-population rules or a first-pass lexicon materializer. A small ingress frame may still be useful for the request-critical subgraph, but its raw boundary count cannot predict synchronous full-closure work while these resident rules execute in the same turn. The next locality test must distinguish request-dependent work from ambient supervision and one-time session materialization.

This does not establish that any of these operations are unnecessary, that they can safely be disabled, or that deferring them improves latency. The curiosity classifier and residual-condition tracker change persistent semantic state. A valid scheduling experiment must preserve the same complete eventual graph and answer, including those updates, while measuring whether they can be settled outside the response-critical path. Likewise, replacing `add_node_if_absent` with indexed lookup requires exact parity for its subset-attribute matching and first-witness behavior.

## Existing scheduler boundary

The substrate already exposes opt-in `run_rules_settle` and `set_rule_area`. The default `WorldAdapter.comprehend()` still calls global `run_rules()`. The settlement API processes every declared area on each round, has one shared positive `budget_per_area`, and carries unfinished dirty rules if its round cap is reached. It does not currently expose a selected-area run or a distinct budget/priority per area, and `converse()` does not return a reply while carrying that residual into a later daemon cycle. Therefore the first implementation gate is an exact full-settlement comparison using the existing API; response-critical deferral requires a priority/residual entrypoint integrated with conversation and the asynchronous daemon lifecycle.

## Next gated experiment

Use identical captured inputs and fresh source-locked processes to compare global `run_rules()` with `run_rules_settle(budget_per_area=0)` under explicit area assignments, first with the barrier form and then the async form. Use Thoughtexperiment CoW branches for isolation. Require exact full graph and reply parity before treating the existing scheduler as a viable baseline; report total cost without claiming response-time improvement. Then implement or prototype per-area priority/residual continuation so a request lane can return while ambient state work remains queued, without removing or disabling its effects. Require the same answer, receipts, and complete eventual graph after both queues settle, while measuring response-critical and settle phases separately. Include no-lost-wakeup mutations for Concept state/membership, ShapeSignature populations, and slang denotations. Counterbalance cold first turns against warmed sessions and vary each population independently. Only a parity-passing result can support moving this work off the request-critical path.

Separately, evaluate an indexed `AddNodeIfAbsent` path on the 7,164-Concept × 15-variant case. Require equivalence against the current scan for empty/missing keys, exact and case-varied strings, duplicate/subset attributes, multiple existing matches, insertion, and mutation lifecycle. Charge index construction and maintenance, then measure both first-pass and warmed-session cost.

## Source and artifacts

- Captured rules: [`slang_variant_bind_denotes`](../../../seeds/slang_lexicon.json#L314), [`curiosity_targets_ambivalent_nodes`](../../../seeds/causal_attitude_networks.json#L721), [`gr_condition_lapse`](../../../seeds/goal_residuals.json#L787), and the [ShapeDecode ladder](../../../seeds/shape_decode_loop.json#L127).
- Engine operations: [`AddNodeIfAbsent` scan and attribute matching](../../../runners/dsl/src/rewrite.rs#L2384), [`NodesOfType` population materialization](../../../runners/dsl/src/term.rs#L9866), [typed-node population lookup](../../../runners/dsl/src/graph.rs#L1978), and [effect parsing](../../../runners/dsl/src/graph_rules.rs#L260).
- Scheduler boundary: [conversation closure entrypoint](../../../substrate/world_adapter.py#L4089), [per-area native settlement](../../../runners/dsl/src/substrate.rs#L5441), [area assignment](../../../runners/dsl/src/substrate.rs#L5613), and [Python binding](../../../runners/dsl/src/py.rs#L4836).
- [Analyzer](../../../scripts/analyze_preoutcome_task_frame_hotspots_v1.py)
- [Machine analysis](../../../evaluation/reports/preoutcome_task_frame_hotspots_v1_analysis_20261005.json)
- [Input protocol](SUBSTRATE_PREOUTCOME_TASK_FRAME_CAPTURE_V1_PREREG_20261005.md), [raw capture](../../../evaluation/reports/preoutcome_task_frame_capture_v1_20261005/capture.json.gz), and [capture source lock](../../../evaluation/substrate_capability/preoutcome_task_frame_capture_v1_20261005_lock.json).
- Prior membership scaling evidence: [live self-report scale v1](SUBSTRATE_LIVE_SELF_REPORT_LIVE_SCALE_V1_RESULTS_20260927.md).
