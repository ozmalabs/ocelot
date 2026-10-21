# Track I0 results: PMB and shared schema decision

Status: harness skeleton and representation decision recorded; baseline scorecard is an honest capability baseline, not a held-out run.

## Baseline (Track I disabled)

The repository has no PMB runner integrated into the default substrate profile. Therefore the baseline has no measured solve/accuracy score for the PMB families. Unsupported is recorded as `NOT_RUN`; it is not scored as zero. The Track I implementation is opt-in and its generators do not alter default boot. The two implemented world generators (Loopover and D4) and their deterministic seed contract are described in `PMB_V1_SPEC.md`; a full scorecard needs a registered agent/evaluator and frozen held-out run.

## Shared `ProcessSchema` decision

Track I uses a non-migrating view node. Native nodes remain authoritative; a schema carries `kind`, `domain`, `params` when exactly evaluable, `pre`/`post` where available, `invariants`, `cost`, `provenance`, `fingerprint`, and the source identity (`realised_by`). The source identity is a node-valued attribute because current rule effects cannot add an edge to a computed-node value. An explicit `has_process_schema` edge links the schema to the agent; domain membership and held/invented membership use graph edges. Unevaluable effects have no fingerprint and remain available as opaque views.

P3's executed relax ladder remains its own `RelaxLadder` representation. This is an adapter boundary, not a claim that P3 consumes `ProcessSchema`; migrating the executor is deferred. Cross-reference: `COGNITION_BUILD_P3_EXTENDED_THINKING_PLAN.md`, deferred targeted-invention rung.

## Gate

I0.1 specification and I0.2 generator/harness scaffolding are present. I0.3 remains open until a PMB-compatible baseline runner and frozen evaluation exist. I0.4 is decided as above, with the P3 adapter explicitly deferred. This does not pass the complete I0 gate in the Track I plan.
