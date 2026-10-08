# Native full-rank GenInfer comparison v1

## Question and arms

Does exact full-rank matrix recovery at the native GenInfer boundary acquire and reuse 1-D and 3-D linear generators while preserving the existing exhaustive 2-D route? Does it abstain on rank-deficient and nonlinear 3-D inputs?

- Baseline binary: current source, no default features.
- Solver binary: identical source with `geninfer_full_rank_matrix_solver` enabled. The feature is off by default.
- Both artifacts are copied to isolated, source-matched Python package overlays and identified by SHA-256.

## Workloads

Five fixed cases cover 1-D/2-D/3-D linear positives, a 3-D rank-deficient control, and a 3-D nonlinear control. Each case runs in a fresh process on each binary, with scale audit both disabled and enabled (20 workers total). Variant order alternates by case and audit mode. Each worker boots the normal core, enables the shipped ShapeDecode loop and GenInfer rule, submits a training observation, then a held-out observation. The source fixtures use predicate and identity slots plus typed integer coordinates. Positive matrices are those in the prior exact-solver feasibility protocol.

## Gates

- Intended binary loaded and hash stable; source fingerprints match across arms and remain stable within each worker.
- Feature-off baseline remains unchanged on the registered fixtures, especially the 2-D path.
- Exact training/held-out status, residual, receipt, and generator parity for 2-D.
- Solver arm acquires the registered 1-D/3-D matrix at training and reuses a training-acquired generator on held-out input.
- Rank-deficient and nonlinear 3-D controls do not acquire their oracle matrix.
- Audited full-rank accounting reconciles: bases = refusals + matrix attempts; attempts = apply rejects + candidate rejects + residual rejects + survivors.
- Report audit-off wall/CPU timing separately from audit-on diagnostic counters.

## Reproduction

```sh
cd runners/dsl
cargo build --release --lib --no-default-features
cp target/release/libsubstrate_rs.so /tmp/geninfer_fullrank_baseline.so
cargo build --release --lib --no-default-features --features geninfer_full_rank_matrix_solver
cp target/release/libsubstrate_rs.so /tmp/geninfer_fullrank_solver.so
cd ../..
python3 evaluation/substrate_capability/geninfer_full_rank_native_comparison_v1.py --prepare \
  /tmp/geninfer_fullrank_baseline.so /tmp/geninfer_fullrank_solver.so
python3 evaluation/substrate_capability/geninfer_full_rank_native_comparison_v1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_native_comparison_v1.py
```

The capture is immutable and the runner refuses to overwrite an existing result. These authored cases do not estimate the prevalence of full-rank frames or establish general-dimensional induction beyond the registered dimensions.
