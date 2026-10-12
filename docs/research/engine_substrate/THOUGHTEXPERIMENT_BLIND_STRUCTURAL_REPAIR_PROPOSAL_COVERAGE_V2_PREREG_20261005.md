# Blind structural repair proposal coverage v2 (preregistration)

## Purpose and comparison status

This is an engineering follow-up to proposal-coverage v1, whose five authored
cases produced 1/5 exact target proposals. It reuses the same fault/target
pairs to measure the effect of adding three explicit edit operators:
single numeric-literal shifts by exactly ±1, deletion of one child from an
existing `where` conjunction, and inversion of one boolean literal in an
effect. Because the v1 misses informed these additions, v2 is a paired
regression/iteration measurement, not an independent confirmation or a
generalization estimate.

## Inputs and procedure

The candidate generator receives only the `faulted_rule` field. It does not
receive the target rule, case label, task examples, or oracle. The evaluation
layer compares the resulting canonical candidate rules with the sealed target
after enumeration. Candidate IDs ignore display name and active metadata.
Three fresh workers must return identical IDs, proposal counts, and target
coverage decisions. All candidate pools must remain below the registered cap
of 256 with exact proposal, valid-proposal, deduplication, and unique-count
accounting.

The paired panel contains the same five cases as v1: comparison flip, numeric
constant shift by one, dropped match edge, added guard, and boolean effect
substitution. The expected engineering hypothesis is that the new operators
recover the constant, guard, and effect targets, while the missing-edge target
remains absent because no edge type or example graph is supplied. Report
actual outcomes regardless of this expectation.

## Measures and interpretation

Report per-case and aggregate target proposal coverage, unique pool size,
operator composition, deduplication counts, truncation, worker repeatability,
and enumeration wall time. The v1/v2 coverage delta is a within-fixture
engineering comparison; timing is descriptive for five tiny rules. A pass
requires source-lock integrity, exact worker semantic agreement, no
truncation, and consistent candidate accounting. Proposal inclusion does not
establish selection, task correctness, held-out generalization, or safe
adoption.

The remaining missing-edge case is an explicit boundary for the
syntax-only interface. Adding such a relation requires evidence about the
graph's available relation vocabulary or observed edges; v2 does not invent
one. Subsequent work must provide training graph fragments as policy input
and measure whether relation proposals can be derived without target labels.

## Artifacts

- [Runner](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v2.py)
- Reuses the v1 [fixture](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json)
- Lock, capture, and analysis under `evaluation/`
