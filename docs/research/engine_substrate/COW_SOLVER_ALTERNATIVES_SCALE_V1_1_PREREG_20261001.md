# Scaled solver-alternative reusable snapshot v1.1 preregistration

Date: 2026-10-01

This rerun preserves the v1 panel's worker design but bounds orchestration to three concurrent fresh processes. The first v1 attempt was interrupted before any aggregate raw capture was written; it is not result evidence. A standalone 256-node worker took about 58 seconds, motivating bounded parallel execution without changing the cells or gates.

## Question and design

Use N={32,128,256}, `path` and `banded2` topologies, and three fresh-process replicates per size/topology (18 workers). Each loads the native CAN rule seed and builds one Microtheory with N Concepts, deterministic external fields, and bidirectional weighted influence edges. Capture one shared-graph-pages snapshot. For each of four preregistered external-field perturbations to Concept 0, execute one reusable CoW branch and one eager-copy branch from the same base; each runs production `can_native_orchestration.scoped_settle` and `native_audit_basin`.

Measure snapshot capture, branch creation, solver settle, and fixed-point probe separately. Use at most three concurrent workers; retain per-alternative state and graph digests. No adoption or external effect occurs.

## Gates

- Complete all 18 size × topology × replicate workers with stable source/native fingerprints and unique process IDs.
- Every alternative produces exactly matching CoW/eager inputs, settled states, steps, energy, frustration, coverage, and graph digest.
- A one-step follow-up settle reports no progress after every solver run.
- Immutable primary, later snapshot forks, and sibling alternatives remain isolated.
- Report capture/fork/settle costs and growth by N/topology; performance conclusions are descriptive on one host and three replicates.

## Limits

One discrete CAN solver and two sparse graph families, not a general planning battery or natural-task sample. State parity does not prove a global optimum. No concurrency within a snapshot, cancellation/reclamation, adoption, independent-host, or serving evidence follows.
