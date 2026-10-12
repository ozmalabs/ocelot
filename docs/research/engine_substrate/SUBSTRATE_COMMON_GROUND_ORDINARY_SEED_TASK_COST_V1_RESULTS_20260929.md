# Common-ground ordinary seed/task cost v1 results

## Result

The current-source replay completed ten fresh workers under an unchanged
source/native lock. The independent analyzer passes **106/106 checks**. Each
worker loaded the registered `conversation`, `conversation_discourse_state`,
and `relations` seed closure, retained exactly the three active discourse
lifecycle rules, passed the two-goal identity and common-ground oracles, and
reached a no-change terminal probe. All terminal graph digests match. The
ordinary `inner.run_rules` path ran ten times per worker; no scale counters
were enabled and their final snapshot is all zero.

Median wall/CPU stage times were:

| Stage | Median wall | Median CPU | Wall range |
|---|---:|---:|---:|
| Python module imports inside worker | 54.53 ms | 54.52 ms | 50.22–68.64 ms |
| Fixture read | 65 μs | not separately captured | 55–88 μs |
| Bare adapter initialization | 255 μs | 256 μs | 241–325 μs |
| Selective registered seed load | 5.48 ms | 5.50 ms | 4.80–15.85 ms |
| Chat and discourse-state setup | 105 μs | 105 μs | 102–143 μs |
| Ten event constructions and six fixture identity links | 766 μs | 767 μs | 700–1,015 μs |
| Ten ordinary native closures | 262 μs | 264 μs | 242–315 μs |
| Terminal no-change probe | 5.3 μs | 5.0 μs | 4.5–7.9 μs |
| Full measured worker span | 77.79 ms | 77.74 ms | 72.52–101.88 ms |

Median peak RSS was **33,088 KiB** (range 33,088–33,100 KiB). The full span
starts inside the child after source fingerprinting and excludes OS process
launch. The table's timed components leave a derived median of about 17.0 ms
wall unallocated, principally encompassing checkpoint graph serialization,
digest/oracle readback, and harness work. Thus this is a stage profile, not a
fully attributed end-to-end decomposition.

## Limits and next gate

This isolates the ordinary `load_seeds_into` API from a bare
`WorldAdapter(seeds=())`; it is not the default core-seed boot, actual
`receive_utterance` ingestion path, or a production conversation. The six
`for_goal` relations are explicit fixture inputs required by the task oracle.
The 10-event closure total is far smaller than import, seed-load, and
unattributed harness cost in this small fixture. Do not extrapolate these
times to larger graphs or natural conversations.

Next capture the same stage boundaries on a representative current-source
production ingestion path with default adapter boot, and repeat closure-work
analysis on an independently authored task/rule topology. Time checkpoint
serialization and semantic readback separately to close the measured-span
remainder.

## Artifacts

- [Preregistration](SUBSTRATE_COMMON_GROUND_ORDINARY_SEED_TASK_COST_V1_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_common_ground_ordinary_seed_task_cost_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_common_ground_ordinary_seed_task_cost_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/common_ground_ordinary_seed_task_cost_v1_lock_20260929.json)
- [Ten-worker raw capture](../../../evaluation/reports/common_ground_ordinary_seed_task_cost_v1_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/common_ground_ordinary_seed_task_cost_v1_analysis_20260929.json)

Claim boundary: one selected seed closure and a frozen two-goal benchmark task
on the default native closure API, from a bare adapter. It establishes
reproducible local stage costs and task semantics, not production route
coverage, natural prevalence, broad latency, or substrate-scale tractability.
