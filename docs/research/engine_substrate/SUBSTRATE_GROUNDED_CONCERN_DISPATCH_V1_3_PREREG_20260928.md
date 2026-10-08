# Grounded concern-dispatch probe v1.3 preregistration

**Date:** 2026-09-28  
**Question:** Given an already constructed instruction representation, does a concern-framing utterance invoke and ground the concern faculty while a non-concern instruction remains on the goal-only route?  
**Scope:** source-locked dispatch/faculty measurement. Both conditions bypass natural-language comprehension.

## Conditions and exact inputs

Four fresh full-seed workers run two conditions twice each, in alternating order:

1. **grounded_compare:** text `Compare where the two letters differ and judge the trial on that region.`; `kind="instruction"`; dispatch `{path:"instruction", predicate:"compare", object:null}`.
2. **non_concern_walk:** text `Walk to the door.`; `kind="instruction"`; dispatch `{path:"instruction", predicate:"walk", object:null}`.

Each constructed representation is passed directly to `conversation_action.act_on_instruction`. No comprehension, seed, code, or runtime changes occur.

## Registered oracles and measures

The positive oracle requires `route=concern_authored`, `goal_kind=author_concern`, a non-null concern with nonempty signature, `minted=true`, `grounded=true`, `path=experiment_rule`, and zero teacher calls. The control oracle requires `route=goal_only`, `goal_kind=instruction`, no concern object, and zero teacher calls. Record exact outputs, concern signature/key, goal ID, seed boot, rule delta, CPU/wall task time, and stable source/runtime locks.

## Integrity gates and claim boundary

Require four unique processes, two per condition, exact schedule and texts, successful worker completion and boot, stable before/after locks, and all per-condition semantic oracles. Preserve failed/partial data without pooling. The result tests this one constructed dispatch and signature only; it does not test natural-language comprehension, correctness against a real trial, general learning, or prevalence.
