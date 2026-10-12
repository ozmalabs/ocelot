# Numeric opposition active query v1.1 preregistration

Date: 2026-10-03

## Motivation

The v1 fixed-first arm used the frozen candidate list in construction order;
that list placed several hand-selected separating probes first. Its strong
one-call result is valid for that order but is not an order-balanced baseline.
This follow-up pairs active selection with randomly permuted sequential query
orders drawn from the same locked candidate pools.

## Design

Use five fresh workers with the same sparse four-example design, bounded
`Neg`/`Eq`/`And` version-space synthesis (size 9, 12 seconds, 128-hypothesis
cap), 32 unlabeled integer inputs, and six oracle calls as v1. Freeze 30
independent seeded permutations of each worker's candidate pool before
execution. For each worker/permutation, run two policies against the same
permutation and same initial generated pool:

1. Native maximum entropy through `select_discriminating_input`; ties follow
   that permutation's order.
2. Sequential random-order baseline: query the first unused input in the same
   permutation.

After each selected query, reveal one locally computed label and filter the
immutable initial version space with the selector's exact typed-output
semantics. Do not resynthesize after labels. Freeze survivors for each arm
before held-out scoring. The 150 matched order blocks are nested within five
worker/training panels; report worker-level summaries and do not treat all
blocks as independent tasks.

Score every final survivor on the existing disjoint 1,296-case fractional grid
and locked 13-case navigation transfer panel. Record version-space completeness,
target support, query sequence, label, selector/synthesis costs, paired query
counts, exact survivor rates, and disagreement/alias controls. Query labels
come from the known harness relation, not a human or independent external
oracle; call count is not oracle wall-cost.

## Gates

- Lock source/build, training examples, candidate pool, all 30 permutations per
  worker, and analyzer before capture.
- Verify every query is a unique pool member and the two paired arms receive
  precisely the same order/pool.
- Independently replay max-entropy choices, sequential-order choices, strict
  typed filtering, stopping, labels, survivor sets, and held-out outcomes.
- Report target-missing or incomplete version spaces as model/search failures;
  never score them as successful identification.
- Interpret differences at worker-cluster level. A result applies only to this
  small numeric family and finite grammar; task/grammar invention and general
  self-improvement remain untested.
