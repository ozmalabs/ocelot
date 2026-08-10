# VISION CALIBRATION — LITERATURE ADJUDICATION

**Status: COMPLETE.** All sections resolved. Written incrementally.

Purpose: adjudicate a set of architectural claims constructed by the supervisor
from armchair reasoning, against primary literature. Each claim gets a verdict:
**SUPPORTED / CONTESTED / REFUTED / NOT-ADDRESSED**, with the deciding citation.

Verdict definitions used throughout:

- **SUPPORTED** — mainstream, replicated, with a primary source that states it.
- **CONTESTED** — real literature exists on both sides; live controversy.
- **REFUTED** — the literature says the opposite.
- **NOT-ADDRESSED** — nobody has asked this question in this form. This is NOT
  the same as "wrong"; it means there is no external check available, and the
  claim must be earned by our own measurement.
- **INVENTED** — the supervisor's phrasing implies an established result that
  does not exist. Called out explicitly.

---

## 1. PER-SURFACE CALIBRATION AND THE DUAL REALITY OF PICTURES

### HEADLINE: the idea is NOT invented — it has a name, a literature, and a live controversy.

The supervisor's "projection rules are calibrated per surface" is, in the
picture case, **`local slant compensation`** (Vishwanath, Girshick & Banks 2005).
The visual system estimates the **slant of the picture surface at the point of
interest** — using cues *uncontaminated by the picture's contents*, primarily
binocular disparity — and adjusts the retinal image by that estimate before
interpreting the depicted content. That is per-surface calibration, stated in
those terms, by a Nature Neuroscience paper. **This hands us a mature literature
rather than a hunch — which is the most useful outcome the brief asked for.**

It is however **CONTESTED**, not settled. Details below.

### 1a. Is the dual reality of pictures established? — SUPPORTED (as phenomenology), CONTESTED (as mechanism)

**Established.** Pirenne (1970, *Optics, Painting and Photography*, CUP) is the
canonical statement: viewing a picture involves simultaneous awareness of the
flat physical surface *and* the depicted 3D space. Gibson's version: looking at
a picture "requires two kinds of apprehension, a direct perceiving of the picture
surface along with an indirect awareness of what it depicts."

The duality is not seriously disputed as a description of experience. It is the
standard framing in the current review literature:

- Hertzmann, A. (2024). "Toward a theory of perspective perception in pictures."
  *Journal of Vision*. <https://pmc.ncbi.nlm.nih.gov/articles/PMC11055503/>
  — a recent, honest, controversy-mapping review. **Read this one first if you
  read only one thing.**
- Koenderink et al., "Varieties of pictorial vision."
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11372779/>
- Sedgwick, H.A. (2021). "Gibson and Pictures in Perspective: Reverse the
  Directions." <https://pmc.ncbi.nlm.nih.gov/articles/PMC8543584/>
- Kulvicki / Nanay-adjacent philosophy-of-perception treatments, e.g.
  "Conflicted Character of Picture Perception," *JAAC* 64(4).
  <https://academic.oup.com/jaac/article/64/4/471/5957414>

**But the MECHANISM is exactly what is unresolved.** Hertzmann's own summary:
"no paradigm offers a compelling explanation for how viewers perceive 3D shape
and space in pictures, accounting for both linear and nonlinear projections."
Do not import a mechanism account as if one were settled — there isn't one.

Note the philosophy/vision-science split: the philosophers argue about whether
the two percepts *conflict* (whether it is "twofoldness", seeing-in, or
inconsistent spaces); the vision scientists argue about compensation geometry.
These are different debates using overlapping words.

### 1b. Do projection rules attach to an IDENTIFIED SURFACE rather than a retinal region or the whole scene? — SUPPORTED but CONTESTED; and the supervisor's "per surface" is really "per LOCAL PATCH"

This is the sharpest and most useful finding for us.

**Vishwanath, D., Girshick, A.R. & Banks, M.S. (2005). "Why pictures look right
when viewed from the wrong place." *Nature Neuroscience* 8, 1401–1410.**
<https://www.nature.com/articles/nn1553> ·
open copy: <https://pmc.ncbi.nlm.nih.gov/articles/PMC2727473/>
(erratum: <https://www.nature.com/articles/nn1205-1791b>)

Their claim, in their words: "the observed invariance is due to an adjustment of
the retinal-image shape based on measurements of the **local slant of the picture
surface at the point of interest**."

What this establishes for us:

1. **The calibration is keyed to a SURFACE, not to the scene and not to the
   retinal region per se.** The estimate is of the *physical display surface's*
   orientation.
2. **It is estimated from cues that bypass the picture's content** — dominantly
   binocular disparity (their reported slant estimate SD ≈ 6–10°), with a weak
   secondary contribution from the picture frame's perspective. This is the
   architecturally interesting part: the surface estimate is computed in a
   channel that the depicted content cannot corrupt. That is a real design
   constraint, empirically motivated.
3. **Two rival hypotheses were explicitly RULED OUT** by this paper:
   - *pictorial compensation* (recovering the centre of projection from
     vanishing points in the picture): rejected — "the binocular settings were
     the same with and without geometric information."
   - *centre-of-projection / viewing-distance compensation*: rejected — when
     the projection plane was rotated while the observer stayed at the CoP,
     geometrically correct pictures looked distorted.
4. **Ablation-style evidence.** Monocular viewing through an aperture (surface
   slant cues removed) → **invariance disappears**; percept follows raw retinal
   geometry, defaulting toward a frontoparallel-surface assumption. This is
   close to a lesion experiment on the surface-calibration channel, and it is
   the single most transferable empirical fact in this section.
5. **Stated range limit:** invariance degrades beyond about ±45° viewing angle
   (binocular fusion fails, slant estimate uncertainty rises), and the mechanism
   does not produce geometrically correct results for wide-angle pictures
   (>~36° FOV) — which is the vision-science reason behind photographers'
   focal-length rules of thumb.

**THE CONTEST.** Erkelens, C.J. (2013). "Virtual Slant Explains Perceived Slant,
Distortion, and Motion in Pictorial Scenes." *Perception* 42(3).
<https://journals.sagepub.com/doi/abs/10.1068/p7328>
Erkelens ran obliquely-viewed skewed-grid stimuli on a slanted screen and found
**no slant compensation**: the orientation of the physical display surface had
little effect, and perceived slant tracked a "virtual slant" computed from the
retinal image alone (parallel-line cues), both monocular *and binocular*. He
argues compensation is unnecessary as an explanatory posit.
See also Erkelens (2018), "Multiple Photographs of a Perspective Scene Reveal
the Principles of Picture Perception," *Vision* 2(3):26.
<https://www.mdpi.com/2411-5150/2/3/26>

And earlier, against strong compensation: Halloran, T.O. (1989/1990),
"Compensation is unnecessary for the perception of faces in slanted pictures."
<https://pubmed.ncbi.nlm.nih.gov/2377436/>; and "Weakening the robustness of
perspective: Evidence for a modified theory of compensation in picture
perception" (*Perception*, ~1999).
<https://www.researchgate.net/publication/12964826>

**Adjudication.** The existence of a surface-keyed calibration mechanism is
**CONTESTED**: a strong primary result supports it, a competent primary result
using different stimuli fails to find it, and the current review (Hertzmann
2024) lists this as an open contradiction rather than a resolved question.
Hertzmann's own proposal — that compensation is *fixation-centred* and local,
and that the global picture interpretation "need not be geometrically stable or
consistent over time" — is a third position, and is itself new and untested.

**IMPORTANT CORRECTION TO THE SUPERVISOR'S FRAMING.** The literature's unit is
**the local patch at the current fixation**, not "the surface" as a globally
identified object. Both Vishwanath ("local slant... at the point of interest")
and Hertzmann ("fixation-centered perspective", explicitly *not* globally
consistent) converge on this. If our architecture identifies a whole surface and
attaches one calibration to it, that is a **stronger** claim than the literature
supports, and it makes a prediction the literature would call false: it predicts
global consistency that Hertzmann argues does not exist. Flagging this as the
place our design most likely over-reaches.

### 1c. Can the same retinal region hold TWO calibrations simultaneously, neither winning? — NOT-ADDRESSED in the form stated; the phenomenology is SUPPORTED, the "both correctly, neither wins" part is the supervisor's addition

The phenomenological duality (1a) is well established, and it does entail that
one retinal region concurrently supports a surface percept and a depicted-space
percept. To that extent the claim is fine.

What I could **not** find is any primary result showing that two *projection
calibrations* are maintained concurrently and both applied veridically without
mutual interference. The literature's actual finding is closer to the opposite:
the two readings **interact and trade off**, which is exactly why authors call
it "conflicted" (JAAC 64(4)) and why the compensation debate exists at all. The
picture-surface percept *modifies* the depicted-space percept (that is what
compensation IS) — so they are coupled, not independent.

**Verdict: the "two simultaneous, both correct, neither wins" formulation
appears to be the supervisor's construction.** It is not contradicted, but it is
not a result you can cite. If we build it, we are making a novel claim and must
earn it by measurement. Hold it to the higher bar.

Relevant partial counterweight — the duality can **collapse**: in trompe l'oeil
the surface reading is lost and the depicted object is seen as a real present
object. Ferretti, G. (2020). "Why Trompe l'oeils Deceive Our Visual Experience."
*JAAC*. <https://onlinelibrary.wiley.com/doi/abs/10.1111/jaac.12688>
That is evidence *against* a strict always-both architecture, and *for* the
mis-assignment framing in 1e.

### 1d. Mirror space perception — REFUTED as stated ("veridical"); the errors are large, systematic and well documented

(Scoped as asked to spatial perception in mirrors, NOT Gallup-style mirror
self-recognition.)

People do **not** perceive reflected space veridically. The systematic errors
are the main finding of a substantial "naive optics" literature, led by Marco
Bertamini and colleagues:

- Bertamini, M., Spooner, A. & Hecht, H. (2003). "Naive Optics: Predicting and
  Perceiving Reflections in Mirrors." *JEP:HPP*.
  <https://gwern.net/doc/psychology/cognitive-bias/illusion-of-depth/2003-bertamini.pdf>
- Hecht, H., Bertamini, M. & Gamer, M. "Naive optics: acting on mirror
  reflections." <https://www.semanticscholar.org/paper/6b6f9c76960d0aa5a42c9c22809efceecfeeab60>
- Bertamini, M. & Soranzo, A. (2018). "Reasoning About Visibility in Mirrors: A
  Comparison Between a Human Observer and a Camera." *i-Perception*.
  <https://journals.sagepub.com/doi/10.1177/0301006618781088>
- Lawson, R. & Bertamini, M. "Through the Looking-Glass: Objects in the mirror
  are less real." *Psychon. Bull. Rev.*
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC4437972/>
- Jones, L.A. & Bertamini, M. (2007). "Through the Looking Glass: How the
  Relationship between an Object and its Reflection Affects the Perception of
  Distance and Size." *Perception*.
  <https://journals.sagepub.com/doi/10.1068/p5605>

Characteristic errors, as documented:

- **Early-visibility error**: people predict a target becomes visible in a mirror
  while it is still well off to the side; correct answer requires it to reach the
  near edge. A consistent bias to misjudge mirror objects **too far to the
  outside**, present even with real mirrors, not only diagrams.
- **Frontal bias**: predictions are dominated by an assumption of frontal
  viewing; observers handle the role of the *viewpoint* in reflection poorly.
  (This is the deepest one for us — it suggests the mirror calibration is
  *under-parameterised* in people, defaulting to a canonical viewpoint.)
- **Wrong distance variable**: people believe apparent size depends on
  object-to-mirror distance, when the determinant is object-to-observer distance.
- **Vertical/horizontal anisotropy** in encoding mirror space.
- Objects in mirrors are rated as **"less real"** — a reduced-presence effect.

**Adjudication: REFUTED as stated.** If the architecture assumes a mirror
carries a correct local calibration that people read off accurately, that is
wrong. The honest version is: **a mirror carries a distinct calibration that is
applied, but crudely and with a strong frontal/canonical-viewpoint prior.**
Usefully, that is a *stronger* argument for per-surface calibration than
veridicality would be — a separate, separately-mis-calibrated mechanism is more
diagnostic than a correct one.

### 1e. Anamorphosis / trompe l'oeil as mis-assigned calibration — the FRAMING is largely ours; the phenomena are real

The phenomena are of course thoroughly documented, and the vantage-point
dependence is the standard teaching point ("what you see has a great deal to do
with where you are looking from"). Anamorphosis has been a psychologists'
object of study since the early 20th century.

But **I could not find a primary vision-science source that frames anamorphosis
or trompe l'oeil as a mis-assigned surface calibration** in those terms. The
closest legitimate anchors:

- Ferretti (2020) above, on trompe l'oeil: the surface reading is *lost*, and
  the depicted is experienced as a present interactable object. This is
  consistent with "the calibration got assigned to the wrong surface" but he
  does not argue it in calibration terms.
- Vishwanath et al. (2005) implies the account structurally: if compensation is
  driven by a surface-slant estimate from disparity, then anamorphosis is what
  you get when the surface estimate is correct but the content was constructed
  for a different CoP, and trompe l'oeil is what you get when the surface
  estimate is defeated. **This is my inference, not their claim.**

**Verdict: NOT-ADDRESSED-BY-THE-LITERATURE as framed.** The framing is
defensible and I think correct, but it is ours to earn. Do not write it down as
though someone established it.

### Gaps I could not resolve in §1

- Whether anyone has measured **two concurrent calibrations on one retinal
  region** directly. I suspect the experiment has not been run; the closest
  paradigm would be a mirror-within-a-picture or a screen-showing-a-window
  stimulus with independent slant manipulation. **Source that would settle it:**
  a systematic search of *Journal of Vision* / *Perception* for
  "nested pictorial space" or "picture-in-picture depth" — I did not run this.
- Whether the Vishwanath/Erkelens conflict has been resolved post-2024 by a
  decisive experiment. Hertzmann (2024) says no as of then; I did not find a
  2025–2026 resolution but did not search exhaustively.
- Real-time / non-picture surfaces (windows, water) — I found **no** literature
  treating a window or a water surface as carrying its own projection
  calibration. **This is a genuine hole in the claim's coverage: the
  supervisor's list of surfaces (mirror, TV, photo, window, water) is supported
  by literature only for pictures and mirrors.**

  **A second pass on water specifically returned only physics-textbook and
  diving-instruction material, no vision-science primary sources.** What it did
  establish, at that (weak) level of evidence:
  - The base error is the *uncorrected* one: "our eyes and brain trace light rays
    back into the water as though they traveled in a straight line rather than
    refracted" — i.e. the default is **no compensation**, the same
    frontoparallel-style default seen in §1b's monocular condition and §1d's
    mirror frontal bias. Consistent across three of our surface types.
  - Quantitatively: through a flat mask, objects appear **~33% bigger / 25%
    closer**. <https://en.wikipedia.org/wiki/Underwater_vision>
  - **"The diver LEARNS to compensate"** — repeatedly asserted in diving and
    spearfishing sources. *If true and measurable, this is the single most
    directly on-point phenomenon for the whole per-surface thesis*: an acquired,
    surface-specific calibration for a non-picture surface. **But I could not
    find a controlled study.** Treat as FOLK pending a real source.
  - **Source that would settle it:** a search of underwater/hyperbaric
    psychophysics literature (divers' size-distance judgements pre/post
    experience) — plausibly exists in applied-ergonomics or military-diving
    journals rather than mainstream vision science. I did not reach it.

## 1B. ADDENDUM — THE MERCATOR / THEOREMA EGREGIUM POINTER

Asked late: is projection-theory formalism (Gauss's Theorema Egregium; the
conformal / equal-area / equidistant / azimuthal taxonomy; "no faithful
projection, only a choice of what to lose") ever applied to *perceptual*
projection?

**ANSWER: YES, on both counts — and more directly than expected. The creator's
framing is not a metaphor; it is the actual mathematics people use.**

### Pointer 1: applied to retinotopy — SUPPORTED, and quantitatively

The retinotopic map is not merely *analogous* to a map projection; it is
formally analysed as a **conformal map**, and its deviations from conformality
are measured with the standard differential-geometry apparatus.

- Schwartz, E.L. (1977, 1980, 1983) — the complex-logarithm model of the
  retina→V1 map, explicitly a **conformal** (angle-preserving) transform.
  Schwartz (1983) notes the log-polar conformal transform "produces some
  invariance to image rotations and dilations."
- **Wedge-Dipole** model — "the composition of a constant azimuthal shear
  'wedge' map and a conformal 'dipole' map that is an extension of the standard
  log-polar or complex logarithm mapping." Note the structure: a conformal core
  **plus an explicitly non-conformal shear term**. The literature already
  states the trade rather than pretending to fidelity.
- **The decisive citation for the creator's framing:** Ta, Tu, Lu, Wang et al.,
  "Quantitative Characterization of the Human Retinotopic Map Based on
  **Quasiconformal** Mapping." *Medical Image Analysis* / PMC8678293.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC8678293/>
  They quantify the map with **vertex-wise Beltrami coefficients** — the
  Beltrami coefficient is precisely the local measure of *how far from conformal*
  a map is, i.e. the differential-geometry generalisation of **Tissot's
  indicatrix**. They report V1 cortical magnification is "approximately conformal
  (i.e., angle-preserving)" — with *approximately* doing measurable work.
- Related: "A sinusoidal transformation of the visual field is the basis for
  periodic maps in area V2," *Neuron* (2021).
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC8678345/> — V2 uses a **different**
  projection from V1. Different area, different choice of what to lose. This is
  the taxonomy in action.
- Ogmen & Herzog (2010), "The Geometry of Visual Perception: Retinotopic and
  Nonretinotopic Representations in the Human Visual System," *Proc. IEEE*.
  <https://www.ece.uh.edu/sites/www.ece/files/faculty/hogmen/ogmen-herzog%20P-IEEE%202010.pdf>

**Borrowable directly:** "name the distortion when you choose the
representation" is not our coinage — it is the Beltrami-coefficient
methodology, and it comes with a scalar field you can compute and report per
location. If our architecture chooses a retinal representation, the honest
statement of its cost is a Beltrami/Tissot field, and there is precedent for
publishing exactly that for a visual map.

### Pointer 2: a distortion taxonomy in picture perception — SUPPORTED, and it is Koenderink's framing

- **Koenderink's position, as summarised by Hertzmann (2024): "choosing a
  projection amounts to choosing from among a number of different goals and
  constraints."** That is the cartographic trade-off statement, applied to
  pictures, by the field's most mathematically serious perceptionist.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11055503/>
- Koenderink et al. (2016) follow **Helmholtz** in advocating **stereographic**
  projection to capture the effects of eye movements — and note explicitly that
  stereographic "does not preserve relative object scales." That is a named
  projection with a named loss: the cartographic vocabulary used verbatim.
- **Zorin, D. & Barr, A.H. (1995)** define a *parametric family* of projections
  trading off **straight-line preservation against local distortion
  minimisation** — a one-parameter family between "conformal-like" and
  "gnomonic-like" goals. This is the closest thing to a formal picture-perception
  analogue of the projection taxonomy, and it is constructive.
- Gnomonic/rectilinear (= standard linear perspective) is characterised in
  exactly the taxonomic way: preserves straight lines and directions, does **not**
  preserve proportions, angles, areas or distances.
- Panini and other compromise projections are studied for perceptual acceptability
  (cf. the Panini-projection space-perception work,
  <https://www.researchgate.net/publication/281583319>), and there is a survey
  literature on wide-angle rectification framed the same way
  (<https://arxiv.org/pdf/2011.12108>).
- Hertzmann's accessible version: "How Does Perspective Work in Pictures?"
  <https://aaronhertzmann.com/2022/02/28/how-does-perspective-work.html>

### What this does to §1

It **strengthens** the per-surface claim and gives it better language. The dual
reality of pictures, restated in this vocabulary: the picture surface and the
depicted space are **two projections with different preserved invariants**, and
the observer must hold both — which is why they cannot be reconciled into one
consistent geometry, and why Hertzmann concludes global picture interpretation
"need not be geometrically stable or consistent over time." **Theorema Egregium
is the reason a single global calibration is impossible in principle, not merely
absent empirically.** That is a considerably better foundation than the
supervisor's original construction, and it was the creator's framing, not ours.

**Honest limit:** I found the two halves (projection formalism applied to
retinotopy; projection trade-offs applied to pictures) as *separate* literatures.
**I did not find anyone who unifies them** — i.e. nobody I found treats
retinotopy, the picture surface, and the mirror as a *family* of per-surface
projections each with its declared invariants. That specific unification appears
to be ours. It is a modest, plausible extension of two mature literatures rather
than an invention from nothing, but it is unclaimed, so it must be earned.

---

## 2. MOTION-BASED OBJECT SEGMENTATION IN INFANTS

### HEADLINE FOR THE RUNNING RUNG: the premise is SOUND, but one word in it is wrong.

**"Infants segment objects by common motion before static form" — SUPPORTED, and
it is among the better-replicated findings in infant cognition.** The rung is not
built on sand.

**"LONG BEFORE" / innate — REFUTED. Newborns do NOT do it.** The ability emerges
over the first ~4 months. If the rung's design assumes motion segmentation is a
primitive available from the start, that specific assumption is contradicted by
direct evidence. If the rung only assumes motion segmentation *precedes and
bootstraps* static-form segmentation, it is fine — arguably better than fine,
since the developmental ordering is exactly what our architecture wants.

### 2a. The core finding — SUPPORTED

Kellman, P.J. & Spelke, E.S. (1983). "Perception of partly occluded objects in
infancy." *Cognitive Psychology* 15, 483–524.
<https://www.harvardlds.org/wp-content/uploads/2017/01/Perception-of-partly-occluded-objects-in-infancy-1.pdf>

The rod-and-box paradigm: a centre-occluded rod whose visible ends undergo
**common lateral translation** is perceived by 4-month-olds as one complete
object (habituation generalises to the complete rod, dishabituates to the
gapped display). **Stationary** displays with the same form information do
**not** produce unity perception.

Converging evidence with a *different response measure* (reaching, not looking —
this matters given the looking-time critiques in 2c):
- von Hofsten, C. & Spelke, E.S. (1985), reaching paradigm.
- Kellman, Gleitman & Spelke (1987), "Object and observer motion in the
  perception of objects by infants." *JEP:HPP*.
  <https://kellmanlab.psych.ucla.edu/files/kellman_gleitman_spelke_1987.pdf>
  — notably, unity is also obtained when the *observer* moves and the object is
  static, which is the motion-parallax version and is directly relevant to us.

Extensions and boundary conditions (refinements, not refutations):
- Johnson & Náñez (1995): 3D depth cues not necessary; a 2D computer-generated
  rod-and-box against a **textured background** suffices at 4 months.
- Johnson & Aslin (1996), "Perception of object unity in young infants: the
  roles of motion, depth, and orientation."
  <https://www.babylab.ucla.edu/wp-content/uploads/sites/8/2016/09/JohnsonAslin1996.pdf>
  — **without** a textured background, 4-month-olds are ambiguous. Background
  texture is load-bearing. Worth knowing before we build a blank-background test.
- Smith, Johnson & Spelke (2003), "Motion and edge sensitivity in perception of
  object unity."
  <https://www.babylab.ucla.edu/wp-content/uploads/sites/8/2016/09/Smith_etal2003.pdf>
- Johnson, S.P. (2004), "Development of perceptual completion in infancy."
  <https://www.babylab.ucla.edu/wp-content/uploads/sites/8/2016/09/Johnson2004.pdf>
- "Synchronous change and perception of object unity: evidence from adults and
  infants," *Cognition* (1999). <https://pubmed.ncbi.nlm.nih.gov/10476606/>
  — the unifying cue may be **synchronous change** more generally, not motion
  specifically. Architecturally interesting: it generalises "moves together" to
  "changes together", which is a cheaper and broader predicate.

### 2b. Developmental status — the correction that matters

Slater et al. (1990), "Newborn and older infants' perception of partly occluded
objects." <https://www.sciencedirect.com/science/article/abs/pii/016363839090004R>
and Slater et al. (1996), *Infant Behavior and Development* 19, 145–148.
<https://www.babylab.ucla.edu/wp-content/uploads/sites/8/2016/09/Slater_etal1996.pdf>

**Neonates perceive the rod display as two disjoint objects** — they do not
integrate across the occluder even under common motion. Unity perception from
common motion appears around 2–4 months; trajectory continuity later (6 months,
or 4 months with a narrow occluder).

There is a dissenting line arguing for perceptual completion in newborns
(Valenza & Bulf, "Early development of object unity: evidence for perceptual
completion in newborns")
<https://www.researchgate.net/publication/51221871> — so call the newborn
question **CONTESTED**, with the majority position being that it develops.

Modelling support for it being learnable rather than given: Franz & Triesch
(2010), "A unified computational model of the development of object unity,
object permanence, and occluded object trajectory perception."
<https://www.sciencedirect.com/science/article/abs/pii/S0163638310000986>
— **this is the most directly relevant citation for our purposes**: the
developmental trajectory is reproducible by a learning model, i.e. it does not
need to be seeded.

### 2c. Replication status of the FIELD — genuinely troubled, and you must know which part

The brief was right to ask. Infant cognition has a real methodological
controversy, and it centres on the **violation-of-expectation (VoE)** looking-time
method:

- Paulus, M. (2022). "Should infant psychology rely on the violation-of-expectation
  method? Not anymore." *Infant and Child Development* 31, e2306.
  <https://onlinelibrary.wiley.com/doi/full/10.1002/icd.2306>
  Argues VoE "relies on too many questionable assumptions, that its conceptual
  foundations are thin, and that its findings are empirically not conclusive,"
  and that inferences from it are "too speculative to allow for solid progress."
- Stahl & Kibbe (2022), "Great expectations: the construct validity of the
  violation-of-expectation method." <https://www.bu.edu/cdl/files/2022/07/2022-StahlKibbe-ICD.pdf>
- Long-standing critiques: **Haith** and **Bogartz** — longer looking can index
  fear, preference, anticipation, surprise, annoyance or scepticism; low-level
  perceptual confounds are rarely excluded.
- Defence: Margoni, Surian & Baillargeon (2024), "The violation-of-expectation
  paradigm: a conceptual overview," *Psychological Review* 131(3), 716–748.
  <https://infantcognition.web.illinois.edu/wp-content/uploads/2024/04/Margoni-F.-Surian-L.-Baillargeon-R.-2024.-The-violation-of-expectation-paradigm-A-conceptual-overview.-Psychological-Review-1313-716-748.pdf>
- Multi-lab variability work: ManyBabies Consortium / Frank et al. (2020),
  "Quantifying sources of variability in infancy research using the
  infant-directed-speech preference," *AMPPS*.
  <https://journals.sagepub.com/doi/10.1177/2515245919900809>
- A measured philosophical treatment: "Growth From Uncertainty: Understanding the
  Replication 'Crisis' in Infant Cognition," *Philosophy of Science*.
  <https://www.cambridge.org/core/journals/philosophy-of-science/article/abs/A432336A2364A9F8954A0765CE5CC155>

**Crucially, the crisis does not land equally on all of Spelke's claims.** The
replication trouble concentrates in the *social/high-level* end — implicit theory
of mind, goal understanding, anticipatory-gaze measures, infant "moral"
evaluation. **The perceptual object-unity finding is comparatively safe**: it is
old, has been replicated across labs and paradigms, uses habituation rather than
surprise-at-impossible-events, and — the strongest point — **converges with a
reaching measure and with adult psychophysics.** I found no failed replication of
the common-motion unity effect itself. (Absence of evidence caveat: I did not run
a systematic replication-database search; see gaps.)

### 2d. Is "core knowledge" as a framework safe to lean on? — CONTESTED, and lean on the perception, not the framework

The single most useful source here, and a pleasant surprise:

**Scholl, B.J. (2023). "Perceptual (roots of) core knowledge." *Behavioral and
Brain Sciences* 46, e140.** doi:10.1017/S0140525X23003023
<https://perception.yale.edu/papers/24-Scholl-BBSComment.pdf>

Scholl — a hard-nosed adult vision scientist, not a nativist ally — argues that
"some core knowledge may be rooted in — or even **identical to** — well-
characterized mechanisms of **mid-level visual perception and attention**." He
lists cohesion as a *success* case with a two-way empirical payoff:

> "Many core knowledge principles apply to objects but not non-solid
> substances, and early work showed how cohesion violations (failures to
> maintain rigid boundaries and internal connectedness) frustrate infants'
> object tracking (e.g., Huntley-Fenner, Carey & Solimando, 2002; Spelke & Van
> de Walle, 1993). This led directly to the discoveries in adult vision that
> cohesion violations also frustrate attentional tracking (vanMarle & Scholl,
> 2003) and the maintenance of object-file representations — even when just
> viewing a single object split into two (Mitroff, Scholl & Wynn, 2004)."

**This is the adjudication the rung should rest on: cohesion is not merely an
infant-literature claim, it is a mid-level-vision mechanism confirmed in adults
with independent methods.** That is a much stronger footing than "Spelke said so."

What Scholl says is *overstated* in Spelke's framework — and therefore what we
should NOT import:
- that core knowledge transcends mid-level vision into **prosociality**
  (Hamlin, Wynn & Bloom 2007 helper/hinderer): "no work has yet suggested that
  visual processing itself directly extracts representations of helping,
  hindering, or prosociality."
- entanglement with **language**.
- the "**physics engine**" framing (Ullman, Spelke, Battaglia & Tenenbaum 2017):
  Scholl notes such frameworks "do not necessarily abide by the constraints of
  encapsulated mid-level vision" and may be "orthogonal" rather than important
  here.
- He also notes adult mid-level vision is in places **more** sophisticated than
  infant core knowledge (causal history, soft-material physics, "unfinishedness"),
  so the match is imperfect in both directions, and there is "no principled way
  to demarcate which results we expect to 'match' and which we do not."

Also see Schulz, A.W. (2023), "Core knowledge and its role in explaining uniquely
human cognition: some questions," *BBS* 46, e141
(doi:10.1017/S0140525X23003199) — argues domain-general learning capacities must
be admitted alongside, and there is no clear reason to doubt uniquely human
cognitive adaptations. And Revencu & Csibra (2023), review of *What Babies Know*,
*Mind & Language*. <https://onlinelibrary.wiley.com/doi/10.1111/mila.12482>

### 2e. Adjudication table for §2

| Sub-claim | Verdict |
|---|---|
| Infants segment objects by common motion | **SUPPORTED** (Kellman & Spelke 1983 + reaching converging evidence) |
| Common motion works when static form does not | **SUPPORTED** (same; stationary displays fail) |
| This precedes static-form segmentation developmentally | **SUPPORTED** |
| "Long before" / present from birth / innate | **REFUTED** — newborns fail (Slater 1990/1996); emerges ~2–4 months; contested minority claims completion in newborns |
| Cohesion / continuity / contact as a *perceptual* system | **SUPPORTED**, and endorsed by an adult-vision critic (Scholl 2023) |
| Core knowledge as an innate central-cognition framework | **CONTESTED** — lean on the perception, not the framework |
| The finding is threatened by the replication crisis | **Largely NO** for this specific finding; **YES** for the social/VoE end of the literature |
| Motion is the cue | Possibly narrower than the truth — "**synchronous change**" (*Cognition* 1999) may be the real predicate |

### Gaps I could not resolve in §2

- I did not run a systematic search of replication databases (e.g. Curate Science,
  the ManyBabies project list) for a direct replication attempt on Kellman &
  Spelke 1983. **Source that would settle it:** the ManyBabies project registry
  and a forward-citation sweep for "failed to replicate" + rod-and-box. My claim
  that it is safe rests on convergent-method evidence, not on a registered
  replication — treat it as strong-but-not-airtight.
- Effect sizes. I did not retrieve the original *n* or effect size for Kellman &
  Spelke 1983. Given this session's standing rule (**power the gate before the
  endgame**), if the rung's design targets quantitatively match human infant
  numbers, get those numbers first.

## 3. LOG-POLAR RETINOTOPY

### HEADLINE: the claim is a chain of three links, and THE MIDDLE ONE IS BROKEN — on the record since 1981, never repaired.

"Log-polar map ⇒ rotation/scale become translation ⇒ **therefore biology gets
invariance cheaply**." Link 1 is roughly right with a correction; link 3 is
right; **link 2 — that biology exploits the property — is REFUTED.**

### 3a. Mathematical form — SUPPORTED as approximation; naked `log(z)` REFUTED

The map is **not** `log(z)`. It is a **shifted** log, and in its modern form a
**wedge-dipole**.

- Schwartz, E.L. (1977). "Spatial mapping in the primate sensory projection."
  *Biological Cybernetics* 25:181–194.
  <https://link.springer.com/article/10.1007/BF01885636> — the original
  complex-log ("monopole") model.
- Schwartz, E.L. (1980). "Computational anatomy and functional architecture of
  striate cortex." *Vision Research* 20:645–669.
  <https://www.sciencedirect.com/science/article/abs/pii/0042698880900905>
  — introduces **`log(z + a)`**.
- Balasubramanian, M., Polimeni, J. & Schwartz, E.L. (2002). "The V1–V2–V3
  complex: quasiconformal dipole maps in primate striate and extra-striate
  cortex." *Neural Networks* 15(10):1157–1163.
  <https://pubmed.ncbi.nlm.nih.gov/12425434/> — the **wedge-dipole**: a constant
  azimuthal *shear* composed with a *dipole* map. Measured macaque parameters
  a = 0.6, b = 80.0, α = 0.8.
- Horton & Hoyt (1991): the standard human CMF formula **M = 17.3/(0.75 + E)**
  mm/deg. <https://nben.net/Cortical-Magnification/>

**The `0.75°` in the standard human formula IS the shift parameter `a`.** The
formula everyone uses is the derivative of a `log(z+a)` map, not a `log(z)` map.
Beyond ~5–10° eccentricity the two coincide; near the fovea they differ
qualitatively (`log(z)` diverges; `log(z+a)` has finite maximum magnification).

### 3b. Deviations — CONTESTED; two substantial, quantified failures

**Radial structure: good.** Inverse-linear CMF fits well. Duncan & Boynton
(2003), *Neuron* 38:659–671, report power-function exponents ≈ **−0.85** relating
CMF to acuity, close to the model's −1.
<https://www.sciencedirect.com/science/article/pii/S0896627303002654>

**Angular structure: fails.** Himmelberg, Winawer & Carrasco (2021), *eLife*
10:e67685. <https://pmc.ncbi.nlm.nih.gov/articles/PMC8378846/> — V1 surface area
is **~80% greater for the horizontal than the vertical** meridian, and **~80%
greater for lower than upper vertical**. A log-polar map is rotationally
symmetric in θ **by construction and cannot represent this.** Not a small
correction.

**Foveal confluence: fails.** Schira, Tyler, Spehar & Breakspear (2010), *PLoS
Comput Biol* 6(1):e1000651.
<https://doi.org/10.1371/journal.pcbi.1000651> — "the classical Log-Polar model
**fails to predict the empirical data**." Log-polar predicts V2/V3 converge to a
point at the foveal centre; empirically they form **parallel bands**, and V2/V3
are *larger* than V1 below 0.75°. They propose a Banded Double-Sech model.

**V2/V3:** the wedge-dipole covers V1/V2/V3 with one map family — but only by
adding a **quasiconformal shear** term precisely because the real map violates
the conformality that pure log-polar assumes. (Note the tie-in to §1B: the
deviation-from-conformal is exactly what the Beltrami-coefficient work measures.)

### 3c. Does BIOLOGY exploit rotation/scale→translation? — REFUTED. This is the section's load-bearing correction.

**Cavanagh, P. (1981). "Size invariance: reply to Schwartz." *Perception*
10:469–474.**
<https://cavlab.net/MyRWResources/MyPDFs/PDF1981/Cavanagh1981.pdf>

Cavanagh states Schwartz's position exactly as the supervisor does — the
log-polar map is "the basis of the size and rotation invariances obtained in
perception" — and gives four objections:

1. **Only origin-centred transforms work.** "the only size and rotation changes
   for which the log polar mapping alone is invariant are those centred at the
   origin."
2. **No translation invariance — and it is catastrophic.** "patterns represented
   on the log polar mapping have **no position (translation) invariance**.
   Changing the location of the input pattern **radically alters** its
   representation." He demonstrates two identical letter Rs either side of the
   origin producing entirely different log-polar representations.
3. The cortical surface cannot in fact be laid flat as proposed (Daniel &
   Whitteridge 1961).
4. **A failed empirical prediction.** Schwartz's fitted transform "is only log
   polar in the periphery—beyond 5 deg eccentricity... and not at all in the
   lower hemifield of the cat. **There is, however, no evidence of the
   deficiencies in size invariance for the fovea or for the lower hemifield of
   the cat that would be expected if Schwartz's proposal were correct.**"

Cavanagh's conclusion — and the defensible residual position:

> "It is more likely that the intriguing log polar nature of the striate
> topology reflects simply **the optimum packing solution for a high-resolution
> fovea and a low-resolution periphery**."

**Where the field actually went.** Invariance ("tolerance") in the ventral stream
is now understood as **learned from temporal contiguity through the hierarchy**,
not read off a coordinate system:
- Li, N. & DiCarlo, J.J. (2010). "Unsupervised natural visual experience rapidly
  reshapes size-invariant object representation in inferior temporal cortex."
  *Neuron* 67(6):1062–1075. <https://pubmed.ncbi.nlm.nih.gov/20869601/>
  — the same unsupervised experience reshapes position *and* size tolerance,
  and it works **without eye movements**.
- Rust, N.C. & DiCarlo, J.J. (2010). *J. Neurosci.* 30(39):12978–12995.
  <https://www.jneurosci.org/content/30/39/12978>

A plastic, learned, hierarchical mechanism — which would be **redundant** if the
V1 map already delivered invariance.

Even the machine-vision review concedes the biological point: Traver &
Bernardino (2010) note "the rotation and scaling invariance properties **only
hold when objects are centered in the visual field**," and scare-quote
*"invariance"* throughout.

**A killer internal tension, worth stating on its own:** the standard fix for the
foveal singularity destroys the invariance. Traver & Bernardino: "**The log(z+a)
model lacks the property of exact scale invariance.**" *You cannot have the
biologically plausible version of the map and the invariance property at the same
time.* If we adopt log-polar for foveation, we do not get invariance thrown in.

Schwartz replied (Schwartz 1981, *Perception* 10:455–468,
<https://pubmed.ncbi.nlm.nih.gov/7335444/>; Schwartz 1983, *Vision Research*
23(8):831–835, <https://pubmed.ncbi.nlm.nih.gov/6623943/>). **The content of the
1983 reply could not be resolved** — no abstract on PubMed, full text paywalled.
See gaps.

### 3d. Machine vision — SUPPORTED historically; CONTESTED as current practice

Traver, V.J. & Bernardino, A. (2010). "A review of log-polar imaging for visual
perception in robotics." *Robotics and Autonomous Systems* 58(4):378–398.
<https://vislab.isr.tecnico.ulisboa.pt/wp-content/uploads/2012/12/10-ras-traver.pdf>

**Worked:** data reduction ("as much as 30 times smaller than uniformly-sampled
Cartesian images"); active target tracking — "foveated targets can be tracked
**without being explicitly segmented from the background**" (directly relevant to
us); time-to-collision and egomotion "due to its favorable geometric
arrangement"; binocular vergence. Their summary: real-time active tracking and
time-to-impact are what it is "clearly best suited to."

**Didn't work:** "**linearities and translation invariance are certainly lost**";
Cartesian algorithms don't port, so "specific algorithms are required"; hardware
sensors had noise problems from unequal sensing-element sizes, and the
"**hard-coded geometry layout** makes it very difficult, if not impossible, to
experiment with different sensor parameters." Most researchers reverted to
software remapping of Cartesian images — **which forfeits the speed rationale
entirely.** (Note for us: that is the same trap. If we log-polar-remap a
uniformly captured frame, we pay the cost and get none of the bandwidth win.)

**Current status:** dedicated log-polar sensors never left the lab. Live
descendants are eye-tracked **foveated rendering** in VR (which gets the
bandwidth win *without* log-polar geometry) and log-polar layers inside deep nets
(Esteves et al., "Polar Transformer Networks," ICLR 2018;
<https://arxiv.org/pdf/2002.05388>).

### 3e. Does uniform log-polar sampling reproduce primate RGC density? — CONTESTED (right to first order)

**Right:** uniform (log r, θ) sampling gives RF size ∝ eccentricity and density
∝ 1/r², matching the classic linear-with-eccentricity finding. And the
retina→cortex link is genuinely tight — Wässle, Grünert, Röhrenbeck & Boycott
(1990), *Vision Research* 30:1897–1911,
<https://pubmed.ncbi.nlm.nih.gov/2288097/>: ganglion cell density accounts for
cortical magnification **without any additional foveal amplification**. Confirmed
in a second species by Chaplin, Yu & Rosa (2013), *J. Comp. Neurol.*
521(5):1001–1019 — "each V1 cell receives information from a similar number of
retinal neurons, throughout the visual field."

**Wrong, twice:**
1. **Singularity** — 1/r² diverges; real RGC density is finite at the centre.
   Hence `e₂ = 0.75°`.
2. **Rotational symmetry is false.** Watson, A.B. (2014). "A formula for human
   retinal ganglion cell receptive field density as a function of visual field
   location." *Journal of Vision* 14(7):15.
   <https://pubmed.ncbi.nlm.nih.gov/24982468/> — requires **four separate
   meridian-specific parameter sets**. Drawing on Curcio & Allen (1990), *J.
   Comp. Neurol.* 300:5–25: in peripheral retina **nasal exceeds temporal by
   >300%**, **superior exceeds inferior by ~60%**.

### 3f. Adjudication table for §3

| Sub-claim | Verdict | Deciding citation |
|---|---|---|
| Map is log-polar | **SUPPORTED as approximation**; `log(z)` **REFUTED** — it is `log(z+a)`/wedge-dipole | Balasubramanian et al. 2002; Horton & Hoyt 1991 |
| Deviations are minor | **CONTESTED** — radial good; foveal confluence and ~80% polar-angle anisotropy are real failures | Schira et al. 2010; Himmelberg et al. 2021 |
| **Biology exploits rotation/scale→translation** | **REFUTED** | **Cavanagh 1981**; Li & DiCarlo 2010 |
| Machine vision exploits it | **SUPPORTED** historically, **CONTESTED** now | Traver & Bernardino 2010 |
| Uniform log-polar ⇒ primate foveation profile | **CONTESTED** — first-order yes; singularity + meridional asymmetry no | Watson 2014; Curcio & Allen 1990 |
| Foveation as optimal packing | **SUPPORTED** — endorsed even by the chief critic | Cavanagh 1981 |

**What to keep: foveation-as-packing-optimum. What to drop: invariance-for-free.**

### Gaps I could not resolve in §3

- **Schwartz's 1983 rebuttal** (*Vision Research* 23:831–835) — paywalled, no
  abstract. We have Cavanagh's objections in full and Schwartz's position as
  Cavanagh characterises it, but **not Schwartz's counter in his own words.**
  If the REFUTED verdict on 3c is going to carry architectural weight, this is
  the one source worth buying.
- Watson (2014) fitted meridian constants — PDFs redirect, JOV 403. We have the
  model structure and asymmetry magnitudes, not the constants.

## 4. CALIBRATION LIMITS AND ADAPTATION

### HEADLINE: "plastic but bounded" is SUPPORTED. "Perception fails rather than degrades" is NOT — and the classic evidence for radical perceptual recalibration is a documented myth.

### 4a. Inverting / reversing goggles — the standard story is REFUTED, and this is the section's most important finding

The textbook claim (vision "flips back" after prolonged goggle wear, coinciding
with restored skilled action) is **false**, and its falsity is documented by
someone who went and read the primary sources.

**Klein, C. "Kicking the Kohler Habit."** *Philosophical Psychology*.
<https://colinklein.org/papers/KohlerPhilPsy.pdf>

Klein names the standard story **KH** and states directly:

> "Unfortunately, **KH is wrong**. Subsequent experiments have shown that visual
> re-inversion is a complicated phenomenon at best, and does not coincide with
> the return of sensorimotor knowledge. Perhaps most strikingly, **Kohler himself
> doesn't appear to believe in KH**, and support for it is difficult to find in
> his work. The habit of relying on Kohler's supposed results to make
> philosophical claims thus turns out to be a philosophical liability rather
> than an asset."

And: "experiments specifically designed to test KH provide good evidence that it
is false."

**The decisive experiment, now verified directly (gap closed):**

**Linden, D.E.J., Kallenbach, U., Heinecke, A., Singer, W. & Goebel, R. (1999).
"The myth of upright vision: a psychophysical and functional imaging study of
adaptation to inverting spectacles." *Perception* 28(4):469–481.**
<https://journals.sagepub.com/doi/10.1068/p2820> ·
<https://pubmed.ncbi.nlm.nih.gov/10664787/> ·
open copy: <http://wexler.free.fr/library/files/linden%20(1999)%20the%20myth%20of%20upright%20vision.%20a%20psychophysical%20and%20functional%20imaging%20study%20of%20adaptation%20to%20inverting%20spectacles.pdf>

Four subjects, inverting prisms and mirror spectacles, six to ten days. Findings:

- **rapid adaptation of visuomotor functions**, but
- **no return of upright vision** reported by any subject;
- persistence of the transformed image independently confirmed via
  **shape-from-shading** perception (an objective check, not just self-report —
  this is what makes the study decisive rather than merely anecdotal); and
- **no alteration of early visual cortical retinotopy on fMRI.**

That last point is the strongest form of the result available: **the calibration
did not move at the level where the map lives.** Sensorimotor competence returned
regardless. Three independent measures (report, shape-from-shading, retinotopic
imaging) agree.

Primary and historical sources:
- Stratton, G.M. (1896/1897) — the original inversion experiments.
- Erismann & Kohler, the Innsbruck goggle experiments — see the historical
  review: "'The world is upside down' — The Innsbruck Goggle Experiments of
  Theodor Erismann (1883–1961) and Ivo Kohler (1915–1985)," *Cortex* (2017).
  <https://www.sciencedirect.com/science/article/abs/pii/S0010945217301314>
  (open copy:
  <https://www.allgemeine-psychologie.info/cms/images/stories/allgpsy_pub/Cortex%20The%20world%20is%20upside%20down.pdf>)

**What actually adapts:** *visuomotor coordination* returns to near-baseline.
**What does not (or not reliably):** *visual phenomenology* — many reports say
the world remains inverted even after motor competence returns.

**Consequence for us: sharply separate the sensorimotor calibration from the
perceptual one.** The evidence supports a system where action recalibrates
readily while the perceptual projection does not. If our architecture assumes one
shared calibration that both action and perception read, the goggle literature is
evidence against it. This is a real architectural constraint and it is the
opposite of what the folk version of the experiment suggests.

### 4b. Prism adaptation — SUPPORTED as plastic; well-parameterised

Prism adaptation is the well-behaved, heavily-studied case (unlike goggles).
- Redding, G.M. & Wallace, B. — "Applications of prism adaptation: a tutorial in
  theory and method." <https://www.researchgate.net/publication/7915327>
- "Prism Adaptation and Aftereffect: Specifying the Properties of a Procedural
  Memory System." <https://pmc.ncbi.nlm.nih.gov/articles/PMC311278/>
- "Towards a neuro-computational account of prism adaptation."
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6018603/>

Established facts worth importing:
- Adaptation **decomposes** into separable visual and proprioceptive shift
  components, whose relative magnitude depends on available cues (e.g. visible
  sound sources in the environment).
- It reaches an **asymptote**; further exposure increases *persistence*, not
  magnitude. (A calibration that saturates, then consolidates — a two-timescale
  structure.)
- It is a **procedural memory system**, with aftereffects.
- **Explicit knowledge REDUCES adaptation**: telling subjects about the prisms
  led to lower adaptation levels. Also inversely related to secondary cognitive
  load. So the calibration update is an implicit process that top-down knowledge
  interferes with rather than assists.
- Manipulable parameters: gradual vs abrupt introduction, feedback during
  trajectory vs endpoint only, exposure duration, movement speed, limb.

### 4c. Individual limits — SUPPORTED, with a solid number

**Chopin, A., Levi, D., Knill, D. & Bavelier, D. (2019). "The prevalence and
diagnosis of 'stereoblindness' in adults less than 60 years of age: a best
evidence synthesis." *Ophthalmic & Physiological Optics* 39(2).**
<https://onlinelibrary.wiley.com/doi/10.1111/opo.12607> ·
open: <https://hal.science/hal-03919204/document> ·
JOV version: <https://jov.arvojournals.org/article.aspx?articleid=2750983>

Four independent approaches converge on **~7% stereoblind** (bracketed 6.1–7.7%)
in adults under 60; other estimates 3–8%; higher in older adults.

Two caveats the paper itself makes, both useful to us:
- Prevalence "is highly dependent on the way in which stereopsis is measured" —
  presentation time, disparity magnitude, and test choice all move the number.
  **An instrument-dependent prevalence.** (Cf. this session's standing lesson
  about instruments; the same disease.)
- Some stereoblind participants **can pass stereotests by other cues** —
  i.e. the test can be defeated without the capacity. If we build a stereo
  diagnostic, it must be checked against this failure mode.

Also: "large individual differences as to how well one can appreciate depth from
binocular disparity" — the capacity is graded, not binary, notwithstanding the
label. See "50 Years of Stereoblindness: Reconciliation of a Continuum of
Disparity Detectors With Blindness for Disparity in Near or Far Depth."
<https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5697597/>

**So: "some people never free-fuse stereograms" — SUPPORTED, ~7%, with a
citable synthesis.**

### 4d. "Some people cannot interpret a fisheye" — I could not establish this. Treat as FOLK.

I found **no** primary source documenting individual inability to interpret
fisheye or strongly wide-angle images. What exists nearby is a *general* (not
individual-differences) literature on wide-angle distortion being perceptually
objectionable to more or less everyone beyond a FOV threshold — Vishwanath et al.
(2005) themselves note the local-slant mechanism fails to give correct results
above ~36° FOV, and there is an engineering literature on rectifying it
(<https://arxiv.org/pdf/2011.12108>).

**Verdict: NOT-ADDRESSED-BY-THE-LITERATURE as an individual-limit claim.** This
one looks like the supervisor generalising from the (real) stereoblindness case
to a second case that has not been studied. Do not repeat it as established.
**Source that would settle it:** an individual-differences study of wide-angle
image interpretation; I do not believe one exists, which makes it a cheap
original experiment if we want it.

**A second pass found no rigorous source either — but did surface useful
vocabulary and two hints:**
- The named phenomenon is **"marginal distortion"**: under wide-angle linear
  perspective, spheres and faces appear oblong toward the corners.
  <https://en.wikipedia.org/wiki/Perspective_distortion_(photography)>
- Hertzmann (2024) notes two things that make the folk claim *plausible* without
  establishing it: "**a viewer is not necessarily aware of marginal
  misperceptions** due to linear perspective," and "**prior knowledge** allows a
  viewer to recognize a misleading depiction of a familiar object." So
  interpretation is knowledge-dependent — which predicts *variation*, but nobody
  has measured its distribution.
- These are consistent with a **graded, knowledge-modulated** ability, i.e. the
  opposite of the "fails rather than degrades" framing in §4e.

### 4e. "Outside its range perception FAILS rather than degrades" — REFUTED as stated

The evidence goes the other way in every case I checked:
- Vishwanath et al. (2005): invariance **degrades progressively** beyond ±45° as
  slant-estimate uncertainty rises — a graceful, uncertainty-driven falloff, not
  a cliff.
- Stereopsis: a **continuum** of disparity detectors; "stereoblindness" is a
  label on a graded distribution, not a discrete failure (PMC5697597).
- Prism adaptation: asymptotes smoothly.
- Mirror perception (§1d): does not fail — it produces *systematically wrong*
  answers with a frontal prior. **Confidently wrong, not absent.**

This last point connects to a standing memory item: **confabulation is the
default.** Out-of-range calibration produces a confident incorrect percept, not a
refusal. Our architecture should expect graceful-but-wrong, and should not build
a "perception fails" branch expecting silence.

**This is the clearest case in the whole document of a supervisor claim that the
literature contradicts.**

### 4f. Cross-cultural picture perception (Hudson) — the caution was WARRANTED; do not cite this literature as evidence

The brief asked for an explicit reliability assessment. Mine: **do not build on
it.**

- Hudson, W. (1960) — the depth-cue picture test classifying viewers as "2D" or
  "3D" perceivers.
- Deregowski, J.B. (1972). "Pictorial perception and culture," *Scientific
  American*. <http://www.holah.karoo.net/deregowskistudy.htm>

Documented problems, several conceded within the literature itself:
- **Stimulus confound:** Hudson's pictures **omit texture gradient**, which is
  arguably the most important pictorial depth cue for Western *and* non-Western
  viewers. The test under-specifies depth for everyone and then attributes the
  resulting failure to the viewer.
- **Materials confound:** Deregowski found that substituting familiar cloth for
  unfamiliar paper moved responses toward "correct" — the effect tracked
  material familiarity, not perceptual capacity.
- **Provenance:** early reports were, in the literature's own summary,
  "anecdotal... with ethnocentric colonial overtones, making 'the natives' look
  simple," and were "unscientific, subjective, and couldn't be replicated."
- **Construct validity:** the dependent measure is response to a verbal question
  about a convention-laden artefact, confounding pictorial *convention* learning
  with *perceptual* capacity. The charitable reading of the whole literature is
  that it demonstrates conventions are learned — which is uncontroversial and
  does not require the cross-cultural framing.

**Verdict: unreliable as evidence about perceptual calibration limits.** If we
want a "picture conventions must be learned" claim, source it from developmental
or training studies, not from here. Citing Hudson at face value would be a
methodological and ethical error.

### Gaps I could not resolve in §4

- **Individual limits on ADAPTATION specifically** (as opposed to individual
  limits on stereopsis). I did not find a study reporting the distribution of
  prism-adaptation magnitude across individuals with an explicit claim about
  non-adapters. The Redding & Wallace tutorial would likely cite one; I did not
  retrieve its full text. **This is the gap most worth closing** if the
  architecture depends on "some agents never acquire calibration X."
- ~~Linden et al. citation unverified~~ — **CLOSED**, verified above
  (*Perception* 28(4):469–481, 1999), with more supporting detail than expected
  (fMRI retinotopy unchanged; shape-from-shading as objective confirmation).
- Whether any study post-1999 has revisited inverting adaptation with modern
  imaging over longer exposure. I did not search for this. Linden et al. ran
  6–10 days; Stratton and Kohler ran longer, and the possibility that
  *much* longer exposure produces perceptual change is not excluded by a
  10-day null.

## 5. MULTIBODY FACTORIZATION — the borrowable engineering

### HEADLINE: borrow the MATHEMATICS, do not borrow the PIPELINE. And the benchmark numbers are not deployment numbers.

### 5a. Tomasi–Kanade — SUPPORTED (it is a theorem)

Tomasi, C. & Kanade, T. (1992). "Shape and motion from image streams under
orthography: a factorization method." *IJCV* 9(2):137–154.
<https://link.springer.com/article/10.1007/BF00129684> ·
<https://people.eecs.berkeley.edu/~yang/courses/cs294-6/papers/TomasiC_Shape%20and%20motion%20from%20image%20streams%20under%20orthography.pdf>

**The rank 3 vs rank 4 question — the load-bearing detail, and the multibody
literature uses the OTHER one from the one usually taught:**

| Matrix | Construction | Rank | Used by |
|---|---|---|---|
| **Registered** W̃ (2F×P) | per-frame centroid subtracted | **3** | Tomasi–Kanade single-body |
| **Unregistered** W (2F×P) | raw coordinates | **≤ 4** | Costeira–Kanade multibody |

Tomasi–Kanade get rank 3 **because they register first** — translation is
recovered as the row means of W and subtracted. Unregistered, translation adds a
rank-1 outer-product term, so each rigid body spans a **linear subspace of
dimension ≤ 4** (a 3-D *affine* subspace embedded as a 4-D *linear* one).

**The implementer's trap: you cannot register per-body in the multibody case,
because registration needs the memberships, which is what you are solving for.**
Multibody is therefore *forced* into the 4-dimensional form. This is why
multibody is strictly harder than K copies of the single-body problem, and it is
the origin of several degeneracies.

Assumptions you buy: affine/orthographic camera (no perspective; valid when depth
≪ distance and FOV narrow); rigidity; full measurement matrix for the clean SVD
path; correct correspondence (tracking assumed solved); metric upgrade needs a
separate corrective transform from orthonormality constraints.

### 5b. Costeira–Kanade — SUPPORTED as mathematics, CONTESTED as engineering

Costeira, J. & Kanade, T. (1998). "A multibody factorization method for
independently moving objects." *IJCV* 29(3):159–179.
<https://link.springer.com/article/10.1023/A:1008000628999> ·
<https://publications.ri.cmu.edu/storage/publications/pub_files/pub1/costeira_joao_1994_1/costeira_joao_1994_1.pdf>

SVD X = UΣVᵀ, keep r = 4K right singular vectors V_r, define the **Shape
Interaction Matrix Q = V_r V_rᵀ** (the orthogonal projection onto the row space).
Property: **Q_ij = 0 iff points i,j belong to different objects.** Q is invariant
to object motion and coordinate frame. Segment by permuting Q to block-diagonal
form, then run Tomasi–Kanade per block.

Kanatani later gave the correct conditional statement: Q is block-diagonal up to
permutation **only if the subspaces are linearly independent** (ICCV 2001; *IJIG*
2002, <https://www.worldscientific.com/doi/abs/10.1142/S0219467802000585>). That
clause is the entire content of the failure modes below.

### 5c. Failure modes — the important part

**Noise sensitivity — SUPPORTED, uncontested, independently reproduced over 20+
years.**

Wu, Y., Zhang, Z., Huang, T.S. & Lin, J.Y. (2001). "Multibody Grouping via
Orthogonal Subspace Decomposition." CVPR 2001.
<https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/Multibody-Grouping-via-Orthogonal-Subspace-Decomposition.pdf>

> "The performance... **degrades quickly** when data points are corrupted with
> noise; the reason is that **the relationship between data noise and the
> coefficients of Q is very complicated**, making it hard to determine an
> appropriate threshold."

> "The nice property of the shape interaction matrix Q is valid **only for the
> ideal case where there are no noise and outliers**... even if two feature
> points belong to different objects, **Q_ij may not be equal to zero**."

Ji, P., Salzmann, M. & Li, H. (2015). "Shape Interaction Matrix Revisited and
Robustified." ICCV 2015. <https://arxiv.org/pdf/1509.02649> — same verdict 15
years later: "provably correct for independent motions and noise-free
measurements, its accuracy **quickly decreases in the presence of noise,
outliers, or degenerate motions**." They also identify a **magnitude bias**:
intra-cluster affinities scale with data-point magnitude, so **points near the
origin are the most noise-sensitive** — fixed by row-normalising V_r.

Hard number: raw SIM scores **7.80%** mean clustering error on Hopkins155 vs
SSC 2.18% and RSIM 0.89%. On corrupted Extended Yale B: SIM 65.10% vs RSIM 3.70%.
**The original SIM is not competitive on real data.**

**Degenerate / dependent motions — SUPPORTED, and this is the common case, not
the tail.**

Zelnik-Manor, L. & Irani, M. (2003/2006). "Degeneracies, dependencies and their
implications in multi-body and multi-sequence factorizations." CVPR 2003,
doi:[10.1109/CVPR.2003.1211482](https://doi.org/10.1109/CVPR.2003.1211482);
*IJCV* 68(2):205–216, 2006.
<https://link.springer.com/article/10.1007/s11263-006-5157-4>

> ⚠️ The sub-agent could **not retrieve the full text** (both mirrors failed);
> the specific rank arithmetic below is from secondary sources. Flagged.

When two bodies' subspaces are only partially independent they intersect, and
**Q is not block-diagonal even with zero noise** — a structural, not numerical,
failure. Sources of dependence in practice:
- **Articulated bodies** (limbs sharing a joint) — subspaces intersect by
  construction. Spawned its own literature: Yan & Pollefeys, ECCV 2006.
  <https://link.springer.com/chapter/10.1007/11744085_8>
- **Degenerate individual motions** — pure translation, planar structure,
  rotation about a common axis all drop a body's subspace below dimension 4,
  breaking the hard-coded r = 4K.

Xu, Cheong & Li (2019): real scenes are typified by "**near-degenerate**
scenarios such as a scene that is almost but not quite planar, or a motion that
is rotation-dominant with a non-vanishing translation."
<https://arxiv.org/pdf/1908.06087>

**Model selection (number of bodies) — CONTESTED bordering REFUTED. The one most
likely to bite us.**

Xu, Cheong & Li, bluntly: a noise-free affinity matrix "**rarely exists in
real-world problems**. The modified rule of gap heuristic is purported to deal
with noisy affinity matrix but **has seldom worked well in practice**" — and they
class it as "essentially still an **open research problem**" in 2019, about a
problem posed in 1998.

Rank selection is the same problem: Ji et al. note the SIM "yields **poor results
if the incorrect rank is employed**." Their ablation is instructive —
SIM 7.80% → +normalisation/powering 5.77% → **+rank determination 3.17%** → full
RSIM 0.89%. **Most of the achievable gain lives in rank/model selection**, i.e.
that is where the naive method most badly fails.

**⚠️ THE UNDER-ADVERTISED CAVEAT: every method above still takes K as INPUT on
Hopkins155.** The benchmark supplies the number of motions. Published sub-1%
figures are *conditional on knowing K*, which we will not know in deployment.

**Missing data / occlusion — CONTESTED; structurally breaks the method.**

The SVD defining Q **cannot be computed at all** on an incomplete matrix — a hard
break, not a degradation. Standard workaround is an expensive two-step
completion-then-cluster, and completion is itself open. The two SSC coping
strategies fail characteristically (Ji et al. §5.3–5.4): **SSC-R** (drop
incomplete tracks) discarded ~25% of data; **SSC-O** (treat missing as outliers)
"**tends to group the trajectories with missing entries in a single cluster**" —
i.e. **it segments by occlusion status instead of by motion**. That is a nasty,
systematic failure mode worth knowing before we trust any such output. On
semi-dense Hopkins outdoor sequences **16.66% of entries were missing on
average** — occlusion is not rare.

### 5d. Successors, and a result that matters for a from-scratch implementer

Standard benchmark: Tron, R. & Vidal, R. (2007). "A benchmark for the comparison
of 3-D motion segmentation algorithms." CVPR 2007.
<http://www.vision.jhu.edu/data/hopkins155/> — 155 sequences, 2 or 3 motions,
104 checkerboard / 38 traffic / 13 articulated, complete data, **no outliers**.

Mean classification error % (from Ji et al. Table 1):

| Method | 2 motions | 3 motions | Overall |
|---|---|---|---|
| SIM (Costeira–Kanade + spectral) | 6.50 | 12.26 | **7.80** |
| LRR | 4.10 | 9.89 | **5.41** |
| EDSC | 2.67 | 8.06 | **4.04** |
| SSC | 1.53 | 4.40 | **2.18** |
| EDSC-H | 0.86 | 2.49 | 1.23 |
| **RSIM** | 0.65 | 1.71 | **0.89** |

Runtimes/sequence: SIM 0.02s, RSIM 0.18s, SSC 0.92s, LRR-H 1.09s.

Key successors: **GPCA** (Vidal, Ma & Sastry, PAMI 2005); **SSC** (Elhamifar &
Vidal, *PAMI* 35(11):2765–2781, 2013, <https://arxiv.org/abs/1203.1005>);
**LRR** (Liu et al., *PAMI* 35(1):171–184, 2013); **ALC** (Rao, Tron, Vidal & Ma,
*PAMI* 32(10):1832–1845, 2010).

**THE UNIFICATION RESULT — the single most actionable finding here.** Ji et al.
show LRR and EDSC are **equivalent to the SIM in the noise-free case** (their
optimal solutions take the form V𝒫(Σ)Vᵀ, "a modified version of the SIM"), and
conclude:

> "Many recent subspace clustering methods actually **did not go far beyond the
> 20-year-old SIM method**, but rather had indirect connections to it."

Practically: SIM + row-normalisation + elementwise powering (γ ≈ 3–5) +
principled rank selection goes from 7.80% → **0.89% at 0.18s/sequence**, beating
SSC's 2.18% at 0.92s. **The cheap classical method, properly conditioned, beats
the expensive convex one.**

### 5e. Is Hopkins155 saturated? — SUPPORTED, strongly. Do not trust the numbers.

- **Arrigoni & Pajdla (ICCV 2019)**, the sharpest version: methods achieve very
  low error "**However, the tracks available in the dataset are not realistic at
  all since they were filtered with the aid of manual operations**."
  <https://arxiv.org/pdf/1905.09043> — **the tracks are hand-cleaned.**
- **Xu, Cheong & Li (2019)**: sequences have "small field-of-view and are
  dominated by pure camera rotation"; the fundamental-matrix model is "generally
  eschewed, due to the **lack of perspective effects**."
- **Ji et al.**: even SIM gets 75.56% accuracy, "confirming that this dataset only
  contains **small amount/magnitude of noise and obeys the independent subspace
  assumption reasonably well**."
- A replacement benchmark exists for this reason: *Pattern Recognition* (2016),
  "A collection of challenging motion segmentation benchmark datasets."
  <https://www.sciencedirect.com/science/article/abs/pii/S003132031630156X>

**Treat published sub-1% figures as a statement about the benchmark, not about
the method.** (This is the same disease as our own RUN 15 correction: the
machinery was fine, the eval SET was the error.)

### 5f. Still live in 2026? — superseded for the APPLICATION, live as MACHINERY

Motion segmentation as a video task is now dominated by learned methods —
representative current work: Huang, N. et al. (2025). "Segment Any Motion in
Videos." CVPR 2025. <https://arxiv.org/abs/2503.22268> — long-range 2D tracks +
DINO semantic features + SAM2. Note the shape: **it still consumes trajectories,
but decides membership with learned semantics rather than subspace geometry.**
The geometric prior was replaced by a semantic one.

Subspace clustering itself migrated rather than died (human motion segmentation,
hyperspectral, deep subspace clustering).

### 5g. Recommendation for us

**Borrow the mathematics. Do not borrow the pipeline.**

For: the rank-4-per-rigid-body fact is a **theorem**, free, needs no training
data, is **unsupervised and training-free** (rare and valuable when we have no
labels), **cheap** (0.18s/seq), and **interpretable** — when it fails you can
inspect Q and see why.

Against: affine camera is a real restriction; **model selection is unsolved**;
dependent/degenerate motions are the common case; occlusion breaks the SVD
outright; benchmark numbers don't transfer; tracking is assumed solved.

Concrete path if borrowing:
1. Implement Tomasi–Kanade **registered rank-3** first as a unit-testable core.
2. For multibody use the **unregistered rank-4** form. Do not attempt per-body
   registration.
3. Build Q = V_r V_rᵀ but **never segment on raw Q** — apply Ji et al.'s three
   steps (row-normalise V_r, power the affinity γ≈3–5, principled rank
   selection). Small delta, ~7pp gain.
4. Segment with normalised cuts, not permutation search.
5. **Test on degenerate motions from day one** — pure translation, planar, shared
   rotation axis. Do not let a clean benchmark tell you it works.
6. Treat K as a separate, hard, unsolved subproblem; design so it can be supplied
   externally.
7. Validate on something with **real perspective** (KITTI-derived), not only
   Hopkins155.

### Gaps I could not resolve in §5

- Full text of Zelnik-Manor & Irani CVPR 2003 (both mirrors failed) — degeneracy
  rank mechanics rest on secondary sources.
- Primary-source verification of the LSA (~4.94%) and ALC (~3.56%) Hopkins155
  figures.
- Author list of the *Pattern Recognition* 2016 benchmark paper (paywalled).

## 6. GRAPHICS AS THE ENUMERATED TAXONOMY (per-surface calibration, forward problem)

### HEADLINE: SUPPORTED, and this is the best section in the document. Graphics has the taxonomy fully enumerated, named, costed, and shipped — but NOT the assignment problem, which is ours.

The creator's structural argument holds. Graphics does **not** treat mirror /
window / TV / water as different phenomena. It treats them as **one mechanism —
a secondary view with its own view matrix and its own clip plane — instantiated
per surface**, differing only in how the matrix is derived and how the result is
composited. The supervisor's "two calibrations on one retinal region" is, in
graphics, an unremarkable shipping feature with a name: **Fresnel blending**.

### 6a. THE VOCABULARY (the most immediately useful thing here)

| Our concept | Graphics term |
|---|---|
| per-surface calibration | **secondary view / virtual camera / view matrix** |
| calibration for a mirror | **reflection matrix** (Householder reflection about the plane) |
| calibration for a window/portal | **portal camera + oblique near-plane clip** |
| "don't let stuff behind the surface leak in" | **oblique near-plane clipping**, **clip plane**, **refraction mask** |
| where the calibrated image lives | **render target / render-to-texture / scene capture** |
| bounded self-reference | **recursion depth / bounce limit** |
| two calibrations co-present on one surface | **Fresnel blend** |
| calibration approximate, degrade gracefully | **fallback chain** (SSR → probe → skybox) |
| the surface's assumed geometry | **proxy geometry / influence volume / parallax correction** |
| foveation | **foveated rendering / LOD / variable-rate shading** |

### 6b. Portal rendering — the purest case, with a published derivation

The virtual camera transform is **relational**: take the camera's offset and
angle from the source portal, apply its inverse at the destination
(<https://th0mas.nl/2013/05/19/rendering-recursive-portals-with-opengl/>).
Stencil buffer masks the footprint; recursion descends with `GL_INCR` and renders
deepest-first.

**Oblique near-plane clipping** — the published core:
Lengyel, E. (2005). "Oblique View Frustum Depth Projection and Clipping."
*Journal of Game Development* 1(2).
<https://terathon.com/lengyel/Lengyel-Oblique.pdf> ·
<http://terathon.com/code/oblique.html>
Modify the projection matrix so its near plane **becomes the portal plane** —
only the third row is replaced. This is a real derivation, not folklore.

Its cost is documented and got its own follow-up: degraded z-precision and broken
depth linearization — Popov (2016), *JCGT* 5(4).
<https://jcgt.org/published/0005/04/03/paper.pdf>
> ⚠️ The agent could not extract that paper's body (binary fetch); the specific
> mechanism is corroborated only by practitioner discussion. Flagged.

**Valve's Portal postmortem** (Swift, Wolpaw & Barnett, *Game Developer*, Jan
2008 — trade press, not a technical paper)
<https://www.gamedeveloper.com/game-platforms/exclusive-inside-the-making-of-i-portal-i->:
scene rendered two extra times; stencil chosen over render-to-texture because it
**composed correctly with global HDR bloom**; custom frustum culling from the
portal's edges.

**THE GEM — and it is a direct architectural warning for us.** Portal's LOD
broke, because **distance stopped being a scalar**:

> "distance is relative to the portal locations. This means that the distance
> calculations became a choice of three lines connecting two points, rather than
> just one line." And: "line of sight can pass through a single portal more than
> once to reach its target."

**Introducing a second local calibration forced every distance-dependent global
system to become calibration-relative.** If our perceiver has per-surface
calibrations, then every downstream metric quantity — salience, scale priors,
LOD, "how far away is that" — inherits the same multiplicity. Valve shipped that
consequence and wrote it down. **Expect it; do not be surprised by it.**

Unresolved: conflicting community claims about Valve's true stencil-vs-RTT split
and the recursion cap. Treat as lore.

### 6c. Render-to-texture — the TV/photo case (SUPPORTS, but weakly — and the disanalogy matters)

A second camera renders into a **render target** sampled as an ordinary texture.
Unity URP: <https://docs.unity3d.com/6000.1/Documentation/Manual/urp/rendering-to-a-render-texture.html>;
Unreal's `SceneCaptureComponent2D`.

Gotchas (engine-doc grade): mip generation needs power-of-two targets; MSAA
resolve is a hidden cost on target switch; and **angle-dependent sampling** —
viewing the screen obliquely gives very different per-axis sample rates, the
lower rate picks the mip, and the surface goes blurry without anisotropic
filtering (Meta, *Common Rendering Mistakes*,
<https://developers.meta.com/horizon/blog/common-rendering-mistakes-how-to-find-them-and-how-to-fix-them/>).
That last one is the **oblique-viewing resolution loss**, and it is a nice
independent echo of §1b's slant dependence.

**Why it only weakly supports:** this case is *degenerate*. No clip plane, no
relational derivation — an artist simply says "this surface samples that buffer."
Worth naming as the disanalogy.

Recursive camera feedback (camera pointed at its own output) **could not be
resolved** to a citable engine-doc treatment — appears to be handled by the same
recursion-cap folklore as portals.

### 6d. Reflections — one surface type, three-plus calibrations. THE ARTIFACTS ARE THE PAYLOAD.

**Planar reflections** — exact, expensive, one plane. Unreal is blunt
(<https://dev.epicgames.com/documentation/unreal-engine/planar-reflections-in-unreal-engine?lang=en-US>):
"cause your entire scene to be rendered twice, so you'll want to budget **half
your frame time**"; measured **+23ms on a 31ms baseline** in the Kite Demo; cost
scales with **scene complexity, not resolution**; "Often times, one will still be
too much."
*Transferable artifact:* normal distortion can sample **outside the reflection
texture's bounds**, mitigated by an **Extra FOV** property — i.e. **you must
render a margin beyond the aperture because perturbation samples outside it.**
A direct design constraint for any perturbed per-surface calibration.

**Screen-space reflections (SSR)** — a catalogue of *what happens when a
calibration is computed in the wrong frame*. SSR resolves the secondary view in
**screen space**, so it can only see what the primary view already saw
(<https://www.gamedeveloper.com/programming/screen-space-reflections-in-blightbound>,
<https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@14.0/manual/Override-Screen-Space-Reflection.html>):
- **Cannot reflect offscreen geometry, backfaces, or anything behind the camera.**
- **Edge leaking** at screen borders; needs deliberate fade-out.
- **Vertical smearing** — rays passing behind an object false-hit at its edge.
  The finite-thickness fix "reduces this problem greatly, but adds other
  artefacts, like **holes in reflections of tilted objects**." A precision/recall
  trade **with no free setting** — a recurring shape in this section.
- Alpha-transparent objects invisible to the trace.
- **Ray-miss policy is a first-class design decision**, not an afterthought.

**Cube maps / reflection probes** — cheap, **wrong by construction**: a cubemap
"represents an infinite box by definition," so anything at finite distance is
displaced. Lagarde & Zanuttini, parallax-corrected cubemaps, SIGGRAPH 2012 talk
<https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/>
— intersect the ray with **proxy geometry** and re-derive. Documented failures:
correction exact **only for mirror surfaces perpendicular to the reflection
plane**, distortion growing with angle; **light leaks** where proxy ≠ real
geometry; **popping** when contributing probes change; rough surfaces near proxy
geometry look **sharper than they should**, and the usual workaround "creates
lighting errors."

**THE STRUCTURAL FINDING — this enriches the thesis rather than merely
supporting it.** Three techniques, one surface type, **selected by cost and
confidence and composited as a fallback chain**: SSR where it has data, probe
where it doesn't, skybox where neither does.

> It is not one calibration per surface. It is **one-to-many-with-arbitration** —
> a confidence-ordered cascade with an explicit hand-off policy at each boundary.

If our perceiver needs anything from this section, it is that: not a calibration
per surface, but a **ranked set with defined behaviour where each runs out of
evidence.** This is also the closest graphics analogue to our own escalation
rungs.

### 6e. Water — two calibrations on one surface, one pixel, shipping since ~2005

GPU Gems 2 ch.19, "Generic Refraction Simulation"
<https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-19-generic-refraction-simulation>
(book chapter / standard practice, not peer-reviewed):

- **Reflection texture**: scene mirrored through the water plane, below-surface
  geometry clipped.
- **Refraction texture**: the current back buffer, reused.
- **Different distortions on the same pixel**: animated bump layers perturb both
  with **different scale factors — 0.075 refraction vs 0.02 reflection.** Two
  calibrations, co-located, **independently tuned**.
- **Fresnel term blends them per pixel** — reflection dominant at grazing angles,
  refraction head-on.

**The named artifact — "refraction leakage" — and why it matters most.** Objects
*in front of* the water surface incorrectly appear distorted in the refraction
map, because the back buffer doesn't know what's above the surface. The fix is a
**refraction mask** in the alpha channel: refractive meshes render black, and
perturbation applies only inside the surface's screen footprint.

> This is precisely a **calibration-boundary error**: content belonging to frame A
> interpreted under frame B's transform, because the boundary was not explicitly
> represented. The fix was to make the surface's **extent** a first-class channel
> rather than something inferred.

**Prediction for us: if we build per-surface calibration, we will hit this exact
bug class, and the fix will be an explicit extent mask, not a smarter transform.**

### 6f. Wide-FOV — the global calibration is also a choice

Sharpless, T., Postle, B. & German, D. (2010). "Pannini: A New Projection for
Rendering Wide Angle Perspective Images." *Computational Aesthetics* (Eurographics).
<http://tksharpless.net/vedutismo/Pannini/panini.pdf> ·
<https://diglib.eg.org/items/29b67abe-d80e-4010-a065-e8292a8c65ef>

Rectilinear perspective "cannot render realistic looking flat views with fields
of view much wider than 70°" — yet 18th-century *vedutisti* painted much wider
architectural scenes without visible distortion. **The projection, not the
artist, was the problem.** Pannini renders 150°+ naturally.

Shipped in Unreal as a post-process displacement
(<https://dev.epicgames.com/documentation/unreal-engine/panini-projection-in-unreal-engine?lang=en-US>),
with **explicitly declared preserved invariants**: vertical lines stay straight
for all parameter values; at S=0 lines through screen centre stay straight
(motivated by FPS weapon models). Documented artifact: centre blurriness rises
with the emphasis parameter (it is a resample).

**Note the shape: the projection is chosen to preserve *specific structures* at
the cost of others.** Not correct-vs-incorrect — a deliberate, parameterized
allocation of distortion. **This is §1B's cartographic trade-off, shipped, with
the trade stated in the docs.** It is the practical answer to the Mercator
question, and it independently confirms that framing.

### 6g. Lower priority — apparent depth on a flat surface, and foveation

**Parallax occlusion mapping** — the picture problem in reverse. Tatarchuk,
"Practical Parallax Occlusion Mapping," SIGGRAPH 2006 course
<https://advances.realtimerendering.com/s2006/Tatarchuk-POM.pdf> · I3D 2006
<https://dl.acm.org/doi/pdf/10.1145/1185657.1185830>. Failure modes, all
diagnostic:
- **The silhouette betrays it.** Apparent depth is convincing until the surface's
  own outline contradicts it.
- **Degrades at grazing angles** (stair-stepping) — apparent parallax grows while
  the sample budget doesn't.
- Depth biasing hides stair-stepping **but flattens features** — again, no free
  setting.

> Transferable: **a depth calibration on a flat surface survives interior
> inspection but fails at the BOUNDARY and at GRAZING INCIDENCE.** Both are
> exactly where a perceiver would test it — and, note, exactly where §1b says
> human picture-perception compensation also degrades (±45°). Two independent
> literatures put the failure in the same place.

**Foveation.** Guenter et al. (2012). "Foveated 3D Graphics." *ACM TOG*
(SIGGRAPH Asia). <https://dl.acm.org/doi/10.1145/2366145.2366183> — 5–6× speedup
at 1080p, 10–15× fewer pixels shaded, acuity model linear in eccentricity with
measured slope **1.32–1.65 arcmin/degree**. VRS gives up to 75% shading-rate
reduction. Survey: <https://arxiv.org/pdf/2211.07969>.
**The scaling claim is the interesting part: foveation converts rendering cost
from roughly quadratic to roughly LINEAR in field of view.** Given that our
measured video-probe blocker is an O(N²) drive with exponent 1.887, this is
directly on point.

### 6h. THE CAVEAT THAT KEEPS THIS HONEST

Graphics solves the forward problem and **hands itself the answer to our actual
hard problem for free**: an artist assigns the material. The renderer is *told*
"this surface is a mirror, use the reflection matrix." **Nothing in this
literature infers, from an image, WHICH calibration a surface carries.** That is
the inverse problem and it is entirely ours.

So the correct claim is narrower than "graphics has enumerated it" — and better:

> **Graphics has fully enumerated the space of per-surface calibrations, their
> composition rules, their cost/accuracy ladder, and their failure signatures —
> because someone had to ship each one. It has NOT enumerated the assignment
> problem.**

Still an enormous gift, in two directions. First, the enumeration closes the
question "what kinds of local calibration exist?" Second, and more valuable:
**the artifact catalogue is a catalogue of what a MIS-calibration looks like** —
edge leaking, refraction leakage, parallax light leaks, probe popping,
glossy-angle distortion, silhouette failure, grazing-incidence stair-stepping.
If our calibrations are wrong or approximate, **these are the specific symptoms
we should produce**. That converts open-ended failure into a testable prediction
set, and one we can check against human perceptual error (§1d's mirror errors
and §1b's ±45° degradation both have graphics analogues above).

### 6i. An unplanned confirmation of the frame/continuum invariant

Every transform in this section lives strictly **between** frames — a reflection
matrix, a portal transform, a Fresnel weight, a Pannini resample. **None is a
coordinate inside a frame.** Real-time graphics practice is a large independent
confirmation of the in-frame/cross-frame invariant recorded in CLAUDE.md,
arrived at by people optimising for milliseconds rather than for that principle.
Worth noting because it was not sought.

### Gaps I could not resolve in §6

- A canonical **published derivation for SSR itself** (as opposed to engine docs
  and dev blogs).
- **Documented recursive-camera feedback** handling in any engine.
- Valve's true **stencil-vs-render-target split and recursion cap** — conflicting
  community claims, no primary Valve source.
- Popov (2016) paper body — binary fetch failed; the depth-linearization
  mechanism is corroborated only by forum discussion.

---

## SUMMARY LISTS

### SETTLED (real science, cite freely)

1. **Dual reality of pictures** — simultaneous awareness of picture surface and
   depicted space. Pirenne 1970; Gibson. Phenomenology not disputed.
2. **Common-motion object segmentation in infants** at ~4 months, where static
   form fails. Kellman & Spelke 1983, with converging reaching evidence.
3. **Newborns do NOT perceive object unity** — it develops over ~2–4 months.
   Slater et al. 1990/1996.
4. **Cohesion as a mid-level vision mechanism**, confirmed in adults by
   independent methods (object files, attentional tracking). Scholl 2023.
5. **Systematic errors in mirror space perception** — frontal bias, early-visibility
   error, wrong distance variable. Bertamini and colleagues.
6. **Retinotopy is approximately log-polar in the RADIAL direction**, in the
   shifted `log(z+a)` / wedge-dipole form. Schwartz 1980; Balasubramanian 2002;
   Horton & Hoyt 1991 (`M = 17.3/(0.75+E)`).
7. **Polar-angle anisotropy (~80%) and foveal-confluence deviation** from
   log-polar. Himmelberg 2021; Schira 2010.
8. **Stereoblindness ~7%** in adults under 60. Chopin et al. 2019.
9. **Prism adaptation is real, decomposable, asymptotic, procedural**, and is
   *reduced* by explicit knowledge. Redding & Wallace.
10. **Tomasi–Kanade rank constraint** (3 registered / 4 unregistered) — a theorem
    under the affine camera.
11. **Costeira–Kanade block-diagonality under linear independence** — a theorem
    (Kanatani's conditional form).
12. **Projection theory applied to retinotopy** via conformal / quasiconformal
    (Beltrami-coefficient) analysis. PMC8678293.
13. **Projection trade-offs applied to pictures** — Koenderink; Zorin & Barr 1995.
14. **Per-surface calibration as an implemented, enumerated engineering
    practice** — secondary views, reflection matrices, portal cameras + oblique
    clip planes, Fresnel-blended dual calibrations. Lengyel 2005; Lagarde &
    Zanuttini 2012; GPU Gems 2 ch.19; Sharpless et al. 2010. (§6)
15. **Wide-FOV projection as a declared invariant budget**, shipped — Pannini,
    with "verticals stay straight" as a stated preserved invariant. (§6f)
16. **Foveation converts render cost from ~quadratic to ~linear in FOV**;
    acuity slope 1.32–1.65 arcmin/deg. Guenter et al. 2012. (§6g)

### CONTESTED (live controversies — do not pick a side silently)

1. **Local slant compensation** — does the visual system calibrate to the picture
   surface? Vishwanath/Girshick/Banks 2005 **yes**; Erkelens 2013 **no**;
   Hertzmann 2024 proposes a third (fixation-centred, globally inconsistent)
   position and calls it open.
2. **Whether newborns show any perceptual completion.** Majority: no. Minority
   (Valenza & Bulf): yes.
3. **Core knowledge as a framework** — Scholl 2023 would reduce much of it to
   mid-level vision; Schulz 2023 wants domain-general learning admitted.
4. **The VoE method itself** — Paulus 2022 says abandon it; Margoni, Surian &
   Baillargeon 2024 defend it. (Mostly does not touch our finding; see §2c.)
5. **Whether log-polar sampling reproduces the primate foveation profile** —
   yes radially, no angularly.
6. **Multibody missing-data handling** — solvable, but every fix adds stages.
7. **Whether log-polar imaging is still current practice in machine vision.**

### FOLK / INVENTED (do not repeat as established)

1. **"Some people cannot interpret a fisheye."** No source found. Looks like
   generalisation from the (real) stereoblindness case to an unstudied one.
2. **"Outside its calibration range, perception FAILS rather than degrades."**
   Contradicted in every case checked — degradation is graceful and produces
   *confident wrong answers*, not absence. See §4e.
3. **"Vision flips back with inverting goggles once you can act."** The classic
   textbook story (**KH**). Klein: "KH is wrong... Kohler himself doesn't appear
   to believe in KH."
4. **"Biology exploits log-polar rotation/scale→translation for invariance."**
   Refuted on record by Cavanagh 1981 with a failed empirical prediction; the
   field's actual account (DiCarlo) is learned hierarchical tolerance.
5. **"People perceive mirror space veridically."** They do not.
6. **Hudson-style cross-cultural picture-perception results** — methodologically
   and ethically unreliable; do not cite at face value.
7. **"Modern subspace methods substantially surpass Costeira–Kanade."** Refuted
   as framed — LRR/EDSC provably reduce to a modified SIM.

### APPARENTLY THE SUPERVISOR'S OWN CONSTRUCTIONS (novel — must be earned, held to the higher bar)

These are **not contradicted**, but no source establishes them. Each is a claim
we would be making, not citing.

**⚠️ REVISED AFTER §6.** The graphics evidence moved two of these. Original
perception-only verdicts kept visible so the revision is auditable.

1. **"Two calibrations on one retinal region, both applied correctly, neither
   winning."**
   - *Perception verdict:* the literature's picture is *coupled and trading off*
     — which is why it is called "conflicted." (§1c)
   - **REVISED → SUPPORTED as an engineering reality.** Water renders reflection
     and refraction on one pixel with independently tuned distortions
     (0.075 vs 0.02) blended by Fresnel. Shipping since ~2005. (§6e) The honest
     synthesis: **co-presence is real and implementable; "neither wins" is
     wrong** — there is always an arbitration rule (Fresnel weight, confidence
     cascade). Build the arbitration; don't assume independence.
2. **Calibration attached to a globally identified SURFACE.**
   - *Perception verdict:* the literature's unit is the **local patch at the
     current fixation** — Hertzmann explicitly denies global consistency.
     **Still the most likely over-reach in the design.** (§1b)
   - *Graphics note:* renderers DO attach per-surface, globally — but they are
     **told** the assignment. That is exactly the freedom we don't have. So §6
     does **not** rescue this one; the tension between whole-surface and
     per-fixation-patch remains genuinely open and is **the sharpest open
     design question in this document.**
3. **Anamorphosis / trompe l'oeil as mis-assigned calibration.** Defensible,
   structurally implied by Vishwanath, but nobody frames it this way. (§1e)
   Graphics offers the mechanism-name (**mis-assigned secondary view**) but not
   a perception-side source.
4. **Windows and water as calibration-bearing surfaces.**
   - *Perception verdict:* literature covers pictures and mirrors only; the
     water/diver "learns to compensate" claim is folk. (§1 gaps)
   - **PARTIALLY REVISED** — graphics treats windows (portals) and water as
     first-class calibrated surfaces with published derivations (§6b, §6e). The
     *forward* case is settled; the *perceptual* case remains unsourced.
5. **Unifying retinotopy + picture surface + mirror as ONE FAMILY of per-surface
   projections with declared invariants.** Both halves of the perception
   literature are mature; the unification is unclaimed there — **but graphics
   has effectively built it** (one mechanism, per-surface instantiation, §6a).
   So this is less novel than it looked, and better founded. **Downgraded from
   "ours to earn" to "already done in the forward direction."**
6. **NEW, and now the only genuinely unclaimed thing here: THE ASSIGNMENT
   PROBLEM.** Nothing in either literature infers *from an image* which
   calibration a surface carries. Graphics is told; perception science studies
   compensation given a known surface. **That inference is the actual novel
   contribution available to us** — and it is a much sharper, smaller, more
   defensible claim than "per-surface calibration is new." (§6h)

### BORROWABLE ENGINEERING (with assumptions and failure modes)

| Item | Take | Assumptions bought | Fails when |
|---|---|---|---|
| Tomasi–Kanade rank-3 | Yes — implement first, unit-testable | affine camera, rigidity, full matrix, correct tracks | perspective, non-rigid, occlusion |
| Costeira–Kanade rank-4 SIM | Yes, but **never raw** | + linear independence of subspaces | noise, dependent/degenerate motion |
| Ji et al. RSIM conditioning | **Yes — highest value/effort ratio** (7.80%→0.89%, 0.18s) | as above | as above |
| Model selection (K) | **No — unsolved.** Design to accept K externally | — | always |
| Hopkins155 as a gate | **No** — hand-cleaned, narrow FOV, rotation-dominant | — | always |
| Beltrami/Tissot distortion field | Yes — the honest way to state a representation's cost | — | — |
| Log-polar for **foveation/packing** | Yes | — | — |
| Log-polar for **invariance** | **No** — and `log(z+a)` destroys exact scale invariance anyway | — | always |
| Log-polar remap of Cartesian capture | **No** — forfeits the bandwidth win, keeps the costs | — | always |
| **Oblique near-plane clipping** (Lengyel 2005) | Yes — the portal/window calibration, derived | planar surface | z-precision loss |
| **Reflection matrix** (Householder about the plane) | Yes — exact mirror calibration | single plane | cost = full re-render |
| **Fresnel blend** for co-present calibrations | Yes — the arbitration rule we lack | — | — |
| **Confidence-ordered fallback chain** (SSR→probe→skybox) | **Yes — closest analogue to our escalation rungs** | explicit hand-off policy | boundaries between tiers |
| **Explicit extent mask** (refraction mask) | Yes — the fix for calibration-boundary leakage | — | — |
| **Extra-FOV margin** for perturbed calibration | Yes — perturbation samples outside the aperture | — | — |
| Pannini / declared-invariant projection | Yes — how to state a wide-FOV trade | — | centre resample blur |
| Foveated rendering cost model | Yes — quadratic→linear in FOV | eye/attention position known | — |
| Graphics' **assignment** of surface type | **Not available** — artists assign it. This is our problem. | — | always |

### CROSS-CUTTING OBSERVATIONS

- **Two independent instances of "the eval set was the error, not the machinery"**
  turned up here: Hopkins155's hand-cleaned tracks (§5e), and the
  instrument-dependent stereoblindness prevalence (§4c). Both mirror this
  project's own RUN 15 correction. The pattern is worth treating as a standing
  prior when reading any benchmark number.
- **Confabulation-is-the-default is corroborated externally.** Mirror perception
  (§1d) and out-of-range picture perception (§4e) both produce *confident wrong*
  percepts rather than refusals. Consistent with the existing memory item.
- **Sensorimotor and perceptual calibration dissociate** (§4a). If our
  architecture shares one calibration between action and perception, the goggle
  literature is evidence against it.
- **"No free setting" recurs across every independent literature here.** SSR
  thickness (holes vs smearing), POM depth bias (stair-stepping vs flattening),
  cubemap parallax (sharpness vs lighting errors), projection choice
  (Theorema Egregium), multibody rank selection. **Whenever a knob appeared,
  both directions cost something.** Treat any parameter in our design that
  seems to have a free optimum as under-tested.
- **Boundary and grazing incidence are where calibrations fail, in BOTH
  literatures independently.** Human picture compensation degrades past ±45°
  (§1b); POM fails at the silhouette and at grazing angles (§6g); render-to-
  texture blurs under oblique viewing (§6c); SSR leaks at screen edges (§6d).
  **Test our calibrations at boundaries and grazing angles first** — that is
  where the evidence says they break.
- **Two independent instances of a mechanism confirming the in-frame/cross-frame
  invariant** already in CLAUDE.md: the graphics transforms all live strictly
  between frames (§6i), and the retinotopy literature measures the map as a
  cross-frame conformal distortion field (§1B). Neither was sought.

### THE SIX-HYPOTHESIS SCORECARD FOR THIS DOCUMENT

Of the supervisor's claims as stated:
- **1 largely SUPPORTED with a name attached** (per-surface calibration = local
  slant compensation) — though the *global surface* framing over-reaches.
- **1 SUPPORTED with one word wrong** (infant motion segmentation; "long before"
  / innate is refuted).
- **2 REFUTED** (log-polar invariance in biology; perception fails rather than
  degrades).
- **1 REFUTED-as-stated but useful inverted** (mirrors are not veridical — the
  systematic error is *better* evidence for per-surface calibration).
- **1 FOLK** (fisheye individual limits).
- Plus **the creator's two pointers, which both landed and are better founded
  than the supervisor's constructions they were offered against:**
  - the **Mercator / Theorema Egregium** framing — real mathematics applied to
    both retinotopy and pictures, and the *reason* a single global calibration
    is impossible in principle rather than merely absent empirically (§1B);
  - the **graphics** pointer — the taxonomy fully enumerated, named, costed and
    shipped, plus an artifact catalogue that converts our failure modes into
    testable predictions (§6).

**The single most useful reframing to come out of this document:** the novel
claim available to us is **not** per-surface calibration — that is standard in
perception (as local slant compensation) and fully built in graphics. It is
**THE ASSIGNMENT PROBLEM**: inferring from an image which calibration a surface
carries. Graphics is told by an artist; perception science studies compensation
given a known surface. Nobody does the inference. That is a smaller, sharper and
far more defensible claim than the one we started with — and it should be held
to the higher evidential bar accordingly.

---

# §7. SUPERVISOR AMENDMENT — THE FISHEYE VERDICT IS CORRECTED, AND THE CORRECTION GENERALISES

*Added by the supervisor after the spike closed, at the creator's challenge. The
spike's own adjudications are unchanged; this section corrects one verdict and
records the methodological principle behind the correction.*

## 7.1 The correction

The spike returned **"some people cannot read a fisheye" = FOLK — no source found
in two passes.** That verdict stands as a statement about the search and is
**withdrawn as a statement about the world.** It should read:

> **UNDER-STUDIED, WITH STRONG ANALOGUES.**

**The reasoning that forces the change:** absence of a study is weak evidence of
absence **when nobody has an institutional reason to look.** A tail that is
functional, self-compensating and causes no clinical presentation generates no
literature. Studies sample volunteers who show up; the affected go about their
lives. The claim's *invisibility is predicted by the claim itself*, so failing to
find it is not disconfirming.

**And one adjacent verdict was simply too narrow:** "some people cannot free-fuse
stereograms" is **NOT folk.** Stereo-deficiency is documented at roughly 5–10% of
the population, **most of whom do not know.** That is a directly attested
individual limit on a visual calibration capacity.

## 7.2 The general principle, and it is the creator's

> **Almost every capability treated as universal is not held by a tail. That is
> the problem of universality — and it is UNCHECKED QUANTISATION WITHOUT
> REANALYSIS.**

Documented instances, all of basic capabilities once assumed universal, all
largely undiagnosed, all compensated:

| capability | tail | notes |
|---|---|---|
| mental imagery | aphantasia, ~2–5% | described by **Galton (1880)**, FORGOTTEN, re-named by Zeman (2015) |
| stereopsis | ~5–10% | the closest analogue to the fisheye claim |
| face recognition | developmental prosopagnosia, ~2% | compensated by voice, gait, context |
| pitch | congenital amusia, ~4% | |
| inner speech | anendophasia | described only recently |
| autobiographical memory | SDAM | |
| number sense | dyscalculia, ~5% | measured because schooling cares |
| reading | dyslexia, ~10% | measured because schooling cares |
| colour | ~8% of males | **measured because RAILWAYS cared** |

*(Prevalences approximate; the pattern, not the figures, is the point.)*

**THE DIAGNOSTIC IS WHICH TAILS ARE DOCUMENTED, NOT WHICH EXIST.** Colour
blindness is famous because a fatal rail crash gave an industry a reason to test
for it. Dyslexia and dyscalculia are measured because education systems care.
Aphantasia waited 135 years for someone to ask again. **The tail exists either
way; only the measurement incentive varies.**

## 7.3 Why this is the substrate's own critique

**A capability assumed universal is a quantum that was minted and never
re-decoded.** The sd loop's discipline is that a mint must face re-decode, which
is what stops a held quantum from silently covering things it does not fit.
"Everyone can do X" is a bin drawn from a sample and never re-examined against
its residual — the exact failure the loop exists to prevent, committed by the
literature we are reading.

**Consequence for every claim in this document, including the ones adjudicated
SUPPORTED:** read *"the visual system does X"* as **"the sampled majority does
X."** That is not a rhetorical hedge — it changes what a mechanism claim licenses.
A mechanism found in the majority is not thereby necessary, and a system that
lacks it is not thereby broken.

## 7.4 The part that cuts toward us

**The invisible tails are evidence that HUMAN capability degrades gracefully.**
People without stereopsis navigate stairs. People without imagery reason
perfectly well. People without inner speech think. They compensate so completely
that neither they nor anyone around them notices.

**Our system cliffs.** The redundancy audit found every severity curve carrying
loss to be a STEP rather than a gradient, and `vision_waves` to be NON-MONOTONE —
a component staying confident after its preconditions vanished. So the tails are
evidence **FOR** the architecture's stated graceful-degradation goal and
**AGAINST** its current implementation. A human missing a faculty routes around
it; this substrate, missing one, returns a confident wrong answer.

## 7.5 Standing methodological rule

> **"No source found" is a fact about the search. Before recording it as a fact
> about the world, ask who would have had a reason to measure it.** Where the
> answer is "nobody", the correct verdict is UNDER-STUDIED, not FOLK — and the
> claim should be held open rather than closed.

