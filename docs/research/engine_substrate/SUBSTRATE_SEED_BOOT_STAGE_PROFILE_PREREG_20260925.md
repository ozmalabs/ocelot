# Seed boot stage profile preregistration

Date: 2026-09-25  
Status: locked exploratory stage-attribution measurement

## Question

Which Python/native loader stages account for the long full-corpus `load_all_seeds` interval, and which stages change between cold and warm seed-index caches?

## Design

- Use the immutable V1.7 baseline snapshot, after checking both its ordered manifest-hash digest and the transformer's canonical source digest.
- Run four distinct fresh processes in the fixed order cold, warm, warm, cold. Clear the snapshot cache before each cold worker; build and hash-verify it before each warm worker.
- Profile only `load_all_seeds` with Python `cProfile`. Capture wall/CPU time under the profiler, calls and cumulative/self time for `_read_seed_index`, `_seed_manifest_paths`, `_seed_sources_digest`, `_build_seed_index`, `_topo_order`, `json.load`, and native `load_seed_manifest`, plus the top 40 cumulative functions.
- Record graph node/edge counts, seed load order/failures, active rule order, grammar, graph, rule store, and access-set hashes. Require full boot-state equality across all four arms and stable cache bytes during each load.
- Record all relevant sources, native build, corpus, lock, preregistration, and runner hashes. The profile's instrumented wall time is not a production latency estimate; no speedup claim is allowed.

## Limits

One frozen corpus and four profiled boots characterize loader stage attribution, not asymptotic scaling or all workloads. The prior unprofiled N=32 comparison provides a separate startup envelope. Any optimization proposal must be followed by uninstrumented repeated measurements and full-state/order parity.

## Frozen inputs

See the linked [`source lock`](../../../evaluation/substrate_capability/seed_boot_stage_profile_lock_20260925.json) for exact hashes and ordered schedule.
