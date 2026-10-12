# Adequacy probe selection under a fixed budget v1 — preregistration

## Question

Does a target-blind probe policy that seeks disagreement among a candidate and a supplied alternative-hypothesis set reduce false acceptance relative to the current seeded hash sampler, at equal oracle-label budgets? How does the result change when the true target is absent from the alternative set or the admissible domain contains only aliasing inputs?

## Design

Use four scalar power-function cases with acquisition rows `x=0` and `x=1`; fresh inputs are selected from the locked finite domain. The candidate is either correct (`x²`) or intentionally wrong (`x`), and the hidden labeler is `x^p`. The challenger set is declared before probing and never includes the hidden target by direct reference: cases cover a represented target, an omitted `x⁵` target, and an `x⁵` target on the singleton alias domain `{x=1}`. A separate correct-candidate control measures useful acceptance. Inputs and labels are evaluated through the native Term evaluator.

Compare two policies at budgets 1, 2, and 4:

1. **Seeded hash:** deterministic target-blind ordering matching the current finite-domain sampling policy.
2. **Maximum prediction entropy:** choose the fresh input with the most balanced partition of the current candidate plus surviving challengers; break ties with the same seeded hash ordering. After each label, remove challengers inconsistent with that label.

Repeat each case/policy/budget combination in three deterministic repetitions. Record selected inputs, label calls, candidate pass/refusal, held-out candidate correctness, remaining challengers, and selection/evaluation time. The hidden labeler is used only after input selection. Report false acceptance on wrong candidates, useful acceptance on the correct candidate, false refusal, and label cost separately.

## Limits and decision

This is a finite, authored scalar study. The alternative set is caller supplied, labels come from a harness-authored analytic oracle, and maximum-entropy selection cannot detect targets absent from both the candidate and its alternatives when the finite domain preserves their alias. Results can justify a later API experiment; they cannot establish general probe adequacy or authenticated evidence.

The protocol is source/native locked before capture. The experiment is informative if maximum-entropy probing improves wrong-candidate rejection at equal label budgets without refusing the correct control; the omitted-target and singleton-domain cases are explicit limits, not expected failures of implementation.
