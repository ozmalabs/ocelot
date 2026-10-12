# Join work attribution v1.3 — provenance correction and confirmation

**Status: registered before v1.3 capture.** The v1.2 counters and exact
cross-process replication are preserved, but source review found that the raw
capture omitted a direct digest for `runners/dsl/src/scale_audit.rs`, which
defines the audited counters. Treat v1.2 as diagnostic, not the final
source-complete record.

## Corrected capture

- Preserve the same 42 configurations, 3 replicates per cell, deterministic
  schedule, audit toggling, counter reset, output graph oracle, and snapshots.
- Hash `scale_audit.rs`, the native matching/effect sources, the finite-key
  analyzer, the runner, the locked protocol/amendment, and native binary.
- Run the same versioned runner in two fresh processes to separate raw outputs.
- Independently verify current hashes, per-case graph/match parity against the
  uninstrumented topology capture, counter conservation, per-rule/global
  equality, exact cross-process integer counts, and fixed-point/bound checks.
- Preserve v1.2 captures and analysis as prior diagnostic evidence; do not merge
  their counts with v1.3.

## Claim boundary

The final result is audit-on integer work attribution for the registered
positive rule family and authored topologies. No audit-on wall time is used, and
no native candidate count is equated with the independent complete-path count.
