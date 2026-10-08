# Finite-key reachability profile v1 preregistration

## Question

Can an explicitly authored two-rule restricted profile provide useful graph reachability while staying inside the finite-key termination fragment, and how does materializing its relation compare with the engine's direct `ReachableFrom` query on the same inputs?

## Restricted profile

The complete active profile is fixed to two positive rules with no `where` terms, fresh-node minting, attribute writes, deletes, external effects, or dynamic rule patching. `direct_link`: match `[x, link, y]`, add empty-attribute `[x, reachable, y]`. `transitive_link`: match `[x, reachable, y]` and `[y, link, z]`, add empty-attribute `[x, reachable, z]`. The full pair is admitted by the finite-key checker as a profile. Only this explicit rule list is loaded in the restricted arm.

## Workloads

Evaluate directed path, outward binary tree, and four-layer complete-bipartite DAGs at N=8,16,32,64, with three fresh-substrate repetitions per cell (36 captures). Build the same initial `link` graph in each substrate. Before closure, query `ReachableFrom(start, edge_type='link')` once for every source and retain the exact source-result sets and total query wall/CPU time. Then run the two-rule profile with the analyzer's finite-fact progress bound plus ten steps of budget. Retain the exact graph and native closure report. Independently derive expected reachability with a plain graph traversal; verify all generated `reachable` edges and direct-query answers against it.

## Gates and measures

Admission requires the checker to accept the complete profile; the direct query, independent traversal, and materialized closure relation to agree for every pair; native closure to reach `fixed_point` within the computed bound without overshoot; complete 12-cell/36-repetition coverage; and stable source/native fingerprints. Report graph edge counts, expected reachability-pair count, checker bound, native progress/pass counts, direct all-source query time, profile closure time, setup time, and memory high-water as process-level context. A negative control with unconditional `add_node` must be rejected by the checker and is not executed.

## Claim limits

This measures one authored reachability profile on three finite DAG morphologies. It does not establish that any current registered seed profile is admitted, that the rule domain has general natural-task prevalence, that unrestricted closure terminates, or that the native loader enforces this profile at all mutation/import/restore boundaries. The direct-query comparison is a local performance comparison, not an asymptotic proof.

## Reproduction

Run `python3 evaluation/substrate_capability/finite_key_reachability_profile_v1.py --lock`, then the same runner without arguments, followed by `python3 evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1.py`.
