# CAN runtime match-order sensitivity v1.1 held-out results (2026-09-29)

## Result

The preregistered held-out replay completed 16 fresh workers: replicates 2 and 3, N=128/256, path/banded2 topologies, and 2-/3-state modes. All eight gates pass: worker and cell coverage, registered rule variants, semantic parity, audit parity, fixed points, target counters, and source stability. Each cell has two independent replicates. The sparse-first order preserves final graph/state/progress and reduces candidate and Term work in every cell.

| N | Topology | Mode | Candidate tests, baseline → sparse-first | Reduction | Term evaluations, baseline → sparse-first | Reduction | Plain closure time, baseline → sparse-first (ms) | Time ratio |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 128 | path | 2state | 6,992,552 → 210,989 | 33.1× | 35,239,752 → 1,198,193 | 29.4× | 1509.3 → 413.1 | 3.65× |
| 128 | path | 3state | 4,447,700 → 169,898 | 26.2× | 22,534,695 → 962,916 | 23.4× | 982.5 → 280.8 | 3.50× |
| 128 | banded2 | 2state | 6,762,831 → 204,410 | 33.1× | 34,091,147 → 1,160,426 | 29.4× | 1477.1 → 384.1 | 3.85× |
| 128 | banded2 | 3state | 5,355,031 → 189,329 | 28.3× | 27,091,910 → 1,073,393 | 25.2× | 1181.5 → 325.6 | 3.63× |
| 256 | path | 2state | 78,812,021 → 1,194,731 | 66.0× | 395,542,729 → 6,786,807 | 58.3× | 18183.9 → 4627.7 | 3.93× |
| 256 | path | 3state | 40,526,762 → 765,992 | 52.9× | 203,919,523 → 4,341,232 | 47.0× | 9055.3 → 2380.1 | 3.80× |
| 256 | banded2 | 2state | 78,056,281 → 1,185,087 | 65.9× | 391,764,029 → 6,732,575 | 58.2× | 18895.6 → 4675.0 | 4.04× |
| 256 | banded2 | 3state | 58,051,652 → 999,568 | 58.1× | 291,767,209 → 5,667,082 | 51.5× | 13340.9 → 3501.8 | 3.81× |

The measured plain closure timings are instrumentation-off. Across these held-out fixture draws, candidate work falls 26.2–66.0×, Term evaluations 23.4–58.3×, and elapsed closure time 3.50–4.04×. This is replication within the same authored CAN workload family, not evidence of natural-workload prevalence or a general join optimizer. The seed is not modified; the reordered rules are installed in-memory by the runner.

## Reproduction and evidence

- [Preregistration](CAN_RUNTIME_MATCH_ORDER_SENSITIVITY_V1_1_HELDOUT_PREREG_20260929.md)
- [Runner](../../../evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_1_lock_20260929.json)
- [Raw capture](../../../evaluation/reports/can_runtime_match_order_sensitivity_v1_1_20260929.json)
- [Original v1 result](CAN_RUNTIME_MATCH_ORDER_SENSITIVITY_V1_RESULTS_20260929.md)

## Next gate

The CAN result is now replicated on held-out fixture draws. The separate current-source anaphora replay checks a second authored rule family and its exact task/graph parity; its result is recorded in [the anaphora v1.2 report](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_2_CURRENT_SOURCE_RESULTS_20260929.md). Broader optimizer adoption still requires more rule families and representative traces, including index invalidation and any cost paid to choose/install the order.
