# ARC-ls20 TRANSFORMATION RECOGNITION — pre-registration (rung 217000)

> **Status: PRE-REGISTRATION, committed ALONE before the confirmatory run.** This
> fixes the gates, thresholds, corpus construction and the decode path BEFORE the
> results doc lands. `VISION_PROTOCOL.md` is untouched. Thresholds are set from a
> FIRST honest exploratory measurement (reported verbatim in §5), per the
> standing "power the gate before the endgame" rule.

## 0. Headline (lead honestly)

This rung applies the substrate's GENUINE strength — the general
`TransformDecode` / `DimInfer` shape machinery (`runners/dsl/src/shape_decode.rs`,
driven by the `seeds/shape_decode_loop.json` `sd_*` rules) — to ls20's OWN core
mechanic, on the SEEN Regions from 216000's pixel eye. ls20: *"a symbol must go
through various transformations (rotate / reflect / recolour / translate) to reach
the goal."* This builds the RECOGNITION half: given a symbol Region and its
goal-form Region from the pixel eye, the substrate recognises the transformation
relating them — decoding the `Transform{dim, delta, generator, k}` — via the
GENERAL decode, with the per-instance transform DISCOVERED by decode, never
hardcoded. PLANNING/EXECUTION (act in the game to perform the transform and reach
the goal) is the named NEXT rung, not attempted here.

## 1. The decode path (fixed here; no ls20-specific transform logic)

Per pair (symbol → goal-form), all seeing, no oracle read downstream:

1. `worlds/arc.py::_render_screen(symbol grid)` → RGB pixels.
2. `worlds/arc.py::recover_grid_from_render(pixels)` → SEEN grid (216000 pixel eye;
   pixels only).
3. carve (4-connected per value) → SEEN symbol cells; `cells_to_signature` →
   `[["cell", r, c, "v<idx>"], ...]` — row/col the INTEGER lattice, colour a
   CATEGORICAL sign. (The `region_signature` bridge does the same from real
   `Region` nodes; multi-colour symbols group by cell-set union.)
4. The GENERAL decode: hold the symbol signature as a `ShapeSignature`, ingest the
   goal-form as a decoded `Observation`, `run_rules()` to fixpoint — the IDENTICAL
   construction the shipped dim_infer instrument (`scripts/dim_infer_args.py::point_S`)
   uses. `sd_transform_decode` / `sd_recognize_transformed` (translate/recolour) and
   `sd_infer_dimension` / `sd_recognize_dim` (rotate/reflect via the rotation90 /
   reflection_r / reflection_c generators) run in ONE fixpoint.

**VERDICT = INTEGER-NATIVE EXACT SET EQUALITY (the in-frame-is-integer path, not a
continuous comparator).** The engine returns `recognized_transformed` ONLY when the
decoded transform explains EVERY cell relation exactly (a consistent functional map
per dimension); an inconsistent/partial residual MINTS instead (refusal). So
`recognized_transformed AND covered_by == the symbol` IS the exact-reconstruction
verdict, performed by the engine — a comparison that can be false. The family
(rotate/reflect/recolour/translate) is read off the decoded `Transform`.

**NO Rust, NO seed, NO new Term.** The transforms are recognised by the EXISTING
general machinery. The only new code is the mechanical eye→shape bridge
(`cells_to_signature` / `region_signature` in `worlds/arc.py`) and this measurement
harness (`scripts/arc_ls20_transform_measure.py`). Default-OFF byte-identical (the
bridge is called by no existing bench). Canonical `.so` md5 stays `793ce09e…`;
`term.rs` and the whole `runners/dsl` diff EMPTY.

## 2. Corpus (ground truth by construction)

ls20-SHAPED symbols on the REAL ls20 palette (`worlds/arc.py::_PALETTE`), SEEN
through the pixel eye. Chiral polyominoes (F/L/S/Y/P/G, colours 9/11/8/14/12/6) —
rotate-vs-reflect is only DISTINGUISHABLE on chiral shapes. Held-out corpus adds
the symmetric symbols (translate/recolour only — `_is_chiral` gates out their
rot/reflect) and a genuine TWO-COLOUR avatar (blue 9 + yellow 11 — the 216000
"shatters into two Regions" residual, grouped by `region_signature`). Each
goal-form is a KNOWN transform of the symbol (identity / translate(dr,dc) /
recolour(swap) / rotate90(k∈1,2,3) / reflect(row|col)). All rng seeds inside
217000–217999.

**HONEST SCOPE (standing rule — synthetic-proven ≠ benchmark value, report both):**
these are ls20-shaped synthetic pairs SEEN through the pixel eye; the LIVE ls20
transformation pairs need `ARC_API_KEY` (absent — the named frontier, exactly as
216000).

## 3. The gates (fixed NOW)

- **G-recognise (headline):** on the clean-render corpus (N ≥ 72 first; held-out
  N ≥ 72, disjoint), overall **recognised fraction ≥ 0.95** (a goal-form that IS a
  transform of the symbol is recognised as `recognized_transformed` with
  `covered_by == symbol`). Per-transform (translate / recolour / rotate / reflect)
  accuracy reported, with which it gets and misses.
- **G-label:** over the FOUR NAMED families, overall **label-correct fraction ≥
  0.90** (the decoded `Transform`'s family matches the applied family; scored on
  chiral shapes for rot/reflect). `identity` is a recognition sanity case, NOT
  scored for label (its trivial map is expressible by many generators — the same
  aliasing fact as symmetric shapes).
- **G-refuse (control — earned refusal):** genuinely UNRELATED pairs (symbol X vs a
  DIFFERENT symbol Y) are REJECTED (minted / no `Transform`), **false-positive rate
  ≤ 0.05**. A recogniser that cannot refuse is not a recogniser.
- **G-general (the bar):** the recognition uses the GENERAL
  `TransformDecode`/`DimInfer` — (a) source-audit clean: NO ls20-special-cased
  transform logic (AST/grep audit of the harness + bridge), the decode construction
  is byte-identical to `dim_infer_args.point_S`; AND (b) the SAME op decodes the
  four families on a NON-ls20 corpus (the F-pentomino with plain string colours, no
  palette, no render). Dimension-arbitrary (ls20's 2D is a degenerate
  parameterisation of the N-dim machinery).
- **G-discipline:** integer-native exact set-equality verdict; default-OFF
  byte-identical; canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED
  (no Rust); `term.rs` + whole `runners/dsl` diff EMPTY; oracle
  `bash scripts/rung7_vision_bench.sh` BEFORE==AFTER; 34-file
  `bash scripts/per_area_settlement_regression.sh` failing-node-id SET BEFORE==AFTER;
  `source_match` reported.

## 4. Seed block

**217000–217999** (claimed §5). Harness seeds: 217000 (first), 217500 (held-out),
+1/+2/+3 offsets for the refuse / symmetric / multicolour / robustness passes — all
inside the block.

## 5. First honest measurement (the threshold basis) + seed claim

First exploratory run (`scripts/arc_ls20_transform_measure.py --tag first`, seed
217000, N=72 clean-render pairs):

```
overall recognised    : 1.0000 [0.9493, 1.0000]
overall label-correct : 1.0000 [0.9450, 1.0000]   (4 named families)
per family: translate 30/30 · recolour 6/6 · rotate 18/18 · reflect 12/12
G-refuse: n=30 false-positives=0 FP-rate=0.0000 [0.0000, 0.1135]
outside-ls20 same op: rotate/reflect/recolour/translate all recognised
```

The clean-render, integer-native, exact-equality path measures at the ceiling on
synthetic seen shapes; the gates (≥0.95 / ≥0.90 / ≤0.05) are set BELOW it so a
held-out corpus with real perception/alignment misses can still pass while the
gate retains teeth. Honest noise envelope (exact-equality is all-or-nothing per
pair): recognition holds at σ=8, drops at σ=16 (steeper than 216000's graceful
IoU — any single flipped cell breaks the exact map).

Seed claim (`python scripts/seed_claim.py 217000 217999`), verbatim:

```
SEED CLAIM 217000-217999: CLEAN -- no collision DETECTED.
  Scope: 919 files with seed sinks; 624 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 6. What this rung is NOT

Not planning/execution (act in the game) — the named NEXT rung. Not a claim of
live-ls20 benchmark value (needs `ARC_API_KEY`). Not a new transform algorithm —
it APPLIES the general decode. Not a continuous comparator (ARC is a clean discrete
integer lattice; the verdict is exact set equality).
