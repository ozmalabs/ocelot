# CEGIS consecutive-agreement stopping replay v1 results

Date: 2026-10-03

## Results

The retrospective trace replay examined six predeclared consecutive-agreement thresholds on the five frozen XOR panels. A one-agreement rule stopped after a median of one added label and saved 52 of 60 possible added labels, but all five returned hypotheses were wrong on the fractional holdout. Thresholds of two, three, and four agreements each left two false hypotheses out of five. Five agreements left one false hypothesis. Six agreements yielded five exact holdout hypotheses and saved only four labels overall; two runs still exhausted the full 12-label trace. The full per-worker outcomes and hashes are in the [replay artifact](../../../evaluation/reports/numeric_opposition_cegis_stop_rule_v1_20261003.json).

This does not establish six agreements as a reliable stopping rule. The replay is retrospective, has five workers from one synthetic target, and the thresholds were compared against the same holdout set. It shows a sharp budget/reliability tradeoff on these traces: aggressive stopping saved work but accepted false models, while the only threshold perfect on this tiny sample saved little. Holdout scores were not used by the policy; they only adjudicate the replay after the fact.

## Artifacts

- [Preregistration](NUMERIC_OPPOSITION_CEGIS_STOP_RULE_V1_PREREG_20261003.md)
- [Replay analyzer](../../../evaluation/substrate_capability/analyze_numeric_opposition_cegis_stop_rule_v1.py)
- [Frozen source capture](NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_RESULTS_20261003.md)
