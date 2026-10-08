# GenInfer scope provenance enforcement v1 results (2026-10-03)

## Outcome

The source-locked 36-worker probe passes its measurement-integrity gates. In
each of the three record states—valid, missing, and contradictory—all 12/12
workers report 2,400 direct-Term candidates, infer the exact oracle transform,
and acquire the target generator through the production shape-decode rules.
Median closure wall times are 9.98 ms, 9.91 ms, and 10.00 ms respectively.
There is no observed behavioral difference by record state.

This confirms the source-derived prediction: native GenInfer filters eligible
`ShapeSignature` nodes using the observation's `scope_id` value. It does not
consult the `FrameScope` record. `require_scope` causes a missing token to fail
closed, but a present token remains accepted even when no matching provenance
record exists or the record contradicts the frame/case/digest metadata. V1.3's
external provenance checks establish that its synthetic labels were aligned;
they do not establish runtime validation of those labels.

The operational capability is therefore exact-ID codebook filtering under a
caller-supplied scope token. Provenance generation/validation and scope
assignment correctness remain caller/evaluator responsibilities. The engine
cannot currently claim that an invalidly assigned token abstains. These results
are about the scope contract only; they do not change v1.3's exactness and cost
measurements for its valid synthetic assignments.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_SCOPE_PROVENANCE_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_scope_provenance_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_scope_provenance_v1_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_scope_provenance_v1_analysis_20261003.json)

Reproduce from the repository root:

```sh
python3 evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1.py --run
python3 evaluation/substrate_capability/analyze_substrate_geninfer_scope_provenance_v1.py
```
