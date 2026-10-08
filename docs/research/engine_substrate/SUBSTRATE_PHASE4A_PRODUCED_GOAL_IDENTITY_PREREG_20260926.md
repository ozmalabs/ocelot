# Phase 4A producer-emitted Goal identity probe

**Question:** does the existing Phase 4A deliberation producer and native execution-trace rule carry the Goal identity needed for independent concurrent tasks, and can scoped closure preserve its result?

Use the production `materialize_from_live_thought_manifold` adapter with the frozen `conversation_deliberation_phase4a` rules. Create independent Goal, live ThoughtManifold evidence, and Microtheory owner frames at N=2/4/8. For every task the source candidate is grounded, execution-ready, and has a resolved outcome, so native selection, `DeliberationExecutionTrace` creation, `for_goal` linking, and settle-back all execute. This producer path emits identity from `Deliberation.about_goal`; the runner must not manually add an execution-trace `for_goal` edge.

Compare global fixed-point closure against repeated scoped-delta sweeps. Use three fresh processes per size/policy (18 workers), fixed construction order, and one selected candidate per Goal. Require exact per-task outcomes and trace-to-goal association, full/scoped normalized projection parity, fixed points, no caps/deferred effects, unique PIDs, and independently reconstructed audit counters. Record construction, closure wall/CPU, candidate pairs, Terms, queue turns, and peak RSS. No tests are added by the benchmark task.

Limits are registered in advance: this is production materialization plus a native producer rule on authored evidence, not a natural workload distribution; the frame partition is runner-authored. It addresses only explicit identity production and closure costs, not cheap-cut prevalence or induction. Do not alter rules or gates after observing results without a dated amendment.
