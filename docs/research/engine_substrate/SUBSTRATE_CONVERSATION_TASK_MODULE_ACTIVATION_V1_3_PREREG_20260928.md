# Conversation task module-activation panel v1.3

Date: 2026-09-28  
Status: preregistered current-source replay; execution has not started.

## Reason for this version

After v1.2 completed, `substrate/world_adapter.py` changed to serialize public adapter calls through a wrapper and add a post-turn heap-reclamation hint. The v1.2 capture remains valid for its locked snapshot, but it does not represent this newer adapter implementation. V1.3 repeats the same five task contracts on the current source state. This is a new snapshot, not a causal comparison.

## Fixed design and instrumentation amendment

Keep the five v1.2 stimuli, schedule, two fresh workers per condition, task oracles, warmed WordNet input, and all source/cache gates unchanged. Amend only the conversation-extent detector: in addition to a direct `WorldAdapter.converse` frame, recognize the serialized wrapper frame when its closure target is the `converse` method and its receiver is a `WorldAdapter`. This is necessary because Python's wrapper code object is named `wrapped` even though it preserves the wrapped method's public `__name__`. Require exactly one such extent per worker; no other adapter method can satisfy the root predicate.

## Lock and gates

Lock this amendment, v1.3 runner/analyzer, base panel inputs, Python/native sources and build metadata, selected runtime data, WordNet corpus, and its existing digest-matched SQLite cache. Require the same 12 integrity, input-stability, cache, schedule, task-oracle, and per-condition footprint gates as v1.2. Any source/cache drift censors the capture. Do not pool the earlier v1.1/v1.2 timing observations with v1.3.

## Claim boundary

This is a current-source replay of five authored conversation contracts. Python activation traces do not establish Rust operation counts, causal necessity, natural task prevalence, or uninstrumented service cost. Task outcomes and instrumented timings remain per-condition and descriptive.
