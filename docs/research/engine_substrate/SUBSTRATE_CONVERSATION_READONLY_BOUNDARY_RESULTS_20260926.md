# Conversation Read-Only Boundary Connected-Frame Results (2026-09-26)

## Outcome

The locked follow-up repairs the shared-candidate alias in the earlier connected-frame stress probe. It creates frame-local mutable candidate copies and a shared evidence node per adjacent frame pair. The in-memory score rule explicitly matches candidate-to-evidence and adds the shared node's `boundary_value`; candidate score/status/selection writes remain local. Both adjacent Microtheories own each shared evidence node, which is read by both frames but never written by closure.

The accepted capture contains 24 fresh workers (four sizes × three replicates × two arms), each with a recorded unique PID. The independent analyzer passes all 15 provenance, schedule, topology, ownership, fixed-point, expected-decision, exact-projection, and parent-summary recomputation checks. All 12 full/scoped pairs match exactly and all 24 workers reach fixed points with the expected winner in each task.

## Cost on this rule family

| Deliberations | Full / scoped candidates | Scoped / full candidate ratio | Full / scoped Terms | Scoped / full Term ratio | Full / scoped median wall | Scoped / full wall ratio | Scoped frame turns |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 41 / 151 | 3.68× | 321 / 1,062 | 3.31× | 0.145 / 0.233 ms | 1.60× | 2 |
| 2 | 82 / 392 | 4.78× | 642 / 2,706 | 4.21× | 0.184 / 0.387 ms | 2.10× | 4 |
| 4 | 190 / 1,488 | 7.83× | 1,528 / 10,038 | 6.57× | 0.263 / 1.052 ms | 4.00× | 8 |
| 8 | 406 / 5,504 | 13.56× | 3,300 / 36,006 | 10.91× | 0.430 / 3.304 ms | 7.67× | 16 |

This is a valid semantic parity result for a shared read-only evidence boundary, but not a performance win for the generic repeated scoped API. Its per-frame scans and repeated owner turns dominate these small cases; the result argues for attributing/removing repeated work before claiming factorisation benefits. Timing is descriptive from three paired fresh-process replicates per size; it is not an asymptotic estimate.

## Limits and failure disclosure

The boundary value is immutable during each closure. This does not test mutation-driven notification, missed boundary wakeups, dynamic repartition, arbitrary/dense dependencies, or production GALS. It is one deliberately authored connected chain and one conversation rule family, not a natural task distribution or general substrate result. The previous shared-mutable-candidate study remains a negative control showing that globally mutable aliased candidate state can break schedule parity.

The first complete semantic capture did not serialize worker PIDs, preventing the independent analyzer from verifying the fresh-process gate. It is preserved as a diagnostic and excluded. The runner was amended to record each PID, its source lock regenerated, and the entire 24-cell capture rerun. The accepted raw and analysis records below are from that rerun.

## Artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_READONLY_BOUNDARY_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_conversation_readonly_boundary_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_conversation_readonly_boundary_v1.py)
- [Accepted raw capture](../../../evaluation/reports/substrate_conversation_readonly_boundary_v1_20260926.json)
- [Independent analysis](../../../evaluation/reports/substrate_conversation_readonly_boundary_v1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/conversation_readonly_boundary_lock_20260926.json)
- [Excluded capture without worker PIDs](../../../evaluation/reports/substrate_conversation_readonly_boundary_v1_missing_pid_diagnostic_20260926.json)
- [Prior shared-mutable-candidate result](SUBSTRATE_CONVERSATION_CONNECTED_FRAME_SCALE_RESULTS.md)
