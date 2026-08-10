# Stage 2 — the ACTUAL readiness gate: SEGMENTATION COHERENCE / SELF-TUNING

The two prior Stage-2 checks (`docs/stage2_sonority.md`, commit `eb335974`)
measured the WRONG gate — sonority wired as a WORD-DISCRIMINATION fusion prong
(the "sharpening" PART 2). The deeper diagnosis in `eb335974` is explicit: the
sonority's role is **SEGMENTATION**, not a word-vote, and the agent's own Stage-2
success signal (`docs/toolbox_and_curriculum.md:345-347`,
`docs/stage2_sonority.md:33`) is:

> *"the sonority-valley segmenter's depth-threshold **self-tunes to a stable
> lexicon grain**."*

This is a STRUCTURAL / `(G,Γ)`-binary coherence signal — **not** a held-out LOSO
recognition accuracy (memory `ozma_no_premature_testing_mid_curriculum`). This
doc runs that ACTUAL gate.

- Gate script: `scripts/stage2_segmentation_gate.py`.
- Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_segmentation_gate`.
- Capture: `/tmp/stage2_seg_gate_full.log`
  (end marker `===MARKER_STAGE2_SEGMENTATION_GATE_COMPLETE===`).

---

## (1) The gate definition + how it was measured

**The skill (verbatim, the agent's own curriculum).** Stage 2 names two halves:
the voiced↔unvoiced AXIS (PART 1, already admitted, d′=6.02, `stage2_sonority.md`)
and the **sonority SKELETON** — *segment by sonority valleys*. The segmenter half's
success signal is the self-tuning-to-a-stable-grain quoted above. THAT is the gate
here.

**The only agent operation is the native segmenter.** `detect_sonority_valleys`
(`runners/dsl/src/audio_primitives.rs:1217`, bound at `runners/dsl/src/py.rs:6079`,
`substrate_rs._native.detect_sonority_valleys`) is run on each FSDD digit word,
**SWEEPING its one free parameter `depth_threshold`** across its full range
(0.02 … 0.80, 40 steps). The envelope it reads is the SAME owned native cochlear
pathway used by the skeleton check (`gammatone_band` → `hair_cell_envelope` → sum
→ decimate to a 1 kHz grid; `stage2_segmentation_gate.py:total_envelope`, verbatim
from `stage2_skeleton_check.py:176`). Mechanical world-adapter, no Python DSP.

**How "self-tuning to a stable grain" was quantified** (the agent's own
structural criteria, `scripts/stage2_segmentation_gate.py`):

1. **GRAIN curve (A)** — mean valleys/token vs `depth_threshold`
   (`:main`, section A). The grain = valley count → spans (manner/syllable units).
2. **SELF-TUNING PLATEAU (B)** — a genuine self-tuning shelf is a *relative-flat*
   run (`|Δgrain|/grain` near 0, NOT absolute) at a **non-trivial** grain (≥ 1
   valley), AND an **INTERIOR local-derivative minimum** bracketed by steeper
   descent on both sides — not the flat top or the collapsed tail of a monotone
   decay (`:B`, `REL_TOL`, `EDGE_GUARD`, `:line 211-238`).
3. **CROSS-SPEAKER COHERENCE (C)** — at the operating point, is a word's grain the
   same across the 6 speakers? Measured RELATIVE to the grain
   (`rel_cross = cross-speaker sd / grain`; `:C`, `:line ~302`).
4. **MANNER/SYLLABLE MATCH (D)** — does the grain track the lexicon's natural
   structure (bi-syllabic zero/four/seven coarser than mono-syllables; rank
   correlation of grain to syllable count; `:D`).

### Donkey audit (file:line)

- **Only the native segmenter** runs (`_n.detect_sonority_valleys`,
  `stage2_segmentation_gate.py:valley_count`); envelope from owned native
  `gammatone_band`/`hair_cell_envelope` (`:total_envelope`). No net, no `.fit`, no
  gradient, no loss.
- **The threshold sweep FINDS the plateau, it is NOT an accuracy fit.** No
  recognition score is computed anywhere in the script. The verdict is the grain's
  STABILITY + CROSS-SPEAKER coherence + manner/syllable match — all read off the
  segmenter alone.
- **No held-out LOSO banked as the gate** — the gate is segmentation structure.
- `CortexLoop` / `scripts/solve_for_n.py` **UNTOUCHED**; no `runners/` diff (the
  segmenter was already bound in `eb335974`); no Rust build needed.

> Diagnostic-instrument honesty: the FIRST two runs of the gate printed `True`,
> but reading the actual numbers showed both were false-positives of an
> over-permissive plateau detector — an ABSOLUTE flatness test fired on the
> collapsed tail (grain ≈ 0.5), and a relative test without an interior/edge
> guard fired on the saturated TOP (grain ≈ 2.1). The detector was corrected to
> require an INTERIOR relative-flat shelf and grain-relative coherence
> (`ozma_fix_the_fixer`: fix the instrument, do not rubber-stamp its boolean).
> The corrected verdict matches the honest reading of the curve.

---

## (2) The readiness verdict — structural evidence (NOT a tuned accuracy)

### (A) The grain curve is a SMOOTH MONOTONE DECAY — no shelf

| depth | grain | | depth | grain |
|---|---|---|---|---|
| 0.02 | 2.21 | | 0.24 | 0.96 |
| 0.08 | 2.01 | | 0.40 | 0.47 |
| 0.16 | 1.40 | | 0.60 | 0.23 |
| 0.20 | 1.16 | | 0.80 | 0.09 |

The grain bleeds smoothly from over-segmentation (2.21 valleys at depth 0.02)
straight through to ≈ 0 (0.086 at depth 0.80), passing through every fractional
value with **no flat band at the lexicon's natural integer grain**.

### (B) NO self-tuning plateau

The per-step **relative** slope `|Δgrain|/grain` is **min 0.005, median 0.089,
max 0.140** — essentially CONSTANT across the whole sweep. That constant
fractional slope is the signature of a pure exponential decay, the OPPOSITE of a
shelf. No interior relative-flat run at a non-trivial grain exists:

```
NO stable, non-trivial plateau found (grain never flattens at a sane grain)
— the segmenter does not self-tune.
```

The segmenter has **no stable operating point**: every grain value is reachable by
a different threshold, none is preferred by the structure.

### (C) NOT cross-speaker coherent

At the most lexicon-like diagnostic point (d* = 0.24, grain ≈ 1 valley — there is
no self-tuned point to read, so this is the closest-to-1-valley diagnostic):

- mean cross-speaker grain sd = **0.42 = 0.44 of the grain** — a word's grain
  swings ~44% of its own value across the 6 speakers (e.g. *five*: per-speaker
  means [0.4, 0.2, 2.1, 0.3, 0.7, 1.4]).
- mean within-token grain sd = **0.92 = 0.97 of the grain** — tokens of the SAME
  word disagree by ~100% of the mean grain.

The grain is **not** the-same-word→the-same-grain. It is incoherent at every
operating point.

### (D) Weak ordinal manner/syllable match (the ONE positive)

Grain-vs-syllable rank corr = **+0.38**; bi-syllabic mean 1.05 > mono 0.91. There
is a weak ordinal trend (bi-syllabic words carve slightly coarser), but it is a
thin margin riding on top of the incoherence in (C) — *six* (mono) carves more
than *four* (bi). This trend alone is NOT the gate; the gate is a stable,
coherent grain, which (A)–(C) refute.

```
=== READINESS GATE — SEGMENTATION SELF-TUNING (structural) ===
  SELF-TUNES (a stable grain PLATEAU exists)         : False
  PLATEAU grain is non-trivial (word actually carves): False
  CROSS-SPEAKER coherent (same word -> same grain)   : False  [cross-spkr 0.44 of grain; within-token 0.97 of grain]
  MATCHES lexicon manner/syllable structure          : True   [rank corr +0.38, bi 1.05 > mono 0.91]
  >>> STAGE-2 SEGMENTER SELF-TUNES TO A STABLE LEXICON GRAIN : False
```

---

## (3) VERDICT — Stage 2 is NOT complete

**The gate the curriculum actually names does NOT fire.** The sonority-valley
segmenter does **not** self-tune to a stable lexicon grain. Its grain is a smooth
monotone function of `depth_threshold` (constant ~9% fractional slope, no shelf),
so there is no preferred operating point, and at every operating point the grain
is cross-speaker- and within-word-incoherent (dispersion ≈ 0.4–1.0 of the grain).
Only a weak ordinal syllable trend survives — necessary flavour, not the gate.

This is consistent with `eb335974`'s structural finding (the sonority is a weak,
coarse word-discriminator) and now localizes the failure precisely: on the
**clean, isolated, single-talker FSDD total-energy envelope**, the sonority
landscape has **no stable manner/syllable valley structure** for the segmenter to
lock onto. The energy envelope of a single short digit does not present
consistent, speaker-robust interior minima at the syllable boundaries.

### The precise next (structural, no accuracy chase)

The blocker is the SIGNAL the segmenter reads, not the segmenter. The
`detect_sonority_valleys` minima-on-total-energy is too shape-unstable across
speakers to yield a stable grain. The fix is to **fix the fixer**
(`ozma_fix_the_fixer`) — give the segmenter a more speaker-robust sonority track,
not to tune `depth_threshold` (no stable threshold exists to tune to):

1. **Segment on the graded TFS SONORITY/periodicity track, not raw total energy.**
   The voicing axis already separates voiced↔unvoiced at d′=6.0 (`stage2_sonority`
   PART 1). Valleys of the *periodicity* envelope (sonorant-nucleus vs
   obstruent/silence) should be far more speaker-robust than energy minima —
   re-run this exact gate with `total_env` ← the TFS voicing track and re-read
   the plateau/coherence.
2. If a stable, coherent grain emerges on the periodicity track, the Stage-2
   segmenter half is admitted and Stage 2 completes; if not, the precise next is a
   coarser landmark (onset/offset of voicing, T7 transitions) rather than minima.

No `depth_threshold` value is a fix: the curve has no shelf, so there is nothing
to tune to. The structural lever is the SIGNAL the valleys are detected on.

```
===MARKER_STAGE2_SEGMENTATION_GATE_COMPLETE===
```
