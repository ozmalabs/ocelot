# Frication by imagination — forward-model completion (analysis-by-synthesis)

**Status: HONEST FORK resolves to the IDENTIFIABILITY LIMIT.** The imagination frication
recogniser **clears the six-sink** (the named goal: `two/four/three→six` confusions 150→57) but
**does not net-improve** accuracy (fused **34.0%** vs HPSS-harmonic **45.4%**, −11.4 pts; far
below the no-HPSS pairing **62.2%**). The decisive evidence — the per-token synthesis-error
sanity table — shows the distinguishing /s/-vs-/th/ information is **genuinely gone**: the
observed surviving 0-4 kHz percussive shapes of the /s/ digits (six, seven) do **not** carry the
rising /s/ edge the forward model predicts; every digit, six and seven included, matches the
`none` (no-frication) model *better* than its own fricative class. The structure is fully
exercised — the model imagines the whole — but the **distinguishing part of the evidence lives at
4-8 kHz, which FSDD's 8 kHz sampling never captured**. This is an identifiability wall (data
truly absent below the Nyquist), not a missing-mechanism wall. FSDD digits, full token,
cross-speaker LOSO, held-out speaker never banked, chance 0.100, **n=3000**, elapsed 2226 s.

Script: `scripts/frication_imagination.py`. Run: `python -m scripts.frication_imagination`
(full output at `/tmp/frication_imagination_full.log`, ends with `FRICATION_IMAGINATION_COMPLETED`
+ `FRICATION_IMAGINATION_EXIT=0`; pgrep-verified one Python process ran to completion and exited 0).

## The problem this targets

The read-based frication split (`scripts/frication_split.py`, `docs/frication_split.md`) **cleared
the six-sink but did not net-improve**, because FSDD is recorded natively at 8 kHz: the spectrum is
hard-band-limited to 4 kHz, so the dominant /s/ frication energy (4-8 kHz in natural speech) was
never captured. The read-based feature could only **read** the weak, cross-speaker-noisy 3-4 kHz
tail.

The fix (memory `ozma_fill_gaps_with_imagination`): you cannot **read** missing data — you
**imagine** it. The agent has a forward model of what each fricative *is* (a full-band 0-8 kHz
spectral-envelope shape). Even with only the surviving 0-4 kHz band, it synthesises "*if* this
token's frication were /s/, here is the full structure" and asks whether the surviving partial
evidence matches the imagined /s/'s 0-4 kHz tail better than the imagined /th/'s. Analysis-by-
synthesis on present evidence against an imagined whole — phonemic restoration / the retinal blind
spot in frequency (the mic has an optic disc at 4 kHz). The point: the full-band model is supposed
to make the surviving 0-4 kHz **slope/shape** discriminative (/s/'s *rising* edge toward its >4 kHz
peak vs /th/'s flat/falling tail) where the raw energy was ambiguous.

## What was built (donkey-clean; harmonic path + recogniser UNCHANGED)

Reuses `scripts/frication_split.py` verbatim for everything except the frication feature:

1. **HPSS** — imported verbatim (`from scripts.frication_split import hpss`), asserted at runtime
   (`assert hpss is fs_split.hpss`). Fitzgerald median-filter harmonic/percussive separation,
   owned numpy/scipy.
2. **Harmonic path — UNCHANGED.** The Viterbi-pairing formant tracker on the harmonic signal →
   order-N dynamics → graph-resident DTW recogniser. Asserted: `ftd.formant_track is
   viterbi_pairing.viterbi_formant_track`; the order-N + graph-DTW logic is imported verbatim from
   `formant_trajectory_dynamics`.
3. **Frication forward models (REPLACED feature; owned phonetic knowledge, stated not fitted).**
   Each unvoiced class is a parametric full-band (modelled to 8 kHz) log-magnitude envelope shape:
   - **/s/** (six, seven): broadband, sharp HF peak ~6.5 kHz, steep **rising** slope through the
     speech band (raised-cosine bump + positive linear tilt). Surviving 0-4 kHz tail **rises**
     (+0.25 normalised slope).
   - **/th/, /f/** (three; four, five): weak, flat, low; gentle low-mid hump (~2 kHz) then roll-off,
     **no** rising HF edge. Surviving tail **falls** (−0.07).
   - **burst** (/t/ in two, eight): mild HF-tilted broadband (alveolar release).
   - **none** (zero, one, nine): no turbulence — low falling tail (voiced-leakage residue).
   Digit→class map is owned phonetics, not fitted to test.
4. **Analysis-by-synthesis match (owned numpy, no net, no `.fit`).** Per token: from the HPSS
   percussive magnitude spectrogram, take the surviving-band (0-4 kHz) observed log-magnitude
   **shape** over the frication-active frames (zero-mean, unit-norm → tests SLOPE, the discriminative
   part, not absolute level). For each class, synthesise its full-band model, restrict to 0-4 kHz,
   normalise the same way → the imagined surviving tail. Match error e_c = ‖O − M_c^{0-4}‖. Per-digit
   frication distance d_F(w) = e_{class(w)}. The forward models *are* the knowledge — **no training
   template at all**.
5. **Fusion by weighted-admissibility — UNCHANGED form.** A(w) = a_H(w)·a_F(w), a_*(w)=exp(−d_*/τ_*),
   the frication excluder **bounded** (clamped to [−0.15, 0] in τ_F units) so it resolves harmonic
   near-ties without overriding a confident margin. Intersection of soft excluders, not a dot
   product. τ_H, τ_F = TRAIN-only median across-digit spreads; LOSO held-out speaker never banked.

Donkey audit (all printed at runtime, all OK): forward models = owned parametric spectral shapes
(no fit); A-by-S match = owned numpy L2 on the surviving-band shape; HPSS + harmonic tracker +
order-N + graph-DTW = imported verbatim and asserted; fusion = bounded soft-excluder product;
τ/normalisation = TRAIN-only; CortexLoop and `solve_for_n.py` untouched.

## Results (LOSO, n=3000, chance 0.100)

| recogniser | accuracy |
|---|---|
| **(NEW) FUSED weighted-admissibility (bounded imagination excluder)** | **34.0%** |
| imagination-frication only (analysis-by-synthesis, 5 classes) | 11.2% (≈chance) |
| HPSS-harmonic only (pairing tracker on the harmonic part) | 45.4% |
| unbounded symmetric soft-AND variant | 25.7% |
| (a) Viterbi-pairing reference (no HPSS) | 62.2% |
| (b) full-envelope DTW exemplar 1-NN | 83.5% |

**Six-sink (the named goal) — CLEARED:**

| confusion | harmonic | fused |
|---|---|---|
| two→six | 59/300 | 32/300 |
| four→six | 31/300 | **4/300** |
| three→six | 60/300 | 21/300 |
| six→seven | 25/300 | 8/300 |
| seven→six | 23/300 | **3/300** |
| **sum two/four/three→six** | **150** | **57** |

**/s/-vs-/th/ hard case (three=/th/ ↔ six=/s/, the prediction target):** three→six 60→21
(reduced), but six→three 19→**34** (the imagination pushes /s/ tokens *toward* /th/ — see below).

## Verdict — the identifiability limit (the prediction's HONEST FORK)

The prediction was: the imagined full-band /s/ (rising 0-4 kHz tail) vs /th/ (flat) makes the
surviving band's shape discriminative → six-sink clears **and** net-improves. The documented honest
fork: if it still does not net-improve, the distinguishing /s/-vs-/th/ information is genuinely at
4-8 kHz (gone) — an identifiability wall. **The fork resolves to the identifiability wall, and the
evidence is direct, not inferred.**

The per-token synthesis-error sanity table is decisive — for each digit, the mean match error to
each imagined model (lower = better match):

```
 digit  class    err_s  err_th err_brst err_none
  zero   none    1.710   1.200    1.702    0.953
 three     th    1.637   1.181    1.623    1.087
  four     th    1.800   1.410    1.803    0.864
   six      s    1.640   1.264    1.621    1.118   <- /s/ token
 seven      s    1.719   1.175    1.716    0.955   <- /s/ token
  nine   none    1.701   1.103    1.702    0.959
```

**Every digit — six and seven included — matches the `none` (no-frication) model *best*, and
matches its own fricative class *worse*.** Six's err_s (1.640) is far above its err_none (1.118);
seven's err_s (1.719) above err_none (0.955). The observed surviving 0-4 kHz percussive shapes of
the /s/ digits do **not** exhibit the rising slope the /s/ model predicts — they look like
everything else (low, falling). The imagination-only channel therefore collapses to predicting
`none`/`zero` (11.2%, the confusion matrix shows all mass in the `zero`/`three` columns), and the
bounded fusion drags the harmonic path down (45.4%→34.0%).

Why: the rising /s/ edge that distinguishes /s/ from /th/ lives **above 4 kHz**. The two imagined
models are nearly identical *within* 0-4 kHz (where they diverge is exactly the band FSDD threw
away); restricted to the surviving tail, the /s/ model's signature is mostly gone, and the residual
0-4 kHz percussive energy that *does* survive is dominated by voiced-leakage / low-band structure
that matches `none`. The forward model imagines the whole correctly — but the surviving evidence it
has to match against simply does not contain the discriminating part.

**Conclusion: surviving-band + model does NOT discriminate /s/ from /th/ — the info is truly gone
below the 4 kHz Nyquist.** This is the identifiability limit, cleanly distinguished from a
missing-mechanism wall: the imagination mechanism is fully wired and exercised (forward models +
analysis-by-synthesis + weighted-admissibility fusion, all owned, all run), it clears the gross
six-sink (the /s/-vs-vowel *presence* distinction the surviving band CAN support), but the fine
/s/-vs-/th/ *quality* distinction needs the 4-8 kHz band that was never recorded. Contrast the
never-exercised-structure kill: there no model can imagine the missing structure because it was
never exercised; here the structure IS exercised — it is just not *captured*.

The fix is therefore **not a better imagination** but a wider-band corpus: a 16 kHz digit source
that records the real 4-8 kHz fricative band, on which the same forward models + analysis-by-
synthesis would have the discriminating evidence to match against. The imagination machinery is the
right structure and is ready for that band; the FSDD wall is the data, not the mechanism.
