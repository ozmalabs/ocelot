# Generated experiment-judge semantics v1 preregistration

**Date:** 2026-09-28  
**Question:** Does the live concern-authoring route install a judge rule that classifies completed synthetic trials according to the independently computed sign of `score / frames`?  
**Scope:** semantic check of one generated rule from one authored concern signature; no natural-language interpretation or external experiment dispatch.

## Worker setup

Run two fresh full-seed workers. In each, supply the same preconstructed compare instruction used by the accepted grounded-dispatch probe to `conversation_action.act_on_instruction`. Require the generated concern to mint and ground as `experiment_rule`, and record active rule names before and after. Then add four isolated Experiment/Run pairs one at a time to the same worker graph, execute native rule closure after each, and capture the Experiment outcome and its `analysed` edge.

| Case | Experiment state | Run status | Score | Frames | Independent expected outcome |
|---|---|---|---:|---:|---|
| Positive | running | done | 3 | 3 | supported |
| Negative | running | done | -2 | 2 | refuted |
| Zero | running | done | 0 | 3 | inconclusive |
| Nonterminal control | running | running | 3 | 3 | no outcome and no analysed edge |

The independent oracle is direct rational sign evaluation: `score / frames > 0` means supported, `< 0` means refuted, and `= 0` means inconclusive. The nonterminal case must remain untouched while its Run status is not `done`.

## Captured measures and gates

Capture source/runtime lock before and after each worker, boot result, exact generated rule name set, concern signature, per-case expected/observed outcome, presence of `analysed` edge, native progress and task wall/CPU time. Require two unique processes, stable locks, exact rule and case inventory, the live concern gate in both workers, exact outcome parity for all four cases, and no teacher calls. Preserve invalid/partial capture and do not pool it.

## Claim boundary

Passing establishes that this one generated judge rule executes its declared sign semantics on four synthetic graph cases. It does not establish that the rule's verdict is a valid evaluation of an actual learned concern, that an experiment child produces trustworthy scores, or that experiment induction generalizes.
