# Clause-aware generated guards v1 preregistration

## Question

Does direct-comparison clause extraction transfer across generated interval guards and nested disjunctions, and does the policy abstain on unsupported arithmetic guards?

## Panel

Use six deterministic panels: interval guards at arities 2/3/4 with mixed comparison orientation; a two-branch nested interval disjunction; and unsupported `Plus` equality and `Times` equality guards. Each false candidate is the identity predicate OR an exception guard; the oracle remains identity. Training/prior examples are unchanged; each exception has a disjoint witness in the holdout. Use the same edge/pairwise proposal slate, native disagreement selector, and eight-label cap.

## Fail-closed policy and gates

Split non-target disjunctions into branches. A branch is supported only when it is a conjunction of direct `Var`/numeric-`Lit` comparisons that the solver can evaluate. Emit satisfying assignments for supported branches; flag any unsupported branch. If a false candidate survives and any potentially satisfiable branch is unsupported, return help even when the finite proposal slate agrees. Lock generator, cases, sources, witnesses, and policy. Independently replay branch classification, proposals, selector, final decision, holdout and cost. Require supported controls to resolve and unsupported controls to abstain without false acceptance.

## Limits

Six authored panels test selected arithmetic and Boolean forms, not prevalence or arbitrary-Term coverage. The host-side generator is supplied by the benchmark and is not substrate-acquired.
