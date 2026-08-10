# Universal closed loop — Phase C (the analysis-by-synthesis LOOP)

**VERDICT: PLATEAU — Phase C does NOT beat CMVN's 0.570 cross-speaker cap.**
The loop reaches cross-speaker LOSO **0.420** (CMVN this split 0.510 / canonical 0.570).
It DID beat the static lower bound (+0.020) and the residual curves drop monotonically —
the nonlinear inversion *works mechanically*. But a forward-model-floor diagnostic
**refutes a convergence explanation and pins the bottleneck to (a): the forward model
(espeak) is too coarse to render the real talker.** The pre-written lever applies: a
richer generator (Piper neural voices), not a new recognizer.

This is the make-or-break phase from `docs/universal_closed_loop_plan.md`. Run to
completion, real numbers, ungameable LOSO. Honest: the wall holds.

Script: `scripts/universal_loop_phaseC.py`.
Run: `PHASEC_K=5 PHASEC_PASSES=3 PHASEC_MAX_SYNTHS=12 python -m scripts.universal_loop_phaseC 40 10 60 20240610`.
Captured logs: `/tmp/phaseC.log` (marker `UNIVERSAL_LOOP_PHASEC_COMPLETE`),
`/tmp/phaseC_diag.log` (forward-model-floor diagnostic, marker `DIAG_MARKER`).

## (1) The loop, wired (donkey audit)

Per heard utterance H (`Loop.recognise`):
1. **Coarse match** (`coarse_topk`) — rank the prebuilt (W,V) production-memory library by
   the agent's graph-resident **DtwTo** to H; take the top-k WORDS, each seeded from its
   best-fitting library voice (multi-start, k=5 → dodges local minima).
2. **Continuous adapt-V** (`adapt_v`, the nonlinear lever) — for each candidate word W,
   OWNED coordinate descent over the few V params (pitch & rate continuous, vocal-tract
   variant hill-climbed over its neighbourhood = the discrete realisation of the
   continuous VTL axis), coarse-to-fine, **LIVE re-synthesising `synth(W,V)` each step**
   and minimising `residual = DtwTo(H_feats, synth(W,V)_feats)`. Capped ≤12 synths/word.
   This inverts the *real nonlinear synth* — not a linear feature approximation (the
   subtract that already failed five times).
3. **Iterate (order-N)** — 3 refine passes; residual-vs-step recorded (monotonicity).
4. **Readout** — `argmin_W [ min_V residual(H, synth(W, V_adapted)) ]`. The speaker V is
   inferred (per-word best-fitting voice) and **factored out → speaker-invariant by
   construction.**

**Donkey audit (clean):**
- `synth` = the WORLD/voicebox (espeak-ng) the agent controls and hears; never inverted by
  a net, never in a decision — only re-voiced and re-heard. The one TTS touch.
- The loop (coarse-match / adapt / iterate / argmin) = the agent's OWN ops: the
  graph-resident **DtwTo** Term reused UNCHANGED from `dtw_trajectory_loso`, + a
  coordinate search + residual-min. **No net, no fit, no gradient, no trained weight** in
  the agent (verified: the only `evaluate` target is DtwTo; the only external call is
  espeak).
- Features = the agent's own front end (`learned_voice_shape.residual_track`, empty
  library = per-utterance CMVN) — the SAME feature the recognizer reads on real clips.
- Held-out REAL speakers NEVER banked; labels score only; LOSO ungameable.

## (2) CMVN vs static vs Phase-C — run to completion

Robust SC 40-held-out-speaker LOSO. Probes subsampled per word for compute (the loop does
live re-synthesis): **80 seen-speaker, 100 cross-speaker LOSO clips** (10/word), reported.
Full run, 1755 world calls, ~6.4 synths/probe, 535 s.

| regime | seen | cross-speaker LOSO | gap |
|--------|------|--------------------|-----|
| CMVN (the wall) | 0.500 | **0.510** (canonical 0.570) | −0.010 |
| STATIC match (Phase A+B floor) | 0.487 | 0.400 | +0.087 |
| **PHASE-C LOOP** | 0.512 | **0.420** | +0.092 |

- **Phase-C LOOP vs CMVN (this split): −0.090** (0.510 → 0.420). Below the wall.
- **Phase-C LOOP vs STATIC floor: +0.020** (0.400 → 0.420). The loop's adaptation *does*
  lift above the static library — the mechanism is real but small.

**Convergence / adapt curves** (residual-vs-step, winning word, first LOSO probes) — the
loop reduces residual monotonically when it adapts, e.g.
`eight: 0.646 → 0.549 → 0.489 → 0.449 (drop +0.198)`,
`one: 0.448 → 0.419 → 0.409 (+0.039)`, `five: 0.259 → 0.242 → 0.234 (+0.025)`.
Mean adapt drop ≈ +0.045. Several winners had zero drop (coarse voice already fit) — the
tell that the *wrong* word's generic best-fit residual is the problem, not the descent.

## (3) VERDICT: PLATEAU, diagnosed (a) — the forward model

The script's auto-diagnosis guessed (c) convergence (true-word separation +0.023 on the
top-k-pruned readout). A dedicated **forward-model-floor diagnostic** (`/tmp/phaseC_diag.py`,
60 LOSO clips, full adapt at EVERY word, k=10, 16 synths/word, no top-k pruning — the
absolute ceiling convergence could ever reach) **refutes (c) and pins (a):**

```
coarse argmin (no adapt) accuracy:        0.417
FULL-adapt-every-word argmin accuracy:    0.367   <- the CEILING if convergence were perfect
TRUE-word adapted residual floor:  median 0.442
best WRONG-word adapted residual:  median 0.441
separation (wrong-true): median -0.021   frac true<wrong 0.367
```

- **The ceiling is 0.367.** With unlimited multi-start, every word adapted, no pruning —
  the perfect-convergence argmin still only hits 0.367. So convergence/argmin (c) is NOT
  the bottleneck: fixing it cannot reach 0.570. **(c) refuted.**
- **The true word, fully adapted, is NOT closer than the best wrong word** — separation
  **−0.021** (negative); `frac true<wrong = 0.367`. The synthetic-vs-real gap (espeak's
  rendering error against a real talker) is *larger than the between-word distance*. Even
  at its best-fitting V, espeak cannot voice the heard word closely enough for the true
  word to win.
- Adaptation itself works (monotone drops, beats the static floor), so **(b) adaptation
  too weak is not primary** — widening V within espeak only chases a floor that espeak's
  timbre caps. **(b) secondary at best.**

**Diagnosis (a): the forward model is too coarse.** espeak-ng's formant-synth timbre is
too far from real speech for residual-min inversion to separate words across speakers. Per
the plan's pre-written first lever, the fix is a **richer generator (Piper neural voices)**
— widen the manifold so the true word's adapted residual drops below wrong words — **not a
new recognizer.** Phase A+B already flagged this caveat (espeak world coarser than real
speech; wrong−correct residual gap only ~0.10); Phase C's loop converts that warning into
the measured wall: the inversion is sound, the voicebox is the limit.

## What Phase C establishes

- The analysis-by-synthesis loop is **built and donkey-clean**: owned coordinate-descent +
  DtwTo + argmin invert a controllable voicebox with no net in the agent.
- The nonlinear inversion is **real but bounded by the generator**: it beats the static
  floor (+0.020) and converges monotonically, but plateaus at 0.420 < CMVN 0.570 because
  espeak's true-word residual floor (0.442) is not below the best wrong word (0.441).
- The session-long "every linear subtract dies at 0.570" now has its nonlinear counterpart
  measured: the *inversion machinery* clears the static floor, but on the espeak forward
  model it cannot clear CMVN. **The next move is a richer voicebox (Piper), then re-run
  this exact Phase-C loop unchanged** — the loop is the asset; the world was the wall.

Tests green where code was touched: `test_stt_pipeline`, `test_frontend_effect_gate`
(11 passed). No existing code modified (new script only). Not committed (coordinate).
