# RATIO_IN_REASONING_LOG.md — the corrected log-frame re-ranking + the log-multiplicative-vs-genuinely-linear map

Supersedes the "additive = wrong shape" verdicts in `RATIO_IN_REASONING.md`. The
prior pass inverted the algebra: it flagged CAN grounding, forecasting regimes,
and analogy as STRETCHES because their quantities are "additive, not
multiplicative." Backwards. The substrate's own audio finding
(`seeds/relational_invariance_findings.json:29-30`, "log_multiplicative_basis_
invariance") states it: **under a logarithm a multiplicative combination becomes
ADDITIVE and therefore SEPARABLE; a ratio cancels a common scale; coherent in any
base.** A ratio in the linear frame IS a difference in the log frame. So a
reasoning quantity being additive is NOT evidence RatioInduce can't touch it — it
is a CANDIDATE that the quantity already lives in the log frame, where a per-frame
multiplicative scale presents as an additive offset a difference (= log-ratio)
factors.

But the corrected lens cuts BOTH ways, and its value is the DISCRIMINATION.
Additive-in-log (a logged product) is a live site; additive-in-linear (a genuine
level shift that was never a product) is not. This document draws that map
honestly — including the sites that stay LINEAR.

## THE TEST (one line, applied to every site)
Is the additive quantity the LOG of a product/ratio (→ LOG-DOMAIN, RatioInduce
applies in the log frame), or a genuine linear level/mean shift that is not a
logged product (→ LINEAR, does not apply)? And even when LOG-DOMAIN: is the
log-quantized quantity INTEGER-OBSERVABLE with the ratio held in Hom (the
frame/continuum invariant, CLAUDE.md:526-566; `coord_ints` refuses Float)? If the
quantity is intrinsically continuous/real-valued in-frame, it fails the invariant
regardless of algebra.

## HEADLINE — what moves STRETCH → LIVE, what stays LINEAR

- **CAN / grounding (site 1): STRETCH → LIVE (LOG-DOMAIN).** The CAN marginal is a
  log-odds readout: `marginal = tanh(β·local)`, `local = Σ_j J_ij σ_j + h_i`
  (`can_ops.rs:236-238`), energy `H = -Σ J σσ - Σ h σ` (`can_ops.rs:352-367`).
  Field h and couplings J combine ADDITIVELY IN THE ENERGY, energy = -log(Boltzmann
  weight), tanh is the log-domain sigmoid. A per-frame confidence SCALE is a common
  h-offset = additive in log = a multiplicative factor on probability = a log-ratio
  a difference cancels. The prior "additive energy = wrong algebra" verdict is
  exactly inverted.
- **Frame primitive (site 5, NEW — the prior pass MISSED it): LIVE, the cleanest
  fit in the whole reasoning layer (LOG-DOMAIN).** `domains/frame.py` stores
  dimension weights as LOGS (`_log_weights`, frame.py:76-82), and
  `relative_weight(a,b) = log_weight(a) − log_weight(b) = log(a/b)`
  (frame.py:171-179) is LITERALLY a log-ratio the module's own docstring calls
  "frame-independent and path-additive" (frame.py:6-8). The reasoning object most
  exactly shaped like RatioInduce's target.
- **Forecasting regimes (site 2): STAYS LINEAR — the honest guard.** The premise
  "log_return is the target, prices multiplicative" is FALSE for THIS codebase. The
  Seldon DGP is `x_{t+1} = mu_regime + phi·(x_t - mu_regime) + eps`, `mu=(0.0, 8.0)`
  (`drafts/seldon_t2_poc/data.py:12,68`) — a two-regime AR(1) on INTEGER cells,
  ZERO `log` anywhere in the stack (grep-verified). The regime is a genuine ADDITIVE
  MEAN SHIFT, not a logged product. Reading it as a log-ratio would MANUFACTURE a
  product the DGP does not contain. RatioInduce does NOT apply.
- **Analogy (site 3): UNRESOLVED → LINEAR/UNAVAILABLE.** The transform delta is a
  SYMBOLIC categorical string residue, not a numeric log quantity — there is no log
  axis to re-read. The missing piece is a numeric magnitude coordinate, not a log
  re-framing.

## THE MAP — per site, file:line + classification

### 1. GROUNDING / CAN — LOG-DOMAIN (applies in the log/energy frame)
- **Where:** `runners/dsl/src/can_ops.rs::mt_mean_field_marginal` (:225-280),
  `mt_energy` (:352-379). Consumers: `insight_seeking.py:95-109`,
  `can_native_orchestration.py:60-84`.
- **Log fact (verified):** `raw_sigma = (beta*local).tanh()` (:236),
  `local = h + Σ w·sj`, `h = ext + identity` (:242-266); `H = -Σ J σσ - Σ h σ`
  (:352-367). tanh(βx) is the log-domain sigmoid ⇒ the marginal is a LOG-ODDS
  readout; energy = -log(weight), additive in h,J.
- **What RatioInduce factors:** across a POPULATION of microtheory/frames differing
  by a common CONFIDENCE SCALE (a uniform field offset Δh), that offset is additive
  in energy = a multiplicative `e^{-βΔh}` on every Boltzmann weight = a common scale
  on the odds. A cross-frame DIFFERENCE of log-odds (pre-tanh `local`) cancels the
  common Δh — the log-ratio RatioInduce induces across the population. Cross-frame
  groundedness comparison genuinely IS a log-ratio.
- **Invariant catch:** marginals/β/h/J are `f32` FLOATS (`node_float_attr`
  throughout). `eval_ratio_infer` reads only INTEGER extents (`coord_ints` returns
  None on Float; CLAUDE.md:526-533). So the algebra fits but the current carriers
  are continuous-in-frame. Wiring needs an integer-observable log-odds quantum (the
  log-odds read at observational resolution — the `resolution` param already
  supports this posture, shape_decode.rs:3253-3266).
- **Verdict:** STRETCH → LOG-DOMAIN LIVE (algebra corrected), gated on an
  integer-observable log-odds quantum.

### 2. FORECASTING regimes — LINEAR (the honest guard; does NOT apply)
- **Where:** `drafts/seldon_t2_poc/data.py:10-17,64-80`;
  `drafts/seldon_t2_text/ingest.py:115-118`, `corpus_gen.py:2-11,72-74`.
- **Why LINEAR:** DGP `x_{t+1} = mu_regime + phi·(x_t - mu_regime) + eps`,
  `mu=(0.0,8.0)` (data.py:12,68); observation = latent rounded to integer cells.
  Regime shift `mu0→mu1` is an ADDITIVE mean displacement in the SAME variable — no
  price, no ratio, no exponentiation, ZERO `log` in the stack (grep-verified). The
  one multiplicative object (`disp_scale`) is a calibration knob already
  scale-invariant. Reading an additive level shift as a log-ratio would manufacture
  a product the DGP does not contain.
- **Verdict:** LINEAR. RatioInduce does not apply. (If the panel were rebuilt on
  log_return — a different DGP — the band would become a log-multiplicative regime
  factor and flip to LOG-DOMAIN. The classification is about THIS code, which is
  linear.)

### 3. ANALOGY / proportional A:B::C:D + concept magnitude — LINEAR/UNAVAILABLE
- **Where:** `domains/analogical_thinking.py::_concept_shape_vector` (:433-457),
  `_pair_witness` (:459-505), `_canon_transform`.
- **Answered from code:** proportional analogy IS additive-in-log on paper
  (A:B::C:D ⟺ logA−logB = logC−logD). But the faculty's "transform" delta is a
  fixed-arity vector of STRING pairs over a symbolic vocabulary (:433-457); pairs
  match iff their transform STRINGS are equal (set-equality of symbols, the
  parallelogram), not a numeric log-difference. There is no magnitude, no coordinate
  extent, nothing `coord_ints` could read.
- **So the blocker is NOT "read the additive delta in log":** there is no numeric
  additive delta — it's symbolic. Weber-Fechner log-perception would apply only IF
  concepts carried a numeric magnitude coordinate, which they do not.
- **Verdict:** UNAVAILABLE/LINEAR — the missing piece is a numeric magnitude axis on
  concepts, not a log re-reading. Survives the corrected lens unchanged.

### 4. sd-loop population rung — LIVE (LOG-independent), and the log lens EXTENDS it
- **Where:** `seeds/shape_decode_loop.json`; `shape_decode.rs::eval_ratio_infer`
  (:3267-3424), `scale_pow2_once` mint path.
- **Stands as prior #1:** N recurrences of one structure at different multiplicative
  integer magnitudes collapse to one held shape + one `latent:scale2`/`latent:ratio`
  dimension; zero new dispatch arm.
- **Log-lens extension:** the collapse IS a log-ratio collapse when recurrences
  differ by a Weber-scaled perceptual quantum — a log-multiplicative magnitude
  presents as the additive integer exponent `k` rung 1 already reads (`latent:scale2`
  = ×2^k = additive k in log₂; CLAUDE.md:530-533). The log frame is not new here; it
  is the frame `scale2` already operates in. Conceptual confirmation, not new wiring.
- **Verdict:** LIVE, LOG-DOMAIN by construction, invariant fully respected.

### 5. Frame primitive — LOG-DOMAIN, cleanest algebraic fit; gated by the invariant (NEW)
- **Where:** `domains/frame.py`: `_log_weights` (:76-82), `relative_weight`
  (:171-179), `dimension_weight` (:155-159), `build_frame` (:110-135).
- **Log fact (verified):** `build_frame` takes LINEAR relative weights and stores
  their LOGS (`out[dim] = math.log(wv)`, :81); `relative_weight(a,b) =
  log_weight(a) − log_weight(b) = log(a/b)` (:171-179), docstring:6-8 "a log-ratio
  log(a)−log(b)=log(a/b) ... frame-independent and path-additive." The module's
  founding ontology already declares a weight to be a log-scaled vector / log-ratio.
- **What RatioInduce factors:** a POPULATION of per-context/per-interlocutor frames
  differing by a per-frame overall importance SCALE (a common additive offset on
  every log_weight = a multiplicative factor on every linear weight). A cross-frame
  difference of `relative_weight` cancels the common offset — RatioInduce's
  population-invariant target expressed in the reasoning layer's OWN log-ratio
  vocabulary. A far cleaner shape match than CAN or analogy.
- **Invariant catch (identical to CAN):** `log_weights` are FLOATS (`math.log`,
  :81). In-frame the invariant demands INTEGER. The log-ratio is real-valued
  in-frame, so it must be the MAP (held in Hom, applied on read, integer-observable
  at resolution), not the stored float weight. Frame.py currently stores the
  continuous log-weight in-frame — the category the invariant forbids for
  RatioInduce's integer reader.
- **Verdict:** LOG-DOMAIN, cleanest algebraic fit, LIVE only if the per-dimension
  weight is re-expressed as an integer-observable quantum with the log-ratio held in
  the map. Wiring cost: integer relative-weight quantization + population assembly.

## OTHER LOG-DOMAIN REASONING QUANTITIES FOUND (candidate sites the prior pass missed)
- **`domains/context_prior_speaker.py:27-29`** — Bayes posterior is a HELD
  `Plus([Log(likelihood_c), Log(prior_c)])` Term, "log-domain so the Bayes product
  is an ADDITIVE Term." A per-listener confidence SCALE on the likelihood is a
  common additive log-offset RatioInduce could factor across a population of
  listeners. LOG-DOMAIN; floats ⇒ same integer-observable caveat. Candidate, gated.
- **`domains/asymmetry_currency.py:17-45`** — communication loss in bits =
  `H_post(misjudged) − H_post(calibrated)`, entropy `−Σ p Log p / Log 2` as a held
  Term. A difference of entropies IS a log-ratio, but it's a scalar bits difference,
  not a population of scale-frames — no per-frame multiplicative nuisance to cancel.
  LOG-DOMAIN quantity, but no population shape → not a RatioInduce site.
- **`seeds/log_graph_law.json:9`** — the substrate's own declared law
  ("multiplicative phenomena are additive in log; information −log p, description
  length, perception Weber-Fechner, scale, growth are all natively log"). The
  theoretical warrant for the corrected lens; the substrate's stated worldview.

## BOTTOM LINE (the localising finding, corrected)

The corrected log lens moves TWO sites STRETCH → LIVE on ALGEBRA — CAN grounding
(the marginal genuinely is a log-odds, so cross-frame groundedness genuinely is a
log-ratio cancelling a common field offset) and the Frame primitive (whose weights
ARE explicit log-ratios, the cleanest fit — and which the prior pass missed
entirely). Both are gated by the SAME real constraint, not the fake "wrong algebra"
one: their log quantities are continuous FLOATS in-frame, and the frame/continuum
invariant requires an integer-observable quantum with the ratio held in Hom before
RatioInduce's integer reader can consume them. So the correction is real and it
RELOCATES the blocker: it was never "additive = wrong shape" (inverted); it is "the
log-quantity is not yet integer-observable in-frame" — a wireable gap (a quantized
log-odds / integer relative-weight emitter), unlike the prior dead-end verdict.

The honest guard holds firmly for TWO sites: forecasting regimes are GENUINELY
LINEAR (`mu=(0.0,8.0)` additive AR(1) on integer cells, zero `log` in the stack;
reading them as log-ratios manufactures a product the DGP lacks), and analogy has
NO numeric log axis (symbolic string transform; the missing piece is a magnitude
coordinate, exactly as before).

The value of this pass is the discrimination: additive-in-LOG (CAN, Frame,
context-prior Bayes — logged products, live behind an integer-observable quantum)
vs additive-in-LINEAR (forecasting regimes — a true mean shift, RatioInduce never
applies). Not every additive quantity is a log-ratio; the two that are (CAN, Frame)
are the correction's real yield, and forecasting is the one the corrected lens must
still call linear.

## The recurring gate, and the real next-capability question
Both new LIVE sites (CAN, Frame) and the two gated candidates (context-prior Bayes)
hit the SAME wall: the log-quantity is a continuous float in-frame, and the
frame/continuum invariant demands integer-observable. That is not a defect — it is
the invariant doing its job. It says the reasoning-layer application of RatioInduce
needs one shared piece of machinery: **an integer-observable log-quantum emitter**
(read a continuous log-odds / log-weight at observational resolution as a stepped
integer, the ratio held in Hom). Build that once and CAN grounding, Frame weights,
and Bayes priors all become RatioInduce populations at once. That shared quantum —
not RatioInduce, and not a per-site fix — is the reasoning layer's next-capability
question this assessment surfaces.
