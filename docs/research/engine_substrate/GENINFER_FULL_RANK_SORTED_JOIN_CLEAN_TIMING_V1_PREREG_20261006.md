# GenInfer full-rank sorted identity-join clean timing v1 preregistration

## Question

Do the identity-comparison reductions measured with audit instrumentation at N=128/512/2,048 translate into lower end-to-end training closure cost on independently shuffled identity rows when comparison instrumentation is absent from the binaries?

## Frozen arms and workload

- Nested clean: `geninfer_full_rank_matrix_solver` only.
- Sorted clean: `geninfer_full_rank_matrix_solver` plus `geninfer_full_rank_sorted_identity_join`.
- Neither binary enables `geninfer_full_rank_identity_join_work_audit`; no per-comparison counter or counter branch is compiled into this capture.
- Relation counts N=128/512/2,048; the same three positive matrices and three refusal controls (rank-deficient, nonlinear within-frame warp, duplicate IDs) as v2.3. Source and target training rows are independently shuffled with deterministic distinct seeds. Two fresh workers per size/family.
- Each case runs once in both clean binaries, audit disabled: 3 sizes × 6 families × 2 repetitions × 2 arms = 72 workers.
- Full native train and held-out graph closure is measured. The held-out phase records cost of reusing the learned graph-resident generator.

## Required gates

1. Runner, analyzer, protocol, source, and binary provenance pass; each arm has one stable distinct binary hash; source manifests match and stay stable per worker.
2. All 72 workers are present exactly once; all three sizes, six families, and two repetitions are covered in both arms.
3. Source/target permutations are valid, independently different, and identical between paired arms. The independent matrix oracle compares canonical relation sets so row order does not affect truth.
4. Train and held-out semantic fields match exactly across arms. Both arms acquire the oracle matrix and reuse it on held-out positives; all refusal controls abstain and mint nothing.
5. Report paired audit-off wall and process CPU time by size and phase, along with process high-water RSS. Use paired per-case ratios and replicate spread. Timing remains specific to this authored workload and host.

The nonlinear control is a static within-frame map (`z := z + x*y`) and does not test the separate order-N trajectory extrapolator for rigid-translation offset streams.

## Capture and analysis

Freeze runner, analyzer, and protocol hashes before capture. Build both release binaries from the same source:

```sh
cd runners/dsl
cargo build --release --lib --no-default-features --features geninfer_full_rank_matrix_solver
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_clean_nested.so
cargo build --release --lib --no-default-features \
  --features geninfer_full_rank_matrix_solver,geninfer_full_rank_sorted_identity_join
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_clean_sorted.so
cd ../..
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_clean_timing_v1.py \
  --prepare /tmp/geninfer_sorted_clean_nested.so /tmp/geninfer_sorted_clean_sorted.so
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_clean_timing_v1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_clean_timing_v1.py
```

The runner refuses to overwrite prior output or overlays. Remove only this protocol's temporary overlay and copied binaries after analysis. This gate addresses a local join cost; it does not estimate natural-task prevalence, higher-dimensional map acquisition, order-N extrapolation, or general capability.
