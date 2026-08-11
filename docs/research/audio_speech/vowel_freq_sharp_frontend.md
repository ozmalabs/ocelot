# Freq-sharp front-end for high-vowel formants — the named fix for the moved limiter (b2886dc7)

## What was run

`scripts/vowel_freq_sharp_frontend.py` — replaces ONLY the input formant estimator of the
b2886dc7 vowel recogniser with a **frequency-sharp two-ears front-end**. The forward model
(`VowelSourceFilterModel`), the formant-frame weighted-admissibility match
(`formant_admissibility` / `relative_formants`), the data harness (`load_vowel_dataset`),
and the LOSO cross-speaker split are **imported UNCHANGED** from `scripts/solve_for_n_vowel.py`
(verified: `git diff scripts/solve_for_n_vowel.py` is empty — the baseline file is untouched).

n = 1500 vowel nuclei, 5 vowels (ao/eh/ih/iy/uw), 6 speakers, leave-one-speaker-out,
held-out speaker never banked.

## Front-end method (stated)

Two-ears fusion (option c):
- **F1 ear** = robust LPC pole (order 12) in 180–1000 Hz.
- **F2/F3 ear** = frequency-sharp 8192-pt FFT (~1 Hz grid) + pre-emphasis (flatten glottal
  tilt) + 7-bin smoothing (merge pitch harmonics within a formant lobe); strongest local
  maximum in the F2 band (900–2600 Hz) and F3 band (2400–3800 Hz).

Donkey audit: owned numpy DSP only (FFT + LPC roots), no net, no `.fit()`, no gradient.
Match + forward model unchanged by diff. Held-out speaker never banked. CortexLoop / flat
`solve_for_n.py` untouched.

## (1) DIRECT — does it resolve the high formants? PARTIALLY.

| vowel | true (F1,F2,F3) | LPC-10 | FREQ-SHARP |
|------|-----------------|--------|------------|
| ao | (570, 840, 2410) | (487, 867, 2310) | (480, **959**, 3127) |
| eh | (530, 1840, 2480) | (541, 1580, 2461) | (529, 1690, 2635) |
| ih | (390, 1990, 2550) | (436, 1790, 2520) | (433, **2020**, 2653) |
| iy | (270, 2290, 3010) | (403, **1691**, 2156) | (401, **1838**, **3247**) |
| uw | (300, 870, 2240) | (368, **1557**, 2251) | (366, **1678**, 3231) |

- iy: F2 1691 → 1838 (closer to but still well below true 2290); F3 2156 → **3247** (now
  near true 3010 — the sharp ear *does* recover iy's high F3 that LPC-10 merged).
- ih: F2 1790 → 2020 (now ≈ true 1990 — clean).
- **uw**: F2 1557 → 1678 (still high; true 870 NOT recovered).
- iy↔uw F2 Fisher separation: 0.34 (LPC-10) → 0.23 (freq-sharp) — slightly WORSE.

## (2) RECOGNITION — net DOWN, but a real high-vowel gain inside it.

| front-end | accuracy (n=1500) |
|-----------|-------------------|
| AbS LPC-10 (the moved limiter, b2886dc7) | **51.3%** |
| AbS FREQ-SHARP (this fix) | **46.6%** |
| 1-NN exemplar baseline | 65.1% |
| chance | 20.0% |

Per-vowel correct (diagonal of the confusion matrices):

| vowel | LPC-10 | FREQ-SHARP | Δ |
|------|--------|-----------|----|
| ao | 285/300 | 109/300 | **−176** |
| eh | 274/300 | 218/300 | −56 |
| ih | 133/300 | 210/300 | +77 |
| iy | 4/300 | 24/300 | +20 |
| uw | 74/300 | 138/300 | **+64** |

The fix did what it targeted on the **high vowels**: uw nearly doubled (74→138),
iy 6× (4→24), ih +77. But the pre-emphasis + fixed 900 Hz F2-band floor broke the
**back/low vowels** the LPC handled fine: ao collapsed 285→109 (now mis-read as uw,
because ao's true F2≈840 sits below the 900 Hz floor, so the sharp ear grabs a spurious
higher peak). The −232 on ao/eh outweighs the +161 on ih/iy/uw → net 51.3% → 46.6%.

## VERDICT — HONEST KILL, with the next limiter pinpointed.

The freq-sharp front-end does **NOT** clear the high-vowel limiter as a net win, and does
not beat LPC-10 (46.6% < 51.3%) or 1-NN (65.1%). It **partially** resolves the high formants
(iy's F3 recovered to ~3247; ih clean at 2020; uw recognition doubled) but introduces a new
back-vowel error (the fixed F2-band floor + pre-emphasis breaks ao), and crucially **fails on
the two formants the task named**: iy F2 stays ~1838 (not 2290) and uw F2 stays ~1678 (not 870).

The next limiter is now located precisely, and it is **not the estimator's frequency
resolution** — a diagnostic that picks the *lowest* prominent local max recovers ao's
F2 (790 ≈ true 840) but **still reads uw F2 = 1562 and iy F2 = 1684**. The realized
FSDD nuclei simply do not carry their canonical formants:

- **uw** is extracted from "two" — a *fronted/coarticulated* /uw/ whose strongest mid-band
  energy is ~1000–1700 Hz, with little energy at the canonical 870 Hz. There is no 870 Hz
  F2 in the signal to resolve.
- **iy** is extracted from "three" — its dominant resonance sits at ~1900 Hz, with the high
  formant cluster at ~3200 Hz (= F3). The canonical 2290 Hz F2 is not the dominant peak.

So the real next limiter is the **forward model's formant TABLE / the data mismatch**: the
Peterson-Barney citation-form formants the synthesiser uses do not match these connected-
digit, coarticulated nuclei. The fix is NOT a sharper ear — it is (a) measured per-corpus
formant targets for the forward model instead of citation-form Peterson-Barney, and/or
(b) extracting cleaner steady-state nuclei (the current energy×(1−ZCR) window catches
coarticulated transitions), and/or (c) band-adaptive formant assignment (no fixed 900 Hz
F2 floor) so back and front vowels are not forced through the same bands.

The freq-sharp ear is a genuine partial sense improvement (recovers iy F3, ih F2, doubles
uw) — but it is dominated by the data/forward-model mismatch, which is the rung below it.
