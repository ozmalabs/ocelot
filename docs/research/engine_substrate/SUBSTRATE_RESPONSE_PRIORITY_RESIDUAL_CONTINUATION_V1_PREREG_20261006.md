# Response-priority settlement and residual continuation v1

Date: 2026-10-06  
Status: preregistered engine/API and workload gate.

## Question

Can the substrate settle a conservative foreground candidate, return the conversation response with ambient work still dirty, then continue all rules to a quiescent graph semantically equivalent to global closure?

## API contract

Add `run_rules_settle_selected(areas, budget_per_area, max_rounds, snapshot_round)` as an opt-in API. It attempts rules only in the selected areas, preserves every unselected dirty bit, and reports both selected work and residual dirty rules by area. Effects from selected rules may dirty either selected or unselected areas. A later ordinary full-settlement call must process all carried work. The existing default/global path stays unchanged.

## Workload and arms

Use the locked seven-turn held-topic sequence, same seed, teaching facts, and all active rules. Global arm uses the existing closure before reply. Priority arm assigns all active rules to `response_critical` except the six v1.2 hotspot rules, which are assigned to `ambient_work`: `slang_variant_bind_denotes`, `curiosity_targets_ambivalent_nodes`, `gr_condition_lapse`, `sd_decode`, `sd_transform_decode`, and `sd_infer_dimension`. Newly authored rules default to `global`, so the foreground selection includes both `response_critical` and `global`. This is a deliberately conservative first partition, not a claim that the six are always noncritical. Intercept every main-substrate rule-run entrypoint used during `converse`, since conversation calls native `run_rules()` outside `WorldAdapter.comprehend()` as well. Priority calls settle only the selected foreground areas; after the response is captured, restore ordinary all-rule settlement and run ambient continuation to quiescence.

No rule is removed or disabled. All user facts and prompts remain identical. Capture response before continuation and graph state after continuation.

## Measures and gates

- API invariant: unselected dirty rules remain dirty; selected rules can re-dirty either area; continuation includes all dirty rules; no residual is silently dropped.
- Response gate: compare reply text, route, receipts, and task outcome to global at each turn.
- Continuation gate: after full settlement, compare v1.2 reference-aware graph fingerprints and graph counts to global at each turn.
- Cost: separate response-path wall/CPU time, selected rule steps, residual counts by area, continuation work/time, and total work. Fingerprinting is outside the timed response interval.
- Utility remains separate; report the existing clarification failure.

## Limits

Preserve the original `WorldAdapter.comprehend` and its host-side adapter hooks. Intercept only the main-substrate `inner.run_rules()` facade during `converse`, because the adapter runs rule closure both inside and outside comprehension. An initial diagnostic pilot replaced `WorldAdapter.comprehend` itself, bypassing conceptualization and monitoring; its structural divergence is a harness confound and is excluded from the experiment. The corrected runner lock records that adapter hooks are preserved.

This is one authored family and one candidate partition. A pass demonstrates a usable scheduler seam and bounded parity, not a general response-critical dependency solver, natural-task prevalence, CPU advantage, or an improvement in learning new structure. A failure must identify whether it is reply, continuation, wake-up, or source-lock parity.

## Diagnostic amendment: event-state tracing

Following the single-pair pilot, the diagnostic runner records compact summaries of `SelfConcern`, `GapRecurrence`, `GapLearningAssessment`, `HumanReview`, `Observation`, and conceptualizer request/verdict/commit records immediately before the response, before continuation, and after continuation. A second diagnostic amendment enables the substrate's mutation journal for turn zero and continuation, retaining rule names plus node/edge types for the boot-integrity, recurrence, assessment, and deferred-rule families. This instrumentation is source-locked and is used only to localize the ordering failure; its timing is excluded from performance claims. Neither amendment changes the confirmatory parity gate or authorizes a confirmatory panel.
