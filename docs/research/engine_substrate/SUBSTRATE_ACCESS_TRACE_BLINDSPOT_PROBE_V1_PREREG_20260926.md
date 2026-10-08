# Access-trace blind-spot probe v1 preregistration (2026-09-26)

## Question

Do the current concrete trace rows account for (a) the `SetAttrIfDifferent` old-value read and (b) a native `UseTool` invocation when each is confirmed independently?

## Design

Use fresh native substrates and pair trace-disabled/enabled runs. For attribute effects, hold the matched graph/rule fixed and vary only whether the target attribute already equals the requested value. The independent oracle is the final attribute value plus fixed-point progress; the event oracle is the count of `effect_attr_write` rows for the target node/key. For tools, put a `UseTool` term in a matched rule's `where`; a Python handler increments a local call counter and returns `True`. The callback count is the independent invocation oracle; trace rows are inspected for any tool event. Each condition runs once in a fresh process invocation of the runner (fresh substrate per arm); process-global tool registry is cleared before/after.

## Predictions and limits

- Attribute changed and unchanged arms both execute the direct old-value comparison. The current trace is predicted to emit a write event only for the changed arm, so it cannot distinguish the unchanged read from no execution. This probe does not quantify CPU/memory cost of the read.
- The tool handler should fire once per actual matched `where` evaluation. The current event vocabulary is predicted to contain no callback event. Handler behavior is intentionally graph-independent because native callback re-entry can deadlock on the substrate mutex.
- Traced and untraced semantic outcomes must match. A mismatch invalidates that arm.
- Cache-key hit/miss accounting, scheduler work outside a RuleUid, and failed matcher candidate recall are out of scope; they need separate counters/oracles.

## Lock and analysis

The runner records source/native hashes, Python/platform, raw event rows, progress/status, independent counts, and explicit pass/fail checks. Results are diagnostic mechanism evidence only and cannot upgrade the trace to complete dependency coverage.
