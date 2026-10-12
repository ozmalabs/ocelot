# Term access-dependency audit v1 results

Date: 2026-09-28

## Source changes

The source review confirmed four dependency shapes. `ParetoDominates` reads two edge resources (`value_edge`, `measure_edge`) and three node-attribute resources (`dimension_key`, `verified_key`, `signed_value_key`); `collect_term_reads()` now records those finite keys and walks its child Terms. ShapeDecode-family helpers that enumerate codebooks, cues, registries, mechanisms, or observation populations are wildcard readers. `Join`, `ProgEval`, `Call`, `Holds`, and `UseTool` can cross the explicit child-Term boundary through graph rendering, Node-backed program decoding, runtime-derived bodies, concept lookup, or reentrant handlers; these are also wildcard readers.

This review is targeted, not exhaustive over the 237 `TermNode` variants. It does not make external file reads graph dependencies, nor prove all native helpers have precise access reports.

## Reproducible replay

The rebuilt extension and three-worker replay pass all six gates: fresh workers, stable source locks, task/semantic parity to the v1.2 capture, exact corrected trace parity across workers, zero trace drops/count-conservation, and the cross-substrate isolation control. Independent analysis confirms zero unexplained static resource mismatches and no observed concrete dependency pair outside the static projection.

Conservative declarations add a small operation-count increment on this workload, identically in all three workers:

| Prompt | Rule enumerations | Candidate tests | Term evaluations |
|---|---:|---:|---:|
| `report your organisation` | +191 (+0.81%) | +38 (+0.06%) | +124 (+0.02%) |
| `describe who you are` | +114 (+0.95%) | +34 (+0.10%) | +104 (+0.03%) |

Fifteen observed rules become wildcard readers across the two prompts. These are deterministic counts, not wall-time results; this small authored workload does not estimate the cost on other domains or larger graphs. Previously registered per-rule counter equations remain uncalibrated and are not promoted to gates.

## Next gate

The initial 237-variant enum/evaluator/children crosswalk is complete in [coverage v1](SUBSTRATE_TERM_ACCESS_DEPENDENCY_COVERAGE_V1_RESULTS_20260928.md). It explicitly leaves 207 variants without helper-level review. Next extend it to evaluator-to-helper call paths, finite keys, wildcard decisions, trace sites, and external dependencies; use that map to select positive/negative fixtures. Then measure conservative-reader cost across task families and scales before making frame-local polynomial-cost claims.

Artifacts: [preregistration](SUBSTRATE_TERM_ACCESS_DEPENDENCY_AUDIT_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_term_access_dependency_audit_v1.py), [independent analyzer](../../../scripts/analyze_substrate_term_access_dependency_audit_v1.py), [lock](../../../evaluation/substrate_capability/term_access_dependency_audit_v1_lock_20260928.json), [raw](../../../evaluation/reports/term_access_dependency_audit_v1_20260928.json), [analysis](../../../evaluation/reports/term_access_dependency_audit_v1_analysis_20260928.json).
