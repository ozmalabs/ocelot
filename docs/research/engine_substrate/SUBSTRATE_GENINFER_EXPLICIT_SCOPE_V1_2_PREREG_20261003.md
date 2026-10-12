# Explicit GenInfer codebook scope v1.2 preregistration (2026-10-03)

## Amendments from v1

The v1 source-locked run stopped before any timed row: the typed graph schema
rejected the fixture's custom `in_scope` edge (`ShapeSignature` Type-2
vocabulary error). The failed case and lock digest are preserved in
[the failure record](../../../evaluation/reports/substrate_geninfer_explicit_scope_v1_capture_failure_20261003.json).
No performance or capability result was produced by v1.

V1.1 removes the undeclared edge and uses the same representation the native
Term consumes: exact `scope_id` attributes on eligible bases and observations,
plus a `FrameScope` record carrying `scope_id`, task/frame identity, and a
SHA-256 digest of the locked synthetic base/goal assignment. The analyzer
checks that both attributes equal the referenced record ID and that the
provenance digest is present. This amendment changes only scope-provenance
materialization; task maps, candidate-count formulas, controls, and success
criteria are unchanged. The fresh lock binds all v1.1 sources.

## Amendment from v1.1

The v1.1 process completed all 45 positive workers, then stopped on the first
scope-mismatch control because that control case has no `mode` field and the
runner indexed it directly. The lock and failure record are preserved at
[the v1.1 capture failure](../../../evaluation/reports/substrate_geninfer_explicit_scope_v1_1_capture_failure_20261003.json).
No aggregate capture was written. V1.2 uses a safe default when classifying
control cases. The locked cases, evaluation logic, and gates are otherwise
unchanged.

## Purpose and implementation

The native `GenInfer` Term accepts an optional scope expression and a
required-scope expression. A supplied scope selects only exact-ID matching
parts before their signatures are parsed. If scope is required and missing,
the Term returns no candidate. If scope is omitted and not required, legacy
global search remains available. This scopes GenInfer's generator induction;
the other shape-recognition rungs still use their existing global behavior.

## Locked design

The positive panel crosses graph mode `{unscoped_global, explicit_global,
frame_scoped}` with K in `{1,2,4,8,16}` and three repeats (45 worker cases).
All modes have the same K frame bases, K observations, four unique relations
per frame, and four linear transforms. `unscoped_global` omits scope IDs and
leaves `gen_infer_scope_required` absent, invoking legacy all-parts search.
`explicit_global` gives every part/observation one shared scope ID;
`frame_scoped` assigns one exact scope ID per frame. Both explicit modes set
`gen_infer_scope_required=1`. Every worker uses a fresh process and full-seed
graph.

Before closure, a pure direct-Term diagnostic records `checked` per
observation and verifies graph node/edge counts do not change. At B=3,
unscoped/global-scope queries should each check K×2,400 candidates, for
K²×2,400 total. Frame-scoped queries should each check 2,400 and K queries
should check K×2,400 total. Production closure separately records exact
outputs, route/base attribution, minted generators, CPU/wall time, RSS delta,
and graph size.

The control panel has 24 workers: three repeats for each of four maps under
both (a) an observation whose scope ID does not match its only base part, and
(b) an observation with no scope ID while scope is required. Each control has
one actual base scope record and one base part; it must not mint the target
generator. Alternate routes and status receipts are retained.

## Gates

1. Exactly 69 source-locked workers run in distinct processes, with stable
   native binary/build manifest and unique case IDs.
2. All three positive modes are 100% exact; explicit-mode receipts name their
   own base and each part/observation scope ID agrees with its provenance
   record.
3. Direct candidate counts equal their unscoped/global/scoped formulas, and
   direct diagnostics leave graph node/edge counts unchanged.
4. Both required-scope controls return zero GenInfer candidate checks and
   mint no target generator.
5. Timing/resource fields are present; results are summarized by K without
   excluding cases. Performance is descriptive rather than a pass threshold.

An improvement claim requires exactness and lower measured closure cost under
frame-scoped conditions at K>1. The gate does not charge for discovering a
scope, updating membership, frame scheduling, or end-to-end data movement; a
later evaluation must do so. If scope provenance is unavailable or fails
validation, required mode must abstain rather than fall back to global search.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_2.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1_2.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_2_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_explicit_scope_v1_2_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_explicit_scope_v1_2_analysis_20261003.json`
