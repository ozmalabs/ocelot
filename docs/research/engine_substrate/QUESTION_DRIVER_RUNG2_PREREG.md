# Question-driver solver dispatch — Rung 2 PREREG

Base `main @ 2b1661c` ("Merge progsyn-rung2-rung3: inputs_json symmetric
fix, MBPP 54->56 measured"), verified fresh via `git log --oneline -1 main`
immediately before creating the worktree (the task's own instruction: main
moved several times today, do not assume the number quoted in the prompt).
Worktree: `/home/matt/ozmadev/ocelot-worktrees/qd-solver-rung2`, branch
`qd-solver-rung2`. `data/` was absent (not a partial real directory) in the
fresh worktree; symlinked with `ln -sfn ... data` and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file.

This is **Rung 2** of
`docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`
(§6.2, "the gap-detection rule for stuck solves, small, low risk"), building
directly on **Rung 1** (already merged to `main`,
`docs/research/engine_substrate/QUESTION_DRIVER_RUNG1_RESULTS.md`): seven
`solve_*`-kind `Resolver`s (`seeds/solver_dispatch.json`,
`domains/solver_dispatch.py`) dispatch through the unchanged
`qd_bind_resolver` JOIN. This document does not redesign the rung — the
task's own instruction is to build precisely what the prereg's §4.3/§6.2
already specified, resolving any ambiguity against that document's own
cited precedent. It records the concrete design + the judgment calls made
resolving that ambiguity, BEFORE writing code.

---

## 1. The precedent being mirrored (read in full before writing this doc)

`seeds/gap_awareness.json`'s `note_unresolved_topic_gap`
(`gap_awareness.json:134-265`, `depends_on: ["intent"]`, currently at
v1.6.0, six gap-minting rules deep — `note_unresolved_topic_gap`,
`note_reported_gap`, `note_unhandled_instruction_gap`,
`note_self_account_gap`, `note_upload_reply_gap`, `note_upload_vision_gap`,
plus the self-retraction rule `retire_duplicate_gap`, all sharing ONE seed
file as the single growing home for "the agent finds its own gaps"): the
world adapter mechanically records a factual `outcome` on a Goal
(`_answer_topic_reply`, `substrate/world_adapter.py:3264-3275`,
`outcome:"resolved"|"unresolved"`, a datum never a decision, per that
method's own comment), and a Rule decides an `unresolved` `answer_topic`
Goal is a knowledge gap: files `SelfConcern{status:"noted", source:"implicit",
kind:"knowledge", content:<the topic>}`, guarded by (a) a `gap_noted`
mint-once marker and (b) a content-dedup `Not(Exists(...))` clause so the
SAME topic is never filed twice. Downstream is entirely unmodified:
`scripts/jabberwock_daemon.py::promote_self_concern` (`:2161-2231`) reads
`kind` generically (falls through to a `comprehend_first` default pipeline
for any kind it doesn't special-case, `_promote_relations_for_concern`
`:2051-2160` — confirmed by direct read, no `KeyError` risk for a new kind
string) and `domains/reflective_faculty.py::_run_self_gaps`
(`:358-420ish`) reads/groups every `SelfConcern` by `(source, kind,
content)` with zero kind-specific branching — a new `kind` value needs no
changes there either. `seeds/composer_dispatch.json` contains no `"kind"`
literal at all (grepped, zero hits) — it operates on `relations`/`content`,
not `SelfConcern.kind`.

## 2. Where the Rung-1 code already stands, re-read for this rung

Read the entire committed `domains/solver_dispatch.py` (506 lines) fresh.
**Every one of the seven resolvers already writes `status` to exactly
`"resolved"` or `"walled"` on every code path** — there is no silent
fall-through anywhere in the committed Rung-1 code (verified by tracing
every branch of all seven functions, not assumed). This matters for
resolving the task's own instruction ("find where it currently
returns/fails silently or just doesn't write a result, and add the
fact-recording write there") honestly: **the mechanical outcome fact this
rung's gap rule needs (`status=="walled"`) already exists**, written at
Rung 1's own construction time, at exactly the failure points the task's
own examples name (`parse_conditional` returning `None` → `solve_deduction`
walls; `decompose_or_refuse` returning `attempted:False` → `solve_decompose`
walls; a bridge finding no linkable entity → `solve_reasoning_bridge`
walls with `"deduction_to_can needs entity+attr"`; a treewidth-exceeding
CAN network → `solve_can_exact` walls with `wall_kind:
"treewidth_exceeds_bound"`). This is also exactly what the Rung-1 prereg's
own §4.3 already names as the trigger: *"a NEW rule... decides that a
solve_* goal whose status=='walled'... is a capability gap."* **Judgment
call #1**, resolved in favour of the prereg's own explicit wording over the
task's more general phrasing: the gap rule's trigger predicate is
`goal.kind in {the 7 solve_* kinds} AND goal.status == "walled"` — no new
`outcome` attr duplicating what `status` already carries.

What the committed code does **not** yet carry is a stable, differentiating
**dedup key**. `note_unresolved_topic_gap` dedups on `g.concept` — a
human-legible identifier of the TOPIC that was unresolved, distinct per
topic. No `solve_*` Goal carries an equivalent field today: `raw` is a
literal constant per kind for six of the seven mint helpers (e.g. every
`solve_can_relax` Goal's `raw` is literally the string `"solve_can_relax"`,
`mint_solve_can_relax_goal`, `solver_dispatch.py:128` — not a
differentiator), and `note` is a description of the OUTCOME (why it
failed), not a stable identifier of WHAT was attempted (two structurally
different intractable CAN networks could plausibly produce the same
generic `note` text). **Judgment call #2**: add a `gap_key` attr, written
by each resolver AT ITS OWN WALL SITE (never at mint time, never at the
resolved path — it exists only where a gap could ever be filed), built
from data already local to that wall branch (the statement text, the
targeted Microtheory/DirectionalCorrespondence node id, the direction, the
candidate/bound). This is the "SAME mechanical outcome-recording... at its
own point of failure" the task asks for, applied to the one piece of
information Rung 1 didn't already write: a stable identity for the
attempt, not a duplicate of the already-written status/note.

## 3. The new rule

`note_solve_exhausted_gap`, added to `seeds/gap_awareness.json` (bumped to
v1.7.0, `depends_on` gains `"solver_dispatch"` — an honest new dependency,
since the rule's `In(g.kind, [...])` list is solver_dispatch's own
vocabulary, not gap_awareness's; the seven kind literals are frozen strings
mirrored from `domains/solver_dispatch.py::SOLVE_RESOLVER_FUNCTIONS`, not
re-derived at runtime — a rule body cannot import Python). Kept in the SAME
seed file as the other six gap rules rather than a new file, matching the
established one-file-per-capability (not one-file-per-gap-kind) precedent
this seed already follows across six unrelated gap surfaces.

Shape, mirrored field-for-field from `note_unresolved_topic_gap`:

```
match:  agent -has_goal-> g
where:  In(g.kind, [solve_deduction, solve_can_relax, solve_can_exact,
                     solve_can_bp, solve_reasoning_bridge,
                     solve_analogical_promote, solve_decompose])
        AND Eq(g.status, "walled")
        AND Not(Eq(g.gap_noted, 1.0))
        AND Not(Exists SelfConcern sc2 where sc2.content == g.gap_key)
effects: set_attr(g, gap_noted, 1.0)
         add_node SelfConcern{status:"noted", source:"implicit",
                               kind:"solve_failure", content: g.gap_key}
         add_edge(agent, has_self_concern, sc)
         add_edge(sc, about_goal, g)
```

**Judgment call #3 — the `kind` string.** Neither the prereg (`"solving_
exhausted"`, illustrative) nor the task ("`kind:"solve_failure"` (or
whatever kind-naming the existing gap_awareness taxonomy suggests on
inspection)") commits to one literal. Existing kinds
(`knowledge`, `reported`, `instruction`, `self_account`, `reply_fix`,
`self_improvement` — enumerated by direct read of every `add_node(...,
"SelfConcern", ...)` call across `gap_awareness.json` +
`conversation_self_concern.json`) are all named after the SHAPE of the
gap, not the surface that found it, so `solve_failure` fits that
convention directly (parallel to `knowledge` for an unresolved topic) and
is disjoint from every existing value. Chosen: `kind:"solve_failure"` —
the task's own literal, which is also the more precise of the two
candidates (the gap is that a solve ATTEMPT failed, not that "solving" as
a general capability is "exhausted").

## 4. What is explicitly out of scope (unchanged from the Rung-1 prereg)

- The `ProblemShape` recognizer (Rung 3) — not touched.
- Anything that decides to MINT a new `solve_*` Goal in the first place —
  out of scope per the task's own instruction; this rung only reacts to an
  already-dispatched Goal's failure.
- No change to `qd_bind_resolver`, `_question_pursue_advance`, `_pump`, or
  any of the seven resolvers' SUCCESS-path behaviour (only their wall
  branches gain one new attr write each).
- No change to `promote_self_concern`, `_run_self_gaps`, or
  `composer_dispatch.json` — verified by direct read (§1 above) that none
  require it, not assumed from the Rung-1 prereg's own claim.

## 5. Live demonstration plan (pre-registered before building)

1. **Three real, structurally different failure cases**, each filing
   exactly one `SelfConcern{kind:"solve_failure"}`:
   - `solve_deduction` on an unparsable statement (`parse_conditional`/
     `parse_universal`/`parse_existential` all return a `None`/failure
     residual).
   - `solve_can_exact` on a real CAN network with a treewidth bound set
     below its real treewidth (a genuine tractability wall, not a
     contrived input — mirrors Rung 1's own `wall_kind:
     "treewidth_exceeds_bound"` path).
   - `solve_decompose` racing candidates that all exceed the supplied
     bound (a genuinely intractable decomposition attempt).
2. **One success case that must NOT file a gap** — a `solve_deduction` (or
   any resolved kind) Goal that resolves normally; assert zero new
   `SelfConcern{kind:"solve_failure"}` nodes appear.
3. **Dedup** — the identical failing case (same kind, same input) run
   twice mints exactly one `SelfConcern`, not two.

All four use the SAME `WorldAdapter` + `load_all_seeds` + `wire_question_
faculty` boot shape `test_solver_dispatch_migrated.py::agent` already
established (module-scoped, real toolbox calls, no stubs).

## 6. Regression plan

`tests/test_solver_dispatch_migrated.py`,
`tests/test_gap_awareness_migrated.py`,
`tests/test_self_gaps_surfacing_migrated.py`, plus a new
`tests/test_solve_gap_awareness_migrated.py` covering §5. All expected
green; any regression gets a paired failing-node-id list in the RESULTS
doc, per house discipline.
