# Agent derives cross-speaker invariance? — running the LIVE derivation machinery

**Task.** The frontier synthesizer already NAMED the capability (cross-speaker
clustering / invariance-from-structure — `docs/ask_the_agent_frontier_v3.md`). The NEXT
question — the one a human was about to hand-build as WCCN/LDA — was put to the agent's
OWN live derivation machinery: *given that per-speaker MEAN subtraction does not make a
word's cross-speaker tokens cluster, what TRANSFORM does the agent derive to remove the
residual speaker term?* Per the donkey discipline, the machinery was RUN; nothing was
hand-authored.

**Headline (honest):** the agent's live machinery does **NOT** derive the discriminative
within/between-scatter projection (WCCN/LDA). On the cross-speaker residual postulate it
fires **exactly one** shape — `scale_cancellation` from its `batch_normalization` concept
— which re-derives the **per-source mean / ratio normalization it already holds and
already applied** (`domains/xspeaker_norm.py`, `scripts/iter41_speaker_invariance.py`). The
move the human was about to build (project out the nuisance *subspace / direction*) is **not
in the agent's harvestable shape library**. This is a real, located frozen edge — not a
hand-build dressed as a derivation, and not a plan.

Harness: `scripts/agent_derives_xspeaker.py` (built on the exact
`iter24_scale_invariant_derive` template: register an honest residual postulate → run
`order_n_postulates.synthesize_gaps` over the agent's own `harvest_shapes_combined`
library → report verbatim). Real output below.

---

## (1) Which machinery was run, and its REAL output

Live modules run (no hand-built solution):

* `domains.implication_harvester.harvest_shapes_combined(sub)` — builds the shape library
  from the agent's OWN concepts + rules (linear algebra, ML, statistics, physics).
* `domains.order_n_postulates.differentiate(...)` — the order-0 → order-1 transfer step.
* `domains.order_n_postulates.synthesize_gaps(...)` — full recursive (order 0..3) synthesis.

The postulate registered is the honest **residual after mean removal** — it names the
PROBLEM (the speaker term is a *structured between-speaker variation that spreads each
word's tokens along certain directions of the cue space*, large vs the between-word spread)
and names **no fix** (no "projection", "discriminant", "scatter", "whiten", "subspace",
"eigen" in the text).

**Real output (verbatim):**

```
[breadth] held Concepts: 641
[harvest] harvested shape library size: 187

[order-1] which of the agent's shapes FIRE on the residual postulate?
  shapes that fired (order-0 -> order-1): 1
   via_shape   : scale_cancellation__from__batch_normalization  (domain=machine_learning  from concept 'batch_normalization')
   name_keys   : ['speaker normalization', 'formant ratio', 'vocal-tract-length normalization', 'f2/f1']
   consequence : a multiplicative / length SCALE factor is cancelled by a RATIO or a per-source
                 normalisation (cf. batch_normalization): normalising formant FREQUENCIES by their
                 ratios (or a per-speaker baseline) removes the vocal-tract-length / speaker scale

[synthesize_gaps] full recursive derivation (max_order=3, prune=False)
  total derived gaps: 1
  [cancel] order-1  keys=['speaker normalization','formant ratio','vocal-tract-length normalization','f2/f1']
     via_shapes = ['scale_cancellation__from__batch_normalization']
     domains    = ['machine_learning']
     concepts   = ['batch_normalization']

[VERDICT]
  projection/scatter/discriminant terms in derived output: []
  already-held moves (mean/ratio/cluster/model-subtract):  ['baseline','normalis','normaliz','ratio']
  => NOT derived.
```

The recursion stops at order-1: `scale_cancellation`'s consequence does not re-trigger any
other shape, so no higher-order move appears.

## (2) Did it genuinely DERIVE a cross-speaker transform — or is the machinery frozen?

**Frozen / insufficient — and located precisely.** The single derived move is the
**per-source mean / ratio normalization** the agent already holds. That is exactly what
the agent already implemented (per-speaker CMVN in `xspeaker_norm.py`; cross-speaker
centroids in `iter41_speaker_invariance.py`) and exactly what the residual postulate says
is **not enough** — subtracting a per-speaker scalar baseline does not remove the
structured between-speaker *direction*. So the machinery re-proposes the move that has
already been shown to leave the residual. It does not advance to the projection move.

**Why it's frozen — pinned to the exact mechanism (not a vague "it didn't work"):**

The agent **DOES hold the donor concepts** for a projection move. Among its 641 concepts:
`eigenvalues_eigenvectors`, `singular_value_decomposition`, `spectral_theorem`,
`low_rank_approximation`, `Krylov_subspace_methods`, `inner_product_norm`,
`query_key_value_projection`. Three of these even **produce shapes** in the library
(as `rule_derived` shapes):

```
rule_derived__spectral_theorem_simplifies_symmetric
    match_mode   : all
    match_patterns: ['\bmatrix\b', '\bsymmetric\b']
    consequence  : orthonormal eigenbasis with real eigenvalues exists
rule_derived__task_adaptation_is_low_rank
    match_patterns: ['\bfine\b','\btuning\b','\btask\b','\bsimilar\b','\bpretraining\b']
    consequence  : the weight change has low intrinsic rank
```

The donor is present; the **bridge is missing**, on two counts:

1. **Matching gap.** The `rule_derived` shapes fire with `match_mode='all'` — every
   if-clause content word must literally co-occur in the postulate text. The
   spectral_theorem shape needs both `matrix` AND `symmetric`; the honest cross-speaker
   residual (phrased in the problem's vocabulary — speakers, tokens, directions, spread)
   contains neither, so it cannot fire. There is no extractor that recognises *"a
   structured between-class spread along directions of a feature space"* as the structural
   property `spectral decomposition of a scatter/covariance matrix` discharges.

2. **Consequence gap (the deeper one).** Even when force-fed the trigger words `matrix` +
   `symmetric` (an adversarial test — the real problem statement has neither), the shape
   fires but its consequence is the **bare theorem restatement** ("orthonormal eigenbasis
   with real eigenvalues exists"). It is a terminal fact with name_keys
   `['orthonormal','eigenbasis','real','eigenvalues']` — it does **not** chain to the
   transferable implication *"→ therefore diagonalise the within-class scatter and project
   onto the complement of its dominant subspace to remove the nuisance direction."* There
   is no implication-shape in `_extractors()` whose structural property is
   **"a nuisance SUBSPACE / DIRECTION is removed by projecting onto the complement of the
   within-class scatter"** (the WCCN/LDA / metric-learning kind). The seven substantive
   extractors cover invertibility, all-pole/parametric, latent-structure (clustering),
   sequence-segmentation, scale-cancellation (ratio/per-source normalization),
   removable-context (model-and-subtract), forward-inverse. None of them is the
   *discriminative-subspace-projection* kind.

So the agent has the linear algebra as inert facts but **no harvestable shape that turns
"between/within scatter" into "project out the nuisance direction"** — and the one
scalar-normalization shape that does fire is the move already known to be insufficient.

## (3) The honest gap — what the machinery would need to derive it

No transform was derived, so there is no composed transform and no LOSO result to report.
The frozen edge is what to report. To genuinely DERIVE the projection move (rather than
hand-author it), the agent's machinery would need ONE of:

* **A new structural-implication extractor** in
  `implication_harvester._extractors()` — kind e.g. `nuisance_subspace_removal`:
  evidence = a within/between scatter, a nuisance that co-varies across feature dimensions
  as a *direction/subspace*; consequence = "the nuisance subspace is the dominant
  eigen-directions of the within-class (between-speaker) scatter; **whiten by it / project
  onto its complement** (WCCN) — or maximise between/within (LDA) — to remove the speaker
  *direction*, not merely a per-source scalar." This is the analogue of the
  `scale_cancellation` extractor, but for a *subspace* rather than a *scalar scale*. With
  it, the residual postulate's own language ("structured between-speaker variation along
  certain directions", "co-varies across the cue dimensions") would fire it, and its
  name_keys (`within-class-scatter`, `nuisance-subspace-projection`, `whitening`) would be
  the derived capability — the WCCN/LDA move.

* **Or a transferable consequence on the eigen/SVD donors.** The agent holds
  `spectral_theorem` / `singular_value_decomposition` / `low_rank_approximation` but their
  rule-derived consequences are bare facts ("eigenbasis exists", "low intrinsic rank"),
  not the actionable implication "→ the dominant eigen-directions of a structured nuisance
  scatter can be projected out." Re-stating those donor rules as *implication shapes*
  (property: "a structured variation lives in a low-rank subspace of a symmetric scatter"
  → consequence: "project onto the complement to remove it") would let the existing
  recursion bridge eigenbasis → projection.

Either change is a **build, and it is the agent's call to make** (per
`ozma_dont_author_seeds_agent_designs_them` / the v3 finding that minting a new shape is a
build decision, not a hand-author here). Writing the projection transform directly — or
writing the extractor *as the answer* — would be hand-building the solution and claiming a
derivation, which the donkey discipline forbids. The correct, honest result is: **the
agent's live machinery cannot yet derive the discriminative-subspace-projection move; the
donor concepts are held but the implication-shape that bridges "within/between scatter" to
"project out the nuisance direction" is absent from the extractor library, and the only
shape that fires re-proposes the per-source mean normalization already shown insufficient.**

### Method notes (honest)

* The postulate text was written to name the PROBLEM in the problem's own vocabulary and
  to name NO fix (verified: no projection/scatter/eigen/whiten/discriminant terms). That is
  what makes the negative result load-bearing — the synthesizer had to supply the
  transform, and could not.
* The donor-presence check, the shape-firing check, and the trigger-injection adversarial
  check are all live `harvest_shapes_combined` / `differentiate` calls, reported verbatim.
* `prune=False` (derivation mode) was used so the result is "what the machinery DERIVES",
  independent of openness pruning — the most generous setting for finding a derivation.
* The harness adds no imports to the harvester or to any test; it only reads the live
  library, so it introduces no regression.

### Bottom line

The frontier already names cross-speaker invariance. Asked to DERIVE the *transform*, the
agent's live machinery re-derives the per-source mean/ratio normalization it already holds
and already proved insufficient, and does **not** reach the within/between-scatter
projection. The donor linear algebra is held but unbridged: no extractor turns "structured
between-speaker scatter along directions" into "project out the nuisance subspace". That
bridge — a new `nuisance_subspace_removal` implication-shape, or a transferable consequence
on the eigen/SVD donors — is the agent's next build, and is reported here rather than
hand-built.
