# Browser affordance mirror truth-maintenance v1 protocol

**Question:** Does the authored `browser_affordance_reach` seed keep `session -has_affordance-> affordance` equal to the reachable-and-present affordance set after topology and presence mutations, with the experimental cache both disabled and enabled?

The prior source-locked public-mutation panel found that removing a `contains` edge shrank `ReachableFrom` while leaving a previously derived mirror edge. The cleanup rule currently handles only `present <= 0`. Amend its where-clause so it removes a mirror when either the affordance element is absent from `ReachableFrom(session, contains)` or `present <= 0`.

Run five fresh paired workers, counterbalancing cache off/on. Each arm boots only the authored browser rule seed and constructs one session, one nested parent, two present leaf elements, and two affordances. Establish the exact initial mirror; then remove the session-to-parent edge (expect 0), restore it (expect 2), set one leaf's `present` to zero (expect 1), restore it (expect 2), remove that leaf's parent-to-leaf edge (expect 1), and restore it (expect 2). After each intervention, run native rules to fixed point and record the full graph, progress count, mirror count, and cache counters. Cache-on/off graphs and counts must match at every checkpoint.

The protocol tests this seed's intended derived mirror semantics under selected public mutations. It does not prove truth maintenance for arbitrary rule families, multiple sessions sharing elements, concurrent changes, or all browser ingestion paths. No timing or natural-prevalence claim is made.

Runner: [`scripts/substrate_browser_affordance_truth_maintenance_v1.py`](../../../scripts/substrate_browser_affordance_truth_maintenance_v1.py)  
Analyzer: [`scripts/analyze_substrate_browser_affordance_truth_maintenance_v1.py`](../../../scripts/analyze_substrate_browser_affordance_truth_maintenance_v1.py)  
Lock: `evaluation/substrate_capability/browser_affordance_truth_maintenance_v1_lock_20260928.json`  
Raw: `evaluation/reports/browser_affordance_truth_maintenance_v1_20260928.json`  
Analysis: `evaluation/reports/browser_affordance_truth_maintenance_v1_analysis_20260928.json`
