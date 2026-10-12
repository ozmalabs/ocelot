# Finite-key closure self-join gate v1.1 — results (2026-09-26)

## Outcome

All **72/72 native cases** pass after the preregistration's edge-universe count was corrected in a versioned amendment. The independent positive-rule interpreter matches every terminal native graph, analyzer admission succeeds, each native run reaches `fixed_point`, progress stays within the recomputed fact bound, and terminal semantics agree across all three rule orders. The explicit null strata activate exactly their intended subset of rules.

The first analysis was preserved and failed the blanket E=5 expectation for null strata. The amendment correctly defines E as the number of edge types present initially or insertable by the rules: E=5 for the rich stratum, E=4 for self-only and reciprocal-pair strata. A match-only type with no facts and no writer cannot enter the finite edge universe. See [amendment](SUBSTRATE_FINITE_KEY_CLOSURE_SELF_JOIN_V1_1_AMENDMENT_20260926.md) and retained [v1.0 failed analysis](../../../evaluation/reports/mint_termination_self_join_v1_analysis_v1_0_attempt_20260926.json).

## Design, interpreter and provenance

The 72-case matrix covers rich reciprocal triangles at N=3/6/9, self-only graphs at N=3/6/9, and reciprocal pairs at N=4/6; each crosses three rule orders and three freshly constructed native substrates. Rules exercise `loop(x,x)`, reciprocal `rel(x,y) ∧ rel(y,x)`, and a three-edge cycle join with repeated variables. A standalone interpreter applies rule matches by variable unification and insertion-only effects until stable. A separate analysis pass runs the production static checker, reconstructs each reference closure, normalizes node IDs, and compares exact edge/node sets.

Evidence: [preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_SELF_JOIN_PREREG_20260926.md), [v1.1 amendment](SUBSTRATE_FINITE_KEY_CLOSURE_SELF_JOIN_V1_1_AMENDMENT_20260926.md), [native runner](../../../scripts/verify_mint_termination_self_join_v1.py), [independent analyzer/interpreter](../../../scripts/analyze_mint_termination_self_join_v1_1.py), [raw capture](../../../evaluation/reports/mint_termination_self_join_v1_20260926.json), [v1.1 analysis](../../../evaluation/reports/mint_termination_self_join_v1_1_analysis_20260926.json). Raw provenance records engine/commit/native hash, runner and prereg hashes, all input and final graphs, and native run reports.

## Representative results

All three rule orders and all replicates agree per stratum. Native closure completes in two passes throughout; it records one progressing firing for null strata and three for rich triangles.

| Family | N | Initial edges e₀ | E | Bound B | Progress | Final witness tags | Final nodes | Final edges |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| rich triangles | 3 | 9 | 5 | 174 | 3 | L,R,T | 6 | 18 |
| rich triangles | 6 | 18 | 5 | 390 | 3 | L,R,T | 9 | 36 |
| rich triangles | 9 | 27 | 5 | 696 | 3 | L,R,T | 12 | 54 |
| self only | 3 | 3 | 4 | 144 | 1 | L | 4 | 6 |
| self only | 6 | 6 | 4 | 321 | 1 | L | 7 | 12 |
| self only | 9 | 9 | 4 | 570 | 1 | L | 10 | 18 |
| reciprocal pairs | 4 | 4 | 4 | 195 | 1 | R | 5 | 8 |
| reciprocal pairs | 6 | 6 | 4 | 321 | 1 | R | 7 | 12 |

Bounds use `B=M+E(N+M)^2−e₀`, with M=3 syntactic literal mint signatures. The bound is loose: all recursive output facts add witnesses/edges but do not activate more rule families beyond the declared triggers.

## Claim boundary

This demonstrates native repeated-variable and self-join matching on the three exercised positive schemas, including exact refusal of unsatisfied L/R/T patterns and order-independent closure. It does not establish completeness of the rule parser or static analyzer over all possible accepted programs, arbitrary join widths, high variable counts, performance scaling, or behavior with nonmonotone effects. The fragment theorem remains restricted to finite-key monotone insertion; unrestricted minting, mutation, deletion, and external state are outside scope.

## Next gate

Test multiple independent written edge types in one recursive rule program, rules with repeated variables in source and target positions, and initial attributed-edge refusal. Independently enumerate analyzer accepted/rejected syntactic variations and verify the runtime parser uses the same field/effect interpretation.
