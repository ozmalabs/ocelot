# ProblemShape production-consumer audit v1

## Method and result

The deterministic AST inventory scanned 833 Python files under `domains/`, `substrate/`, and `runners/dsl/python/`. All parsed. It found no production import of `domains.problem_shape` and no production-domain consumer import outside the producer module. Consequently there are no statically linked calls through that API in the scanned roots. The source-linked `problem_shape_growth.json` contains five rules over `ProblemShapeObservation`; one mints `ProblemShape`, and the rest decode, recognize, mark residuals, or redecode observations.

The scan excludes tests, scripts, data manifests beyond the identified growth seed, and reflective/dynamic imports. It is static evidence, not a proof of runtime unreachability. `domains/analogy_search.py` mentions `observed_problem` only among bookkeeping edges excluded from analogy signatures; this does not read or use learned ProblemShape keys.

## Capability implication

The substrate can mechanically extract a structural signature, represent observations, recognize held shapes, mint on recurrence, and re-decode after codebook growth. Current evidence does not show a production domain importing those keys to select a resolver, alter a plan, substitute a solver, or change an answer. Therefore the preceding key/behavior comparison identifies a potential misuse boundary, but no existing production behavior consumer was available for a held-out downstream-reuse evaluation.

The next gate requires an explicitly scoped consumer contract before implementation: declare which outputs may depend on structural recognition, preserve all behavior-affecting Goal parameters, define abstention on unresolved or conflicting shapes, and attach an independent output-quality oracle. Evaluate it in a test-only adapter first, on held-out task families; add a production route only if that probe demonstrates quality and cost gains over direct dispatch.

Artifacts: [AST audit](../../../scripts/audit_problem_shape_production_consumers_v1.py), [machine-readable result](../../../evaluation/reports/problem_shape_production_consumer_audit_v1_20260928.json), [producer](../../../domains/problem_shape.py), [growth seed](../../../seeds/problem_shape_growth.json).
