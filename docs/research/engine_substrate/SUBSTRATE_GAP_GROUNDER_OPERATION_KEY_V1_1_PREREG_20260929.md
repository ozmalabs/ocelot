# Gap grounder operation-key comparison v1.1 preregistration

This is a frozen rerun of v1 after correcting `self_verify_gate` registration on `WorldAdapter`. It retains v1's fixtures, two key arms, seven sequences per arm, and 22 calls. The only experimental change is the corrected gate implementation; `domains/self_verification.py` is now explicitly included in the input lock. The purpose is to separate key-policy route effects from the earlier missing-verdict readback.

For each event, retain v1's status, key, outcome, route, accepted/verifier fields, and graph deltas. In addition, summarize verifier gate inputs/readbacks when present. A successful generic pipeline verification must not be described as proof that a spectral-value gap was filled: the current `verify_faculty` claim is the shared classify/route/finalize pipeline claim, not a fixture-specific B claim. Compare each shared second call to its isolated fixture's status/outcome and whether verification was executed and accepted.

Gate: all 22 calls complete, pre/post lock matches, and v1 identity controls pass. Report route/identity outcomes and verifier outcomes separately. This remains a synthetic two-operation-family panel with one argument-renamed B equivalent, not a natural task distribution or proof of task-specific correctness.

```sh
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1_1.py --lock
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1_1.py
python3 evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1_1.py
```
