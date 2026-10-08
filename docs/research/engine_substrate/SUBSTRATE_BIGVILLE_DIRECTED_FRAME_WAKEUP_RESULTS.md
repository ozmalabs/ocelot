# Bigville directed-frame wakeup results

**Run:** 2026-09-25. **Evidence grade:** controlled directionality mechanism probe on Bigville-constructed CAN frames. Injected links and the state intervention are synthetic.

## Preserved v1 sensitivity failure

The original locked v1 run used authored scenario evidence, but that intervention did not reliably change the state of a neighbor across the selected directed cut. The full and event arms matched with zero reported residuals, while the omission control also had zero residual in all three topologies. Its predeclared sensitivity check failed. Preserve [v1 protocol](SUBSTRATE_BIGVILLE_DIRECTED_FRAME_WAKEUP_PREREG_20260925.md), [v1 raw report](../../../evaluation/reports/substrate_bigville_directed_frame_wakeup_20260925.json), and [v1 lock](../../../evaluation/substrate_capability/bigville_directed_frame_wakeup_lock_20260925.json); do not interpret v1 as proving directed wakeup correctness.

## Amended v1.1 probe

The v1.1 amendment retains 12 frames and the three edge directions, but removes intra-frame causal edges, zeros fields/states, injects directed unit-weight cross-frame links, then sets one target frame's `world_safe.external_field` to +1. This forces controlled propagation through the current `can_native_update_3state` rule. The target positions are the chain sink, the leaves-to-hub center, and a hub-to-leaves leaf.

Full round-robin and event scheduling both reached zero residual under the independently recomputed full-graph update equation, and their final states matched for all three topologies. The omission control exposed stale dependencies in every topology:

| Topology | Directed links | Full turns | Event turns | Event enqueues | Omission residual |
|---|---:|---:|---:|---:|---:|
| Chain | 11 | 156 | 12 | 11 | 1 |
| Leaves → hub | 11 | 24 | 12 | 11 | 11 |
| Hub → leaves | 11 | 36 | 2 | 1 | 1 |

These turn counts include baseline settlement in `full turns`? No: they count the post-intervention settlement record only. Event queue visitation follows dependency direction: a changed target wakes source frames that read it. In the two fan-out cases, the event arm processes only relevant frames rather than all 12.

The [v1.1 protocol amendment](SUBSTRATE_BIGVILLE_DIRECTED_FRAME_WAKEUP_V1_1_AMENDMENT_20260925.md) discloses the intervention change. See [runner](../../../scripts/substrate_bigville_directed_frame_wakeup_v1_1.py), [lock](../../../evaluation/substrate_capability/bigville_directed_frame_wakeup_v1_1_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_bigville_directed_frame_wakeup_v1_1_20260925.json), [independent analyzer](../../../scripts/analyze_substrate_bigville_directed_frame_wakeup_v1_1.py), and [analysis](../../../evaluation/reports/substrate_bigville_directed_frame_wakeup_v1_1_analysis_20260925.json).

## Claim boundary

This shows that the caller-side static queue propagates state changes in both directed orientations for this single rule and controlled topology, while the omitted-notification controls detect the resulting stale state. It does not measure naturally occurring direction patterns, dynamic boundary-edge insertion/deletion, multiple rule families, native writer-to-frame notifications, or task-level utility. One size and one intervention per topology are mechanism evidence, not a scaling curve.
