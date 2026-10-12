# Live self-report work trace v1.2 results

Date: 2026-09-28  
Status: complete capture; functional capability gate failed; operation accounting passed.

## Capture integrity

The run used three fresh worker processes from `/tmp/ocelot_self_report_work_trace_v1_2`. The source snapshot was built only after two consecutive source-lock reads agreed. The copied Python/seed closure (1,671 files), 20 individually locked sources, native extension, native build record, and Rust source fingerprint all matched the stable source. Each worker's start and finish lock matched the frozen lock. The archived compressed source bundle is [available here](../../../evaluation/substrate_capability/source_bundles/live_self_report_work_trace_v1_2_20260928.tar.zst) (SHA-256 `a0e903ff527c1c7c1cd6571efcb5f27c9c769762afb9ba6055793768883bacdd`).

The raw capture is [the JSON report](../../../evaluation/reports/live_self_report_work_trace_v1_2_20260928.json), its frozen inputs are [the source lock](../../../evaluation/substrate_capability/live_self_report_work_trace_v1_2_lock_20260928.json), and the independently computed checks are [the analyzer output](../../../evaluation/reports/live_self_report_work_trace_v1_2_analysis_20260928.json). The analyzer returned a failing capability gate as preregistered; no worker was dropped.

## Functional result

All three workers returned the same result for both prompts. `report your organisation` returned “I understood that as an instruction to report 'organisation', but I hold no faculty for it yet -- I've filed it as a gap to work on.” `describe who you are` returned “I hold real state for that, but no fluent account of it yet.” Both turns had no communication route and no associated Goal. Thus, the previously observed resolved `self_report` route did not reproduce on this source snapshot. This is a current-source capability shortfall, not a scheduler instrumentation failure. It corroborates the source-version-sensitive regression already recorded in the route regression and contrast panels; it does not establish why the route changed.

## Work and attribution result

Each turn's all-scope work rows reconciled with scoped and process-global scheduler/deferred-queue snapshots; no events were dropped. The analyzer observed 78 work rows across four graph scopes for turn 0 and 72 across four scopes for turn 1 in every worker. The turns were deterministic across the three workers at the recorded graph/reply level.

For turn 0, aggregate candidate tests were 49,512 and Term evaluations 539,803; for turn 1, 35,499 and 368,735. Per-rule and per-clause candidate attribution, unmatched totals, and Term variant totals all reconciled. The repeated totals describe this exact full-seed source snapshot and these two prompts, not a general workload distribution or asymptotic bound.

## Claim boundary and follow-up

This capture validates all-scope scheduler/deferred-queue accounting and matcher/Term attribution on a current self-report-adjacent conversation route, including a reproducible route shortfall. The original positive-route task gate fails. The measurement cannot claim the successful action route is currently operational, explain the regression, estimate route prevalence, prove frame locality, or establish scaling. Next, use source history and controlled interventions to isolate the minimum change that restores the action route, then rerun the frozen positive-route contract against the isolated change. Keep this negative current-source result in the capability map until that gate is shown to pass again.

An initial source-closure comparison with the 2026-09-27 matcher-cost positive-route lock found 25 changed files among 1,669 shared Python/seed paths and two newly present paths. That earlier lock records hashes but no source bundle; its locked contents differ from both the current worktree and `HEAD`. The comparison establishes source-version drift, but it does not identify a causal edit, and the exact successful source snapshot is not presently replayable from the retained lock alone. A causal restoration study therefore first needs recovery of that source snapshot or an explicitly labeled reconstruction; do not attribute the regression to any one of the changed files based only on this hash comparison.
