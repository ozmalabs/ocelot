# ARC-ls20 TRANSFORMATION RECOGNITION — results (rung 217000)

**Lead honestly:** this rung applies the substrate's GENUINE strength — the general
`TransformDecode` / `DimInfer` shape machinery (`runners/dsl/src/shape_decode.rs`,
`seeds/shape_decode_loop.json`) — to ls20's OWN core mechanic, on the SEEN Regions
from 216000's pixel eye. It builds the RECOGNITION half only: given a symbol Region
and its goal-form Region from the pixel eye, the substrate recognises the
transformation (rotate / reflect / recolour / translate) relating them, decoding the
`Transform{dim, delta, generator, k}` via the GENERAL decode — the per-instance
transform DISCOVERED by decode, never hardcoded. **PLANNING/EXECUTION (act in the
game to perform the transform and reach the goal) is the named NEXT rung, not
attempted here.** Prereg: `LS20_TRANSFORM_PREREG.md` @ **8790ac38c4f3984383e28b2dd61584030d79c8aa**
(committed alone, before the confirmatory run).

## Result — all four gates PASS (first + held-out confirmatory)

| run | pairs | overall recognised | overall label-correct (4 named) | refuse FP-rate |
|---|---|---|---|---|
| FIRST (seed 217000, chiral corpus) | 72 | **1.0000 [0.9493, 1.0000]** | **1.0000 [0.9450, 1.0000]** | **0.0000** (0/30) |
| **HELD-OUT (seed 217500, +symmetric +2-colour avatar)** | 112 | **0.9911 [0.9512, 0.9984]** | **0.9901 [0.9460, 0.9983]** | **0.0000** (0/110) |

Per-transform (held-out, the harder disjoint corpus):

| family | n | recognised | label-correct |
|---|---|---|---|
| translate | 55 | 0.9818 [0.9039, 0.9968] | 0.9818 |
| recolour  | 11 | 1.0000 | 1.0000 |
| rotate (rotation90 k∈1,2,3) | 21 | 1.0000 | 1.0000 |
| reflect (reflection_r/_c)   | 14 | 1.0000 | 1.0000 |
| identity (recognition sanity; label n/a) | 11 | 1.0000 | — |

- **G-recognise (headline):** overall recognised ≥ 0.95 → **PASS** (1.0000 first;
  0.9911 held-out). Every goal-form that IS a transform of the symbol is recognised
  as `recognized_transformed` with `covered_by == symbol`, on shapes SEEN through the
  pixel eye.
- **G-label:** label-correct (4 named families) ≥ 0.90 → **PASS** (1.0000 / 0.9901).
- **G-refuse (earned refusal):** FP-rate ≤ 0.05 → **PASS** (0.0000 / 0.0000). Every
  unrelated pair MINTS (refusal); no spurious `Transform`.
- **G-general (the bar):** **PASS** — source-audit clean (below) AND the IDENTICAL
  decode recognises all four families on a NON-ls20 corpus (F-pentomino, plain string
  colours, no palette, no render): rotate→rotation90, reflect→reflection_c,
  translate→shift, recolour→subst.

## Exactly how the transform is decoded (the GENERAL op, not a hack)

Per pair, seeing-not-oracle end to end (the oracle grid is never read downstream):

```
symbol grid --_render_screen--> RGB pixels
   --recover_grid_from_render (216000 pixel eye, pixels ONLY)--> SEEN grid
   --carve (4-conn per value)--> SEEN cells --cells_to_signature-->
        [["cell", r, c, "v<idx>"], ...]                       (the HELD symbol)
goal-form (KNOWN transform, SEEN the same way) --> the OBSERVATION
```

The decode is the IDENTICAL construction the shipped dim_infer instrument
(`scripts/dim_infer_args.py::point_S`) uses: hold the symbol as a `ShapeSignature`,
ingest the goal-form as a decoded `Observation` (`dim_types = ["pred", "coord:r",
"coord:c", "val"]` — the general schema), `native.run_rules()` to fixpoint.
`sd_transform_decode`/`sd_recognize_transformed` handle translate (a per-dimension
`shift` quantum delta on coord dims 1/2) and recolour (a categorical `subst` on the
value dim 3); `sd_infer_dimension`/`sd_recognize_dim` handle rotate/reflect via the
held `rotation90` / `reflection_r` / `reflection_c` `DimensionGenerator`s, minting a
`Transform{generator, k}`. **No ls20-specific transform table; the per-instance
transform is discovered by decode.** ls20's 2D is a DEGENERATE parameterisation of the
N-dim machinery (`coord:r`/`coord:c` are two of N coordinate slots), so the same op
serves any domain.

**VERDICT = INTEGER-NATIVE EXACT SET EQUALITY** (the "in-frame is integer" ARC path,
not a continuous comparator): the engine returns `recognized_transformed` ONLY when
the decoded transform explains EVERY cell relation exactly (a consistent functional
map per dimension); an inconsistent/partial residual MINTS instead. So
`recognized_transformed AND covered_by == symbol` IS the exact-reconstruction verdict,
performed by the engine — a comparison that can be false (the refuse control proves it
can). The `test_exact_equality_verdict_a_near_miss_is_refused` gate confirms a symbol
+ ONE extra cell is refused, not fuzzily matched.

**Source audit (G-general).** `test_decode_uses_the_general_machinery_no_ls20_hack_ast`
parses `decode_transform`: it drives the general `ShapeSignature`/`Observation`/
`run_rules` loop and NEVER names a generator or family to SELECT a transform (no
`rotation90`/`reflect`/`translate`/`ls20` string in the decode). `cells_to_signature`
CODE mentions no transform logic and no ls20 branching. The bridge is a mechanical
(row, col, colour)→relation translation; the recognition is the general decode's.

## Multi-colour grouping (the 216000 residual, closed for recognition)

The two-colour avatar (blue 9 + yellow 11) shatters into two Regions (216000). The
`region_signature` bridge GROUPS Region ids by cell-set union into ONE shape, and the
general decode then recognises all four families across the grouped colours
(rotate/reflect/translate/recolour all `recognised=True`, `colours=2`). The colour
is a CATEGORICAL sign (`"v9"`/`"v11"`), so a multi-colour recolour resolves as several
independent `subst` swaps rather than demanding one impossible uniform shift.

## Honest residuals + envelope

- **Symmetric shapes alias rotate↔reflect — a mathematical fact, not a miss.** A
  symmetric shape's rotation IS one of its reflections, so the *label* is
  non-unique there (`square`/`plus`/`I-bar`: 12/12 still RECOGNISED as a transform,
  only the family name aliases). Reported separately; rot/reflect label accuracy is
  scored on CHIRAL shapes only. `identity` aliases the same way (its trivial map is
  expressible by many generators — e.g. the engine labels it `cycle4`/`reflection_r`),
  so identity is a recognition sanity case, not scored for label.
- **One real held-out miss (named): symmetric-shape translate alignment.** The 2×2
  square translated by (5,1) was REFUSED (minted) — a highly symmetric shape admits
  multiple cell-correspondences and the decode's alignment picked one giving
  inconsistent per-dimension deltas. 1/112 pairs; inside the gate; the honest edge of
  the exact-equality alignment on symmetric shapes.
- **Exact-equality is brittle to sub-palette-step perception noise (envelope).**
  Because the verdict is all-or-nothing per pair, ANY single flipped cell in either
  perceived shape breaks the exact map: recognition holds at σ=8 render noise (1.000)
  and drops at σ=16 (0.000) — steeper than 216000's graceful IoU (which held to
  σ=16). FP stays 0 throughout (noise never fabricates a transform). The headline is
  the CLEAN render, matching 216000's clean-render G-parity headline.
- **Synthetic-mechanism, not live-ls20 benchmark (standing rule — report both).**
  These are ls20-SHAPED symbols on the real ls20 palette, SEEN through the pixel eye;
  ground truth is by construction. The LIVE ls20 transformation pairs need
  `ARC_API_KEY` (absent — the named frontier, exactly as 216000). The mechanism is
  proven general and exact; the benchmark value is unmeasured offline.

## Discipline

- **No Rust, no seed, no new Term.** The transforms are recognised by the EXISTING
  general `TransformDecode`/`DimInfer` + `sd_*` rules. The only change to a tracked
  file is `worlds/arc.py` (+`cells_to_signature`/`region_signature`/`SHAPE_DIM_TYPES`
  — the mechanical eye→shape bridge the ls20 plan named missing). New files:
  `scripts/arc_ls20_transform_measure.py`, `tests/test_arc_transform_recognition_migrated.py`.
- **Default-OFF byte-identical:** the bridge functions are called by no existing
  bench; `worlds/arc.py`'s existing paths are unchanged.
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` — UNCHANGED.** `term.rs`
  untouched; the whole `runners/dsl` tracked diff is EMPTY.
- **Oracle `bash scripts/rung7_vision_bench.sh`:** BEFORE **214 passed, 10 skipped,
  0 failed** == AFTER **214 passed, 10 skipped, 0 failed**.
- **`bash scripts/per_area_settlement_regression.sh` (34-file):** BEFORE **23 failed,
  277 passed, 5 skipped** == AFTER (same); the FAILING NODE-ID SET is IDENTICAL
  (`diff` empty). The 23 reds are the pre-existing environment-conditional
  conversation/reading cluster (topic_route / gap_awareness / elaboration /
  cortices_tick / composer_driver), independent of this change (this rung touches
  none of those files).
- **New test:** `tests/test_arc_transform_recognition_migrated.py` — 13/13 pass.
- `source_match = own`.

## The named NEXT rung

**PLANNING / EXECUTION.** The agent now RECOGNISES the transformation a symbol must
undergo; the next rung PLANS and ACTS in the game to PERFORM it (the transform
mechanic + the navigation route to the goal, `quanta_navigation`) and reach the WIN.
Plus the remaining higher-order object-reasoning operators (counting, containment/
topology, symmetry-detection as a first-class predicate) and the real anti-aliased
64×64 ls20 render (needs `ARC_API_KEY`).
