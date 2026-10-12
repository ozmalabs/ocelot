# Full-seed nonlinear DimInfer codebook ablation preregistration

## Question

Does the production full-seed shape-decode path select the intended held nonlinear transform or short generator composition, transfer it across asymmetric point-set geometries, and avoid novelty quanta—and does removing only the required generator change that outcome?

## Workload

Test eight locked transform sequences over three six-relation asymmetric point sets, with three fresh worker processes per family/geometry cell (72 workers). Primitive families: `rotation90`, `reflection_r`, `reflection_c`, `scale2`, and `cycle4` (modulus 4). Composition families: `rotation90 → cycle4`, `reflection_r → cycle4`, and `rotation90 → scale2`. Every relation is typed `pred,coord:r,coord:c,val`; predicates and values are preserved. Geometry coordinates include wrap-boundary values 0 and 3 for cycle4. For each worker, start two independent full-core states from the same seed snapshot: intact codebook, and a matched ablation with only the generator(s) required by that family removed. Explicitly set `agent.gen_infer_enabled=0` in both states. Apply the sequence to the base, add the target observation, and run the production native rule closure. Preserve the complete observation state, transform records, minted quanta, remaining generator inventory, closure wall time, PID, and start/end source lock.

The ablation is a causal diagnostic of reliance on held generator entries, not a claim that the rest of the codebook is absent. Other seeded generators remain available and may explain an equivalent shape; record those alternate routes as outcomes. The fixed coordinate fixtures and seed generator inventory are defined in the runner and reconstructed independently by the analyzer.

## Primary outcomes and gates

1. Complete 72-cell coverage, three fresh process replicates per family/geometry, unique worker PIDs, no worker failures, stable source/native hashes, and independently reconstructed inputs.
2. Score recognition status separately from exact route. Route success requires the output Transform record's ordered `generators` and `ks` to match the intended sequence and the target to equal the independently generated coordinates.
3. Compare intact vs ablated selected route, status, quanta delta, generator inventory, and closure time. Report alternate-generator explanations, rung-1 explanations, and unresolved/minted outcomes without filtering.
4. Verify that GenInfer is disabled in both arms and that the requested ablation removed exactly the declared generator names.
5. Report per-family and per-geometry results; pooled means do not establish generalization.

## Claim boundary

This measures the shipped 2-D integer-lattice transform codebook and production full-seed rule path on selected synthetic shapes. It tests held-structure application and codebook dependence, not induction of nonlinear primitives, natural-task prevalence, broad composition, or general intelligence. The ablation may reveal equivalences among seeded operators; those are part of the result.
