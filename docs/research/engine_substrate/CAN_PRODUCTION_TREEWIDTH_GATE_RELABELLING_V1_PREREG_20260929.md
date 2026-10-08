# Production treewidth gate relabelling v1 preregistration (2026-09-29)

## Question

Does the production `junction_tree_exact_settle` width gate preserve exactness under label/order changes to the same known-width grid, and how often does its min-fill upper bound conservatively refuse a graph whose supplied column decomposition fits the configured bound?

## Panel

Generate q×32 binary grid models for q=1…6. For each q, run 12 deterministic replicates with identical graph/factor family but randomized concept insertion order and randomized edge insertion order. This changes native node IDs and iteration/tie order while preserving the geometry, weights, and known column-major width-q elimination certificate. Invoke the production `junction_tree_exact_settle` path at its default width bound 4 with `commit=False`; capture its decision, estimated width, wall/CPU time, and any returned MAP state. For every accepted result, independently compare energy with column dynamic programming. For every refused result, verify the call did not return a state. Record false-refusal counts for q≤4 and unsafe acceptance counts for q≥5 separately.

## Lock and gates

Lock this protocol, runner, production inference and treewidth sources, native artifact, and build record before 72 fresh workers. Require complete replicate coverage; exact extraction of each generated graph; a width-q certificate from the supplied column order; exact independent-oracle agreement for every accepted MAP; no returned MAP state on refusal; no graph state mutation; and exact pre/post source-lock agreement. False refusals are an outcome, not a run-integrity failure.

## Scope

This is a controlled topology/ordering stress test for one production solver gate. It measures label sensitivity and conservative refusal on grids; it does not establish natural-task cut frequency, optimality of min-fill, or capability outside binary pairwise models.

```sh
python3 evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1.py --lock
python3 evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1.py
python3 evaluation/substrate_capability/analyze_can_production_treewidth_gate_relabelling_v1.py
```

The first locked invocation stopped before a solver call because its mutation snapshot passed integer ids to a `NodeID` API. This harness-only failure and handle-based correction are documented in the [v1.1 amendment](CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_1_AMENDMENT_20260929.md); the initial lock is retained and the v1.1 run uses a new lock.
