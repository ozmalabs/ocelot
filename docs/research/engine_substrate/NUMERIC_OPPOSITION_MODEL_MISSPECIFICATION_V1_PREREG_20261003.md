# Numeric relation model-misspecification v1 preregistration

## Question

When the target relation is additive conservation, outside the learner's
Neg/Eq/And grammar, does query selection detect that no available hypothesis
is adequate, or can it stop with a false singleton?

## Design

Generate five deterministic panels. Each panel has two positive and two
negative integer-valued training examples from the relation ax + ay == ex + ey,
and a frozen 32-row unlabeled integer query pool disjoint from training.
Synthesize all bounded consistent terms with size at most 9. Run
maximum-entropy and seeded sequential query policies for at most six labels,
using the additive oracle only after a query is chosen. Keep the query order
identical for policy comparisons. Score every initial and final survivor on a
disjoint 1,296-case fractional grid.

Report empty version spaces, false singleton stops, unresolved alias sets,
oracle calls, selector time, synthesis time, and held-out accuracy. A singleton
that is not exact counts as a false-confidence outcome. This is an explicit
out-of-grammar target, not a candidate-selection benchmark for an in-grammar
task.

Lock the runner, analyzer, protocol, native/Term synthesizer, query selector,
generator, and engine binary before capture. Five panels are repeated draws
from one authored relation, not five independent task families.
