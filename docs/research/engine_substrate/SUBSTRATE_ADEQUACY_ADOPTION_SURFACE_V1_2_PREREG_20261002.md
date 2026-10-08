# Strict code-write adoption surface v1.2 — current-source replay

Date: 2026-10-02

This is a fresh current-source replay of the corrected four-condition adoption-surface panel. V1's pre-seed-load curriculum baseline was invalid for adoption accounting and is preserved as diagnostic. V1.1 moved that baseline after all fixture/seed setup and obtained the expected outcomes; v1.2 repeats the same protocol after the shared adoption-boundary documentation and implementation reached its current state.

## Frozen panel

Run each condition in three fresh processes:

1. `valid_signature`: strict `WorldAdapter.converse` with a correct request-bound provider signature; expect exactly one newly adopted `code_write_construction` shape.
2. `tampered_signature`: same, but alter one signature character before creating the receipt; expect an internally `accepted` receipt, strict-route refusal, and zero code-write shape delta.
3. `direct_legacy_call`: call `teach_write_shape_from_example` on a strict adapter without evidence; expect refusal and zero code-write shape delta.
4. `curriculum_legacy_call`: load the bundled full lesson seed set, record the baseline after setup, then call `code_curriculum.learn_functions_from_lesson` without evidence; expect every attempted function refused and zero code-write shape delta.

All cases use the authored square example family. Count only typed code-write construction signatures. Capture source, native, seed inventory, and curriculum fixture identities before, during, and after worker execution.

## Limits

The panel covers the audited example-teaching routes only. It does not gate `compose_write_shape_from_predication`, arbitrary direct calls to `domains.teach.teach`, or non-strict agents. Provider truthfulness, external key isolation, independent task-family transfer, and general self-improvement remain unproven.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_2.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1_2.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adoption_surface_v1_2.py
```
