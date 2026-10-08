# Thoughtexperiment tracked mutation source audit v2

The current-source scanner passes its fixed inventory of 23 public `TypedGraph` methods taking `&mut self`: 12 semantic graph writers, one revision-tracked scope transition, one derived-index declaration, and nine observer/journal controls. All semantic writers contain their expected revision and before-image logging paths, directly or through tracked helpers. The audited `graph.rs` SHA-256 is `ae30e2398bb03ccb7ad09c50dca4947add06623ff7c0d1f65955f31f1f76126d`.

This refresh supersedes the stale source hash reported in v1 for current-source claims. It is static source-wiring evidence only: it does not execute every mutation route, establish completeness beyond the enumerated public API, cover unsafe or interior mutation, or prove concurrency safety. The 26-case journal matrix supplies finite dynamic coverage for selected single-threaded operations; its own stated limits remain in force. Receipt validation should continue to be paired with exact full-state audits and concurrency controls.

## Artifacts

- [Scanner](../../../evaluation/substrate_capability/audit_thoughtexperiment_tracked_mutations_v2.py)
- [Machine-readable capture](../../../evaluation/reports/thoughtexperiment_tracked_mutations_v2_20261004.json)
- [Journal matrix v1.6 results](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_6_RESULTS_20261004.md)
- [Revision/receipt validation results](THOUGHTEXPERIMENT_REVISION_RECEIPT_VALIDATION_V1_RESULTS_20261004.md)
