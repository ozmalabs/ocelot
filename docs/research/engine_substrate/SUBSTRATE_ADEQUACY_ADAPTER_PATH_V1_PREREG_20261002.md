# Provider-authenticated WorldAdapter route v1 — preregistration

Date: 2026-10-02

## Question

Does the opt-in strict `WorldAdapter.converse` code-example path adopt an eligible example when a trusted provider signs request-bound adequacy evidence, and refuse an otherwise accepted receipt when the provider signature is corrupted?

## Frozen design

- Two cases: a correct signed square example, and the same evidence with one signature nibble changed before receipt creation.
- Three fresh worker processes per case.
- Each worker boots the standard core seeds, creates an adapter with strict authentication enabled and a test-only provider key, builds an adequacy request bound to the candidate and exact Term, adjudicates the receipt, then calls the public `converse` method with separate evidence.
- The tampered case must still receive an `accepted` core receipt. This isolates provider authentication from receipt consistency.
- Positive acceptance requires an `accepted` receipt, authenticated provider result, a user-visible learned-shape response, and at least one added `ShapeSignature`.
- Tamper rejection requires an `accepted` core receipt, no learned-shape response, and zero added `ShapeSignature` nodes.
- Checkpoint policy and secret non-serialization are covered by the prior targeted smoke check; this panel tests live conversation routing only.

## Scope and limitations

This is a single authored scalar task and a process-local test key. It checks the live adapter path, not production key isolation, signer truthfulness, alternate/direct teaching entrypoints, natural task prevalence, or general learning capability. The function example itself is fixed and the test oracle is authored. No deployment security claim follows.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adapter_path_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adapter_path_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adapter_path_v1.py
```

The runner writes a source/native-locked capture and refuses to overwrite an existing lock or capture.
