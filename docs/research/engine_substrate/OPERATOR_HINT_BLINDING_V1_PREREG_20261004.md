# Operator-hint blinding v1 preregistration

## Question

Can the bounded synthesis and native query selector identify which of two
predeclared primitive expansions explains examples, without the task-specific
operator being supplied to candidate search?

## Frozen panel and arms

Reuse the five additive and five product panels from the locked 2026-10-03
model-adequacy study. For each panel, run bounded synthesis at size 7 in both
expanded grammars: `Neg/Eq/And/Plus` and `Neg/Eq/And/Times`. Search receives the
same initial examples and probe pool in both arms. Merge the two pools by
canonical Term JSON and retain provenance indicating which grammar produced
each candidate. The policy itself receives this joint hypothesis set and the
selection pool, but no task name, target formula, or held-out labels.

Compare active selection over the joint set with Plus-only and Times-only
controls. Each policy may request at most six oracle labels from the frozen
selection order, chosen by the native maximum-entropy selector. Labels are
computed by the task oracle; held-out examples remain unavailable until every
arm stops. Synthesis time for both grammar searches is charged to the joint
arm; all search and selection work is reported.

Because the enumerator scores Boolean labels as numeric 0/1, policy prediction
normalizes native Boolean outputs and finite numeric outputs exactly equal to
0 or 1 into the corresponding Boolean class. Other output types/values are
invalid and removed after a label. The same normalization is used in selector
partitioning, filtering, and independent replay.

## Measures and gates

Lock sources, panel rows, grammar definitions, size/time budgets, and analyzer
before capture. Independently verify each returned candidate fits revealed
examples, replay every query choice and oracle label, check complete survivor
transitions, and rescore every final candidate on the 1,296-point fractional
holdout. Report exact-target candidate coverage by grammar, joint-policy
correct resolution, false singleton, empty set, unresolved ambiguity, labels,
synthesis work, selector evaluations, and wall/CPU time. All ten panels and
every arm must be reported, including timeout and no-fit outcomes.

## Limits

The experiment chooses among only two experimenter-enumerated primitives and
two numeric target families. This tests evidence-based grammar-family choice,
not open-ended primitive invention, natural-task capability, or production
self-improvement. The task oracle remains external.
