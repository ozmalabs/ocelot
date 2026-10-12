# Scheduler dirty-density and positive-match v1 results (2026-09-26)

## Result

The amended, source/native-locked capture covered 54 cells in fresh processes: `R={8,32,128}`, three dirty counts per size, prefix/suffix placement, and three replications. All worker inputs remained stable. Independent analysis passed **219/219 checks**.

Across every cell, plain and audit-enabled runs had identical reports and whole graphs. Exactly `k` positive one-edge matches produced exactly `k` derived edges and progress steps, with a two-pass fixed point. Integer work matched the corrected equations:

| Work item | Prefix | Suffix |
|---|---:|---:|
| Passes | 2 | 2 |
| External-poll slots | `2R` | `2R` |
| Fixed-point probe slots | `R+1` | `2R-k+1` |
| Dirty-vector slots | `R` | `R` |
| Selected rules / enumerations | `k` / `k` | `k` / `k` |

The probe result distinguishes dirty count from dirty position: with a dirty prefix it short-circuits at slot zero, while a suffix requires scanning to its first dirty slot. External polling and dirty-vector construction still scan the full rule vector. Planning-time counters varied and are descriptive only.

## Protocol correction and limits

An exploratory first run exposed an incorrect predicted prefix probe count. Its raw file was overwritten by the final capture and is not retained; it is excluded from the confirmatory evidence. The amendment records the corrected equation and that limitation. No engine source or workload changed between attempts.

This is an authored one-edge positive family after one controlled graph mutation. It does not establish work on general joins, repeated mutation dynamics, scoped scheduling, deferred queue families, natural tasks, frame locality, or commodity-scale throughput. Next measure positive joins with multiple pattern edges and mutation-driven requeues, while capturing complete queue work; then compare identical workloads under full and boundary-preserving execution only after runtime access dependencies are complete.

## Artifacts

- [Preregistration](SUBSTRATE_SCHEDULER_DIRTY_DENSITY_V1_PREREG_20260926.md)
- [Amendment](SUBSTRATE_SCHEDULER_DIRTY_DENSITY_V1_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_scheduler_dirty_density_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_scheduler_dirty_density_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_scheduler_dirty_density_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_scheduler_dirty_density_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_scheduler_dirty_density_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/scheduler_dirty_density_v1_lock_20260926.json)
