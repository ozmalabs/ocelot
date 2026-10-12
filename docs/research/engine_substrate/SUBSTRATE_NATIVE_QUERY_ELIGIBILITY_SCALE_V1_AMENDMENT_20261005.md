# Native query-eligibility scaling v1 implementation amendment

The first harness launch attempted 25 workers but all failed before measurement because the native rule API requires `add_edge`'s target argument to be a variable name, not an `ArgminUnique` expression. The failed capture and its source lock are retained at `evaluation/reports/native_query_eligibility_scale_v1_implementation_failure_20261005.json` and `evaluation/substrate_capability/native_query_eligibility_scale_v1_implementation_failure_lock_20261005.json`.

The selector now follows the already exercised v1.3 implementation shape: it stores the `ArgminUnique` result as an episode attribute. This is a harness schema correction only. Workload sizes, predictions, ranks, timing boundaries, parity gates, and analysis remain as preregistered. The corrected runner receives a new lock before any measured worker is run.

