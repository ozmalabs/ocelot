# Finite-key reachability profile v1.2 crossover replication preregistration

## Question and selection

Replicate the v1.1 apparent cost crossover (binary tree, N=64, Q=8 all-source batches) while reducing fixed-order and small-repetition timing risk. Include binary-tree N=128 as a size holdout and ternary-tree N=64,128 as topology holdouts. The v1.1 report selected these cells before this protocol was written; no outcomes from v1.2 are inspected during selection.

## Workloads

Use the same admitted two-rule profile: direct `[x, link, y] -> add_edge(x, reachable, y)` and transitive `[x, reachable, y], [y, link, z] -> add_edge(x, reachable, z)`. A binary tree uses heap children `2p+1,2p+2`; a ternary tree uses `3p+1,3p+2,3p+3`, truncated at N. Cross shapes binary/ternary with N=64,128. Run 15 fresh-substrate repetitions per cell (60 captures). For Q=1,2,4,8,16,32, a batch asks every source once. Alternate which query arm runs first by repetition and Q parity.

## Cost and correctness accounting

The direct arm total is common graph construction plus Q direct `ReachableFrom(start, link)` batches. The profile arm total is common graph construction plus two-rule installation plus closure plus Q `Neighbours(start, reachable)` batches. Report wall and CPU components and end-to-end totals. Compute an independent DFS oracle and compare every source output from both query forms, plus the full materialized relation. Require checker admission, fixed point within the finite-fact bound, complete unique matrix, stable source lock, and rejection of an unrestricted fresh-node negative control. Summarize medians and paired per-repetition ratios; describe a crossover only if the median paired ratio is below one and at least 12/15 replicate totals favor materialization at that Q.

## Limits

This targeted synthetic replication tests timing stability and reuse on two tree families. It does not estimate natural-task prevalence, general asymptotic behavior, or prevalence of reusable derived relations. The selected cells and fixed query implementation limit external validity.

## Reproduction

Run `python3 evaluation/substrate_capability/finite_key_reachability_profile_v1_2.py --lock`, run it again without arguments, then run `python3 evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_2.py`.
