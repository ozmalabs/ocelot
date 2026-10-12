# Shape-decoding concurrency profile v3 — branch setup GIL intervention preregistration

**Question:** Does allowing other Python worker threads to proceed while native experimental forks and edge-aperture setup execute improve synchronized fanout-8 shape-decoding rehearsal throughput?

**Intervention:** In the PyO3 bindings, preserve wrapper-state eligibility checks under the GIL, then clone the native `Arc<Mutex<Substrate>>` handle and run only `fork_full_copy_experiment`, `fork_shared_slab_experiment`, `fork_shared_graph_pages_experiment`, and `set_experiment_edge_scope` inside `py.allow_threads`. Keep each source/branch native mutex held for the same operation as before. No graph, rule, task, or candidate semantics change.

**Design:** Repeat the established 100k-node positive shape-axis `dedup_identity_fix` panel: scoped full-copy and shared-graph-page backends; sequential and synchronized concurrent fanout 8; three fresh processes per cell (12 total), zero warmups. Compare against the existing v2 pre-intervention raw capture with identical task and metrics. Record wall per wave, summed per-thread CPU, CPU/wall, and phase timings. Validate exact task oracle, branch results, backend/mode parity, primary graph/rule revision, source and native binary locks, and build freshness. This measures total bindings intervention; it does not isolate individual fork/scope calls.

**Interpretation:** A gain requires concurrent wave wall to improve against v2 under both backend and semantic gates, with CPU overlap increasing above the v2 ~1× baseline. Three repeats on one host are exploratory. Release of the GIL does not ensure useful parallelism while sibling calls serialize on a shared native mutex or compete for memory bandwidth.
