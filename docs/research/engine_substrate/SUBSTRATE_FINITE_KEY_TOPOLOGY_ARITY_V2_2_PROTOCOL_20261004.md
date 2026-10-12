# Finite-key topology and match-arity v2.2 current-source replay protocol

Date: 2026-10-04

## Question

How do closure work and cost vary with input topology and positive match arity on current source, with the same finite-key insertion effect?

## Factorial

Repeat the frozen v2 panel unchanged: directed path, directed cycle, outward star, and complete directed graph without self-loops. Path/cycle/star use N={16,32,64,128,256}; complete uses N={8,12,16,20}. Match arity is 1, 2, or 3 consecutive `link` triples with distinct variables. There are 57 topology/size/arity cells and three repeats per cell (171 pairs of plain/audit runs). Each matched cell randomizes plain versus audit arm order. The fixed effect creates one literal `Witness{tag:shared}` and inserts `derived(last_match_variable,witness,{})`.

## Gates

Require all 171 cells, native `fixed_point`, zero budget overshoot, progress within the finite-fragment bound, and exact independent injective-binding terminal graph equality for both arms. Recompute factorial coverage, pair parity, counter/timing validity, lock stability, native build freshness, loaded extension hash, and parent log integrity independently. Lock runner, analyzer, protocol, checker, manifest helper, Rust parser/matcher/graph/scheduler/audit sources, build manifest, and loaded extension. Raw graph projections are retained in gzip JSON; the v2 capture remains historical.

## Claim boundary

This is one positive finite-key rule/effect family on authored graphs. Topology, arity, observed joins, and timings describe only this factorial. It does not establish general closure complexity, natural topology prevalence, or unrestricted mint termination.
