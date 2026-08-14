# Question-driver solver dispatch — Rung 2 RESULTS

Base `main @ 2b1661c` ("Merge progsyn-rung2-rung3: inputs_json symmetric
fix, MBPP 54->56 measured"), verified fresh via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/qd-solver-rung2`, branch
`qd-solver-rung2`, commit `5feaae0`. `data/` was absent (not a partial real
directory) in the fresh worktree; symlinked (`ln -sfn ... data`) and
confirmed `data/wiktionary/en.jsonl.gz` resolves to the real
492,560,156-byte file — the documented gotcha, checked directly.

This document reports what was BUILT against the already-reviewed
`docs/research/engine_substrate/QUESTION_DRIVER_RUNG2_PREREG.md` (which in
turn implements §4.3/§6.2 of
`docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`)
— it does not re-derive the design; see the PREREG for the investigation
and the reasoning behind every judgment call this document only reports the
outcome of.

**Headline:** every one of the seven Rung-1 `solve_*` resolvers
(`domains/solver_dispatch.py`) already wrote `status:"walled"` at every
honest-failure point — the mechanical outcome fact this rung needed
already existed. Rung 2's entire diff is: (1) one new datum per wall site
(`gap_key`, via a new `_wall` helper), (2) one new graph rule
(`note_solve_exhausted_gap`, `seeds/gap_awareness.json` v1.7.0) that reads
`status=="walled"` + the seven `solve_*` kinds and DECIDES a capability gap
should be filed, and (3) a new test file demonstrating it live. Zero
changes to `qd_bind_resolver`, `_question_pursue_advance`,
`promote_self_concern`, `_run_self_gaps`, or `composer_dispatch.json` —
verified by direct read (below), not assumed.

---

## 1. What was built

### 1.1 `domains/solver_dispatch.py` — `_wall` helper + seven call sites

A new module-level helper (`_wall(sub, goal_node, gap_key, note, **extra)`,
`solver_dispatch.py:88-102`) wraps the exact two-attr write
(`status:"walled"` + `note`) every Rung-1 wall branch already made, adding
ONE new attr: `gap_key`, a stable per-attempt identity built from data
already local to that call site. Every wall branch in all seven resolvers
now calls it instead of the two bare `set_attr` calls:

| resolver | wall site(s) | `gap_key` shape |
|---|---|---|
| `solve_deduction` | ladder exhausted | `"solve_deduction:<statement>"` |
| `solve_can_relax` | no `targets_mt` | `"solve_can_relax:no_targets_mt"` |
| `solve_can_exact` | no `targets_mt` / treewidth exceeds bound | `"solve_can_exact:no_targets_mt"` / `"solve_can_exact:mt=<id>:tw=<treewidth>"` |
| `solve_can_bp` | no `targets_mt` | `"solve_can_bp:no_targets_mt"` |
| `solve_reasoning_bridge` | missing entity/attr / not applied / no `targets_mt` / bad direction | `"solve_reasoning_bridge:deduction_to_can:missing_entity_attr"` / `":<entity>:<attr>"` / `":can_to_deduction:no_targets_mt"` / `":bad_direction:<direction>"` |
| `solve_analogical_promote` | no `targets_correspondence` / not minted | `"solve_analogical_promote:no_targets_correspondence"` / `":corr=<id>"` |
| `solve_decompose` | no candidates / no bound / treewidth exceeds bound | `"solve_decompose:no_candidates"` / `":no_bound"` / `":candidates=<sorted names>:bound=<n>"` |

No resolver's SUCCESS path changed — verified by direct read of the final
file (every `sub.set_attr(goal_node, "status", "resolved")` call site is
byte-unchanged from Rung 1).

### 1.2 `seeds/gap_awareness.json` v1.6.0 → v1.7.0

Bumped `depends_on` from `["intent"]` to `["intent", "solver_dispatch"]`
(an honest new dependency: the rule's kind-membership list is
`solver_dispatch`'s own vocabulary). Added `note_solve_exhausted_gap`,
field-for-field the same shape as `note_unresolved_topic_gap`
(`gap_awareness.json:134-265`):

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

`retire_duplicate_gap` (the existing self-retraction rule, unmodified)
already scopes to `source in {implicit, explicit_report}` — the new
`solve_failure` gaps (`source:"implicit"`) fall under its dedup/retraction
umbrella for free, no changes needed there either.

### 1.3 Downstream verified unmodified, by direct read (not assumed)

- `scripts/jabberwock_daemon.py::promote_self_concern` (`:2161-2231`) reads
  `kind` generically; `_promote_relations_for_concern` (`:2051-2160`) has
  no branch for `"solve_failure"`, so it falls through to the
  `want_experiment=False` default path (`comprehend_first` pipeline,
  `:2158-2160`) — traced through the function body, no `KeyError`, no
  special-case needed.
- `domains/reflective_faculty.py::_run_self_gaps` (`:358-420`) groups every
  `SelfConcern` by `(source, kind, content)` with zero kind-specific
  branching (`_GAP_SOURCE_ORDER`/`_GAP_SOURCE_PHRASE` key on `source`, not
  `kind`) — a new `kind` value needs no changes.
- `seeds/composer_dispatch.json` — grepped fresh, zero `"kind"` literal
  hits; it operates on `relations`/`content`, never `SelfConcern.kind`.

## 2. Live demonstration

All in `tests/test_solve_gap_awareness_migrated.py` (5 tests, real toolbox
calls throughout, no stubs), against the same module-scoped
`WorldAdapter(seeds=()) + load_all_seeds + wire_question_faculty` boot
`test_solver_dispatch_migrated.py::agent` established.

### 2.1 Three structurally different real failures, each files exactly one gap

- **`test_solve_deduction_failure_files_a_solve_failure_gap`** — statement
  `"purple elephants dream sideways rung2"` walls (`parse_conditional`/
  `parse_universal`/`parse_existential` all return their honest `None`
  residual); asserts `gap_key == "solve_deduction:<statement>"`,
  `gap_noted == 1.0`, exactly one `SelfConcern{kind:"solve_failure",
  content:<gap_key>}` exists, `source=="implicit"`, `status=="noted"`, and
  the edge shape (`agent -has_self_concern-> sc -about_goal-> g`) matches
  `note_unresolved_topic_gap`'s own precedent exactly.
- **`test_solve_can_exact_failure_files_a_solve_failure_gap`** — a REAL
  Bigville resident CAN belief network (real treewidth ≈2) dispatched
  through `solve_can_exact` with `treewidth_bound=1` (a genuinely too-tight
  bound, not a contrived non-network input): walls with
  `wall_kind:"treewidth_exceeds_bound"` and a real measured `treewidth > 0`
  that exceeded the bound; exactly one gap filed. **Found and fixed a real
  test-authoring bug while building this**, recorded here rather than
  silently corrected: `treewidth_bound=0` does NOT force a wall —
  `domains/solver_dispatch.py::solve_can_exact` reads
  `int(at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND)`, and `0`
  is falsy in Python, so an explicit `0` is silently indistinguishable from
  "not supplied" and falls back to the default bound of 4. This is
  pre-existing Rung-1 behaviour (not touched by this rung), named here
  because it is a real, live footgun for any future caller passing an
  explicit `treewidth_bound=0`.
- **`test_solve_decompose_failure_files_a_solve_failure_gap`** — two real
  `solve_deduction` goals mint two real `knowledge_logical` schemas
  (`"if X is a cat, X can purr"` / `"if X is a cat, X is furry"`, sharing
  the `cat` antecedent); `project_deduction_shared_attr` builds a real
  coupling graph over them; `solve_decompose` races it at `bound=0`
  (strictly below its real measured treewidth) — a genuinely intractable
  decomposition attempt, not a missing-input wall. Walls with
  `wall_kind:"treewidth_exceeds_bound"`; exactly one gap filed.

### 2.2 The discriminating proof — a resolved goal files no gap

**`test_solve_success_files_no_gap`** — `"if X is a dog, X can bark"`
resolves normally (`status=="resolved"`, no `gap_key`/`gap_noted` written
at all, matching that these attrs are wall-only data); the total count of
`SelfConcern{kind:"solve_failure"}` nodes is unchanged before/after. This
is the test that actually distinguishes "the rule decides correctly" from
"gaps get filed unconditionally."

### 2.3 Dedup

**`test_repeated_identical_solve_failure_is_deduped`** — the identical
unparsable statement dispatched as two SEPARATE `Goal` nodes (`g1`, `g2`,
same `gap_key`): after `g1` walls, exactly one matching `SelfConcern`
exists; after `g2` walls with the SAME `gap_key`, the count is STILL
exactly one — the second identical failure files no second gap, mirroring
`note_unresolved_topic_gap`'s own content-dedup guard byte-for-byte.

## 3. Regression

Fresh baseline verified: `git log --oneline -1 main` == `2b1661c`
(re-checked at worktree creation); worktree created via `git worktree add
--detach ... 2b1661c`; `data/` symlink verified fresh (not a pre-existing
partial directory) then confirmed resolving to the real 492MB file.

**Rung-2's own suite** (`tests/test_solver_dispatch_migrated.py` (11) +
`tests/test_gap_awareness_migrated.py` (9) +
`tests/test_self_gaps_surfacing_migrated.py` (5) +
`tests/test_solve_gap_awareness_migrated.py` (5, new)):

```
30 passed in 252.45s (0:04:12)
```

**Wider composer/self-concern regression**
(`test_composer_driver_migrated.py` + `test_self_concern_promote_migrated.py`
+ `test_topic_route_selfheal_migrated.py` + `test_elaboration_migrated.py`,
31 node ids total):

```
1 failed, 30 passed in 519.40s (0:08:39)
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
```

**Verified pre-existing, not a rung-2 regression — by direct A/B on the
pristine base commit, not by inference from an old baseline file or from
Rung 1's own RESULTS doc.** A throwaway third worktree
(`/home/matt/ozmadev/ocelot-worktrees/qd-rung2-ab-check`, detached at
`2b1661c`, `data/` freshly symlinked, ZERO rung-2 files present) reproduced
the exact same failure — same assertion, same diff
(`relation_head_cases.communicate.rule_count_delta` mismatch), same
`[self-build] minted live rule ...` stderr trace — running
`test_ground_concern_dispatch_parity` alone. Removed afterward
(`git worktree remove --force`). This is the SAME test QUESTION_DRIVER_
RUNG1_RESULTS.md §3 already found pre-existing on `main @ 1480d48`
(unrelated to this rung's diff, which touches only
`domains/solver_dispatch.py`, `seeds/gap_awareness.json`, and new test/doc
files — none of which `test_ground_concern_dispatch_parity` or the
`ground_concern`/self-build composer path touches).

No other regressions found in either sweep.

## 4. Judgment calls (every one made explicit, per the task's own instruction)

### 4.1 The trigger predicate is `status=="walled"`, not a new `outcome` attr

The task's general phrasing ("find where it currently returns/fails
silently... add the fact-recording write there") was resolved against the
PREREG's own more specific §4.3 wording ("a solve_* goal whose
`status=='walled'`... is a capability gap") after re-reading the COMMITTED
Rung-1 code and confirming every wall branch already wrote `status`
comprehensively (traced every branch of all seven resolvers). Duplicating
that as a second `outcome` attr, parallel to `_answer_topic_reply`'s own
field name, would have been a needless second copy of the same fact under
a different name — `answer_topic` Goals use `outcome` because `status`
there already carries the `qd_bind_resolver` dispatch lifecycle
(`pending`/`dispatched`) AND is separately overloaded by other conversation
rules; `solve_*` Goals only ever reach `resolved`/`walled` from their OWN
resolver, so `status` alone is an unambiguous, already-written signal.

### 4.2 The one genuinely new datum needed: `gap_key`

`note_unresolved_topic_gap` dedups on `g.concept` — a human-legible,
per-topic-unique identifier. No `solve_*` Goal carried an equivalent
before this rung (`raw` is a fixed literal per kind for six of the seven
mint helpers, e.g. every `solve_can_relax` Goal's `raw` is literally the
string `"solve_can_relax"`; `note` describes the OUTCOME, not a stable
identity of the ATTEMPT). `gap_key` is computed at each wall site from
data already local there (statement text / targeted node id / direction /
candidate names + bound) — this is the one piece of "mechanical
outcome-recording... at its own point of failure" Rung 1 genuinely had not
already written.

### 4.3 The `kind` string: `"solve_failure"`

Neither the PREREG (`"solving_exhausted"`, explicitly illustrative) nor the
task (`"solve_failure"`, offered as one option among "whatever kind-naming
the existing gap_awareness taxonomy suggests") commits to one literal.
Existing `SelfConcern.kind` values (`knowledge`, `reported`, `instruction`,
`self_account`, `reply_fix`, `self_improvement` — enumerated by direct
grep across `gap_awareness.json` + `conversation_self_concern.json`) are
all named after the SHAPE of the gap, not the mechanism that found it.
`solve_failure` fits that convention (parallel to `knowledge` for an
unresolved topic) and is disjoint from every existing value. Chosen over
the PREREG's illustrative alternative because it more precisely names what
happened (a solve ATTEMPT failed; "solving_exhausted" implies a budget/
capability was exhausted more broadly, which is not what any of the seven
resolvers' wall conditions currently represent — none of them track a
budget).

### 4.4 One seed file, not a new one

The new rule was added to `seeds/gap_awareness.json` (bumped in place)
rather than a new `seeds/solve_gap_awareness.json`, matching the
established precedent of that file already hosting six structurally
unrelated gap-detection rules (topic/instruction/self_account/upload×2/
reported) as ONE growing capability home rather than one-file-per-surface.
`depends_on` gained `"solver_dispatch"` as an honest new dependency (the
rule's kind list is that seed's vocabulary) — checked for cycles: neither
`solver_dispatch` (`depends_on: ["question_driving"]`) nor
`question_driving` (`depends_on: []`) depends on `gap_awareness`, directly
or transitively, so no cycle; confirmed live by a full `load_all_seeds()`
boot completing without error.

### 4.5 `_wall` as a shared Python helper, not seven duplicated write-backs

A small module-level helper (`solver_dispatch.py::_wall`) factors the
repeated two-attr write into one call site per wall branch. This is
presented as DRY mechanical I/O, not a decision: it performs the exact
same `set_attr` calls every wall branch already made, plus writes whatever
`gap_key`/`extra` the CALLER computed and handed it — it contains no
conditional logic of its own and makes no choice about what constitutes a
failure (that remains entirely the caller's own honest-wall branch, as in
Rung 1).

## 5. GO / NO-GO

**GO.** The gap-detection rule mirrors `note_unresolved_topic_gap` exactly
(same match/where/effects shape, same mint-once + content-dedup double
guard), fires correctly on three structurally different real solve-toolbox
failures, correctly does NOT fire on a real success, and correctly dedups
a repeated identical failure — all demonstrated live against real toolbox
calls, no stubs. Every downstream consumer
(`promote_self_concern`/`_run_self_gaps`/`composer_dispatch.json`) was
verified unmodified by direct read. Regression: 30/30 green in the rung's
own suite; 30/31 green in the wider composer/self-concern sweep, with the
one failure verified pre-existing by direct A/B on the pristine base
commit (not inferred), matching the exact same failure Rung 1's own
RESULTS doc already recorded as pre-existing on the prior base commit.

## 6. What this document does NOT establish

1. **No `ProblemShape` recognizer (Rung 3) was built or touched.**
   Deliberately out of scope, per the task's own instruction.
2. **Nothing here decides to MINT a new `solve_*` Goal.** This rung only
   reacts to an already-dispatched Goal's failure — a genuinely separate
   concern, named out of scope by the task.
3. **`gap_key` granularity is a judgment call, not a proven-optimal
   scheme.** For kinds whose only wall path is a missing `targets_mt`/
   `targets_correspondence` edge (`solve_can_relax`, `solve_can_bp`, one
   path each of `solve_reasoning_bridge`/`solve_analogical_promote`), the
   `gap_key` is a FIXED string (e.g. `"solve_can_relax:no_targets_mt"`)
   that would dedup ALL such caller-usage-error walls into one gap
   regardless of which goal/caller triggered it. This is a deliberate,
   honest choice (a missing-edge wall is a caller-usage error, not a
   distinct "problem instance," so collapsing them is arguably correct)
   but it is not exercised or proven optimal by this rung's own tests —
   named as a residual, not silently assumed away.
4. **The `treewidth_bound=0`-is-falsy footgun (§2.1) is a pre-existing
   Rung-1 behaviour, not fixed by this rung.** Named because it was found
   live while building this rung's own test, not because fixing it was in
   scope.
5. **`gap_key` collision across GENUINELY DIFFERENT problems of the same
   kind sharing the same generated key is possible but not observed.** For
   example, two different intractable CAN networks that happen to produce
   identical `(mt_id, treewidth)` pairs after a graph rebuild (unlikely
   within one boot, since `mt` node ids are unique per `add_node` call, but
   not impossible across separate boots/checkpoints where ids could be
   reused) would incorrectly dedup into one gap. `note_unresolved_topic_gap`
   carries the analogous risk today (two different topics that happen to
   share literal concept text) — this is the same class of limitation,
   not a new one introduced here.
