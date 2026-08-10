# REAL-VIDEO EYE PROBE — pre-registration

**HONEST EXPLORATORY PROBE — no CONFIRM target.** Point the low-resolution eye
that works today (`Substrate::segment_and_track`, reached via `native.segment`)
at REAL natural video for the first time and MEASURE which wall it hits first.
Everything proven so far is SYNTHETIC integer-exact (clean 0/1 pixel worlds); the
~7-9% confabulation and the whole carve+track pipeline are UNTESTED on real
natural texture / real motion / real noise. This probe exercises them. **All
outcomes are the result** — "perception survives, bounded" and "perception
breaks" are BOTH good findings. The failure I must not commit is dressing a
broken carve as working, or tuning the clip to fake a clean carve.

## The eye under test (unchanged — NO Rust, NO seed)

`Substrate::segment_and_track` (`runners/dsl/src/substrate.rs`), reached via
`native.segment(game, h, w, values, cell_ids)` (`py.rs` ~3080). Segmentation is
**union-find over 4-connected cells of EXACTLY EQUAL integer value**; each region
matched cross-frame to a prior `Region` NodeID by overlap (≥50%) then
velocity-PREDICTED nearest-same-value centroid within `radius = span+2` (the
Phase-B fix, `PHYSICS_FALL_FROM_EYE_FIX_RESULTS.md`). Region attrs read from the
graph: `cy/cx/drow/dcol/count/is_ground/rvalue`. I reuse the existing harness
`domains/falling_world.py` (`boot_falling`, `setup_world`, `read_regions`) — the
SAME code the physics gates drive — feeding real-video value grids in place of
`fall_pixels`. This is a measurement/EMIT probe: a thin video→grid adapter is the
only new code (admissible I/O). **If I reach for Rust, I stop and report why.**

## The input — REAL footage (stated sim-vs-real honesty)

- **Clip:** `naming_corpus/ABC_Phonics_Chant_for_Children_Sounds_and_Actions_from_A_to_.mp4`
  — a genuine broadcast/YouTube educational video: a REAL woman presenter in a
  blue shirt on a white studio background, moving her arms/head/torso doing
  phonics actions, with an animated letter "F" overlay. 854×480, 30fps, 262s.
  This is real footage of a real moving person, NOT a synthetic stand-in and NOT
  a black-background single-bright-object cheat.
- **Window:** start `t=50.0s`, duration `4.0s`, resampled to **15fps → 60
  frames**. Verified CUT-FREE (max inter-frame mean-abs-diff 18.9 < 20 cut
  threshold) with steady continuous motion (mean inter-frame diff 5.2). The
  presenter's arms move continuously through the whole window; no scene cut.
- **Preprocessing (honest, stated):** ffmpeg `fps=15,scale=64:36,format=gray` —
  **GREYSCALED** (luma only; colour discarded, per "luminance is structure") and
  **HEAVILY DOWNSAMPLED** from 854×480 to a **64×36 grid** (2304 cells; the eye
  cannot do real resolution real-time). Aspect-preserving (64/36 = 1.78 ≈
  854/480). The real footage is therefore seen by the eye at toddler resolution
  in grey — REAL frames, greyscaled + heavily downsampled. I say so.
- **Quantization → values (the eye's native scheme):** the eye clusters only
  EXACTLY-EQUAL values (union-find), so the number of grey LEVELS is the decisive
  lever. The eye's own `downsample_quantize` default is `levels=4` per channel.
  I quantize luma to L levels as `v = (luma * L) // 256` and **sweep
  L ∈ {4, 8, 16, 32}** — L=4 is the eye's shipped default (PRIMARY); the sweep IS
  the carve-quality finding (coarse→flood/under-seg vs fine→shatter/over-seg on
  natural texture). Deterministic; no RNG.

## What I MEASURE (read from the graph, per frame, never eyeballed)

For each L and each of the 60 frames, drive `native.segment` then `read_regions`:

1. **Carving quality.** `n_regions` total; `n_nonground`; ground fraction
   (largest-region cells / 2304); region-size distribution incl. count of
   speckle regions (count ≤ 2 cells). Real objects in scene ≈ 1-2 salient
   (person; background; intermittent letter overlay). OVER-segmentation ⇔
   `n_nonground` ≫ 2 with many speckle; UNDER-segmentation ⇔ whole frame ≈ 1-2
   giant regions. Tie low-carve-quality to the eye's known failure modes
   (equal-value flood; low-contrast).
2. **Tracking persistence.** Per-Region-id lifetime = number of consecutive
   frames the id survives (via `longest_continuous_run`-style adjacency).
   Report the lifetime distribution, the max lifetime, and CHURN = fraction of
   ids that live exactly 1 frame (born→die). Does velocity-predictive matching
   help, or does non-translational / occluding / deforming real motion break it?
3. **Confabulation proxy (the untested ~7-9%, exercised on real input).** No
   per-cell ground truth exists on real video, so I report an HONEST PROXY:
   fraction of carved regions that correspond to no stable real object =
   ephemeral (1-frame) OR speckle (count ≤ 2). Stated explicitly as a proxy, not
   the synthetic ground-truth confab.
4. **First wall — ranked.** Which breaks first: texture over-segmentation,
   tracking churn, contrast/flood, or scale? The honest bottleneck between
   "toddler eye on a clean blob" and "perceives real video."
5. **Could the learning loop even run?** Is there ANY id persisting ≥ `MIN_ORBIT`
   (=4) frames with coherent (non-speckle) size — a substrate the order-N /
   discovery loop could attach to — or is perception too broken to feed it? I do
   NOT force a physics discovery; I only assess whether the substrate exists.

Per-frame wall-clock and the 64×36 resolution are recorded (the scale reality).
Products verified via `read_regions` graph read-back (attrs), not process waits.

## Discriminator (registered BEFORE any number — all outcomes are the result)

- **"Perception survives, bounded":** at some L the eye carves + tracks at least
  one real coherent object (the person) across ≥4 frames with one stable id, a
  measured confab-proxy rate, and a named dominant wall.
- **"Perception breaks":** real texture/motion shatters carving or churns
  tracking so badly no coherent object holds one id across ≥4 frames at any L —
  then the finding is exactly WHERE and WHY, with numbers, and the first fix.

I will NOT tune the clip for an easy carve and will report whatever the ordinary
footage does. Greyscale + downsample are stated preprocessing, not a cheat.

## Discipline / provenance (asserted in results)

- Worktree branch `worktree-agent-a506315cbf8accc6f` (NOT main); this prereg
  committed BEFORE any carve/track/confab number.
- Engine built by `scripts/engine_build.sh` in THIS worktree; provenance gate
  `test_engine_provenance_migrated` its own step; assert `source_match ∈
  {own, shared}`; record engine sha.
- ORACLE `scripts/rung7_vision_bench.sh` (data/ symlinked) **222/0 BEFORE and
  AFTER**.
- SEED CLAIM 143000-143999 header (verbatim):
  `SEED CLAIM 143000-143999: CLEAN -- no collision DETECTED.`
  The probe draws NO seed (deterministic decode + quantization + segmentation).
- `pytest -k migrated` on instrument seams (3 pre-existing reds, not mine).
- Report what I got WRONG.
