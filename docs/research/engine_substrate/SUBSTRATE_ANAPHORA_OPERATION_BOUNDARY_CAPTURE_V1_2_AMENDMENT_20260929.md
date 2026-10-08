# Anaphora operation-boundary capture v1.2 amendment

Date: 2026-09-29, before the v1.2 lock and capture.

## V1.1 ownership diagnostic

V1.1 passes production-task, source, tracing parity, and graph reconstruction
gates, but its first turn interval includes the lazy `_ensure_intent_seeds()`
load performed inside `receive_utterance`. In the first case this adds 481
nodes before the utterance closure, including 201 `LexSlot`, 148 `Lexeme`,
102 `Concept`, and seed/rule/frame infrastructure nodes. V1.1's birth-time
rule therefore assigns 360 seed/configuration nodes to the first message
frame. The resulting authored-cut metrics are invalid as a task-frame census.
Preserve the v1.1 capture and report its measurement-scope failure; do not
present those cuts as task locality.

## Correction

Construct the same default adapter, explicitly call its idempotent
`_ensure_intent_seeds()` before the task-frame baseline, and record all nodes
introduced by that call as global pre-task configuration. `receive_utterance`
calls the same method on the ordinary route; the warm-up only moves the lazy
load outside the message frame. Keep the task suite, ownership-by-birth rule,
global-type list, tracing scope, and all semantic gates unchanged. The runner
must verify exact final graph digest parity against both v1.1 trace-off and
trace-on captures for every case and worker before any frame metric is
interpreted.

Use fresh v1.2 runner/analyzer/lock/raw/analysis paths. No earlier lock or raw
capture is overwritten. If warm-up changes a task graph or oracle, classify the
affected cell inconclusive and stop the cut interpretation.
