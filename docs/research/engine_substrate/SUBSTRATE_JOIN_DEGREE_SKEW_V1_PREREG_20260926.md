# Two-edge join degree-skew v1 preregistration

Date: 2026-09-26

## Question

At fixed successful join multiplicity and fixed decoy-edge count, how does placing one-sided candidates on the left relation versus the right relation change native candidate work and closure cost? Does the measured effect depend on match-literal order?

## Fixture and design

Use one isolated writer/target pair per process. Each fixture has `M={4,16,64}` true two-edge paths. Add `D=qM`, `q={0,4,16}`, one-sided decoy edges: `D_left` anchor-to-middle edges with no corresponding right edge and `D_right` middle-to-target edges with no corresponding left edge. For nonzero `D`, compare left-skew `(D,0)`, balanced `(D/2,D/2)`, and right-skew `(0,D)`. The `q=0` baseline occurs once. Thus every compared split at the same `(M,q)` has the same successful binding count and total decoy-edge count; only the incidence side differs. Compare trigger-left-right-game and trigger-right-left-game literal orders. Run three fresh-process replications for 126 cells. Each cell runs an uninstrumented closure and a separately reconstructed audit-on closure.

Collect match-clause candidate tests, actual installed edge order from `export_rules()`, queue enqueues/drains, fixed-point status, exact plain/audit graph/report parity, process CPU and monotonic wall time for the closure call, and source/native identity. The engine applies a count-based cost reorder at installation, so the protocol records authored and installed order and attributes clause positions to installed edge type. Timing starts immediately before `run_rules_report` and ends immediately after; fixture construction, interpreter startup, and audit capture serialization are excluded. Audit-on time is diagnostic only; primary timing is uninstrumented. Do not subtract timer overhead or infer commodity-scale throughput from this small fixture.

## Gates

- Source/native lock is stable before, during, and after every worker.
- 126 unique fresh-process cells and three exact integer-work repetitions per parameter/order/split cell.
- Exactly `M` complete bindings, `M` enqueues and drains for each deferred queue family, one drain batch, one target output, expected framebuffer materialization, trigger deletion, fixed point, and zero overshoot.
- Plain/audit graph and report parity within each cell; both literal orders have identical final graph for each split.
- Clause candidate totals conserve against per-rule totals; per-clause counts are present for all four match edges. Exported installed order matches the source-locked count-based reorder and tie behavior.
- Timing values are positive and recorded for both audit-off and audit-on runs; no universal runtime claim.

## Limits

This measures one regular, isolated, four-literal schema with synthetic one-sided decoys. It does not establish natural-task degree distributions, scaling beyond `M=64`, memory use, a general complexity class, or the benefit of an implemented optimizer. The candidate counter is instrumented; timing uses separate plain and audit runs. A split effect can depend on edge insertion order and matcher implementation, both of which are locked by this runner/source identity.
