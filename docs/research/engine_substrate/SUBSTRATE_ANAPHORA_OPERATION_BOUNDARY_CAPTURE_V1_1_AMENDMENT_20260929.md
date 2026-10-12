# Anaphora operation-boundary capture v1.1 amendment

Date: 2026-09-29, before the v1.1 lock and capture.

## V1 harness failure

The locked v1 attempt is retained at
`evaluation/reports/anaphora_operation_boundary_capture_v1_raw_20260929.json`.
All ten workers failed before producing a case row because the projection
helper passed serialized integer node IDs to `WorldAdapter.neighbours` and
`intent_of`, whose native API requires `NodeID`. V1 contributes no semantic,
structural, or timing result. The error is a harness/API-boundary defect; the
task suite and structural ownership rule remain unchanged.

## Correction

V1.1 retains native message handles for adapter calls and converts to stable
integer IDs only for serialized records. All workload text, message ownership,
global-type exclusion, partition arms, trace scope, and gates remain as frozen
in v1. Use versioned runner/analyzer/lock/raw/analysis paths. Freeze the new
protocol and complete source/build lock before capture. No v1 raw file is
overwritten or reclassified.
