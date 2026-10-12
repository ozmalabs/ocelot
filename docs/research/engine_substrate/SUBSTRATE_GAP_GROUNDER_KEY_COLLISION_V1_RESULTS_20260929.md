# Gap grounder key collision v1 results (2026-09-29)

## Question

Does the fixed `name_hint` used by `extend_for_gap` distinguish different gaps from the same faculty, and does a prior gap change how the next one is handled?

## Frozen design and provenance

The preregistered panel used two structurally different `CapabilityGap` fixtures with `faculty="shared_family"`. Fixture A is a three-step classify/route/mark-handled chain. Fixture B requests a `spectral_value` primitive for log-magnitude extraction. Six fresh-graph sequences covered isolated A and B, exact repeats of each, and both A→B and B→A. The runner exercised `domains.substrate_extension.extend_for_gap(..., verify=True)`, including its real grounding and verification path. All ten calls derive the same concern key, `gap_shared_family`.

The runner's pre-run and post-run hashes match the frozen lock. The capture contains all six sequences and ten calls. The raw capture, analyzer output, protocol, runner and lock are retained below. The measured workload is one authored pair of fixtures; call wall time is not used to make a scaling claim.

## Results

| Sequence/call | Observation status | Grounder outcome | Verification accepted | Axis delta | Primitive-request delta |
|---|---|---|---:|---:|---:|
| Isolated A | minted | composed | false | 2 | 0 |
| Isolated B | minted | rejected primitive | false | 2 | 0 |
| A then A (second) | recognized duplicate | composed | false | 0 | 0 |
| B then B (second) | recognized duplicate | rejected primitive | false | 0 | 0 |
| A then B (second) | recognized duplicate | composed | false | 0 | 0 |
| B then A (second) | recognized duplicate | primitive request | not returned | 0 | 1 |

The exact-repeat controls preserve their first-call routing outcome and suppress a second axis. The cross-fixture cases do not: B alone is rejected as a primitive, but B after A is routed through the composition pipeline; A alone is composed, but A after B becomes a primitive request. In both cases the second observation is marked `recognized_duplicate`, despite its distinct structural signature. Thus this fixture demonstrates order-dependent route interference under the faculty-derived key. It does not show that the returned composition is useful: both isolated A and shared A→B report verification rejection, and the shared B→A branch creates a primitive request.

## Interpretation and limits

The collision is operationally consequential in this pair because the deduplication key determines whether the later gap enters the held-composition path or primitive-request path. The contemporaneous verifier readback was invalid: a follow-up audit found that the graph gate had not been registered with the WorldAdapter native rule engine. The corrected gate now accepts the actual composed A fixture in 3/3 fresh source-locked repetitions; the corrected-verifier operation-key rerun is now available ([v1.1 results](SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_1_RESULTS_20260929.md)). This report therefore establishes key collision and downstream route perturbation, not a production defect across all faculty families or a natural collision rate ([verifier integration results](SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_RESULTS_20260929.md)). Existing domain callers also use `name_hint` as a vocabulary/faculty identity in several paths, so replacing every hint with a structural digest would require compatibility evidence.

The next experiment should compare the existing faculty key with a candidate composite identity (faculty plus a canonicalized gap-operation signature) on representative grounder families. It must keep exact-repeat, value-varied equivalent gaps, structurally distinct same-faculty gaps, and order-balanced shared-graph controls. Score recognition identity separately from outcome, verify acceptance, created requests/axes, persistence, and downstream reuse. Retain the current key as an arm. Do not change production key policy until the panel shows both repeat suppression and reduced false coalescence without harmful splitting of equivalent gaps.

## Artifacts

- Protocol: [`SUBSTRATE_GAP_GROUNDER_KEY_COLLISION_V1_PREREG_20260929.md`](SUBSTRATE_GAP_GROUNDER_KEY_COLLISION_V1_PREREG_20260929.md)
- Runner: [`gap_grounder_key_collision_v1.py`](../../../evaluation/substrate_capability/gap_grounder_key_collision_v1.py)
- Analyzer: [`analyze_gap_grounder_key_collision_v1.py`](../../../evaluation/substrate_capability/analyze_gap_grounder_key_collision_v1.py)
- Source/fixture lock: [`gap_grounder_key_collision_v1_lock_20260929.json`](../../../evaluation/substrate_capability/gap_grounder_key_collision_v1_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/gap_grounder_key_collision_v1/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/gap_grounder_key_collision_v1/analysis.json)
