# Bigville induced-boundary variable elimination preregistration

## Question

After exact component messages have been computed, can min-sum variable elimination on their induced boundary factor graph replace explicit `d^k` assignment enumeration while preserving whole-graph MAP?

## Design

Use cast prefixes N=15/25, three deterministic matchings of up to six disjoint cross-resident pairs among residents 0–11, boundary dimensions k=0/2/4/6/8/10/12, and three fresh worker processes. Each matching pattern has six pairs with distinct endpoints; k selects the first k/2 pairs. Pattern 0 pairs (0,1),(2,3),(4,5),(6,7),(8,9),(10,11); pattern 1 pairs (0,7),(1,8),(2,9),(3,10),(4,11),(5,6); pattern 2 pairs (0,4),(1,9),(2,6),(3,11),(5,10),(7,8). Pattern-specific endpoint topics are respectively `(trust_mayor,claim_credible)`, `(trust_mayor,world_safe)`, and `(claim_credible,debtor_trustworthy)`; weights in matching order are `(0.25,-0.25,0.5,0.25,-0.25,0.5)`. This extends the earlier k≤6 message-reuse envelope. Retain graph-discovered interior components and exact component message tables. Represent every boundary unary, boundary-boundary pairwise factor, and component message table as a finite-scope min-sum factor. Eliminate boundary variables using deterministic min-fill order (ties by variable ID), storing argmin backpointers. Recover the boundary MAP in reverse elimination order, then recover each interior assignment from its cached component message argmin. Score the full assembled state independently and compare its exact energy against whole-graph min-fill/JT.

Record boundary primal-graph min-fill width, variable order, component message work, each elimination bucket's union-scope size and row/evaluation count, total factor-table entries processed, peak table entries, and timings for message construction, boundary elimination/reconstruction, and global JT. Compare measured elimination row count with the exhaustive `d^k` boundary assignment count; this is the algorithmic predictor, while measured timings include Python table overhead.

## Gates and limits

Require source/build locks, three fresh workers, all 42 cells, exact graph-discovered boundary/interior factorization, correct message count, deterministic valid elimination orders/backpointers, complete domain-valid global states, independent whole-model energy agreement to 1e-7, and reconstructed operation counts. This is an offline Python algorithm experiment over bounded controlled topology. It does not establish natural boundary graph width, native frame inference, or end-to-end speedup. The global JT comparator is already width 2 here; beating it is not presumed.
