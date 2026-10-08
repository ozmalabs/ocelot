# Ownership-order census v1 results

**Result:** name-level ownership collisions are common in the authored full seed corpus, although duplicate ownership of one target node ID is absent. The current first-edge helper therefore resolves real repeated names using whichever ownership edge appears first.

## Capture

The frozen full-boot census loaded 731 seeds, with 11 reported failures, and produced 24,891 nodes and 11,129 edges. It found 8,594 `has_concept`/`has_rule` edges over 8,594 distinct `(edge type,target node ID)` pairs: no target node ID has multiple owners. Grouping the same rows by `(edge type,target node name)` yields 8,340 named groups, of which **224 have more than one distinct source microtheory**. Four groups contain duplicate same-owner rows. Source fingerprints were stable before and after the census.

Examples include `agent` under `enact`, `communication`, and `thematic_roles`; `substrate_rs_canonical_instance` under four microtheories; `backpropagation` under `machine_learning` and `computational_neuroscience`; and homonyms such as `CoAP` under `network_protocols` and `embedded_iot_realtime`. These may be legitimate homonyms rather than conflicting ownership of one node. However, `_owning_mt_map()` keys by name and keeps only the first row, so it discards this distinction and gives the choice operational meaning.

## Interpretation and next gate

This establishes a live-corpus exposure to edge-order-sensitive source selection, not the frequency of such cases in natural tasks or proof that receipt adoption already changes a task result. Since duplicate target IDs are absent, the primary issue is name collision and lossy name-keyed source attribution, not multiple `has_concept` edges attached to a single concept node. The helper's docstring calls this the first owning Mt but the current graph has no explicit precedence relation.

Next evaluate a targeted transfer on a full-boot-derived fixture containing a selected ambiguous name: create an isolated branch that removes/re-adds or adds ownership rows in a different order, adopt its receipt, and compare `_owning_mt_map()` plus downstream harvested source metadata across Direct, eager, and shared-snapshot paths. Then decide whether the contract should preserve ownership-edge history, return all candidate owners, or define explicit canonical precedence. Any semantic change must retain legitimate cross-domain homonyms rather than collapse them silently.

## Limits

The full boot reports 11 failed seeds; the capture is one authored corpus snapshot on one host. The deterministic example list is capped at 25. It is a descriptive structural census and not a task-performance or scaling result.

See [preregistration](THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_ownership_order_census_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_ownership_order_census_v1_raw_20261001.json).
