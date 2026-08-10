# EYE ON DOOM — RESULTS (block 152000–152999)

**SEED CLAIM 152000-152999: CLEAN** (verbatim `check_claim` in
`VISION_EYE_ON_DOOM_PREREG.md`; 571 unresolved sinks tree-wide priced; VizDoom
seeded ONCE at `152000`, no other RNG).

This is a **PROBE** (like 143000): point the shipped eye at Doom RGB pixels and
SCORE its carve against VizDoom's per-pixel labels-buffer GROUND TRUTH. No
CONFIRM target. The deliverable is a **ground-truth-scored baseline + the
precisely isolated wall(s)**, which the real-video chain (145000–150000) never
had — Doom hands us frame-aligned truth. DEGRADE was expected and is the finding.

## Oracle (unmoved — this is a probe, new files only)

| | `bash scripts/rung7_vision_bench.sh` |
|---|---|
| BEFORE | **222 passed, 0 failed** (178.34s) |
| AFTER  | **222 passed, 0 failed** |

New files only (`scripts/eye_on_doom_probe.py`, `tests/test_eye_on_doom_migrated.py`,
this doc, the prereg, `results/eye_on_doom*`). Nothing existing changed, so the
shipped carve path is **byte-identical BY CONSTRUCTION** — the oracle holds on
both sides.

## Engine

`source_match == shared`, source fingerprint
`3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60`. NO build
hash pinned (§10/§12 — assert `source_match`, never a mutable hash). Recorded in
`results/eye_on_doom.json`.

## Setup (reproducible)

- **Scenario:** VizDoom 1.3.0 bundled `defend_the_center` (player STATIONARY
  unless it turns; enemies move — isolates object-motion from egomotion), headless
  (`set_window_visible(False)`), `RES_320X240`, `RGB24`, depth + labels enabled.
- **Seed:** `game.set_seed(152000)`; fixed action every tic → deterministic.
- **Conditions:** `stationary` (fixed `attack`) and `turning` (fixed `turn_right`),
  60 tics each, frame captured every tic.
- **Grid:** 60×80 = exact 4× area-mean downsample of 240×320 (declared §13
  residual). Luma = ITU-R 601. Quantized to L∈{4,8} (L=4 = the eye's shipped
  default). Motion field from `vector_field` block=4 (declared §13 aperture).
- **Carve:** the EXISTING Rust primitive — `native.segment`
  (`segment_and_track`, value carve) and `native.segment_motion`
  (`segment_motion_and_track`, common-fate) via `falling_world`. Regions read
  back from the graph via `within` edges (cell→Region); scored by POSITION
  (IoU), never by cross-process region-id identity.
- **Ground truth:** each enemy is a labels-list actor; VizDoom writes the
  ACTORS' `value` into the labels buffer and marks WORLD GEOMETRY (floor/walls)
  with reserved values 0 and 1. GT objects for scoring = **named actors only**
  (enemy `MarineChainsawVzd`=127; `DoomPlayer`=255 = the weapon/self sprite); the
  0/1 geometry is background, so a carve on the floor is a false positive.

## Headline — RGB-only carve vs ground truth

`value_carve`, L=4 (the shipped default), enemy = `MarineChainsawVzd`:

| condition | enemy IoU (mean / median / max) | recall@0.1 / @0.25 / @0.5 | n enemy-samples | non-ground regions/f | false-pos regions/f | wall ms/f |
|---|---|---|---|---|---|---|
| **stationary** | **0.018 / 0.000 / 0.20** | 0.09 / 0.00 / 0.00 | 11 | 12.5 | 11.5 | 2.0 |
| **turning**    | **0.243 / 0.250 / 0.667** | 0.82 / 0.56 / 0.13 | 78 | 7.8 | 5.7 | 1.2 |

Raw enemy-IoU distribution (turning, value L4, n=78): **14 exactly 0, 20 in
(0,0.25), 34 in [0.25,0.5), 10 ≥0.5.** A real, spread signal — not all-zero, not
usable. The stationary number is near-floor for a reason that IS the wall (below).

## THE WALLS, ISOLATED WITH NUMBERS

**1. SUB-GRID RESOLUTION is the dominant wall (measured at the pixel).** The
enemy `MarineChainsawVzd` is only **~55–71 pixels** of the 76 800-pixel frame
(<0.1%). After 4× downsample the STATIONARY enemy is a **median of 2 grid cells
(min 1, max 5)** — and in **40 of 51** enemy-present frames it does not survive
downsample into the 60×80 grid AT ALL (0 cells). Enemy IoU **as a function of GT
area** makes the wall a curve, not an impression:

| GT enemy area (cells) | n | mean IoU |
|---|---|---|
| 1–2 | 8 | **0.000** |
| 3–5 | 3 | 0.067 |

Under `turning` the same enemies come nearer (median **7** cells, max 22) and IoU
jumps to a **flat ~0.24–0.25 plateau** for every size ≥3 cells:

| GT enemy area (cells) | n | mean IoU |
|---|---|---|
| 3–5 | 24 | 0.253 |
| 6–10 | 39 | 0.235 |
| 11–22 | 15 | 0.248 |

So the stationary↔turning IoU gap (0.018 vs 0.243) is **enemy APPARENT SIZE, not
carving quality or egomotion** — the stationary enemy is sub-grid; the only frames
with a carve-able enemy are the turning ones. Below ~3 cells → IoU 0; at ≥3 cells
→ a ~0.25 ceiling. **This is the wall the real-video chain kept hitting, now
quantified against truth.**

**2. THE WEAPON SPRITE IS A PERSISTENT FALSE OBJECT.** The eye carves a stable
region over the `DoomPlayer` gun at the bottom of every frame: weapon-sprite IoU
**0.246** (stationary L4), **0.256** (turning L4). At rest the eye carves the GUN
(0.246) **~14× better than any enemy** (0.018). The HUD gun is the single most
reliably-carved "object" in Doom — and it is not a world object at all.

**3. BACKGROUND TEXTURE OVER-SEGMENTS, and finer grain SHATTERS it.** At L=4
the value carve holds ~8–12 non-ground regions/frame (of which ~all but ~1 are
false positives on wall/floor texture). At L=8 it **EXPLODES**: **275 (stationary)
/ 328 (turning) non-ground regions per frame**, ~all false positives — Doom's
textured brick walls fracture into hundreds of spurious "objects." Enemy IoU is
NOT rescued by the finer grain (0.243→0.261, inside noise), while tracking
fragmentation blows up (below). **Finer base grain fragments** — the same law the
Omniglot arc measured; L=4 (shipped) is correctly the operating point.

**4. EGOMOTION HURTS THE COMMON-FATE CARVE.** Under `turning` the whole scene
ego-flows, so common-fate cannot separate a moving enemy from the moving
background: motion-carve enemy IoU **0.159** < value-carve **0.243** (L4), and
L8 motion collapses further to **0.094** (recall@0.25 0.28→0.15). Weapon-sprite
IoU under motion falls to **0.061/0.003** — the gun, being static in the frame
while everything ego-flows, is correctly NOT grouped as moving, which is the one
thing common-fate gets right here. *Honest confound:* a clean egomotion isolation
would compare a LARGE enemy with vs without turning; the stationary enemy is
sub-grid, so this comparison is within-turning (motion vs value) only.

**5. TRACKING FRAGMENTS EVEN WHEN CARVING SUCCEEDS.** For the GT enemy
`object_id` (constant while alive), the best-overlapping carved region is the
SAME region-id across **0.82** of consecutive frames (turning value L4), but a
single enemy's lifetime is split across a **mean of 2.75 (max 4) distinct carve
region-ids** — it is re-born under a new id as it moves. At L8 fragmentation
worsens to **8.0 (max 14)**. Holding one object as one trajectory is unsolved —
exactly the "carve/track fragmentation" wall row 150000 named as the next lever,
now scored against `object_id` truth.

## Depth-assisted carve — the free lever that DID NOT pay off (measured, not over-invested)

Doom hands a per-pixel depth buffer for free; the prediction was that enemies
pop out in depth. **They did not, at this grid/scenario:** depth-value-carve
enemy IoU **0.000 (stationary) / 0.003 (turning)**, recall@0.1 ≤ 0.01. The depth
carve produces only ~2 large, very stable regions/frame (near-floor + walls;
tracked as ONE region with fragmentation 2.0, same-id 0.91) — clean, persistent,
and NOT the enemy. The 4× area-mean downsample washes out a small enemy's depth
contrast against the wall behind it. **Depth is real and free but does not
auto-solve carving here** — the RGB-only score remains the primary, most
transferable number (real cameras do not hand you clean depth anyway).

## Architecture / invariant audit (CLAUDE.md — the agent is Rust)

- **Carve is the existing Rust primitive**, byte-identical to the shipped eye
  (`segment_and_track` / `segment_motion_and_track`). No Rust changed, no seed
  added, no default moved.
- **The VizDoom driver is a world adapter** — reads game bytes, hands the eye raw
  pixels, decides nothing about graph state. The labels buffer / labels list are
  the SCORING ORACLE and are NEVER fed to the eye.
- **Scoring is pure set arithmetic** over the carve output (read from the graph
  via `within` edges) and the labels grid. No conditional over graph state
  selects agent behaviour.
- **New files only** ⇒ coarse/shipped path byte-identical by construction; oracle
  222/0 both sides confirms it.
- **Region ids scored by POSITION (IoU), never id-identity** — the carve's
  region ids are a cross-process HashMap artifact (§ discipline 5).

## WHAT I GOT WRONG

- **I predicted depth would beat RGB. It did not** (≈0.00 vs 0.24). At a 4×
  area-mean grid the enemy's depth contrast is washed out and depth carves only
  the big stable geometry. The free channel is not free value.
- **I designed `stationary` as the clean object-motion baseline. It is not** —
  `defend_the_center`'s enemies are sub-grid at rest (median 2 cells), so the
  stationary run mostly measures the sub-grid wall, and the only carve-able-enemy
  frames are the turning ones (which add egomotion). A clean "large enemy, no
  egomotion" baseline needs a scenario/geometry with a near enemy and a fixed
  camera (or a coarser enemy / finer grid). Named, not patched.
- **`stationary` used `attack`**, which fires the weapon (muzzle flash + gun
  animation) — a small extra confound on the stationary carve. The sub-grid wall
  dominates regardless, but a pure-`noop` baseline would be cleaner (it dies
  faster in this scenario, the reason `attack` was chosen).
- **Turning's HIGHER IoU initially reads like "turning helps."** It does not —
  it is enemy apparent size (the IoU-vs-area table makes this explicit). I nearly
  reported the raw stationary/turning gap as an egomotion result; it is a size
  confound.

## Where this sets up the next rung

The mechanisms the real-video chain built now have a ground-truth target:
**egomotion compensation** (148000's motion-compensated / P-frame search) applied
to the common-fate carve under turning; **appearance-tracking** (151000) to hold
one enemy as one trajectory across the fragmentation; and a **grid/scale** lever
for the sub-grid wall (the enemy must exceed ~3 cells to score). Each is now
falsifiable against per-pixel + `object_id` truth, not guessed.

## Proposed VISION_PROTOCOL.md ledger row

| **152000–152999 (eye-on-Doom PROBE; NO Rust, NO seed — new files only; the existing carve pointed at VizDoom RGB, scored against the labels-buffer ground truth)** | **THE EYE ON DOOM, SCORED AGAINST PER-PIXEL TRUTH — a LOW but HONEST baseline with FOUR walls quantified (PROBE, DEGRADE-as-expected; the ground truth the real-video chain 145000–150000 never had).** The shipped carve (`native.segment` value + `native.segment_motion` common-fate, byte-identical) on greyscaled+downsampled `defend_the_center` RGB (60×80 grid, L∈{4,8}, seed 152000, headless RES_320X240), regions read from the graph via `within` edges and scored by IoU vs VizDoom's labels buffer + `object_id` continuity. **RGB-only enemy IoU (value L4): 0.243 turning / 0.018 stationary** (recall@0.1 0.82, @0.25 0.56, @0.5 0.13 turning; raw dist 14×0 / 20 / 34 / 10 over n=78 — a real spread, not usable). **FOUR WALLS, with numbers:** (1) **SUB-GRID RESOLUTION dominates** — the enemy is 55–71 px (<0.1% of frame) → median **2 grid cells** at rest, GONE in 40/51 frames; IoU is 0.000 below 3 cells and a flat ~0.25 plateau at ≥3 cells (the stationary↔turning gap is enemy SIZE, not carving/egomotion — IoU-vs-area table proves it); (2) **the WEAPON SPRITE is a persistent false object** — carved at IoU ~0.25, **~14× better than any enemy at rest**; (3) **background texture OVER-SEGMENTS and finer grain SHATTERS it** — non-ground regions/frame 8→**328** L4→L8, ~all false positives, enemy IoU unrescued (Omniglot's "finer grain fragments" again; L4 is the operating point); (4) **egomotion HURTS common-fate** — motion-carve 0.159 < value-carve 0.243 under turning, L8 motion 0.094. **TRACKING FRAGMENTS even when carving works** — one `object_id` split across mean 2.75 (max 4) carve-ids, 8.0 (max 14) at L8 — the 150000-named carve/track-fragmentation wall, now scored. **DEPTH — the free lever — DID NOT pay off** (enemy IoU ≈0.00; 4× area-mean washes out the enemy's depth contrast; depth carves only big stable geometry). WHAT I GOT WRONG: predicted depth>RGB (false); designed `stationary` as the clean baseline (enemies sub-grid at rest, so it mostly measures wall 1); nearly reported the size confound as egomotion. Architecture audit CLEAN: no Rust, no seed, no default moved; VizDoom driver is a world adapter; labels buffer is the oracle, never fed to the eye; scored by POSITION not region-id. shared engine `3a66c0636a98` (source_match==shared, no Rust); oracle **222/0 BEFORE and AFTER**; gate `test_eye_on_doom_migrated` **7/7** (scorer correct on a constructed synthetic case — able to fail; end-to-end VizDoom→carve→score, skips explicitly if VizDoom absent); §9 byte-identity — new files only; `SEED CLAIM 152000-152999 CLEAN`. Raw: `results/eye_on_doom.json`, `results/eye_on_doom_imgs/` (RGB\|labels\|carve triptychs); `VISION_EYE_ON_DOOM_RESULTS.md`. NAMED NEXT LEVERS: egomotion compensation (148000's P-frame search) on the turning common-fate carve; appearance-tracking (151000) to hold one enemy as one trajectory; a grid/scale lever for the sub-grid wall (enemy must exceed ~3 cells). |
