# Remaining deferred-queue family audit v1 preregistration

Date: 2026-09-26

## Question

Do scale-audit enqueue/drain counters conserve records for the previously unexercised `rule_edits` and `fb_samples` families, and does audit instrumentation preserve closure output?

## Design

For `N={1,2,4,8}` independent writer/target pairs, each writer matches one trigger and queues (1) a `SetRuleClause` edit that opens its target rule and (2) an `FbSample` on a fixed 4×4 BGRA shared-memory frame at a 2×2 grid. The writer deletes its trigger edge to prevent repeat enqueue. Three fresh-process replications per size run independently reconstructed audit-off and audit-on arms. Both arms must reach fixed point; whole graph and closure report must match exactly. Audit-on captures global and per-rule queue counters around full monolithic closure.

The generated frame, graph fixture and rule bodies are deterministic apart from process-unique shared-memory names. The source lock includes the engine, queue producer/drain implementations, framebuffer reader, protocol, runner, analyzer and native build identity.

## Exact queue predictions

Each writer fires once. Thus, for each queue family, enqueued items = drained items = `N`, drain batches = 1, and drain time is nonnegative. Per-rule producer attribution must show one enqueue of each family for each writer rule. Every target's opened rule must add its `seen_i` edge; every sample must materialize grid data under its game node. No queue record may remain pending after full closure.

## Limits

This is a synthetic in-process shared-memory fixture. It validates queue accounting and audit-on semantic parity, not queue throughput, natural frequency, external writer concurrency, scoped closure fallback behavior, or framebuffer segmentation quality. The grid is deliberately tiny; drain timings are descriptive only.
