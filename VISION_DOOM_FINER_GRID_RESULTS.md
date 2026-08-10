# DOOM FINER GRID + HUD MASK — RESULTS (block 153000–153999)

**SEED CLAIM 153000-153999: CLEAN** (verbatim `check_claim` in
`VISION_DOOM_FINER_GRID_PREREG.md`; 573 unresolved sinks tree-wide priced;
VizDoom seeded ONCE at `153000`, no other RNG).

A MEASUREMENT rung on top of 152000's ground-truth-scored baseline
(`VISION_EYE_ON_DOOM_RESULTS.md`). It attacks the two walls the clean
stationary/no-egomotion regime lets us attack: **wall 1 — sub-grid resolution**
(sweep the grid 4×→2×→1×) and **wall 2 — the ego-attached weapon-sprite percept**
(a fixed-region crop). The existing carve, re-scored; NO Rust, NO seed, NO
existing-file change.

## Oracle (unmoved — new files only)

| | `bash scripts/rung7_vision_bench.sh` |
|---|---|
| BEFORE | **222 passed, 0 failed** (169.66s) |
| AFTER  | **222 passed, 0 failed** (170.27s) |

New files only (`scripts/doom_finer_grid_probe.py`,
`tests/test_doom_finer_grid_migrated.py`, this doc, the prereg,
`results/doom_finer_grid*`). Nothing existing changed, so the shipped carve path
is **byte-identical BY CONSTRUCTION** — the oracle holds on both sides. The probe
REUSES 152000's gated scorer + carve drivers (import), so the carve is provably
the same primitive.

## Engine

`source_match == shared`, source fingerprint `3a66c0636a98…` (identical to
152000 — no Rust touched). NO build hash pinned (§10/§12 — assert `source_match`,
never a mutable hash). Recorded in `results/doom_finer_grid.json`.
Worktree fixed engine + `data/` symlinks per §10.1–§10.2 (the provenance gate
passes 7/7 in-tree; the worktree was relocated out of the canonical tree's
`.claude/` to stop pytest rootdir/conftest cross-collection — see WHAT I GOT
WRONG).

## Setup (reproducible)

- **Scenario:** VizDoom 1.3.0 `defend_the_center`, headless, `RES_320X240`,
  `RGB24`, depth + labels enabled, `render_hud=false`.
- **Regime:** STATIONARY player — fixed `attack` every tic (no egomotion;
  enemies approach). `game.set_seed(153000)`; 60 tics captured, frame per tic →
  deterministic. **One capture, scored at three downsample resolutions** (so the
  enemies are IDENTICAL across resolutions).
- **Resolutions:** DOWN ∈ {4, 2, 1} → grids 60×80 / 120×160 / 240×320 (full
  VizDoom res). L=4 (shipped quantization default; not the lever).
- **Carve:** the EXISTING Rust primitives — `native.segment_motion`
  (common-fate, **the pre-registered PRIMARY** — texture-blind) and
  `native.segment` (value, reported as the aperture-free comparison), via
  `falling_world`. Motion flow aperture `block = 16 // DOWN` (constant ~16-px
  physical patch across resolutions, declared §13).
- **Ground truth:** VizDoom labels buffer; GT enemy = named actor
  (`MarineChainsawVzd`); weapon/self = `DoomPlayer`. Scored by IoU/POSITION,
  never by region-id.

## THE HUD MASK — a DISCLOSED STEPPING-STONE, not the principled treatment

**The weapon sprite and HUD are NOT "false objects."** The eye perceives them
correctly — they are real, persistent percepts. They are simply not WORLD
objects: they are the agent's own **apparatus** (it senses its state through the
HUD, it acts THROUGH the weapon), **EGO-ATTACHED** — fixed in view-space, they
do not obey world-motion. That is the agent's own boundary (project principle:
boundary = typed edges from `agent_root`, `senses` / `acts_on`, never a
hardcoded flag).

The mask here is a **fixed screen-region crop** (drop carved regions lying
entirely in pixel rows ≥ 150 of 240 — where the DoomPlayer weapon was measured to
render, rows [155..239]; enemies render at the horizon, rows [116..130]).
**Hardcoding a screen-region is exactly the kind of magic-number the architecture
avoids** (§13). It is disclosed here as a SCAFFOLD to isolate the enemy-carving
measurement — **NOT** the principled treatment.

**The principled treatment (a strong future rung, named not built):** recognize
self/apparatus by **INVARIANCE TO EGOMOTION**. Under player turning the world
optic-flow moves but the HUD/weapon stay fixed in view-space; what is
motion-invariant-to-egomotion is SELF (the ego-stable overlay), distinct from
world objects that flow. That is a discoverable boundary, not a mask.

## HEADLINE — the sub-grid wall is REAL and CLEARED for the VALUE carve; the PRIMARY MOTION carve hits a DEEPER wall

Enemy IoU vs GRID RESOLUTION (`defend_the_center`, stationary, seed 153000,
L=4). Enemy IoU is over the enemy-present frames where the enemy SURVIVES
downsample into the grid; survival is itself the sub-grid metric.

| DOWN | grid | enemy survives / present | enemy IoU **value** (mean, n) | enemy IoU **motion** (mean, n) | weapon IoU value un→masked | wall ms/f value / motion |
|---|---|---|---|---|---|---|
| **4×** | 60×80 | **11 / 57** | **0.018** (n=11) | 0.015 (n=11) | 0.246 → 0.064 | 2.3 / 10.0 |
| **2×** | 120×160 | **30 / 57** | **0.155** (n=30) | 0.005 (n=30) | 0.258 → 0.067 | 37.8 / 162.6 |
| **1×** | 240×320 | **50 / 57** | **0.250** (n=50) | 0.004 (n=50) | 0.265 → 0.065 | 889.5 / 2796.6 |

**Matched subset — the IDENTICAL 11 enemies that survive at ALL THREE
resolutions** (isolates pure IoU-vs-resolution from the survival confound):

| carve | 4× | 2× | 1× |
|---|---|---|---|
| **value** | **0.018** | **0.422** | **0.372** |
| **motion** (primary) | 0.015 | 0.014 | 0.016 |

### Wall 1 (sub-grid resolution) is REAL and CLEARED — for the VALUE carve

- **Survival rises 11 → 30 → 50 of 57** enemy-present frames: at 4× the enemy
  washes out of the grid in 46/57 frames; at full res it survives in 50/57. This
  IS the sub-grid wall, measured directly.
- **Matched-subset value IoU jumps ~20×**: 0.018 (4×) → 0.422 (2×) / 0.372 (1×)
  on the SAME 11 enemies. Below 3 cells → IoU 0; once the enemy is resolved the
  value carve grabs it. (2× peaks above 1×: at full res the textured Doom walls
  over-segment — 296 vs 42 false-positive regions/frame, 152000's "finer grain
  fragments" — diluting the enemy's best-region IoU. The operating point for the
  value carve is ~2×.)
- **IoU-vs-cell-count** confirms the curve: 4× {1–2 cells: 0.000, 3–5: 0.067};
  2× {1–2: 0.000, 6–15: 0.403, 16–40: 0.611}; the enemy must exceed ~3 cells.

### Wall 2 (ego-attached weapon percept) cropped, enemies UNTOUCHED

- Weapon-sprite IoU falls **0.25 → 0.065** under the crop (a ~4× reduction) at
  every resolution. It does **NOT** reach 0: the residual is a carved region
  STRADDLING the band boundary — precisely the imperfection that marks the
  fixed-region crop as a crude scaffold, not the principled ego-invariance
  treatment.
- **Enemy IoU is EXACTLY unchanged** by the crop at every resolution
  (0.018→0.018, 0.155→0.155, 0.250→0.250; |Δ| < 1e-9): enemies render above the
  band, so no enemy region is ever cropped. The band is geometry-correct.

### THE DEEPER WALL — the PRIMARY (motion) carve does NOT grab even a resolved enemy

The pre-registered primary is the **common-fate MOTION carve** (texture-blind).
Its matched-subset enemy IoU is **FLAT at ~0.015 across ALL resolutions**
(0.015 → 0.014 → 0.016) — a fully-resolved 50-cell enemy is carved no better than
a 2-cell one. **Finer grid does nothing for the motion carve.** This is the
two-sided alternative the prereg named: a wall DEEPER than sub-grid resolution.

The mechanism: in the STATIONARY regime the enemy approaches by **looming**
(radial expansion toward the player), a near-sub-pixel per-frame displacement for
a distant sprite — too weak a common-fate signal for the block-matched flow field
to separate the enemy from the static background, at ANY grid resolution.
Resolution cannot fix a motion signal that is below the flow aperture. So:

> **Sub-grid resolution was the wall for the TEXTURE (value) carve, and finer
> grid clears it. It was NEVER the wall for the object-notion (motion) carve —
> the wall there is the looming signal's weakness, which resolution does not
> touch. "Bins propose, continuous decides": here finer bins let the VALUE
> carve propose the enemy, but the MOTION carve's proposal is empty regardless.**

## Cost — full-res is NOT real-time-feasible on this carve

Doom runs at 35 tics/s = **28.6 ms/frame** real-time. Per-frame carve cost:

| DOWN | value ms/f | motion ms/f | real-time? |
|---|---|---|---|
| 4× (60×80) | **2.3** | 10.0 | value ✓, motion ✓ |
| 2× (120×160) | 37.8 | 162.6 | value ~1.3× over |
| 1× (240×320, 76 800 cells) | **889.5** | 2796.6 | ~31× (value) / ~98× (motion) over |

Full-res is **~30–100× too slow** for real-time on this connected-components +
graph-readback carve — the cost is dominated by the 76 800-cell segmentation and
the 296 over-segmented regions/frame the textured walls fracture into at full
res. **4× is comfortably real-time; ~2× value is the practical ceiling.** A carve
that scales to full res in real-time is a separate engine task (the memory-layout
/ SIMD-stencil direction), not measured here.

Triptychs (RGB | labels | carve, mask boundary drawn) at the largest-enemy frame,
per resolution: `results/doom_finer_grid_imgs/doom_finer_{value,motion}_d{4,2,1}_f10.png`.

## Architecture / invariant audit (CLAUDE.md — the agent is Rust)

- **Carve is the existing Rust primitive**, byte-identical to the shipped eye
  (`segment_and_track` / `segment_motion_and_track`, imported from 152000's
  driver). No Rust changed, no seed added, no default moved.
- **The VizDoom driver is a world adapter** — reads game bytes, hands the eye raw
  pixels, decides nothing about graph state. The labels buffer is the SCORING
  ORACLE, never fed to the eye.
- **The HUD mask is a FIXED geometric crop of the carve readout** (drop regions
  in a fixed pixel band, by POSITION only) — mechanical world-adapter I/O, no
  conditional over graph state, no agent decision. Disclosed as a scaffold.
- **Scoring is pure set arithmetic** (IoU) by POSITION, never by cross-process
  region-id (§ discipline 5). Verified cross-process stable: the headline H1/H2
  gate assertions pass identically in **3 fresh processes**.
- **New files only** ⇒ coarse/shipped path byte-identical by construction; oracle
  222/0 both sides.

## WHAT I GOT WRONG

- **I called the weapon/HUD a "false object" throughout the first draft.** They
  are not — the eye perceives them CORRECTLY; they are ego-attached
  self-apparatus (the agent's own tool + instrumentation), not world objects.
  Reframed throughout after the correction; the measurement is unchanged. The
  fixed-region mask is a disclosed stepping-stone, and the principled treatment
  (ego-invariance to egomotion) is named, not bolted on.
- **I predicted enemy IoU would rise materially with resolution for the PRIMARY
  (motion) carve. It did not** — motion is flat at ~0.015 at every resolution.
  The sub-grid wall was the wall for the VALUE carve; the motion carve hits the
  deeper looming-signal wall. This is the honest two-sided outcome, not a null.
- **I first placed the worktree INSIDE the canonical tree's `.claude/`
  directory.** Because the worktree was nested under the canonical
  gamma-substrate, pytest's rootdir/conftest discovery cross-collected the two
  trees and the provenance gate failed 221/1 (this_tree ≠ realpath(ROOT)).
  Relocating the worktree to `research/.claude/worktrees/` (the convention the
  other agents use, a SIBLING of the tree) fixed it → 222/0. A worktree must not
  nest inside the tree it forks.
- **I expected the mask to drop weapon IoU to ~0.** It drops to ~0.065, not 0 — a
  straddling region survives the crop. Honest, and it underlines that the crude
  crop is a scaffold.

## Where this sets up the next rung

Two named, falsifiable levers, in priority order:
1. **The ego-invariance boundary** (replaces the mask): recognize self/apparatus
   by motion-invariance-to-egomotion — the ego-stable overlay stays fixed while
   the world flows under turning. A discoverable typed boundary from `agent_root`,
   not a screen-region magic number. This is the principled wall-2 treatment.
2. **The deeper motion wall:** the common-fate carve cannot grab a slow-looming
   enemy at any resolution. Either (a) a looming-specific flow (radial /
   scale-change field — the enemy grows, it does not translate), or (b) accept
   that the VALUE (appearance) carve is the enemy-proposer here and pair it with a
   strong continuous verdict ("bins propose, continuous decides"). The value
   carve at ~2× already reaches matched-subset IoU 0.42 — the appearance path is
   the live one; the object-notion motion path needs a looming primitive.

## Proposed VISION_PROTOCOL.md ledger row

| **153000–153999 (Doom finer-grid + ego-apparatus crop; NO Rust, NO seed — new files only; the existing carve re-scored at 3 grid resolutions + a disclosed fixed-region scaffold crop)** | **THE SUB-GRID WALL IS REAL AND CLEARED FOR THE VALUE CARVE (enemy IoU jumps ~20×); THE PRIMARY MOTION CARVE HITS A DEEPER WALL (flat at any resolution).** One stationary `defend_the_center` capture (seed 153000, no egomotion, L=4, headless RES_320X240) scored at DOWN∈{4,2,1} → 60×80/120×160/240×320, regions read from the graph via `within` edges, IoU vs the labels buffer by POSITION. **VALUE carve: matched-subset enemy IoU (identical 11 enemies) 0.018 (4×) → 0.422 (2×) → 0.372 (1×)** — a ~20× jump; enemy SURVIVAL 11→30→50 of 57 frames; IoU 0 below 3 cells, resolved above (2× is the operating point — full res over-segments Doom's walls 42→296 FP regions/f, "finer grain fragments" again). **MOTION carve (pre-registered primary, common-fate): matched-subset IoU FLAT at ~0.015 across ALL resolutions** — a fully-resolved 50-cell enemy carved no better than a 2-cell one: the DEEPER wall the prereg named (the stationary enemy approaches by slow LOOMING, a near-sub-pixel signal below the flow aperture; resolution cannot fix it). So sub-grid resolution was the wall for the TEXTURE carve, never for the object-notion carve. **EGO-APPARATUS reframe (creator correction):** the weapon/HUD are NOT false objects — the eye perceives them correctly; they are the agent's own EGO-ATTACHED apparatus (senses via HUD, acts via weapon), fixed in view-space. The fixed-region crop (rows ≥150 of 240, justified by measured weapon geometry [155..239] vs enemy horizon [116..130], render_hud=false) is a DISCLOSED STEPPING-STONE scaffold, explicitly a magic-number the architecture avoids; it cuts weapon IoU 0.25→0.065 (residual = a straddling region) and leaves enemy IoU EXACTLY unchanged. PRINCIPLED treatment named not built: recognize self by INVARIANCE-TO-EGOMOTION (world flows under turning, the ego-overlay stays fixed) — a discoverable boundary, not a mask. **COST:** full-res NOT real-time (value 889ms/f, motion 2.8s/f vs Doom's 28.6ms; 4× value 2.3ms is real-time; ~2× the ceiling). Architecture audit CLEAN: no Rust/seed/default moved; VizDoom driver a world adapter; crop is a fixed positional readout crop, no graph-state decision; scored by IoU/position not region-id (headline gate stable in 3 fresh processes). shared engine `3a66c0636a98` (source_match==shared, no Rust); oracle **222/0 BEFORE and AFTER**; gate `test_doom_finer_grid_migrated` **9/9** (scorer + mask crop constructed cases able-to-fail; H1 value-clears-wall AND motion-hits-deeper-wall AND survival-rises read from the recorded run; H2 crop cuts weapon percept, enemy exactly unchanged; skips if VizDoom absent). §9 byte-identity — new files only. Raw: `results/doom_finer_grid.json`, `results/doom_finer_grid_imgs/` (RGB\|labels\|carve triptychs ×3 resolutions). NAMED NEXT LEVERS: the ego-invariance self/apparatus boundary (replaces the mask); a looming-specific flow primitive (the enemy grows, it does not translate) OR pair the value/appearance proposer with a continuous verdict. `SEED CLAIM 153000-153999 CLEAN`. |
