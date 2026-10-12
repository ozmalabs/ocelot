# Finite-key closure rule-interaction gate v1 — results (2026-09-26)

## Outcome

All **36/36** native cases and all independent analyzer gates pass. Three different positive rule bodies, including two-edge joins and five total edge types, produce exact reference closures in each of three installation orders. Every native call reports `fixed_point`, all native final node/edge graphs equal an independently interpreted monotone closure, and all progress counts are below the analyzer's finite-fact bound. Terminal semantics are invariant to ABC/CBA/BCA order; convergence passes vary with order as expected (ABC: 2 passes; CBA/BCA: 3).

## Design and evidence

The preregistered matrix crosses N={4,8}, cycle/path initial graphs, ABC/CBA/BCA rule order, and three fresh substrate constructions (36 total). Initial graphs carry separate directed `link` and `rel` types. Rule A mints A-witnesses on one-edge matches and writes `made_a`; B has the two-edge join `link(x,y) ∧ rel(y,z)`, mints B-witnesses and writes `made_b`; C joins `made_a(x,a) ∧ made_b(x,b)`, mints a C-witness and writes two `result` edges. No rule deletes or mutates graph facts.

The classifier admits all cases with M=3 literal mint signatures and E=5 total edge types. The independent interpreter iterates the rule bodies over the finite graph until stable; the separate analyzer replays every raw native graph, recomputes exact expected nodes/edges and bound, and checks order invariance. See [preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_RULE_INTERACTION_PREREG_20260926.md), [native runner](../../../scripts/verify_mint_termination_interaction_v1.py), [independent analyzer/reference interpreter](../../../scripts/analyze_mint_termination_interaction_v1.py), [raw capture](../../../evaluation/reports/mint_termination_interaction_v1_20260926.json), and [analysis](../../../evaluation/reports/mint_termination_interaction_v1_analysis_20260926.json). Raw provenance includes engine identity, source commit, runner/prereg/native hashes, rule specs, initial graphs, final graphs, and native reports.

## Representative closure counts

`B = M + E(N+M)^2 − e₀`, with M=3 and E=5. All replicates within each design cell match these results.

| N | Topology | Initial edges e₀ | Fact bound B | Native progress | Native passes (ABC; CBA/BCA) | Final nodes | Final edges |
|---:|---|---:|---:|---:|---|---:|---:|
| 4 | cycle | 8 | 240 | 3 | 2; 3 | 7 | 18 |
| 4 | path | 6 | 242 | 3 | 2; 3 | 7 | 13 |
| 8 | cycle | 16 | 592 | 3 | 2; 3 | 11 | 34 |
| 8 | path | 14 | 594 | 3 | 2; 3 | 11 | 29 |

The loose bound counts every possible endpoint pair for every edge type; only a small fraction is reachable in these fixtures. The pass difference demonstrates schedule/order effects on convergence length without changing final state.

## Claim boundary

This validates one three-rule program family and the exercised accepted syntax: positive one-/two-edge matches, distinct shared variables, `add_node_if_absent` with string scalar keys, and empty-attribute `add_edge` across five edge types. It does not validate every syntax admitted by the analyzer, arbitrary join widths, many rule bodies, node counts beyond 8 for this interaction, timing/memory cost, or behavior under nonmonotone/external effects. The result strengthens the finite-key closure theorem's runtime evidence; it does not broaden the theorem to unrestricted Ocelot rules or weak acyclicity.

## Next gate

Add adversarial admitted schemas: repeated variables/self-joins, three-edge joins, multiple independent mint types, rule-order permutations with interacting derived-edge types, and initial edge attributes. Independently compare analyzer acceptance and complete rule parsing; any unsupported effect must be rejected by the analyzer or proven to preserve the finite universe.
