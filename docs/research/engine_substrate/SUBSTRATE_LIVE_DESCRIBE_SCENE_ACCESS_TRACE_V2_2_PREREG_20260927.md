# Live describe-scene access trace v2.2 preregistration (2026-09-27)

## Question

Does adding the concrete Scene and its direct Percept inputs to the task-boundary projection explain a material share of selected native accesses previously classified only as outside each request's lifecycle core?

## Design

Clone the v2.1 paired traced/untraced replay and preserve its three replicate pairs, fresh worker processes, authored A/B schedule, per-request trace intervals, and semantic gates. The scope correction is explicit: retain the request-specific lifecycle projection as A/B, and record the attached `_conv_scene` plus its direct `has_percept` targets as a separate shared task-input projection. Do not assign shared input nodes to A or B. Record their IDs, type counts, induced-width upper bound, boundary incidence and unique external nodes. Classify each selected access row independently against A, B, and shared-input node sets; overlaps are allowed and reported.

## Gates

Require the inherited v2.1 gates: six distinct worker processes, three matched pairs, stable lock inputs before and after each worker, all threads joined, original serialization/lifecycle/reply gates, exact per-pair reply/event/final-state/whole-graph semantic parity, complete nonempty per-request traces with zero dropped events, no access events in untraced arms, and trace-count reconciliation. Additionally require the shared scene-input projection to contain exactly one `Scene` and three `Percept` nodes in each worker; all three repeats must agree on lifecycle and scene boundaries and on traced event aggregates. The scene input remains separate from request ownership in all summaries.

## Analysis boundary

Report weighted event counts and distinct aggregated rows touching each lifecycle core and the shared scene input, both per request and by access kind. “No named node touch” is not evidence of no dependency: the native trace is selected and incomplete. The shared Scene/Percept set is a validated input projection, not a complete closure of every rule-produced node causally derived from that scene. No natural-task or asymptotic claim follows from this fixture.

## Reproduction

Generate `evaluation/substrate_capability/live_describe_scene_access_trace_v2_2_lock_20260927.json` with `PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_live_describe_scene_access_trace_v2_2.py --lock`, then store its `locked_inputs` under that path. Run the same command without `--lock`; the driver prints each worker start/completion to stderr and writes aggregate and raw worker reports under `evaluation/reports/` after all workers complete.
