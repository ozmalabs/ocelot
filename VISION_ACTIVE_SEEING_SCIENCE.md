# Active Seeing — Science Adjudication

> **SUPERVISOR VERIFICATION (2026-07-21).** The load-bearing citation — EISEN, the
> "objects-from-motion, transferred-to-stills is already built" finding on which the
> Claim-D reframing rests — was independently verified against the arXiv 2205.08515
> abstract: title (*"Unsupervised Segmentation in Real-World Images via Spelke Object
> Inference"*), author list (Chen, Venkatesh, Friedman, Wu, Tenenbaum, Yamins, Bear),
> and method (learns a STATIC grouping prior from MOTION self-supervision using Spelke's
> "moves together" definition, with a bootstrap that EXPLAINS AWAY already-segmented
> motion) all confirmed. **CAVEAT: the "ECCV 2022" venue tag is UNCONFIRMED** — arXiv
> lists May 2022 only; treat as arXiv-2205.08515 until the venue is checked. Claim-E/F
> citations remain training-recall per the Uncertainties section and are NOT
> supervisor-verified.

**Scope:** Read-only adjudication of the gamma-substrate vision project's arrived-at
position on *why image/video nets fail at seeing* and *what seeing is*. Each claim
(A–F) is scored SUPPORTED / OVERSTATED / REFUTED / UNDER-STUDIED against the actual
literature, with real citations. The project has already MEASURED behind each claim;
this is not a lit survey but an adjudication, biased toward finding where the claims
overreach (B, D, E are the exposed ones).

Date: 2026-07-21. Status: COMPLETE. ~22 sources; B/D/E prioritised per brief.

---

## Claim A — Seeing is ACTIVE/sensorimotor, not a function from images

**VERDICT: SUPPORTED (as a theoretical stance) / OVERSTATED in the word "REQUIRED".**

The core of Claim A — that vision is constituted by sensorimotor exploration rather
than by a function from static images — is a mainstream, well-developed position, not
a fringe one. O'Regan & Noë's *A sensorimotor account of vision and visual
consciousness* (Behavioral and Brain Sciences, 2001) is its canonical statement:
seeing *is* the exercise of mastery over sensorimotor contingencies; the world serves
as its own external memory. This lineage runs back through Gibson's ecological optics
(optic flow specifies surface layout and self-motion), and forward through Bajcsy's
*Active Perception* (Proc. IEEE, 1988) and Ballard's *Animate Vision* (Artificial
Intelligence, 1991), which argue that perception is easier and better-posed when the
observer can move. The efference-copy machinery the claim relies on (self-motion as a
POSIT that gets subtracted) is von Holst & Mittelstaedt's reafference principle (1950)
and Sperry's corollary discharge (1950) — see Claim F.

The specific empirical hook — that a *perfectly stabilised* retinal image fades and
vanishes (Troxler; Ditchburn & Ginsborg 1952; Riggs et al. 1953), and that fixational
microsaccades/drift are necessary to sustain and even sharpen vision (Rucci et al.,
Nature 2007; Martinez-Conde, Macknik & Hubel, Nat Rev Neurosci 2004) — is solid and
directly supports "static input alone does not sustain seeing."

**Where it OVERSTATES:** "self-motion is REQUIRED to bootstrap objecthood" is stronger
than the evidence licenses. The developmental literature (Claim B) supports motion as
the *earliest and privileged* cue, but object motion (not necessarily the *observer's*
self-motion) does much of that work in infants, and mature observers demonstrably parse
still photographs. The defensible narrower claim: **relative motion (self-motion OR
object motion) is the developmentally primary and best-posed cue for carving an unknown
scene; static carving is a later, prior-dependent competence.** The distinction between
*self*-motion (with efference copy) and *object* motion matters and the project should
keep it sharp — infants exploit both, and the pure "you must move yourself" reading is
narrower than the infant data.

**Citations:** O'Regan & Noë 2001 (BBS); Gibson 1979 (*The Ecological Approach to
Visual Perception*); Bajcsy 1988 (Proc IEEE); Ballard 1991 (Artif. Intell.); Rucci et
al. 2007 (Nature); Martinez-Conde et al. 2004 (Nat Rev Neurosci). [Rucci/Martinez-Conde
recalled from training + search corroboration; abstracts not individually fetched —
flagged.]

---
## Claim D — Nets fail fundamentally; self-supervised video is the nearest miss

**VERDICT: OVERSTATED. The field is substantially further along "objecthood from
motion" than the claim credits. The honest residual is real but narrow.**

This is where the project is most exposed to "you re-derived what's already built."
There is a mature, named lineage that does almost exactly "carve objects from motion,
self-supervised, then transfer the grouping to static frames":

- **EISEN / "Spelke Object Inference"** (Chen, Venkatesh, Friedman, Wu, Tenenbaum,
  Yamins, Bear — ECCV 2022, arXiv 2205.08515). This is the most direct prior art. It
  operationalises Spelke's cognitive-science definition ("an object is stuff that moves
  together") as a *learning signal*: motion self-supervision teaches a static grouping
  prior, and a bootstrapping process "explains away" the motion of already-segmented
  objects (their word for what the project calls efference-copy-style subtraction of
  known motion). It then segments *still* images at SOTA. A 2025 follow-up
  ("Discovering and using Spelke segments", arXiv 2507.16038) extends this. **This is
  "objecthood from motion, then transferred to stills" — already built, cited, and
  benchmarked.** The project's Claim A/B developmental story is the explicit design
  rationale of this line, not a gap in it.
- **SAVi / SAVi++** (Kipf et al. ICLR 2022; Elsayed et al. NeurIPS 2022): Slot Attention
  for video using *optical flow prediction* (and later sparse LiDAR depth) as the
  self-supervised objective to decompose real driving scenes into object slots without
  mask labels. Object-centric learning (Slot Attention, Locatello et al. NeurIPS 2020;
  SIMONe; object-centric world models) is a whole subfield whose premise is exactly
  "objecthood should EMERGE, not be labelled."
- **Egomotion-tied representation learning**: Agrawal, Carreira & Malik, *Learning to
  See by Moving* (ICCV 2015); Jayaraman & Grauman, *Learning image representations tied
  to egomotion* (ICCV 2015 / IJCV 2017). These use the agent's OWN motor/egomotion
  signal as the supervisory regularizer — i.e. representations tied to self-motion, with
  proprioceptive motor signals, which is close to the project's "efference copy" hook.
- **Structure/depth from self-motion**: SfMLearner (Zhou et al. CVPR 2017), Monodepth2
  (Godard et al. ICCV 2019) — self-supervised monocular depth + egomotion jointly from
  video, no labels.

**So the claim "nets fail fundamentally at objecthood-from-motion" is false as stated.**
Nets have carved objects from motion self-supervision and transferred to stills.

**The honest, narrower residual** (what these systems genuinely do NOT do, and where the
project's specific version could still be novel):
1. **They optimize a proxy (flow/feature/pixel prediction or affinity), not carving
   directly with a representable refusal.** Objecthood is read out of a representation
   trained for prediction; there is no operation that says "this span matches nothing I
   hold — keep it as residual." The project's "collapse, keep the residual" as an
   explicit MDL operation is a different mechanism, not just a different training loss.
2. **They are mostly PASSIVE (V-JEPA, SAVi, object-centric video) — fed clips, no motor
   loop, no efference-copy SUBTRACTION.** V-JEPA (Meta, 2024) is the nearest miss: it
   learns from passively watched video by latent prediction, and its acknowledged
   limitation is precisely the lack of action-conditioned prediction (no motor, no
   corollary discharge). EISEN and the egomotion papers DO use motion/egomotion, so the
   "no self-motion at all" reading is wrong — but explicit *efference-copy subtraction as
   an architectural operation* (vs. motion-as-a-loss-target) is not standard.
3. **The refusal / open-endedness is not first-class** — see Claim E.

**Net verdict:** "nets fail fundamentally" → REFUTED as a blanket claim; the specific
combination the project should claim is not "objects from motion" (done) but the
*mechanism*: explicit efference-copy subtraction + a representable MDL refusal +
graph-native assignment, rather than a prediction proxy read out for slots.

**Citations:** Chen et al. 2022 (EISEN, ECCV, arXiv 2205.08515); "Discovering and using
Spelke segments" 2025 (arXiv 2507.16038); Kipf et al. 2022 (SAVi, ICLR); Elsayed et al.
2022 (SAVi++, NeurIPS, arXiv 2206.07764); Locatello et al. 2020 (Slot Attention,
NeurIPS); Agrawal, Carreira & Malik 2015 (ICCV, arXiv 1505.01596); Jayaraman & Grauman
2015/2017 (ICCV/IJCV, arXiv 1505.02206); Zhou et al. 2017 (SfMLearner, CVPR); Godard et
al. 2019 (Monodepth2, ICCV); V-JEPA / Meta 2024 (blog + code; limitation from secondary
sources — flagged).

---

## Claim E — "A comparison can be false, a selection cannot," so a net STRUCTURALLY
## cannot refuse

**VERDICT: OVERSTATED as stated; the NARROWER version is DEFENSIBLE and worth keeping.**

The strong claim — that a net can *only* return the least-bad label and confidently-wrong
is architectural — is false as an absolute, because abstention is a large, mature
subfield:

- **Selective classification / reject option**: Chow (1970) formalised the optimal
  reject rule; Geifman & El-Yaniv (*Selective classification for deep neural networks*,
  NeurIPS 2017) gave a risk–coverage framework thresholding the softmax response with
  guarantees; SelectiveNet (Geifman & El-Yaniv, ICML 2019) trains the abstention jointly.
- **Calibration / overconfidence**: Guo et al. (*On calibration of modern neural
  networks*, ICML 2017) — modern nets ARE miscalibrated/overconfident, which is evidence
  FOR the project's intuition, but the response has been to fix it, not to declare it
  impossible.
- **Open-set recognition** (Scheirer et al. 2013; Bendale & Boult OpenMax CVPR 2016),
  **OOD detection** (Hendrycks & Gimpel 2017), **conformal prediction** (Vovk;
  Angelopoulos & Bates), **evidential deep learning** (Sensoy et al. NeurIPS 2018),
  **energy-based OOD** (Liu et al. NeurIPS 2020). You *can* bolt "none of the above" onto
  a net.

So "a net structurally cannot refuse" is REFUTED at face value.

**BUT the narrower claim survives and is the one to keep:** a threshold on a
*selection's* score (max-softmax, a logit margin, an added "reject" logit) is a *post-hoc*
reject over the SAME discriminative comparison among known classes — it does not
constitute *intrinsic* refusal by *comparison against a held model of the input*. The
architecturally-principled refusers are exactly the **reconstruction / generative /
energy-based** ones: an energy-based model or a generative/reconstruction model CAN say
"this input matches nothing I hold" because its score is a *comparison of the input
against a model*, not a *selection among labels*. Discriminative softmax classifiers are
known to assign arbitrarily high confidence to far-OOD and adversarial inputs (Nguyen et
al. 2015 "fooling"; Hendrycks & Gimpel 2017; Guo et al. 2017), which is precisely the
"forced to pick where it should decline" failure. The project's "refusal via
comparison-against-a-reconstruction" is on the RIGHT side of this line — it is what the
generative/energy-based refusers do — but the field already frames this distinction
(discriminative vs. generative confidence; density-based vs. classifier-based OOD).

**Defensible statement of Claim E:** *A thresholded selection is a post-hoc reject over
the known-class comparison and remains vulnerable to confident far-OOD/adversarial
errors; intrinsic refusal requires scoring the input against a held model
(reconstruction/energy/density), which is a comparison that CAN be false. The project's
refusal-as-residual is the latter kind — but "a net cannot refuse" overstates it; "a
DISCRIMINATIVE SELECTION cannot intrinsically refuse" is the true and non-trivial claim,
and it is already partially in the literature.*

**Citations:** Chow 1970 (IEEE Trans IT); Geifman & El-Yaniv 2017 (NeurIPS), 2019
(SelectiveNet, ICML); Guo et al. 2017 (ICML); Nguyen, Yosinski & Clune 2015 (CVPR,
"fooling"); Hendrycks & Gimpel 2017 (ICLR, MSP baseline); Bendale & Boult 2016 (OpenMax,
CVPR); Sensoy et al. 2018 (evidential, NeurIPS); Liu et al. 2020 (energy OOD, NeurIPS).
[Several recalled from training + partial search corroboration — venues flagged where not
individually fetched.]

---

## Claim F — We don't perceive the eye's own shift; self-motion is the posit that gets
## subtracted (reafference)

**VERDICT: SUPPORTED as the standard account, with a real, named caveat.**

The reafference / efference-copy / corollary-discharge account of perceptual stability is
the textbook explanation: von Holst & Mittelstaedt's *Reafferenzprinzip* (1950) and
Sperry's corollary discharge (1950) posit that a copy of the motor command cancels the
self-generated sensory consequence, so only the *residual* (exafference — world-caused
change) reaches perception. This directly matches the project's "self-motion is the posit
and gets subtracted; only the residual reaches perception." Saccadic suppression (reduced
sensitivity around saccade onset) and predictive receptive-field remapping triggered by
an efference-copy signal are well-documented instantiations. The self-tickle result —
Blakemore, Wolpert & Frith, *Central cancellation of self-produced tickle sensation*
(Nat Neurosci 1998), and "Why can't you tickle yourself?" (NeuroReport 2000) — is the
canonical demonstration that self-generated sensation is attenuated by a forward-model
prediction; this is now framed as predictive-coding cancellation of self-generated
signals.

**The caveat (dissent to flag):** pure *cancellation* theories of space constancy are
known to be insufficient on their own — the extraretinal signal is not an exact copy of
the actual eye movement, so cancellation cannot fully account for constancy, and
post-saccadic retinal information contributes (e.g. Deubel et al.; the "immediate
post-saccadic information mediates space constancy" line). Saccadic suppression itself has
multiple contributors (efference-copy processing AND backward masking / luminance
mechanisms). So the mechanism is real and mainstream, but "self-motion is subtracted and
only the residual reaches perception" is a clean idealisation of a process that in
biology is approximate and supplemented by post-hoc retinal correction. For the project's
purposes (a design principle: collapse the predicted self-motion, keep the residual) the
account is SUPPORTED; just don't claim the biological cancellation is exact.

**Citations:** von Holst & Mittelstaedt 1950 (reafference principle); Sperry 1950 (J Comp
Physiol Psychol, corollary discharge); Blakemore, Wolpert & Frith 1998 (Nat Neurosci),
2000 (NeuroReport, "Why can't you tickle yourself?"); Bridgeman et al. / Deubel et al. on
post-saccadic space constancy (dissent — recalled + search corroboration, not
individually fetched). [Blakemore/Sperry/von Holst recalled from training + search
corroboration — flagged.]

---
## Claim B — A single static frame cannot be segmented into objects by any per-frame
## relation

**VERDICT: OVERSTATED as universally stated; SUPPORTED in the narrow, correct reading
the project actually measured. This is the most important claim to sharpen.**

The claim has two readings, and only one is defensible:

**(i) The strong reading — "no system can carve a still into objects" — is REFUTED.** A
mature system with learned priors segments single images routinely. Segment Anything
(Kirillov et al., ICCV 2023) segments arbitrary stills; DINO self-supervised ViTs (Caron
et al., ICCV 2021) produce object-segmenting attention maps on stills with NO
mask/box/label supervision; border-ownership neurons in V2 (Zhou, Friedman & von der
Heydt, J Neurosci 2000) assign figure-ground on static images; classical Gestalt
figure-ground works on static displays. Humans obviously parse photographs. So "a static
frame genuinely cannot be segmented into objects" is false without qualification.

**(ii) The narrow reading — which is what the project MEASURED — is SUPPORTED.** The
seven mechanisms the project tested (value-flood, competitive border ownership, aperture,
enclosure, phase-congruency/wave, MDL contour closure) are HAND-AUTHORED, PRIOR-FREE,
per-frame *geometric relations* — not learned deep priors. The finding that these do not
make the ground *finite* on a natural frame (closure works on a synthetic gapped circle
but not a natural scene) is consistent with the vision-science consensus: **figure-ground
and border-ownership assignment is UNDERDETERMINED by local image relations and requires
priors/context** (border-ownership depends on information far outside the classical
receptive field; V2 combines it with stereo/motion/Gestalt cues — Zhou et al. 2000;
Grossberg's FACADE work). So a prior-free per-frame geometric relation being insufficient
is exactly what the field would predict.

**The load-bearing question — where does the prior come from?** The project's claim is
that the priors that make static segmentation possible are THEMSELVES learned from
motion. The developmental evidence supports this as the *earliest* route but does not
prove it is the *only* one:
- Kellman & Spelke (Cognitive Psychology, 1983): 4-month-olds perceive a partly-occluded
  object as one connected thing when its visible parts undergo COMMON MOTION, and NOT
  when the parts are stationary with aligned edges, homogeneous colour, simple shape.
  I.e. common motion is the earliest and privileged infant object cue; static Gestalt
  form is a *later*-developing competence. Spelke (Cognitive Science, 1990) formalises
  this as principles-of-object-perception (cohesion, boundedness) grounded in motion.
- The EISEN/Spelke-object CV line (Chen et al. 2022; see Claim D) is a working existence
  proof that a STATIC grouping prior can be LEARNED FROM MOTION self-supervision and then
  applied to stills — i.e. exactly "static segmentation, but the priors are learned from
  motion."

**Honest verdict:** the project's blanket phrasing ("a single static frame genuinely
cannot be segmented into objects by any per-frame relation") OVERSTATES; the defensible
and evidence-backed claim is: **prior-free, hand-authored per-frame geometric relations
cannot carve an unknown natural scene into finite objects (measured, and consistent with
figure-ground being underdetermined without priors); static carving requires priors, and
those priors are developmentally motion-first (Kellman & Spelke) and have been
successfully learned-from-motion in ML (EISEN).** Do not claim static segmentation is
*impossible* — claim it is *not prior-free*, and that the prior's origin is motion.

**Citations:** Kellman & Spelke 1983 (Cognitive Psychology 15:483–524); Spelke 1990
(Cognitive Science 14:29–56); Zhou, Friedman & von der Heydt 2000 (J Neurosci 20:6594);
Kirillov et al. 2023 (Segment Anything, ICCV); Caron et al. 2021 (DINO, ICCV, arXiv
2104.14294); Chen et al. 2022 (EISEN, ECCV).

---

## Claim C — Seeing is PRIOR to naming

**VERDICT: SUPPORTED.**

That carving/segmentation is upstream of and separable from naming/recognition, and that
grounding a symbol requires a non-symbolic percept it can attach to, is well-supported:

- **Symbol grounding** (Harnad, *The Symbol Grounding Problem*, Physica D 1990): symbols
  are meaningless unless grounded in non-symbolic sensorimotor categories; a name for an
  object presupposes the capacity to pick that object out. This directly backs "a name
  attaches only to a percept you can already carve." Modern framings note LLMs
  *circumvent* rather than solve grounding by parasitizing already-grounded human text.
- **Moravec's paradox** (Moravec 1988; Brooks): high-level reasoning/naming is cheap for
  machines, low-level perception/sensorimotor grouping is hard — consistent with carving
  being the hard, prior, foundational competence and naming the easy downstream one.
- **Segmentation upstream of recognition**: the project's distinction between
  *recognition-of-a-known-shape* (codebook match, works on stills) and
  *carving-the-unknown* (does not) maps onto the vision-science and CV separation of
  segmentation/grouping from classification, and onto the developmental fact that infants
  parse objects (Kellman & Spelke) long before they name them.

The one caveat: segmentation and recognition are *interactive*, not strictly serial, in
mature vision (recognition feedback aids figure-ground — e.g. familiar-configuration
effects). So "prior to" is right developmentally and architecturally, but in the mature
system there is top-down coupling. The project's claim (naming needs a carvable percept;
carving-the-unknown is the hard prior step) survives that caveat.

**Citations:** Harnad 1990 (Physica D 42:335–346); Moravec 1988 (*Mind Children*); Kellman
& Spelke 1983. [Moravec's paradox recalled from training — flagged.]

---

## "Where the field already is" — object-discovery-from-motion map (for Claim D)

Ordered roughly by how close each is to "objecthood from self-motion":

1. **EISEN / Spelke-object inference** (Chen et al., ECCV 2022; follow-up 2025) —
   CLOSEST. Learns static grouping priors from motion self-supervision using the literal
   Spelke "moves-together" definition; bootstraps by explaining away known motion;
   segments stills at SOTA. If the project's headline were "objecthood from motion,
   transferred to stills," this IS that, published.
2. **SAVi / SAVi++** (Kipf et al. ICLR 2022; Elsayed et al. NeurIPS 2022) — object slots
   from optical-flow / depth self-supervision on real video, no masks.
3. **Egomotion-tied representations** (Agrawal-Carreira-Malik ICCV 2015;
   Jayaraman-Grauman ICCV 2015 / IJCV 2017) — representations supervised by the agent's
   OWN motion signal; closest to "efference copy as supervisor."
4. **Object-centric learning** generally (Slot Attention, Locatello NeurIPS 2020;
   SIMONe; object-centric world models) — objecthood as an emergent latent, not a label.
5. **Self-supervised depth+egomotion** (SfMLearner CVPR 2017; Monodepth2 ICCV 2019) —
   world structure from self-motion, no labels; NeRF/3DGS for static multi-view.
6. **V-JEPA** (Meta 2024) — nearest miss on the "prediction not carving, passive not
   active" axis: latent video prediction, passively watched, no motor/efference-copy,
   objecthood a hoped-for byproduct. The project's critique of V-JEPA is fair; its
   critique of the WHOLE field is not.

**Consequence: do not re-derive "objects from motion." It exists.** Position the project
against the *mechanism* differences, not the phenomenon.

---

## The honest novelty reframing

After the literature, sorting the project's candidate novelties into
ALREADY-COVERED vs. GENUINELY-OPEN:

**Already substantially covered (do not claim as novel):**
- "Objecthood emerges from motion / self-motion, transferred to stills" — EISEN, SAVi,
  egomotion-representation line. Covered.
- "Motion is the developmentally primary object cue" — Kellman & Spelke, 40 years old.
- "Seeing is active/sensorimotor" — O'Regan & Noë, Bajcsy, Ballard, Gibson. Covered.
- "Discriminative softmax is overconfident / needs abstention" — Guo et al., the whole
  selective-prediction/OOD field. Covered.
- "Self-motion is cancelled by efference copy; residual = world" — reafference principle,
  1950. Covered as biology.

**Genuinely open / where THIS project's specific version could be novel (candidates to
test, ranked):**
1. **A REPRESENTABLE, intrinsic refusal via comparison-against-a-held-model, made
   first-class in the architecture** — not a thresholded selection bolted on post-hoc,
   and not merely an energy score, but a graph-resident "this span matches nothing I
   hold → keep as residual" operation that the system can carry, name, and act on. The
   *distinction* (generative/energy refusers vs discriminative selectors) is in the
   literature; a refusal that is a NAMED GRAPH OBJECT the agent reasons over is not
   standard. **Most promising residual.**
2. **Explicit efference-copy SUBTRACTION as an architectural "collapse-and-keep-residual"
   operation**, vs. motion-as-a-loss-target. EISEN "explains away known motion" is the
   nearest prior; whether making the subtraction an explicit, inspectable graph operation
   (rather than an implicit training dynamic) buys anything measurable is OPEN and
   testable.
3. **The graph-native (G,Γ) formulation with a REFUSAL/RESIDUAL that is inspectable and
   composable** — the object-centric-learning field represents objects as opaque slot
   vectors; a typed-graph, MDL-gated carving whose residual and refusals are first-class
   symbolic objects is a genuinely different representational commitment. Novelty is in
   *inspectability/composability of the carving*, not in "objects from motion."
4. **The frame/continuum invariant (in-frame integer, continuous only cross-frame)** — I
   found NO direct literature analogue in this search; it reads as a project-specific
   design axiom. UNDER-STUDIED / possibly novel, but also possibly just a re-encoding of
   quantization + continuous embedding; needs its own adjudication (out of scope here).
5. **MDL contour closure as the static-carving mechanism** — MDL/description-length
   approaches to grouping and contour completion EXIST (Occam-grouping, minimum-
   description-length segmentation); the project's own measurement already shows it does
   NOT solve natural-scene carving prior-free, so this is not the novel win — it is a
   measured negative, correctly.

**The single sharpest genuinely-novel residual to pursue:** a *representable, intrinsic
refusal* — the carving operation returns "matches nothing I hold, kept as residual" as a
first-class graph object the agent can reason about, promote, and ground — combined with
*explicit efference-copy subtraction* as the mechanism that produces the residual. The
phenomenon (objects from motion) is taken; the *inspectable refusal + explicit
subtraction as named graph operations* is the defensible frontier.

---

## Flagged uncertainties

- **Recalled-not-fetched citations** (asserted from training with only search-snippet
  corroboration, NOT individually fetched — verify before publishing): Rucci et al. 2007
  (Nature); Martinez-Conde et al. 2004 (Nat Rev Neurosci); Sperry 1950; von Holst &
  Mittelstaedt 1950; Blakemore/Wolpert/Frith 1998 & 2000; Moravec 1988; Chow 1970;
  several Claim-E venues (Bendale & Boult, Sensoy, Liu, Nguyen). Author/venue are from
  memory + snippets; page numbers where given for Kellman-Spelke/Spelke/Harnad are from
  training and should be checked.
- **V-JEPA's exact acknowledged limitations** came from secondary summaries (turingpost,
  Meta blog snippet), not the primary paper; the "no action-conditioned prediction"
  limitation is well-attested but the framing is secondary-sourced.
- **Contested finding (Claim F):** pure cancellation theories of space constancy are
  disputed — extraretinal signals are inexact and post-saccadic retinal information
  contributes (Deubel, Bridgeman lineage). The reafference *principle* is mainstream; its
  *exactness* is not. Flagged as a real scientific dispute, not a settled point.
- **Claim B's crux is partly inferential:** that ALL static-segmentation priors
  ultimately trace to motion is SUPPORTED developmentally (Kellman-Spelke) and by one ML
  existence proof (EISEN), but is not PROVEN as the only possible origin — DINO learns
  segmenting priors from a static image corpus (though that corpus's statistics arguably
  encode motion/co-occurrence indirectly). Treat "priors are motion-derived" as
  well-supported-but-not-exclusive.
- **Frame/continuum invariant (Claim-adjacent):** no literature analogue found in this
  search; could not confirm novelty or prior art. Genuinely unadjudicated here.
- Not searched exhaustively: I prioritised B/D/E per the brief; the abstention and
  object-centric subfields are large and this is ~20 sources, not a full survey.

