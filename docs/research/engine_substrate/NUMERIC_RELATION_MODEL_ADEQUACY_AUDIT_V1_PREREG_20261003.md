# Numeric relation model-adequacy audit v1 preregistration

## Question

After a bounded learner reports one surviving Term, does a separate batch of
oracle-labeled challenge inputs reduce false confidence on out-of-grammar
relations without rejecting an in-grammar positive control?

## Tasks and panels

Use three numeric relations over four inputs: additive conservation
(ax + ay == ex + ey), product conservation (ax * ay == ex * ey), and
componentwise opposition (ax == -ex AND ay == -ey). The first two are absent
from the Neg/Eq/And grammar; opposition is the in-grammar control. Generate
five deterministic panels per relation, each with two positive and two
negative training examples. Synthesize bounded size-9 version spaces with the
same Term engine, grammar, cap, and 32-row active-query pool.

Compare paired policies: (1) maximum-entropy queries stop when the version
space reaches a singleton; (2) use the same entropy phase, then spend up to six
total labels on a separate, pre-frozen challenge pool even after a singleton
appears. Any observed mismatch removes the candidate; report empty,
ambiguous, correct-singleton, and false-singleton outcomes. Score all
survivors on a disjoint 1,296-case fractional grid. Require every
componentwise-opposition panel to contain at least one exact target hypothesis
initially and retain it through every oracle observation.

The challenge pool is an explicit model-adequacy probe, not a proof of
adequacy. It uses a supplied local oracle and six additional labels; natural
oracle cost and general task transfer remain outside this experiment.

## Lock and analysis

Freeze the runner, analyzer, this protocol, synthesizer, selector, native
engine sources/build, and every generated training/query/audit pool before
capture. Independently reconstruct query-policy transitions and exact holdout
scores. Report synthesis, query, selector, challenge-audit and total lifecycle
costs separately by task family.
