# Bigville connected-frame stress results

**Run:** 2026-09-25. **Evidence grade:** controlled topology stress on the current authored Bigville CAN runtime path. The injected cross-resident edges are benchmark perturbations; they are not part of the authored world model.

## Protocol and audit

The 100 resident CAN frames were built through the live Bigville builder and current `can_native_update_3state` rule. The benchmark compared full round-robin scoped settlement with the existing Python static dependency queue after adding (a) no cross-frame edges, (b) a 100-link frame ring, or (c) a 99-link star centered on resident 0. Each injected undirected link is represented by two directed `causal_influence` edges between the frames' `world_safe` Concepts, each with weight 0.2. Ten authored evidence updates were applied to the same resident positions in each arm.

All six fresh-process arms completed. The independent raw-record audit matched all locked source hashes, checked ring/star edge counts, reconstructed internal plus injected weights, recomputed every recorded fixed-point residual in canonical topic order, and found zero residuals at all 60 terminal checkpoints. Full and event arms had exact state equality at baseline and every checkpoint in all three topologies. See the [preregistration](SUBSTRATE_BIGVILLE_CONNECTED_FRAME_STRESS_PREREG_20260925.md), [runner](../../../scripts/substrate_bigville_connected_frame_stress.py), [lock](../../../evaluation/substrate_capability/bigville_connected_frame_stress_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_bigville_connected_frame_stress_20260925.json), [independent analyzer](../../../scripts/analyze_substrate_bigville_connected_frame_stress.py), and [analysis](../../../evaluation/reports/substrate_bigville_connected_frame_stress_analysis_20260925.json).

## Operation counts

| Topology | Injected undirected links | Full candidate pairs | Event candidate pairs | Full Term units | Event Term units | Event turns (median/update) |
|---|---:|---:|---:|---:|---:|---:|
| Disconnected | 0 | 7,545 | 95 | 80,368 | 1,084 | 1 |
| Ring | 100 | 7,525 | 125 | 91,432 | 1,408 | 2 |
| Star | 99 | 7,525 | 100 | 91,772 | 3,368 | 1.5 |

On these fixed workloads, event scheduling reduced candidate pairs by 98.3–98.7% and Term units by 96.3–98.7% against full round-robin scans. The star's high-degree hub raised event Term work relative to the disconnected and ring cases, while remaining below the full scan. Single-process wall times were recorded but are descriptive only; the runner order was not counterbalanced and setup/timing noise was not preregistered as a decision criterion.

## Claim boundary and next gate

This is evidence that the current static CAN wake queue preserves the full-graph fixed point for three symmetric, controlled boundary topologies and the selected mutation sequence. It does not establish arbitrary boundary-message semantics, directed-edge wakeup correctness, edge insertion/deletion during execution, native GALS, natural boundary prevalence, or scaling beyond this one 100-frame size. The next gate is a locked mutation sequence that changes cross-frame edges and tests directed read dependencies, with full rescan as the reference; follow with a second authored runtime task path before generalizing locality.
