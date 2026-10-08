# Coverage-aware class return policy v1 preregistration

## Question

Can an evidence-only policy distinguish insufficient probe coverage from
harmless syntax ambiguity, expanding probes before asking an external teacher?

## Policy

Reuse the five-task, 25-panel candidate sets and schedules from the locked
semantic-equivalence study. Start with the original probe domain. On selector
abstention, summarize numeric coverage over all original selection/challenge
rows. For each of `ax, ay, ex, ey`, the registered coverage criterion requires
a zero, a value at or below -2, and a value at or above +2. If any criterion is
missing, expand to the frozen zero-aware selection and challenge inputs, then
resume entropy selection with the same six-label total budget. A singleton
receives up to two challenge labels. On unresolved stop with adequate coverage,
return a finite behavior class if all survivors agree across the full covered
probe set; otherwise request one teacher hint. Empty spaces request help.

Policy code receives inputs, candidate Terms, observations, and oracle labels
only. It does not receive task identity, teacher hints before help, or holdout
values/scores. Coverage thresholds are declared for this numeric benchmark and
are not claimed as a general-domain certificate.

## Comparison and analysis

Compare policy decisions and labels/help calls with the earlier
abstention-triggered teacher policy on the identical panels. Score returned
Terms/classes after policy execution on the disjoint 6,560-case fractional
holdout. Independently replay coverage summaries, query/fallback transitions,
class partitions, helper calls, and all output scores. Report finite class
accuracy, empty/false singleton rates, label cost, help calls, and lifecycle
cost.

The experiment measures a bounded numeric recovery policy. It does not prove
that the coverage rule transfers to nonnumeric or natural tasks.
