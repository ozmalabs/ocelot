# iter-47 — RICHER TOP-DOWN CONTEXT: bigram -> trigram / 4-gram with backoff

> The enrichment: iter-46 wired the agent's OWN **bigram** transition model
> P(w | prev) as one top-down likelihood node in the SAME variadic
> Argmax-of-product as every audio cue, and proved it lifts continuous recognition
> (+0.055 on the 14-way ctx-covered subset) and **collapses under the word-order
> shuffle** (real sequential context). It also showed "more context -> more lift"
> (14-way > 12-way). The next enrichment is a **LONGER HISTORY**: replace the bigram
> with a **trigram / 4-gram** backed off (Katz/stupid-backoff style) to bigram then
> unigram for sparse contexts. The audio cue-graph (the "hat") is UNCHANGED. Working
> tree only — NOT committed.

---

## (1) What was built — audited

**The n-gram-with-backoff context node.** For a held query word with preceding
history h = (w_{-1}, w_{-2}, w_{-3}, ...) (most-recent-first), the top-down node emits

    P_ctx(w | h)  =  STUPID-BACKOFF mixture of:
                       trigram P(w | w_{-2}, w_{-1})   if that context was SEEN in train
                       bigram  P(w | w_{-1})           backed off with discount lambda
                       unigram P(w)                    final fallback (always present)

- **Pure COUNTS + a fixed backoff discount lambda (0.4)** — Brants et al. 2007
  stupid-backoff. The agent's OWN n-gram transition counts (the sentence_learning
  bigram statistic generalised to a longer history) + Laplace smoothing over the
  candidate lexicon. **NO neural LM, NO fit, NO weight, NO gradient.**
- It enters `enriched_hvpt_accept.heldout_combined` as **ONE extra_lik_channel** —
  identical wiring to the iter-46 bigram. The n-gram ORDER changes only how the single
  likelihood dict is computed; the combine STRUCTURE (the 28-factor product and the
  HAT x CONTEXT peer combine) is byte-identical to iter-46.

**The only new world-adapter code (`scripts/iter47_richer_context.py`):**
- `gather_gold_words_hist` keeps the FULL preceding history (iter-46 kept only one prev
  word); history read from the FULL gold sequence so dropped short words still serve as
  context (the iter-46 fix that gives high bigram coverage).
- `build_ngram_model` counts n-grams up to order N keyed by the k-word context tuple;
  `ngram_likelihoods` emits the stupid-backoff mixture per held query AND the EFFECTIVE
  ORDER actually used (= longest context seen in train) for honest per-order coverage.
- `hist_word_order_shuffle` = the decisive control generalised: permute targets across
  pairs (history positions + target frequency preserved, the history->target link
  destroyed). Every order rebuilt on this must collapse to ~unigram.

Recognition becomes:

    predict(s) = Argmax over the lexicon of  [ bottom-up audio cues x P_ctx(w | history) ]

## (2) Venue + controls

- **Continuous LibriSpeech gold-span words** (faster-whisper forced alignment), held-out
  SPEAKERS (LOSO) — the iter-46 context venue.
- **Comparators per ORDER (2=bigram baseline, 3=trigram, 4=4-gram):** bottom-up vs
  +n-gram (real) vs +n-gram (word-order-shuffle), in both the 28-factor product and the
  HAT x CONTEXT peer combine.
- **Per-order CONTEXT COVERAGE:** the fraction of queries whose full (order-1)-word
  context was actually seen in training (NOT backed off). The trigram context is SPARSER
  than the bigram's; backoff handles the sparse contexts. Reported per order.
- **The WORD-ORDER SHUFFLE per order** — the decisive control at every order.

## (3) Results

_Run in progress — `PYTHONUNBUFFERED=1 python -m scripts.iter47_richer_context 8 50 6 14`,
log `/tmp/iter47_run8.out`. Filled in on completion (pgrep-verified)._

## (4) Verdict

_Pending the complete run._
