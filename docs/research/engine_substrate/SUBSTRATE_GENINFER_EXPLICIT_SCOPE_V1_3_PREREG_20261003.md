# Explicit GenInfer codebook scope v1.3 preregistration (2026-10-03)

## Amendments and preserved failures

V1 stopped before timed rows because the typed graph schema rejected its
custom `in_scope` edge. Its lock and failure record remain preserved at
[evaluation/reports/substrate_geninfer_explicit_scope_v1_capture_failure_20261003.json](../../../evaluation/reports/substrate_geninfer_explicit_scope_v1_capture_failure_20261003.json).

V1.1 removed that edge and represented membership with exact `scope_id`
attributes plus a `FrameScope` provenance record. Its runner then failed on a
control case missing a `mode` field. V1.2 fixed the control classifier and
captured 69 cases. Post-capture review found that v1.2 created observations but
omitted the required `agent -observed-> observation` edge. The seed's production
rules select observations through that edge, so its `run_rules()` calls did not
evaluate the panel. V1.2's raw capture and failed analysis are retained, but
its zero-acquisition result is a harness failure, not a runtime compatibility
finding. V1.3 adds the production edge for positive and control observations;
all other case definitions and gates are carried forward.

## Purpose and implementation

The native `GenInfer` Term accepts an optional scope expression and a
required-scope expression. A supplied scope selects only exact-ID matching
parts before their signatures are parsed. If scope is required and missing,
the Term returns no candidate. If scope is omitted and not required, legacy
global search remains available. The evaluation compares that operation under
three modes, and exercises it through the seeded production rule loop.

## Locked design

The positive panel crosses graph mode `{unscoped_global, explicit_global,
frame_scoped}` with K in `{1,2,4,8,16}` and three repeats (45 worker cases).
All modes have the same K frame bases, K observations, four unique relations
per frame, and four linear transforms. `unscoped_global` omits scope IDs and
leaves `gen_infer_scope_required` absent, invoking legacy all-parts search.
`explicit_global` gives every part/observation one shared scope ID;
`frame_scoped` assigns one exact scope ID per frame. Both explicit modes set
`gen_infer_scope_required=1`. Every worker uses a fresh process and full-seed
graph, and each observation is linked from the agent by the `observed` edge
used by the production shape-decode rules.

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
4. Both required-scope controls return zero GenInfer candidate checks and mint
   no target generator.
5. Timing/resource fields are present; results are summarized by K without
   excluding cases. Performance is descriptive rather than a pass threshold.

An improvement claim requires exactness and lower measured closure cost under
frame-scoped conditions at K>1. The gate does not charge for discovering a
scope, updating membership, frame scheduling, or end-to-end data movement; a
later evaluation must do so. If scope provenance is unavailable or fails
validation, required mode must abstain rather than fall back to global search.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_explicit_scope_v1_3.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_explicit_scope_v1_3_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_explicit_scope_v1_3_analysis_20261003.json`
