# Voice impressionist — source/content factoring + the analysis-by-synthesis payoff

**Bar: human-ear naturalness, binary-admissible — it sounds like speaker S or it
does not.** Two linked tasks, both owned by the agent's source-filter DSP (no
net, no .fit, no gradient, no sweep-to-fit). CortexLoop / solve_for_n untouched.
Numbers, not booleans; honest about where it sits vs human-natural.

Builds on `docs/voice_impressionist.md` (the now-faithful forward model:
copy-synth transparent 121.6 dB, residual worth ~133 dB vs synthetic, the
`lpc_*` pole-reversal + bandwidth-sign bug fixed). That doc's named next step —
**source/content factoring** — is TASK 1 here.

---

## (1) TASK 1 — the held-voice impression via SOURCE/CONTENT FACTORING

### The factoring (what was built / composed)

The strict filter-only swap (`B'` in the prior doc) proved speaker identity
rides primarily in the glottal **SOURCE** (f0 + voice quality), not the tract
filter alone (filter-only swap = 1/6, everything landed on the source speaker).
So to render NEW content in speaker S's **held** voice:

  * **NEW CONTENT** = the filter **TRAJECTORY** (the gesture / word): the content
    word's own `lpc_coeff_track` + its own residual fine-structure + its own
    per-hop timing.
  * **HELD SPEAKER** = the **SOURCE CHARACTER** + tract scale:
      - **f0** — re-space the content residual's pitch pulses to S's f0;
      - **voice quality** — warp the source open-quotient grain width + spectral
        tilt toward S's recovered `oq` / `tilt`;
      - **VTL** — scale the content's tract by S's recovered tract length (a
        multiplicative frequency warp).

  `render = lpc_cross_resynth( content_coeff_track(VTL-warped),`
  `                            glottal_warp_residual(content_residual → S's source) )`

**Built natively in Rust (owned DSP):**

  * `audio_primitives.rs:2214` **`glottal_warp_residual`** — the source-character
    transplant. **PSOLA-style pitch transplant** with **decoupled read/output
    cursors** (`:2255`–`:2316`): the output cursor advances by S's target period
    (sets S's pitch — re-using content pulses to raise pitch, skipping to lower
    it), the read cursor sweeps the whole content exactly once (word duration =
    content's, so the filter trajectory still aligns). Plus a one-pole
    **spectral-tilt warp** toward S's source colour (`:2336`) and per-hop energy
    normalisation back to the content's loudness contour (`:2317`). PyO3 bind
    `py.rs:6181`.
  * `audio_primitives.rs:2361` **`lpc_roots_formants_buggy`** — a measurement-only
    reproduction of the historical bug for TASK 2(b) (reversed coeffs +
    sign-wrong bw gate). PyO3 bind `py.rs:6202`. NOT for production.
  * World adapter `scripts/voice_impression_factored.py` (reads WAVs, calls the
    owned primitives, writes WAVs/numbers): `render_held_voice` (`:170`) composes
    `lpc_coeff_track` + `lpc_residual_track` + `glottal_warp_residual` +
    `lpc_cross_resynth`; the VTL is a relative tract warp
    `exp(S_level − carrier_level)` (`:365`) realised as a linear resample of the
    content signal (pure signal math). Speaker code via the owned
    `domains.voice_impressionist.recover_voice_code` (median f0/oq/tilt — pure
    selection, no fit).

**Donkey audit: clean.** Source transplant = owned PSOLA + 1-pole DSP; filter
trajectory = owned `lpc_coeff_track`; residual = owned `lpc_residual_track`;
render = owned `lpc_cross_resynth`. NO TTS net, NO neural vocoder, NO
speaker-embedding net, NO .fit / gradient / loss, NO sweep-to-fit. The PSOLA
fix was a structural correction (decoupled cursors so pitch transplants in BOTH
directions — verified: george 160 Hz code → render f0 160 Hz, was 123 before the
fix; jackson/lucas/theo/yweweler/nicolas all land their code f0 ±2 Hz).

### Validation (FSDD, 8 kHz, 6 speakers; word NOT said by S — the carrier's gesture)

A real small sample of S (≈6 tokens across 2 digits) → recover S's code → render
a word S did NOT say (the carrier's digit, re-voiced as S). Identity is measured
on the **source-sensitive** print `[log f0, oq, tilt, formant-level]` (z-scored) —
a timbre-only mean-cochleagram is a spectral-envelope average and is nearly
**f0-blind**, so it cannot see the source factor the impression actually carries;
this print can.

```
(a) IDENTITY    — rendered held word lands nearest its OWN speaker : 3/6  (chance 0.17)
    FACTOR SEP  — S-render closer to S than to B (paired)          : 22/30 = 73.3%  (chance 50%)
(b) INTELLIG.   — rendered word lands nearest the RIGHT word-print : 31/60 = 51.7%  (chance 0.10)
    control     — carrier RAW tokens, NO transplant (metric ceiling): 10/20 = 50.0%
```

**Discriminability** is well above chance: 3/6 nearest-own (chance 1/6), 73.3%
paired factor-separation (was 43% before the PSOLA fix + relative VTL + source
print). **Intelligibility is preserved** — the rendered word (51.7%) matches the
metric's own ceiling on raw un-transplanted tokens (50.0%): **the source
transplant does NOT smear the phonemes.** Per-word, the clear digits
(0,1,2,5,7,9) ride 67–83%; the weak ones (3,4,6,8) are weak in the raw control
too (a cochlea-word-print-metric limit, not a transplant artefact).

**The honest residual.** The 3 misses (lucas, nicolas, yweweler) are the
**low-f0 cluster**: real f0 lucas 95 / yweweler 110 / jackson 116 / nicolas 119
Hz all sit within ~25 Hz, and the recovered code's median-f0 from a tiny sample
carries ±10–15 Hz error, so these speakers cross-confuse. The transplant itself
is **faithful** (render f0 = code f0 to ±2 Hz); the gap is (i) f0-overlap among
the FSDD male speakers and (ii) the secondary source cues (oq, tilt) being weak /
near-degenerate at 8 kHz (tilt ≈ 0 for everyone). f0 alone already gives 3/6.

WAVs (auditioned non-degenerate, RMS 0.05–0.07, correct durations, audible f0
contrast george 160 Hz vs lucas/jackson ~114 Hz): `/tmp/voice_imp2/held_*_says_7.wav`
(the held word per speaker) + `/tmp/voice_imp2/intel_*_word*.wav` (every digit
in george's / lucas's voice).

**Is the held-voice impression ADMITTED?** **Partly.** The factoring is the right
structure and it works: the source character (f0 + glottal quality) transplants
onto new content faithfully while the word survives. Discriminability is above
chance on every measure and the strict filter-only failure (1/6) is now a
source-transplant success (3/6 nearest-own, 73% paired). But it is **not yet a
clean human-ear "unmistakably S"** — bounded by f0-overlap and weak secondary
source cues at 8 kHz. Honest: the structure is admitted; the *fidelity* is
mid-band, not human-natural.

---

## (2) TASK 2 — the analysis-by-synthesis payoff: did fixing the voice fix the ear?

Perception = inverting the forward model, so a faithful forward model should make
hearing better for free via the shared model. Two measurements.

### (a) Grounding-loop round-trip (Stage 4): speak via the faithful model → hear → recognise

Re-ran `scripts/stage4_grounding` on the curriculum base (Stage-0 native front end
+ Stage-3 speaker-invariant rep, native DtwTo). **Authoritative full-pool run:**

```
NEW base (Stage-3 invariant) round-trip self-recognition : 17.5%  (n=40, chance 10%)
OLD base (pre-curriculum)    round-trip self-recognition : 62.5%  (prior closed-loop number)
AFTER babble-refine          round-trip self-recognition : 30.0%  (+12.5 pts)

per-persona (NEW / OLD / BABBLE):
  pip      f0 230 vtl 0.85 :  20% / 60% / 30%
  ada      f0 190 vtl 0.95 :  10% / 40% / 20%
  milo     f0 120 vtl 1.05 :  20% / 80% / 40%
  bertram  f0  95 vtl 1.15 :  20% / 70% / 30%
STAGE-4 GROUNDING-LOOP GATE: False
```

(With a capped prototype pool — `--quick` — NEW base rises to 35% and the gate
reads True; the full pool is the honest authoritative measurement and it is the
one reported.)

**Honest: fixing the voice did NOT make the Stage-4 loop fire on the curriculum
base.** The round-trip on the Stage-3-invariant inverse is 17.5% — barely above
chance (10%) and far **below** the OLD pre-curriculum base (62.5%) on the SAME
projection-spoken audio. It is above the prior **broken-instrument** 12.5%, and
babble-refine lifts it +12.5 pts to 30%, but the loop does NOT close on the
curriculum base. The bottleneck is NOT the forward model's faithfulness (now
proven transparent) — it is the **Stage-3 invariant inverse mis-recognising the
agent's own synthetic voice** (it collapses onto `three`, the wrong-sink; the
medoid-prototype + VTL-norm rep generalises worse to the synthetic personas than
the OLD formant-traj + mel-kNN base). The voice is fixed; the *invariant inverse*
is the next blocker, not the voice.

### (b) Isolating the bandwidth bug's cost on EARLIER-stage perception

A/B (`scripts/bandwidth_bug_ab.py`): the **same** clean-16k corpus (1565
cross-speaker tokens, 30 speakers), the **same** Stage-3 speaker-invariant rep
and **same** native DtwTo decision — only the **formant instrument** swapped
between CORRECTED and OLD-BUGGY (reversed coeffs / sign-wrong bandwidth gate).

```
cross-speaker invariance d' : BUGGY 0.278  →  CORRECTED 0.331   (+0.053, +18.9%)
structural separation (frac): BUGGY 0.658  →  CORRECTED 0.672   (+0.014)
```

**Fixing the bandwidth bug RAISES the Stage-3 speaker-invariance cluster gap by
+0.053 d' (+18.9%)** and the within<between separation by +1.4 pts. The buggy
gate accepted spurious wide poles (every pole had negative bandwidth, so the
`bw < bw_max` filter rejected nothing); the corrected `bw > 0 && bw < bw_max`
gate rejects them, sharpening the word separation. **So the broken forward model
WAS throttling the ear — by ~19% of the cross-speaker invariance signal — at the
formant-extraction stage.** Real and positive, but **moderate**, not dramatic
(frequencies survived the bug; only the bandwidth gate was wrong, so only the
fraction of frames with spurious poles was affected).

### Did fixing the voice lift the hearing, by how much, honest?

**Yes at the earlier stage, no at Stage 4.** The corrected instrument lifts the
Stage-3 invariance d' +18.9% (the formant extractor is genuinely sharper). But
that lift did NOT propagate to a closed Stage-4 grounding loop on the curriculum
base — the Stage-3 invariant inverse still under-recognises the agent's own
synthetic personas (17.5%, below the OLD base's 62.5%). The forward model is no
longer the limit; the invariant inverse is.

---

## (3) VERDICT

  * **Held-voice impression admitted?** **Structurally yes, fidelity partial.** The
    source/content factoring is built and works — S's source character (f0 +
    glottal quality + VTL) transplants onto new content faithfully (render f0 =
    code f0 ±2 Hz) while the WORD survives (intelligibility 51.7% = the metric's
    raw-token ceiling 50%). Discriminability is above chance everywhere (identity
    3/6 vs chance 1/6; paired factor-separation 73.3% vs 50%), turning the prior
    strict filter-only failure (1/6) into a source-transplant success. NOT yet
    human-ear "unmistakably S" — bounded by FSDD male-speaker f0-overlap and weak
    secondary source cues at 8 kHz.
  * **Hearing improved?** **At the formant stage, yes (+18.9% Stage-3 d').** The
    bandwidth-bug fix demonstrably sharpened the ear. At the grounding-loop stage,
    **no** — the loop does not close on the curriculum base (17.5%, gate False).
  * **Does Stage 4 fire now, or the precise next?** **Stage 4 does NOT fire.** The
    forward model is fixed (transparent + faithfully factored), so it is no longer
    the blocker. **The precise next step: the Stage-3 speaker-invariant inverse
    mis-recognises the agent's own synthetic voice** (collapses to `three`; 17.5%
    vs the OLD base's 62.5% on the same audio). The work is on the invariant
    inverse / medoid-prototype representation's generalisation to the synthetic
    personas — not on the voice. (Babble-refine already buys +12.5 pts toward it.)

**Bottom line:** factoring built + held-voice source transplant works and keeps
the word ✓; the bandwidth fix sharpened earlier-stage perception (+18.9% d') ✓;
but Stage 4 still does not fire — the bottleneck has moved off the (now-faithful)
forward model and onto the Stage-3 invariant inverse. Honest, measured, no net.

*Logs: `/tmp/voice2_full.log` (all three tasks, end marker
`###VOICE2_REPORT_COMPLETE_MARKER###`). WAVs: `/tmp/voice_imp2/`. Not committed.*
