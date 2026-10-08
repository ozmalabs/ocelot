# Live runtime closure-entry replay v8 preregistration

V8 repeats the same 15 primary `run_rules` call replay from closure-entry v2's parent route, but uses checkpoint schema V6 to retain EvalCache occupancy/configuration and reachable-query telemetry; serializable neighbour, filter, argmax, and Holds entries. Capture the graph, full ordered rules, and checkpoint before each call, lock the payloads and code, then restore each into a new substrate. The checkpoint serializes neighbour, filter, argmax, and Holds entries. Nonempty reachable and SD-operation maps remain fail-closed.

Require exact rule/scheduler restoration, graph within the documented one-ULP persistence bound, and exact per-rule counters against the source-locked parent. Keep cache occupancy independent from counter parity. This is still one authored route and does not establish natural frequency or scaling.
