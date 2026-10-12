# Real-collision receipt attribution v1 results

**Result:** a receipt changes selected source attribution for a name collision drawn from the full seed corpus, with identical final canonical graph facts in all three fresh workers.

## Outcome

Each worker loaded the full corpus (731 successful seed loads, 11 failures) and deterministically selected the two-owner `CoAP` group. Its target nodes were 3901 and 5916; owner Microtheories were 3823 (`network_protocols`) and 5865 (`embedded_iot_realtime`). Both branches rewired those same two ownership rows in the same semantic final graph, issuing the higher owner ID first in Direct. Receipt output sorted the added rows by edge key. In every worker:

- Direct `_owning_mt_map()` returned `('network_protocols', 3823)`.
- After receipt adoption, `_owning_mt_map()` returned `('embedded_iot_realtime', 5865)`.
- Whole-graph canonical node/edge facts were exactly equal.

All seven preregistered gates passed: three distinct worker PIDs, deterministic two-target/two-owner fixture selection, sorted receipt additions, canonical graph equality, changed attribution, and stable source/seed fingerprints. This demonstrates a consumer-output change on actual corpus identities and a real corpus name collision, beyond the deliberately synthetic two-owner probe.

## Meaning and remaining boundary

`CoAP` is represented by two distinct Concept nodes owned by two domain Microtheories. The helper collapses both to one name key and reports whichever owner its edge traversal encounters first. Receipt adoption therefore changes the reported source domain without changing the represented facts. This is a reproducible implementation behavior; it is not evidence that the alternate domain is semantically wrong, that a user-facing answer changes, or that normal conversation events invoke this helper.

Next compare `harvest_shapes()` or another real downstream consumer across Direct and receipt states, then define source attribution for homonyms (retain a set of owners, require qualified identities, or store explicit precedence). Continue with order-sensitive task continuations and receipt regressions after the API contract is chosen.

See [preregistration](THOUGHTEXPERIMENT_REAL_COLLISION_RECEIPT_ATTRIBUTION_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_real_collision_receipt_attribution_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_real_collision_receipt_attribution_v1_raw_20261001.json).
