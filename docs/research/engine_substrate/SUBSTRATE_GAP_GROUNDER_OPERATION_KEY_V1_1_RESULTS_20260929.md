# Gap grounder operation-key comparison v1.1 results (2026-09-29)

## Corrected-verifier comparison

This repeats v1's 22-call/two-arm panel after native verifier registration was fixed and adds `domains/self_verification.py` to the source lock. The input lock matches before and after. Both arms retain the repeated-B and value-renamed-B suppression controls; A and B remain distinct observation and operation signatures.

| Arm / sequence | Second observation | Status | Outcome | Accepted | Axis delta |
|---|---|---|---|---:|---:|
| Faculty / isolated A | A | minted | composed | true | 2 |
| Faculty / isolated B | B | minted | built primitive | true | 2 |
| Faculty / A→B | B | recognized duplicate | composed | false | 0 |
| Faculty / B→A | A | recognized duplicate | primitive request | n/a | 0 |
| Faculty + operations / isolated A | A | minted | composed | true | 2 |
| Faculty + operations / isolated B | B | minted | built primitive | true | 2 |
| Faculty + operations / A→B | B | minted | built primitive | true | 1 |
| Faculty + operations / B→A | A | minted | composed | false | 1 |

The corrected current arm shows the practical cost of the faculty-key collision in A→B: the distinct spectral gap is coalesced with A, sent to composition, and rejected, while isolated B reaches a verified primitive builder. The candidate key preserves that B route in A→B. But the candidate does not make shared-graph behavior order-independent: after B, A reaches composition but is rejected, whereas isolated A is accepted. In that cross-order case, the host-measured probe still reports real pass and fake-twin failure, while native gate readback reports discrimination, no-regression, and grounding false. This is a state/context interference or readback-consistency signal; the panel does not identify its causal mechanism.

In both arms the B repeat and B-value second calls are recognized duplicates and return the accepted built-primitive route. Argument renaming is coalesced as intended for this pair. The candidate adds one axis when the second, distinct operation family appears; the faculty arm adds none. Wall time is not interpreted as a performance result.

## Interpretation and limits

The operation-multiset candidate improves one directional identity error and preserves the value-renamed B control, but it is not a complete key policy: its B→A composed route still fails in the shared graph. `verify_faculty` checks a generic classify/route/finalize pipeline claim; the primitive builder runs its own distinct verifier. Acceptance is therefore mechanism-specific, not automatically proof that the original `CapabilityGap` is solved. Future work must capture complete verifier claim/probe attrs, fresh-state and shared-state contrasts, and task-specific gap oracles. Include a same-operation/different-role-wiring negative before evaluating topology-aware identity. No global key migration is justified by this panel.

## Provenance

The panel used 14 fresh graphs and 22 calls through the real `extend_for_gap(..., verify=True)` path. The candidate arm appends the sorted predicate multiset in the harness only. The verifier source is now explicitly hashed in the source lock.

- Protocol: [`SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_1_PREREG_20260929.md`](SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_1_PREREG_20260929.md)
- Runner: [`gap_grounder_operation_key_v1_1.py`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1_1.py)
- Analyzer: [`analyze_gap_grounder_operation_key_v1_1.py`](../../../evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1_1.py)
- Source/fixture lock: [`gap_grounder_operation_key_v1_1_lock_20260929.json`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1_1_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/gap_grounder_operation_key_v1_1/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/gap_grounder_operation_key_v1_1/analysis.json)
