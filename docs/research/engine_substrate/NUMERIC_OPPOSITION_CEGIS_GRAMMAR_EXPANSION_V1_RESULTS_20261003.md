# Counterexample-triggered grammar expansion v1 results

Date: 2026-10-03

## Sequence and outcomes

Three source-locked diagnostic runs examined whether a bounded CEGIS learner can recover from the false singletons seen on the out-of-grammar XOR target.

- **V1:** after the first reserve counterexample, add the predeclared `Not` operator and resynthesize at size cap 9. All five expansions fit their revealed labels, but none were exact on the fractional holdout. Inspection showed the direct XOR representation needs size 10.
- **V1.1:** raise only the size cap to 11. The first expanded candidate still failed to generalize in all five workers: the policy stopped after one expanded synthesis, with no further counterexample loop.
- **V1.2:** continue querying a frozen reserve pool after expansion, and resynthesize each time the current candidate disagrees with the oracle. Independent replay passed. All five final candidates were exact on the 1,296-case holdout. Post-capture analysis found the first holdout-exact candidate after 4, 4, 6, 8, and 9 additional labels (median 6). The policy nevertheless used its full 12-label additional budget in every worker because holdout correctness was hidden from it; every run ended at `query_budget_exhausted`.

This is evidence that counterexample-triggered resynthesis can repair this specific false-singleton failure when a human supplies a useful operator expansion (`Not`) and a sufficient size cap. It also exposes an unresolved stopping problem: the evaluator can identify the first exact candidate retrospectively, but the learner does not know that it has become exact and keeps spending labels. The grammar expansion, target family, oracle, size change, and escalation rule are all authored. No primitive was invented autonomously, and no unrelated family was tested.

## V1.2 artifacts

- [Amendment](NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_2_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_numeric_opposition_cegis_grammar_expansion_v1_2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_cegis_grammar_expansion_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_2_lock_20261003.json)
- [Capture](../../../evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_20261003.json)
- [Analysis](../../../evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_analysis_20261003.json)

Earlier [v1 protocol and capture](../../../evaluation/substrate_capability/measure_numeric_opposition_cegis_grammar_expansion_v1.py), [v1.1 amendment](NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_1_AMENDMENT_20261003.md), and [model-adequacy baseline](NUMERIC_OPPOSITION_CEGIS_MODEL_ADEQUACY_V1_RESULTS_20261003.md) are retained for the failure sequence.
