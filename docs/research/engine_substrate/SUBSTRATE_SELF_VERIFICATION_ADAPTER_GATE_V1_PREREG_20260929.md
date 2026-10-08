# Self-verification WorldAdapter gate integration v1 preregistration

## Question

Does the self-verification gate execute and return its graph-written verdict on the normal `WorldAdapter` path, for both a real composed faculty and a known-fake mechanism?

## Frozen panel

Run three fresh `WorldAdapter(seeds=())` positive cases through `substrate_extension.extend_for_gap(..., verify=True)` using the existing three-stage classify/route/finalize gap. Run three fresh negative cases through `self_verification.verify_claim` using its held-out threshold fixture, with the submitted mechanism equal to the known-fake twin. For each case capture host-measured probe flags, graph-written `g_discriminates`, `g_no_regression`, `g_grounded`, and `verdict`, returned result, graph Rule node count, native rule registry count/name, and before/after source hashes.

Positive-panel expectations are acceptance with all three gates true; negative-panel expectations are rejection because the fake does not survive the discriminative examples. Also require exactly one graph/native `self_verify_gate` registration per substrate and require the graph `verdict` to equal the returned boolean. These are evaluator integration checks, not general proof that every domain verifier is sound.

## Provenance and execution

The lock includes the verifier, gap extension, composer/shape-decoder source and seeds, adapter/boot/graph code, native source/binary/build metadata, fixture definitions, and runner. Run the runner with `--lock`, then normally, followed by its analyzer. No production inputs are modified during measurement.

```sh
python3 evaluation/substrate_capability/self_verification_adapter_gate_v1.py --lock
python3 evaluation/substrate_capability/self_verification_adapter_gate_v1.py
python3 evaluation/substrate_capability/analyze_self_verification_adapter_gate_v1.py
```
