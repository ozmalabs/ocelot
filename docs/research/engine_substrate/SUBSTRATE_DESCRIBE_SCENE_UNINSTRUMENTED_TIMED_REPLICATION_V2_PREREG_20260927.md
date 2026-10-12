# Uninstrumented describe-scene timing replication v2 preregistration (2026-09-27)

## Question

What are the repeatable boot, two-request wall/CPU, and peak-memory costs of the live describe-scene fixture on the same source and native build used for v2.4?

## Design

Run five fresh Python processes sequentially. Each process boots seeds once, attaches the same three-percept scene, and starts two simultaneous identical `converse()` requests behind a barrier. Do not enable access tracing, rule-scale auditing, measurement lock proxies, selection barriers, or graph readback during the timed calls. Record per-thread wall and CPU durations, whole-process boot CPU/wall, RSS after boot and at exit, peak RSS, replies, and request-bound Goal/lifecycle evidence. Lock the full runtime source closure and native extension before and after every worker and the parent process.

This measures one controlled fixture and a concurrent two-request schedule. It does not provide isolated single-call cost, natural-task prevalence, or asymptotic scaling. The observed implementation source may be changing; any lock drift censors the series.

## Gates

- Five unique worker processes use identical locked inputs.
- Each process finishes two requests, both callers join, both expected replies return, and each inbound has one resolved Goal with selection, execution, and action-result events.
- No worker exceptions and identical source locks before/after.
- Report median, min/max, and per-replicate values; never hide a censored worker.

## Artifacts

[Runner](../../../scripts/substrate_describe_scene_uninstrumented_timing_v2.py), [lock](../../../evaluation/substrate_capability/describe_scene_uninstrumented_timing_v2_lock_20260927.json), [raw results](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_20260927.json), [analysis](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_analysis_20260927.json).

## Outcome (2026-09-27)

All seven execution gates pass. Five worker processes record the preregistered wall/CPU/RSS fields, and a separate GNU `/usr/bin/time -v` worker confirms the peak-RSS measurement. See the [results and limits](SUBSTRATE_DESCRIBE_SCENE_UNINSTRUMENTED_TIMED_REPLICATION_V2_RESULTS_20260927.md).
