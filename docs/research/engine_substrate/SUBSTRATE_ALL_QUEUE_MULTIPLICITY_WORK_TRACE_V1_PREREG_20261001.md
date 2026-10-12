# Unified five-family queue and mutation-work trace v1 preregistration

Date: 2026-10-01

## Question

Can a single positive-join workload exercise and reconcile all five deferred queue families under operation-work tracing, while measuring binding multiplicity and deletion-driven requeue suppression?

## Design

Use `R={1,8,32}` independent writer/target pairs and `M={1,4,16}` two-edge bindings per writer, with three fresh-process replications per cell. Each writer has one shared trigger edge, M left/right intermediate paths, one game, one RulePatch, one observation/network, and one previous/current percept pair. Its matched rule applies the patch, queues a rule-clause edit, TrackIdentity, NetCollapse, and framebuffer sample, then deletes its shared trigger. The target clause update must unlock the target rule; trigger deletion and the fired-state mutation suppress later writer re-enqueue. A fixed 4×4 frame feeds each game. Compare independently constructed audit-off and audit-on substrates. Trace all scheduler/deferred operation work around the audit-on full closure.

Each cell runs audit-off and audit-on closures from independently constructed identical substrates. Capture whole graph/report state and per-rule scale-audit counters. Inputs are locked to all engine sources relevant to matching, queues, framebuffer reads, Python bindings, runner, analyzer, protocol, binary, and build record.

## Expected invariants

- Full closure reaches fixed point, with zero budget overshoot.
- Audit-on and audit-off graph and report match exactly.
- Exactly `R` target `seen_i` edges and `4R` grid cells are present.
- `rule_edits`, `fb_samples`, `track_identity`, and `net_collapses` each enqueue and drain exactly `R×M` items in one batch.
- RulePatch enqueues once per writer because repeated bindings reference the same pending patch and duplicate patch enqueue is suppressed; total drained patches equal R in one batch.
- Per-writer enqueue attribution is M for the four non-patch families and 1 for RulePatch.
- Trace has zero dropped rows, valid operation/scope/unit fields, and one supported operation-kind marker per operation.
- Operation-trace enqueue, drained-item, and drain-batch units equal the independent scale-audit counters by family for every cell.
- All R target rules fire, all R trigger edges are removed, and all games receive four framebuffer cells.
- Exactly `R` trigger edges are deleted; later passes cannot enqueue again.

The audit-on queue drain and planner timings are descriptive only. The key scaling outcome is exact integer work versus both `R` and `M` under semantic parity.

## Limits

This is an authored join family with repeated per-binding queue effects, one deduplicated RulePatch, and trigger deletion. It does not establish arbitrary join-order behavior, skewed-degree response, scoped scheduler cost, natural queue prevalence, or natural frame structure. Framebuffer input is static and local; no external writer races are measured.
