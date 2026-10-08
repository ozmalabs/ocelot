# Positive join multiplicity and operation-work trace v2 results

**Result:** the native work trace reconciles queue-family work with scale-audit counters while varying successful positive-join multiplicity and loaded writer/target pairs.

The source/native-locked panel has 27 fresh processes: `R={1,8,32}` writer/target pairs, join multiplicity `M={1,4,16}`, and three replications per cell. All **219/219 checks pass**, including audit-off/audit-on graph and report parity, fixed-point completion, exact target/trigger/framebuffer outcomes, zero trace drops, valid operation markers, and operation-trace queue reconciliation.

For every cell, each `rule_edits` and `fb_samples` queue enqueues and drains exactly `R×M` items in one family-specific batch. Scheduler pass count remains 3; selected-rule, dirty-vector, and external-poll units are each `6R`. These remain stable across `M` because the fixture creates more successful bindings per writer while preserving the writer count. Median candidate tests grow from 7/56/224 at `M=1` to 277/2,216/8,864 at `M=16` for `R=1/8/32`. This is a cost signal for the authored join shape; it does not establish an asymptotic law.

| Writer/target pairs R | Candidate tests, M=1 | M=4 | M=16 | Queue items per family, M=1 / 4 / 16 |
|---:|---:|---:|---:|---:|
| 1 | 7 | 25 | 277 | 1 / 4 / 16 |
| 8 | 56 | 200 | 2,216 | 8 / 32 / 128 |
| 32 | 224 | 800 | 8,864 | 32 / 128 / 512 |

This trace covers full closure only. It builds on the earlier scoped/fallback work-trace panel for RulePatch, TrackIdentity, and NetCollapse; together with separate family studies, five queue families now have operation-level or family-counter evidence, but they are not all present in one workload trace. Host callbacks, full matching costs, memory use, natural-task prevalence, and general partition safety remain open. See the [v2 preregistration](SUBSTRATE_JOIN_MULTIPLICITY_WORK_TRACE_V2_PREREG_20261001.md), [runner](../../../scripts/substrate_join_multiplicity_work_trace_v2.py), [analyzer](../../../scripts/analyze_substrate_join_multiplicity_work_trace_v2.py), [source/native lock](../../../evaluation/substrate_capability/join_multiplicity_work_trace_v2_lock_20261001.json), [raw capture](../../../evaluation/reports/substrate_join_multiplicity_work_trace_v2_workers_20261001.json), and [analysis](../../../evaluation/reports/substrate_join_multiplicity_work_trace_v2_analysis_20261001.json).
