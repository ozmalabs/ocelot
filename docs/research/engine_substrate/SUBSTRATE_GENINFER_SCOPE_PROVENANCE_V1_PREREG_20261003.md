# GenInfer scope provenance enforcement v1 preregistration (2026-10-03)

## Motivation and source hypothesis

The explicit-scope v1.3 measurement records `FrameScope` nodes and independently
checks their metadata, but native `load_parts_with_scope` appears to filter
`ShapeSignature` nodes by exact `scope_id` only. It does not appear to read a
`FrameScope` node. This panel tests that source-derived hypothesis through the
full seeded production rule path.

## Design

Run 36 isolated workers: 4 distinct linear maps × 3 scope-record states × 3
repeats. Each worker has one `ShapeSignature` and one matching `Observation`,
both carrying the same scope token, required-scope enabled, and the production
`agent -observed-> observation` edge. Scope-record states are: (1) a matching
`FrameScope` with the expected frame, case ID, and SHA-256 provenance; (2) no
`FrameScope`; (3) a `FrameScope` with the matching token but contradictory frame,
case ID, and digest. Thus the scope token and candidate part are held constant;
only the independent provenance record changes.

Before closure, evaluate the scoped GenInfer Term and record its candidate
count without graph mutation. Then run the full seeded closure and record exact
output, target-generator acquisition, status/receipt, work, time, and memory.
All files, native build metadata, seed closure, and protocol are source locked;
each worker is a fresh process.

## Predictions and interpretation

Source inspection predicts all three record states will be treated identically:
GenInfer reads matching `scope_id` attributes and does not consult the
`FrameScope` record. The evaluation gate is measurement integrity, not a
security/correctness claim: 36 locked workers, stable source, 2,400 diagnostic
candidates per worker, exact fixture oracle, and consistent target acquisition
across all three states. If missing or contradictory records abstain, that
would falsify the source hypothesis and trigger code-path review. If they
acquire, the result establishes that provenance is evaluator-side metadata and
is not enforced by the current native operation. No claim is made that a
`FrameScope` node itself is an unforgeable authority.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_scope_provenance_v1.py`
- Lock: `evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1_lock_20261003.json`
- Capture: `evaluation/reports/substrate_geninfer_scope_provenance_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_scope_provenance_v1_analysis_20261003.json`
