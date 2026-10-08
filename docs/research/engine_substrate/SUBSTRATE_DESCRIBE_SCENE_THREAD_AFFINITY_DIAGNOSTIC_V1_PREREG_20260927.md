# Describe-scene thread-affinity diagnostic v1 preregistration (2026-09-27)

## Question

Under one source-locked runtime, does the exact `describe what you see` instruction produce the same selected parse, Goal lifecycle, graph-visible response, and public reply when a fresh adapter is used on the boot thread versus a plain child thread?

## Procedure

In one fresh process, construct two independent full-seed `WorldAdapter` instances with seed persistence disabled. Attach the same three-percept Scene to each. Call the same utterance with `speech_act="instruction"` and speaker `alice`: first synchronously on the constructing thread, then from one plain `threading.Thread` with no access-trace, scale-audit, conversation-lock wrapper, or concurrency barrier instrumentation. Join the child thread and record the same stage fields for each arm: inbound graph kind, comprehension dispatch, interpretation disposition, request-bound Goal count and lifecycle, discourse event kinds, outbound graph Messages, returned surface, and exceptions. Compare normalized semantics and record timings descriptively.

## Gates and limits

Require the full source lock to match before and after both arms; require two fresh adapters, no exceptions, and a joined child thread. Report a semantic mismatch without censoring the diagnostic: a mismatch is its measured outcome. One pair identifies a mechanism-specific discrepancy only; it does not estimate prevalence or prove a general thread-safety defect.

## Reproduction

Generate `evaluation/substrate_capability/describe_scene_thread_affinity_diagnostic_v1_lock_20260927.json` with the runner's `--lock` mode, then run it using `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`.
