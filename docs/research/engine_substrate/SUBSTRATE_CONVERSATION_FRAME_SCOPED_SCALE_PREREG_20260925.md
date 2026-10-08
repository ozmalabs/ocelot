# Conversation deliberation frame-scoped scale preregistration

**Question.** On a second native task path, does frame-scoped closure preserve the full deliberation result, and how do candidate/Term work and wall/CPU cost grow with the number of independent deliberations?

## Locked design

- Use `WorldAdapter(seeds=())`, load only `conversation_deliberation_phase4a`, and create N independent native deliberations at N=1/2/4/8, with three fresh-process replicates per size and policy.
- Each deliberation contains the same three candidates as the phase-4A runtime fixture: grounded repair, grounded answer, and ungrounded high-score answer. The expected native result is answer selected, repair rejected, unsupported rejected.
- Assign each deliberation, its goal, and its candidate nodes to a distinct one-hop `Microtheory.has_concept` scope in the shared graph. No relation crosses between task frames. This is a disconnected positive control, not a claim about all conversation workloads.
- Compare one `run_rules_report` full-graph closure with repeated round-robin `run_rules_scoped` calls over the N scopes. Stop scoped turns only after a complete round makes zero progress; confirm terminal status with a zero-work report.
- Measure candidate pairs, Term evaluations/units, progress, scoped frame turns, wall time, CPU time, and process peak RSS. Compare normalized per-deliberation outputs and full graph state between policies. Keep timing descriptive; semantic parity and counter completeness are the gates.
- Lock protocol, runner, conversation seed, materializer, native bindings, and scheduler source before execution. Require current native build provenance.

## Decision rules and limits

All 24 workers must settle at the report API's `fixed_point` status. Every task frame must select exactly its grounded `answer`, reject `repair` as outcompeted, and reject the unsupported candidate for missing grounding. Full and scoped normalized projections must match for every pair. Record all scope turns and audit counters; do not infer linearity from only four sizes.

This tests the real conversation deliberation rule path under disconnected task frames. It does not test shared candidates, cross-frame links, actual message-driven task prevalence, asynchronous native scheduling, or natural conversation distributions. If generic scoped matching rescans globally, that cost is part of the measurement and must remain visible.
