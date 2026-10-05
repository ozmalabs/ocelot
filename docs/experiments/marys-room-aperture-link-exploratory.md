# Mary's Room: aperture-relative minting and "link vs compress" — EXPLORATORY

Status: post-hoc and exploratory. Written after Arm C (P6 not supported) was
seen. Not preregistered; no frozen file, confirmatory number, or verdict changed.
Script: `scripts/marys_room_aperture_link.py`. Output:
`results/marys_room_aperture_link_exploratory.json`. Engine `b6a41e3bbba6`.
Pool HO_core (N = 302, 272 hue-scored); task target 0.95·A0 = 0.730 (A0 = 0.768).

## A. Is the minter's failure about aperture?

In this substrate, fuzzy matching is an aperture quotient
(`seeds/observer_aperture.json`): unresolved dimensions are projected to a
constant, resolved ones are quantised at grain ρ, then matched literally. Arm C
gave the minter one aperture family: Cartesian (RG, BY), uniform grain 1/s, with
magnitude resolved. Here the same minter runs under that family across 10 grains,
and under a direction-only aperture (magnitude quotiented away; grain on hue
angle), with and without minting.

| Aperture | Best configuration | Rate (bits/sample, incl. model) | Task acc. | Mean angle |
|---|---|---|---|---|
| Arm C raw LMS (b=6) | — | 18.64 | 0.754 | 3.38° |
| Arm C opponent (b=6) | — | 12.42 | 0.735 | 13.50° |
| Arm C learned VQ (k=64) | — | 19.56 | 0.776 | 10.36° |
| Cartesian + minter | s=200 (best of 10) | 17.96 | 0.717 (never reaches 0.730) | 4.81° |
| Direction, bin index | 45° | 3.00 | 0.798 | 13.18° |
| Direction, bin index | 15° | 5.00 | 0.798 | 4.39° |
| Direction, bin index | 5° | 7.00 | 0.798 | 1.37° |
| Direction + minter | 5° (27 minted) | 6.71 | 0.798 | 1.42° |

Findings:

- The direction-only aperture meets the task target at 3 bits per sample, and at
  ~7 bits it beats raw coordinates on angular error (1.4° against 3.4°) at about
  a third of the rate.
- The gain comes from the aperture, not from minting. Minting on the direction
  lattice is within about a bit of a plain bin index (6.71 vs 7.00 bits at 5°;
  worse at coarse grains). Its only advantage is skipping empty bins, which is
  an entropy-coding effect.
- The Cartesian minter never reaches the target at any grain. With magnitude
  resolved, intensity (Naka–Rushton) spreads each hue across many lattice
  points, so exact repeats are rare and are mostly of dim or saturated vectors.
- Caveat: the decoder reads only direction, so a direction-only aperture cannot
  lose task information. What it discards (brightness and saturation) is not
  scored. Accuracy above A0 (0.798 vs 0.768) comes from coarse bins snapping
  about 3% of labels, not from added information.

## B. Does exposure add something incompressible but linkable?

Mary holds four concept prototypes before exposure (the frozen theory anchors,
256 bits, already paid). Each experience is coded as an edge to one of them plus
a residual relative to her own prediction.

| Component | Measured |
|---|---|
| Edge: link agreement, theory vs eye | 86.4% of 302 |
| Edge: entropy of the eye's link | 1.65 bits |
| Edge: entropy of eye's link given her predicted link | 0.58 bits |
| Relinks among 272 scored (corrected / broken) | 27 / 9 |
| Residual angle vs her prediction (median / mean) | 3.64° / 8.21° |
| Coding eye angle at 1°: alone vs given her prediction | 8.49 vs 7.13 bits (fixed length) |
| Generic smooth calibration (Fourier in predicted hue × log td, fit on TRAIN) | does not transfer: best median 3.77°, K≥2 worse |
| Fit the published model class (Gaussian bands + Naka–Rushton, 7 params) to 93 TRAIN exposures | recovers 564/42, 534/36, 420/28, 512 exactly |
| Held-out error of that fit | median 0°, max 2.8e-13° over all 302, incl. reflectances, eyelid, metamers; zero at 547.84 nm |

Findings:

- In this model Mary does learn something from exposure: this eye's receptor
  parameters, which standard-observer research does not contain. It is not
  incompressible. Seven numbers (224 bits, learned once from 93 monochromatic
  exposures) reproduce every later experience exactly, including stimulus
  classes she never saw.
- The residual only looks unstructured relative to her CIE-based theory. A
  generic smooth correction in her own coordinates fails, but the right model
  class removes it completely. It was model misspecification, not novel content.
- The edge is real but small, and it is compression with a prepaid codebook.
  Relative to her predicted concept, the experienced link carries about 0.6 bits
  per experience before calibration and 0 after. Arm C's learned codes failed
  because they had to pay for their codebook; Mary's concepts were paid for
  before release.
- Scope: this test cannot find genuinely incompressible content. The eye is
  deterministic and Mary was given its exact model class, so the residual had to
  vanish. A residual that persisted with more exposures and still generalised
  would require stochastic transduction or an eye outside the model class. Shot
  noise would leave a residual that is incompressible but carries no information
  about the stimulus.

## Interpretation (not a result)

In this model, what Mary gains on release is two things. The first is a few facts
about her own eye, which "complete physical knowledge" would already include if
it covered her individually rather than a standard observer. The second is
pointer edges from instances to concepts she already held. Neither needs a new
representational kind. Whether this carries over to human phenomenal experience
is outside what the model can test.
