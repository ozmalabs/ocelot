# Distinct-Term equivalence-class positive control v1 results

## Result

All five frozen opposition panels pass. After one labeled query and one probe
coverage expansion, the policy returns exactly two structurally distinct
Terms: `ax == -ex` and `-ax == ex`. The declared same-sign control `ax == ex`
is excluded in every panel. Returned class sizes are two distinct canonical
Term trees, rather than multiple IDs for one tree. The policy's covered sets
contain 124–127 probes per panel.

An independent analyzer replays every survivor transition and label, checks
that the two class members agree on the covered probes, and rescans each
member on the registered 6,560-case fractional holdout. It also evaluates a
separate set of 3,024 balanced positive/negative cases per member, including
extreme finite values, signed zero, and subnormal/large magnitudes. All
members match the opposition relation on both evaluation domains in all five
panels. The same-sign control is not exact.

## Interpretation and limits

This is a controlled positive control showing that the policy and graph-level
class receipt path can represent a class of structurally distinct Terms
without confusing it with repeated candidate IDs. The two expressions are
hand-supplied algebraic variants of one simple relation; the test does not
measure their discovery, broad semantic deduplication, natural-task frequency,
or open-ended induction. The wider check is finite and task-specific.

## Reproduction artifacts

- [Preregistration](DISTINCT_TERM_EQUIVALENCE_CLASS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/distinct_term_equivalence_class_v1.py)
- [Source lock](../../../evaluation/substrate_capability/distinct_term_equivalence_class_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/distinct_term_equivalence_class_v1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_distinct_term_equivalence_class_v1.py)
- [Analysis](../../../evaluation/reports/distinct_term_equivalence_class_v1_analysis_20261004.json)
