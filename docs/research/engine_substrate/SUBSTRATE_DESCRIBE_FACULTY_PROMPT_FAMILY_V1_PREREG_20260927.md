# Describe faculty prompt-family construction v1 preregistration (2026-09-27)

## Question

Does the first-use faculty-construction cost recur across source-predicted paraphrases of scene-description requests, and is it absent on a nearby attached-scene self-report route?

## Conditions

Run two fresh full-seed worker processes for each condition, in a fixed shuffled schedule:

| Condition | Prompt | Expected route |
|---|---|---|
| canonical | `describe what you see` | `describe_scene` |
| tell-see | `tell me what you see` | `describe_scene` |
| describe-scene | `describe the scene` | `describe_scene` |
| report-observe | `report what you observe` | `describe_scene` |
| self-identity control | `tell me about yourself` | `self_report` |

The description prompts combine a member of `_SELF_REPORT_VERBS` with a cue in `_PERCEPTION_CUES`; the control has a strong self-identity cue and no perception cue. All workers use the same three-percept fixture and speaker. Wrap the action route and `_ensure_describe` only to record the selected route, call count, and rule-count delta. Record boot/request wall and CPU, current RSS at request boundaries, peak RSS, public reply, request-owned Goal, and lifecycle events. No native access tracing, scale audit, or final-graph readback is enabled.

## Gates

- Ten unique fresh processes (two per condition), all with identical full source/native locks before and after.
- Each worker loads full seeds and executes exactly one prompt.
- Every description condition selects `describe_scene`, resolves one request-bound `describe_scene` Goal through selection/execution/action-result, returns a string containing the three fixture colours, calls `_ensure_describe` once, and adds 24 rules during the cold request (18 faculty plus six conceptualizer).
- The self-identity control selects `self_report`, resolves one request-bound `report_self` Goal through selection/execution/action-result, does not invoke `_act_describe_scene` or `_ensure_describe`, and adds zero rules in those construction phases.
- Report all workers and per-condition values; any route, capability, lifecycle, or lock failure stays visible and blocks the corresponding prevalence claim.

## Limits

This is a deliberately source-stratified prompt panel, not a sample of natural user traffic. It estimates whether the route-level setup behavior is stable across these five formulations, not the population frequency of those formulations or the necessity of the constructed rules. The self-report control is a route control, not an unrelated task family. Two replicates per formulation provide an integrity check, not precise latency statistics.
