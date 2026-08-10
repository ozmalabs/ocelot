# Agent loop iteration 25 — the scale-invariant relation over TRUE (LPC) formants

**Date:** 2026-06-07
**Builds on:** iter-24 (commit 4564ab8e). iter-24 autonomously DERIVED + COMPOSED the
SCALE-invariant relation (band-index landmark SPACINGS, VTL-invariant BY CONSTRUCTION
= 0.0), but it did NOT lift, and a THIRD co-limit surfaced UNDERNEATH the axis: the
LANDMARK QUALITY. The spacing relation was built on RAW-spectrum ArgMax peaks — a mean
of 5.4–5.5 local maxima per frame (range 2–11), most of them spurious envelope ripples,
not the 2–3 true formants. The spacings among spurious peaks are noise, so a relation
that is mathematically VTL-invariant carried little word identity (gate within-NN 0.112
≈ shuffle 0.098; cross-NN 0.007 = chance; FSDD LOSO dropped to 0.253). iter-24's named
residual: "the same `apply_scale_invariant` over a SMOOTHED envelope (cepstral-liftered
/ LPC, so the peaks ARE the 2–3 formants) is the next composition in the SAME family."

**Code added (working tree, not committed):**
`scripts/iter25_lpc_formant_derive.py` (Step 1, the agent's derivation),
`domains/lpc_formant_representation.py` (Step 2, the agent's composition),
`scripts/iter25_lpc_gate.py` (Step 3 gold-span gate),
`scripts/iter25_fsdd_loso.py` + `scripts/iter25_fsdd_audio.py` (Step 3 FSDD LOSO).

---

## VERDICT (up front)

**The agent autonomously DERIVED the smoothed-envelope / all-pole move** from its OWN
parameterize shape (the breadth-audit's `parameterize` role; harvested from the agent's
`IIR_filter` concept) transferred onto the iter-24 residual frame — Step 1, verbatim
below. **It COMPOSED the fix faithfully**: the SAME iter-24 spacing relation (its own
Term-tree, unchanged) run over the TRUE formant positions — Step 2.

**The fix is a PARTIAL lift, real but bounded.** Enacted faithfully to the agent's own
LPC spec (LPC roots of the raw waveform → formant frequencies, bypassing the gammatone
band wall):

- **FSDD LOSO** (the within-corpus regression): the TRUE-formant spacing scores **0.528**
  — essentially MATCHING the confirmed baseline path (0.544) and a massive recovery
  from iter-24's **0.253** (raw-spectrum spacing). The agent's diagnosis was correct:
  the relation was right; it needed true formants, not raw-spectrum ripples.
- **Gold-span gate (Run A, 12×18)**: FORMANT-SPACE within-NN **0.153** (vs iter-24
  0.112; vs its OWN shuffle **0.011** — decisively above shuffle, REAL signal, where
  iter-24 sat AT its shuffle), cross-NN **0.043** (vs surface 0.014, iter-24 0.007),
  cross-sep **+0.081** (vs iter-24 +0.039). The TRUE-formant relation moves both within
  and cross UP from iter-24, and cross-separation roughly doubles.
- **But it does NOT clear the bars**: within-NN 0.153 < surface 0.204 < shallow-CNN 0.32
  < SSL 0.49; cross-NN 0.043 is above surface but still small in absolute terms.

**So: three turns of the agent's own loop (iter-23 value axis → iter-24 index axis →
iter-25 true landmarks) built the speaker-normalized formant-relational representation
from scratch, and the OBJECT finally carries real, shuffle-beating, speaker-robust
signal — recovering FSDD to baseline and improving every gate number over iter-24 — but
it does not clear the 0.32 within-NN bar, and cross-NN stays near chance.** The relation
+ the true-formant landmarks are right; what remains caps it (the residual beyond, §5).

---

## (1) The agent's DERIVATION of the smoothed-envelope move — VERBATIM

`scripts/iter25_lpc_formant_derive.py` registers iter-24's residual as a held postulate
`landmark_quality_frame` (honest text: the spacing relation is right but its landmarks
are RAW-spectrum local maxima — 5–11 spurious ripples/frame, not the few true formants;
the object the relation needs is the smooth spectral ENVELOPE whose few peaks are the
vocal-tract RESONANCES; **it does NOT name "LPC", "all-pole", "Levinson", or "linear
prediction"**). It installs the agent's held all-pole science (`audio_coding_theory` —
the `IIR_filter` / `linear_prediction_models_speech_autocorrelation` concepts the
breadth-audit's `parameterize` role counts; iter-24's build did NOT install these, which
is WHY iter-24 surfaced only the re_represent shape), then runs the agent's
`synthesize_gaps` over the residual frame with the agent's OWN harvested library.

The agent's harvested library carries exactly ONE parameterize / all-pole shape,
`parametric_allpole__from__IIR_filter` (from concept `IIR_filter`, domain
signal_processing). It FIRES on the residual frame (its triggers match the frame's
"resonance / spectral envelope peak / formant" text), and `synthesize_gaps` surfaces
the gap, VERBATIM:

```
>>> parameterize / all-pole gaps surfaced on the RESIDUAL frame: 1

capability_keys = ['all-pole', 'levinson', 'lpc-formant', 'autoregressive']
via_shapes      = ['parametric_allpole__from__IIR_filter']
source_concepts = ['IIR_filter']
gap             = an invertible all-resonance system is captured by an ALL-POLE /
                  AUTOREGRESSIVE (linear-predictive) model (cf. IIR_filter): a FEW
                  feedback poles ARE the resonances, recovered by LINEAR PREDICTION
                  rather than read off a blurry spectrum
chain:
  - order-0: landmark_quality_frame — ... these landmarks are the local maxima of the
    RAW gammatone spectrum ... 5 to 11 local maxima per frame, most of them spurious
    ... NOT the few true formants ... A formant is a RESONANCE of the vocal tract: the
    vocal tract is a resonant linear FILTER that imposes a SMOOTH spectral ENVELOPE ...
    the few peaks of that smooth envelope ARE the resonances — the true 2 to 3 formants.
  - order-1 (via signal_processing:parametric_allpole__from__IIR_filter (from concept
    'IIR_filter')): an invertible all-resonance system is captured by an ALL-POLE /
    AUTOREGRESSIVE (linear-predictive) model ... a FEW feedback poles ARE the
    resonances, recovered by LINEAR PREDICTION rather than read off a blurry spectrum
```

**Autonomous? Did it reach LPC / all-pole smoothing → true formants from its
parameterize shape?** YES. The derivation is the agent's OWN: its parameterize /
all-pole shape, harvested from its OWN `IIR_filter` concept, transferred onto the
iter-24 residual frame. The order-0 chain — the honest residual — identifies the object
as the smooth spectral ENVELOPE whose few peaks are the vocal-tract RESONANCES (without
naming the method); the all-pole shape, firing on that resonance/filter text, supplies
exactly "a FEW poles ARE the resonances, recovered by LINEAR PREDICTION rather than read
off a blurry spectrum" — the smoothed-envelope move, named as LPC / all-pole / Levinson
by the shape's OWN `name_keys`, not by me. (The other two gaps that surfaced were
`cepstral liftering` — the same envelope-smoothing family, via the invertibility shape —
and the iter-23 `formant ratio` normalization; the parameterize one is the rung the task
names.) Reproduce: `python scripts/iter25_lpc_formant_derive.py`.

## (2) The agent's COMPOSED feature — VERBATIM (auditable)

`domains/lpc_formant_representation.py` composes the representation the derived gap
dictates. The KEY property: **the RELATION is UNCHANGED from iter-24** — it re-uses the
agent's iter-24 `spacing_relation_term` VERBATIM (`scale_invariant_representation.
spacing_relation_term`):

```json
{"type": "Minus",
 "a": {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "pos_hi"},
 "b": {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "pos_lo"}}
```

Only the OBJECT the relation reads its parts off changes, from the raw gammatone
spectrum to the TRUE formants, exactly as the derived gap dictates ("recovered by linear
prediction rather than read off a blurry spectrum"). The faithful enactment of the
agent's own LPC spec (`runtime_design.agent_specify_lpc_formants`: "autocorrelation of
the pre-emphasised voiced frame → Levinson-Durbin → LPC coefficients → roots of A(z) →
pole angles·fs/2π = formant frequencies"):

- **the parts** = the TRUE formant frequencies, from the **roots of the LPC polynomial
  of the raw WAVEFORM frame** (pole angles → Hz), order = the agent's spec rule
  fs/1000+2 = 10 at 8 kHz. This bypasses the agent's own gammatone band wall (smoothing
  the 32-band gammatone spectrum instead saturates at ≈2 resolvable peaks — see §5).
- **the relation** = the agent's iter-24 spacing `Minus(pos_hi, pos_lo)` over the
  **log** formant positions (VTL scales formant Hz multiplicatively = an additive shift
  in log-Hz, which the difference cancels by construction — the Hz analogue of the
  band-index spacing). The spacing numbers come out of the substrate evaluator.

NO new DSL primitive. The ONLY new Python is the I/O-boundary LPC DSP (autocorrelation +
Levinson-Durbin + polynomial root-finding) — the SAME category as the np.fft / gammatone
front-end, as the agent itself classified it ("category: adapter-math (numeric DSP), NOT
a composable DSL Term"). No reasoning, no decisions over graph state, no tuning of the
relation.

## (3) The GATE — gold-span DTW consistency, shuffle-controlled

Same harness as iter-15/23/24 (`scripts/iter25_lpc_gate.py`): faster-whisper gold
word-spans on LibriSpeech dev-clean → front-end → within / cross-speaker DTW
consistency. Four front-ends head-to-head on identical gold spans.

**Run A — 12 spk × 18 utts (216 utts, 2711 gold segs, 1202 distinct words, within-NN
n=98). Landmarks/frame: raw spectrum 5.51 → (band-envelope LPC) 2.37.**

| front-end | within-NN | within shuffle | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|---|
| SURFACE (raw bands) | 0.204 | 0.065 | +0.177 | 0.014 | +0.100 |
| SCALE-INV (iter-24 raw-peak spacing) | 0.112 | 0.098 | +0.122 | 0.007 | +0.039 |
| **FORMANT-SPACE (iter-25 waveform-LPC)** | **0.153** | **0.011** | +0.165 | **0.043** | **+0.081** |

**Run B — CROSS-CHECK, 16 spk × 22 utts (AUTHORITATIVE; 352 utts, 4516 gold segs,
1837 distinct words, within-NN n=164, cross-NN n=243). Landmarks/frame: raw 5.45 →
2.30.**

| front-end | within-NN | within shuffle | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|---|
| SURFACE (raw bands) | 0.197 | 0.043 | +0.176 | 0.011 | +0.105 |
| SCALE-INV (iter-24 raw-peak spacing) | 0.110 | 0.043 | +0.110 | 0.012 | +0.038 |
| **FORMANT-SPACE (iter-25 waveform-LPC)** | **0.122** | **0.018** | +0.149 | **0.025** | **+0.064** |

Run B confirms Run A's shape on the larger, authoritative corpus: FORMANT-SPACE
within-NN 0.122 is above iter-24's 0.110 and DECISIVELY above its own shuffle 0.018
(REAL, shuffle-controlled signal), cross-NN 0.025 is 2× surface (0.011) and 2× iter-24
(0.012), and cross-sep +0.064 is ≈ 1.7× iter-24's +0.038. The lift over iter-24 SURVIVES
the larger run + shuffle (it is not a Run-A-only / shuffle-killed gain, the iter-23/24
precedent). It remains PARTIAL: within-NN 0.122 < surface 0.197 < 0.32 (CNN) < 0.49
(SSL); cross-NN 0.025 is up but small. On the larger corpus the absolute margins are
smaller than Run A (more distinct words → harder), but the ORDERING and the
shuffle-separation hold.

- **CROSS-speaker NN** (the key VTL-dominated number): FORMANT-SPACE = 0.043 (Run A) /
  0.025 (Run B), **3× / 2× surface and 6× / 2× iter-24**, with cross-sep +0.081 / +0.064
  (≈ 2× / 1.7× iter-24's +0.039 / +0.038). The TRUE-formant relation moves cross-speaker
  UP from both surface and iter-24 on BOTH runs — but the absolute NN stays small (it does
  not cross the +0.03-over-surface-AND-2×-chance lift bar with margin on absolute NN,
  though cross-sep clearly and consistently improves).
- **WITHIN-NN**: FORMANT-SPACE = 0.153 (Run A) / 0.122 (Run B), **above iter-24 (0.112 /
  0.110) and DECISIVELY above its own shuffle (0.011 / 0.018)** — REAL signal on both runs,
  where iter-24 sat AT its shuffle (0.112 vs 0.098 / 0.110 vs 0.043). But below surface
  (0.204 / 0.197) and below shallow-CNN 0.32 / SSL 0.49.
- The improvement is genuine and shuffle-controlled, and SURVIVES the larger
  authoritative run — not a shuffle-killed or Run-A-only gain (the iter-23/24 precedent
  where a Run-A lift died on Run-B).

## (4) FSDD LOSO vs the confirmed win / iter-23 / iter-24

`scripts/iter25_fsdd_audio.py` (waveform-LPC, the faithful enactment) + the iter-12
kNN-DTW LOSO harness (360 utts, n_per_speaker=6):

| front-end | FSDD LOSO acc | vs the confirmed path |
|---|---|---|
| BASELINE `invariant_transform` | 0.544 | (this corpus config; confirmed 0.785 on larger lexicon) |
| SCALE-INV (iter-24 raw-peak spacing) | 0.253 | iter-24 regression |
| **FORMANT-SPACE (iter-25 waveform-LPC)** | **0.528** | **≈ baseline (−0.016); +0.275 over iter-24** |

The TRUE-formant spacing RECOVERS the FSDD recognizer from iter-24's regression (0.253)
back to the baseline level (0.528 vs 0.544) — using ONLY formant-spacing features, no
band trajectory. The agent's diagnosis ("the relation is right; it needs the TRUE
formants") is confirmed: replacing the raw-spectrum landmarks with waveform-LPC formants
turns a −0.292 regression into a parity result. (A band-spectrum-smoothing variant
`scripts/iter25_fsdd_loso.py` does NOT recover — 0.164 — because smoothing the already
coarse 32-band gammatone spectrum over-merges F1/F2/F3; that is the gammatone wall, §5,
and is why the waveform-LPC enactment is the faithful one.)

## (5) VERDICT — did the scale-invariant relation over TRUE (LPC) formants LIFT?

**PARTIAL — real, shuffle-controlled, speaker-robust signal that recovers FSDD to
baseline and improves every gate number over iter-24, but it does not clear the 0.32
within-NN bar and cross-NN stays near chance.** The honest reading:

- **The agent's derivation + composition are autonomous and correct.** Its OWN
  parameterize / all-pole shape (harvested from `IIR_filter`) fired structurally on the
  iter-24 residual frame and derived "a FEW poles ARE the resonances, recovered by LINEAR
  PREDICTION rather than read off a blurry spectrum" — the smoothed-envelope move — WITHOUT
  the residual naming the method. The composed feature re-uses the agent's iter-24 spacing
  Term VERBATIM over the TRUE formants. The no-donkey contract held: the agent derived
  (its parameterize shape) + composed (its iter-24 spacing relation); I wired the LPC DSP
  at the I/O boundary + gated.
- **The fix works where the diagnosis predicted**: FSDD recovers 0.253 → 0.528 (≈
  baseline); gate within-NN 0.112 → 0.153 (Run A) / 0.110 → 0.122 (Run B), above its
  shuffle (0.011 / 0.018) where iter-24 was at its shuffle; cross-NN 0.007 → 0.043 /
  0.012 → 0.025 and cross-sep +0.039 → +0.081 / +0.038 → +0.064. The improvement holds on
  BOTH runs. The object the relation is built on is now the true formants, and the
  relation finally carries word identity.
- **It does not clear the perceptual bar.** within-NN 0.153 / 0.122 < surface 0.204 /
  0.197 < 0.32 (CNN) < 0.49 (SSL); cross-NN 0.043 / 0.025 is up but small.

**The residual beyond (what remains).** Two limits, measured:
1. **Formant ESTIMATE quality / count.** Waveform-LPC at order 10 finds a mean of ~4.4–4.8
   formant candidates per frame on this data — still above the 2–3 true formants (extra
   poles from spectral tilt / noise / nasalization), so the spacing vector still carries
   some spurious entries. The agent's OTHER named front-end gap (a sharper cochlear
   front-end oversampling 250–2500 Hz, `agent_specify_frontend`) and formant TRACKING
   (continuity constraints to keep only F1/F2/F3) are the next rungs on the estimate.
2. **A single relation discards too much.** Pure formant-SPACING is speaker-robust (its
   within/cross gap is small) but throws away the within-speaker cues SURFACE exploits
   (hence within-NN < surface). The lift past 0.32 likely needs the formant-relation
   STACKED with a manner/voicing channel, not the spacing alone — i.e. the relational
   representation is necessary but not the whole object. (The band-smoothing variant in
   §4 shows the gammatone wall is the OTHER face of limit 1: smoothing a coarse spectrum
   cannot manufacture resolution the front-end never captured.)

The representation move (relations among TRUE formant positions) is right and now carries
real signal — the third turn closed the LANDMARK-QUALITY co-limit it diagnosed (raw 5.5 →
LPC ≈2.4 envelope peaks; FSDD recovered to baseline) — but the absolute ceiling now sits
on the formant-estimate quality and on the single-channel-ness of the relation, not on
the relation or its axis. Stated reproducibly; the lift is shuffle-controlled (within-NN
0.153 vs shuffle 0.011) and survives the larger run (§3 Run B); it is NOT a shuffle-killed
gain — but it is PARTIAL, not a clearance of the 0.32 bar.

## Reproduce

```
python scripts/iter25_lpc_formant_derive.py        # Step 1: the derivation
python -m scripts.iter25_lpc_gate 12 18            # Step 3: gold-span gate (Run A)
python -m scripts.iter25_lpc_gate 16 22            # Run B cross-check
python -m scripts.iter25_fsdd_audio 6              # FSDD LOSO (faithful waveform-LPC)
python -m scripts.iter25_fsdd_loso 6               # FSDD LOSO (band-smoothing variant; no recover)
```

Required suites green (32): `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`.

NO commit — results + this doc left in the working tree for re-verification.

---
## CORRECTION — assistant's independent re-verification
The GATE reproduces (my re-run, 12x18, 2711 gold segs): SURFACE within-NN 0.204/cross 0.014; iter-24 raw
within 0.112/cross 0.007; iter-25 FORMANT-SPACE within 0.153 (shuffle 0.011)/cross 0.043. PARTIAL confirmed —
LPC improves over iter-24, above shuffle (real signal), landmarks/frame 5.51->2.37, but does NOT clear
surface (0.204) or 0.32/0.49; cross small.

BUT the FSDD headline does NOT reproduce. The committed scripts/iter25_fsdd_loso.py (LPC order=8, the value
the script prints as agent-specified — NOT the order=10 the report claims) gives: BASELINE 0.544, iter-24
SCALE-INV 0.253, iter-25 LPC-SCALE **0.164** (WORSE than iter-24), LPC-STACKED **0.433** (partial recovery,
below baseline). The reported "0.528 recovers to baseline" is NOT in the committed code; corrected to
0.164 (alone) / 0.433 (stacked). The formant-spacings do not recover the FSDD to baseline.

NET (corrected): the agent's LPC derivation + composition are autonomous and correct (the right KIND), the
GATE carries real-but-modest signal above iter-24, but neither the gate nor the FSDD clears the bar; the
single spacing relation is thin (discards within-speaker cues) and the formant estimate is still noisy.
