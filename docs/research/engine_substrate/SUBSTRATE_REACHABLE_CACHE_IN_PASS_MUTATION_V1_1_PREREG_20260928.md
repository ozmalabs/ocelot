# ReachableFrom in-pass mutation probe v1.1 preregistration

**Question:** Does clearing graph-dependent evaluation state immediately after a progressing rule prevent a later same-pass rule from missing a newly inserted edge?

Construct three ordered rules on one root. Rule 1 reads `ReachableFrom(root, path)` while matching the already reachable node and writes an already-present idempotent marker edge, priming the memo without progress. Rule 2 inserts a second `path` edge from a preinstalled `add_path` trigger. Rule 3 matches a preinstalled `detect` trigger and adds `detected` when its candidate belongs to `ReachableFrom(root, path)`. Cache off is the semantic control. Run each mode in five independent workers; counterbalance mode order. The final least-fixed-point graph must contain `root -detected-> new_target` in both arms.

The initial graph contains `root -path-> old_target`, the probe/marker pair for the old target, and the add_path/detect pair for the new target. Only Rule 2 changes topology. The repaired engine must clear graph-dependent evaluation state immediately after the progressing rule, before the later same-pass consumer evaluates. Cache-on and cache-off runs must finish with identical graphs and progress counts, including the detected edge. Retain exact final graphs, progress counts, loaded read/write sets, cache counters, and provenance. This is a constructed monotone three-rule diagnostic, not a timing claim or a claim about natural task frequency.

## Historical v1 falsifier outcome

The source-locked v1 reproduction produced `detected=true` with cache off and `detected=false` with cache on in all five workers; it returned one progress step in the cached arm and two in the control. The v1.1 implementation run must satisfy the semantic oracle in both modes.

Runner: [`scripts/substrate_reachable_cache_in_pass_mutation_v1_1.py`](../../../scripts/substrate_reachable_cache_in_pass_mutation_v1_1.py)  
Analyzer: [`scripts/analyze_substrate_reachable_cache_in_pass_mutation_v1_1.py`](../../../scripts/analyze_substrate_reachable_cache_in_pass_mutation_v1_1.py)
