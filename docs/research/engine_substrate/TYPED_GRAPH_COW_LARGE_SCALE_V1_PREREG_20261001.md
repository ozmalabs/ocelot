# TypedGraph CoW large-scale extension v1 — preregistration

**Date:** 2026-10-01  
**Question:** Do the measured clone and sparse-write characteristics of the TypedGraph shared-slab path persist from 50k to 100k and 200k nodes across three simple topologies?

## Design

Run the existing source-locked `typed_graph_cow_probe_v2.py` release probe with the existing release binary (no compilation during the measurement), at 100,000 and 200,000 nodes for path, star, and near-square grid graphs, with five alternating-order repeats per cell. Measure eager versus shared-slab clone, clone plus one node-attribute write, and clone plus spaced 1%-of-nodes node-attribute writes. Fixture construction remains outside timed regions. Every measured branch also checks exact node/type/neighbor query parity, divergent sibling writes, and unchanged primary values.

Before execution, preserve a lock containing the runner and Rust source hashes, the binary hash, toolchain, requested cells, and repeat count. Do not replace the retained result if the probe errors or any semantic cell fails.

## Gates

- Exact coverage of six size/topology cells and five repeats each.
- All exact query and sibling-isolation checks pass.
- Runner, Rust source, binary, and toolchain provenance remain in the raw capture and match the pre-run lock.
- Report per-cell medians and ratios for all three operations; preserve regressions and topology differences.

## Interpretation limits

This extends a TypedGraph-only, empty-attribute synthetic probe. It does not measure full Substrate field copying, edge-attribute indexes, realistic rule closure, RSS/PSS, branch reclamation, concurrent inference, or end-to-end thoughtexperiment cost. Two added sizes and five repeats do not establish an asymptotic law; any curve fit is exploratory only.
