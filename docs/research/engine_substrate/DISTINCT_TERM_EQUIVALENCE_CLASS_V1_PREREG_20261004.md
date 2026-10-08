# Distinct-Term equivalence-class positive control v1 preregistration

## Question

Can the coverage-aware policy return a finite behavior class containing
structurally distinct Terms, after removing a behaviorally distinct control,
and do the class members continue to agree on a separate wider evaluation
domain?

## Frozen task and hypotheses

Use the five existing frozen opposition panels, including their training
examples and query schedules. Replace their precomputed candidate pool with
three declared Terms: `ax == -ex`, `-ax == ex`, and the same-sign control
`ax == ex`. The first two are distinct canonical Term trees and encode the
same equality under operand symmetry; the control differs. Run the unchanged
coverage-aware policy, label budget, and coverage rule. The harness supplies
the candidates; this is not a candidate-generation experiment.

## Independent evaluation

Replay every query transition from the frozen candidate Terms and labels.
Require a returned class to contain exactly the first two Terms and exclude
the same-sign control. Independently compare member predictions on the
policy's covered probes, the registered fractional holdout, and a separate
balanced wider-domain set with boundary/extreme finite values. Report labels,
coverage expansions, class size, and any false return.

## Limits

This is a controlled positive control for distinct-Term class handling on one
authored relation. The equivalence is a simple algebraic symmetry, candidates
are supplied, and the wider domain is finite. It does not establish semantic
deduplication, open-ended hypothesis induction, natural-task prevalence, or
general transfer.
