# Materialized proposal resolver comparison v1

## Question

Does staging an ambiguity-aware graph-rule resolver reduce measured Term work relative to the nested v1.2 formulation, while preserving proposal and decision semantics?

## Conditions

Use the same proposal fixture, sizes N=2/4/8/16/32/64, score distributions (`unique_max`, `tied_max`), three fresh workers, native scale-audit counters, and current engine build as the v1.2 comparison. The staged candidate has five rules: cache `MaxOver` once on the target; mark proposals whose score equals that cached maximum; cache `Count(Filter(is_top))` on the target; mark ambiguity if the count exceeds one; select a proposal only when the count equals one and that proposal is marked top. Compare counted Term evaluations and candidate tests against the v1.2 nested resolver capture at matching N/distribution. Exclude elapsed and `_ns` metrics from deterministic work comparisons.

## Gates

All workers/cells must match the locked source/native build. Proposal sets must remain exact and idempotent. Unique cases must select exactly the unique maximum with no ambiguity; tied cases must set ambiguity and make no selection. Counts must replicate across workers. For the materialization claim, every staged cell must use fewer total Term evaluations than the corresponding v1.2 cell. If correctness passes but any work reduction fails, report the counterexample and do not claim a general reduction.

## Limits

This is one handcrafted staged rewrite on the same authored proposal family, through N=64. It tests measured operation reduction, not asymptotic complexity, production-rule maintenance under changing proposal sets, or general resolver quality. The baseline v1.2 raw capture is fixed evidence and will not be rewritten.
