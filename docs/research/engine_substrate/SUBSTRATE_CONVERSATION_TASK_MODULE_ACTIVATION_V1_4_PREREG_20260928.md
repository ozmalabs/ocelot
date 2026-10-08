# Conversation task module-activation panel v1.4

Date: 2026-09-28  
Status: preregistered current-source replay; execution has not started.

## Reason for this version

V1.3 was censored when `substrate/world_adapter.py` changed during its worker schedule. A new stable-source census now records that adapter hash, and the current hash has remained stable on recheck. V1.4 repeats the same five conversation task contracts against a fresh source lock. V1.3's partial records remain censored; v1.2 remains preserved for its earlier locked snapshot.

## Fixed design and instrumentation

Use v1.2's five stimuli, fixed schedule, two fresh workers per condition, independent task-oracle predicates, and prewarmed WordNet corpus/index. Use v1.3's wrapper-aware extent detection: accept either a direct `WorldAdapter.converse` frame or the serialized wrapper frame whose closure target is exactly the `converse` method on a `WorldAdapter`. Require one root extent and a nonempty domain trace in each worker. All other task conditions, task oracles, and cache controls remain unchanged.

## Source lock and gates

Before execution, lock this preregistration, v1.4 runner/analyzer, base task-panel inputs, Python/native source and build metadata, runtime data, WordNet corpus, and its existing digest-matched SQLite cache. Require ten unique workers, two per condition, stable parent and worker inputs, cache stability and metadata, no cache rebuild, exact schedule, and exact module/function/call-edge footprints across each condition's paired replicates. Any input drift censors the panel. Do not pool timing with v1.1/v1.2/v1.3.

## Claim boundary

This is a current-source replay of five authored conversation contracts. Python activation traces do not establish native Rust work, causal necessity, natural task prevalence, or uninstrumented service cost. Report outcomes and profiler-instrumented timings separately by task condition.
