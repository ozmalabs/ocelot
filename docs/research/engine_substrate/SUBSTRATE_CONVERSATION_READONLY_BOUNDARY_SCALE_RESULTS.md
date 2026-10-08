# Conversation read-only boundary scale results

## Outcome

The locked 24-worker native replay passed every preregistered gate: all workers reached `fixed_point`, all expected choices were made, and all 12 full/scoped pairs had identical normalized projections. The prior shared-mutable-candidate counterexample remains preserved as the negative control. This supports keeping candidate and selection state local when frames share evidence objects.

| Deliberations | Full candidate pairs | Scoped candidate pairs | Full Term evaluations | Scoped Term evaluations | Full median wall | Scoped median wall | Scoped frame turns |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 | 109 | 323 | 784 | 0.143 ms | 0.149 ms | 2 |
| 2 | 78 | 379 | 646 | 2,782 | 0.180 ms | 0.256 ms | 4 |
| 4 | 156 | 1,402 | 1,292 | 10,420 | 0.246 ms | 0.567 ms | 8 |
| 8 | 312 | 5,380 | 2,584 | 40,264 | 0.360 ms | 1.666 ms | 16 |

The near equality with the disconnected conversation run is expected from source inspection: the Phase 4A native rules do not read `SharedGroundingEvidence` or the `supports_candidate` edge. Each candidate already has its own copied grounding and valuation attributes. The added shared node creates graph connectivity and overlapping scopes but no rule dependency or propagation. Thus this establishes parity for read-only graph overlap, while scoped repeated matching remains costlier through N=8; it does not validate connected inference, native boundary wakeup, or cheap-cut factorisation.

The important representation distinction is now experimentally bounded: shared mutable candidates can make full/scoped outcomes schedule-dependent, while shared read-only evidence with per-frame candidate state preserves parity in this workload. To test actual propagation, add a separately preregistered runtime rule path that reads a shared evidence node and updates frame-local derived state, then compare event/scoped settlement with full closure under mutations and retractions. Avoid folding such a rule into the Phase 4A claim.

Artifacts: [preregistration](SUBSTRATE_CONVERSATION_READONLY_BOUNDARY_SCALE_PREREG_20260925.md), [runner](../../../scripts/substrate_conversation_readonly_boundary_scale.py), [independent audit](../../../scripts/analyze_substrate_conversation_readonly_boundary_scale.py), [raw report](../../../evaluation/reports/substrate_conversation_readonly_boundary_scale_20260925.json), and [lock](../../../evaluation/substrate_capability/conversation_readonly_boundary_scale_lock_20260925.json).
