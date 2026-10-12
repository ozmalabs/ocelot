# Reusable snapshot memory and reclamation v2 results

Date: 2026-10-01

## Result

The source-current panel completed 45 measured fresh workers across 3 sizes × 3 storage backends × 5 repeats, plus 9 warmups in a seeded randomized schedule. All 8 independent analyzer checks passed: the grid and process count are complete, runner/source/native fingerprints match, all lifecycle stages were sampled, primary state stayed unchanged, branch writes remained local, and a later fork reproduced the captured base.

At 50,771 total fixture nodes (50,000 added), median current PSS deltas from each worker's pre-snapshot primary baseline were:

| Backend | Snapshot alive | Branch alive | Branch dropped, snapshot alive | Snapshot dropped |
|---|---:|---:|---:|---:|
| Full copy | 10,996 KiB | 27,832 KiB | 27,860 KiB | 27,860 KiB |
| Shared slabs | 3,004 KiB | 11,844 KiB | 11,872 KiB | 11,872 KiB |
| Shared graph pages | 284 KiB | 772 KiB | 772 KiB | -88 KiB |

The shared graph-page route has a much smaller marginal resident footprint in this large synthetic fixture. Its snapshot-plus-branch PSS was about 0.75 MiB above primary baseline, versus about 27.2 MiB for full copy. Shared slabs fall between them. These are whole-process Linux PSS observations, including runtime, Python, fixture, and allocator effects.

## Reclamation interpretation

The semantic lifecycle passes: after the candidate branch is dropped, a new fork from the still-live snapshot sees the original captured revision and no candidate-only node. PSS does **not** show reliable reclamation after Rust objects are dropped. Full-copy PSS remains near its high-water sample; shared graph-page PSS varies below baseline after snapshot drop. Allocator arenas, kernel page accounting, and process-level measurement noise prevent interpreting these stage deltas as live heap ownership or a reclamation guarantee. The study therefore validates branch disposal semantics and quantifies resident footprint at lifecycle stages, but leaves bounded-memory reclamation under pressure open.

At 0 and 10,771 total nodes, all three implementations' PSS varied materially with runtime/allocator state; no stable small-state PSS advantage is claimed. This is one host and one synthetic self-correction fixture without candidate prediction, rule execution, concurrent readers, active cancellation, or serving integration.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_SNAPSHOT_RECLAMATION_V2_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_snapshot_reclamation_v2.py)
- [Analyzer](../../../scripts/analyze_tho_snapshot_reclamation_v2.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_snapshot_reclamation_v2.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_snapshot_reclamation_v2_analysis.json)
