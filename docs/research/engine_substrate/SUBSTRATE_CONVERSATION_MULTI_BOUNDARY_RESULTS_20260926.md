# Conversation Multi-Boundary Write-to-Owner Mapping Results (2026-09-26)

## Outcome

The 27-worker locked probe changed 1, 2, or 3 shared evidence values simultaneously in 2-, 4-, and 8-frame chains. Before mutation, the runner derived readers by traversing each evidence node's live incoming `derived_from_evidence` edges, then mapped candidate readers through their live `has_concept` owners. The result matched both the scoring rule's explicit boundary read and the expected endpoint owners in every worker:

- N=2, mutate edge 0: owners `{0,1}`.
- N=4, mutate edges 0 and 1: owners `{0,1,2}`.
- N=8, mutate edges 0, 1, and 5: owners `{0,1,2,5,6}`.

Mapped-required scoped closure matched full closure exactly in all nine pairs and required zero work from the final full fixed-point probe. Omitting frame 1 produced stale projections in all nine cases; catch-up made positive progress and restored exact equality. All baseline and recovered outcomes selected the expected candidates and passed full fixed-point checks. The independent analyzer passes all 17 provenance, matrix, mapping, ownership, parity, omission, recovery, and timing gates.

## Descriptive costs

Medians across three fresh workers per arm/size. Mapping and frame reopening are timed separately from boundary writes, epoch invalidation, and closure. The reopening step is common setup work but excluded from the closure timer.

| Frames | Derived owners | Live access-to-owner map | Reopen affected frames | Full closure | Mapped-required scoped closure | Omitted-frame arm + catch-up |
|---:|---|---:|---:|---:|---:|---:|
| 2 | 0, 1 | 19 µs | 52 µs | 0.099 ms / 4 steps | 0.180 ms / 10 steps / 4 turns | 0.173 ms / 6 steps / 4 catch-up steps |
| 4 | 0, 1, 2 | 30 µs | 82 µs | 0.155 ms / 4 steps | 0.428 ms / 19 steps / 6 turns | 0.397 ms / 14 steps / 4 catch-up steps |
| 8 | 0, 1, 2, 5, 6 | 49 µs | 126 µs | 0.256 ms / 4 steps | 1.159 ms / 33 steps / 10 turns | 1.086 ms / 28 steps / 4 catch-up steps |

At eight frames, adding the separately timed mapping and reopening medians gives a rough total of 0.44 ms for full closure and 1.33 ms for mapped scoped closure. This sum is descriptive; the samples are not paired at the individual timing-operation level. The owner-map time grows with the number of candidate readers visited, while generic scoped closure again costs more than a full scan on this small rule family.

## Limits

This validates a transparent caller-side dependency walk for one authored chain and specific typed access relation. It does not extract dependencies from arbitrary rules/effects, use native observers, include concurrent mutation, cover dynamic edge birth/deletion, or establish locality prevalence on natural tasks. The owner ids are known Microtheory scopes. The probe therefore informs the contract a general event-to-owner mapper would need, but does not implement that mapper.

## Artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_MULTI_BOUNDARY_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_conversation_multi_boundary_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_conversation_multi_boundary_v1.py)
- [Accepted raw capture](../../../evaluation/reports/substrate_conversation_multi_boundary_v1_20260926.json)
- [Independent analysis](../../../evaluation/reports/substrate_conversation_multi_boundary_v1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/conversation_multi_boundary_lock_20260926.json)
