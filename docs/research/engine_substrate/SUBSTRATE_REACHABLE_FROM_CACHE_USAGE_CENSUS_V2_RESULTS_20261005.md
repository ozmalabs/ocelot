# Current-source ReachableFrom usage census v2

## Scope and result

The census searches all 1,016 current `seeds/**/*.json` manifest paths for typed `ReachableFrom` Term nodes, then parses all 880 Python source files under `domains`, `substrate`, `worlds`, and `runners/dsl/python` for literal references and selected helper call sites. It finds two typed Term instances, both in `seeds/browser_affordance_reach.json` (the session-to-element containment query in each of its two rules), three Python literal references, and five calls to the helper routes: three `grounding_reach` calls, one `flag_ungrounded_confident` call, and one `seed_dependency_closure` call. All authored seed Terms are concentrated in this browser rule family.

Current source still shows `PySubstrate.evaluate()` constructing a fresh default `EvalCache` per call, and the high-level `substrate_rs.Substrate` wrapper still has no cache toggle. The rule-rewrite cache is owned by the native Substrate and its explicit toggle is available on native PySubstrate. Thus repeated browser rule queries can share entries during a stable graph phase; the direct grounding and frozen-seed helpers do not share this memo across their separate host evaluation calls.

The census is a source-frequency proxy, not runtime activation or natural-task prevalence. Its JSON manifest scan was run over the full path inventory with ripgrep's exact typed-node search, then parsed the one candidate manifest. The inventory records a digest of the complete seed path list and hashes every parsed source file and candidate manifest; the engine/current tree is not a pristine checkout.

## Evidence and next gate

The source findings align with existing dynamic evidence: the corrected browser rule profile passes semantic parity and reports large synthetic DOM-shaped cache reuse; the native same-graph panel and v1.2 cache/materialization comparison verify shared rewrite-cache accounting. They do not establish real BrowserWorld prevalence or live-page performance. Since the only source-authored seed family with typed reachability is the browser affordance profile, the next decisive gate is an actual BrowserWorld task session with cache telemetry and representative changing graph phases, followed by a broader task-route audit only if new typed consumers are found.

Artifacts: [runner](../../../evaluation/substrate_capability/audit_reachable_from_cache_usage_v2.py), [machine-readable capture](../../../evaluation/reports/substrate_reachable_from_cache_usage_v2_20261005.json), [cache/materialization comparison](REACHABILITY_CACHE_MATERIALIZATION_COMPARISON_V1_2_RESULTS_20261005.md), and [browser-profile cache result](SUBSTRATE_BROWSER_PROFILE_REACHABLE_CACHE_V1_3_RESULTS_20260928.md).
