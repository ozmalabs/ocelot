# Aperture-Grain Thought-Manifold Tube (block 349000)

## What this closes

Block 348 built the train of thought as a trajectory through a ThoughtManifold, steered by
a **tube** — but on the plain is-a seed the tube could only be a *concept-region* (a set of
admissible concept names). The richer, confirmed-literal form — the set-point being an
`observer_aperture` whose **grain** sets the tube WIDTH (vague/coarse grain = wide tube =
freeform; sharp/fine grain = narrow tube = focus) — was inert there, because
`analogy_search.concept_signature` returned only lexical/attr/relational tuples with no
dynamical/qualia axes for grain to coarsen. Block 349 seeds those axes and upgrades the
tube to the real aperture-grain form, demonstrated for real.

## The seed (what makes grain bite) — teacher-free, additive

1. Install the qualia codebook `seeds/shape_vocabulary.json` + `seeds/qualia_space.json`
   (pure node data — 16 QualiaDimension incl. `dynamical:valence` (field:state, quantum
   1.0) and `dynamical:commitment` (field:identity_field, quantum 0.25), 34
   DimensionEdgeRole, 1 QualiaSchema; `edges:[]`, `productions:[]` so loading fires no new
   rules). This makes `_qualia_schema` return `have=True` with a non-empty `field_axes`;
   without it `_dynamical_relations` returns `[]` and grain is a no-op.
2. Set the CAN field attrs `state` (→ dynamical:valence) and `identity_field` (→
   dynamical:commitment) on the demo concepts, giving each distinct dynamical coordinates
   grain can split or collapse (the same attr-write path `tests/test_qualia_space_migrated`
   proves yields real dynamical tuples).

## The upgrade (additive) — a set-point-observer path

`domains/regulated_train_of_thought.py` gains a `setpoint_observer` path alongside the
block-348 `tube_region` path (selected by which is passed; concept-region is byte-identical
when `setpoint_observer` is None):
- **tube** = the aperture-projected signature the set-point admits
  (`concept_signature(set_point, observer=setpoint_observer)`);
- **deviation** = `len(trajectory_signature − admitted)` — the DISCRETE-QUANTA integer
  count of the trajectory's aperture-projected signature tuples outside the admitted set
  (one tuple = one quantum, grain being the quantum; reuses the same `_round_to_vocab`
  lattice — no floats);
- the block-347 attention_width control law consumes this integer unchanged; the
  aperture-aware frontier steers toward the tube.

## Result (measured, pure graph, teacher-free, discrete quanta)

| claim | result |
|---|---|
| G1 multi-axis signature + grain bites (coarse admits 4 tuples, fine 6) | **PASS** |
| G2 fine-grain set-point → narrow tube → informative deviation → focus | **PASS** |
| G3 coarse-grain set-point → wide tube → low deviation → freeform roam | **PASS** |
| G4 sharpen grain mid-run → deviation jumps → width steps up | **PASS** |
| G5 teacher-free (ask-spy 0 on the held path) | **PASS** |
| G6 backward-compat: concept-region `tube_region` path == block-348 | **PASS** |

The set-point's **grain** genuinely sets the tube width: a fine grain keeps the
trajectory's coordinates distinct (informative deviation, the loop narrows to focus); a
coarse grain collapses them into the admitted buckets (low deviation, the loop roams
freeform); sharpening mid-run splits previously-admitted tuples apart, jumps the deviation,
and widens attention. This is the vague↔sharp dial working for real, because grain now
coarsens a genuinely multi-axis `concept_signature`. The set-point being *literally* an
`observer_aperture` (not an analogue) was the confirmed-literal finding — consistent with
`attention_width` being aperture's *sibling* and `ThoughtManifold` being `FutureManifold`'s
*sibling*.

## Honest record: G4 test bug, fixed honestly

The first run FAILED G4. The failure was a **test-logic bug, not a mechanism failure**: the
draft G4 compared two hand-computed width formulas that were byte-identical
(`min(MAX, 1+1)` on both branches), so `width_steps_up` could never be true; and it started
from a width already pinned at the max shell, leaving no room to observe a step-up. The
underlying widen-on-deviation law was already demonstrated (block-348 C3, and G2/G3 here).
The fix runs the actual controller from a headroom start (`width0=0`): under a coarse
set-point the width stays low; under the sharpened set-point the deviation crosses the
widen threshold and the width steps up `0→1→2`. The assertion was corrected to test the
real controller; the substrate was not changed to make it pass.

## Deferred status — superseded by later landed blocks

The original deferred list was accurate at block 349. It is now historical: block 350 landed the optional global-workspace broadcast/competition path, and block 351 landed the gated dimension-minting path. See [`GLOBAL_WORKSPACE_RESULTS.md`](GLOBAL_WORKSPACE_RESULTS.md), [`GATED_MINTING_RESULTS.md`](GATED_MINTING_RESULTS.md), and the capability-suite result documents. These later local results remain bounded mechanism evidence, not production or general-agency claims.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files + `conceptualizer.py` untouched (audit green).
- Teacher-free (no LLM); no model/venv/`/applications`.
- Block 346/347/348 experiments still pass (backward-compat).
- Committed block-349 only, add-by-name.

## Artifacts

- `domains/regulated_train_of_thought.py` (M) — the additive `setpoint_observer` /
  aperture-grain tube path (`_admitted_signature`, `_aperture_deviation`).
- `scripts/gen_rung3_aperture_grain_tube.py` — the experiment (G1–G6, teacher-call spy),
  which seeds the qualia coords teacher-free.
