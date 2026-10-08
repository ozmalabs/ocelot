# Nonlinear dimension induction v1.1 results (2026-09-26)

## Admitted run

The corrected, pre-locked full-seed production-path probe completed 60 fresh substrate cases: three transform families × two arms × ten replicates. All ten analysis gates pass, including exact input/source-lock match, complete factorial, the linear positive control, zero matrix induction in frozen controls, and independent confirmation that the nonlinear training schedules have no exact 2×2 integer-matrix fit within the registered bound.

The initial v1 harness attempt is retained and excluded. It passed observation signatures as JSON strings instead of structured lists; all 60 cases, including linear controls, fell to ordinary quantum minting. That failed capture is a harness defect, not negative capability evidence. v1.1 corrects the encoding and requires the positive control to pass for admission.

A second fresh-process execution under the identical v1.1 source/input lock completed another 60 cases. Route, mint, quantum, and generator outcomes match across every corresponding cell; all admission gates pass in both processes. Both analyses pass all gates. Quadratic enabled-closure latency is also stable across processes: median 1,013.06/1,013.38 ms, p90 1,991.00/1,985.35 ms, max 2,042.45/1,994.12 ms (replicate 1/2). Piecewise medians are 40.41/40.55 ms. This is a same-machine, same-build process replication, not an independent environment replication.

## Outcomes

| Family | Production induction | Frozen/no induction | Independent matrix transfer |
|---|---:|---:|---:|
| Linear `T(x,y)=(x+y,2y)` | 10/10 acquire exact matrix; both training and transfer recognized | 10/10 fail to acquire; both stages mint | 10/10 exact |
| Quadratic shear `T(x,y)=(x+y²,y)` | 0/10 induce; training and transfer both mint quanta | 10/10 mint | 0/10 |
| Piecewise shear `T(x,y)=(x+max(y−1,0),y)` | 0/10 induce; training and transfer both mint quanta | 10/10 mint | 0/10 |

No nonlinear operator or linear matrix was newly present in the nonlinear production cases. The observed `minted` result is fallback to a CapabilityAxis quantum, not acquisition of the transformation. Thus this production path demonstrates bounded linear induction and transfer on these fixtures, while the two registered nonlinear families remain uninduced. This is a narrow negative result for these geometries and current seed, not an impossibility result for other substrate learning routes.

## Cost

Per-closure wall time across both stages and ten replicates, in milliseconds (single build/machine capture):

| Family | Production median / p90 / max | Frozen median / p90 / max |
|---|---:|---:|
| Linear | 34.0 / 72.9 / 95.4 | 0.45 / 0.49 / 0.75 |
| Quadratic shear | 1,013 / 1,991 / 2,042 | 0.43 / 0.48 / 0.55 |
| Piecewise shear | 40.4 / 74.5 / 76.4 | 0.45 / 0.61 / 0.84 |

These times include the enabled GenInfer attempt. The quadratic case reaches roughly two seconds per closure despite not acquiring a map, exposing a costly miss path. This is consistent with finite 2×2 matrix enumeration and candidate validation; it is not a stable throughput benchmark or a commodity-scale claim. Report setup and interpreter cost separately in any future scaling study.

## Interpretation and next gate

The tractability report’s split is now directly observed in a small production path: an in-family transformation is acquired and reused; out-of-family nonlinear transforms trigger fallback and can be much more expensive. The experiment does not establish a general nonlinear learner, nor does it test natural frequency or long-term adopted-operator maintenance. Next: independently replicate these three families with a frozen environment, add a bounded richer hypothesis-class arm only after its representation/search budget is specified, and assess the cost impact of stopping linear search after a principled residual/refusal condition.

## Artifacts

- Protocol: [`SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_1_PREREG_20260926.md`](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_1_PREREG_20260926.md)
- Runner and independent analyzer: [`substrate_nonlinear_dimension_induction_v1_1.py`](../../../scripts/substrate_nonlinear_dimension_induction_v1_1.py), [`analyze_substrate_nonlinear_dimension_induction_v1_1.py`](../../../scripts/analyze_substrate_nonlinear_dimension_induction_v1_1.py)
- Frozen source/input lock: [JSON](../../../evaluation/substrate_capability/nonlinear_dimension_induction_v1_1_lock_20260926.json)
- Raw capture and analysis: [raw](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_20260926.json), [analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_analysis_20260926.json)
- Fresh-process replication: [replicate 1 raw](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep1_20260926.json), [replicate 1 analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep1_analysis_20260926.json), [replicate 2 raw](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep2_20260926.json), [replicate 2 analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_1_rep2_analysis_20260926.json)
- Excluded v1 harness attempt: [protocol](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_PREREG_20260926.md), [raw](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_analysis_20260926.json)
