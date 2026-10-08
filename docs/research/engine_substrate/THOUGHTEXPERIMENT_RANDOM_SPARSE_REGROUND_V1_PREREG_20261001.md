# Thoughtexperiment randomized sparse reground v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does deletion regrounding preserve exact survivor/conflict judgments on seeded sparse graphs with varied incident-edge changes?

## Design

Run five fresh worker processes. Each worker builds independent directed sparse graphs at 1,000, 10,000, and 50,000 nodes for seeds 4101 and 4102. Each graph has `2N` unique directed `rel` edges with deterministic ordinal attributes and 50 deletion targets sampled from non-isolated nodes. Targets are balanced across five treatments: unchanged, node-attribute conflict, incident-edge-attribute conflict, added incident edge, and removed incident edge. Capture exact node and incident-edge before-images before applying the treatment mutations.

Expected verdicts come from the Python generator's node/edge model after mutations, not from `Substrate.incident_edges`. Time the complete `reground()` call after graph and receipt setup. Record total/degree summaries, per-treatment verdict counts, complete timings, and exact per-conclusion parity.

## Gates and source lock

Require five distinct worker PIDs, all graph generation seeds/cell rows present, and exact survivor/discard parity with the independent model for every target. Capture host/runtime, source SHA-256, native binary SHA-256, and Rust engine fingerprint; refuse stale native builds.

## Limits

This is a seeded random sparse model, not a sample of natural tasks or a proof about arbitrary graphs. The target sample is conditioned on nonzero degree. Conflict modes are synthetic and balanced by the harness. The benchmark measures complete regrounding only, not imagination, snapshot creation, commitment, or end-to-end thoughtexperiment cost.
