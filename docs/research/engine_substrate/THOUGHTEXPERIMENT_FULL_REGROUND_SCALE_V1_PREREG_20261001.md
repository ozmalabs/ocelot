# Thoughtexperiment full reground scale v1 — preregistration

**Date:** 2026-10-01  
**Question:** How does complete `reground()` cost scale with total graph size, number of node-deletion conclusions, and the incident-edge aperture those conclusions validate?

## Design

Use three fresh worker processes, five timed reground calls per cell, and six graph treatments:

| Nodes | Topology | Deletion conclusions | Target aperture |
|---:|---|---:|---|
| 1,000 | chain | 1 | one interior node |
| 10,000 | chain | 16 | spaced interior nodes |
| 50,000 | chain | 128 | spaced interior nodes |
| 10,000 | star | 1 | hub with 9,999 incident edges |
| 50,000 | star | 1 | hub with 49,999 incident edges |
| 50,000 | star | 128 | leaves with one incident edge each |

For each target, create an `ImaginedConclusion` with exact node type/attribute and incident-edge before-images. Exclude fixture construction and receipt creation from timing; time the full public `reground()` call, including all verdicts and durable status/reason writes. The independent oracle expects every proposal to survive on an unchanged graph and checks the final status and detail counts.

## Measures and gates

Capture all per-repeat wall times, median and p95 by worker/cell, graph node/edge counts, total validated incident-edge count, survivor/discard counts, five source hashes, native binary hash, engine fingerprint, and host/runtime metadata. Pass only with three distinct worker PIDs and exact oracle parity in every cell. Report per-worker medians and aggregate median; do not fit or claim an asymptotic law from this small matrix.

## Limits

This is a synthetic access/locality and deletion-trace benchmark. It excludes snapshot creation, imagination, proposal minting, commitment gating, and graph mutation. Chains/stars do not represent a natural-task sample. The star-hub rows intentionally expose a large deletion payload; they are not directly comparable to many low-degree proposals without considering the reported incident-edge count.
