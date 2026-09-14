# Harvest Qwen3.8 — is-a from REPRESENTATION GEOMETRY vs templated elicitation (DIRECTION 2)

## The question

The mechanism-recovery arc (blocks 318-329) asked whether the LLM's structure can
be read off its representations. This run applies that to is-a extraction: is the
hypernymy structure already **linearly present** in the qwen3_5 residual stream,
so that reading the geometry beats the lossy single-token generation read?

**Baseline to beat** (block 337, `scripts/llm_harvest_isa_full.py`): templated
constrained-argmax elicitation gets **0.272 VALID is-a edges** on open-vocab
WordNet nouns, where *valid* = the object is an ANY-level WordNet ancestor of the
subject.

## Method (all additive; no protected file touched, `.so` not rebuilt)

- **Inventory** (`_wordnet_inventory`, `SEED_RNG=0`): 1,200 (child, immediate-parent)
  WordNet noun pairs; the FULL ancestor cone per subject is kept so validity uses
  the same ANY-level-ancestor definition as the baseline. Split **by subject**:
  780 train / 420 held-out (no subject crosses the split). Retrieval candidate
  pool = 956 distinct gold parents.
- **Representation**: one HF forward per distinct word (`hidden_all_layers`),
  last-token hidden state at every layer (0 = embeddings, 1..32 = post-block),
  under the SAME template as the baseline, `"A {} is a kind of"`. Subjects and
  candidate parents are embedded identically. Words may be multi-token; the
  last-token state is used by design (documented). 2,086 words × 33 layers,
  embedded in 5,716 s CPU (~4.4 s/word early, ~1.9 s/word once cache warmed).
- **Readers** (fit on TRAIN, scored on HELD-OUT, per layer):
  - **offset** `δ = mean(parent − child)`; `pred = child + δ`, nearest candidate
    by cosine.
  - **affine** ridge `W: child → parent`; `pred = W·child`, nearest candidate.
  - **probe** logistic on `[child, parent, parent−child]`, true vs false pair →
    separability **AUC**.
  Retrieval `valid@1` uses the baseline's ANY-ancestor definition; `exact@1` is
  the immediate parent.
- **Controls** (must collapse to chance, exactly like the elicitation controls):
  - **random-direction**: replace `δ` with a random gaussian of the same norm.
  - **shuffled-pairs**: permute train parents before fitting `δ` (destroys the
    child↔parent correspondence, keeps the parent marginal).
- **Head-to-head**: templated constrained-argmax elicitation
  (`elicit_isa_batch`) on the IDENTICAL held-out subjects and IDENTICAL candidate
  set.
- **Steering probe** (in-channel, from the "ask the LLM to generate weights"
  steer): read the model's softmax **confidence** over the candidate parents and
  test whether it separates valid from invalid picks (AUC) and whether keeping
  the most-confident half raises validity.

## Results (measured, held-out)

### Head-to-head (identical 420 held-out subjects, validity = ANY ancestor)

| channel | valid@1 | reading |
|---|---|---|
| **templated elicitation (argmax)** | **0.386** | the channel to beat, on this split |
| **geometry best layer (L31, offset)** | **0.255** | worse than elicitation |
| random-direction control (L31) | 0.229 | offset barely clears random |
| **shuffled-pairs control (L31)** | **0.255** | **exactly equals the offset** |
| probe separability AUC (L31) | 0.525 | ≈ chance (0.5) |
| block-337 open-vocab reference | 0.272 | geometry ≈ this, elicitation exceeds it |

**Δ(geometry − elicitation) = −0.131.** VERDICT: **geometry does NOT beat
elicitation — a real negative result.**

(Elicitation scores 0.386 here vs 0.272 in block 337 because this split uses a
956-word candidate pool and a 1,200-pair inventory, not block 337's 8,160-word
pool over 6,000 subjects; the load-bearing comparison is geometry-vs-elicitation
on the *same* split, plus geometry vs the 0.272 reference — geometry loses both.)

### Layer sweep (offset valid@1 with controls; abbreviated)

| layer | offset valid | affine valid | probe AUC | rand ctrl | shuf ctrl |
|---|---|---|---|---|---|
| 0 (embed) | 0.002 | 0.002 | 0.000 | 0.002 | 0.002 |
| 6 | 0.076 | 0.024 | 0.546 | 0.062 | 0.076 |
| 7 | 0.233 | 0.083 | 0.445 | 0.210 | 0.233 |
| 9 | 0.233 | 0.088 | 0.508 | 0.207 | 0.233 |
| 20 | 0.226 | 0.088 | 0.491 | 0.176 | 0.226 |
| 27 | 0.243 | 0.098 | 0.470 | 0.221 | 0.243 |
| 31 | 0.255 | 0.093 | 0.525 | 0.229 | 0.255 |

Full per-layer table: `var/agent2_channel_metrics.json`.

## The controls kill the signal — this is why they matter

At every layer the **shuffled-pairs control equals the offset reader exactly**
(e.g. L31: 0.255 = 0.255). Shuffling destroys the child→parent correspondence but
preserves the parent marginal, so the only thing the offset does is **shift every
subject toward the region of common WordNet hypernyms** (`entity`, `object`,
`substance`, …), which a subject's ancestor cone almost always contains — a
distributional prior, not is-a knowledge. The random-direction control sits just
below (0.229), confirming a small generic-centroid effect, but the child-specific
mapping adds **nothing**. The probe AUC never leaves the 0.45–0.55 band (chance).

This is the same discipline that failed the block-328 concept probe (antonym AUC
0.59, control failed): a reader "scoring" is meaningless until it clears
random+shuffle. Here it does not.

## Honest reading

- **The qwen3_5 hidden states at the layers `HFForward` exposes do NOT linearly
  carry is-a** in a way an offset/affine/logistic reader can exploit above its own
  shuffle control. Hypernymy is not a clean linear/affine offset in this model's
  last-token residual stream (at least under the natural per-word template and the
  last-token-pool choice).
- **Elicitation wins the head-to-head** (0.386 vs 0.255) and also beats the
  geometry reader against the 0.272 reference. The lossy single-token generation
  read is, on this model, a *better* channel than the geometry — the opposite of
  the hypothesis.
- This directly informs the deferred **Plan B numpy mechanism reader**
  (`HARVEST_QWEN38_PLAN_B_MECHANISM_READER.md`): a naive linear read of the
  residual stream is not where is-a lives, so a Plan-B reader should not expect to
  recover is-a from last-token hidden geometry with a linear probe. If is-a is
  recoverable at all it is nonlinear and/or not last-token-pooled.

## The steering finding (bonus, in the Q&A channel)

Prompted by the steer "what if we asked an LLM to generate weights for a subset of
things", I read the elicitation channel's own softmax as a model-generated
confidence:

- **confidence separates valid from invalid picks: AUC = 0.746** (well above
  chance),
- keeping the **top-half most-confident** picks raises validity **0.386 → 0.529**.

So the better lever on THIS model is not a new geometric channel but **confidence-
weighting the existing Q&A channel** — which is exactly DIRECTION 1's remit. This
is reported here only as a cross-check; the geometry direction's own answer is the
negative result above.

## Artifacts

- `scripts/llm_geometry_isa_channel.py` — the run (additive, non-protected).
- `var/agent2_channel.log` — full run log + summary.
- `var/agent2_channel_metrics.json` — per-layer sweep + head-to-head + controls.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only, no
  Rust rebuild). Script never enters a substrate path.
- Protected READ-ONLY files untouched (`can_ops.rs`, `can_junction_tree.py`,
  `can_native_bp.py`, `model_reader.py`).
- Model / venv / nltk_data under `/applications` — NOT committed; run log +
  metrics under `var/` (git-ignored). Nothing committed by this agent.
