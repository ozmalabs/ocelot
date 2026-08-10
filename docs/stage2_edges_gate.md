# Stage 2 — segmentation-coherence gate, RE-RUN on VOICING EDGES (landmarks)

The precise next from commit `f98e7206`. The two prior runs of THIS gate
(`scripts/stage2_segmentation_gate.py` on total energy,
`scripts/stage2_periodicity_gate.py` on the TFS periodicity track) both ran the
ACTUAL Stage-2 gate the curriculum names —

> *"the sonority-valley segmenter's depth-threshold **self-tunes to a stable
> lexicon grain**."* (`docs/toolbox_and_curriculum.md:345-347`)

— by **COUNTING MINIMA** (`detect_sonority_valleys`) on a per-frame envelope, and
both found **NO** self-tuning: a monotone exponential decay (no shelf),
cross-speaker grain sd **0.44** (energy) / **0.64** (periodicity) of grain, not
coherent. The DEEPER diagnosis (`docs/stage2_periodicity_gate.md`): the blocker is
the **OPERATION**, not the signal. **Valley-counting on any per-frame envelope of a
short isolated digit has no speaker-invariant shelf** — the *number and depth* of
interior minima is itself speaker-dependent (`lucas` carves 2–3× coarser). The
periodicity track is a superb voiced↔unvoiced classifier (d′=6.0, PART 1) but a
poor segmentation-by-valley-count source.

This run replaces the OPERATION with **voicing ONSET/OFFSET LANDMARKS (EDGES)**.

- Gate script: `scripts/stage2_edges_gate.py`.
- Run: `PYTHONUNBUFFERED=1 python -m scripts.stage2_edges_gate`.
- Capture: `/tmp/stage2_edges_gate_full.log`
  (end marker `===MARKER_STAGE2_EDGES_GATE_COMPLETE===`).
- pgrep-verified COMPLETED; **3000/3000** tokens had a usable periodicity track.

This is the STRUCTURAL segmentation-coherence gate (a `(G,Γ)` signal), **NOT** a
held-out recognition accuracy (`ozma_no_premature_testing_mid_curriculum`). The
corrected interior-shelf detector is reused VERBATIM and the **NUMBERS** are read,
not the boolean.

---

## (1) The edge-based segmenter + the gate (donkey audit, file:line)

**The two changes from the periodicity run are the OPERATION and the swept knob.**
Everything else — the corrected interior-shelf plateau detector, the grain-relative
coherence test, the syllable-match test, the verdict logic — is **VERBATIM** from
`scripts/stage2_periodicity_gate.py`.

- **The signal is unchanged** = the graded TFS periodicity (voicing) track,
  `scripts/stage2_edges_gate.py:periodicity_envelope` (copied VERBATIM from the
  validated T4 chain, commit `90b799c9`): native `gammatone_band` (8 bands over
  F0/low-formant place) → `band_autocorr` → `summary_autocorrelogram` →
  `periodicity_track`, per-frame periodicity strength in [0,1]. No Python DSP.
- **The edge rule** = `scripts/stage2_edges_gate.py:edge_count` — voicing
  onset/offset landmarks via a **hysteresis state machine** over the native track.
  The operating LEVEL is the **per-token median** of the periodicity track
  (self-referencing → the landmark is relative to *this token's own* voicing range,
  the speaker-robust move, not an absolute global threshold). A hysteresis band of
  width `h` straddles it: `thr_hi = level + h/2` (onset: rise above to enter
  voicing), `thr_lo = level - h/2` (offset: fall below to leave voicing). Walk
  `p[t]`: UNVOICED + cross `thr_hi` → **ONSET** landmark (→ VOICED); VOICED + cross
  `thr_lo` → **OFFSET** landmark (→ UNVOICED). The **grain = the total number of
  landmarks** = the voicing transitions per word (the sonority skeleton). Wider `h`
  → only the big sonorant↔obstruent swings cross → fewer, more speaker-robust edges
  (hysteresis rejects chatter).
- **This is the same hysteresis idea already native** in
  `runners/dsl/src/audio_primitives.rs:378` `schmitt_peaks` (a Schmitt trigger with
  a 0.7 release ratio), here applied to **TRANSITIONS** (voicing edges) instead of
  peaks. Per the task ("no Rust needed"), the edge rule runs as a thin **mechanical
  landmark transducer** over the native d′=6.0 track — a deterministic crossing
  counter, **NOT** DSP (no filter/FFT/fit), **NOT** a net, **NOT** a decision over
  graph state, **NOT** a tuned knob.
- **The swept parameter** = the **hysteresis band width** `h` (0.02…0.80, 40
  steps), NOT a valley `depth_threshold`. The sweep FINDS the plateau; it is NOT an
  accuracy fit.
- **Donkey-clean.** Only the native TFS chain + the edge rule run. No net, no
  `.fit`, no gradient, no loss, no recognition score. `CortexLoop` /
  `scripts/solve_for_n.py` UNTOUCHED; no `runners/` diff; no Rust build.
- **The corrected detector is reused unchanged**: an INTERIOR relative-flat shelf
  (`REL_TOL`, `EDGE_GUARD=3`) at a non-trivial grain (`GRAIN_FLOOR=1.0`), plus
  grain-relative coherence (`rel_cross`, `rel_tok`). The boolean is NOT
  rubber-stamped; the numbers are below.

---

## (2) The readiness verdict — do voicing EDGES self-tune? (NUMBERS, not boolean)

### (A/B) Plateau — **NO shelf.** Same monotone-decay shape as both valley runs.

The grain curve is a **pure monotone exponential decay** as `h` widens — 5.61 edges
at `h=0.02` down to 0.23 at `h=0.80`, with the relative slope essentially constant
across the whole sweep:

```
per-step |Δgrain|/grain:  min 0.051   median 0.084   max 0.117
```

A self-tuning shelf needs the relative slope to drop near 0 over a band, bracketed
by steeper descent on both sides (an interior local-derivative minimum). It never
does — a constant ~8 %/step relative slope is the signature of a pure exp decay
with **no plateau to lock onto**. **The edge rule does not self-tune** — exactly the
same failure shape the energy-valley and periodicity-valley runs produced. Changing
the operation from valleys to edges did **not** create a shelf.

### (C) Cross-speaker coherence — **improved (0.64 → 0.34) but still above the bar.**

At the diagnostic operating point `h*=0.26` (grain ≈ 2 edges):

| run | cross-speaker grain sd (of grain) | within-token sd (of grain) |
|---|---|---|
| energy valleys | 0.44 | 0.97 |
| periodicity valleys | 0.64 | — |
| **voicing edges (this run)** | **0.34** | **0.69** |

Edges are **the tightest cross-speaker grain of the three** (0.34 vs 0.44/0.64) —
the landmark *is* more speaker-robust than the valley count, as predicted. But 0.34
is still **above the 0.25 coherence bar**, and the per-speaker breakdown shows
**why**: the grain is **systematically speaker-dependent**, not noise. `lucas`
carves coarsest on almost every digit (`nine` 3.7, `one` 3.0, `zero` 2.8) while
`george` carves finest (`nine` 0.2, `one` 0.3, `zero` 0.3, `five` 0.3) — the SAME
speaker-dependent grain the deeper diagnosis named, just attenuated. Within-token sd
(0.69 of grain) is also high: even same speaker / same word, the edge count wobbles.

### (D) Manner/syllable match — **PASSES (the one prong that fires).**

```
grain-vs-syllable rank corr : +0.527   (>0 = grain tracks syllable structure)
bi-syllabic  (zero/four/seven) mean grain : 2.087
mono-syllabic                  mean grain : 1.855   (bi > mono ✓)
named targets:  seven 2.56 (~2-3 ✓)   six 2.17 (~2-3 ✓)   two 1.75 (expect ~1)
```

Edges track the sonority skeleton **ordinally**: bisyllabic words carry more voicing
excursions → more edges, and `seven`/`six` (unv-v-unv) sit above the monosyllabic
mean. This is the structural property the diagnosis hoped edges would expose, and it
is real (rank corr +0.53). But note `two` reads 1.75 not ~1 — the **absolute** edge
count is inflated by the same within-token / cross-speaker chatter that sinks (C):
the ordinal trend survives, the **quantized per-word grain does not**.

---

## (3) VERDICT — the deeper fallback (continuous-speech TP-troughs), NOT another isolated-digit tweak

```
SELF-TUNES (a stable grain PLATEAU exists)          : False  (pure exp decay, no shelf)
PLATEAU grain is non-trivial                        : False  (no plateau)
CROSS-SPEAKER coherent (rel_cross < 0.25)           : False  (0.34 — improved from 0.44/0.64 but over bar)
MATCHES lexicon manner/syllable structure           : True   (rank +0.53, bi 2.09 > mono 1.86)
>>> STAGE-2 SEGMENTER SELF-TUNES TO A STABLE GRAIN  : False
```

**Stage 2 does NOT complete. The gate does NOT fire.**

This is the **fourth** operation/signal tried on the isolated-digit
segmentation-coherence gate (energy valleys → periodicity valleys → … → voicing
edges), and the verdict is now **consistent and structural**, not a tuning miss:

1. **The edge operation was the right move in the predicted direction.** Voicing
   landmarks gave the **tightest cross-speaker grain of any run** (0.34 vs 0.44 /
   0.64) and the manner/syllable ordinal trend now passes (+0.53). The diagnosis
   ("a transition is a sign-of-slope event, less level-sensitive than a depth
   threshold") was **correct as far as it went** — edges beat valleys.

2. **But there is STILL no self-tuning plateau, and the grain is STILL
   speaker-dependent** (`lucas` coarse, `george` fine on the same words). The honest
   structural reading: **the sonority-segmentation cue is NOT cleanly present in
   isolated single digits.** A short isolated digit has too few, too-speaker-variable
   voicing transitions for ANY per-token landmark rule to quantize to a stable,
   coherent lexicon grain — improving the operation tightened the variance but did
   not create the shelf, because the shelf isn't there to find in this material.

3. **Therefore the lever is the deeper fallback the prior runs already named — NOT
   another isolated-digit tweak.** No further edge-rule variant (different
   hysteresis seeding, slope-sign instead of level-crossing, a third threshold) is
   warranted: all of them read the same impoverished single-digit voicing profile.
   The segmentation cue that *does* self-tune lives in **continuous speech**, where
   the boundary signal is the **transition-probability (TP) troughs** across a
   *stream* of syllables/words (`ozma_learns_from_sentences`,
   `scripts/sentence_learning.py`: a recurring lexicon condenses, transition info
   gain 1.21 bits, held-out next-unit prediction 1.52× the frequency baseline and
   collapses under shuffle — structure is in the ORDER). Isolated digits have no
   stream, hence no TP-trough to carve at; that is the structural reason all four
   isolated-digit gates fail.

### The precise next (structural, no isolated-digit tweak, no accuracy chase)

Move the Stage-2 segmentation half off isolated digits onto a **continuous-speech
stream** and re-run the SAME segmentation-coherence gate against **TP-trough
boundaries** (the boundary primitive that the prior continuous-speech work already
showed self-tunes and collapses under shuffle), keeping the **voicing-edge landmark
as the per-utterance sonority feature** that feeds it (it earned its place: tightest
cross-speaker grain + passing manner trend). The voicing-edge segmenter is now a
validated *tool* (a speaker-robustness-improving landmark detector), retired from
the isolated-digit gate as a *self-tuning* segmenter — the cue it needs is the
stream the isolated digit cannot provide.

```
===MARKER_STAGE2_EDGES_GATE_COMPLETE===
```
