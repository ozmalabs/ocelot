# Thoughtexperiment revision-token audit (2026-10-01)

## Finding

The revision is an O(1) tuple: `(TypedGraph::mutation_version, gamma_epoch, rules.len())`. It is a tracked revision, not a content digest. To make that contract reliable for downstream Rust callers, the semantic stores that participate in branch/adoption semantics (`rules`, `checker`, `terms`, `concepts`, and `interner`) are now crate-private. Public callers receive read-only accessors and tracked mutation methods. `TypedGraph` remains mutable through its writer API, whose mutations advance its version.

The earlier `set_rule_area` omission is fixed. Effective changes to rule scheduling metadata, concepts, active shape target, terms, rules, and grammar productions advance Γ. PyO3 production insertion now goes through the same tracked Substrate method. Append-only symbol interning does not change the meaning of existing symbols; access to truncate or rewrite the interner is not exposed.

## Mutation-path contract

| Mutation path | Token effect | Assessment |
|---|---|---|
| `TypedGraph` writer | Graph mutation version advances | Covered, including direct callers using supported graph APIs |
| Add/remove/edit rule and rule area | Γ epoch advances on effective mutation | Covered through Substrate methods |
| Add grammar production, with or without graph mirror | Γ epoch advances | Covered through Substrate methods and PyO3 |
| Add term / define concept / change active shape target | Γ epoch advances on effective mutation | Covered through Substrate methods |
| Semantic-store fields | Crate-private; public read-only accessors | Downstream direct field bypass closed |
| Temporary rule activation masks | Restored before exclusive mutable call returns | Transient execution state; no safe concurrent observer during mutation |

This closes downstream API bypasses. Internal crate code remains trusted to mutate through tracked methods when a mutation can affect branch semantics; future internal direct writes require audit.

## Cost measurement

`experiment_revision_fingerprint_probe` compares the O(1) tracked token with a full semantic-store serialization and digest (31 repetitions; median; stores and graph each sized equally). The tracked token remains approximately 0.00002–0.00003 ms across sizes. Full fingerprint medians are 0.0092 ms at 0 entries, 3.398 ms at 100, 34.979 ms at 1,000, and 179.603 ms at 5,000 entries per store. This is a strong reason to retain tracked revisions rather than hash semantic state during branch capture/adoption.

The same source-locked probe confirms that adding a term, rule, production, and concept through their supported methods changes the token in all four cases. `cargo check -p substrate-rs` succeeds. The fingerprint probe is diagnostic evidence, not a cryptographic content-addressing guarantee or a substitute for API discipline.

## Remaining boundary

This revision covers the guarded graph/rule/grammar state used by the residual-adoption path. It does not fingerprint caches, telemetry, arbitrary external effects, or every mutable execution subsystem. Edge-attribute receipts and journal before-images have since been added and source-locked at [the follow-up probe](../../../evaluation/substrate_capability/thoughtexperiment_edge_attr_delta_v1.py); assumption-preserving adoption and concurrent ownership remain open. The adoption panel's 9/9 gates remain evidence for the exercised graph receipts, not a general merge guarantee.
