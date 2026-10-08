# GenInfer relation-count × matrix-bound profile — preregistration

**Question.** How do relation count and the data-derived matrix-entry bound contribute independently to GenInfer training work and closure cost?

## Fixed design

- Current-source 64-shard native engine in a temporary source-verified overlay.
- Factorial: relation counts N=4/16/64 × matrix bounds B=3/5/7 × three fresh-process repetitions (27 workers).
- Positive transform: `[B−1, 1, 1, 1]` over the same authored training-point family, yielding determinant-positive transformations at every bound.
- The existing full-seed runner supplies training, held-out, corrupted-held-out, and exact-output checks. Its `run_rules()` calls are wrapped with the existing native scale audit; timings include instrumentation and are diagnostic only.
- Record eligible bases by observed bound; matrix attempts; application, structural-candidate, residual rejects, and survivors; request/cache/kernel counts; closure work and graph size.
- Reconcile requests = cache hits + kernel calls; eligible bases = sum by bound; expected attempts = `Σ_b count_b × ((2b+1)^4−1)`; and attempts = application rejects + candidate rejects + residual rejects + survivors.
- Require the training goal's observed bounds to equal the treatment B, exact training acquisition, exact held-out transfer, and rejection of corrupted held-out data.
- Run cells in fixed N-major, B-middle, repetition-minor order. The unit of replication is a fresh worker process.

## Preparation and capture

```sh
cd runners/dsl
cargo build --release --lib --no-default-features
cd ../..
python3 evaluation/substrate_capability/substrate_geninfer_training_work_profile_v2.py \
  --prepare runners/dsl/target/release/libsubstrate_rs.so
python3 evaluation/substrate_capability/substrate_geninfer_training_work_profile_v2.py --run
python3 evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v2.py
```

The runner delegates overlay preparation and instrumented workers to the V1 work-profile helper, while locking its own factorial, protocol, analyzer, and helper hashes. It refuses to overwrite an existing capture. It does not replace the canonical extension.

## Interpretation

Report matrix-attempt growth and per-attempt relation growth separately. If attempts rise according to the bound formula while time per attempt is stable, bound-driven enumeration dominates. If attempts remain fixed across N while time grows, data processing per candidate dominates. If both rise, the combined cost is multiplicative in these dimensions. This panel characterizes the authored 2D integer-linear family only; it cannot establish a natural distribution of B, capability across other hypothesis classes, or a general complexity bound.
