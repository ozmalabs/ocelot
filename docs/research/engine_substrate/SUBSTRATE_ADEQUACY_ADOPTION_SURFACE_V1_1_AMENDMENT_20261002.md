# Strict code-write adoption surface v1.1 — amendment

Date: 2026-10-02

V1's source-locked 12-process capture is preserved as diagnostic at `evaluation/reports/substrate_adequacy_adoption_surface_v1_diagnostic_raw_20261002.json`. V1 correctly observed that direct `code_write_growth` calls refused under strict policy, but its `curriculum_legacy_call` measured the before-state before `load_all_seeds()`. Seed setup therefore appeared as 27 adopted code shapes per worker, masking the intended lesson-ingestion outcome.

V1.1 retains the four conditions, three fresh workers per condition, source/native/seed/fixture lock, and all outcome definitions. It moves the curriculum before-state to after seed loading and immediately before lesson ingestion. Success requires exactly one new typed code-write shape for valid signed evidence, and zero new typed code-write shapes for tampered evidence, direct receipt-only teaching, and published-curriculum teaching without evidence. The tampered arm must retain an `accepted` internal receipt.

This correction is based on the observed V1 lifecycle and is recorded before the rerun. The scope remains one host and one authored scalar task family. The panel checks the public routes that call `teach_write_shape_from_example`; low-level direct `teach()` and non-strict agents remain outside strict-policy enforcement.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adoption_surface_v1_1.py
```
