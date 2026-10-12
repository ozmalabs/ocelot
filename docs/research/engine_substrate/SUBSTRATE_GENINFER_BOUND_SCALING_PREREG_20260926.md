# GenInfer data-derived bound scaling preregistration

## Question

How do exact GenInfer candidate work and direct native Term latency scale with its data-derived 2-D matrix bound, and does a same-bound predicate-corruption control remain explicitly unexplained?

## Workload and method

Use coordinate scales s=1/2/3/4 over one locked four-relation asymmetric L signature `[(0,0),(s,0),(2s,0),(2s,s)]`, all with predicate `cell` and value `red`, typed as `pred,coord:r,coord:c,val`. Apply the fixed shear matrix `[1,1,0,1]`, mapping `(r,c)→(r+c,c)`. Per source formula the data-derived bound is B=3s; expected candidate calls are `(2B+1)^4−1` (identity excluded). For each scale, make two fresh-core calls: the exact positive and a null with one relation predicate changed to `noise`. Add only the single base ShapeSignature; call the production Rust `GenInfer` Term directly with `max_dims=2`; preserve complete result dictionaries, wall/process CPU time, source lock, and process identity. Three fresh workers each cover all four scales. This isolates candidate-search scaling; automatic full-seed mint/redecode behavior is covered by the separate GenInfer measurement and is not claimed here.

## Gates and limits

Require three fresh stable workers, 24 calls total, source/build fingerprints unchanged, independently reconstructed B and candidate counts, exact matrix/residual-free positive outcomes, explicit null refusal at each scale, complete result fields, and positive timings. Report raw points and medians; no asymptotic fit or extrapolation beyond s≤4. This is a fixed 2-D integer-linear family, one transform and one selected negative-control class, not general hypothesis-learning or noise-distribution evidence.
