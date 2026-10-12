# Live runtime dirty-rule entry audit v1 preregistration

## Question

Do the active dirty-rule bits immediately before each primary `run_rules` call explain the scheduler's per-call selected-rule counts on the fixed two-request route?

## Method

Reuse the locked v1.6 replicate-0/audit-on worker and the v1.1 closure-entry capture as the reference for call order and graph/rule entry states. At each primary facade `run_rules` entry, record the native `dirty_rule_count` and `dirty_rule_names` before delegating unchanged. Compare the ordered count vector against `scheduler_selected_rules` rows from the same request's native work trace. Resolve names and areas to local rule indices where unique; preserve ambiguous names explicitly.

Require task, reply, final graph, behavioral counter, and source-lock parity with the parent. This is read-only telemetry; it does not alter dirty flags or scheduler behavior.

## Scope

One authored route and one replicate. Agreement identifies dirty-bit selection as an explanation for selected-rule count differences; it does not restore dirty-node sets, incremental cursors, term caches, rule-protection metadata, or prove exact replay by itself.
