# Integrated Rung 3 nonlinear-map synthesis v1.1.1 — results

**Date:** 2026-09-29. **Question:** does the shipped `prog_synthesis` request path reach its graph-authored Rung 3, produce an accepted reflected Program, and transfer nonlinear coordinate maps to registered holdouts?

## Protocol history and validity

The original v1 lock specified tuple-valued pair outputs, but its runner converted them to lists before ingestion. The all-gap v1 capture therefore failed its linear positive control and is retained as a diagnostic. V1.1 corrected tuple preservation, but 15 successful workers crashed while serializing native `NodeID` values; that partial capture is also retained and excluded. V1.1.1 makes the capture serialization explicit and runs all 20 cases in fresh processes. Its lock covers the preregistration/amendment, runner, analyzer, task tables, relevant sources, seed files, native extension, and engine provenance.

All capture/source/native and route gates pass: one header/footer, 20/20 unique workers, no worker failures, current source/native hashes match, all workers remain source-stable, all 20 reach the enumerate rung, all terminate, and the linear positive control accepts and transfers 5/5. The registered semantic gate that every accepted program transfer exactly fails, so the overall analysis is correctly marked `integrity_pass: false` (9/10 checks). That failure is the measured generalization outcome, not missing or corrupted capture data. V1, v1.1, and v1.1.1 captures are not pooled.

## Results

| Task | Route outcome | Exact heldout transfer | Median enumerate tests | Median pump wall time | Median pump CPU time |
|---|---|---:|---:|---:|---:|
| Linear | accepted | 5/5 | 118,900 | 1,216 ms | 1,217 ms |
| Quadratic shear | accepted | 5/5 | 121,404 | 1,235 ms | 1,233 ms |
| Hinge shear | accepted, wrong extrapolation | 0/5 | 121,536 | 1,206 ms | 1,207 ms |
| Absolute shear | gapped at candidate budget | 0/5 | 200,000 | 1,609 ms | 1,611 ms |

Overall, 15/20 requests were accepted by the normal training-row verifier. Ten accepted programs (all linear and quadratic repetitions) match all six heldout examples. Five hinge programs share the predicate-based candidate `r + (c > 1)` in the first coordinate. It fits the registered training rows but predicts a constant increment above the threshold, while the target hinge continues to grow; all 30 heldout predictions are wrong. This is a concrete accepted false generalization. The five absolute-value requests honestly gap after the full 200,000-candidate budget. Median peak process RSS is approximately 60–63 MiB for accepted linear/quadratic/hinge runs and 79 MiB for absolute-map failures. Wall and CPU times cover the complete `pump` phase after spec ingestion (enumeration plus rule and adapter work); they are not isolated enumerator timings. The selected operator inventory was the same broad 29-operation set for every family; operators were not manually supplied by this harness.

The independent analyzer's [report](../../../evaluation/reports/synthesis_rung3_nonlinear_map_v1_1_1_20260929_analysis.json) contains the preregistered gate outcomes and per-family costs; the [raw capture](../../../evaluation/reports/synthesis_rung3_nonlinear_map_v1_1_1_20260929_raw.jsonl) records each graph-resident program and holdout prediction; the [lock](../../../evaluation/substrate_capability/synthesis_rung3_nonlinear_map_v1_1_1_20260929_lock.json) preserves provenance. The comparison with the isolated caller-supplied grammar study is descriptive: the integrated `pump` route takes about 1.2 seconds on the acquired maps while enumerating a broad default operator inventory; the direct compact-grammar acquisition medians ranged from 0.20 ms to 47.04 ms across the four task/grammar pairs. Neither comparison isolates every setup cost or estimates another host. These timings are from one local CPU/build and are not an independent-host scaling estimate.

## Interpretation and next measurement

This establishes that the existing graph-authored synthesis path can acquire and adopt linear and quadratic executable Programs on these fixed examples, but it also accepts an overfitted hinge candidate and fails to find an absolute-value map under its default budget. It is not general nonlinear dimension induction: no new primitive or `DimensionGenerator` was minted, and the enumerator received ordinary input/output examples within the existing Program IR vocabulary. The false acceptance shows that a training-fit verdict is not a substitute for transfer validation.

Next preregister a larger, threshold-balanced training panel and an explicit heldout abstention/adjudication policy; add a negative control where a candidate fits training but diverges on withheld regions; compare default grammar against a small task-declared grammar without hiding the default route's cost. Measure the residual-to-enumeration trigger, learned operator selection, verification, persistent graph adoption, and later-task reuse as separate events. Do not increase a training budget or alter grammar selection without a new lock and fresh capture. See the [initial protocol](SUBSTRATE_SYNTHESIS_RUNG3_NONLINEAR_MAP_V1_PREREG_20260929.md), [tuple-type amendment](SUBSTRATE_SYNTHESIS_RUNG3_NONLINEAR_MAP_V1_1_AMENDMENT_20260929.md), and [capture-serialization amendment](SUBSTRATE_SYNTHESIS_RUNG3_NONLINEAR_MAP_V1_1_1_AMENDMENT_20260929.md).
