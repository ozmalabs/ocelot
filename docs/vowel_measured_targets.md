# Vowel AbS: per-corpus measured targets + cleaner nucleus + band-adaptive assignment

**Named fix for the corrected diagnosis (commit a0cabc7b).** The AbS vowel recogniser
stalled at **51.3%** (vs 1-NN **65.1%**). The corrected diagnosis: not the front-end
ear resolution (a0cabc7b killed that), but the forward model's **citation
Peterson-Barney formant table mismatching the coarticulated FSDD vowels** — e.g. /uw/
in "two" fronted (no 870 Hz F2), /iy/ in "three" resonating lower than 2290.
**Proposed fix:** measure the realized per-vowel targets from the corpus instead.

Script: `scripts/solve_for_n_vowel_measured.py` (full run captured to
`/tmp/vowel_measured_full.log`, end marker `SOLVE_FOR_N_VOWEL_MEASURED_COMPLETED`,
pgrep-verified completed; isolation in `/tmp/vowel_isolate.log`).

---

## (1) What was wired — donkey audit

Three **owned-DSP** changes (measured statistics, no net/fit/gradient); the agent's
cognition (forward model + formant-frame weighted-admissibility match + speaker VTL
search) is **imported UNCHANGED** from `scripts/solve_for_n_vowel.py`:

1. **Per-corpus measured formant targets** — for each vowel, realized F1/F2/F3 = robust
   **median** of the band-adaptive formant estimates over the **TRAIN** speakers' nuclei.
   A train-only measured statistic (like a corpus-counted n-gram). Replaces the citation
   `VOWEL_FORMANTS` table.
2. **Cleaner nucleus extraction** — among the top-N high-energy voiced 40 ms windows,
   pick the one with the **lowest log-mel spectral flux** to its temporal neighbours
   (the steadiest steady-state, away from coarticulated consonant-transition edges).
3. **Band-adaptive formant assignment** — assign frequency-ordered stable LPC-pole
   resonances to the F1/F2/F3 slots by **order-preserving nearest-assignment in
   log-frequency** to the targets (no fixed 900 Hz floor).

**LOSO discipline (verified):** targets are measured inside each fold from
`train_items` only (`[it for it in items if it["speaker"] != held]`); the held-out
speaker's clips are never in that set, so its targets never see its own data. The fold
audit prints per-fold targets — they differ across folds, confirming the measurement is
fold-local. 1-NN bank is likewise train-only; held-out never banked.

**Forward model + match + speaker search unchanged (verified):** `VowelSourceFilterModel`,
`formant_admissibility`, `relative_formants`, the VTL `scale_grid` search, and the
citation baseline `abs_recognise_formant` are imported verbatim — not re-authored.
`scripts/solve_for_n.py` (flat solver) and the CortexLoop are untouched.

---

## (2) Results — LOSO, cross-speaker, n=1500 (5 vowels, chance 20%)

| recogniser | accuracy |
|---|---|
| AbS citation-table formant (baseline) | **52.3%** (51.3% with the old nucleus) |
| AbS **measured-target** formant (the fix) | **32.4%** |
| 1-NN exemplar baseline (train-only) | 63.9% |

The measured-target recogniser is **WORSE** than the citation baseline (32.4% vs 52.3%).

### Measured vs citation targets (median over all speakers)

| vowel | citation F1/F2/F3 | measured F1/F2/F3 |
|---|---|---|
| ao | 570 / 840 / 2410 | 487 / **850** / 2364 |
| eh | 530 / 1840 / 2480 | 546 / **1663** / 2625 |
| ih | 390 / 1990 / 2550 | 434 / **1908** / 2601 |
| iy | 270 / 2290 / 3010 | 382 / **2165** / 3191 |
| uw | 300 / **870** / 2240 | 361 / **1506** / 2255 |

**The diagnosis's premise is confirmed at the measurement level:** /uw/ F2 is realized at
**1506 Hz**, not the citation 870 — fully fronted, exactly as predicted. /iy/ F2 is
2165, below the citation 2290. The measured targets ARE the realized coarticulated
vowels. **But fixing the table did not fix recognition.**

### Confusion — measured-target (the fix), row=true col=pred

```
       ao    eh    ih    iy    uw
ao:    19     9   155    55    62      <- ao COLLAPSES (was clean at 288 under citation)
eh:     2   266    21     2     9
ih:     7    93    51    55    94
iy:     1     8    76    85   130
uw:     3    18   103   111    65
```

Under the citation table `ao` was recognised cleanly (288/300). Under the measured
targets `ao` collapses (19/300) — because the measured back/high vowels now overlap and
the band-adaptive estimator no longer floors them apart. The uw/iy highs and ao/eh
backs did **not** both hold.

---

## (3) Verdict — HONEST KILL, limiter relocated

**Measured targets do NOT improve recognition; they make it worse (32.4% vs 52.3%).**
The prediction is killed. But the failure pinpoints the true limiter via a clean 2×2
isolation (full LOSO, steady nucleus, n=1500):

| targets | input estimator | accuracy |
|---|---|---|
| citation | citation fixed-gate | **52.3%** |
| citation | band-adaptive | 41.5% |
| **measured** | citation fixed-gate | **52.1%** |
| **measured** | band-adaptive | 32.4% |

Two facts fall out:

- **Swapping citation→measured targets, holding the estimator fixed, changes nothing**
  (52.3% → 52.1%). **The table was never the limiter.** The corrected diagnosis is
  itself wrong: realized targets and citation targets give the same accuracy.
- **The band-adaptive input estimator is a regressor** (52→41 / 52→32), because its
  neutral cross-vowel anchor pulls every input's poles toward the cross-vowel mean,
  erasing the contrast. (Cleaner nucleus alone is marginal: +1.0 pt, 51.3→52.3%.)

### The actual limiter: the realized vowels are not separable in formant-frame space

The pairwise distance between the **measured** targets in the speaker-relative
log-formant space the match actually uses (small = confusable):

```
      ao    eh    ih    iy    uw
ao: 0.00  0.46  0.68  0.83  0.63
eh: 0.46  0.00  0.26  0.48  0.24
ih: 0.68  0.26  0.00  0.25  0.07   <- ih/uw = 0.07: realized uw == ih
iy: 0.83  0.48  0.25  0.00  0.24
uw: 0.63  0.24  0.07  0.24  0.00
```

The four front/high vowels (eh, ih, iy, uw) sit **0.07–0.26 apart** — one indistinct
cloud; only `ao` separates (0.46–0.83). The realized FSDD /uw/ ("two", fronted to
F2≈1506) lands **0.07** from /ih/: they are the same point in formant-frame space.
The data is too coarticulated for an F1/F2/F3-frame match to separate, **regardless of
whether the targets are citation or measured** — which is exactly why correcting the
targets cannot help.

The citation table's 52% was, ironically, a partial **accident of mis-assignment**: its
wrong 870 Hz floor for uw and its fixed-gate input estimator happened to push uw/ao into
a low-F2 corner away from the front cluster, buying separation the realized values don't
have. The measured targets remove that accidental separation and expose the real
overlap.

### Next limiter (pinpointed)

The F1/F2/F3 steady-state formant frame is **insufficient to separate the coarticulated
FSDD high/front vowels** — they genuinely overlap there. The next rung is **not** better
targets or a sharper ear; it is a **richer representation than three static formants**:
formant **trajectory / dynamics** (the diphthongal and coarticulatory motion that
distinguishes "two" from "six" from "three" — the order-N-over-time the memory already
flags), or higher formants / spectral detail, or dropping back to the exemplar 1-NN
(63.9%) which keeps the full envelope and already beats both AbS variants. The
single-steady-frame source-filter forward model has hit its ceiling on this corpus.

**Do NOT commit — coordinate.**
