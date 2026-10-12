# Native candidate-adequacy gate v3 results

## Outcome

All 40 fresh panels completed under a source lock. The capture passed all five run checks, and the independent analyzer passed all ten replay and integrity checks. Validation remained balanced at 16 positive and 16 negative examples, with zero and boundary examples in each class. Each panel used 3,665 held-out rows; labels were revealed only after native candidate predictions and decisions were recorded.

The graph scored each candidate by `min(TPR,TNR)` and required 0.98. Since each class has 16 examples, this criterion requires perfect validation accuracy in both classes. It selected the right supplied candidate on all 20 additive/product controls and requested help on all 10 inequality panels. On opposition, it requested help on 7/10 panels, improving on v2's 0/10 help rate. It still accepted the product candidate on 3/10 fresh panels. The candidate's mean minimum class accuracy across opposition panels was 0.8875, with a range of 0.75–1.0; its three accepted panels score 1.0 on both validation classes. The selected candidate achieves 91.16% held-out raw accuracy on those panels while representing the wrong relation.

| Task | Select | Request help | False help | False accept |
|---|---:|---:|---:|---:|
| Additive | 10/10 correct | 0/10 | 0/10 | 0/10 |
| Product | 10/10 correct | 0/10 | 0/10 | 0/10 |
| Opposition | 3/10 wrong product | 7/10 | 0/10 | 3/10 |
| Inequality | 0/10 | 10/10 | 0/10 | 0/10 |

This prospective result confirms that a class-specific criterion is more sensitive to the opposition challenge, while exposing the remaining finite-sample failure: some balanced samples contain no observed false positive for the narrower relation, so even a perfect-per-class validation threshold accepts it. The next useful mechanism is targeted acquisition of labeled examples where the selected candidate predicts true, prioritizing cases not already queried; it must be evaluated for query cost and validated on fresh held-out rows. Existing entropy-probe evidence suggests this may help when the domain contains a separating witness, but does not establish that the witness is selected or available for these relations.

## Post-hoc query-utility follow-up

An explicitly exploratory replay applies deterministic target-blind query ranking to the three opposition false accepts. Selecting only rows where the chosen candidate predicts true finds a counterexample in all three panels after one query; uniform queries find one of three at the same budget. Both have zero false help on the 20 selected positive controls. Since this reuses v3 held-out labels and only three false-accept panels, it motivates but does not confirm a four-query prospective gate. The detailed [exploratory report](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_PROBE_UTILITY_V1_EXPLORATORY_20261005.md) records the method and limits.

## Reproduction and evidence

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_v3.py --lock`, then `--run`, followed by `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_v3.py`.

- [Preregistration](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_V3_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_candidate_adequacy_v3.py)
- [Source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_v3_lock_20261005.json)
- [Capture](../../../evaluation/reports/native_candidate_adequacy_v3_20261005.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_v3.py)
- [Analysis](../../../evaluation/reports/native_candidate_adequacy_v3_analysis_20261005.json)

This is evidence about native scoring and help decisions on a finite numeric family and a supplied two-candidate menu. It does not establish natural-task error rates, autonomous invention, or general self-improvement.
