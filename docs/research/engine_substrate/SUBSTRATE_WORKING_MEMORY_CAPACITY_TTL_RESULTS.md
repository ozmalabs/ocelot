# Working-memory capacity, replacement, and TTL — 2026-09-25

## Result

The amended pre-locked four-scenario run matched all expected graph outcomes:

- **Same-task capacity:** with the policy set to two slots, two inputs were accepted and the third same-task input was refused with `capacity_limit`. Two active slots remained.
- **Cross-task replacement:** after admitting low-priority (`0.1`) and high-priority (`0.9`) chat items, a project item at priority `0.8` replaced the lowest-priority foreign-task slot. The high-priority chat item remained; the replaced slot recorded `interference_count=1` and `cross_task_interference`.
- **Unmaintained expiry:** input at epoch 1 produced expiry 9. The item remained active at epoch 8, then expired at epoch 9 with `maintenance_lapsed` and no held content.
- **Maintained expiry:** maintenance at epoch 8 extended the expiry to 16. The slot remained active at epoch 9, then expired at epoch 16 and released its content.

## Cost observations

Each case used a fresh process. Boot took 11.4–11.9 ms and peak RSS was 35.4–35.2 MiB (including Python/native import baseline). The first gate tick in each scenario took about 0.40–0.42 ms; subsequent gate and clock ticks took about 0.12–0.17 ms. These are single-run descriptive timings for tiny graphs, not scale estimates.

## Interpretation and limits

The current authored working-memory rules enforce bounded active slots, refuse same-task overflow, choose the lowest-priority foreign-task victim under this controlled case, and expire slots at the declared epoch boundary unless maintained. This is a selected mechanism envelope, not evidence of effective natural-task memory management. It does not measure learned or utility-optimal eviction, high-contention simultaneous admissions beyond the pre-existing focused source case, long-term episodic retention, durable restart, corruption recovery, or large-scale costs.

## Harness amendment

The first locked invocation failed in the replacement worker because the harness attempted to JSON-serialize a native `NodeID`; no aggregate raw report or verdict was written. The runner was amended to stringify that diagnostic identifier. The task set and criteria were unchanged. The first lock is retained, and the amended preregistration note and v2 lock were frozen before the scored rerun.

## Reproducibility

- Protocol: [`SUBSTRATE_WORKING_MEMORY_CAPACITY_TTL_PREREG_20260925.md`](SUBSTRATE_WORKING_MEMORY_CAPACITY_TTL_PREREG_20260925.md)
- Harness amendment: [`SUBSTRATE_WORKING_MEMORY_CAPACITY_TTL_AMENDMENT_20260925.md`](SUBSTRATE_WORKING_MEMORY_CAPACITY_TTL_AMENDMENT_20260925.md)
- Original lock: [`working_memory_capacity_ttl_lock_20260925.json`](../../../evaluation/substrate_capability/working_memory_capacity_ttl_lock_20260925.json)
- Amended lock: [`working_memory_capacity_ttl_amended_lock_20260925.json`](../../../evaluation/substrate_capability/working_memory_capacity_ttl_amended_lock_20260925.json)
- Runner: [`substrate_working_memory_capacity_ttl.py`](../../../scripts/substrate_working_memory_capacity_ttl.py)
- Independent auditor: [`analyze_substrate_working_memory_capacity_ttl.py`](../../../scripts/analyze_substrate_working_memory_capacity_ttl.py)
- Raw run: [`substrate_working_memory_capacity_ttl_amended_20260925.json`](../../../evaluation/reports/substrate_working_memory_capacity_ttl_amended_20260925.json)
- Independent analysis: [`substrate_working_memory_capacity_ttl_analysis_20260925.json`](../../../evaluation/reports/substrate_working_memory_capacity_ttl_analysis_20260925.json)

All eight v2 input hashes matched during independent audit. This evidence concerns working-memory slots, distinct from episodic event storage and long-term ShapeIndex persistence.
