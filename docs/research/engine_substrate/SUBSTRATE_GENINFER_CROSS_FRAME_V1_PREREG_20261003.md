# GenInfer cross-frame dependency v1 preregistration (2026-10-03)

## Question

The v1.3 synthetic result showed cheaper GenInfer under exact frame scopes.
This paired production-path panel tests the boundary condition: what happens
when the basis needed to explain an observation is in its own frame, explicitly
included as a cross-frame dependency, or available only outside the supplied
scope? It measures whether scoping reduces work while preserving valid
explanations and makes the cost of a missing dependency visible.

## Design

Run 36 source-locked cases: three conditions (`local_basis`,
`cross_frame_in_scope`, `cross_frame_excluded`) × K `{2,4,8,16}` frame bases ×
three repeats. Every case has K bases with distinct frame-labeled predicate
signatures and one observation. The target map and generated observation are
identical between its global and scoped arms, which use separate fresh seeded
graphs in the same worker process. All graph frames are assigned distinct
scope tokens.

In `local_basis`, frame 0's basis explains its own transformed observation;
the observation scope is frame 0. In `cross_frame_in_scope`, frame 1's basis
explains an observation attributed to frame 0, and the observation's scope
explicitly includes frame 1's basis. In `cross_frame_excluded`, the same
frame-1 dependency is present globally but the observation scope is frame 0,
which contains only the unrelated frame-0 basis. The global arm omits scope and
uses the legacy all-parts search; the scoped arm requires the specified token.
All observations are connected through the production `observed` edge.

Record pre-closure candidate counts, production status, exact target map,
receipt base, closure work/time, and process HWM delta. Candidate-count
expectations are K×2,400 for the global arm and 2,400 for the scoped arm.
Exact acquisition is required for both arms when the needed basis is in scope;
when the needed basis is excluded, global acquisition is expected and scoped
non-acquisition is measured as a lost explanation, not scored as correctness.

## Gates and interpretation

- 36 unique locked cases in isolated workers, stable native/source manifests.
- Global and scoped candidate counts match their formulas; direct diagnostics
  do not mutate the graph.
- All generated fixtures satisfy the independent matrix oracle.
- Global closure acquires the exact target in all conditions.
- Scoped closure acquires the exact target in local/in-scope conditions and
  does not acquire it when the required basis is excluded.
- Receipts identify the intended base in positive acquisition conditions.

Cost reductions under local/in-scope conditions are descriptive; the primary
capability result is the work/accuracy trade-off under a missing cross-frame
basis. The panel uses authored integer-linear geometry on one host and does not
measure discovery of dependencies, natural task prevalence, or boundary
assignment accuracy. `FrameScope` records label synthetic assignment but are
not assumed to be runtime-validated; a separate probe has shown they are not.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_cross_frame_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_cross_frame_v1.py`
- Lock: `evaluation/substrate_capability/substrate_geninfer_cross_frame_v1_lock_20261003.json`
- Capture: `evaluation/reports/substrate_geninfer_cross_frame_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_cross_frame_v1_analysis_20261003.json`
