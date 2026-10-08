# Live runtime closure-entry states v2 preregistration

Capture the same two-request primary route and 15 `run_rules` call-entry states as v1.1, now including the native `RuleSchedulerCheckpointV1` immediately before each call. The checkpoint contains dense per-rule dirty bits, dirty-node sets, per-edge cursor positions and deletion versions, the global edge-deletion version, and `any_mutation`. Graph, ordered rules, and scheduler payload are hashed together. Retain the prior v1.1 capture unchanged.

Acceptance: parent task/reply/graph/counter parity remains exact; 15 calls are captured; before/after locks match; checkpoint vectors align to rule counts. This is a capture of one authored route, not a broad determinism or tractability claim. Eval cache and closure-affecting configuration are known omissions in this revision.
