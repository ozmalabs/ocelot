# Speech & Language Development — Progress Note

*A research prototype in the gamma-substrate agent ("Jabberwock"). Every result below is earned from scratch and runs with no pretrained speech, language, or vision model in the decision path ("donkey=0"); pretrained tools appear, if at all, only as removable bootstrap scaffolds or eval-only scorers.*

## The claim, in two parts

1. **A capability with an unusual profile:** the system learns grounded word meaning from real children's programming, and learns speech structure from real audio — **from scratch, dynamically, faster than realtime, on a consumer CPU**, with none of the pretrained encoders / GPU training that comparable recognizers depend on. This is a *research prototype at small scale* — the grounded lexicon is a handful of words (small-n) and absolute accuracies are modest; the claim is about the **method and its cost profile**, not about matching a deployed recognizer.
2. **A scientific claim:** the *way* it does so is, at least indicatively, a **model of cognitive development** — it passes through the canonical stages of language acquisition, hits the canonical problems, and solves them the canonical way, in the developmental order, without that order being imposed.

## The developmental stages it traversed

Each is a real problem in child language acquisition; each was reached because the previous stage's limit *made* it the next problem.

1. **Production before perception** — one looped generative model; perceive by inverting your own babble (motor theory).
2. **Perceptual narrowing** — tune to the ambient sound distribution with no labels, *before* word recognition (Werker/Kuhl).
3. **The meaning problem** — sound-form recognition in isolation is a dead end; words must mean things (symbol grounding). *A deliberate check against the child-development literature caught and corrected a wrong turn here.*
4. **Word learning under ambiguity (gavagai)** — cross-situational statistics + joint attention; the world supplies the referent (Yu & Smith; Tomasello).
5. **Meaning reshapes perception** — referential meaning preserves acoustically-weak contrasts that pure sound-learning discards (functional load).
6. **Communication as a two-mind problem** — model the listener, choose an encoding, repair misunderstandings, build common ground (Clark).
7. **Grounding in the real multimodal world** — bind word to object by synchronous joint attention, gated to the ostensive moments inside real footage.
8. **The repetition law** — vocabulary grows through depth of *genuine* repetition, not variety — which is *why* toddler media is relentlessly repetitive. Rediscovered independently.

## Grounding in real children's programming (the capability)

The system streams real children's programming off a media server and learns word↔object meaning from it, using its **own** earned vision (no pretrained vision net) and joint-attention timing:

- On **educational** content it recognises the on-screen referent at **~3× chance**; shuffling the audio–video timing collapses it to chance (joint-attention timing is the signal).
- It grounds where content is **ostensive** (naming shows) and floors on **narrative** — exactly the developmental distinction (children learn from naming, not action montage).
- Vocabulary accumulates through **depth of repetition** — many viewings of the *same* repetitive material — not through variety, and not through re-watching *identical* frames (that is provably inert; the value of re-processing is extracting higher-order structure, not redundancy).

Runs **faster than realtime on a consumer CPU** (~13 minutes of video grounded in ~30 seconds), streaming, incremental, from scratch.

## From words to grammar: the order-N climb (the newest chapter)

Beyond single words, the agent builds structure by composing **orders** — and, importantly, it **authors the composition machinery itself** via its self-build composer (it wrote two graph-native grammatical constructions from framed concerns, not hand-written by us):

- **Order-2** (word↔object binding) and **order-3** (sequence/narrative) composition **rescue grounding on noisy content exactly where per-instance recognition fails** — higher-order structure compensating for a weak foundation.
- **Syntactic bootstrapping** (Gleitman — use the frame "the ___" → noun to infer word category) works on connected speech: the agent **self-identifies the closed class of function words from its own distributional statistics** (0.95 match to real function words, no labels), and the specific frame predicts word category above every control.

### The recurring bottleneck — and its resolution

Across four chapters, one thing gated every higher order: **order-1 word-form purity** — whether repeated instances of a word snap to a *consistent* identity. The resolution came from a precise reframe: **a word-form is a quantized N-dimensional *curve*** (a trajectory through the low-dimensional articulatory manifold), and consistency is a **quantization snap**, not an accuracy dial. Representing each token as its acoustic *trajectory* and quantizing by dynamic-time-warping similarity lifted order-1 purity **0.30 (pooled) → 0.66 (discretized) → 0.93 (curve)**, near the 0.99 ceiling — the single biggest gain in the arc, donkey=0. With that clean foundation the full stack runs end to end:

> raw audio → earned phones → **quantized N-D-curve word-forms** → function/content split → self-identified function words → syntactic frames → syntactic bootstrapping — **all donkey=0, no human labels on the decision path.**

## Why this indicates a true model of cognition

The stages appeared **in the developmental order**; at each the system hit the field's **named problem** and used the **canonical mechanism**; and **none of it was imposed** — each stage's limit forced the next. When a learning system's trajectory converges on the child's — problems, mechanisms, *and order* — without that being built in, the economical explanation is that both are governed by the same underlying structure. That is the sense in which this is, indicatively, a model of cognition.

## Honest scope and open residuals

This is a research prototype at small scale; absolute accuracies are modest and it is not a deployed recognizer. Its result is a *principle* — that speech, word meaning, and grammatical structure can be **earned developmentally and grounded in the world**, cheaply and in real time, and that doing so reproduces the shape of human acquisition.

The three residuals were then each pushed to a decisive, quantified conclusion — every one named to its cause, none "irreducible":

1. **0.93 → 0.99 order-1** — closed as a clean *negative*: the cross-speaker gap is **coarticulation** (the same word differing by sentence context), **not** vocal-tract length. Under a fair rank metric, neither additive normalization nor vocal-tract-length warping improves same-word ranking (a positive control confirms the warp machinery works — it just isn't the dominant factor in real speech). So 0.93 is the **context-free order-1 purity on clean dev-clean under this particular (knob-laden) cluster metric** — a metric-and-corpus-specific number, *not* a proven information ceiling; going higher needs context-dependent (triphone-like) word-forms. *(This also included a self-caught rigor fix: an earlier "gap halved" number was a threshold-picking metric artifact.)*
2. **Syntactic-frame coverage** — **resolved with tractable data**: a two-level word-form (fine trajectory quanta for grounding, distributional super-clusters for frames) plus scale makes the *specific* "the/a → noun" frame beat the generic frame robustly from ~5,000 tokens, well-powered to ~1,800 held-out instances by 50,000.
3. **Category induction** — a quantified, honest fork: the word's own **form** (acoustic + earned morphology) is category-informative and rescues the rare-word tail, but the margin over chance doesn't yet climb solidly with data alone, because content words have a heavy singleton tail (few clusterable types survive). The named lever is a *cleaner order-1* so more distinct content words survive as pure forms — which converges with residual 1.

**The recurring constraint:** across every level — orders 2 and 3, syntactic frames, categories — the binding constraint is the same: **order-1 word-form purity / cross-speaker word-form invariance.** The from-scratch (donkey=0) encoders reach only ~**0.24–0.27 cross-speaker NN-recall** on a fair held-out dev-clean pool — a large, *unclosed* gap.

**A ceiling claim, falsified.** An earlier version of this note claimed 0.93 was the "genuine information ceiling of the acoustic frame — even a borrowed nonlinear network cannot lift it." A decisive fair-pool falsification (see `fair_pool_falsification_results.md`) **overturns that claim.** Scoring three representations through the *identical* NN-recall kernel on *one* fixed pool (3000 held-out tokens), with bootstrap CIs:

| representation | cross-speaker NN-recall [95% CI] | ROC-AUC |
|---|---|---|
| APC (donkey=0) | 0.270 [0.220, 0.320] | 0.763 |
| REF MetricEncoder (donkey=0) | 0.230 [0.183, 0.280] | 0.642 |
| **wav2vec2** (pretrained, eval-only) | **0.817 [0.773, 0.857]** | 0.986 |

The borrowed pretrained network **dominates** — CIs disjoint, gap **+0.55**, even larger than the historical 0.668 quoted at a different pool. So the frame level is **not** at a hard information ceiling: there is large representational headroom (~0.27 → ~0.82) that a learned context-predictive/contrastive frame model captures. What the from-scratch encoders hit is **their own** ceiling under the current objective/scale, not the acoustic frame's.

**What survives, and what doesn't.** The *falsified* half is "the frame cannot be beaten." The *surviving* half is the constructive one: the **orders above** — sequence, syntax, grounding — genuinely compensate for frame-level ambiguity (order-3 rescued noisy order-1 by +0.216), which is how humans understand continuous speech despite acoustic ambiguity. But that higher-order compensation is a *complement* to a stronger frame representation, **not** a proof that a stronger frame representation is unreachable. Closing the fair gap (a matched-compute masked/contrastive frame objective) is now an open, and apparently tractable, build target.

**A live borrowed dependency (segmentation seam).** The flagship word-level results take word spans from **MMS_FA, a pretrained forced aligner** (isolated, eval-only). The *decision path* is donkey=0, but the **input tokenization is borrowed**: the agent does not yet segment its own words in the headline pipelines. A from-scratch alternative — "segmentation-by-reverse-quantization" — is built but is **not wired into the headline pipelines**. Until it is, borrowed word boundaries are a real, standing dependency, and should be read as part of the scope, not glossed over.

The full developmental stack — raw audio → quantized-curve word-forms → function/content split → self-identified function words → syntactic frames → syntactic bootstrapping → self-discovered categories — runs end to end with no human labels on the decision path.

The convergence is the finding; the from-scratch, real-time, CPU-only, learn-from-children's-TV capability is what makes its **cost-and-method profile** unusual. It is a small-scale research prototype, not a deployed recognizer, and — as the fair-pool falsification shows — its from-scratch frame representation is well below what a pretrained network reaches, a gap that is now a concrete build target rather than a claimed ceiling.
