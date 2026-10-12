# Overlapping rule conflict and cycle probe v1 — results

All preregistered gates pass in three fresh workers. Two rules share the same trigger and stable true predicate but write conflicting values (`1` and `2`) to one attribute using `set_attr_if_different`.

| Insertion order | Cycle detection | Termination | Progress steps | Final value | Callback calls |
|---|---:|---|---:|---:|---:|
| A then B | off | progress budget reached | 12 | 2 | 12 |
| A then B | on | repeated graph state | 4 | 2 | 4 |
| B then A | off | progress budget reached | 12 | 1 | 12 |
| B then A | on | repeated graph state | 4 | 1 | 4 |

The rules do not converge to a fixed point. Each completed pass rewrites the value first to one result and then to the other; reversing insertion order reverses the final value. With cycle detection, the engine reports a repeated graph state after two passes. Without it, the run reaches the configured progress budget. The cycle detector saves work in this fixture but does not make the conflicting rule set confluent or valid.

This establishes a concrete critical-pair/termination gap: the engine has a bounded-run safety mechanism, but no general conflict resolution or automatic compensation ordering. The probe uses a pure stable callback and one binding. Cycle detection fingerprints graph state, so it does not establish safety when hidden external state or side channels change independently.

Artifacts: [preregistration](SUBSTRATE_OVERLAPPING_RULE_CONFLICT_PROBE_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_overlapping_rule_conflict_probe_v1.py), [analyzer](../../../scripts/analyze_overlapping_rule_conflict_probe_v1.py), [raw capture](../../../evaluation/reports/overlapping_rule_conflict_probe_v1_20260928.json), [lock](../../../evaluation/substrate_capability/overlapping_rule_conflict_probe_v1_lock_20260928.json), [analysis](../../../evaluation/reports/overlapping_rule_conflict_probe_v1_analysis_20260928.json).
