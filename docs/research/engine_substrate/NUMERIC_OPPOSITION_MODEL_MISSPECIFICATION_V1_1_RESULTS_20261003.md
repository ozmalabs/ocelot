# Numeric relation model-misspecification v1.1 results

The corrected, source-locked five-panel run uses identical frozen query orders
for maximum-entropy and sequential policies. Both now receive feature maps and
can score the frozen query pool. The selector represents a Term evaluation
failure as an explicit output class; an oracle answer removes failed or
ill-typed candidates. Independent analysis passes 5/5 checks, including query
shape, exact prediction transitions, disjoint holdout rescoring, and source
hash binding.

A separate controlled evaluator-failure case exercises both the regular and
batched selector paths: each returns a marked error prediction, chooses a
discriminating query, then removes the failing candidate after the oracle
answer. This confirms the failure bucket at both API boundaries. The five generated
out-of-grammar panels themselves produce no raised native Term-evaluation
errors at selected queries; their failures are generalization and typed-output
failures.

The bounded Neg/Eq/And learner returns 31 hypotheses across four panels and
no fit in the fifth. Every initial hypothesis and every final survivor is
inexact on the disjoint 1,296-case fractional holdout. Maximum entropy uses
1, 4, 2, 0, and 1 queries across workers; sequential uses 1, 4, 3, 0, and 1.
Both policies end with false singleton hypotheses in the same three panels and
empty version spaces in the remaining two. Maximum entropy saves one
simulated label in one panel; the other panels tie. It does not detect model
misspecification reliably or improve held-out adequacy. This is one authored
out-of-grammar relation, not general active-learning evidence.

V1 is diagnostic for synthesis/held-out findings only; its query runner passed
row lists instead of the feature mappings required by the selector. This v1.1
replay corrects that binding and tests the selector change under a new lock.
The current evidence says explicit evaluation-error outcomes restore query
availability but do not prevent false confidence when the bounded hypothesis
space is wrong. A further gate needs an independently justified adequacy test
or a broader oracle/query budget, plus unrelated target relations. See
[amended protocol](NUMERIC_OPPOSITION_MODEL_MISSPECIFICATION_V1_1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1.py),
[source lock](../../../evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1_lock_20261003.json),
[capture](../../../evaluation/reports/numeric_opposition_model_misspecification_v1_1_20261003.json),
and [analysis](../../../evaluation/reports/numeric_opposition_model_misspecification_v1_1_analysis_20261003.json).
