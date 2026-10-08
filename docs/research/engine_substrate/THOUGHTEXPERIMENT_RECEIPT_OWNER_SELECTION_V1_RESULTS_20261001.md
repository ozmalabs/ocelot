# Receipt owner-selection diagnostic v1 results

**Result:** receipt adoption changes an ambiguity-sensitive production helper's output in all eight fresh workers, despite exact parity of canonical edge facts.

## Gates and observation

The frozen fixture has `mt_a` at node 0, `mt_b` at node 1, and a same-name concept at node 2. Each branch adds the `mt_b` ownership edge before the `mt_a` edge. All five gates pass: eight distinct worker PIDs; source/native fingerprint stability; exactly two sorted receipt additions; identical canonical edge-key/attribute sets; and an owner choice change in every worker. Direct branch order selects `('mt_b', 1)`. The receipt sorts additions by edge key, so the primary after adoption selects `('mt_a', 0)`.

This is a demonstrated consumer-level behavioral difference, not merely a serialized-vector mismatch. The helper intentionally reduces source ownership to one `(name -> owner)` pair, so the ordering change selects which source microtheory is reported for `shared_concept`.

## Limits and next action

The fixture is deliberately ambiguity-bearing and does not prove that every task hits this helper or that the selected source changes a downstream task answer. The full-seed census finds 224 multiply-owned named groups, so the condition exists in the authored corpus. Next decide the semantic API for multiply-owned names: preserve edge mutation order in receipts, retain all owner candidates in the helper result, or declare an explicit canonical precedence. Then test harvest/source attribution on selected real corpus collisions and replay both task receipt fixtures through an order-sensitive continuation. Do not make an arbitrary sort the hidden semantic authority.

See [preregistration](THOUGHTEXPERIMENT_RECEIPT_OWNER_SELECTION_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_receipt_owner_selection_v1.py), [raw capture](../../../evaluation/reports/thoughtexperiment_receipt_owner_selection_v1_raw_20261001.json), and the [ownership census](THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_RESULTS_20261001.md).
