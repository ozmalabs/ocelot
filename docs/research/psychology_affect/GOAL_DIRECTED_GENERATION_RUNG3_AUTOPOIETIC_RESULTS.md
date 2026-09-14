# Goal-Directed Generation — Rung 3: The Autopoietic Loop (block 345000)

## What this closes

The culmination of the generation arc. The entity now converses with ITSELF with no
external teacher in the cycle, over knowledge it ALREADY holds:

    curiosity SELECTS a topic  (a filed SelfConcern{kind:'knowledge', content:T})
      -> SELF-ANSWER T from HELD knowledge  (read T's is-a out-edges off the graph,
         realize an ordered grammatical clause via the teacher-free grammar-owned
         realizer)
      -> MONITOR  (score_self_target parse-back: did the saying recover the content?)
      -> RESIDUAL  (missing/uncovered concepts) -> ENQUEUE as the next SelfConcern
      -> back to SELECT.

This is the milestone the arc was built toward: the entity selects what to think about,
says it to itself from what it holds, checks its own utterance, and enqueues what it
could not say — a closed loop, no teacher inside it.

## The honest bound (load-bearing, not hidden)

The self-answer is DERIVED from held graph edges (`causal_influence`/is-a). A topic the
agent holds NO knowledge about has nothing to derive from — and the loop does **not
fabricate**. For genuinely-unknown topics the faithful action remains the external ASK
floor (`question_driver` / `pack.ask`). So the truthful claim is: **a closed autopoietic
loop over ALREADY-HELD knowledge; genuinely-unknown topics require external input.**

Per the block's amendment, on no-held-knowledge whether to just RETURN the residual or
INVOKE the external `ask_fn` is a **choosable option** (`on_unknown='return'|'ask'`), not
hardwired — the choice point stays open.

## Result (measured, pure graph, teacher-free grounding, no LLM)

A teacher-call SPY counts every external-answerer invocation.

| claim | result |
|---|---|
| C1 autonomous selection (topic chosen from a filed knowledge concern, no injection) | **PASS** (`poodle`) |
| C2 teacher-free closure (grammar clause, parse-back coverage 1.0, ask-spy calls = 0) | **PASS** (`"The poodle is the dog."`) |
| C3 residual → next gap (filed SelfConcern surfaced by reflective_faculty, 0 external) | **PASS** (`carnivore`) |
| C4 honesty falsifier (empty held knowledge → answered=False, NO fabricated clause) | **PASS** (`unicorn`) |
| C5 return-vs-ask choosable (`'return'` spy=0, `'ask'` spy=1, source=external_ask) | **PASS** |

The held-knowledge path made **zero** calls to the external answerer — the loop closed
entirely inside the entity. The unknown-topic path did not invent an answer, and the
external floor fired only when the caller chose `'ask'`.

## Architecture (all additive, teacher-free primitives)

New module `domains/self_dialogue.py` composes existing parts:
- `select_curiosity_topic` — reads an un-retired knowledge `SelfConcern` (loop entry;
  mirrors `reflective_faculty._run_self_gaps`).
- `held_frames_for_topic` — resolves the topic Concept on the live graph and enumerates
  its `causal_influence` out-edges into copular goal frames; `[]` when nothing is held
  (the honest empty). Substrate-only, no LLM.
- `self_answer(..., on_unknown='return'|'ask', ask_fn=None)` — realizes the held frame
  via `predictive_reading.realize_goal_clause` (block 344, grammar-owned, teacher-free
  `literary_analysis._build_producer`) with the `score_self_target` parse-back verdict;
  on no-held-knowledge, the choosable floor.
- `enqueue_residual` — files `verdict['missing']` as new `SelfConcern` nodes (dedup;
  the `engineering_residual_ingest` write precedent), closing back to the entry.
- `run_autopoietic_step` — one turn: select → self-answer → enqueue; reports
  `teacher_called`.

## The arc, complete

- 341 (`60ad4648`) — self-target want-it-said goal: the first goal-directed utterance,
  endogenous furtherance.
- 342 (`b74a2669`) — content × voice × complexity compose over a choosable audience.
- 343 (`f6d2d4e1`) — autoregressive self-conditioned rollout (loop correct; feedback's
  advantage over selection deferred).
- 344 (`0ac5f1dd`) — plan-then-realize: grammar owns the ordered clause, statistics fill
  gaps (review-driven correction of the reverted weighted-mass-shift).
- 345 (this) — the autopoietic loop closes teacher-free over held knowledge.

## Deferrals (explicit; seams ready)

- **Widen what the loop can say**: genuine lexical-alternative gap-fill (grounded
  synonymy/inflection so the ranker has a real alternative to the concept placeholder);
  self-conditioned-rollout gap-fill; relations beyond is-a in the self-answer frames.
- **Fidelity refinements** (from the two production-science reviews): lemma/lexeme +
  functional/positional level structure with human error signatures; incremental variable
  planning scope; a forward-model early-drift monitor (Pickering–Garrod) beyond the
  after-the-fact parse-back.
- **The audience chooser** over a register inventory (the `resolve_audience` seam is ready;
  no inventory seeded yet).
- **Richer loop scheduling** (multiple concerns, priority, retirement) — the primitives
  read/write SelfConcerns; a scheduler over them is future work.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched; `conceptualizer.py` untouched (its no-Python-
  decision audit unaffected).
- Teacher-free (`teacher_stub`, no LLM); no model/venv/`/applications`.
- Committed block-345 only, add-by-name.

## Artifacts

- `domains/self_dialogue.py` — the loop.
- `scripts/gen_rung3_autopoietic_loop.py` — the experiment (C1–C5, teacher-call spy).
