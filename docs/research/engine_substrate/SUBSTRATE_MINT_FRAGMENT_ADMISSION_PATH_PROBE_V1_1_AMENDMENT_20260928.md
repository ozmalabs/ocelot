# Finite-key fragment admission-path probe v1.1 amendment

Date: 2026-09-28  
Status: amendment before v1.1 capture; v1 raw and analysis are preserved and excluded from confirmatory counts.

## V1 deviation and cause

The v1 runner completed three workers and all four route rows, but its independent analyzer failed two gates. Direct `add_rule`, `import_rules`, and CAS revision each accepted the checker-rejected `add_node` rule in 3/3 workers. The graph self-mint row did not install a rule in 3/3 workers. Source inspection explains the fixture error: v1 constructed `WorldAdapter(seeds=())` and called its default `tick()`. The default cognitive-cycle plan selects struct rules when there is no enabled dual-process policy, so this call does not necessarily run graph-resident `Rule` nodes. The row was therefore not evidence that graph self-mint rejects the rule.

The v1 raw capture remains at [`substrate_mint_fragment_admission_path_probe_v1_20260928.json`](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_20260928.json), and its failed independent analysis remains at [`substrate_mint_fragment_admission_path_probe_v1_analysis_20260928.json`](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_analysis_20260928.json). No v1 files will be overwritten.

The first v1.1 setup worker reached the self-build path and installed the rule, but its capture serialized hashes for every JSON file under `seeds/` even though this fixture explicitly boots with `seeds=()`. That produced an 82.9 MB, unscored pilot. The pilot is preserved in compressed form as [`v1.1 pilot capture`](../../../evaluation/reports/substrate_mint_fragment_admission_path_probe_v1_1_pilot_20260928.json.gz). The confirmatory lock omits unrelated seed-tree hashes; it continues to hash `WorldAdapter`, `boot_core`, the native cycle/parser/engine sources, native build, checker, protocol, runner, and analyzer. The graph-rule fixture itself and all route arms are unchanged.

## V1.1 change

The v1.1 graph self-mint arm calls the explicit `run_cycle("graph_then_struct", 100)` plan, whose native cycle dispatch directly invokes `graph_rules::run_graph_rules_opts` before struct rules. This isolates the graph-resident Rule compilation path from optional/default cycle-policy selection. The newly compiled rule still has a deliberately absent match edge, and the runner records the cycle report and confirms that no such edge exists. One unscored setup worker may be run before locking; its output must be retained as a pilot and excluded from the three confirmatory workers. All other fixture data, route arms, replicates, and claims are unchanged.

The v1.1 lock additionally hashes `cognitive_cycle.rs`. V1.1 writes new uniquely versioned lock, raw, and analysis files. It does not replace v1 evidence. An analyzer failure, worker error, lock drift, or route mismatch remains a failed result and must be retained.
