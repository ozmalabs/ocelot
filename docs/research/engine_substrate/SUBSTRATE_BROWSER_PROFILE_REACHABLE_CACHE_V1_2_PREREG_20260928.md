# Browser profile ReachableFrom cache v1.2 preregistration

**Question:** Can the cache avoid copying a large trace footprint on every hit, preserve exact access traces, and improve ordinary tick time when both scale auditing and access tracing are disabled?

V1.1 exposed a source-level cost: `HashMap::get(...).cloned()` cloned each cached `SmallVec<NodeID>` footprint on every hit. V1.2 stores each result/footprint pair behind `Arc`; cache hits clone only the Arc and result Value's Arc. It also replays the footprint only when access tracing is enabled. This changes storage and the cache-hit path, not rule semantics or invalidation.

Repeat the loaded five-seed `WorldAdapter` profile factorial N={2,8,32,128}, B={1,4}, three fresh workers per cell. In each worker and cache mode, run two fresh-profile twins: an audit arm with scale audit and access trace on; and a quiet arm with both disabled. Counterbalance cache order and alternate audit/quiet order by replicate. Record cache activity on both, but use quiet-arm elapsed tick as the primary timing comparison. Audit-arm `hits + misses` must equal `term_eval:ReachableFrom`; off arms must have zero cache stats. All four outcomes in each worker must produce identical graph state, expected mirror edges, progress, and a zero-work terminal tick; audit arms additionally require exact trace parity.

Peak payload remains the same documented structural estimate as v1.1: key/value objects, result-slice contents and Arc headers, spilled footprint storage, excluding map buckets/control bytes and allocator overhead. It is not RSS. The panel does not estimate natural browser-page prevalence or run Chromium.

## Artifacts

Runner: [`scripts/substrate_browser_profile_reachable_cache_v1_2.py`](../../../scripts/substrate_browser_profile_reachable_cache_v1_2.py)  
Analyzer: [`scripts/analyze_substrate_browser_profile_reachable_cache_v1_2.py`](../../../scripts/analyze_substrate_browser_profile_reachable_cache_v1_2.py)  
Lock: `evaluation/substrate_capability/browser_profile_reachable_cache_v1_2_lock_20260928.json`  
Raw: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_2_20260928.json`  
Analysis: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_2_analysis_20260928.json`
