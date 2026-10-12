# Numeric relation model-misspecification v1 results

The source-locked experiment used five deterministic four-example panels for
additive conservation, a target relation absent from the Neg/Eq/And grammar.
Synthesis returned 31 candidate Terms in four panels and no candidates in one.
Every initial hypothesis was inexact on the disjoint 1,296-case fractional
holdout; all final survivors were also inexact. The independent analyzer
passed 4/4 integrity and replay checks.

Maximum-entropy querying selected no query in any panel with hypotheses: each
had at least one candidate that failed evaluation somewhere in the frozen
query pool, and the selector discarded every input on which any candidate
failed. The four nonempty pools therefore remained unresolved; the fifth was
empty at synthesis. Sequential querying used 9 labels across the five panels,
ending with false singleton hypotheses in three panels and an empty version
space in one. It did not find an adequate Term. These are simulated local
oracle calls, not external-query economics.

This exposes two distinct limits: the current entropy selector cannot use a
query when a candidate evaluation fails, and sequential elimination can yield
false confidence in a singleton despite the model being out of grammar. The
first gap is an engine/API behavior suitable for a follow-up: represent
candidate evaluation failure as an explicit prediction outcome, then measure
whether entropy querying can safely eliminate partial or ill-typed hypotheses.
Even with that change, held-out adequacy cannot be inferred without new
observations or a model-adequacy test. Five panels repeat one authored target;
no general misspecification guarantee follows. See the
[protocol](NUMERIC_OPPOSITION_MODEL_MISSPECIFICATION_V1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/numeric_opposition_model_misspecification_v1.py),
[source lock](../../../evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_lock_20261003.json),
[capture](../../../evaluation/reports/numeric_opposition_model_misspecification_v1_20261003.json),
and [analysis](../../../evaluation/reports/numeric_opposition_model_misspecification_v1_analysis_20261003.json).

## Correction — v1 query-policy analysis is diagnostic only

A runner audit found that v1 passed four-value row lists to
select_discriminating_input, which requires feature dictionaries. Consequently
its reported no-query outcomes did not measure selector behavior; the v1
analysis omitted an input-shape gate. Preserve the v1 capture only as a
synthesis/holdout diagnostic and disregard its active-query conclusions. V1.1
corrects the binding and locks the query environment shape.
