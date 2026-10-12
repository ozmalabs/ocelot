# Finite-key closure topology and match-arity v2 protocol

## Question

How do native closure work and cost for the finite-key insertion fragment vary with input topology and positive match arity, holding the mint/effect signature fixed?

## Factorial

Topologies are directed path, directed cycle, outward star, and complete directed graph without self-loops. Path/cycle/star use N={16,32,64,128,256}; complete uses N={8,12,16,20}. Match arity is 1, 2, or 3 consecutive `link` triples, with distinct variables. There are 57 topology/size/arity cells and three fresh-substrate replicates per cell (171 cells).

Each cell has matched uninstrumented and opt-in scale-audit closure runs in randomized within-replicate order. Both use one fixed literal `add_node_if_absent` witness signature and add `derived(last_match_variable,witness,{})`. The audit arm records aggregate and per-rule candidate/Term counters. Timing endpoints are setup, closure wall, and closure CPU; audit-on cost is diagnostic and not treated as native default cost.

The independent oracle enumerates positive joins with the runtime's injective-variable semantics, computes the exact witness and derived edges, and compares complete normalized node/edge projections. Every run must report `fixed_point`, no budget overshoot, analyzer acceptance, and progress within the finite graph-fact bound. Candidate and Term work, final graph size, and costs are reported separately; the bound itself is not a wall-time estimate.

## Provenance and analysis

A pre-run lock covers fixture runner, independent analyzer, analyzer/checker, protocol, shared manifest helper, native parser/matcher/closure/audit source, build manifest, and loaded native extension. The run captures the shared manifest and parent console log. The independent analyzer regenerates the factorial inventory and oracle states, checks exact matched-arm parity, per-case bounds, timing/counter validity, source stability, engine freshness, and log hashes.

## Claim boundary

This is one fixed finite-key rule/effect family over four authored topologies and three match arities. It measures native cost and work counters for these inputs; it does not establish a general cost exponent, natural graph prevalence, arbitrary rule-program complexity, or runtime speedups from the audit counters.
