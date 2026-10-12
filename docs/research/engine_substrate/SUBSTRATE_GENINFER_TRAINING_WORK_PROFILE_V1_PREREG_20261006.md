# Full-seed GenInfer training work profile — preregistration

**Question.** Which measured work terms grow with the number of relations during full-seed GenInfer training closure, and which remain tied to the data-derived matrix bound?

## Design

- Use one current-source 64-shard native build, installed only in a temporary overlay with a verified build record.
- Run positive full-seed cases at 4, 16, and 64 relations, bound 5, with three fresh processes per size (nine workers total).
- Preserve the existing V1 training/held-out/corruption case and semantic oracles. The analyzer gates training acquisition, exact held-out transfer, and corrupt-held-out rejection.
- Reset and enable the native `scale_audit` immediately around each `run_rules()` call. Capture GenInfer request/cache/kernel counts, eligible bases by bound, matrix attempts, and apply/candidate/residual rejection or survivor counts alongside wall/CPU time, closure work, graph size, and peak-RSS delta.
- Require counter reconciliation: requests = cache hits + kernel calls; eligible bases = sum by bound; matrix attempts = sum of `(2B+1)^4-1` per eligible base; attempts = all four outcome categories.
- Treat counter totals as work attribution. Timings include audit overhead and are diagnostic only; they are not comparable to the prior uninstrumented capture.

## Preparation and capture

```sh
cd runners/dsl
cargo build --release --lib --no-default-features
cd ../..
python3 evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py \
  --prepare runners/dsl/target/release/libsubstrate_rs.so
python3 evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py --run
python3 evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v1.py
```

The runner copies the exact current Rust source, Python package, Cargo manifest/lock, and selected binary into `/tmp/ocelot_geninfer_training_work_v1`, records and checks its build fingerprint, then preloads that package in each worker. It does not replace the canonical extension. The raw capture binds the native binary, V1 task, protocol, runner, analyzer, and per-worker source hashes. The runner refuses to overwrite an existing capture.

## Interpretation

Compare candidate counts, rejection partitions, eligible bases, and bounds across sizes. Constant attempt counts with rising elapsed time imply more per-candidate work or graph work, not a larger matrix search. Growth in bases or bounds identifies a different search-cost source. This three-size authored family can locate the current hotspot; it cannot establish a general complexity bound or natural-task prevalence.
