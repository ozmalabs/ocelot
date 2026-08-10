# Legacy cortex compatibility boundary

`domains.motor_cortex` and `domains.cortex_persistence` reproduce an early
Jabberwock architecture in which Python wrappers scan graph nodes, schedule
cognitive work, retain counters, and mint actions. They remain available so
historical speech experiments and stored sessions do not break, but they are
not the current motor core.

New cognition must follow the repository guardrail:

- Rust-evaluated graph rules own selection, inference, memory, learning, and
  action planning.
- Python may copy physical observations into graph facts, enact a
  graph-authored command, and serialize graph data.
- New code must not import `MotorCortex` as a general motor-policy component.
- New persistence should use `domains.graph_snapshot_io`; the legacy
  `save_session` and `load_session` functions additionally rehydrate Python
  cognitive wrappers and emit `DeprecationWarning`.

The embodied runners share only their semantically identical host mechanics
through `domains.embodied_graph_transducer`: compatible edge insertion,
cardinality validation, raw pose/state stamping, and stable reporting
projections. The module contains no tick loop, policy ranking, or learned
state.
