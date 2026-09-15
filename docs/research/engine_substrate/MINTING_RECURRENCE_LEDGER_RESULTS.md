# Minting recurrence ledger — results

## Outcome

The native ledger test passed: one `P, ∅, P` episode at threshold 2 had one predicate candidate, two evidence links, derived persistence 2, one offer at persistence/segment `(2, 2)`, terminal `minted`, and durable episode/candidate-to-axis provenance. An extra `run_rules()` pass did not change candidate, evidence, offer, or axis counts.

The held-out downstream consumer passed. `bind(ITEM,SLOT)` minted under the retained predicate-only recurrence policy and made the matching `OperationRequest` admissible/reachable. Two otherwise-isomorphic controls also reached the predicate count and minted candidate/axis: a binding-looking name with no `ResidualRelationWitness`, and `bind(ITEM,GROUP)`. Neither licensed the SLOT request. Licensing compared only `relation_head`, `arg1_role`, and `arg2_role` graph attributes.

The double-load control called `load_seeds_into(..., ["minting_recurrence_ledger"])` twice. The returned seed mapping was unchanged and each `mrl_*` rule appeared exactly once.

## Commands and results

```text
PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_minting_recurrence_ledger_migrated.py tests/capability/minting/test_recurrence_control.py -q
8 passed in 0.36s

PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track4_accommodation_gate.py
PASS: G1–G6; four recurring predicates minted at count 2; threshold and one-segment controls minted 0; duplicate refused; teacher-free.

PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track5_keystones_and_scorecard.py
PASS: K1–K5; threshold-99 control minted 0 despite surface residuals; genuine threshold-2 run minted; LLM arm remained off.

PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/ -k migrated
BLOCKED AT COLLECTION: 20 unrelated optional-dependency import errors (av, scipy, torch, vizdoom, soundfile, cv2). The new recurrence test and targeted recurrence suite passed before this broad command; no failure was attributable to this migration.
```

## Terminal outcomes

The deterministic native test records `minted`; the recurrence control also verifies `recognized_duplicate` is terminally retained and does not grow another axis. `recognized`, `recognized_transformed`, and `recognized_duplicate` are explicitly handled by `mrl_record_offer_terminal` rather than discarded.
