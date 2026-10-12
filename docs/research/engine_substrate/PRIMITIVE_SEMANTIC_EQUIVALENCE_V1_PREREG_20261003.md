# Behavioral-equivalence and zero-aware query v1 preregistration

## Question

When a finite query selector abstains among several surviving Terms, does an
expanded zero-aware probe domain distinguish harmful from behaviorally
-equivalent ambiguity? Can the system return finite prediction-equivalence
classes without a teacher hint, and when does the hint add value?

## Design

Reuse the five-task, 25-panel training sets and initial candidate Terms from
source-locked primitive-menu help v1.1. Replay the original nonzero query and
challenge pools as a control. In a paired arm, add zero-valued inputs and
boundary patterns to fresh, pre-frozen query and challenge pools. Ensure
selection/challenge rows are disjoint from training and from a separate
zero-inclusive 6,560-case fractional holdout. Candidate and policy code do not
receive task identity or holdout values/labels; the harness supplies requested
query labels. Run entropy selection with six-label total budget and up to two
post-singleton challenge rows.

For unresolved survivors, form equivalence classes by their typed predicted
output signatures over the finite, pre-frozen selection plus challenge input
pool. This is an observable finite partition, not a proof of universal
semantic equivalence. In a paired action arm, request one teacher/operator hint
on the same unresolved trigger and synthesize in the hinted family. Count label
queries and help calls separately. The hint is an oracle upper bound, not a
live assistant interface.

## Analysis gates

Replay the original v1.1 entropy transcript exactly; verify expanded schedules,
query decisions, labels, survivor transitions, finite equivalence partitions,
source binding, and all candidate/final scores on the disjoint holdout. Report
per-task harmful versus harmless ambiguity, query and help costs, and whether
zero-aware inputs reduce false survivors. Held-out scoring is post hoc only.

This study remains five authored numeric tasks and does not prove adequacy
outside its finite inputs or general learning capability.
