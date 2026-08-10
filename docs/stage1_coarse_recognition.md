# Stage 1 — COARSE ISOLATED RECOGNITION (the squint, clean single words)

The agent executes STAGE 1 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"coarse isolated
recognition (squint-first) — a front end worth squinting from."* This is the
agent acting on its own ranked gap map (`docs/sense_self_assessment.md`) and its
own ordering principle 3 ("coarse before fine — the squint first"), not a
hand-authored plan (memory `ozma_dont_author_seeds_agent_designs_them`).

Run capture: `/tmp/stage1_full.log` (end marker
`===MARKER_STAGE1_COARSE_RECOGNITION_CHECK_COMPLETE===`).
Structural check: `PYTHONUNBUFFERED=1 python -m scripts.stage1_coarse_recognition_check`.

---

## (1) The Stage-1 definition (the agent's own, verbatim from its curriculum)

- **Skill to acquire.** Recognise isolated, clean, single-talker words from the
  COARSE gestalt representation — the squint pass.
- **Toolbox used.** T5 (the squint / coarse↔fine resolution ladder,
  `domains/acoustic_resolution.py`), T1 (native recognition Terms — the
  `Argmin`/`Argmax` decision in the graph), T2 (`DtwTo` trajectory-alignment
  kernel, a native Term), T8 (weighted-admissibility combine), the T12 front-end
  output; the **NATIVE front end from Stage 0** (native `lpc_roots_formants` /
  TFS) is the chain everything reads.
- **Prerequisites.** Stage 0 — **DONE** (`docs/stage0_transduction.md`, gate
  fired: the temporal-code limb (TFS graded voicing) + the sharp-front-end limb
  (native all-pole formant extraction) owned natively, bit-faithful to the Python
  oracle, 0.005 Hz max drift).
- **Success signal (a BINARY READINESS GATE, not an accuracy number).** "The
  coarse-band recogniser is stable and the resolution ladder (T5) holds at coarse
  — the squint already separates the easy contrasts." Read from the agent's own
  self-measurement instruments as a STRUCTURAL / coherence signal —
  **structure-admitted, proceed** — never from a held-out LOSO accuracy sweep
  (the accuracy test comes AFTER the curriculum;
  memory `ozma_no_premature_testing_mid_curriculum`).

### What the agent did

**(a) The Stage-0 hand-off (mechanical, no new capability).** The standing
recognition cue extractors that estimate sharp formants
(`_vtl_formant_allpole`, `_vtl_formant_dynamic`, `vtl_formant_track`) were still
calling the **Python** DSP `domains.lpc_formant_representation._lpc_roots_formants`
— the precise next step the Stage-0 doc named (`docs/stage0_transduction.md` (3):
*"Wiring the native formant primitive into `agent_frontend` cue extractors … is
the precise next step, and it belongs to Stage 1's hand-off"*). They are now
re-pointed at the agent's OWNED NATIVE chain
(`substrate_rs._native.lpc_roots_formants` — autocorr → Levinson-Durbin → roots
of A(z) → pole-angle Hz, Stage-0 / W1 / Gap 2), via one thin boundary helper:

| file:line | change |
|---|---|
| `domains/agent_frontend.py:80` | `_native_lpc_roots_formants(seg, fs, order, …)` — thin one-line hand-off into `substrate_rs._native.lpc_roots_formants` (feeds the RAW frame; Rust does pre-emph+window+autocorr+Levinson+root-find+pole→Hz internally) |
| `domains/agent_frontend.py:324` | `_vtl_formant_allpole`: `_lpc_roots_formants = _native_lpc_roots_formants` (was Python import) |
| `domains/agent_frontend.py:397` | `_vtl_formant_dynamic`: same re-point |
| `domains/agent_frontend.py:487` | `vtl_formant_track`: same re-point |

The native chain was proven **bit-faithful** to the Python oracle in Stage 0
(0.005 Hz max formant drift over 274 real FSDD frames), so this is a pure
re-point — the SAME formant structure, now owned in-substrate, composable /
gateable. **Verified wired** (`/tmp/stage1_full.log` part (a)): native
`lpc_roots_formants` returns formants `[342.7, 1844.6, 1898.2, 2587.4, 3415.8]`
Hz on a real token, and all three cue readouts flow non-zero (allpole 72/72,
dynamic 72/72, track 8 frames × 6 chan) — the native formants/voicing flow into
the cues.

**(b) Coarse isolated recognition (squint-first).** The agent composes
recognition of isolated digit words at the COARSE scale first:

- **The squint (T5).** The native cochleagram (T12) collapsed to `resolution`=3
  low/mid/high band-means per frame (the seed coarsest rung,
  `seeds/acoustic_resolution.json` → `ladder [3,6,12,25]`), kept as an ORDERED
  per-frame trajectory and per-frame mean-subtracted (the agent's own
  speaker-baseline removal, `enrich_sign_bands` normalize) so the coarse SHAPE is
  speaker/level-relative — the gestalt dimensional collapse where the invariant
  structure lives and fine speaker/noise variation is suppressed
  (`scripts/stage1_coarse_recognition_check.py:coarse_trajectory`).
- **The native decision (T1 + T2).** Recognition is composed as the agent's
  native graph Terms — `Argmin` over candidate words (`Concept : is_word == 1`)
  of `DtwTo`(observed coarse trajectory, word's coarse prototype trajectory) — the
  SAME shape as `domains/native_cognition.predict_articulatory_term`, the score
  being the pure coarse-trajectory `DtwTo`. Evaluated by the Rust substrate
  (`substrate.evaluate`), not Python
  (`scripts/stage1_coarse_recognition_check.py:coarse_predict_term`).

### Donkey audit

- NO net, NO `.fit`, NO gradient, NO loss, NO sweep-to-fit, NO swept knob
  (grep of the new script + the hand-off is clean; the squint is the agent's own
  `np.array_split`-into-N-band-means gestalt collapse, the decision is the native
  `Argmin`-of-`DtwTo` Term).
- `resolution`=3 is read from the seed dial, not a Python literal.
- The Stage-0 native all-pole chain is the front end (the hand-off).
- `CortexLoop` + `scripts/solve_for_n.py` **untouched** (git diff confirms — no
  `runners/` diff at all; the native chain was already built in Stage 0).
- The structural check reads **3000 real FSDD** waveforms (clean, isolated,
  single-talker — exactly the Stage-1 input class); **no held-out LOSO accuracy
  is banked as the verdict** — the gate is the SEPARATION STRUCTURE.

---

## (2) The READINESS GATE verdict — structure-admitted

The gate is **structural admission**, not a tuned number: does the coarse squint
COMPOSE and produce a coherent, SEPARABLE structure over the isolated words (the
gestalt clusters cohere / coarse word-identity emerges)? Read via the agent's own
native `DtwTo` instrument over **3000 real FSDD tokens, 6 speakers** — for each
token, the coarse-trajectory `DtwTo` distance to its OWN-word prototype vs to
OTHER-word prototypes:

| structural check | value | gate |
|---|---|---|
| the squint composes (every token → 3-band ordered trajectory) | True | ✓ |
| the native decision composes (Argmin of DtwTo, native eval) | True | ✓ |
| within-word coarse DtwTo (mean ± sd) | **0.0084 ± 0.0048** | tighter |
| between-word coarse DtwTo (mean ± sd) | **0.0110 ± 0.0041** | looser |
| structural separation (own-word nearest cluster) | **0.761** of tokens | majority |
| standardized coarse cluster gap d′ (between − within / pooled sd) | **0.573** | real effect |

```
=== READINESS GATE ===
  squint composes (coarse trajectory)            : True
  native decision composes (Argmin of DtwTo)     : True
  coarse structure separates words (within<betw) : True (sep 0.761)
  gestalt clusters cohere (standardized gap > 0.2): True (d'=0.573)
  >>> STAGE-1 COARSE STRUCTURE ADMITTED          : True
```

**GATE FIRES.** The coarse squint COMPOSES (the native cochleagram collapses to
the 3-band gestalt trajectory for every token), the native recognition decision
COMPOSES (the `Argmin`-of-`DtwTo` Term evaluates over the squint in Rust), and the
coarse representation produces a COHERENT, SEPARABLE structure: within-word coarse
trajectories are systematically tighter than between-word (0.0084 < 0.0110) on a
clear majority of tokens (76.1%) with a real standardized cluster gap (d′ = 0.573).
The squint already separates the easy contrasts at the coarsest rung — the
agent's own Stage-1 success signal ("the squint already separates … only then is
un-squinting warranted"). The structure is admitted in-substrate — a structural
coherence property of the coarse representation read from the agent's own native
`DtwTo` instrument, NOT a tuned held-out accuracy.

---

## (3) Is Stage 1 COMPLETE?

**Yes — the readiness gate fires.** Both halves of Stage 1 are done:

1. **The Stage-0 hand-off is wired** — the standing recognition cue extractors
   consume the agent's OWN native all-pole formant chain instead of the Python
   DSP (native formants/voicing flow into the cues; verified non-zero readouts).
2. **Coarse isolated recognition is composed squint-first** — the native
   cochleagram collapsed to the seed-coarsest 3-band gestalt trajectory, with the
   native `Argmin`-of-`DtwTo` recognition decision evaluating over it, and the
   coarse representation yields a coherent, separable word-identity structure (the
   resolution ladder T5 holds at coarse — the squint separates the easy
   contrasts, so un-squinting is NOT yet warranted).

The Stage-1 success signal as the agent defined it — "the coarse-band recogniser
is stable and the resolution ladder holds at coarse" — is met as a STRUCTURAL
admission, not an accuracy. Stage 2 (sonority / voicing structure, adding the
graded TFS voicing prong via T8 onto this working coarse recogniser) is the next
stage, and its prerequisite (a working coarse recogniser to add the prong to) is
now satisfied.

### Honest scope note (the precise edge of what was done)

- The gate verified is **structural separability of the coarse squint** read via
  the native `DtwTo` (within-word tighter than between-word with a real
  standardized gap) — the correct Stage-1 signal under the donkey constraint (no
  accuracy sweep, no banked held-out). It is NOT a claim of high recognition
  accuracy; it is the binary admission that the coarse structure SEPARATES the
  words, which is exactly what "squint-first separability" means.
- The prototypes are single per-digit exemplars from one speaker; the 10
  prototype tokens themselves contribute degenerate zero-distance self-matches
  (~10 of 3000, negligible) — the separation signal is carried by the other
  ~2990 real tokens, including all 5 held-back speakers (the structure separates
  ACROSS speakers at coarse, the point of the squint's speaker-generality).
- The squint is deliberately coarse (3 bands): the residual non-separated 23.9%
  of tokens is the fine-contrast tail the LATER stages address (Stage 2 voicing,
  Stage 3 speaker-invariant, Stage 5 frication) — un-squinting (stepping the T5
  ladder 3→6→12→25) is reserved for a MEASURED plateau, not done pre-emptively
  (principle 3). The gate's job is only to confirm the coarse gestalt is admitted.

Stage 1's gate is **the squint composes + the coarse word-identity separates** —
and it fires.

```
===MARKER_STAGE1_COARSE_RECOGNITION_CHECK_COMPLETE===
```
