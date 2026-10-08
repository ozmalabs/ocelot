# Conversation Shared-Evidence Boundary Wakeup Results (2026-09-26)

## Semantic outcome

A locked 27-worker comparison changed the shared evidence value between two settled closure epochs. Each affected deliberation's epoch was advanced, invalidating local candidate scores. The `full` arm used native full closure; `required` explicitly reran both incident frame scopes; `omitted` reran only frame 0 although both frame epochs were invalidated. All nine size/replicate pairs (2, 4, and 8 frames × three replicates) pass the preregistered gates:

- Required two-frame execution matches full closure exactly and needs zero additional work in the subsequent full-closure fixed-point probe.
- Omitting frame 1 always leaves a pre-repair projection different from full closure, with frame 1's selection missing/stale. A full catch-up pass performs positive work and restores exact projection parity.
- All baseline and post-repair probes are full-graph fixed points; all expected post-change winners are selected. Closure leaves the shared evidence value unchanged.

The independent analyzer passes all 20 provenance, process/schedule, boundary ownership, required-notification, omission-detection, recovery, and terminal fixed-point checks.

## Mutation-phase cost

Medians across three fresh processes per arm and size. Timing includes frame reopening/reset, boundary mutation, epoch invalidation, and the arm's closure path; it excludes initial graph construction and baseline settlement. Omitted-arm time includes the full catch-up pass. These are descriptive micro-measures.

| Frames | Full closure | Required two-frame scoped closure | Omitted frame + full catch-up |
|---:|---:|---:|---:|
| 2 | 0.101 ms; 4 progress steps | 0.190 ms; 10 scoped steps, 4 frame turns; zero full-probe work | 0.168 ms; 6 scoped steps, 2 frame turns; catch-up 4 steps |
| 4 | 0.143 ms; 4 progress steps | 0.301 ms; 12 scoped steps, 4 frame turns; zero full-probe work | 0.249 ms; 6 scoped steps, 2 frame turns; catch-up 4 steps |
| 8 | 0.220 ms; 4 progress steps | 0.704 ms; 12 scoped steps, 4 frame turns; zero full-probe work | 0.398 ms; 6 scoped steps, 2 frame turns; catch-up 4 steps |

The omitted control is an audit of semantic necessity, not a proposed policy: omission saves immediate work but returns a stale projection. Required scoped execution is correct here, but costs more than full closure at these sizes because two complete scoped cycles are needed across the two incident owners.

## Limits

This confirms explicit caller-notification semantics for one changed read-only evidence node in a chain and demonstrates that a missing dependent-frame execution is detectable and recoverable. The runner supplies the affected frame ids; the engine does not derive or deliver notifications. Only one boundary edge is mutated, with no cycles, competing writes, node birth/deletion, mutation storms, or dense boundaries. No natural task rate, general scheduler completeness, asymptotic complexity, or scaling claim follows.

## Artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_BOUNDARY_WAKEUP_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_conversation_boundary_wakeup_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_conversation_boundary_wakeup_v1.py)
- [Accepted raw capture](../../../evaluation/reports/substrate_conversation_boundary_wakeup_v1_20260926.json)
- [Independent analysis](../../../evaluation/reports/substrate_conversation_boundary_wakeup_v1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/conversation_boundary_wakeup_lock_20260926.json)
