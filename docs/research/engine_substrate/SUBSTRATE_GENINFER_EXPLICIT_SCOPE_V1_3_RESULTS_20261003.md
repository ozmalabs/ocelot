# Explicit GenInfer codebook scope v1.3 results (2026-10-03)

## Outcome

The source/native-locked capture passes all 69 cases and all five preregistered
gates. The three positive modes produce exact outputs for all 279 observations;
all 24 fail-closed scope controls produce zero target-generator acquisitions.
The direct diagnostic candidate totals follow the locked formulas. At K=16,
frame-scoped mode checks 38,400 candidates per closure versus 614,400 in both
global modes. Each scoped frame query checks 2,400 candidates; global queries
see all 16 parts.

Median production closure wall time at K=16 is 258.24 ms for frame-scoped,
1,056.98 ms for unscoped-global, and 1,068.07 ms for explicit-global mode.
Thus this synthetic panel shows about 4.09× and 4.14× lower closure time for
frame-scoped mode. At K=8, the corresponding times are 116.75, 290.74, and
287.85 ms. K=1 is effectively tied near 10 ms. Median measured HWM delta is
384 KiB in every cell; this is a coarse process high-water delta, not per-frame
memory accounting.

The result provides an end-to-end production-rule demonstration that GenInfer
can use exact scope IDs to constrain eligible codebook parts while preserving
the generated transformations. It supports bounded-frame work reduction on
this fixed 2-D integer-linear family. It does not measure scope discovery,
assignment errors, boundary construction, scheduling, cross-frame information
flow, arbitrary graph operations, realistic task distributions, or total
system cost. All work is run in one process per synthetic case on one host.

## Harness correction

V1.2's 69-row capture is retained and its analysis remains failed. The
observations in that runner lacked the agent's `observed` edge, which the
production seed rules require to select them. Its zero-acquisition result was
therefore a fixture omission and says nothing about a runtime regression. V1.3
adds this edge and has its own preregistration, source lock, raw capture, and
analysis. No v1.2 artifacts were overwritten.

## Artifacts and reproduction

- [Preregistration](SUBSTRATE_GENINFER_EXPLICIT_SCOPE_V1_3_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_explicit_scope_v1_3_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_explicit_scope_v1_3_analysis_20261003.json)

Reproduce from the repository root with:

```sh
python3 evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3.py --run
python3 evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1_3.py
```

The runner refuses capture if the native build is stale or any locked source
has drifted.
