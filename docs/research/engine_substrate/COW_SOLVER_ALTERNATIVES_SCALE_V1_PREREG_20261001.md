# Scaled solver-alternative reusable snapshot v1 preregistration

Date: 2026-10-01

## Question

Does one reusable CoW snapshot support multiple branch-local alternatives for the native CAN solver as graph size and local connectivity grow, while preserving eager-copy solver results and primary/sibling isolation?

## Design

Use sizes N={32,128,256}, topologies `path` and `banded2`, and three fresh-process replicates per size/topology (18 workers). Each worker loads the native CAN rule seed and builds one Microtheory with N Concepts, deterministic external fields and bidirectional weighted influence edges. Capture one `shared_graph_pages` snapshot. For each of four preregistered external-field perturbations to Concept 0, execute one `snapshot.fork()` branch and one eager full-copy branch from the same base; each branch runs production `can_native_orchestration.scoped_settle` and `native_audit_basin`.

Measure snapshot capture, branch creation, solver settle, and fixed-point probe separately. Retain per-alternative state and graph digests. Candidate order and graph generation are deterministic. No adoption or external effect occurs.

## Gates

- All 18 size × topology × replicate workers complete with stable source/native fingerprints.
- All four alternatives in every worker produce exactly matching CoW/eager inputs, settled states, steps, energy, frustration, coverage, and graph digest.
- A one-step follow-up settle reports no progress after each solver run.
- The immutable primary, later snapshot forks, and sibling alternatives remain isolated.
- Report capture/fork/settle costs and growth by N/topology; performance conclusions are descriptive because one host and three replicates are used.

## Limits

This is one discrete CAN solver and two sparse graph families, not a general planning battery or natural-task sample. State parity is not a proof that the solver finds a global optimum. No concurrency, cancellation/reclamation, adoption, independent-host, or vLLM-style serving evidence follows.
