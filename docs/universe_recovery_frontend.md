# Universe-recovery front end — the acoustic SENSE swap, cross-speaker

## Thesis (memory `ozma_trained_model_is_partial_universe_recovery`)

The raw cochleagram is the **crudest** universe-recovery: it reads the
exterior's surface spectrum but never recovers **speaker-normalisation**
(Ladefoged–Broadbent; the absolute-features wall that capped cross-speaker LOSO
at ~0.50). A trained self-supervised speech model (wav2vec2-class) is a
**partial universe-recovery** whose **mid layers are already speaker-normalised**
(existing probe `/tmp/ssl_w2v2.log`: cross-speaker same-word separation +0.088,
isolated +0.148, peak layer ~4–7).

**The donkey line — PERCEIVE WITH IT, DON'T THINK WITH IT.** The SSL model is the
**SENSE** (a fixed forward pass that reads the exterior's structure). It is the
feature extractor only. The **COGNITION** (the recognition decision) stays the
agent's owned ops — 1-NN over DTW trajectory distance — held byte-identical
across both senses.

## Build

`scripts/universe_recovery_frontend.py`. Two acoustic SENSES feed the SAME agent
recogniser:

1. **COCHLEAGRAM-CMVN** — a gammatone/ERB-spaced log filterbank cochleagram per
   frame (32 bands), per-utterance CMVN. The crude spectral front end (the
   absolute-features ~0.50 bar). Owned boundary DSP.
2. **SSL-RECOVERY** — `facebook/wav2vec2-base` mid-layer (layer 7) per-frame
   features, L2-normalised (cosine geometry). The partial universe-recovery; the
   net is a fixed forward pass on the waveform — **the SENSE, never the decision.**

**Cognition (identical for both):** 1-NN over length-normalised DTW
(`frame_inference_v1._dtw`, the agent's owned nearest-exemplar Argmin). No fit,
no gradient, no net in the decision.

## Test — robust SC cross-speaker LOSO (isolated words)

The cleanest test of the SENSE. An exemplar lexicon (bank) is built **only from
TRAIN speakers**; held-out speakers' clips are **NEVER banked**. Per held-out
clip: read the SENSE → 1-NN DTW against the train bank → argmin word. The SAME
split feeds both senses (same clips, same recogniser; only the sense differs).

- 40 train speakers / 25 held-out speakers (disjoint).
- bank ≈ 520 train clips, test ≈ 309 held-out clips.
- 10 digit words (`zero`..`nine`), chance 0.10.

## Results (cross-speaker LOSO, isolated words)

Run: `python -m scripts.universe_recovery_frontend 40 25 3 2 7`
(40 train / 25 held-out speakers; bank 520 train clips; test 309 held-out clips;
10 digits; chance 0.10). Captured to `/tmp/universe_recovery.log`, marker
`[MARKER] UNIVERSE_RECOVERY_FRONTEND_COMPLETED`, pgrep-verified exit.

| Acoustic SENSE | Cognition | Cross-speaker acc | n |
|---|---|---|---|
| Cochleagram-CMVN (crude spectral) | owned 1-NN DTW | **0.718** | 309 |
| SSL-recovery (wav2vec2 L7, speaker-normalised) | owned 1-NN DTW | **0.777** | 309 |

**LIFT (SSL − cochleagram) = +0.058 (+8% relative)** (chance 0.10).

## Verdict

**The claim HOLDS, but modestly.** With the cognition held byte-identical (owned
1-NN DTW), swapping ONLY the acoustic sense — crude cochleagram → SSL mid-layer
partial-universe-recovery — lifts cross-speaker accuracy **+0.058 (0.718 →
0.777, +8% relative)**. The speaker-normalised mid-layer recovers invariance the
crude cochleagram cannot, so the lift comes from the SENSE, not the cognition.

**Honest caveats:**

- The lift is **modest (+0.058)**, not the "FAR over" the prediction hoped for.
  The reason is that the cochleagram baseline here is **stronger than the ~0.50
  formant-trajectory wall** the task cited: a 32-band ERB log-filterbank
  cochleagram with per-utterance CMVN already reaches **0.718** cross-speaker on
  isolated digits — a much richer spectral sense than the LPC-formant trajectory
  that capped at ~0.50. Against that stronger crude sense, the SSL recovery still
  wins, but by less.
- So the precise reading: a fuller universe-recovery does recover *additional*
  speaker-invariant structure (the wall is partly the sense), but on isolated
  digits a well-built cochleagram already carries most of the recoverable
  invariance. The SSL edge would likely widen on harder material (continuous
  speech, larger vocabularies, noisier speakers) where the crude sense
  under-determines more.

## Donkey audit

- **Net touches the FEATURE READ ONLY.** wav2vec2 appears solely as a fixed
  forward pass producing a per-frame feature matrix. There is no net, no fit, no
  gradient anywhere in the recognition decision.
- **Cognition = the agent's owned ops.** 1-NN over DTW trajectory distance,
  byte-identical for both senses (the only thing that changes is the acoustic
  sense fed in).
- **LOSO ungameable.** The bank is built from train speakers only; held-out
  speakers' clips are never banked.
- **CortexLoop untouched.** This is a world-adapter sense-swap experiment; no
  agent loop, rule engine, or graph state is modified.

Reproduce: `python -m scripts.universe_recovery_frontend 40 25 3 2 7`
(args: n_train_spk n_held_spk n_bank_per n_test_per ssl_layer). Log captured to
`/tmp/universe_recovery.log`, end marker
`[MARKER] UNIVERSE_RECOVERY_FRONTEND_COMPLETED`.
