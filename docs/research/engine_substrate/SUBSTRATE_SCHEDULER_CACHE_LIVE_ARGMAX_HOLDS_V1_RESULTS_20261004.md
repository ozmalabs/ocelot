# Live Argmax/Holds scheduler-cache replay v1 results — 2026-10-04

The source-locked fixture passes all gates. A single native rule naturally populated one neighbour entry, one argmax entry, and one holds entry (`[reachable, neighbours, filter, argmax, holds, sd_ops] = [0,1,0,1,1,0]`). After forcing the rule dirty without a graph change, the full checkpoint restored exactly into two independent stores. Their next closure executions matched in global counters, per-rule work, graph output, and scheduler state.

This closes the evaluator-generated nonempty payload gap for this specific argmax/holds key shape. The fixture has one Microtheory, three Concept candidates, and one authored rule. It does not establish cache-hit frequency, natural-task prevalence, or scale. Reachable and SD-operation caches remain unsupported, and the primary-route V8 result separately covers nonempty neighbour/filter payloads.

Evidence: [preregistration](SUBSTRATE_SCHEDULER_CACHE_LIVE_ARGMAX_HOLDS_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/scheduler_cache_live_argmax_holds_v1.py), [source lock](../../../evaluation/substrate_capability/scheduler_cache_live_argmax_holds_v1_lock_20261004.json), and [capture](../../../evaluation/reports/scheduler_cache_live_argmax_holds_v1_20261004.json).
