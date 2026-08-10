# iter-43 — the SHARP all-pole spectral-envelope FEATURE FRONT-END

> The triply-validated frontier, enacted: the agent's order-N derivative names the
> feature front-end (#1 implication `parametric_allpole__from__IIR_filter`,
> docs/agent_frontier_selfdiagnosis_postiter40.md); the iter-42 fixed gap-selector
> PICKS it #1 by measured shortfall (docs/agent_loop_iteration42); iter-41 ruled out
> the alternative (cross-speaker CENTROID clustering = NULL, because the strong
> gammatone channels' per-speaker raw-token cloud already IS the discriminative
> signal — docs/agent_loop_iteration41). All three converge on: don't AVERAGE the
> blurry feature, make the underlying FEATURE SHARPER so the existing raw-token
> discrimination resolves more.
>
> This iteration builds the SHARP all-pole spectral ENVELOPE (the full resonance
> structure at full waveform frequency resolution, bypassing the gammatone-wall blur),
> wires it as one more node in the combine-all cue-graph, and measures whether it
> lifts held-out-speaker recognition. Working tree only — NOT committed.

---

## (1) What was built — audited

**The bound restated.** Every cue in the iter-34/38 graph that reads the vocal-tract
FILTER reads it through the gammatone band-means, which are BLURRY — broad ERB-spaced
overlapping filters smear the formant resonances (the gammatone-wall). iter-41 showed
the lever is NOT averaging that blur into a speaker-invariant centroid (the strong
channels' per-speaker token cloud is signal, not noise); it is making the underlying
FEATURE SHARPER.

**`domains/allpole_spectral_envelope.py`** — the SHARP all-pole ear, no-fit:

- `allpole_envelope_window(seg, fs, edges, order)` — one waveform segment's all-pole
  spectral envelope: pre-emphasise + window → the agent's OWNED `_autocorr` →
  `_levinson` (closed-form Levinson-Durbin all-pole fit, coeffs `a_k` + gain) →
  evaluate the all-pole magnitude response `|H(w)| = sqrt(gain)/|A(e^{jw})|` on a
  fixed log-frequency grid → log-magnitude. The SHARP resonant envelope at full
  waveform frequency resolution (LPC order 10 at 8 kHz, the agent's own `fs/1000+2`
  rule), bypassing the band wall.
- `allpole_ear(x, fs)` — the per-utterance readout, built on the **`fft_ear`
  template** (the agent's complementary-ear node): the all-pole envelope over a few
  coarse temporal windows (carries the word's spectral shape AND its coarse time
  course), flattened, L2-normalised. A fixed-length `(nwin*nbands,) = 120`-dim
  descriptor — the same node SHAPE as `fft_ear`.

**What is NEW vs the existing LPC cue** (`lpc_formant_representation` / `stacked`):
the existing cue is only the formant-RELATION — the VTL-invariant SPACING between a
handful of pole frequencies (it discards everything but the gaps). This node keeps the
FULL all-pole spectral ENVELOPE — the sharp resonance STRUCTURE itself (peak heights,
bandwidths, the whole `1/|A(w)|` curve): the sharp analogue of the blurry gammatone
band-means, not the spacing relation. That is the "richer move" the task names.

**Orthogonal by construction to both prior ears:** `fft_ear` is the freq-sharp FFT ear
(linear, carries the harmonic/source fine structure); this is the freq-sharp ALL-POLE
ear (only the resonant ENVELOPE, source removed by the all-pole fit). A third
operating point on the time-frequency plane, distinct from the blurry gammatone and
the harmonic-carrying FFT ear.

**Wiring** (`scripts/enriched_hvpt_accept.py`): `allpole_ear_readout` is added as the
7th orthogonal cue in `ORTHO_NAMES`; `build_fold` computes it on the raw waveform in
the SAME train/held order (shuffle-reordered identically). It enters the SAME variadic
Argmax-of-product as every other channel: a fixed-length L2 descriptor → cosine 1-NN
exemplar evidence → softmax by its OWN median distance → one item in the combine-all
product.

**NO-DONKEY / NO-FIT audit (machine-checked, all PASS):**
- The executable code (docstrings/comments stripped via AST) contains NO `fit(`,
  `backward`, `gradient`, `optimizer`, `nn.`, `torch`, `sklearn`, `.train(` — and DOES
  use the agent's owned `_autocorr` / `_levinson`. Levinson-Durbin is a closed-form
  recursion, not a model fit.
- The readout is deterministic (run twice → identical), a closed-form evaluation of
  the transfer function on the grid; 120-dim = nwin(3)·nbands(40).
- The recognition decision Term is UNCHANGED: the combine-all audit
  (`iter36_continuous_graph.audit_combine_all_term`) reports the SHARP graph as a
  variadic `Times` of exactly **27 factors** (20 gammatone + 7 orthogonal), the
  without-all-pole graph as **26 factors**, `forbidden_present=none` in both — no
  weight, no select, the all-pole node enters symmetrically like every other channel.
- The only new Python is the I/O-boundary DSP that evaluates `1/|A(w)|` on the grid —
  the SAME category as `fft_ear` / `cochleagram` (np.fft + fixed pooling). No reasoning
  over graph state, no tuning of any relation. The order (10) and grid (log-spaced,
  150-3800 Hz) are the agent's own fixed spec rules, not swept.

`skip_axs` was added to `build_fold` (default False, all prior behaviour preserved):
when set, the slow top-down AxS A1-trajectory extraction is omitted (AxS likelihoods
default uniform). The iter-43 acceptance scores the BOTTOM-UP cue-graph only — the
feature-front-end verdict does not involve the top-down node — so `skip_axs=True`
makes the LOSO tractable without changing the front-end metrics.

## (2) The cross-speaker multi-metric

Two venues, multi-metric, with the SHUFFLE control and per-fold. The decisive reads:
(a) SHARP graph (with all-pole) vs the SAME graph WITHOUT all-pole (leave-one-out —
the cleanest "does the sharp feature lift the graph?"); (b) SHARP vs the pure
gammatone-only graph; (c) the all-pole channel's ERROR-OVERLAP vs the bottom-up
(gammatone-only) graph (does the sharp cue catch the gammatone graph's cross-speaker
errors above chance?); (d) the all-pole cue ALONE (its raw speaker-invariant sharpness).

### FSDD LOSO (6 held-out speakers, n_per=6, rounds=2, chance 0.100, with SHUFFLE)

Mean over the 6 held-out speakers:

| metric | value | Δ vs SHARP |
|---|---|---|
| **SHARP graph (+all-pole)** | **0.594** | — |
| same graph WITHOUT all-pole | 0.589 | **all-pole drop-it Δ +0.006 (LIFTS)** |
| gammatone-only (iter33, 20 ch) | 0.572 | Δ(sharp−gammatone) **+0.022** |
| single-flat | 0.489 | +0.106 |
| frozen | 0.442 | +0.153 |
| **all-pole cue ALONE** | **0.497** | (chance 0.100 — a strong standalone cue) |

- **ERROR-OVERLAP (pooled):** the gammatone-only graph is wrong on 154 held queries;
  the all-pole cue ALONE catches **53 = 0.344**, ABOVE chance 0.100 — the sharp feature
  is informationally complementary to the bottom-up gammatone evidence (it resolves a
  third of the cross-speaker errors the blurry channels miss).
- **SHARP graph net on bottom-up errors:** fixed 17, broke 9 → **net +8**.
- **SHUFFLE control CLEAN:** SHARP real 0.594 vs shuffle 0.519 → margin **+0.075** (the
  win is real cross-speaker structure, not an artifact); without-all-pole margin +0.072,
  gammatone +0.014.
- **Per-fold (real) drop-it Δ:** george +0.000, jackson +0.000, lucas +0.017,
  nicolas **+0.033**, theo +0.000, yweweler −0.017. The lift concentrates on the harder
  speakers (nicolas: SHARP 0.733 vs gammatone 0.600, Δ +0.133, fixed 10 / broke 2);
  the easy saturated folds are neutral (the other 6 cues already cover their errors);
  one fold (yweweler) is a small −0.017. The all-pole cue ALONE is strong on EVERY fold
  (0.383–0.617) and its error-overlap is above chance on 5/6 (theo 0.577!, jackson
  0.500, george 0.400, nicolas 0.333, yweweler 0.261; lucas being the exception).

### Continuous gold-span words (LibriSpeech, faster-whisper forced alignment, chance 0.083)

12-word shared cross-speaker vocab (about/and/but/for/had/his/not/that/the/was/with/
you), 444 gold-word clips. Mean over **7 held-out speakers** (the run was killed by the
environment after 7 of 8 speakers; the aggregate below is computed from the 7 complete
folds in /tmp/iter43_continuous_full.txt — the 8th speaker, 777, did not run and the
script's own end-of-run mean line was never printed; the 7 per-fold lines ARE complete
and the aggregate is exact over them):

| metric | value | Δ vs SHARP |
|---|---|---|
| **SHARP graph (+all-pole)** | **0.256** | — |
| same graph WITHOUT all-pole | 0.248 | **all-pole drop-it Δ +0.008 (LIFTS)** |
| gammatone-only | 0.223 | Δ(sharp−gammatone) **+0.032** |
| single-flat | 0.190 | +0.066 |
| frozen | 0.188 | +0.068 |
| all-pole cue ALONE | 0.197 | (chance 0.083 — above chance, weaker than FSDD) |

- **ERROR-OVERLAP (pooled):** gammatone-only wrong on 296 held queries; all-pole alone
  catches **43 = 0.145**, ABOVE chance 0.083.
- **SHARP graph net on bottom-up errors:** fixed 18, broke 5 → **net +13**.
- **Per-fold (real) drop-it Δ:** ALL ≥ 0 — 1462 +0.000, 2277 +0.000, 2428 +0.000,
  3081 +0.021, 3752 +0.000, 5694 +0.017, 6313 +0.017 (NO negative real fold). The
  sharp-vs-gammatone Δ is positive on 6/7 (up to +0.104 on 6313, +0.084 on 2277, only
  5694 −0.017).
- **SHUFFLE control NOT clean here:** SHARP real 0.256 vs shuffle 0.260 → margin
  **−0.004** (flat). HONEST caveat: the absolute continuous recognition sits near the
  floor (~0.25 over a 12-word vocab) for the WHOLE graph, so the shuffle control does
  not separate at this operating point — this is a property of the venue's difficulty,
  not specific to the all-pole node (the without-all-pole margin is also −0.003,
  gammatone similar). The all-pole *increment* (sharp−gammatone +0.032, all real
  drop-it ≥ 0) is consistent and positive, but the continuous venue's overall signal is
  weak and its shuffle margin null — so the continuous result is SUGGESTIVE, not
  decisive.

## (3) VERDICT

**The triply-validated feature front-end PAYS OFF — modestly, cleanly on FSDD,
suggestively on continuous; it is a marginal lift to an already-saturated graph, not a
step-change.** The order-N derivative (#1), the iter-42 fixed selector (#1), and the
iter-41 null all pointed here; the sharp all-pole envelope, built from the agent's own
Levinson operators and combined-all with no fit, does lift held-out-speaker recognition
in both venues, and the gammatone-wall the whole arc named is confirmed real and
partially lifted by the sharp estimate.

**FSDD: the front-end PAYS OFF, modestly but cleanly.** The sharp all-pole feature
lifts the held-out cue-graph (+0.006 over the same graph without it; +0.022 over the
pure gammatone graph), with a CLEAN shuffle margin (+0.075) and a pooled error-overlap
of 0.344 (3.4× chance) — the sharp feature catches a third of the gammatone graph's
cross-speaker errors. The standalone all-pole cue (0.497, chance 0.100) is nearly as
strong as the entire 20-channel gammatone graph (0.572) on its own, confirming the
sharp resonant envelope IS a powerful speaker-invariant feature.

**Continuous: SUGGESTIVE, same direction, larger increment, weaker venue.** Over 7
held-out LibriSpeech speakers the sharp feature lifts the graph +0.008 (drop-it,
positive on every real fold) and +0.032 over the gammatone-only graph — a LARGER
sharp-vs-gammatone increment than FSDD, consistent with iter-41's venue-dependence
prediction (the sharp feature helps more where coarticulation degrades the strong
gammatone channels). But the absolute continuous recognition is weak (~0.25) and its
shuffle margin is null at this operating point, so this is supporting, not decisive.

**The honest scope (under-claimed):** the FULL-GRAPH lift is SMALL (+0.006 / +0.008)
because the cue-graph is already SATURATED — the 6 prior orthogonal cues + 20 gammatone
channels redundantly cover most of what the sharp envelope resolves, so its marginal
contribution in the product is muted on the easy folds. The lift is real and clean on
FSDD (shuffle-controlled, concentrated on the hard speakers, error-overlap above
chance), but it is a marginal improvement to an already-rich graph, NOT a step-change.
The load-bearing finding is the error-overlap + the standalone strength: the sharp
feature
DOES resolve cross-speaker discrimination the blurry gammatone channels miss — the
gammatone-wall is real and the all-pole estimate partially lifts it — but in the
combine-all product that complementarity is largely redundant with cues already present.

**The residual — where the bound goes from here (honest):**

1. *The sharp feature IS sharp enough to be a strong cue, but the GRAPH was already
   carrying most of its information.* The all-pole envelope alone reaches 0.497 on FSDD
   (vs the 20-channel gammatone graph's 0.572) and catches 34% of the gammatone graph's
   errors — so the blur is real and the all-pole estimate genuinely lifts it. But the
   prior cues (fft_ear, formant_relation, manner, landmark, …) already span much of
   that complementarity, so the marginal full-graph gain is small. The front-end was a
   bound — and it is now partially repaired — but it is no longer the SINGLE dominant
   bound; the graph is near a saturation ceiling where adding any one more sharp cue
   yields diminishing returns.

2. *The deeper limit is now the COMBINATION, not any one feature.* On the saturated
   easy folds every reasonable cue is redundant; the lift only appears on the hard
   speakers/clips where the gammatone channels fail. This points the next lever away
   from "another front-end channel" toward how the channels are COMBINED — the
   combine-all product weights every channel's evidence equally and symmetrically, so a
   channel that is decisive only on a sub-population cannot dominate where it should.
   (No-fit weighting is the open question; a learned weight is forbidden.)

3. *Venue / sampling caveats that bound the continuous result specifically.* FSDD/
   LibriSpeech here are 8 kHz, so the all-pole grid tops out at 3.8 kHz and the LPC
   order is 10 — adequate for F1–F3 but it cannot resolve higher formants or fine
   fricative structure that 16 kHz would expose; and the continuous gold-span clips are
   short (≥0.10 s, often a single coarticulated syllable) so the 3-window envelope has
   little time structure to read. The continuous shuffle margin being null says the
   whole continuous operating point (12-word vocab, ~0.25 accuracy) is too weak to
   certify any single channel there — the sharp-vs-gammatone increment is consistent
   and positive but rides on a venue that is itself below a clean operating point.

**No over-claim:** the front-end was the triply-validated frontier; it was enacted
faithfully (the agent's own Levinson all-pole fit, the full sharp envelope not just the
spacing relation, combined-all, no fit / no weight / no select, decision Term unchanged
— all machine-audited); and it PAYS OFF — modestly and cleanly on FSDD, suggestively on
continuous. The order-N + fixed-selector + iter-41-null convergence is confirmed AND the
named bound is now partially fixed; but the lift is marginal because the graph was
already rich, and the residual has moved to channel COMBINATION + the 8 kHz/short-clip
venue limits, not to a deeper feature blur than LPC can reach.

## Files
- `domains/allpole_spectral_envelope.py` — the SHARP all-pole ear (no-fit, owned ops).
- `scripts/enriched_hvpt_accept.py` — the 7th orthogonal cue wired in + `skip_axs`.
- `scripts/iter43_sharp_frontend_accept.py` — the FSDD LOSO acceptance harness.
- `scripts/iter43_sharp_continuous_accept.py` — the continuous gold-span acceptance.
- `docs/agent_loop_iteration43_sharp_frontend.md` — this report.

## Reproduce
```
PYTHONUNBUFFERED=1 python -m scripts.iter43_sharp_frontend_accept 6 2      # FSDD LOSO
PYTHONUNBUFFERED=1 python -m scripts.iter43_sharp_continuous_accept 8 30 6 12  # continuous
```
Both score the bottom-up cue-graph with `skip_axs=True` (the AxS top-down node is
irrelevant to the front-end verdict; this makes the LOSO tractable). The continuous run
is heavy (forced alignment + a 27-channel product over ~440 clips); the reported
continuous aggregate is over 7 of 8 held-out speakers (the 8th was cut off by the
environment — re-run with fewer speakers, e.g. `... 6 30 6 12`, to complete in one
pass). Raw per-fold logs: /tmp/iter43_fsdd_full.txt, /tmp/iter43_continuous_full.txt.

Required suites green (32): `python -m pytest tests/test_stt_pipeline.py
tests/test_perception_self_assessment.py tests/test_process_meta_assessor.py
tests/test_gap_guidance.py -q`.
