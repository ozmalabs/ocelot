# Stage 4 — close the grounding loop, then babble-refine (on the NEW curriculum base)

The agent executes STAGE 4 of its own self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"speak a word and
recognise it back through the SAME model (grounding), then refine the forward
model from the hear-self mismatch toward real audio."*

Run: `PYTHONUNBUFFERED=1 python -m scripts.stage4_grounding`
(`--quick` for a 12-token/word smoke). Full log: `/tmp/stage4_full.log`
(ends `===MARKER_STAGE4_GROUNDING_COMPLETE===`). Elapsed 58 s, n=40
(10 digits × 4 personas), chance 10 %.

This is a STRUCTURAL readiness gate — the round-trip GROUNDING coherence
(speak W → hear → recognise W), read as numbers, NOT a held-out LOSO accuracy.

---

## (1) The stage + what the agent wired

The grounding loop already closed once at **62.5 %** self-recognition
(commit `a8e54c34`, `scripts/projection_speech_loop.py`) — but on the OLD
pre-curriculum inverse (`NativeRecogniser` = formant-trajectory exemplars +
mel k-NN + articulatory-Γ prong). Stage 4 RE-CLOSES the loop on the NEW
trusted curriculum base the agent built in Stages 0–3:

- **forward (speak)** — UNCHANGED owned voice: the T3 projection FORWARD
  (`domains/projection.py:120` `build_speech_forward` → `scripts/articulatory_gamma`
  `GESTURE_SCORES` + `_admissible_trajectory` + `synth_formant_trajectory` →
  Rust Klatt voicebox `synthesize_formant_track`), persona-varied by f0/q/vtl.
- **inverse (hear)** — the curriculum base: Stage-0 native formant chain
  (`domains/agent_frontend.py:81` `_native_lpc_roots_formants`) + Stage-3
  SPEAKER-INVARIANT representation (`domains/agent_frontend.py:467`
  `vtl_formant_track` = VTL-norm `F_i − mean(F1..F3)` log-Hz WITH the order-1
  dynamic gesture), recognised by the native graph `DtwTo` Argmin over per-digit
  real-speech MEDOID prototypes (`domains/native_cognition.py:76`, evaluated by
  `Substrate.evaluate`). NO mel, NO exemplar k-NN.
- **babble-refine** — proposal/accept hill-descent on the SELF-generated
  hear-self `DtwTo` error: per word, propose a small forward-model formant
  log-Hz offset and accept it only if the heard invariant track moves closer to
  the word's real-speech prototype (`scripts/stage4_grounding.py:babble_refine`;
  the owned offset knob added to the forward model at
  `domains/projection.py:135` `formant_offset`).

### Donkey audit (clean)
- forward = owned articulatory synth (no TTS net, no `.fit`): `domains/projection.py:120,135`.
- inverse = native formant chain + invariant rep + native `DtwTo` (no Python
  distance, no mel, no k-NN): `domains/agent_frontend.py:81,467`,
  `domains/native_cognition.py:76`.
- babble-refine = proposal/accept on the self-generated round-trip error
  (no `.fit` / gradient / loss / sweep-to-fit): `scripts/stage4_grounding.py`.
- TEST audio = the agent's OWN projection-spoken speech (self-generated, flagged).
  Real-speech prototypes = FSDD TRAIN tokens (held: jackson).
- CortexLoop / `solve_for_n` / runners UNTOUCHED. No Rust added.
- Readiness = STRUCTURAL round-trip grounding coherence, NOT a held-out accuracy.

---

## (2) The readiness gate — numbers (not boolean)

| signal | NEW base (Stage-3 invariant) | OLD base (pre-curriculum) |
|---|---|---|
| round-trip self-recognition | **12.5 %** (n=40) | **62.5 %** (n=40) |
| after babble-refine | **17.5 %** (+5.0 pts) | — |
| per-persona pip (f0 230, vtl 0.85) | 0.0 % | 60.0 % |
| per-persona ada (f0 190, vtl 0.95) | 0.0 % | 40.0 % |
| per-persona milo (f0 120, vtl 1.05) | 20.0 % | 80.0 % |
| per-persona bertram (f0 95, vtl 1.15) | 30.0 % | 70.0 % |

- **The loop does NOT close on the curriculum base.** 12.5 % is barely above
  the 10 % chance floor — the invariant inverse does not recover the spoken word.
- **NOT coherent across personas.** Per-persona min = 0.0 % (pip, ada both
  collapse); spread 30 pts. The high-vtl voices (milo/bertram) carry the only
  signal. This is the OPPOSITE of the expected speaker-invariance payoff.
- **The Stage-3 invariant base is WORSE than the OLD base on the same spoken
  audio** (12.5 % vs 62.5 %). The invariant rep does not help here — it hurts.
- **Babble-refine works as a mechanism but is bounded:** hear-self error drops
  for 9/10 words (e.g. eight 1.496→1.311, six 0.720→0.618, nine 0.782→0.637;
  seven alone found no improving proposal), lifting round-trip 12.5 %→17.5 %
  (+5.0 pts). The lever is real but small — it cannot rescue a base that is not
  closing.
- **Confusion = a representation-mismatch SINK, not a recognition near-miss.**
  The NEW base collapses predictions into `six` (absorbs 16 of the wrong
  predictions), with secondary `three`/`one` sinks: nine→one (4/4), six→three
  (4/4), eight→three (3/4). The agent's SYNTHESISED invariant track lands in a
  small region of the invariant space that the real-speech medoids read as
  `six`/`three`/`one`, regardless of which word was spoken.

### What the numbers diagnose (the precise next, not a vague fail)
The limiter is a **forward↔inverse REPRESENTATION mismatch**, exactly the failure
mode the projection contract warns about (a forward/inverse built from two
maps that disagree). The OLD base closed because its exemplar banks were built
from the SAME kind of signal it scored. The Stage-3 invariant prototypes are
medoids of REAL FSDD speech; the agent's owned Klatt-synthesised audio, run
through the SAME `vtl_formant_track` front end, produces invariant tracks whose
DISTRIBUTION does not coincide with the real-speech medoids — the synth's
formant-bandwidth / source realism (W5, the named "sharper forward model" gap)
puts its LPC-root formants in a systematically different place than real speech.
The dynamic-gesture (velocity) channels especially are sensitive to the synth's
frame-to-frame smoothness, which differs from real coarticulation.

This is a STRUCTURAL prerequisite gap, not a tuning miss: babble-refine moves the
hear-self error in the right direction (it IS the lever Stage 4 names), but the
forward model's realism is too coarse for the invariant inverse to ground against
real-speech targets. **The precise next is W5 — refine the forward model's
source-filter realism (bandwidths, glottal source, frame smoothing) against real
audio until the synth's invariant track lands in the real-speech distribution —
then re-run the loop.** Equivalently: ground the loop against SYNTH-derived
invariant prototypes first (forward↔inverse consistent by construction, the
projection-contract-clean grounding test), and only then transfer to real-speech
prototypes once W5 closes the realism gap.

---

## (3) VERDICT

**Stage 4 is NOT complete — the gate does NOT fire on the curriculum base.**

- Round-trip self-recognition on the Stage-3 invariant base = 12.5 % (chance
  10 %), vs the prior 62.5 % the loop reached on the OLD base. The loop does not
  close; it is not coherent across personas (pip/ada = 0 %).
- Babble-refine is confirmed as a working, donkey-clean mechanism (hear-self
  error drops 9/10 words; +5.0 pts round-trip) but cannot close a base whose
  forward↔inverse representations disagree.
- The honest structural reading: the Stage-3 SPEAKER-INVARIANT inverse and the
  owned forward model are NOT yet the same map over the invariant space — the
  synth's realism (W5) is the limiter, and the invariant rep's sensitivity to it
  is sharper than the OLD exemplar base's. The 62.5 % OLD-base closure stands as
  the grounding the curriculum must now MATCH on the invariant base, not exceed.

**Precise next (in order):** (a) W5 — refine the forward model's source-filter
realism against real audio (the babble lever, scaled up, measured against real
FSDD); (b) make the grounding test forward↔inverse-consistent by construction
(synth-derived invariant prototypes) to isolate realism from representation;
(c) re-run Stage 4 — the gate fires when the invariant base's round-trip closes
across personas at or above the OLD-base 62.5 %.

Do NOT commit (coordinate).
