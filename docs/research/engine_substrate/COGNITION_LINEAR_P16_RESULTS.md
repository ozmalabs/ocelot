# Linear P16 results

## Registered v2 result

The corrected v2 held-out draw completed and passed its registered conformance gate. The raw scorecard contains 800 rows: 200 paired worlds for each of two families, with one native primitive-search and one graph-expression record per world. All rows completed, all paired world and access hashes matched, all 800 emitted actions had independently verified external receipts, and the analyzer found no integrity failures. All 500 fault-injection controls passed (100 each for missing, stale and tampered expressions, wrapper/native mismatch, and unauthorized emission). All five analyzer tampering probes detected their mutations.

The descriptive goal outcomes were 400/400 for native depth-1 primitive search and 25/400 for graph-expression execution: permutation 200/200 versus 9/200, and state-dependent tool 200/200 versus 16/200. This gap does not alter the registered conformance pass. It shows that the approved expression mechanism often emitted a valid action that did not solve this sampled one-step goal; this is not evidence of comparative strategy quality or autonomous operator learning. Graph-expression work was 11 compositions per task (2,200 per family), versus one native search expansion per task (200 per family). Mean recorded task time summed 0.1058 seconds for expression execution and 5.0557 seconds for primitive search across both families; these per-arm task timings exclude separate claims about boot and do not establish practical latency benefit. Expression-arm graph snapshots totaled 310,800 nodes per family and approximately 21.3 MB serialized bytes; search totaled 48,622 nodes per family and no serialized-graph measure.

The v1 held-out attempt is invalid for inference because its preregistration contains a 61-character build-receipt hash. The analyzer rejected the recorded runtime against that malformed contract before producing a report. Its raw bytes remain archived and hashed; no v1 outcomes are reported or reanalyzed. V2 uses a corrected standalone freeze, a new runner/analyzer version, and a disjoint seed offset of 2,000,000.

The supported P16 boundary is exact native artifact attestation, graph-selected expression execution, bounded native frontier search, and verified simulator receipts in finite one-step four-element worlds. Multi-step strategy quality, autonomous process discovery, broader tool learning, physical actions and any capability level remain unestablished. P17 may now evaluate whether acquired qualia changes predictions and behavior, but must preserve these limits.

Raw and analyzer files remain outside git:

- `/tmp/cognition-linear-p16-v2-heldout.json` — SHA-256 `d7255637f3b01948df0c3e0aaa4503b1bb7a93ca056edf5f48429f1da7bee2d2`
- `/tmp/cognition-linear-p16-v2-heldout-analysis.json` — SHA-256 `5449a0ce7a3d440faf585ec1c53c9f0d79e79811dd51932b741a0da9475263ee`
- invalid v1 raw `/tmp/cognition-linear-p16-heldout.json` — SHA-256 `02cebd99658af2fd539efde2b08a5845280b49a9385d373969defdd81e80b641`; no analyzer report was produced.

The v2 runtime attested `ATTESTED`: wrapper `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`, loaded extension `b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1`, build receipt `6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1`, source fingerprint `73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54`. The v2 source-bundle, runner, analyzer, profile, world, dependency-closure and engine-source digests are frozen in [`COGNITION_LINEAR_P16_V2_PREREG.md`](COGNITION_LINEAR_P16_V2_PREREG.md).

## Verification

The clean-artifact v2 development allocation passed with 32/32 paired rows, 500/500 controls and 5/5 analyzer tamper probes. The full focused P16/profile/Track-I regression bundle passed 130 tests before the runner versioning correction; v2's self-check and development scorecards were then independently analyzed as passing. The held-out analyzer reports `integrity_status: PASS` and `registered_conformance_status: PASS`.
