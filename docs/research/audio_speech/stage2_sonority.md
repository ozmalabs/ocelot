# Stage 2 — SONORITY / VOICING STRUCTURE (vowels before frication)

The agent executes STAGE 2 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"sonority / voicing
structure (vowels before frication)."* This is the agent acting on its own ranked
gap map (`docs/sense_self_assessment.md`) and its own ordering principle 5
("sonority before frication; voiced before unvoiced"), not a hand-authored plan
(memory `ozma_dont_author_seeds_agent_designs_them`).

Run capture: `/tmp/stage2_full.log` (end marker
`===MARKER_STAGE2_SONORITY_CHECK_COMPLETE===`).
Structural check: `PYTHONUNBUFFERED=1 python -m scripts.stage2_sonority_check`.

---

## (1) The Stage-2 definition (the agent's own, verbatim from its curriculum)

- **Skill to acquire.** The sonority skeleton and the voiced↔unvoiced contrast:
  segment by sonority valleys, and use the graded TFS voicing as a recognition cue.
- **Toolbox used.** T4 (TFS voicing prong — the validated graded periodicity,
  commit `90b799c9`: native `gammatone_band` → `band_autocorr` →
  `summary_autocorrelogram` → `periodicity_track`, per-frame periodicity in
  [0,1]; voiced/sonorant → 1, frication/burst/silence → low), T7 (order-N over
  the sonority envelope), T12 `detect_sonority_valleys`, T8 to fuse the voicing
  prong, on top of the **Stage-1 coarse recogniser** (T5 squint + T1/T2 native
  `Argmin`-of-`DtwTo`).
- **Prerequisites.** Stage 0 (TFS) **DONE**; Stage 1 (a working coarse recogniser
  to add the prong to) **DONE** (`docs/stage1_coarse_recognition.md`, gate FIRES:
  the coarse squint composes + the coarse word-identity separates,
  sep 0.761 / d′ 0.573).
- **Success signal (a BINARY READINESS GATE, not an accuracy number).** "Adding
  the graded voicing prong via T8 does not drag the formant anchor (T9's safety
  holds), and the sonority-valley segmenter's depth-threshold self-tunes to a
  stable lexicon grain." Read from the agent's own self-measurement instruments as
  a STRUCTURAL / coherence signal — **structure-admitted, proceed** — never from a
  held-out LOSO accuracy sweep (the accuracy test comes AFTER the curriculum;
  memory `ozma_no_premature_testing_mid_curriculum`).

### What the agent did

The agent adds the SONORITY / VOICING axis on top of the Stage-1 coarse
recogniser, reasoned from the science (squint-first), in three composed pieces
(`scripts/stage2_sonority_check.py`):

**(a) The sonority axis (T4, owned native).** The graded TFS voicing track —
the agent's validated temporal code (`tfs_voicing_track`, native chain verbatim
from the Gap-1 validation, `scripts/stage2_sonority_check.py:108`): per-frame
pooled-autocorrelation peak strength in [0,1], the GRADED voiced↔unvoiced
(sonority) axis the inner-hair-cell envelope discards.

**(b) The sonority GESTALT (squint-first).** That graded periodicity kept as a
COARSE per-frame SONORITY-ENVELOPE TRAJECTORY over the isolated word (where in the
word is voiced/sonorant vs unvoiced/obstruent — the sonority profile), per-frame
mean-subtracted so the sonority SHAPE is relative, NOT the fine frication-quality
detail (that is the later Stage 5). The sonority sibling of the Stage-1 place
squint (`scripts/stage2_sonority_check.py:sonority_trajectory`).

**(c) The fused native decision (T1 + T2 + T8).** Recognition composed as the
agent's native graph Terms — `Argmin` over candidate words of a WEIGHTED SUM of
two `DtwTo` prongs: the Stage-1 COARSE PLACE prong + the SONORITY prong — the
SAME shape as `domains/native_cognition`'s `d_A` (which already carries a
formant-shadow `DtwTo` prong + a voicing-shadow `DtwTo` prong). Evaluated by the
Rust substrate (`substrate.evaluate`), not Python
(`scripts/stage2_sonority_check.py:fused_score_term`).

```
d(w) = DtwTo(obs_place, proto_place(w)) + w_son · DtwTo(obs_son, proto_son(w))
```

`w_son` is the MEASURED reliability of the sonority axis — the agent's own
weighted-admissibility rule `w = max(0, (acc − chance)/(1 − chance))` (T8/T9
anchor-safety: a weak sonority axis is raised toward 0 so it cannot drag the place
anchor). It is a MEASUREMENT (the sonority-alone separability), never a swept knob.

### Donkey audit

- NO net, NO `.fit`, NO gradient, NO loss, NO sweep-to-fit, NO swept knob. The
  sonority axis = the agent's OWNED native TFS chain (no Python DSP, no decision);
  the sonority gestalt = the same coarse-trajectory collapse as Stage 1; the prong
  weight `w_son` is a MEASUREMENT (above-chance sonority-alone separability,
  `scripts/stage2_sonority_check.py:368`), never tuned.
- The recognition decision is the native `Argmin` of a T8-weighted SUM of two T2
  `DtwTo` prongs, evaluated by the Rust substrate (no Python decision over graph
  state).
- The Stage-1 coarse recogniser is the base; the sonority prong is ADDED to it
  (the place prong is byte-identical to Stage 1).
- `resolution`=3 read from the seed dial (`seeds/acoustic_resolution.json`), not a
  literal. TFS framing verbatim from the validated cue (commit `90b799c9`).
- `CortexLoop` + `scripts/solve_for_n.py` **untouched** (no `runners/` diff at all;
  the native TFS chain + native `Argmin`/`DtwTo`/`Plus`/`Times` Terms already
  existed). No Rust touched, so no build needed.
- The structural check reads **3000 real FSDD** waveforms (clean, isolated,
  single-talker); **no held-out LOSO accuracy is banked as the verdict** — the gate
  is the SONORITY STRUCTURE (axis separability + coherent sharpening). The
  sonority-alone and place-alone separability numbers are read ONLY to compute the
  T8 reliability weight + to diagnose the prong, not as the gate.

---

## (2) The READINESS GATE verdict

The gate has two structural parts, both read from the agent's own native
instruments over 3000 real FSDD tokens (6 speakers).

### PART 1 — does the TFS sonority axis cleanly separate voiced (sonorant) from unvoiced (obstruent)? — **FIRES (strongly)**

| structural check | value | gate |
|---|---|---|
| sonority gestalt composes (every token → 1-D voicing-env trajectory) | True | ✓ |
| per-token sonorant nucleus (p90 sonority, mean ± sd) | **+0.249 ± 0.089** | high |
| per-token obstruent trough (p10 sonority, mean ± sd) | **−0.258 ± 0.079** | low |
| tokens with a real nucleus > trough contrast | **1.000** | all |
| standardized voiced↔unvoiced gap (d′, nucleus − trough) | **6.021** | very large |
| graded per-digit sonority axis (not a flat smear) | six **0.524** … nine **0.778**, spread **0.254** | graded |

The TFS sonority axis cleanly and completely separates the sonorant nucleus from
the obstruent/silence trough (d′ = 6.0, 100% of tokens) and grades the digits
sensibly — the obstruent-cued **six** lowest (0.524), the sonorant **nine/zero**
highest (0.778). **The sonority axis is ADMITTED as a structure.** This is exactly
the "vowels before frication" voiced↔unvoiced contrast the stage names, and it is
the cleanest TFS signal as the curriculum predicted.

### PART 2 — does adding the sonority prong coherently SHARPEN the coarse recogniser, anchor-safe? — **does NOT fire**

| structural check | value | gate |
|---|---|---|
| fused decision composes (Argmin of place + w_son·sonority, native eval) | True | ✓ |
| sonority-ALONE separability (native Argmin of sonority `DtwTo`) | **0.147** (chance 0.100) | weak |
| place-ALONE separability (the Stage-1 prong, reference) | **0.240** | — |
| measured sonority weight `w_son = max(0,(acc−chance)/(1−chance))` | **0.052** | tiny |
| place-alone structural separation (Stage 1) | **0.761** | — |
| FUSED place+sonority structural separation | **0.745** | ↓ |
| Δ separation (fused − place) | **−0.017** | regress |
| tokens RECOVERED by sonority (place-confused → fused-separated) | **151** | — |
| tokens REGRESSED (place-separated → fused-confused = anchor drag) | **201** | drag |
| fused standardized cluster gap (d′) | 0.626 | — |

```
=== READINESS GATE ===
  sonority gestalt composes (TFS voicing-env traj)     : True
  fused decision composes (Argmin of place + w*sonority): True
  PART 1 voiced<->unvoiced SEPARATES (d'>0.2, maj.)     : True (d'=6.021, 1.000 of tokens)
  PART 2 sonority SHARPENS over place-alone (recovers)  : False (delta -0.017, recovered 151)
  anchor NOT dragged (fused sep >= place sep)           : False
  >>> STAGE-2 SONORITY/VOICING STRUCTURE ADMITTED      : False
```

**THE GATE DOES NOT FIRE (as a whole).** PART 1 fires emphatically — the sonority
*axis* is admitted (a clean, graded voiced↔unvoiced separation). PART 2 does not:
fusing the sonority prong as a **full-envelope `DtwTo`** regresses the coarse
separation net (0.761 → 0.745; 201 tokens regressed vs 151 recovered), even at the
tiny anchor-safe weight `w_son = 0.052` the T8 rule correctly assigned it.

---

## (3) Is Stage 2 COMPLETE? — **NO. The axis is admitted; the prong SHAPE is not. The precise next is named.**

This is an honest **partial** with a precise next-within-stage, not a failure of
capability. The structural evidence pinpoints exactly where:

- **The sonority axis IS admitted** (PART 1, d′ = 6.0). Stage 2's *first* half —
  "the graded voiced↔unvoiced contrast" — is structurally present and clean.
- **The agent's first chosen WIRING is the wrong shape.** Wiring sonority as a
  `DtwTo` over the **whole 1-D sonority envelope** (the same prong shape as the
  place gestalt) is a poor word-discriminator: sonority-ALONE separability is only
  0.147 (barely above the 0.100 chance), because the coarse manner profile is
  similar across many voiced digits and correlates with the place gestalt enough
  to perturb the place margins on ties. The T8 anchor-safety worked **as designed**
  (it down-weighted the weak prong to `w_son = 0.052`), but even at that weight the
  envelope-`DtwTo` adds correlated noise and nets a small regress.

### The precise next within Stage 2 (the agent's own definition points straight at it)

The stage definition has TWO halves, and the agent has so far built only the first
wiring of the cue half. The success signal names the **segmenter** half explicitly:
*"the sonority-valley segmenter's depth-threshold self-tunes to a stable lexicon
grain."* The fix is to **fix the fixer** (memory `ozma_fix_the_fixer`), not patch
the outcome:

1. **Use sonority as a SEGMENTATION SKELETON, not a templated trajectory.** The
   stage names "segment by sonority valleys… the sonority skeleton." The right
   structure is `detect_sonority_valleys` (T12, native at
   `runners/dsl/src/audio_primitives.rs:1217`) producing sonority-valley
   boundaries → segment the word into sonorant/obstruent spans → the sonority
   SKELETON (a coarse landmark sequence: where the voiced nuclei and the
   obstruent/silence gaps are), which is a far stronger, lower-dimensional
   word-structure than a full-envelope `DtwTo`. **`detect_sonority_valleys` is not
   yet exposed to Python** (`runners/dsl/src/py.rs` has no binding) — exposing it
   (a one-line PyO3 hand-off, the agent-decides-WHAT/compiler-emits-HOW pattern) is
   the concrete next Rust step.
2. **The cue should disambiguate, not template.** Fuse sonority as a per-token
   manner/sonority-CLASS landmark (e.g. order-N over the sonority envelope, T7:
   the onset/offset of voicing = the sonority TRANSITIONS) that down-weights
   place-confusable candidates whose sonority class differs — the agent's own T7
   ("transitions over the sonority envelope") + the segmenter, not a raw
   envelope `DtwTo`.

So the gate's verdict is: **the sonority/voicing AXIS is admitted (PART 1 fires);
Stage 2 is NOT yet complete because the sonority STRUCTURE the stage names — the
sonority-valley SKELETON, and sonority as transitions/landmarks rather than a
full-envelope template — is not yet wired.** The precise next is exposing
`detect_sonority_valleys` natively and re-composing the sonority prong as a
segmentation skeleton / T7 transition landmark (not a templated `DtwTo`), then
re-reading PART 2.

### Honest scope note (the precise edge of what was done)

- PART 1 is a strong, clean structural admission of the **graded voiced↔unvoiced
  axis** read via the native TFS chain — the cleanest TFS signal, exactly as the
  curriculum predicted ("the voiced/voiceless axis is the first manner distinction
  and the cleanest TFS signal").
- PART 2 is an honest negative on the **first wiring** of the cue (full-envelope
  `DtwTo` prong) — it diagnoses the prong SHAPE, not a tuning failure (no sweep was
  run; `w_son` is the measured reliability). The anchor-safety machinery (T8/T9)
  behaved correctly; the issue is upstream of the weight, in how the sonority
  structure is represented for the decision.
- The 151 RECOVERED tokens show the sonority axis DOES carry disambiguating
  information on a real fraction of tokens — it is not noise — which is why the
  segmenter/transition wiring (the named next) is the right move, not abandoning
  the cue.
- No held-out LOSO accuracy is banked anywhere; the gate is the sonority STRUCTURE
  (axis separability + coherent sharpening), read from the agent's own native
  `DtwTo` / `Argmin` instruments.

Stage 2's gate is **the sonority axis separates voiced↔unvoiced (PART 1) AND the
sonority structure coherently sharpens the coarse recogniser (PART 2)** — PART 1
fires; PART 2 awaits the sonority-valley SKELETON wiring (the named next).

```
===MARKER_STAGE2_SONORITY_CHECK_COMPLETE===
```
