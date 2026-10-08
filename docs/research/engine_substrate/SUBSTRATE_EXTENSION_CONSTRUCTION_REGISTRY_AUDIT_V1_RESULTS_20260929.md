# Extension construction registry audit v1 results (2026-09-29)

An AST-based source audit of `domains/substrate_extension.py` found one string-valued construction selected by `_select_construction`: `spectral_value`. The `build_primitive` route constructs the forward log-magnitude term and its nonselective negative-control twin. It contains no second buildable computational primitive family to use for a cross-family semantic-verification replication.

This is a narrow source inventory, not a runtime census of every capability-acquisition path in the substrate. In particular, it does not cover rule minting, GenInfer/MetaShape learning, or host-side builders. It constrains what the next extension semantic-verification gate can claim: another family must first be added to this registry or independently located and audited elsewhere.

- Audit script: [`audit_extension_construction_registry.py`](../../../evaluation/substrate_capability/audit_extension_construction_registry.py)
- Source-locked output (source SHA-256 included): [`extension_construction_registry_v1.json`](../../../evaluation/reports/extension_construction_registry_v1.json)

