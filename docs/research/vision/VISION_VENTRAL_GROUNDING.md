# VISION — GROUNDING THE VENTRAL "WHAT" PHASE IN BIOLOGY

*A moderate research spike (2026-07-18), four parallel agents, every load-bearing
claim cross-checked against ≥2 independent primary/review sources, anti-fabrication
discipline enforced (cite real authors/years; label (A) textbook-solid / (B)
leading-but-contested / (C) folk-oversimplification; flag single-source /
abstract-only reads). This grounds the rungs PAST the eye core functions — colour
identity, proto-objects, and the objecthood "what" layer where the arc's cortex
line hit its wall.*

## THE HEADLINE — the wall is the OBJECTIVE, and generator discovery is the native crossing

The four agents converge on ONE diagnosis and ONE crossing:

**Diagnosis: the ventral code is TASK/OBJECTIVE-driven, not statistics-driven.**
Untangling emerges from a *discrimination-under-nuisance* objective (DiCarlo & Cox
2007 *TICS*; DiCarlo/Zoccolan/Rust 2012 *Neuron*; goal-driven DNNs predict IT
*because of the task objective, not the architecture* — Yamins et al. 2014 *PNAS*).
Input **covariance** — what Hebbian learning captures — recovers nuisance-dominated
structure (the leading eigenvector = the DC blob). **That is exactly the arc's
diagnosed dead end.** Hebbian-on-images failed for the SAME reason unsupervised
statistics fail to predict IT: covariance is the wrong objective. **The wall is a
missing OBJECTIVE, not a missing layer.**

**Crossing: untangling ≡ generator discovery.** A tangled manifold = identities
acted on by nuisance transformations (pose/size/view/lighting). Untangling = factor
observed variation into *identity* (which manifold) × *generator-orbit* (position
along it). That is PRECISELY "discover the transformation between frames" — the
substrate's generator discovery, already proven for time/depth/stereo (one op on
more frames). Point it at object appearance: multiple frames of one object under
varying nuisance → discover the generator; **identity = the generator-invariant
residual; nuisance = the generator parameter.** Untangling as DISCOVERY (compress
one object's frame-to-frame variation, MDL-gated), NOT supervised readout, NOT
covariance. The substrate's core mechanism is the natural formulation of the
ventral stream's job.

## LEVEL-BY-LEVEL MAP (this level and the next)

### Mid-level form (V2 → V4) — the proto-object stage, BEFORE the wall
- **(A) Border-ownership / figure-ground:** V2 (and V4) cells assign an identical
  local edge to a *figure side* (Zhou/Friedman/von der Heydt 2000 *J.Neurosci.*
  20:6594). A directed boundary that OWNS a surface — not a per-pixel edge flag.
- **(A) Illusory contours in V2, not V1** (von der Heydt/Peterhans/Baumgartner 1984
  *Science* 224:1260) — contour completion driven by *configuration*, gap-bridging.
- **(A) Naturalistic texture selectivity in V2** (Freeman/Ziemba/Simoncelli/Movshon
  2013 *Nat.Neurosci.*; Ziemba 2016 *PNAS*) — higher-order statistics over V1
  outputs, position-tolerant. Texture = quantize the STATISTICS, not the pixels.
- **(A) V4 curvature / boundary-conformation part coding** (Pasupathy & Connor 2001
  *J.Neurophysiol.* 86:2505; 2002 *Nat.Neurosci.* 5:1332) — boundary as
  curvature-at-angular-position around the shape's OWN center (object-centered,
  a cross-frame map — curve intensional, sampled points in-frame integer).
- **(B) Proto-object = a coherent pre-identity stage** (von der Heydt / Niebur
  grouping-cells program): border-ownership + grouping + closure/convexity test for
  "objectness". Leading, theory-laden; the discrete-token-vs-graded question is open.
- **(C) avoid:** "V2/V4 recognize objects" — they assign borders and group regions,
  NO identity.

### Colour up the ventral stream — categorical colour + constancy
- **(A) No single "colour centre"; a distributed modular chromatic stream.** "Globs"
  = mm-scale luminance-invariant hue modules in posterior IT / V4-complex (Conway/
  Moeller/Tsao 2007 *Neuron*), interdigitated with shape-selective interglobs and
  adjacent to face patches. "V4 = the colour area" (Zeki) was a SAMPLING ARTIFACT of
  a modular substrate (**(C)**; Lennie 1999 correction).
- **(A) Early cortex (V1–hV4) codes hue CONTINUOUSLY** (Persichetti 2015; Brouwer &
  Heeger 2009). Categorical CLUSTERING appears later, **top-down / task-gated** — a
  gain-reweighting of the continuous code (Brouwer & Heeger 2013 *J.Neurosci.*), NOT
  bins baked into sensory encoding. **(A) Perceptual/unique hues do NOT align with
  the cone-opponent cardinal axes** (Krauskopf 1982) → categories are a LEARNED
  RE-PARTITION of the space, not a read-off of the sensor basis. Weak innate seed
  near cross-linguistic boundaries (**(B)** infants).
- **(A) Colour constancy is ill-posed** (reflectance × illuminant); Retinex + V1
  double-opponent local contrast is the FIRST step; global illuminant inference
  completes it downstream (V4/PIT, lesionable independent of discrimination, **(B)**).
  Fits the frame invariant: reflectance in-frame, illuminant a cross-frame map.
- **(A) Surface colour binds PRE-OBJECT** — to a border-owned, filled-in region
  (filling-in, neon spreading, watercolour illusion), gated on border-ownership NOT
  recognition. Same hinge as mid-level form.

### IT / object recognition — the wall itself
- **(A) Manifold untangling:** V1→V2→V4→IT progressively flattens/separates object
  manifolds until IT is ~linearly separable. **Single-neuron invariance is NOT the
  goal** — invariance is a POPULATION/geometric property (**(C)** to avoid: "IT
  neurons are invariant grandmother detectors").
- **(B→A) The face code is a learned low-D AXIS code** (Chang & Tsao 2017 *Cell*
  169:1013): ~50-D face space (≈25 shape + ≈25 appearance), each cell ≈ one axis, a
  face = its projection; linear decode reconstructs the face. A high-level category
  IS a learned low-D axis basis with linear readout. (Interpretation contested —
  Rossion/Taubert; monkey↔human gap.) Shape(landmark-integer)/appearance(texture)
  echoes in-frame-integer / cross-frame-continuous.
- **(A) Category-selective regions** (FFA/PPA/EBA/VWFA) are reproducible PEAKS in a
  DISTRIBUTED, topographically-organized map (Haxby 2001; large-scale axes:
  animate/inanimate, real-world size). Not hand-partitioned modules — emergent
  attractors. Modular-vs-expertise-vs-distributed all partly true (**(B)**).
- **(A) Core recognition ~feedforward** (~100–200 ms; Thorpe 1996 *Nature* 381:520)
  BUT **recurrence is critical for challenge images** (occluded/cluttered/degraded —
  Kar/Kubilius/DiCarlo 2019 *Nat.Neurosci.* 22:974; the late IT signal solves them;
  CORnet-S shallow-recurrent). Feedforward-vs-recurrent split is IMAGE-DEPENDENT.
- **(A) Goal-driven DNNs are the best IT models** (Yamins 2014) — but the match has
  STALLED below the noise ceiling and DIVERGES: texture-bias (Geirhos 2019),
  adversarial fragility, OOD failure, worst exactly where recurrence matters. The
  TASK-objective is what makes them brain-like; the feedforward architecture is where
  they break. → do NOT import a feedforward stack.

### Development — the scaffold is a SEED (learned-vs-innate, resolved)
- **(A) Innate retinotopic/eccentricity proto-map** present at birth (Arcaro &
  Livingstone 2017 *eLife*; macaque ~10 days, 2.2° from adult), with feature biases
  (SF, curvature) tied to eccentricity BEFORE categorical selectivity.
- **(A) Category domains are EXPERIENCE-DEPENDENT, carved into the scaffold:** face
  patches emerge ~200 days; face-deprived macaques develop NO face patches yet keep
  normal retinotopy + non-face domains (Arcaro et al. 2017 *Nat.Neurosci.* 20:1404).
  Human FFA takes >10 years. **"Innate scaffold + experience refines" ≡ seed codebook
  + dynamic-quantization growth** — and it generalizes the arc's V1-orientation
  finding up the WHOLE ventral hierarchy.
- **(B) Softening:** congenitally-blind adults show fusiform face-selectivity via
  haptics (Ratan Murty/Kanwisher 2020 *PNAS*) — the ADDRESS is fixed by connectivity/
  wiring, the CONTENT by structured input of ANY modality. Necessity is for
  structured input, not vision per se. Do NOT encode an innate face template (CONSPEC
  contested; a weak top-heavy/high-contrast bias is the defensible floor).
- **Dorsal/motion early — CONFIRMED with caveat:** low-level MT co-earliest with V1
  (partly V1-independent); but GLOBAL-motion integration matures late through
  childhood and is selectively VULNERABLE (Braddick & Atkinson "dorsal-stream
  vulnerability") — early ≠ robust; the vulnerability is itself a gate.
- **Two-streams:** what/where (Ungerleider-Mishkin) + what/how (Milner-Goodale,
  patient DF). Streams INTERACT (not clean split; "dorsal is illusion-immune" is
  **(C)** — Ebbinghaus-grasp dissociation contested).

## BUILD IMPLICATIONS (the grounded next-phase plan)

1. **Cross the wall with an IDENTITY-UNTANGLING OBJECTIVE = multi-frame generator
   discovery, NOT Hebbian/covariance.** Given multiple frames of one object under
   varying nuisance (pose/size/view/lighting), discover the generator that maps
   between them (MDL-gated, the existing sd-loop growth); identity = generator-
   invariant residual, nuisance = generator parameter. This is "one op on more
   frames" applied to appearance, and it is objective-driven the RIGHT way (compress
   variation) instead of covariance-driven (DC blob).
2. **SEED the proto-map; quantize domains onto it.** The retinotopic/eccentricity
   scaffold + feature biases = seeded CapabilityAxes over an eccentricity-scaled
   field; category domains = minted quanta where residual structure recurs, biased by
   the scaffold (foveal → fine identity; peripheral → scene stats). Do NOT grow
   retinotopy from image covariance. Expect distributed-field + emergent attractors,
   NOT built-in category detectors.
3. **Build proto-objects FIRST — they are before the wall.** Border-ownership = a
   directed contour relation (a `bounds`/`figure_side` typed edge that points at the
   figure it owns) — the grounded-transitive-contour direction, native to the graph.
   Grouping/figure-ground/contour-completion = transitive MDL-gated closure. Texture
   = quantize higher-order statistics. Surface colour binds HERE (pre-object).
4. **Recurrence = the run_rules fixpoint.** Fast basin-snap/net-reflex = feedforward
   core recognition; iterated collapse (render→residual→revise) = the recurrent path
   for occlusion/clutter/figure-ground. The substrate is architecturally AHEAD of the
   feedforward DNN account here — LEAN IN.
5. **Store identity as an axis-codebook of quanta** (à la the ~50-axis face code):
   mint axes where they compress the identity space; encode an instance as its
   projection coordinates; linear readout.
6. **Colour identity (building now): categories are a LEARNED RE-PARTITION of a
   continuous space, NOT fixed bins on the cone-opponent axes**, gateable by task/
   label. Mint from the colour DISTRIBUTION (where it clusters + compresses).
   Colour constancy = a LATER cross-frame illuminant-discounting rung (local
   double-opponent → global illuminant inference; multi-illuminant unsolved — budget
   a real inference, not surround-subtraction).

## FAILURE-MODE GATES — the "real tell" for the next rungs
(ranked; the arc's discipline: a failure mode is a claim about what a mechanism DRIVES)
1. **Apperceptive vs associative dissociation** — the FORM↔RECOGNITION seam. Ablate
   the percept→concept edge: recognition dies while reconstruction ("copy") survives
   (associative) vs corrupt the render itself (apperceptive). Proves the two stages
   are separable, not one blob.
2. **McCollough contingent aftereffect — THE decisive predictive-coding test.**
   Orientation-contingent illusory colour from adapting colour⊗orientation joint
   statistics; error-driven decorrelation = the negative residual of an over-fit
   contingency prior = render-from-prior + opponent-residual. **A feedforward
   classifier CANNOT fake it.** Highest discriminative value.
3. **Face-inversion + Thatcher** — holistic configural quanta that bind only in the
   canonical (upright) reference frame. Tests that composition (the Omniglot +21pp
   "arrangement") is reference-frame-dependent holistic, not a part-bag.
4. **Crowding** — eccentricity-scaled statistical pooling (summary-statistic
   jumbling in clutter); validates the foveation / eccentricity-decay prior.
5. **Cerebral achromatopsia** — remove the colour SIGN while chromatic-edge/structure
   computation persists; validates the luminance-structure / colour-sign split.

## SETTLED / CONTESTED / FOLK ledger
- **SETTLED (A):** border-ownership; illusory contours in V2; V2 texture statistics;
  V4 curvature-part coding; manifold untangling → linear separability; single-neuron
  invariance is NOT the goal; core recognition ~feedforward + recurrence critical for
  challenge images; FFA/PPA/EBA/VWFA exist + Haxby distributed decoding; goal-driven
  DNNs best IT models + texture-bias divergence; innate retinotopic proto-map;
  category domains experience-dependent; continuous early colour code; unique hues ≠
  cardinal axes; Retinex/double-opponent first constancy step; pre-object surface
  colour via border-ownership.
- **CONTESTED (B):** Chang-Tsao axis-code interpretation; modular-vs-expertise-vs-
  distributed FFA; how-much-feedforward (image-dependent); glob chromotopy/unique-hue
  bias; categorical clustering = task-gain only?; prelinguistic vs linguistic colour
  categories; retinal-wave instructiveness; blind-FFA softening necessity-of-vision;
  Ebbinghaus-grasp dissociation.
- **FOLK to avoid (C):** "V2/V4 recognize objects"; "IT neurons are invariant
  grandmother detectors"; conflating MTL concept cells (Quiroga) with IT coding;
  "V4 = the colour area"; "colour categories are purely linguistic (or purely
  innate)"; "double-opponent cells solve constancy"; "dorsal is illusion-immune";
  innate face template (CONSPEC).

## Key sources
DiCarlo & Cox 2007 *TICS* 11:333 · DiCarlo/Zoccolan/Rust 2012 *Neuron* 73:415 ·
Chang & Tsao 2017 *Cell* 169:1013 · Kar/Kubilius/DiCarlo 2019 *Nat.Neurosci.* 22:974 ·
Yamins et al. 2014 *PNAS* 111:8619 · Geirhos et al. 2019 ICLR · Haxby et al. 2001
*Science* 293:2425 · Kanwisher/McDermott/Chun 1997 *J.Neurosci.* 17:4302 · Thorpe/
Fize/Marlot 1996 *Nature* 381:520 · Zhou/Friedman/von der Heydt 2000 *J.Neurosci.*
20:6594 · von der Heydt/Peterhans/Baumgartner 1984 *Science* 224:1260 · Freeman/
Ziemba/Simoncelli/Movshon 2013 *Nat.Neurosci.* · Pasupathy & Connor 2001/2002 ·
Conway/Moeller/Tsao 2007 *Neuron* · Brouwer & Heeger 2013 *J.Neurosci.* · Persichetti
2015 · Krauskopf/Williams/Heeley 1982 · Arcaro & Livingstone 2017 *eLife* + Arcaro et
al. 2017 *Nat.Neurosci.* 20:1404 · Ratan Murty/Kanwisher 2020 *PNAS* · Braddick &
Atkinson 2003 · Heywood & Cowey 1997 *TICS* (achromatopsia) · McCollough 1965.

*Source-quality: most reads were abstract/review-level (Arcaro eLife read in fuller
text); no load-bearing claim rests on a single snippet; paywalled full texts
(Witzel-Gegenfurtner 2018 AnnRev, Chang-Tsao 2017, DiCarlo 2007/2012) flagged and
corroborated via ≥2 secondary sources. No citation/number/quote fabricated.*
