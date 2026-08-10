# REAL-VIDEO EYE PROBE — RESULTS: **PERCEPTION BREAKS ON REAL VIDEO — at the CARVE. The equal-value eye shatters a naturally-textured object into 100-500 regions per frame (68-92% of them 1-2 cell speckle), while the white background floods into ONE region. The ~7-9% synthetic confab becomes 68-92% on real texture. Tracking is NOT the wall — for the fragments that exist, continuity is genuine — but no OBJECT ever holds one region, so the physics-discovery precondition (one object = one Region trajectory) fails. First wall, named with numbers: TEXTURE OVER-SEGMENTATION.**

Pre-registration `VISION_REAL_VIDEO_PROBE_PREREG.md`, committed **`bf1db27d55`**
BEFORE any carve/track/confab number. Honest exploratory probe, NO CONFIRM
target — both discriminator outcomes are a result. The outcome is
**"perception breaks,"** located exactly, with the first fix named.

## What was fed — REAL footage, greyscaled + heavily downsampled (stated)

- **Clip:** `naming_corpus/ABC_Phonics_Chant_for_Children_Sounds_and_Actions_from_A_to_.mp4`
  — a GENUINE educational YouTube video: a REAL woman presenter in a blue shirt
  on a white studio background, moving her arms/head/torso doing phonics actions,
  with an animated letter "F" overlay. 854×480, 30fps. This is real footage of a
  real moving person — **not a synthetic stand-in, not a black-background
  single-bright-object cheat.**
- **Window:** `t=50.0s`, 4.0s → **15fps → 60 frames**. VERIFIED cut-free
  (max inter-frame mean-abs-diff **18.9 < 20**; mean 5.2) with continuous arm
  motion throughout — chosen for MOTION (the prerequisite of a tracking test),
  not for an easy carve.
- **Preprocessing (honest sim-vs-real caveat):** ffmpeg
  `fps=15,scale=64:36,format=gray`. **GREYSCALED** (luma only; colour discarded)
  and **HEAVILY DOWNSAMPLED** 854×480 → **64×36 grid** (2304 cells). The frames
  are REAL; what the eye sees is real-but-toddler-resolution-grey. I say so.
- **Quantization:** the eye's native scheme `v = (luma·L)//256` → L distinct grey
  levels, swept **L ∈ {4, 8, 16, 32}** (L=4 = the eye's shipped
  `downsample_quantize` default). Deterministic; no RNG drawn.

## The eye — UNCHANGED (NO Rust, NO seed; a measurement/EMIT probe)

`Substrate::segment_and_track` via `native.segment`, driven by the EXISTING
`domains/falling_world.py` harness (`boot_falling`/`setup_world`/`read_regions`)
— the same code the physics gates use. Segmentation is union-find over 4-connected
cells of **exactly-equal integer value**; cross-frame identity by overlap then
velocity-predicted nearest-same-value centroid within `span+2`. New code is a thin
video→grid adapter (`scripts/real_video_eye_probe.py`) — admissible I/O. No Rust
was needed or written.

## 1. CARVING — over-segmentation of the object, flood of the background (BOTH)

Every number read from the graph (`read_regions`), per frame, over 60 frames.
The scene has ≈1-2 salient real objects (person; background; intermittent overlay).

| L | regions/frame (mean, max) | non-ground/frame (mean) | ground fraction (largest region) | speckle (≤2 cells) /frame | **speckle fraction of all regions** | wall ms/frame |
|---|---|---|---|---|---|---|
| **4** (default) | 114.2 (145) | 113.2 | **0.74** | 78.1 | **68.4 %** | 1.2 |
| 8 | 251.9 (299) | 250.9 | 0.70 | 201.2 | **79.9 %** | 2.2 |
| 16 | 397.8 (456) | 396.8 | 0.69 | 338.3 | **85.0 %** | 3.5 |
| 32 | 529.2 (605) | 528.2 | 0.68 | 488.4 | **92.3 %** | 5.5 |

- **~1 object → 113-528 regions.** The person shatters into HUNDREDS of pieces at
  every quantization. There is no L that carves her as one region.
- **BOTH failure modes at once.** The white background under-segments (FLOODS into
  ONE region covering 68-74 % of the field — the eye's known equal-value flood),
  while the textured foreground over-segments (shatters into confetti). This is
  visible in `results/real_video_carve.png` (one flat background colour; the
  person a spray of tiny regions).
- The largest NON-ground region is median **153 cells** (the blue shirt, a
  high-contrast near-uniform patch that DOES flood into a blob) with a long tail
  of speckle — but even it is a body PART, and it is not stably trackable (below).
- A numpy replica of the exact equal-value carve reproduces the eye's counts
  (L=4 f10: 93 vs eye range; L=16 f10: 396 vs eye mean 398) — confirming the carve
  is understood, and **the carve is fully deterministic (60/60 frames byte-identical
  region-size multiset across two runs).**

## 2. CONFABULATION — the untested ~7-9 %, finally exercised, becomes **68-92 %**

On real natural texture the fraction of carved regions that correspond to NO real
object (1-2 cell speckle — texture/JPEG/edge artefacts) is **68 % (L=4) → 92 %
(L=32)** — the robust, deterministic, per-frame speckle fraction above. An
id-lifetime-based confab proxy corroborates (0.80-0.97) but is the weaker measure
(it is partly contaminated by id recycling, §5). Either way: **the ~7-9 %
confabulation measured on synthetic clean pixels is an order of magnitude larger
on real input.** The overwhelming majority of what the eye "sees" on real video is
texture confabulated into phantom regions.

## 3. TRACKING — NOT the wall; the tracker faithfully tracks the wrong primitives

For the regions that DO exist, cross-frame continuity is genuine:

- **false-persist rate 2-6 %** — when a region persists across two consecutive
  frames, its centroid stays within 3 cells (a real continuous hop) 94-98 % of the
  time. The velocity-predictive matcher is not the bottleneck.
- **genuine continuous tracks exist:** 18-44 non-ground, non-speckle regions are
  tracked (centroid-continuous) for ≥4 consecutive frames; the longest genuine
  single-region track runs **51-59 of 60 frames**.
- **but the stably-tracked regions are speckle / tiny sub-features.** The longest
  non-ground true tracks are mostly 1-cell points (med_cells 1) or ~10-cell
  fragments — stable precisely because they barely move. The one large object-ish
  region (the ~150-505 cell shirt) is NOT stably tracked: it deforms/merges/splits
  as she gestures, breaking centroid continuity. **The eye tracks a texture speck
  for the whole clip and loses the object every few frames.**

Conclusion: tracking works on whatever it is given; the failure is entirely
upstream in the carve. Fix carving before touching tracking.

## 4. FIRST WALL — ranked

1. **TEXTURE OVER-SEGMENTATION (the wall).** Equal-value 4-connected union-find
   has no notion of an object — only of flat iso-value patches. Real luminance is a
   continuous gradient, so a textured object fragments into 100-500 regions and the
   background floods into one. Root cause, not a tuning artefact: the synthetic
   worlds worked *because* they were piecewise-constant 0/1 fields, where
   exact-equality IS the object boundary. On natural texture it is catastrophic.
2. **Confabulation** (68-92 % speckle) — a direct consequence of (1), not a
   separate mechanism.
3. **Background flood / low-contrast** — the same defect on the uniform side
   (68-74 % of the field is one region).
4. **Object-level tracking** — NOT reached as a wall (continuity is genuine); it is
   starved of object-level regions to track.
5. **Scale / compute** — NOT the wall at 64×36: 1.2-5.5 ms/frame (well under
   real-time). The O(N²) scale wall from earlier assembled-eye probes lives in the
   heavier SAD/parallax path, not in this bare union-find segmenter. It would bite
   only at much higher resolution.

## 5. COULD THE LEARNING LOOP RUN? — substrate exists, but attaches to a speck

There ARE stably-tracked non-speckle regions (§3), so the order-N / discovery loop
would find SOMETHING to attach to — but it would attach to a ~10-cell texture
fragment's near-static trajectory, not to the person. The precondition that made
`PHYSICS_FALL_FROM_EYE` work — **one object ⇒ one Region whose centroid traces the
object's motion** — is NOT met on real video, because the object is 100+ regions
and its one large piece deforms out of continuity. Perception is not too broken to
produce a tracked trajectory; it is broken enough that no tracked trajectory is an
object's. **No forced physics discovery was attempted** (correctly — there is no
object track to discover physics from).

## 6. VERDICT

**PERCEPTION BREAKS on real video**, at the carve, with numbers:
~1 object → **113-528 regions/frame**, **68-92 % speckle confab**, background
flooded to **one 68-74 % region**, and **no object ever held as one region**. The
eye that carves a clean synthetic blob perfectly cannot carve a real textured
object at all. This is a good result — the wall is named.

**The first fix** (named, not built): the carve needs an object notion beyond
exact iso-value connectivity — luminance-SIMILARITY region growing (threshold /
gradient) rather than exact equality, edge-bounded segmentation, or the
motion-common-fate / grounded-contour grouping the memory notes already point to
(`VISION_EYEVIEW`'s parallax `group_common_fate`). Exact-equality union-find is
correct on piecewise-constant synthetic worlds and wrong on natural texture; that
gap IS the distance between "toddler eye on a clean blob" and "perceives real
video."

## 7. PROVENANCE / DISCIPLINE

- Worktree branch **`worktree-agent-a506315cbf8accc6f`** (NOT main); prereg commit
  **`bf1db27d55`** BEFORE any number.
- Engine **`ac8625525b09`**, **`source_match = shared`** (Rust source fingerprint
  identical to this worktree's build `dfc1402d15eb`; NO Rust changed by this rung).
  Provenance gate its OWN step: `test_engine_provenance_migrated` **7 passed**.
- ORACLE `scripts/rung7_vision_bench.sh` (data/ symlinked): **BEFORE 222 passed /
  0 failed**; **AFTER 222 passed / 0 failed** (§9 trivial — no Rust/Term/seed).
- SEED CLAIM 143000-143999 header (verbatim):
  `SEED CLAIM 143000-143999: CLEAN -- no collision DETECTED.` The probe drew NO
  seed (deterministic decode + quantization + segmentation).
- Instrument seams `pytest -k migrated` (provenance + failure_baseline): **18
  passed**, no new red (the 3 pre-existing reds are not mine).
- Resolution **64×36 = 2304 cells**; per-frame wall **1.2-5.5 ms** (L=4→32).
  loadavg unchanged (`[5.98,5.90,3.87]`), OMP_NUM_THREADS=2.
- Machine-readable: `results/real_video_probe.json`. Visuals:
  `results/real_video_carve.png` (the shatter), `results/real_video_input.png`.

## 8. WHAT I GOT WRONG (in full)

1. **My first tracking metric (1-frame-ephemeral "churn") read 0.00 and would have
   said "tracking is fine."** It is CONTAMINATED: node ids are RECYCLED on death
   (verified directly — removed id 754 was reused by the next birth), so a raw
   node-id is not a stable object handle across real-video births/deaths. 95-99 %
   of ids appear non-consecutively (recycled-id collisions across gaps). I caught
   this, marked the raw-id metrics `_RAWID`, and recomputed tracking by CENTROID
   continuity (false-persist 2-6 %, true-consec runs) — which is what §3 reports.
   Lesson re-learned: check every read-back; a stable-looking id count can be an
   allocator artefact.
2. **The id-lifetime-based confab proxy (0.80-0.97) is likewise partly
   recycling-contaminated** (recycled ids inflate lifetime, so fewer flagged
   ephemeral → it slightly UNDER-counts). I demoted it to corroboration and lead
   with the robust, deterministic per-frame speckle fraction (68-92 %).
3. **A JSON field I first eyeballed, `modal_main_id = [3171, 11]`, is (id,
   frame-occurrences), NOT (id, cell-count).** I misread "11" as a cell count and
   nearly reported the largest object piece as ~11 cells; the correct largest
   non-ground region is median **153 cells**. Corrected by direct measurement.
4. **Id-assignment is non-deterministic across processes** (Rust HashMap
   RandomState in the matcher tie-breaks) — confab_obs wobbled 0.76↔0.80 between
   runs. The CARVE is deterministic (60/60 identical); only the id/track layer
   wobbles a few %. Reported, not hidden; the headline confab (speckle fraction) is
   on the deterministic carve.
5. **The clip has a white studio background.** Not engineered — it is what the
   ordinary footage is — but it makes the background-flood finding partly a
   property of THIS clip. The over-segmentation of the FOREGROUND (the real
   finding) is independent of the background and would hold on any natural texture.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine | oracle before/after | verdict |
|---|---|---|---|---|
| real-video eye probe | The equal-value eye (`segment_and_track`) on a real 60-frame cut-free window of natural video (moving presenter, 64×36 grey): ~1 object carves into **113-528 regions/frame**, **68-92 % of them ≤2-cell speckle confab** (the synthetic ~7-9 % ×10 on real texture), background floods to **one 68-74 % region**; tracking continuity is genuine (false-persist 2-6 %) but **no object ever holds one region** so the physics-discovery precondition fails; wall 1.2-5.5 ms/frame (scale not the limit here). First wall = **TEXTURE OVER-SEGMENTATION**; first fix named (similarity/edge/common-fate carve). Node-id recycling verified and corrected for. | `ac8625525b09` (shared, source-identical; NO Rust) | 222/0 → 222/0 | **PERCEPTION BREAKS at the carve** (honest wall, numbered) |
