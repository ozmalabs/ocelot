# Live scheduler-work trace v3 preregistration

Date: 2026-09-28  
Status: whole-request, all-graph-scope operation-work capture.

## Question

Does enabling work-only tracing across all graph scopes in the process assign the scheduler and deferred-queue totals observed during the live `describe_scene` request to graph-scoped `run_rules` operations?

## Method and gates

Use the same full-corpus boot, static/meter/mover scene, and request as v1/v2. Reset scale/work counters after boot. Enable scale auditing and all-scope work-only tracing for the request, then disable tracing and capture all-scope work rows, all graph-scoped scheduler/deferred counters, legacy global counters, reply, and source/native fingerprints.

1. Three fresh workers complete with stable source/native fingerprints and the expected reply.
2. Work trace has no drops; every row has a nonzero scope, operation ID, and positive units.
3. For each scope, aggregate work rows exactly equal scoped scheduler/deferred counters across all metric families, including zeros.
4. Summed scoped counters equal legacy process-global scheduler/deferred totals for this measured interval. Any discrepancy is reported by metric and retained as an explicit failed gate; do not infer an owner for unmatched work.
5. Across workers, total work and operation-indexed work profiles reproduce. Raw pointer scope IDs and serialized graph IDs are not compared across processes.

## Claim boundary

Passing assigns measured scheduler/deferred work to graph scopes and active `run_rules` operations for one authored dialogue route. It does not establish graph-access trace completeness, natural-task locality, semantic state parity, or scaling. Work emitted outside an active `run_rules` operation is expected to remain a visible global-versus-scoped residual until separately attributed.
