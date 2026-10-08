# Response-priority residual-continuation v1.2.1: counterbalanced cost preregistration

Date: 2026-10-06  
Status: preregistered four-pair counterbalanced replication; same task family and fixed engine build.

## Question

Does the response-plus-continuation cost signal persist when global and priority arm order is counterbalanced across fresh paired workers?

## Design

Repeat the exact seven-turn held-topic workload, four-rule ambient partition, native extension, and mutation-journaling-off measurement from v1.2 cost. Use four fresh worker pairs (eight workers total), `PYTHONHASHSEED=0`, and the following preregistered pair order: global/priority, priority/global, global/priority, priority/global. Worker/replicate order is preserved in the capture. Every worker boots independently; report boot separately. Capture response path and continuation times, rule-work counters, post-response residuals and semantic outcomes. No code or seed changes are allowed after the lock is written.

## Gates

1. Eight-worker source-lock and worker-input stability pass; journaling remains disabled.
2. Pair order matches the lock exactly, with distinct PIDs for all workers.
3. Replies, held-topic outcomes, graph fingerprints, cardinalities, and convergence match within and between arms for every turn.
4. Report paired replicate differences and per-turn distributions; distinguish response, continuation, and total costs. Do not use a single aggregate ratio as proof of general speedup.

This is an order-counterbalanced replication on one authored task family, not a natural-task prevalence or scale study. Even a consistent result only supports the next cross-family gate.

## Artifacts

Runner: `scripts/substrate_response_priority_residual_continuation_v1_2_1_counterbalanced_20261006.py`  
Analyzer: `scripts/analyze_response_priority_residual_continuation_v1_2_1_counterbalanced_20261006.py`  
Capture: `evaluation/reports/response_priority_residual_continuation_v1_2_1_counterbalanced_20261006/capture.json.gz`  
Lock: `evaluation/substrate_capability/response_priority_residual_continuation_v1_2_1_counterbalanced_20261006_lock.json`
