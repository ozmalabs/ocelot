# Clause-aware literal proposals v1 results (2026-10-04)

## Result

The locked comparison passes all eight independent replay gates. On the same
noise-padded four-variable Term, the exhaustive product has 256 joint rows;
the first-64 budgeted slate does not reach the separating row and correctly
requests help. A clause-aware generator finds one separating assignment by
solving direct comparisons within each conjunctive branch. It checks two
branches and performs 60 scalar constraint checks, then uses one oracle label
to reject the false candidate.

| Policy | New proposals | Total slate | Labels | Decision | Native Term evaluations | Policy time |
|---|---:|---:|---:|---|---:|---:|
| Exhaustive | 256 | 529 | 1 | Accept surviving identity | 1,605 | 26.4 ms |
| Budgeted, cap 64 | 64 | 337 | 0 | Request help | 1,364 | 27.1 ms |
| Clause-aware | 1 | 274 | 1 | Accept surviving identity | 840 | 13.4 ms |

Clause generation itself took 3.22 ms in this one capture, for a combined
measured clause-generation plus policy time of about 16.6 ms. Exhaustive
Cartesian proposal-generation time was not separately captured, so this is
not a complete end-to-end timing comparison. Native Term evaluation counts
exclude the scalar Python constraint checks and should be read alongside the
60-check count. Times are single-run observations.

## Interpretation and limits

This is evidence that a host-side solver for direct comparisons in
conjunctive Term branches can avoid product enumeration on this specific
guard, including when the term contains contradictory noise literals. The
proposal method was authored for the experiment; the substrate provided Term
execution, selector, and state isolation but did not autonomously discover
this method. It covers neither arbitrary nested formulas nor nonlinear,
disjunctive, or cross-variable constraints. Next evaluate generated Boolean
and arithmetic guard families, count parse/constraint work, include formulas
that require search across disjunctions, and require abstention whenever no
verified satisfying assignment is found. This does not establish general
proposal tractability or unrestricted semantic equivalence.

## Reproduction

- [Protocol](CLAUSE_AWARE_LITERAL_PROPOSALS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/clause_aware_literal_proposals_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_clause_aware_literal_proposals_v1.py)
- [Lock](../../../evaluation/substrate_capability/clause_aware_literal_proposals_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/clause_aware_literal_proposals_v1_20261004.json)
- [Analysis](../../../evaluation/reports/clause_aware_literal_proposals_v1_analysis_20261004.json)
