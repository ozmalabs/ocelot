# Mixed-relation join-cost and order-selection v1 preregistration

Date: 2026-10-01

## Question

Across independent four-clause path, star, and cycle patterns, does the engine's edge-cardinality/connected-edge install order minimize measured prefix candidate work when relation populations differ, and can an independent simulator predict the observed work?

## Design

Use N={16,32}, three matcher shapes (path4, star4, cycle4), five relation-population layouts, and three fresh-process replicates (90 workers). Each pattern has four distinct Concept→Concept relations named `mix_r0`…`mix_r3`. Four layouts give one relation Q=N while the other three have Q=4N, rotating the sparse relation through pattern positions; a balanced control uses Q=4N for every relation. For each Q, build deterministic directed cyclic-offset edges. Use `graph_from_dict()` to load the synthetic typed relations, then import one effect-free production-parser rule. This bypasses the application ontology's dynamic edge-admission policy to test matcher behavior over typed graph facts; synthetic relation names and this loading route are part of the claim boundary.

Capture the actual installed match order and native per-position candidate counts. An independent Python matcher simulator predicts prefix work for the installed order and exhaustively evaluates all 24 clause permutations on the same graph. Report the installed order's total work against the simulator's minimum, including ties and any heuristic regret. The independent order oracle replays the source's rarest-edge-first, then connected-rarest rule.

## Gates

- Complete 90 unique cells and PIDs with source-locked runner, analyzer, protocol, seed, native extension, and matcher/audit source.
- Independent greedy replay matches the engine's installed order.
- Independent prefix simulation matches observed native per-clause candidate counts exactly, and prefix sums reconcile with global candidate tests.
- Exhaustive 24-order work model is finite and deterministic for every graph; order regret is computed from the exact same simulator.
- Effect-free closure preserves the canonical graph and has zero progress; repeated terminal probe is stable.

## Limits

This is a synthetic matcher-cost study with homogeneous typed nodes, one active rule, four clauses, relation populations from N to 4N, and N≤32. The persistence loader accepts synthetic relation symbols without exercising graph-time admissibility checks. It validates the match-work model and ordering heuristic on controlled shapes; it does not show a production engine improvement, natural task distribution, productive closure, or general complexity bound.
