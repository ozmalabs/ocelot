# Strict code-write adoption surface v1 — preregistration

Date: 2026-10-02

## Question

Does an adapter configured with `require_authenticated_code_examples=True` enforce the authentication gate across every identified production route into teach-by-example adoption, including the live conversation surface, direct `code_write_growth` calls, and the published-curriculum helper?

## Frozen panel

Four conditions run in three fresh processes each:

1. `valid_signature`: signed correct evidence through `WorldAdapter.converse`; expected to teach exactly one `code_write_construction` shape.
2. `tampered_signature`: same route with one HMAC signature character changed, then an internally consistent receipt is created over those tampered rows; expected receipt status is `accepted`, but expected code-write shape delta is zero.
3. `direct_legacy_call`: direct call to `teach_write_shape_from_example` on a strict adapter without provider evidence; expected refusal and zero code-write shape delta.
4. `curriculum_legacy_call`: call `code_curriculum.learn_functions_from_lesson` on a strict adapter using the locked bundled lesson fixture and no provider evidence; every attempted function must refuse and code-write shape delta must be zero.

The outcome counts only `ShapeSignature` nodes whose `kind` is `code_write_construction`, because ordinary conversation/reading may create other shape signatures. All attempts share the same authored square example family. The curriculum fixture is separately source-hashed.

## Interpretation limits

This checks the located production callsites that route through `teach_write_shape_from_example`; it does not make arbitrary Python calls to lower-level `teach()` impossible, nor does an opt-in policy affect non-strict adapters. It is not a process security boundary, provider-truth guarantee, key-isolation result, independent task-family transfer result, or general self-improvement result.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_surface_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adoption_surface_v1.py
```

The source/native/seed lock includes the adapter and adoption modules, the Rust/native runtime, all seed manifests, and the bundled curriculum fixture. The runner refuses to overwrite an existing lock or capture.
