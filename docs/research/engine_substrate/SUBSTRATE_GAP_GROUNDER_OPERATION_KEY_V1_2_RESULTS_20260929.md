# Gap grounder operation-key comparison v1.2 results (2026-09-29)

## Current native-binary replication

The v1.2 preregistered replay completed 22/22 calls under the current native extension (`_native.abi3.so`, 10,327,104 bytes, SHA-256 `54a6481b26ec28a240fe8f33360a93b8e0e7e621b396a81d36e69dae0291ed1c`). Pre/post source-lock equality holds. It reproduces every discrete v1.1 result: the faculty-key arm merges A/B and misroutes B in A→B; the faculty-plus-operation arm sends B through its accepted primitive builder in A→B and suppresses B/B-value duplicates; A after B still composes and fails verification under the candidate. The six-case verifier integration replay also passes against this current extension: 3/3 positive pipeline cases and 3/3 known-fake rejections, with native/graph gate registration and verdict parity.

The previous v1.1 captures locked a larger, earlier native extension (130,368,728 bytes; SHA-256 `0f95ca6d...`). Their discrete outcomes match the current-binary replication exactly, but their timings and binary provenance apply only to that earlier artifact. No timing claim is made from either small panel.

## Interpretation

Current-binary evidence strengthens the identity finding: the measured directional false coalescence and its correction persist across the two captured native binaries. It also confirms the unresolved reverse-order case. A key based only on faculty and operation heads cannot ensure shared-graph isolation or reliable task acceptance. The untested same-operation/different-role-wiring case remains a required negative control. This is still one synthetic gap family pair; do not generalize prevalence or change production key policy globally.

## Artifacts

- Protocol: [`SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_2_PREREG_20260929.md`](SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_2_PREREG_20260929.md)
- Runner: [`gap_grounder_operation_key_v1_2.py`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1_2.py)
- Analyzer: [`analyze_gap_grounder_operation_key_v1_2.py`](../../../evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1_2.py)
- Source/fixture lock: [`gap_grounder_operation_key_v1_2_lock_20260929.json`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1_2_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/gap_grounder_operation_key_v1_2/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/gap_grounder_operation_key_v1_2/analysis.json)
- Current-binary verifier replication: [`self-verification gate results v1.1`](SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_1_RESULTS_20260929.md), [capture](../../../evaluation/reports/self_verification_adapter_gate_v1_1/capture.json), and [analysis](../../../evaluation/reports/self_verification_adapter_gate_v1_1/analysis.json)
