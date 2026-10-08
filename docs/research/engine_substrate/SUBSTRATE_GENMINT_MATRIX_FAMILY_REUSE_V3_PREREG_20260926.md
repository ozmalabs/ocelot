# GenMint matrix-family transfer and reuse v3 preregistration

## Question

Across a broader set of invertible 2-D integer transforms, how often does the full-seed GenMint path acquire the intended generator from the training observation, transfer it to held-out geometries, and amortize its acquisition cost as application count increases?

## Design

Run a randomized matched factorial over six matrices: prior `[1,1,0,2]`, shears `[1,0,1,1]`, `[1,1,0,1]`, and `[1,2,0,1]`, coordinate swap `[0,1,1,0]`, and signed quarter-turn `[0,1,-1,0]`. Cross each with the three fixed predicate layouts from v2 (`adjacent_01`, `opposite_03`, `adjacent_12`), GenInfer disabled/enabled, reuse prefixes K={0,4,16}, and three fresh-process replicates. This yields 108 randomized design cells per replicate and 324 workers total. Each worker starts from a fresh full core seed, presents the six-relation training observation, then applies the matrix to K independently generated four-relation held-out bases. The 16 held-out geometries and training point set are fixed from the v2 seed and source, to make the matrix-family extension the sole planned factor change. Record complete statuses, minted generators, selected transforms/residuals, per-stage closure wall times, quanta, graph size, and process RSS.

## Primary measures and gates

1. Training acquisition: exact intended matrix present as a linear DimensionGenerator after training; also report recognized status without intended acquisition.
2. Transfer: for every application selecting the training-acquired generator, independently apply its matrix and residuals to the held-out base and score exact target rows. Report routes separately for preexisting, training-acquired, application-minted, application-reused, and no-generator paths.
3. Economics: compare matched enabled/disabled total closure cost and training/application components at each K. Report medians and per-matrix/layout strata; do not infer general break-even from pooled-only results.
4. Integrity: exact worker count, unique PIDs, locked source/native inputs, randomized schedule reconstruction, balanced cells, independent input reconstruction, repeated outcome determinism, and complete output fields. Any failure is reported, not silently filtered.

## Claim boundary

This is a controlled authored 2-D integer-linear family on one host and one full-seed path. It is not a natural-task prevalence estimate, a broad learning guarantee, or commodity-scale measurement. The matrices are selected probes; heldout geometry diversity is controlled but does not sample the world. Application prediction conditional on route must not be conflated with training acquisition. Report all misses and deferred-acquisition tails.
