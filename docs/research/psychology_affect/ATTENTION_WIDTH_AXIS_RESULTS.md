# Attention-Width — the Goal↔Associative Axis + Honest Termination (block 347000)

## What this closes

Two fidelity fixes the consciousness / inner-speech literature review flagged for the
train of thought (block 346):

- **#1 Associative transitions blended with goal-directed.** Real trains of thought are
  not one regime: they blend deliberately-constrained goal-directed transitions with
  associative / spreading-activation flights (James's substantive vs transitive parts;
  Christoff et al.'s deliberate↔automatic continuum; Bar associative + Dolan/Dayan
  model-based). The block-346 train only did the goal-directed regime (residual + is-a
  ancestors).
- **#3 Honest termination.** A train that stops only when its agenda empties is a
  rumination engine (Nolen-Hoeksema: pathological non-termination = failed
  disengagement). The block-346 train only stopped on agenda-exhaustion / max_turns.

## The design: one adjustable attention-width axis (not two stances)

Per the user's reframe — "could it be both? an adjustable axis" — goal-directed and
associative are the two ENDS of a single continuous `attention_width ∈ [0,1]`, not two
stances to pick between:

- **width 0 — narrow / goal-directed:** residual + is-a ancestors only (byte-identical to
  the block-346 default `residual_stance`).
- **width mid (≥0.34):** add is-a children (hyponyms, `in_neighbours`) + siblings
  (co-children of a parent) — lateral/downward association.
- **width 1 — wide / associative:** add any-relation neighbours (spreading activation over
  `analogy_search._DEFAULT_REL_EDGES`) — James's transitive flights.

**Honest naming.** This is the graph-walk ANALOGUE of aperture, and a DISTINCT axis from
it. The substrate's `aperture` (`observer_aperture` resolves/grain) governs the RESOLUTION
of a readout over a signature FIELD; `attention_width` governs the BREADTH of the
neighbourhood a train admits over the concept GRAPH. Both are narrow↔wide dials, but they
live in different spaces — so this is named distinctly and does NOT touch `resolves`/`grain`.

**Termination as a dynamic on the axis, not a bolted-on rule.** `novelty_window`: the train
disengages when the last K turns recovered nothing NEW (`stop_reason='novelty_stalled'`) —
the train circling without learning lets go. `novelty_window=None` disables it (the
block-346 agenda-exhaustion behavior). This is a lightweight novelty proxy; the
`learning_progress_curiosity` smoothed-progress signal is the noted richer upgrade.

## Result (measured, pure graph, teacher-free)

Seed: an is-a DAG with siblings + two branches (`poodle/beagle→dog`, `cat→mammal`,
`sparrow→bird`, both → `animal`). A teacher-call spy counts external-answerer calls.

| claim | result |
|---|---|
| C1 width shapes the train (0 vs wide → distinct shapes on one seed) | **PASS** |
| C2 honest termination prevents rumination (stalls vs churns to agenda-empty) | **PASS** |
| C3 teacher-free at every width (ask-spy 0) | **PASS** |
| C4 backward-compat (width 0 == block-346 residual default, byte-identical) | **PASS** |

- width 0 → `poodle→mammal→animal` (tight is-a spine); width 0.5/1.0 →
  `poodle→mammal→animal→beagle→dog→cat→bird→sparrow` (wanders siblings, children, and
  cross-branch to the `bird` line). Distinct narrow-vs-wide shapes from one seed.
- C2: the churning train **stops `novelty_stalled` after 3 turns** (window on) vs runs to
  6 (agenda-exhaustion, window off) — disengagement for a real reason.
- block-346 experiment still passes 6/6 (backward-compat regression).

## Honest note

On this small seed, width 0.5 and 1.0 produced the SAME shape — mid-width already reaches
the whole connected neighbourhood, so full width adds nothing here. The axis is continuous
and correct; this particular graph is simply small enough that mid and wide converge. The
demonstrated contrast is narrow-vs-wide (two shapes), not three; on a larger graph with
longer relation chains they would differ. Not overclaimed.

## Where this is heading (the next block)

The user's escalation: the train becomes a FEEDBACK LOOP for the reasoning aperture — the
train's own novelty/residual feeds back to MOVE the width, and the loop's SET-POINT is
itself a shape at an adjustable aperture (vague grain ⇒ freeform thought, sharp grain ⇒
narrow focus). That is shape-matching control over the reasoning width, and it reuses the
substrate's real `observer_aperture` (shape + grain) as the set-point. It is a distinct,
larger block (verify → build → experiment → commit next), NOT retrofitted here. The
`novelty_stalled` termination in this block becomes the LIMITING CASE of that loop (even a
maximally-vague set-point yields no novelty → disengage).

## Deferred (unchanged)

- Feedback-loop / dynamic-set-point block (next).
- Global workspace (produce seriality via broadcast/competition) — after the loop.
- Gated dimension-minting (on accumulated persistent residual) — needs the qualia substrate.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched; `conceptualizer.py` + `self_dialogue.py` untouched.
- Teacher-free (no LLM); no model/venv/`/applications`.
- Committed block-347 only, add-by-name.

## Artifacts

- `domains/train_of_thought.py` — the `attention_width` axis (`breadth_stance`,
  `_children`/`_siblings`/`_relation_neighbours`, `goal_stance`/`associative_stance`) +
  novelty-stall termination in `run_inner_conversation` (additive; block-346 default
  preserved).
- `scripts/gen_rung3_attention_width.py` — the experiment (C1–C4, teacher-call spy).
