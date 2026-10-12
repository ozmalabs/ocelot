# Live self-report task-boundary v2 implementation amendment

Date: 2026-09-27 local

The v2 runner extends the current-source self-report matcher-cost worker with a final graph projection. It declares task-owned node sets from the inbound message, origin, Goal/lifecycle identity edges, candidate/receipt links, and outbound response links; then enumerates all typed edges crossing each set and computes the deterministic min-fill upper bound over its owned induced graph. It also records direct cross-task edges and shared external nodes. The full graph is never written to the result. Existing matcher identity, arity, ambiguity, conservation, and lifecycle checks remain in place.

See [the preregistration](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_PREREG_20260927.md).
