# Provider-authenticated WorldAdapter route v1.1 — amendment

Date: 2026-10-02

V1's first six-worker capture is retained as diagnostic at `evaluation/reports/substrate_adequacy_adapter_path_v1_diagnostic_raw_20261002.json`. It showed that the public reply correctly distinguished valid from tampered signatures, but the preregistered raw count of *all* `ShapeSignature` nodes was not an adoption measure: ordinary conversation processing minted unrelated signatures in both arms (18 total additions in the valid arm and 17 in the tampered arm).

V1.1 changes the adoption outcome to the identity delta of nodes whose `ShapeSignature.kind` is exactly `code_write_construction`. All other cases, source/native/seed locking, process count, order, and authored oracle remain unchanged. The v1.1 panel is a fresh six-process replay; it must show exactly one new code-write construction per valid signed case and zero per tampered-signature case. The tampered case must still have an internally accepted receipt so the panel isolates the provider-authentication check.

This correction was prompted by observed v1 behavior and is disclosed before the v1.1 rerun. Scope remains one authored scalar function, one host, and a process-local test key. It does not establish signer truthfulness, key isolation, alternate-route enforcement, or general learning capability.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adapter_path_v1_1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adapter_path_v1_1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adapter_path_v1_1.py
```
