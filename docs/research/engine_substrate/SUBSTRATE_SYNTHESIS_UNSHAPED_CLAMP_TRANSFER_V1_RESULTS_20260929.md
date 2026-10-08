# Unshaped clamp synthesis transfer v1 — results

**Date:** 2026-09-29. **Question:** can the ordinary program-synthesis route acquire and transfer a simple clamp composition without either registered threshold operator-shape selector?

## Protocol and integrity

Two clamp functions use `min(max(x, lower), upper)`: bounds `[0,5]` and `[-2,4]`. Each has six training rows and six disjoint heldout inputs. Five fresh processes ran per task through the standard `ensure_program_synthesis` → `ingest_spec` → `pump` path, with no `ps_enum_ops` injection. The independent analyzer passes all nine capture-integrity gates and both transfer gates: exact lock/schedule, complete unique workers, current source/native hashes, stable workers, Rung 3 terminal outcomes, no selector shape or explicit operator list, and full independent holdout readback for each accepted Program.

This is the preregistered task-family probe, not the preceding one-worker pilot ([protocol](SUBSTRATE_SYNTHESIS_UNSHAPED_CLAMP_TRANSFER_V1_PREREG_20260929.md)).

## Results

| Task | Accepted / exact transfer | Median candidates | Median pump wall time | Median pump CPU time | Peak RSS |
|---|---:|---:|---:|---:|---:|
| Clamp `[0,5]` | 5/5; 30/30 points | 8,230 | 34.2 ms | 36.7 ms | 43.8 MB |
| Clamp `[-2,4]` | 5/5; 30/30 points | 6,663 | 27.0 ms | 29.5 ms | 43.8 MB |

All ten programs use the expected two-operation form, `Min(upper, Max(input, lower))`. Neither task triggers a registered operator shape or supplies an explicit grammar. No accepted false generalization was observed across these 60 holdout predictions. Full per-worker outputs, candidate work, and timing ranges are in the [analysis](../../../evaluation/reports/synthesis_unshaped_clamp_transfer_v1_20260929_analysis.json) and [raw capture](../../../evaluation/reports/synthesis_unshaped_clamp_transfer_v1_20260929_raw.jsonl); the [lock](../../../evaluation/substrate_capability/synthesis_unshaped_clamp_transfer_v1_20260929_lock.json) records source, seed, native, task, and runner provenance.

## Interpretation and limits

This adds positive evidence beyond the two explicitly shaped threshold grammars: the production route can solve these small scalar clamp tasks with its default numeric grammar, return graph-resident executable Programs, and transfer them to the registered holdouts at modest candidate counts and local CPU costs. It does not establish general default-grammar tractability. The operators are already in the enumerator's fixed ontology, constants are exposed by examples/request text, and the formulas are shallow. It also does not measure noisy data, false-acceptance prevalence, larger programs, natural task frequency, or new operator invention.

The next evaluation should retain a third unshaped operator family but increase expression depth and include adversarial training sets with multiple fitting candidates. This will reveal whether the current route remains reliable when Occam ordering must choose among structurally different programs, and when the broad grammar's candidate count grows. See the [runner](../../../scripts/substrate_synthesis_unshaped_clamp_transfer_v1.py) and [analyzer](../../../scripts/analyze_substrate_synthesis_unshaped_clamp_transfer_v1.py).
