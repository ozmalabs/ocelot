# GenInfer full-rank sorted identity-join scale v1 preregistration

## Question

Does sorting typed identity keys and merging them preserve the native solver's exact behavior while avoiding the current per-source scan of all target relations as frame relation count grows?

## Frozen arms and workload

- Nested arm: current source with `geninfer_full_rank_matrix_solver`; identity alignment scans every target row for every source row.
- Sorted arm: identical source with `geninfer_full_rank_sorted_identity_join`; identity keys are sorted and merged before the same full-rank matrix recovery and candidate validation.
- Both arms enable the same matrix solver. The only source difference is the Cargo feature selecting identity alignment.
- Relation counts: N=8, 32, and 128. Positive geometries: shear-cycle, coordinate reflection/permutation, and upper-triangular shear. Controls at every N: rank-deficient 3-D coordinates, nonlinear 3-D mapping, and duplicate identity keys.
- Two independent fresh workers per geometry/size. Each case is run in both arms with native audit disabled and enabled: 6 families × 3 sizes × 2 repetitions × 2 arms × 2 audit states = 144 workers.
- Every worker boots the normal core and sends training and held-out observations through the native GenInfer/ShapeDecode closure. Train relations have unique IDs except the explicit duplicate-ID control. Coordinates include a fixed full-rank seed followed by deterministic generated rows; the rank-deficient control remains in a plane.

## Required gates

1. Capture hashes match the frozen runner, analyzer, and this protocol. Each arm has one distinct binary hash. Rust source fingerprints match across arms and remain stable within each worker.
2. All 144 workers are present exactly once; each family/size has both repetitions, both arms, and both audit states.
3. For each paired case and audit state, train and held-out semantic outputs match exactly across arms for status, coverage, residual, receipts, closure work, and generator library.
4. All three positive geometries acquire the exact oracle matrix in both arms, recognize train and held-out observations with receipts, and reuse the learned generator on held-out data.
5. Rank-deficient, nonlinear, and duplicate-ID controls remain unrecognized, emit no transform receipt, and mint no generator in either arm or phase.
6. Native full-rank counter conservation passes for each audited phase. Audit-off train/held-out wall and process CPU time are retained. Worker process max RSS is recorded as a descriptive high-water mark, including Python and substrate startup.
7. Scaling interpretation reports N, exact semantic outcomes, latency, and RSS by arm. The source-level alignment work is O(N²) for nested scans and O(N log N) sorting plus O(N) merge for the candidate; latency is empirical and is not promoted from these authored frames alone.

## Capture and analysis

Freeze the runner, analyzer, and this file before capture. Build both binaries from the same checkout:

```sh
cd runners/dsl
cargo build --release --lib --no-default-features --features geninfer_full_rank_matrix_solver
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_join_nested.so
cargo build --release --lib --no-default-features --features geninfer_full_rank_sorted_identity_join
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_join_sorted.so
cd ../..
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v1.py \
  --prepare /tmp/geninfer_sorted_join_nested.so /tmp/geninfer_sorted_join_sorted.so
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v1.py
```

The runner refuses to overwrite its capture or an existing temporary overlay. The report is specific to authored 3-D identity-aligned frames on one host. It does not establish natural prevalence, useful performance on natural tasks, or tractability of rung 3–4 induction.
