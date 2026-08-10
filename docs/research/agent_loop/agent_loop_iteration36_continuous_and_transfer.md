# Iteration 36 — move the recognition GRAPH to CONTINUOUS speech + test the back-transfer to digits

> User prediction: on DIGITS the orthogonal cues (AxS, formant, manner) were
> informationally REDUNDANT (the bottom-up already nails arbitrary digits, so the
> digit task plateaued ~0.590 at iter-34). On CONTINUOUS speech the bottom-up FAILS
> (coarticulation / cross-speaker / segmentation), so the SAME cues become
> informationally COMPLEMENTARY — they catch the bottom-up's errors. And cues that
> catch the continuous bottom-up's errors should ALSO catch the DIGIT hard-fold
> errors (yweweler / lucas, where the digit bottom-up breaks cross-speaker) → drive
> up the digit mean. The whole (continuous) drives the slice (digits).
>
> Builds on iter-34 (`docs/agent_loop_iteration34_enriched_graph.md`, the 23-node
> enriched graph, digit n=8 0.590) and iter-35 (`docs/agent_loop_iteration35_axs_node.md`,
> the single-pass no-fit AxS node — REAL but REDUNDANT on digits, drop-it −0.002).
> Written INCREMENTALLY; runs captured to `/tmp`; `PYTHONUNBUFFERED=1`. NO commit.

## THE MECHANISM UNDER TEST

iter-35's refinement: orthogonal-in-MECHANISM ≠ orthogonal-in-INFORMATION. The
richness lever is monotone only for INFORMATIONALLY-complementary cues. On the
held-out-voice DIGIT task the bottom-up 1-NN already captures what inverting `speak()`
recovers, so AxS adds nothing (−0.002 drop-it). iter-35 BANKED the AxS + top-down
pathway for "a HARDER VENUE where they catch different errors." This iteration IS
that venue: CONTINUOUS gold-span words, cross-speaker.

Two questions:
- **(A)** does the graph pay off on CONTINUOUS where it was redundant on digits — do
  the AxS / formant / manner cues become COMPLEMENTARY (positive drop-it) when the
  bottom-up fails?
- **(B)** does the continuous-forced cue set DRIVE UP the digits — does the digit n=8
  mean rise above iter-34's 0.590, esp. the hard folds (yweweler, lucas)?

## NO-DONKEY contract

The SAME enriched recognition graph — `domains/many_settings_recognizer
.predict_many_settings_term` (the variadic Argmax-of-product), the agent's owned
cochlear settings + FFT-ear + formant-relation + manner/voicing + single-pass AxS
nodes — applied to CONTINUOUS gold-span words by feeding the iter-34/35 `build_fold`
/ `score_fold` machinery a `voice_audio = {speaker: [(x, fs, word), ...]}` built from
faster-whisper forced-alignment word spans (the iter-15 gold-span harness) instead of
FSDD isolated digits. Combine-all, no fit, no select-best, no weight. The cues are the
agent's owned operators; the harness only wires + gates + slices the audio.

## A harness bug found + fixed (world-adapter only, agent graph UNCHANGED)

The first continuous smoke run had `GRAPH == iter34 == iter33` on every fold and all
drop-it = +0.000 — the product was insensitive to channels. Root cause:
`enriched_hvpt_accept._enr_substrate` cached its scratch substrate keyed only on the
channel COUNT. FSDD's vocabulary is constant (10 digits every fold) so this was fine
there, but continuous folds have DIFFERENT shared vocabularies per held-out speaker;
the cached substrate accumulated stale `is_word` Concepts (the Argmax ranges over ALL
`is_word` Concepts) with stale `p_ch` attrs, collapsing the prediction. FIX: key the
cache on `(n_channels, frozenset(candidate_words))` and rebuild on change. This is a
world-adapter cache-correctness fix — it does NOT touch the agent's graph / cues /
product. Proof it is harmless on FSDD: PART B reproduces iter-34/35's digit numbers
BYTE-FOR-BYTE (below), so the delta is purely the continuous venue, not the fix.

The combine-all-not-select audit holds for every channel count used here (20/23/24):
`predict_many_settings_term(n)` is `Argmax(NodesWhere) of Times[p_ch0..p_ch{n-1}]`,
node types `{Argmax, Attr, Lit, NodesWhere, Times, Var}`, exactly `n` Times items, NO
`Max/Sort/Pick/If/Div`/weight anywhere. No fit, no select-best, no per-channel weight.

---

## PART A — the graph on CONTINUOUS speech (`/tmp/iter36_continuous_n8.txt`)

LibriSpeech dev-clean, 8 held-out speakers (LOSO), faster-whisper forced-alignment
GOLD word spans (the iter-15 harness) → per-word waveform clips. Shared cross-speaker
vocabulary of 12 words (all 7-8 speakers each): `and but for had have his not out that
the was with` — all FUNCTION words (the gold-span reality of LibriSpeech: function
words dominate, and they are the WORST case for the bottom-up — heavy reduction /
coarticulation / cross-speaker variation). 501 clips, chance 0.083. Same enriched
recognition graph as iter-34/35 (20 gammatone + FFT-ear + formant-relation +
manner/voicing + single-pass AxS), combine-all.

### (graph) recognition, LOSO over 8 speakers

| metric (mean over 8 LOSO folds) | value | vs |
|---|---|---|
| **GRAPH (all cues + AxS)** | **0.234** | the full graph |
| iter34 (23 nodes, no AxS) | 0.225 | |
| iter33 (gammatone only) | 0.222 | |
| single-setting flat | 0.183 | the bottom-up single channel |
| frozen | 0.177 | |

- **GRAPH vs single-flat Δ +0.051; GRAPH vs frozen Δ +0.056.** On continuous, the
  graph beats the single bottom-up channel by a wide margin — UNLIKE digits, where the
  combination win over single-flat was modest and the per-cue contribution redundant.
- **SHUFFLE (voice-partition randomised): GRAPH real 0.234 − shuffle 0.208 = +0.026
  CLEAN; single-flat real 0.183 − shuffle 0.185 = −0.002.** The graph carries real
  cross-voice structure on continuous; the single bottom-up channel does NOT.

### (consistency) cross-speaker same-word DTW-NN (representation level)
cross-speaker NN **0.165** vs chance 0.083 (2×), shuffle 0.100 → **margin +0.065**.
The bottom-up representation carries SOME cross-speaker word identity but it is weak —
exactly the "bottom-up fails on continuous cross-speaker" premise.

### (3) PER-NODE DROP-IT — which DIGIT-REDUNDANT cues are now CONTINUOUS-COMPLEMENTARY?

| cue | alone | drop-it Δ (continuous) | drop-it Δ (DIGITS, iter-34/35) | verdict |
|---|---|---|---|---|
| **AxS** | 0.181 | **+0.009 COMPLEMENTARY** | **−0.002 redundant** | **FLIPS to complementary** |
| manner_voicing | 0.158 | **+0.005** | +0.012 | complementary both |
| fft_ear | 0.163 | **+0.001** | −0.006 (in iter-35) | flips positive |
| formant_relation | 0.143 | −0.000 | +0.017 | ~neutral on continuous |

**The headline: the AxS top-down node — REDUNDANT on digits (−0.002, iter-35's exact
finding) — FLIPS to COMPLEMENTARY on continuous (+0.009 drop-it).** This is precisely
iter-35's banked prediction: "the AxS would help where the bottom-up FAILS, not on
digits the bottom-up already nails." It does.

### (3b) ERROR-OVERLAP — the DECISIVE test, free of product saturation

The 20-gammatone product saturates (multiplies to near-one-hot), which can MASK a
complementary cue's contribution in the combined drop-it. The clean test: on the held
queries where the BOTTOM-UP (gammatone product) is WRONG, what fraction does each cue
ALONE catch? (chance 0.083). Over all 389 bottom-up errors across the 8 folds:

| cue alone | catches of 389 bottom-up errors | rate | vs chance 0.083 |
|---|---|---|---|
| **manner_voicing** | 68 | **0.175** | **2.1×** |
| **AxS** | 59 | **0.152** | **1.8×** |
| **fft_ear** | 52 | **0.134** | **1.6×** |
| **formant_relation** | 47 | **0.121** | **1.5×** |

**Every cue — including the AxS — catches the continuous bottom-up's errors at
1.5–2.1× chance.** They carry information the bottom-up lacks. On digits the same cues
were informationally redundant (the bottom-up was already right). The cues did not
change; the venue did.

## PART B — the back-transfer to DIGITS (`/tmp/iter36_digit_transfer_n8.txt`)

Re-ran the digit HVPT (`enriched_hvpt_accept 8 2`) with the SAME (cache-fixed) graph
configuration the continuous task exercises — the full cue set including the AxS node.

| metric (mean over 6 FSDD LOSO speakers, n=8) | value | iter-34/35 |
|---|---|---|
| ENRICHED+AxS graph (24 nodes) | **0.588** | 0.588 (iter-35) |
| iter-34 (23, no AxS) | 0.590 | 0.590 |
| iter-33 (gammatone) | 0.567 | 0.567 |
| single-flat | 0.496 | 0.496 |
| frozen | 0.427 | 0.427 |

- **enr+AxS 0.588 does NOT rise above iter-34's 0.590 (Δ −0.002).** The AxS / cue set
  forced by continuous does NOT drive up the digit mean.
- **Per-fold (REAL, byte-identical to iter-34/35) — the hard folds do NOT rise:**

| held-out | enr+AxS | iter-34 | AxS drop-it |
|---|---|---|---|
| george | 0.713 | 0.725 | −0.012 |
| jackson | 0.575 | 0.575 | +0.000 |
| **lucas** | **0.350** | **0.362** | −0.013 |
| nicolas | 0.637 | 0.613 | +0.025 |
| theo | 0.550 | 0.562 | −0.012 |
| **yweweler** | **0.700** | **0.700** | +0.000 |

  The hard folds yweweler (tied) and lucas (−0.012) do NOT rise; AxS drop-it on digits
  averages −0.002 (redundant), reproducing iter-35 exactly.
- The full digit run reproduces iter-34/35 to the digit on every metric (AxS alone
  0.302, label-shuffle 0.094 collapses, shuffle margin +0.010) — confirming the
  cache-fix is harmless on FSDD and pinning the continuous result to the venue.

## VERDICT

**(a) Does the graph pay off on CONTINUOUS where it was redundant on digits? YES.**
- GRAPH 0.234 beats single-flat 0.183 by +0.051 and frozen by +0.056; the graph's
  real−shuffle margin is +0.026 CLEAN while single-flat's is −0.002.
- The **AxS top-down node FLIPS from redundant on digits (−0.002) to complementary on
  continuous (+0.009 drop-it)** — iter-35's banked prediction realised.
- The DECISIVE, saturation-free error-overlap: every cue (manner 2.1×, AxS 1.8×, fft
  1.6×, formant 1.5×) catches the continuous bottom-up's errors well above chance. On
  digits these same cues were informationally redundant. The mechanism is confirmed:
  orthogonal-in-mechanism becomes orthogonal-in-INFORMATION exactly where the bottom-up
  fails.

**(b) Does continuous DRIVE UP the digits (the back-transfer)? NO — honestly reported.**
- The digit mean is 0.588 (enr+AxS) vs iter-34's 0.590 — it does NOT rise. The hard
  folds (yweweler tied, lucas −0.012) do NOT rise. The cues that catch continuous
  errors do NOT catch the digit hard-fold errors.

**Why (a) holds but (b) does not — the honest refinement of the user's prediction.**
The user's mechanism is CONFIRMED on its first half (the cues are complementary where
the bottom-up fails — continuous) and FALSIFIED on its second half (the same cues do
NOT transfer to lift the digit hard folds). The reason: the digit hard folds
(yweweler, lucas) are NOT a case of the bottom-up making the KIND of error the cues
catch. The digit bottom-up's cross-speaker errors are still bottom-up-shaped (spectral
detail confusions among 10 arbitrary, acoustically-distinct digits), and the
orthogonal/top-down cues are individually WEAKER than the bottom-up there (AxS alone
0.302, formant 0.421 vs single-flat 0.496) — so on digits, where the bottom-up is the
strongest single cue, the complementary cues have nothing to add even on the hard
folds. On continuous FUNCTION words the bottom-up single channel is weak (0.183) and
its errors are coarticulation/reduction-driven, a DIFFERENT error kind the cues do
catch. The slice (digits) is not driven by the whole (continuous) because the slice's
residual errors are a different shape from the whole's — the digit task genuinely
plateaus at ~0.59 for this cue family, and the headroom is a harder venue (continuous),
not a better combination on digits.

**NET.** The richness lever pays off on CONTINUOUS where it was redundant on digits
(the graph beats the bottom-up by +0.051 with a clean shuffle margin; the AxS becomes
complementary; every cue catches the bottom-up's errors above chance) — the first half
of the prediction, the part about the cues becoming complementary, is CONFIRMED
multi-metric with the decisive saturation-free error-overlap. The back-transfer (the
second half — continuous driving up the digits) is NOT observed: the digit mean and
hard folds are unchanged (0.588 vs 0.590). The cues are continuous-complementary but
digit-specific in their non-transfer; the digit plateau is real and the headroom is
the continuous venue itself, not a digit gain. Combine-all, no fit, no select, no
weight throughout; PART B reproduces iter-34/35 byte-for-byte (no-fit reproducibility);
required suites green (32).

### Honest limits / how far
- Absolute continuous accuracy is LOW (GRAPH 0.234, chance 0.083 — 2.8× chance) on a
  12-word FUNCTION-word vocabulary. This is gold-span isolated-word recognition, not
  end-to-end ASR; it removes the segmenter to isolate the recognition graph. The lift
  over single-flat (+0.051) and the clean shuffle margin (+0.026) are the real signal,
  not the absolute number.
- The vocabulary is all function words (gold spans on LibriSpeech are dominated by
  them). Function words are the hardest bottom-up case (best for showing the cues
  become complementary) but also the least acoustically distinct (low absolute ceiling).
- The combined drop-it numbers are small (AxS +0.009) because the 20-gammatone product
  SATURATES; the error-overlap (the saturation-free probe) is the cleaner evidence and
  is unambiguous (all cues 1.5–2.1× chance at catching bottom-up errors).
- The back-transfer is honestly NULL — the user's "whole drives the slice" prediction
  does not hold for the digit slice; reported as such, not spun.

## Reproduce
```
python -m scripts.iter36_continuous_graph 8 40 8 12   # PART A (/tmp/iter36_continuous_n8.txt)
python -m scripts.enriched_hvpt_accept 8 2            # PART B (/tmp/iter36_digit_transfer_n8.txt)
```
Wiring: `scripts/iter36_continuous_graph.py` (gold-span slicing + shared-vocab gating +
error-overlap; reuses `scripts/enriched_hvpt_accept.build_fold/score_fold` UNCHANGED),
the cache-key fix + `return_preds` in `scripts/enriched_hvpt_accept.py`. Combine-all
audit: `predict_many_settings_term(20/23/24)` = Argmax-of-Times, no forbidden nodes.
Required suites green (32): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance.
