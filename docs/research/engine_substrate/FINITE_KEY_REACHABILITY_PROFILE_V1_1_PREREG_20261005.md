# Finite-key reachability profile v1.1 reuse preregistration

## Question

Does one-time closure and materialization of the restricted two-rule reachability profile repay its cost when the resulting relation serves repeated all-source query batches?

## Fixed profile and workloads

Use the exact v1 profile: direct `[x, link, y] -> add_edge(x, reachable, y)` and transitive `[x, reachable, y], [y, link, z] -> add_edge(x, reachable, z)`. Cross path, outward binary tree, and four-layer complete-bipartite DAGs at N=8,16,32,64 with three fresh-substrate repetitions (36 cases). For each case, compare Q=1,2,4,8 batches, each containing one query from every source. The direct arm uses native `ReachableFrom(start, link)`; the materialized arm uses `Neighbours(start, reachable)` after closure.

## Accounting and correctness

Measure graph construction as common setup. Direct end-to-end wall/CPU total is graph setup plus Q direct batches. Materialized total is graph setup plus rule installation plus closure plus Q lookup batches. Preserve separate component times. Each batch must match an independent DFS for every source. Require the profile checker to admit the rules, closure to reach its finite progress bound, all 36 cases and all four Q values to be present, source fingerprints to remain stable, and the unrestricted-mint negative control to be refused. Report medians by topology and N, including profile/direct ratio at each Q; only report a break-even where profile total is lower.

## Limits

This is a bounded synthetic reuse experiment for one authored profile. It does not establish natural-task prevalence, a registered or enforced restricted mode, general scaling, or a universal CPU advantage. Timing is local to this implementation and fixed query ordering.

## Reproduction

Run `python3 evaluation/substrate_capability/finite_key_reachability_profile_v1_1.py --lock`, then the runner without arguments, then `python3 evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_1.py`.
