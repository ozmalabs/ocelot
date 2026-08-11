# The Manifold Approach to Machine Learning — Grounding

*A research grounding for the gamma-substrate speech agent. Topic: the manifold
hypothesis and manifold learning as the principled route to DATA-EFFICIENT
representation — the frontier where strong structure replaces data. The
through-line in every section is the data-efficiency angle: **how recovering the
manifold reduces the samples needed.***

---

## 0. The principle in one sentence

Real high-dimensional data does not fill its ambient space — it concentrates
near a low-dimensional manifold. The cost of learning (samples AND parameters)
scales with the **intrinsic** dimension of that manifold, not the **ambient**
dimension of the signal. So if you can *recover the manifold* (or supply it as a
prior), you pay for the intrinsic dimension you actually have, not the ambient
dimension you appear to have. That gap is the data you buy back.

This is the formal version of this project's established lesson — that **earned
analytic structure** (a compose-not-train basis) beats the unlabeled-data floor.
The manifold is *what* that structure is the structure of.

---

## 1. The manifold hypothesis — the basis of data-efficiency

**Statement.** High-dimensional natural data (images, audio, video) lies on or
near a low-dimensional manifold embedded in the ambient space; the manifold's
coordinates correspond to the underlying explanatory factors of variation. This
is foundational to deep representation learning (Bengio, Courville & Vincent,
"Representation Learning: A Review and New Perspectives," arXiv:1206.5538, 2013;
the hypothesis itself traces to Vincent & Bengio, early 2000s).

**The load-bearing theorem (sample complexity is ambient-dimension-free).**
Narayanan & Mitter, "Sample Complexity of Testing the Manifold Hypothesis"
(NeurIPS 2010): given upper bounds on intrinsic dimension, volume, and
curvature, Empirical Risk Minimization fits a near-optimal manifold using a
number of i.i.d. samples that is **independent of the ambient dimension**. The
explicit bound is *polynomial in curvature, exponential in intrinsic dimension,
linear in intrinsic volume.* (https://proceedings.neurips.cc/paper/2010/file/8a1e808b55fde9455cb3d8857ed88389-Paper.pdf)

**The canonical paper.** Fefferman, Mitter & Narayanan, "Testing the Manifold
Hypothesis," *Journal of the American Mathematical Society* 29(4):983–1049, 2016
(arXiv:1310.0425). Gives an algorithm that tests, from i.i.d. samples alone,
whether a manifold of bounded intrinsic dimension *d*, volume ≤ *V*, and
**reach** ≥ τ (a curvature/condition-number bound — the largest *r* such that
every point within *r* has a unique nearest point on the manifold) fits a
distribution. The decision rule is a constant-factor gap test, sample bounds
driven by *geometry* (volume, reach), not ambient dimension.

**Why deep nets are data-efficient — the same mechanism, in approximation
theory.** Schmidt-Hieber, "Deep ReLU network approximation of functions on a
manifold" (arXiv:1908.00695, 2019): for inputs on a *d\**-dimensional manifold,
a sparse deep ReLU net approximates a β-smooth function to error ε with on the
order of **ε^(−d\*/β)·log(1/ε)** nonzero parameters — scaling with the
*intrinsic* d\*, not the ambient dimension. Shaham et al. (2018, cited in Pope
et al. below): universal approximation depends *strongly* on intrinsic
dimension, *weakly* on ambient. This is the formal escape from the curse of
dimensionality ("blessing of structure"; cf. arXiv:2408.06996).

**Generalization, too.** Birdal, Lou, Guibas & Şimşekli, "Intrinsic Dimension,
Persistent Homology and Generalization in Neural Networks" (NeurIPS 2021,
arXiv:2111.13171): generalization error is formally linked to a fractal
(persistent-homology) dimension that can be *much smaller* than the ambient
parameter dimension.

**Data-efficiency angle:** every theoretical result above replaces an
ambient-dimension term with an intrinsic-dimension term in the sample- or
parameter-count. The manifold *is* the data-efficiency.

**Honest scope:** not a universal law. "Token embeddings violate the manifold
hypothesis" (arXiv:2504.01002, 2025) is a documented counterexample — the
hypothesis is empirically strong for natural images/audio/video but not every
modality.

---

## 2. Intrinsic dimension estimation — measuring how much structure is there

You cannot exploit the manifold without knowing its dimension. The estimators:

- **MLE (Levina & Bickel 2004,** NeurIPS; https://www.stat.berkeley.edu/~bickel/mldim.pdf**).**
  Models neighbors as a Poisson process on a *d*-manifold. Per-point estimate
  `m̂_k(x) = [ (1/(k−1)) Σ_{j=1}^{k−1} log(T_k(x)/T_j(x)) ]^{−1}`, where T_j is
  the distance to the j-th nearest neighbor; average over points. The most
  widely used estimator; sensitive to the neighborhood size *k*.

- **TwoNN (Facco, d'Errico, Rodriguez & Laio 2017,** *Scientific Reports*
  7:12140**).** Uses only the two nearest neighbors. The ratio μ = r₂/r₁ is
  Pareto-distributed with shape parameter *exactly* the intrinsic dimension *d*;
  recover *d* as the slope of −log(1−F(μ)) vs log μ. Robust to curvature/density
  because it uses only the smallest scale; tends to *underestimate*.

- **Correlation dimension (Grassberger–Procaccia 1983,** *Physica D***).** The
  correlation integral C(r) ∝ r^{D₂} as r→0; D₂ = slope of log C(r) vs log r.
  Heavy data demand: resolving D₂≈6 needs ~10⁵ points (a concrete curse-of-
  dimensionality cost).

- **PCA participation ratio.** `d_PR = (Σλ_j)² / (Σλ_j²)` over PCA eigenvalues.
  Cheap, closed-form, but *linear* → overestimates curved manifolds (a circle,
  ID=1, needs 2 linear dims) and is biased at small sample size.

**What natural data actually shows (Pope, Zhu, Abdelkader, Goldblum & Goldstein,
"The Intrinsic Dimension of Images and Its Impact on Learning," ICLR 2021,
arXiv:2104.08894):**
- MNIST ID ≈ 7–13; CIFAR-10 ≈ 13–26; ImageNet ≈ **26–43** against **150,528**
  ambient pixels.
- The two headline findings, which are *the* data-efficiency claims:
  **lower intrinsic dimension → fewer training samples needed**, and **ambient
  (extrinsic) dimension has little impact on generalization** (shown by
  GAN-controlled experiments holding ID fixed while varying pixels).

**What SPEECH shows:**
- **ISOLET** (spoken letters, 617 acoustic features): intrinsic dimension
  ≈ **9–22** depending on estimator (TwoNN ≈ 9.1; the survey arXiv:2509.15517
  notes TwoNN underestimates here, with other estimators ~12.6–22).
- **Articulatory / production DOF ≈ 3–7.** Jansen & Niyogi, "A Geometric
  Perspective on Speech Sounds" (Univ. Chicago TR-2005-08): the *effective*
  production dimension is ~3–7 because "the system can be described by a few
  physical parameters describing the configuration of the vocal apparatus."
  ARTI-6 (arXiv:2509.21447, 2025) is a concrete 6-D articulatory encoding.
- **SSL speech embeddings** (wav2vec 2.0 / HuBERT) are 768-D (base) / 1024-D
  (large) ambient, with much lower, layer-dependent *local* intrinsic
  dimension (LID rises under noise; GRIDS, arXiv:2605.02715). No single
  canonical absolute-ID scalar for raw SSL speech embeddings exists in the
  literature — it's reported relatively, layer-wise.

**The key number for this project:** the speech *production* manifold is
**~3–7 dimensional**, and the *phoneme* acoustic manifold is **~10–20**. Against
an ambient cochleagram/embedding of hundreds of dimensions, that is the size of
the data-efficiency prize.

---

## 3. Manifold learning methods — geometry vs. visualization, and out-of-sample

The critical axis for *this* project: a usable phone representation must
**extend to new points** (embed a never-seen frame), not just visualize a fixed
set. The methods, with cost and extension:

| Method | Assumption | Solution | Native out-of-sample? | Geometry preserved |
|---|---|---|---|---|
| **Isomap** (Tenenbaum et al. 2000, *Science* 290) | manifold isometric to a convex Euclidean subset; geodesic ≠ Euclidean | **closed-form eigen** (MDS on geodesic graph distances) | No → Nyström | global geodesic |
| **LLE** (Roweis & Saul 2000, *Science* 290) | locally linear patches; reconstruction weights are intrinsic | **closed-form eigen** (sparse `(I−W)ᵀ(I−W)`) | No → Nyström | local weights |
| **Laplacian Eigenmaps** (Belkin & Niyogi 2003, *Neural Comp.* 15) | graph Laplacian ≈ Laplace–Beltrami operator | **closed-form generalized eigen** `Ly=λDy` | No → Nyström | local; links to spectral clustering |
| **Diffusion Maps** (Coifman & Lafon 2006, *ACHA* 21) | random-walk/heat diffusion; diffusion distance = Euclidean in embedding | **closed-form eigen** (Markov operator) | **Yes** (Geometric Harmonics) | multi-scale diffusion distance |
| **LTSA** (Zhang & Zha 2004, *SIAM JSC* 26) | unfolded manifold ⇒ tangent spaces align; local PCA | **closed-form eigen** (alignment matrix) | No | local tangent; supports reconstruction |
| **t-SNE** (van der Maaten & Hinton 2008, *JMLR* 9) | probabilistic neighbor matching; Student-t kernel fixes crowding | **gradient, non-convex** | **No** | local only; global distorted |
| **UMAP** (McInnes & Healy 2018, arXiv:1802.03426) | uniform on manifold, locally constant metric, locally connected | spectral init + **gradient** | approx (fuzzy-graph transform) | local; global contested |
| **Contractive/Manifold AE** (Rifai et al. 2011, ICML/NeurIPS) | manifold = uncontracted Jacobian directions (tangent plane) | **gradient (parametric NN)** | **Yes** (encoder) | local tangent; *built for classification* |

**Out-of-sample is solved for the spectral family.** Bengio et al.,
"Out-of-Sample Extensions for LLE, Isomap, MDS, Eigenmaps, and Spectral
Clustering" (NeurIPS 2003/2004): all of these are learning eigenfunctions of a
data-dependent kernel, and the **Nyström formula** gives a closed-form map for a
new point with extension error comparable to the embedding's own training-set
variability. So "eigen methods can't extend" is *false* — they extend via
Nyström.

**Visualization tools are not feature extractors.** Kobak & Linderman (*Nature
Biotech*, bioRxiv 2019.12.19.877522) show UMAP's apparent global-structure
advantage over t-SNE is **an artifact of its Laplacian-eigenmap initialization**
— matched init makes them perform the same. "Stop Misusing t-SNE and UMAP for
Visual Analytics" (arXiv:2506.08725) and DR reviews show both **collapse global
distances** (geodesic correlation as low as ~0.3), **exaggerate class
separation** (misleading as classification features), and are **hyperparameter-
fragile**. For a *usable* phone representation, prefer the isometry/geodesic-
preserving eigen methods and geometry-preserving autoencoders, not t-SNE/UMAP.

**Data-efficiency angle:** a closed-form eigen-embedding extracts the intrinsic
coordinates in one shot with no training loop, no labels, and no gradient
descent — pure structure, zero label cost. The autoencoder family pays a
gradient/data cost but returns a native parametric extension and a tangent-space
invariance for free.

---

## 4. The SPEECH manifold — and the nuisance problem that breaks it

**Production is genuinely low-DOF — the manifold is real and physical.**
- **Maeda model** (review: Frontiers Robotics AI, 2022, PMC9040071): **7
  articulatory parameters explain 88% of vocal-tract variance** over 519 X-ray
  images; the whole tract (incl. lips) is describable "with reasonable accuracy
  by as few as seven parameters." Parameters are physiologically interpretable
  (jaw height, tongue front-back, flattening, tip, rotation).
- **Source-filter theory** (Fant): speech = a small parametric source (impulse
  train / noise) through a linear vocal-tract filter — a low-D generative model.
  "Learning and controlling the source-filter representation of speech with a
  VAE" (*Speech Communication*, 2023) frames it explicitly as a low-D latent
  manifold from which the high-D signal is generated.
- **Articulatory inversion as manifold recovery:** "Acoustic to Articulatory
  Inversion…" (arXiv:2504.13308, 2025): **4–8 components suffice** to represent
  the inversion mapping; a 6-D articulatory set still yields natural speech.
- **Modern learned codec:** "Coding Speech through Vocal Tract Kinematics" /
  Articulatory Encodec (arXiv:2406.12998, 2024): **14 channels @ 50 Hz**,
  speaker-independent, generalizes to unseen speakers — and crucially **speaker
  embedding is disentangled from articulation** (enables zero-shot voice
  conversion).
- Phoneme distributions are explicitly **low-dimensional nonlinear submanifolds**
  recovered by Isomap/LLE (PMC6706093), and the cited *reason* is the production
  argument: "the intrinsic dimensionality remains small because the system can be
  described by a few physical parameters."

**The nuisance problem — why naive manifold learning recovers the WRONG
manifold.** This is the agent's `lack_of_invariance` gap, stated formally:
- The **lack-of-invariance problem** (Understanding Speech in the Context of
  Variability, ScienceDirect; JASA 153(1):209, 2023): the acoustic→phoneme
  mapping is **many-to-many** — one acoustic pattern maps to different phonemes
  across talkers; one phoneme has different acoustics across talkers.
- Therefore the **dominant axes of acoustic variation are speaker, prosody, and
  rate — NOT phonetic.** "Speaker variability is the *primary* challenge in ASR
  performance degradation." A manifold method run blind on raw acoustics will
  recover the **speaker manifold**, because that is where the variance is.
- In SSL models the nuisance is *localized*: speaker cues concentrate in the
  **early layers** (mirroring mel-filterbank F0/formants), phonetic structure
  emerges in **middle layers** (Layer-wise Analysis, arXiv:2107.04734; place/
  manner/voicing are linearly probeable there). The transformer stack is
  autoencoder-like (deviates then reconstructs).

**What recovers the PHONETIC manifold (weak structure that beats blind
geometry):**
- **Time-variance asymmetry as the separating axis:** content is *time-variant*
  within an utterance; speaker identity is *time-invariant* (Disentangling Voice
  and Content, NeurIPS 2023). This is a *free structural prior* — no labels — for
  splitting the two manifolds.
- **The nuisance direction is concrete:** the **per-utterance mean of CPC
  features captures most speaker information**; per-utterance mean subtraction +
  variance normalization suppresses speaker identity and improves cross-speaker
  acoustic-unit discovery (arXiv:2108.00917). This is *directly actionable* — a
  cheap, label-free nuisance-projection.
- **ABX phone discrimination** (within- vs across-speaker; ZeroSpeech) is the
  benchmark that *measures* whether you recovered the phonetic manifold or the
  speaker manifold — the across-speaker gap *is* the residual nuisance.

**Data-efficiency angle:** the phonetic manifold is ~10–20 D, the production
manifold ~3–7 D. Recovering it — and quotienting out the speaker/prosody/rate
nuisance — means a downstream phone classifier sees a handful of meaningful
dimensions instead of hundreds of mostly-nuisance ones. That is the sample
budget freed.

---

## 5. Manifold structure as a prior / regularizer — the sample-complexity case

- **Manifold Regularization** (Belkin, Niyogi & Sindhwani 2006, *JMLR*
  7:2399–2434): add an *intrinsic* norm (graph-Laplacian smoothness over
  labeled + unlabeled points) to the usual RKHS ambient norm. Representer
  theorems give LapSVM/LapRLS; plain SVM/RLS are the zero-intrinsic-weight
  special case. The load-bearing assumption: P(x) is informative about P(y|x)
  *only if the geometry/manifold assumption holds*.
- **Provable labeled-sample win (conditional):** Niyogi 2013 (*JMLR*
  14:1229–1250) constructs a manifold class (circle embeddings) where **no
  supervised learner can learn**, but a learner that knows/learns the manifold
  from unlabeled data succeeds with few labels — a genuine minimax separation in
  *labeled* sample complexity. This is the cleanest "structure buys back labels"
  result.

**Data-efficiency angle:** unlabeled data sculpts the manifold, the labels only
locate the decision boundary *on* it — the regime where a handful of labels
suffices.

---

## 6. Honest caveats

**(a) Unlabeled data has no worst-case advantage.** Ben-David, Lu & Pál (COLT
2008): without an assumption tying P(x) to the labels, SSL **cannot beat
supervised learning by more than a constant factor**. Niyogi's win is *real but
conditional* on the manifold actually carrying label information. Singh, Nowak &
Zhu (NeurIPS 2008, "Unlabeled data: Now it helps, now it doesn't") pin the
regime: it helps when the **margin/cluster structure is resolvable from the
unlabeled sample density** and hurts when classes aren't separated.

**(b) The manifold is hard to estimate.** Distance concentration (arXiv:
2401.00422): in high dimension nearest-neighbor distances converge, so the kNN
graph that *every* manifold method depends on stops being "local." Fitting under
large noise is provably hard and needs bounded curvature / large reach
(arXiv:2312.10598, 1910.05084). **Neighborhood size is a sensitive
hyperparameter** — too small fragments the manifold, too large short-circuits
across folds (the classic Isomap failure).

**(c) The nuisance-manifold problem (section 4).** Run blind, manifold learning
recovers the *dominant-variance* manifold, which in speech is the *speaker*, not
the *phoneme*. Geometry alone does not know which directions you care about.

**(d) Do deep nets already learn the manifold? Largely, yes.** Ansuini, Laio,
Macke & Zoccolan (NeurIPS 2019, arXiv:1905.12784): trained CNNs have hidden-layer
intrinsic dimension orders of magnitude below their width; ID follows a
"hunchback" (rises early, falls late); **last-layer ID predicts test accuracy**.
Important nuance: the manifolds are *curved*, achieving separability by
**dimension reduction, not flattening** (invisible to PCA). So explicit manifold
regularization risks **re-deriving what a deep net learns for free**.

**(e) The bitter lesson (Sutton 2019).** "General methods that leverage
computation are ultimately the most effective, and by a large margin." Across
chess (search > grandmaster knowledge), Go (AlphaGo Zero removed human
expertise and got stronger), **speech (HMMs + data beat 1970s knowledge-based
systems)**, and vision (CNNs beat SIFT/edge detectors), hand-engineered
structural priors lost to compute-scaling. This is the standing argument
*against* a hand-built manifold prior.

**The reconciliation — and why this project is not (a)–(e) over again.** The
bitter lesson's premise is *scale*: general method + Moore's-law compute + a lot
of data. This project's premise is the *opposite* corner — **little/no data, no
giant pretrain.** Sections 1–2 show that in the small-data regime the
intrinsic/ambient gap is *exactly* what you can't afford to pay for, and the
manifold prior is *exactly* the thing that pays it. Deep nets "learn the
manifold for free" only after consuming the unlabeled-data floor this project's
prior findings already showed is the binding constraint. Manifold structure is
redundant with deep learning *only at scale*; below scale it is the lever. The
honest residual risk is real: blind manifold learning recovers the speaker, and
a closed-form embedding on raw acoustics will under-perform a trained SSL model
*if* you have the data — so the win must be claimed in the **low-data,
nuisance-quotiented** regime and *measured* (ABX across-speaker), not assumed.

---

## 7. Synthesis

### (a) The principle — when/why recovering the manifold buys back data

Learning cost scales with intrinsic, not ambient, dimension (Narayanan–Mitter
2010; Schmidt-Hieber 2019; Pope et al. 2021). Speech's intrinsic dimension is
tiny — **~3–7 D in production, ~10–20 D in phoneme acoustics** — against a
hundreds-D ambient signal. Recovering that manifold means a downstream phone
classifier pays for ~15 dimensions, not ~500, and the freed sample budget *is*
the data bought back. The catch (Ben-David 2008; section 4): the win is real
**only when the recovered manifold carries phonetic information** — which it does
*not* by default, because the dominant variance is speaker/prosody/rate. So the
principle is precise: **recover the manifold AND quotient out the nuisance**; do
it in the low-data regime where deep nets haven't yet paid the unlabeled floor.

### (b) Ranked manifold methods for a data-efficient, extensible speech phone rep

Ranked by fit to *this* project's needs (closed-form > gradient; native/Nyström
out-of-sample; addresses speaker nuisance; usable as features not viz):

1. **Diffusion Maps + Geometric Harmonics** (Coifman & Lafon 2006). Closed-form
   eigen; **native out-of-sample** (Geometric Harmonics); density-aware
   diffusion distance is noise-robust. *Nuisance:* not automatic — but compose
   with per-utterance mean-subtraction (CPC nuisance direction) *before* the
   diffusion kernel. Top pick: cheap, extends, robust.
2. **Laplacian Eigenmaps + Nyström** (Belkin & Niyogi 2003; Bengio et al. 2004).
   Closed-form generalized eigen; Nyström extension; *and* it is the same
   operator as Manifold Regularization (section 5) — so the embedding and the
   semi-supervised classifier are one framework. *Nuisance:* build the graph on
   nuisance-normalized features, or use *weak* phonetic side-info (time-variance
   asymmetry) to weight edges.
3. **Isomap + Nyström** (Tenenbaum et al. 2000). Closed-form eigen; global
   *geodesic* geometry — matches the keystone (a shape is an arc/orbit; geodesic
   length is its intrinsic measure). *Nuisance:* none built in; needs nuisance-
   quotiented input and is sensitive to short-circuit edges. Use when global
   geodesic structure matters more than local density.
4. **Contractive / Manifold-Tangent Autoencoder** (Rifai et al. 2011). Gradient
   cost + needs data, BUT **native parametric extension** and the **tangent-space
   directions give a manifold-invariant classifier directly** — the only method
   here that hands you invariance as an object. *Nuisance:* the tangent
   directions can be *aligned* to nuisance via the time-invariance prior. Use
   when you can afford the gradient loop and want learned invariance.
5. **LTSA** (Zhang & Zha 2004). Closed-form eigen; recovers explicit local
   tangent coordinates and supports reconstruction — natural fit to "shape =
   local tangent of a residual recurrence." No native extension, no nuisance
   handling; a specialist tool for tangent-space analysis.

*Explicitly NOT for features:* **t-SNE / UMAP** — gradient, no/approx
extension, distorted global geometry, exaggerated separation (Kobak–Linderman
2019; arXiv:2506.08725). Use only for sanity-viz, never as the representation.

**The cross-cutting move that addresses the nuisance for all of them:** project
out the **per-utterance mean** (the concrete CPC speaker direction,
arXiv:2108.00917) and/or weight the neighborhood graph by the **time-variance
asymmetry** (content varies, speaker is constant; NeurIPS 2023) *before*
building the manifold — then measure with **ABX across-speaker** to confirm you
got the phonetic manifold, not the speaker one.

### (c) Connection to the agent's keystones

- **"Shape = the trajectory of a residual-feedback recurrence" = a manifold /
  attractor/orbit.** This is literally the dynamical-systems definition of a
  manifold (an orbit/limit-cycle is a 1-D manifold; an attractor is a low-D
  manifold in state space). The keystone and the manifold hypothesis are the
  *same object* viewed generatively (recurrence) vs. geometrically (manifold).
  The agent already holds the generative side; manifold learning is the
  *inverse* — recover the manifold the recurrence traces out. Articulatory
  inversion (section 4) is exactly "recover the residual-recurrence law (the
  motor program) from its acoustic orbit."
- **Order-N shape matching = manifold geometry, intrinsically.** Matching the
  structural shape of two surface-unrelated domains is matching their *manifold
  geometry* (geodesic structure, curvature, intrinsic dimension) modulo the
  embedding — solar-system ↔ atom is a manifold isometry up to scale. The
  agent's held geometry concepts (geodesic, curvature, topology, intrinsic
  dimension) are *precisely* the manifold-learning toolkit; this grounding
  supplies the methods that compute them (Isomap = geodesic; LTSA/CAE =
  curvature/tangent; the ID estimators = intrinsic dimension).
- **The nuisance/lack_of_invariance gap gets a concrete mechanism.** The agent's
  named gap is now actionable: nuisance = dominant-variance manifold (speaker);
  the fix = per-utterance-mean projection + time-variance-weighted graph,
  measured by ABX. `source_filter_theory` and `place/manner_of_articulation`
  are the low-DOF *generative* manifold the phonetic recovery is aiming at.

### (d) Is this just re-deriving SSL / deep nets?

Partly — and honestly so. Deep nets *do* compress data onto a low-ID manifold
and final-layer ID predicts accuracy (Ansuini et al. 2019), so at scale explicit
manifold learning is redundant, and the bitter lesson warns against
hand-engineered structure (Sutton 2019). **But the redundancy is scale-
conditional.** This project's binding constraint is the *unlabeled-data floor*
(its own prior finding); deep nets only earn their free manifold *after* paying
that floor. In the small-data corner, a closed-form eigen-embedding recovers the
intrinsic coordinates with zero labels and zero gradient steps — the
compose-not-train basis this project already proved buys +7% with no data, now
named (it is a manifold chart). The defensible claim is narrow and testable:
**in the low-data, speaker-quotiented regime, an explicit manifold chart is a
free prior that a small SSL model has not yet earned** — claim it there, measure
it with ABX across-speaker, and drop it if (as the measure-or-drop discipline
demands) it proves redundant with the cochleagram + predictive-residual priors
already in place.

---

## Sources (primary, inline above)

Manifold hypothesis / data-efficiency: Narayanan & Mitter NeurIPS 2010;
Fefferman, Mitter & Narayanan JAMS 29:983–1049 2016 (arXiv:1310.0425);
Schmidt-Hieber arXiv:1908.00695; Pope et al. ICLR 2021 (arXiv:2104.08894);
Birdal et al. NeurIPS 2021 (arXiv:2111.13171); Bengio, Courville & Vincent
arXiv:1206.5538. Counterexample: arXiv:2504.01002.
ID estimation: Levina & Bickel NeurIPS 2004; Facco et al. *Sci. Rep.* 7:12140
2017; Grassberger & Procaccia *Physica D* 1983; survey arXiv:2509.15517; Jansen
& Niyogi UChicago TR-2005-08; ARTI-6 arXiv:2509.21447; GRIDS arXiv:2605.02715.
Manifold learning: Tenenbaum et al. *Science* 290 2000 (Isomap); Roweis & Saul
*Science* 290 2000 (LLE); Belkin & Niyogi *Neural Comp.* 15 2003 (Laplacian
Eigenmaps); Coifman & Lafon *ACHA* 21 2006 (Diffusion Maps); van der Maaten &
Hinton *JMLR* 9 2008 (t-SNE); McInnes & Healy arXiv:1802.03426 (UMAP); Zhang &
Zha *SIAM JSC* 26 2004 (LTSA); Rifai et al. ICML/NeurIPS 2011 (CAE/Manifold
Tangent Classifier); Bengio et al. NeurIPS 2004 (Nyström out-of-sample);
Kobak & Linderman *Nat. Biotech* 2019; arXiv:2506.08725.
Speech manifold: Maeda review Front. Robotics AI 2022 (PMC9040071); Fant
source-filter via *Speech Comm.* 2023; inversion arXiv:2504.13308; Articulatory
Encodec arXiv:2406.12998; phoneme manifold PMC6706093; lack-of-invariance JASA
153(1):209 2023; Disentangling Voice & Content NeurIPS 2023; layer-wise
arXiv:2107.04734; CPC nuisance arXiv:2108.00917.
Prior/regularizer + caveats: Belkin, Niyogi & Sindhwani *JMLR* 7 2006; Niyogi
*JMLR* 14 2013; Ben-David, Lu & Pál COLT 2008; Singh, Nowak & Zhu NeurIPS 2008;
distance concentration arXiv:2401.00422; manifold-fitting arXiv:2312.10598,
1910.05084; Ansuini et al. NeurIPS 2019 (arXiv:1905.12784); Sutton, "The Bitter
Lesson" 2019.
