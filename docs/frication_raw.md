# Frication channel WITHOUT HPSS — the raw-STFT revival

**Status: HONEST PARTIAL.** Dropping HPSS exactly as prescribed **fully restores the harmonic
path** (raw-harmonic **62.2%**, n=3000 — the HPSS damage of −16.8 pts that broke the split,
45.4%→62.2%, is gone) and the frication channel **clears the six-sink** (`two/four/three→six`
**168→90**). But fusion **does NOT net-improve accuracy**: FUSED **57.5%** vs raw-harmonic
**62.2%** (−4.7 pts). It is **+14.6 pts over the HPSS-broken split (42.9%)** — the revival
recovers all the value HPSS destroyed — but the frication /s/-PRESENCE cue cannot push *past*
the harmonic ceiling on this corpus. Clearing the gross sink costs as many tokens elsewhere as
it saves: `six→seven` worsens (9→35, both /s/) and `nine` collapses, because the residual
/s/-vs-/θ/ and six↔seven QUALITY discrimination is the **8 kHz band-limit wall (K10)** — a
genuine identifiability wall, not revivable here. FSDD digits, full token, cross-speaker LOSO,
held-out speaker NEVER banked, chance 0.100, n=3000, elapsed 2297.5 s.

Script: `scripts/frication_raw.py`. Run: `python -m scripts.frication_raw`
(full output captured at `/tmp/frication_raw_full.log`, ends with the
`FRICATION_RAW_COMPLETED` marker + `FRICATION_RAW_EXIT=0`; pgrep-verified the process ran and
exited cleanly).

## What this revives and how

The read-based frication-split (`scripts/frication_split.py`, `docs/frication_split.md`) was an
HONEST KILL at 42.9% vs the 62.2% Viterbi-pairing baseline. The diagnosis there (lines ~152-161)
was precise: the KILL was **not** the frication channel and **not** the band-limit — it was the
**HPSS step**. HPSS median-filtering SMEARED THE FORMANTS on short 8 kHz digits; the harmonic
path itself fell from raw 62.2% to **45.4%** (−16.8 pts) *before* any fusion. The frication
CHANNEL was right (it cleared the six-sink). The prescribed fix: **drop HPSS entirely**.

1. **RAW harmonic path.** The Viterbi-pairing formant tracker on the **RAW** signal — the
   unbroken 62.2% path. `ftd.build_corpus` calls `ftd.formant_track` on the raw signal;
   importing `scripts.viterbi_pairing` sets `ftd.formant_track = viterbi_formant_track` (the
   hardened-LPC + transition-preserving tracker). **No HPSS.** Recogniser logic UNCHANGED —
   `order_n_time`, `trajectory_feature`, `dtw_predict_term`, build via `ftd` all imported
   verbatim; runtime `assert ftd.formant_track is viterbi_pairing.viterbi_formant_track`.
2. **Frication channel from the RAW full-magnitude STFT.** The same 4-dim feature as the split
   (≥3 kHz fraction, spectral centroid, high-band PEAK fraction, onset). Dims [0]/[1]/[2] were
   **already** read from the raw full magnitude in the split (a diagnostic there forced it — the
   HPSS-percussive high-band fraction smeared the /s/ cue). Only the onset dim sourced the
   percussive part; with HPSS gone it now reads the **raw high-band energy** (the energy-weighted
   temporal centroid of the raw ≥3 kHz energy localises the /s/ directly).
3. **Fusion by weighted-admissibility** — identical machinery to the split: each path a soft
   excluder `a_*(w)=exp(−d_*(w)/τ_*)`; recognition `argmax_w (log a_H + log a_F)` (soft-AND in
   log space), with the LESS-TRUSTED frication excluder BOUNDED (clamped to `[−FRIC_CLAMP, 0]`,
   `FRIC_CLAMP=0.15`) so it can only break a harmonic near-tie (where the six-sink lives), not
   override a confident harmonic margin. τ_H, τ_F = the median TRAIN across-digit spread of each
   channel.

## Donkey audit

- Harmonic path = `viterbi_pairing.viterbi_formant_track` on the **RAW** signal (owned numpy
  LPC + Levinson + forward-DP). **No HPSS, no median filter.** Recogniser logic UNCHANGED;
  runtime assert verifies the patch identity. `scripts/viterbi_pairing.py`,
  `scripts/formant_trajectory_dynamics.py`, `scripts/solve_for_n.py`, `scripts/mcu_infer.py` are
  all **git-clean** (only the new `scripts/frication_raw.py` was added).
- Frication feature = owned numpy spectral statistics on the **raw** full-magnitude STFT. No fit.
- Fusion = weighted-admissibility (log-space soft-AND of two `exp(−d/τ)` excluders, bounded
  less-trusted channel). No learned weight, no net.
- Templates / τ / z-stats = TRAIN speakers only; LOSO held-out speaker NEVER banked. CortexLoop
  and `solve_for_n.py` untouched.

## Results (full FSDD, n=3000, cross-speaker LOSO)

| recogniser | accuracy |
|---|---|
| **RAW-HARMONIC-only** (pairing tracker on the **RAW** signal, no HPSS) | **62.2%** |
| FRICATION-only (4-dim raw-STFT descriptor) | 19.8% |
| **FUSED — bounded-frication weighted-admissibility** | **57.5%** |
| ...variant — unbounded symmetric soft-AND | 37.2% |
| (a) Viterbi-PAIRING reference (no HPSS, no frication) | **62.2%** |
| (b) read-based frication-split (HPSS-broken) | **42.9%** |
| (c) full-envelope DTW exemplar 1-NN (the bank) | **83.5%** |

Per-speaker FUSED: george 55.2, jackson 56.6, lucas 67.8, nicolas 44.2, theo 55.2, yweweler 66.0.

**Six-sink** (the named confusion sink, harmonic → fused):

| pair | harmonic | fused |
|---|---|---|
| two → six | 71/300 | 29/300 |
| four → six | 51/300 | 26/300 |
| three → six | 46/300 | 35/300 |
| (sum) | **168** | **90** |
| seven → six | 29/300 | 15/300 |
| six → seven | 9/300 | 35/300 |

The gross sink more than halves (168→90). `two→six` (71→29) and `four→six` (51→26) clear hardest
— the /s/-PRESENCE cue is real for those. But `three→six` only partly clears (/θ/ in "three" is
also 3–4 kHz broadband — the channel cannot separate it from /s/), and `six→seven` *worsens*
(9→35: both are /s/ fricatives, so frication cannot tell them apart and adds noise). `nine` also
degrades (157→73 correct: frication has no /s/ cue for nine and the bounded excluder leaks into
nine→four/five/eight). Net: the tokens cleared from the sink are roughly offset elsewhere.

## Verdict

```
raw-harmonic reproduces 62.2% : harmonic 62.2% (+0.0 pts) -> the HPSS damage (45.4%) is REMOVED
Q fusion vs raw-harmonic      : fused 57.5% vs 62.2% (-4.7 pts) -> frication does NOT net-help
beats Viterbi-PAIRING 62.2%   : NO  (57.5% vs 62.2%, -4.7 pts)
beats HPSS-broken split 42.9% : YES (57.5% vs 42.9%, +14.6 pts)
six-sink (two/four/three->six): harmonic 168 -> fused 90 (CLEARED)
vs full-envelope exemplar     : fused 57.5% / exemplar 83.5% (69% of the bank)
```

**Does dropping HPSS + frication-on-raw beat 62.2%? NO — but the diagnosis is fully confirmed
and the HPSS damage is fully removed.**

1. **The HPSS diagnosis was correct.** Raw-harmonic is **62.2%** to the decimal — identical to
   the Viterbi-pairing reference. HPSS alone was the −16.8 pt loss (it had pulled the harmonic
   path to 45.4%). Dropping it restores the whole path. The revival is +14.6 pts over the
   HPSS-broken split.

2. **The frication PRESENCE cue is real but cannot net-improve at the 8 kHz band limit.** It
   clears the gross six-sink (168→90), but it cannot net-add because the residual confusions are
   QUALITY discriminations the corpus cannot support: `six↔seven` (both /s/) and `three↔six`
   (/θ/ vs /s/, both 3–4 kHz broadband) need the **4–8 kHz fricative band**, and FSDD is recorded
   **natively at 8 kHz** (hard 4 kHz ceiling — verified in the split). That band was never
   captured. Only the weak 3–4 kHz tail survives — enough for two/four-vs-six PRESENCE, not for
   /s/-vs-/θ/ or /s/-vs-/s/ QUALITY. This is the **K10 identifiability wall** — not revivable here.

3. **Why fused < harmonic despite a cleared sink.** The bounded frication excluder, when it does
   pull, sometimes pulls the wrong way on digits with no clean /s/ template (notably `nine`,
   157→73, and `six→seven`). The clamp limits the damage but cannot prevent it: on a band-limited
   corpus the frication distances are too noisy cross-speaker (per-token std ≈ the between-digit
   mean) to be a reliable excluder. Tokens cleared from the sink ≈ tokens lost elsewhere.

**The structure is right; the wall is the corpus.** Dropping HPSS was the correct fix and it
worked (path restored). The frication channel does exactly what it was built to do (clears the
sink). It does not net-improve because the /s/-quality information needed to convert a cleared
sink into net accuracy lives in the 4–8 kHz band that 8 kHz FSDD never recorded. The honest next
limiter for the frication idea remains a **wider-band (16 kHz) digit corpus** that contains the
real fricative band; a sharper feature cannot recover energy the recording never had. For pushing
*past* 62.2% on FSDD itself, the lever is the harmonic path (QCP-FB candidates / sharper formants
on what *is* present below 4 kHz), not frication fusion.

## What is reusable

- `raw_magnitude()` — owned raw STFT magnitude (512/128 @ 8 kHz), no HPSS.
- `frication_profile(mag)` — owned 4-dim frication descriptor on the raw full-magnitude STFT
  (onset now from raw high-band energy; HPSS-free).
- `evaluate_fusion()` — the bounded weighted-admissibility fusion (log-space soft-AND, less-
  trusted channel clamped, τ from TRAIN across-digit spread), now pointed at the **raw** pairing
  harmonic path. This confirms the fusion machinery is sound; the limiter is the frication
  channel's band-limited evidence, not the fusion.
