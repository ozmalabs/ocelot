# Describe-scene plain concurrency diagnostic v1 preregistration (2026-09-27)

## Question

Do two identical live describe-scene calls started concurrently on one adapter complete their request-bound Goal lifecycles when using only the adapter's built-in serialization, with no measurement lock wrapper, access trace, scale audit, or event barrier inside a request?

## Procedure

In one fresh process, load full seeds once, attach the standard three-percept Scene, and start two Python threads behind a `threading.Barrier`. Each calls `converse("describe what you see", speech_act="instruction", speaker="alice")`. Join both threads; then recover each inbound Message by its exact text and `from="interlocutor"`, and read its selected parse, interpretation, linked Goals, discourse events, public reply, and outbound graph Messages. Capture full source inputs before and after the operation.

## Gates and limits

Require source stability, both threads joined, two exact inbound Messages, and no uncaught thread exception. Report each request's behavior without censoring differing outcomes. This is one fixture and one simultaneous-start schedule; it isolates ordinary concurrent calling from the added v2.3 measurement hooks but does not establish arbitrary concurrency safety.

## Reproduction

Generate `evaluation/substrate_capability/describe_scene_plain_concurrency_diagnostic_v1_lock_20260927.json` with the runner's `--lock` mode, then run with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`.
