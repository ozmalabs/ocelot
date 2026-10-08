# ProblemShape induction economics diagnostic preregistration

**Status:** diagnostic, fixed-order, project-authored workload. It measures cost and rung status on current ProblemShape paths; it does not estimate natural-task frequency.

## Question

What work does the graph-resident ProblemShape path perform for seeded recognition, a first residual, recurrent residual minting, re-decode after codebook growth, and a novel singleton that must remain residual?

## Fixed workload and order

Use full seed boot plus real `solver_dispatch` task constructors. Resolve three ordinary deduction goals and three real Bigville CAN exact goals, then observe each through `problem_shape.observe`. Use the three deduction schemas to construct real decomposition candidates; observe a first bound-1 decomposition (residual), then a bound-0 decomposition (recurrence triggers mint/re-decode), then a bound-5 decomposition (recognizes from the grown codebook). Finally observe one real CAN-to-deduction reasoning-bridge goal as a novel singleton. Keep this order fixed because recurrence and codebook growth are stateful.

## Measures

For each `observe` call, record pre/post status, rung outcome, node/edge deltas, mint count, progress count, wall/CPU nanoseconds, optional native scale-audit counter deltas, and process peak RSS. Goal construction/solver resolution and full seed boot are recorded separately from observe cost. One pass only; timing is descriptive. Require expected statuses (seeded cases recognized; first decompose residual; recurrence creates exactly one new shape and re-decodes prior residual; next decompose recognized; singleton remains residual and does not mint).

## Limits

The task cases are real application constructors but a small authored sample and use one fixed sequence. This measures pathway economics, not residual prevalence, held-out induction accuracy, mint precision across a population, transfer, or scaling. Scale-audit counters are diagnostic and do not establish low overhead.

## Reproduction

Run `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_problem_shape_induction_economics.py --output evaluation/reports/substrate_problem_shape_induction_economics_20260925.json` after verifying native-build provenance.

## Amendment v1.1 — per-rule attribution

The first diagnostic execution confirmed the expected transitions but exposed that whole-engine candidate counts during `observe` include all active seed rules, so the aggregate counters cannot isolate the ProblemShape cost. Before treating that aggregate as rung-specific, add the native opt-in per-rule counter snapshot, capture it around each observe call, and map rule indices to native rule names. Keep the workload/order and success criteria unchanged; report both the whole-engine counts and per-rule ProblemShape counts. These instrumented wall times remain descriptive and do not support an overhead claim.
