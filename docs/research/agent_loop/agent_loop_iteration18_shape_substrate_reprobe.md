# Iteration 18 — re-probe the perceptual ceiling on the "shape" substrate

**Question.** The agent's shape-based self-refactor is done. Did it lift the
perceptual ceiling that was co-limiting continuous-speech recognition? (The
iter-15 GATE found the OLD surface front-end ceilinged at gold-span within-NN
~0.20 — below shallow-CNN 0.32 and SSL 0.49, so the representation was
co-limiting, not just boundaries.)

**Short answer: NO — and the premise needs correcting.** The "shape refactor"
that was committed is the agent's *symbolic* Term-tree shape machinery
(analogical transfer / grounding / derivation), NOT a perceptual front-end. The
speech representation feeding the GATE is byte-for-byte the iter-15 stack. Re-run
LIVE, the GATE within-NN is **0.203** — statistically the same 0.20 ceiling. The
perceptual representation is still co-limiting. Shape did not touch it.

---

## (0) What the refactor actually changed

The recent "shape" / "jabberwock" / "refactor A–D" commits
(`ada9ddc`, `89afd20`, `62c25d4`, `c5104d5`, `3301d37`, `f874fd3`, `f2a7c1c`)
all operate on the agent's **symbolic reasoning / knowledge-graph** layer:

- `src/shape.rs` — `shape::children()` now recurses into Plus/Times/Holds/…;
  `structural_depth_bump_for` + `has_sibling_pattern_recurrence` give Term-trees
  a structural-depth + recursion Shape axis (distinct shapes in the donor
  catalog 1 → 10). This is the **Term-tree** shape used for derivation dispatch
  and analogical transfer.
- `harvester_shape.py` / `implication_harvester.py` — Shape-aware path made
  primary in `synthesize_gaps` (0 → 103 derivations across 5 grounded
  postulates); regex no longer dominates.
- `concept_grounding.py`, `concept_promotion_rules.py`, `code_authoring.py`,
  `comprehension.py`, `wire_island_mts.py`, `physics_foundation.json`,
  293 "Y of Z" seed promotions — grounding becomes seed-resident Term-trees.

**None of these touch the perceptual audio front-end.** Verified: no commit
since the iter-15 GATE (`3c6cb0c`) touches `invariant_units.py`,
`dynamics_features.py`, `cmvn.py`, `representation.py`, the cochlea/gammatone/A1
path, or `continuous_speech_recognition.py`'s framing — except iter-16
(`d81d539`), which added the analysis-by-synthesis *decision* + the `DtwTo` Rust
Term (a recognition change, not a representation change). Every `shape` token in
the speech-domain files is NumPy `array.shape`, not a shape representation. There
is no shape-based perceptual feature, no shape-based distance for matching, and
no shape-based AxS distance anywhere in the tree.

So the task's premise — "a shape-based front-end refactor is done" — does not
hold for the perceptual pipeline. The measurements below confirm this empirically
rather than just by code reading.

---

## (1) THE GATE — gold-span same-word consistency (decisive)

`python -m scripts.iter15_goldspan_gate 8 12` — faster-whisper forced alignment
on LibriSpeech dev-clean, 96 utts / 8 speakers, 1171 gold word segments, 632
distinct words (chance ~0.002). full-DTW intra/inter separation + same-word NN.

| Front-end | WITHIN NN | WITHIN sep | shuffle NN | shuffle sep | CROSS NN |
|---|---|---|---|---|---|
| INV (per-utt invariant) | 0.237 | +0.164 | 0.037 | +0.027 | 0.029 |
| **CMVN (uVTLN+ps_CMVN+PR)** | **0.203** | **+0.252** | 0.037 | −0.089 | 0.021 |

**GATE within-NN = 0.203** (CMVN, the proven cross-speaker front-end), within-sep
+0.252. Shuffle controls hold (NN 0.037, sep collapses/negative).

**Verdict vs the references:**

- OLD surface ceiling: ~0.20 → **NEW: 0.203. Did NOT move.**
- shallow-CNN-with-gold-spans: 0.32 → still **below** it.
- SSL-with-gold-spans: 0.49 → still **far below** it.

The harness's own gate fires FAIL (within-NN < 0.22): "the representation is
weaker than shallow-CNN-with-gold-spans; the gap is NOT only segmentation."

**The shape refactor did NOT lift the perceptual ceiling.** The representation is
still co-limiting.

---

## (2) Within-speaker chunk consistency (no gold spans) — Step 2

`python -m scripts.iter13_continuous_xspeaker` — continuous-chunk within/cross
full-DTW on held-out speakers, BEFORE (per-utt invariant) vs AFTER (per-speaker
CMVN), shuffle-controlled. Old baseline: separation ~+0.11 / within-NN ~0.13.

**Not decisive here, and unchanged by construction.** This probe exercises the
*same* `coarse_stream_of` → corpus-TP → `chunk_with_corpus_tp` chunker and the
*same* `invariant_transform`/CMVN front-end and full-DTW kernel as before — none
of which the shape refactor touched. The continuous-chunk number is additionally
*segmenter*-limited (no gold spans), so it is a lower bound, not a representation
probe; the GATE in §1 already isolates the representation with gold spans and
shows it unchanged (0.203). The live re-run is dominated by the chunker's known
quadratic cost on long LibriSpeech sentences (the per-utterance fresh-Substrate
chunk is O(minutes) per utterance), so it does not converge quickly; it was
running at report time without having reached the chunk-DTW stage. Given the code
path is provably untouched and the GATE already answers the representation
question, this measure cannot show a shape-driven lift and is not load-bearing
for the verdict.

---

## (3) FSDD recognition — regression check

`python -m scripts.mcu_infer` (the confirmed speaker-invariant FSDD LOSO
recognizer, commit `2648ba07`).

| Metric | This run | Confirmed/prior |
|---|---|---|
| FLOAT (full lexicon) LOSO | **0.764** | 0.764 |
| INT16 (full lexicon) LOSO | **0.761** | 0.761 |
| unigram | 0.100 | 0.100 |
| (confirmed best) | — | 0.785 |
| INT16 compact P1/P3/P5 | 0.461 / 0.503 / 0.525 | same |

**No regression.** Matches the prior numbers exactly — expected, since this DSP
pipeline is untouched by the shape refactor. The small-vocab win holds.

---

## (4) Analysis-by-synthesis (shape-matched AxS) — Step 4

There is **no shape-matched AxS distance** in the tree — "shape-matched AxS" was
a *future* lever named in the iter-16 commit, never built. The AxS distance is
the iter-16 A1-patch `DtwTo`. Re-run `python -m scripts.analysis_by_synthesis_accept 3`
(FSDD, LOSO) to confirm no regression:

| Measure | This run | iter-16 |
|---|---|---|
| bottom-up 1-NN DTW LOSO | 0.478 | 0.478 |
| AxS native-A1 graph DtwTo | **0.300** | 0.300 |
| AxS audio-resynth | 0.078 | 0.078 |
| AxS shuffle | 0.072 (chance 0.10, collapses) | 0.072 |
| AxS cross-speaker 2AFC | 0.678 | 0.678 |
| bottom-up cross-speaker 2AFC | 0.818 | 0.818 |

**Reproduces iter-16 exactly.** No shape change, no regression. AxS still works
(3× chance, cross-speaker above chance) but does not beat bottom-up — bounded by
forward-model quality, as before.

---

## (5) VERDICT

**The shape refactor did NOT lift the perceptual ceiling. The representation is
still co-limiting continuous large-vocab recognition.**

- GATE gold-span within-NN: **0.203** (NEW) vs ~0.20 (OLD) — unchanged; still
  below shallow-CNN 0.32 and far below SSL 0.49. Shuffle-controlled.
- The committed "shape" refactor is the agent's *symbolic* Term-tree shape
  system (derivation/analogy/grounding). It does not — and structurally cannot,
  as written — change the gammatone→invariant→CMVN perceptual front-end the GATE
  measures. The unchanged GATE number is the live confirmation.
- FSDD LOSO 0.764/0.761 and AxS 0.300 / 2AFC 0.678 both reproduce exactly —
  no regression anywhere.

**So the continuous gap does NOT collapse to boundaries+AxS.** It remains
multi-limited: the perceptual representation is still a co-limit, exactly as
iter-15 found. To lift the ceiling, a genuinely shape-based *perceptual*
representation would have to be built (the front-end the GATE feeds — currently
band-trajectory + CMVN matched by full-DTW — has no structural/shape encoding).
The symbolic shape machinery is real and useful for the reasoning layer, but it
is the wrong layer for this ceiling.

Tests green: `test_stt_pipeline` + `test_perception_self_assessment` +
`test_process_meta_assessor` + `test_gap_guidance` = 32 passed.

(Results left in the working tree; not committed, per instruction.)
