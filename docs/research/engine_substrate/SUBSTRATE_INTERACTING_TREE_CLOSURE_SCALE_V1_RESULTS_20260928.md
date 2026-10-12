# Interacting tree closure scale v1 results

**Run date:** 2026-09-28  
**Evidence grade:** source-locked 36-worker native panel; runner gates passed and the independent analyzer passed 11/11 checks.  
**Question:** how do two interacting monotone rules scale on balanced binary trees versus high-fanout stars, with audit instrumentation on and off?

## Result

Each graph has N attributed `TreeItem` nodes, 2(N−1) directed typed edges (both `child` and `parent`), one initially active root, and N−1 pending nodes. `activate_ready` changes pending children of active parents to ready; `commit_ready` changes ready nodes to active. All 36 workers reached the exact terminal oracle: N nodes, 2(N−1) edges, all nodes active, no pending/ready nodes, fixed-point status, zero budget overshoot, and valid sampled parent/attribute values. Each size/topology/audit cell has three fresh processes.

Audit-off closure medians and audit counters are:

| N | Topology | Median closure CPU / wall | Passes (audit-on median) | Candidate tests (each of 3 audit-on workers) | Attr-set attempts | Live RSS increase | Process peak RSS range |
|---:|---|---:|---:|---:|---:|---:|---:|
| 10,000 | Balanced | 42.2 / 42.2 ms | 14 | 279,972 | 19,998 | 9.8 MB | 42.7–43.1 MB |
| 10,000 | Star | 12.2 / 12.2 ms | 2 | 39,996 | 19,998 | 10.1 MB | 40.8–41.5 MB |
| 100,000 | Balanced | 488.6 / 489.5 ms | 17 | 3,399,966 | 199,998 | 66.4 MB | 95.9–96.3 MB |
| 100,000 | Star | 132.7 / 132.7 ms | 2 | 399,996 | 199,998 | 46.6 MB | 93.2–94.5 MB |
| 1,000,000 | Balanced | 6.11 / 6.11 s | 20 | 39,999,960 | 1,999,998 | 428.3 MB | 642.2–642.9 MB |
| 1,000,000 | Star | 1.68 / 1.68 s | 2 | 3,999,996 | 1,999,998 | 456.8 MB | 832.7–832.8 MB |

For every audit-on cell, each rule accounts for exactly N−1 attribute-set attempts, for 2(N−1) total. Candidate counts are fully attributed to the two rules and reconcile with the global counter; there are no unattributed candidate tests. Audit-on closure is slower than audit-off (about 2.3–3.0× in these medians), so the uninstrumented measurements are the primary timing result. Peak RSS includes construction and the terminal validation/readback path; it should not be read as closure-only memory. In particular, star peak RSS exceeds balanced-tree peak RSS at 1M despite the shorter closure, while live post-closure RSS is similar.

## Interpretation

At equal N and edge count, topology changes both the number of closure passes and the matcher work. The balanced tree requires 14/17/20 passes and about ten times as many candidate tests as the star at each size; the star settles in two passes. From 10k to 100k to 1M, star closure time grows roughly with N in this three-point panel. Balanced-tree time and candidate work grow faster, consistent with the increasing propagation depth and extra matcher scans. These are descriptive curves for this rule pair and these two topologies; they are not a general asymptotic theorem.

The panel goes beyond the single-rule ring by introducing a second interacting rule and two topologies, but it remains a favorable monotone status-propagation program. It does not cover destructive effects, rule conflict, external callbacks, inference, learned frames, or varied pattern arity. The result demonstrates why node/edge counts alone are insufficient predictors of closure work and why scale claims need topology and rule-structure controls.

## Reproduction and custody

- Preregistration: [`SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md`](SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PREREG_20260928.md)
- Pre-lock pilot amendment: [`SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md`](SUBSTRATE_INTERACTING_TREE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md); three 10k setup pilots are excluded from the confirmatory panel.
- Runner: [`substrate_interacting_tree_closure_scale_v1.py`](../../../scripts/substrate_interacting_tree_closure_scale_v1.py)
- Independent analyzer: [`analyze_substrate_interacting_tree_closure_scale_v1.py`](../../../scripts/analyze_substrate_interacting_tree_closure_scale_v1.py)
- Source lock: [`interacting_tree_closure_scale_v1_lock_20260928.json`](../../../evaluation/substrate_capability/interacting_tree_closure_scale_v1_lock_20260928.json)
- Raw capture: [`substrate_interacting_tree_closure_scale_v1_20260928.json`](../../../evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json)
- Independent analysis: [`substrate_interacting_tree_closure_scale_v1_analysis_20260928.json`](../../../evaluation/reports/substrate_interacting_tree_closure_scale_v1_analysis_20260928.json)
