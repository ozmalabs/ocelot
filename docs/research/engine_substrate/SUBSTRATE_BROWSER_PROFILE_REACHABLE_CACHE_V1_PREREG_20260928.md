# Browser profile ReachableFrom cache panel v1 preregistration

**Question:** Does cache reuse persist when the browser-affordance rule runs through the ordinary `WorldAdapter` tick with its five-seed browser profile loaded, rather than on an isolated native substrate containing only the two browser rules?

## Workload and design

Boot `WorldAdapter` with the same seed list used by `tests/test_browser_reachable.py`: `decision_core`, `learning_core`, `perception_core`, `region_grouping`, and `browser_affordance_reach`. Create graph-resident `WorldInstance` session/element records and nested `contains` edges plus `affords` edges, matching the graph shape produced by browser DOM ingestion. Then call `WorldAdapter.tick()` to run the normal profile cycle. Browser launch and external network are omitted because the current sandbox blocks Chromium startup; this panel measures the actual seeded adapter and engine path over explicitly constructed DOM-shaped records.

Cross N={2,8,32,128} affordances and B={1,4} direct wrappers, three fresh workers per cell (24 workers). Each worker runs cache off/on in counterbalanced order. Record ordinary tick steps, exact native graph, exact expected `has_affordance` edge set, native access-trace rows, dropped trace count, matcher counters, `ReachableFrom` interior work, and elapsed tick time. Timing is descriptive; traversal units are the primary cost.

## Gates

1. Lock all transitive seed manifests loaded by the named profile, relevant Python/Rust sources, current native build, and runner/analyzer inputs.
2. 24 unique fresh processes and exact 4×2×3 design with counterbalanced cache arms.
3. Both arms execute the adapter tick, match expected progress, reach the expected mirror graph, and match exact graph/access traces.
4. Candidate tests, where evaluations, and rule enumerations match between arms; reachable-work counters are nonzero and cache-on never exceeds cache-off.
5. Independent analysis verifies the lock, manifest, parent log, every graph oracle, and each pairwise semantic/counter comparison.

This is a loaded profile integration result using synthetic DOM-derived records. It does not estimate live-page latency or topology prevalence. It does not resolve Chromium's sandbox failure, cache memory, or every mutation route.

## Artifacts

Runner: [`scripts/substrate_browser_profile_reachable_cache_v1.py`](../../../scripts/substrate_browser_profile_reachable_cache_v1.py)  
Analyzer: [`scripts/analyze_substrate_browser_profile_reachable_cache_v1.py`](../../../scripts/analyze_substrate_browser_profile_reachable_cache_v1.py)  
Lock: `evaluation/substrate_capability/browser_profile_reachable_cache_v1_lock_20260928.json`  
Raw: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_20260928.json`  
Analysis: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_analysis_20260928.json`
