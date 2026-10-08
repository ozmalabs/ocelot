# Term external-dependency predicate probe v1.2 results

Date: 2026-09-28

## Results

Three fresh workers reproduce all five preregistered cells. The independent analyzer passes 11 gates, including current source/native lock, child stdout/stderr hashes, unique worker PIDs, exact per-cell agreement, callback/fire/trace conservation, and zero dropped trace events.

| Predicate form | Callback returns | Calls / trace dispatches | Progress | Final marker |
|---|---|---:|---:|---|
| Direct `UseTool` returning true | true, true | 2 | 1 | written |
| `And(false, UseTool)` | none | 0 | 0 | absent |
| `And(UseTool, false)` | true | 1 | 0 | absent |
| Two rules, each with direct `UseTool` | two true per RuleUID | 4 total, 2 each | 2 | both written |
| Stateful direct predicate (true, then false) | true, false | 2 | 1 | written |

All rules conservatively declare `reads_any=true`. The short-circuit controls distinguish reachability: a false first operand suppresses the callback, while a false second operand rejects the candidate after the callback has already run. In the stateful cell, one candidate invokes the predicate twice with different answers; the first true result commits the marker, and the second false result occurs during the no-progress settle pass. The rule engine reports a fixed point even though the callback's external state has changed its answer within the same settle.

These results confirm the behavior of the frozen fixtures, not a general callback policy. They show that `UseTool` can execute for a candidate that is ultimately rejected, that repeated predicate calls can return inconsistent answers, and that multiple rules multiply callback work by RuleUID. Using effectful or state-dependent callbacks in match predicates therefore weakens ordinary fixed-point and replay assumptions.

## Capture amendment

An initial analyzer defect inverted a marker-absence check. Its raw capture was overwritten before it could be archived; the failure and custody lapse are disclosed in the [amendment](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_AMENDMENT_20260928.md). The corrected analyzer and fresh capture are the only evidence used below.

## Reproduction

[Preregistration](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_PREREG_20260928.md), [amendment](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_AMENDMENT_20260928.md), [lock](../../../evaluation/substrate_capability/term_external_dependency_probe_v1_2_lock_20260928.json), [runner](../../../scripts/substrate_term_external_dependency_probe_v1_2.py), [raw capture](../../../evaluation/reports/term_external_dependency_probe_v1_2_20260928.json), [independent analyzer](../../../scripts/analyze_term_external_dependency_probe_v1_2.py), [analysis](../../../evaluation/reports/term_external_dependency_probe_v1_2_analysis_20260928.json).
