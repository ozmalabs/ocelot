# Mary's Room: modelling her eye versus knowing it — EXPLORATORY

Status: post-hoc and exploratory, not preregistered. No frozen file or verdict
changed, and no eye was built. The documented capture + saturation replica
matches the eye to 7.8e-16. Script: `scripts/marys_room_model_vs_know.py`.
Output: `results/marys_room_model_vs_know_exploratory.json`.

## Setup

- **What Mary knows (meta-knowledge):** the eye's model class (Gaussian-band
  capture, Naka–Rushton with a shared half-saturation, the opponent transform)
  and population facts about human photopigments.
- **What she does not know:** her own eye's 7 parameters. True values:
  L 564/42, M 534/36, S 420/28, half-saturation 512; red–green zero 547.84 nm.
- **Prior (declared before results).** Peak means are from Dartnall, Bowmaker &
  Mollon (1983): 558.4 / 530.8 / 419.0 nm. Mapped into the model class by the
  best Gaussian fit to the Govardovskii et al. (2000) template, that gives
  centres 552.4 / 524.8 / 417.0 nm and widths 49 / 47 / 32 nm.
  - Centre SDs come from Webster & MacLeod (1988): 1.57 / 0.90 / 0.80 nm.
  - Width SD 10% and half-saturation 10^(3 ± 0.5) quanta are declared, with no
    literature value.
  - "Broad" variant: centre SDs taken from the microspectrophotometry spreads,
    5.2 / 3.5 / 3.6 nm.
- **Read-out assumption.** Mary can read her own experienced state (the eye's
  RG, BY) with noise σ per axis. σ = 0.005 is primary, which is about the largest
  Poisson SD measured; 0.001 and 0.02 are sensitivity cases. Without some
  read-out of her own states, no exposure could teach her anything about her eye.
- **Room-legal light.** Six neutral ColorChecker patches plus a bare white, at
  10–3000 td. Two rooms: E light only (strict), or E, D65 and A (a room lit
  variously by daylight and lamps). Each is tested with and without closed-lid
  light at 100–10⁴ td.
- **Release.** The 93 monochromatic training exposures.

## T1. Modelling without knowing

| | Population prior | Broad prior |
|---|---|---|
| True eye's z-scores (cL, cM, cS) | 7.4, 10.2, 3.8 | 2.2, 2.6, 0.8 |
| Prior tail probability of the true eye | < 1/4000 | 0.002 |
| Predicted red–green zero, 5–95% | 536.1–540.5 nm | 532.3–543.6 nm |
| Percentile of the true zero (547.84 nm) | 100 | 99.8 |
| Prior-mean predictor: held-out median angle | 5.57° | 5.57° |
| Prior-mean predictor: label agreement with the eye | 0.815 | 0.815 |

Before exposure, Mary's mechanistic self-model is confidently wrong. Her actual
red–green zero lies above every one of 4000 prior draws. The plain CIE
standard-observer prediction (554.08 nm, median angle 3.64°) is closer to her eye
than her own population-based mechanistic model. Part of this comes from the
prior construction: Gaussians fitted to the asymmetric pigment template peak
about 6 nm below λmax and are wider than this eye's Gaussians. Either way, this
model eye is an outlier relative to human pigments rendered in its own model class.

## T3. What the room already identifies (population prior, σ = 0.005)

| Light available | Bits gained | Posterior/prior SD (cL, cM, cS) | MAP red–green zero | MAP held-out median angle |
|---|---|---|---|---|
| Room, E only | 15.8 | 1.00, 1.00, 0.97 | 537.5 nm | 1.92° |
| Room, E only + eyelid | 16.7 | 0.97, 1.00, 0.97 | 537.5 nm | 1.92° |
| Room, E/D65/A | 21.8 | 0.54, 0.73, 0.94 | 541.9 nm | 2.17° |
| Room, E/D65/A + eyelid | 22.7 | 0.48, 0.69, 0.93 | 542.6 nm | 1.62° |
| Release only (93 mono) | 36.9 | 0.07, 0.11, 0.39 | 547.75 nm | 0.03° |
| Room + release | 37.6 | 0.06, 0.10, 0.37 | 547.75 nm | 0.03° |

- **Strict room (one light).** Mary learns about 16 bits, almost all about
  saturation (half-saturation SD falls to 4–6% of prior) and bandwidths. Her cone
  centres stay at prior uncertainty. The least-constrained direction is almost
  pure M-centre (with some L): whites under one light cannot tell her where her
  M cone sits. Her best self-estimate of the zero, 537.5 nm, is no better than
  before.
- **The eyelid adds about 1 bit.** It slightly narrows the L width, which is
  consistent with long-wave light, but does not locate any cone.
- **A room with several "white" lights leaks much of her eye.** At σ = 0.005 the
  MAP zero moves to 542.6 nm. At σ = 0.001 it reaches 547.28 nm (held-out angle
  0.11°, label agreement 0.997). "Black and white" is a perceptual description,
  not a spectral one: whites under daylight and lamps are spectrally different
  stimuli. The direction left unknown is then the S-cone centre.
- **Release.** 93 monochromatic exposures pin the eye down. Held-out angle is
  0.03° and agreement with the eye's labels is 1.000, including on reflectances,
  eyelid light and metamers the fit never saw.

## T2. Bits per release exposure (after the E/D65/A + eyelid room)

| σ | Order | Room bits | After 1 / 5 / 10 / 93 | Exposures to "know" (zero SD and centre SDs < 0.5 nm) |
|---|---|---|---|---|
| 0.005 | random | 22.7 | 22.7 / 27.5 / 28.8 / 37.6 | 32 |
| 0.005 | greedy | 22.7 | 26.6 / 31.6 / 33.7 / 37.6 | 6 |
| 0.001 | greedy | 36.9 | 41.4 / 47.4 / 49.7 / 53.7 | 1 (linearised; MAP check below) |
| 0.02 | either | 13.5 | — / — / — / 24.5 | not reached in 93 |

- The most informative exposures are bright short-wave and long-wave lights, in
  the order 440, 630, 500, 450, 680 nm at 10⁴ quanta, then 400 nm.
- MAP check (room + 6 greedy exposures): the zero reaches 547.47 nm and the
  held-out angle 0.13° at σ = 0.005; 547.83 nm and 0.005° at σ = 0.001.
- The linearised (Fisher) figures overstate what the room gives: they are
  evaluated at the true parameters, while the prior sits 7–10 SD away. The MAP
  fits are the honest version.

## Bearing on "she can model her eye, she cannot know it"

- **Supported.** Meta-knowledge (model class plus population) leaves Mary
  confidently wrong about her own eye. The parameter values arrive only by
  running the eye and reading its states. A handful of well-chosen exposures is
  enough, and the gain is 15–38 bits depending on read-out noise.
- **Qualified by the room.** The room is not a clean null. Spectrally varied
  "white" light and a precise self-read-out recover most of her eye before
  release. Only a single-illuminant room keeps her cone centres unknown.
- **Qualified by what is gained.** What she gains is a finite set of facts about
  one physical system. Once she has them she can write them down, and someone
  else can know them. The acquaintance is in the channel (her eye running, her
  read-out of its states); the content is propositional.
- **Assumption that carries the result.** Everything here rests on Mary having
  numerical access to her own experienced states. That access is the part a
  physical description of the eye does not supply by itself.
