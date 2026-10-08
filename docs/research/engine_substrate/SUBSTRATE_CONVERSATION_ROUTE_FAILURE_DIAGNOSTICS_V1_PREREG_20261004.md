# Conversation route failure diagnostics v1 preregistration

Date: 2026-10-04

## Question

At which explicit decision point do the repeatable scene-description and
concern-authoring failures occur in the fixed five-task episode?

## Method

Use two fresh full-seed workers and the same order-0 five-prompt episode.
Instrument (without changing return values) the existing
`_ensure_describe`, `_act_describe_scene`, `act_on_instruction`, and `ask_back`
functions. Record their input condition, returned route/Goal/note, describe
faculty build status and rule-count delta, plus each prompt Message's native
`comp_*`, `communication_route`, interpretation disposition, and arbitration
basis fields. Retain final graph digests and lock source/runtime inputs.

## Interpretation

Distinguish: describe dispatch not attempted; faculty build unavailable;
request-owned `describe_scene` Goal missing; describe action succeeds but reply
release/final routing changes; or an upstream native repair preempts concern
authoring. No production behavior is altered. Repeatable instrumentation and
source-lock integrity are the capture gates.

## Limits

Two workers on one task order diagnose this exact failure path only. The concern
prompt is an authored contract stimulus and contains an underspecified
comparison target; a clarification may be semantically appropriate. This
diagnostic does not adjudicate prompt quality or task correctness.
