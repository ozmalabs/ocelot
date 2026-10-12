# Directed boundary replay results

**Run:** 2026-09-25. **Evidence grade:** pre-locked synthetic mechanism run on the current CAN rule engine.

## Result

The runner used 12 Concept nodes in three four-node Microtheories, with directed path edges `i → i+1`. A +1 field at the final node settled to the all-+1 state. It then repeated deletion, insertion, negative-weight replacement, and positive-weight replacement of boundary edge `7 → 8` three times (12 actions total).

Full rescan and caller event scheduling matched exact state at every action. All 24 measured arm/action checkpoints terminated and had zero residual under an independent recomputation of the CAN update equation. Every mutation changed eight node states. The omitted-notification deletion control left residual 1, confirming the control was sensitive.

| Measure, summed over 12 actions | Full rescan | Event queue |
|---|---:|---:|
| Progress applications | 96 | 96 |
| Scoped frame turns | 36 | 24 |
| Terminal residual failures | 0 | 0 |

Event propagation therefore reduced scoped frame turns by one third on this fixed path while preserving progress count and exact state. No wall-time or allocation claim is supported.

Artifacts: [preregistration](SUBSTRATE_DIRECTED_BOUNDARY_REPLAY_PREREG_20260925.md), [runner](../../../scripts/substrate_directed_boundary_replay.py), [lock](../../../evaluation/substrate_capability/directed_boundary_replay_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_directed_boundary_replay_20260925.json), [independent analyzer](../../../scripts/analyze_substrate_directed_boundary_replay.py), and [analysis](../../../evaluation/reports/substrate_directed_boundary_replay_analysis_20260925.json).

## Claim boundary and next gate

This validates reconstruction of the caller-side directed dependency relation after repeated single-edge mutations on one synthetic path, with full rescan as the reference. It does not test simultaneous mutation during a rule firing, arbitrary topologies, node birth/deletion in the same sequence, automatic native effect-to-frame notification, or a second runtime task path. Next combine directed mutation with node lifecycle changes and measure a second workload before generalizing the tractability claim.
