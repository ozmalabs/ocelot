# CEGIS model adequacy and transfer v1 results

Date: 2026-10-03

## Outcome

The paired, source-locked study completed five workers for each target, and the independent analyzer passed all checks. For the in-grammar componentwise-opposition control, all five runs reached exact singletons on the disjoint fractional holdout after 2–3 oracle labels (median 2). For the out-of-grammar XOR-of-axis-oppositions target, four of five runs stopped at a singleton that was inexact on the holdout; the remaining run exhausted the bounded candidate space after six oracle labels and returned no fit. The XOR arm used 3–5 labels among terminating workers (median 4) and took a median 8.61 seconds per synthesis round. All searches reached the declared size cap; the no-fit worker exhausted the returned version space rather than timing out.

The result isolates an important boundary: counterexample labels can shrink and rebuild a version space, but singleton status is not evidence that the grammar contains the target. In this panel, the system reported four confident wrong answers for the unsupported relation. Empty-space detection occurred once, but only after exhausting its fixed grammar and search limits. No task identity, formula, or holdout labels were given to the learner; target labels came from the outer local oracle.

## Scope and limits

This is a paired diagnostic for one small numeric relation and one related unsupported target, with five shared query pools and a fixed `Neg`/`Eq`/`And` grammar. It does not estimate adequacy detection across unrelated tasks, and the target/grammar pair is authored. Holdout correctness is evaluator-only. The analyzer checks captured candidates against all revealed labels, replays the maximum-entropy query, verifies oracle labels, and independently rescales final terms; it does not reconstruct the synthesizer's complete candidate sets with a separate enumerator.

## Artifacts

- [Preregistration](NUMERIC_OPPOSITION_CEGIS_MODEL_ADEQUACY_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_numeric_opposition_cegis_adequacy_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_cegis_adequacy_v1.py)
- [Source lock](../../../evaluation/substrate_capability/numeric_opposition_cegis_adequacy_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/numeric_opposition_cegis_adequacy_v1_20261003.json)
- [Analysis](../../../evaluation/reports/numeric_opposition_cegis_adequacy_v1_analysis_20261003.json)
