# Generated experiment-judge semantics v1 results

**Run:** 2026-09-28; two unique fresh full-seed workers.  
**Protocol:** [preregistration](SUBSTRATE_GENERATED_EXPERIMENT_JUDGE_SEMANTICS_V1_PREREG_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/generated_experiment_judge_semantics_v1_20260928.json), [independent analysis](../../../evaluation/reports/generated_experiment_judge_semantics_v1_analysis_20260928.json), [source/input lock](../../../evaluation/substrate_capability/generated_experiment_judge_semantics_v1_lock_20260928.json), [runner](../../../scripts/substrate_generated_experiment_judge_semantics_v1.py), [analyzer](../../../scripts/analyze_substrate_generated_experiment_judge_semantics_v1.py).

## Result

All 16 independent integrity and semantic gates pass. Both workers minted and grounded the same concern from the same preconstructed instruction, installed the expected active rule `judge_experiment_outcome_steer_compare_where_the_two_letters_differ_and_judge_the_trial`, and made zero teacher calls. The generated native rule matches all three completed synthetic cases against the independently computed sign oracle and leaves the nonterminal control unchanged.

| Case | Expected | Observed (both workers) | Native progress | Settle wall time per worker |
|---|---|---|---:|---:|
| Score 3 / 3 frames, `done` | supported | supported | 1 | 5.74–5.79 ms |
| Score -2 / 2 frames, `done` | refuted | refuted | 1 | 4.39–4.70 ms |
| Score 0 / 3 frames, `done` | inconclusive | inconclusive | 1 | 4.07–4.87 ms |
| Score 3 / 3 frames, `running` | no verdict | no verdict; no `analysed` edge | 0 | 3.67–4.22 ms |

## Interpretation and limits

This establishes execution of the generated judge rule on its stated score-sign semantics, including its terminal-status guard and one-shot graph effect, in two fresh full-seed workers. It does **not** show that the generated concern is semantically correct for the phrase “where the letters differ,” or that a real child experiment's score is trustworthy. The cases were synthetic and constructed directly in the graph; there was no visual trial, learned hypothesis, child dispatch, or adoption decision. The next gate should connect the generated concern to a real contrastive task with a blinded independent oracle and verified run provenance.
