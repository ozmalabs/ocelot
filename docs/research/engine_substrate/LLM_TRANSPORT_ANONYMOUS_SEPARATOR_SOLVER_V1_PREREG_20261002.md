# LLM transport anonymous-separator solver v1 preregistration (2026-10-02)

## Question

Can graph-only minimum-separator discovery on each anonymized task graph feed a generic exact solver that preserves monolithic MAP energy and held-out output, and what is the total per-instance search-plus-solve cost?

## Frozen sample and procedure

Use all ten held-out transitions and learned/shuffled controls from the source-locked Qwen3-0.6B L12→L13 transport graph assay, in three fresh workers (60 total cells). Rebuild and extract each live graph. Assign a fresh deterministic pseudorandom permutation of anonymous integer IDs to all 16 variables for each cell; pass only these IDs and the factor graph topology to a graph-only minimum vertex-separator search. Search subsets in increasing size and return every separator at the minimum size that leaves at least two nonempty components.

For each returned separator, run generic exact conditioning: enumerate assignments to separator variables; enumerate each remaining connected component's assignments independently; score unary, internal pairwise, separator, and cross-boundary factors exactly; combine the component minima; and return the best full state. Select the best result across all proposed minimum separators. Compare with the monolithic JT MAP run on the same extracted factors. Charge proposal, all candidate solves, and candidate selection to the structural route. Measure both inference methods without allocation tracing; record process RSS. Score held-out signs only after inference.

## Gates

Require source/native/export locks stable; all 60 cells covered; randomized IDs actually obscure variable construction order; all graphs connected with 16 variables/64 factors; all minimum separators valid and exhaustive through the minimum size; all candidate separator solves valid; selected energy matches JT and direct rescore within 1e-8; returned target signs match JT exactly; graph unchanged; and report proposal, candidate solve, total structural route, and JT timing separately. The analyzer independently validates subset coverage and all result arithmetic.

## Claim boundary

This tests end-to-end graph-only search plus generic exact inference on one fixed complete bipartite K₈,₈ topology from one model/layer pair. Node identities and role labels are hidden from proposal and solver, but topology remains authored and repeated; the candidate proposer is exhaustive and combinatorial. Passing does not show natural cheap-cut prevalence, practical scaling, or autonomous frame learning across varied task structures.
