# CAN mixed-degree join-order v1 preregistration

Date: 2026-10-01

## Question

For the production CAN Hebbian four-clause pattern, does install-time edge-cardinality order remain minimum-work when the coactivation relation degree distribution changes while N and Q stay fixed?

## Design

Use N={16,32}, Q={N,4N,floor(N(N−1)/4)}, two directed pair layouts, and three fresh-process replicates (36 workers). `uniform` uses the established cyclic-offset layout; `source_skewed` fills ordered outgoing pairs from the lowest-index concepts before moving to the next source, maximizing degree concentration subject to unique directed pairs. Every pair gets one Coactivation node and its two production edge types. Build graph facts before importing one effect-free copy of the production Hebbian rule so current `add_rule` sees exact relation cardinalities.

Capture actual install order and per-position candidate tests. An independent typed adjacency simulator replays the installed-order candidate work and exhaustively computes all 24 clause permutations for that exact graph. Record selector regret and prefix profiles. The native rule is effect-free to enumerate every binding without changing the workload graph; the production match pattern, variable sharing, and relation types remain unchanged.

## Gates

- 36 unique cells/processes, stable source lock, and exact N/Q/topology counts.
- Independent cardinality/connected-edge replay matches the native installed match sequence.
- Independent typed-graph simulation matches candidate-test counters at each clause prefix and globally.
- All 24 orders are evaluated per graph; the installed-order work is at least the modeled minimum.
- Graph is unchanged, effects/progress are zero, and terminal probe is stable.

## Limits

This isolates one production pattern under two synthetic layouts at small N. The hub layout is intentionally adversarial and is not a natural-data frequency claim. It measures matching only, not productive closure, other rules, or adaptive policies. Exhaustive work is exact for these finite graphs; no general complexity bound follows.
