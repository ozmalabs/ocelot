# Native full-rank GenInfer comparison v1.1 preregistration

## Question

Does the opt-in exact full-rank solver reliably acquire and transfer integer linear generators over varied 3-D geometries, while preserving 2-D behavior and refusing rank-deficient, nonlinear, and ambiguously aligned cases?

## Frozen arms and workload

- Baseline: same current Rust source, built with `--no-default-features`.
- Solver: same source, built with `--features geninfer_full_rank_matrix_solver`.
- Eight fixture families, each repeated in three independent fresh processes: 1-D reflection; existing 2-D shear control; 3-D shear-cycle; 3-D coordinate reflection/permutation; 3-D upper-triangular shear; 3-D rank-deficient; 3-D nonlinear; and 3-D duplicate-ID ambiguity control.
- Each fixture/repetition runs both binaries with scale audit off and on: 8 × 3 × 2 × 2 = 96 workers. Variant order alternates by fixture and audit arm.
- Each worker boots the normal core, enables the shipped ShapeDecode loop and GenInfer route, adds registered training and held-out bases, then observes both targets through full native rule closure.

## Required gates

1. Analyzer, runner, and protocol hashes match the capture; each variant has one stable binary hash; source fingerprints are equal between arms and stable within every worker.
2. Complete 96-worker paired coverage and all three repetitions for every fixture family.
3. All positive 1-D/3-D cases acquire the exact registered matrix during training, emit recognized transformation receipts, and reuse the generator on held-out examples. The 2-D projection matches between variants on status, coverage, residual, receipts, generators, and closure work.
4. Rank-deficient, nonlinear, and ambiguous-ID cases remain unrecognized, add no generator in either arm, and emit no transform receipts. Training and held-out controls are checked independently.
5. Native audit conservation holds per phase: `bases = refusals + attempts`, and `attempts = apply_rejects + candidate_rejects + residual_rejects + survivors`.
6. Audit-off wall and process CPU times are retained as descriptive measurements; no timing promotion is allowed without repeated paired uncertainty analysis.

## Capture and analysis

The runner and analyzer are frozen by their SHA-256 values in the capture. The analyzer runs only after all workers complete and independently recomputes the semantic and counter gates.

```sh
cd runners/dsl
cargo build --release --lib --no-default-features
cp target/release/libsubstrate_rs.so /tmp/geninfer_fullrank_v1_1_baseline.so
cargo build --release --lib --no-default-features --features geninfer_full_rank_matrix_solver
cp target/release/libsubstrate_rs.so /tmp/geninfer_fullrank_v1_1_solver.so
cd ../..
python3 evaluation/substrate_capability/geninfer_full_rank_native_comparison_v1_1.py \
  --prepare /tmp/geninfer_fullrank_v1_1_baseline.so /tmp/geninfer_fullrank_v1_1_solver.so
python3 evaluation/substrate_capability/geninfer_full_rank_native_comparison_v1_1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_native_comparison_v1_1.py
```

The capture is immutable; the runner refuses to overwrite it. These authored geometries do not estimate natural prevalence, do not cover dimensions above three, and do not establish induction from underdetermined examples.
