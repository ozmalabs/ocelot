# SALIENCE-DRIVEN FOVEATION — PRE-REGISTRATION (block 159000-159999)

Written and COMMITTED before the E1M1 (H2) run (VISION_PROTOCOL.md §3).

## SEED CLAIM 159000-159999: CLEAN

Verbatim `check_claim` (`python3 scripts/seed_claim.py 159000 159999`):

```
SEED CLAIM 159000-159999: CLEAN -- no collision DETECTED.
  Scope: 859 files with seed sinks; 581 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The block reserves the VizDoom seed + RNG base only (no seed manifest consumed).

## THE PRINCIPLE — foveation = supergraph-optimal compute allocation

158000 proved depth-from-motion (FOE + radial consistency) + independent-mover
isolation WORK when the flow carries signal (recovered real Doom depth vs the
VizDoom depth buffer, Spearman up to +0.40), but they NULL on the coarse
down=2/L=4 flow because it is quantization/noise-limited (mean div ≈ 0 vs mean
|curl| = 0.44) AND full-resolution flow EVERYWHERE is O(N²) (~3× over the
real-time budget). THE FIX: don't resolve everything — resolve the flow FINELY
only where it is SALIENT, coarse elsewhere. Spend the resolution budget where the
(super)graph values it most (the salient / independently-moving region), not
uniformly. Foveation is the perception instance of "value graph-wide, allocate
where worth-most."

## THE MECHANISM (reuse-heavy)

1. COARSE global flow (down=2) over the whole frame — the existing block-SAD
   `vector_field`.
2. SALIENCE on it: estimate the FOE (158000), radial-decompose, take the
   TANGENTIAL residual FIELD = the per-cell "surprise after self-motion is
   cancelled" (157000's efference→residual→salience, made SPATIAL and
   depth-INDEPENDENT so the peak lands on the INDEPENDENT MOVER, not on the
   highest-magnitude near/parallax background).
3. FOVEATE: at the top-salience region(s) RE-COMPUTE the flow at FINE resolution
   (down=1) in a LOCAL WINDOW only.
4. Run 158000's depth-from-motion + mover isolation on the FINE-flow window.

REUSED (158000): `estimate_foe`, `radial_decompose`, `depth_from_motion`,
`flag_movers`, `otsu_cutoff`, `expansion_gate`, `spearman`, `auc_fast`,
`iou_masks`, `_flow_field`, `_downsample_depth`, `FLOOR`, `R_MIN`. REUSED
(157000): `dominant_mode_gain` (single-vector residual, the raw-vs-residual
control). REUSED (E1M1 adapter): `capture_e1m1` / walk / seed / depth+labels
buffers, `downsample_grey`, `downsample_labels`, `quantize`. ADDED (mechanical
numpy GLUE only): `salience_field` (tangential-residual spatial salience),
`_connected_components` + `select_fovea` (argmax / top-K window selection),
`fine_flow_window` (the existing block-matcher on a CROP).

## HYPOTHESES, STATISTICS, DECISION RULES

### H1 — SYNTHETIC (ideal oracle, able to fail). A forward-translation scene (radial expansion from a KNOWN FOE over a DEPTH-VARYING background) + a SMALL independently-moving object + a view-fixed apparatus. The coarse sensor models a block matcher at half resolution (area-average the flow, HALVE the displacement, ROUND to integers — 158000's measured quantization wall made analytic); the fine sensor keeps full-resolution flow.

- **(i) coarse under-resolves at the salient region.** The coarse depth-from-motion
  Spearman (recovered vs known depth) in the foveal window is DEGRADED relative to
  fine (fewer cells, quantized displacements). Decision: `coarse_depth_spearman <
  fine_depth_spearman` (fine strictly recovers), fine over ≈ 4× the cells.
- **(ii) salience LOCATES the region.** The residual (tangential) salience argmax
  lands ON the mover; the RAW |flow| argmax lands OFF it (on the highest-magnitude
  near/parallax background — the 157000 reason salience must be on the RESIDUAL).
  Decision: `residual_peak_on_mover == True` AND `raw_flow_peak_on_mover == False`.
- **(iii) foveated fine flow RECOVERS.** In the same window, fine depth Spearman
  ≥ 0.90 (near-exact on the ideal oracle) and the mover is isolated (IoU ≥ 0.5),
  both ≥ the coarse arm. Decision: `fine_depth_spearman >= 0.90` AND
  `fine_mover_iou >= 0.5` AND `fine_depth_spearman > coarse_depth_spearman`.
- **(iv) COST.** Foveated (coarse-everywhere + one fine window) is a small fraction
  of full-res-everywhere. Decision: `foveated_fraction_of_fullres <= 0.5`.

### H2 — E1M1 (real WAD, 158000's walk/seed/grid), GROUND-TRUTH-SCORED against the VizDoom DEPTH + labels buffers.

- **(a) DEPTH.** Per-frame Spearman(recovered depth r/|flow|, downsampled depth
  buffer) on radial-consistent background cells, on efference-forward frames:
  the COARSE-full-frame arm (158000's null, −0.11) vs the FOVEATED-fine-in-window
  arm vs the coarse-in-the-same-window arm vs the full-fine-everywhere ceiling
  (158000's +0.40). Decision: a POSITIVE result is the foveated-fine-in-window
  median beating the coarse-in-window median (the null it re-resolves) by a
  CI/distribution margin, and approaching the full-fine ceiling. Sign reported.
- **(b) IMP recovery (the sub-pixel wall).** (b1) Does coarse salience LAND on the
  imp? (fovea-to-imp distance, imp GT from the labels buffer — SCORING oracle for
  WHERE only). (b2) At a fine window placed ON the imp GT (scoring-oracle
  placement), does the imp produce super-pixel (trackable, |flow|>floor) flow that
  the coarse pass misses? Report coarse vs fine imp-flow-cell counts. Decision:
  POSITIVE if fine imp-flow-cells > coarse (super-pixel recovery); the imp being
  invisible to coarse motion salience (b1) is a NAMED DEGRADE, not a hidden one.
- **(c) COST / real-time (measured ALONE).** ms/frame for the foveated pass
  (coarse down=2 flow + fine windows) vs full-res-down=1-everywhere. Doom's budget
  ≈ 28.6 ms/frame. Decision: report both vs budget; POSITIVE if foveated is
  within budget where full-res is over.

### CONTROLS (must correspond, §6)

- **No salient region (pure radial, no independent mover):** the residual salience
  is ≤ the integer-flow rounding band (≈ 0.71 px) everywhere ⇒ nothing clears the
  one-pixel salience floor ⇒ NO fovea fires (falls back to coarse). Decision:
  `n_fovea == 0`.
- **Salience on the RESIDUAL, not the egomotion background:** the residual peak is
  ON the mover while the raw-|flow| peak is on the fastest (near/parallax)
  background — the reason salience must be the residual (157000). Decision as (ii).
- **Two salient regions:** two matched movers ⇒ top-2 foveae land on BOTH, not one
  merged window. Decision: `both_regions_covered == True`.

## PREDICTIONS (stated in advance, with provisos)

- H1 (i)-(iv): I predict all hold — the mechanism is analytic (tangential is
  depth-free; the FOE falls out; r/|flow| = Z/speed). The coarse null on the ideal
  oracle is a RESOLUTION degrade (fewer cells + integer quantization), NOT the
  negative null 158000 measured on real block-match noise — H1 proves the
  mechanism, H2 carries the real null. Proviso: a mover slower than ≈ 1 px of
  coarse tangential is below the coarse sensor's resolution (the sub-pixel wall)
  and cannot be LOCATED coarsely — the mover must clear the coarse rounding band
  to be a fovea target (the same wall H2's imp exhibits).
- H2 (a): I predict the foveated-fine-in-window depth BEATS the coarse-in-window
  null and approaches the full-fine ceiling — but MODESTLY and NOISILY on real
  block-matched flow, and only on frames where the fovea fires on a
  depth-structured region. Proviso that would break: if the salient window lands on
  a textureless / motion-poor region, the fine flow there is as unreliable as the
  coarse and depth washes out.
- H2 (b): I predict the imp is SUB-PIXEL at coarse (0 monster tracks, the
  156/157/158 wall), so coarse motion salience will LIKELY NOT land on it (b1 a
  named DEGRADE — motion salience cannot bootstrap a mover with no coarse motion
  signal), while a fine window placed on the imp DOES resolve super-pixel flow
  (b2) — proving foveation resolves the imp IF pointed there, but that
  motion-only salience cannot point there. Honest split expected.
- H2 (c): I predict foveated ms/frame << full-res-everywhere ms/frame; whether
  either is within the 28.6 ms budget depends on the block-matcher cost (156000's
  ~87 ms/frame carve is a separate, unchanged residual — I time the FLOW passes).
- Honest DEGRADE path: if the foveated depth does NOT beat the coarse-in-window
  null, or the fovea mis-locates, or the imp stays unrecoverable, I diagnose
  (window landing / flow quality / sub-pixel) — a diagnosed negative is a result
  (§7).

## EXACTLY THE LISTED TESTS

`tests/test_salience_foveation_migrated.py`: H1 (i)-(iv) able-to-fail; the three
controls (no-salient→no-fovea, residual-not-raw-peak, two-regions→both); H2
(foveated-fine depth beats the coarse-in-window null OR the named degrade; imp
super-pixel-in-fine-window OR the named sub-pixel degrade; foveated < full-res
cost); the §10 provenance assertion is `source_match in {own, shared}` (NEVER
`== "shared"`, NEVER a pinned hash). Reads MEASURED values, never an exact d2;
skips H2 if WAD/VizDoom absent. No sweeps, no re-runs — a further attempt needs a
NEW pre-registration.

## ARCHITECTURE (CLAUDE.md — the agent is Rust)

NO agent decision in Python. `salience_field` / `select_fovea` /
`fine_flow_window` are MECHANICAL numpy over the flow / salience fields (argmax,
top-K, connected components, block-SAD on a crop) — no conditional over graph
state. Depth / mover are 158000's mechanical sensors; salience is 158000's radial
residual as a field. `capture_e1m1` / the scripted walk are the world adapter; the
DEPTH + labels buffers are the SCORING ORACLE (Spearman / IoU / distance by
POSITION), never fed to the eye, never cross-process region-id. NO Rust added, NO
seed consumed, NO default moved — NEW FILE ONLY, so every shipped
154/155/157/158 path is byte-identical BY CONSTRUCTION (all salience / depth /
flow imports are unchanged). Engine `shared` (source identical), asserted
`in {own, shared}`.

## OUTCOME (engine + oracle)

- Engine (worktree, no Rust change): `source_match = shared` (canonical engine via
  the `.pth`), recorded in `results/salience_foveation.json`.
- Oracle `scripts/rung7_vision_bench.sh` BEFORE: **222 passed / 0 failed**
  (data/ symlinked). AFTER + all H1/H2/control numbers: recorded in
  `VISION_SALIENCE_FOVEATION_RESULTS.md`.
