# Vision — PRIOR ART

*What already exists, in this repo and in the world, for the problems the vision ladder
hit. Written 2026-07-17, after rung 3 was recorded NOT BUILT. Additive: this document
changes no code and retracts no result.*

**Why this exists.** The ladder spent nine pre-registered failures on one root cause (a
learning rule with no stable fixed point) and then failed rung 3 on a second
(`the average has no direction`). Both are questions the literature has answers to. This
document asks, per system: *does it already solve one of ours, and are we reinventing it
or walking into a known dead end?*

**Reading rule.** Every claim below is marked for confidence and for the
*this-exists* / *this-would-work-here* distinction the brief demanded. "Runnable" means
someone checked the last commit.

---

## 0. The headline findings, first

Four things this survey established, in descending order of how much they should change
what we do next:

1. **Retinal direction selectivity is INNATE, and rung 3 as posed is a known dead end.**
   Elstrott, Anishchenko, Krumin, Reitner & Feller (2008, *Neuron* 58:499) —
   *"Direction selectivity in the retina is established independent of visual experience
   and cholinergic retinal waves."* DSGCs are adult-like at eye opening in **dark-reared**
   mice **and** in β2-nAChR-KO mice that have **no cholinergic waves**. Meanwhile
   **cortical** DS genuinely requires experience (Li, Fitzpatrick & Van Hooser 2006,
   *Nat Neurosci* 9:676; Li, Van Hooser, Mazurek, White & Fitzpatrick 2008, *Nature*
   456:952 — dark rearing across eye opening **prevents** DS and later experience does
   **not** rescue it; ~6h of moving gratings suffices to induce it).
   **Our rung 3 asked a retina-shaped population to LEARN a thing the retina does not
   learn.** The H1a null is not our model failing to find a real effect — it is the model
   agreeing with Elstrott. This reframes the rung 3 result from *failure* to
   *replication of a known biological fact.*

2. **Our "the average has no direction" is CORRECT, is NOT in the literature in our
   form, but is MISLOCATED — the culprit is our stimulus ensemble, not Oja.** The sharp
   statement: for a stationary ensemble the covariance is diagonalised by space-time
   Fourier modes with spectrum `S(k,ω)`. A travelling wave occupies the pair
   `(k,ω)/(−k,−ω)`. If motion is **isotropic**, `S(k,ω) = S(k,−ω)` — the leftward and
   rightward modes are **exactly degenerate**, the covariance operator **commutes with
   time-reversal**, so no eigenvector can break the symmetry and every real eigenvector
   in the leading eigenspace is a **standing wave** (= sum of two opposite travelling
   waves). That is our result, stated as a symmetry argument.
   **The constructive corollary matters more than the negative:** on a *directionally
   biased* ensemble the degeneracy **lifts** and the leading PC **is** a travelling wave.
   **Oja is not direction-blind. Isotropy is.** (See §4 for why this still won't give us
   a direction *map*.)

3. **GCAL's stability is OUR Oja, under a different norm — we independently
   rediscovered the field's standard stabiliser.** GCAL's learning rule is *plain
   fixed-sign Hebbian plus divisive sum-to-1 normalisation*. Explicit renormalisation
   `w ← (w + αηx)/‖w + αηx‖` Taylor-expands to `Δw ≈ αη(x − ηw)` — **that is Oja**.
   GCAL uses L1, we found L2. Same contraction, different norm. This is convergent
   validity for rung 2, and it means our nine failures were spent rediscovering
   something the field has assumed since the 1990s.

4. **`gaze_walk` is the wrong eye, and the fix is a published model that maps onto our
   substrate in ~20 lines.** Engbert, Mergenthaler, Sinn & Pikovsky (2011, *PNAS*
   108:E765) is a **self-avoiding walk in a quadratic potential** — locally directional
   (from its own trail), globally rotation-symmetric, **telling the agent no direction**.
   It is the non-isotropic-but-non-cheating drift the brief asked for. And the diagnosis
   sharpens **three times** over what rung 3 recorded (§3.2, §3.5b):
   - `gaze_walk` is **piecewise-constant velocity, direction uniform on [0,2π), held 20
     steps** (`domains/dorsal_world.py:181`). Motion **IS locally coherent within an
     epoch** — isotropy lives **only in the ensemble average**. **The directional signal
     exists at the 20-step timescale and Oja averages it away.**
   - The real block is therefore **not isotropy per se — it is that there is NO direction
     correlation ACROSS epochs** (ballistic, then memoryless).
   - **And within each epoch the motion is 1D, which is structurally blind:** *"No events
     are recorded at edges parallel to the camera motion"* (AMI-EV, *Science Robotics*
     2024). **A drift must be circular or a closed 2D figure.** This is how N-MNIST was
     built (Orchard 2015: three saccades tracing a **triangle**, ±0.5°).

5. **But our decay-through-the-floor failure is genuinely undocumented, and GCAL's
   homeostatic threshold would NOT have caused our BCM annihilation** — because it sits
   in a structurally different place (§2.3). Both of these are real contributions.

6. **Two mechanisms come with NOISE-FREE CONTROLS** — the thing the L0 retraction says we
   most need (§3.3): **SNR-dependent surround** (Atick & Redlich: closed-form prediction
   that the surround broadens in the dark; control = same video at two luminances) and
   **ON/OFF as a residual mint** (a rectified channel makes the negative residual
   permanently unexplained, so our **existing** `vg_mint_kernel_from_patch` should mint
   **exactly one** quantum — **and that quantum IS the OFF channel**). **A bare grid +
   drift cannot accidentally pass either.**

---

## 1. What is already in this repo

Surveyed read-only. The short version: **there is more vision machinery here than the
ladder uses, some of it duplicated, and the graph-native vision Terms do not currently
run.**

### 1.1 BLOCKER — the vision Terms are not in the installed binary

`runners/dsl/src/vision_primitives.rs` and the `ChangeDetect` / `TemporalDiff` /
`Foveate` arms in `term.rs` were committed 2026-07-16 (`0a1a1ee4bb`). The
`substrate_rs` wheel actually imported at
`/home/matt/.local/lib/python3.14/site-packages/substrate_rs/` is dated **Jul 13** and
raises `ValueError: bad Term JSON: UnknownTermType("ChangeDetect")`.

Vision/audio test set: **6 failed, 53 passed**. Three failures are this stale build
(`test_changedetect_byte_parity_with_scipy_valid`, `test_changedetect_stride_and_shape_contract`,
`test_dual_codebook_scopes_exist_and_motion_stream_is_functional` — "vf_temporal_diff
never fired"). `maturin develop` in `runners/dsl/` is a prerequisite before the vision
floor can be evaluated at all. `test_agent_can_query_kernels_via_dsl` fails `36 == 9`,
which looks like an **independent kernel-count bug**, not the stale build.

### 1.2 Inventory

| Item | Path | Lines | Status | Reusable? |
|---|---|---|---|---|
| Rust vision primitives | `runners/dsl/src/vision_primitives.rs` | 305 (~55 real) | **REAL, unbuilt** | Yes |
| Shared-mem eye | `runners/dsl/src/framebuffer.rs` | 791 | **REAL, works** | **Yes — best-engineered thing in the vision tree** |
| fb adapter | `worlds/fb_eye.py` | 56 | REAL (trivial) | Yes |
| `GraphEye` | `domains/vision_graph.py` | 472 | **REAL, broken now**, cv2-heavy | Partly — 4 fixed kernels, not developmental |
| Vision adapter | `domains/vision_world.py` | 152 | REAL, thin, correct shape | Yes |
| Corpus / curriculum | `domains/vision_corpus.py`, `vision_curriculum.py` | 347, 238 | REAL | Yes |
| Scattering | `domains/scattering_feature.py` | 250 | REAL, numpy-only, **not graph-native** | Baseline only |
| "Conditional foveation" | `domains/conditional_foveation.py` | 348 | REAL — but is **Omniglot classification, not optics** | **No — misleading name** |
| Kernel/hierarchy lib | `runners/dsl/python/substrate_rs/vision.py` | 924 | **REAL, works** | **Yes — and the top duplication risk** |
| `sensory_convolution` | `seeds/sensory_convolution.json` | 539 | **REAL selector, 6 hand-designed kernels** | As a selector; **not** as emergence |
| `vision_floor` | `seeds/vision_floor.json` | 558 | REAL (11 rules), **non-functional pending build** | Yes |
| `vision_growth` | `seeds/vision_growth.json` | 146 | **REAL, passes** | **Yes — the actual developmental core** |
| `vision_waves` | `seeds/vision_waves.json` | 2422 | REAL (15 rules, Hebbian + BCM) | Yes |
| `vision_dorsal` | `seeds/vision_dorsal.json` | 1112 | REAL (4 rules, Oja) | Yes |
| `vision_maps` | `seeds/vision_maps.json` | 84 | REAL (1 rule) | Yes |
| 8× encyclopedic seeds | `seeds/vision_{perception,foundation,color,motion,object,scene,cognition,computer}.json` | 46–163 ea | **PROSE** — `{head, body}` strings, 0 nodes | **No** |
| Audio front end | `runners/dsl/src/{audio_primitives,pipeline_runtime,cochlear_nucleus,inferior_colliculus,auditory_cortex}.rs` | 4233 + … | **REAL, works** | **Yes — copy the SHAPE** |

### 1.3 The retraction is confirmed in-tree — and `vision_growth` is the honest successor

`seeds/sensory_convolution.json` verified against the file, not the docstring: **6 Kernel
nodes, every one `"designed": 1.0`**, 3×3, integer weights, hand-typed (`onset`
`[-1,-1,-1,0,0,0,1,1,1]`, `centre_surround` `[-1,-1,-1,-1,8,-1,-1,-1,-1]`, …). Nothing
emerged from anything. Its **one rule** (`keep_discriminative_kernel`) is real and
genuinely graph-native — so the accurate description is **a SELECTOR over a hand-designed
pool**. The selection machinery is sound; the emergence claim is dead, exactly as
`VISION_DEVELOPMENT_ARC.md:39/41` records.

`seeds/vision_growth.json` is the *actual* answer to that retraction and it passes today:
`vg_mint_kernel_from_patch` (a patch whose structure no held kernel explains —
`best|Dot(w,x)| < novelty_threshold × |x|` — **becomes** a kernel, stamped
`designed: 0.0`) + `vg_learn_kernel_oja` (full graph-native Oja `w ← w(1−ηy²) + ηyx` as a
`VecAdd`/`MapList` Term tree). **Build on this, not on `sensory_convolution`.**

### 1.4 Duplication risk — do not write a third Oja

Already present twice: Oja in `seeds/vision_growth.json` (graph-native) **and**
`substrate_rs/vision.py::oja_update` (numpy). Hebbian in `seeds/vision_waves.json` **and**
`vision.py::hebbian_update`. And `substrate_rs/vision.py` **already contains** a Gabor
bank (`v1_bank(n_orientations=8)`), an **LGN ON/OFF pair** (`lgn_pair(sigma_on,
sigma_off)`), `dog`, `complex_cell`, and a V1→V2→V4 hierarchy — **all unused by the
floor**, all passing their tests. Before building an ON/OFF split (§3), check this file.

### 1.5 The audio front end is the better-shaped sensory stack — and the shape is the steal

Audio is ~10× vision and runs today. The architecture:

```
numpy samples
  └─ domains/cochlear_nucleus_adapter.py::process_audio    (71 lines — the ENTIRE Python side)
       └─ sub._inner.run_audio_pipeline(nid, raw, fs)      → Rust
                                                              ↓
runners/dsl/src/pipeline_runtime.rs   walks Operation nodes via feeds_into edges,
                                      dispatching on each node's `kind` attr:
   "gammatone" → "envelope" → "onset_detect" → "broadband_coincidence"
                                                              ↓
graph nodes: OnsetEvent / EnvelopeChannel / BroadbandOnset
```

**The key idea, and the single biggest architectural gap: the audio pipeline IS graph
data.** `domains/cochlear_nucleus.py` installs `Operation` nodes wired by `feeds_into`
edges; the Rust runtime *walks that graph* and calls the matching primitive per node
`kind`. So the agent can read its own pipeline, add a band, retune a band (change `fc`),
splice a stage. **Vision has no equivalent** — its topology is hardcoded in
`GraphEye._process_frame` and in a fixed `vf_*` rule chain.

Audio also has what vision entirely lacks:
- **Filterbanks (three):** `gammatone_band`, 32 log-spaced bands 80Hz–7.5kHz
  (`coch_band_centers`/`cochleagram`), and an **ERB-spaced** `cochlea` (Glasberg & Moore
  1990) in `substrate_rs/audio.py` — the direct structural twin of `vision.py::v1_bank`.
- **Gain control / adaptation (several, real):** `hair_cell_envelope` (half-wave rectify +
  one-pole IIR LPF), `floor_dbs` ("adaptive floor — auditory neurons adapt to
  background"), `detect_onsets` (threshold rides an **asymmetric local floor**, "latches
  on dips, decays slow up") + a **refractory period** (`onset_refractory_ms`, 30ms), and
  `domains/cmvn.py` — per-band mean/variance normalisation composed as a **graph
  Term-tree**. **`cmvn.py` is the closest thing in the tree to a graph-native gain
  control and is the model for a vision contrast normaliser.**
- **An STRF layer:** `auditory_cortex.rs` `A1Patch` — a parametrised spectro-temporal
  kernel. **An STRF is a spatiotemporal receptive field; this is architecturally the same
  object a developmental V1 needs**, already parametrised, already graph-resident,
  already running.

**Vision has NO gain control at all.** `seeds/vision_perception.json`'s
`adaptation_normalizes_responses` is prose with nothing behind it.

---

## 2. GCAL / LISSOM / Topographica — the stability question

**Primary:** Stevens, Law, Antolík & Bednar (2013), *"Mechanisms for stable, robust, and
adaptive development of orientation maps in the primary visual cortex"*, *J Neurosci*
33(40):15747–66 ([PMC6618482](https://pmc.ncbi.nlm.nih.gov/articles/PMC6618482/)).

**What it is.** V1 orientation-map development from ON/OFF LGN sheets + laterally
connected V1, driven by "retinal-wave-like" input then natural images. The paper is
structured as an **ablation lattice**: L (LISSOM baseline) → GCL (+gain control) → AL
(+adaptation) → GCAL (both). *That structure is the most valuable thing in it for us* —
it is exactly the arm design our protocol demands.

### 2.1 Runnable? **No. Abandoned.**

- The canonical repo is **[`ioam/topographica`](https://github.com/ioam/topographica)**
  (`github.com/topographica/topographica` **404s**). **Last real commit 2017-08-27**;
  `pushed_at` 2018-07-27. Not archived — just dead. **Python 2 only** (`setup.py`
  classifiers list *only* 2.6/2.7); depends on `gmpy` and `PIL` (not Pillow).
- **No Python 3 fork exists.** Newest fork activity 2019-08-25.
- Successors: `holoviz/param` and `holoviz/holoviews` are **alive** (pushed July 2026) —
  but these are the *visualisation* spinoffs that outlived the science. The
  neuroscience-specific successors **`ioam/imagen`** (2020-11-29) and
  **`ioam/featuremapper`** (2020-11-15) are **both dead**.
- `hernanbari/pylissom` (PyTorch LISSOM, 8 stars) — **also dead, last commit 2018-10-21**,
  and **no evidence it implements GCAL** specifically.
- GitHub code search for `GCAL LISSOM` / `HomeostaticResponse topo` returns **zero
  results**. **There is no GCAL implementation in any maintained package.** Archived at
  [ModelDB #151951](https://modeldb.science/showmodel?model=151951) — preserved, not
  maintained.

**Verdict: "this exists" but decisively NOT "we can run this."** Reimplementation from
the equations (all constants are below) is cheaper than Python-2 archaeology.

### 2.2 The three letters, with the actual mechanisms

**GC — contrast gain control, in the LGN (not V1).** Divisive normalisation via lateral
inhibition within the ON/OFF sheets (their Eq. 2):

```
η_j,O(t+δt) = f( γ_O Σ_i ψ_i ω_ij  /  (k + γ_S Σ_i η_i,O(t) ω_ij,S) )
```

`γ_O = 14.0` (afferent strength), `γ_S = 0.6` (gain-control strength), `k = 0.11` (keeps
output defined for weak input), `σ_S = 0.125` (circular Gaussian suppressive field).
**In models L and AL: `k = 1`, `γ_S = 0`** — gain control is disabled by zeroing γ_S.
That is a clean, data-shaped ablation of exactly the kind our protocol §0 requires.
Purpose: reduce **presynaptic** drive variance across patterns.

**A — homeostatic adaptation of the V1 threshold** (Eqs. 7–8):

```
η̄_j(t) = β·η̄_j(t−1) + (1−β)·η_j(t)      β = 0.991
θ_j(t)  = θ_j(t−1) + λ·(η̄_j(t) − μ)      λ = 0.01, μ = 0.024
```

with `η̄_j(0) = μ`, `t_init = 0.20`. Purpose: reduce **postsynaptic** firing variance.

**L — laterally connected** (inherited LISSOM, Eqs. 5–6):
`η_j = f(γ_A C_A + γ_E C_E + γ_I C_I)`; short-range excitatory `exc_strength = 1.7`,
long-range inhibitory `inh_strength = 1.4`, settled over ~16 iterations into activity
bubbles. **Learning rates: `α_E = 0.0` (excitatory laterals do NOT learn), `α_I = 0.3`,
`α_A = 0.1/τ_A`.** Lateral weights normalised *within* type; afferent ON and OFF weights
normalised **together**.

### 2.3 GCAL's homeostatic θ is NOT BCM — and this is the design lesson for our annihilation

This is the sharpest transferable point in the paper, and it is a *placement* argument:

- **BCM** slides the threshold that separates potentiation from depression. The threshold
  sits **inside the learning rule** and gates the **sign of Δw**. If it outruns activity,
  everything depresses → **annihilation** (our 0.004).
- **GCAL's θ** is a threshold on the **activation function `f`**, entirely **outside** the
  learning rule. It shifts the neuron's f–I curve and **never flips the sign of Δw**.
  GCAL's Δw is sign-fixed positive and is bounded by **normalisation** instead.

**So GCAL and BCM are not two flavours of one trick — they are homeostasis at two
different places in the loop, and GCAL's placement structurally cannot annihilate.**
If we want homeostasis without annihilation risk, that placement is the lesson, and it is
cheap: Eqs. 7–8, three constants.

The paper knows BCM exists and dismisses it in **one clause** — the *only* mention of
Bienenstock in the whole paper notes a "sliding threshold for plasticity (Bienenstock
et al., 1982)" is among mechanisms that "would likely achieve similar results." That is
an **unsupported aside, not a result**. Our BCM annihilation is a real counterexample to
that clause. (**Oja is not mentioned anywhere in the paper**; Triesch is not cited.)

### 2.4 The learning rule — and its exact relation to Oja

**GCAL's rule is plain, fixed-sign Hebbian plus divisive sum-to-1 normalisation** (Eqs.
9–10):

```
Δw_ij,A = α · η_j · η_i          then     Σ_i w_ij,A = 1.0 enforced
```

Verified directly in the CNS05 PDF (Eq. 3, the same LISSOM rule):

```
w'_ij,ρab = (w_ij,ρab + α_ρ η_ij X_ρab) / Σ_ruv [ w_ij,ruv + α_r η_ij X_ruv ]
```

**Relation to Oja.** Oja's rule is the **first-order Taylor expansion of exactly this
operation**: `w ← (w + αηx)/‖w + αηx‖` expands to `Δw ≈ αη(x − ηw)`. GCAL uses **L1**
(sum-to-1) where Oja is **L2** — the same contraction under a different norm, with the
`−ηw` decay applied *exactly and explicitly* each step rather than approximated.

> **Our Oja result and GCAL are the same discovery.** We found the multiplicative-decay
> form; they use the renormalise-every-step form. Both supply the contraction that
> fixed-sign Hebb lacks. This is strong convergent validity for rung 2 — and it should be
> **cited as such rather than presented as novel.**

**Which mechanism does the real work?** The ablation answers cleanly, and the answer is
layered:
- **Normalisation does the weight-boundedness work — and it is in ALL FOUR models,
  including baseline L.** It is *not* what GCAL adds. Their L is already stable against
  blow-up.
- **GC + A do the *map*-stability work** — a **different failure mode from ours**.

### 2.5 Did they hit OUR failure? — **Partly, and the direction is opposite**

**On unconstrained Hebbian they state it but never demonstrate it.** Verbatim:

> *"Unless it is constrained, Hebbian learning will lead to ever-increasing (and thus
> unstable) values of the weights (Rochester et al., 1956)."*

Note the citation: **Rochester 1956**, 57 years old. This is a **received truism stated in
passing to motivate normalisation, not an experiment.** There is no figure of unnormalised
Hebbian blowing up. **And the direction is opposite to ours:** they assert *ever-increasing*
weights (divergence); **our failure was decay to zero.**

**Nobody in this family documents our decay-through-the-floor transient, because they
never ran the unnormalised case.** Our nine pre-registered failures traced to one root
cause is **a cleaner empirical result on that specific question than anything in this
literature.** That is a genuine contribution and should be written up as one.

**What they DO document is a different instability — contrast-driven map churn:**

> *"with high-contrast input, connections between ON/OFF and V1 cells are more likely to be
> overwritten as differently oriented patterns are presented, leading to continual
> reorganization of receptive fields and a corresponding loss of stability"*

Model L becomes "highly unstable" above **~30% contrast**; Fig. 6F shows a "highly
disorganized" map at 100% contrast. That is RFs being **rewritten**, not weights
vanishing. GCAL is the fix for **that**.

> **Do not let the shared word "stability" collapse the two.** GCAL answers a question
> **downstream** of ours: we are establishing that a fixed point exists at all; GCAL
> assumes that (via normalisation) and asks whether the resulting map survives contrast
> variation. **Our contrast is not yet varied — so we have not yet reached GCAL's
> problem.** When we do, GC+A is the answer and the L/GCL/AL/GCAL lattice is the design.

### 2.6 Retinal waves in GCAL — weaker than ours; do NOT cite them as having solved this

GCAL's pre-eye-opening input is:

> *"loosely modeled after retinal waves (Wong, 1999) and represented as noisy disk-shaped
> patterns"*

— randomly placed disks, radius a substantial fraction of the sheet, Gaussian-blurred
edges, plus uniform zero-mean noise. **No wave statistics whatsoever:** no propagating
fronts, no wavefront velocity, no correlation length, no refractory dynamics. It is
**noisy disks with a retinal-wave label.** Post-eye-opening they switch to natural image
patches (Shouval et al. 1996).

Their Fig. 10 result is genuinely good and is a target for us: **switching disks →
natural images at iteration 6000 causes no drop in map stability** and no retuning —
that is the "robust and adaptive" claim.

> **Our rung 1 waves — random ignition + rule-driven propagation + refractoriness — are
> arguably MORE biologically faithful input than GCAL ever used.** That is a defensible
> differentiator, and it means **GCAL is not a baseline we can cite as having solved
> wave-driven map formation.** (The broader LISSOM lineage — Bednar's 2002 thesis
> *Learning to See*; Bednar & Miikkulainen, *Neurocomputing* 2005 — claims previsual
> spontaneous activity suffices for realistic OR/OD maps, but with similarly abstract
> patterns.)

### 2.7 Direction selectivity in this family — yes, but in LISSOM, NOT GCAL

**GCAL itself: zero.** The 2013 paper mentions direction and motion **nowhere**. All
stimuli are static, ON/OFF units have "constant, sustained output," all connections have
constant delay — **temporal structure is explicitly abstracted away. GCAL is
architecturally incapable of DS as published.**

**The LISSOM lineage did it ten years earlier, in a branch GCAL did not inherit:**
- Bednar & Miikkulainen (2003), *"Self-organization of spatiotemporal receptive fields and
  laterally connected direction and orientation maps"*, *Neurocomputing* 52–54:473–480.
- Bednar & Miikkulainen, *"Joint maps for orientation, eye, and direction preference in a
  self-organizing model of V1"*, *Neurocomputing* (2006)
  ([CNS05 PDF](https://nn.cs.utexas.edu/downloads/papers/bednar.cns05.pdf)).

**The mechanism — lagged LGN cells, and the cost is steep:**

> *"The time delays model the 'lagged' cells recently found in cat LGN that respond to
> retinal inputs only after a fixed delay."*

- **16 LGN sheets** = {ON, OFF} × **4 lags (3,2,1,0)** × {left, right eye}. Versus 2 sheets
  for orientation-only LISSOM. **An 8× fan-out of the LGN layer purely to buy a time axis.**
- Input: **moving natural image patches**, drawn "in four discrete timesteps, like frames
  of a movie," moving in random directions. Scale: 54×54 photoreceptors → 36×36 LGN →
  **142×142 V1**, **20,000 fixations**.
- **Same normalised Hebb rule — NO new learning machinery was needed for direction.**
  **Direction fell out of the INPUT REPRESENTATION, not the rule.**
- Results: "Nearly all neurons developed spatiotemporal receptive fields selective for
  orientation, and most were also selective for direction," RFs **space-time inseparable**
  (matching DeAngelis et al.), direction ⊥ orientation, joint DR/OD/OR maps.

A hook directly relevant to us, from their discussion:

> *"motion preferences can arise from any source of different delays in neural activity
> propagation, in addition to the LGN lags modeled here."*

**The gap worth naming: nobody in this family combined GCAL with direction.** Direction
(2003–06, pre-GCAL, unstabilised against contrast) and GCAL (2013, stable but static) are
**disjoint branches that were never merged. Stable direction-map development does not
exist in this literature.**

**Modern independent confirmation:** Larisch et al. (2025), *"A systematic analysis of the
joint effects of ganglion cells, lagged LGN cells, and intercortical inhibition on
spatiotemporal processing and direction selectivity"*, *Neural Networks*
([bioRxiv 2024.01.31.578157](https://www.biorxiv.org/content/10.1101/2024.01.31.578157v1.full)).
Chemnitz group, not Bednar's. Finding: *"intercortical inhibition alone leads to
bidirectional selectivity; a temporal shift in the thalamocortical pathway breaks this
symmetry in favor of one direction."* Confirms lagged-LGN independently and recently.
*(Confidence: MEDIUM — both ScienceDirect and bioRxiv returned 403; abstract-level only.)*

---

## 3. The eye — optics, eye movements, retina circuits, waves, events

### 3.1 ISETBio — alive, MATLAB-only, and **not worth it for us**

`isetbio/isetbio` is genuinely maintained (pushed **2026-07-13**) — and **MATLAB-only**.
**Every Python port is dead or a stub:** `hjiang36/pyEyeBall` (an official-team port) is
three weeks of work abandoned in **2015**, 0 stars, alpha; **`ISET/ISETPy` contains
exactly two files — LICENSE and README.** It is a spec to reimplement, not a dependency.

**And it stops where we need it to start:** ISETBio covers optics → cone mosaic →
photocurrent. **It does not cover ON/OFF or the inner-retinal circuit** — the thing we
actually lack. **Verdict: not worth it.** Take the eye-movement model (§3.2) from Engbert
instead; that is the only part of the ISETBio story we need, and it is elsewhere.

### 3.2 Fixational drift — **the Engbert self-avoiding walk is the honest answer, and it is our top item**

**Engbert, Mergenthaler, Sinn & Pikovsky (2011), *PNAS* 108:E765**, *"An integrated model
of fixational eye movements and microsaccades"* — **verified: it IS a self-avoiding walk
in a quadratic potential.**

```
h_ij → h_ij + 1            (occupied site)
h_kl → (1−ε)·h_kl          (all sites — the SLOW relaxation is REQUIRED for persistence)
u(i,j) = λL[((i−i₀)/i₀)² + ((j−j₀)/j₀)²]
(i′,j′) = argmin over neighbours of { h_kl + u(k,l) }
```

`λ=1, χ=2, ε=10⁻³, h_c=7.9, L=51`. A microsaccade fires when activation exceeds `h_c`,
via a separate quartic potential.

> **This is structurally our substrate already**: a small lattice, one scalar per cell
> that increments on visit and decays otherwise, plus an argmin over neighbours. The
> `Argmin` and `Neighbours` Terms exist. It is ~20 lines and cheaper than almost anything
> else in the pipeline.

**Persistent-short / antipersistent-long — confirmed:**

| Lag | Model | Experiment |
|---|---|---|
| Short (≤10 iter) | α = 1.32±0.02 (**H≈0.66**, superdiffusive) | 1.38±0.05 |
| Long (10–50) | α = 0.71±0.06 (**H≈0.36**, antipersistent) | 0.79±0.11 |

Crossover ~20 ms. **Self-avoidance makes the persistence; the potential makes the
antipersistence.** *Honest caveat that partly undercuts the story: filter out
microsaccades and the long-lag antipersistence largely disappears — drift alone ≈
persistent-then-Brownian.*

**THE CRUX, ANSWERED: the SAW is a non-isotropic model that does NOT cheat.** It is
locally directional (from its own trail) and globally rotation-symmetric. **No direction
is told to the model** — the same standard `WaveWorld.ignite` meets.

**And it reframes our diagnosis of `gaze_walk` a second time.** `gaze_walk`
(`domains/dorsal_world.py:181`) is ballistic for 20 steps, then **memoryless** — a fresh
direction drawn uniformly. So the block is **not isotropy per se; it is that there is no
direction correlation ACROSS epochs**, while *within* an epoch the motion is 1D (see the
blindness constraint in §3.5b). The SAW supplies short-timescale directional coherence
with no prior.

> **One real caution:** the deterministic 4-connected argmin only steps N/S/E/W — a
> **cardinal-axis artifact** that would be a subtle way of telling the agent the answer.
> **Use the stochastic variant** (Schwetlick et al., arXiv:2303.11941).

**Rucci's whitening claim — confirmed, with the real numbers.** `S(k,ω) = I(k)·Q(k,ω)`;
for Brownian drift `Q ∝ k²`; natural images measure **`I(k) ∝ k^−1.9`** (*not* −2 — use
the real exponent); the product `k^0.1` ≈ flat. Honest band: **~0.1–10 c/deg** measured
(~30 c/deg theoretical ceiling). `D ≈ 40 arcmin²/s` (human 20–200). **Rucci, Iovin,
Poletti & Santini (2007), *Nature* 447:852** is sign-specific and therefore strong:
**11 c/deg dropped >16% under stabilization; 4 c/deg unaffected.** **Ratnam et al. 2017
adds the key fact: the benefit does NOT depend on the motion being self-generated — no
efference copy needed.**

> **So yes: drift's role IS to convert SPATIAL structure into TEMPORAL structure.** For a
> substrate whose motion machinery has nothing to read, **the eye movement is what makes
> the signal.** This is the deepest idea in the survey.

**Code: essentially none.** `lschwetlick/EngbertMicrosaccadeToolbox` is Python, maintained
(2026-03-25), CI, Zenodo DOI — but **detection/analysis only, not the generative model**.
Useful for *validating* our α_s/α_l against published values. We implement the SAW
ourselves.

### 3.3 Retina circuit simulators — narrower than the brief assumed

| System | Status | Note |
|---|---|---|
| **open-retina** | **Live** (2026-04-10) | A CNN. **No structure to grow** — right answer for a callable front-end, wrong answer for us. |
| **Macular** (INRIA GitLab) | **Live** (2026-04-07) | **VirtualRetina's actual successor.** See below. |
| **COREM** | **Dead** (2023-04-19) | Canonical, still the best-documented circuit. *Int J Neural Syst*, not *J Neural Eng*. |
| **convis** | **Unbuildable** | **PyTorch 0.4.** |
| **deep-retina** | **Museum piece** | Advertises 2023; **last real commit 2019**. |
| `retinal-simulator` | **Does not exist** | — |

*Skeptical note worth keeping: GitHub's `pushed_at` lies — deep-retina's 2023 badge is
metadata churn over a 2019 tree.*

**Contrast gain control (Wohrer & Kornprobst) — divisive, at the bipolar, shunting:**

```
dV_Bip/dt = I_OPL − g_A·V_Bip
g_A = G_σA * E_τA * Q(V_Bip),    Q(V_Bip) = g_A⁰ + λ_A·V_Bip²
```

High local contrast → large `g_A` → **divides** the response *and* shortens
`τ = 1/(g_leak + g_A)`. **One line buys both of Shapley & Victor's findings.**
**But be honest: `λ_A` ships at 0.** Gain control is **off by default and nobody derived
it.**

**Macular's design should interest us specifically:** the user writes **LaTeX equations
into a GUI; Macular generates C++**, organised as a layered hierarchy. **Model is data,
runtime is compiled, no user imperative code.** That is our architecture rule, arrived at
independently — **prior art for Γ**, and worth citing as such.

**Meister's 2025 "Standard Model of the Retina" (arXiv:2510.17820) is our Occam ladder,
in the retina literature:** the ~40 RGC types are **not 40 mechanisms — they are one
mechanism at 40 parameter settings**; magno/parvo differ by **one parameter vector**.
That is *one held shape + per-dimension deltas*, not a fresh `CapabilityAxis` per cell
type — the `DimInfer` rung-2 reading, in someone else's field.

**Srinivasan, Laughlin & Dubs (1982) — centre-surround IS `prediction_minus_observation`.**
The surround is the **optimal linear predictor of the centre, subtracted; the output is
the residual.** Our own meta-shape, in the first synapse.

> **But be skeptical of "centre-surround IS whitening."** The direct test
> ([PMC1575921](https://pmc.ncbi.nlm.nih.gov/articles/PMC1575921/)) concludes **it is
> not**: whitening yields the `|f|` ramp, **not a DoG**. You need **three** constraints —
> decorrelation **+** response equalisation **+** a size/sparseness constraint.

**The two mechanisms with NOISE-FREE CONTROLS — the most valuable finding for a ladder
that just retracted L0 for a measure that passed noise:**

1. **SNR-dependent surround (Atick & Redlich).**
   `K_exp = M/√(M²(R+N²)+N₀²)`, `M = [R/(R+N²)]·MTF`. Prediction: the surround
   **broadens and weakens in the dark, sharpens in the light** — **closed-form and
   falsifiable**. **Control: feed the same video at two luminances. If the fitted surround
   does not change, it is null.** A bare grid + drift **cannot accidentally pass this**.
2. **ON/OFF as a residual mint.** A single non-negative channel **cannot** represent a
   signed residual without a costly pedestal. Feed our **existing** mint-on-residual rule
   (`vg_mint_kernel_from_patch`) a **rectified** channel and the negative residual is
   permanently unexplained — it should mint **exactly one** quantum, and **that quantum
   IS the OFF channel.** **This is the most substrate-native item in the whole survey: a
   mechanism our ladder DERIVES rather than receives** — and it is the same
   "mint exactly one quantum, then re-decode" shape the sd loop already gates.

**Everything else** (σ ratios, τ values, the magno/parvo vector) **is a hand-set constant
with no derivation. Do not claim those emerge.** That is precisely the
`sensory_convolution` `designed:1.0` error, one level up.

**Also stealable — Baccus's validation protocol:** fit only the **outputs**, then check
hidden units against **separately-recorded interneurons that were never fit**.
**"Don't fit the thing you're claiming emerged."** Given the L0 retraction, **that
discipline is worth more than any of the code in this section.**

### 3.4 Retinal waves — our model IS the standard model; the FIXED refractory period is the toy part

**Godfrey & Swindale (2007)** verified against **both paper and C++ source**.
Activity-dependent refractoriness:

```
ΔR_i = H₁ + (N_i · H₂ · D/M)        # threshold jump ∝ input received
```

Mouse: `H₁=1.0, H₂=0.5, P=50s, K=0.6s, D=2.0s`.

**Two findings that should land hard:**
- **They use NO stochastic ignition at all.** Thresholds initialise uniform-random, then
  it is **deterministic and chaotic**. **Randomness is an OUTPUT, not an input.** We could
  **drop `ignite()` entirely** — which is a strictly stronger form of our own
  paradigm-forcing rule (§0 of the protocol: the adapter supplies entropy and a clock —
  here it supplies **only** the clock).
- **Coverage uniformity: SD of activity duration drops 26.2% → 4.1%.** For a
  developmental substrate where **every cell should get comparably trained**, that number
  alone justifies the change. **It is one extra term.**

**Hennig criticality — real but TUNED, not self-organised.** Size exponent α: model 1.5,
experiment 1.55–1.93; an **exponentially truncated** power law, pure only at
`k₀≈1.4 kHz`. They say plainly: *"we initially choose parameters such that power-law
distributions are obtained."* **No branching-parameter claim — they frame it as
percolation** (`ρc⁺≈0.70` ≈ hex site-percolation `p_c≈0.6970`).

> **So our model will NOT sit at criticality for free.** The ratio of ignition rate to
> refractory recovery is a knob — **and our `driven` channel is a SECOND ignition source
> that will push it around.** (Honest tension not to paper over: Butts says `f*≈0.18`,
> Hennig says `ρc≈0.70`. **Different rules, not the same claim.**)

**THE STANDARD STATISTIC — name it: the Wong/Meister/Shatz correlation index `C(d)`.**
B-spikes in a **±50 ms** window around each A-spike, normalised by B's rate (1.0 =
independent), plotted **against pair distance**. **Every paper reports it.**
**We currently have NO wave-statistics test at all. If we match one thing, match `C(d)`.**

**Three problems with 16×16 specifically:**
1. **Our neighbourhood is too small.** Godfrey: 85 µm dendritic radius / 34 µm spacing ≈
   **~19 neighbours, graded by dendritic overlap**. Butts: R=120 µm ≈ 3.5 steps. **Our
   4-neighbour `neighbour` edges are well below biological coordination number — and the
   percolation threshold depends directly on coordination number. This is the most likely
   reason our waves will not match statistics.**
2. **Scale.** 16×16 at 34 µm ≈ **0.3 mm²**. Godfrey's tested range bottoms at 0.65 mm²; a
   real wave domain is 0.156 mm². **One wave covers ~half our grid.** Our size
   distribution will be **cutoff-dominated — do not over-claim a power law.**
3. **Good news:** Hennig's *experimental* power law came from an **8×8 MEA**. Our 256
   cells are **not obviously under-resolved**.

**Ge et al. 2021 citation correction: it is *Science* 373:eabd0830, NOT Nature.** The
claim holds causally (§4.4). **But be skeptical of the STRENGTH:** circular variance
0.61/0.56; only **~33–46% of waves within 60°** of the dominant direction **vs 33% by
chance** — **~10–13pp over chance, in a narrow P8–P11 window. Implement it as a weak
drift, not a conveyor belt.**

**Code & data:**
- **`BennyCa/Retinal-Wave-Simulator`** (C++, 2023-04-09, GPL-3) — **contains the actual
  Godfrey model. Best thing to port from.**
- **`sje30/waverepo` — 366 real recordings (355 mouse) as HDF5, readable from Python.**
  **That is our ground truth, and data does not rot.**
- Hennig has **no wave code** on GitHub (all 21 repos are spike sorting).
- ⚠️ **`sje30/sjemea` and the 2025 pretraining repo have NO LICENSE.**

### 3.5 Event cameras — **the honest answer is mostly negative at our scale**

**v2e is the only maintained one (2026-04-13). ESIM is abandoned (2023-12-25, 83 open
issues) and inapplicable anyway** — it needs a renderer we do not have.

Reading v2e's **source** rather than its paper surfaced things the paper rounds off:
- **Bandwidth is intensity-dependent:** `eps = inten01·(Δt/τ)`,
  `inten01 = (I+20)/275 ∈ [0.073, 1.0]`. **Dark pixels are slow → motion blur in the
  dark.** The most physically interesting part.
- **The paper says two-pole; the shipped code is first-order.**
- **Defaults disagree across four places in the same repo.** Import `EventEmulator`
  without params and you **silently** get noise **off** and bandwidth **infinite** — an
  ideal DVS, **exactly what the paper criticises vid2e for.**
- The shot-noise source carries the author's own TODO: *"the shot noise rate should
  increase with intensity but factor is negative here."* **Treat 0.25 as empirical.**

**(a) "Events give ON/OFF for free" — half true, and the false half matters.** DVS
polarity is `sign(Δ log I)` — a **TEMPORAL** contrast sign. Retinal ON/OFF is **SPATIAL**
centre-surround opponency. **A DVS pixel has no spatial surround at all.** Events give a
magnocellular-ish **transient channel, not the pathway split.** (Our OFF channel should
come from §3.3's residual mint instead — which derives it.)

**(b) The 2D-blindness constraint — the single most actionable finding in the survey.**
From AMI-EV (*Science Robotics* 2024): ***"No events are recorded at edges parallel to the
camera motion."*** **A 1D drift makes you structurally blind along its own axis.** AMI-EV
uses a rotating wedge prism (12 Hz, ~1.5–2.0 px circular trajectory); **N-MNIST's triangle
does it crudely.** **Our drift must be circular or a closed 2D figure.**

> **And this indicts `gaze_walk` a third time:** it draws a fresh direction every 20 steps,
> so it covers directions **over time** but is **blind along the current axis WITHIN each
> epoch** — during the very window in which the delay line must read the motion.

**This is not speculation — it is how N-MNIST was built.** Orchard et al. (2015) mounted
an ATIS on a pan-tilt and made **three saccades tracing a triangle, ±0.5°, ~300 ms**, for
**exactly our reason**.

**(c) At 16×16, "drift" is a misnomer — it is a saccade.** One pixel is **6.25% of the
field**. Human fixational drift is **sub-pixel at our scale → ZERO events.** N-MNIST paid
a **21% field-of-view tax** (28×28 digit in a 34×34 array) for its ±0.5° saccade. **Ours
would be worse.**

**(d) The log transform is genuinely free and genuinely valuable.** `Δ log I` is **exactly
invariant to multiplicative illumination**. At 16×16, where we have no pixels to spare on
gain-control machinery, **this is the best value-for-money item on the list.**

**(e) The sparsity argument collapses at 16×16.** At N=256, touching every pixel costs
nothing. Worse: shot noise at the `noisy` preset × 256 px ≈ **43 noise events/tick at
30 Hz** against a handful of signal events — **and we have no spatial redundancy to
denoise against.**

**(f) THE 16×16 KILLER, and it is blunt:** downsampling to 16×16 **averages 16×16 blocks
— a lowpass. Temporal contrast is GENERATED by spatial structure moving across a pixel,
and we just averaged that structure away.** We keep exactly the low-spatial-frequency
content event cameras are **worst** at. **No study exists at 16×16; N-MNIST's 34×34 is the
demonstrated floor — 4.5× our pixel count.** (The "16 events → 91%" subsampling paper does
**not** support this — it subsamples *events at full spatial resolution* and says nothing
about 256-pixel arrays.)

**(g) Interpolation — worst-possible-failure-mode warning.** SuperSloMo gets **ordering**
right for smooth motion; **sub-frame timing is invented**. *Ordering is real information;
detail is fabricated.* If our tick rate ≈ frame rate we throw the ordering away anyway and
interpolation is pure cost. **Silent-failure risk: v2e interpolates at INPUT resolution.
Feed it pre-downsampled 16×16 frames and SuperSloMo estimates optical flow on a 256-pixel
image — confabulated garbage dressed in a physically-calibrated noise model.**

**THE ONE-HOUR TEST THAT GATES THE WHOLE PATH:** take real video, downsample to 16×16,
plot **`Δ log I` per cell over time**. **If temporal contrast rarely crosses 0.2 log
units, the event representation is EMPTY at our scale** and no simulator realism fixes it.
Expect: marginal for natural video, fine for large high-contrast moving objects — **and
the DRIFT, not the event conversion, is what makes it work. With a static camera at 16×16
we will measure exactly zero.**

---

## 4. Direction selectivity — what actually breaks the symmetry

### 4.1 Every working model injects a temporal asymmetry. The only question is WHERE.

| Model | Symmetry breaker | Prior, or learned? |
|---|---|---|
| **Barlow–Levick (1965)** | **delay on one arm + AND-NOT veto** | Structural prior |
| **Hassenstein–Reichardt** | **delay on one arm + multiplication** | Structural prior |
| **Adelson & Bergen (1985) motion energy** | the **space-time-oriented filter itself**; quadrature pair + squaring | The filter **is** the prior |
| **Lagged vs non-lagged LGN** (Saul & Humphrey; Bednar 2003) | **temporal delay in the INPUT** | Structural prior |
| **Kim et al. (2014)** | **space-time wiring specificity** | Anatomical prior |
| **STDP models** | **the learning rule's own time asymmetry** | **Learned — the only learned route** |

**The minimal ingredient is always: a delay + a nonlinearity.** A delay alone is
direction-blind at second order unless the ensemble is biased; a nonlinearity alone has no
time arrow.

### 4.2 A correction we need to make to our own write-up

Our root-cause note says second-order statistics are direction-blind. **That is not true in
general and we should not publish it in that form.** The Hassenstein–Reichardt correlator
**is a second-order (pairwise) operator** and estimates direction fine. The rigorous
treatment is **Fitzgerald, Katsov, Clandinin & Schnitzer (2011), *PNAS* 108:12909**,
*"Symmetries in stimulus statistics shape the form of visual motion estimators"* —
pairwise correlators are *one component* of the optimal strategy; higher-order correlations
improve it. **Direction IS present in the second-order spatiotemporal cross-correlation.**

The correct statement is the **degeneracy/symmetry** argument in §0.2: it is our
**isotropic ensemble**, not second-order statistics per se, that kills it. Our
`gaze_walk` makes this concrete and slightly worse than we said: drift is
**piecewise-constant velocity, direction uniform on [0,2π), held 20 steps**
(`domains/dorsal_world.py:181`). **Motion IS locally coherent within an epoch** — the
isotropy lives only in the ensemble average. **So the directional signal is present at the
20-step timescale and Oja averages it away.** That is precisely "symmetry-breaking faster
than the averaging timescale," which `VISION_PROTOCOL.md` already names as the next
hypothesis. The literature agrees, and calls it STDP.

### 4.3 The retinal DS circuit is a WIRING prior, and it is honest about it

**Kim, Greene, Zlateski, Lee, … Seung (2014), *Nature* 509:331**, *"Space-time wiring
specificity supports direction selectivity in the retina"* (EyeWire)
([PMC4074887](https://pmc.ncbi.nlm.nih.gov/articles/PMC4074887/)):
- **BC2** (proximal, near SAC soma) vs **BC3a** (distal). **BC2 lags BC3a by 50–100 ms.**
- Outward motion from the soma → proximal-first, distal-later → if speed matches the lag,
  signals **arrive simultaneously and sum** → large depolarisation. Inward → asynchronous →
  weak. A space-time oriented RF **built out of anatomy**.
- **It is wiring, reconstructed from fixed tissue. The paper offers NO developmental or
  activity-dependent account.** A structural prior, honestly labelled.

`distance-from-soma → temporal lag` **is** the prior. And per Ge 2021 (§4.4), that same
prior is what makes the waves directional in the first place.

### 4.4 Retinal waves ARE directionally biased — our isotropic wave model is *a* bug

**Ge, Zhang, Gribizis, Hamodi, Sabino & Crair (2021), *Science* 373:eabd0830**,
*"Retinal waves prime visual motion detection by simulating future optic flow"*
([PMC8841103](https://pmc.ncbi.nlm.nih.gov/articles/PMC8841103/)) — verified in detail:
- Stage II waves in mouse have a **temporal→nasal propagation bias** in a transient window,
  **P8–P11**. Circular variance 0.5611 at P10–11; concordance with forward-motion optic
  flow 0.611 ± 0.026.
- The bias is **enforced by asymmetric GABAergic inhibition from starburst amacrine cells
  via GABA-A** — *the same innate circuit asymmetry that underlies adult DS*. SAC ablation
  destroys directionality without changing other wave properties; **FRMD7** mutation (the
  gene establishing SAC asymmetry) eliminates it.
- Chronic gabazine → **superior colliculus** DS impaired: gDSI 0.265 → 0.175; DS neuron
  fraction ~21% → ~11%.
- **Crucially: chronic GABA-A blockade does NOT alter DS development in the RETINA.**
  Waves instruct **downstream** (SC), not the retina.

**Read the causality carefully: SAC structural asymmetry → wave bias → downstream DS.**
Not waves → DS. **The wiring prior is upstream of everything.**

**Skeptical counterweight — do NOT treat "add a bias and Oja learns DS" as settled.** The
closest computational analogue to our rung 3 ran the exact control and got a **null**:
*Pre-training ANNs with retinal waves*, **PLOS Comput Biol 2025**
([10.1371/journal.pcbi.1012830](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1012830))
compared temporal→nasal-biased waves vs **unbiased** waves and concluded *"the mere
presence of patterned spontaneous activity, rather than the propagation bias during a
specific developmental time frame, might be driving enhanced motion processing."*
Directionality was **not necessary**. (Caveats: trained with backprop; reports **no**
direction-selective units.) Code:
[comp-neural-circuits/pre-training-ANNs-with-retinal-waves](https://github.com/comp-neural-circuits/pre-training-ANNs-with-retinal-waves).

**One paper says the bias instructs DS; the nearest simulation says it doesn't matter.**
That is a live disagreement and our substrate is well placed to adjudicate it — with a
pre-registration, and with `dark` correctly meaning *waves continue* (protocol §6).

### 4.5 Cortical DS is learned, and STDP is the standard mechanism

- **Rao & Sejnowski** — *Predictive Sequence Learning in Recurrent Neocortical Circuits*
  ([NIPS 1999](https://proceedings.neurips.cc/paper/1783-predictive-sequence-learning-in-recurrent-neocortical-circuits.pdf));
  *Spike-Timing-Dependent Hebbian Plasticity as Temporal Difference Learning*, *Neural
  Comput* 13:2221 (2001) ([PDF](https://homes.cs.washington.edu/~rao/nc_td.pdf)).
  **Verified:** biophysical simulations in which a network **learns to predict moving
  stimuli and develops direction-selective responses**, with space-time RFs resembling DS
  cells in alert monkey V1. STDP triggered by dendritic backpropagating action potentials
  implements a **temporal-difference** rule. **This is the closest match to what we want.**
- **Wenisch, Noll & Obermayer (2005), *Biol Cybern*** — *"Spontaneously emerging direction
  selectivity maps in visual cortex through STDP"*
  ([link](https://link.springer.com/article/10.1007/s00422-005-0006-z)). **DS *maps* emerge
  via STDP from intrinsic spontaneous activity ALONE — no directional stimulus needed.**
  Axonal/lateral **conduction delays are essential**. **This is our rung 3, done, with
  STDP instead of Oja.**
- **Buchs & Senn (2002), *J Comput Neurosci*** — a temporally asymmetric spike-based rule
  redistributes vesicle release probability, producing an asymmetric RF.
- Honda et al. (2011), *J Neurosci* 31:1516 — DS development in retinotectum via STDP.

### 4.6 The underrated cheap option: nonlinear Hebbian

**Brito & Gerstner (2016), *PLOS Comput Biol* 12:e1005070**, *"Nonlinear Hebbian Learning
as a Unifying Principle in Receptive Field Formation"*
([link](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1005070)) —
sparse coding, ICA, STDP and BCM **all unify into nonlinear Hebbian learning**, which is
*sufficient* for RF formation. The rule

```
Δw_i = η · g(y) · (x_i − g(y)·w_i)
```

is **exactly as local as Oja** — one nonlinearity on the output — and it reaches
**higher-order statistics**, which is what carries direction (**van Hateren & Ruderman
1998, *Proc R Soc B* 265:2315** ran **ICA on natural image *sequences*** and got
space-time-oriented, **direction-selective** filters resembling V1 simple cells;
[PMC1689525](https://pmc.ncbi.nlm.nih.gov/articles/PMC1689525/)). PCA never does this
(Bell & Sejnowski 1997; Hyvärinen).

**It is a one-line change to `vg_learn_kernel_oja`,** which already computes `y = Dot(w,x)`
and `w ← w(1−ηy²) + ηyx` as a Term tree.

---

## 5. What the engine would need

*Per the corrected brief: mechanisms are ranked by what the biology requires, NOT by ease
of implementation. Where a mechanism needs something the substrate lacks, that gap is
named here as a first-class requirement. This codebase's own rule is "primitive in Rust,
composition in graph" — a missing primitive is a thing to BUILD, never a reason to pick
worse science.*

Verified engine surface: **163 Term variants**; `Dot`, `MapList`, `Fold`, `VecAdd`,
`Neighbours`, `InNeighbours`, `MaxOver`, `Argmin`/`Argmax` exist. **No `Zip`. No `Range`.**

| # | Mechanism (biology) | What the engine must gain | Size |
|---|---|---|---|
| **E1** | **STDP eligibility trace** (§4.5 — the learned route to DS) | **Nothing structural.** Per-synapse trace as an edge attr: `trace_i ← trace_i·decay + x_i`, then `Δw_i ← η·(trace_i·y − x_i·ȳ)`. Each synapse reads only its own input, own trace, own weight, and a **broadcast postsynaptic scalar**. Expressible with `MapList`/`Dot`/`VecAdd` today. Needs the trace read from the **previous tick** — confirm the fixpoint's read/write ordering gives that. | **S** |
| **E2** | **Conduction delays** (§2.7, §4.5 — *essential* per Wenisch; the LISSOM answer) | A **delay line per afferent**. `vision_dorsal` already has 0–3-step delays, so the primitive exists; what's missing is **delays on LATERAL connections** (Wenisch's requirement) and a longer, per-edge-parametrised delay. Likely a Rust Term (`DelayedAttr(edge, k)`) + a per-edge ring buffer. | **M** |
| **E3** | **Divisive normalisation / contrast gain control** (§2.2 GC; §1.5 audio's `cmvn.py` precedent) | `Σ_i η_i ω_ij,S` over a suppressive neighbourhood, then a divide. **Expressible today** (`Fold` over `Neighbours` + arithmetic). The vision-side gap is that **nothing computes it** — this is a seed-rule build, not an engine gap. `domains/cmvn.py` is the template. | **S** |
| **E4** | **Homeostatic threshold on the activation function** (§2.3 — the non-annihilating homeostasis) | Two per-unit scalar attrs (`η̄`, `θ`) updated by two rules. **Nothing structural.** Three constants (β=0.991, λ=0.01, μ=0.024). **This is the cheapest high-value item in the whole document.** | **S** |
| **E5** | **Nonlinear Hebbian** (§4.6) | **Nothing.** One nonlinearity `g(y)` inside `vg_learn_kernel_oja`. A one-line Term-tree change. | **XS** |
| **E6** | **Outer product / rank-2 weight update** (any matrix-form rule) | **`Zip` or `Range`, or an `OuterProduct` Rust Term.** Genuinely absent (verified). Not needed for E1–E5 — each synapse computes its own scalar product, so the outer product is *implicit* in the edge set. **Only needed if we want matrix-form updates.** Defer until something demands it. | **M** |
| **E7** | **Sanger/GHA deflation** (to get a direction *map* rather than one global direction) | **A synapse must read ANOTHER unit's weight vector.** Structurally absent. Would need a Term that reads a sibling unit's weights via a shared hub — architecturally invasive. **But note the alternative:** LISSOM/GCAL get maps from **lateral interactions + WTA**, not deflation, and `vm_burst_lateral` is already that precedent. **Prefer laterals; do not build deflation.** | **L (avoid)** |
| **E8** | **Rubner–Tavan / Földiák anti-Hebbian laterals** (decorrelation) | **A lateral term that modifies the output being competed over, inside the fixpoint.** This is the fixpoint-race the tree currently forbids. Would need either a **two-phase tick** (settle laterals to a sub-fixpoint, *then* learn — which is **exactly what LISSOM does with its ~16 settling iterations**) or an explicit relaxation Term. **This is a real, named engine requirement, and LISSOM's 16-iteration settle is the precedent that it is the right shape.** | **M–L** |
| **E9** | **A graph-data vision PIPELINE** (§1.5 — audio's `Operation`/`feeds_into`) | Vision needs the audio architecture: `Operation` nodes + `feeds_into` edges + a `pipeline_runtime` dispatch arm per op kind. Then the agent can read/retune/splice its own retina. **The single biggest architectural gap between the two sensory stacks.** | **M** |
| **E10** | **ON/OFF split, centre-surround, biphasic temporal kernels** | Numpy versions **already exist unused** in `substrate_rs/vision.py` (`lgn_pair`, `dog`). **But do NOT port them — that repeats the `designed:1.0` error.** §3.3's **residual mint** DERIVES the OFF channel from the rectified-channel residual using the rule we already have. **Nothing new needed.** | **S** |
| **E11** | **Engbert SAW drift** (§3.2 — the top item) | **Nothing.** A per-cell scalar `h` (increment on visit, `(1−ε)` decay), a quadratic potential, and an `Argmin` over `Neighbours` — **all Terms exist.** ~20 lines. **Use the stochastic variant** (arXiv:2303.11941) — the deterministic 4-connected argmin only steps N/S/E/W, a **cardinal-axis artifact that would tell the agent the answer.** Must be **2D-closed** (§3.5b). | **S** |
| **E12** | **Activity-dependent refractoriness** (§3.4 — `ΔR_i = H₁ + N_i·H₂·D/M`) | **Nothing — one extra term** on the existing `wv_refract` rule. Buys **26.2% → 4.1%** coverage uniformity, non-repeating domains, and **lets us drop `ignite()` entirely** (Godfrey uses **no stochastic ignition**: random init, then deterministic chaos). | **XS** |
| **E13** | **`C(d)` correlation index** (§3.4 — the field's canonical wave statistic) | A test/measure, not an engine change. **We have NO wave-statistics gate today.** Ground truth: **`sje30/waverepo`, 366 real recordings as HDF5.** | **S** |
| **E14** | **Wider, graded neighbourhood** (§3.4 — ~19 neighbours, not 4) | More `neighbour` edges with a `weight` attr. **No new primitive.** Our 4-neighbour lattice is **below biological coordination number, and percolation threshold depends directly on it** — the most likely reason our waves will not match `C(d)`. | **S** |
| **E15** | **`Δ log I` (log intensity)** (§3.5d) | **Nothing.** Exactly invariant to multiplicative illumination — **the best value-for-money item at 16×16**, where we have no pixels to spare on gain-control machinery. **But run the §3.5 one-hour gate first.** | **XS** |

**Two-phase tick (E8) is the one to think hardest about.** LISSOM settles lateral activity
over ~16 iterations *before* applying the learning rule. Our fixpoint conflates the two.
If we want laterals (and §2.7/§4.5 both say we do), the settle/learn separation is
probably a genuine engine requirement rather than a workaround — and it is how the
reference implementation of our own rung 4 mechanism works.

---

## 6. Are we reinventing something? Are we on a dead end?

**Reinventing (say so in the write-up, do not claim novelty):**
- **Oja as the stabiliser.** GCAL/LISSOM have used the L1 form since the 1990s (§2.4). Our
  rung 2 is a rediscovery. **The nine failures are the interesting part, not the fix.**
- **Lateral interaction → map topography** (rung 4) is LISSOM's core mechanism, 1990s.

- **Our wave model IS Butts et al. 1999** (§3.4) — random ignition + local propagation +
  refractoriness is **the standard model, not a toy**. The **toy part is the FIXED
  refractory period**; Godfrey's is activity-dependent.
- **Macular** (§3.3) generates C++ from LaTeX equations written into a GUI — *model is
  data, runtime is compiled, no user imperative code*. **Our architecture rule, arrived at
  independently. Prior art for Γ.**
- **Meister's "Standard Model of the Retina"** (§3.3): ~40 RGC types are **one mechanism
  at 40 parameter settings**. That is our `DimInfer` rung-2 reading, in another field.

**Genuinely ours (worth writing up):**
- **The decay-through-the-floor failure of unstabilised fixed-sign Hebbian.** The
  literature asserts *divergence* from a 1956 citation and **never ran the experiment**
  (§2.5). We ran it and got the **opposite sign**.
- **BCM annihilation as a counterexample** to Stevens et al.'s one-clause dismissal (§2.3).
- **Waves with real propagation dynamics** rather than GCAL's noisy disks (§2.6).
- **The isotropy degeneracy stated as a symmetry argument** (§0.2, §4.2) — correct, and not
  in the literature in this form, *once corrected* to blame the ensemble rather than
  second-order statistics.

**Dead ends — stop now:**
- **Rung 3 as posed ("a retina-like population learns DS from waves") is a KNOWN DEAD END.**
  Elstrott/Feller 2008: retinal DS is present in dark-reared **and** wave-less animals.
  **Our H1a null replicates a real biological fact.** Record it as such; do not re-run it
  with a new rule and expect a different answer *at the retinal grain*.
- **Sanger/GHA deflation** for map formation (E7) — laterals already do this job.
- **Resurrecting Topographica** (§2.1) — Python 2, dead since 2017, no Py3 fork.
- **ISETBio** (§3.1) — MATLAB-only, **no viable Python port** (`ISETPy` is two files), and
  it **stops at photocurrent — it does not cover the inner-retinal circuit we lack.**
- **open-retina** (§3.3) — a CNN with **no structure to grow**.
- **Porting `substrate_rs/vision.py`'s `lgn_pair`/`dog` into seeds** — that is
  `designed:1.0` again. Derive OFF from the residual mint instead (E10).
- **The event-camera path is probably a dead end AT 16×16** (§3.5) — downsampling
  lowpasses away the very spatial structure whose motion generates temporal contrast;
  N-MNIST's 34×34 is the demonstrated floor, **4.5× our pixel count**. **Gate it with the
  one-hour `Δ log I` test before spending anything.** Steal v2e's *model* (`lin_log` →
  intensity-scaled IIR → our existing `TemporalDiff` → per-cell frozen Gaussian threshold
  → emit/reset), **never v2e itself** (no torch, no 151 MB checkpoint) — and **never feed
  it pre-downsampled frames** (§3.5g).

**Live and worth doing (in order):**
1. **Fix the build** (§1.1) — nothing here is measurable until `ChangeDetect`/
   `TemporalDiff`/`Foveate` are in the installed `.so`. **Three of six vision tests are
   this; `36 == 9` looks independent.**
2. **Swap `gaze_walk` for the Engbert SAW** (E11, §3.2), stochastic variant, **2D-closed**.
   ~20 lines, maps onto our lattice natively, **unblocks direction without telling the
   agent a direction**, and is **validatable against published α_s≈1.32 / α_l≈0.71** using
   a maintained Python toolbox. **Highest leverage, lowest cost, and it directly addresses
   the structural block rung 3 named.**
3. **Activity-dependent refractoriness** (E12, §3.4) — one term; 26.2%→4.1% coverage
   uniformity; **lets us delete `ignite()`**.
4. **Add `C(d)` as a gate** (E13) + fetch `waverepo`'s HDF5 ground truth. **We have no
   wave-statistics test today; this is the field's canonical one.**
5. **Widen the neighbourhood to ~19 graded neighbours** (E14) — below-threshold
   coordination number is the most likely reason our waves miss `C(d)`.
6. **Decide which grain rung 3 lives at.** Retinal ⇒ **wire the prior** (Kim 2014
   `distance→lag` + Barlow–Levick veto) and **report that as the finding**. Cortical ⇒
   **STDP** (E1) + **lateral conduction delays** (E2), per Wenisch, who got DS *maps* from
   spontaneous activity alone.
7. **The two noise-free gates** (§3.3): **SNR-dependent surround** (two luminances, same
   video) and **OFF-as-residual-mint**. Given that L0's sign measure passed noise, **these
   are the only two mechanisms in this survey a bare grid + drift cannot accidentally
   pass.**
8. **Nonlinear Hebbian** (E5) — one line, reaches the higher-order statistics that carry
   direction (van Hateren).
9. **Homeostatic θ outside the learning rule** (E4) — three constants, cannot annihilate.
10. Contrast gain control (E3) — but note we have not yet *reached* GCAL's problem, since
    we do not vary contrast.

**Adopt regardless of any of the above — Baccus's validation protocol** (§3.3): fit only
the **outputs**, then check hidden units against **separately-recorded interneurons that
were never fit**. ***"Don't fit the thing you're claiming emerged."*** Given the L0
retraction, **this discipline is worth more than any code in this document**, and it
belongs in `VISION_PROTOCOL.md` §1 as a fourth calibration.

---

## 7. Confidence ledger

| Claim | Confidence | Basis |
|---|---|---|
| GCAL rule = Hebb + L1 normalisation ≈ Oja | **HIGH** | CNS05 PDF Eq. 3 read directly; corroborated across notebook + book chapter. 2013 Eq. 9/10 came via page extraction with garbled brackets — substance solid, typography unconfirmed. |
| Topographica dead, Py2-only, no Py3 fork | **HIGH** | Repo metadata, setup.py classifiers, fork survey. |
| GCAL θ ≠ BCM θ (placement argument) | **HIGH** | Eqs. 7–8 vs BCM definition; structural, not interpretive. |
| GCAL never demonstrated Hebbian instability | **HIGH** | Only the Rochester-1956 clause; no figure. |
| Elstrott 2008 — retinal DS innate | **HIGH** | Primary paper. |
| Li/Van Hooser/Fitzpatrick — cortical DS needs experience | **HIGH** | Two primary papers. |
| Ge 2021 wave directional bias | **HIGH** | Primary paper, verified in detail. |
| PLOS 2025 null on wave bias | **HIGH** | Primary paper + public code. |
| Kim 2014 space-time wiring | **HIGH** | Primary paper. |
| Wenisch 2005 DS maps from STDP + spontaneous activity | **MEDIUM-HIGH** | Abstract + citations; full text not read. |
| Larisch 2025 | **MEDIUM** | Abstract-level only; ScienceDirect + bioRxiv both 403. |
| Engbert 2011 SAW — equations, α_s/α_l | **HIGH** | Primary paper verified in detail. |
| Rucci whitening; `I(k) ∝ k^−1.9`; 11 c/deg >16% | **HIGH** | Primary papers; sign-specific result. |
| Godfrey & Swindale — `ΔR` term, no stochastic ignition, 26.2%→4.1% | **HIGH** | **Paper AND C++ source** both read. |
| Hennig criticality is TUNED not self-organised | **HIGH** | Their own words: *"we initially choose parameters such that power-law distributions are obtained."* |
| Ge 2021 bias is WEAK (~10–13pp over chance) | **HIGH** | Primary paper's own numbers. |
| v2e internals (intensity-dependent bandwidth; first-order not two-pole; inconsistent defaults) | **HIGH** | **Source read, not the paper.** |
| 16×16 lowpass kills temporal contrast (§3.5f) | **MEDIUM-HIGH** | Sound argument from first principles + N-MNIST's 34×34 floor; **no study exists at 16×16 — hence the one-hour gate.** |
| Centre-surround is NOT simply whitening | **MEDIUM-HIGH** | Direct test (PMC1575921); contradicts the common summary. |
| ISETBio Python ports dead/stub | **HIGH** | Repo contents inspected. |
| Repo inventory (§1) | **HIGH** | Files read; tests run (6 failed / 53 passed). |
| Engine surface (§5) | **HIGH** | `term.rs` grepped: 163 variants, no Zip/Range. |
| `substrate_rs/vision.py` duplication | **HIGH** | Independently re-grepped: `lgn_pair`, `v1_bank`, `dog`, `gabor`, `hebbian_update`, `oja_update` all present. |
