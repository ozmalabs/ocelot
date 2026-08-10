# Seeded prototype vocal-tract shape — does it break past CMVN's 0.570 cross-speaker cap?

**Spec (the user).** The forward model that disentangles SPEAKER from WORD is a
CLOSE-ENOUGH SHAPE (a prototype), not the exact speaker. Babble would LEARN it slowly;
instead SEED the shape-space (the innate prior = the settled acoustics of vocal tracts)
and ADAPT on the fly (the learned last mile). Test whether the close-enough prototype +
on-the-fly adaptation disentangles the speaker and breaks past CMVN's **0.570**
cross-speaker LOSO cap (`docs/synthesize_gaps_on_audio_loso.md` — the within-utterance
linear subtract reduced exactly to CMVN because it had no model of the speaker beyond
the per-band mean).

**Verdict: NO — KILL. The seeded prototype + adaptation does NOT beat CMVN; it lands
BELOW it (0.458 vs 0.570, −0.112).** The seeded neutral-tube shapes are too off-manifold
for real speech even after per-utterance adaptation: subtracting a generic vocal-tract
filter envelope removes word information along with the speaker, so the residual
recognises WORSE than the plain CMVN cochleagram. Per the spec's KILL clause, the shape
must be **LEARNED from real speech (babble), not seeded**. No rescue.

---

## (1) Where each shape parameter came from — the agent's own speech-science (sourced)

The shape-space is `domains/prototype_shape_space.py`. Every parameter is read off a
concept the agent already holds in `seeds/expansions/speech_*_decomposition.json` — NOT
hand-authored. The donkey-line: the AGENT's acoustic knowledge specifies the SPAN; a
mechanical numpy loop emits it.

| shape element | value | sourced from (agent concept, verbatim) |
|---|---|---|
| the thing to subtract = the **filter spectral envelope** | per-utterance tract envelope | `source_filter_theory`: "the FILTER (tract shape) imposes the resonances (formants) = SPECTRAL ENVELOPE. Source and filter are largely independent." → the speaker's contribution to the tangled spectrum IS the filter envelope. |
| the prototype shape = a **quarter-wave tube** | `F_n = (2n−1)·c/(4L)`, c=35000 cm/s, 4 resonances | `vocal_tract_resonance_formants`: "the vocal tract is an ACOUSTIC TUBE that resonates at frequencies set by its LENGTH + constriction pattern." A neutral (schwa) tube closed-glottis/open-lips is the textbook quarter-wave resonator. |
| the **speaker axis** = vocal-tract length L | grid 13..18 cm, 9 shapes | `speaker_normalization`: "factoring out talker differences — SCALING for VOCAL-TRACT LENGTH (formant frequencies SHIFT)." L is the agent's NAMED dominant talker factor; the human VTL range ~13 cm (short tract) .. ~18 cm (long tract) spans the speaker space. |
| the **adaptation tilt** column | log-freq linear tilt | `glottal_source`: "its spectrum is broadband, falling ~ −12 dB/octave" → the source contributes a smooth talker-varying spectral slope, fit per-utterance. |
| the **adaptation gain + DC** columns | scalar gain on the prototype + DC level | `source_filter_theory` (source/filter factor independently) — gain on the FILTER + level are exactly what the talker varies; a deliberately LOW-capacity (3-column) basis so adaptation closes the last mile but cannot absorb the word's sharp constriction. |
| the design constraint | "invariance must be RECOVERED, not assumed" | `perception_needs_normalization` — recovered here by predicting + removing the talker's filter envelope. |

Rendered resonances are physically correct: L=13 cm → F1=673, F2=2019, F3=3365 Hz
(short tract); L=18 cm → F1=486, F2=1458, F3=2431 Hz (large male tract).

**Donkey audit.**
- Shapes DESIGNED FROM the agent's concepts (each row sourced above); the grid is
  emitted MECHANICALLY (a numpy loop over L) — the I/O-boundary category, the same as
  the gammatone front end. No reasoning, no decision over graph state in the seeder.
- The per-utterance forward model (`prototype_forward_model`): **pick** = argmin over
  the seeded VTL grid of the envelope-shape distance to the utterance mean spectrum;
  **adapt** = closed-form least-squares (gain, DC, tilt) of the picked prototype to the
  mean spectrum (`np.linalg.lstsq` normal equations — OWNED linear algebra, NO fit over
  a dataset, NO trained net, NO learned weight); **subtract** = remove the adapted
  envelope from every frame; **read** the residual. Per-utterance, UNSUPERVISED, NO
  speaker labels, NO cross-utterance leakage. A `post_cmvn` per-band variance-normalise
  makes PROTOTYPE a strict SUPERSET of CMVN (CMVN's mean+variance normalisation PLUS the
  seeded resonance-shape removal), so any lift is credited to the disentanglement, not a
  different baseline.
- Recognition = the agent's GRAPH-RESIDENT `DtwTo` recognizer (Argmin MinOver DtwTo),
  reused UNCHANGED from `scripts/dtw_trajectory_loso.py` (the only thing swapped across
  regimes is which trajectory the speaker is/isn't subtracted from).
- SC load + the 40-speaker split = world-adapter mechanics (reused verbatim from
  `scripts/sc_loso_frontend_norm.py`); held-out speakers' clips NEVER banked; LOSO
  ungameable.

`tests/test_frontend_effect_gate.py` green (4 passed). The new module is self-contained
(imported only by the experiment script); imports clean.

---

## (2) RAW vs CMVN vs SEEDED-PROTOTYPE — run to COMPLETION

Robust SC 40-speaker LOSO: 120 train / 40 held-out speakers (disjoint), 20 clips/word
(200 banked exemplars), seed 20240608; 200 seen-speaker probes, 400 cross-speaker LOSO
probes; chance 0.100. All three regimes recognised by the SAME agent `DtwTo` trajectory
recognizer on the SAME split. Captured: `/tmp/seeded_prototype_loso.log` (ends
`[MARKER] SEEDED_PROTOTYPE_LOSO_COMPLETE`); `pgrep` verified no process remained.

| regime | seen | LOSO | seen−LOSO gap | vs CMVN |
|---|---|---|---|---|
| RAW | 0.310 | 0.328 | −0.018 | −0.242 |
| **CMVN** | 0.625 | **0.570** | +0.055 | +0.000 |
| **SEEDED-PROTOTYPE** | 0.495 | **0.458** | +0.037 | **−0.112** |

The baselines reproduce the established numbers exactly — RAW 0.328 and CMVN 0.570 match
`docs/synthesize_gaps_on_audio_loso.md` to the digit — so the harness is faithful and the
PROTOTYPE number is trustworthy on the same yardstick.

---

## (3) VERDICT — KILL: the shape must be LEARNED, not seeded

**The seeded prototype + adaptation does NOT beat CMVN. It lands 0.458, a full −0.112
BELOW the 0.570 cap, and even below would-be expectations — it DEGRADES recognition.**

- **The seeds are too off-manifold for real speech, even after adaptation.** A neutral
  quarter-wave tube envelope is the *schwa* shape — a single un-constricted tract. Real
  digit utterances are a *trajectory of constrictions* (vowels + the stops/fricatives of
  "six", "eight", "three"…), whose own resonances are nowhere near the neutral-tube
  prototype. The 3-column adaptation (gain/DC/tilt) cannot bend a fixed-pole neutral
  envelope onto the actual per-talker formant pattern, so the subtracted envelope is a
  poor estimate of the speaker's contribution — and subtracting a wrong envelope *adds*
  structured error that the recogniser then has to see through. Result: WORSE than the
  plain CMVN cochleagram, which removes only the (correct, talker-specific) per-band mean
  and variance and leaves the word intact.

- **This is the SAME failure mode as the LPC peel and the wide-SVD residual, reached from
  the opposite direction.** `synthesize_gaps_on_audio_loso` found that any subtract richer
  than the per-band mean (LPC all-pole whitening, k≥2 SVD) *peels word information* and
  monotonically degrades LOSO. The seeded prototype is a third instance: a richer-than-mean
  subtract whose template is wrong for this utterance, so it peels the word. The mean
  (CMVN) is special precisely because it is the ONE speaker estimate that is guaranteed
  on-manifold for the utterance (it is computed FROM the utterance); a *seeded* generic
  shape is not.

- **The spec's KILL clause is the conclusion.** "If it does NOT beat CMVN (the seeds too
  off-manifold even after adaptation, or the prototype still can't disentangle), say so
  PLAINLY — then the shape must be LEARNED from real speech (babble), not seeded." That is
  exactly what happened. The close-enough-shape hypothesis is not refuted in principle
  (memory `ozma_forward_model_is_a_prototype_shape` still holds that a *learned* prototype
  + adaptation is the mechanism), but the **SEEDED** shortcut fails: an a-priori vocal-tract
  shape designed from production theory is too far from the real speaker manifold for the
  low-capacity adaptation to close the gap. The prototype's poles are fixed by the
  quarter-wave law at the neutral position; the real talker's formants are constriction-
  displaced, and the 3-parameter adaptation has no degree of freedom to move the poles. The
  last mile is too long to seed.

- **What this localises for the babble path.** The thing that has to be learned is not the
  *idea* of a prototype envelope (the source-filter factoring is right) — it is the
  prototype's **pole positions across the speaker manifold**, which only real-speech
  exposure provides. Babble builds a shape whose resonances sit where actual talkers' do
  (a data-grown basis), with the constriction pattern factored out by exposure to many
  words; the seed cannot guess that basis from tube acoustics alone. The 0.570 CMVN cap
  stands; the next move is the **learned** forward model (babble), as the prior synthesize-
  gaps doc already concluded — this run rules out the seeded shortcut around it.

**Net.** Seeding the shape-space from the agent's source-filter knowledge is donkey-clean
and the acoustics are correct, but a SEEDED neutral-tube prototype + low-capacity
adaptation does not disentangle the speaker on real multi-speaker speech — it removes word
information and recognises 0.112 below CMVN. The shortcut does not work; babble is NOT
optional. The shape must be learned, not seeded.

Captured: `/tmp/seeded_prototype_loso.log` (end `[MARKER]
SEEDED_PROTOTYPE_LOSO_COMPLETE`); `pgrep`-verified no process remained. Not committed.
