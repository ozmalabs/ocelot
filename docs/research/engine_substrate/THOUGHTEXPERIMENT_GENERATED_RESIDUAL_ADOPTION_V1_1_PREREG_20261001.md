# Thoughtexperiment generated-residual adoption v1.1 — preregistration

**Date:** 2026-10-01  
**Question:** Does rule-generated residual adoption preserve exact semantics across multiple effect families, graph sizes, and a large node-deletion aperture, and how does the end-to-end cost divide across phases?

## Design

Run three fresh workers over a fixed panel of four rule families (`attribute`, `add`, `mixed`, `hub_delete`) at 64 and 1,000 semantic nodes, with three deterministic seeds per cell (72 trials total). The hub-deletion treatment uses a focal node incident to 32 spokes, so its deletion receipt must capture and remove that complete incident-edge set. Other fixture edges are seeded and excluded from the target aperture. Rules are installed in the substrate and execute through `imagine()`, `reground()`, default gate refusal, and explicitly approved commit.

For each treatment, retain a complete pre-imagination graph and independently apply the declared rule effects, including deletion cascade and the minted-node ID from the commit receipt. Compare the entire semantic graph after commit. Also verify rehearsal and default refusal preserve primary semantic state. Record wall time for `imagine`, `reground`, default refusal, approved commit, and total; these are descriptive measurements, not complexity claims. Source and native binary hashes plus engine fingerprint are captured and stale builds are refused.

## Gates

Require three distinct worker PIDs, all 72 treatment cells, expected conclusion and write kinds per family, rehearsal isolation, refusal without semantic mutation, successful authorized writeback, and exact full-graph oracle parity on every trial. Report per-phase medians by family and size, plus node/edge counts and hub aperture degree. Any correctness failure invalidates the corresponding timing comparison.

## Limits

This remains a synthetic authored-rule panel. It tests effect handling and locality sensitivity, not learned-rule acquisition, natural-task frequency, or utility. Two graph sizes and one constructed hub degree cannot establish asymptotic bounds or a general scaling law. It does not test concurrent primary writers; revision-conflict and commit atomicity have separate probes.
