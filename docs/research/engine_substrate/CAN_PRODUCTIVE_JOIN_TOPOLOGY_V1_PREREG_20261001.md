# Productive CAN topology sensitivity v1 preregistration

Date: 2026-10-01

## Question

Does the measured CAN join order remain low-work when the same number of coactivation pairs is arranged in hub-biased or clustered layouts instead of the original cyclic layout?

## Design

Use the same two production CAN Hebbian rules, with their full `where` guards and productive mint/reweight effects. Compare three exact installed orders: default heuristic, sparse-first, and measured-best (the latter through `add_rule_preserving_match_order`). Use N={32,64}, Q={N,4N,floor(N(N−1)/4)}, three fresh processes per layout/size/population cell, and layouts:

- `cyclic`: the prior fixture's increasing cyclic-offset ordering;
- `hub`: center-out and center-in directed pairs first, followed by remaining cyclic pairs;
- `clustered`: within-community directed pairs first (community width `round(sqrt(N))`, minimum 4), followed by remaining cyclic pairs.

Within every cell the same generated pair sequence is used across all three order arms. The runner records and hashes the pair sequence, then records installed order, productive per-pair outcomes, terminal closure, global and per-rule candidate work, elapsed time, and canonical final graph digest. Every order also runs without instrumentation. A result analyzer independently checks the worker schedule, exact order and pair digests, outcome oracle, fixed point, graph parity, instrumentation parity, and counter reconciliation.

## Gates

- 36 unique workers cover all 3 layouts × 2 sizes × 3 Q levels × 3 replicates.
- Source, protocol, analyzer, runner, seed, native extension, and build record remain stable.
- Pair layouts are distinct within each matched N/Q/replicate; each arm in a cell has the same pair input.
- Exact active rules and installed order match the protocol.
- Every pair receives the expected causal link and evidence state; graph growth matches its oracle.
- All arms terminate below the step cap; the terminal probe makes no progress.
- Canonical graph facts agree across matcher-order arms within each topology cell.
- Instrumented/uninstrumented outcomes and progress agree; per-rule candidate counts reconcile globally.

## Limits

This tests topology sensitivity for the same CAN family, not another independent rule family. Hub and clustered sequences are deterministic constructed layouts rather than samples from natural tasks. N≤64 and Q≤N(N−1)/4. Results cannot establish a general order selector or average-case complexity claim.
