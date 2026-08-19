# The future dispatcher — routing solve-shaped goals through question_driver — PREREG

Base `main @ 1480d48` ("Merge problem-decomposition: race coupling-graph
guesses, decompose-or-refuse, GO"), verified via `git log --oneline -1 main`
before writing this document. This is a **PREREG-ONLY task**: investigation
+ design, no implementation, no seed JSON, no tests, no worktree/branch. Per
the task's own instruction, this document is the checkpoint the user
reviews before anything below it gets built.

Today's session landed a seven-item reasoning/solving toolbox on `main`
(deduction: `domains/propositional_deduction.py` +
`domains/inference_generation.py`; CAN solving:
`domains/can_native_orchestration.py`, `domains/can_junction_tree.py`,
`domains/can_native_bp.py`; bridging:
`seeds/entity_concept_correspondence.json` +
`domains/reasoning_can_bridge.py`; analogical promotion:
`seeds/directional_correspondence.json` + `domains/analogical_thinking.py`;
decomposition: `domains/problem_decomposition.py`). The user's framing,
verbatim: *"The future dispatcher is the master cognitive process —
choosing what to think about."* and *"there is no view from nowhere...
eliminate search space + cheap is the move... basically 80/20,
iteratively."* This document investigates whether that dispatcher already
exists in some form, grounds a design in the real current code (not the
conversation's design language taken on faith), and sizes what is
realistically buildable next.

**Headline finding, stated up front because it reshapes every answer
below:** the project already has exactly the DISPATCH mechanism the user is
asking for — `qd_bind_resolver` (`seeds/question_driving.json`), a
kind-string JOIN between `Goal` and `Resolver` nodes sharing an `Agent` hub
— and it is **already generic over kind**, not specific to conversational
question-answering. Adding new solving facilities as new dispatch targets
requires **zero new rules** for the dispatch step itself: two new
`Resolver{name, resolves_kind}` nodes plus their callables reuse
`qd_bind_resolver` byte-for-byte. What does NOT yet exist, and is
substantially harder, is the part that decides **which** kind a raw,
unclassified problem should be minted as in the first place — that is a
shape-recognition problem with no real observed corpus yet, and this
document's §6 sizing recommends it be deferred to its own, later,
data-informed prereg rather than designed here from first principles.

---

## 1. `question_driver.py`'s actual dispatch mechanism (Q1)

### 1.1 It is exactly what CLAUDE.md says, verified against the live file

Read in full: `domains/question_driver.py` (915 lines) and
`seeds/question_driving.json` (1174 lines), both fresh, not summarised from
CLAUDE.md. CLAUDE.md's own description ("Order-N growth..." /
"quanta navigation" sections, the composer/driver migration entry) is
**accurate and current, not stale** — the `qd_bind_resolver` rule
(`seeds/question_driving.json:191-259`) reads exactly as described:

```
match:  ag -has_goal-> goal ,  ag -has_resolver-> resolver
where:  goal.status == "pending"  AND  goal.kind == resolver.resolves_kind
effects: add_edge(goal, "resolve_with", resolver); set_attr(goal, "status", "dispatched")
```

Five `Resolver` nodes ship today (`question_driving.json:10-51`):
`elevator_compute` (`resolves_kind:"world"`), `know_ground` (`"know"`),
`reflect` (`"meta"`), `contrast` (`"contrast"`), `gap_parse` (`"gap"`).
Compound/compare goals are handled by a SEPARATE fold-up mechanism
(`qd_decompose`/`qd_compound_resolve`/`qd_compound_wall`,
`question_driving.json:261-627`) that never goes through a Resolver at all
— they're minted with `status:"waiting"`, not `"pending"`, so
`qd_bind_resolver`'s match never touches them (`question_driver.py:563`,
`_ingest_target`'s `is_branch` branch).

Execution is `substrate/world_adapter.py::_question_pursue_advance`
(`world_adapter.py:7929-7953`), the `question_pursue` reflex's response: it
walks `Goal` nodes with `status=="dispatched"`, reads the ALREADY-BOUND
`resolve_with` edge (the join's own effect, not a re-decision), looks up
the resolver's `name` in `self._master["goal_resolvers"]` (a plain dict
populated by `wire_question_faculty`, `question_driver.py:805`,
`world_adapter.py:7927`), and calls it. **The executor never branches on
graph state beyond "which name is bound."**

### 1.2 What adding new solve-kinds concretely requires

Because the JOIN is generic (string-equality on `kind`), adding
`"solve_deduction"` / `"solve_can"` / `"solve_decompose"` as new dispatch
targets is **purely additive graph data**:

1. Three new `Resolver{name:"solve_deduction", resolves_kind:"solve_deduction"}`
   (etc.) nodes + `Agent -has_resolver-> Resolver` edges — a new seed
   (e.g. `seeds/solver_dispatch.json`), mirroring `question_driving.json`'s
   own five-node block exactly.
2. Three new **resolver callables**, module-level functions with the exact
   signature every existing resolver already has —
   `fn(adapter, goal_node) -> None`, reading the Goal's attrs and writing
   `answer`/`status`/`note`/(new: `stop_reason`, see §3) back onto the SAME
   node (`question_driver.py:290-514` is the five live examples). Each
   callable is a **thin boundary invocation** of an EXISTING toolbox
   function — `propositional_deduction`/`inference_generation` for
   deduction, `can_native_orchestration`/`can_junction_tree`/
   `can_native_bp` for CAN, `problem_decomposition.decompose_problem` for
   decomposition — plus the mechanical write-back the five existing
   resolvers already do. This is the CLAUDE.md-sanctioned world-adapter
   shape, not new agent logic (§4 below is precise about the boundary).
3. Registration into `_RESOLVER_FUNCTIONS`
   (`question_driver.py:509-515`) or an equivalent dict passed to
   `wire_question_faculty` — one line, mechanical.

**What this does NOT require:** any change to `qd_bind_resolver` itself,
`_question_pursue_advance`, or `_pump`. The dispatch RULE is already
kind-agnostic; it does not know or care that "solve_deduction" is a new
concept.

**What it does NOT solve:** something has to WRITE `kind:"solve_deduction"`
onto a `Goal` node in the first place, for a genuinely novel/unclassified
problem. Today that "something" is `comprehend_question.comprehend()` — a
Python text classifier producing a `TargetSpec` with `kind` in
`{world, know, meta, compound, compare, gap}` (`question_driver.py:34-44`
docstring; `_ingest_target`, `question_driver.py:555-596`, is a mechanical
translation of whatever `comprehend` already decided, not itself a
decision). **`comprehend`'s existing five/six kinds are the accepted,
grandfathered comprehension boundary — CLAUDE.md permits a "thin
I/O-boundary classifier... converting an opaque external form into the
smallest graph token."** But teaching `comprehend` to also recognise
"this is a deduction problem" vs "this is a CAN problem" vs "this needs
decomposing first" is a NEW decision, of exactly the kind CLAUDE.md's
SHAPES-NOT-NUMBERS section says must not be added as a fresh Python
if/elif — this is precisely §2 below.

### 1.3 A real, present cross-population risk (found, not hypothesised)

`Goal` is not a private node type owned by `question_driver.py`. A grep
across the tree finds **`Goal` nodes minted, with their own independent
`kind` vocabularies, by at least four other subsystems**:
`domains/reflective_faculty.py` (`kind:"find"`, `kind:"describe_scene"`,
lines 1901/1955/1986), `domains/reading_drive.py` (`kind:"produce_analysis"`
/`"comprehend"`, line 1534), `domains/conversation_action.py` (a `kind`
parameter, line 281), and the world_adapter's own conversational
`answer_topic` goal kind (`seeds/conversation_topic_route.json`, read by
`seeds/gap_awareness.json`'s `note_unresolved_topic_gap`,
`gap_awareness.json:134-265`). All of these share the SAME
`Agent -has_goal-> Goal` edge type `qd_bind_resolver` joins on.

Today this is **accidentally safe** — none of these other kind strings
collide with `world`/`know`/`meta`/`contrast`/`gap`/`compound`/`compare`,
so `qd_bind_resolver` never mis-fires on them, for the same reason
`SHAPE_KIND_FIELD_RESULTS.md` §2.1 found the `CapabilityAxis`/`faculty`
row-arity "guard" to be accidental rather than designed: *"a side effect
of each kind's own row schema... an accident that currently produces the
right behaviour, not a rule anyone wrote down."* **Nothing today enforces
this namespace.** Whoever picks the string `"solve_deduction"` must check
it against this list by hand; there is no structural guard. This is named
here as a real, standing risk to record before building, not a blocker —
`"solve_deduction"`/`"solve_can"`/`"solve_decompose"` do not collide with
anything found in this investigation.

---

## 2. Is there already a "which solving facility fits this problem"
   codebook? (Q2)

### 2.1 What exists today, checked directly

Three candidate precedents were investigated, all in
`domains/analogical_thinking.py` (1241 lines, read in full),
`runners/dsl/src/shape_decode.rs` (grepped for every `kind` site), and the
`seeds/math_capability_shapes.json`/`seeds/self_design_axis.json` seeds
`question_driver.py`'s own `_QD_SEEDS` tuple already depends on
(`question_driver.py:539-540`):

1. **The MetaShape codebook** (`analogical_thinking.py`'s order-4
   abstraction, `MetaShape`/`ShapePrinciple`/`FunctionalRole` nodes,
   landed by `META_SHAPE_FIRST_CLASS_RESULTS.md`) — this discriminates
   concepts by ABSTRACT OPERATING PRINCIPLE ("feedback control",
   "associative recall", ...), not by "which of my own solving facilities
   should handle this." It is the closest EXISTING machinery in spirit
   (a real recognise → residual → mint loop, `sd_recognize`-shaped), but
   it operates over `Concept` nodes' keyword-evidenced vocabulary, not
   over problem STRUCTURE (a conditional statement, a coupling graph, a
   belief network) — wrong grain for this purpose, not wrong mechanism.
2. **`math_capability_shapes.json`'s `ShapeSignature{kind:"math"/"faculty"}`
   population** — a real, working precedent for "kind discriminates which
   pool an entry belongs to," but confirmed (§2.2 below) to work ONLY
   because the PYTHON READER (`_run_math_bridge`,
   `reflective_faculty.py:8011`, via `_load_shape_signatures:7357-7376`)
   filters by `kind` at read time — the Rust decode POOL itself does not
   partition on it.
3. **`self_design_axis.json`'s `CapabilityAxis{name:"self_design"}`** — the
   closest existing analogue to "choosing WHAT to work on next" at the
   AGENT level (gated on an open `DesignGap`, frontier-pick eligible,
   `self_design_axis.json:57-135`). This is the **capability-selection**
   layer (which capability axis to invest attention in), one level above
   question_driver's **goal-resolution** layer (which resolver handles
   THIS already-minted goal). The two are complementary, not competing:
   `self_design_axis` decides whether to build a NEW faculty at all;
   `qd_bind_resolver` decides which EXISTING resolver handles an
   already-typed goal. Neither one, today, decides "is this problem
   deduction-shaped or CAN-shaped."

**Verdict: no existing codebook does this job. A fresh one is needed** —
but see §2.3/§6 for why it should not be minted from a hypothesised
vocabulary.

### 2.2 The decisive grounding fact: `kind` does not partition a decode
   pool — confirmed, not assumed

`docs/research/engine_substrate/SHAPE_KIND_FIELD_RESULTS.md` (read in
full; a design spike that landed **NO-GO** on building a `kind`-based
guard) measured directly: *"`kind` does not partition a decode pool and
never has... nothing filters on it"* at the Rust `ShapeDecode` layer
(§1.2(1), citing `CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`'s own
finding: *"the node type is the only mechanism that partitions a
pool"*). Every `sd_recognize`-style rule restricts its `match_type` to
ONE graph node type before any `Covers`/`AntiUnify` runs (§2.4, citing
`seeds/meta_shape_growth.json`'s `msg_recognize`).

**Consequence for a "ProblemShape" codebook, stated precisely so it isn't
re-discovered the hard way:** tagging new entries as
`ShapeSignature{kind:"problem_shape"}` would NOT keep them in their own
pool — `runners/dsl/src/shape_decode.rs::load_parts` (confirmed by direct
read, cited at `analogical_thinking.py:672-686` for exactly this reason
already, re: `DirectionalCorrespondence`) loads **every** `ShapeSignature`
node with a `name`+`signature` attr into the SAME live decode pool
regardless of `kind`. A "problem-shape" signature that happened to
structurally match a real deduction-schema's `signature` would silently
compete for `inference_generation.resolve_implication_gap`'s live decode
slot. **The only genuinely safe partition is a NEW NODE TYPE**
(`ProblemShape`, mirroring the deliberate `DirectionalCorrespondence`
precedent, `analogical_thinking.py:672-687`: *"the only genuinely safe
gate is a node-TYPE boundary"*), not a `kind` tag on the shared
`ShapeSignature` type. Also worth noting: `SHAPE_KIND_FIELD_RESULTS.md`
§1.2 found `kind` is ALREADY overloaded three separate, incompatible ways
across the tree (`ShapeSignature.kind` mostly-inert, `math_capability_
shapes.json`'s domain-label `kind`, `DimensionGenerator.kind`'s algorithm
dispatch) — a fourth meaning should not be added to that name at all.

### 2.3 What a fresh `ProblemShape` signature would need to encode — and
   why this document does not commit to a vocabulary

If built, `ProblemShape` would need a `signature` in the SAME
positional-relation-vector form every other shape-comparable node uses
(`analogical_thinking.py::_concept_shape_vector`'s discipline: fixed
arity, fixed axis order, `AntiUnifyWitness`-consumable). Candidate
discriminating features, each grounded in a real structural fact already
present in this session's own toolbox:

- **Deduction-shaped**: the problem statement parses as a conditional
  (`propositional_deduction.parse_conditional` succeeds) — an
  antecedent/consequent pair exists, i.e. a `ShapeSignature{kind:
  "knowledge_logical"}` schema is mintable from it
  (`propositional_deduction.py:250-283`).
- **CAN-shaped**: the problem references a `Microtheory` with
  `causal_influence` edges among its `Concept`s (`can_network_from_mt`,
  `can_junction_tree.py`, reused unchanged by
  `problem_decomposition.project_can_identity`) — a belief-network
  coupling structure, not an implication chain.
- **Decomposition-needed**: NEITHER of the above cleanly applies, but a
  coupling graph CAN be projected (shared-attr / shared-event / CAN
  identity) and its `min_fill_upper_bound` is high enough that racing +
  possibly refining (`problem_decomposition.race_projections`/
  `refine_projection`) is worth attempting before any single-shot solver
  is tried.

**This document deliberately does NOT commit to this as the final
vocabulary.** Every other successful shape-codebook rung in this
tree — `math_capability_shapes.json`, `meta_shape_growth.json`, the
transform/dimension-inference ladder in `shape_decode.rs` — was minted
from REAL observed cases, not a hypothesised taxonomy written in advance
(this is the same discipline `PROBLEM_DECOMPOSITION_PREREG.md` §2 itself
followed: "grounded in REAL representations already in this codebase, not
synthetic fixtures"). Today there is **no corpus of real problems that
have actually been routed through this toolbox and observed to need one
facility over another** — the toolbox landed THIS session. Minting a
`ProblemShape` codebook now would be writing the taxonomy from
introspection, which is exactly the risk `SHAPE_AUDIT.md`'s findings
warn about (a recognizer with no observed residual to grow from). §6
sizes this as its own, later, data-informed rung.

---

## 3. Does `problem_decomposition`'s `stop_reason` feed the dispatcher, and
   is `gap_depth` reusable? (Q3)

### 3.1 `gap_depth`'s actual shape, read directly

`gap_depth` (`question_driver.py:563`, `qd_gap_guard`,
`question_driving.json:629-745`) is a **monotonic float counter** on a
`Goal` node, incremented by exactly 1 per recursion level, guarded by a
single `Lt(gap_depth, 1)` bound. It answers ONE question: "have I already
recursed once trying to ground a gap?" It carries no residual VALUE, no
history, no stop-reason taxonomy — just a depth.

### 3.2 `stop_reason`'s actual shape, read directly

`problem_decomposition.refine_projection` (`problem_decomposition.py:
367-422`) returns a categorical `stop_reason` in
`{"bound_met", "budget_exhausted", "no_improvement"}` PLUS a `log` list
recording every round's `(candidate, treewidth, gap)` — a genuine residual
TRACE (the `gap = width - bound` signal shrinking or not, round over
round), not a single depth counter.

### 3.3 Verdict: same PATTERN, not the same DATA — partial reuse only

What IS structurally shared between the two, and worth reusing
deliberately: **the discipline of "an effort budget as DATA on the Goal
node, not Python state,"** which `gap_depth` already establishes as a
working precedent (`qd_gap_guard`'s `Lt(gap_depth, 1)` guard is exactly
the shape a future `Lt(solve_rounds_used, solve_budget)` guard would take).
That PATTERN transfers cleanly. The CONTENT does not: `stop_reason` is a
3-way categorical outcome + a residual log, `gap_depth` is a bare counter.
**Feeding `stop_reason` into the dispatcher genuinely requires new attrs
on the Goal node** — e.g. `decompose_stop_reason` (string),
`decompose_residual_log` (the round-by-round trace, mirroring how
`elevator_compute` already writes `wall_kind`/`missing`/`note` as
free-form diagnostic attrs, `question_driver.py:318-323`) — written by
the new `solve_decompose` resolver's own mechanical write-back
(§4 below), exactly the way every existing resolver writes its own
faculty's verdict onto the node it resolved. **This is new evidence, not
a repurposing of `gap_depth`**, but it follows `gap_depth`'s own
established convention for HOW effort-as-data is represented, so it is
not a fresh invention either — a genuine partial answer, not a clean yes
or no.

---

## 4. `ground_unknowns`, the "seek further information" precedent, and
   what "seek a different process" would require (Q4)

### 4.1 Where it actually lives, read directly

`WorldAdapter.ground_unknowns` (`substrate/world_adapter.py:4798-4826`) is
a per-word mechanical I/O loop: for each unknown token in `text` (length
guard, not-already-known guard), call `teacher(form)` — the bare word —
and absorb the payload via `learn_from_teacher`; on a `None` payload, call
`self._queue_inquiry(w)`. **The decision of WHAT a word means is entirely
the teacher's** (the docstring: *"The teacher decides the meaning; the
adapter is the per-word I/O loop"*) — this is the canonical example of the
CLAUDE.md-sanctioned Python I/O boundary: mechanical translation, no
decision over graph state beyond "did the teacher answer or not."

`_queue_inquiry` (`world_adapter.py:9507-9524`) mints a
`CommunicativeGoal{communicate_kind:"inquire", inquires_about_form:...}`
— **note: a DIFFERENT node type than `Goal`**, wired via the SAME
`Agent -has_goal-> ...` edge type. Its own docstring states the policy is
FIXED, not a live decision: *"the fixed faculty policy is 'ask about what
you couldn't ground'; the goal is data."* This is a THIRD independent
population sharing the `has_goal` edge (alongside `Goal` and whatever
`answer_topic`/`find`/`describe_scene` uses) — another instance of the
§1.3 namespace-sharing finding, now three-deep.

### 4.2 What "seek a different solving process" concretely requires

`ground_unknowns` is specifically about grounding a MISSING WORD/FACT —
its unit of failure is "this token has no meaning," and its unit of
recovery is "ask the teacher for one." A stuck SOLVE goal
(`refine_projection` returning `"no_improvement"` or
`"budget_exhausted"`, or a deduction/CAN resolver walling honestly) is a
structurally DIFFERENT kind of failure: not "I lack a fact," but "I have
the facts and the wrong TOOL for them, or the right tool ran out of
budget." Extending `ground_unknowns`'s decision space to cover this would
be a category error — it would have to grow a second, unrelated failure
mode inside a function whose entire contract is "per-word teacher loop."

**The correct home, once the real code is read, is the `gap_awareness`
pipeline (§4.3), not `ground_unknowns` and not a new resolver-internal
retry.** This is neither "a new Goal kind" nor "a new resolver" in the
`qd_bind_resolver` sense — it is a NEW GAP-DETECTION RULE, structurally
identical to the one gap_awareness.json already ships for exactly this
shape of problem.

### 4.3 The precedent to mirror, read in full

`seeds/gap_awareness.json`'s `note_unresolved_topic_gap`
(`gap_awareness.json:134-265`) is the exact template: the WORLD ADAPTER
mechanically records a factual outcome onto a Goal
(`world_adapter._answer_topic_reply` sets `outcome:"resolved"|"unresolved"`
— a datum, never a decision, per the seed's own description field), and a
RULE decides an `unresolved` `answer_topic` goal is a knowledge gap,
files `SelfConcern{source:"implicit", kind:"knowledge", ...}` with a
content-dedup guard, and marks `gap_noted` so it fires once.

The SAME shape applies directly: the new `solve_decompose` (etc.) resolver
mechanically writes `stop_reason`/`status` onto its Goal (exactly
`elevator_compute`'s existing write-back pattern, §1.2 item 2), and a NEW
rule (e.g. `note_solve_exhausted_gap`, seed TBD) decides that a `solve_*`
goal whose `status=="walled"` (or whose `stop_reason` is
`"budget_exhausted"`/`"no_improvement"`) is a capability gap and files
`SelfConcern{kind:"solving_exhausted", content:<what was tried>}` —
byte-identical shape to the existing rule, different `kind` string and
trigger predicate. **From there the EXISTING human-gated spine already
handles everything downstream**: `promote_self_concern`
(`scripts/jabberwock_daemon.py:2161-2224`, read in full) turns a promoted
`SelfConcern` into a `StandingConcern{status:"pending"}`, and
`composer_dispatch.json`'s `ComposerCue` priority ladder
(`seeds/composer_dispatch.json`) routes it to the `experiment` composer
for a genuine self-experiment — no new promotion/experiment machinery is
needed. **This is the single cleanest, smallest-diff answer in this whole
document**: one new gap-detection rule, reusing everything downstream
unmodified.

---

## 5. Rule-shaped vs Python-I/O-shaped, precisely (Q5)

Per CLAUDE.md's own carve-outs (quoted, not paraphrased, where it
matters):

### 5.1 MUST be Rule (seed JSON), never Python

- **Any new kind-dispatch decision** — deciding a raw problem is
  deduction-/CAN-/decomposition-shaped is exactly *"an `if`/`else` that
  reads graph state and decides what to do next"* (CLAUDE.md,
  "Self-correction prompts"). If a `ProblemShape` codebook is ever built
  (§2.3, deferred), its recognise/mint step must be `sd_recognize`/
  `sd_mint_quantum`-shaped rules over the new node type, matching
  `seeds/meta_shape_growth.json`'s `msg_recognize`/`msg_mint` precedent —
  never a `comprehend_question.py` branch.
- **The gap-detection rule for a stuck solve** (§4.3) — the DECISION that
  an unresolved/exhausted solve goal is a capability gap is exactly the
  shape `note_unresolved_topic_gap` already is: a Rule, in a seed.
- **Any new `qd_bind_resolver`-adjacent join logic** — there is none
  needed (§1.2: the existing rule is already generic), but if a future
  slice needed, say, priority-among-multiple-eligible-resolvers, THAT
  decision would be a Rule (an `Argmin`/`Argmax` Term over candidate
  bindings, exactly `race_projections`'s own `Argmin`-over-`Neighbours`
  idiom, `problem_decomposition.py:279-285`), never a Python `min()`.

### 5.2 Legitimate Python (world-adapter-shaped, per CLAUDE.md's own
   examples)

- **The three new resolver callables** (`solve_deduction`/`solve_can`/
  `solve_decompose`) — each is *"a thin boundary invocation of an existing
  faculty"* + *"a MECHANICAL write-back of that faculty's own result onto
  the Goal node's attrs"* (`question_driver.py:272-284`'s own description
  of the FIVE existing resolvers, which this document's design extends
  verbatim, not by analogy). This is not a judgment call — it is the SAME
  code shape as `elevator_compute`/`know_ground`, which CLAUDE.md's own
  "What good Python code looks like" section endorses as the canonical
  world-adapter pattern.
- **Mechanical extraction of structural attrs onto the Goal at ingest**
  (e.g., "this problem statement parses as a conditional" →
  write `parsed_conditional: True`) — PURE EXTRACTION, legitimate,
  mirroring `_ingest_target`'s existing `op`/`params`/`concept` writes
  (`question_driver.py:564-574`). The line this document is careful to
  hold: extraction of a fact about the input is I/O; DECIDING which
  `kind` that fact implies is not (§5.1).
- **Registration/wiring** — `_RESOLVER_FUNCTIONS` dict entries,
  `wire_question_faculty` calls: one-line mechanical plumbing, the same
  class of code `question_driver.py:805` already is.

### 5.3 The one genuinely gray area, named honestly

`comprehend_question.comprehend()`'s EXISTING five/six-way kind
classification is Python today and is treated by this codebase as an
accepted boundary faculty (CLAUDE.md's own carve-out: *"A thin
I/O-boundary classifier is permitted... when it is genuinely converting
an opaque external form into the smallest graph token, AND there's no
Rust primitive that can do the job."*). This document does **not**
propose extending `comprehend` with new solve-kind branches — that would
be a fresh violation dressed as consistency with the existing (arguably
already at the edge of the carve-out) five-way split. The dispatch for
NEW solve-kinds should either (a) be supplied EXPLICITLY by a caller
(the §6.1 first slice — no auto-recognition at all), or (b) come from a
genuinely graph-native `ProblemShape` recognizer (§2.3/§6.3) once one
exists — never from growing `comprehend_question.py`'s existing if/elif
ladder.

---

## 6. Sizing — this is NOT one rung (Q6)

Three genuinely separable rungs, of very different size and risk, plus an
honest note on a fourth that may not be needed at all.

### 6.1 Rung 1 — wire the resolvers, kind supplied explicitly (smallest,
   safest, buildable NOW)

Add `seeds/solver_dispatch.json` (3 `Resolver` nodes,
`resolves_kind` in `{solve_deduction, solve_can, solve_decompose}`,
depending on `question_driving` + whatever seeds each toolbox module
itself needs) + 3 resolver callables in a new module (mirroring
`question_driver.py`'s existing five, §1.2 item 2) + registration. Proves
the dispatch machinery generalises to non-conversational solving with
**zero changes to `qd_bind_resolver`/`_question_pursue_advance`/`_pump`**.
Crucially, this slice does NOT need `comprehend_question` to recognise
anything — a caller/test mints `Goal{kind:"solve_deduction", ...}`
directly (the way `_ingest_target` already does for `world`/`know`
kinds), proving the JOIN and the resolver write-back independently of the
much harder recognition question. GO/NO-GO for this slice is
straightforward and mirrors `PROBLEM_DECOMPOSITION_PREREG.md`'s own
discipline: each resolver's write-back should reproduce, byte-for-byte,
what calling the underlying toolbox function directly already produces
(the CAN-identity correctness-anchor pattern that rung's own §2.1 already
established works for exactly this kind of wiring).

### 6.2 Rung 2 — the gap-detection rule for stuck solves (small, low risk)

`note_solve_exhausted_gap` (§4.3), mirroring `note_unresolved_topic_gap`
exactly. Depends on Rung 1 existing (needs a real `solve_*` resolver
writing a real `status`/`stop_reason` to trigger on). Independently
useful even before Rung 3 exists — any EXPLICITLY-dispatched solve goal
that walls or exhausts its budget already becomes a filed, promotable gap
under the existing human-gated spine, with no new promotion/experiment
machinery required (§4.3's "cleanest, smallest-diff" note).

### 6.3 Rung 3 — the `ProblemShape` recognizer (large, genuinely uncertain,
   defer to its own prereg)

This is the piece that actually delivers "the dispatcher chooses what to
think about" for a RAW, unclassified problem. Per §2.3, it should not be
designed from a hypothesised vocabulary — it needs real observed cases
(run Rung 1's explicit-dispatch resolvers on real problems drawn from
this codebase's own real representations, the same discipline
`PROBLEM_DECOMPOSITION_PREREG.md` §2 and `CAN_JUNCTION_TREE_PREREG.md`
already followed), a new `ProblemShape` node type (§2.2, NOT a `kind` tag
on `ShapeSignature`), and its own `sd_recognize`/`sd_mint_quantum`-shaped
rules. This is comparable in scope to `META_SHAPE_FIRST_CLASS_PREREG.md`'s
own rung (a full recognizer-plus-growth-path build), not a small
extension — it deserves its own prereg, written after Rungs 1-2 exist and
have produced real cases to mint from, not before.

### 6.4 A fourth item that may already be covered

The user's third framing item, "seek further information/processes,"
raised the question of whether `ground_unknowns`'s decision space needs
extending to cover "seek a different process." §4.2/§4.3's answer is that
it does NOT need extending — the existing `SelfConcern` →
`promote_self_concern` → `composer_dispatch` → experiment spine already
covers "the agent decides to try something different" once Rung 2 files
the gap. **No fourth rung is needed for this** unless a future measurement
shows the existing experiment-composer path produces the wrong KIND of
variant for a stuck solve goal specifically (untested, because Rung 1/2
don't exist yet to produce a real case) — named here so it isn't silently
assumed solved either.

---

## 7. What this document does NOT establish (registered in advance)

1. **No code, seed JSON, or tests were written.** This is investigation +
   design only, per the task's explicit instruction.
2. **The `ProblemShape` signature vocabulary in §2.3 is illustrative, not
   registered.** It is deliberately not committed to — §6.3 recommends
   minting it from real observed cases, not from this document's own
   reasoning about what SHOULD discriminate the three facilities.
3. **Whether the three named toolbox facilities (deduction/CAN/
   decomposition) are an exhaustive or even a well-chosen first set of
   solve-kinds is not established.** They are the ones that landed this
   session; a fourth or fifth facility may need its own resolver later,
   which Rung 1's pattern accommodates without further design.
4. **The §1.3 namespace-sharing risk on `Goal.kind` is named, not fixed.**
   No structural guard is proposed (a `kind`-collision check, a
   namespacing convention) — this document only records that the risk is
   real and currently accidental-safety, per the direct precedent
   `SHAPE_KIND_FIELD_RESULTS.md` §2.1 already found for a structurally
   identical situation elsewhere in the tree.
5. **Whether `qd_bind_resolver`'s single-resolver-per-kind assumption
   holds once solve-kinds exist is not tested.** Today each `kind` maps
   to exactly one `Resolver`; a future problem that could be solved by
   MULTIPLE eligible facilities (needing an `Argmin`/`Argmax` choice
   among them, §5.1's third bullet) is named as a possible future need,
   not designed here.
6. **No claim is made that this is the ONLY buildable next step in the
   reasoning/solving toolbox arc.** It answers specifically the "future
   dispatcher" question raised live in conversation.

---

## 8. Recommendation

**Build Rung 1 next** (§6.1): it is small, its correctness criterion is
sharp (byte-identical reproduction of calling the toolbox directly, the
same discipline every toolbox rung this session already used), it
requires no new Rust and no dispatch-shape design risk, and it is the
piece every later rung depends on for real data to mint from. **Do not
attempt Rung 3 (the `ProblemShape` recognizer) until Rung 1 has produced
real routed cases to observe** — minting a discrimination codebook from
this document's own hypothesised vocabulary, rather than from residuals a
real recognizer actually failed to cover, would repeat the exact mistake
`SHAPE_AUDIT.md` catalogues throughout this codebase's history: a shape
matcher built before there is a shape to match.
