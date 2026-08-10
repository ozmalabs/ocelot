# Gaussian Splatting as a Model of Biological Perception — Science Adjudication

> **SUPERVISOR VERIFICATION (2026-07-21).** The load-bearing NEW claim — Claim E, that
> 3DGS-as-brain-model is UNCLAIMED and the only related work runs the OTHER direction — was
> spot-verified: *Perceptual-GS* (Zhou et al., arXiv 2506.12400, ICML 2025 / PMLR v267,
> "Scene-adaptive Perceptual Densification for Gaussian Splatting") is confirmed REAL and is
> exactly the reverse direction — it folds human visual sensitivity INTO splatting's
> densification, not "the brain does splatting." The E negative is a HONEST SEARCH-LEVEL
> ABSENCE (three query formulations), explicitly NOT a proof of nonexistence — treat as "not
> found," never "does not exist." The refutation-grade claims (B fixed cortical
> magnification, C change-blindness) rest on well-established literature. Citations flagged
> in-text as fetched-corroborated vs training-recalled are NOT supervisor-verified beyond
> that flag (place/grid-cell, Rao-Ballard, Friston, Lee-Mumford are training-recall — check
> before external use).

**Scope:** Read-only adjudication of the gamma-substrate vision project's arrived-at
position on the question *"Does the brain use a version of 3D Gaussian Splatting?"* Each
claim (A–F) is scored SUPPORTED / OVERSTATED / REFUTED / UNDER-STUDIED against the actual
literature, with real citations. This is an adjudication, not a survey — biased toward
finding where the claims overreach. The exposed claims (B, C, E) are prioritised. Matches
the standard of the companion file `VISION_ACTIVE_SEEING_SCIENCE.md`, which refuted two of
the project's own claims.

Background held accurately: **3D Gaussian Splatting** (Kerbl, Kopanas, Leimkühler,
Drettakis, *3D Gaussian Splatting for Real-Time Radiance Field Rendering*, ACM TOG /
SIGGRAPH 2023) represents a scene as an explicit set of 3D anisotropic Gaussians (mean,
covariance/orientation, opacity, view-dependent colour via spherical harmonics), rendered
by projecting each Gaussian to a 2D footprint ("splat") and alpha-compositing front-to-back.
It is FIT by stochastic gradient descent over a collection of posed multi-view images
(camera poses obtained from Structure-from-Motion, typically COLMAP), minimising a
photometric reconstruction loss (L1 + D-SSIM), with **adaptive density control**: clone/split
Gaussians where the view-space positional gradient is large (under-reconstructed regions),
and prune near-transparent or oversized ones.

Date: 2026-07-21. Status: COMPLETE. ~20 sources; B/C/E prioritised per brief.

---

## Claim A — Early-vision PRIMITIVES already ARE anisotropic Gaussians

**VERDICT: SUPPORTED as the standard descriptive model / OVERSTATED in the word "ARE".**

The factual core is solid and mainstream. Retinal ganglion and LGN receptive fields are
well modelled by a **Difference-of-Gaussians** (center-surround), the Rodieck & Stone /
Rodieck (1965) model. V1 simple-cell receptive fields are well described by **Gabor
functions** — a Gaussian envelope times a sinusoid, i.e. an oriented, elongated,
anisotropic Gaussian-windowed grating (Daugman 1985, *JOSA A*; Jones & Palmer 1987, *J
Neurophysiol*, who fit 2D Gabors to macaque simple cells and found them a good
description). And critically, this is not just a curve fit imposed by modellers:
Olshausen & Field (1996, *Nature*) showed that **sparse coding of natural images
spontaneously produces localized, oriented, bandpass (Gabor-like) basis functions** — the
statistics of natural images plus a sparsity/efficiency objective *generate* the
primitive. So "the visual field is encoded as a set of oriented Gaussian(-windowed)
primitives" is genuinely close to the standard model of early vision, and the anisotropy
(orientation + elongation) that 3DGS's covariance ellipsoids carry has a real biological
analogue.

**Where it OVERSTATES ("ARE"):** a Gabor is a *descriptive fit*, not a mechanism, and the
fit's limits are well known and load-bearing here:
- **Non-classical receptive fields / contextual modulation.** V1 responses depend
  strongly on stimulus far outside the classical RF (surround suppression, contour
  facilitation) — a fixed Gabor cannot capture this (Cavanaugh, Bair & Movshon 2002;
  and the broad non-classical-RF literature).
- **Nonlinearity.** Simple cells are not linear Gabor filters plus a static
  nonlinearity; contrast normalization (Heeger 1992; Carandini & Heeger 2012, *Nat Rev
  Neurosci*, "Normalization as a canonical neural computation") is essential, and complex
  cells are phase-invariant (energy model, not a single Gabor).
- **Diversity of shapes.** Recent sparse-coding work (sparse-set coding) recovers
  *small unoriented* features and pure edge-detectors alongside Gabor wavelets — the
  population is not a clean bank of identical anisotropic Gaussians.

A 3DGS Gaussian carries a **mean + covariance + opacity + view-dependent colour** and is
composited to *reconstruct radiance*. A V1 Gabor is an oriented bandpass **filter** whose
output is a rectified, normalized firing rate — it is not a radiance primitive that
alpha-composites, and colour is handled by a separate, largely decorrelated channel (see
Claim F and the project's own "luminance is structure, colour is a sign"). So the honest
statement is: **early vision's primitives are anisotropic-Gaussian-*shaped* filters — a
genuine and non-trivial match to the geometry of a splat's footprint — but they are
FILTERS (analysis kernels), not radiance-reconstructing splats (synthesis primitives),
and the standard model of what they do (normalized energy, contextual modulation) is more
than a Gaussian.**

**Citations:** Rodieck 1965 (*Vision Research*, DoG model of cat RGC); Daugman 1985 (*JOSA
A*, 2D Gabor); Jones & Palmer 1987 (*J Neurophysiol* 58:1233, Gabor fits to macaque V1);
Olshausen & Field 1996 (*Nature* 381:607, sparse coding → Gabor-like bases); Carandini &
Heeger 2012 (*Nat Rev Neurosci* 13:51, normalization). [Rodieck, Daugman, Jones-Palmer,
Carandini-Heeger recalled from training + search-snippet corroboration; Olshausen-Field
and Jones-Palmer directly corroborated by fetched snippets. Venue/year should be
re-checked before publishing.]

---

## Claim B — Adaptive primitive DENSITY = foveation / cortical magnification = splatting's residual-driven density control

**VERDICT: OVERSTATED — this is the sharpest overreach in the set. The biology and the
algorithm do different things under a superficially similar description.**

Two distinct things are being equated, and they should not be:

**(i) Cortical magnification is a FIXED anatomical gradient, not per-scene densification.**
The retinotopic map is well described by a **logarithmic conformal map** that devotes a
hugely disproportionate share of cortex to the fovea — cortical sampling of foveal cones
is up to ~160× that of peripheral cones, and roughly 40% of V1 serves the central few
degrees. This gradient is **hardwired and scene-invariant**: it is fixed by retinal cone
density and the retino-cortical projection, established developmentally, and does **not**
change because a particular scene has high reconstruction error in a particular place. The
number and placement of the "primitives" (receptors, cortical sampling units) is a
structural constant of the organism.

**(ii) 3DGS adaptive density control GROWS primitives per-scene where residual is high.**
Splatting's densification clones/splits Gaussians specifically in regions where the
photometric reconstruction gradient is large — i.e. **the representation's resolution is
allocated by the current scene's error signal**, and it is different for every scene fit.
This is a data-driven, per-scene, error-following reallocation. Nothing anatomical in the
retino-cortical gradient does this.

**What the brain DOES do dynamically is point the fixed high-resolution patch — active
sampling, not primitive growth.** The dynamic, error-following component of biological
vision is **where you aim the fovea** (saccades to informative/high-uncertainty regions —
active perception, Bajcsy 1988; Yarbus's task-dependent scanpaths) and **fine oculomotor
adjustment of fixational drift** toward higher-cone-density retinal zones, which yields
sub-cone-diameter "super-resolution" (recent foveola work, e.g. the *sub-cone visual
resolution by active adaptive sampling* line, ~2024). That is adaptive *sampling of a
fixed sensor array*, not *growing new primitives where reconstruction error is high*. The
resource being reallocated is **gaze/attention over a fixed gradient**, not the *count and
placement of the primitives themselves*.

**The narrower defensible version:** *The brain has a FIXED foveal resolution gradient
(cortical magnification) plus ACTIVE GAZE CONTROL that points that gradient at
task-relevant / high-uncertainty regions. This resembles splatting's densification only at
the level of "spend representational resolution where it matters," but the mechanism is
different: biology moves a fixed-resolution aperture (active sampling); splatting grows and
prunes the primitive set per scene (adaptive densification). Equating "foveation" with
"residual-driven density control" conflates a scene-invariant anatomical gradient +
attention with a per-scene error-driven reallocation of primitives.* One interesting hedge
worth noting honestly: there IS experience-dependent, error-driven allocation of cortical
territory over *developmental/plastic* timescales (cortical remapping after deprivation),
and simulated cortical magnification has been shown to help self-supervised object learning
(2025 arXiv work) — but that is slow developmental plasticity, not the per-*scene*,
per-fit densification that 3DGS performs and that the claim equates it to.

**Citations:** Bajcsy 1988 (*Proc IEEE*, active perception); logarithmic conformal
retino-cortical map + ~160× / ~40%-of-V1 figures (multiple sources; e.g.
Schwartz 1980 log-conformal model; corroborated by fetched cortical-magnification
snippets — primary papers not individually fetched, flagged); *Simulated Cortical
Magnification Supports Self-Supervised Object Learning* (2025, arXiv 2509.15751); active
fixational-drift super-resolution in the foveola (~2024, PMC11521370). [Cone-density and
V1-percentage figures are from fetched search snippets, not primary papers — flagged.]

---

## Claim C — 3D primitive representation from MULTIPLE VIEWS with KNOWN POSES (efference copy), held as a persistent internal model

**VERDICT: The pose-source half is SUPPORTED; the persistent-dense-internal-model half is
REFUTED by the change-blindness / grand-illusion literature. Narrow to "transient,
gaze-centred, task-relevant."**

Split the claim into its two parts, because they get opposite verdicts.

**(i) "Poses come free from efference copy" — SUPPORTED (and a genuine advantage over
3DGS).** 3DGS requires camera poses from Structure-from-Motion; the brain has a native
extraretinal pose signal — the **efference copy / corollary discharge** of eye and body
movements (von Holst & Mittelstaedt 1950; Sperry 1950), which the visual system uses to
interpret retinal change in a self-motion-referenced frame (adjudicated in the companion
file, Claim F). So "the brain has the poses natively, without SfM" is a fair and real
disanalogy in the brain's favour. (Caveat carried from the companion file: the extraretinal
signal is *approximate*, not an exact camera pose, and post-saccadic retinal information
supplements it — so it is a noisy pose prior, not COLMAP-grade extrinsics.)

**(ii) "The brain holds a persistent, dense, stable internal 3D model (a stored splat
cloud)" — REFUTED.** This is the most exposed sub-claim, and the change-blindness /
"grand illusion" literature argues directly against it. Large scene changes go unnoticed
across saccades, flicker, "mudsplashes", and film cuts (Rensink, O'Regan & Clark 1997,
*Psychol Sci*, "To see or not to see"; Simons & Levin 1997/1998, *TiCS* and the
door-study; O'Regan 1992, *Can J Psychol*, "the world as an outside memory"). The standard
interpretation is that **the internal representation is sparse and largely limited to what
is currently attended** — the richly-detailed stable world we *feel* we have is not backed
by a dense stored model; the world serves as **its own external memory**, re-queried by
gaze on demand (O'Regan & Noë 2001; Noë, *Is the visual world a grand illusion?* 2002).
This is precisely the project's own committed position ("the world as outside memory",
"transient gaze-centred model", the memory note *confabulation is the default*). A **stored,
dense, persistent splat cloud is the reconstructionist picture the grand-illusion argument
was written to reject.** (Honest counter-tension to flag, not to overclaim: change
blindness shows *change is not compared*, not that *nothing* is stored — there is evidence
for large-capacity but volatile/overwritten object representations, e.g. Hollingworth &
Henderson on scene memory; and V4/IT hold objects across saccades transiently. So the true
statement is "no persistent *dense photometric* internal model", not "no internal
representation at all".)

**(iii) Level-mismatch flag: biological spatial representation is largely ALLOCENTRIC, not
a primitive cloud.** The brain's *durable* spatial representation is the hippocampal-
entorhinal **place-cell / grid-cell** system (O'Keefe & Dostrovsky 1971; Hafting et al.
2005, *Nature*; Moser, Kropff & Moser 2008) — an allocentric cognitive map, a fundamentally
different representational kind from a viewer-referenced set of radiance Gaussians. What is
persistent in biology is a *sparse, abstract, allocentric map* (and object files /
gist), not a dense egocentric splat cloud. So the persistent-representation analogy fails
twice: what persists is neither dense nor photometric nor egocentric-splat-shaped.

**Narrowed claim that survives:** *The brain reconstructs a TRANSIENT, gaze-centred,
task-relevant, sparse scene estimate using natively-available (but approximate)
self-motion poses from efference copy — NOT a persistent dense internal splat cloud. Where
representation genuinely persists, it is a sparse allocentric map (place/grid cells) or
abstract object/gist memory, not a stored primitive cloud.* The efference-copy-as-pose
insight is the keeper; the persistent-splat-cloud reading is refuted by the project's own
adopted literature.

**Citations:** O'Regan 1992 (*Can J Psychol* 46:461, "world as outside memory"); Rensink,
O'Regan & Clark 1997 (*Psychol Sci* 8:368); Simons & Levin 1997 (*TiCS* 1:261) & 1998
(*Psychon Bull Rev*, door study); O'Regan & Noë 2001 (*BBS* 24:939); Noë 2002 (*J
Consciousness Studies*, grand illusion); von Holst & Mittelstaedt 1950; Sperry 1950;
O'Keefe & Dostrovsky 1971 (*Brain Res*); Hafting, Fyhn, Molden, Moser & Moser 2005
(*Nature* 436:801, grid cells). [Rensink/Simons-Levin/O'Regan corroborated by fetched
snippets; place/grid-cell citations recalled from training — flagged.]

---

## Claim D — Vision is ANALYSIS-BY-SYNTHESIS / inverse graphics; splatting is a 3D AbS loop (render → compare → grow where residual is high)

**VERDICT: SUPPORTED-BUT-CONTESTED. The AbS/inverse-graphics programme is real and active;
feedforward-sufficiency accounts are the standing dissent. The specific "iterative
render-compare-densify loop" is more contested than the general programme.**

**The programme is real and well-cited.** "Vision as Bayesian inference / analysis-by-
synthesis / inverse graphics" is a major research line:
- **Yuille & Kersten 2006** (*TiCS*, "Vision as Bayesian inference: analysis by
  synthesis?") — the canonical modern statement that perception inverts a generative
  model.
- **Yildirim, Belledonne, Freiwald & Tenenbaum 2020** (*Science Advances*, "Efficient
  inverse graphics in biological face processing") — an inverse-graphics model that inverts
  a 3D face-graphics program, explains the hollow-face illusion, and maps onto the primate
  face-patch circuit. This is the strongest recent neural evidence for inverse graphics
  *and it directly uses a 3D graphics renderer* — the closest existing thing to "the brain
  inverts a renderer."
- **Predictive coding** (Rao & Ballard 1999, *Nat Neurosci*; Friston 2005/2010, free
  energy) — perception as top-down prediction with only the **prediction error** propagated
  up. This is the "render → compare → correct" loop at the mechanistic level.
- Lineage: Helmholtz's unconscious inference; Grenander's pattern-analysis-by-synthesis;
  Mumford; Lee & Mumford 2003 (hierarchical Bayesian inference in visual cortex).

**The standing dissent — feedforward sufficiency.** The competing account is that **core
object recognition is fast and largely feedforward**: a single feedforward sweep through the
ventral stream (~100–150 ms to IT) suffices to "untangle" object-identity manifolds into a
linearly separable representation (DiCarlo & Cox 2007, *TiCS*, "Untangling invariant object
recognition"; DiCarlo, Zoccolan & Rust 2012, *Neuron*, "How does the brain solve visual
object recognition?"). On this view the heavy iterative synthesis loop is not needed for
the bulk of recognition. The reconciliation now emerging: **recurrence/feedback is
recruited for the HARD cases** — occlusion, clutter, degraded or ambiguous stimuli
(Kar, Kubilius, Schmidt, Issa & DiCarlo 2019, *Nat Neurosci*, "Evidence that recurrent
circuits are critical to the ventral stream's execution of core object recognition";
Tang et al.; Kietzmann et al. on recurrent CNNs matching temporal dynamics). Note this
cuts against the project's own *feedforward-nets-fail-fundamentally* framing in a useful
way: the field's position is "feedforward suffices for the easy bulk; recurrence/synthesis
for the hard tail," not "feedforward is fundamentally broken."

**On the specific 3DGS-as-AbS mapping.** The abstract structure — a generative renderer,
compared to the image, with residual-driven refinement — is a fair *description* of both
predictive coding and 3DGS's fitting. But two honest gaps: (a) the brain's synthesis
objective is **prediction-error minimisation over learned features**, not photometric pixel
reconstruction (Claim F); (b) neurally plausible inverse graphics (Yildirim et al.) is
explicitly built to **avoid slow iterative optimisation** by amortising it into a fast
feedforward recognition pass — i.e. the field's own best neural model of inverse graphics
is the *opposite* of 3DGS's slow per-scene gradient-descent densification loop. So "vision
is a render-compare-grow loop" is SUPPORTED as an abstract computational goal (AbS) but the
3DGS-style *iterative per-scene optimisation* is not how the biology is thought to run it in
real time.

**Citations:** Yuille & Kersten 2006 (*TiCS* 10:301); Yildirim, Belledonne, Freiwald &
Tenenbaum 2020 (*Science Advances* 6:eaax5979); Rao & Ballard 1999 (*Nat Neurosci* 2:79);
Friston 2010 (*Nat Rev Neurosci* 11:127); Lee & Mumford 2003 (*JOSA A* 20:1434); DiCarlo &
Cox 2007 (*TiCS* 11:333); DiCarlo, Zoccolan & Rust 2012 (*Neuron* 73:415); Kar et al. 2019
(*Nat Neurosci* 22:974). [Yildirim + DiCarlo corroborated by fetched snippets; Rao-Ballard,
Friston, Lee-Mumford, Kar recalled from training + search corroboration — flagged.]

---

## Claim E — Has anyone proposed 3D GAUSSIAN SPLATTING SPECIFICALLY as a model of biological perception?

**VERDICT: UNDER-STUDIED → effectively UNCLAIMED. The COMPONENTS are old and supported;
the SPECIFIC 3DGS-as-perception synthesis was NOT found in the literature. State it as an
honest gap, not as manufactured novelty.**

3DGS is a mid-2023 method, so a brain-model application would necessarily be very recent or
absent. A directed search across three phrasings ("3D Gaussian splatting model of
biological vision / brain perception"; "Gaussian splatting cognitive science neuroscience
model of perception"; "brain as a differentiable renderer / Gaussian primitives
perception") returned **no paper proposing 3DGS as a model of how biological perception
works.** What exists instead falls into three clearly different buckets:

1. **3DGS used as an engineering/measurement tool on biological data** — brain CT view
   synthesis (GaSpCT), multi-modal medical imaging (MedGS), and *Pose Splatter* (a 3DGS
   model for quantifying animal pose/appearance for neuroscience behavioural analysis).
   These use splatting to *image or measure* biology; none claims the brain *does*
   splatting.
2. **Perception imported INTO splatting (the reverse direction)** — *Perceptual-GS*
   (Zhou et al., ICML/PMLR 2025) folds human visual sensitivity into densification,
   allocating finer Gaussians to perceptually critical regions; 3DGS perceptual-quality
   datasets (3DGS-QA). These borrow human-perception *metrics* to make renders look better
   to humans — the opposite of proposing the brain as a splatter. (One review mentions a
   loose "inspired by the neurological hypothesis of 3D spatial cognition" framing, but not
   a splatting-as-perception model.)
3. **Generative-model / inverse-graphics accounts of perception that PRE-DATE 3DGS** —
   analysis-by-synthesis (Yuille & Kersten 2006), efficient inverse graphics (Yildirim et
   al. 2020), predictive coding (Rao & Ballard 1999; Friston), and hierarchical-generative-
   model theories of mental imagery (Breedlove et al., biorxiv 2019 / the HGM imagery line)
   and fMRI generative reconstruction (Shen/Kamitani lineage). These say perception inverts
   *a* generative model — but the primitive is not a set of explicit anisotropic 3D
   Gaussians, and none is 3DGS.

**Honest finding:** the individual ingredients are established and supported — Gaussian(-
windowed) primitives in early vision (Claim A), generative/inverse-graphics perception
(Claim D), efference-copy pose (Claim C-i), sparse/efficient scene coding (Claim F). The
*specific* synthesis "biological perception ≈ 3D Gaussian splatting" appears to be
**unclaimed in the literature as of this search**. That makes the project's framing a
genuine *recombination proposal*, not a re-derivation of a published model — but also not a
validated hypothesis. **Do not cite a nonexistent paper to make it look either settled or
novel; report the gap.**

**Citations (for what DOES exist):** Kerbl et al. 2023 (3DGS, SIGGRAPH); Zhou et al. 2025
(*Perceptual-GS*, PMLR v267); *Pose Splatter* 2025 (OpenReview); GaSpCT 2024 (arXiv
2404.03126); Yildirim et al. 2020 (*Sci Adv*); Rao & Ballard 1999. [Search-level negative
result — absence of evidence across three query formulations; not a proof of nonexistence.
Flagged: I did not exhaustively search 2025–2026 preprints, so a very recent proposal could
exist; the claim is "not found," not "does not exist."]

---

## Claim F — The DISANALOGY is the TRAINING/OBJECTIVE, not the representation

**VERDICT: SUPPORTED. The representation-vs-learning split is defensible; each half of the
disanalogy checks out.**

The claim is that the brain does NOT (a) do global backprop over a stored collection of
posed views, and (b) minimise photometric reconstruction — instead it confabulates a
sparse, categorical, action-oriented model. Both halves hold up:

**(a) Not global backprop over stored posed views.** The biological-plausibility-of-backprop
literature is clear that exact backpropagation — symmetric weight transport, a global loss,
storing all training examples — is not neurally realistic (Crick 1989, *Nature*, "the
recent excitement about back-propagation" / weight-transport problem; Lillicrap et al. 2016
feedback alignment; Lillicrap, Santoro, Marris, Akerman & Hinton 2020, *Nat Rev Neurosci*,
"Backpropagation and the brain"). The brain learns online, locally, without a stored posed-
image dataset to gradient-descend over. So 3DGS's *fitting procedure* (SGD over a fixed
multi-view capture) is the clean disanalogy — this matches the project's own architecture
rule (primitives discovered/grown, not back-propagated).

**(b) Not photometric reconstruction; sparse, categorical, predictive.** Perceptual
representation is **efficient/sparse** (Barlow 1961 efficient-coding; Olshausen & Field 1996;
Simoncelli & Olshausen 2001, *Annu Rev Neurosci*), and the coding objective in predictive
coding is **prediction-error minimisation over learned features**, not pixel-accurate
photometric reproduction (Rao & Ballard 1999; Friston 2010). Perception is also demonstrably
**non-veridical and categorical** — it confabulates a best-guess, revisable, action-oriented
model rather than a faithful render (the change-blindness/grand-illusion evidence of Claim C;
the project's own memory note *confabulation is the default*; colour as a sparse categorical
*sign* rather than a dense per-pixel channel, per the project's *luminance is structure,
colour is a sign*). 3DGS, by contrast, explicitly optimises an L1 + D-SSIM **photometric**
loss toward a veridical radiance reconstruction. So the objective genuinely differs: **the
brain minimises surprise over a sparse predictive code; 3DGS minimises pixel error over a
dense radiance field.**

**One honest tension to flag, not fatal:** the split "same representation, different
objective" is slightly too clean, because objective and representation co-determine each
other — a sparse-predictive objective *produces* a sparse categorical representation, whereas
a photometric objective *produces* a dense radiance field. So it is not strictly true that
the representation is the same and only the training differs; the different objective yields a
*different representation* (sparse-categorical vs dense-photometric). The defensible version:
**the GEOMETRIC PRIMITIVE (an anisotropic Gaussian footprint) is shared and is the real
analogy; the objective (predictive/sparse vs photometric) differs, and that difference
propagates into the representation being sparse-categorical rather than dense.** That is a
sharper and more honest statement than "only the training differs."

**Citations:** Crick 1989 (*Nature* 337:129); Lillicrap et al. 2020 (*Nat Rev Neurosci*
21:335, "Backpropagation and the brain"); Barlow 1961 (efficient coding); Simoncelli &
Olshausen 2001 (*Annu Rev Neurosci* 24:1193); Olshausen & Field 1996 (*Nature*); Rao &
Ballard 1999 (*Nat Neurosci*); Friston 2010 (*Nat Rev Neurosci*). [Crick, Lillicrap,
Barlow, Simoncelli-Olshausen recalled from training + search corroboration — flagged.]

---

## Where the analogy HOLDS vs BREAKS

| Genuinely HOLDS | Genuinely BREAKS |
|---|---|
| **Anisotropic-Gaussian primitive geometry.** V1 Gabor RFs = Gaussian-windowed oriented gratings; a splat's covariance ellipsoid has the same oriented/elongated shape (Claim A). | **The primitive's ROLE.** V1 Gabors are analysis FILTERS (rectified/normalized energy); splats are synthesis primitives that alpha-composite radiance. Filter ≠ radiance splat (Claim A). |
| **Gaussians as the *emergent* natural-image basis.** Sparse coding of natural images spontaneously yields Gabor-like bases (Olshausen & Field 1996). | **Density control mechanism.** Cortical magnification is a FIXED anatomical gradient + active gaze; 3DGS GROWS/prunes primitives per-scene by reconstruction error. Fixed-aperture-pointing ≠ per-scene densification (Claim B). |
| **Perception inverts a generative model (analysis-by-synthesis / inverse graphics).** Real, cited programme (Yuille-Kersten; Yildirim; predictive coding) (Claim D). | **Persistent dense internal model.** Change-blindness / grand illusion: NO stored dense splat cloud; world = outside memory; what persists is a sparse allocentric map (place/grid cells) (Claim C). |
| **Native pose from efference copy** (vs 3DGS's required SfM). A real advantage of the biological setup (Claim C-i). | **Learning rule.** Brain is local/online, not global backprop over a stored posed-image dataset (Crick; Lillicrap) (Claim F-a). |
| **Spend resolution where it matters** (foveation and densification share this *goal*). | **Objective.** Brain minimises prediction error over a sparse predictive code; 3DGS minimises photometric L1+SSIM over a dense radiance field (Claim F-b). |
| **A residual/error signal drives refinement** (predictive coding's prediction error ≈ splatting's reconstruction residual, as an abstract loop). | **Real-time procedure.** Neurally-plausible inverse graphics amortises into a FAST FEEDFORWARD pass (Yildirim); 3DGS is SLOW iterative per-scene SGD. And feedforward-sufficiency (DiCarlo) contests the heavy-iteration reading (Claim D). |

---

## The honest novelty reframing

After the literature: **"brain ≈ Gaussian splatting" is a RECOMBINATION of established parts
(anisotropic-Gaussian primitives + inverse-graphics/analysis-by-synthesis + efference-copy
pose + sparse-predictive coding), not a genuine new mechanism at the level of any single
component — but the SPECIFIC synthesis "3DGS-as-perception" is itself unclaimed (Claim E).**
So the honest framing is: *the parts are all supported and old; the assembly is unclaimed;
the assembly is a HYPOTHESIS, not a validated model, and its most exposed joint (persistent
dense storage, Claim C; per-scene densification = foveation, Claim B) is the part the
literature most directly contradicts.*

Sorting THIS project's candidate novelties into ALREADY-COVERED vs GENUINELY-OPEN:

**Already substantially covered (do not claim as novel):**
- Anisotropic-Gaussian primitives in early vision — Jones & Palmer 1987; Olshausen & Field
  1996. 40 years old.
- Perception as inverse graphics / render-compare — Yuille & Kersten; Yildirim; predictive
  coding. Covered.
- Sparse/efficient, non-veridical perceptual representation — Barlow; Simoncelli-Olshausen;
  the grand-illusion line. Covered.
- Efference copy as self-motion signal — reafference principle, 1950. Covered as biology.

**Genuinely open / where THIS project's version could be novel (ranked):**
1. **Splat-primitives DISCOVERED by MDL / refusal rather than back-propagated.** The field's
   Gaussians are either *fit by SGD* (3DGS) or *emergent from a sparsity penalty* (Olshausen-
   Field) — in both cases via continuous optimisation. A primitive *minted* by an explicit
   description-length / refusal operation (the sd-loop's "residual mints a quantum"), as a
   discrete graph act rather than a gradient step, is not standard. **Most promising —
   it is the one part with no clean literature analogue as a *mechanism*.**
2. **A REPRESENTABLE RESIDUAL where no primitive covers — a first-class "I don't have this
   yet."** 3DGS's residual is a scalar loss consumed by the optimiser and discarded;
   predictive coding's prediction error is propagated but not *held as an object*. A
   *named, carryable* residual the agent can reason over and later ground is a genuinely
   different representational commitment (this is the same frontier the companion file
   flagged for the active-seeing thread — consistent, and still open here).
3. **Self-motion / efference copy as the NATIVE pose source vs SfM.** Biology has this
   (Claim C-i) and so do egomotion-representation-learning papers (Agrawal-Carreira-Malik;
   Jayaraman-Grauman, per the companion file) — so the *idea* is covered, but wiring it as
   an explicit pose input to a *splat-style* primitive fit specifically is not something the
   literature has done (because nobody has done 3DGS-as-perception at all — Claim E).
   Novelty is in the *combination*, not the ingredient.
4. **The frame/continuum invariant (Gaussian params continuous/cross-frame; footprint
   discrete/in-frame).** This maps cleanly onto 3DGS — the Gaussian's mean/covariance ARE
   continuous real-valued parameters, and its rasterised footprint IS a discrete pixel
   set, so "continuous only cross-frame, integer in-frame" is *descriptively* consistent
   with how a splat works. I found **no literature framing this as an invariant/principle**;
   it reads as a project-specific design axiom (also flagged UNDER-STUDIED in the companion
   file). Possibly novel, possibly a re-encoding of quantization + continuous embedding;
   needs its own adjudication (out of scope).

**Single sharpest genuinely-novel residual:** **MDL/refusal-minted primitives + a
first-class representable residual** — i.e. the splat-set is GROWN by a discrete "this span
matches nothing I hold, keep it as a named residual, mint a quantum" operation rather than by
photometric SGD (3DGS) or a sparsity penalty (Olshausen-Field), and the residual is a
carryable graph object rather than a discarded scalar loss. Every other candidate is either
covered (1950s–1990s) or is a recombination whose only novelty is that nobody has assembled
3DGS-as-perception before (Claim E).

---

## Flagged uncertainties

- **Recalled-not-fetched citations** (asserted from training with only search-snippet
  corroboration, NOT individually fetched — verify before publishing): Rodieck 1965;
  Daugman 1985; Jones & Palmer 1987 (year/venue); Carandini & Heeger 2012; Rao & Ballard
  1999; Friston 2010; Lee & Mumford 2003; Kar et al. 2019; von Holst & Mittelstaedt 1950;
  Sperry 1950; O'Keefe & Dostrovsky 1971; Hafting et al. 2005; Crick 1989; Lillicrap et al.
  2020; Barlow 1961; Simoncelli & Olshausen 2001. Page/volume numbers where given are from
  memory and should be checked.
- **Directly corroborated by fetched search snippets** (higher confidence, but abstracts not
  read in full): Olshausen & Field 1996; Yildirim et al. 2020 (*Sci Adv* eaax5979); DiCarlo
  & Cox 2007 / DiCarlo-Zoccolan-Rust 2012; Rensink-O'Regan-Clark 1997 / Simons-Levin /
  O'Regan "outside memory"; the cortical-magnification log-conformal + ~160× / ~40%-of-V1
  figures; the foveola active-sampling super-resolution result; *Perceptual-GS*; *Pose
  Splatter*; GaSpCT.
- **Claim E is a search-level NEGATIVE** — "no 3DGS-as-perception model found" across three
  query formulations. This is absence of evidence, not proof of absence; I did not
  exhaustively sweep 2025–2026 preprints. A very recent proposal could exist. Report as
  "not found," never as "does not exist."
- **Cortical-magnification quantitative figures** (~160× foveal:peripheral cortical
  sampling, ~40% of V1 to the fovea) come from fetched summary snippets, not the primary
  papers (Schwartz; Duncan & Boynton; Cowey & Rolls). Directionally solid and standard, but
  the exact numbers should be primary-sourced.
- **Contested findings honestly retained:** (a) feedforward-sufficiency (DiCarlo) genuinely
  contests the heavy-iteration reading of AbS — Claim D is SUPPORTED-BUT-CONTESTED, not
  settled; (b) change blindness shows *change is not compared*, which is weaker than
  *nothing is stored* — Claim C's refutation is of a *persistent dense photometric* model,
  not of all internal representation (large-capacity-but-volatile object memory exists,
  Hollingworth & Henderson).
- **Not searched exhaustively:** ~20 sources, depth over breadth per brief, prioritising B/C/E.
  The efficient-coding, object-centric, and inverse-graphics subfields are each large; this
  is an adjudication of the project's six claims, not a survey.
