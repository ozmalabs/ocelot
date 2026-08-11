# Frication split — HPSS harmonic/percussive + a frication channel, fused by weighted-admissibility

**Status: HONEST KILL on accuracy, with a clear two-part diagnosis.** (1) **HPSS HURT the
harmonic path** — HPSS-harmonic 45.4% vs the no-HPSS pairing **62.2%** (−16.8 pts): the
median-filter separation denudes the formants on short 8 kHz digits. (2) The frication channel
**clears the six-sink** (the named goal: `two/four/three→six` 150→69 confusions) **but does not
net-improve accuracy** (fused 42.9% vs HPSS-harmonic 45.4%, −2.5 pts), because the root limiter is
the FSDD corpus band-limit (native 8 kHz → 4 kHz ceiling) — the dominant /s/ frication energy was
never recorded. The split is the right *structure*; the walls are (a) HPSS-over-short-digits and
(b) the band-limited corpus — not the recognition logic. FSDD digits, full token, cross-speaker
LOSO, held-out speaker never banked, chance 0.100, n=3000, elapsed 2141 s.

Script: `scripts/frication_split.py`. Run: `python -m scripts.frication_split`
(full output captured at `/tmp/frication_split_full.log`, ends with the
`FRICATION_SPLIT_COMPLETED` marker + a `FRICATION_SPLIT_EXIT=0` line; pgrep-verified the
process ran on one core at ~100% CPU and exited).

## The problem this targets

The Viterbi-pairing recogniser (`scripts/viterbi_pairing.py`, commit `104a75bf`) reached
**62.2%** LOSO. The gap to the **83.5%** full-envelope exemplar bank is dominated by
**frication**: the voiced-frame LPC formant tracker has no good candidate at broadband /
unvoiced /s/ bursts, so `six` is the confusion sink (`two→six`, `four→six`, `three→six`). The
voiced path is structurally **blind** to the unvoiced evidence — it only reads frames the energy
gate calls voiced, and even there the LPC poles through frication are garbage.

## The fix — separate, handle each, fuse

1. **HPSS** (Fitzgerald median-filter, owned numpy/scipy DSP, no net). Median-filter the
   magnitude spectrogram along TIME → harmonic estimate (horizontal formant ridges), along FREQ
   → percussive estimate (vertical transients = frication/bursts). Soft Wiener masks, applied to
   the complex STFT, inverse-STFT (owned overlap-add) → a harmonic signal and a percussive
   signal.
2. **Harmonic path.** Run the Viterbi-pairing formant tracker (hardened-LPC + transition-
   preserving pseudo-Huber penalty) on the **harmonic** signal → order-N dynamics → graph-
   resident DTW. **Recogniser UNCHANGED** — `order_n_time`, `trajectory_feature`,
   `dtw_predict_term`, `build_corpus`/eval logic all imported verbatim from
   `scripts/formant_trajectory_dynamics.py`; only `ftd.formant_track` is set to the pairing
   tracker (exactly as `scripts/viterbi_pairing.py` does — donkey-audited at runtime by
   `assert ftd.formant_track is viterbi_pairing.viterbi_formant_track`).
3. **Frication path** (owned 4-dim feature, no fit). STATED feature:
   - `[0]` high-band fraction — mean over time of (energy ≥ 3 kHz)/(total), full spectrogram.
   - `[1]` spectral centroid (Hz), full spectrogram.
   - `[2]` high-band PEAK fraction — 90th percentile over time of the per-frame high-band
     fraction (the brief intense /s/ burst, which a mean over a long voiced token dilutes).
   - `[3]` onset position [0,1] — energy-weighted temporal centroid of the high-band PERCUSSIVE
     energy (where the turbulence sits in the token).
   Per-digit template = mean profile over TRAIN speakers, z-scored by TRAIN pooled std. **A
   direct diagnostic drove a feature correction**: the HPSS-*percussive* high-band fraction
   SMEARS the /s/ cue, whereas the RAW full-spectrogram high-band fraction separates six (0.067)
   from two (0.006) and four (0.002) cleanly — so the spectral-shape dims read from the full
   magnitude; the percussive part is used only for the temporal onset dim.
4. **Fusion by weighted-admissibility** (owned; NOT a dot product). Each path is a soft excluder
   `a_*(w) = exp(−d_*(w)/τ_*)`; the recognition is `argmax_w a_H(w)·a_F(w)` — the **soft-AND**
   (intersection) of two admissibilities. Computed in **log space** (`argmax (log a_H + log a_F)`)
   for numerical stability (a direct `exp` underflows to 0 for every digit when distances ≫ τ,
   collapsing argmax to the first key — a bug that first made fusion always predict "zero").
   τ_H, τ_F = the median TRAIN across-digit *spread* of each channel (its discriminative dynamic
   range — NOT the median nearest distance, which is ~0 for the harmonic correct class and made
   τ_H collapse, the channel-dominance bug). Frication is the **less-trusted** excluder (weak
   cross-speaker), so it is **bounded**: its log-admissibility is clamped to `[−FRIC_CLAMP, 0]`
   so it can only break a harmonic near-tie (where the six-sink lives), not override a confident
   harmonic margin. The verdict is insensitive to the clamp value (see below).

## Donkey audit

- HPSS = owned numpy/scipy (`scipy.ndimage.median_filter` + `np.fft` rfft/irfft overlap-add). No
  net, no `.fit()`.
- Harmonic formant tracking = `viterbi_pairing.viterbi_formant_track` (owned numpy LPC + Levinson
  + forward-DP). Recogniser logic UNCHANGED (runtime assert verifies the patch identity).
- Frication feature = owned numpy spectral statistics. No fit.
- Fusion = weighted-admissibility (product of `exp(−d/τ)` soft excluders, in log space). No
  learned weight, no net.
- Templates / τ / z-stats = TRAIN speakers only; LOSO held-out speaker NEVER banked. CortexLoop
  and `solve_for_n.py` untouched.

## Results (full FSDD, n=3000, cross-speaker LOSO)

| recogniser | accuracy |
|---|---|
| HARMONIC-only (pairing tracker on the **HPSS harmonic** part) | **45.4%** |
| FRICATION-only (4-dim percussive/spectral descriptor) | 19.6% |
| **FUSED — bounded-frication weighted-admissibility** | **42.9%** |
| ...variant — unbounded symmetric soft-AND | 32.3% |
| Viterbi-PAIRING reference (**no HPSS**, no frication) | **62.2%** |
| full-envelope DTW exemplar 1-NN (the bank) | **83.5%** |

Per-speaker fused: george 46.2, jackson 47.0, lucas 35.8, nicolas 34.0, theo 43.2, yweweler 51.2.

**Six-sink** (the named confusion sink, `into → six`, harmonic → fused):

| pair | harmonic | fused |
|---|---|---|
| two → six | 59/300 | 20/300 |
| four → six | 31/300 | 10/300 |
| three → six | 60/300 | 39/300 |
| (sum) | **150** | **69** |
| seven → six | 23/300 | 16/300 |
| six → seven | 25/300 | 39/300 |

The sink more than halves (150 → 69). `two→six` and `four→six` clear hardest (the frication cue is
real for those); `three→six` only partly clears (/θ/ in "three" is also 3–4 kHz broadband, so the
frication channel cannot separate it from /s/), and `six→seven` actually *worsens* (both are /s/
fricatives — frication cannot tell them apart and adds noise to that pair).

### Clamp diagnostic (quick, 6/spk — NOT a tuning sweep; reported for honesty)

| FRIC_CLAMP | harmonic | fused | symmetric | sink (two/four/three→six) |
|---|---|---|---|---|
| 0.15 | 45.8% | 43.9% | 35.6% | 21 → 7 |
| 0.30 | 45.8% | 36.7% | 35.6% | 21 → 2 |
| 0.50 | 45.8% | 35.6% | 35.6% | 21 → 1 |

The tighter the clamp, the closer fused → harmonic-only (protects accuracy, clears less of the
sink); the looser, the closer fused → the worse symmetric soft-AND. **At no bound does fusion
exceed the harmonic-only ceiling** — clearing the sink costs as many tokens elsewhere as it
saves. So `FRIC_CLAMP` is frozen at the small near-tie-only value (0.15), not tuned.

## Verdict and the two limiters

```
Q1 HPSS-harmonic vs pairing : harmonic 45.4% vs 62.2% (−16.8 pts) -> HPSS does NOT help the harmonic path
Q2 fusion vs HPSS-harmonic  : fused 42.9% vs harmonic 45.4% (−2.5 pts) -> frication channel does NOT net-help
beats Viterbi-PAIRING 62.2% : NO (42.9% vs 62.2%, −19.3 pts)
six-sink (two/four/three->six): harmonic 150 -> fused 69 (CLEARED)
vs full-envelope exemplar   : fused 42.9% / exemplar 83.5% (51% of the bank)
```

There are **two distinct findings**, and the prediction was half right (the six-sink cleared) and
half wrong (it did not net-help):

**Limiter 1 — HPSS denudes the harmonic path on short 8 kHz digits.** The whole motivation was
"HPSS cleans the harmonic formants." It does the opposite here: the median-filter harmonic
estimate over a ~0.4 s digit at FS=8000 (STFT 512/128) is too aggressive — it smears the formant
ridges and the soft Wiener mask removes formant energy along with the frication, so the pairing
tracker on the *harmonic* signal (45.4%) is **16.8 pts worse than on the raw signal (62.2%)**.
The harmonic-extraction time-median needs more frames than a short digit affords, and the
8 kHz / 512-FFT frequency grid is too coarse for the time-median to find clean horizontal ridges.
This is the dominant loss; the frication fusion is then improving a path that HPSS already broke.

**Limiter 2 — the FSDD corpus is band-limited below the /s/ frication band.** The frication
channel does exactly what it was built to do — it **clears the six-sink** (150 → 69) — but it does
**not net-improve** accuracy, and the reason is the corpus, not the structure. **FSDD is recorded
NATIVELY at 8 kHz** (verified: `6_george_0.wav` reports `fs=8000`), so its spectrum is
hard-band-limited to 4 kHz. The dominant /s/ frication energy (4–8 kHz in natural speech) **was
never captured**. Only the weak 3–4 kHz tail survives — enough to separate `two/four`-vs-`six`,
but `three` (/θ/ is also 3–4 kHz broadband) overlaps `six`, `six`↔`seven` (both /s/) cannot be
told apart, and the cue is too noisy cross-speaker (per-token std ≈ the between-digit mean) to
net-help. HPSS + frication + weighted-admissibility fusion is the **right structure**; the
**band-limited corpus is the wall** on the frication side.

**Next limiter / what to try next.**
- The frication idea needs **wider-band audio**: a 16 kHz digit corpus that actually contains the
  4–8 kHz fricative band. A sharper frication feature cannot recover energy the recording never
  had — this is the honest ceiling on the frication channel for FSDD.
- The harmonic idea needs **HPSS that survives short digits**, or to be dropped: run the pairing
  tracker on the **raw** signal (the 62.2% path) and add only the frication *channel* (computed
  from the raw STFT, which already separates two/four-vs-six) as a bounded excluder — i.e. keep
  the frication fusion but skip the harmful harmonic-extraction step. The infrastructure here
  already supports that (the frication feature reads the full magnitude spectrogram, not the
  percussive reconstruction).
- Or **QCP-FB candidates** to sharpen the harmonic path on what *is* present below 4 kHz (the
  survey's other named lever).

## What is reusable

- `hpss()` — owned Fitzgerald median-filter HPSS (returns harmonic signal, percussive signal,
  percussive magnitude, full magnitude). Works; just not a net win on short 8 kHz digits.
- `frication_profile()` — owned 4-dim frication descriptor; the high-band-fraction / centroid /
  high-band-peak dims separate the /s/ digits on what survives below 4 kHz.
- `evaluate_fusion()` — weighted-admissibility (log-space soft-AND of two soft excluders) with a
  bounded less-trusted channel, τ from TRAIN across-digit spread (the correct scale; the median
  *nearest* distance collapses τ_h to 0). This fusion machinery is the reusable piece — point its
  harmonic excluder at the raw-signal pairing path to test the "frication channel without the
  harmful HPSS step" variant above.
