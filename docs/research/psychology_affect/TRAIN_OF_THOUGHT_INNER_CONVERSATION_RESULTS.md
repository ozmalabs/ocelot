# The Train of Thought — an Unspoken Conversation With Yourself (block 346000)

## The reframe (the key insight)

A train of thought is not "run the retrieval loop N times." It is the goal-directed,
audience-targeted, self-monitored utterance machinery of rungs 341–345 turned INWARD —
**an unspoken conversation with yourself** (Vygotsky's inner speech: private speech
internalized into a condensed, self-directed cognitive tool). Concretely:

- target = self, audience = self, articulation **COVERT** — the clause is realized and
  HEARD (parsed back) but never emitted as overt speech;
- a TURN = SPEAKER-SELF says a covert clause about the current topic + LISTENER-SELF
  hears it (the parse-back) and registers the RESIDUAL (what failed to recover);
- the CONVERSATION = turns chained, speaker/listener-self alternating, each turn
  conditioned on the prior self-utterance and its residual;
- what drives the NEXT turn is a **pluggable stance** over `(wa, turn, seen)`. The core
  stance is `residual` (pursue what didn't land + the transitively-implied ancestors);
  richer stances (question / disagree / elaborate) plug into the same seam later.

The deeper faculties are what SPEAKER-SELF reaches for when a plain self-restatement
leaves residual — not bolt-ons, but the conversation reaching for more when saying-it-
plainly-to-itself fails. Here the always-available one is transitive reasoning (the is-a
cone); order-N and dimension-minting are honestly deferred (below).

## What was built (additive)

`domains/train_of_thought.py` (composes `self_dialogue` + `grounded_representation`;
`self_dialogue.py` untouched as the block-345 base case):
- `inner_turn` — one covert self-utterance (via `self_dialogue.self_answer`; surface
  `covert=True`, heard via parse-back, never routed to an overt sink) + the residual.
- `transitive_ancestors` — `grounded_representation.cone` over `causal_influence` minus
  the topic and its direct objects: the transitive is-a ancestry the train can DERIVE
  (inference), teacher-free on the plain is-a seed — the always-available reasoning floor.
- `residual_stance` (default) + a `_STANCES` registry — the pluggable `(wa, turn, seen)
  -> list[topic]` interface.
- `run_inner_conversation(wa, *, topic, max_turns, stance, stance_fn, on_unknown,
  ask_fn, enqueue)` — the agenda-driven chain; stops `converged` / `max_turns` /
  `no_topic`; reports `frontier_growth` and `teacher_called`.

## Result (measured, pure graph, teacher-free, no LLM)

Pre-seed: an is-a DAG `poodle→dog→mammal→animal→organism` (+ a `sparrow→bird→animal`
branch) and a filed knowledge `SelfConcern{content:'poodle'}`. A teacher-call SPY counts
external-answerer invocations.

The inner conversation (covert — heard, never spoken):
```
turn 1 [poodle]:  "The poodle is the dog."      (covert, answered, residual [])
turn 2 [mammal]:  "The mammal is the animal."   (covert, answered, residual [])
turn 3 [animal]:  "The animal is the organism." (covert, answered, residual [])
turn 4 [organism]: ""  (covert, answered=False, residual ['organism'])
topics_thought = [poodle, mammal, animal, organism]   frontier_growth = [3,2,1,0]
```

| claim | result |
|---|---|
| C1 sustained self-dialogue (>1 covert turn, each conditioned on the prior) | **PASS** (4 turns) |
| C2 residual drives the next turn (train MOVES via transitive ancestors) | **PASS** |
| C3 cone escalation teacher-free (mammal/animal reasoned beyond the direct edge, spy 0) | **PASS** |
| C4 frontier evolution + honest stall (agenda 3→2→1→0 converged; no fabricated top) | **PASS** |
| C5 pluggable stance (a custom `first-step` stance drove the SAME loop, different train shape, teacher-free) | **PASS** |
| C6 external-ask floor choosable (`return` → spy 0; `ask` → spy 1, firing ONLY at the unknown top) | **PASS** |

The transitive cone is what makes this reasoning rather than recitation: turn 1 sees
`mammal/animal/organism` beyond the direct `dog`, and the train walks the hierarchy it
DERIVED. It converges honestly at `organism` (top of what's held) — no invented parent.
The custom stance produced `[poodle, dog, mammal, animal, organism]` (it kept the direct
step the default skips), proving the stance seam is real.

## Honest record: the harness was wrong first, not the mechanism

The first run "failed" C3/C5 with `ask_spy=1`. That was the TEST harness invoking
`on_unknown='ask'` (so the honest floor correctly fired at the unknown top `organism`)
while the assertions demanded spy=0. The fix was to the HARNESS: run the teacher-free
demonstration with `on_unknown='return'` (the train converges over held knowledge without
reaching out), and add C6 as a separate check that `on_unknown='ask'` invokes the floor
exactly at the unknown top. The mechanism was correct throughout; the assertions were
corrected to match the honest behavior, not the reverse.

## Deferred (honest, not faked)

- **Order-N** (`order_n_postulates.synthesize_gaps`) and **DIMENSION MINTING**
  (`context_model._mint_dim` / `cross_text_prior` StyleDimension / the collapse-residual
  loop) are NOT exercised here. They require richer held structure than a plain is-a seed:
  order-N needs concepts carrying structural-property `definition`/`why` prose; minting
  needs `seeds/qualia_space.json` + typed dimensional edges + the collapse/feature-stream
  loop. Left as opt-in hooks, deferred to their own properly-seeded block rather than
  faked on this seed. Dimension-minting is reframed (per the steer) as the inner
  conversation encountering a thought it has no axis for and coining one — an intrinsic
  driver, to be built where the substrate genuinely supports it.
- Richer stances (question / disagree / elaborate) plug into the demonstrated seam.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched; `conceptualizer.py` untouched (audit unaffected);
  `self_dialogue.py` (block 345) untouched.
- Teacher-free at loop time (no LLM); no model/venv/`/applications`.
- Committed block-346 only, add-by-name.

## Artifacts

- `domains/train_of_thought.py` — the inner conversation.
- `scripts/gen_rung3_train_of_thought.py` — the experiment (C1–C6, teacher-call spy).
