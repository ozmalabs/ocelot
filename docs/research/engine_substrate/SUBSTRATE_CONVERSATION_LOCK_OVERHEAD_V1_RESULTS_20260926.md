# Conversation lock overhead v1 results

## Result

The source-locked run completed 20 pairs (40 timed full turns) on one full-seed adapter after two warmups. All 40 turns returned the expected describe-scene baseline. Guarded turns had a median of 1.724 s and p90 of 2.234 s; no-op-lock control turns had a median of 1.664 s and p90 of 2.249 s. The median within-pair guarded-minus-control delta was +18.1 ms, with observed paired deltas from −67.1 ms to +109.2 ms.

This result is **inconclusive about lock overhead**: the paired variation is much larger than the median delta, and the graph evolves across turns on this one adapter. It does show that this route itself is expensive in the captured environment (roughly 1.7 s/turn), so the earlier guess that the guard would be near-zero relative to full turns is not established. A fresh-adapter randomized-block study and direct uncontended lock microbenchmark are appropriate follow-ups before attributing the delta.

## Evidence and limits

- Preregistration: [`SUBSTRATE_CONVERSATION_LOCK_OVERHEAD_PREREG_20260926.md`](SUBSTRATE_CONVERSATION_LOCK_OVERHEAD_PREREG_20260926.md)
- Runner: [`substrate_conversation_lock_overhead_v1.py`](../../../scripts/substrate_conversation_lock_overhead_v1.py)
- Analyzer: [`analyze_substrate_conversation_lock_overhead_v1.py`](../../../scripts/analyze_substrate_conversation_lock_overhead_v1.py)
- Lock: [`conversation_lock_overhead_v1_lock_20260926.json`](../../../evaluation/substrate_capability/conversation_lock_overhead_v1_lock_20260926.json)
- Raw capture: [`substrate_conversation_lock_overhead_v1_20260926.json`](../../../evaluation/reports/substrate_conversation_lock_overhead_v1_20260926.json)
- Analysis: [`substrate_conversation_lock_overhead_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_conversation_lock_overhead_v1_analysis_20260926.json)

One adapter, one route, one environment, and an evolving graph were measured. This is not a multi-adapter latency estimate, a concurrency throughput result, or a native API benchmark.
