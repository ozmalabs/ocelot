# Nonlinear dimension induction v1.5: measured search attribution

## Result

V1.5 repeats the locked 40-cell linear/coupled-quadratic design with counters placed directly at GenInfer requests, cache hits, kernel calls, eligible bases, and matrix candidate outcomes. The run passes all 17 admission gates, including positive enabled-path activity, zero GenInfer requests in frozen controls, exact cache/kernel request reconciliation, candidate-count reconciliation from both outcome buckets and the bound histogram, and the existing linear positive control.

The coupled-quadratic enabled arm has no target-compatible generator or exact held-out transfer prediction in 10/10 runs. Each observation adds one novelty `CapabilityAxis`; the `DimensionGenerator` count stays at five. Each training and transfer stage makes exactly one uncached GenInfer kernel call per run. Across the ten runs, training searches 48,000 matrices over 20 eligible bases at B=3; transfer searches 7,812,480 matrices over 20 bases at B=12. Every attempted matrix reaches residual validation and all are rejected there: 0 application failures, 0 missing shape candidates, 48,000 training residual rejections and 7,812,480 transfer residual rejections, with zero surviving candidates. The counters exactly match `(2B+1)^4−1` per eligible base.

The enabled linear control acquires and transfers the expected operator in all 10 runs. Training sees 40 GenInfer requests, 20 cache hits, and 20 kernel calls; 262,400 matrices are checked across 40 eligible bases at B=4, with 20 candidates surviving residual validation. Transfer requires no GenInfer call after acquisition and is recognized exactly. Frozen arms make zero GenInfer requests. Mean closure times under the enabled audit are 13.695 ms train and 1,980.246 ms transfer for coupled quadratic, versus 0.606/0.518 ms frozen. The linear enabled means are 70.510/0.876 ms.

## Interpretation

The v1.3 cost attribution is now confirmed: this path enumerates the expected data-bounded matrix space, and the nonlinear miss occurs because no enumerated linear map passes residual consistency. This distinguishes a hypothesis-class gap from an unexecuted search or an empty codebook. It also shows a substantial search-size increase as the observation's coordinate extent raises B from 3 to 12. Training cache reuse is real in the linear path (20 of 40 requests); the coupled-quadratic path has no cache hits.

These are operation counts from an audit-enabled source/native-locked build and one authored finite fixture. Wall times include scale-audit instrumentation and are not comparable as clean counter-off performance estimates. The result does not show that a richer nonlinear grammar will acquire the operator, and does not support natural-task prevalence or commodity-scale timing claims.

## Next gate

Design a bounded structured nonlinear hypothesis family (including cross-coordinate products) and preregister its candidate language, canonicalization, resource budget, and false-mint controls. Avoid expanding the full 2×2 linear enumeration bound as a proxy for richer learning. Hold the current linear positive control, frozen arm, identity-aligned held-out transfer, and target-hidden scoring fixed. Report grammar candidate count, cost per candidate, acquisition/refusal, cache behavior, and prior-codebook stability. Separately measure audit overhead with matched audit-on/off executions before using latency to compare candidate families.

## Reproduction

The source/native lock is `evaluation/substrate_capability/nonlinear_dimension_induction_v1_5_lock_20261005.json`; raw capture and independent analysis are `evaluation/reports/substrate_nonlinear_dimension_induction_v1_5_20261005.json` and `evaluation/reports/substrate_nonlinear_dimension_induction_v1_5_analysis_20261005.json`. Protocol, runner, and analyzer are linked below. The v1.4 inert-instrument capture is documented separately in [the v1.4 amendment](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_4_AMENDMENT_20261005.md).
