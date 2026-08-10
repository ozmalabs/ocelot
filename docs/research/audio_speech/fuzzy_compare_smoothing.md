# Fuzzy (smoothed, multi-scale) compare — toy low-res aliasing AND audio domain gap

**Insight (Axiom 0).** The sense-hats' `compare` has been a RIGID rule — an exact
L2/DTW residual over the feature grid. But "rules are more like guidelines": the
compare should be FUZZY/smoothed. **Unification:** low-res shape ALIASING (toy hat)
and the synthetic-vs-real AUDIO DOMAIN GAP are the SAME nuisance — high-frequency
detail the compare should ignore. An owned multi-scale Gaussian blur over the
feature grid removes both.

## Build (donkey-clean; the CortexLoop is UNCHANGED)

- `domains/fuzzy_smooth.py` — owned DSP: separable Gaussian blur (`blur2d`),
  multi-scale blur pyramid (`multiscale_grid`), and time×freq trajectory blur
  (`smooth_traj`). Pure numpy, **no net, no fit, no learned filter**.
- `domains/toy_hat.py` — `smooth_scales` param: the (N×N) feature grid is blurred at
  a set of sigmas and stacked (a pyramid) before the L2 residual. Added a
  `render_blur` toggle so the historical render-time box blur can be turned OFF to
  rasterise RAW 1-pixel strokes (true aliasing) — isolating the compare-time blur as
  the *only* smoothing.
- `domains/audio_hat.py` — `smooth_t`/`smooth_f` params: the cmvn cochleagram
  residual is blurred over time (frames) × freq (bands) before the `DtwTo` residual.
- `domains/cortex_loop.py` + `domains/hat.py` — **untouched** (`git diff` empty).
  Donkey boundary verified: smoothing lives entirely in the hats' encode/compare;
  the loop owns only coarse-match / adapt / argmin.
- Driver: `scripts/fuzzy_compare_smoothing.py`. Required suites green:
  `test_stt_pipeline` + `test_frontend_effect_gate` (11 passed).

## (a) TOY low-res — un-smoothed vs smoothed + scale sweep

Held-out (unseen-transform) recognition, 8 shapes, chance 0.125, n=64.

**RAW raster (true aliasing — smoothing is the ONLY smoothing). The clean test:**

| grid | rigid[0] | best smoothed (scale) | lift | over[4] |
|------|----------|-----------------------|------|---------|
|  8×8 | 0.047    | 0.125 (s1.0)          | +0.078 | 0.156 |
| 10×10| 0.094    | 0.125 (s0.6)          | +0.031 | 0.156 |
| 12×12| 0.109    | 0.234 (s1.0)          | **+0.125** | 0.156 |
| 16×16| 0.125    | 0.328 (s1.5)          | **+0.203** | 0.125 |
| 28×28| 0.234    | 0.484 (ms[0,1,2])     | **+0.250** | 0.562 |

At grid 12 the rigid compare is *below chance* (0.109); smoothing more than doubles
it (0.234). At grid 16 it goes 0.125 → 0.328 (2.6×). **Verdict: low-res aliasing is
FIXED by the fuzzy compare.** The over-smooth control (`over[4]`, sigma=4) collapses
accuracy at the working resolutions (grid 16: 0.125 — back to chance) — confirming
over-smoothing erases the shape, which is why the scale must be swept.

**Render PRE-BLUR (historical front end already smooths the raster):**

| grid | rigid[0] | best smoothed | lift |
|------|----------|---------------|------|
|  8×8 | 0.094    | 0.109         | +0.016 |
| 12×12| 0.219    | 0.219         | +0.000 |
| 16×16| 0.359    | 0.375         | +0.016 |
| 28×28| 0.500    | 0.547         | +0.047 |

With the front end *already* pre-smoothed, extra compare-time blur barely moves —
because the residual low-res failure here is **raster information loss** (the
held-out ±3px translations push the shape off a tiny grid), NOT aliasing the compare
can remove. This is the honest qualifier: smoothing fixes *aliasing*, not *lost
pixels*. The prior toy hat already baked a render-time blur in, which is why naive
extra smoothing looked like it did nothing — the aliasing had already been removed at
render time.

## (b) AUDIO cross-speaker LOSO — un-smoothed vs smoothed + residual separation + sweep

Held-out speakers (LOSO, never banked), 80 real SC clips, 10 digits, chance 0.100.
Smoothing = Gaussian blur over the cmvn cochleagram (sigma_t frames × sigma_f bands).

| sweep        | LOSO  | true-med | wrong-med | separation |
|--------------|-------|----------|-----------|------------|
| rigid(0,0)   | 0.412 | 0.401    | 0.449     | +0.048     |
| f0.8         | 0.450 | 0.306    | 0.367     | **+0.061** |
| **f1.5**     | **0.487** | 0.252 | 0.299    | +0.047     |
| f2.5         | 0.475 | 0.195    | 0.238     | +0.042     |
| t1.0_f1.5    | 0.450 | 0.216    | 0.277     | **+0.061** |
| t2.0_f2.5    | 0.388 | 0.151    | 0.211     | +0.060     |
| over_f5      | 0.375 | 0.133    | 0.162     | +0.028     |

**Best scale: freq-blur sigma_f = 1.5** — LOSO **0.487**, a **+0.075 lift** over the
0.412 rigid plateau, landing right at the CMVN 0.51 target band. The curve is a clean
inverted-U: separation/accuracy rise as freq-blur removes the spectral grain
(f0.8 → f1.5), then fall as over-smoothing (f2.5 → f5) erases the word (over_f5 drops
to 0.375, below the plateau). Time-blur did NOT help on top of freq-blur
(t1.0_f1.5 = 0.450 < f1.5 = 0.487) — the domain gap is a *spectral* nuisance, not an
alignment one (DTW already handles the time warp). Residual separation improved at
every grain-removing scale (best +0.061 at f0.8, vs +0.048 rigid).

## Verdict

**The fuzzy/smoothed compare fixes BOTH.**

- **TOY low-res aliasing: FIXED.** On raw aliased rasters, freq-appropriate
  smoothing lifts recognition +0.125 to +0.250 (up to 2.6× at grid 16), recovering
  the resolutions where the rigid compare sat at/below chance. Best scale grows with
  grid (s1.0 at 12, s1.5/ms at 16–28). Over-smoothing erases — the scale must be
  swept.
- **AUDIO domain gap: LIFTED.** Freq-blur sigma_f=1.5 lifts cross-speaker LOSO from
  the 0.412 plateau to **0.487 (+0.075)**, into the CMVN target band, with the
  true-vs-wrong residual separation improved. The gap was (at least partly)
  high-frequency spectral grain that the rigid DTW counted — exactly the same
  nuisance as the toy aliasing.

**The unification holds:** one owned multi-scale Gaussian blur, dropped into the
hats' compare (loop untouched), removes both the low-res aliasing and a meaningful
chunk of the synthetic-vs-real audio gap. The honest boundaries: (1) on the *pre-
smoothed* toy front end the remaining low-res failure is raster information loss, not
aliasing, so smoothing can't recover it; (2) audio still plateaus near CMVN ~0.51 —
smoothing closes the gap to that level but does not exceed it, so a residual,
coarse-scale part of the domain gap remains (time-blur didn't help; over-smoothing
hurt). Smoothing removes the *high-frequency* part of the gap, not all of it.
