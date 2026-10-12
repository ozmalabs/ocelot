# Directed boundary and node lifecycle replay results

**Run:** 2026-09-25. **Evidence grade:** corrected preregistered synthetic mechanism confirmation.

## Preserved v1 harness failure

The original v1 run failed after node birth: the event arm seeded frame 1 for every action even though a new Concept was owned by frame 2. The audit showed edge-mutation checkpoints had passed; birth and deletion then diverged, while full rescan settled. A focused diagnostic confirmed direct scoped settlement of frame 2 finds the born node after the same directed edge sequence. This was a harness notification error, not evidence of an engine defect. Preserve the [v1 preregistration](SUBSTRATE_DIRECTED_BOUNDARY_LIFECYCLE_REPLAY_PREREG_20260925.md), [runner](../../../scripts/substrate_directed_boundary_lifecycle_replay.py), and [failed raw report](../../../evaluation/reports/substrate_directed_boundary_lifecycle_replay_20260925.json).

## Corrected v1.1 result

Amendment v1.1 seeds frame 1 for mutations to boundary edge `7 → 8` and frame 2 for birth/deletion of a node owned there. The 18-action sequence repeats directed edge deletion, insertion, positive/negative weight replacement, and node birth/deletion three times. Full rescan and event arms match exact states and active-node masks at every checkpoint. Independent equation recomputation reports zero residual at all 36 measured checkpoints. The omitted-notification deletion control retains residual 1.

| Measure across 18 actions | Full rescan | Event queue |
|---|---:|---:|
| Progress applications | 171 | 171 |
| Scoped frame turns | 60 | 42 |
| Terminal residual failures | 0 | 0 |

Event scheduling uses 30% fewer frame turns in this fixed synthetic path while preserving the number of progressing rule applications. Wall time, allocation, and general graph scaling were not measured.

The disclosed [v1.1 amendment](SUBSTRATE_DIRECTED_BOUNDARY_LIFECYCLE_REPLAY_V1_1_AMENDMENT_20260925.md), [runner](../../../scripts/substrate_directed_boundary_lifecycle_replay_v1_1.py), [lock](../../../evaluation/substrate_capability/directed_boundary_lifecycle_replay_v1_1_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_directed_boundary_lifecycle_replay_v1_1_20260925.json), [independent analyzer](../../../scripts/analyze_substrate_directed_boundary_lifecycle_replay_v1_1.py), and [analysis](../../../evaluation/reports/substrate_directed_boundary_lifecycle_replay_v1_1_analysis_20260925.json) preserve the provenance chain.

## Claim boundary

This confirms repeated directed boundary invalidation plus node lifecycle handling for one rule, one path, and one frame assignment. It does not establish natural locality, arbitrary dynamic topology, native notifications, or production GALS. Next test a second runtime task path and a wider set of mutation interleavings before generalizing.
