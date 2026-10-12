# Live describe-scene access trace v2.4 preregistration (2026-09-27)

## Question

Does the complete v2.3 paired traced/untraced driver—including the rule-work audit, per-request trace interval, nested reply readback, and A-selection/B-wait schedule—complete on the same current source generation where trace-only isolation passed?

## Design

Use the v2.3 fixture and three paired fresh-process traced/untraced replicates, on an exact source closure lock captured before launch and checked at every worker start/end and after all workers finish. Preserve the authored A/B ordering and selection barrier. Keep separate gates for thread completion, both request lifecycles, exact pair semantic parity, source stability, and trace completeness. Do not interpret any cost or locality result unless every lifecycle and integrity gate passes.

The v2.3 run was censored on a different source snapshot; v2.4 is a fresh current-source execution and does not retroactively repair that evidence. The trace-only isolation report is an independent diagnostic, not a control arm for this richer schedule.

## Gates and claim boundary

All six workers must join without errors; both Goals must resolve through selection, execution, and action-result events; A/B scheduling and paired graph/output parity must pass; source locks must remain stable; traced access counters must be complete and reconcile, with no events in untraced arms. Any failed lifecycle gate censors all access-cost/locality claims.

Even a passing run provides selected native accesses for this one task fixture, not complete dynamic dependency coverage or natural-task prevalence.

## Reproduction

Create the lock with `scripts/substrate_live_describe_scene_access_trace_v2_4.py --lock`, store `locked_inputs` at `evaluation/substrate_capability/live_describe_scene_access_trace_v2_4_lock_20260927.json`, then run with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. See the [runner](../../../scripts/substrate_live_describe_scene_access_trace_v2_4.py), [summary](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_20260927.json), and [raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json).
