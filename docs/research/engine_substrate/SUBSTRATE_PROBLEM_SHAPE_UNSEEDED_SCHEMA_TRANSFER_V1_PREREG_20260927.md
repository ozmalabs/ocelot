# ProblemShape unseeded-schema transfer v1 preregistration (2026-09-27)

## Question

Does the full-seed ProblemShape codebook generalize from held shapes to two distinct real `solve_*` schema families left unseeded (`solve_can_relax`, `solve_can_bp`), while refusing to mint on singleton residuals and keeping the families structurally distinct?

## Design

Run two fresh full-seed processes for each of five scenario families (ten workers total). Every scenario creates real CAN Microtheories from distinct locked Bigville resident records, mints the Goals through `domains.solver_dispatch`, resolves them through the normal reflex/rule path, then calls `domains.problem_shape.observe`. Use `observe_measure` for native per-rule candidate/Term counts and fixed-point receipts. Record each Goal’s structurally extracted signature key, resolver status, observation initial/final status, covering shape, mint delta, codebook inventory, wall/CPU/RSS, and full source/build provenance.

Scenarios, in fixed order:

1. **Seeded exact control:** two `solve_can_exact` observations; both should match the seeded shape and mint nothing.
2. **Singleton controls:** one `solve_can_relax` and one `solve_can_bp`; keys should differ, both remain residual, no mint.
3. **Relax recurrence transfer:** two `solve_can_relax` Goals over different residents and different `k_starts` values; the schema key deliberately abstracts these parameter values, so one recurrence mint should re-decode both.
4. **BP recurrence transfer:** two `solve_can_bp` Goals over different residents and combine values (`max_product`, `sum_product`); one recurrence mint should re-decode both.
5. **Mixed-family separation:** two relax and two BP Goals; each family should mint one distinct shape, recognize its own pair, and never cover the other family.

The fixed scenario schedule is encoded in the runner. Each worker uses a fresh adapter, full seed boot, the same selected resident order, and the same scenario definitions. Rule access tracing remains off; scale audit counters are enabled only around individual observations. Hash the full current runtime/native closure and all relevant seed inputs before and after every worker.

## Gates

- Ten distinct worker processes, two per scenario; full source/native locks stable and equal to the registered lock at every worker boundary.
- Underlying CAN solver Goals resolve before they are observed. Every observation receives a nonempty expected structural key.
- Seeded exact control: both observations are recognized by the seeded key, zero new shapes.
- Singleton controls: relax/BP keys differ, both stay residual, zero new shapes.
- Relax/BP recurrence: each pair shares its within-family key, differs across any cross-family key; exactly one new shape per pair; final pair members recognized by that key.
- Mixed family: exactly two new shapes, one key per solver family; all four observations recognized by the correct key at the end.
- Every observation and post-observation closure reports fixed point. Preserve all worker records; any missing cell or failure invalidates the corresponding claim.

## Limits

This tests two specific unseeded categorical Goal schemas within CAN solving, not open-ended concept invention, natural novelty frequency, false-mint precision over a broad distribution, or downstream task improvement. `k_starts` and `combine` values are deliberately varied within the same presence-based structural key; this measures abstraction/reuse but does not establish that those values are behaviorally irrelevant to solver outcomes. Candidate counts are instrumented operation counts, not uninstrumented latency.
