# GenInfer full-rank sorted identity-join scale v2 preregistration

## Question

Does the sorted identity-key join reduce the actual number of identity-key field comparisons as relation count grows, while preserving the exact native solver behavior? V1 showed end-to-end timing too close to noise at N≤128 and did not count join comparisons directly.

## Frozen arms and workload

- Nested: `geninfer_full_rank_matrix_solver` plus `geninfer_full_rank_identity_join_work_audit`.
- Sorted: the same features plus `geninfer_full_rank_sorted_identity_join`.
- Both arms therefore contain the same audit instrumentation. The new counter counts each field comparison in an identity key, and is accumulated only when native scale audit is enabled. It covers the nested equality probe or sorted comparator calls (sort, duplicate check, and merge).
- Relation counts N=8/32/128/512/2,048. Three positive 3-D matrix families (shear-cycle, coordinate reflection/permutation, upper-triangular shear) and three controls (rank-deficient, nonlinear, duplicate identity keys). Two fresh workers per family/size.
- Every worker runs each arm with scale audit off and on: 5 sizes × 6 families × 2 repetitions × 2 arms × 2 audit states = 240 workers.
- Each worker performs normal native training and held-out graph closure. The candidate uses the same matrix recovery, candidate validator, minting, and re-decode path as the nested arm.

The nonlinear control is a **within-frame map** (`z := z + x*y`) and probes whether this integer-linear matrix solver refuses a nonlinear relation mapping. It does not test sequence extrapolation. `TimeInfer`'s separate order-N path fits finite differences over the per-pair offset stream when every consecutive pair is a rigid translation; that is polynomial trajectory extrapolation and is outside this join benchmark.

## Required gates

1. Runner, analyzer, protocol, source, and binary provenance pass; each arm has one stable and distinct binary hash; source manifests match and remain stable per worker.
2. All 240 workers are unique and present, with both repetitions and all arms/audit states for every size/family cell.
3. Exact paired semantic agreement holds for train and held-out status, coverage, residual, receipts, closure work, and generator library.
4. All positive cases acquire the exact matrix, return receipts, and reuse the learned generator on held-out data. Rank-deficient, nonlinear, and duplicate-ID controls refuse in both phases and mint no generator.
5. Existing full-rank native counter conservation passes in each audited phase. Identity-key comparison counts are present and positive where alignment is attempted. For every positive case at N≥32, sorted comparison count is lower than nested count.
6. Report comparison-count medians by N, phase, and arm; audit-off latency, CPU, and process RSS are descriptive only. Because the work-counter code is compiled into both binaries and branches on audit state, v2 timing is instrumented and cannot replace v1's clean timing comparison.
7. Interpret measured work counts separately from asymptotic source analysis: nested scans are expected to grow quadratically; sorted key sorting plus merge should grow as N log N. The capture does not estimate natural-task prevalence or rung 3–4 learning cost.

## Capture and analysis

Freeze all three source hashes before the first worker. Build both arms from the same checkout:

```sh
cd runners/dsl
cargo build --release --lib --no-default-features \
  --features geninfer_full_rank_matrix_solver,geninfer_full_rank_identity_join_work_audit
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_join_v2_nested.so
cargo build --release --lib --no-default-features \
  --features geninfer_full_rank_matrix_solver,geninfer_full_rank_sorted_identity_join,geninfer_full_rank_identity_join_work_audit
cp target/release/libsubstrate_rs.so /tmp/geninfer_sorted_join_v2_sorted.so
cd ../..
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2.py \
  --prepare /tmp/geninfer_sorted_join_v2_nested.so /tmp/geninfer_sorted_join_v2_sorted.so
python3 evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2.py --run
python3 evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v2.py
```

The runner refuses to overwrite a previous capture or temporary overlay. Remove only this protocol's `/tmp` overlay and copied binaries after analysis. This is an authored 3-D scaling experiment on one host, not a general tractability or capability result.
