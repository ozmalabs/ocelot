# Goal-Directed Generation — Rung 1.5: The Autoregressive Self-Conditioned Rollout (block 343000)

## What this rung builds

Rungs 1–2 took a top-k SELECTION over ONE prediction — a bag of the highest-ranked words,
no feedback. Rung 1.5 makes it a true rollout, the analysis-by-synthesis predictor run
FORWARD: emit a word, FEED IT BACK into the context + register, RE-PREDICT with the
extended context, repeat — the reader's own next-word synthesis, now with its own output
as the observation (self-conditioned), unclamped by any external surface (no `abs_compare`,
no `_words(target)`). Goal + audience conditioning (rung 2) carry through every step, so
content × voice × complexity compose per emitted word. `rollout_unclamped` in
`predictive_reading.py` is the loop; it terminates on a stop condition and records per-step
source provenance so degeneracy is measured, not hidden.

## Result (measured, pure graph)

Three goals, self audience, rolled autoregressively and compared to the rung-2 selection:

| claim | result |
|---|---|
| C1 feedback preserves furtherance (content recovered) | rollout **3/3** (selection 3/3 contrast) |
| C2 terminates cleanly (`stop=goal_covered`, no runaway/stall) | **3/3**, mean repeat_rate **0.000** |
| C3 ordered + provenanced stream | ✓ per-step source recorded |

The per-step provenance shows meaningful ordering — e.g. `poodle,dog,animal`:
`the`(class_prior) `and`(class_prior) `animal`(goal) `dog`(goal) `poodle`(goal) `a`(voice)
`indeed`(voice). Framing → content → voice tail, terminating once the goal is covered. The
loop is self-conditioned (each word extends the context the next is predicted from),
goal-steered, and terminating, with content recovered by the parse-back.

## Honest finding: the loop is correct, but feedback did not yet BEAT selection

The rollout surface was essentially the SAME as the rung-2 top-k selection
(`the and animal dog poodle a indeed` vs `the and animal dog poodle a`). So:

- What is PROVEN: the self-conditioned autoregressive loop exists, is unclamped, carries the
  goal/audience conditioning per step, terminates without degenerate repetition, and emits
  an ordered, source-provenanced token stream that still recovers the goal content.
- What is NOT yet demonstrated: that feeding a word back produces *better* or meaningfully
  *different* output than one-shot selection. At this scale the ranking is dominated by the
  composed goal/voice/register terms, and appending one emitted word barely shifts the next
  prediction when the goal set is small and fixed. The *value* of feedback (as opposed to
  its mere correctness) would surface with (a) longer content where later words genuinely
  depend on earlier ones, (b) grammatical structure driving next-word dependence, or (c)
  more prediction mass on the grounded sign-grammar production path — which is exactly
  rung 2's deferred "shift the mass" question.

This is reported as a partial result, not oversold: rung 1.5 delivers the *mechanism*
(self-conditioned rollout) and proves it is well-behaved, but the payoff of feedback over
selection is future work, gated on the grounded-grammar mass shift.

## Degeneracy handling (measured, not hidden)

`rollout_unclamped` guards against the two feedback failure modes and surfaces them:
- runaway → `max_steps` cap;
- repetition → `no_immediate_repeat` skips already-emitted candidates; a stall then stops
  with `stop_reason='exhausted'` (visible) rather than looping; `repeat_rate` is reported;
- non-termination → `stop_on_goal_cover` ends the stream once all goal content is out plus a
  small voice tail (`voice_headroom`), leaving `goal_uncovered` visible if content couldn't
  be emitted.
All three runs stopped on `goal_covered` with repeat_rate 0.0 — clean termination.

## Scope

- IS: the standalone unclamped self-conditioned autoregressive rollout, goal + audience
  conditioned, terminating, provenanced; content recovery preserved under feedback.
- ISN'T (deferred): demonstrating feedback's advantage over selection (needs longer/
  structured content or the grounded-grammar mass shift); grammatical coherence (bounded by
  the register model); the ASK/curiosity loop closure (rung 3). Parse-back ran in recognizer
  mode (no trained LanguageWorld here).

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched.
- `conceptualizer` no-Python-decision audit unaffected (no conceptualizer change this block).
- No model/venv/`/applications` involved (pure graph).
- Committed block-343 only, add-by-name.

## Artifacts

- `domains/predictive_reading.py` — `rollout_unclamped` (the self-conditioned loop +
  stop/degeneracy handling + per-step provenance).
- `scripts/gen_rung15_rollout.py` — the experiment (rollout vs selection, C1/C2/C3).
