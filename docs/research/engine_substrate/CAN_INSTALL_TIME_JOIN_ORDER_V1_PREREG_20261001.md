# CAN install-time join-order policy v1 preregistration

Date: 2026-10-01

## Question

When the graph is populated before production Hebbian rules are installed, does `Substrate::add_rule`'s edge-cardinality heuristic choose an order close to the empirically efficient sparse-first traversal, and does that differ from the common rules-before-data construction path?

## Design

Use the same N={32,64,128}, Q={0,N,4N,floor(N(N−1)/4),N(N−1)}, three-replicate panel and exact productive fixture as [productive coactivation closure v1](CAN_PRODUCTIVE_COACTIVATION_CLOSURE_V1_RESULTS_20261001.md). For each cell, create the Microtheory, Concepts, Coactivation ledger, and half-rounded-down seeded causal links first. Load the CAN vocabulary with an empty rule list, then install only the two target production rules using `import_rules`, once with authored clauses and once with sparse-first clauses. Record their actual installed orders and run full productive closure with per-rule scale audit.

Join the captured graph-first arms to the earlier source-locked v1 productive panel, which used rules-before-data construction and already includes authored-order and sparse-first controls. Require previous capture lock integrity, same pair-level outcomes and canonical final graph digests, exact rule-order predictions from an independent implementation of the install-time cardinality/connected-edge ordering algorithm, per-rule/global candidate reconciliation, bounded closure, and a no-progress terminal probe. Compare candidate counts and wall times by N,Q,construction order, and actual installed first clause.

## Gates

- 45 new fresh workers cover each of the 15 N×Q cells three times, with stable source and prior-capture hashes.
- Only the two target rules are active; the independent install-order oracle exactly predicts both installed clause sequences.
- Every input pair reaches its causal/evidence oracle; graph growth and terminal fixed point are exact.
- Graph-first authored/sparse arms match the prior rules-before-data capture's corresponding canonical result.
- Per-rule candidate tests reconcile with global `cand_tested` in every new arm.

## Limits

This isolates when the current install-time heuristic sees graph data on one synthetic pair family. It does not establish which construction sequence production deployments use universally, optimal ordering for arbitrary patterns, natural Q/topology distributions, or adaptive reordering after graph mutation. Timing uses instrumented runs and is descriptive; instrumentation parity was checked in the matched prior panel.
