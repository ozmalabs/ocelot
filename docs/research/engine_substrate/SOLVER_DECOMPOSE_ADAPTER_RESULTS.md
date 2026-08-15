# A real-statement NL adapter for `solve_decompose` — RESULTS

Prereg: `SOLVER_DECOMPOSE_ADAPTER_PREREG.md`, same worktree/branch, base
`main @ 7017989` ("Merge solver-analogy-adapter: second NL adapter for
solve_*, GO -- a self-correction"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-decompose-adapter`, branch
`solver-decompose-adapter`, commits `819091a` (PREREG) + `518796c`
(implementation + tests). `data/` was absent in the fresh worktree (not a
partial real directory); symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data
data`) and confirmed `data/wiktionary/en.jsonl.gz` resolves to the real
492,560,156-byte file. `main`'s tip re-checked at RESULTS time: still
`7017989` (no concurrent Bigville-session commits landed during this rung's
own run).

**Headline finding: the task's own hypothesis was correct, confirmed live
before writing any code.** `mint_solve_deduction_goal` has taken a bare
statement string since Rung 1 — it was NEVER gated behind a pre-built graph
object, unlike the other five previously-unwired resolvers. `problem_
decomposition.project_deduction_shared_attr`/`project_deduction_complete`
are mechanical, node-source-agnostic shape extraction over whatever
`ShapeSignature` nodes they are handed. Building a candidate projection from
real deduction schemas was therefore **already pure composition of two
things this codebase already had**, not new parsing capability. The only
genuinely new piece of code is a DRIVER (a bounded `run_rules()` tick loop
to resolve the intermediate `solve_deduction` sub-goals) plus a small,
pure, zero-mutation suitability pre-check — smaller in kind than either
prior `_from_text` rung's own new code, since no new construction/parser had
to be found or built. GO. Live-demonstrated on real Bigville-styled
statements, both the success path (a genuine, measured treewidth
discrimination reproducing `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain
test on independent statement text) and both honest-refusal shapes
(resolver-side wall on a too-tight bound; adapter-side decline that leaves
zero graph mutation on unsuitable input).

---

## 1. What building a candidate projection from graph nodes actually requires

Read directly off `domains/problem_decomposition.py:150-183`
(`project_deduction_shared_attr`/`project_deduction_complete`), confirmed
live before writing any new code (PREREG §1-2): a **fixed, mechanical
function of a node list**. Given `schema_nodes` (a plain list of
`ShapeSignature` NodeIDs), it reads each node's own `signature`/`supplies`
JSON via `_schema_attrs` (`problem_decomposition.py:124-147` — a mechanical
read of fields `propositional_deduction.py` itself already writes when it
mints a schema) and derives edges from shared antecedent/consequent attr
tokens. **It is node-TYPE-specific** (it expects `ShapeSignature{kind:
"knowledge_logical"}` nodes carrying those two JSON fields) **but not
caller- or statement-specific** — it never inspects how the nodes were
minted, only what they carry. `race_projections`'s own `Argmin`-over-
`min_fill_upper_bound` selection (unchanged, `problem_decomposition.py:
247-292`) is likewise a pure function of `(nodes, edges)` pairs, indifferent
to provenance.

This is the fact the task asked to characterise precisely, and it is
exactly as mechanical as hypothesised — see §3 for why the remaining cost
is a driver, not a parser.

## 2. `solve_deduction` was already NL-native — the load-bearing correction
   to the prior rungs' own ranking

`SOLVER_NL_ADAPTER_PREREG.md` ranked `solve_decompose` #3, "expensive, and
non-independent... its true cost is whichever of ranks 4-6 [the CAN-network
resolvers] below it draws candidates from." That framing assumed
`solve_decompose`'s cost is inherited from whichever upstream resolver
builds its candidates' underlying objects. But `mint_solve_deduction_goal`
(`domains/solver_dispatch.py:160-171`) — unlike `solve_reasoning_bridge`/
`solve_analogical_promote`/the three CAN resolvers — has taken a bare
`statement: str` since Rung 1: it was never one of the "graph object the
caller must have separately minted" prerequisites the original ranking table
enumerated. **Deduction-schema candidates therefore never actually
inherited rank 4-6's cost — they inherited rank 0's (a statement string),
because `solve_deduction` itself was already the cheapest of the seven
resolvers by construction.** The original ranking's mistake was scoping
`solve_decompose`'s cost to "whichever upstream object it projects over" in
the abstract, without checking that one of the three object types
(deduction schemas) was already reachable from text for free.

Live-confirmed before finalising the ranking (PREREG §2), real `WorldAdapter`
boot, `load_all_seeds`, `wire_question_faculty`, three genuine Bigville-
styled conditional statements (real Bigville CAN-topic vocabulary,
`world_safe` — the SAME tokenisation `SOLVER_NL_ADAPTER_RESULTS.md` §4.1
already demonstrated — plus ordinary "resident"/"mayor" nouns, deliberately
NOT the prior rung's own literal fish/mammal fixture text):

```
"If X is a resident, X can vote."          -> resolved, logical_resident_can_vote,   node #24392
"If X is a resident, X is world safe."     -> resolved, logical_resident_world_safe, node #24396
"If X is a mayor, X can govern."           -> resolved, logical_mayor_can_govern,     node #24404

schema_nodes = [#24392, #24396, #24404]
project_deduction_shared_attr -> edges=[(#24392,#24396)], edge_reason={(...): 'resident'}, treewidth=1
project_deduction_complete    -> edges=[3 edges, K3],                                        treewidth=2
```

Reproducing, on independent statement text, exactly the shape
`QUESTION_DRIVER_RUNG1_RESULTS.md`'s own hand-built chain test measured
(shared_attr treewidth=1 vs complete treewidth=2) — confirming this is not
an artefact of one hand-picked fixture triple.

## 3. So what genuinely new code did this rung need?

**A driver, not a parser — the one substantive new piece, and it is smaller
than either prior `_from_text` rung's own addition.** Every prior
`_from_text` adapter (`mint_solve_reasoning_bridge_goal_from_text`,
`mint_solve_analogical_promote_goal_from_text`) only ever MINTS a Goal and
returns it un-resolved, leaving pumping to the caller, because their own
prerequisite object never itself needed an already-resolved Goal along the
way. `solve_decompose`'s prerequisite is different in KIND: `mint_solve_
decompose_goal`'s own contract (`solver_dispatch.py:442-453`) stages
candidates in `solve_caps` EAGERLY, at mint time — so the candidate list
must be built from already-resolved `ShapeSignature` nodes before this
adapter can mint anything at all. There is no way to defer this the way the
two prior rungs deferred resolver dispatch to the caller.

The fix: drive each per-statement `solve_deduction` sub-goal to resolution
internally, via `_drive_to_resolution` — a same-shape, own-copy mirror of
`question_driver.py::_pump`'s own bounded tick loop (`domains/question_
driver.py:652`, production code already called by `QuestionDriver.drive()`,
not test-only) and `tests/test_solver_dispatch_migrated.py::_pump`'s
identical inline copy. This is the SAME already-existing Rust rule-engine
invocation (`native.run_rules()`) every other driver in this codebase
already performs — sequencing an existing loop, never a new Python decision
about what a goal's result means, and squarely inside the "Between ingest
and emit, call substrate.tick()" allowance CLAUDE.md's architecture rule
names explicitly.

## 4. Honest-decline discipline — a documented, deliberate departure from
   the prior two `_from_text` adapters, not silently glossed over

Both prior `_from_text` adapters guarantee **zero Goal nodes minted at all**
on any decline, because their own suitability checks are pure reads with no
graph mutation. `solve_decompose`'s own suitability signal — "does this
statement resolve to a real schema" — is `solve_deduction`'s OWN verdict,
knowable in general only by actually installing a node (via its `mint_*`
installer functions).

**Fix, confirmed to restore the SAME zero-mutation-on-TOTAL-decline
guarantee**: `_would_parse_as_deduction`, a pure pre-check calling ONLY
`parse_universal`/`parse_existential`/`parse_conditional` (never their
`mint_*` siblings) in the same fixed order `solve_deduction`'s own ladder
uses. Confirmed live and by direct read (PREREG §4) that all three delegate
to `reading_collapse.read_clause`/`decompose_sentence` with `write=False,
learn=False` throughout — no `add_node`/`mint_*` call is reachable from any
of the three. Only once ≥2 statements pass this pure pre-check does the
adapter mint or drive ANY sub-goal — so a **total** decline is a genuine,
zero-graph-mutation refusal, matching the prior two adapters' discipline
byte-for-byte (verified live, §5.3 below, via node-count equality before and
after).

**The honestly-documented departure**: a PARTIAL success (≥2 statements pass
the pre-check, their sub-goals then driven for real) DOES leave real,
inspectable `solve_deduction` Goal + `ShapeSignature` nodes for the
statements actually used — even a statement that is FILTERED OUT by the
pre-check because it's mixed in with usable ones never touches the graph
(live-verified, §5.4), but the usable ones necessarily do, because their
resolution IS the candidate data. This is the unavoidable cost of `solve_
decompose`'s prerequisite being an already-resolved node, not a bare
string — not an oversight, and not silently absorbed into a false "mints
nothing, ever" claim.

## 5. Live demonstration

### 5.1 Success — real statements, real race, real decomposition, verified
    by hand

```
statements: ["If X is a resident, X can vote.",
             "If X is a resident, X is world safe.",
             "If X is a mayor, X can govern."]
goal = mint_solve_decompose_goal_from_text(agent, statements, bound=1)

after dispatch through the UNCHANGED qd_bind_resolver -> solve_decompose:
  status: 'resolved'
  winner_projection: 'deduction_shared_attr'
  treewidth: 1.0
  resolve_with -> Resolver{name: 'solve_decompose'}
```

**Correctness verified by hand against the actual bags/parent structure**
`decompose_or_refuse` produced (mirroring the "verify the real output, not
just status" discipline both prior rungs used), not merely
`status=="resolved"`:

```
full['bags']:   {#24400: {#24400, #24404}, #24404: {#24404}, #24412: {#24412}}
full['parent']: {#24400: #24404, #24404: None, #24412: None}
race candidates: [{'name': 'deduction_shared_attr', 'treewidth': 1},
                  {'name': 'deduction_complete_overcoupled', 'treewidth': 2}]
```

3 bags over 3 real schema nodes, the `Argmin`-decided winner correctly
`deduction_shared_attr` (treewidth 1) over the deliberately-overcoupled
`deduction_complete_overcoupled` (treewidth 2, K₃) — the race did real,
measured discriminating work, not merely picking whichever candidate was
listed first. Also confirmed (`test_success_candidates_are_built_over_the_
real_resolved_schema_nodes`): the 3 `solve_deduction` sub-goals this adapter
itself minted carry the real schema names `logical_resident_can_vote`/
`logical_resident_world_safe`/`logical_mayor_can_govern` — the candidates
race real, inspectable nodes, not placeholder data.

### 5.2 Honest wall (resolver-side) — real candidates, genuinely too tight
    a bound

```
same 3 statements, bound=0 (shared_attr's own treewidth=1 exceeds it)
after dispatch: status: 'walled'
  wall_kind: 'treewidth_exceeds_bound'
  note: "treewidth 1 (exact) exceeds bound 0 -- refusing decomposition, not attempting it blindly"
  gap_key: 'solve_decompose:candidates=deduction_complete_overcoupled,deduction_shared_attr:bound=0'
full['attempted']: False
```

The UNMODIFIED `decompose_or_refuse`'s own honest-refusal path fires exactly
as it already does for a hand-built candidate list — this adapter's only
contribution is correctly building the candidates from real text and
letting the existing resolver decide. Rung 2's `note_solve_exhausted_gap`
gap-filing (unchanged) fires correctly on this wall (`gap_key` present and
content-specific).

### 5.3 Honest decline (adapter-side) — unsuitable input mints ZERO nodes,
    confirmed by node-count equality

```
[ "If X is a resident, X can vote." ]                     -> None  (only 1 statement)
[]                                                          -> None  (empty)
None / "not a list" / ["only one statement"]                -> None  (bad shapes)
statements=<3 real ones>, bound=None                        -> None  (missing bound)
[ "The mayor likes apples.", "Is the mayor trustworthy?" ]  -> None  (neither is deduction-shaped)
```

`(len(Goal nodes), len(ShapeSignature nodes))` measured identical
before/after every one of the above (`test_decline_too_few_statements_
mints_nothing`, `test_decline_non_deduction_statements_mints_nothing`,
`test_decline_bad_input_shapes_mints_nothing`) — the SAME "never mint
garbage from unsuitable input" discipline, and the SAME zero-mutation
guarantee, both prior `_from_text` adapters established.

### 5.4 Partial success — the honestly-documented departure, live

```
mixed = ["If X is a resident, X can vote.",
         "If X is a resident, X is world safe.",
         "The mayor likes apples."]     # NOT deduction-shaped
goal = mint_solve_decompose_goal_from_text(agent, mixed, bound=1)
-> not None; after pump: status='resolved', winner_projection='deduction_shared_attr'

Goal-node delta for this call: exactly 3 (2 solve_deduction sub-goals for
the 2 usable statements + 1 solve_decompose goal) -- the unsuitable third
statement was filtered by the pure pre-check and never reached mint_solve_
deduction_goal at all, confirmed by the exact delta count, not merely
"eventually resolved".
```

## 6. The old direct-mint path is unaffected

`mint_solve_decompose_goal(adapter, candidates, bound)` — the ORIGINAL,
hand-supplied-candidates entry point — still dispatches byte-identically
(`test_old_direct_mint_path_unaffected`, two hand-built schemas via `mint_
solve_deduction_goal` + `project_deduction_shared_attr`, called directly):
reaches `status in ('resolved','walled')`. The new function is a pure
ADDITION alongside it, never a replacement.

## 7. Regression

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py \
    tests/test_solver_math_boundary.py \
    tests/test_solver_nl_adapter.py \
    tests/test_solver_analogy_adapter.py \
    tests/test_problem_decomposition.py \
    tests/test_solver_decompose_adapter.py \
    -q -p no:randomly
84 passed in 122.31s
```

Extra sweep, the deduction/analogy facilities' own adjacent suites, run
fresh for extra confidence (matching both predecessor rungs' own practice):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_deduction_extension.py \
    tests/test_deduction_generalization.py \
    tests/test_quantified_deduction.py \
    tests/test_reasoning_facility_bridge.py \
    tests/test_situation_model_wire.py \
    tests/test_directional_correspondence.py \
    -q -p no:randomly
89 passed in 191.57s
```

**173/173 green across all fourteen suites, zero regressions, zero
waivers.**

```
$ git diff --stat 7017989 -- domains/solver_dispatch.py
 domains/solver_dispatch.py | 162 +++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 161 insertions(+), 1 deletion(-)

$ git diff 7017989 -- domains/solver_dispatch.py | grep '^-' | grep -v '^---'
-    "mint_solve_decompose_goal",
```

The single removed line is the `__all__` entry replaced by the two-entry
version (`mint_solve_decompose_goal`, `mint_solve_decompose_goal_from_text`)
— every existing function's body is byte-unchanged. No Rust touched; no
`cargo build` needed. No seed file was modified — the new Goal still
dispatches through the UNCHANGED `qd_bind_resolver` JOIN and the
already-installed `solve_decompose` Resolver (`seeds/solver_dispatch.json`,
untouched).

## 8. GO / NO-GO

**GO.** `solve_decompose` is now reachable from real natural-language
text via `mint_solve_decompose_goal_from_text`, scoped precisely to ONE
node-source type (deduction schemas from a list of ≥2 deduction-shaped
statements) — demonstrated live on genuine Bigville-styled sentences, both
the success path (correctness verified by hand against the real race/bags/
parent structure, reproducing `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own
measured discrimination on independent statement text) and both honest-
refusal shapes (a real resolver-side wall on a too-tight bound; five
adapter-side declines, all confirmed to leave zero graph mutation via exact
node-count equality). 173/173 regression tests green, fresh, across the
task-named suites plus an additional adjacent-facility sweep. The diff is
purely additive — `solve_decompose`'s own internals, `solve_deduction`'s own
internals, and `problem_decomposition.py` are all untouched.

**The prior rung's "expensive, non-independent" ranking for this resolver
does not hold up as stated.** `solve_decompose`'s TRUE dependency
(`solve_deduction`) was cheap from day one — the ranking's error was
treating "inherits whichever upstream object it projects over" as
necessarily expensive without checking that one of the three upstream
object types was already free. This is the SAME class of correction
`SOLVER_ANALOGY_ADAPTER_RESULTS.md` made for `solve_analogical_promote` (a
grep on the wrong vocabulary, there) — here the miss was scoping cost
inheritance to "the object type in the abstract" rather than checking each
of the three concrete object types this resolver's candidates can be built
from.

**Not merged, not pushed to `main`.** `main`'s tip was checked fresh
(`7017989`) immediately before creating this worktree and again at RESULTS
time (still `7017989`), and every commit (`819091a`, `518796c`) lives on the
`solver-decompose-adapter` branch only. This rung did not run any command
that touched `main` at any point. The orchestrator performs the merge.

---

## 9. What this document does NOT establish

1. **CAN-network candidates (`project_can_identity`/`project_can_complete`)
   have no NL path.** Unchanged finding from `SOLVER_NL_ADAPTER_PREREG.md`
   §2: no NL-to-CAN-network path exists anywhere in this codebase (the only
   builder, `bigville_can_beliefs.build_resident_can_mt`, is a mechanical
   translation of an already-drawn numeric `params` dict, not from text).
   Not attempted here, not silently assumed solved.
2. **Situation-model candidates (`project_situation_model_shared_event`)
   have no `solve_*`-wired NL path.** `situation_model_reader.py`'s own
   ingestion machinery exists but was never wired as a `solve_*` resolver
   prerequisite anywhere in this toolbox — characterising whether it is
   cheap or expensive to reach from text is a SEPARATE, unscoped
   investigation, named as a follow-on, not attempted here.
3. **The candidate race is fixed at exactly two candidates
   (`deduction_shared_attr`/`deduction_complete_overcoupled`)**, mirroring
   `QUESTION_DRIVER_RUNG1_RESULTS.md`'s own chain-test shape. A caller
   wanting a different candidate SET (more variants, or only one) needs the
   lower-level `mint_solve_deduction_goal`/`project_deduction_*`/`mint_solve_
   decompose_goal` primitives directly — this adapter does not expose a way
   to choose which projections to race.
4. **Only deduction-shaped statements are read.** Any statement shape
   `parse_conditional`/`parse_universal`/`parse_existential` do not already
   accept (e.g. a compound multi-fact statement, an indirect/reported
   belief) is silently filtered by the pure pre-check exactly as `solve_
   deduction` itself would honestly wall on it — this adapter inherits
   `solve_deduction`'s own scope boundary completely, does not extend it.
5. **The zero-mutation decline guarantee is TOTAL-decline-only, not
   per-statement.** §4/§5.4 document this explicitly: a partial success
   leaves real sub-goal nodes for the statements actually used. This is a
   genuine, measured difference from the prior two `_from_text` adapters'
   stronger "mints nothing on ANY decline" guarantee — reported here as an
   honest boundary, not glossed over as equivalent.
6. **`refine_projection`'s own bounded-iterative-refinement path
   (`refine_budget>0`) was not exercised live in this rung's own
   demonstration** — `mint_solve_decompose_goal_from_text` passes
   `refine_budget` straight through to `mint_solve_decompose_goal`
   unchanged (default 0, off), and this rung's own tests use the default.
   The refinement machinery itself is unedited and was already tested
   elsewhere (`tests/test_problem_decomposition.py`, part of this rung's own
   regression sweep, green).
7. **Synthetic-proven mechanism ≠ benchmark value, per house standard**:
   every number above is a mechanism demonstration (does the adapter
   correctly build real candidates / race them / decompose or wall on real
   statements), not a coverage/accuracy claim over how often real,
   naturally-occurring multi-statement decomposition problems would
   successfully parse and resolve via this scope.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/solver-decompose-adapter
git log --oneline -1 main   # 7017989 at branch time

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_solver_decompose_adapter.py -q -p no:randomly

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_solver_dispatch_migrated.py tests/test_solve_gap_awareness_migrated.py \
  tests/test_problem_shape_migrated.py tests/test_solver_math_boundary.py \
  tests/test_solver_nl_adapter.py tests/test_solver_analogy_adapter.py \
  tests/test_problem_decomposition.py tests/test_solver_decompose_adapter.py \
  -q -p no:randomly

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_deduction_extension.py tests/test_deduction_generalization.py \
  tests/test_quantified_deduction.py tests/test_reasoning_facility_bridge.py \
  tests/test_situation_model_wire.py tests/test_directional_correspondence.py \
  -q -p no:randomly
```
