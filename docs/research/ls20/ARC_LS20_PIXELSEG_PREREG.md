# ARC-ls20 PIXEL-SEGMENTATION PARITY — pre-registration (rung 216000)

**Posture:** HONOUR the seeing-not-oracle commitment on ls20 for the FIRST time.
ls20 already runs graph-native, but the eye reads the SYMBOLIC INTEGER GRID
(`arc3_grid`) — a perfect oracle-*given* segmentation (connected-components on
exact integer colour indices). This rung makes the eye SEE the game: derive the
segmentation from the RENDERED PIXELS ALONE. The integer grid is demoted to a
SCORING ORACLE ONLY (exactly as VizDoom depth/labels, 161000/203000) — it builds
the golden trace and grades IoU; it is NEVER fed to the pixel perception path.

**The mechanism (registered):** a NEW opt-in `pixel_eye` path. The adapter feeds
the eye ONLY the 192×192 RGB render (`worlds/arc.py::_render_screen`). A mechanical
pixel→palette→grid step (`worlds/arc.py::recover_grid_from_render`, the exact
inverse of `_render_screen` — the analysis-by-synthesis render/quantize pair, cf.
StrokeRender/StrokeQuantize) (a) REGISTERS the cell lattice from the pixels
(recover `cell_px` + dims from coherent colour-boundary spacing, snapped to the
nearest exact divisor of the image size — no oracle H/W), (b) QUANTIZES each cell's
median pixel colour to the nearest of the 16 palette entries. The recovered SEEN
grid is fed into the UNCHANGED carve (`_perceive_regions` / native
`segment_and_track`). The carve/segmentation stays graph-native; the adapter only
does mechanical pixel I/O — no agent decision (source-audited).

**Seed block:** `SEED CLAIM 216000-216999: CLEAN -- no collision DETECTED.`
(`python3 scripts/seed_claim.py 216000 216999`, exit 0; verbatim below.)

**Engine:** NO Rust build. Canonical `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`**,
`term.rs` + whole `runners/dsl` diff EMPTY, `source_match` reported in RESULTS.

## The measurement (registered)

ORACLE carve (golden trace): cv2 connected-components (4-conn, per unique value —
the documented spec of the native `segment`) on the ORACLE integer grid.
PIXEL carve: `_render_screen(grid)` → RGB pixels → `recover_grid_from_render`
(pixels ONLY) → the SAME carve on the RECOVERED grid. The ONLY difference between
the two paths is oracle-grid vs recovered-from-pixels grid — isolating the
perception delta. Metric: per-Region position-set **IoU** (best match, geometry) +
**matched-Region fraction** (best IoU ≥ 0.5), pooled over frames, Wilson/normal CIs.

**Corpus:** the offline `arc3_env` faithful ls20-PROTOCOL stand-in (the private
ls20 rules need `ARC_API_KEY`, absent) — `navigate` (the ls20 NAVIGATION mechanic),
`switches`, `collect` — plus a synthetic ls20-SHAPED 64×64 sequence (real
scale/density: dark-grey field/walls=4, mid-grey rooms=3, a two-colour avatar
9+11, a value-11 countdown meter, a red goal). 38 frames, 246 oracle Regions in
the first measurement.

## The first honest measurement (baseline the gates are drawn from)

`_render_screen` is a **LOSSLESS block render** (solid palette blocks, no
anti-aliasing), so a correct pixel→grid recovery reproduces the oracle grid
EXACTLY → clean-render parity is near-1.0 **by construction**. The first
measurement confirms this and the pipeline's correctness:

| condition | mean per-Region IoU | matched-Region fraction | exact-grid frames |
|---|---|---|---|
| CLEAN render (headline) | **1.0000 [1.0000, 1.0000]** | **1.0000 [0.9846, 1.0000]** | 38/38 |
| + Gaussian noise σ=8 | 1.0000 | 1.0000 | 38/38 |
| + Gaussian noise σ=16 | 1.0000 | 1.0000 | 38/38 |
| + Gaussian noise σ=24 | 0.9680 | 0.9675 | 35/38 |
| + Gaussian noise σ=32 | 0.6820 | 0.6585 | 24/38 |
| + Gaussian noise σ=48 | 0.5785 | 0.5488 | 21/38 |

The clean-render number is near-trivially high (lossless render); its VALUE is the
source-audit (perception reads ONLY pixels, never the oracle) + the DEGRADATION
ENVELOPE. The real 64×64 anti-aliased browser render is unavailable offline; the
Gaussian-noise sweep stands in for render degradation and locates the palette-step
quantization limit (~51 grey levels between adjacent palette entries).

## The gates (registered BEFORE the confirmatory run)

- **G-parity (headline):** on the CLEAN `_render_screen`, mean per-Region IoU
  **≥ 0.99** AND matched-Region fraction **≥ 0.99**. (Passes by construction on a
  lossless render — proves the pixel path reproduces the oracle carve exactly while
  reading ONLY pixels. The lossless-render caveat is stated, not hidden.)
- **G-robust (the gate with teeth — CAN fail):** under Gaussian pixel noise
  **σ=16** on the render (moderate degradation), mean per-Region IoU **≥ 0.95** AND
  matched-Region fraction **≥ 0.95**, on a HELD-OUT rng seed + extended episode.
  This gate FAILS by σ=32 in the first measurement, so σ=16 is a real test.
- **G-no-oracle (load-bearing):** AST + runtime audit — the pixel perception path
  derives the value grid ONLY from render pixels; `arc3_grid` is read ONLY on the
  default (oracle) path and by the scorer. Runtime proof: with a POISONED
  `arc3_grid` but a correct render, the pixel path recovers the TRUE grid.
- **G-discipline:** integer-native; default-OFF byte-identical (`pixel_eye` off =
  the standing oracle path, unchanged); canonical `.so` md5 stays `793ce09e…`
  (no Rust); `term.rs` + `runners/dsl` diff EMPTY; oracle `rung7_vision_bench.sh`
  BEFORE==AFTER; `per_area_settlement_regression.sh` (34-file) BEFORE==AFTER.

## Discriminator

- **CONFIRM:** clean-render parity ≥ 0.99/0.99 AND σ=16 held-out parity ≥ 0.95/0.95;
  the whole existing ls20 stack then runs on SEEING with no other change; source
  audit shows the eye samples ONLY pixels; discipline gates all hold.
- **DEGRADE (a valid landing — name the blocker):** parity below a gate — report
  the straight number and WHERE it fails (palette quantization? cell registration?
  colour bleed?). A measured gap is the frontier, not a failure to hide.
- **FALSIFY:** the pixel path cannot be added without reading the oracle grid, or it
  disturbs the default oracle path / the oracle bench / the regression. Report the
  coupling with evidence; do NOT rescue by leaking `arc3_grid` into perception.

This rung is PERCEPTION parity only. The higher-order shape reasoning (the
symbol-transformation mechanic via TransformDecode/DimInfer; counting / containment
/ symmetry; the two-colour-avatar shatter) is the NEXT gap — named, not attempted.

## `check_claim` (verbatim)

```
SEED CLAIM 216000-216999: CLEAN -- no collision DETECTED.
  Scope: 918 files with seed sinks; 619 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
