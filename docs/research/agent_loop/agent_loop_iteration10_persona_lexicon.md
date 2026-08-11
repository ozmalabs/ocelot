# Autopoietic loop — iteration 10 (ground the cross-speaker lexicon on the persona world)

Turn the crank a tenth time on the LAST inadmissible link of the recognition
structure. iter-9 left it precisely located: perception / units / invariance /
word-scale-chunking all CROSSED; the one broken link is the **cross-speaker
lexicon**, which retrieved only at the frequency prior because the held-out
LibriSpeech corpus was **corpus-starved** — at 22-60 utts there was almost no
cross-speaker word REPETITION to learn a speaker-invariant chunk→word map from.
The binding constraint was **missing evidence in the data**, not a missing
algorithm.

This iteration removes that constraint with the agent's own
`persona_speech_world`: the agent CONTROLS many speaking personas (distinct
f0 / Q / vocal-tract length) and CHOOSES the words, so it can MANUFACTURE the
cross-speaker repetition real held-out data lacked — every persona says every
word in a small controlled vocabulary. If the lexicon learns the
speaker-invariant chunk→word map from that repetition, the last link becomes
admissible and the recognition structure completes (the "switch-on").

## Honest headline

**The data constraint is gone, but the structure did NOT switch on — it is
necessary-but-not-sufficient, and the binding sub-issue is now the METRIC
(the rate-invariant trajectory-shape chunk distance), exactly as the task framing
anticipated.** The repetition is now rich (390-403 cross-speaker multi-member
chunks vs iter-9's 4-19); the lexicon DOES retrieve the right words above the
frequency-prior on most runs (content-recall 0.31-0.38 > freq-control 0.20-0.28
in 2 of 3 seeds). But word-accuracy stays pinned at the unigram/chance floor
(0.125-0.156 vs unigram 0.125), because the chunk-similarity metric ceilings word
identity at ~0.5 EVEN with oracle labels. More repetition did not raise lexicon
purity (0.25 starved → 0.21-0.24 rich) — the wall moved from the data to the
representation. I did NOT tune to cross; the freq-matched control is computed in
the same breath and kills the crossing on 1 of 3 seeds.

## The build (world adapter — `scripts/iter10_persona_lexicon.py`)

Python only voices the personas (the I/O boundary) and measures. The recognition
CHAIN is the agent's own forward build (CSR): perception → invariant transform →
word-scale chunking (corpus-TP, iter-9) → cluster lexicon (the agent's composed
cross-speaker clusterer). No agent reasoning in Python, no tuning to cross.

1. **Corpus with repetition.** 8 personas (a child → a deep voice, distinct
   f0 / Q / vtl) × 8-word vocabulary (`one three five seven nine two four eight`)
   × 4 reps = 256 single-word utterances. Each `speak_as` re-voices a word the
   agent was taught (from FSDD clips) in a persona's voice + a ±4% per-rep f0
   jitter (a natural repetition, never byte-identical). Each word now recurs
   across MANY speakers — the cross-speaker evidence the lexicon was starved of.
2. **Full improved stack** per utterance: perception → `invariant_transform`
   (default) → word-scale chunking (`CORPUS_TP`, the corpus-wide TP from iter-9).
3. **Ground the cross-speaker lexicon** = the agent's `ClusterLexicon`
   (`cross_speaker_clustering.cluster` over pooled trajectory vectors, k = #vocab).
4. **Recognise held-out** — either held-out PERSONAS (speaker-independent, the
   whole point) or held-out REPETITIONS (same speakers, new utterances).

## Measure (LIVE — real numbers)

### Held-out PERSONAS (speaker-independent), 8×8×4, seed 1

```
chunks/word ratio    : 2.03
lexicon purity       : 0.205   (multi-member 0.205 over 390 cross-speaker chunks)

WORD ACCURACY (position-aligned):   agent 0.125   unigram 0.125   chance 0.125
CONTENT-WORD RECALL (position-free): agent 0.312  unigram-set 0.125  freq-ctrl 0.200
  word-acc crosses unigram : NO  (0.125 vs 0.125)
  recall crosses freq-ctrl : YES (0.312 vs 0.200)
>>> NOT YET
```

### Held-out REPETITIONS (same speakers), 8×8×4, seed 1

```
chunks/word ratio    : 2.11
lexicon purity       : 0.212   (multi-member 0.212 over 405 cross-speaker chunks)
WORD ACCURACY:        agent 0.141   unigram 0.125   chance 0.125
CONTENT-WORD RECALL:  agent 0.312   unigram-set 0.125   freq-ctrl 0.233
>>> NOT YET
```

### Reproducibility across seeds (held-out personas) — the honest control

```
seed  multi_chunks  purity  word_acc  unigram  content_recall  freq_ctrl   recall-crosses?
  1       390        0.205    0.125     0.125       0.312         0.200          YES
  2       396        0.242    0.156     0.125       0.234         0.249          NO
  3       403        0.233    0.141     0.125       0.375         0.279          YES
```

The multi-chunk count (390-403) and purity (0.21-0.24) are stable. The
content-recall-vs-freq-control crossing holds in 2 of 3 seeds and FAILS in 1.
word-acc never crosses unigram. **The crossing is not robust — necessary, not
sufficient.**

### Before (starved) → after (repetition-rich) — does the repetition help?

```
config                                   multi-chunks   multi-purity
STARVED   (3 personas × 8 words × 2 reps)      75          0.253
RICH      (8 personas × 8 words × 4 reps)   390-403        0.21-0.24
```

The repetition multiplied the cross-speaker evidence **5×** (75 → ~400
multi-member chunks) — the corpus-starvation iter-9 identified is genuinely
removed. But multi-member purity did NOT rise; it slightly fell. **More
cross-speaker evidence did not buy a cleaner map.** The wall moved off the data.

### Where the wall actually is — the metric ceiling (the decisive probe)

Strip the chunker out and ask the metric directly: take WHOLE-utterance
trajectory vectors (1 chunk = 1 word, no over-segmentation) and measure how well
the chunk-similarity embedding separates the 8 words across personas.

```
1-NN same-word rate (rate_inv embed)        : 0.492   (chance 0.125)
1-NN same-word rate (traj embed)            : 0.492   (identical)
ORACLE-centroid acc, WITH labels (rate_inv) : 0.512   (the best case the metric can give)
ORACLE-centroid acc, WITH labels (traj)     : 0.512
whole-utt cluster purity, k=8 / 16 / 24 / 32: 0.336 / 0.406 / 0.441 / 0.480
```

Even with **oracle labels** and no over-segmentation, word identity ceilings at
~0.51 on the agent's OWN speech. The fixed-length trajectory-shape embedding
(both `rate_inv` and `traj`, which coincide here) captures ~half of word identity
across personas — well above chance, far from clean. This is the binding
sub-issue: **the rate-invariant chunk-distance metric, not the corpus.**

## Reading the numbers honestly (the admissibility verdict)

1. **The corpus-starvation constraint is REMOVED.** 390-403 cross-speaker
   multi-member chunks (iter-9 had 4-19). The persona world manufactured exactly
   the repetition real held-out data lacked. Real, reproducible.

2. **The lexicon retrieves above the prior — sometimes.** content-recall
   0.31-0.38 beats the freq-matched control on 2 of 3 seeds (and beats the
   unigram set every time). So the speaker-invariant map carries *some* genuine
   word-identity signal. But it is NOT robust to the honest control.

3. **word-accuracy does NOT cross unigram (0.125-0.156 vs 0.125).** Two faults
   compound: over-segmentation on these short single-word utterances (2.0
   chunks/word, so position-aligned scoring is off), and the 0.51 metric ceiling.
   Position-aligned recognition sits at the floor.

4. **The last link did NOT become admissible.** With the data constraint
   removed, the result is **necessary-but-not-sufficient**: the persona world
   proved the lexicon CAN see cross-speaker repetition, but the chunk-distance
   metric can't turn that repetition into a clean enough chunk→word map to cross
   the prior. **No switch-on.**

5. **The synthetic→real transfer is a SEPARATE further step.** Even had it
   crossed here, a crossing on the agent's OWN synthesised personas would show
   the last link's MECHANISM works on self-speech — not that it transfers to real
   recorded speakers. We did not reach the crossing, so this caveat is moot but
   stated.

## Controls / honesty

- **Did I tune to cross?** No. Vocabulary = 8 FSDD digits (fixed). Cluster k =
  #distinct vocab words (the natural target, not swept). Per-rep f0 jitter ±4%
  (a fixed natural-repetition amount, not searched). `CORPUS_TP` on (iter-9
  default for word-scale chunking). No threshold tuned to pass a metric.
- **The freq-matched control killed the crossing on seed 2.** The content-recall
  beats the unigram set on every seed — which alone would read as "above
  baseline" — but the frequency-matched random draw (20-draw average) recalls
  MORE on 1 of 3 seeds. The control is reported plainly; the crossing is not
  robust.
- **The oracle-centroid probe is the decisive honesty move.** It removes BOTH
  clustering noise and over-segmentation (labels + whole-utterance) and still
  ceilings at 0.51 — proving the loss is the metric, not the lexicon builder or
  the chunker, and not the corpus.
- **Stable numbers reproduce:** multi-chunk count 390-403, purity 0.21-0.24,
  word-acc 0.125-0.156, oracle-centroid 0.512 reproduce across seeds.

## The located next constraint (iteration-11)

The recognition wall is now precisely: **the cross-speaker chunk-similarity
METRIC ceilings word identity at ~0.5 on the agent's own speaker-invariant
speech.** The corpus is no longer the wall (iter-9's verdict is retired); the
fixed-length trajectory-shape embedding is. Two forward paths, both the agent's:
- **A richer chunk-identity descriptor than the resampled trajectory.** The
  order-0 path + order-1 velocity over normalised time captures ~half of word
  identity; the agent's `order_n_concepts` already composes higher orders
  (order-2 curvature) and its `analogy` / `feature_generator` can transfer the
  formant-RATIO and band-vs-band descriptors it invented for FSDD onto the chunk
  level — features the trajectory-shape distance throws away.
- **Fix the over-segmentation on short utterances.** corpus-TP chunking is built
  for continuous speech; on single-word utterances it splits ~2:1. The agent's
  own statistical_learning science says a single word has no internal TP trough —
  so the corpus-TP should self-terminate at 1 chunk for these. The interaction of
  word-scale chunking with very short utterances is the secondary sub-issue.

## Status / acceptance

- **(1) the persona corpus:** built — 8 personas × 8 words × 4 reps = 256 utts,
  390-403 cross-speaker multi-member chunks (iter-9 had 4-19). The evidence
  exists now.
- **(2) lexicon purity before→after:** starved (75 chunks) 0.253 → rich (400
  chunks) 0.21-0.24. The repetition multiplied the evidence 5× but did NOT raise
  purity — the wall moved off the data.
- **(3) word-acc vs unigram + freq-matched control:** word-acc 0.125-0.156 vs
  unigram 0.125 — **did NOT cross.** content-recall 0.31-0.38 vs freq-control
  0.20-0.28 — crosses on 2 of 3 seeds, NOT robust. Real numbers, controls hold.
- **(4) configuration verdict:** **NO switch-on.** The last link did NOT become
  admissible. With the corpus-starvation constraint removed, the result is
  **necessary-but-not-sufficient**: the data was necessary (and is now present),
  but the rate-invariant chunk-distance METRIC is the final sub-issue (oracle
  ceiling 0.51). This is exactly the outcome the task framing flagged as
  possible. The synthetic→real transfer is a separate further step, not reached.
- `test_stt_pipeline` + `test_perception_self_assessment` +
  `test_process_meta_assessor` + `test_gap_guidance`: **32 passed** (the script
  is a new world adapter; no default behaviour changed).
- Not committed; left in the working tree + this doc.

### Reproduce

```
# held-out personas (speaker-independent) and held-out repetitions
python -m scripts.iter10_persona_lexicon 4 personas
python -m scripts.iter10_persona_lexicon 4 reps

# reproducibility + the freq-control across seeds
python -c "import scripts.iter10_persona_lexicon as IT; \
  [print(IT.run(4,'personas',seed=s,verbose=False)) for s in (1,2,3)]"

python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q     # 32 passed
```
