# iter-15 — gold-span GATE + dissimilarity-peak segmenter

Two gated steps on the continuous-speech chunk-consistency bottleneck. Step 1 is a
cheap pre-check: with GOLD word boundaries, is OUR front-end's representation
sufficient (the ~0.3–0.5 within-NN band the SSL + shallow-CNN reached)? Step 2
(only if the gate passes) forward-builds the SOTA unsupervised boundary cue
(dissimilarity-peak = order-1 finite difference) from the agent's own primitives.

**Headline: the gate did NOT cleanly pass, and the segmenter did NOT move
consistency. Honest negative — the bottleneck is not only the boundaries; OUR
representation is itself weaker than shallow-CNN-with-gold-spans on continuous
LibriSpeech.**

---

## STEP 1 (GATE) — OUR front-end + GOLD forced word spans

`scripts/iter15_goldspan_gate.py`. faster-whisper (tiny) word timestamps give gold
word-span boundaries; OUR front-end (gammatone `frames_of` → `invariant_transform`
→ per-speaker CMVN) is sliced at those gold spans; same-word WITHIN- and
CROSS-speaker DTW consistency measured with the iter-14 metric (intra/inter
separation + nearest-neighbour accuracy), shuffle-controlled.

LibriSpeech dev-clean, **10 speakers × ≤16 utts = 160 utts, 1935 gold word
segments, 946 distinct words** (chance ≈ 0.001):

| front-end (gold spans) | within-NN | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|
| INV (per-utt invariant) | **0.198** (shuf 0.024) | +0.198 (shuf −0.048) | 0.014 | +0.123 |
| CMVN (uVTLN+ps_CMVN+PR) | **0.208** (shuf 0.012) | +0.349 (shuf **+0.118**) | 0.007 | +0.039 |

Reference: agent's CURRENT (proportional/landmark) within-NN ~0.13, sep ~+0.11.
SSL + shallow-CNN gold-span ceiling (mine_ssl_goldspan): within-NN ~0.49.

### Gate verdict: **FAIL / marginal** (within-NN 0.208 < 0.22 threshold, < 0.3 target)

Gold spans DO lift within-NN from ~0.13 → ~0.20 and within-sep from ~0.11 → ~0.20
(INV, shuffle-clean) — boundaries matter. **But the ceiling with perfect
boundaries is only ~0.20**, far below the ~0.49 the SSL + shallow CNN reaches with
the same gold spans. So on continuous LibriSpeech the agent's representation is the
*co-limiting factor*, not just the segmentation. Per the pre-registered gate, this
says: do NOT build the segmenter on the premise that "the representation is already
enough and the whole remaining gap is the segmenter."

Two honest caveats on the numbers:
- **within-sep under CMVN is contaminated** (shuffle +0.118, not ~0): per-speaker
  CMVN distorts the intra/inter paired-distance metric. The NN-acc metric stays
  shuffle-clean (0.012) and is the trustworthy one — and it agrees with INV (~0.20).
- A 24-utt smoke run gave within-NN ~0.23–0.29; that was the small-pool optimistic
  reading. At 160 utts / 946 distinct words (the realistic, ~6× harder pool) it
  settles at ~0.20. The larger run is the honest number.
- **Cross-speaker is at chance even with gold spans** (NN 0.007–0.014). Perfect
  word boundaries do NOT buy cross-speaker invariance for this front-end — a
  separate, larger limitation than within-speaker consistency.

---

## STEP 2 — dissimilarity-peak segmenter (built; run for completeness)

The gate did not pass, so by the pre-registered rule Step 2 is not licensed as the
fix. The segmenter was already built and run; reported honestly as a negative.

`domains/dissimilarity_segmentation.py` — the agent forward-builds the SOTA
unsupervised boundary cue (Kamper) from its OWN `order_n_concepts`: a boundary is
a prominence PEAK of the frame-to-frame DISSIMILARITY curve, i.e. the order-1-time
finite difference (change-rate) of the invariant features. Graph-resident boundary
Term (mirrors `forward_segmentation` / `landmark_segmentation`): inter-frame
`DissimFrame` nodes carry `d`/`prev_d`/`next_d`; the boundary set is
`Filter(DissimFrame, f, And(Gt(d,prev_d), Gt(d,next_d), Gt(d, mean_d)))` — an
order-1 sign-change (local maximum) of the change-rate, gated above the utterance's
mean change-rate (derived, not swept), with an optional DPDP min-separation
duration penalty. Verified the `Gt` peak Term evaluates natively in the substrate.

`scripts/iter15_dissimilarity_segmenter.py` — within-speaker probe, per-component
ablation, shuffle-controlled. **12 speakers × ≤20 utts = 240 utts, K=48** (front-end
held fixed at per-utt invariant; only the segmenter varies):

| lever | chunks/word | within-NN | within-sep | sep shuffle |
|---|---|---|---|---|
| BEFORE corpus-TP | — | 0.049 | +0.029 | +0.028 |
| BEFORE landmark-syllable | — | 0.108 | +0.092 | −0.019 (clean) |
| DISSIM all-peaks (no prominence, no dur) | — | **0.111** | **+0.116** | −0.003 (clean) |
| DISSIM prominent (mean-d gate) | — | 0.060 | +0.048 | −0.015 (clean) |
| DISSIM prominent + dur (DPDP) | 0.98 | 0.072 | +0.022 | +0.009 (clean) |
| DISSIM all-peaks + dur | 1.34 | 0.096 | +0.099 | +0.007 (clean) |

### Step-2 verdict: **NO MOVEMENT over BEFORE**

The best dissimilarity variant (all-peaks: sep +0.116 / NN 0.111) is statistically
tied with the iter-14 landmark chunker (sep +0.092 / NN 0.108) — inside noise, not
a gain (the bar was BEFORE + 0.04). All variants are shuffle-clean (no artifact),
so the null is real, not a broken instrument.

Two notes that matter for the science, not just the score:
- The **prominence gate HURT** (sep +0.116 → +0.048): requiring change-rate above
  the mean drops too many true boundaries on continuous speech. The bare local-max
  (all-peaks) is the better cue here — consistent with boundaries not always being
  the most prominent spectral change.
- The duration penalty produced word-scale chunk counts (chunks/word 0.98 with
  DPDP) but did not improve consistency — the chunk *scale* was already roughly
  right; the limiter is the *representation inside the span*, which is exactly what
  the gate diagnosed.

---

## Configuration verdict (the honest bottom line)

1. **Gate**: OUR front-end with gold spans reaches within-NN ~0.20 (shuffle-clean),
   up from ~0.13 with the agent's own segmentation, but well below the ~0.49 SSL +
   shallow-CNN gold-span ceiling and below the 0.3 sufficiency target. The
   representation is **co-limiting**, not sufficient. Cross-speaker is at chance
   even with gold spans.
2. **Segmenter built**: dissimilarity-peak boundary cue composed from the agent's
   `order_n_concepts` (order-1 change-rate local maximum), graph-resident Term,
   natively evaluated.
3. **Within-speaker BEFORE→AFTER**: corpus-TP +0.029 / landmark +0.092 → best
   dissimilarity +0.116 (sep), 0.049/0.108 → 0.111 (NN). Tied with landmark; not a
   shuffle-verified gain. Prominence gate hurts; duration penalty neutral.
4. **Did NOT close** toward the gold ceiling; cross-speaker / recognition NOT run
   (gate did not pass and within-speaker did not move).
5. **Verdict: the dissimilarity-peak segmenter did NOT move within-speaker
   consistency toward the gold ceiling.** And the gate shows the gold ceiling is
   itself low (~0.20) for this representation — continuous speech is NOT just a
   boundary problem here. The honest next lever is the **representation inside the
   span on continuous speech** (the within-span features + cross-speaker invariance
   that gold spans alone do not fix), not a better segmenter.

No tuning; all reported gains are shuffle-controlled and the only positive (gold
spans > agent spans) survives shuffle. `test_stt_pipeline`,
`test_perception_self_assessment`, `test_process_meta_assessor`, `test_gap_guidance`
green (32 passed). Nothing committed.

## Files
- `domains/dissimilarity_segmentation.py` — graph-resident dissimilarity-peak
  segmenter (new).
- `scripts/iter15_goldspan_gate.py` — Step 1 gate (new).
- `scripts/iter15_dissimilarity_segmenter.py` — Step 2 within-speaker probe (new).
