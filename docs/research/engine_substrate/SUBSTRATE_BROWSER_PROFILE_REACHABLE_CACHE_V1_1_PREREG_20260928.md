# Browser profile cache telemetry v1.1 preregistration

**Question:** On the loaded five-seed BrowserWorld adapter tick, how many repeated `ReachableFrom` calls hit/miss the opt-in memo, how many entries are simultaneously live, and what is the cache's estimated peak value/footprint payload?

This is a telemetry extension of the source-locked v1 profile replay, not a new workload family. It repeats the same N={2,8,32,128}, B={1,4}, three-worker factorial through the normal `WorldAdapter.tick()` path. V1.1 retains all v1 graph, progress, matcher-counter, access-trace, terminal no-op, and source/native provenance gates. Each arm additionally records cumulative cache hits/misses, current entries and map capacity, result values, adjacency-footprint nodes, current estimated payload bytes, peak entries, and peak estimated payload bytes.

The byte estimate includes per-entry key/value structs, reachable result-slice elements and Arc headers, and spilled footprint storage. It excludes hash-table buckets/control bytes, allocation metadata, allocator fragmentation, and retained bucket slack; it is a payload estimate, not RSS. Peak values are captured before the terminal no-op tick. Cache disabled should record zero activity and zero entries. Cache enabled should have nonzero hit and miss counts, a nonzero peak entry count and payload estimate, and `hits + misses == term_eval:ReachableFrom` for this rule-only query workload. Pairwise semantic and trace parity remains mandatory.

No Chromium launch is required; the previous direct launch failed under the sandbox. These results cannot estimate real-page frequencies or total BrowserWorld process memory.

## Artifacts

Runner: [`scripts/substrate_browser_profile_reachable_cache_v1_1.py`](../../../scripts/substrate_browser_profile_reachable_cache_v1_1.py)  
Analyzer: [`scripts/analyze_substrate_browser_profile_reachable_cache_v1_1.py`](../../../scripts/analyze_substrate_browser_profile_reachable_cache_v1_1.py)  
Lock: `evaluation/substrate_capability/browser_profile_reachable_cache_v1_1_lock_20260928.json`  
Raw: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_1_20260928.json`  
Analysis: `evaluation/reports/substrate_browser_profile_reachable_cache_v1_1_analysis_20260928.json`
