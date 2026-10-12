# Term-literal joint proposals v1 preregistration

## Question

Can joint Cartesian assignments of all literal-bearing guard variables repair the higher-arity misses in the frozen adversarial family, and how does that proposal cost grow from arity two to four?

## Paired policies

Use the existing six locked point/interval guards, oracle, training and prior examples, disjoint holdout, native disagreement selector, and eight-label cap. Compare (A) edge plus pairwise literal proposals with (B) the same slate plus assignments formed from the Cartesian product of direct literal values for all literal-bearing variables in each Term. Keep unrelated variables at zero. Deduplicate by IEEE-754 bit pattern and exclude every training, prior, or holdout row. Cap generated joint rows at 64; report the generated count and abort rather than silently truncate if exceeded. Do not change terms or inputs.

## Measures and analysis

Lock source hashes, upstream capture/analysis hashes, each panel digest, policy definitions, and the 64-row cap. Independently replay proposal generation, disjointness, selector transcript, output class, holdout scoring, native evaluations, proposal counts, and timings. Report per-cell false candidate acceptance, labels, native evaluations, and elapsed time. The targeted repair gate requires all six false candidates to be rejected by the joint arm within eight labels. This finite authored family is a stress test, not a natural-task prevalence estimate or an equivalence proof.

## Expected scaling boundary

Joint rows grow as the product of literal values per variable. The 2/3/4-variable sweep measures only small products (at most 16 rows here); larger supports may require selective combination or adaptive search. This experiment measures completeness for this family and exposes combinatorial cost; it does not claim polynomial behavior in guard size.
