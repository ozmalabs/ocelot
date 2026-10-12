# Shared evidence rule propagation preregistration

## Question

Can native scoped closure propagate a shared evidence update to frame-local derived state and match full-graph closure through activation, value change, and retraction?

## Workload

- Fresh `WorldAdapter(seeds=())`; install only two benchmark-native rules using `add_rule`.
- Rule A matches `Evidence -supports-> FrameLocalState`; when evidence is active and the local `derived` value differs from evidence `signal`, copy `signal` to `derived`.
- Rule B matches the same relation; when evidence is inactive and local `derived != 0`, reset local `derived` to zero. These are explicit input retraction semantics; no automatic truth maintenance is assumed.
- Use N=1/2/4/8 frame nodes with 0/1/3/7 shared evidence nodes linking adjacent frame pairs. Each evidence has two distinct local output states, one owned by each endpoint frame. The graph is connected for N>1; evidence nodes belong to both adjacent scopes, while frame and state nodes are frame-local.
- Three fresh-process replicates per size and arm: full graph, scoped round-robin over every frame, and a sensitivity control omitting the right endpoint scope for one selected shared evidence edge. The omission arm must retain a stale local output to prove the fixture detects missing notification.
- At four checkpoints, independently reset/measure closure after: (0) inactive baseline; (1) activate evidence with signal 1; (2) while active, change signal to 0; (3) deactivate evidence (retract). All full/scoped states must match expected values at every checkpoint. In the omission arm only the intentionally omitted endpoint may remain stale; all other outputs must match the oracle.
- Record checkpoint state, report status, progress, scoped turns, candidate enumerations, Term evaluations, wall/CPU time, peak RSS, and exact graph-state projections. Timing is descriptive.
- Lock protocol, runner, rule definitions, substrate bindings/scheduler sources, and native build provenance before execution.

## Claims and limits

A passing full/scoped arm would validate this explicit two-rule, shared-input propagation fragment with fixed topology and caller-directed scope visitation. It would not prove general notification completeness, automatic truth maintenance, natural locality, or cost advantage. The omission control is a required sensitivity check. Preserve any gate failure without changing the locked workload.
