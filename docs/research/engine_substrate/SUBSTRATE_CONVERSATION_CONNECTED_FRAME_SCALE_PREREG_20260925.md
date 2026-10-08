# Conversation connected-frame scale preregistration

## Question

Does repeated round-robin scoped closure preserve native deliberation outcomes when adjacent frame scopes overlap on shared candidate nodes, and what work is added by this boundary coupling?

## Frozen workload and procedure

- Load only `conversation_deliberation_phase4a` into a fresh `WorldAdapter(seeds=())` per worker.
- Use N=1/2/4/8 deliberations and three fresh-process replicates per size and arm (`full`, `scoped`). Each deliberation has a local grounded repair and an unsupported candidate. For N>1, each adjacent pair shares one grounded answer candidate, producing a connected chain of overlapping scopes. The shared candidate has the same valuation context in each adjacent deliberation; its expected value increases by edge index, so each deliberation's expected winner is its highest-index adjacent shared candidate. N=1 has one local grounded answer.
- Assign each deliberation, goal, local candidates, and incident shared candidates to its Microtheory scope. Shared candidates therefore belong to both adjacent scopes. No other edges connect deliberations.
- Compare native full report closure with repeated round-robin `run_rules_scoped`; stop scoped only after a no-progress complete round, then require a zero-work fixed-point report.
- Preserve all full/scoped graph projections, task decisions, fixed-point status, progress, frame turns, candidate enumeration, Term evaluations, wall/CPU time, and RSS. Require exact paired normalized projection parity and the expected selected answer for every deliberation. Counters and timing are descriptive, never parity criteria.
- Lock this protocol, runner, seed, materializer, bindings, and scheduler sources before execution; require a current native build.

## Interpretation limits

This is a deliberately constructed shared-candidate chain for one deliberation rule family. It tests overlapping scopes and a shared-node boundary, not natural conversation prevalence, arbitrary cross-frame rules, long-range dense coupling, or asymptotic complexity. If a shared candidate's global status causes a semantic collision, preserve the run and report the failure rather than changing the fixture after lock.
