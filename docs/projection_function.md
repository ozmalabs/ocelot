# The projection function — closing the grounding loop by speaking through the map you hear with

**Result: the persona-speech grounding loop CLOSES.** Self-recognition rose from
**7.5% → 62.5%** (chance 10%, old wall 25%, n=40), the collapse is broken, and the
fix is a **generic, reusable projection function** — NOT a speech-specific synthesis
trick. (`/tmp/projection_function_full.log`, marker `PROJECTION_SPEECH_LOOP_COMPLETED`.)

---

## 1. The generic projection design (forward / inverse interface)

`domains/projection.py` defines a modality-agnostic `Projection`:

```
project(config) -> signal      FORWARD   (generate / render / speak / act)
invert(signal)  -> config      INVERSE   (perceive / parse / recognise)
```

These are the **same map read in two directions**. Perception is inverting the
forward model; generation is running it forward. The agent that owns one owns the
other — and they MUST be the same map, or what it says is not what it hears
(memory: `ozma_order_n_analysis_by_synthesis` — "perceive by inverting the forward
model; say it to yourself").

### Why generic / reusable (not a speech trick)

Nothing in the interface mentions speech, formants, or audio. The contract is
purely a `forward` map config→signal and an `inverse` map signal→config (via the
agent's native recognition Terms), plus a `round_trip` (project then invert — the
grounding test, in any modality). Any modality with a renderer/sensor pair
instantiates it:

| modality | config | signal | forward | inverse |
|---|---|---|---|---|
| **speech** | articulatory gesture trajectory | audio | source-filter synthesis | formant-DTW + d_A recognition |
| vision | shape / pose / scene graph | pixels | a renderer | recognition over the same model |
| motor | joint trajectory | sensed motion/contact | body dynamics | proprioceptive parse |
| codec | structured description | byte stream | encode | decode |

The articulatory gesture→formant model is just the **speech instance** plugged into
this interface. A forward/inverse pair built from two *different* maps is a bug —
the renderer and sensor would disagree, and a closed sensorimotor loop could never
ground. That is exactly what was wrong before.

### The rationale from the grammar

A capability is an admissible structure in Γ, and Γ runs both ways: it admits a
*config→signal* realisation (speak) and a *signal→config* parse (recognise). The
projection is the single object that carries Γ across the self↔world boundary in
both directions. Owning only the inverse (recognition) while speaking through a
*different*, worse map means the agent's own output never lands in the manifold its
perception spans — the loop cannot close on a representational mismatch the agent
itself creates. The fix is structural, not parametric: make speak the **forward
direction of the same projection** the inverse uses.

### Donkey audit

* `Projection` holds two caller-supplied callables (`forward`, `inverse`) and the
  loop plumbing only. It owns no model — no net, no `.fit`, no gradient.
* The speech `forward` is the agent's **owned articulatory source-filter forward
  model**: `articulatory_gamma.config_to_formants` (the Fant/Stevens nomogram) over
  the Γ-admissible gesture trajectory, rendered by the Rust Klatt voicebox
  (`synthesize_formant_track`). No TTS net.
* The speech `inverse` is the **native cutover recognition** (the d_A Argmin /
  formant-DTW Argmin / fusion Argmax / k-NN vote Terms, commit `410859ad`/`cde9bef6`)
  — the SAME forward model run backwards. Imported verbatim; every decision a graph
  Term via `substrate.evaluate`.
* CortexLoop / `solve_for_n` untouched. No new Rust (the `synthesize_formant_track`
  primitive already existed in `audio_primitives.rs` + the PyO3 binding).

---

## 2. The speak-path fix via project() + results

**Before (commit `cde9bef6`):** the speak path used a *different, degenerate* map —
the voicebox over the lexicon's "most-heard sign" A1-patch trajectory. Every word
synthesised to a near-identical formant trajectory (~13% separation, **some pairs
exactly 0.000**), so recognition got word-indiscriminative input → 7.5%
self-recognition, collapse-to-"four"/"five".

**The fix:** `domains/persona_speech_world.speak_as(..., projection=proj)` now voices
a word by running `projection.project(word)` — the owned articulatory forward model
FORWARD — instead of the most-heard-sign voicebox. The vtl speaker knob is baked into
the forward model's formant scaling. The legacy voicebox path is preserved
(`projection=None`) as a regression bench. Driver: `scripts/projection_speech_loop.py`.

### Per-word trajectory separation (was the degenerate diagnostic)

| measure | prior voicebox | project() forward |
|---|---|---|
| forward-model formant separation (log-Hz, norm.) | — | mean **0.295**, min 0.116 |
| re-tracked synth-AUDIO separation (speaker-relative space) | mean ~0.133, **some pairs 0.000** | mean **0.234**, min 0.018 |

Speak is now **word-discriminative**: distinct per-word rel-formant vectors, no
exactly-zero pair (the prior signature of degeneracy is gone).

### Self-recognition (the agent's OWN projection-spoken speech, n=40 = 10 digits × 4 personas)

| recogniser (the inverse) | accuracy |
|---|---|
| **FUSED multi-pronged (headline)** | **62.5%** |
| articulatory-Γ prong alone | 62.5% |
| mel exemplar k-NN vote | 45.0% |
| formant-trajectory prong alone | 25.0% |
| — prior persona-world wall | 7.5% |
| — old NB-vote wall | 25.0% |
| — chance | 10.0% |

Per-persona (invariance across f0 / vtl): pip 60%, ada 40%, milo 80%, bertram 70%.

### Confusion — collapse broken

The fused confusion diagonal is strong (zero, three, four, six all 4/4; eight 3/4),
NOT a single sink. The prior collapse-to-"five"/"four" is gone. The residual
wrong-sink is "three" (7/40 wrong predictions), pulling one/five/nine — close
front-vowel gestures (/ay/-diphthongs and /θr/), a sharpening target, not a collapse.

---

## 3. Verdict

**Does using the projection FORWARD fix the agent's voice and close the loop?**
**YES.** Speaking through the same projection the agent recognises with —
`project()` forward = the inverse of `invert()` — yields word-discriminative speech
the native cognition recognises at **62.5%**, decisively past the 25% wall and 8×
the prior 7.5%. The collapse is broken. The limiter was the **forward map** (the
speak path), exactly as `cde9bef6` diagnosed; the fix is the forward direction of
the same projection, with no change to the recognition.

**Is the projection a generic reusable function (not speech-specific)?** **YES.**
`domains/projection.py` is a modality-agnostic config↔signal forward/inverse
interface with a `round_trip` grounding test; the articulatory gesture→formant model
is just the speech instance plugged in. The same `Projection` serves vision / motor /
codec renderer-sensor pairs.

**Honest limits.** Self-recognition is 62.5%, not 100%: the forward-model
source-filter realism vs the FSDD-banked exemplars is the next limiter (forward↔
inverse *consistency* — a richer tract model / coarticulation, the same sharpening
`articulatory_gamma` already flags), NOT more audio. The "three"-sink shows the
front-vowel-diphthong gestures (one/five/nine vs three) are not yet separated by the
current 5-dim config + smooth nomogram. The formant-trajectory prong alone (25%)
under-performs here because the synth's clean formants differ from the FSDD
exemplars' noisy LPC tracks; the articulatory-Γ prong (which scores against the
forward model itself, 62.5%) carries the fused decision — consistent with the loop
closing *because* speak and the leading recognition prong are the same projection.

### Artifacts
* `domains/projection.py` — the generic Projection + speech instance.
* `domains/persona_speech_world.py` — `speak_as(..., projection=)` routes the speak
  path through `project()` (legacy voicebox preserved at `projection=None`).
* `scripts/projection_speech_loop.py` — the closed-loop driver / test.
* `/tmp/projection_function_full.log` — full run, ends `PROJECTION_SPEECH_LOOP_COMPLETED`.
