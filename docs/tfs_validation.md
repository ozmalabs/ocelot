# TFS validation — gap 1 (temporal fine structure) in recognition

Validate the **TEMPORAL FINE STRUCTURE** primitive (`band_autocorr` +
`summary_autocorrelogram` + `periodicity_track`, commit a7cfe71a) in the native
recognition path — close, or honestly fail-to-close, **gap 1** of the agent's
self-assessment (the most-upstream "single-cochlea wall" sense gap).

Run: `PYTHONUNBUFFERED=1 python -m scripts.tfs_validation`
(full LOSO log: `/tmp/tfs_validation_full.log`, end marker `TFS_VALIDATION_COMPLETED`).

---

## (1) The agent's design — which TFS-derived cue, how wired, rationale

**Cue chosen: VOICING / periodic-vs-aperiodic (GRADED).** Of the three candidate
recognition signals the TFS can provide (voicing, F0/pitch, formant-sharpening), the
agent picks voicing as the one with the clearest path to a number, because the prior
frication/gap thread already isolated it as the *right discriminating dimension that
the existing channel scored wrongly*:

- The gap channel (silence-then-frication) is the sharpest six/seven/stop-burst marker
  and clears the six-sink (commit 5defadb8: eight +15.7).
- But the **binary energy gate** `unvoiced_gap_detect` **over-corrected seven (-30.6)**:
  it scored seven's *partial* voicing like six's *hard* silence, so fusion did **not**
  net-improve (59.4% vs the 62.2% formant base). The prior verdict pinpointed the next
  limiter exactly: *"the voicing envelope is coarse (binary energy gate); the sharpening
  is a GRADED frication/voicing model."*

**The TFS is that graded model.** Voiced (vowel) frames are strongly periodic → a tall,
well-defined pooled-autocorrelation peak (`periodicity_strength` ≈ 1). Frication / burst
/ silence are aperiodic → a flat profile (strength low). The strength is a *continuous*
voiced↔unvoiced axis — exactly what the binary gate could not give.

**Wiring (recogniser core intact).** The articulatory prong's distance already declares
a voicing term:

```
d_A(w) = W_FORMANT_SHADOW · DtwTo(obs_rel, syn_rel(w)) + W_GAMMA · γ(w)
       [+ W_VOICING_SHADOW · DtwTo(obs_voi, syn_voi(w))]          # W_VOICING_SHADOW = 0.6
```

`obs_voi` was the binary gate. The agent swaps in **`obs_voi` = the TFS graded
periodicity envelope**. Nothing else changes — the formant prong (the 62.2% Viterbi-
pairing DTW Argmin Term), the fusion math (native weighted-admissibility Argmax), the
n-gram, and the exemplar bank are imported **verbatim** from `perception_composition` /
`articulatory_gamma`. The *only* behavioural change between (b) and (c) is whether
`obs_voi` is the binary gate or the graded TFS periodicity.

**The new primitive** `tfs_voicing_track(sig, fs)` is a thin world-adapter over the
**owned native** TFS chain (no Python DSP, no decision):

```
gammatone_band (real native cochlear band, 8 bands 150–3200 Hz)
  → band_autocorr           (within-band fine-structure autocorrelation = phase-lock)
  → summary_autocorrelogram (pool across bands = Licklider/Meddis pitch readout)
  → periodicity_track       (per-frame strength of the dominant pitch-range peak)
```

Framing matches the tracker / energy gate exactly (win 256 / hop 96 @ 8 kHz); pitch-lag
search 25–100 (F0 80–320 Hz).

**Donkey audit.** TFS = owned native primitives (`audio_primitives.rs`), no net / `.fit`
/ gradient. The cue is computed *from the real native gammatone bands* via thin one-line
`py.rs` bindings (`gammatone_band`, `hair_cell_envelope`, plus the three TFS functions).
Recogniser logic byte-unchanged. Real FSDD (no self-generated audio). Held-out **never**
banked (LOSO). `CortexLoop` + `solve_for_n.py` untouched. `cargo build --release` passes;
the `.so` was rebuilt (`maturin develop --release`).

Rust changes this run: added `gammatone_band` + `hair_cell_envelope` py.rs bindings
(the three TFS functions were already exposed in a7cfe71a). Both are one-line hand-offs
to primitives that already existed in `audio_primitives.rs`.

---

## (2) Per-gap diagnostic — does TFS recover voicing the envelope provably cannot?

The inner-hair-cell **envelope** is the per-band magnitude *after* half-wave-rectify +
low-pass — it has discarded the sub-millisecond fine timing, so periodicity is
unrecoverable from it (the binary energy gate can only threshold *loudness*, and fires
on loud frication too). The TFS reads the timing back from the band's fine waveform.

FSDD (george), graded TFS periodicity in [0,1] (voiced→1, frication/burst→low):

| digit | tfs_mean | tfs_p90 | tfs_p10 | spread | energy_gate_voiced_frac |
|-------|----------|---------|---------|--------|-------------------------|
| five  | 0.861 | 1.000 | 0.520 | 0.791 | 0.82 |
| one   | 0.888 | 1.000 | 0.608 | 0.628 | 0.94 |
| nine  | 0.875 | 1.000 | 0.568 | 0.743 | 0.92 |
| zero  | 0.874 | 1.000 | 0.598 | 0.714 | 0.91 |
| six   | 0.662 | 1.000 | 0.339 | 0.783 | 0.56 |
| seven | 0.832 | 1.000 | 0.409 | 0.727 | 0.79 |
| eight | 0.777 | 1.000 | 0.445 | 0.765 | 0.65 |
| three | 0.768 | 1.000 | 0.455 | 0.744 | 0.80 |

The graded axis separates fully-voiced digits (one/zero/nine, mean ≈ 0.87–0.89) from the
gap-cued digits (six 0.662, eight 0.777, three 0.768), with frication/burst frames sinking
to p10 ≈ 0.34–0.45 while voiced frames hit p90 = 1.0. **The binary energy gate has no such
gradation** — it emits {0,1} on loudness alone. **Envelope-cannot, TFS-can: confirmed.**

---

## (3) Recognition WITH the TFS cue vs baselines

<!-- FILLED FROM /tmp/tfs_validation_full.log AFTER THE FULL LOSO RUN COMPLETES -->

---

## (3b) Verdict

<!-- FILLED FROM THE FULL RUN -->
