# Primitive-family selection v1 preregistration (2026-10-03)

## Question

Given examples that underdetermine whether additive or multiplicative equality
is intended, can maximum-entropy queries distinguish useful operator-family
candidates more efficiently than fixed query order, without seeing the task
label or held-out examples?

## Design

Use all five additive and five product training panels frozen in numeric model-
adequacy audit v1.1. For every panel, synthesize both candidate families:
Neg/Eq/And/Plus and Neg/Eq/And/Times; size 7, no constants, at most 128
candidates, 12 s per family, and the same 32-row unlabeled input pool. The
operator menu is supplied to the learner, but the target relation/task label
is not passed to the candidate selection policies. Query labels come only from
the harness oracle implementing the locked target relation.

Compare paired policies over the union of family candidates: maximum-entropy
selection from remaining pool rows versus the next row in a pre-frozen order.
Both stop at a singleton or empty set, or after six total labels. No held-out
scores are used by either policy. Score every initial/final candidate on the
1,296-point fractional grid after selection. Record synthesis work by family,
query counts, selector latency, remaining operator families, exact/false
singleton/empty/ambiguous outcomes, and full lifecycle cost.

## Analysis gates

Independently replay all frozen panels, synth outputs, query choices and
candidate transitions; verify candidate holdout scores and source/capture
binding. Report per-target and paired outcomes. The study measures selection
among two supplied operator families on two related numeric targets; it does
not measure open-ended primitive discovery, help-seeking, or transfer.

## Frozen inputs

Hash this protocol, runner, analyzer, source/build inputs, and selected panel
rows before capture. Preserve all partial/empty synthesis results and query
abstentions.
