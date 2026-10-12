# Concern-prompt grounding diagnostic v1 preregistration

**Date:** 2026-09-28  
**Question:** Does the v1.4 concern-task `ask_back` route depend on how its two-letter comparison is worded?  
**Scope:** diagnostic of interpretation and action routing for one authored task, not a capability or prevalence estimate.

## Design

Run three semantically matched prompt arms in two fresh full-seed workers each:

1. Baseline: “Compare where the two letters differ and judge the trial on that region.”
2. Pair paraphrase: “Compare where the pair of letters differs and judge the trial on that region.”
3. Explicit referents: “Compare where letter A and letter B differ and judge the trial on that region.”

All other setup follows the source-locked live conversation capability worker: same full seed boot, no LLM, persistence disabled, same current corpus and runtime, same worker instrumentation and action wrappers. Schedule arms in alternating order: baseline, pair paraphrase, explicit referents, then repeat in the same order. Each worker is a distinct process. No prompt-dependent code or seed changes are allowed.

## Outcomes

For each prompt, retain exact reply, interpretation, goal count, communication route, action result, concern value, teacher calls, task time, and source/input locks. The primary route outcome is whether it avoids `typed_unresolved_action_dependency` plus `ask_back` and creates at least one goal. The action outcome is whether the existing concern-authoring action records `route=concern_authored` with a non-null concern. A rephrasing that changes the clarification token but still creates no goal is not counted as reaching the action route. The two-repeat results are descriptive and do not estimate a population rate.

## Integrity gates

- Six unique fresh worker processes; two per arm; no worker errors.
- Parent and worker source/runtime locks match before and after every task.
- Exact schedule, arm prompts, and baseline setup are recorded in raw output.
- Every worker records exactly one inbound turn and a complete interpretation.
- Raw capture is create-once; analysis is a separate command and cannot rewrite it.

If a gate fails, retain the capture as invalid/partial and do not interpret arm outcomes. No source, seed, cache, or runtime behavior is changed by this experiment.

## Claim boundary

This diagnostic can establish wording sensitivity on this current source snapshot. If any arm reaches concern authoring, that is a task-specific route demonstration only. If none does, the concern faculty remains untested. It does not show why an individual lexical or relational expression fails, nor establish general language understanding, concern capability, or tractability.
