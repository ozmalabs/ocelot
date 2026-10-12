# Continuous singleton audit v1 preregistration

## Question

Does the high false-accept rate in adaptive factored search persist when
singleton confirmation examples cover continuous, task-valid and near-miss
inputs rather than reusing integer-valued selection examples?

## Paired post-search comparison

Freeze the 20 candidate outcomes from adaptive factored search v1. Do not
change candidate generation, active labels, branch decisions, or accepted
candidate identity. For each accepted singleton, compare three audit actions:

1. **Integer baseline:** the captured policy's two matching integer reserve
   labels (already in the locked capture).
2. **Continuous audit:** present up to four newly generated continuous
   examples from `[-2.4,2.4]`, balanced across two task-valid and two near-miss
   cases, in a deterministic shuffled order. Stop and refuse the candidate at
   the first mismatch; accept after all four match. These are new oracle
   queries, not values or labels from the sealed fractional holdout grid.
3. **Help/abstain:** request help without accepting the candidate.

Task-conditioned examples come from fixed generators for additive, product,
absolute-value, and minimum relations. Candidate identity and examples are
fixed across the compared audit actions. Policy decisions may use audit labels
only; exact holdout correctness is computed afterward.

## Measures and gates

Lock source/native and upstream capture hashes, panel mapping, and continuous
example generator before replay. Independently verify balance, relation-valid
positives, oracle-positive near-miss negatives, disjointness from training and
selection pools, candidate predictions, label transcript, stopping/decision,
and sealed 1,296-point holdout scores. Report false acceptance, correct
acceptance, refusal/help, number of audit labels, and native evaluation cost
by task and policy. Include the existing integer outcomes and all 20 panels.

## Limits

This isolates the acceptance audit after search. It does not redo search using
continuous residuals, repair candidates, or measure end-to-end adaptive cost.
The four task-conditioned generators and operator menu remain authored; four
queries cannot certify arbitrary real-valued equivalence.
