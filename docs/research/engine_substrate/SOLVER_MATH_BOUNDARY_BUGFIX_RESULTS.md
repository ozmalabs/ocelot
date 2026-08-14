# Fixing the two solve_deduction defects `SOLVER_MATH_BOUNDARY_RESULTS.md` diagnosed — RESULTS

Base `main @ a3a1899` ("Merge solver-math-boundary: real math problem battery
maps the toolbox's edges"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-math-boundary-bugfix`, branch
`solver-math-boundary-bugfix`, commits `2b00e39` (Bug 1) + `3a65ea3` (Bug 2).
`data/` was absent in the fresh worktree (not a partial real directory);
symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file.

This document reports two narrow, precisely-scoped fixes to the two real
silent-wrong/silent-degraded defects `SOLVER_MATH_BOUNDARY_RESULTS.md`
diagnosed and pinned as regression tests but explicitly did not fix (that
task's own scope was diagnostic/mapping only). No new solver capability is
built here — both fixes correct existing, already-diagnosed behaviour inside
`domains/propositional_deduction.py` / `domains/solver_dispatch.py`.

**No new PREREG was written for this task** — both bugs were already
precisely diagnosed in `SOLVER_MATH_BOUNDARY_RESULTS.md` §5/§6, and the task
instructing this rung explicitly said so.

---

## 0. Corrected framing (a factual correction to the earlier boundary-map
   doc's own language, not new work)

`SOLVER_MATH_BOUNDARY_RESULTS.md` (and this task's own original framing, in
places) described the fact that six of the seven `solve_*` resolvers "require
a caller to have already built the prerequisite graph object by hand" as if
it might be read as a capability *wall*. It is not. **It is a wiring gap, not
a wall**: none of `solve_can_relax`/`solve_can_exact`/`solve_can_bp`/
`solve_reasoning_bridge`/`solve_analogical_promote`/`solve_decompose` rejects
natural-language input for any principled semantic reason — no NL-to-CAN-
network, NL-to-`DirectionalCorrespondence`, or NL-to-candidate-projection
adapter has been written yet, the same step `solve_deduction` already has via
`parse_conditional`/`parse_universal`/`parse_existential`. Building those six
missing adapters is a real, separate, sizeable follow-on. **It is explicitly
OUT OF SCOPE for this task** and nothing toward it was built here — this
section only corrects the earlier document's phrasing so a future reader does
not mistake "no adapter written yet" for "cannot be reached from text."

---

## 1. Bug 1 — `solve_deduction` fabricated a spurious implication from
   non-conditional (question-shaped) input

### 1.1 Exact root cause, traced live before writing any fix

`parse_conditional`'s `bare_universal` branch
(`domains/propositional_deduction.py:213-223`, pre-fix) reads the WHOLE
statement as one turn:

```python
else:
    form = "bare_universal"
    whole = rc.read_clause(agent, statement, write=False, learn=False)
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    pair = _relation_and_attr(preds[0])
    if pair is None:
        return None
    antecedent_attr = _norm_attr(preds[0][1])
    consequent_relation, cons_tail = pair
```

The only gate on `preds[0]` is `_relation_and_attr` — it checks the
predication's **relation label** (`is_a` → property, `can` → capability) and
nothing else. It never inspects the general reader's own `speech_act`
verdict, which `read_clause` already computes and returns
(`domains/reading_collapse.py:1646`, `out["speech_act"] = "question" if
ends_q else "statement"`, further refined by the winning construction's own
`ground_template`).

Traced live, both the tokenization path AND the exact grounding for
`"What is 17 * 23?"`:

```
$ python3 -c "... rc.read_clause(a, 'What is 17 * 23?', write=False, learn=False) ..."
speech_act: question   construction: wh_question   preds: [['is_a', '17', '23']]
```

`"What is 17 * 23?"` decodes to the `wh_question` construction
(`_ground_question`, `domains/reading_collapse.py:1297-1331`). Its residual
span after the inverted-auxiliary split is `"17 * 23"`; `_find_main_verb`
finds no verb in `["17", "*", "23"]`, so `_ground_question`'s own honest
fallback (lines 1318-1321) fires: `subject = _arg_head(toks[0])` ("17"),
`predicate = "is_a"`, `obj_head = _arg_head(" ".join(toks[1:]))` ("23", `*`
dropped by the head-cleaning). **This fallback is CORRECT behaviour for
`_ground_question`** — it is the honest, general reading of a genuine copular
wh-question with no resolvable main verb (e.g. "What is a mammal?"). The bug
is entirely on the `parse_conditional` side: it has no gate at all
distinguishing "this is a QUESTION whose grounding happens to use the
`is_a` label" from "this is a DECLARATIVE bare-universal STATEMENT" — a
conditional/universal *premise* is, by definition, an assertion, never a
question, and `parse_conditional` never checked for that. This is exactly
the missing "is this even a conditional/universal SHAPE" gate the task asked
to characterize precisely: **a too-permissive fallback with no upstream
shape gate**, not a parser that is merely too loose about arithmetic symbols
specifically — the same defect fires on any question-shaped input, verified
on three structurally different examples (§1.3).

A live, load-bearing wrinkle found and traced (not left mysterious): calling
`rc.decompose_sentence(agent, statement)` first (which `parse_conditional`
always does, unconditionally, to decide the multi-clause split) mutates
persistent codebook/lexicon state such that a bare stand-alone
`read_clause(agent, "What is 17 * 23?", write=False, learn=False)` call on a
FRESH agent (no prior `decompose_sentence` call) grounds via the
`definitional` construction instead (`skeleton=[['COP']]`, subject `"what"`,
not the `wh_question` skeleton) — but produces the identical class of bug
either way: `preds = [['is_a', 'what', '17_*_23']]`, still an `is_a`
predication that `_relation_and_attr` still accepts, still with
`speech_act == "question"` (from the same `ends_q` initialization the
question mark alone sets, since neither construction's own template
overrides `speech_act` away from `"question"`). **This confirms the fix
target is the speech-act gate, not "which construction happens to win" —
both code paths a fresh vs. `decompose_sentence`-warmed agent take share the
identical `speech_act == "question"` signature**, which is exactly why the
fix below closes both variants with one check.

### 1.2 The fix

`domains/propositional_deduction.py:213-244` (the `bare_universal` branch of
`parse_conditional`), one new gate immediately after computing `whole`:

```python
whole = rc.read_clause(agent, statement, write=False, learn=False)
if whole.get("speech_act") == "question":
    # The honest residual: a QUESTION has no declarative antecedent/
    # consequent to hold, no matter what relation label its own
    # grounding happens to produce (see the docstring section above).
    return None
```

Scoped deliberately to the `bare_universal` branch only. The
`conditional_split` branch (`domains/propositional_deduction.py:198-212`)
reads CLAUSE FRAGMENTS — `rc.read_clause(agent, clauses[0], ...)` where
`clauses[0]` is a **list**, not a string — so `is_turn` is `False` there
(`reading_collapse.py:1624`), the turn-level `WH`/`AUXINV` question skeleton
is never even reachable (`_skeleton_from_words`'s own `speech_turn` gate),
and `"If X is a fish, X can swim."` is structurally unaffected by
construction, not merely spared by this new check.

### 1.3 Live demonstration

```
$ python3 -c "... pd.parse_conditional(a, s) for each s ..."
'What is 17 * 23?'                                                            -> None
'A rectangular garden is 5m by 3m. If you increase both sides by 2m, what     -> None
  is the new area?'
'All men are mortal. Socrates is a man. Is Socrates mortal?'                  -> None
'If X is a fish, X can swim.'   -> {'antecedent_attr': 'fish', 'consequent_relation': 'can', ...}
'A bird can fly.'               -> {'antecedent_attr': 'bird', 'consequent_relation': 'can', ...}
```

Through the full dispatch (`solve_deduction`, `mode="auto"`):

```
What is 17 * 23?                                                  -> walled  (no schema)
A rectangular garden is 5m by 3m. ... what is the new area?       -> walled  (no schema)
All men are mortal. Socrates is a man. Is Socrates mortal?        -> walled  (no schema)
If X is a fish, X can swim.        -> resolved  logical_fish_can_swim
A bird can fly.                    -> resolved  logical_bird_can_fly
```

Wall note for the arithmetic case (read straight off the goal, not
paraphrased): `"'What is 17 * 23?' does not parse as an existential premise
(no recognised leading existential quantifier, or the remainder does not
ground via parse_conditional) -- the NAMED residual"` — the honest ladder
exhaustion message, matching the shape every other clean wall in the battery
(arithmetic/algebra/search/permutation) already produces.

**All three of the battery's silently-wrong pins share this exact root
cause, not just the arithmetic case the task named explicitly** — all three
end in `?`. `test_geometry_word_problem_...` and
`test_two_premise_syllogism_...` were also flipped by this one gate (see
§1.5); this is reported as a finding, not scope creep — the fix is one
gate, and its correct blast radius genuinely covers all three.

### 1.4 Regression proof this does not weaken genuine conditional/universal
   parsing

```
$ python3 -m pytest tests/test_solver_math_boundary.py -q
18 passed in 20.62s      # (before Bug 2's fix; the two ladder-order pins still asserted the OLD ladder behaviour, correctly)
```

`test_single_conditional_resolves_correctly` (`If X is a fish, X can
swim.` → `logical_fish_can_swim`) and `test_bare_universal_resolves_correctly`
(`A bird can fly.` → `logical_bird_can_fly`) pass **byte-identical** — same
schema name, same `chain` text, confirmed by direct re-run before and after
the edit. Neither statement's `speech_act` is `"question"`
(`ends_q` requires a literal trailing `?`, neither statement has one), so
neither takes the new early-return path at all — the gate is inert for them,
not merely non-blocking.

### 1.5 Tests updated (not just the one the task named)

`tests/test_solver_math_boundary.py`:

- `test_arithmetic_expression_resolves_WRONGLY_instead_of_walling` →
  **renamed** `test_arithmetic_expression_now_walls_honestly`, asserts
  `status == "walled"`, `gap_key == "solve_deduction:What is 17 * 23?"`,
  `schema_name is None`.
- `test_geometry_word_problem_resolves_WRONGLY_instead_of_walling` →
  **renamed** `test_geometry_word_problem_now_walls_honestly`, asserts
  `status == "walled"`, `schema_name is None`. (Flipped by the same gate;
  the task named only the arithmetic case, but leaving this one asserting
  the old, now-false "resolves wrongly" behaviour would have re-broken the
  suite the moment the gate landed, so it is updated here too.)
- `test_two_premise_syllogism_resolves_but_never_answers_the_query` →
  **renamed** `test_two_premise_syllogism_now_walls_honestly`, asserts
  `status == "walled"`, `schema_name is None`; docstring updated to record
  that `solve_deduction` still has no query-answering step at all (that
  boundary, `SOLVER_MATH_BOUNDARY_RESULTS.md` §5, is unchanged by this
  fix — the fix only stops the fabrication, it does not add application/
  query-answering).

---

## 2. Bug 2 — `mode="auto"` never reached the quantifier-stripping parsers

### 2.1 Exact root cause

`domains/solver_dispatch.py::solve_deduction` (pre-fix,
`domains/solver_dispatch.py:274-280`):

```python
ladder = {
    "conditional": [("conditional", pd.mint_logical_schema)],
    "universal": [("universal", pd.mint_universal_schema)],
    "existential": [("existential", pd.mint_existential_premise)],
}.get(mode, [("conditional", pd.mint_logical_schema),
             ("universal", pd.mint_universal_schema),
             ("existential", pd.mint_existential_premise)])
```

`mode="auto"` (the default) tried `mint_logical_schema` (the plain
conditional/bare-universal parser, which does NOT strip a leading quantifier
word) FIRST. `"All philosophers are mortal."`/`"Some bird is a penguin."` are
also grammatically valid bare-universal clauses on their own (subject = `"all
philosophers"`/`"some bird"`, verbatim — the same shape
`mint_logical_schema`'s own bare_universal path already grounds), so
`mint_logical_schema` ALWAYS succeeded first on a leading-quantifier
sentence, and `solve_deduction`'s loop keeps the first success
(`domains/solver_dispatch.py:284`, unchanged by either fix). The dedicated,
quantifier-stripping parsers (`mint_universal_schema`/
`mint_existential_premise`, from `propositional_deduction.py`) were
therefore **never reached** under `mode="auto"`, even though they exist,
work correctly, and produce a strictly better-quality schema — confirmed
live by direct A/B on the identical statement (§2.3).

### 2.2 The fix

Reorder the `mode="auto"` ladder to try the quantifier-aware parsers FIRST:
`universal → existential → conditional`
(`domains/solver_dispatch.py:306-311`):

```python
}.get(mode, [("universal", pd.mint_universal_schema),
             ("existential", pd.mint_existential_premise),
             ("conditional", pd.mint_logical_schema)])
```

This is not a reordering gamble weighed against risk — it is **provably
safe for every non-quantified statement**, traced directly in
`propositional_deduction.py`: `mint_universal_schema`/
`mint_existential_premise` both delegate immediately to
`_split_leading_quantifier` (`propositional_deduction.py:494-516`), which
returns the honest `None` residual in O(1) — one lowercase comparison of the
statement's FIRST WORD against the held `QuantifierLexicon`
(`universal: all/every/each`, `existential: some`) — **before any
reading-pipeline call at all** — whenever the statement has no recognised
leading quantifier word. `"a"`/`"an"` are deliberately NOT lexicon members
(`_split_leading_quantifier`'s own docstring), so an indefinite
bare-universal (`"A bird can fly."`) and an ordinary conditional (`"If X is
a fish, X can swim."`) both refuse BOTH quantifier-aware parsers immediately
and fall straight through to the unchanged `mint_logical_schema` — same
function, same input, same result, byte-identical schema, confirmed live
(§2.3).

### 2.3 Live demonstration

```
mode  statement                          -> status    schema_name                              form_used
auto  All philosophers are mortal.       -> resolved  logical_universal_philosopher_mortal      universal
universal All philosophers are mortal.   -> resolved  logical_universal_philosopher_mortal      universal
auto  Some bird is a penguin.            -> resolved  existential_bird_penguin                  existential
existential Some bird is a penguin.      -> resolved  existential_bird_penguin                  existential
auto  If X is a fish, X can swim.        -> resolved  logical_fish_can_swim                     conditional
auto  A bird can fly.                    -> resolved  logical_bird_can_fly                      conditional
```

`mode="auto"` on `"All philosophers are mortal."` now produces the EXACT
schema (`logical_universal_philosopher_mortal`, singularised antecedent,
`form_used="universal"`) that an explicit `mode="universal"` call produces —
parity, verified by direct A/B, not asserted. Before this fix it produced
`logical_all_philosophers_mortal` (the unstripped blob, `form_used`
unrecorded — the old ladder never wrote `form_used` differently per branch,
it was always `"conditional"` in that case). The plain conditional
(`"If X is a fish, X can swim."`) and indefinite bare-universal (`"A bird
can fly."`) resolve via `form_used="conditional"` exactly as before the
reorder.

### 2.4 Regression proof genuine non-quantified dispatch is unchanged

`test_auto_mode_leaves_a_plain_conditional_unchanged` (new pin, added
alongside the ladder-order fix): `mode="auto"` on `"If X is a fish, X can
swim."` asserts `schema_name == "logical_fish_can_swim"` AND
`form_used == "conditional"` — both fields, not just the outcome status, so
a future change that silently altered which branch of the ladder fired
would be caught even if it happened to produce the same schema name by
coincidence.

### 2.5 Tests updated

`tests/test_solver_math_boundary.py`:

- `test_auto_mode_does_not_strip_leading_universal_quantifier` → **renamed**
  `test_auto_mode_now_strips_leading_universal_quantifier`, asserts
  `schema_name == "logical_universal_philosopher_mortal"` (was
  `logical_all_philosophers_mortal`) and the new `form_used == "universal"`
  check.
- `test_explicit_universal_mode_DOES_strip_the_quantifier` — unchanged
  (explicit mode already bypassed the ladder; still asserts the same
  schema).
- `test_auto_mode_leaves_a_plain_conditional_unchanged` — new pin, §2.4.

---

## 3. Full regression

Fresh baseline verified per house discipline: `git log --oneline -1 main`
== `a3a1899` (re-checked immediately before creating this worktree);
worktree created via `git worktree add --detach
/home/matt/ozmadev/ocelot-worktrees/solver-math-boundary-bugfix a3a1899`;
`data/` confirmed absent (not a pre-existing partial real directory) before
`ln -sfn`, then confirmed with `ls -la data/wiktionary/en.jsonl.gz` (present,
492,560,156 bytes).

```
$ python3 -m pytest \
    tests/test_solver_math_boundary.py \
    tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py \
    tests/test_deduction_generalization.py \
    tests/test_deduction_extension.py \
    tests/test_quantified_deduction.py \
    -q
100 passed in 76.51s (0:01:16)
```

**100/100 green — zero regressions, zero pre-existing-red waivers needed.**
This is deduction's own full named test population (per the task's own
regression list), run fresh against the post-both-fixes worktree tip
(`3a65ea3`), not inferred from `results/failure_baseline.json` or any other
historical record. No paired failing-node-id list is needed — nothing
regressed.

`git diff --stat a3a1899 HEAD`:

```
domains/propositional_deduction.py |  32 ++++++++-
domains/solver_dispatch.py         |  52 +++++++++++---
tests/test_solver_math_boundary.py | 140 ++++++++++++++++++++++++-------------
3 files changed, 165 insertions(+), 59 deletions(-)
```

Nothing else in the tree was touched. No Rust was touched; no `cargo build`
was needed. No seed file was modified — both fixes are pure Python-adapter
logic (a shape gate inside `parse_conditional`, a ladder-order literal
inside `solve_deduction`'s dispatch), consistent with CLAUDE.md's "mechanical
translator, no agent decision" discipline: neither fix adds a NEW decision —
Bug 1's gate reads a verdict the general reader ALREADY computed
(`speech_act`) and only refuses on it (never overrides what the reader
decided); Bug 2's reorder does not change WHAT any parser decides, only the
FIXED, inspectable ORDER a caller-supplied `mode="auto"` iterates existing,
independent parsers in — the same "fixed adapter ladder, not a semantic
decision" characterization `QUESTION_DRIVER_RUNG1_RESULTS.md` §4.5 already
gave this exact ladder.

---

## 4. GO / NO-GO

**GO.** Both bugs are fixed, narrowly and precisely:

- Bug 1: one gate (`whole.get("speech_act") == "question"`) inside
  `parse_conditional`'s `bare_universal` branch, scoped to exactly the
  branch where the defect lived; the `conditional_split` branch is
  structurally unreachable by this defect class and untouched.
- Bug 2: a three-element list literal reorder inside `solve_deduction`'s
  `mode="auto"` ladder, provably safe for non-quantified input because the
  quantifier-aware parsers' own O(1) refusal path was already the correct
  no-op for that case.

Both fixes are demonstrated live (§1.3, §2.3) against the real toolbox (no
stubs), both are proven non-destructive to genuine conditional/universal
parsing by direct A/B (§1.4, §2.4), and the full named regression suite is
100/100 green, verified fresh on this exact commit.

**Not merged, not pushed to `main`.** This rung did not run any command that
touched `main` at any point — `main`'s tip was checked fresh
(`a3a1899`) immediately before creating this worktree, and every commit
(`2b00e39`, `3a65ea3`) lives on the `solver-math-boundary-bugfix` branch
only. The orchestrator performs the merge.

---

## 5. What this document does NOT establish

1. **The six other `solve_*` resolvers still have no NL adapter.** §0
   corrects the framing (wiring gap, not a wall) but builds nothing toward
   closing it — explicitly out of scope for this task, per the task's own
   instruction.
2. **`solve_deduction` still has no second-fact ingestion or query-answering
   step.** Bug 1's fix stops the two- and three-sentence word-problem/
   syllogism cases from fabricating a wrong-shaped answer; it does not add
   the capability (`inference_generation.py`'s `detect_implication_gaps`/
   `resolve_implication_gap`) to actually apply a premise to a fact or
   answer a query — that capability boundary,
   `SOLVER_MATH_BOUNDARY_RESULTS.md` §5's own verdict, is completely
   unchanged by this rung.
3. **Arithmetic/algebra/search/permutation problems still have no home in
   this toolbox.** They walled cleanly before this rung and wall cleanly
   after it, for the unrelated, already-correctly-diagnosed reason
   (`SOLVER_MATH_BOUNDARY_RESULTS.md` §8: no arithmetic/algebra bridge
   exists anywhere in the codebase) — Bug 1's fix only stops the SPECIFIC
   silent-wrong failure mode (a question-shaped statement grounding an
   accidental `is_a`, not the general absence of arithmetic evaluation).
4. **The `decompose_sentence`-mutates-subsequent-`read_clause` wrinkle
   named in §1.1** (a fresh vs. `decompose_sentence`-warmed agent grounds
   `"What is 17 * 23?"` via a different construction, `definitional` vs.
   `wh_question`) is reported here as context for why the fix targets
   `speech_act` rather than construction name, but is not itself
   investigated or fixed — both variants share the same `speech_act`
   signature, so the fix closes both without needing to understand or
   change that state-mutation behaviour, which remains exactly as it was.
5. **No new PREREG, no new battery.** This is a bugfix rung against
   already-diagnosed, already-pinned defects — no new problem population was
   run, no new capability boundary was mapped.
