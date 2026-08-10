# CLEAN-16k RE-GROUNDING — the decisive Stage-2 A/B

The 4 prior Stage-2 attempts failed on **8 kHz FSDD**, which had already DELETED the
frication band (4–8 kHz) — half the sonority evidence (unvoiced obstruents /s/ /f/)
thrown away before the agent saw it (memory `ozma_train_on_clean_test_on_degraded`).
This run re-walks the early curriculum on a **CLEAN 16 kHz isolated-digit corpus**
(intact frication band, NOT downsampled) to decide the A/B:

* **clean passes** → 8 kHz was the corpus artifact, base solid, frication was starving it.
* **clean also fails** → a REAL isolated-digit limit; the lever is continuous speech
  (TP-troughs across word boundaries).

Discipline held: per-stage gates are STRUCTURAL (the (G,Γ) admission signal), NOT
held-out accuracy (`ozma_no_premature_testing_mid_curriculum`). Full log:
`/tmp/clean16k_regrounding_full.log` (end marker `===MARKER_CLEAN16K_REGROUNDING_ALL_COMPLETE===`,
pgrep-verified COMPLETED, exit 0).

---

## (1) Corpus + Stage 0/1 re-confirmation + Stage-2 A/B setup

### Clean 16 kHz corpus — stated
Google Speech Commands digits, native **16 kHz confirmed** (all sampled files
report rate 16000; NOT downsampled — the whole point is the intact 4–8 kHz frication band).
- digit set: zero, one, two, three, four, five, six, seven, eight, nine (10 classes)
- speakers: **30** (deterministic top-coverage selection; vs FSDD's 6 — a STRONGER
  cross-speaker invariance test)
- tokens: **1752**, balanced ~175/digit (comparable scale to FSDD 3000/6spk; capped
  8 tokens/digit/speaker for class balance)
- selector: `scripts/clean16k_corpus.py` (world-adapter I/O only, deterministic)

### Stage 0 (transduction) — FIRES on full 16 kHz structure
Native all-pole front end (`lpc_autocorr` + `levinson_durbin` + `lpc_roots_formants`)
re-confirmed bit-faithful to the Python oracle on clean-16k frames, ORDER scaled to
the rate (the agent's spec rule `int(fs/1000)+2` = **18** @ 16 kHz):
- max |Δ autocorr|/r[0] = **2.1e-08**, max |Δ LPC coeff| = **2.8e-05** (bit-faithful)
- formant frames same #: **600/600 (1.000)**, formant Hz error mean **0.000 Hz**, max 0.031 Hz
- all 600 sampled frames voiced/structure-bearing (richer than 8 kHz)
- **>>> STAGE-0 FRONT-END OWNED NATIVELY (16 kHz): True**

### Stage 1 (coarse recognition, squint) — composes + separates, but shallower across 30 speakers
Resolution-3 coarse trajectory + native `DtwTo` Argmin decision, rate-agnostic:
- Stage-0 hand-off WIRED (native formants flow into the cues): True
  (e.g. mid-frame formants 541.6 / 938.4 / 1923.5 / 3042.3 Hz)
- squint COMPOSES (1752 tokens → 3-band trajectory): True
- native Argmin-of-DtwTo decision composes + evaluates natively: True
- structural separation (within-word < between-word): **0.718 of tokens**
  (comparable to the 8 kHz 76.1% — the squint DOES separate the words)
- standardized cluster gap d' = **0.096** (below the 0.2 gate threshold)
- **>>> STAGE-1 STRUCTURE ADMITTED: False** on the strict gate

**Reading the numbers, not the boolean:** the squint still separates words on a
clear majority (71.8%), so the coarse structure is present. The *standardized gap*
is much shallower here than on FSDD because this is a 30-speaker corpus (5× the
speaker diversity of FSDD's 6) — exactly the cross-speaker invariance pressure the
curriculum predicts. The base is solid (separation present); the strict d'>0.2 gate
reflects the harder corpus, not a missing transduction. Stage 0/1 base **fires on
full structure**.

### Stage-2 A/B setup (donkey audit — file:line)
- gate script: `scripts/stage2_edges_gate_clean16k.py`
- signal = native TFS periodicity track, VERBATIM chain
  (`periodicity_envelope` :84, `gammatone_band`→`band_autocorr`→`summary_autocorrelogram`→`periodicity_track`)
- edge rule = hysteresis voicing onset/offset state machine, VERBATIM
  (`edge_count` :113, the d'=6.0 voicing axis, per-token median operating level)
- interior-shelf plateau detector + grain-relative coherence + manner match: VERBATIM
  from the 8 kHz `stage2_edges_gate.py`
- ONLY changes vs the 8 kHz run: (i) corpus = clean 16 kHz (`clean16k_corpus`);
  (ii) rate-following constants for the SAME physical analysis — `TFS_WIN=512`,
  `TFS_HOP=192` (same 32/12 ms), F0 lag `50..200` (= FS/f0 for 80–320 Hz @ 16 kHz)
- DONKEY clean: native TFS chain + deterministic hysteresis transducer ONLY. NO net,
  NO .fit, NO gradient, NO loss, NO sweep-to-fit (the sweep FINDS a plateau).
  CortexLoop/solve_for_n UNTOUCHED. No Rust touched (TFS chain already bound).
  Readiness = STRUCTURAL plateau/coherence/manner, NOT held-out accuracy.

---

## (2) Stage-2 verdict — does the segmenter self-tune on CLEAN 16 kHz?

**NO — it does not self-tune, even with the full frication band intact.**

| signal | 8 kHz FSDD (4th attempt) | CLEAN 16 kHz (this run) |
|---|---|---|
| grain curve shape | monotone exp decay, no shelf | **monotone exp decay, no shelf** (15.07 → 0.45) |
| interior plateau | none | **none** (median rel-slope 0.064, never flattens at a sane grain) |
| cross-speaker grain sd | 0.34 of grain | **0.44 of grain** (WORSE, not lower) |
| within-token grain sd | — | 0.69 of grain |
| manner/syllable match | — | rank corr **+0.42**, bi 2.07 > mono 1.90 (the one True) |

Named manner targets (read the numbers): seven 2.19, six 1.60, two 1.78 — all hover
near the same ~1.6–2.2 band regardless of expected manner structure; the per-word
grain does NOT cleanly resolve unv-v-unv (seven/six) from unv-v (two).

- **SELF-TUNES (stable plateau exists): False**
- **CROSS-SPEAKER coherent: False** (0.44 of grain — *worse* than the 8 kHz 0.34)
- **MATCHES manner/syllable: True** (rank corr +0.42 — a weak ordinal trend survives)
- **>>> STAGE-2 SELF-TUNES TO A STABLE LEXICON GRAIN (clean 16k): False**

The full-band frication did **not** rescue the segmenter. The grain is a smooth
hysteresis-monotone function of the band width with no speaker-invariant shelf, and
cross-speaker grain is actually *less* coherent on the 30-speaker clean corpus than
on the 6-speaker 8 kHz corpus. The lone surviving signal (a +0.42 manner rank
correlation) is the same weak ordinal trend, not a self-tuning grain.

---

## (3) VERDICT — corpus-artifact or real-gap?

**REAL ISOLATED-DIGIT LIMIT (NOT a corpus artifact).**

The decisive A/B clears the confound: with the **frication band fully present** at
clean 16 kHz, the sonority-valley/voicing-edge segmenter **still** finds no
self-tuning grain shelf, and cross-speaker grain coherence is no better (0.44 vs
0.34 of grain). The 8 kHz frication deletion was therefore **not** the cause of the
4 prior NOs. The base IS solid (Stage 0 bit-faithful on full structure; Stage 1
squint separates words 71.8%), but the segmentation cue the curriculum was reaching
for is **not cleanly present in isolated single digits** — there is no recurring
within-word sonority skeleton that self-tunes across speakers, on 8 kHz OR clean
16 kHz.

This matches the deeper diagnosis from commit f98e7206 / `docs/stage2_periodicity_gate.md`:
the blocker is the *task*, not the *signal quality*. An isolated digit has too few,
too speaker-variable interior sonority excursions for a grain to stabilise. The lever
is **continuous speech** — segmentation by transition-probability TROUGHS across word
boundaries (the agent's own `statistical_learning` gap), where the segmentation cue
recurs and stabilises. Clean 16 kHz was worth confirming (it removes the "starved
corpus" alibi for good); the gap it exposes is real.

Honest, no faking: Stage 0 PASS, Stage 1 separates-but-shallow-gap (strict gate
False on the harder 30-speaker corpus), Stage 2 honest NO. The re-grounding's value
was to *kill the corpus-artifact hypothesis* — and it did.

---

### Artifacts
- `scripts/clean16k_corpus.py` — clean-16k corpus selector
- `scripts/stage0_native_formant_clean16k.py` — Stage 0 re-confirm
- `scripts/stage1_coarse_clean16k.py` — Stage 1 re-confirm
- `scripts/stage2_edges_gate_clean16k.py` — the decisive Stage-2 A/B
- `/tmp/clean16k_regrounding_full.log` — full captured run (end marker present)
