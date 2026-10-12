# Accepted proposition polar-conflict v1 preregistration

Date: 2026-10-03  
Runner: [`accepted_proposition_polar_conflict_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_polar_conflict_v1.py)  
Lock: [`accepted_proposition_polar_conflict_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_polar_conflict_v1_lock_20261003.json)

## Question

Does the native accepted-proposition polar-answer path abstain when two accepted claims contradict each other, and does the selected result depend on proposition insertion order?

## Conditions

Run five conditions, with three fresh graphs per condition. Each graph loads the communication-arbitration rules and receives one fixed `open(gate)` polar query:

- `unique_affirmed`: one accepted affirmed proposition; expected exactly one `yes` plan.
- `unique_negated`: one accepted negated proposition; expected exactly one `no` plan.
- `conflict_affirmed_first`: accepted affirmed then accepted negated claim; expected no answer plan (abstention/conflict required).
- `conflict_negated_first`: same contradictory claims in reverse insertion order; expected no answer plan.
- `retracted_conflict`: accepted affirmative plus retracted negative claim; expected exactly one `yes` plan.

Record all selected plan values and the proposition polarity/status/evidence ID attached to each support node. The integrity gate requires complete rows and stable locked source/runtime inputs. The behavior gate separately compares outputs with the oracle; an incorrect non-abstaining conflict answer is reported as a capability failure, not an integrity failure.

## Limits

The harness supplies a fixed parse and explicit claim graph. It does not test natural-language extraction, lifecycle-authenticated uptake, source-event/speaker attribution, ambiguity across different predicates, wh-query retrieval, or response rendering. Three repetitions characterize this authored topology only; they are not a statistical estimate over natural conversations.
