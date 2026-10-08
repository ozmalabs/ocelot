# Browser seed ReachableFrom cache panel v1 preregistration

**Question:** Does the experimental per-graph `ReachableFrom` memo reduce repeated transitive traversal in the actual authored `browser_affordance_reach` rules, while preserving their mirror-edge result and access trace?

## Source-derived workload

Load both rules verbatim from `seeds/browser_affordance_reach.json`. This seed is required by `worlds/browser.py` for its graph-native nested-affordance mirror, and its mint rule evaluates membership of each `el` in `ReachableFrom(sess, "contains")`. The fixture creates one session, B wrapper elements directly below it, N present leaf elements nested below the wrappers, and one affordance per leaf. The matcher binds `sess contains el0` and `el affords aff`; `el0` is a session anchor and `el` is admitted by the rule's reachability predicate. This reproduces the authored rule's variable structure without launching a browser or making network calls.

Cross N={2,8,32,128}, B={1,4}, three fresh workers per cell (24 workers). In each worker compare cache off/on in counterbalanced arm order. Record exact graph, fixed-point status/progress, runtime access-trace rows, dropped events, candidate/where counters, `ReachableFrom` interior units, and wall time. Timing is descriptive; the primary outcome is adjacency-work count.

## Gates

1. Fresh native build, stable source and seed lock before/after and in each worker, 24 unique worker PIDs.
2. Both source-authored rules load; each arm reaches fixed point and emits exactly the N expected session `has_affordance` edges.
3. Cache-off/on exact graph, progress, runtime trace rows, and dropped-event counts match within each worker.
4. Candidate and where-evaluation counts match between arms; report the traversal-work ratio for every N×B cell.
5. The work counter is nonzero in both arms, and the cache arm does not exceed the uncached work in any cell.

A pass supports this particular source-authored browser rule over the specified DOM-shaped fixtures. It does not estimate real browser-page prevalence, end-to-end BrowserWorld latency, memory cost, or all cache invalidation routes. No network or browser executable is required.

## Artifacts

Runner: [`scripts/substrate_browser_reachable_cache_v1.py`](../../../scripts/substrate_browser_reachable_cache_v1.py)  
Analyzer: [`scripts/analyze_substrate_browser_reachable_cache_v1.py`](../../../scripts/analyze_substrate_browser_reachable_cache_v1.py)  
Lock: `evaluation/substrate_capability/browser_reachable_cache_v1_lock_20260928.json`  
Raw: `evaluation/reports/substrate_browser_reachable_cache_v1_20260928.json`  
Analysis: `evaluation/reports/substrate_browser_reachable_cache_v1_analysis_20260928.json`
