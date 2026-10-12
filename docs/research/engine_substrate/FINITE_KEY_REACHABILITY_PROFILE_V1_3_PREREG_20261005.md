# Finite-key reachability profile v1.3 high-reuse follow-up preregistration

## Question

Do the binary and ternary N=128 tree cases approach a robust cost crossover when each materialized relation is reused for substantially more all-source query batches?

## Fixed selection and workload

This follow-up is selected from v1.2 before observing v1.3 outcomes: binary-tree and ternary-tree at N=128, the two cells with median paired ratios closest to one at Q=32. Use the same two-rule finite-key reachability profile and exact tree generators. Run 30 fresh-substrate repetitions per topology. Compare Q=32,64,128,256 batches, each querying every source. Alternate the query arm order by repetition and Q parity as in v1.2.

## Accounting and gates

Direct total is common graph construction plus repeated native `ReachableFrom(start, link)` batches. Profile total is common setup plus rule installation, closure, and repeated `Neighbours(start, reachable)` batches. Preserve wall and CPU component timings and pair the two arm totals within each case/repetition. Independently recompute the relation with DFS and require all direct and materialized answers to match. Require finite-key checker admission, closure fixed point within the fact bound, exact 2×30 case matrix, stable input fingerprints, alternating order, and rejection of unrestricted fresh-node minting. Call a robust crossover only when median paired profile/direct ratio is below one and at least 24/30 repetitions favor materialization at that Q.

## Limits

This targeted synthetic experiment measures high reuse on two tree families at one size. It does not measure natural frequency of reusable relations or establish general asymptotics or system-wide speedup.

## Reproduction

Run `python3 evaluation/substrate_capability/finite_key_reachability_profile_v1_3.py --lock`, run it again without arguments, then run `python3 evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_3.py`.
