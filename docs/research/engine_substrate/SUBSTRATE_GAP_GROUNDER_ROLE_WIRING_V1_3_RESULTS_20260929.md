# Gap grounder same-head role-wiring v1.3 results (2026-09-29)

## Results

The 16-call, 10-fresh-graph source-locked panel met its fixture and order gates. B and C have different full observation signatures and different declared I/O contracts, but identical relation-head multisets. Consequently, both the current faculty key and the faculty-plus-operation-head candidate produce the same key for B and C.

| Candidate arm sequence | Second status | Outcome | Primitive name | Accepted | Axis delta | HeldPrimitive delta |
|---|---|---|---|---:|---:|---:|
| B→B | recognized duplicate | built primitive | `spectral_value` | true | 0 | 0 |
| B→C | recognized duplicate | built primitive | `recover_signal` | true | 0 | 1 |
| C→B | recognized duplicate | built primitive | `spectral_value` | true | 0 | 1 |

Isolated B and C each mint two axes and install one accepted primitive. For both key arms and both orders, the second different fixture is labelled `recognized_duplicate` yet installs a distinct `HeldPrimitive`. Only the exact B repeat suppresses both the extra axis and held primitive. The key is therefore an axis identity, not a complete observation/capability deduplication contract.

The returned `term_tree` for isolated C (`recover_signal`, input `magnitude_spectrum`, output `recovered_signal`) is identical to B's forward `spectral_value` term (`signal` → `spectrum`). Both receive `accepted=true`. The verifier tests whether a synthesized pure tone's energy peaks at selected bins; it does not test the declared input/output direction or recovery behavior. Magnitude-only spectra also discard phase, so they do not uniquely determine a general signal. Thus C's acceptance demonstrates a validation-scope gap: the primitive passes its configured frequency-bin checks while the artifact does not implement the requested I/O contract.

## Interpretation and limit

This is a constructed same-head role-wiring counterexample, not a prevalence estimate. It shows that the operation-head key cannot separate role wiring, but the more consequential failure is that the current extension path still creates and accepts a differently named artifact after axis-level duplicate recognition. A stronger verifier must bind the tested mechanism to the gap's declared inputs, outputs, and semantics, and should refuse the magnitude-only inverse request. A same-head distinction key alone would not correct the builder's current forward-term reuse or verifier's scope.

## Provenance

The run used current `extend_for_gap(..., verify=True)` with the current native binary. The full lock hashes verifier and extension sources, native engine and build record, fixture definitions, runner, and protocol. Pre-run and post-run lock values match.

- Protocol: [`SUBSTRATE_GAP_GROUNDER_ROLE_WIRING_V1_3_PREREG_20260929.md`](SUBSTRATE_GAP_GROUNDER_ROLE_WIRING_V1_3_PREREG_20260929.md)
- Runner: [`gap_grounder_role_wiring_v1_3.py`](../../../evaluation/substrate_capability/gap_grounder_role_wiring_v1_3.py)
- Analyzer: [`analyze_gap_grounder_role_wiring_v1_3.py`](../../../evaluation/substrate_capability/analyze_gap_grounder_role_wiring_v1_3.py)
- Source/fixture lock: [`gap_grounder_role_wiring_v1_3_lock_20260929.json`](../../../evaluation/substrate_capability/gap_grounder_role_wiring_v1_3_lock_20260929.json)
- Raw capture: [`capture.json`](../../../evaluation/reports/gap_grounder_role_wiring_v1_3/capture.json)
- Analysis: [`analysis.json`](../../../evaluation/reports/gap_grounder_role_wiring_v1_3/analysis.json)

## Follow-up: independent I/O oracle and bounded correction

The preregistered v1.4 direct-DFT oracle confirms the v1.3 diagnosis on the frozen fixtures: 6/6 valid forward outputs match, while 6/6 inverse-labeled artifacts reuse and pass as the forward term. The v1.5 source-locked correction panel adds requested-primitive and declared-port checks: it preserves 6/6 forward acceptances and returns an honest `recover_signal` primitive request in 6/6 magnitude-only inverse cases. The independent ambiguity witness passes in both panels. These linked results establish correction of this specific counterexample, not general verifier soundness ([v1.4 results](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_4_RESULTS_20260929.md), [v1.5 results](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_5_RESULTS_20260929.md)).
