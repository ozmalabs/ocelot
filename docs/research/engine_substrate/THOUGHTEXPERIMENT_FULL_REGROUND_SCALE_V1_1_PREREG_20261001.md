# Thoughtexperiment full reground scale v1.1 — preregistration

**Date:** 2026-10-01  
**Question:** At fixed chain topology and degree-2 deletion targets, how do total graph size and deletion-receipt size independently affect complete reground latency?

## Design

Use a full 3×3 factorial: graph sizes 1,000, 10,000, and 50,000 nodes crossed with 1, 16, and 128 node-deletion conclusions. Every graph is a directed chain with edge attributes; target nodes are evenly spaced interior nodes, each with one incoming and one outgoing edge. Each cell is constructed independently. Use five fresh worker processes and seven timed repeats per cell.

Before timing, create exact node and incident-edge before-images in durable `ImaginedConclusion` records. Time the full public `reground()` operation, including incident-edge validation, result accumulation, and status/reason writes; exclude graph and receipt setup. Independent oracle: every deletion conclusion survives, none is discarded, and the result detail count equals the requested deletion count.

## Measures and gates

Record all repeat times, per-worker median and nearest-rank p95, node/edge/deletion/validated-edge counts, exact oracle status, host/runtime, native binary hash, source hashes, and engine fingerprint. Require five distinct worker PIDs and oracle parity for every worker/cell. Report median of worker medians and maximum worker median (a coarse five-worker tail descriptor).

## Limits

This panel isolates graph size and receipt size only for one sparse topology and degree-2 targets. It is not evidence about hubs, broad graph distributions, snapshot/imagination costs, mixed conflicts, or asymptotic complexity. Comparing the prior chain and star panel with this factorial is descriptive because the protocols and worker counts differ.
