# Goal-Directed Generation — Rung 2: Compose Content × Voice × Complexity (block 342000)

## The defect this rung fixes

Rung 1 proved a goal can steer the synthesis, but it did so by cranking a single
`goal_weight` (4.0) until the goal term DOMINATED the ranking. That picked WHAT to say
but OVERRODE voice and complexity rather than composing with them — the +1.000 came from
brute goal-dominance, not from a principled choice of *how* to say it. Rung 2 makes
content, voice, and complexity **compose**.

## The design: two orthogonal slots on the communicative goal

Following the steer that a self-target utterance may still be aimed at a (chosen) audience,
the goal now carries two INDEPENDENT slots:

- **TARGET** (`target_kind` + `for_target`/`for_audience`) — WHERE satisfaction is measured
  (the furtherance check). Set in rung 1.
- **AUDIENCE** (`audience` + `for_audience`, via `resolve_audience`) — WHO the utterance is
  SHAPED FOR (voice + complexity), orthogonal to the target.

`resolve_audience` is the reachable **selection seam**: unbound → the endogenous default,
SELF-as-own-audience (voice = the agent's own idiolect; complexity = its own grounding
depth); specified → shape for that audience; and a future agent-driven chooser plugs in at
this same seam. No register inventory or sampler was built (none exists yet) — the choice
point is left OPEN and reachable, not forced. A self-target goal can therefore be aimed at a
chosen audience (rehearse / say-it-as-if-to-X) while satisfaction stays endogenous.

## How the three signals compose (not stomp)

`utterance_shaping.shape_from_audience` turns the resolved audience + goal content into:
- **content** → the *must-say residual* = content the audience does not already hold
  (audience-relative complexity). For a self audience with empty known-set, residual = all
  content (say it fully at your own grain); for a novice who knows `dog`, `dog` is credited
  as known and drops out of the residual.
- **voice** → the register/idiolect words: the agent's own `WriterStyle` recurring surface
  for a self audience; the specified audience's register otherwise. Voice carries framing,
  never content (content-overlap is dropped).

These ride **different channels** in `predict_next_words`: content via `goal_content`
(weight 2.0, down from rung-1's stomping 4.0), voice via the `register` channel
(`voice_weight` 1.5). Because they are separate terms in the held `Plus` ranking, they
**add** rather than one overriding the other. Utterance LENGTH accommodates the residual
content plus voice headroom, so voice shapes the utterance without crowding content out
(composition, not competition — see the honest interim failure below).

## Result (measured, pure graph)

Three goals, each run with a SELF audience (default) and a SPECIFIED novice audience:

| claim | result |
|---|---|
| C1 composition holds (content recovered) | self **3/3**, spec **3/3** satisfied (cov 1.00) |
| C2 voice/complexity audience-driven (surface differs by audience) | **3/3** goals |
| C3 choice reachable (specified audience changes voice+complexity, content intact) | ✓ |

Example (`poodle,dog,animal`):
- SELF audience → `"the and animal dog poodle a"` (own idiolect framing + full content).
- NOVICE audience (knows `dog`) → `"animal poodle plainly simply"` (specified register
  `plainly/simply`; `dog` credited-known and dropped from the residual).

Same content goal, different voice and complexity, driven purely by the audience slot —
and content recovered in both. This is the rung-1 defect fixed: goal picks *what*, audience
picks *voice* and *complexity*, all three compose.

## Honest interim failure (kept, because it is the finding)

The first run FAILED C1 for the self audience (cov 0.67): with 7 idiolect voice words
competing for a fixed top-k=4 against 3 content words, voice CROWDED OUT one content word.
That is a real phenomenon (verbose register displacing content in a scarce-length
utterance), but it means voice and content were *competing for slots*, not composing. The
fix was to set utterance LENGTH = residual + voice headroom so content is never crowded out
— composition, not competition. The alternative (lower voice_weight until content always
wins) was rejected: it would reduce voice to decoration and reintroduce goal-stomping.

## Scope (what rung 2 is and isn't)

- IS: content × voice × complexity composing over a target-independent, choosable audience
  slot, with the self-audience endogenous default and the choice point reachable.
- ISN'T (deferred): the full autoregressive self-conditioned rollout (rung 1.5 — this still
  uses top-k content selection over the composed ranking); the ASK/curiosity loop closure
  (rung 3). Parse-back ran in recognizer mode (no trained LanguageWorld here).

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python only).
- Protected READ-ONLY files untouched.
- `conceptualizer` no-Python-decision audit stays green (audience binding is data-driven:
  a binder table + conditional-expression edge writes, no decision `if`/`elif`).
- No model/venv/`/applications` involved (pure graph).
- Committed block-342 only, add-by-name.

## Artifacts

- `domains/conceptualizer.py` — `mint_communicative_goal` gains the orthogonal `audience`
  slot; `resolve_audience` (the selection seam) + `_bind_audience_slot` (idempotent,
  data-driven).
- `domains/utterance_shaping.py` — voice + complexity signals from the resolved audience.
- `domains/predictive_reading.py` — `predict_next_words` gains `voice_words` (register
  channel) and a rebalanced `goal_weight` so content/voice compose.
- `scripts/gen_rung2_compose.py` — the experiment (self + specified audience, C1/C2/C3).
