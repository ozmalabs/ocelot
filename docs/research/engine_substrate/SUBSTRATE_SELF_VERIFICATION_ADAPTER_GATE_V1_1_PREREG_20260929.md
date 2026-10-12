# Self-verification WorldAdapter gate integration v1.1 preregistration

Replicate the v1 six-case positive/negative adapter gate panel after the native extension rebuild. Keep the three positive composed-pipeline cases and three known-fake claims unchanged. The input lock includes the current native binary and its build record; other fixtures and metrics are unchanged. Require one graph gate and one native registry gate per case, graph verdict/API parity, acceptance for positive cases, and rejection for fake cases.

```sh
python3 evaluation/substrate_capability/self_verification_adapter_gate_v1_1.py --lock
python3 evaluation/substrate_capability/self_verification_adapter_gate_v1_1.py
python3 evaluation/substrate_capability/analyze_self_verification_adapter_gate_v1_1.py
```
