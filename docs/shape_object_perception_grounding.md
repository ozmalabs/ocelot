# Shape & Object Perception — component / part-based models, grounding for the jabberwock

Research spike (web + literature) feeding the jabberwock a plan for the LOCATED handwriting
wall. This doc is REFERENCE for the agent — legitimate research feeding its cognition, NOT a
substitute for it. The PLAN is the jabberwock's (driven separately).

## The located wall (where this research is pointed)

The handwriting frontier is now pinned by three honest gates:
- segmentation works but does not lift recognition (dd171c02) — not the bottleneck;
- an earned cheap geometric per-segment feature walls at ~33% (5695f2b3, BUILD A null) —
  pooled substroke moments −5.7pp, curvature-law turn-profile −20.7pp, StructSim graph 18%;
- the agent HOLDS the structural composition machinery (shape-math: `AntiUnify` /
  `AntiUnifyWitness` / `Substitute` / `Unify` / `StructSim`, parts+relations, residual-recurrence
  generation) and a working writer-style residual (writer-ID 6× chance, 5695f2b3).

So the gap to borrowed frozen-Gemma (91%) is a **PERCEPTUAL-FEATURE gap**: a high-dim,
deformation-tolerant per-part feature. NOT segmentation, matcher, prior, or structural shape-math
— those are held. The crux: **earn a high-dim perceptual part-feature WITHOUT borrowing a
pretrained net, that COMPOSES with the held structural part+relation representation.**

For EACH model below: (i) how the per-part PERCEPTUAL FEATURE is obtained
(EARNED-from-data / HAND-designed / BORROWED-pretrained), and (ii) how PARTS COMPOSE.

---

## HUMAN / cognitive-science & neuroscience models

### Biederman — Recognition-by-Components (geons), 1987
- (i) FEATURE: **hand-designed** primitive vocabulary — ≤36 geons (cylinder/cone/box…) read off
  *non-accidental properties* of edges (curvature, collinearity, parallelism, symmetry,
  cotermination), invariant to viewpoint/noise. No learned perceptual feature; a fixed geometric
  alphabet.
- (ii) COMPOSE: a **structural description** — geons + their relations (relative size, position,
  attachment, top-of/side-of). Recognition = best match of (geons, relations) to stored models.
- FIT: this is exactly the jabberwock's *held* side (a fixed part vocab + parts+relations). Confirms
  the missing piece is NOT the structural description but the *per-part feature* feeding it.

### Marr & Nishihara — generalized cylinders / hierarchical parts, 1978
- (i) FEATURE: **hand-designed** generalized cylinders (sweep a cross-section along an axis); parts
  defined on the **object-centred** axis, not image pixels.
- (ii) COMPOSE: a **hierarchy** — coarse whole-axis → finer part-axes, each part its own coordinate
  frame (recursive part-of). Stable, viewpoint-independent.
- FIT: motivates a multi-scale / hierarchical part feature; the axis idea → medial-axis below.

### Medial axis / shape skeleton (Blum; Marr; bone graphs)
- (i) FEATURE: **hand-designed** geometric transform — the skeleton (locus of bi-tangent centres) +
  radius function. Human vision shows evidence for a *pruned* medial-axis model (PMC 2019).
  Sensitive to boundary noise (must be pruned).
- (ii) COMPOSE: skeleton branches = parts; the **bone graph** abstracts branches into a hierarchical
  parts+relations graph (parses shape into part hierarchy directly from the skeleton).
- FIT: a cheap, graph-native part DECOMPOSITION that already emits parts+relations — but still a
  *geometric* feature (same family as the agent's ~33% cheap feature). Good for parsing, not for the
  perceptual-feature gap on its own.

### Gestalt grouping; topological perception (Chen); curvature/codons (Hoffman & Richards); shape bias (Smith)
- (i) FEATURE: **hand-designed** grouping laws / topological invariants / curvature-extrema part cuts
  (the *minima rule*: cut a contour at negative-curvature minima → parts = "codons"). Smith: children
  generalise by SHAPE early (developmental shape bias).
- (ii) COMPOSE: grouping → parts; codons → contour parts; minima-rule cuts ≈ the agent's curvature-
  extrema segmentation (dd171c02). Topological-first (Chen): global topology precedes local features.
- FIT: the **minima rule corroborates the agent's corner-cut segmentation**; the shape bias says a
  shape feature is the right target. Still hand-designed features.

**Human-side verdict:** the cognitive models supply the *structural* story (fixed part vocab + parts +
relations + hierarchy) the agent ALREADY holds, and confirm the missing piece is the per-part feature.
None of them EARN a high-dim perceptual feature — they all hand-design a geometric one (the agent's
~33% regime).

---

## MACHINE / CV-ML models

### Lake — Bayesian Program Learning (BPL), Omniglot-native, 2015
- (i) FEATURE: **EARNED (weakly) + generative** — sub-stroke *primitives are collected/clustered from
  the background characters* (a learned library of motor sub-strokes), not a perceptual image feature.
  The "feature" is the program; the LIKELIHOOD is a **renderer** (run the motor program + ink + motor
  noise → image, compare to the observed image). So matching is **analysis-by-synthesis in image
  space**, which is where the perceptual signal actually enters.
- (ii) COMPOSE: a hierarchical **probabilistic program** — character = parts (strokes) → sub-parts
  (sub-strokes from the primitive library) → relations between parts (from a relation library) →
  render. Compositional + causal + learning-to-learn.
- FIT: **closest to the agent** (Omniglot-native, parts+relations+generation = the held machinery).
  KEY LESSON: BPL's perceptual power is the **renderer / analysis-by-synthesis** (compare in image
  space), not a learned encoder. The agent has the program side; what it lacks is the **render-and-
  compare-in-image-space likelihood** that turns its program into a perceptual score.

### Felzenszwalb — Pictorial Structures / Deformable Part Models (DPM)
- (i) FEATURE: **hand-designed** per-part appearance (HOG part filters) — a gradient-histogram template.
- (ii) COMPOSE: parts + **spring** (deformable) geometric relations; score = part-appearance + spatial
  deformation cost; inferred by dynamic programming over a tree of parts.
- FIT: the deformable parts+relations idea matches `StructSim` (soft leaves) + relation edges; HOG is a
  cheap gradient feature (agent's regime). Confirms relations should be *soft/deformable* (held).

### Zhu & Mumford — And-Or grammars / stochastic compositional models
- (i) FEATURE: hand-designed terminals at the leaves; the power is the **grammar**.
- (ii) COMPOSE: an **And-Or graph** — AND = part decomposition, OR = alternative configurations; a
  stochastic grammar over parts. Recursive, reconfigurable.
- FIT: the agent's `AntiUnify`/`Unify` lattice + held rules ≈ the grammar side. Held.

### Hinton — Capsule Networks & GLOM (part-whole hierarchy)
- (i) FEATURE: **EARNED end-to-end** — capsules/columns learn pose+identity embeddings; GLOM learns by
  **reconstruction (autoencoding) + agreement regularisers** (an image-level self-supervised objective).
- (ii) COMPOSE: **routing/agreement-by-consensus** — lower parts vote for higher wholes; "islands of
  agreement" = the parse tree; equivariant pose, invariant part-whole weights.
- FIT: agreement ≈ the agent's relational consistency; but capsules/GLOM EARN the feature via a big
  trained net (expensive, not graph-native). The transferable idea: **agreement/consensus** as the
  compose rule, and **reconstruction** as the self-supervised signal to earn the feature.

### Slot attention / object-centric learning
- (i) FEATURE: **EARNED** via reconstruction; slots compete to explain the image (an autoencoder).
- (ii) COMPOSE: a fixed set of slots bind to parts/objects by iterative attention.
- FIT: same reconstruction-earns-the-feature lesson; slot = part role (the agent's WorldRole/slot idea).

### Scattering transform / steerable wavelets (Bruna & Mallat, 2011–13)  ★ the crux candidate
- (i) FEATURE: **EARNED-FREE / fixed-by-design** — a cascade of **wavelet convolutions + modulus +
  local averaging**. The filters are FIXED (not trained), so it needs **NO pretrained net and NO
  training data for the filters**, yet yields a **high-dim** representation that is *translation-
  invariant* and *Lipschitz-stable to deformations* (exactly the deformation tolerance handwriting
  needs). First layer ≈ SIFT; deeper layers add invariant detail.
- (ii) COMPOSE: the scattering coefficients are a per-region perceptual descriptor; compose by computing
  them **per segment** (the agent's segments) → a high-dim per-part feature that plugs into the held
  parts+relations.
- FIT: **the cheapest principled way to EARN-not-borrow a high-dim perceptual feature.** SOTA on
  *small-training-set* handwritten digits precisely because the filters carry the prior instead of
  training. Graph-native-able as fixed convolution Terms (wavelet bank = a fixed kernel; modulus =
  `Abs`/`Magnitude`; averaging = pooling). No learned net needed → satisfies earn-not-borrow at near-
  zero cost.

### ScatSimCLR — scattering + contrastive, for small datasets (2021)  ★ the principled upgrade
- (i) FEATURE: **EARNED, self-supervised, cheap** — a ScatNet front-end (fixed wavelets) + a SMALL
  trainable head learned by **contrastive self-supervision** (maximise agreement between two augmented
  views of the same input). The fixed scattering slashes the trainable parameter count → works on
  small data with no external pretraining.
- (ii) COMPOSE: per-part scattering → small learned projection → contrastive invariance to the right
  deformations.
- FIT: **the convergent answer** — fixed scattering gets the high-dim perceptual base for free; a tiny
  self-supervised head (contrastive, or the agent's held closed-form PCA→LDA `Whiten`/`WithinScatter`)
  earns deformation-invariance from the data the agent already has (the 20 reps per char = natural
  augmentations / the writer-style variation manifold). Earned, not borrowed; cheap; composes.

### Analysis-by-synthesis / vision-as-inverse-graphics (Yildirim; 3DP3; BPL's renderer)
- (i) FEATURE: **no encoder at all** — the perceptual signal is the **render-and-compare residual** in
  image space. The "feature" is implicit in the generative model + a comparison metric.
- (ii) COMPOSE: invert a generative (graphics/program) model: search programs whose rendering best
  reconstructs the image.
- FIT: directly usable by the agent — it HOLDS the generative side (residual-recurrence shape
  generation, parts+relations). Add a **render + image-space compare** and the program BECOMES the
  perceptual likelihood (the BPL lesson), no learned encoder. Complementary to scattering: scattering
  earns a discriminative feature; analysis-by-synthesis earns a generative likelihood.

---

## Convergent finding (ranked by FIT + COST — cheap/graph-native first)

How to EARN a high-dim perceptual part-feature that COMPOSES with the held shape-math:

1. **Scattering / fixed-wavelet per-segment feature (★ cheapest, earn-FREE).** Fixed wavelet bank +
   modulus + averaging = a high-dim, deformation-stable per-part descriptor with NO training and NO
   borrowed net. Computable as fixed-kernel Terms (conv = held linear ops, modulus = `Abs`/`Magnitude`,
   pool = mean). Plug per-segment → the held parts+relations / `StructSim` soft leaves. Directly attacks
   the perceptual-feature wall; closest to "earn-not-borrow at near-zero cost."
2. **Self-supervised head on the scattering base (★ principled, cheap, EARNED).** Tiny learned
   projection on top of (1) trained by self-supervision — contrastive over the 20-reps-per-char natural
   augmentations, OR the agent's own held closed-form `Whiten`/`WithinScatter` (PCA→LDA) which it
   ALREADY used to earn an encoder (speech→handwriting transfer). Earns deformation-invariance from
   held data; no external pretraining (ScatSimCLR pattern).
3. **Analysis-by-synthesis likelihood (★ uses the held generator).** Render the agent's program to an
   image and compare in image space (BPL's actual source of perceptual power). Turns the held residual-
   recurrence generation into a perceptual likelihood — no encoder. Pairs naturally with (1)/(2) as the
   verify step (recognition-by-generation).
4. Medial-axis / minima-rule parsing (supports decomposition, same cheap-geometric family — already
   ~33% regime; use to improve parsing, not as the perceptual feature).
5. Capsules / GLOM / slot-attention (EARN the feature but via a big trained net — expensive, least
   graph-native; mine for the *agreement* compose-rule and the *reconstruction* self-supervision idea,
   not the architecture).

**The one-line answer for the agent:** the missing piece is a high-dim perceptual per-part feature;
the cheapest earn-not-borrow route is a FIXED scattering/wavelet per-segment descriptor (high-dim,
deformation-stable, no training, no borrowed net), optionally refined by the agent's own held closed-
form PCA→LDA self-supervision over its natural 20-reps augmentations, and/or verified by analysis-by-
synthesis (render-and-compare) using the held residual-recurrence generator. All of this composes with
the held parts+relations / `StructSim` shape-math.

## Sources
- Biederman RBC / geons: https://en.wikipedia.org/wiki/Recognition-by-components_theory ;
  https://web.mit.edu/9.670/www/Feb15HumanObjectRecognitionPsychophysics/human_Obj_recog.pdf
- Marr & Nishihara, generalized cylinders / Binford (via skeleton refs below).
- Medial axis / skeleton / bone graphs: https://pmc.ncbi.nlm.nih.gov/articles/PMC6894409/ (pruned
  medial-axis in human vision); https://www.sciencedirect.com/science/article/abs/pii/S1077314211000798
  (bone graphs); https://arxiv.org/pdf/1703.08628 (AMAT).
- Lake BPL: https://github.com/brendenlake/BPL ;
  https://medium.com/@antoine.louis/human-level-concept-learning-through-probabilistic-program-induction-9cc4fd7028c9 ;
  https://ar5iv.labs.arxiv.org/html/1902.03477 (Omniglot 3-year report).
- DPM / pictorial structures (Felzenszwalb): standard CV literature.
- And-Or grammars (Zhu & Mumford): standard CV literature.
- Capsules / GLOM: https://www.cs.toronto.edu/~hinton/absps/glomfinal.pdf ;
  https://ar5iv.labs.arxiv.org/html/2102.12627
- Scattering transform: https://arxiv.org/abs/1112.1120 ; https://arxiv.org/pdf/1203.1513 ;
  https://www.di.ens.fr/~mallat/papiers/Bruna-Mallat-Pami-Scat.pdf
- ScatSimCLR (scattering + contrastive, small data): https://arxiv.org/pdf/2108.13939
- Self-supervised (MAE / contrastive): https://www.ijcai.org/proceedings/2023/0762.pdf (MAE survey) ;
  https://www.lightly.ai/blog/simclr (SimCLR)
- Analysis-by-synthesis / inverse graphics: https://arxiv.org/pdf/2111.00312 (3DP3) ;
  https://www.science.org/doi/10.1126/sciadv.aax5979 (efficient inverse graphics, faces) ;
  https://www.semanticscholar.org/paper/fbf839e06b9d67f781678dbd8ac9f3dad4177fc1 (Yildirim).
