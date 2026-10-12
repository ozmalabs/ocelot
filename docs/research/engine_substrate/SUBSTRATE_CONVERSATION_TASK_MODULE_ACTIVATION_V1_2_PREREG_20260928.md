# Conversation task module-activation panel v1.2

Date: 2026-09-28  
Status: preregistered current-source replay; execution has not started.

## Purpose

Repeat v1.1's five authored conversation task conditions on the current worktree. The post-capture source comparison identified a change to `domains/comprehend_text.py`; this run refreshes the source lock and tests whether the same task outcomes and module-activation traces hold. It is a new source snapshot, not a causal comparison to v1.1 because other runtime files may also have changed.

## Fixed design

Keep the v1.1 task stimuli, fixed worker order, two fresh processes per condition, profiled `WorldAdapter.converse` extent, independent task-oracle predicates, warmed WordNet database, and all existing gates unchanged. No route or oracle may be edited after locking. The five conditions are scene description, held self-knowledge answer, self-report action, unknown-word clarification, and concern authoring.

## Lock and external inputs

Before execution, lock this preregistration, v1.2 runner/analyzer, the base panel inputs, source/native extension/build artifacts, seeds/runtime data, the selected WordNet corpus, and its existing digest-matched SQLite cache. The WordNet database must already exist and have `(schema=1, digest=<corpus digest>)`; every worker verifies unchanged corpus/cache hashes and metadata. Any input drift censors the panel. No worker may build the index.

## Outcomes and interpretation

Require ten unique processes, exactly two per condition, one conversation extent and a nonempty domain trace per worker, stable worker and parent locks, all cache gates, and exact equality of module/function/call-edge key sets between replicates within each condition. Report each task-oracle outcome independently. Report Python call and time measures as profiler-instrumented descriptive data; do not infer native execution, causal module necessity, natural prevalence, or uninstrumented cost.

V1.1 remains preserved as the prior-source result. Compare v1.2 to it descriptively only, and do not attribute outcome or footprint changes to the single known `comprehend_text.py` edit. Archive raw capture and independent analysis unchanged after execution.
