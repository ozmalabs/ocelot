# P14 held-out results

**Protocol:** [`COGNITION_LINEAR_P14_PREREG.md`](COGNITION_LINEAR_P14_PREREG.md), corrected revision 1  
**Run:** 2026-10-22  
**Scope:** finite S4 commutator parity and a one-call graph-authored process macro. The registered criteria are classified below without extending their scope.

## Results

| Criterion | Result | Evidence |
|---|---|---|
| Authored operator | **PASS** | 200/200 authored macro tasks solved versus 0/200 for the held commutator under the same one-operator-call cap; +100 percentage points against the registered ≥20-point criterion. |
| Development qualification | **PASS** | 8/8 development tasks solved versus 0/8 for the parent; invariant checks matched 8/8; work was 32/32 units; candidate remained `awaiting_human`. |
| Checked laws | **PASS** | 100/100 supported structural commutator-even claims became checked with one binding proof reference each. |
| False finite-sample laws | **PASS** | 100/100 commutator-odd claims with validated native counterexamples were rejected; zero false proofs. |
| Tampering safety | **PASS** | 50/50 corrupted proof-reference controls stayed blocked; 50/50 altered-criteria approvals stayed awaiting human review. |
| Integrity | **PASS** | Zero missing/duplicate pairs, world/access hash mismatches, input-audit failures, invariant failures, allocation errors, provenance mismatches, work-accounting errors or external actions. |

The macro runs `compose(commutator(a,b), commutator(a,b))` as one native application. This is a bounded task with a one-call limit, so the comparator cannot apply the held commutator twice. The authored arm used 4 declared work units per task (two commutator constructions, one composition and one application); the held arm used 1 application. The result is a one-call task advantage at higher per-task algebra work, not a compute-efficiency claim. The candidate was not promoted, and the draw did not issue human approval.

Mean profile boot was 0.2178 seconds for the held arm and 0.2075 seconds for the authored arm. The recorded mean graph snapshots were 1,906 nodes/452,546 serialized bytes and 1,947 nodes/468,040 bytes, respectively. These are end-of-trial graph snapshots from the accumulating paired adapters, not isolated per-task memory deltas. Law-panel and tampering-panel boots averaged 0.2044 and 0.2135 seconds. External actions were zero in every record.

Agent inputs included the held permutation generators, initial state, ordinary task goal and, in the treatment arm, the graph-authored expression. They excluded answer labels, hidden truth labels and task-specific strategies. Proof records bind the checked statement/assumption digests, exact process parameters, checker rule, family/model digests and epochs. The runner records these input channels and proof bindings, but does not reduce evidence exposure to a single scalar; exposure-count criterion is therefore `NOT_MEASURED`.

Human comparison is `UNAVAILABLE_PROTOCOL_NOT_MATCHED`. The panel establishes neither open-ended operator discovery nor broad theorem proving, transfer beyond this finite S4 family, external-action authorization, or any capability level. The corrected preregistration explicitly superseded its first freeze before a held-out run; the registered draw was executed once under revision 1.

## Provenance and raw records

The implementation commit was `10a320a086cf61e726d7166055c84155748334b0`; corrected preregistration commit was `d288dae2`; the runner's execution commit was `db0fee28c2959fd9136190018f663597b144b0c3`. Component hashes matched corrected revision 1: source bundle `f5e9d0bb159dd94f939eeb9c884e89eaad894d4c2fd1a7f21bf7a3c721ccaed8`, runner `2afa5db61b1c41f24a20f14db43b62176d1bdb2a923ec1a2d4dd6444f524bc85`, analyzer `c9bfbbc7afd6e2fddc88388377caf6c7a1d34826af2d0d8b6f611e1236146027`, profile `022a07d8e7748e19144a0c1bef1e09a6394c209def933173fcf08f430f7d759e`, world adapter `3eabdfd1f28edca08f64800eab0a37b8d2911ece810160b9d4d62c05f5557985`, engine source `e0b2298a4495d16eb2661dd14ecfdc70ed3960d85646481f85c53fe4ea8cca6d`, engine binary `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`, and protocol bundle `6ba31746b644bc2898699372bc2307bbfb54f74dc590ecfac1e061207f8c832c`.

Raw scorecard `/tmp/linear-p14-heldout.json` SHA-256: `5cb1fb1601a2a09c4c9024188db430993beb26ceb1cfd35a1410647d0c5381c7`. Analysis `/tmp/linear-p14-heldout-analysis.json` SHA-256: `a566e5723f203735439a50fd1fa549060d3b5f5af177c877db07cee1c553d197`. Both raw files remain outside git.
