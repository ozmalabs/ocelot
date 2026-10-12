# Conversation task module-activation panel v1

Date: 2026-09-28  
Status: preregistered before capture.

## Question

Which Python domain functions are called during five selected conversation routes, and how repeatable is the call-path footprint across fresh processes under the same source snapshot?

## Frozen workload

Reuse the five current panel conditions and their existing task contracts unchanged: scene description, held self-knowledge answer, self-report action, unknown-word clarification, and concern authoring. Run two fresh processes per condition in the existing fixed schedule. Each worker uses the current full-seed boot path and the exact `task_ok` contract in `scripts/substrate_live_conversation_capability_panel_v1.py`.

## Instrumentation

- Install `sys.setprofile` around the worker, but aggregate only calls whose dynamic extent is inside its single `substrate.world_adapter.WorldAdapter.converse()` call.
- Record domain module/function call counts and directed caller→callee counts. Keep host-to-domain entry edges separate.
- Do not collect line events, inspect task outputs during profiling, or change rule/seed/handler behavior.
- Record the unprofiled task wall/CPU fields already returned by the workload runner only as profiler-instrumented observations. No trace-overhead claim is made without a paired off arm.

## Source and replication gates

- Lock the base panel inputs, this protocol, the trace driver, and analyzer before workers. Base inputs include the runtime/seed closure, all Python files under `scripts/`, `data/slabs/`, native extension/build provenance, Python/platform, and commit.
- Each worker's base inputs must match the lock before and after execution; the parent repeats the lock after the complete schedule.
- Require 10 distinct PIDs, exactly two workers per condition, one captured conversation extent per worker, and a nonempty domain call trace.
- Independently re-evaluate each task contract from captured reply and graph-linked route/Goal/message records. Report task success by condition; do not pool distinct task types as a general capability score.
- Compare call-path footprints within each condition across its two workers. Report intersection, union, and exact equality; do not interpret a missing call as proof a module is unnecessary.

## Claim boundary

This is a selected, authored conversation-route panel. It measures Python call activity in five task implementations on one current source snapshot. It does not estimate task prevalence, establish cross-modal generality, prove causal necessity, trace Rust/native internal operations, or measure profiler overhead. The held-self-knowledge task's inherited oracle is intentionally a limited reply-form contract, not a semantic fact oracle.
