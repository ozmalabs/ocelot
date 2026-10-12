# CEGIS cross-task query-order v1 preregistration

## Question

Does first-disagreement family-order sensitivity transfer from the triangular-number task to a distinct list-statistic task when the synthesis literal vocabulary is held constant and independent of observed labels?

## Tasks and conditions

Use the already implemented CEGIS faculty without source edits on two grounded tasks:

- Triangular number `T(n)=sum(0..n)`: scalar descriptor `n`, known `n=1`, family `n=2..12`, heldout `17,23,50,99,100,250`, existing arithmetic/control operator set.
- Population variance: grounded list descriptors `sum`, `sum_sq`, `n`; known list `[2,4]`; the twelve fixed lists from `scripts/cegis_faculty_on_variance.py`; heldout lists `[5,5,5,5,5]`, `[1,100]`, `[3,1,4,1,5,9,2,6]`, `[12,7,19,3,25,8]`, and `[0,0,0,0,1]`; lean arithmetic operator set from that script.

For each task, compare five fresh-process pairs of ascending family order and deterministic seeded permutations. Every synthesis call keeps the native default literal set `{-1,0,1,2}`. To stop the synthesizer's automatic addition of integer-valued outputs, the benchmark wrapper passes a float-convertible label object that is intentionally not an `int` or `float`; the native synthesizer converts it numerically for target matching but does not add it to the literal set. The analyzer verifies wrapper policy and task labels from independent formulas/statistics.

Run 20 workers in a seed-shuffled order; each worker gets a fresh substrate and fresh oracle/descriptors. Use max size 9, 60-second per-synthesis timeout, and 12 CEGIS rounds. A 240-second process watchdog preserves worker timeouts as failures.

## Measures and gates

Record task/arm/replicate/order, every selected query and oracle call, synthesis candidate counts and elapsed times, final formula/status, heldout scores, CPU/wall costs, and worker PIDs. Require source/native/task lock match, exact schedule/cell coverage, unique fresh PIDs, no unreported worker errors, selected-query/call reconciliation, constant-set-control confirmation, independently reconstructed labels, and complete heldout readback.

Report policy differences separately by task: query count, family-oracle calls, exact heldout score, candidate work, synthesis time, CEGIS time, convergence/gaps. Five pairs per task are descriptive; do not claim policy superiority from these tasks alone.

## Claim boundary

This tests order sensitivity across one scalar arithmetic function and one list-statistic function. The tasks and candidate families are authored, and the current routine sequentially asks the oracle about family items while scanning for a disagreement. The probe does not test information-gain ranking, autonomous task/family construction, or natural-task prevalence.
