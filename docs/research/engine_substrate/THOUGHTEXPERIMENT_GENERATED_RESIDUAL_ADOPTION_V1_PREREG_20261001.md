# Thoughtexperiment generated-residual adoption v1 — preregistration

**Date:** 2026-10-01  
**Question:** Do native rule-generated mixed residuals remain isolated during rehearsal and commit to exactly the rule-intended full-graph result when explicitly approved?

## Design

Run five fresh workers with ten deterministic seeds each. Every graph has 48 nodes, one target fact, one explicit edge-removal match, one node-removal match, and a seeded sparse context graph among unrelated background nodes. A graph-resident rule fires only when the injected hypothesis link matches the target. Its effects change one target attribute, remove one edge, mint a derived node, add an edge to that node, and remove a stale node.

For each seed, capture the complete primary graph before imagination. After `imagine()`, compare its semantic node/edge projection to the baseline to ensure only experiment trace records were added. Reground conclusions, run the default gate and confirm no content write, then run an explicitly approved commit. An independent Python oracle starts from the pre-imagination complete graph, applies the declared rule effects (including node-delete edge cascade), maps the derived node using the writeback receipt, and compares the full semantic graph after commit.

## Gates

Require five unique worker PIDs and 50 seeds; exact native rule-generated conclusion kinds; semantic primary parity after rehearsal; default refusal without semantic changes; explicit approval and successful writeback; and exact full-graph oracle parity after commit for every seed.

## Source lock and limits

Capture source and binary hashes, engine fingerprint, host/runtime, seeds, per-trial operation outcomes, and graph counts; refuse stale native builds. This is a constructed rule family and does not measure whether the system can learn a useful rule or whether natural tasks produce such residuals.
