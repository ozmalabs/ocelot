# The first NL-to-structure adapter for the six unwired `solve_*` resolvers — PREREG

Base `main @ d92c7d2` ("Merge progsyn-delimjoin-budgetwall: delim-join +
budget-wall sizing, both NO-GO"), verified via `git log --oneline -1 main`
immediately before creating this worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-nl-adapter`, branch
`solver-nl-adapter`.

## 0. Corrected framing this task inherits (not re-derived)

`SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md` §0 already corrected the record:
the fact that six of the seven `solve_*` resolvers require a caller to have
already built the prerequisite graph object is a **wiring gap**, not a
designed wall — nobody has written the NL-to-structure adapter for any of
the six yet, the same step `solve_deduction` already has via
`propositional_deduction.parse_conditional`/`parse_universal`/
`parse_existential`. This task investigates all six precisely, ranks them by
REAL evidenced cost (not shape-of-the-problem guessing), and builds the
cheapest one if it is genuinely cheap.

## 1. What each of the six resolvers reads off its Goal node, read directly
   off `domains/solver_dispatch.py` before ranking anything

| resolver | required graph object (read off the Goal) | source lines |
|---|---|---|
| `solve_can_relax` | `targets_mt` edge → a `Microtheory` (a full CAN belief network: `Concept` nodes + weighted `causal_influence` edges) | `solver_dispatch.py:331-372` |
| `solve_can_exact` | `targets_mt` edge → same as above | `solver_dispatch.py:375-408` |
| `solve_can_bp` | `targets_mt` edge → same as above | `solver_dispatch.py:411-443` |
| `solve_reasoning_bridge` | **direction-dependent**: `deduction_to_can` needs TWO PLAIN STRING ATTRS on the Goal itself (`entity`, `attr`, both read via `at.get(...)`, no edge, no pre-built node at all); `can_to_deduction` needs a `targets_mt` edge → a full CAN Microtheory, same as the three CAN resolvers above | `solver_dispatch.py:446-489` |
| `solve_analogical_promote` | `targets_correspondence` edge → an already-recorded `DirectionalCorrespondence` node (itself the product of `analogical_thinking._pair_witness`/`record_directional_correspondence` over two REAL `Concept` graph nodes) | `solver_dispatch.py:492-520` |
| `solve_decompose` | candidates staged in `solve_caps` — a list already produced by `problem_decomposition.py`'s `project_*` functions, which themselves each require a pre-existing `Microtheory` (`project_can_*`) or a list of already-minted `ShapeSignature`/`SmEvent` nodes (`project_deduction_*`/`project_situation_model_*`) | `solver_dispatch.py:523-565`, `domains/problem_decomposition.py:99-186` |

**The load-bearing structural fact**: `solve_reasoning_bridge`'s
`deduction_to_can` direction is the ONLY one of the twelve (six resolvers,
two of them two-directional) whose prerequisite is not a graph NODE the
caller must have separately minted/found, but two PLAIN STRINGS — the exact
same shape `mint_solve_deduction_goal`'s own `statement` string already is.
Every other prerequisite (a CAN Microtheory, a DirectionalCorrespondence, a
candidate-projection list) is itself a structured graph object with no
existing NL route into it anywhere in the codebase (checked directly, §2).

## 2. Does an NL-to-that-object path already substantially exist elsewhere?
   — checked by reading, not guessed

- **CAN belief networks** (`targets_mt`, needed by `solve_can_relax`/
  `solve_can_exact`/`solve_can_bp`, and `solve_reasoning_bridge`'s
  `can_to_deduction` direction). `worlds/bigville_can_beliefs.py` is the
  ONLY builder in the tree, and it is a MECHANICAL TRANSLATION of an
  already-drawn `bigville_cast100.json` resident record's numeric `params`
  dict (`build_resident_can_mt`, `worlds/bigville_can_beliefs.py:134-200`)
  into 5 `Concept` nodes + 5 weighted `causal_influence` edges — there is no
  path from raw NL text to a `params` dict, let alone to a weighted causal
  edge, anywhere in this codebase. Building this would mean inventing
  causal-relation-with-weight extraction from prose, a genuinely new,
  large capability, not a small connector. **No reuse found. Expensive.**
- **`DirectionalCorrespondence`** (needed by `solve_analogical_promote`).
  `analogical_thinking.record_directional_correspondence` (`domains/
  analogical_thinking.py:699-737`) already exists and is fully mechanical —
  but its two inputs (`node_a`, `node_b`) must be REAL `Concept` graph nodes
  that already carry vocabulary-hit-derived shape vectors
  (`_concept_shape_vector`), and the correspondence it records is a
  STRUCTURAL similarity computed over the held `FunctionalRole`/
  `ShapePrinciple`/`MetaShape` vocabulary — not something a single sentence
  states directly. An NL adapter here would need (a) two concept NAMES
  extracted from an analogy-shaped sentence ("X is like Y", "X corresponds
  to Y" — no existing parser for this shape anywhere in the tree, checked by
  grep for `analog*`/`correspond*` constructions in `seeds/reading_
  constructions.json`: none), AND (b) both names resolving to EXISTING
  `Concept` nodes already in the graph (a lookup that is cheap, mirroring
  `reasoning_can_bridge._find_concept_by_name`) — but (a) is a genuinely new
  parse shape, not a reuse. **Partial reuse (the correspondence-recording
  half); the NL-recognition half does not exist. Moderate cost.**
- **`solve_deduction`'s own output composing into `solve_reasoning_bridge`**
  (the task's own hinted possibility). Checked directly: `solve_deduction`
  writes `schema_name`/`answer` (a `knowledge_logical` `ShapeSignature`
  name) onto its Goal — it does NOT write a plain `(entity, attr)` pair
  anywhere a caller could read back mechanically; the schema's own
  `signature`/`supplies` JSON (`propositional_deduction.mint_logical_
  schema`) encodes an antecedent/consequent PATTERN (`is_a(X, attr)`), not a
  bound entity. Composing `solve_deduction`'s output into `solve_reasoning_
  bridge` would need a THIRD thing — a bound instance ("X" resolved to a
  specific named entity) — which is exactly the capability
  `SOLVER_MATH_BOUNDARY_RESULTS.md` §5 already found `solve_deduction` does
  not have (no second-fact application/query-answering step). **This
  particular composition does not substantially exist; ruled out as the
  candidate it was hinted to be.**
- **`solve_reasoning_bridge`'s `deduction_to_can` direction itself** — its
  ONLY two inputs are `entity` (a bare string, passed straight to
  `situation_model_reader._entity`, an existing get-or-create-by-name
  primitive already reused by a dozen other modules — confirmed by grep:
  `coref_entities.py`, `inference_generation.py`, `character_tom.py`,
  `global_monitoring.py`, `reading_drive.py` all call `smr._entity`
  directly) and `attr` (a bare string, normalised via `propositional_
  deduction._norm_attr` — one `.lower().replace()` chain, already used by
  `solve_deduction` itself). **Both extraction primitives — read one
  declarative copular predication out of real text via `reading_collapse.
  read_clause`, then read off `(subject, object)` — are the EXACT machinery
  `parse_conditional`'s `bare_universal` branch and `situation_model_
  reader.ingest_predication`'s property branch (`_is_property_pred`) already
  use, verbatim, for a different purpose. Nothing new needs to be built to
  extract `(entity, attr)` from "X is Y" — it is a straight reuse of two
  already-existing, already-battle-tested reader calls.** Confirmed LIVE
  (§3below) before writing this ranking, not assumed from the shape of the
  problem alone: `read_clause(agent, "Verity Peaseblossom is world safe.",
  write=False, learn=False)` grounds directly to
  `[["is_a", "verity_peaseblossom", "world_safe"]]` — the reader's OWN
  multi-word-noun-phrase joining already collapses "world safe" into one
  underscore-joined token, `_norm_attr` is then a no-op pass-through, and
  `world_safe` is BYTE-IDENTICAL to a real Bigville resident's own CAN
  topic name (`worlds/bigville_can_beliefs.TOPIC_NAMES`). **This is the
  cheapest of the six by a wide margin, confirmed live, not assumed.**
- **`solve_decompose`'s candidates**. Every `project_*` builder
  (`problem_decomposition.py:99-186`) takes an ALREADY-BUILT `mt`/
  `schema_nodes`/`sm_event_nodes` argument — this resolver's true
  prerequisite is strictly downstream of (and therefore never cheaper than)
  whichever of the CAN-network or deduction-schema adapters would need to
  exist first. **No standalone reuse; inherits the cost of whichever
  upstream object it projects over. Expensive, and non-independent of the
  CAN-network cost above.**

## 3. Live confirmation the extraction actually works, BEFORE ranking is
   finalised (not assumed from reading code alone)

Run against a REAL `WorldAdapter` boot (`load_all_seeds`) and a REAL
Bigville resident (`seeds/bigville_cast100.json`, resident 0, "Verity
Peaseblossom"), via `worlds.bigville_can_beliefs.build_resident_can_mt`
(the exact pattern `tests/test_solver_dispatch_migrated.py::_resident_mt`
already uses for `solve_can_exact`'s own P13b-style hand-built-network
demonstration):

```
sentence: "Verity Peaseblossom is world safe."
read_clause(...) -> [["is_a", "verity_peaseblossom", "world_safe"]]
entity = "verity_peaseblossom", attr = "world_safe"  (pd._norm_attr, no-op here)
reasoning_can_bridge.apply_derived_fact_as_can_evidence(a, entity, attr,
    positive=True, alpha=1.0)
-> {'applied': True, 'concept': #24290, 'entity': 'verity_peaseblossom',
    'attr': 'world_safe', 'evidence': 1.0, 'alpha': 1.0}
```

The token-based correspondence rule (`sm_entity_denotes_believer_by_name_
tokens`, `seeds/entity_concept_correspondence.json`) resolves
`"verity_peaseblossom"` (lowercase, underscore-joined — the reader's own
subject-token convention) to the real `Resident` node named "Verity
Peaseblossom" (title-case, space-joined — the cast JSON's own convention)
purely via token-set equality (`name_variant_merge._name_tokens` lowercases
and splits both), never a byte-identical-string coincidence. This is the
SAME general resolution mechanism `SOLVER_MATH_BOUNDARY_RESULTS.md`'s own
P13b used the hand-built-network route for — the new piece here is only the
`(entity, attr)` extraction from a real declarative sentence, not the
CAN-side plumbing, which is already fully general.

Honest-wall confirmed too, same live boot: a real sentence whose predicate
attr does not exist as a Concept in the resident's Mt —

```
reasoning_can_bridge.apply_derived_fact_as_can_evidence(a, "verity_peaseblossom",
    "honest", positive=True, alpha=1.0)
-> {'applied': False, 'reason': "Microtheory 'Verity Peaseblossom_beliefs'
    holds no Concept named 'honest'"}
```

— and a question-shaped sentence grounds to an EMPTY predication list
(`"Is Verity Peaseblossom trustworthy?"` → `[]`, `speech_act: "question"`),
and a non-copular event sentence (`"Verity Peaseblossom likes apples."` →
`[["likes","verity_peaseblossom","apples"]]`) grounds to a relation
`_is_property_pred` does NOT accept — both are real, natural sentences an
adapter with no shape gate could be tempted to mangle (mirroring exactly the
Bug 1 defect class `SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md` fixed for
`solve_deduction`), so the adapter built below gates on both.

## 4. Ranking, by real evidenced cost (cheapest first)

1. **`solve_reasoning_bridge` (`deduction_to_can` direction) — CHEAPEST,
   confirmed live.** Needs two bare strings; both extraction steps are pure
   reuse of already-existing, already-shipped reader calls
   (`reading_collapse.read_clause`, `propositional_deduction._norm_attr`,
   `situation_model_reader._is_property_pred`); the downstream CAN-side
   resolution (`apply_derived_fact_as_can_evidence`, the correspondence
   rules) is already fully general and untouched. Zero new parsing
   capability required — only a shape gate (question/non-property refusal)
   and a thin composing function.
2. **`solve_analogical_promote` — MODERATE.** The correspondence-recording
   half (`record_directional_correspondence`) is fully mechanical and
   reusable; concept-name lookup against existing `Concept` nodes is cheap.
   But there is no existing parser anywhere in the tree for an
   analogy-shaped sentence ("X is like Y" / "X corresponds to Y") — that
   half is genuinely new, unbuilt parsing work, not a reuse.
3. **`solve_decompose` — EXPENSIVE, and non-independent.** Every
   `project_*` candidate builder requires an already-built CAN Microtheory
   or already-minted deduction/situation-model nodes — its true cost is
   whichever of ranks 4-6 below it draws candidates from, plus the
   decomposition-shape extraction itself.
4. **`solve_can_relax` / `solve_can_exact` / `solve_can_bp` — MOST
   EXPENSIVE, tied.** All three need a full CAN belief network (Concepts +
   weighted causal edges). No NL-to-CAN-network path exists anywhere in the
   codebase; the only builder (`bigville_can_beliefs.build_resident_can_mt`)
   is a mechanical translation from an already-drawn NUMERIC params dict,
   not from text. Building this is inventing causal-relation-with-weight
   extraction from prose — a substantial new capability, not a connector.

## 5. What will be built

**`solve_reasoning_bridge`'s `deduction_to_can` direction**, rank 1. A new
`mint_solve_reasoning_bridge_goal_from_text(adapter, statement)` in
`domains/solver_dispatch.py` (alongside the existing `mint_solve_reasoning_
bridge_goal`, following its own naming), that:

1. Reads `statement` through `reading_collapse.read_clause` (unmodified),
   exactly as `parse_conditional`'s `bare_universal` branch already does.
2. Declines (`return None`) on `speech_act == "question"` — the SAME gate
   `SOLVER_MATH_BOUNDARY_BUGFIX_RESULTS.md`'s Bug 1 fix added to
   `parse_conditional`, applied here for the identical reason (a question's
   own honest fallback grounding can still surface an `is_a`-shaped
   predication that would otherwise pass every downstream check).
3. Declines on no predication, or a predication whose relation is not a
   property predication (`situation_model_reader._is_property_pred` — an
   already-existing, already-reused-elsewhere helper — checked, not a new
   classifier).
4. Extracts `entity = subject`, `attr = propositional_deduction._norm_attr(object)`
   and dispatches through the UNCHANGED `mint_solve_reasoning_bridge_goal(
   adapter, "deduction_to_can", entity=entity, attr=attr, positive=True)`.

`positive` is fixed `True` — no negation-detection machinery exists anywhere
in the reading pipeline for a plain declarative sentence (checked: no
`NEG`/negator markup reaches a grounded predication's relation or polarity
in `reading_collapse.py`), so this adapter honestly does not attempt
negated facts; a future rung that wires negation detection is a named,
separate follow-on, not built here.

`solve_reasoning_bridge`'s OWN internals (`domains/solver_dispatch.py:446-
489`) are NOT touched — only a new front door is added, dispatching through
the unchanged `qd_bind_resolver`/`solve_reasoning_bridge` machinery exactly
as every existing `mint_solve_*_goal` helper already does.

## 6. Live demonstration plan (to run and report in RESULTS)

- **Success**: real sentence "Verity Peaseblossom is world safe." (a real
  Bigville resident's real CAN network, built via the SAME `_resident_mt`
  pattern the existing test suite already uses) → adapter → Goal minted →
  `qd_bind_resolver` dispatch (unchanged) → `solve_reasoning_bridge` →
  `status == "resolved"`, `applied == True` — verified by additionally
  reading the Concept's own `identity_field`/evidence state, not just
  `status`.
- **Honest wall (resolver-side miss)**: real sentence with a predicate that
  does not match any Concept name in the resident's CAN network → Goal
  minted → dispatch → `status == "walled"`, `gap_key` filed correctly
  (Rung 2's `note_solve_exhausted_gap` unchanged).
- **Honest decline (adapter-side gate)**: a real question-shaped sentence
  and a real non-copular-event sentence → the adapter itself returns `None`
  — no Goal minted at all, never a fabricated entity/attr pair — mirroring
  the non-negotiable requirement that an adapter for unsuitable input must
  decline cleanly, not silently mint garbage (exactly the Bug 1 failure
  mode this rung must not repeat).

## 7. Regression plan

`tests/test_solver_dispatch_migrated.py`, `tests/test_solve_gap_awareness_
migrated.py`, `tests/test_problem_shape_migrated.py`,
`tests/test_solver_math_boundary.py`, plus a new
`tests/test_solver_nl_adapter.py` for this rung's own live demonstrations —
all green, verified fresh (not from `results/failure_baseline.json`) before
declaring GO.
