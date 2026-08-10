# PRE-REGISTRATION — DOOM FINER GRID + HUD MASK (block 153000–153999)

**SEED CLAIM 153000-153999:** `CLEAN`

Verbatim `python3 scripts/seed_claim.py 153000 153999` output (§3 clause 8 —
the pasted verdict INCLUDING the unresolved-sink count, not a mention):

```
SEED CLAIM 153000-153999: CLEAN -- no collision DETECTED.
  Scope: 854 files with seed sinks; 573 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The block is priced with 573 unresolved sinks tree-wide; the claim is that no
collision is DETECTED, never that none exists. This run seeds VizDoom ONCE at
`DOOM_SEED = 153000` (the block base) and draws no other RNG (the carve, the
downsample, the mask and the scoring are all deterministic).

## 0. Framing — this is a MEASUREMENT rung on top of 152000's baseline

152000 (`VISION_EYE_ON_DOOM_RESULTS.md`) pointed the shipped eye at Doom RGB and
scored it against VizDoom's labels buffer. Baseline: enemy IoU 0.243 turning /
0.018 stationary (DEGRADE). FOUR walls were isolated. This rung attacks the two
that the clean stationary/no-egomotion regime lets us attack directly:

- **Wall 1 (DOMINANT): sub-grid resolution.** At the 60×80 grid (4× downsample)
  the stationary enemy is a median of **2 grid cells** and washes out of the grid
  entirely in **40 of 51** enemy-present frames; enemy IoU is 0.000 below 3 cells
  and a ~0.25 plateau above. The lever is grid RESOLUTION.
- **Wall 2: the weapon sprite is a persistent false object** (IoU ~0.25). It
  occupies a FIXED bottom-band screen region; mask it out.

Like 152000 this is a PROBE with a MEASUREMENT deliverable, not a directional
CONFIRM bet — but unlike 152000 it has a falsifiable *relationship* (IoU vs
resolution) which the gate checks on the recorded run (able to fail).

## 1. Hypotheses (two-sided)

**H1 — finer grid clears the sub-grid floor and enemy IoU rises.** Sweep the
downsample factor DOWN ∈ {4, 2, 1} → grids 60×80, 120×160, 240×320 (full VizDoom
res). The SAME stationary enemies (one capture, three downsamples) go from ~2
cells → ~8 → ~16+ cells. Prediction: enemy IoU rises MATERIALLY with resolution
and enemy survival (frames where the enemy survives downsample into the grid)
rises toward all enemy-present frames. **Two-sided:** the alternative is that IoU
stays on its ~0.25 plateau even when the enemy is 16+ cells — a DEEPER wall (the
carve cannot grab even a resolved enemy tightly: over-merge with background, or
the common-fate looming signal is too weak). Which one, and why, is the finding.

**H2 — the fixed weapon-sprite mask removes the persistent false object without
touching enemies.** The weapon (DoomPlayer label) renders in a FIXED bottom band
(measured rows [155..239] of 240; `render_hud=false`, so no status bar — the band
is pure weapon furniture); enemies render at the horizon (measured rows [116..130]).
Masking the bottom band (rows ≥ 150 of 240, full width — a mechanical
world-adapter crop) should drop weapon-sprite IoU to ~0 and leave enemy IoU
unchanged (masked ≈ unmasked). **Two-sided:** if masking also lowers enemy IoU,
the band clips enemies (a geometry error) and the mask is wrong.

## 2. The statistics, exactly

Primary carve mode = **MOTION** (`native.segment_motion`, common-fate,
texture-blind — sidesteps wall 3, the value carve's texture over-segmentation);
VALUE carve (`native.segment`) reported alongside as the aperture-free comparison.
All at L=4 (the shipped quantization default; L is NOT the lever here). Per
resolution DOWN ∈ {4,2,1}, per carve mode, masked and unmasked:

- **enemy IoU** — for each GT enemy object (labels-list entry with
  `object_name != "DoomPlayer"`) that survives downsample into the grid, the best
  IoU between its modal-labels cell-set and any non-ground carved region's
  cell-set (read from the graph via `within` edges). mean / median / min / max +
  the RAW per-frame distribution.
- **enemy survival count** — of the enemy-present frames, how many the enemy
  survives downsample into the grid (`enemy value present in the modal-label
  grid`). This is the sub-grid wall metric itself.
- **matched-subset enemy IoU** — enemy IoU restricted to the frames where the
  enemy survives at ALL THREE resolutions (identical enemies), so the pure
  IoU-vs-resolution effect is not confounded by the survival count. **This is the
  quantity the gate asserts (`IoU_1x > IoU_4x` on the matched subset, motion
  carve) — able to fail if finer grid did not help.**
- **enemy IoU vs GT cell count** — the resolution wall as a curve.
- **weapon-sprite IoU** (masked vs unmasked) — the H2 false-object metric.
- **false-positive region count** — non-ground carved regions matching no GT
  object (loosest threshold).
- **per-frame wall ms** — carve time per resolution (CHARACTERIZATION only, run
  in the same process; not a verdict — reported to note real-time feasibility).

## 3. n, fixed in advance

VizDoom `defend_the_center`, `set_seed(153000)`, action = fixed `attack` every
tic (STATIONARY player — no egomotion; `attack` keeps the player alive longer than
`noop`, so more enemy-present frames — the muzzle-flash confound sits INSIDE the
masked band and so does not touch the enemy carve), capture up to `N_FRAMES = 60`
tics (or until the episode ends). Three resolutions × two carve modes × {masked,
unmasked}. n = frames captured (deterministic under the fixed seed + fixed
action), reported with the result. No power analysis: this is an exploratory
probe with no directional CONFIRM, so §3.3's power requirement (which governs
confirmatory claims) does not bind — stated explicitly, not skipped.

## 4. Confirmatory seeds never used for anything

None spent — this is a probe. The only seed drawn is `DOOM_SEED = 153000` (VizDoom
episode determinism), inside the declared block, seeded once.

## 5. Decision rule / what a null means

No accept/reject gate on the absolute IoU. The record is the measurement. A
NON-jump (IoU flat across resolution even when the enemy is 16+ cells) is a RESULT
— it names a deeper wall than sub-grid resolution. The gate
(`tests/test_doom_finer_grid_migrated.py`) asserts:
1. the measured relationship on the recorded run — matched-subset motion-carve
   enemy IoU at 1× > at 4× (able to fail if finer grid did not help);
2. the HUD mask removes the weapon false-positive on a CONSTRUCTED case and
   leaves an above-band object untouched;
3. the scorer is correct on a synthetic known-object case.
It does NOT hard-code the absolute Doom IoU.

## 6. Exactly the listed measurements. No sweeps.

Three resolutions, two carve modes, {masked, unmasked}, L=4 fixed. No parameter
search over L / block / mask-boundary to improve the score — those are DECLARED
§13 residuals below. L=8 is NOT swept here (152000 already characterized "finer
grain fragments"; this rung's lever is grid resolution, not quantization).

## 7. Prediction, stated in advance (with provisos)

- **H1:** enemy IoU rises materially with resolution (matched subset, motion
  carve), and survival rises toward all enemy-present frames. *Proviso that would
  break it:* if IoU stays on the ~0.25 plateau at 16+ cells, the sub-grid wall
  was NOT the whole story and a deeper carve wall dominates — I will isolate and
  name it (looming signal too weak for common-fate → aperture; or over-merge with
  background → the value carve's tightness).
- **H2:** weapon-sprite IoU → ~0 under the mask; enemy IoU masked ≈ unmasked.
  *Proviso:* if enemy IoU drops under the mask, the band clips an enemy and the
  fixed geometry is wrong — I will report the overlap and the corrected band.
- **Cost:** full-res (76 800 cells) costs materially more carve time than 4×
  (4 800 cells). Reported as characterization; I predict it is still within
  real-time on Doom's small frames (< ~100 ms/frame), but this is measured.

## 8. DECLARED RESIDUALS (§13 — magic numbers stated, NOT tuned to the score)

- **DOWN ∈ {4, 2, 1}** — clean integer downsample factors of Doom's 240×320
  (grids 60×80, 120×160, 240×320). The sweep variable itself; not chosen to
  flatter any single IoU.
- **HUD-mask band = pixel rows ≥ 150 of 240, full width.** JUSTIFIED BY RENDERING
  GEOMETRY, not by score: the weapon (DoomPlayer) sprite was measured to occupy
  rows [155..239] and enemies rows [116..130]; `render_hud=false` so there is no
  status bar. Row 150 sits 5 px above the weapon top (covers it fully) and 20 px
  below the enemy horizon (clears it). Applied in pixel space before downsample
  (resolution-independent: grid boundary = round(150/240 · GH)).
- **block (motion flow aperture) = 16 // DOWN** → {4× : 4, 2× : 8, 1× : 16},
  keeping the physical flow patch at a CONSTANT ~16-pixel aperture across
  resolutions (so H1's resolution effect is not confounded by a shrinking physical
  aperture). The value carve — which has NO aperture parameter — is reported
  alongside as the aperture-free resolution signal.
- **L = 4** — the eye's shipped quantization default; fixed, not swept.
- **IoU thresholds {0.1, 0.25, 0.5}** — recovery reported at all three; the RAW
  IoU distribution is reported so no thresholded rate is dressed as the result.
- **DOOM_SEED = 153000** — the block base; fixed for reproducibility.

## 9. Architecture audit (CLAUDE.md — the agent is Rust)

- The carve is the EXISTING Rust primitive (`segment_and_track` /
  `segment_motion_and_track` via `native.segment` / `native.segment_motion`),
  byte-identical to the shipped eye. No Rust changed, no seed added, no default
  moved.
- The VizDoom driver is a WORLD ADAPTER: it reads bytes from the game and hands
  the eye raw pixels. It decides NOTHING about graph state. The labels buffer /
  labels list are the SCORING ORACLE — never fed to the eye.
- The HUD mask is a FIXED screen-region crop of the sensor input (zero the luma
  in a fixed pixel band before downsample) — mechanical world-adapter I/O, no
  conditional over graph state, no agent decision. The band is fixed geometry,
  declared above.
- Scoring (`downsample_*`, `quantize`, `iou`, `score_frame`, `apply_hud_mask`) is
  pure set arithmetic over the carve output and the labels grid, by POSITION/IoU,
  never by cross-process region-id identity (§ discipline 5).
- New files only (`scripts/doom_finer_grid_probe.py`, this prereg, the results
  doc, the gate, `results/doom_finer_grid*`). Because nothing existing changed,
  the coarse/shipped carve path is byte-identical BY CONSTRUCTION — the oracle
  bench must read 222/0 both sides.

## 10. Engine provenance

Engine is `shared`: the loaded native matches the tree's Rust source fingerprint
(`3a66c0636a98…`, identical to 152000 — no Rust touched). The result records
`source_match` + `source_fingerprint`; NO build hash is pinned (§10 / §12 — assert
source_match, never a mutable hash).

## 11. Oracle

`bash scripts/rung7_vision_bench.sh` BEFORE (recorded before writing probe code) —
must read 222 passed / 0 failed. Re-run AFTER; must remain 222/0 (data/ symlinked
in the worktree, §10.2).
