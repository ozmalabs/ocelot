# Articulatory-Γ forward model — a core prong of speech recognition

`scripts/articulatory_gamma.py` (run:
`PYTHONUNBUFFERED=1 python -m scripts.articulatory_gamma`; quick: `--quick`).

## Premise

The sensing apparatus is hot garbage. FSDD is recorded at 8 kHz, hard-band-limited
to 4 kHz, so the dominant /s/ frication energy (4–8 kHz in natural speech) is
**exactly zero** in the signal. You cannot *read* the missing band. So speech
recognition must be **multi-pronged**; the articulatory forward model is a
**necessary** prong — always built and fused, never a fallback. The band-limit
wall is not a problem to be removed with "better audio" (the reader's surrender);
it is the **test** — the place where the imagination is provable, because the
data is exactly zero, so any recovery was back-populated from the shadow + the
physics.

This is deeper than `scripts/frication_imagination.py` (which models the
**acoustic** spectral-envelope of each fricative class). Here the forward model is
**articulatory**: the mouth as a physical system whose *configuration* sets the
vocal-tract resonances. Physics = Γ-admissibility over the mouth's possible
movements over time. We do not model the physics; we **write the grammar**.

## (1) The articulatory Γ (gestural targets + admissibility constraints)

### Gestural targets — owned articulatory phonetics, stated not fitted

Each digit-segment is a low-dimensional vocal-tract config. **Param set** (5 dims
in [0,1] + a categorical source):

| param | 0 | 1 |
|---|---|---|
| `tongue_frontness` | back | front |
| `tongue_height` | low / open | high / close |
| `constriction_place` | glottal / pharyngeal | labial (front-to-back location) |
| `constriction_degree` | open vowel | full closure / fricative groove |
| `lip_rounding` | spread | rounded |

plus `source ∈ {voiced, fric, burst, sil}`.

Each FSDD digit is an ordered sequence of these targets (its gesture score) — the
American-English citation form. E.g. **six** /s ih k s/ = alveolar sibilant groove
(`place≈0.78, degree≈0.92, fric`) → high-front lax vowel → velar stop burst → /s/
groove again. **three** /θ r iy/ = dental fric → retroflex r → high-front. The full
table is in the script.

### Γ — the mouth's physics as an admissibility grammar (owned numpy)

Three constraints make a movement-sequence admissible:

- **Continuity** — the config changes smoothly between targets, no teleport. The
  admissible path is a cosine interpolation across the gestural targets; a
  discontinuous jump is inadmissible.
- **Inertia** — articulators have mass: bounded velocity and acceleration
  (`|vel| ≤ 0.18`, `|accel| ≤ 0.12` config-units/frame, frozen physical bounds
  from the gestural-timing scale, not swept on test). A path demanding
  faster-than-inertial motion is penalised.
- **Reachability** — only certain configs are valid (the valid-config manifold):
  a fricative groove / closure (high `degree`) at an alveolar/palatal place
  *requires* the tongue raised, so a low-tongue high-degree config is off-manifold
  and penalised. The interpolated path must stay on the manifold.

This **is** Γ over the movement-space, over time.

## (2) Source-filter projection (owned DSP)

A config → formant resonances via the owned articulatory→formant nomogram
(Fant/Stevens, grounded not fitted): F1 rises as the tract opens, F2 rises as the
constriction moves forward (rounding lowers it), F3 set by length + rounding with a
retroflex drop (the r-cue). Plus a source/voicing trajectory (voiced harmonic vs
unvoiced fric/burst/silence). So a gestural **trajectory** synthesises a **formant
trajectory + voicing envelope**. All these formants lie below 4 kHz — the formant
**shadow** is fully inside the surviving band, which is *why* the shadow survives
the band-limit even when the /s/ frication band does not.

## (3) Analysis-by-synthesis (the imagination)

Given the garbage band-limited input, read the surviving **shadow**: the
speaker-relative log-formant trajectory (the Viterbi-pairing tracker's 0–4 kHz
formants, per-token-mean removed = VTL-cancelled). For each digit hypothesis *w*:
synthesise *w*'s admissible (Γ-feasible) config-trajectory, project source-filter
to a synthesised speaker-relative formant trajectory, resample to the observed
length (the gesture-timing warp), and score the match. The articulatory distance
`d_A(w) = formant-shadow L2 mismatch + Γ-cost(w)`. The /s/ is recovered because the
admissible tongue-to-groove-and-back path is the one whose shadow fits — the
physics over-determines it, because the physics *is* the admissibility.

## (4) Fusion (multi-pronged, weighted-admissibility)

Combine three prongs by intersecting soft excluders (sum of measured-reliability-
weighted log-admissibilities):

- **Formant-trajectory prong** — the Viterbi-pairing tracker → order-N dynamics →
  graph-resident DTW recogniser, imported verbatim (the ~62.2% baseline class). The
  strong base; leads at full weight.
- **Articulatory-Γ prong** — `d_A(w)` above, weighted by its **measured**
  reliability `(acc − chance)/(1 − chance)`, where `acc` is the prong's accuracy
  measured by inner-LOSO **on the train fold only** (no outer-held voice present, no
  sweep). A weak prong's excluder flattens toward 0, so it can break a near-tie
  without overriding a confident formant margin.
- **N-gram prong** — the train-only digit unigram prior.

The decision is the agent's graph Argmax Term over Concept words, native-evaluated.

## Donkey audit

- Articulatory Γ = owned admissibility grammar (continuity/inertia/reachability as
  numpy constraint functions); no net, no `.fit`, no gradient. Gestural targets are
  stated phonetics.
- Source-filter = owned DSP (the articulatory→formant nomogram + source model).
- Analysis-by-synthesis + fusion = weighted-admissibility (the iter-48 measured-
  reliability pattern); the argmax is the graph Term.
- Formant-trajectory prong = `viterbi_pairing` + `formant_trajectory_dynamics`,
  verbatim. Exemplar baseline = `mcu_infer` log-mel banded-DTW, verbatim.
- N-gram counted train-only. Exemplars / tau / reliability weights = train speakers
  only; LOSO held-out speaker never banked. CortexLoop untouched.

## Results

Full FSDD LOSO, 3000 tokens, 6 speakers, held-out never banked
(`/tmp/articulatory_gamma_full.log`, marker `ARTICULATORY_GAMMA_COMPLETED`,
elapsed 2252 s).

| prong | accuracy (n=3000) |
|---|---|
| formant-trajectory alone (Viterbi-pairing, the base) | **62.2 %** |
| articulatory-Γ alone (gesture-from-shadow synthesis) | **24.0 %** (chance 10.0 %) |
| n-gram alone (train-only digit unigram) | 10.0 % (FSDD is balanced → flat) |
| **multi-pronged fusion** | **59.4 %** (−2.8 pts vs formant-only) |
| exemplar bank (full-envelope log-mel DTW) | 83.5 % |

### What the articulatory prong recovers (the test passes)

The articulatory-Γ prong scores **24.0 %**, well above the 10.0 % chance floor —
the simplified forward model genuinely recovers the gesture from the surviving
shadow, with the /s/ band exactly zero in the signal. It cleanly **fixes** several
frication confusions when fused:

| confusion | formant-only | fused |
|---|---|---|
| seven → six | 29/300 | **9/300** |
| six → three | 40/300 | **28/300** |
| six → two | 28/300 | **18/300** |

These are exactly the /s/-onset cases the articulatory shadow was built for: six and
seven both begin with the alveolar-sibilant gesture, and the admissible
tongue-to-groove-and-back path pulled them apart from their mid/back-vowel and
dental-fricative competitors — recovering the /s/ from its shadow with the /s/ band
at exactly zero.

### Where it is limited (the honest result — fusion does NOT net-improve)

The fused headline **drops 2.8 pts** (62.2 → 59.4 %), and the six-sink **worsens**
(288 → 357 non-six tokens wrongly → six). Where the articulatory prong *disagrees*
with the strong formant prong, it is wrong more often than right on the margin — it
introduces new errors (three → six 46 → 70, six → seven 9 → 37) that outweigh the
ones it fixes. Even weighted by its measured reliability
(`w_art = (0.24 − 0.10)/0.90 ≈ 0.16`, so its excluder is small), a prong that is
76 % wrong cannot net-help by tie-breaking unless its errors avoid the formant
prong's *near-ties* specifically — and here they do not.

This is the band-limit test reported honestly: the articulatory imagination **is a
real prong** (24 % ≫ chance, and it fixes the /s/-onset cases it targets), but the
**present forward model is too coarse** to be a reliable second vote. The specific
limits, in priority order for the **next sharpening** (never "more data"):

1. **No voicing/gap shadow.** The Viterbi-pairing tracker emits only *voiced*
   frames, so the unvoiced silence-then-frication gap — the sharpest cue for the
   /s/-initial digits (six, seven) and the stop bursts (two, eight) — is **absent**
   from the observed shadow `obs_rel`. Wiring a per-frame voicing/gap envelope as a
   second shadow component is the single biggest lever (the model already
   synthesises `synth_voicing`; only the observation side is missing).
2. **5-dim config + smooth nomogram, not an area-function tract.** The
   articulatory→formant map is a grounded but coarse 3-parameter nomogram; it cannot
   express the front-cavity resonance that separates /s/ from /θ/ in the surviving
   band, nor true coarticulatory locus equations.
3. **Citation-form gesture scores, no speaker/coarticulation variation.** One stated
   target sequence per digit; real tokens vary the timing and degree of the gestures.

None of these is "get better audio." The band-limit wall stays; the sharpening is a
**richer forward model**, exactly where the framework says the work belongs.

### Verdict

The articulatory-Γ prong is **built, wired, and donkey-clean**, and it **recovers
gestures from the shadow above chance** (24.0 % vs 10.0 %), fixing the /s/-onset
frication confusions it targets (seven→six 29→9, six→three 40→28, six→two 28→18).
But **multi-pronged fusion does NOT yet improve** the headline (−2.8 pts) — the
simplified forward model is too coarse to be a reliable second vote, and its
disagreements with the formant prong net-hurt. The next sharpening is the
**voicing/gap shadow** + a **richer tract model**, not more input.
