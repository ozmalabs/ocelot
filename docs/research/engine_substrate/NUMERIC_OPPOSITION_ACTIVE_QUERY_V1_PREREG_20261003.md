# Numeric opposition active-query v1 preregistration

Date: 2026-10-03

## Question

Given a sparse initial sample and a finite generated version space, can the
substrate select informative counterexamples that identify the numeric
opposition relation with fewer oracle calls than fixed-first or seeded-random
querying?

## Frozen design

Run five fresh workers. Each worker receives four labeled integer examples
(two axis-aligned positives, one same-direction negative, one orthogonal
negative) and one frozen pool of 32 unlabeled integer vector pairs. The
coverage-directed relation-learning v1.1 design supplies deterministic worker
seeds; training remains deliberately sparse and does not include x-only/y-only
negative counterexamples. Generate a bounded version space with the current
`domains.generator.synthesize` path: `Neg`, `Eq`, `And`, no constants, maximum
size 9, 12-second cap, at most 128 solutions. Use the unlabeled query pool as
probe environments for observational-distinctness pruning. Preserve
`halt_reason`; timeout, solution cap, or a missing target are reported as
such, never labelled a complete version space.

Replay each generated hypothesis pool under three query policies with the same
six-call oracle budget: native max-entropy selection through
`select_discriminating_input`, fixed-first in frozen candidate order, and
seeded-random over that same pool. The oracle labels only the selected query.
Each policy filters the immutable initial hypothesis pool by observed labels;
no post-query resynthesis is charged or implied. Stop early on a singleton,
no disagreement, or budget exhaustion. Freeze the final survivor set before
scoring it.

Evaluate frozen survivors on the disjoint 1,296-case fractional vector grid
and the 13-case navigation residual panel with its locked action-to-vector
encoding. Report candidate pool size/completeness, target support, every query
and oracle label, survivor counts, calls, selector/synthesis CPU and wall
costs, and held-out confusion counts. The navigation labels are only used
after query selection to test transfer.

## Gates and interpretation

- All source/build hashes and training/query inputs match the lock; all query
  calls use unique members of the frozen pool and stay within budget.
- Confirm whether the exact relation is present in the generated pool before
  comparing query policies.
- Recompute all prediction partitions, oracle labels, and held-out scores
  independently.
- Treat max-entropy gains as conditional on this finite generated hypothesis
  pool and fixed probe pool. This does not establish a general active learner,
  new grammar invention, or autonomous task discovery.
