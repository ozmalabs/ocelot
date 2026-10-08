# Gap grounder same-head role-wiring v1.3 preregistration

## Question

Can the faculty-plus-operation-head key distinguish two same-faculty observations with identical relation-head multisets but reversed task direction and role wiring? Does the real primitive builder's verification gate detect that direction change?

## Frozen fixtures

- B requests the forward spectral log-magnitude operation: signal → spectrum, represented by `spectral_value(signal,magnitude)` and `log_scale(magnitude,value)`.
- C requests signal recovery from a magnitude spectrum, with distinct role wiring and I/O names but the same relation heads: `spectral_value(magnitude_spectrum,recovered_signal)` and `log_scale(recovered_signal,magnitude_spectrum)`.

Both have faculty `shared_family`; both use the selected test frequencies and sample count. The fixture's task labels and I/O declarations differ. Run two key arms: the unchanged faculty key and faculty plus sorted relation-head multiset. The candidate is expected to collide here by construction; the experiment measures whether that collision affects recognition, artifacts, and verifier outcomes.

## Sequences

In each arm, use fresh graphs for isolated B, isolated C, repeat B, B→C, and C→B. This is 5 fresh graphs and 8 calls per arm, 10 graphs and 16 calls total. Exercise `extend_for_gap(..., verify=True)` and capture full gap attrs, observation signatures/status, concern key, returned primitive name/operation/term tree, verifier gates, axes, requests, held primitives, codebook epoch, and native steps. Lock all relevant Python/Rust/native sources, binary/build manifest, fixtures, and protocol before and after.

## Primary analysis and limits

Compare each isolated fixture with the corresponding second observation in both orders. Record whether C's verifier passes and whether its returned term tree is identical to B's. A passing forward-tone peak test is not a valid recovery oracle by itself: use the declared I/O direction as the task contract and report that distinction explicitly. Do not change production key policy. This is one synthetic adversarial pair and does not estimate natural prevalence.

```sh
python3 evaluation/substrate_capability/gap_grounder_role_wiring_v1_3.py --lock
python3 evaluation/substrate_capability/gap_grounder_role_wiring_v1_3.py
python3 evaluation/substrate_capability/analyze_gap_grounder_role_wiring_v1_3.py
```
