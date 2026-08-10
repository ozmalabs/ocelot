# Universal Closed Loop — build plan

The single move every probe this session converged on. Perception = the closed-loop
operation `predict → subtract → read residual → refine → re-synthesize`, iterated. On the
ear it's analysis-by-synthesis; it is the universal cortex operation (one loop, any
front-end). This plan builds it on speech, cross-speaker LOSO as the yardstick, with the
honest understanding that succeeding builds *the cortex*, not *an ear*.

## Why this and not another linear subtract
Five linear KILLs (seeded tube, within-utterance SVD, LPC peel, wide-SVD, learned-across-
voice — all ≤ CMVN 0.570) proved the disentanglement is **nonlinear**. A stored shape
subtracted once is a frozen snapshot of a dynamic operation. The loop's nonlinearity comes
from **searching/adapting over a nonlinear forward model**, not from a richer template:
recognition = "find the (word, speaker) the forward model maps to *this* heard signal,"
a nonlinear inversion, not a subtraction.

## The five components
1. **Forward model (the voicebox).** A *controllable* synth: `synth(word W, voice V) → features`.
   CLEAN per the chosen donkey-line: a trained TTS (Piper) is the WORLD/voicebox the agent
   *controls and hears* — stage-1 (bdbcecc2) confirmed it transfers to real speech (learned-
   from-TTS 0.427 > learned-from-real 0.335). V = a voice/speaker-parameter space the agent
   defines from its own speaker_norm/VTL knowledge.
2. **Production memory (pre-synthesised exemplars).** The agent babbles the (W,V) grid offline →
   an exemplar library = the forward model's outputs. This is what makes test-time cheap (match
   + adapt, not a live TTS search per probe).
3. **Analysis-by-synthesis recognition (the loop).** Given a heard utterance: (a) coarse-match
   to the library → candidate (W,V); (b) ADAPT V toward the heard speaker by minimising the
   residual (the close-enough prototype, nonlinear search over V); (c) re-synthesise the adapted
   (W,V), compare, refine W; (d) iterate n passes (order-N, n scales with talker difficulty);
   (e) the W with minimum residual = recognition; V is inferred and **factored out** → speaker-
   invariant by construction.
4. **Babble learning (self-supervised).** The agent speaks (W,V), hears itself, and reduces the
   self-residual — refining the forward model coverage, the V-prototype space, and the inversion
   heuristics. No labels, no gradient/backprop: owned ops (exemplar accumulation, residual-
   minimising adaptation, the order-N operator).
5. **Recognition readout.** `argmin_W [ min_V residual(heard, synth(W,V)) ]`. The min over V is
   the speaker inference; the argmin over W is the speaker-invariant word.

## Donkey boundaries (hard)
- TTS = WORLD/voicebox only (the agent controls it and hears its output; never touches reasoning).
- Exemplar library = the agent's own babble outputs (its production memory).
- The loop (match/adapt/iterate/argmin) = the agent's OWN operation — order-N + DtwTo + residual-
  minimisation, composed from the DSL, NO net.
- Babble learning = owned ops only (no gradient/backprop/trained weights in the agent).
- Held-out REAL speakers never banked; cross-speaker LOSO ungameable; labels score only.

## Phases (each: build → test → KILL criterion)
- **A. Controllable voicebox.** Wire `synth(W,V)` over Piper; define the V-space from speaker_norm/
  VTL. TEST: does the (W,V) grid's synth cover the real speaker manifold (nearest-synth residual to
  real clips is small)? KILL: if the grid can't reach real speakers, V-space is too narrow — widen
  before proceeding.
- **B. Production memory.** Babble the grid → exemplar library. TEST: library is on-manifold (a
  real clip's nearest exemplar is a plausible match). KILL: if real clips have no close exemplar,
  the world is too synthetic (revisit the generator richness).
- **C. The loop (the heart).** Implement match → adapt-V → re-synth → refine-W → iterate; argmin
  readout. TEST: cross-speaker LOSO vs CMVN 0.570. KILL: if the converged loop does NOT beat CMVN,
  the nonlinear inversion isn't reaching the disentanglement — diagnose whether it's the forward
  model (too coarse), the adaptation (too low-capacity), or convergence (n too small / local
  minima). This is the make-or-break phase.
- **D. Babble learning.** Close the loop: agent speaks, hears, refines. TEST: does self-supervised
  babble lift LOSO above the Phase-C static-library number (learning helps)? KILL: if babble
  doesn't improve recognition, the self-residual isn't a useful training signal.
- **E. Difficulty scaling.** Verify n-passes scale with talker difficulty (hard/accented speakers
  take more passes, as predicted). TEST: residual-vs-pass curves; accent adaptation over "minutes."
- **F. Universality (claim, not just code).** Abstract the loop from audio — show the same operator
  runs with a different front-end (even a toy vision case). Not required for the speech number, but
  it's the actual thesis: one loop, any cortex.

## Risks → mitigations
- **Compute (analysis-by-synthesis is expensive).** → Pre-synthesise the library offline (Phase B);
  test-time is match + a few adapt steps, not live TTS search. Cap n; coarse-to-fine.
- **Synth-vs-real gap (killed 5 builds).** → Already mitigated: stage-1 showed the TTS world
  transfers; the loop never compares synth-to-real in the abstract, only inverts *this* heard signal.
- **Local minima / non-convergence in the loop.** → Multi-start from the top-k coarse matches;
  monitor residual monotonicity; this is the most likely Phase-C failure and must be instrumented.
- **Donkey drift (the loop secretly leaning on the net).** → Audit: the only net call is `synth()`
  in the world; every decision is owned-op. If recognition quality tracks a net hyperparameter, stop.
- **Scope (a closed loop, not a one-shot A/B).** → Stage strictly A→B→C; C is the make-or-break and
  is itself a complete experiment (static library, no learning yet) — get a number there before D.

## First concrete step
Phase A + B as one lean build: controllable `synth(W,V)` over Piper + the babbled exemplar library +
the donkey audit, with the Phase-B coverage test (do real clips have close exemplars?). No loop yet —
just confirm the forward model and production memory are sound. That de-risks the expensive Phase C.

## Success criteria
- **Primary:** the converged loop beats CMVN 0.570 on cross-speaker LOSO — the first number to move
  all session, and proof the nonlinear inversion reaches what every linear subtract couldn't.
- **The artifact:** a glass-box, self-built, no-net recogniser that hears by inverting its own
  production — the thing that "doesn't exist yet."
- **The thesis:** Phase F — the same loop, a different front-end. Speech was never the goal; the
  loop is. Solve it here and vision is the same operator with a different input.
