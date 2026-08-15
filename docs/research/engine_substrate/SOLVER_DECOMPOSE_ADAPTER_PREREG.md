# A real-statement NL adapter for `solve_decompose` — PREREG

Base `main @ 7017989` ("Merge solver-analogy-adapter: second NL adapter for
solve_*, GO -- a self-correction"), verified via `git log --oneline -1 main`
immediately before creating this worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-decompose-adapter`, branch
`solver-decompose-adapter`.

## 0. What this task is checking

`SOLVER_NL_ADAPTER_PREREG.md` ranked `solve_decompose` #3 of six unwired
resolvers: *"every `project_*` builder requires an already-built CAN
Microtheory or already-minted deduction/situation-model nodes... its true
cost is whichever of ranks 4-6 below it draws candidates from, plus the
decomposition-shape extraction itself."* `QUESTION_DRIVER_RUNG1_RESULTS.md`
§2.2 then built (in its own test) a genuine two-facility chain — three
`solve_deduction` Goals mint three real `knowledge_logical` schemas, the
schema NodeIDs read straight off `solve_caps[g]["result"]["node"]`, handed to
`problem_decomposition.project_deduction_shared_attr`/
`project_deduction_complete`, raced via a `solve_decompose` Goal — showing
the composition WORKS, but that test hand-supplies literal statement text as
Python-side data, not as a general-purpose entry point another caller could
reuse. This task's job: characterise precisely what "build a candidate
projection from graph nodes" requires, and check whether a general NL
adapter for `solve_decompose` is genuine new work or pure composition of
what already exists (`mint_solve_deduction_goal`, itself already an NL
adapter since day one — `solve_deduction`'s prerequisite was always a bare
statement string, never a graph object) with `problem_decomposition.py`'s
existing candidate builders.

## 1. What building a candidate projection from graph nodes actually
   requires — read directly, not guessed

`domains/problem_decomposition.py:150-183`
(`project_deduction_shared_attr`/`project_deduction_complete`) is a
**mechanical, pure function of a node list**: given `schema_nodes` (a plain
Python list of `ShapeSignature` NodeIDs), it reads each node's own
`signature`/`supplies` JSON attrs (`_schema_attrs`, `problem_decomposition.py:
124-147` — a mechanical read of fields `propositional_deduction.py` itself
already writes when it mints a schema, confirmed by direct read) and derives
edges from shared antecedent/consequent attr tokens. **It is node-type-
SPECIFIC in the sense that it expects `ShapeSignature{kind:"knowledge_
logical"}` nodes with those two JSON attrs — but it is NOT statement- or
caller-specific: it does not care how the nodes were minted, only that they
carry those fields.** `project_can_identity`/`project_can_complete` are the
CAN-network sibling (mechanical read of `causal_influence` edges via
`can_junction_tree.can_network_from_mt`, needs an already-built `Microtheory`)
and `project_situation_model_shared_event` is the third (mechanical read of
`SmEvent` agent/theme/goal role edges). **None of the three builders contain
a decision — "which candidate is right" is `race_projections`'s job
(`Argmin` over `min_fill_upper_bound`), not the builder's.**

This directly confirms the task's own hypothesis: **candidate-projection
construction from a set of already-real schema nodes is a fixed, mechanical
shape extraction, not new capability.** The only genuinely open question is
whether *getting* real schema nodes from raw natural-language statements is
itself cheap — and it already is, verified next.

## 2. `solve_deduction` was ALREADY an NL adapter, from Rung 1 — checked, not
   assumed

Unlike `solve_reasoning_bridge`/`solve_analogical_promote`/the three CAN
resolvers (whose Goal-minting entry points needed a pre-built graph object —
a Microtheory, a `DirectionalCorrespondence`), `mint_solve_deduction_goal`
(`domains/solver_dispatch.py:160-171`) has taken a bare `statement: str`
since `QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`'s own Rung 1 — it was
never gated behind a pre-built object. `solve_deduction` the resolver
(`domains/solver_dispatch.py:459-523`) internally tries `propositional_
deduction.mint_universal_schema` / `mint_existential_premise` /
`mint_logical_schema` in a fixed order and installs a real `ShapeSignature`
node on success, stashing `{"node": <NodeID>, ...}` in `solve_caps` (read
back exactly as `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain test does,
`tests/test_solver_dispatch_migrated.py:416-418`).

**Live-confirmed before finalising anything** (real `WorldAdapter` boot,
`load_all_seeds`, `wire_question_faculty`, three genuine Bigville-styled
conditional statements — real Bigville CAN-topic vocabulary, `world_safe`,
the same tokenisation `SOLVER_NL_ADAPTER_RESULTS.md` §4.1 already
demonstrated, plus ordinary "resident"/"mayor" nouns, NOT the prior rung's
literal fish/mammal fixture text):

```
"If X is a resident, X can vote."          -> resolved, logical_resident_can_vote,       node #24392
"If X is a resident, X is world safe."     -> resolved, logical_resident_world_safe,     node #24396
"If X is a mayor, X can govern."           -> resolved, logical_mayor_can_govern,         node #24404

schema_nodes = [#24392, #24396, #24404]
project_deduction_shared_attr -> nodes=[...], edges=[(#24392,#24396)], edge_reason={(...): 'resident'}
project_deduction_complete    -> nodes=[...], edges=[(#24392,#24396),(#24392,#24404),(#24396,#24404)]
min_fill_upper_bound: shared_attr treewidth=1, complete treewidth=2   (real, measured discrimination)
```

Exactly the same shape `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain test
measured (`shared_attr` treewidth=1 vs `complete` treewidth=2), reproduced
here on independent, non-fixture statement text, confirming this is not an
artefact of one hand-picked sentence triple.

**Honest-wall statements checked too, live, before finalising:** a
non-conditional statement ("The mayor likes apples.") and a question ("Is
the mayor trustworthy?") both correctly WALL inside `solve_deduction` itself
(`status: "walled"`, the existing, unedited honest residual — "the general
reading pipeline does not ground ... into an antecedent is_a + consequent
is_a/can predication pair") — confirming an adapter over this machinery
inherits `solve_deduction`'s own already-correct refusal behaviour for free,
no new gating needed for THAT failure mode.

## 3. So does the general NL adapter compose cheaply, or need something new?

**It composes cheaply — confirmed live, not assumed from the shape of the
problem.** The chain is exactly the task's own hypothesis: N statements ->
dispatch each through the ALREADY-EXISTING `mint_solve_deduction_goal` (an
NL adapter since day one, needing no new parsing) -> drive each to
resolution via the SAME `fire_reflexes()`+`run_rules()` tick loop
`question_driver.py::_pump` (production code, not test-only,
`domains/question_driver.py:652`) and `tests/test_solver_dispatch_migrated.py
::_pump` both already use -> read back each real `ShapeSignature` node from
`solve_caps[g]["result"]["node"]` (exactly the field the Rung 1 chain test
already reads) -> hand the collected node list to the ALREADY-EXISTING,
UNEDITED `problem_decomposition.project_deduction_shared_attr`/
`project_deduction_complete` -> mint a `solve_decompose` Goal via the
ALREADY-EXISTING `mint_solve_decompose_goal`.

**The one genuinely new piece is NOT a parser — it's a driver.** Every prior
`_from_text` adapter (`mint_solve_reasoning_bridge_goal_from_text`,
`mint_solve_analogical_promote_goal_from_text`) only ever MINTS a Goal and
returns it un-resolved, leaving pumping to the caller — because their own
prerequisite object (two strings; a `DirectionalCorrespondence` built from
two already-resolved Concept nodes) never itself needed a resolved Goal
along the way. `solve_decompose`'s prerequisite is different in KIND: the
candidate list must be built from ALREADY-RESOLVED `ShapeSignature` nodes at
mint time (`mint_solve_decompose_goal`'s own contract, `solver_dispatch.py:
442-453` — candidates are staged in `solve_caps` eagerly, not deferred), and
those nodes only exist once each per-statement `solve_deduction` sub-goal
has actually been driven to resolution. There is no way to defer this: this
adapter must drive N cheap sub-goals internally before it can mint anything
useful. This is the SAME already-existing Rust rule-engine invocation
(`native.run_rules()`) every other driver in this codebase already performs
(`question_driver.py::_pump`, `QuestionDriver.drive()`'s own `_pump` calls),
never a NEW Python decision about what a goal's result MEANS — the adapter
only sequences an existing loop, then reads back an existing field.

## 4. Honest decline discipline — a real, documented difference from the
   prior two `_from_text` adapters, not silently glossed over

Both `mint_solve_reasoning_bridge_goal_from_text` and `mint_solve_
analogical_promote_goal_from_text` guarantee **zero Goal nodes minted at
all** on any decline, because their own suitability checks
(`speech_act=="question"`, `_is_property_pred`, concept-name-count) are pure
reads over the reader's output, no graph mutation. `solve_decompose`'s own
suitability check is harder: "does this statement resolve to a real
`ShapeSignature` schema" is `solve_deduction`'s OWN verdict, which (via the
`mint_*` installer functions) is only knowable by actually installing a node
on success.

**Fix, so the SAME zero-mutation decline guarantee holds:** a pure,
zero-mutation pre-check, `_would_parse_as_deduction`, calling ONLY the pure
`parse_universal`/`parse_existential`/`parse_conditional` functions (never
their `mint_*` siblings) in the SAME fixed order `solve_deduction`'s own
ladder already uses — confirmed live (§2 above, and re-confirmed in §6) that
`parse_conditional`/`parse_universal`/`parse_existential` are pure PARSE
functions (`reading_collapse.read_clause(..., write=False, learn=False)`
throughout, no `mint_*`/`add_node` call reachable from any of the three) —
so a statement is only counted as "usable" before anything is minted.
**Only once at least 2 statements pass this pure pre-check does the adapter
mint/drive ANY solve_deduction sub-goal at all** — so a total decline (fewer
than 2 statements pass) is a genuine, zero-graph-mutation refusal, matching
the prior two adapters' own discipline exactly. A PARTIAL success (2+ pass
the pre-check, sub-goals then driven for real) DOES leave real, inspectable
`solve_deduction` Goal + `ShapeSignature` nodes in the graph for the
statements actually used — this is a real, honestly-documented difference
from the prior two rungs' "mints nothing on decline, ever" guarantee, not an
oversight: it is the unavoidable cost of this resolver's prerequisite being
a resolved node, not a string, and it leaves exactly the SAME kind of
inspectable trace `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain test already
produces on a successful chain.

## 5. Node-source scope — ONE type only, named as the honest boundary

`problem_decomposition.py` has THREE candidate-builder families
(`project_can_*`, `project_deduction_*`, `project_situation_model_*`). This
task scopes to exactly ONE: **deduction schema nodes from a list of
deduction-shaped statements**, for the same reason both prior NL-adapter
rungs scoped narrowly to their own single well-evidenced case rather than
attempting universal coverage:

- **CAN-network candidates** (`project_can_identity`/`project_can_complete`)
  need an already-built `Microtheory` — `SOLVER_NL_ADAPTER_PREREG.md` §2
  already found (and this task does not re-litigate) that there is NO
  NL-to-CAN-network path anywhere in the codebase; building one is a
  genuinely new, large capability (causal-relation-with-weight extraction
  from prose), not a connector. Out of scope, unchanged finding.
- **Situation-model candidates** (`project_situation_model_shared_event`)
  need a list of already-minted `SmEvent` nodes — there is no existing
  `solve_*`-kind NL adapter that mints `SmEvent` nodes from raw text in this
  toolbox (situation-model ingestion is a SEPARATE facility,
  `situation_model_reader.py`, never wired as a `solve_*` resolver
  prerequisite at all). A real adapter here would need to characterise that
  facility's own NL-readiness from scratch — a separate, unscoped
  investigation, named as a follow-on, not attempted here.
- **Deduction-schema candidates** are the ONE source type with a
  ready-made, already-NL, already-resolver-wired pipeline
  (`mint_solve_deduction_goal` + `solve_deduction`) feeding a mechanical,
  unedited candidate builder (`project_deduction_shared_attr`/
  `project_deduction_complete`) — confirmed live end to end, §2-3 above.

## 6. What will be built

`mint_solve_decompose_goal_from_text(adapter, statements: list, bound: int,
*, max_exact_n: int = 10, refine_budget: int = 0, mode: str = "auto")` in
`domains/solver_dispatch.py`, immediately after `mint_solve_decompose_goal`:

1. Decline (`return None`, zero graph mutation) if `statements` is not a
   non-empty list/tuple, or `bound is None`.
2. Filter to non-empty/non-whitespace statements, THEN to only those passing
   the pure `_would_parse_as_deduction` pre-check (zero mutation). Decline if
   fewer than 2 survive — cannot build a meaningful coupling graph from 0-1
   nodes; matches `race_projections`'s own "at least one candidate" floor
   plus the task's own "enough real nodes/candidates" bar.
3. For each surviving statement: `mint_solve_deduction_goal(adapter,
   statement, mode=mode)`, drive to resolution via a local `_drive_to_
   resolution` helper (a same-shape, own-copy mirror of `question_driver.py
   ::_pump`'s bounded tick loop — "same pattern, own cache, no cross-import",
   the house convention `analogical_thinking.py`'s own module comment
   documents and `_find_concepts_by_name` already followed in the prior
   rung). Collect `solve_caps[g]["result"]["node"]` for every sub-goal that
   reaches `status=="resolved"` (an honest defensive re-check — the
   pure pre-check and the resolver's own ladder are NOT byte-identical
   code paths, so re-verifying the ACTUAL outcome rather than trusting the
   pre-check's prediction is the same "verify, don't assume" discipline
   every rung in this arc has used).
4. Decline (return the goal-less `None`) if fewer than 2 real schema nodes
   were actually collected after driving (the pre-check can pass while the
   real resolver still walls for a reason the pure parse-only check cannot
   see, e.g. `_norm_attr` producing an empty token — an honest defensive
   floor, not assumed unreachable).
5. Build BOTH candidates via the UNEDITED `problem_decomposition.
   project_deduction_shared_attr` and `project_deduction_complete` over the
   collected node list (racing two candidates, not one, mirrors
   `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain test — proves the race
   step does real discriminating work, not merely "the only candidate
   available happens to win").
6. Return `mint_solve_decompose_goal(adapter, [cand_shared, cand_complete],
   bound, max_exact_n=max_exact_n, refine_budget=refine_budget)` — the
   UNCHANGED existing entry point, dispatching through the UNCHANGED
   `qd_bind_resolver` -> `solve_decompose` exactly as every other caller.

**Not touched:** `solve_decompose`'s own internals, `solve_deduction`'s own
internals, `problem_decomposition.py` (zero edits — every function called is
read-only reuse), `seeds/solver_dispatch.json`. Pure addition, mirroring the
diff shape of both prior `_from_text` rungs.

## 7. GO/NO-GO leaning

**GO**, scoped precisely to ONE node-source type (a list of deduction-shaped
statements, ≥2 of which must resolve to real schemas) — mirroring both
predecessor rungs' own narrow-scope discipline. CAN-network and
situation-model candidate sources are named, sized follow-ons (§5), not
silently assumed solved. The one honest, non-silent departure from the
zero-mutation-on-decline bar of the prior two rungs is documented in §4
(partial success leaves real, inspectable sub-goal nodes; total decline does
not) — a genuine difference in this resolver's prerequisite kind, not an
oversight.

## 8. Regression plan

`tests/test_solver_dispatch_migrated.py`, `tests/test_solve_gap_awareness_
migrated.py`, `tests/test_problem_shape_migrated.py`, `tests/test_solver_
math_boundary.py`, `tests/test_solver_nl_adapter.py`, `tests/test_solver_
analogy_adapter.py`, `tests/test_problem_decomposition.py`, plus a new
`tests/test_solver_decompose_adapter.py` for this rung's own live
demonstrations — all green, fresh (not from `results/failure_baseline.json`),
before declaring GO final.
