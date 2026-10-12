# Receipt edge-order diagnostic v1 results

**Result:** semantic receipt adoption is exact on the mixed-act task, but ordered graph views do not preserve Direct mutation order. The observed difference is currently a compatibility gap, not a demonstrated task-semantic failure.

## Protocol and gates

The source-locked diagnostic replays `phase3_mixed_act_dialogue.v1` through Direct, eager-receipt, and shared-snapshot-receipt arms with eight fresh workers. Read-only sequence probes run outside timing. All inherited task, event identity, closure, terminal-state, receipt-adoption, and canonical graph gates pass. The comparison covers 80 event checkpoints per arm.

## Findings

- Edge-slab sequence differs from Direct in 72/80 checkpoints in each receipt arm. The first divergence occurs at event 1, edge position 188. Both vectors have 195 edges and the canonical edge facts agree; the local sequence differs because the receipt's added edges are applied in sorted receipt order.
- `incident_edges()` differs in 72/80 checkpoints: 392 node buckets across 14,840 node/checkpoint comparisons. At the first reported new event node, Direct reflects mutation insertion order while receipt adoption reflects a different ordering.
- Public `neighbours()` and `in_neighbours()` order agrees in all 26,968 exposed `(direction,node,type)` buckets for both receipt arms.
- The only direct production caller found for `incident_edges()` is imagination's removed-node before-image conflict check. It converts both current and expected edges to keyed maps before comparing, so that caller is order-insensitive.
- `graph_to_dict()` has many production consumers, including persistence, snapshots, and domain utilities. Current audit found no demonstrated semantic failure from vector order, but serialized order is externally observable and lacks a settled canonical-vs-mutation-order contract.
- A second consumer audit found a concrete order-sensitive helper: `domains/implication_harvester._owning_mt_map()` keeps the first `has_concept`/`has_rule` row for each concept/rule name. A source-locked eight-worker diagnostic then confirms that identical writes produce different helper outputs under Direct versus receipt adoption even though canonical edge facts match. The full seed-boot census finds 224 of 8,340 named ownership groups under multiple distinct microtheories, though no target node ID itself has multiple owners. Thus order divergence can alter a production consumer result under a condition present in the live corpus. The diagnostic does not yet show a task answer change; end-to-end continuations remain needed. See the [owner-selection result](THOUGHTEXPERIMENT_RECEIPT_OWNER_SELECTION_V1_RESULTS_20261001.md) and [ownership census](THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_RESULTS_20261001.md).

## Interpretation and follow-up

The result narrows the gap: native typed-neighbor traversal remained stable in this workload, while full graph serialization and incident-edge sequences changed. The order-sensitive owner helper makes compatibility consequential whenever ownership is ambiguous. The likely mechanism is `graph_diff` sorting added edges followed by `apply_graph_delta` appending in receipt order; `graph_to_value` then emits edge-slab iteration order. This is source-supported, not a proof that every divergence has this cause.

Before changing the implementation, specify the contract. Resolve owner ambiguity explicitly (single-owner invariant, declared precedence, or deterministic canonical tie-break) rather than relying on incidental graph order. If `graph_to_dict()` is a semantic snapshot, compare and document canonical facts rather than incidental vector order, and preserve any consumers that intentionally use order. If mutation order is contractual, receipts need an explicit stable order field and adoption must reproduce it. The source-locked controlled receipt probe has now demonstrated a helper output change with canonical graph equality. Next compare downstream harvest metadata on selected real corpus collisions, decide the contract, add an order-sensitive continuation to both task fixtures, then re-run both task oracles and receipt round-trip parity. Do not sort public output silently until compatibility impact is resolved.

## Limits

One authored task family, one host, and eight workers; not a prevalence estimate. The result says nothing about all edge mutations, concurrent adoption, or every graph consumer. Typed-neighbor coverage is broad for this captured task but not exhaustive over all graph states.

See [preregistration](THOUGHTEXPERIMENT_RECEIPT_EDGE_ORDER_DIAGNOSTIC_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_receipt_edge_order_diagnostic_v1.py), [raw capture](../../../evaluation/reports/thoughtexperiment_receipt_edge_order_diagnostic_v1_raw_20261001.json), and [analysis](../../../evaluation/reports/thoughtexperiment_receipt_edge_order_diagnostic_v1_analysis_20261001.json).
