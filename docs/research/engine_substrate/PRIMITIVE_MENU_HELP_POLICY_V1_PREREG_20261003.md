# Primitive-menu selection and help policy v1 preregistration

## Question

Given a bounded menu of candidate operator families, can the learner use oracle
queries to select an adequate model, and can an explicit help request recover
when the menu leaves no queryable adequate model?

## Tasks and panel construction

Five task families use the four numeric inputs `ax, ay, ex, ey`: additive
conservation, product conservation, ordering (`ax < ex`), in-grammar opposition
(`ax == -ex`), and inequality (`ax != ex`). Generate five deterministic panels
per task from the integer grid `{-3,-2,-1,1,2,3}^4`, with eight positive and
eight negative labeled examples. Freeze 32 selection and 32 challenge rows per
panel. The holdout is the disjoint fractional 1,296-row grid.

The initial grammar menu is Base (Neg/Eq/And), Plus, Times, and Lt, each as a
separate bounded grammar. The learner sees the menu and examples, not the task
label. The harness oracle supplies labels on requested rows. If the policy
requests assistance, a separate teacher callback returns a task-relevant
operator-family hint, including Not for the inequality target. Count this as
one external-help call, separate from label queries; do not equate their
information value or monetary cost.

Compare entropy and fixed-order query policies, each with a query-only arm and
an arm that requests help after empty-set, selector-abstention, or unresolved
ambiguity outcomes. Stop querying on a singleton only after two frozen
challenge observations, or on empty/abstention, or after six total labels.
After a help request, synthesize once with the hinted family on the same
training examples; do not expose holdout scores to policy code.

## Analysis

Lock runner, analyzer, sources, panel schedules, task definitions, and policy
settings before capture. Independently replay query and help decisions; verify
candidate outcomes on the holdout, count labels/help calls, and report
synthesis/query/help lifecycle cost by task. Report false singleton,
empty-set, ambiguous, exact singleton, and post-help outcomes.

The teacher hint is an oracle upper bound on external assistance, not an
implemented language-model interface. This study does not establish
open-ended primitive invention, natural task transfer, or cost equivalence
between teacher calls and labels.
