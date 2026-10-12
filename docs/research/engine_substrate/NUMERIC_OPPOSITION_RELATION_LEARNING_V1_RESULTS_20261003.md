# Numeric opposition relation learning — results

Date: 2026-10-03

## Result

The source-locked run completed five independent synthesis workers. All five
found a size-ordered hypothesis that fits all 16 training labels. Independent
analysis re-evaluated each frozen AST over the full 1,296-case held-out
fractional grid. Only one of five generalized exactly. Four workers selected
shorter hypotheses using only the x components; each matched all 36 held-out
positive cases but falsely labeled 180 of 1,260 negative cases as opposite.
One worker found the full two-axis predicate and scored 36/36 positives and
1,260/1,260 negatives correctly.

The exact worker explored 9,862 candidate terms and retained 642 distinct
training behaviors; it took 1.192 s
wall / 1.192 s CPU. The four underfit workers stopped after 59–705 terms in
5–68 ms. Median cost is 5.5 ms, but this hides the roughly 220× increase for
the one panel whose data forced the conjunction. The synthesizer is
size-ordered and returns the first fitting hypothesis, so the result reflects
training identifiability and Occam order together.

## Interpretation

This is direct evidence that `domains.generator.synthesize` can infer the
two-axis numeric relation from labeled examples without receiving its formula,
and that the resulting Term generalizes exactly on one large, disjoint
fractional grid when training examples distinguish both dimensions. It is
also a negative sample-sufficiency result: four random balanced panels did
not include a negative example that separated an x-only rule from the true
two-axis relation. The held-out set was not used to resynthesize.

The benchmark is one synthetic relation, one fixed grammar, five training
draws, and one numeric domain. Labels are evaluator supplied; the grammar
already contains `Neg`, `Eq`, and `And`. This does not demonstrate autonomous
task discovery, unsupervised relation learning, new primitive invention, or
integration of the learned relation into Thoughtexperiment cue grounding. The
initial analyzer had an import-path error; the corrected independent
reanalysis passes measurement-integrity checks and reports the capability
failure honestly.

## Artifacts

- [Preregistration](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_PREREG_20261003.md) and [analysis amendment](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_ANALYSIS_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_numeric_opposition_relation_learning_v1.py), [initial analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_relation_learning_v1.py), and [corrected independent analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_relation_learning_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/numeric_opposition_relation_learning_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/numeric_opposition_relation_learning_v1_20261003.json) and [corrected analysis](../../../evaluation/reports/numeric_opposition_relation_learning_v1_1_analysis_20261003.json)
