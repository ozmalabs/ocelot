# Live runtime closure-entry replay v5 preregistration

V5 repeats the same 15 primary `run_rules` call replay from closure-entry v2's parent route, but uses checkpoint schema V4 to retain EvalCache occupancy/configuration and reachable-query telemetry. Capture the graph, full ordered rules, and checkpoint before each call, lock the payloads and code, then restore each into a new substrate. The checkpoint API is fail-closed: if any cache map is non-empty, restoration is expected to reject until entry serialization exists; capture and report occupancy regardless.

If all cache maps are empty, require exact rule/scheduler restoration, graph within the documented one-ULP persistence bound, and exact per-rule counters against the source-locked parent. Keep cache occupancy independent from counter parity. This is still one authored route and does not establish natural frequency or scaling.
