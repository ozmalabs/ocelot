# Stage 2 — segmentation-coherence gate, RE-RUN on the TFS PERIODICITY signal

The precise next from commit `1a2f9460`. The prior run
(`scripts/stage2_segmentation_gate.py`, `docs/stage2_segmentation_gate.md`) ran the
ACTUAL Stage-2 gate the curriculum names —

> *"the sonority-valley segmenter's depth-threshold **self-tunes to a stable
> lexicon grain**."* (`docs/toolbox_and_curriculum.md:345-347`)

— on the native **TOTAL-ENERGY** envelope and found **NO** self-tuning: a smooth
monotone exponential decay (no shelf), cross-speaker grain sd 0.44 of grain, not
coherent. Its diagnosis (`ozma_fix_the_fixer`): the blocker is the **SIGNAL**, not
the threshold. Feed the segmenter the graded **TFS PERIODICITY / voicing track**
(native `band_autocorr` → `summary_autocorrelogram` → `periodicity_track` — the
SAME d′=6.0 voiced↔unvoiced axis from PART 1, `stage2_sonority.md`) instead of
energy; periodicity valleys mark voiced↔unvoiced (sonority) boundaries that should
be far more speaker-stable than energy minima.

This is the STRUCTURAL segmentation-coherence gate (a `(G,Γ)` signal), **NOT** a
held-out recognition accuracy (`ozma_no_premature_testing_mid_curriculum`).

- Gate script: `scripts/stage2_periodicity_gate.py`.
- Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_periodicity_gate`.
- Capture: `/tmp/stage2_periodicity_gate_full.log`
  (end marker `===MARKER_STAGE2_PERIODICITY_GATE_COMPLETE===`).
- pgrep-verified COMPLETED; 3000/3000 tokens had a usable periodicity track.

---

## (1) The periodicity-fed segmenter + the corrected gate (donkey audit, file:line)

**The ONLY change from the prior run is the SIGNAL.** Everything else — the depth
sweep (0.02…0.80, 40 steps), the corrected interior-shelf plateau detector, the
grain-relative coherence test, the syllable-match test, and the verdict logic — is
**VERBATIM** from `scripts/stage2_segmentation_gate.py` (the detector the agent
fixed after it caught its own instrument printing two false-positive `True`s).

- **The new signal** = the graded TFS periodicity track,
  `scripts/stage2_periodicity_gate.py:periodicity_envelope` (lines 116-145), copied
  VERBATIM from `scripts/stage2_sonority_check.py:tfs_voicing_track` (the validated
  T4 chain, commit `90b799c9`): native `gammatone_band` (8 bands over F0/low-formant
  place) → `band_autocorr` → `summary_autocorrelogram` → `periodicity_track`,
  per-frame periodicity strength in [0,1]. No Python DSP, no decision.
- **The segmenter** = `_n.detect_sonority_valleys`
  (`runners/dsl/src/audio_primitives.rs:1217`, bound `runners/dsl/src/py.rs:6079`),
  run on the periodicity track (`:valley_count`, lines 148-156). The periodicity
  frame rate `FS/TFS_HOP = 8000/96 = 83.33 Hz` is passed as the segmenter's `fs` so
  its ms→sample windows (smoothing 25 ms, min-separation 50 ms) land correctly on
  the periodicity grid. The segmenter's `depth` is a **relative** ratio (depth from
  the lower flanking peak, `audio_primitives.rs:1287`), so the [0,1] periodicity
  values feed it directly and the SAME depth sweep applies.
- **Donkey-clean.** Only the native TFS chain + the native segmenter run. No net,
  no `.fit`, no gradient, no loss, no recognition score. The threshold sweep FINDS
  the plateau; it is NOT an accuracy fit. `CortexLoop` / `scripts/solve_for_n.py`
  UNTOUCHED; no `runners/` diff; no Rust build (TFS + segmenter already bound).
- **The corrected detector is reused unchanged** (`:B`, lines 196-245): an INTERIOR
  relative-flat shelf (`REL_TOL`, `EDGE_GUARD=3`) at a non-trivial grain
  (`GRAIN_FLOOR=1.0`), plus grain-relative coherence (`rel_cross`, `rel_tok`). The
  boolean is NOT rubber-stamped; the numbers are read below.

---

## (2) The readiness verdict — read off the NUMBERS, not the boolean

### (A) The grain curve is STILL a smooth monotone decay — no shelf

The periodicity grain bleeds smoothly from over-segmentation (2.78 valleys at depth
0.02) straight through to 0 (depth ≥ 0.68), passing through every fractional value
with **no flat band at the lexicon's natural integer grain**:

| depth | grain | | depth | grain |
|---|---|---|---|---|
| 0.02 | 2.78 | | 0.20 | 0.87 |
| 0.06 | 2.30 | | 0.28 | 0.44 |
| 0.10 | 1.82 | | 0.40 | 0.11 |
| 0.16 | 1.18 | | 0.60 | 0.004 |
| 0.18 | 1.02 | | 0.68 | 0.00 |

### (B) NO self-tuning plateau

```
NO stable, non-trivial plateau found (grain never flattens at a sane grain)
— the segmenter does not self-tune.
```

The interior relative-flat-shelf detector finds **no** qualifying run. The grain is
a clean monotone decay just like the energy run — there is no interior derivative
minimum at a non-trivial grain, so there is **no stable operating point** to
self-tune to. (The reported sweep-wide `max 666.667` relative slope is the
last-step ÷ near-zero-grain artifact at the collapsed tail; the detector's
`EDGE_GUARD`/`GRAIN_FLOOR` correctly excludes that tail, which is precisely the
false-positive class the agent fixed in the prior run.)

### (C) NOT cross-speaker coherent — and WORSE than energy

At the most lexicon-like diagnostic point (d* = 0.18, grain ≈ 1 valley; there is no
self-tuned point to read):

- **mean cross-speaker grain sd = 0.647 = 0.64 of the grain** — a word's grain
  swings ~64% of its own value across the 6 speakers. **This is WORSE than the
  energy run's 0.44.**
- **mean within-token grain sd = 1.050 = 1.04 of the grain** — tokens of the SAME
  word disagree by ~100% of the mean grain (energy: 0.97).

The driver is visible per-speaker: `lucas` carves systematically ~2–3× coarser than
everyone else on EVERY digit (e.g. *one* per-speaker means `[0.3, 0.8, 2.1, 0.1,
0.5, 0.4]`; *three* `[0.4, 0.6, 2.1, 0.4, 0.3, 0.7]`). The periodicity track's
absolute level / valley shape is **not** speaker-normalised, so a single speaker's
voicing landscape presents far more interior periodicity minima at the same depth.
The d′=6.0 axis is a strong *per-frame voiced/unvoiced discriminator*, but its
*valley structure over a word* is not speaker-stable.

### (D) Manner/syllable match — STRONGER (the one positive, improved)

Grain-vs-syllable rank corr = **+0.661** (energy: +0.38); bi-syllabic mean 1.21 >
mono 0.93. Periodicity DOES track syllable structure more cleanly than energy did —
*seven* (2 syl) carves coarsest at 1.60, *zero* (2 syl) at 1.08, both above the
mono mean. But this ordinal trend rides on top of the incoherence in (C); it is
necessary flavour, not the gate. (*six*, mono, still carves 1.60 — its medial
`/k-s/` obstruent break — so the trend is not clean.)

```
=== READINESS GATE — SEGMENTATION SELF-TUNING on PERIODICITY (structural) ===
  SELF-TUNES (a stable grain PLATEAU exists)         : False
  PLATEAU grain is non-trivial (word actually carves): False
  CROSS-SPEAKER coherent (same word -> same grain)   : False  [cross-spkr sd 0.65 = 0.64 of grain; within-token 1.04 of grain]
  MATCHES lexicon manner/syllable structure          : True   [rank corr +0.66, bi 1.21 > mono 0.93]
  >>> STAGE-2 SEGMENTER SELF-TUNES TO A STABLE LEXICON GRAIN (periodicity): False
```

---

## (3) VERDICT — Stage 2 is STILL NOT complete; the precise next is LANDMARKS

**The gate does NOT fire on periodicity either.** Switching the segmenter's input
from total energy to the graded TFS periodicity did **not** produce a self-tuning
plateau, and it made cross-speaker coherence **worse** (0.64 of grain vs energy's
0.44), not better. The one thing periodicity improved is the ordinal syllable trend
(rank corr +0.38 → +0.66), but that was already passing and is not the gate.

This **falsifies the prior run's hypothesis** that the periodicity *valleys* would
be more speaker-robust than energy *valleys*. The honest structural reading: the
problem is not which scalar envelope the minima are read off — **minima-detection on
any per-frame envelope of a short isolated digit has no stable, speaker-invariant
shelf**, because the *number and depth of interior minima* is itself speaker- and
token-dependent (clearest in the `lucas` offset). The periodicity track is a
superb *voiced/unvoiced classifier* (d′=6.0) but a poor *segmentation-by-valley-
count* source — graded sonority does not carve at consistent depths across speakers.

### The precise next (structural, no threshold tuning, no accuracy chase)

Take the fallback the prior run already named (commit `1a2f9460`, point 2): stop
counting *minima*, and instead detect the **voicing ONSET/OFFSET LANDMARKS** (the
T7 sonority *transitions* — the rising and falling EDGES of the periodicity track).
The rationale is structural and matches the `(G,Γ)` reading:

- A **valley count** is depth-threshold-sensitive and speaker-unstable (no shelf, as
  both runs now show). A **transition/edge** (voiced→unvoiced and unvoiced→voiced
  crossings of the graded track) is a *zero-derivative-sign* event, far less
  sensitive to absolute level — it should be the speaker-robust boundary primitive
  the valley count is not.
- The d′=6.0 axis is exactly where edges are SHARP: the periodicity goes high in
  sonorants and low in obstruents/silence with a large margin, so the crossing
  *location* is stable even when the *number of shallow interior dips* is not.
- This needs a landmark detector on the periodicity track (sign-of-slope crossings
  of a hysteresis band), composed from native ops — NOT a new `depth_threshold`
  value (no depth is a fix; the curve has no shelf to tune to).

If voicing-edge landmarks self-tune to a stable, coherent boundary count, the
Stage-2 segmenter half is admitted and Stage 2 completes; if the edges are also
speaker-unstable, the blocker is upstream (the segmentation cue itself is not
present in single isolated digits, and continuous-speech TP-troughs become the
lever — `ozma_learns_from_sentences`).

```
===MARKER_STAGE2_PERIODICITY_GATE_COMPLETE===
```
