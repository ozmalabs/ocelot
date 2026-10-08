# GenInfer fused candidate validator — preregistration

**Question.** Can the GenInfer candidate validator combine its structural prefilter and slot-comparison loops while preserving exact behavior and lowering work or audit-off closure time?

## Implementation arms

- **Baseline:** current two-pass `build_candidate` path, compiled with `--no-default-features`.
- **Fused:** same source and shard count, compiled with `--features geninfer_fused_candidate_validation`; only the GenInfer call site selects the combined traversal. TransformDecode and standalone DimInfer remain on the baseline path in both builds.
- The feature is experimental and off by default. Both artifacts must be built from identical Rust/Python source, and their separate hashes are retained.

## Workloads

- Full-seed positive matrix family: N=4/64, B=3/5/7, three fresh-process repetitions per cell. The V1 run still executes training, held-out application, and corrupted-held-out control.
- Independently authored nonlinear-induction family: linear positive control and coupled-quadratic negative/transfer control, two registered repetitions each from the existing V1.5 fixtures.
- Each task runs on both binaries with scale audit off and on. Paired variant order alternates; task/mode pairs are shuffled with seed 20261006.
- Total: 22 tasks × 2 variants × 2 audit modes = 88 fresh workers.

## Gates and measures

- Exact paired equality of training, held-out, and corruption decisions, statuses, residuals, transformation receipts, generators, and closure work on both families.
- Under audit, exact GenInfer search-accounting parity and attempt formula reconciliation. Term-unit deltas are retained because the fused path may perform partial slot work before a later structural rejection; that reflects actual work in the combined traversal.
- Audit-off per-stage wall and process CPU time, plus peak-RSS delta; audit-on time is diagnostic only.
- Verify each worker loaded the intended native overlay, both arms use identical source manifests, source remains stable across the worker, and each variant has one stable, distinct binary hash.

## Preparation and capture

```sh
cd runners/dsl
cargo build --release --lib --no-default-features
cp target/release/libsubstrate_rs.so /tmp/geninfer_candidate_baseline.so
cargo build --release --lib --no-default-features --features geninfer_fused_candidate_validation
cp target/release/libsubstrate_rs.so /tmp/geninfer_candidate_fused.so
cd ../..
python3 evaluation/substrate_capability/thoughtexperiment_geninfer_fused_candidate_comparison_v1.py \
  --prepare /tmp/geninfer_candidate_baseline.so /tmp/geninfer_candidate_fused.so
python3 evaluation/substrate_capability/thoughtexperiment_geninfer_fused_candidate_comparison_v1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_fused_candidate_comparison_v1.py
```

Both binaries are copied into isolated source-matched temporary package trees; the canonical extension is not replaced. The runner refuses to overwrite its capture. The independent analyzer gates pair completeness, source and binary provenance, exact semantic parity, and GenInfer counter conservation before reporting timing ratios.

## Interpretation

Promote no performance claim unless exact parity passes on both registered families and audit-off times show a consistent paired improvement. A reduction in `term_unit:GenInfer` alone is not enough if the fused path adds hidden or partial comparisons; report its measured units and the changed rejection-path accounting. This study does not establish natural-task prevalence or speedup on other families.
