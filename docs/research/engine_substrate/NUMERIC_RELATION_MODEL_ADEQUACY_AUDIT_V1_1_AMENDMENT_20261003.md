# Numeric relation model-adequacy audit v1.1 amendment

## Reason for amendment

The v1 capture remains immutable and diagnostic. Its analyzer passed transcript
replay, input-pool, holdout-score, paired-policy, and source-binding checks, but
failed the positive-control gate: one four-example opposition panel did not
contain an exact target in the synthesized candidate set. Thus v1 cannot
establish whether challenge auditing preserves an available correct model.

## Control correction

Repeat the same three tasks and five deterministic workers with the same
synthesizer, grammar, maximum size, query budgets, 32-row query and challenge
pools, and 1,296-case disjoint fractional holdout. Keep additive and product
training at two positive and two negative examples. For opposition only,
replace the four-example random training set with 8 positive and 8 negative
coverage-directed examples: two axis cases plus six distinct nonzero
componentwise oppositions, and two single-component counterexamples plus six
sampled negatives. This is a deliberate positive-control correction; results
for opposition are not sample-size matched to the out-of-grammar tasks.

The locked pools are regenerated excluding the selected training examples.
All panels, synthesis settings, sources, and analyzer are frozen before the
new capture. The same exact-target survival gate applies. V1 results are not
overwritten or pooled with v1.1. The audit remains a finite diagnostic using a
local oracle and does not prove general model adequacy.
