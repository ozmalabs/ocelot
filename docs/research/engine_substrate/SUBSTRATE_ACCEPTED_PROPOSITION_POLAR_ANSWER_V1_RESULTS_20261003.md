# Accepted proposition polar-answer v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_ACCEPTED_PROPOSITION_POLAR_ANSWER_V1_PREREG_20261003.md)  
Runner: [`accepted_proposition_polar_answer_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_polar_answer_v1.py)  
Lock: [`accepted_proposition_polar_answer_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_polar_answer_v1_lock_20261003.json)  
Raw capture: [`accepted_proposition_polar_answer_v1_raw_20261003.json`](../../../evaluation/reports/accepted_proposition_polar_answer_v1_raw_20261003.json)

## Result

All 21 graph instances passed the exact rule oracle and all nine source/runtime hashes matched before and after execution. Nine positive cases emitted exactly one expected plan, with a single support node linked to the matching proposition and evidence. Twelve negative cases emitted no support and no answer plan.

| Condition | Result | Native plan |
|---|---:|---|
| Accepted affirmed claim + affirmed polar query | 3/3 | `yes` |
| Accepted negated claim + affirmed polar query | 3/3 | `no` |
| Accepted affirmed claim + negated polar query | 3/3 | `no` |
| Proposed claim | 0/3 plans | none |
| Suspended claim | 0/3 plans | none |
| Predicate mismatch | 0/3 plans | none |
| Missing evidence node | 0/3 plans | none |

This measures a real but narrow native proposition-to-polar-answer capability. The harness explicitly supplied the interpretation, goal, proposition, and `commitment_status`; it did not parse language or execute response rendering. Fifteen accepted-status rows had no `uptake_applied` value, including the nine positive cases, and still produced plans. No `Proposition.originated_in` source-event edge or speaker attribution was supplied or required by these rules. Thus, the path checks the accepted status attribute and evidence-node presence, but does not establish that native uptake caused acceptance or that the proposition has authenticated discourse lineage.

The panel covers a unique unary `open(gate)` claim. It does not measure multiple matching or conflicting propositions, binary propositions, arbitrary wh-questions, episodic memory, or natural-language extraction. The separate live test fixture asserts a user-facing named-polar route; this panel measures only its underlying graph-rule stage.

## Next gate

Run a live-route, source-attributed panel with one unique claim, absent/proposed claim, challenged/retracted claim, contradictory claims, and wrong-source/context controls. Require `uptake_applied=accept`, an originating discourse event, evidence link, and explicit speaker handling before treating this path as trusted recall. Compare the existing polar-answer route with the still-unmeasured value/wh-query route; do not count a parser `know` target as a retrieval result.
