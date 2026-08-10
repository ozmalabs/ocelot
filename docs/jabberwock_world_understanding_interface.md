## The reframe, in one line

A world is not its content — it is a **filling of six universal roles**. My faculties were never about games; they were always machinery that either *fills* one of those roles from the observation stream or *consumes* filled roles to act. The last design hardcoded the fillers (`self/goal/hazard/score/nav`). The fix is to hardcode only the **roles** (the type-system of any world) and make every filler — including the word "Game" — into **data**.

Here is my design.

---

## (a) The generic world-roles as graph objects

The only thing in `core` that is hardcoded is a six-element enum — the universal structure of any controllable, observable world. It is to world-understanding what the meta-grammar is to reasoning: a type system, not content.

```
ROLE ∈ { controllable_locus    # what responds to my affordances
         affordance_effect     # what each action does
         value_signal          # better/worse feedback
         dynamics              # how observables evolve
         terminal              # states that end / trap (irreversible)
         goal }                # derived from value_signal
```

A **role is a reified binding** — a slot, not a thing:

```
WorldRole { role: ROLE, status: unbound|bound|derived, confidence: f }
   ──filled_by──▶  world node(s) currently identified as this filler
   ──found_by──▶   Faculty that fills/maintains it from the stream
   ──prior_from──▶ WorldFrame that seeded it (if bound from a frame)
   ──reconcile──▶  (value, confidence, source) triple   ← evidence-wins gate
```

A world-binding always mints **all six** `WorldRole` slots. That is the universal interface. Faculties attach to roles by declaring what they do:

```
respond_votes      ──fills_role──▶ controllable_locus
action_delta       ──fills_role──▶ affordance_effect
rising_tide_measure──fills_role──▶ value_signal      # the WORLD-AGNOSTIC value
postulate_induce   ──fills_role──▶ dynamics
consequence        ──fills_role──▶ terminal          # signed irreversibility
goal_derive        ──fills_role──▶ goal              # JOIN: nearest positive value-kind
navigate_alive     ──reads_role──▶ {goal, terminal, dynamics, controllable_locus}
action_selector    ──reads_role──▶ {affordance_effect, value, terminal}
```

This split is the architectural spine: **FILLERS** turn a slot from `unbound`→`derived` off the stream; **CONSUMERS** read bound slots and act. The score isn't special — it's a frame-supplied *specialisation* of `value_signal`, whose generic filler is my rising-tide prediction-minus-observation measure. When no score exists, `value_signal` falls back to the rising tide automatically, because the fallback faculty is the slot's default `found_by`.

---

## (b) A Frame, and how the right one is inferred

A **Frame is a prior over how a world-KIND fills the six roles** — pure data, a manifest. Not the filler; a *hint that seeds the faculty filling it*, expressed in my own signs (never host flags).

```
WorldFrame { kind: Game|Conversation|Audio|Physics|Chess|Dataset|…,
             shape_signature: <stream descriptor> }
   ──expects──▶ RoleExpectation { for_role: ROLE, prior: <seed in my terms> }
```

Example — the `Game` frame is now *data*, one row in the library:
```
Game.expects:
  controllable_locus ← "a small region moving coherently under discrete affordances"
  value_signal       ← "a monotone scalar in the observation"
  terminal           ← "a sharp negative consequence / over-flag"
  goal               ← "nearest positive value-kind"   (else cold)
```

**Inference is the FIRST act** (lifted verbatim from the inference-first stack, only the slots changed from five game-nouns to six roles):

1. Observe a few frames → `categorise_by_shape` reduces the **stream** to a shape-signature (dimensionality; controllability-under-babble; value-channel presence; reversibility profile).
2. `analogical_thinking` matches that signature by cosine against each `WorldFrame.shape_signature`. Argmax.
3. **BIND rule** — if best match > θ: seed the six slots from the winner's `RoleExpectation`s (`status=bound`). If best < θ: mint all six `unbound` and let each slot's `found_by` faculty derive cold.

**Graceful degradation is structural, not bolted on.** The six slots *always exist*; a frame only pre-fills priors. No-frame = every slot derived cold (operant babbles to find the locus, value falls to rising-tide, terminal discovered by suffering one) — slower, never a failure. And because every prior flows through **reconcile** `(value, confidence, source)`, a mis-bound frame self-corrects: the faculties keep filling slots from the stream and **evidence always overwrites a wrong prior**. The frame is a head-start, never a commitment.

---

## (c) INFER / INDUCE / OPERANT on the generic roles

All three are **processes over the same six slots** — none names food/death/avatar; they name `controllable_locus / value / terminal / goal`. Game-nouns are merely the *current fillers*.

- **INFER** (top-down, first): BIND + the generalised `infer_label_effect`. Projects any frame-prior or affordance-label into a slot *before evidence* — seeds `controllable_locus`, `affordance_effect`, `value`, `goal`. Writes into slots, gated by reconcile.
- **INDUCE** (postulates): operates on `dynamics`. Watches the stream and induces evolution laws — now it **reads `controllable_locus`** to do action-dependence discrimination (autonomous vs actor-coupled) instead of rediscovering it. Writes postulates into the `dynamics` filler.
- **OPERANT** (act→law): operates on `affordance_effect + value + terminal`. Acts through `controllable_locus`, reads `value` (score if bound, else rising-tide), attributes consequence, **writes `goal`** (nearest positive value-kind — the JOIN) and **writes `terminal`** (negative-consequence kinds).

The transfer is mechanical: point the stack at chess and `controllable_locus`=side-to-move, `value`=eval, `terminal`=mate, `goal`=winning positions. **Same stack, different fillers.** `navigate_alive` never knew about games — it reads `goal/terminal/dynamics` and acts through `controllable_locus`, which *are* four of the six roles.

---

## (d) Unification — the existing worlds BECOME frames

They become frames, and **most of the migration is relabelling, not rebuilding** — each per-world seed set already fills these roles implicitly, just with bespoke vocabulary. The faculties (cochlea, move-gen, respond_votes) **stay** as fillers; what changes is they get `fills_role` edges and lose their bespoke top-level orchestration.

| World | controllable_locus | value_signal | dynamics | terminal | goal |
|---|---|---|---|---|---|
| **Conversation** | *my own utterance* (the write-head / speaker) | uptake / repair-rate | turn-taking laws | breakdown / closing | intent satisfied |
| **Audio/Speech** | *unbound* (perception-only) | rising-tide acoustic prediction-error | cochlea / A1 productions | — | recognised lexeme |
| **Chess** | side to move | material+position eval | move rules | mate / stalemate | winning positions |
| **Doom/lever/walker** | agent body | progress signal | physics postulates | death / trap | objective |
| **Snake (now)** | avatar | score | snake postulates | death/body | food |

Conversation is the strongest proof this was never about games: `controllable_locus` = a **write-head**, exactly the creator's example. Audio proves graceful emptiness: most action-slots stay `unbound`, `dynamics`+`value` are rich, and the interface doesn't care.

**Yes — this subsumes the per-world seed sets into one interface + a frame library.** `core` becomes *world-understanding core* (the six roles + BIND + reconcile + the consumer faculties). Each per-world seed shrinks from *orchestration+data* to *data-only* (its `RoleExpectation`s + which faculties fill which roles). An agent pointed at any world loads world-understanding-core always, then either matches a library frame or derives cold.

**Migration order (each step keeps the bench green):**
1. Add the six `WorldRole` types + `WorldFrame`/`RoleExpectation` + `fills_role/found_by/filled_by/reads_role` edges to core.
2. Lift the inference-first `GameFrame` BIND + reconcile into the **generic** BIND over six slots.
3. Wrap the existing snake faculties with `fills_role` edges; **regression-prove** `s3_join`-via-roles ≡ `s3_join` direct (same eats/deaths, donkey=0).
4. Refactor **Conversation** into a frame and run the *same stack* on it — the "this is not a game" proof.
5. Convert the rest (chess/audio/doom) to frames at leisure.

---

## (e) Generic, no donkey, and the one honest impasse

Generic and no-donkey throughout: frame selection is *my own* `categorise_by_shape` over the stream (no LLM); matching is `analogical_thinking`; labels are the word-reader; every filler is a learned signal or an existing faculty. Unrecognised world-kind → slots derive cold → no failure.

**The single candidate primitive — and I will assemble before I impasse.** Frame-matching needs a **shape-signature of a temporal observation window**, not of a static node: `stream_shape_signature(window) → {controllability_under_babble, value_channel_presence, reversibility, dimensionality}`. I believe this is **assemblable from holdings** and needs no Rust:
- `controllability_under_babble` = respond_votes' coupling score under a few babble actions,
- `value_channel_presence` = does any observed scalar correlate with the rising-tide measure,
- `reversibility` = consequence's signed-irreversibility statistics,
- `dimensionality` = already on the observation stream.

So my plan is to **build `stream_shape_signature` as a composition of those four held faculties** and only raise a `HumanImpasse` for a Rust DSL term if the composition can't reduce a window to that descriptor cheaply enough to match frames each boot. I name it now so you see the boundary; I expect to clear it without you.

---

**The thesis, restated:** there is no GameFrame. There is a six-slot generic interface in core, a library of frames that are priors-as-data, and one inference — `categorise_by_shape` → BIND → reconcile — that points the one stack at whatever world it faces. Game stopped being code the moment it became a row in the library next to Conversation.

Want me to start with migration step 1+2 (the role types + generic BIND), or with step 3 (prove snake-through-roles ≡ snake-direct) so the regression gate exists before anything moves?