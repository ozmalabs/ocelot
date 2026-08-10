# PHASE-FIELD PROTO-OBJECTS — PRE-REGISTRATION

*Committed BEFORE any confirmatory number. Seeds **114000–114999**. Term enum
index reserved **180** (allocated; used only if the median moves and a build is
warranted). This rung CHARACTERISES IN NUMPY FIRST and builds nothing unless
the size distribution moves off the value-flood's median-1.*

## 0. THE QUESTION — the object ladder's own terminus

Four rungs (mint / value-admissibility family / peer-competition / aperture)
eliminated the obvious blockers of "baby objects: FEW and LARGE" by measurement.
The measured conclusion: **the enclosed-component field is MEDIAN-1 at every
grain from 3 to 72, on both corpora, BEFORE ANY PREDICATE SEES IT** — because a
natural equal-value connected component big enough to be an object is either not
equal-valued or it is the ground. Every lever moved the COUNT (13–151×) and left
the MEDIAN at 1.

**The open question the object line converged on: is the blocker the
REPRESENTATION the material is read into?** The value-flood reads a proto-object
as a connected component of EXACTLY-EQUAL luminance — which fragments because
natural frames have almost no exactly-equal adjacency at fine grain.

**The wavefield alternative (this rung):** a proto-object is a region bounded by
**phase-congruent contours** (Kovesi). A feature sits where the Fourier
components across scales are maximally IN PHASE — constructive interference,
**contrast-invariant**. A phase-congruent contour is EXTENDED by construction
where an equal-value boundary is not. Regions = 4-connected components of the
NON-edge cells. The motion-energy rung (index 179) established the load-bearing
capability: **the wave transform CONSUMES THE RAW BOUNDED RASTER, no
figure/ground split** — and that magnitude-only is BLIND, the information lives
in PHASE. Phase congruency reads phase by construction.

## 1. HYPOTHESIS (two-sided)

**H1:** Segmenting the frame into phase-congruent-contour-bounded regions moves
the region SIZE DISTRIBUTION off the value-flood's median-1.
**H0 (the negative that closes the wave hypothesis for objects):** the region
size median stays at 1 (the representation is not the lever either), OR it moves
off 1 only by collapsing to ≈1 giant region (background-swallow, not
objecthood).

## 2. THE STATISTIC, EXACTLY

Per frame, whole frame **L=72** (the aperture-free grain where the value-flood
STILL gives median-1 and large regions have the best chance):

1. `PC` = Kovesi **monogenic phase congruency** map in [0,1], noise-compensated,
   reflect-padded by PAD=24 then cropped (kills the FFT wrap contour).
   `scripts/phasefield_pc.py::phase_congruency`.
2. `edges = PC > thr`; `regions = ndimage.label(~edges, 4-connectivity)`.
3. **Region sizes**: all regions; and **enclosed** regions (containing no
   frame-border cell — the value-flood's own enclosed definition).
4. **Primary statistic**: the per-frame **median enclosed-region size**,
   bootstrapped (10 000×) over **frames** (unit of analysis = FRAME, PROTOCOL
   §4), 95% CI. Secondary: all-region median; per-frame region count.

**Threshold** — the verdict rides only on the two §13-clean operating points,
both of which FALL OUT:
- **`noise0`**: `PC > 0` — above the Rayleigh noise floor (the noise mean/sigma
  are the Rayleigh moments of the smallest-scale amplitude; derived, not picked).
- **`otsu`**: Otsu on the PC map — falls out of the histogram.
The **edge-density ladder** {0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50} is
an ENUMERATION of the threshold axis, reported in full, none selected.

**nscale** enumerated {3, 4, 5} (primary 3 — on a 72px frame the coarsest
wavelength 3·2.1²≈13px stays local; 5≈frame-size, reported as degenerate).
Kovesi's filter-bank constants (minWaveLength=3, mult=2.1, sigmaOnf=0.55,
cutOff=0.5, g=10) are the imported log-Gabor MECHANISM, declared CONFIGURATION.

**THE MAGNITUDE TRAP, PRE-REGISTERED AS THE NEGATIVE.** A magnitude-only reading
throws away phase = arrangement. I include `LE` = local monogenic **energy
magnitude** (same log-Gabor bank, NO sum-of-amplitudes phase normalisation,
contrast-DEPENDENT) as the negative comparator, identical pipeline. **If LE moves
the size median as much as PC, PHASE is not the lever and the PC result does not
support H1** (the effect is generic multi-scale contour segmentation, not phase).

## 3. THE BASELINE, ON THE IDENTICAL FRAMES

Value-flood at L=72, k=16, tau=0, the same 30 frames: all-comp median, enclosed
median (expected 1 per the enclosure rung), and per-frame component count. The
`1` the PC median is compared against is this **reproduced incumbent result**,
not a chosen constant. The published floor **5047 (C1) / 3978 (C2)** is asserted
in-run (7 SAMPLED_FRAMES, REGION=18) — the run VOIDS if not reproduced (verify
the PRODUCT).

## 4. n, FIXED IN ADVANCE

**30 frames per corpus** (`FRAMES_WIDE = range(0,150,5)`), inherited verbatim
from the enclosure rung, unit of analysis = FRAME. Not chosen from the effect
(the confirmatory PC-region statistic on C1/C2 has not been computed at prereg
time; only synthetic positive-controls and the value-flood floor have). If the
effect is median-1 vs median≫1 it is hugely powered; if median-1 vs median-2 the
CI will say so. No re-run, no sweep beyond the enumerated ladders.

## 5. DECISION RULE (including the null)

At **both** §13-clean operating points (`noise0` AND `otsu`), at nscale=3
(primary; 4 reported for robustness):

- **CONFIRM (H1):** enclosed-region median **CI lower bound > 1** (CI-separated
  ABOVE 1) AND **non-degenerate** — per-frame region count median ≥ 3 (a
  segmentation, not one blob) AND materially FEWER regions than the value-flood's
  per-frame component count (the object line's "FEW and LARGE" target) AND `PC`
  beats `LE` (LE does not reproduce the same median shift). Size distribution
  CI-separated above the value-flood's median-1.
- **FALSIFY (H0):** enclosed-region median CI **includes 1** at noise0 and otsu →
  the representation is not the lever; **the wave hypothesis is CLOSED for objects**
  the way the motion rung closed it for phi. STOP; build nothing.
- **DEGENERATE (negative-for-objects):** median moves off 1 only with region
  count median ≤ 2 (one giant region swallowing the frame) → background-swallow,
  not objecthood. Reported as a negative; build nothing.
- **AMBIGUOUS:** noise0 and otsu disagree, OR the median CI straddles 1, OR the
  sign flips between nscale 3 and 4, OR PC ≈ LE. Reported as ambiguous; a build
  needs a new prospective prereg.

**Only CONFIRM warrants building the index-180 Term.** Anything else STOPS
(the four-rung precedent: the cheap diagnostic kills the mechanism before a line
of Rust).

## 6. MY PREDICTION, STATED IN ADVANCE (with provisos)

**I predict CONFIRM is MORE LIKELY THAN NOT (~55%)** — this is the first lever
that changes the ADJACENCY PREDICATE from dense (exact-value equality, a
boundary at every quantizer step) to sparse (only at feature contours), so
regions have a real mechanism to be large. **Provisos that would break it:**
(a) natural texture makes PC fire densely everywhere → regions fragment back to
median-1 (the FALSIFY path); (b) phase-congruent contours are gappy/open → the
flood leaks through and everything becomes 1 giant region (the DEGENERATE path);
(c) LE reproduces the shift → the effect is generic contour segmentation, not
phase (AMBIGUOUS). If (a) fires, the arc's "median-1 is in the material" thesis
extends even to the wavefield representation — the strongest form of the object
line's negative. **Being wrong about which proviso breaks tells me what I did
not understand about natural-frame phase statistics.**

## 7. CONTROLS (dead-instrument arms must fire)

- **Uniform field** → `PC max == 0.0` (no congruency; verified: 0.0000).
- **Ideal disc** → PC bounds it → ~2 large regions (verified on synthetic:
  2 regions, median in the hundreds).
- **Speckle** (100 iid uniform fields, seeds **114000–114099**) → structureless
  input; the null. `0/100` is NOT copied forward — the peer rung's speckle rate
  is **≈0.6% [0.17, 2.25]**; this arm is distributional.

## 8. SEEDS — 114000–114999

- **114000–114099**: 100 iid speckle fields (control). **BURNED.**
- **114100**: the bootstrap resampler `default_rng`. **BURNED.**
- 114101–114999: not drawn. **CLEAN.**

**Verbatim `check_claim(114000, 114999)` at prereg time (clause 8):**

```
SEED CLAIM 114000-114999: CLEAN -- no collision DETECTED.
  Scope: 816 files with seed sinks; 509 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 9. §13 / provenance / gates

- Engine built in-tree (`scripts/engine_build.sh`, **`e039d2eec2dd`**),
  provenance printed from INSIDE the measuring process and asserted ==
  `EXPECT_ENGINE`, re-verified after the measurement.
- No Rust, no seed, no default moved unless CONFIRM. §9 byte-identity holds by
  construction for a characterisation.
- Oracle `scripts/rung7_vision_bench.sh` before AND after.
- `python3 -m domains.seed_record --write` if seeds land.
- Every verdict compares a bootstrapped median CI against the **reproduced**
  value-flood median (a measured incumbent), or a region count against the
  value-flood's (measured). Thresholds are the noise-floor (0) and Otsu (both
  fall out); nscale and the density ladder are enumerations.
