# The Reading Arc (runs 61–83) — reading handwriting at a human-equivalent level

*Consolidation, 2026-07-07. The continuation of OMNIGLOT_ARC.md, from
isolated-glyph recognition to a validated, human-mechanism reading model.
Every run gated, committed, donkey=0. Paused pending word-weighting on the
forward model (see "The pickup point").*

## The arc in one breath

Cursive reading started this arc as a reported *boundary* — floored at 0.7%
word / ~18% char, and I called it a training-free wall (run 67). It was not a
wall; it was a chain of wrong framings. A research spike plus a cascade of
creator reframes dissolved it: the reading *quantum is the word, not the
letter*; reading is *prediction-dominant with a loose, robust visual*; the
*visual ceiling is not the reading ceiling*; and the recurring bottleneck under
everything is *fast adaptation to a new hand*. What came out is a reading model
that reproduces **three independent human signatures**, a **complete
decomposition of writer-adaptation**, and reading **unified into the
jabberwock's own language faculty** — with the remaining lift localized to one
precise, named capability.

## 1. The reframe cascade (how a "boundary" became a solved model)

- **The boundary (62–67).** Per-letter cursive recognition floors ~18% char
  across every recognizer (per-stroke, raw SC+TPS, parse-marginal) and every
  lever (writer-adaptive allographs, Fisher weighting, trie-beam). Localized to
  the per-letter geometric signal itself: cursive letters are near-identical in
  shape (same-letter distance 0.205 vs different 0.235).
- **The research spike.** The Bayesian Action-Perception model (Gilet/Diard/
  Bessière 2011) — a *training-free* motor recognizer — scores 93% within-writer,
  50% cross-writer. Our floor was the human/BAP **cross-writer bottom-up limit**,
  not a failure. Humans read cursive with a *weak* per-letter channel rescued by
  a top-down loop; the fix is not a stronger eye.
- **Writer-relative pose (69) — the breakthrough.** Runs 62–67 used a
  rotation/scale-*invariant* representation, discarding pose. But pose (baseline,
  slant, x-height) in the *writer's own frame* is the discriminative signal
  invariance throws away. Re-admitting it lifts within-writer cursive char
  15%→55% — the reframe validated, the arc turns.
- **The word quantum (74).** Reading isn't letter-by-letter; the word is the
  unit. Whole-word holistic matching crushes per-letter within-writer (70% vs
  20%). Mostly coarse word-shape (the easy majority); hard anagrams need context.
- **Prediction-dominant + loose visual (75) — the gold.** The jumbled/misspelled/
  wrong-word phenomena prove reading is *strong prediction × loose visual*.
  Sentence context lifts reading 26%→57% with a toy bigram; the loose (open-
  bigram) visual is transposition-robust where strict breaks. The ~55% visual
  was never the bottleneck — the starved prediction channel was.

## 2. The reading model

**Training-free visual + rich language prior — the human stack.** A loose,
from-scratch eye that only has to *rank* a predictor's guesses; a strong
predictor that dominates. Writer-adaptation makes the loose visual *usefully*
loose (writer-consistent), not sharp. Whole-word gesture for the easy majority;
prediction for the hard, ambiguous minority. This is not "read with no language
knowledge" (no human does that) — it is the visual novelty (donkey=0) plus the
language prior humans spend a lifetime learning.

## 3. The three human signatures (the validation)

The model reproduces, on demand, three independent non-obvious facts about human
reading — the strongest evidence the model is *right*:

1. **Jumbled-word robustness (75).** Transpose interior letters and the loose
   visual holds (51.2%) where the strict one breaks (42.6%). The transposed-
   letter effect, in the machine.
2. **Proofreading-blindness (75).** The reader reads the *predicted* word over
   correct-but-surprising ink — "more" over ink reading "push" — on a dial:
   override 71%→0% as visual weight rises. Getting the ink "wrong" in the
   human sense is the signature that prediction dominates.
3. **Skill–speed coupling (83).** "Better cursive readers are faster readers":
   accuracy and confirm-fraction move together (r = +0.90–0.99), both rising as
   the register fills. One dial — prediction strength — drives both.

## 4. The fast-adaptation map (the meta-problem, fully decomposed)

Every win in the arc is *within-writer* (already adapted); every failure is
*cross-writer* (cold). The meta-problem is **fast adaptation to a new hand**, and
runs 77–80 mapped it completely:

- Reliable seeds exist (77: prediction-dominant harvest, 77.6% precision vs run
  73's 29%).
- Accumulation is sample-*efficient* for seen letters but **cannot** generalize
  to unseen ones (79, proven analytically: exemplar fusion has flip-to-right = 0).
- A **hand-transform** generalizes to all classes — pose alone, no labels, gives
  +20pp across the whole alphabet (79) — but pose is ~the transform ceiling; a
  richer shared style adds only a few points (80). The last stretch (35→55%) is
  per-letter idiosyncrasy that needs coverage, not a transform.

**So adaptation = a free pose-transform (15→35%, all classes, instant) +
harvest-accumulation (35→55%, per-letter, covered classes only).** The adapted
per-letter visual ceiling is ~55%.

## 5. The jabberwock reads with its own mind (82) — and the anticipation gap

Reading was unified into the jabberwock's native faculty: `predict_context_term`
+ `semantic_reading_context` (its own graph-native word-superiority mechanism)
reads the handwriting and beats the external bigram on real IAM (cross p=0.016),
donkey=0, no external model. But a sharp finding underneath: **rich comprehension
≠ rich prediction.** The deep faculty (sense selection, construction grammar, the
cortices) *comprehends* known words; it does not *anticipate* the next one. The
one predictive interface is order-1 (bigram-equivalent). The AbS predictive
reader (83) is richer in context *breadth* but emits an **unordered set**, not a
scored-directional next-word prediction — so it beats bottom-up but not the
ordered bigram. The missing capability is **anticipation made scored and
directional**.

## The numbers (honest, live anchors)

| stage | within-writer | cross-writer | notes |
|---|---|---|---|
| per-letter cursive floor (64) | — | ~18% char | every recognizer, every lever |
| writer-relative pose (69) | 55% char | 29% char | the breakthrough |
| whole-word holistic (74) | 70% word | 19% word | sight-vocab, coarse-shape driven |
| prediction-dominant, synthetic (75) | 57.5% word | — | +31pp from a toy bigram |
| full model, real IAM (76) | 13% word | 7% word | cross-corpus visual confound |
| native faculty, real IAM (82) | 15.6% word | 13.1% word | jabberwock's own mind, beats bigram |
| adapted per-letter visual ceiling | ~55% char | ~50% (BAP) | fast-adaptation map complete |

**Honest bottom line.** Within-corpus, adapted, the model reads ~50–70% word
(synthetic/holistic) — a real training-free capability up from a 0.7% floor.
Real-IAM sits at ~13–16%, depressed by a *cross-corpus* visual (a DeepWriting
bank on IAM ink), not a fundamental wall. Human-level (90%+) is not reached.
Deep-net IAM systems at 5–10% WER do something (trained per-frame posteriors) we
do not, and we do not compete with them. The value here is the *science*: the
reading model, the three human signatures, and the fast-adaptation
decomposition.

## The pickup point — word weighting on the forward model

The prediction channel is fully mapped and the lift is localized to **one**
capability. Runs 81–83:

- run 81: a capable LLM would be the rich directional predictor — blocked by
  local resources (30B OOMs, no API), untested.
- run 82: the native `predict_context_term` faculty is order-1.
- run 83: the AbS predictive reader is richer in breadth but emits an
  **unordered set** — no P(next | context). It beats bottom-up, loses to the
  ordered bigram, and collapses toward a frequency prior.

The gap is precise: **the forward model (the production faculty run forward as
the reader's predictor) needs to emit a *scored, directional* prediction over the
word lattice — P(next word | context) — not an unordered set.** That is exactly
**word weighting on the forward model**. When the forward model carries word
weights (directional, scored), the AbS reader's prediction becomes a real
next-word distribution, the loose visual ranks *against a strong ordered
predictor*, and the rich lift run 83 could not reach should materialize —
without an external LLM, in the jabberwock's own faculty.

**When word-weighting lands, re-run the run-83 attach** (handwriting visual →
the now-scored-directional forward-model prediction), measuring the lift against
the bigram (57.5 / 13.1) and run-82 order-1 (59.1 / 15.6), plus the confirm-
fraction and the skill–speed correlation. That is the resumption point.

## Discipline (held throughout)

donkey=0 (no trained nets on the visual/decision paths; the language prior is the
sanctioned rich component, per the human architecture). The `seeds/
stroke_shapes.json` seed guard (md5 `b9615a2bac21dbb14f7357ae240a958c`) held
unchanged across all 23 runs. Every run gated, powered where it mattered
(Wilson CIs, McNemar, count-matched nulls), committed, with honest anomalies
recorded. The parallel session owns `domains/` + `seeds/` (the language faculty);
this arc's runs read them but never modified them.
