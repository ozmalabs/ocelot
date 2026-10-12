# Clause contradiction and aliasing v1 results (2026-10-04)

## Result

The twelve-panel locked capture passes all nine independent replay gates. It
includes the six prior transfer/unsupported controls and six new cases. The
solver classifies contradictory bounds, an interval with no representable
binary64 value, and a bound beyond the largest finite float as
`proven_unsat`; each produces no clause query. The repeated-compatible-bound
case is satisfiable and is rejected with one label using a query already in
the pairwise slate. A direct cross-variable equality is unresolved; the
clause-aware policy requests help while the false candidate survives. The
mixed contradiction-plus-alias guard uses one base-slate label to remove the
false candidate; after that, it accepts the remaining identity even though
the unresolved branch was not solved. Unsupported `Plus` and `Times` guards
also request help with zero labels. Clause-aware arms have no false
acceptances on the registered holdouts.

The pairwise controls still falsely accept the interval arity-3/4, arithmetic,
and cross-variable-alias candidates in the corresponding cells. This keeps
the evidence discriminative: abstention and clause proposals account for the
improvement, not an easier panel.

## Proof fragment and limits

The unsatisfiability result applies to conjunctions of direct unary numeric
comparisons over finite binary64 values. For each variable, the evaluator
checks every literal endpoint and adjacent representable floats. For a
conjunction of unary equality/order bounds, any nonempty finite-float interval
contains one of those candidates; if none satisfies, the conjunction is
empty in the registered finite domain. The upper-edge control also verifies
that infinities are excluded from this domain. This is a small proof
fragment, not a general Term solver. Cross-variable relations remain
unresolved, and clause-derived candidate discovery is harness-authored.

The results do not prove unrestricted equivalence or full coverage for every
supported branch. A satisfiable clause witness can be blocked by training,
prior, holdout, or proposal overlap; the policy tracks such a branch as
unresolved and asks for help if the false candidate remains. The next gate is
generated mixed formulas with conjunctions, aliases, and disjunctions, plus
independent proof-oracle checks for the finite-float contradiction fragment.

## Reproduction

- [Protocol](CLAUSE_CONTRADICTION_ALIASING_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/clause_contradiction_aliasing_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_clause_contradiction_aliasing_v1.py)
- [Lock](../../../evaluation/substrate_capability/clause_contradiction_aliasing_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/clause_contradiction_aliasing_v1_20261004.json)
- [Analysis](../../../evaluation/reports/clause_contradiction_aliasing_v1_analysis_20261004.json)
