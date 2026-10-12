# Response-priority residual-continuation v1.2: operational-cost preregistration

Date: 2026-10-06  
Status: preregistered three-worker-per-arm follow-up; rule-write mutation attribution disabled.

## Question

For the finite-parity workload established by the confirmatory run, how is measured work and elapsed time divided between response-priority settlement and later all-area continuation?

## Design

Use the same source and inputs as the v1.2 confirmation: the seven-turn held-topic workload; global and priority arms; the four-rule ambient partition; three fresh workers per arm; and `PYTHONHASHSEED=0`. Pin the rebuilt native extension and this protocol/runner pair in a new lock. Disable `OZMA_RULE_LIFECYCLE_TRACE` so per-rule graph-write journaling is off. Retain ordinary wall-clock measurement around response and continuation phases. This panel remains diagnostic: Python host adapters still run as normal, and measured cost is specific to this workload and machine.

For every turn and arm, report response elapsed time, continuation elapsed time, rule progress/attempt counts where exposed, residual counts before continuation, continuation steps/rounds, total phase time, node/edge counts, and semantic parity. Summarize per-worker and per-turn distributions; do not pool boot time into turn cost. The global arm has no deferred-area work, so report its response phase separately and state the continuation path explicitly.

## Gates

1. Six-worker source-lock and input stability pass; mutation attribution is disabled.
2. All seven turns retain reply, held-topic outcome, graph, and zero-residual parity.
3. Every arm/turn reports the response and continuation phases separately; no timing from capture serialization or analysis is included.
4. Report raw per-worker observations and medians without a speed threshold or broad generalization.

A pass measures only phase-specific cost on this workload. It does not establish commodity-scale performance, asymptotic behavior, natural-task prevalence, or the acquisition cost of learned structure.

## Artifacts

Runner: `scripts/substrate_response_priority_residual_continuation_v1_2_cost_20261006.py`  
Analyzer: `scripts/analyze_response_priority_residual_continuation_v1_2_cost_20261006.py`  
Capture: `evaluation/reports/response_priority_residual_continuation_v1_2_cost_20261006/capture.json.gz`  
Lock: `evaluation/substrate_capability/response_priority_residual_continuation_v1_2_cost_20261006_lock.json`
