# Substrate concurrency surface audit (2026-09-26)

## Scope

This is a targeted source audit following the reproduced `Already mutably borrowed` failure and the route-specific `WorldAdapter.converse` RLock mitigation. It maps the known borrow pattern and shows why the mitigation must not be reported as general adapter or native thread safety. It is not an exhaustive audit of every PyO3 entry point.

## Confirmed source shape

- `PySubstrate` stores the core graph in `Arc<Mutex<SubstrateRs>>` (`runners/dsl/src/py.rs`, `PySubstrate` initialization near line 1472).
- Native `run_rules`, `run_rules_report`, the delta report variants, scoped runners, and settling methods use `&mut self`; rule-running methods call `py.allow_threads` around access to the mutex-protected core (e.g. `run_rules` near line 3629; report variants near 3642–3811).
- Read methods such as `node(&self)` still enter the same PyO3 object while locking the core (near line 2094). A thread entering such a method while another thread is in an `&mut self` GIL-releasing call can fail at PyO3's object borrow layer before the Rust mutex can serialize graph access. This matches the v1.1 traceback, but the complete binding contract still merits an API-level review.
- The initial RLock covered only `WorldAdapter.converse`, leaving `self.inner.run_rules()` call sites in utterance ingress, live deliberation, `tick`, and vision settlement exposed. The implementation wraps all public `WorldAdapter` functions with the per-instance RLock, and both `s._inner` and `inner` use a native-call facade sharing it. Three-worker captures confirm `converse` blocks public `tick` and direct node reads through `inner`, `s`, and `s._inner`. This verifies these paths under one schedule, not all public-method combinations.
- The adapter owns background/concurrent facilities (`start_agent`/`stop_agent`, vision worker lifecycle, and adapter host concurrency). Their interactions with arbitrary simultaneous Python calls are not established by the describe-scene capture.

## Exposure and next decision

The adapter-wide RLock serializes public method calls and calls through the adapter-owned `s` and `inner` facades. It does not serialize private methods called directly, raw native handles retained before facade installation, code reaching the facade’s private `_native`, external PyO3 callers, or whole-adapter operations over shared Python-side indexes. Separate native facades now share a lock by native object identity; a three-worker capture with two facades passes the tested overlap. Its interaction with autonomous workers, callbacks, and teardown lock order still needs explicit capture. The next options are:

1. expand cross-entrypoint captures over the public adapter method families and document direct native-access escape hatches; or
2. redesign/audit PyO3 methods so GIL-releasing work does not hold an exclusive `PyClass` borrow, then test all read/write entry classes while native graph locking is active.

Next, build a cross-entrypoint race matrix (conversation/write, tick/read, vision/read, teardown/tick), plus captures involving complete WorldAdapters sharing all Python-side indexes over one native object and autonomous workers. Each case must check exception freedom and graph/result parity. The converse/tick, direct-handle, and shared-native-facade captures remain narrow evidence only. See [shared-facade results](SUBSTRATE_SHARED_NATIVE_FACADE_SERIALIZATION_V1_RESULTS_20260926.md). See [direct handle results](SUBSTRATE_DIRECT_NATIVE_ACCESS_SERIALIZATION_V1_RESULTS_20260926.md).
