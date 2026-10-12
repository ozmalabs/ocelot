# Multi-operator family search v1 preregistration

## Question

How does bounded Term synthesis perform when a task's useful primitive is
hidden in a shared, wider grammar, and how often can native example selection
resolve the generated version space without a task-specific primitive hint?

## Frozen design

Use four independently specified numeric relations: additive conservation,
product conservation, absolute-value equality, and pairwise minimum equality.
Create five seeded panels per task from rows over `[-3,3]^4`, with balanced
positive/negative initial examples and disjoint 32-row selection pools. Search
each panel once using the shared grammar
`Neg/Eq/And/Not/Plus/Times/Div/Abs/Min/Max/Lt/Gt/Or`, maximum Term size 7,
12-second timeout, and 128-solution cap. The search receives examples and
variable environments only; task identity is used only by the external label
oracle and the sealed scorer. Run up to six native maximum-entropy queries over
the initially synthesized candidate set. Do not resynthesize after a label in
this v1; record pool exhaustion and empty sets explicitly.

## Measures and gates

Freeze task construction, seeds, grammar, source/native fingerprints, and the
independent analyzer before execution. Independently replay synthesis candidate
fit on revealed labels, every query choice/label/survivor transition, and
candidate predictions over the full 1,296-point fractional grid. Report exact
candidate coverage at generation, exact final resolution, false singleton,
empty/ambiguous outcomes, labels, candidate evaluations, explored terms,
timeouts, and wall/CPU synthesis cost. Include every panel, including timeout
and no-fit cases.

## Limits

The task families and operator menu are authored, numeric, and closed. Search
does not receive the task-specific operator, but does receive a grammar that
contains all four targets. V1 tests generation and selection in one bounded
grammar, not residual-driven resynthesis, open-ended concept invention, or
natural-task capability.
