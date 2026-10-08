# GenInfer full-seed closure by COW shard count — preregistration

**Question.** Does the 512-shard typed-graph COW configuration change the cost or correctness of the existing full-seed GenInfer closure workload relative to the 64-shard build?

This is an engine-cost gate. It does not estimate natural-task prevalence, frame locality, or the cost of learning a new hypothesis class. The existing `substrate_geninfer_fullseed_scaling_v1.py` workload supplies the task and its semantic checks. This panel changes only the compiled `cow_shards_*` feature and executes both variants in fresh processes.

## Fixed design

- Variants: default 64 shards (`--no-default-features`) and `cow_shards_512`.
- Positive cases: relation counts 4, 16, and 64; bound 5; three fresh-process repetitions each.
- Controls: disabled GenInfer and one predicate-corrupted training example, relation count 8, bound 5; three repetitions each.
- Total: 15 cases × 2 variants = 30 fresh worker processes. Variant order alternates by case index.
- Measurements: per closure call, wall time, process CPU, `run_rules()` work, graph node/edge counts, and process peak-RSS delta; plus acquired generator, held-out transformation, corrupted held-out behavior, and source stability.
- Each worker loads the selected temporary extension before importing the existing V1 runner. It fails unless the recorded loaded path is the selected overlay and the source manifest is identical before and after the case.
- Report paired medians by case family and relation count. Keep closure work counts and semantic parity gates separate from timing. Do not infer asymptotic complexity from this finite panel.

## Preparation and capture

From the repository root, build each feature in turn from the same current `runners/dsl` source:

```sh
mkdir -p /tmp/ocelot_fullseed_cow_shards_v10
cd runners/dsl
cargo build --release --lib --no-default-features
cp target/release/libsubstrate_rs.so /tmp/ocelot_fullseed_cow_shards_v10/native64.so
cargo build --release --lib --no-default-features --features cow_shards_512
cp target/release/libsubstrate_rs.so /tmp/ocelot_fullseed_cow_shards_v10/native512.so
cd ../..
python3 evaluation/substrate_capability/substrate_geninfer_cow_shard_closure_v1.py \
  --prepare /tmp/ocelot_fullseed_cow_shards_v10/native64.so \
  /tmp/ocelot_fullseed_cow_shards_v10/native512.so
```

Preparation mirrors current Rust source, package Python files, `Cargo.toml`, and `Cargo.lock` into isolated temporary trees, installs each supplied artifact there, and records/verifies its source fingerprint. Never install either variant over the canonical extension. After both overlays are prepared, run:

```sh
python3 evaluation/substrate_capability/substrate_geninfer_cow_shard_closure_v1.py --run
```

The runner refuses to overwrite its capture. The capture records both binary hashes, every worker source manifest, runner/protocol/analyzer hashes, and all per-worker outputs. The analyzer must reject missing workers, cross-worker source drift, incorrect engine paths, failed semantic checks, or case/pair mismatch before summarizing timings.

## Decision rule

This gate passes only if every positive worker acquires the expected transform and exactly transforms held-out data, every corrupted held-out input remains inexact, disabled controls do not acquire GenInfer output, both variants have identical closure work counts and final semantic outcomes per paired case, and every source/provenance check passes. Any mismatch blocks shard promotion. Timing informs whether a larger representative route panel is justified; this small synthetic family alone cannot change the production default.
