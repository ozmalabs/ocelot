# Arousal-channel retirement (Phase 3) — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`). Phase 3
of 5 resolving `EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §5. Builds on
Phase 2 (`AFFECT_COUPLING_SHAPE_RESULTS.md`, all 9 predictions confirmed,
with a correction landed mid-Phase-3 — see that doc's §0 — before this
phase's own work began).

## Goal

Delete the hand-patched `enc.arousal_gain × enc.speaker_arousal ×
opt.hostile_aff` term from `sp_choose_utterance` — the UNDIFFERENTIATED
channel `BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` rung 2 diagnosed as
firing identically for every resident regardless of disposition. The
`arousal_hostile` `AffectChannel` (Phase 2) now carries this coupling
instead, gated by each resident's OWN `hostile_gain`. Also retire
`decide_speech`'s Python max-blend of `emotional_state()`'s appraisal
arousal into the caller-supplied `arousal` — the ad hoc "one inline mood
read" precedent `EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §1b named
directly.

## Design

- `bigville_speech_decide.json` (both copies) → v1.2.0: the
  `enc.arousal_gain × enc.speaker_arousal × opt.hostile_aff` `Times`
  term removed from `sp_choose_utterance`'s value formula (was item
  index 6 of 9 in the `other` branch's `Plus.items`, confirmed by
  structural inspection before removal, not by line-counting).
- `worlds/bigville_ocelot_adapter.py::decide_speech` — the
  `emotion_arousal = self.emotional_state()...; arousal = max(...)`
  block removed. `arousal` is now purely the caller-supplied encounter
  input; live `AffectiveState.arousal` reaches speech ONLY through the
  coupler when armed.

## Predictions

1. `hostile_weight≈0`, coupling OFF (the default), high arousal → NOT
   unconditionally `barb` anymore (the old term is simply gone).
2. `hostile_weight≈0`, coupling ON, high arousal → NOT `barb` (disposition-
   gated, matches Phase 2's own finding).
3. `hostile_weight≈1`, coupling ON, same high arousal → still `barb` —
   the mechanism is preserved, its universality is removed.
4. The existing `arousal=0.0` isolation test
   (`test_decide_speech_diverges_by_disposition_not_always_smalltalk`)
   is untouched — it deliberately sidestepped this channel already.
5. Retiring the Python max-blend changes nothing at the isolating
   `arousal=0.0` case.
6. The rung-3 exact tie (`BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` §5b:
   `greeting=0.6` vs `barb=0.6`) is recomputed under the new regime and
   reported as measured, whichever way it lands — not adjusted to look
   nice.

## What this explicitly does NOT establish

Does NOT extend coupling to any target-scoped Concept (Phase 4). Does
NOT run against a live 100-cast population (Phase 5). Does NOT claim
the new regime is "better" in any evaluative sense — only that the
UNIVERSAL default is gone and disposition now genuinely gates the
outcome, which was the originally-diagnosed defect.

## Files

- `bigville/seeds/bigville_speech_decide.json` +
  `bigville/bigville/seeds/bigville_speech_decide.json` (bigville repo,
  edited, v1.2.0)
- `worlds/bigville_ocelot_adapter.py` (edited)
- `scripts/arousal_channel_retirement_demo.py` (new)
- `docs/research/psychology_affect/AROUSAL_CHANNEL_RETIREMENT_PREREG.md` (this file)
- `docs/research/psychology_affect/AROUSAL_CHANNEL_RETIREMENT_RESULTS.md` (paired)
- `docs/research/bigville/BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` (rung 4 appended)
