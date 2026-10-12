# GenInfer cross-frame dependency v1 results (2026-10-03)

## Outcome

The paired, source-locked production-rule panel passes all gates across 36
cases, with three repeats at K=2/4/8/16. Global closure acquires the exact
transform in all 36 cases. Scoped closure acquires it in all 24 local or
explicitly included-dependency cases, and in 0/12 cases where the needed basis
is present in another frame but excluded by the supplied scope. Receipts name
the oracle base whenever acquisition succeeds. Candidate checks per query are
2,400 in scoped mode and K×2,400 globally.

Per-K median closure wall times show the work reduction and its correctness
condition:

| Condition | K=16 global | K=16 scoped | Global/scoped | Scoped exact acquisitions |
|---|---:|---:|---:|---:|
| Local basis | 64.48 ms | 14.43 ms | 4.47× | 3/3 |
| Cross-frame basis included | 64.38 ms | 14.28 ms | 4.51× | 3/3 |
| Cross-frame basis excluded | 64.30 ms | 4.85 ms | 13.26× | 0/3 |

The excluded-basis arm is faster because it searches less and terminates
without the explanation. That is not a capability improvement: all three
paired global workers acquire the correct generator while all three scoped
workers miss it. This directly demonstrates that scope quality and dependency
coverage bound the value of frame-local execution. Explicitly including the
cross-frame basis preserves exact inference while retaining the measured
reduction in candidate work.

The source implements exact `scope_id` filtering before parsing codebook parts
([loader](../../../runners/dsl/src/shape_decode.rs#L266)); the `GenInfer` Term
passes the caller-supplied scope and required flag into that loader
([Term evaluation](../../../runners/dsl/src/term.rs#L10268)). This benchmark
labels frames and dependencies explicitly; it does not discover either one.
Scope provenance metadata is not runtime validated, as separately measured in
the [provenance probe](SUBSTRATE_GENINFER_SCOPE_PROVENANCE_V1_RESULTS_20261003.md).
The workload is authored 2-D integer-linear geometry on one host. It does not
estimate how often natural tasks have such boundaries or how to learn a safe
boundary.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_CROSS_FRAME_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_cross_frame_v1.py)
- [Primary analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_cross_frame_v1.py)
- [Per-K analysis](../../../evaluation/substrate_capability/analyze_substrate_geninfer_cross_frame_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_geninfer_cross_frame_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_cross_frame_v1_20261003.json)
- [Gated analysis](../../../evaluation/reports/substrate_geninfer_cross_frame_v1_analysis_20261003.json)
- [Per-K analysis output](../../../evaluation/reports/substrate_geninfer_cross_frame_v1_1_analysis_20261003.json)

Reproduce from the repository root:

```sh
python3 evaluation/substrate_capability/substrate_geninfer_cross_frame_v1.py --run
python3 evaluation/substrate_capability/analyze_substrate_geninfer_cross_frame_v1.py
python3 evaluation/substrate_capability/analyze_substrate_geninfer_cross_frame_v1_1.py
```
