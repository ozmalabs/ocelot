# Positive join multiplicity × operation-work trace v2 preregistration

Date: 2026-10-01

## Question

When a rule has multiple successful two-edge join bindings, do `rule_edits` and `fb_samples` operation-work rows reconcile to family counters and scale with successful bindings, and how does this interact with loaded rule count and closure mutations?

## Design

Use `R={1,8,32}` independent writer/target rule pairs and join multiplicity `M={1,4,16}`, with three fresh-process replications per cell. Each writer's body matches a shared per-rule trigger edge, one of `M` left edges from an anchor to an intermediate node, one corresponding right edge from that intermediate node to a target, and an anchor-to-game edge. Every successful binding queues one rule edit and one framebuffer sample; deleting the shared trigger suppresses subsequent closure re-firing. The queued edit opens the target rule, which then derives a `seen_i` edge. A fixed 4×4 shared-memory frame is sampled onto each of the `R` game nodes. During the audit-on full-closure arm, enable the native all-scope operation-work trace only around `run_rules_report`; preserve the independent audit-off arm as exact semantic control.

Each cell runs audit-off and audit-on closures from independently constructed identical substrates. Capture whole graph/report state and per-rule scale-audit counters. Inputs are locked to all engine sources relevant to matching, queues, framebuffer reads, Python bindings, runner, analyzer, protocol, binary, and build record.

## Expected invariants

- Full closure reaches fixed point, with zero budget overshoot.
- Audit-on and audit-off graph and report match exactly.
- Exactly `R` target `seen_i` edges and `4R` grid cells are present.
- Each of `rule_edits` and `fb_samples` enqueues and drains exactly `R×M` items.
- Each family drains in one between-pass batch for this construction.
- Each writer rule is attributed exactly `M` enqueues per family.
- Trace has zero dropped rows, valid operation/scope/unit fields, and one supported operation-kind marker per operation.
- Operation-trace enqueue, drained-item, and drain-batch units equal the independent scale-audit counters by family for every cell.
- Exactly `R` trigger edges are deleted; later passes cannot enqueue again.

The audit-on queue drain and planner timings are descriptive only. The key scaling outcome is exact integer work versus both `R` and `M` under semantic parity.

## Limits

This is an authored join family with one binding path per intermediate node and repeated queue effects. It does not establish arbitrary join-order behavior, skewed-degree response, scoped scheduler cost, natural queue prevalence, or natural frame structure. Framebuffer input is static and local; no external writer races are measured.
