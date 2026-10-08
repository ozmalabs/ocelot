# Thoughtexperiment navigation polarity repair v1 — preregistration

**Date:** 2026-10-02  
**Question:** Can the graph-authored structural composer recover a faulted real navigation rule by selecting and constructing an applicable comparison-flip edit, with utility scored on held-out native rule executions?

## Scope and claim boundary

This is one new rule-repair family: grid-navigation gradient polarity. The real `hop_descend_gradient` rule is fault-injected by flipping its comparison directions. The substrate receives graph-resident rule provenance and an issue axis whose residual describes the failure and contains the cue `flip`. `ground_concern` composes a structural candidate through graph-resident RuleSummary/EditOp selection. A held-out native task oracle scores the generated rule after the candidate is fixed.

This tests a prompted, bounded structural-repair capability. The task fault, residual vocabulary, candidate operator catalogue, and held-out oracle are evaluator-authored. It does not establish autonomous fault diagnosis, open-ended edit invention, or a self-improvement rate. The v1 four-family proposal-utility panel remains separate and is not passed by this single family.

## Fixture and oracle

Load the source rule from `seeds/grid_navigation.json`; create the faulty rule by applying `apply_flip_comparison` to its effects and retaining the target rule name. Each held-out case contains an avatar cell at `(5,5)` and a nearest frontier cell exactly one step away in one of four cardinal directions. The graph also includes `flood_epoch`, `_adist`, `_epoch`, and `_dist` fields required by the existing rule. The independent oracle expects `Up`, `Down`, `Left`, or `Right` toward the lower-distance cell. Cases are fixed and identical across arms/workers.

For each held-out case, initialize a fresh core+grid-navigation substrate, install the faulted rule, optionally install one candidate variant, execute native closure, and record `chosen_action`. No task-oracle output is exposed to `ground_concern` or candidate generation. Measure the original unmodified rule as a positive oracle control and the faulted rule as a negative control.

## Arms and observations

- **Faulted control:** original comparison directions inverted; expected 0/4 oracle cases.
- **Original-rule oracle control:** source rule without fault; expected 4/4.
- **Graph-composed candidate:** call `ground_concern` with a graph-resident issue axis and capture its structural variant before scoring it.
- **Candidate-surface panel:** enumerate every candidate from the unchanged `_default_candidates` function on the faulty rule and score every one on the same four cases. Preserve generated order and labels; this distinguishes useful utility from syntactic breadth.

Run three fresh workers. Record per-case state, expected action, actual action, closure work, and elapsed time for composition, candidate enumeration, and native evaluation. Report all candidate outcomes; do not discard failures or infer a utility advantage from candidate order. Because the known generator may already put `flip_comparison` first, do not claim search-cost improvement unless measured against a separately preregistered ordering control.

## Gates

- Source/native lock matches before, during, and after all three fresh workers.
- All workers use the same source-derived faulty rule and four held-out cases.
- The faulted control fails all four cases; the original-rule control passes all four.
- The graph composer returns a built `flip_comparison` variant for `hop_descend_gradient`.
- The composed variant matches the generated `flip_comparison` edit modulo the variant name.
- Candidate enumeration is read-only with respect to the active target rule and returns at least three distinct candidates.
- The graph-composed edit and the `flip_comparison` surface candidate each pass all four held-out cases; every other candidate result is retained.
- Candidate labels, per-case outcomes, and worker summaries reconcile exactly.

Any failed gate invalidates the confirmatory claim. Keep pilot outputs distinct from the locked capture. This is a mechanism and task-utility result for one authored family, not a cross-family transfer or tractability theorem.
