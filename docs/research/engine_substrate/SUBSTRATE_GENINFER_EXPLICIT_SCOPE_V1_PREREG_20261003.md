# Explicit GenInfer codebook scope v1 preregistration (2026-10-03)

## Purpose

Implement and measure an explicit exact-match codebook scope for the native
GenInfer Term, addressing the observed shared-codebook scan cost. Scope is
graph data: a `FrameScope` record carries a stable scope ID and provenance
digest; each eligible base `ShapeSignature` and its `Observation` carries the
same `scope_id` and an edge to that record. The Term accepts a scope expression
and a required-scope expression. A supplied scope selects only exact-ID
matching parts before signature parsing. If scope is required and absent, the
Term returns no candidate. If scope is omitted and not required, legacy
global search remains available.

The change scopes **GenInfer only**. Other recognition rungs still use their
existing global behavior. This gate therefore evaluates generator acquisition
and bounded-matrix candidate scanning, not a complete frame-local cognitive
pipeline or an autonomous frame-discovery system.

## Design

The positive panel crosses graph mode `{unscoped_global, explicit_global,
frame_scoped}` with K in `{1,2,4,8,16}` and three repeats (45 worker cases).
All modes have the same K frame bases, K observations, four unique relations
per frame, and four linear transforms. `unscoped_global` omits scope IDs and
leaves `gen_infer_scope_required` absent, invoking legacy all-parts search.
`explicit_global` gives every part/observation one shared provenance-linked
scope ID, exercising explicit selection while retaining all K parts.
`frame_scoped` assigns one exact scope ID per frame. Both explicit modes set
`gen_infer_scope_required=1`. Every worker uses a fresh process and full-seed
graph.

Before closure, a direct-Term diagnostic records `checked` per observation
without mutating graph node/edge counts. At B=3, global queries should each
check K×2,400 candidates, for K²×2,400 total. `frame_scoped` queries should
each check 2,400 and K queries should check K×2,400 total. Production closure
separately records exact per-frame outputs, route/base attribution, minted
generators, CPU/wall time, RSS delta, and graph size.

The control panel has 24 workers: three repeats for each of four maps under
both (a) an observation whose scope ID does not match its only base part, and
(b) an observation with no scope ID while scope is required. Each control has
one scope record and one base; it must not mint the target generator. These
cases exercise fail-closed scope selection. Controls do not assert that the
other global recognition rungs cannot find some alternate route; route and
status receipts are retained.

## Gates

1. Exactly 69 source-locked workers run in distinct processes, with stable
   native binary/build manifest and unique case IDs.
2. All three positive modes are 100% exact; every
   scoped receipt names its own base and every part/observation membership
   record agrees on scope ID and provenance digest.
3. Direct candidate counts equal their unscoped/global/scoped formulas, and direct
   diagnostics leave graph node/edge counts unchanged.
4. Both required-scope controls return zero GenInfer candidate checks and
   mint no target generator.
5. Timing/resource fields are present; results are summarized by K without
   excluding cases. Performance is descriptive rather than a pass threshold.

An improvement claim requires both exactness and lower measured closure cost
under scoped conditions at K>1. This gate does not charge for discovering a
scope, updating membership, frame scheduling, or end-to-end data movement; the
next evaluation must do so. If scope provenance is unavailable or fails
validation, the required mode must abstain rather than silently reverting to
global candidate search.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_explicit_scope_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_explicit_scope_v1_analysis_20261003.json`
