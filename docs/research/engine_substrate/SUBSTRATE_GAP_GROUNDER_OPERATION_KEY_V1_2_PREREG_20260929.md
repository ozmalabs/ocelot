# Gap grounder operation-key comparison v1.2 preregistration

This is a byte-for-byte protocol/design replication of v1.1 after the native extension was rebuilt. It repeats the same 22-call current-key versus faculty-plus-operation-multiset comparison, including exact B repeats, renamed-argument B, and both A/B orders. The locked input now hashes the current `_native.abi3.so` and its build record. No other fixture, arm, or metric changes are intended.

Keep the corrected-verifier interpretation from v1.1: record recognition, route, primitive/composition acceptance, and verifier gate inputs/readbacks separately. A generic pipeline claim is not evidence that an arbitrary gap was solved. Gate: 22 calls; all fixture/order assertions; pre/post source lock stable. Compare v1.1 outcomes with this current-binary replay and identify any binary-dependent change.

```sh
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1_2.py --lock
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1_2.py
python3 evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1_2.py
```
