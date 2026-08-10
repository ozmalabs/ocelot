# VISION PRIOR ART MAP

**Status: COMPLETE** (research spike, 2026-07-19). No code was written and no
repository state was touched; this file is the sole deliverable.

**Bottom line up front.** The Cornsweet question is ANSWERED and the rung is
saved: a filling-in system that uses *unmodified* gradients provably reconstructs
the veridical image and destroys the illusion (Cohen-Duwek & Spitzer 2019,
verbatim), and three independent camps converge on the same fix — weight or
threshold the gradient before using it. The paint-from-sample boundary asymmetry
is CORROBORATED verbatim, twice, and stated as *unavoidable for local filters*.
The escalation ladder is only partly RVQ — its closer prior art is the quadtree
literature, and most of RVQ's famous failure modes are structurally inapplicable
to us. ANN indexing is not merely unnecessary at our K; it is measurably slower.

**Framing.** The deliverable of this project is the composed SYSTEM. Prior art
on individual mechanisms is a WIN: it means we adopt a mature version and
inherit its known failure modes for free. This document prioritises
BORROWABLE-WITH-ATTRIBUTION and KNOWN-FAILURE-MODES over novelty adjudication.
"Nobody has done this" is held to a higher evidential bar than everything else.

---

## Contents

1. Cornsweet: flat fill vs gradient fill — the filling-in literature
2. Paint-from-sample: artifacts, especially boundary asymmetry
3. Residual / multi-stage vector quantization
4. ANN for a *growing* codebook (demoted — we have no large-K problem)
5. Settled / contested / folk
6. Borrowable engineering
7. Known failure modes
8. Explicit gaps

---

## 1. CORNSWEET: FLAT FILL vs GRADIENT FILL

**Our measured result being adjudicated.** Order-1 (flat) fill → Craik–O'Brien–
Cornsweet present and CORRECT. Escalate to an order-2 (gradient/plane) code and
extrapolate that plane across the far field → the percept INVERTS.

**Headline verdict: this is a KNOWN CONSTRAINT with a KNOWN FIX, and the fix is
named explicitly in the literature — twice, independently, from two different
theoretical camps. We can save the rung.** Furthermore the psychophysics says
BOTH of our arms are wrong in a specific, testable way (see 1.4): the true
percept is neither flat nor a far-field-extrapolated plane, but a gradient that
DECAYS with distance from the inducing edge.

### 1.1 Does the filling-in literature say flat or gradient? — FLAT, and constitutively so

**CORROBORATED.** In Grossberg's Feature Contour System the filled-in surface is
the steady state of a **nonlinear diffusion** process whose sources are the
feature-contour (edge) signals and whose barriers are the BCS boundaries. The
steady state of a diffusion equation inside a compartment that is sealed by
boundaries and has no interior sources is a **constant**. So a diffusive
filling-in model produces a flat fill *by construction* — it is not a modelling
choice that could have gone the other way, it is what the PDE does. Cornsweet
falls out because the only surviving sources are the two opposed cusps at the
edge, and each compartment equilibrates to its own cusp value.

- Grossberg, S. & Mingolla, E. (1985). Neural dynamics of form perception:
  boundary completion, illusory figures, and neon color spreading.
  *Psychological Review* 92(2), 173–211. — BCS/FCS split.
- Grossberg, S. & Todorović, D. (1988). Neural dynamics of 1-D and 2-D brightness
  perception: A unified model of classical and recent phenomena.
  *Perception & Psychophysics* 43, 241–277.
  <https://link.springer.com/article/10.3758/BF03207869> — **explicitly simulates
  the Craik–O'Brien–Cornsweet effect** among its target phenomena. This is the
  deciding citation for "filling-in produces Cornsweet with a flat fill".
- Grossberg, S. (1994). 3-D vision and figure-ground separation by visual cortex.
  *Perception & Psychophysics* 55, 48–121.
  <https://pubmed.ncbi.nlm.nih.gov/8036093/> — FACADE proper.

**So: our order-1 arm is the standard model, and it is standard for a principled
reason.** Adopt-with-attribution: our flat fill is a discrete, boundary-gated
re-derivation of FCS diffusive filling-in.

### 1.2 Is the inversion a known problem with a known fix? — YES. Retinex names it as a design requirement

**CORROBORATED — this is the single most valuable finding in this document.**

Land & McCann's Retinex computes lightness in four stages: (1) differentiate the
image; (2) **THRESHOLD to discard gradual/slow gradients**; (3) integrate the
surviving edge contrasts across space; (4) anchor to absolute values.

The Cornsweet effect *is* stage (2). The stimulus is two equiluminant fields
joined by a sharp cusp with slow opposed return gradients. The visual system
discards the slow return gradients as sub-threshold and integrates only the
cusp — yielding a step. **If you do NOT discard the slow gradient — if instead
you fit it and integrate or extrapolate it — the integration walks back to the
true equal luminance and the effect cancels or reverses.**

That is exactly our order-2 failure, and it is the reason the threshold exists.
The threshold is not an implementation detail of Retinex; it is the load-bearing
step that makes Cornsweet come out.

- Land, E. H. & McCann, J. J. (1971). Lightness and retinex theory.
  *Journal of the Optical Society of America* 61(1), 1–11.
- Land, E. H. (1986). An alternative technique for the computation of the
  designator in the retinex theory of color vision. *PNAS* 83, 3078–3080.
- Adelson & Pentland / Gilchrist's summary of the four stages, and the
  observation that "the importance of edges, and the lesser importance of slow
  gradients, is indicated by the COCE", is laid out in the MIT Persci lightness
  review: <https://persci.mit.edu/gaz/publications/gazzan.dir/gazzan.htm>

**Borrowable fix #1 (cheap, exact):** gate escalation on a *gradient
admissibility threshold* — a slow, low-amplitude gradient is not eligible to
become an order-2 code at all, no matter what the residual says. Retinex has
been doing this since 1971. This is a one-parameter change to our escalation
predicate and it should restore Cornsweet at order-2.

### 1.3 The deeper structural result: thresholded derivatives have NON-ZERO CURL

**CORROBORATED, and it says far-field extrapolation is not a well-posed
operation.**

- **Arend, L. E. & Goldstein, R. (1987). Lightness models, gradient illusions,
  and curl. *Perception & Psychophysics* 42(1), 65–80.**
  <https://pubmed.ncbi.nlm.nih.gov/3658639/> ·
  <https://link.springer.com/content/pdf/10.3758/BF03211515.pdf>

Their argument, which lands directly on our mechanism: gradient illusions force
any model of suprathreshold appearance to include **spatial integration that
fills the area between edges** — you cannot get them from local operators. But
once you threshold the derivatives (as Retinex must, per 1.2), the resulting
vector field has **non-zero curl**, i.e. the line integral between two points is
path-dependent. Simple spatial integration is therefore **structurally
ill-posed**. They report that human observers resolve the curl problem by two
means: **field segmentation** and **lightness-gradient manipulation**.

Translated into our terms: "fit a plane in one region and extrapolate it across
the far field" assumes a globally consistent (curl-free) gradient field. Real
images do not supply one. The human solution — *field segmentation* — is
precisely "confine the order-2 code to its own boundary compartment and do not
extrapolate past it".

**Borrowable fix #2 (structural, exact):** an order-2 code's domain of validity
is its own segment. The escalation should refine *within* the compartment that
demanded it, never extrapolate across a boundary into the far field. This is
also what our own boundary-gating already claims to do — so the inversion may be
diagnosable as a **boundary-gating leak specific to the order-2 path**, i.e. a
bug in our system rather than a property of the idea. That is a concrete thing
to go and check before building anything.

### 1.4 What the psychophysics actually measures — NEITHER flat NOR extrapolated

**CONTRADICTED (our order-1 arm), and this is the interesting part.**

- **Blakeslee, B. & McCourt, M. E. (2013). Brightness induction magnitude
  declines with increasing distance from the inducing field edge.
  *Vision Research* 78, 39–45.**
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3556186/> ·
  <https://pubmed.ncbi.nlm.nih.gov/23262229/>

Using quadrature-phase motion cancellation and point-by-point matching they
measured the *spatial profile* of induced brightness and found it **declines
with distance from the inducing edge**. Their conclusions: "A homogeneous
filling-in mechanism cannot explain the induced structure in the test fields of
these stimuli"; the results "argue strongly against filling-in mechanisms as
well as against any mechanism that posits that induction is homogeneous." ODOG
predicts the gradient structure and accounts for ~95% of the variance.

Caveat, stated honestly: **this paper studies grating induction, simultaneous
contrast and White's effect — it does not test COCE specifically.** So it is
strong evidence about induced brightness profiles in general and only
suggestive about Cornsweet.

**The synthesis this points at, and the experiment it suggests:** the correct
order-2 code is a gradient that **decays with distance from the edge**, not a
plane extrapolated at constant slope. A constant-slope extrapolation
over-integrates and flips the sign in the far field (our inversion); a flat fill
under-integrates (no decline signature). A decaying gradient does both jobs.
If our order-2 escalation were changed from "fit a plane, extrapolate" to "fit
an edge-anchored decaying gradient", the prediction is that Cornsweet survives
escalation *and* we pick up the Blakeslee–McCourt decline-with-distance
signature for free. **That is a falsifiable, cheap, single-rung experiment and it
is the recommended next move on this thread.**

### 1.5 The anti-filling-in position, and what evidence separates the camps

**The field is genuinely CONTESTED. Both camps are live in 2026.**

*The philosophical form:*
- Dennett, D. C. (1991). *Consciousness Explained.* — the brain "ignores an
  absence" / "jumps to a conclusion" rather than filling in pixels.
- **Pessoa, L., Thompson, E. & Noë, A. (1998). Finding out about filling-in: A
  guide to perceptual completion for visual science and the philosophy of
  perception. *Behavioral and Brain Sciences* 21(6), 723–748** (with open peer
  commentary — the canonical entry point to the whole debate).
  <https://philpapers.org/rec/PESFOA-2>
  Their verdict against Dennett: forms of completion that involve *spatially
  propagating neural activity* "cannot be described as results of the brain's
  'ignoring an absence' or 'jumping to a conclusion'."
- Dennett, D. C. (1998). No bridge over the stream of consciousness.
  *BBS* 21(6), 753–754. — his reply in the same issue.

*The empirical form (filtering, not filling-in):*
- **Blakeslee, B. & McCourt, M. E. (1999). A multiscale spatial filtering
  account of the White effect, simultaneous brightness contrast and grating
  induction. *Vision Research* 39, 4361–4377** — the ODOG model.
  <https://www.sciencedirect.com/science/article/pii/S0042698999001194>
  Mechanism: oriented difference-of-Gaussian filters across scales with contrast
  normalization. Because the filter bank is band-limited, low-spatial-frequency
  content is lost — and *that loss is the induction*. No diffusion, no
  compartments, no propagation.
- Blakeslee, B. & McCourt, M. E. (2015). The ODOG model of brightness
  perception: overview and executable Mathematica notebooks. *Behavior Research
  Methods.* <https://link.springer.com/article/10.3758/s13428-015-0573-4>
  — **a reference implementation exists and is executable.** Directly borrowable
  as an external oracle to test our percepts against.
- **Robinson, A. E. & de Sa, V. R. (2013). Dynamic brightness induction causes
  flicker adaptation, but only along the edges: evidence against the neural
  filling-in of brightness. *Journal of Vision* 13(6).**
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3670579/>
  The cleanest discriminating experiment found: adapt to induced flicker, then
  test. Adaptation appears when the test region's edges align with the inducer's
  edges, and **vanishes for a smaller inset region**. If brightness genuinely
  filled the interior, inset regions should show adaptation too. They do not.

*The empirical form (statistics of natural scenes, neither camp):*
- **Purves, D., Shimpi, A. & Lotto, R. B. (1999). An empirical explanation of
  the Cornsweet effect. *Journal of Neuroscience* 19(19), 8542–8551.**
  <https://www.jneurosci.org/content/19/19/8542>
  The percept tracks the *probability* that the two flanking territories are
  same-material-different-illumination vs different-material-same-illumination;
  manipulating scene context to change that probability enhances or diminishes
  the effect accordingly. Not a mechanism story at all — an accumulated-
  experience story.

*Evidence FOR filling-in (so the debate stays honest):*
- Paradiso, M. A. & Nakayama, K. (1991). Brightness perception and filling-in.
  *Vision Research* 31, 1221–1236. — masking reveals a propagating brightness
  signal.
- **Davey, M. P., Maddess, T. & Srinivasan, M. V. (1998). The spatiotemporal
  properties of the Craik–O'Brien–Cornsweet effect are consistent with
  'filling-in'. *Vision Research.***
  <https://pubmed.ncbi.nlm.nih.gov/9797949/> — COCE brightness propagates at a
  fixed ~19 deg/s in the central field (≈155–205 mm/s across V1/V2), with a
  temporal-frequency cutoff that scales with spatial frequency as a finite-speed
  propagation process requires. **This is the strongest COCE-specific evidence
  for filling-in**, and it is a *timing* argument — the one thing a
  feedforward filter bank cannot easily produce.
- A temporal window for estimating surface brightness in the COCE. *Frontiers in
  Human Neuroscience* (2014).
  <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4217394/>

### 1.5b THE DECIDING CITATION FOR OUR INVERSION — unmodified gradients reconstruct the veridical image

**CORROBORATED. This resolves the question the spike was commissioned to answer.**

- **Cohen-Duwek, H. & Spitzer, H. (2019). A compound computational model for
  filling-in processes triggered by edges: watercolor illusions.
  *Frontiers in Neuroscience* 13:225.**
  <https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2019.00225/full>
  · <https://pmc.ncbi.nlm.nih.gov/articles/PMC6438899/>

This is the closest published system to ours: filling-in as a **Poisson equation
with image gradients as heat sources**, solved to a steady state. And it states
our failure as a design requirement:

> "**Without modification, unmodified gradients would reconstruct the original
> image during diffusion.**"

> "The model modifies the original gradients by multiplying the double-opponent
> responses by the weight function [derived from multi-scale Gabor filters]."

And it reproduces COCE with the *same* parameters as its watercolour
simulations:

> "our model can also predict the classic Craik–O'Brien–Cornsweet (COC) effect"

**This is the whole diagnosis in one sentence.** A filling-in system that uses
the *actual* gradients faithfully does not produce an illusion — it
reconstructs the veridical image. For a Cornsweet stimulus the veridical image
has two *equal* flanking fields, so a faithful order-2 code drives the percept
to the null. Our system is then one bias term away from crossing the null and
reading as an inversion; a far-field linear extrapolation supplies exactly such a
bias, since a constant slope integrated over a long distance overshoots.

**So the correct order-2 code is not "the gradient" but "the gradient, weighted
by a scale-dominance function that suppresses the slow component."** That is the
same fix as Retinex's threshold (§1.2), but *graded rather than binary*, and with
a published reference model and a parameter set that is known to reproduce COCE.
**This is the single most borrowable thing in this document.** Note the third
independent arrival at the same fix: Retinex thresholds it, Arend & Goldstein
segment it, Cohen-Duwek & Spitzer weight it. Three camps, one answer: **the raw
gradient must not be used as-is.**

### 1.5c CAUTION — a percept opposite to the local gradient is a REAL phenomenon

Before we treat our inversion as purely an error, one honest complication:

- **Cavanagh, P. & Anstis, S. (2018). Diamond patterns: cumulative Cornsweet
  effects and motion-induced brightening. *i-Perception* 9(4).**
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6075612/>

In diamond patterns the accumulated Cornsweet steps produce "**a global lightness
shift opposite in direction to the actual luminance gradients within each
diamond**". The effect weakens as the spike angles become shallower and
"disappears when the angles are flat as in a ramp grating."

So *human* perception does exhibit a global shift opposed to the local gradients,
under cumulative geometry. This does not excuse our inversion on a single
Cornsweet edge — that one is diagnosed by §1.5b — but it does mean **"the
percept opposes the gradient" is not by itself proof of a bug**, and any test we
write should discriminate the single-edge case (where inversion is wrong) from
the cumulative case (where it is the human result).

### 1.6 Standing and criticisms of BCS/FCS/FACADE

**Standing: influential, still actively extended, but under sustained empirical
pressure and no longer the consensus account of brightness.** Documented
specific failures:

- **Non-assimilative watercolour effect.** FACADE predicts the assimilative
  watercolour effect it was designed for but *cannot* predict the
  non-assimilative variant: colour spread is derived from the chromatic surface
  itself and there is no mechanism to create complementary colours. See the
  compound filling-in model paper:
  <https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2019.00225/full>
- **Afterimage data require non-diffusive filling-in.** Orientation-tuning of
  two-stimulus afterimages produces results the model cannot account for "unless
  the filling-in stage mechanisms are different from a diffusive-type process".
  Wede & Francis (2006), *The time course of visual afterimages: data and
  theory*: <http://www1.psych.purdue.edu/~gfrancis/Publications/WedeFrancis2006.pdf>
- **The anchoring problem.** Discounting the illuminant yields only *relative*
  reflectance; absolute lightness needs a separate anchoring rule (Gilchrist's
  anchoring theory). FCS diffusion does not supply one.
- **The induction-profile result of 1.4** is the most direct blow: homogeneous
  filling-in predicts a flat interior and the interior is measurably not flat.

**Honest note on what this means for us:** we should NOT read "FACADE is
contested" as "our flat fill is wrong". Our flat fill is a *computational
mechanism that reproduces the illusion*, and it reproduces it for the same
mathematical reason FCS does. The contested question is whether the *brain*
does it that way. Those are different claims and we should only ever make the
first one.

### 1.7 Verdicts

| Claim | Verdict | Deciding citation |
|---|---|---|
| Filling-in accounts produce Cornsweet with a FLAT fill | **CORROBORATED** | Grossberg & Todorović 1988 |
| Flat fill is constitutive of diffusion, not a choice | **CORROBORATED** (mathematical) | FCS diffusion PDE; Grossberg & Mingolla 1985 |
| Integrating/extrapolating the slow gradient cancels or reverses Cornsweet | **CORROBORATED — known constraint, known fix (threshold)** | Land & McCann 1971 (stage 2); Persci review |
| Far-field gradient extrapolation is ill-posed (non-zero curl) | **CORROBORATED** | Arend & Goldstein 1987 |
| A filling-in model using UNMODIFIED gradients destroys the illusion (reconstructs the veridical image) | **CORROBORATED — this is the diagnosis** | Cohen-Duwek & Spitzer 2019 |
| The specific sign-INVERSION we measured is reported verbatim in the literature | **UNDETERMINED** — the null-crossing is fully explained (Cohen-Duwek & Spitzer), but I found no paper reporting a sign-inverted Cornsweet produced by far-field plane extrapolation specifically | would be resolved by: a modelling paper that ablates the gradient-weighting step and reports the resulting percept. Cohen-Duwek & Spitzer state the consequence but do not show the ablation. |
| A percept opposing the local luminance gradient is always an error | **CONTRADICTED** — it is the human result under cumulative geometry | Cavanagh & Anstis 2018 |
| The true percept is a flat plateau | **CONTRADICTED** (for induction generally; untested for COCE) | Blakeslee & McCourt 2013 |
| Filling-in is the consensus explanation of Cornsweet | **CONTRADICTED — genuinely contested** | Robinson & de Sa 2013; Blakeslee & McCourt 1999; Purves et al. 1999 |

### 1.8 Recommended actions from Section 1

**In priority order.**

1. **Weight the gradient before you use it — do not escalate to the raw
   gradient** (§1.5b). This is the answer. Three independent camps converge on
   it: Retinex thresholds the slow component away (1971), Arend & Goldstein
   confine it by field segmentation (1987), Cohen-Duwek & Spitzer weight it by a
   multi-scale dominance function (2019). The last has published parameters that
   reproduce COCE. A faithful order-2 code is *supposed* to destroy the
   illusion — that is what fidelity means — so the escalation predicate must
   admit only the dominant-scale component of the residual.
2. **Check for a boundary-gating leak on the order-2 path** (§1.3). Cheapest
   possible test, and the curl result says far-field extrapolation is ill-posed
   regardless. If our order-2 code escapes its compartment, that is our bug and
   nothing in the literature excuses it.
3. **Change order-2 from "plane, extrapolated" to "edge-anchored decaying
   gradient"** (§1.4). Falsifiable prediction: Cornsweet survives escalation AND
   we gain the Blakeslee–McCourt decline-with-distance signature for free.
4. **Discriminate single-edge from cumulative geometry in the test** (§1.5c).
   Inversion is a bug on one edge and the human result on diamond patterns. A
   test that does not separate these will mislead us in both directions.
5. **Use the executable ODOG notebooks as an external oracle** (§1.5) — a
   published, independent implementation from the camp that *disagrees* with our
   mechanism. Checking against a hostile oracle is the strongest test available.

---

## 2. PAINT-FROM-SAMPLE — ARTIFACTS, ESPECIALLY BOUNDARY ASYMMETRY

**Headline verdict: the asymmetry is CORROBORATED, twice, independently, and in
both cases it is stated as CONSTITUTIVE of the method rather than as a bug.**
Colour/appearance crosses weak and iso-luminant contours while being stopped by
strong ones, because every method in this family carries exactly one affinity
criterion, and one criterion necessarily partitions contours into "above" and
"below" it. Our mechanism contains nothing about the asymmetry and produced it
anyway — that is the expected outcome, not a surprise, and graphics has been
living with it for twenty years.

### 2.1 The asymmetry — deciding citations

**(a) Colorization. CORROBORATED, verbatim.**

- **Kim, E., Lee, S., Park, J., Choi, S., Seo, C. & Choo, J. (2021). Deep
  Edge-Aware Interactive Colorization against Color-Bleeding Effects.
  *ICCV 2021* (oral).** <https://arxiv.org/abs/2107.01619> ·
  project page <https://eungyeupkim.github.io/edge-enhancing-colorization/>

  From the Introduction, verbatim:

  > "their improvements are limited to edges appearing with strong gray-scale
  > contrast or along the objects corresponding to the predefined categories.
  > **Color bleeding often occurs between the different objects that share
  > similar gray-scale intensities** and also along the edges that appear inside
  > the objects, such as a zigzag pattern of a color pencil"

  And the definition of the artifact itself:

  > "the color-bleeding artifact, a problematic color spreading near the
  > boundaries between adjacent objects"

  This is the asymmetry stated exactly as we measured it: strong contrast stops
  the spread, similar-intensity (iso-luminant) contours do not. Their fix is to
  give up on automatic edge detection entirely and take a **user scribble**
  marking the bleeding edge — which is an admission that the asymmetry is not
  solvable from within the luminance-affinity framework.

**(b) Edge-aware filtering. CORROBORATED, and stated as UNAVOIDABLE.**

- **He, K., Sun, J. & Tang, X. (2013). Guided Image Filtering.
  *IEEE TPAMI* 35(6), 1397–1409** (orig. ECCV 2010).
  <https://people.csail.mit.edu/kaiming/publications/pami12guidedfilter.pdf>

  From the Limitations section, verbatim:

  > "The guided filter has a common limitation of other explicit filters—it may
  > exhibit halos near some edges. 'Halos' refer to the artifacts of unwanted
  > smoothing of edges. (On the contrary, 'gradient reversal' refers to the
  > artifacts of unwanted sharpening of edges...) **Halos are unavoidable for
  > local filters when the filters are forced to smooth some edges. For example,
  > if strong textures are to be smoothed, the weaker edges would also be
  > smoothed.** Local filters like guided/bilateral filters would concentrate the
  > blurring near these edges and introduce halos. Global optimization-based
  > filters (e.g. the WLS filter) would distribute such blurring more globally.
  > The halos are suppressed at the price of global intensity shifting."

  And, on Fig. 8, the iso-luminant case in one sentence:

  > "The result in (c) has halos because the edge is not [in]distinguishable in
  > gray-scale."

  Two things fall out of this that matter to us. First, **the strong/weak
  asymmetry is named explicitly** ("if strong textures are to be smoothed, the
  weaker edges would also be smoothed"). Second, **it is proved to be a
  structural property of LOCAL methods**, and the escape is global optimization,
  which trades the local artifact for a global one (intensity shifting). There is
  no free lunch here and the field knows it.

**Consequence for us: our measured asymmetry is not evidence of a defect in our
mechanism, and it is also not evidence of anything special about it.** It is the
generic signature of appearance propagation gated by a single scalar affinity.
We should stop treating it as a finding and start treating it as a constraint we
inherited, with a twenty-year literature attached.

### 2.2 Colorization by optimization — the mechanism and its assumption

- **Levin, A., Lischinski, D. & Weiss, Y. (2004). Colorization using
  optimization. *ACM Transactions on Graphics (SIGGRAPH)* 23(3), 689–694.**
  <https://dl.acm.org/doi/10.1145/1186562.1015780>

  The premise, in the authors' framing: *neighbouring pixels in space-time that
  have similar intensities should have similar colours.* Formalised as a
  quadratic cost minimised subject to user-scribble constraints; the solution
  propagates colour "in a manner that respects intensity boundaries."

  **The assumption is the whole story.** Affinity is computed from luminance
  only. Therefore: (i) a boundary that is real but iso-luminant is invisible to
  the affinity and colour crosses it; (ii) a strong luminance step stops colour
  even when it is not an object boundary (e.g. a shadow edge or a specular
  highlight within one object) — the *converse* error, and one we should check
  for in our own system since it is the same mechanism's other failure mode.
  Shadow-aware colorization exists precisely because of (ii):
  <https://link.springer.com/article/10.1007/s00371-024-03500-5>

  A modern survey of the whole line: *Two Decades of Colorization and
  Decolorization for Images and Videos*
  <https://www.researchgate.net/publication/360254530> ; and *From shades to
  vibrance: a comprehensive review of modern image colorization techniques*,
  Frontiers in Computer Science (2025)
  <https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1626641/full>
  — the latter names "edge noise, color bleeding, and boundary mismatch" as
  widespread structural distortions, "especially evident in models without strong
  instance-awareness or edge supervision."

### 2.3 Inpainting — a different family, a different dominant artifact

Relevant because it is the same "fill a region from a sample" operation, but the
artifact that dominates is **error propagation through greedy fill order**, not
boundary asymmetry.

- **Criminisi, A., Pérez, P. & Toyama, K. (2004). Region filling and object
  removal by exemplar-based image inpainting. *IEEE TIP* 13(9), 1200–1212.**
  Known limitations, well documented by the improvement literature:
  - the **confidence term decays to zero** after several fill levels, after
    which the priority ordering carries no information ("fast priority
    dropping");
  - **unreasonable priority calculation** — the data/confidence product is
    fragile;
  - the greedy order means **"bad choices on the borders make the completion of
    the centre impossible"** — an early wrong patch is never revisited;
  - high time complexity from exhaustive patch search.
  Survey of the fixes: <https://thesai.org/Downloads/Volume10No6/Paper_55-A_New_Image_Inpainting_Approach.pdf>
  ; structure-consistent patch matching, *Neurocomputing* (2018)
  <https://www.sciencedirect.com/science/article/pii/S0925231217309773>
- **Telea, A. (2004). An image inpainting technique based on the fast marching
  method. *Journal of Graphics Tools* 9(1), 23–34.** Cheap and robust; known to
  go **blurry over large regions** (it is a diffusion, so it has exactly the
  flat-fill character discussed in §1.1).
- **Barnes, C., Shechtman, E., Finkelstein, A. & Goldman, D. B. (2009).
  PatchMatch: a randomized correspondence algorithm for structural image
  editing. *ACM TOG (SIGGRAPH)* 28(3).** The standard fast approximate patch
  search. Note for us: it is **approximate and randomized** — it does not give
  byte-identical outputs across runs unless the seed is pinned. Given our stated
  preference for exact, byte-identical results, PatchMatch is borrowable only
  with a fixed seed and a documented determinism gate.

### 2.4 Texture synthesis — the escalation target, and its failure mode

Directly relevant because "texture" is the top rung of our escalation ladder.

- **Efros, A. A. & Leung, T. K. (1999). Texture synthesis by non-parametric
  sampling. *ICCV 1999.***
  <https://people.eecs.berkeley.edu/~efros/research/EfrosLeung.html>
  **The known failure mode is a two-sided trap**, and the IPOL reproducibility
  paper states it bluntly:
  > "The path between verbatim copy of the exemplar and garbage growing is
  > somewhat narrow... it is often hardly possible to set parameters in order to
  > avoid both garbage growing and verbatim copy."
  and: the algorithm sometimes "slips into a wrong part of the search space and
  starts growing garbage", **especially when the input texture is not
  stationary.**
  Reference implementation with full analysis: Aguerrebere, Gousseau & Tartavel,
  *Exemplar-based Texture Synthesis: the Efros–Leung Algorithm*, **IPOL 2013**
  <http://www.ipol.im/pub/art/2013/59/> — peer-reviewed, executable, with source.
  **This is the single best borrowable artifact in Section 2: a reference
  implementation with a published failure analysis.**

  *Why this matters to our ladder specifically:* the non-stationarity condition
  is the same condition that makes a region demand escalation in the first place.
  So our order-3 rung inherits a failure mode that is *correlated with the
  trigger for entering that rung.* That is worth a pre-registered check.

- **Efros, A. A. & Freeman, W. T. (2001). Image quilting for texture synthesis
  and transfer. *SIGGRAPH 2001.*** The minimum-error-boundary-cut is the
  standard fix for seam artifacts when pasting sampled patches — directly
  applicable if we ever paste rather than parameterise.

### 2.5 Superpixels — the region-proposal layer

- **Achanta, R., Shaji, A., Smith, K., Lucchi, A., Fua, P. & Süsstrunk, S.
  (2012). SLIC superpixels compared to state-of-the-art superpixel methods.
  *IEEE TPAMI* 34(11), 2274–2282.**
  <https://www.cs.jhu.edu/~ayuille1/JHUcourses/VisionAsBayesianInference2022/4/Achanta_SLIC_PAMI2012.pdf>
  k-means in 5-D (CIELAB + xy) with a search window bounded by the superpixel
  size. Two parameters: number of superpixels, and **compactness** — which is
  precisely a knob trading boundary adherence against regularity.
  Relevant honest note: the compactness parameter is *another single scalar
  affinity criterion*, so SLIC inherits the same asymmetry — and the review
  literature confirms that "algorithms less focused on compactness showed greater
  robustness to image transformations."
  Modern taxonomy/survey: <https://arxiv.org/html/2409.19179v1>

### 2.6 Verdicts

| Claim | Verdict | Deciding citation |
|---|---|---|
| Colour bleeding across boundaries is a known nuisance in colorization | **CORROBORATED** | Kim et al. ICCV 2021 |
| The bleeding shows a STRONG vs WEAK / iso-luminant ASYMMETRY | **CORROBORATED, verbatim, twice** | Kim et al. 2021 ("objects that share similar gray-scale intensities"); He et al. TPAMI 2013 ("if strong textures are to be smoothed, the weaker edges would also be smoothed") |
| The asymmetry is a bug that can be fixed within the framework | **CONTRADICTED** — "halos are unavoidable for local filters"; the SOTA fix is a user scribble | He et al. 2013; Kim et al. 2021 |
| Our mechanism producing the asymmetry without encoding it is notable | **CONTRADICTED as novelty; CORROBORATED as correctness** — it is the generic signature of single-scalar affinity gating | §2.1 |
| The converse error (strong non-object edge wrongly stops the fill) is also known | **CORROBORATED** | shadow-aware colorization, Visual Computer 2024 |
| Exemplar/texture synthesis has a narrow parameter window between verbatim copy and garbage | **CORROBORATED** | IPOL 2013 (Efros–Leung analysis) |

### 2.7 Recommended actions from Section 2

1. **Reclassify our asymmetry result** from "finding" to "inherited constraint,
   corroborated" and cite Kim et al. 2021 + He et al. 2013 wherever we report it.
2. **Go and test the CONVERSE failure** (§2.2 (ii)): does a strong but
   non-object contour — a shadow edge, a specular highlight — wrongly stop our
   fill? The literature says it must. If it does not, *that* is the interesting
   result, and it is a much higher bar than the one we cleared.
3. **Pre-register a non-stationarity check on the order-3 (texture) rung**
   (§2.4). The garbage-growing failure mode correlates with the escalation
   trigger.
4. **Note the determinism cost of PatchMatch** before adopting it (§2.3) — it is
   randomized, and we prefer byte-identical outputs.

---

## 3. RESIDUAL / MULTI-STAGE VECTOR QUANTIZATION

**Headline verdict: PARTLY the same operation — and the most useful finding is a
NEGATIVE. Our mechanism shares RVQ's residual recursion but differs on three of
four defining properties, and the majority of RVQ's famous failure modes
(codebook collapse, straight-through-estimator bias, commitment-loss tuning,
quantizer dropout) are artifacts of learning a codebook by gradient descent.
A system that MINTS an entry when a residual is unexplained has no gradient, no
STE and no commitment loss, so those modes are STRUCTURALLY INAPPLICABLE, not
merely unobserved. Importing their mitigations would be cargo-culting.**

What does transfer is smaller, older and less cited: **greedy-stagewise
suboptimality**, **uneven stage utilization**, and **stage-count diminishing
returns**. Section 3.3 is the one that should change our behaviour.

### 3.1 Is it RVQ? — decompose and check

| Property | Classical RVQ/MSVQ | Ours | Same? |
|---|---|---|---|
| Sequential refinement of the previous stage's *residual* | Yes (defining) | Yes | **SAME** |
| Depth applied uniformly to every vector | Yes | No — conditional on residual | **DIFFERENT** |
| Codebook fixed at operation time | Yes (trained offline) | No — minted at operation time | **DIFFERENT** |
| Stages homogeneous (same codebook structure, successive residual spaces) | Yes | No — constant → plane → texture is a *model-class* escalation | **DIFFERENT** |

**The residual recursion is genuinely the same.** Juang & Gray's formulation —
quantize, subtract, quantize the residual with a second codebook — is exactly
our "encode with a low-order code, measure residual" step.
- **Juang, B.-H. & Gray, A. H. (1982). Multiple stage vector quantization for
  speech coding. *ICASSP 1982*, vol. 7, 597–600.**
  <https://doi.org/10.1109/ICASSP.1982.1171604>
- **Barnes, C. F. & Frost, R. L. (1993). Vector quantizers with direct sum
  codebooks. *IEEE Trans. Information Theory* 39(2), 565–580.** Formalises the
  **direct-sum codebook**: N stages of size M give Mᴺ effective codewords at N·M
  storage.
- **Barnes, Rizvi & Nasrabadi (1996). Advances in residual vector quantization:
  a review. *IEEE Trans. Image Processing* 5(2).** — the survey.
- **Gersho, A. & Gray, R. M. (1992). *Vector Quantization and Signal
  Compression.* Kluwer.** <https://link.springer.com/book/10.1007/978-1-4615-3626-0>
  Unifies tree-structured, multistage, product and mean-removed VQ as one
  constrained-VQ family, all trading optimality for complexity. (Chapter number
  for the constrained-VQ treatment unverified — believed Ch. 12.)

**Conditional depth IS a known variant, but it is recent and thin.**
- **Chae et al. (2025). VRVQ: Variable Bitrate Residual Vector Quantization for
  Audio Coding. *ICASSP 2025*.** <https://arxiv.org/abs/2410.06016> ·
  <https://github.com/SonyResearch/VRVQ>
  Their motivation is ours verbatim: current models use "a fixed number of
  codebooks per frame, which can be suboptimal in terms of rate-distortion
  tradeoff, particularly in scenarios with simple input audio, such as silence."
  **Difference that favours us:** VRVQ *learns* the allocation via a
  differentiable importance map with an STE through the masking operation. We
  *read* the allocation off a measured residual threshold. Ours is simpler and
  more interpretable.
- SwitchCodec — dynamically-activated expert quantizers per input.
  <https://arxiv.org/pdf/2505.24437>

**⚠ TERMINOLOGY WARNING — "quantizer dropout" is NOT conditional depth.**
SoundStream's dropout selects n_q uniformly at *random* per training example. It
is a training regularizer to make one model serve many bitrates, not a
residual-driven decision. **Do not cite it as prior art for our mechanism.**

**Our REAL closest prior art is not RVQ at all — it is the quadtree literature.**
Heterogeneous model classes per stage (flat → plane → texture) is
**variable-block-size polynomial coding**: blocks approximated by
`f(x,y) = a + bx + cy` with least-squares fit and a residual/threshold-driven
split criterion.
- Quadtree-structured recursive plane decomposition coding of images:
  <https://www.academia.edu/27122142/Quadtree_structured_recursive_plane_decomposition_coding_of_images>
- Image coding based on quadtree-structured recursive least-squares
  approximation: <https://ieeexplore.ieee.org/document/266841/>
- **HEVC's Residual Quadtree (RQT)** is the production descendant:
  <https://www.hhi.fraunhofer.de/en/departments/vca/research-groups/video-coding-technologies/research-topics-of-video-coding-technologies-group/past-research-topics/hevc-high-efficiency-video-coding/transform-coding-using-the-residual-quadtree-rqt-1.html>

**Recommendation: stop calling it RVQ.** "RVQ" invites RVQ's failure modes as
objections, most of which do not apply. The accurate framing is **"residual-driven
order escalation with an online-grown codebook"** — RVQ-like in recursion,
quadtree-like in order escalation, and genuinely novel in operation-time minting.
This also connects Section 3 back to Section 1: HEVC RQT and the Cornsweet
escalation are the same operation, and the codec literature has been tuning its
split criterion for twenty years.

### 3.2 The modern learned lineage — what each contributed

- **van den Oord, Vinyals & Kavukcuoglu (2017). Neural Discrete Representation
  Learning (VQ-VAE). *NeurIPS 2017*.** <https://arxiv.org/abs/1711.00937>
  The discrete bottleneck trained end-to-end via the **straight-through
  estimator** + **commitment loss** (weight β). Single-stage, not RVQ.
- **Razavi, van den Oord & Vinyals (2019). VQ-VAE-2. *NeurIPS 2019*.**
  <https://arxiv.org/abs/1906.00446> Hierarchical multi-scale codes — *hierarchy*
  buys fidelity, not just more codes. Scale-hierarchical, not residual-staged.
- **Zeghidour et al. (2021). SoundStream. *IEEE/ACM TASLP*.**
  <https://arxiv.org/abs/2107.03312> RVQ into a jointly-trained neural codec +
  structured quantizer dropout, claiming 3–18 kbps from one model "with a
  negligible quality loss". **DAC later contradicts this — see 3.4.**
- **Défossez et al. (2022). EnCodec: High Fidelity Neural Audio Compression.**
  <https://arxiv.org/pdf/2210.13438> The **loss balancer**, plus a Transformer
  entropy model over quantized units for a further 20–30% bandwidth reduction.
- **Kumar et al. (2023). High-Fidelity Audio Compression with Improved RVQGAN
  (DAC). *NeurIPS 2023*.** <https://arxiv.org/pdf/2306.06546> **The most useful
  paper here, because it diagnoses failures rather than claiming successes.**

### 3.3 THE FAILURE MODE THAT ACTUALLY REACHES US — greedy-stagewise suboptimality

**This is our real exposure and it is the oldest failure mode in the field.**

Stage 1 picks the codeword minimising *its own* distortion. That choice fixes the
residual stage 2 must handle. The pair (stage-1, stage-2) minimising *total*
distortion may require stage 1 to make a locally *worse* choice. Sequential
encoding cannot find it. The literature states it directly: "the sequential
search path is greedy based on a stage-wise nearest-neighborhood strategy instead
of a direct sum nearest-neighborhood requirement", and "the conventional
stage-by-stage design of the codebooks in MSVQ is suboptimal with respect to the
overall performance measure."

**Why this bites our ladder specifically.** Our stage 1 is a *constant fit*. The
constant minimising stage-1 residual is the **mean**. But the mean is not
necessarily the constant that leaves a residual most *explainable by a plane*. A
greedy constant fit can manufacture residual structure the next order handles
worse than a jointly-chosen pair would.

**Note the convergence with Section 1.** §1.5b says a faithful order-2 code
destroys the Cornsweet illusion; §3.3 says a greedy order-1 code manufactures the
residual that triggers order-2. These are the same seam viewed from two
literatures. **The escalation decision is where both problems live.**

Known fixes, all with costs:
- **M-L / M-search (delayed decision):** keep the best M candidates per stage,
  resolve at the end. Cost: M× the search.
- **Joint codebook design:** optimise all stage codebooks against the total
  objective. Chan & Gersho et al., *Enhanced multistage vector quantization by
  joint codebook design*: <https://ieeexplore.ieee.org/document/179932/>
- **Barnes & Frost's caution:** optimal stagewise partitioning can cost *more*
  than exhaustive direct-sum search. Staging buys **storage**, not necessarily
  **search time**. No free lunch.

**→ RECOMMENDED EXPERIMENT, HIGHEST PRIORITY IN SECTION 3.** Compare greedy
(constant-then-plane) against a **joint least-squares plane fit** on identical
regions. Cheap, exact, and it is the first objection a reviewer from the
classical VQ community will raise.

### 3.4 Failure modes that do NOT reach us — and why that is worth stating

| Failure mode | Root cause | Reaches us? |
|---|---|---|
| Codebook collapse (gradient variety) | STE gives uninformative gradients; unselected codes never updated; encoder drift | **No** — no gradient, no encoder drift |
| STE bias | Gradient approximation through non-differentiable argmin | **No** |
| Commitment-loss β tuning | Balancing a learned objective | **No** |
| Quantizer dropout side effects | Random truncation during *training* | **No** (unless we adopt dropout) |
| Dead codes / low utilization | Codes that stop being selected | **Possibly — different cause, see 3.5** |
| Greedy-stagewise suboptimality | Local-vs-global stage choice | **YES — §3.3** |
| Uneven stage utilization ("hourglass") | Structural to residual staging | **YES — §3.6** |
| Stage-count diminishing returns | Structural | **YES — §3.7** |

For the record, since these are the famous ones and we will be asked:

**Codebook collapse.** DAC: "We identify a critical issue in existing models
which don't utilize the full bandwidth due to **codebook collapse** (where a
fraction of the codes are unused)." Measured utilization from the rotation-trick
paper is startling — **ViT-VQGAN on ImageNet: 0.3%**; TimeSformer/BAIR 0.4%;
TimeSformer/UCF-101 0.1%. Fifty et al., *Restructuring Vector Quantization with
the Rotation Trick* <https://arxiv.org/html/2410.06424v1>. Causes: uninformative
STE gradient ("the location of e within the Voronoi partition — be it close to q
or far away at the boundary — has no impact on the gradient update"); and encoder
non-stationarity.

**The one collapse fix with a transferable lesson:** DAC's **factorized +
L2-normalized codes** — do the lookup in a *low-dimensional* space. Their
latent-dimension ablation, bitrate efficiency:

| Latent dim | 2 | 4 | **8** | 32 | 256 |
|---|---|---|---|---|---|
| Bitrate efficiency | 84% | 97% | **99%** | 98% | **59%** |

Lookup in the native 256-d space costs **40 points of efficiency**. The
transferable lesson for us is forward-looking: **if we ever scale K, reducing
lookup dimensionality will buy more than indexing will** (see §4).

Also notable, and a caution about ablating one thing at a time: DAC found the
*adversarial loss* was load-bearing for codebook usage — removing it dropped
bitrate efficiency 99% → 62%. Utilization is sensitive to the *whole* objective.
**Our corollary is a genuine simplification worth claiming: our utilization is
determined by our minting criterion and nothing else.**

### 3.5 Dead codes — reaches us by a different route

We have no gradient, so codes cannot "drift dead". But we *can* accumulate
entries minted from one-off residuals never selected again — same *symptom*
(index skew, wasted capacity), different *cause* (over-eager minting /
noise-fitting rather than optimization failure).

**→ BORROWABLE INSTRUMENT, adopt this.** DAC's **bitrate efficiency**: "the sum
of the entropy (in bits) of each codebook when applied on a large test set
divided by the number of bits across all codebooks. For efficient bitrate
utilization this should tend to 100%." Compute the empirical entropy of our index
distribution against log₂(K). **Learning-free, cheap, works at K=4 as well as
K=1024, and it would tell us immediately whether minted entries are earning their
place.** This is the best single instrument in this document.

### 3.6 Uneven stage utilization — the "hourglass", and an open question that is ours to answer

In RQ-VAE semantic IDs, intermediate-layer codebook tokens become "overly
concentrated", producing an hourglass distribution — described as "a
characteristic feature of the RQ-VAE architecture". *Breaking the Hourglass
Phenomenon of Residual Quantization*, EMNLP 2024 Industry Track:
<https://aclanthology.org/2024.emnlp-industry.50.pdf>

The general point survives the neural specifics: **stages in a residual cascade
do not carry equal information, and the middle stages are the usual casualty.**

**With conditional depth this could go either way** — worse (deep stages see only
the hard tail, a heavily biased sample) or better (we never waste a stage on an
easy region). **I could not find any paper measuring utilization skew under
CONDITIONAL depth. VRVQ does not report it. This is a genuine open question and a
free, publishable measurement our architecture is uniquely positioned to make.**

### 3.7 Stage-count diminishing returns — the argument FOR our design

Structural: each stage operates on a residual with less energy and less structure
than the last. DAC's Figure 1 shows per-codebook entropy decaying across 32
codebooks (EnCodec: ~9.6 → ~8.8 bits against a 10-bit ceiling).

**Our conditional mechanism is a direct attack on this problem — we spend stages
only where energy remains. This is the strongest theoretical argument for the
design and the one to lead with.**

### 3.8 The dropout cautionary tale — a published claim overturned by ablation

Worth recording because it is a clean instance of the discipline we care about.
SoundStream (2021) claimed dropout gives variable bitrate "with a negligible
quality loss". DAC (2023) measured it:

> "We identify a side-effect of **quantizer dropout** — a technique designed to
> allow a single model to support variable bitrates, actually hurts the
> full-bandwidth audio quality"

| Dropout prob. | Mel dist ↓ | ViSQOL ↑ | **SI-SDR ↑** |
|---|---|---|---|
| **0.0** (none) | **0.98** | 4.09 | **10.14** |
| 0.5 (DAC's compromise) | 1.01 | 4.03 | 9.74 |
| **1.0** (SoundStream-style) | 1.09 | 3.96 | **9.12** |

**~1.02 dB SI-SDR cost at full bandwidth.** They keep p=0.5 knowingly, buying
variable-rate capability with full-rate quality.

**Indirect but real relevance to us:** the *shape* of the lesson generalises to
any conditional-depth scheme. **If later stages are ever fitted or tuned in the
presence of truncated prefixes, the full-depth path degrades.** If our
higher-order codes are ever minted or adjusted using statistics gathered only
from regions that escalated, we have the same asymmetry by another route. Worth
checking.

One more general warning from DAC worth carrying: their *balanced data sampling*
finding — without it, "the model produces waveforms that have a max frequency of
around 18kHz" because the corpus's average true sampling rate silently became a
ceiling. **The model learned the statistics of the corpus rather than the physics
of the signal.** For a system that mints codes from observed residuals the risk
is direct and there is no loss function to tell us it happened.

### 3.9 Verdicts

| Claim | Verdict | Deciding citation |
|---|---|---|
| The residual recursion is the same operation as RVQ/MSVQ | **CORROBORATED** | Juang & Gray 1982; Barnes & Frost 1993 |
| Conditional (residual-driven) depth is a known variant | **CORROBORATED, but recent and thin** | Chae et al. VRVQ, ICASSP 2025 |
| Heterogeneous model-class escalation (flat→plane→texture) is RVQ | **CONTRADICTED — it is quadtree variable-block polynomial coding** | quadtree RLS coding; HEVC RQT |
| Operation-time codebook minting is standard in RVQ | **CONTRADICTED — every RVQ system found trains offline and freezes** | (absence across the surveyed lineage) |
| RVQ's famous failure modes apply to us | **CONTRADICTED for the gradient-derived majority** | §3.4 applicability table |
| Greedy-stagewise suboptimality applies to us | **CORROBORATED — our main exposure** | Barnes & Frost 1993; Chan & Gersho |
| Utilization skew under conditional depth is characterised | **UNDETERMINED — nobody has measured it** | would be resolved by: our own measurement. VRVQ is the paper that should have reported it and does not. |

---

## 4. ANN FOR A *GROWING* CODEBOOK (demoted)

**Headline verdict: DROP THIS ENTIRELY FOR NOW. At K = 1–4 the answer is
brute-force linear scan, and the literature's own numbers show the alternatives
are ACTIVELY SLOWER at small k.** The demotion was correct and the evidence
supports going further than demotion.

### 4.1 The decisive numbers

Hamerly's Table 2 reports wall-clock across k = 3, 20, 100, 500 on n = 1.25M:

| Dataset | k | Lloyd's (naive) | Elkan | Hamerly | k-d tree |
|---|---|---|---|---|---|
| uniform, d=2 | **3** | 4.0 s | **7.2 s** ← *slower than naive* | 2.7 s | 3.5 s |
| uniform, d=32 | **3** | 66.4 s | 48.1 s | 46.9 s | **208.4 s** ← *3× slower* |
| mnist50, d=50 | **3** | 2.92 s | 2.42 s | 2.41 s | 4.90 s |
| covtype, d=54 | **3** | 3.52 s | 3.07 s | 2.95 s | 6.65 s |

At k=3, **Elkan's exact acceleration is 80% slower than brute force** in low
dimension and the k-d tree is **3× slower** in d=32. The best accelerator buys
~1.2–1.4× on realistic data.

Hamerly's general principle settles it: "With high-dimensional data, indexing
schemes such as k-d trees do not work well, to the point where examining every
data point (i.e. using no special data structure for acceleration) can be much
faster than algorithms intended for low-dimensional acceleration."
- **Hamerly, G. (2010). Making k-means even faster. *SDM 2010*.**
  <https://www.ccs.neu.edu/home/radivojac/classes/2024fallcs6140/hamerly_sdm_2010.pdf>

At K = 1–4, the whole comparison is a handful of distance evaluations — likely
one cache line, fully vectorizable, no branch mispredictions. Elkan's O(k²)
inter-center distance table at k=4 is 16 entries maintained to avoid at most 3
distance computations.

### 4.2 The question actually worth answering: incremental insertion

**HNSW is natively incremental** — an explicit design claim: the construction
"does not require the elements to be shuffled before the insertion — the
stochasticity is achieved by using level randomization, thus allowing truly
incremental indexing even in case of temporarily alternating data distribution."
Insertion is O(log N) expected.
- **Malkov, Y. A. & Yashunin, D. A. (2018). Efficient and robust approximate
  nearest neighbor search using HNSW graphs. *IEEE TPAMI* 42(4), 824–836.**
  <https://arxiv.org/pdf/1603.09320>

**But the incremental claim does not survive sustained update streams.**
- **Singh, Subramanya, Krishnaswamy & Simhadri (2021). FreshDiskANN.**
  <https://arxiv.org/pdf/2105.09613> — "simple graph update rules result in
  degradation of index quality over a stream of insertions and deletions for
  popular graph-based algorithms such as HNSW and NSG", with "a consistently
  deteriorating trend in search performance with recall dropping for a fixed
  candidate list size."
- **Deletion is worse than insertion.** FreshDiskANN marks deletes lazily;
  "accumulating a large number of deletes leads to a drop in index recall",
  requiring periodic offline consolidation that "incurs latency spikes and
  operational overhead." HNSW specifically "can create unreachable points in the
  graph after deletion and insertion operations"
  (<https://arxiv.org/html/2407.07871v1>). **If our codebook ever RETIRES
  entries, this is the sharp edge** — and note we already have retire semantics
  elsewhere in the substrate.
- **FAISS IVF**: vectors can be added without retraining the coarse quantizer,
  but centroids were fit to the old distribution → unbalanced inverted lists and
  recall decay under drift; mitigation is periodic retraining. *Sourced from
  FAISS documentation and secondary write-ups, not a primary paper with measured
  drift curves — see §7.*

### 4.3 Exact (non-approximate) speedups — the right family if we ever need one

Since we want byte-identical output, §4.2's family is the wrong one. These
preserve exactness:

- **Partial Distortion Elimination (PDE)** — accumulate squared distance
  dimension-by-dimension; abort as soon as the partial sum exceeds the current
  best. Zero assumptions, trivially exact, composes with everything.
  **Caveat: "The overhead of partial distance search is usually only cost
  effective in high dimension."** The one technique nearly free enough to
  consider at our K — though at K≤4 the branch cost likely exceeds the arithmetic
  saved.
- **ENNS** — Guan, L. & Kamel, M. (1992). Equal-average hyperplane partitioning
  method for vector quantization of image data. *Pattern Recognition Letters*
  13(10), 693–699. Prunes on the difference of vector means. Assumes squared
  Euclidean. Characterised in the ANN literature as giving "modest constant
  factor improvements... by projecting points onto a single line".
- **Elkan, C. (2003). Using the triangle inequality to accelerate k-means.
  *ICML 2003*.** <https://cdn.aaai.org/ICML/2003/ICML03-022.pdf> Exact; n upper
  bounds + kn lower bounds + O(k²) inter-center distances. Author's claim: for
  **k ≥ 20** many times faster than the prior best — i.e. **explicitly outside our
  regime.**
- **Hamerly (2010)** — one lower bound per point instead of k; "eliminate the
  innermost k-means loop 80% of the time or more"; memory **O(n)** vs Elkan's
  **O(nk + k²)**; wins up to ~50 dimensions, Elkan wins higher.

### 4.4 Verdicts

| Claim | Verdict | Deciding citation |
|---|---|---|
| ANN methods assume a static pre-trained codebook | **CORROBORATED with an exception** — HNSW is natively incremental by design | Malkov & Yashunin 2018 |
| Incremental insertion is free / lossless | **CONTRADICTED** — index quality degrades over update streams | FreshDiskANN 2021 |
| Deletion is the harder case | **CORROBORATED** | FreshDiskANN 2021; arXiv 2407.07871 |
| Indexing helps at our K (1–4) | **CONTRADICTED — it actively hurts** | Hamerly SDM 2010, Table 2 |
| A principled brute-force/index crossover point is established | **UNDETERMINED** | see §7 |

### 4.5 Recommended action

**Do nothing here.** Revisit only if K crosses ~1000 *and* profiling shows the
comparison loop is hot — and note DAC's factorization result (§3.4: 99% vs 59% at
8-d vs 256-d lookup) suggests that **if we ever scale K, reducing lookup
dimensionality will buy more than indexing will.**

---

## 5. SETTLED / CONTESTED / FOLK

### SETTLED — treat as established; cite, don't re-derive

1. **Diffusive filling-in produces a FLAT fill inside a boundary-sealed
   compartment, and reproduces Cornsweet.** (Grossberg & Todorović 1988.) It is
   what the PDE does, not a modelling choice.
2. **A filling-in system that uses UNMODIFIED gradients reconstructs the
   veridical image and destroys the illusion.** (Cohen-Duwek & Spitzer 2019,
   verbatim.) The raw gradient must be weighted/thresholded before use — three
   independent camps converge on this (Retinex 1971, Arend & Goldstein 1987,
   Cohen-Duwek & Spitzer 2019).
3. **Thresholded image derivatives have non-zero curl; simple spatial
   integration is therefore ill-posed.** (Arend & Goldstein 1987.)
4. **Appearance propagation gated by a single scalar affinity crosses weak and
   iso-luminant contours while being stopped by strong ones.** (Kim et al. 2021;
   He et al. 2013.) Stated as unavoidable for local filters.
5. **Halos vs gradient reversal are distinct artifacts with distinct causes**, and
   the global-optimization escape trades local halos for global intensity
   shifting. (He, Sun & Tang 2013.)
6. **Exemplar texture synthesis has a narrow parameter window between verbatim
   copy and garbage growing**, and garbage growing is worst on non-stationary
   input. (IPOL 2013.)
7. **The residual recursion (quantize, subtract, quantize the residual) is
   RVQ/MSVQ.** (Juang & Gray 1982.)
8. **Greedy stagewise encoding is suboptimal w.r.t. total distortion**, and
   optimal stagewise partitioning can cost more than exhaustive direct-sum
   search. (Barnes & Frost 1993.)
9. **Codebook indexing is counterproductive at small k** — measurably slower than
   brute force. (Hamerly 2010, Table 2.)
10. **Graph ANN indices degrade in quality over sustained insert/delete streams**,
    deletion worse than insertion. (FreshDiskANN 2021.)

### CONTESTED — genuinely open; do not cite one side as settled

1. **Whether the brain fills in at all.** Filling-in (Grossberg; Paradiso &
   Nakayama 1991; Davey et al. 1998) vs multiscale filtering (Blakeslee &
   McCourt 1999, 2013; Robinson & de Sa 2013) vs empirical/statistical (Purves
   et al. 1999) vs the philosophical anti-filling-in position (Dennett 1991;
   Pessoa, Thompson & Noë 1998 BBS + commentary). **All four camps are live in
   2026.** The strongest COCE-*specific* pro-filling-in evidence is a *timing*
   argument (finite propagation speed), which is the one thing a feedforward
   filter bank cannot easily produce.
2. **Whether the induced percept is flat or a decaying gradient.** Measured as
   declining-with-distance for grating induction, simultaneous contrast and
   White's effect (Blakeslee & McCourt 2013) — but **not tested for COCE
   specifically.**
3. **Whether a percept opposing the local luminance gradient is an error.** It is
   the human result under cumulative diamond geometry (Cavanagh & Anstis 2018).
4. **The standing of BCS/FCS/FACADE.** Influential and still extended, but with
   documented specific failures (non-assimilative watercolour; afterimage data
   requiring non-diffusive filling-in; the anchoring problem) and under pressure
   from the filtering camp.
5. **Whether quantizer dropout is free.** SoundStream 2021 says negligible cost;
   DAC 2023 measured ~1.02 dB SI-SDR. **DAC has the ablation, so weight it
   higher — but this is recent and the field has not fully absorbed it.**

### FOLK — believed, repeated, but I could not find a primary source

1. **"Brute force is fine up to ~1M vectors."** Widely repeated; I found only
   vendor and blog sources, no benchmark establishing a principled crossover as a
   function of K, dimension and query count.
2. **"FAISS IVF degrades gracefully when you add without retraining."** Sourced
   from FAISS documentation and secondary write-ups; no primary paper with
   measured drift curves found.
3. **"Colour bleeding is *just* a resolution/quality problem."** The literature
   contradicts this — it is structural to single-scalar affinity gating, and the
   SOTA fix is to take a user scribble (Kim et al. 2021), i.e. to give up on
   solving it automatically.
4. **"Our escalation ladder is RVQ."** Repeated internally; §3.1 shows it matches
   on one of four defining properties and that the closer prior art is the
   quadtree literature.

---

## 6. BORROWABLE ENGINEERING (the centrepiece)

Ordered by expected value to us.

### 6.1 Gradient weighting before filling-in — Cohen-Duwek & Spitzer (2019)

- **What it gives:** a published Poisson-filling-in model that reproduces COCE
  *and* the watercolour illusions with one parameter set, by weighting gradients
  with a multi-scale-Gabor dominance function before using them as heat sources.
- **Assumptions:** gradients as heat sources; a multi-scale filter bank to
  compute the dominance weight; steady-state solve.
- **Cost:** a Gabor bank + a Poisson solve. Both are standard.
- **Gives up:** fidelity, deliberately — that is the point. It will not
  reconstruct the veridical image, by design.
- **Reference implementation:** the paper is open-access with the model fully
  specified; **I did not find a released code repository** (see §7).
- **What must be true of our substrate:** we need a scale-selective weight on the
  residual before it becomes an order-2 code. Our escalation predicate is the
  natural home. This is the highest-value borrow in the document.

### 6.2 Bitrate efficiency as a utilization instrument — DAC (2023)

- **What it gives:** empirical entropy of the index distribution over log₂(K).
  Tends to 100% when the codebook is earning its keep.
- **Assumptions:** none beyond having indices and a test set.
- **Cost:** negligible; a histogram.
- **Gives up:** nothing. It is exact and additive.
- **Reference implementation:** described precisely in the DAC paper; the
  descript-audio-codec repo is public.
- **What must be true of our substrate:** we need to log which codebook entry
  each region selected. Almost certainly already available.
- **Note:** this is the instrument our own standing rule about dead instruments
  should like — it is computed from the index stream, *not* by the component that
  mints entries.

### 6.3 Retinex gradient threshold — Land & McCann (1971)

- **What it gives:** the binary version of 6.1. Discard sub-threshold gradients
  before integration.
- **Assumptions:** a threshold exists that separates illumination gradients from
  reflectance edges. **This assumption is exactly what Arend & Goldstein 1987
  attack** — real images do not always supply one.
- **Cost:** one parameter, one comparison.
- **Gives up:** graded response; it is a hard gate. Our own standing rule
  applies — *a hard gate is priced by the feature's error rate, not its effect
  size.* Prefer 6.1's graded weight for that reason.
- **Reference implementation:** many; McCann's are canonical.

### 6.4 ODOG as a hostile external oracle — Blakeslee & McCourt (2015)

- **What it gives:** executable Mathematica notebooks implementing a published
  brightness model from the camp that *disagrees* with our mechanism.
- **Assumptions:** oriented DoG filter bank + contrast normalization.
- **Cost:** Mathematica, or a reimplementation.
- **Gives up:** nothing — we are using it as a check, not adopting it.
- **What must be true of our substrate:** we need to emit a brightness field
  comparable to its output on the same stimulus. Straightforward.
- **Why it matters:** checking against a *hostile* oracle is the strongest
  available test and directly serves the "make the seam legible to experts" goal.

### 6.5 Efros–Leung reference implementation — IPOL (2013)

- **What it gives:** peer-reviewed, executable texture synthesis with a published
  failure analysis, for our order-3 rung.
- **Assumptions:** stationary exemplar texture. **The non-stationarity failure
  correlates with our escalation trigger** — see §2.4.
- **Cost:** exhaustive patch search; slow.
- **Gives up:** determinism is achievable (seeded) but the parameter window
  between verbatim copy and garbage is narrow and the paper says so.
- **Reference implementation:** <http://www.ipol.im/pub/art/2013/59/> with source.

### 6.6 Joint vs greedy stage fitting — Chan & Gersho

- **What it gives:** removes our one live classical failure mode.
- **Assumptions:** the total-distortion objective is what we actually want.
- **Cost:** M× search for M-L delayed decision; or a joint least-squares fit,
  which for constant+plane is cheap and closed-form.
- **Gives up:** nothing for the closed-form case. **This is exact.**
- **What must be true of our substrate:** we must be able to fit the plane
  directly rather than fitting the constant and then the residual. For
  least-squares this is a one-line change and is *strictly better*.

### 6.7 Guided filter — He, Sun & Tang (2013)

- **What it gives:** O(N) edge-aware filtering with no gradient reversal.
- **Assumptions:** a guidance image; local linear model in a window.
- **Cost:** linear time, no approximation.
- **Gives up:** **halos remain, unavoidably** (authors' own Limitations section).
- **Reference implementation:** ubiquitous (OpenCV `ximgproc::guidedFilter`).

### 6.8 Deliberately NOT borrowed

- **PatchMatch** — randomized; breaks byte-identical determinism unless seeded,
  and we have a stated preference for exact.
- **HNSW / IVF / PQ** — wrong regime entirely (§4). Actively slower at our K.
- **Quantizer dropout** — a training regularizer for a gradient-trained codec. We
  have no training. It would import a measured ~1 dB penalty for a capability we
  already have structurally.
- **EMA codebook updates** — DAC measured them *worse* than projected lookup on
  both quality and utilization, and we have no gradient to smooth anyway.

---

## 7. EXPLICIT GAPS — what I could not resolve

Held to the standard that an honest "unresolved" beats a plausible summary.

| Gap | What would resolve it |
|---|---|
| **No paper reports a sign-INVERTED Cornsweet produced by far-field plane extrapolation specifically.** Cohen-Duwek & Spitzer state the consequence (unmodified gradients reconstruct the veridical image) but do not show the ablation. | A modelling paper that ablates the gradient-weighting step and reports the resulting percept. Failing that: **run the ablation ourselves against their published model** — it is fully specified. |
| **Whether Blakeslee & McCourt's decline-with-distance result holds for COCE.** Their 2013 paper covers grating induction, simultaneous contrast and White's effect — **not COCE.** | A point-by-point brightness match across a Cornsweet field. I found no such measurement. This may be genuinely unmeasured. |
| **Whether Cohen-Duwek & Spitzer released code.** | The authors' lab page / a direct enquiry. I found the paper open-access but no repository. |
| **The exact wording of Levin et al. 2004's own limitations section.** ACM DL returned 403; I characterised the mechanism from the abstract, secondary implementations and the survey literature. | The SIGGRAPH 2004 PDF (author copies exist on Hebrew University / Technion pages). |
| **Utilization skew under CONDITIONAL-depth RVQ.** Nobody has measured it; VRVQ is the paper that should have reported it and does not. | **Our own measurement.** This is a free, publishable result. |
| **FAISS IVF degradation rate when adding without retraining.** Only documentation and secondary sources found. | FAISS wiki + the Big ANN NeurIPS'23 streaming track (arXiv:2409.17424). |
| **A principled brute-force/index crossover as a function of K, dimension, query count.** | ANN-Benchmarks (Aumüller et al., *Information Systems* 87, 2020) — but its smallest datasets are ~10⁴–10⁶ points, orders of magnitude above our regime. **The literature is silent here because the answer is obvious at our K, not because it is unknown.** |
| **Gersho & Gray chapter number for constrained VQ**; **Buzo et al. 1980 exact pagination**; **one row of the rotation-trick utilization table (64×64×3)** extracted from HTML rather than PDF. | The book; IEEE Xplore; the arXiv PDF respectively. Minor. |

---

## 8. THE FOUR THINGS TO DO NEXT

Consolidated across all sections, in priority order.

1. **Weight the gradient before escalating to it** (§1.5b, §6.1). Three
   independent camps converge on this and one has published parameters that
   reproduce COCE. A faithful order-2 code is *supposed* to destroy the illusion.
   **This is the rung the spike saved.**
2. **Run greedy-vs-joint on the constant→plane fit** (§3.3, §6.6). Cheap, exact,
   closed-form, strictly better if it differs — and it is the first objection a
   classical-VQ reviewer will raise. Note it shares a seam with (1): the
   escalation decision is where both problems live.
3. **Adopt bitrate efficiency as a utilization instrument** (§3.5, §6.2), and
   **measure utilization skew under conditional depth** (§3.6) — nobody has, and
   we are uniquely positioned to.
4. **Test the CONVERSE colour-bleed failure** (§2.7): does a strong but
   non-object contour (shadow edge, specular highlight) wrongly *stop* our fill?
   The literature says it must. If it does not, that is a far higher bar than the
   one we cleared — and our current asymmetry result should be reclassified from
   "finding" to "inherited constraint, corroborated by Kim et al. 2021 and He et
   al. 2013".

---

*End of map. Sections 1–8 complete.*

