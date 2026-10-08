# GenInfer residual-semantics audit results (2026-09-26)

## Result

All six independent integrity and semantic gates pass across 40 field observations (four transform families × two conditions × five repeated calls). Every exact positive returns its expected matrix, `explained=true`, `residual_dims=0`, empty `transforms` and `dims`, and 6,560 checked candidates. Every p1 coordinate perturbation returns that same matrix with `explained=true`, `residual_dims=1`, `dims=[1]`, and exactly one residual `{kind: shift, dim: 1, delta: 1, pred: p1}`. The output is stable across all maps and repeats.

This confirms that GenInfer's boolean reports successful decomposition into a linear generator plus residual dimension transforms. It is not a matrix-only exact-fit predicate. Accordingly, the earlier coordinate controls were valid tests of matrix-only fit but invalid controls for the broader `explained` contract. Predicate-corrupt and missing/extra-relation controls remain distinct cases and were refused in the prior factorial capture.

## Limits

The audit uses one four-relation motif, four small 2-D matrices, one p1 shift, and direct Term-field reads. It characterizes this output path only; it does not validate residual-transform soundness for other transform families or estimate false-positive rates over natural observations. No timings are reported.

## Artifacts

Protocol: [`SUBSTRATE_GENINFER_RESIDUAL_SEMANTICS_PREREG_20260926.md`](SUBSTRATE_GENINFER_RESIDUAL_SEMANTICS_PREREG_20260926.md). Runner and analyzer: [`geninfer_residual_semantics_probe_v1.py`](../../../scripts/geninfer_residual_semantics_probe_v1.py), [`analyze_substrate_geninfer_residual_semantics_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_residual_semantics_probe_v1.py). Raw capture: [`substrate_geninfer_residual_semantics_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_residual_semantics_v1_20260926.json). Analysis: [`substrate_geninfer_residual_semantics_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_residual_semantics_v1_analysis_20260926.json).
