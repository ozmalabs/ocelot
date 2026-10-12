# Shape-decoding rehearsal phase profile v1 — preregistration

**Date:** 2026-10-01  
**Question:** Which measured phases dominate the shape-decoding rehearsal whose shared-page branch did not gain throughput under threaded execution?

## Design

Use the same positive `sd_mint_quantum` `dedup_identity_fix` fixture at 100k linked noise nodes. In six fresh processes (three each for scoped full-copy and scoped shared-graph-page backends), compute the baseline model outside the timed operation and call `imagine_and_check_convergence(..., _measure_phases=True, record_trace=False)` once. Capture total wall time plus the returned branch snapshot/setup, rule patch, model-after prediction, inner snapshot/readout/closure phases, and forward-look timing records. Require the same convergence/applicability oracle and exact primary immutability gates as the preceding parallel panel. No concurrency is used in this phase attribution panel.

## Gates

- Six unique fresh processes, stable source/native-binary hashes, three observations and 100k noise nodes per run.
- All runs apply `dedup_identity_fix`, are non-inert, converge, and preserve primary graph/rules/revision.
- All requested phase fields are present, nonnegative, and sum consistently with the enclosing measured operation within expected nested/overlap accounting.
- Report per-backend medians and raw per-process records.

## Interpretation limits

One synthetic task, two branch backends, three repeats per backend, one host. Instrumentation adds overhead; nested phase timings may overlap and are diagnostic rather than a calibrated cost model. This identifies where follow-up optimization could matter, not that optimizing a phase will improve throughput.
