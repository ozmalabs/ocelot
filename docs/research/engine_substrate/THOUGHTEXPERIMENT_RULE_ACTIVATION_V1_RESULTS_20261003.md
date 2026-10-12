# Thoughtexperiment rule activation v1 results

The source-locked capture exercised the selected recurrence and conversation
repair in four fresh workers per family. All eight candidates installed under
the captured graph/rule revision and restored the intended outputs. A stale
revision after a graph mutation was rejected in every worker with no rule-store
change. Malformed candidate JSON was also rejected without rule-store change.
The independent analyzer passed 6/6 gates; source and native build hashes
remained stable.

Median activation time was 0.193 ms and median post-activation task execution
was 0.629 ms. The new PyO3 operation checks the semantic revision, parses and
validates the successor name against active-rule collisions, and replaces the
target while holding the same substrate lock. The API does not validate task
quality or authorize adoption; the harness calls it only after the candidate
was selected and held-out validated.

This closes a mechanism gap between returned proposal evidence and live rule
installation on disposable task substrates. It does not establish autonomous
adoption decisions, long-run utility, rollback after later regressions,
concurrent adoption policy, broad task transfer, or self-improvement. See the
[protocol](THOUGHTEXPERIMENT_RULE_ACTIVATION_V1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/thoughtexperiment_rule_activation_v1.py),
[source lock](../../../evaluation/substrate_capability/thoughtexperiment_rule_activation_v1_lock_20261003.json),
[capture](../../../evaluation/reports/thoughtexperiment_rule_activation_v1_20261003.json),
and [analysis](../../../evaluation/reports/thoughtexperiment_rule_activation_v1_analysis_20261003.json).
