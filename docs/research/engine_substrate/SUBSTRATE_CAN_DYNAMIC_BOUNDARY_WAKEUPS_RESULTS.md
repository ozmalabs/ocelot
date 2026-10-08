# CAN dynamic boundary wakeup pilot — 2026-09-24

## Question and protocol

After an already-settled frame execution is perturbed, can an event-style frame queue recover the same result as a full round-robin rescan?

[`scripts/substrate_can_dynamic_boundary_wakeups.py`](../../../scripts/substrate_can_dynamic_boundary_wakeups.py) builds two identical N=8, two-frame CAN substrates, settles both, and applies the same mutation to each. The event copy starts from the frames directly affected by the caller-reported mutation and propagates wakes when a frame's state changes, using the current directed causal edges to find frames that read that changed state. The reference resumes by scanning every frame. Both outputs are checked against an independent implementation of the 3-state local update equation on the final graph.

The four deterministic cases are insertion and deletion of a cross-frame causal edge, replacement of the `weight` attribute on an existing cross-frame edge, and an `external_field` change. Every mutation changes the settled state, so the comparisons exercise actual post-mutation work rather than a no-op. The harness records initial and resumed progress, frames directly notified, terminal states, fixed-point residuals, source hashes, binary hash, and environment.

## Results

All four event runs match the full-rescan terminal state and reach the independent full-graph fixed point. The insertion, deletion, and field-change cases each required one progressing rule application. Replacing edge weights flipped a concept and propagated through the frame graph, requiring four progressing applications under both policies. Event runs used 2–5 frame turns.

An insertion negative control starts from the same settled state but supplies no initial frame notification. It leaves the affected state stale, disagrees with the full-rescan output, and has nonzero full-graph residual. This confirms the case can detect a missed direct notification.

| Mutation | State changed | Event turns | Event progress | Full-rescan progress | Same terminal state | Both fixed points |
|---|---:|---:|---:|---:|---:|---:|
| Cross-frame edge insertion | yes | 3 | 1 | 1 | yes | yes |
| Cross-frame edge deletion | yes | 2 | 1 | 1 | yes | yes |
| Existing edge `weight` replacement | yes | 5 | 4 | 4 | yes | yes |
| `external_field` change | yes | 2 | 1 | 1 | yes | yes |

Raw records and provenance are in [`evaluation/reports/substrate_can_dynamic_boundary_wakeups_20260924.json`](../../../evaluation/reports/substrate_can_dynamic_boundary_wakeups_20260924.json).

## Claim boundary

This is a mechanism probe, not a runtime frame scheduler. The event runner is Python and receives explicit direct-frame notifications from the mutation caller. Thus it measures propagation completeness after a correct initial notification; it does not establish that native rule effects, host mutations, or external adapters automatically notify every affected frame. The workload has one update rule, eight nodes, two frames, and four mutation types. It does not establish general dependency extraction, node birth/deletion, arbitrary term-family invalidation, scale behavior, or equivalence of asynchronous basin selection. A broader mutation matrix and native writer-to-scheduler integration remain necessary.

## Next gate

Add positive and negative notification controls across typed edge insert/delete, edge-attribute replacement, node-attribute changes, node birth/deletion, and writers whose terms read across the boundary. Compare dynamic traces and final residuals with full rescans. Only after those pass should native effect-to-frame notifications be implemented and measured.
