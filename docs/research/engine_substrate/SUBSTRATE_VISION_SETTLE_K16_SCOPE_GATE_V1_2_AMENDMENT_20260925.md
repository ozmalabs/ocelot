# K=16 result reporting amendment v1.2

Date: 2026-09-25. The v1.1 four-arm outputs are preserved and their tuning/OSI parity audit remains valid. This amendment corrects the interpretation of per-frame termination fields.

The v1.1 runner labeled any positive `tick()` return as `tick_cycle_detected`. The API returns only a progress count, so this label does not prove that cycle detection fired and does not distinguish a fixed point from a repeated-state exit. The raw runner also retained counts by that label rather than each tick's progress value. Its `no_silent_or_zero_progress_probe_reports` check therefore does not validate termination statuses. Do not treat the tagged-tick `probe_status_counts` as termination statuses or infer per-call cap distance from them.

For v1.2 reporting, treat tagged-tick values solely as positive-return counts (the runner's branch records the label iff the returned count is positive); mark tick termination reason and exact per-call progress as unavailable in v1.1. Full-rescan `run_rules_report` statuses remain explicit. Tuning arrays, independently recomputed OSI, exact global/root-scoped parity, and exact tagged-tick/full-rescan response parity are unaffected. Future repetitions must persist tick progress values and use a cycle-reporting API if termination reason is an endpoint.
