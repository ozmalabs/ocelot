# Clause contradiction and aliasing v1 preregistration

## Question

Can clause-aware query synthesis distinguish a directly provable empty conjunction from unsupported variable-alias constraints, and does it abstain on the latter?

## Panel

Extend the six locked clause-transfer cases with six controls: contradictory direct bounds, a gap between adjacent binary64 values, a finite-domain upper-edge case, repeated compatible bounds on one variable, a satisfiable cross-variable equality alias, and a disjunction containing both a contradiction and an unsupported alias. Candidate form is identity OR guard; oracle, training, prior, and base selector remain unchanged. Satisfiable false guards have disjoint holdout witnesses.

## Policy and gates

Classify direct `Var`/numeric-`Lit` conjunctions as satisfiable with a constructed witness, proven unsatisfiable over finite binary64 values, or unresolved. A direct `Var`/`Var` relation or other unsupported node is unresolved. Offer witnesses from satisfiable branches. If a satisfiable branch cannot yield a disjoint query proposal, treat coverage as unresolved. If a false candidate survives while any branch is unresolved, request help even when the finite proposal slate agrees. A proved-unsatisfiable branch contributes no proposal and does not itself force help. Independently replay status classification, satisfiability witnesses, proposal disjointness, selector, holdout, and resource counts under the eight-label cap.

## Limits

The proof fragment is conjunctions of direct unary numeric comparisons over finite binary64 values. This experiment does not prove completeness for arbitrary Terms or estimate natural-task frequency.
