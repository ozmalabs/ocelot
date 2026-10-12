# Clause-aware literal proposals v1 preregistration

## Question

Can direct comparison constraints in a Term conjunction produce a separating input without enumerating the full literal Cartesian product?

## Paired policies

Use the locked noise-padded four-variable candidate from the proposal-budget stress. Compare the existing exhaustive 256-row arm, the 64-row fail-closed arm, and a clause-aware arm. The clause-aware generator visits conjunctive branches containing direct `Var`/numeric-`Lit` comparisons, tests literal endpoints and adjacent IEEE-754 values against each variable's constraints, and emits at most one satisfying assignment per branch. It skips assignments already in training, prior, holdout, or the pairwise slate. It may use at most eight oracle labels. No candidate, oracle, or heldout data change.

## Measures and gates

Lock current sources and the upstream stress capture. Independently reconstruct clause extraction, satisfying assignments, proposal disjointness, selector transcripts, final decisions, holdout errors, native Term evaluations, constraint checks, proposal counts, and wall/CPU time. Success requires rejecting the false candidate with at most two new clause proposals and one label, with fewer generated proposals than exhaustive enumeration. This authored case cannot establish coverage of arbitrary Boolean Terms or natural-task prevalence.

## Claim boundary

The proposal generator is a host-side experiment policy over native Term evaluation and selection. It is not evidence that the substrate autonomously learned clause extraction, and it does not prove semantic equivalence beyond measured queries.
