# Self-verification WorldAdapter gate integration v1 results (2026-09-29)

## Finding

The earlier gap-grounder panels reported rejected composed outcomes, but their verifier was not actually evaluating its native gate on the `WorldAdapter` route. `_ensure_gate_rule` wrote a graph `Rule` with a singular `effect` attribute, while the active native rewrite registry remained without `self_verify_gate`; `Substrate.tick()` therefore had no registered gate to fire. A direct post-call snapshot showed measured probe inputs `real_pass=1`, `twin_pass=0`, and claim inputs `no_regression=1`, `grounded=1`, but no graph-written `g_discriminates`, `g_no_regression`, `g_grounded`, or `verdict`. The returned false fields were missing-attribute defaults, not a valid rejection verdict.

A controlled in-memory diagnostic normalized the graph rule to native `add_rule` form (`name`, `match`, `where`, plural `effects`): it fired in one native step and wrote all gates and `verdict=1`. The production bridge now registers that native rule idempotently when ensuring the graph Rule. No composition or verification policy changed.

## Locked replication

The preregistered panel ran three fresh positive cases through `extend_for_gap(..., verify=True)` and three fresh negative known-fake threshold claims through `verify_claim` on `WorldAdapter(seeds=())`. Results:

- **Positive pipeline:** 3/3 accepted; `real_pass=1`, `twin_pass=0`, `g_discriminates=1`, `g_no_regression=1`, `g_grounded=1`, `verdict=1`.
- **Known-fake mechanism:** 3/3 rejected; the mechanism failed its held-out discrimination cases, with no-regression and grounding gates true.
- **Registration/readback:** all six graphs contain exactly one graph `self_verify_gate` node and exactly one native registry entry. The returned accepted boolean matches the graph-written verdict in 6/6 cases.
- Pre-run and post-run source/fixture locks match.

This validates the adapter integration path and one positive/negative verifier fixture. It does not establish soundness of all claims, other adapters, lifecycle restart behavior, concurrent verification, or task capability beyond the authored pipeline.

## Artifacts

- Protocol: [`SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_PREREG_20260929.md`](SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_PREREG_20260929.md)
- Runner: [`self_verification_adapter_gate_v1.py`](../../../evaluation/substrate_capability/self_verification_adapter_gate_v1.py)
- Analyzer: [`analyze_self_verification_adapter_gate_v1.py`](../../../evaluation/substrate_capability/analyze_self_verification_adapter_gate_v1.py)
- Source/fixture lock: [`self_verification_adapter_gate_v1_lock_20260929.json`](../../../evaluation/substrate_capability/self_verification_adapter_gate_v1_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/self_verification_adapter_gate_v1/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/self_verification_adapter_gate_v1/analysis.json)
- Corrected implementation: [`self_verification.py`](../../../domains/self_verification.py)
