# Offline GenMint candidate efficacy with reusable CoW snapshot v1.1 preregistration

Date: 2026-10-01

## Question

Can the reusable `Substrate.snapshot("shared_graph_pages").fork()` lifecycle serve the GenMint candidate-evaluation consumer while preserving the exact semantics and isolation of the existing direct shared-page and eager-copy routes?

## Design

Repeat the v1 candidate efficacy factorial unchanged: 3 matrix families × 2 layouts × 5 independent repetitions (30 workers), with the same training, held-out positive transfer, negative tasks, frozen baseline, and equal-exposure/no-consolidation controls. After candidate training, capture one immutable reusable snapshot of the candidate state. Evaluate one child through `snapshot.fork()` and compare it with existing eager-copy and direct `fork_shared_graph_pages_experiment()` children. Keep a separate reusable snapshot per worker; branch writes and closure must not change its source candidate or the primary baseline.

Lock runner, analyzer, source closure, protocol, native artifact, and generated-engine provenance before execution. Preserve row-wise positive/negative outcomes, branch state digests, snapshot identity/backend/source revision, timing, and worker failures. No adoption or external effects are permitted.

## Gates

- All 30 cells complete under the locked schedule without worker errors.
- Reusable snapshot identifies the expected shared-graph-pages backend and candidate graph/rule revision.
- Positive and negative semantic output fields match eager and direct shared-page controls exactly for each worker; no additional generator is minted during evaluation.
- Primary, candidate source, and sibling branches remain isolated; reusable source digest is stable after evaluation.
- Report fork and end-to-end evaluation cost descriptively. This is an interface/consumer compatibility test, not a speed superiority test.

## Limits

This is one authored linear-generator task family on one host. It does not establish a solver/planner consumer, concurrent branch safety, cancellation/reclamation, revision-conflict adoption, natural task prevalence, broad learning capability, or vLLM/KV-cache integration.
