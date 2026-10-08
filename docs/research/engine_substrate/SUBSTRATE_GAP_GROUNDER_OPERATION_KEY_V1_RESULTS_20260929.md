# Gap grounder operation-key comparison v1 results (2026-09-29)

## Result

The frozen 22-call paired panel met its identity/route gate. The faculty-only arm reproduced the prior order effect: A→B routed B through composition (verification rejected), while B→A routed A to a primitive request. The candidate faculty-plus-sorted-operation-multiset arm separated the two fixtures in both orders. In A→B, B was freshly minted and followed its isolated `rejected_primitive` route; in B→A, A was freshly minted and followed its isolated `composed` route. Candidate exact B repeats and B→B-value both marked the second observation `recognized_duplicate`, with zero second axis delta. The B-value variant has different observation arguments/signature but the same operation heads.

| Key arm | Sequence second observation | Status | Outcome | Axis delta | Verification |
|---|---|---|---:|---:|---|
| Faculty | A→B | recognized_duplicate | composed | 0 | rejected |
| Faculty | B→A | recognized_duplicate | primitive_request | 0 | n/a |
| Faculty | B→B | recognized_duplicate | rejected_primitive | 0 | rejected |
| Faculty | B→B-value | recognized_duplicate | rejected_primitive | 0 | rejected |
| Faculty + operation multiset | A→B | minted | rejected_primitive | 1 | rejected |
| Faculty + operation multiset | B→A | minted | composed | 1 | rejected |
| Faculty + operation multiset | B→B | recognized_duplicate | rejected_primitive | 0 | rejected |
| Faculty + operation multiset | B→B-value | recognized_duplicate | rejected_primitive | 0 | rejected |

For both arms, isolated A, B and B-value retained their own first-call outcome. All three isolated fixture calls minted axes, and the then-current verifier read back false for every composed outcome. **Correction from the follow-up verifier integration audit:** those false readbacks were not valid rejections. The graph gate node had not been registered with the WorldAdapter's native rule engine, leaving its verdict fields unset. After adding the native registration bridge, the same composed A fixture passes the verifier's three gates in 3/3 fresh locked replications; see [the verifier integration result](SUBSTRATE_SELF_VERIFICATION_ADAPTER_GATE_V1_RESULTS_20260929.md). The key-policy panel therefore establishes route/identity behavior only; acceptance comparisons across its key arms must be rerun under the corrected verifier before the key candidate can be evaluated for capability value. It costs one extra axis for a first observation of each operation family in a shared graph; this panel did not measure a meaningful timing or memory difference.

## Limits and interpretation

This is a controlled caller-level comparison, not a production key change. Its candidate identity retains the multiset of observation relation heads and ignores arguments and role wiring. It shows value-name invariance for one B/B-value pair and separation for one different operation family; it does not handle same-operation structures with different topology, estimate natural prevalence, or justify global migration. A same-operation, different-role-wiring negative and held-out operation family remain required. The verifier registration defect has been fixed and independently measured, but this key-policy comparison has not yet been rerun against that corrected verifier.

## Provenance and artifacts

The runner made 14 fresh graphs and 22 calls through `domains.substrate_extension.extend_for_gap(..., verify=True)`. The pre-run and post-run input locks match. The current arm calls the original function unchanged. The candidate arm wraps the existing `reflective_faculty.induce_concern` call only in the harness and appends an escaped, sorted relation-head multiset to `name_hint`.

- Protocol: [`SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_PREREG_20260929.md`](SUBSTRATE_GAP_GROUNDER_OPERATION_KEY_V1_PREREG_20260929.md)
- Runner: [`gap_grounder_operation_key_v1.py`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1.py)
- Analyzer: [`analyze_gap_grounder_operation_key_v1.py`](../../../evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1.py)
- Source/fixture lock: [`gap_grounder_operation_key_v1_lock_20260929.json`](../../../evaluation/substrate_capability/gap_grounder_operation_key_v1_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/gap_grounder_operation_key_v1/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/gap_grounder_operation_key_v1/analysis.json)
