# Thoughtexperiment correction candidate surface audit v1 — preregistration

**Date:** 2026-10-01  
**Question:** Across the active rules loaded by the standard core fixture, how broad is the current default self-correction candidate generator, and where does task-shaped candidate support exist?

## Protocol

In three fresh worker processes, construct the same standard substrate fixture used by the correction copy comparison, enumerate every active native rule, and call `_default_candidates` for each target rule without applying candidates or mutating the graph. Capture active rule count, candidate counts, candidate labels and label-family counts, plus the rules for which a domain-shaped candidate is emitted. Verify graph and rule state are unchanged by enumeration and require identical semantic inventory across workers. Fingerprint the source files, native binary, and runner per worker.

## Gates

- Three independent fresh worker processes complete.
- All workers enumerate the same active rule and candidate-label inventory.
- Enumeration leaves the graph and rewrite-rule inventory unchanged.
- The known `sd_mint_quantum` fixture includes `dedup_identity_fix`.
- Report task-shaped candidate coverage separately from generic syntactic transforms.

## Limits

This is a source-surface audit, not a task-utility evaluation. Candidate availability does not imply that a variant applies, converges, preserves task behavior, or is safe to adopt. The audit is intended to identify whether the current substrate has enough independent task-shaped correction families for a cross-family learning claim.
