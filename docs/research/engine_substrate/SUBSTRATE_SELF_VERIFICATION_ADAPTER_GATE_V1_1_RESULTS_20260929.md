# Self-verification WorldAdapter gate integration v1.1 results (2026-09-29)

The preregistered six-case replay repeated the positive/negative gate panel against the rebuilt current native extension (10,327,104 bytes; SHA-256 `54a6481b26ec28a240fe8f33360a93b8e0e7e621b396a81d36e69dae0291ed1c`). It passes all v1 gates: three composed-pipeline positives accepted; three known-fake threshold claims rejected; returned decisions match graph-written verdicts; each case graph and native registry contain exactly one `self_verify_gate`; source/input hashes match before and after.

This matches v1's discrete outcomes under its earlier 130,368,728-byte binary. It supports repeatability across these two engine artifacts and this verifier fixture, not general soundness or other domain claims. Wall time is not compared.

- Protocol: [`SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_1_PREREG_20260929.md`](SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_1_PREREG_20260929.md)
- Runner: [`self_verification_adapter_gate_v1_1.py`](../../../evaluation/substrate_capability/self_verification_adapter_gate_v1_1.py)
- Analyzer: [`analyze_self_verification_adapter_gate_v1_1.py`](../../../evaluation/substrate_capability/analyze_self_verification_adapter_gate_v1_1.py)
- Source/fixture lock: [`self_verification_adapter_gate_v1_1_lock_20260929.json`](../../../evaluation/substrate_capability/self_verification_adapter_gate_v1_1_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/self_verification_adapter_gate_v1_1/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/self_verification_adapter_gate_v1_1/analysis.json)
