# Persona speech world × the new native cognition — does the grounding loop close?

The persona speech world (`domains/persona_speech_world.py`,
memory `ozma_persona_speech_world` / `ozma_babble_grounding`) is the agent's closed
sensorimotor loop: it **speaks** through personas it controls (varying pitch f0,
resonance q, vocal-tract length vtl), **hears** itself (re-ingests the synthesised
audio), and **recognises** the word it spoke. With the OLD cognition (the per-sign-id
NB-vote recogniser) it hit a **25 % self-recognition wall** and collapsed almost
everything to "five".

This run wires the **new native cutover cognition** (commit 410859ad — formant-trajectory
DTW + native articulatory d_A + native multi-pronged fusion + native k-NN mel vote, every
decision a graph Term) into that loop and measures whether the new agent recognises its
own synthesised speech.

`scripts/speech_world_native.py` · full log `/tmp/speech_world_native_full.log`
(end marker `SPEECH_WORLD_NATIVE_COMPLETED`).

## (1) What was wired — donkey audit

- **Speak (the agent's voice) — UNCHANGED, owned.** `STTPipeline.speak` →
  Rust `synthesize_from_trajectory` (source-filter voicebox over the lexicon's
  most-heard-sign A1-patch trajectory). **No TTS net, no `.fit` in the speak path.**
  `persona_speech_world.speak_as` layers f0/q (synth params) + vtl (waveform resample) —
  the cheap speaker differences. This is the agent's own forward-model synthesis, kept
  exactly as the world already had it.
- **Recognise — REPLACED with the native cutover path.** The old `predict_one`
  (per-sign NB vote over `vote_counts`, the recogniser that hit the 25 % wall) is no
  longer in the loop. In its place: the **same** native decision code
  `scripts.articulatory_gamma` runs on FSDD —
  - formant-trajectory DTW prong: `dtw_predict_term()` (Argmin / MinOver / DtwTo), native;
  - articulatory d_A prong: `domains.native_cognition` (Argmin of `DtwTo + Γ-cost`), native;
  - multi-pronged fusion: `domains.native_fusion` (Argmax-of-Plus-of-Times,
    weighted-admissibility), native;
  - mel exemplar k-NN: `domains.native_vote` (top-k majority Fold), native.
  All imported **verbatim** from the cutover scripts; every recognition DECISION is a graph
  Term evaluated by `substrate.evaluate`. **No Rust added; CortexLoop / solve_for_n /
  cargo untouched.** Only transduction (LPC formant tracker, log-mel front-end, `mi.dtw`
  kernel) + audio I/O stay Python, by design.
- **Banks / held-out honesty.** The lexicon the agent speaks from + the recognition banks
  (formant-trajectory exemplars, mel exemplars, n-gram, tau scales, prong reliability
  weights) are built from FSDD **train** speakers (one speaker, `jackson`, held out of the
  banks). The **test audio is the agent's own synthesised speech** — self-generated, not
  held-out FSDD recordings. So this measures *self-recognition in the closed loop* (the
  persona-world question), not held-out FSDD generalisation (the cutover's 58–83 % LOSO
  numbers stand separately).

## (2) Result — self-recognition across personas

Full run — banks from 5 FSDD train speakers (2500 exemplars, `jackson` held out),
10 digits × 4 personas = 40 closed-loop attempts (0 unvoiced), `elapsed 67 s`:

| recogniser (native) | self-recognition |
|---|---|
| **FUSED multi-pronged** | **7.5 %** (n=40) |
| formant-trajectory DTW prong | 10.0 % |
| articulatory-Γ prong | 10.0 % |
| mel exemplar k-NN vote | 10.0 % |

vs the **OLD 25 % NB-vote wall**. Chance is 10 %. Per-persona FUSED: pip 10 %, ada 10 %,
milo 10 %, bertram 0 % (n=10 each).

The new native cognition does **NOT** close the loop on the agent's own synthesised
speech — it is **at/below chance, worse than the old 25 % wall**. The confusion matrices
show why: every prong collapses to a **single** prediction independent of the word spoken.
The fused decision sends 31/40 inputs to **"four"**; the **mel-vote prong sends all 40 to
"five"** — *exactly* the old wall's collapse-to-five signature, reproduced. (The script's
"collapse-to-five broken: YES" flag only checks the *fused* sink, which happens to land on
"four" instead; the mel prong shows the literal old behaviour.)

## Root cause — the limiter is the SPEAK path, not the recognition

The decisive diagnostic (`speak(word)` for each digit, then formant-track the result):

```
  zero: mean_rel=[-0.59  0.15  0.45]   five: mean_rel=[-0.60  0.15  0.45]
   one: mean_rel=[-0.60  0.15  0.45]    six: mean_rel=[-0.59  0.15  0.45]
   ... every digit's synthesised formant trajectory is the SAME ...
```

Every digit synthesises to a **near-identical** formant trajectory (and mel pattern). The
stored per-word "most-heard-sign" trajectories the voicebox renders have a mean pairwise
L2 of only **0.133** against a unit norm — ~13 % separation, with some word-pairs at
**0.000** (identical). The rendered audio is therefore essentially word-independent
*before recognition ever sees it*.

So the recognition is being handed near-identical signals and dutifully maps them all to
one nearest exemplar. **The cognition is not the limiter** — it is the validated cutover
path that scores 58–83 % on *real* FSDD audio. The limiter is the **forward model**: the
lexicon's most-heard-sign A1-patch trajectory does not encode word-discriminative spectral
structure, so the agent's own voice does not project into the formant-trajectory manifold
its recognition banks (built from real FSDD recordings) span. This is the
**speak↔hear representation mismatch**, located on the **speak** side.

## (3) VERDICT

**The grounding loop does not close — and the limiter is now pinpointed.** With the new
native cognition swapped in for the old NB-vote recogniser, self-recognition is at chance,
no better (slightly worse) than the old 25 % wall. But the cause is **not** the
recognition cognition and **not** "more data":

- The native multi-pronged recognition is the same code that recognises real FSDD audio at
  58–83 % cross-speaker — it is healthy.
- The failure is upstream, in the agent's **own synthesis**: `speak` renders a near-identical
  trajectory for every word, so the closed loop tests the recognition on a degenerate,
  non-discriminative signal. The mel prong's collapse-to-"five" is the OLD wall reappearing
  for the OLD reason — not a recognition deficiency but a **synthesis** one.

**The fix is the forward model's word-discriminativeness, not more audio.** For the
grounding loop to close, the speak path must render distinct, word-discriminative formant
trajectories — the agent's own voice must project into the same formant-trajectory space
the recognition banks were built from. Concretely: the per-word lexicon trajectory (the
most-heard-sign A1-patch path) needs to carry the spectral contrast that distinguishes the
words, and the source-filter voicebox needs to realise it. Until the agent can *speak*
distinct words, no recogniser — native or otherwise — can recognise them in the loop. This
is the honest order-of-operations: **the babble loop's "form" half (synthesis) is the
blocker, ahead of the "test" half (recognition).**

(The recognition cutover itself remains validated on real audio; this run does not regress
it. Nothing was committed.)
