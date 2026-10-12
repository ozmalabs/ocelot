# Live self-report all-scope work trace v1 preregistration

Date: 2026-09-28  
Status: source-locked replication on an independent live task family.

## Question

Can per-turn candidate/Term counters and all-scope scheduler/deferred work be captured and reconciled on the live self-report route, including a prompt that currently reproduces route shortfall?

## Workload and capture

Run the two frozen prompts from self-report matcher-cost v1.9 in three fresh full-seed processes, preserving their order and same-recipient setup:

1. `report your organisation`: expected `self_report` route with one resolved, identity-bound Goal and selection→execution→action-result lifecycle;
2. `describe who you are`: expected route shortfall, no task Goal/lifecycle producer, and nonempty public reply.

Before each turn, reset scale counters, per-rule attribution, and runtime work trace. Enable global/per-rule scale audit and all-scope work tracing for exactly the `WorldAdapter.converse` call, then disable capture and record graph/task projections, all-scope work rows, per-scope and process-global scheduler/deferred counters, per-rule/per-clause candidate totals, term totals, unattributed totals, and source fingerprints. Trace timing is descriptive only.

Lock the full Python/seed source closure, relevant Rust/PyO3 and native build files, runner, analyzer, protocol, native extension hash, build manifest, and runtime provenance. Verify source stability at worker start/end and after all workers.

## Registered checks

- Three distinct fresh processes, stable locks, expected route/lifecycle conditions, and identical per-prompt task projections and semantic graph summaries across workers.
- Per prompt, per-rule and per-clause candidate tests plus explicit unattributed candidate tests reconcile to the global matcher total; per-rule Term evaluations reconcile to global Term totals, including variant totals.
- All-scope work rows have valid operation/scope IDs, exactly one operation-kind row per operation, and zero drops.
- Per-graph-scope traced scheduler/deferred units reconcile with scoped counter snapshots; summing scopes matches global scheduler/deferred totals.
- Report workload work separately for the successful route and the shortfall prompt; do not pool them into one task success rate or one scaling slope.

## Claim boundary

This is one independently authored live task family on one current source snapshot. It tests source-linked operation accounting and matcher/Term attribution across another route. It does not estimate natural route prevalence, complete access-trace recall, runtime frame interfaces, scaling, or general task capability. A failed shortfall expectation is reported as a capability change and prevents claiming replication of the frozen route pattern.
