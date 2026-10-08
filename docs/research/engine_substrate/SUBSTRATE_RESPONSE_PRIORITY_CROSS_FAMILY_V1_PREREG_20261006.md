# Response-priority cross-family v1 preregistration

Date: 2026-10-06  
Status: preregistered finite semantic and descriptive-cost panel.

## Question

Does the response-priority rule partition that preserved held-topic replies and graph state also preserve task utility and final graph state across independently authored live-conversation routes?

## Task families and controls

Reuse five route conditions from the source-linked [live-conversation task-graph harvest v2](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V2_PREREG_20261004.md): scene description, held self-knowledge answer, self-report action, unknown-word clarification, and concern authoring. Preserve each condition's existing `task_ok` criterion from the harvest runner. These are five authored route families, not a random sample of natural conversations.

## Arms and schedule

Global uses ordinary closure. Priority assigns only `slang_variant_bind_denotes`, `curiosity_targets_ambivalent_nodes`, `gr_condition_lapse`, and `retire_duplicate_gap` to `ambient_work`; it settles `response_critical` plus canonical `global` during the response call, then performs unbounded all-area continuation. Preserve host adapter hooks by replacing only the substrate `run_rules` entrypoint. Two fresh worker pairs per condition use alternating order: replicate 0 global then priority; replicate 1 priority then global. Across five conditions this yields 20 fresh workers, with ten pairs and balanced order. Use the same seed set and current native extension, `PYTHONHASHSEED=0`, and mutation-attribution journaling disabled.

## Measurements

Record boot separately from task response and continuation. For every worker, retain the task route/action/reply fields required by the existing utility criterion, selected call count/steps/attempts, residual by area before continuation, continuation steps/rounds/residual, final normalized semantic graph fingerprint and node/edge counts, source lock, PID, and peak memory. Record within-condition pair order. A fingerprint comparison is bounded by the four-round WL invariant; report counts and task outcome parity separately.

## Gates

1. Twenty fresh workers match the source lock, inputs remain stable, PIDs are unique, and the alternating arm order is exact.
2. Every worker passes its pre-existing condition-specific utility criterion; report any failures by condition and arm.
3. Within every condition/replicate pair, replies and route outcomes agree; global and priority final normalized graph fingerprints and node/edge counts agree after continuation.
4. Priority continuation finishes with zero residual and no round-cap hit; report response residual and continuation work separately.
5. Report per-condition costs, not one pooled speed number. This panel is descriptive for selected authored routes and one machine; it cannot establish natural-task prevalence or general tractability.

If a condition fails utility or parity, retain that failure and diagnose the route before widening the scheduler claim. A pass opens broader task sampling and frame-boundary measurement; it does not close the cheap-cut prevalence gate or assess rung 3/4 acquisition.

## Artifacts

Runner: `scripts/substrate_response_priority_cross_family_v1_20261006.py`  
Analyzer: `scripts/analyze_response_priority_cross_family_v1_20261006.py`  
Capture: `evaluation/reports/response_priority_cross_family_v1_20261006/capture.json.gz`  
Lock: `evaluation/substrate_capability/response_priority_cross_family_v1_20261006_lock.json`

## Protocol amendment: corrected task-oracle route

The first runner attempt stopped at `self_report_action` because the harvest runner's `task_ok` helper calls `.get()` on route-name strings. No capture was written and those partial workers are excluded. Use the harvest's independent `task_oracle` from its analyzer for route utility; preserve the runner's additional scene faculty-build condition (`one build call`, rule delta 18) explicitly, and independently require stable locked inputs, successful boot, no error, and one inbound turn. The lock includes both harvest sources and this amendment before the full run.
