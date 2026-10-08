# Current describe-scene path diagnostic v1 preregistration (2026-09-27)

## Question

For the exact instruction `describe what you see` on the attached three-percept Scene fixture, which observable stage fails when the current adapter returns an unknown-command response: graph speech-act classification, comprehension dispatch, native interpretation, Goal production, or reply release?

## Procedure and gates

Run one fresh process from the current locked runtime. Load the full seed set with persistence disabled, attach the same grey static / yellow meter / blue mover scene, call `WorldAdapter.converse` once with `speech_act="instruction"` and speaker `alice`, and record the result plus graph readbacks from the exact inbound Message. Capture source inputs before and after the turn. Require equality with the preregistered lock. Record `sak_kind`, `comp_*` parse/dispatch fields, interpretation attributes, all Goals linked by `comprehends`, discourse events linked to the same state/Goal, outbound replies and their provenance. This is a diagnostic, not an intervention or an evaluation of general language capability.

## Reproduction

Create `evaluation/substrate_capability/describe_scene_current_path_diagnostic_v1_lock_20260927.json` from the runner's `--lock` output, then run the runner with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. A run with changed source hashes is censored.
