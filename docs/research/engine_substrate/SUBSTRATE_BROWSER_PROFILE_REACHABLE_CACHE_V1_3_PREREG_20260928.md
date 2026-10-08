# Browser profile ReachableFrom cache v1.3 preregistration

**Question:** Do the v1.2 shared-footprint implementation and immediate same-pass invalidation preserve semantics and quiet-tick performance with the repaired browser mirror truth-maintenance rule?

V1.1 exposed a source-level cost: `HashMap::get(...).cloned()` cloned each cached `SmallVec<NodeID>` footprint on every hit. V1.2 stores each result/footprint pair behind `Arc` and replays the footprint only while access tracing is enabled. A later correctness repair clears graph-dependent cache state immediately after each progressing rule. The browser seed's cleanup rule now also removes a mirror when its element is no longer reachable; this panel reruns the same audit/quiet cache factorial against that corrected rule set.

Repeat the loaded five-seed `WorldAdapter` profile factorial N={2,8,32,128}, B={1,4}, three fresh workers per cell. In each worker and cache mode, run two fresh-profile twins: an audit arm with scale audit and access trace on; and a quiet arm with both disabled. Counterbalance cache order and alternate audit/quiet order by replicate. Record cache activity on both, but use quiet-arm elapsed tick as the primary timing comparison. Audit-arm `hits + misses` must equal `term_eval:ReachableFrom`; off arms must have zero cache stats. All four outcomes in each worker must produce identical graph state, expected mirror edges, progress, and a zero-work terminal tick; audit arms additionally require exact trace parity.

Peak payload remains the same documented structural estimate as v1.1: key/value objects, result-slice contents and Arc headers, spilled footprint storage, excluding map buckets/control bytes and allocator overhead. It is not RSS. The panel does not estimate natural browser-page prevalence or run Chromium.

## Artifacts

Runner: [`scripts/substrate_browser_profile_reachable_cache_v1_3.py`](../../../scripts/substrate_browser_profile_reachable_cache_v1_3.py)  
Analyzer: [`scripts/analyze_substrate_browser_profile_reachable_cache_v1_3.py`](../../../scripts/analyze_substrate_browser_profile_reachable_cache_v1_3.py)  
Lock: `evaluation/substrate_capability/browser_profile_reachable_cache_v1_3_lock_20260928.json`  
Raw: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_3_20260928.json`  
Analysis: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_3_analysis_20260928.json`
