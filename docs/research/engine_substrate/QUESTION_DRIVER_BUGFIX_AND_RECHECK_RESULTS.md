# Question-driver solver dispatch — bugfix + Rung 3 data-sufficiency recheck — RESULTS

Base `main @ c87d065` ("Merge progsyn-dictitems-sortby: DictItems + SortBy
Terms, MBPP 61->62 (task 475), GO"), verified via `git log --oneline -1 main`
immediately before creating the worktree (re-checked fresh, per the task's
own warning that main has moved multiple times today — not assumed from any
cached hash). Worktree: `/home/matt/ozmadev/ocelot-worktrees/qd-bugfix-recheck`,
branch `qd-bugfix-recheck`, created via `git worktree add --detach ... c87d065`.
`data/` was absent in the fresh worktree (not a partial real directory);
symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data data`) and confirmed
`data/wiktionary/en.jsonl.gz` resolves to the real 492,560,156-byte file —
the documented gotcha, checked directly, not assumed.

This document covers two independent pieces of work against the
question_driver solver-dispatch arc (`QUESTION_DRIVER_RUNG1/2/3_RESULTS.md`):
a real bugfix (Part 1) already diagnosed but not fixed by Rung 2, and a
data-sufficiency recheck (Part 2) of Rung 3's two explicitly-deferred
follow-ons. **Part 1: fixed, live-demonstrated, regression-clean, committed
(`e2c61c8`). Part 2: NO-GO on both deferred pieces, unchanged from Rung 3 —
nothing in the codebase has touched this population since Rung 3 landed, and
this document's own new bugfix tests do not change that verdict (reasoning
in §2).**

---

## Part 1 — the `treewidth_bound=0` footgun, fixed

### 1.1 Scope and reasoning (written before the broader sweep, per house
    discipline)

`QUESTION_DRIVER_RUNG2_RESULTS.md` §2.1 named, but explicitly did not fix
(§6.4: *"pre-existing Rung-1 behaviour, not fixed by this rung"*), a live
footgun in `domains/solver_dispatch.py::solve_can_exact`:

```python
bound = int(at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND)
```

`at.get("treewidth_bound")` returns the Goal's own stored value — which, for
an explicit `treewidth_bound=0`, is the float `0.0`. `0.0 or X` evaluates to
`X` in Python (falsy short-circuit), so an explicit, deliberate zero-bound
request is silently indistinguishable from "no bound supplied at all," and
the resolver substitutes `cjt.DEFAULT_TREEWIDTH_BOUND` (4) instead. A
treewidth-0 request is a real, valid, if degenerate, request — the true
treewidth of a single-node or edgeless CAN network is exactly 0, and a
caller asking "only accept if this network needs zero coupling" deserves to
have that request honoured, not silently loosened to "accept up to
treewidth 4."

**The fix**: distinguish "attr absent/None" from "attr present, including an
explicit falsy numeric value" via `is None`, not Python truthiness. A single
helper, `_at_num(at, key, default)` (`domains/solver_dispatch.py:99-118`),
replaces the bare `or` idiom at every site where the distinction is real
(§1.2 below). This is a mechanical attr-read fix — no change to what any
resolver decides, no new decision logic, no new Γ production, no new node
type; it only changes which value a resolver reads off a Goal attr that was
already there.

**Scope boundary, stated explicitly**: this fix touches read sites only.
Every `mint_solve_*_goal` helper's OWN write side already correctly
distinguished `None` from an explicit `0`/`0.0` before this fix (e.g.
`mint_solve_can_exact_goal`: `if treewidth_bound is not None: attrs[...] =
float(treewidth_bound)`, `domains/solver_dispatch.py:186-187` pre-fix,
unchanged) — the bug was purely in the seven resolvers' own attr reads, not
in how a Goal got minted. Nothing about `_wall`, `_stash_result`,
`qd_bind_resolver`, `note_solve_exhausted_gap`, or any seed file is touched.

### 1.2 Every falsy-zero-vs-None call site in the file, swept, judged
    individually

Grepped every `at.get(...)` read in `domains/solver_dispatch.py` (11 sites,
pre-fix) and judged each on its own merits — "does this site's *default*
differ from its *falsy zero*, such that an explicit zero would be silently
overridden":

| site (pre-fix) | real footgun? | fixed |
|---|---|---|
| `solve_deduction`: `at.get("statement") or at.get("raw") or ""` | no — a text fallback chain, not a numeric zero/None confusion; an explicit empty-string statement genuinely has no useful parse target, so falling through to `raw` is the intended behaviour, not a bug | left as-is |
| `solve_deduction`: `at.get("mode") or "auto"` | no — `mode` is a non-empty enum string in every real caller; an empty string is not a meaningful "explicit mode" | left as-is |
| `solve_can_relax`: `int(at.get("k_starts") or 1)` | yes, same shape as the others, but not LIVE-observable today: `k_starts` only branches on `k_starts > 1`, and 0 and 1 take the identical `else` branch either way — still fixed, for round-trip fidelity of the stored value and to close the class, not because it changes observed behaviour today | **fixed** → `_at_num(at, "k_starts", 1)` |
| `solve_can_exact`: `int(at.get("treewidth_bound") or cjt.DEFAULT_TREEWIDTH_BOUND)` | **yes — the diagnosed bug** | **fixed** |
| `solve_can_exact`: `int(at.get("max_exact_n") or cjt.DEFAULT_MAX_EXACT_TREEWIDTH_N)` | yes, same class (an explicit `max_exact_n=0` would silently become 10) | **fixed** |
| `solve_can_exact`: `at.get("commit")` (`True if ... is None else bool(...)`) | already correct (uses `is None`) | no change needed |
| `solve_can_bp`: `at.get("combine") or "max_product"` | no — string enum, same reasoning as `mode` | left as-is |
| `solve_can_bp`: `int(at.get("max_rounds") or cbp.DEFAULT_MAX_ROUNDS)` | yes — an explicit `max_rounds=0` (run zero BP rounds, read only the prior/initial belief) is a real, meaningful, distinct-from-default request | **fixed** |
| `solve_can_bp`: `float(at.get("epsilon") or cbp.DEFAULT_EPSILON)` | yes — an explicit `epsilon=0.0` (require exact convergence, the tightest possible tolerance) is a real, meaningful, distinct-from-default request | **fixed** |
| `solve_can_bp`: `bool(at.get("commit") or False)` | no — default is already `False`; explicit `False` and absent are observably identical | left as-is |
| `solve_reasoning_bridge`: `bool(at.get("positive", True))` | no — already correct (`dict.get(key, default)` only substitutes on a genuinely absent key, not on a falsy present value) | no change needed |
| `solve_reasoning_bridge`: `float(at.get("alpha") or 1.0)` | **yes — a second real, live bug of the identical shape**: an explicit `alpha=0.0` (zero-weight evidence — a real, meaningful request: "note this derived fact but give it no CAN influence") was silently promoted to `alpha=1.0` | **fixed** |
| `solve_reasoning_bridge`: `int(at.get("t") or 0)` | no — default is already `0`; explicit `0` and absent are observably identical | left as-is |
| `solve_decompose`: `at.get("bound")` (`is None` wall-guard, then `int(at.get("bound"))`) | already correct — explicitly wall-guarded on `is None` *before* the bare read, so an explicit `bound=0` reaches the `int()` call and is honoured | no change needed |
| `solve_decompose`: `int(at.get("max_exact_n") or 10)` | yes, same class | **fixed** |
| `solve_decompose`: `int(at.get("refine_budget") or 0)` | no — default is already `0`; explicit `0` and absent are observably identical | left as-is |

**Six real fixes** (`k_starts`, `treewidth_bound`, `max_exact_n`×2 — one
each in `solve_can_exact`/`solve_decompose`, `max_rounds`, `epsilon`,
`alpha`) — the diagnosed `treewidth_bound` bug plus five siblings of the
identical shape, one of which (`alpha`) is judged equally live/real (a
legitimate zero-weight-evidence request silently promoted to full weight).
Five sites left unchanged, each with an explicit, individually-argued
reason (a string-enum fallback, a default that already equals the falsy
value, or an already-correct `is None`/`dict.get(key,default)` read) — not
silently skipped.

### 1.3 The fix itself

```python
def _at_num(at: dict, key: str, default):
    v = at.get(key)
    return default if v is None else v
```

`domains/solver_dispatch.py:99-118` (full docstring in the file explains the
`or`-vs-`is None` distinction and names which sites were and were not
converted, so a future reader does not have to re-derive §1.2's table).
Applied at the six real sites (`domains/solver_dispatch.py:313, 356-357,
393-394, 430, 512`).

### 1.4 Live demonstration

`tests/test_solver_dispatch_migrated.py`, three new tests (`14` total in the
file, up from 11):

1. **`test_solve_can_exact_treewidth_bound_zero_is_honored_on_a_genuine_zero_treewidth_network`**
   — a REAL single-Concept, zero-`causal_influence`-edge CAN network (true
   treewidth 0, not a contrived input — `_edgeless_single_concept_mt`,
   mirroring `_resident_mt`'s own construction idiom), dispatched through
   `solve_can_exact` with `treewidth_bound=0` explicit. Asserts: the Goal's
   own `treewidth_bound` attr is `0.0` (the mint-side write, always correct);
   `status == "resolved"`; `treewidth == 0.0`; and — the load-bearing
   assertion — the stashed real toolbox-call result's own
   `treewidth_bound` key is `0`, i.e. the value actually PASSED into
   `cjt.junction_tree_exact_settle` was the caller's real 0, not a
   substituted 4.
2. **`test_solve_can_exact_treewidth_bound_zero_is_honored_not_defaulted_on_real_nonzero_network`**
   — the discriminating regression pin: a REAL Bigville resident CAN network
   (measured treewidth ≈2, well inside the old silently-substituted default
   of 4) dispatched with `treewidth_bound=0` explicit. Pre-fix, this would
   have wrongly `status == "resolved"` (2 ≤ 4, the substituted default).
   Post-fix (measured): `status == "walled"`, `wall_kind ==
   "treewidth_exceeds_bound"`, `treewidth > 0.0`, and the stashed result's
   `treewidth_bound == 0` (not `4`) — the honest-refusal reason cites the
   caller's REAL bound, not the old default.
3. **`test_solve_can_exact_nonzero_and_absent_bound_behaviour_unchanged`** —
   regression proof over three sub-cases on real Bigville networks: (a) no
   `treewidth_bound` supplied at all → still falls back to
   `cjt.DEFAULT_TREEWIDTH_BOUND` and resolves, byte-identical to Rung 1's
   own `test_solve_can_exact_resolves_via_qd_bind_resolver`; (b) an explicit
   non-zero bound equal to the default (4) → still resolves; (c) an explicit
   non-zero bound too tight for the real network (1) → still walls with
   `wall_kind == "treewidth_exceeds_bound"`, matching
   `QUESTION_DRIVER_RUNG2_RESULTS.md`'s own
   `test_solve_can_exact_failure_files_a_solve_failure_gap`.

```
$ python3 -m pytest tests/test_solver_dispatch_migrated.py -q
..............                                                           [100%]
14 passed in 13.44s
```

All three new tests use real toolbox calls (`cjt.junction_tree_exact_settle`
via the unchanged `qd_bind_resolver` JOIN, over real Bigville resident CAN
networks or a real minimal single-Concept network) — no stubs, no synthetic
strings, mirroring every prior rung's own discipline.

### 1.5 Regression

The four task-named files, run as two separate invocations (reported as
actually run, not merged into a single command that was never literally
executed):

```
$ python3 -m pytest tests/test_solver_dispatch_migrated.py -q
14 passed in 13.44s
$ python3 -m pytest tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py tests/test_can_junction_tree.py -q
26 passed in 24.21s
```

40/40 green across both runs.

Also (the wider composer/self-concern sweep, matching every prior rung's own
regression scope):

```
$ python3 -m pytest tests/test_gap_awareness_migrated.py \
    tests/test_self_gaps_surfacing_migrated.py -q
14 passed in 230.18s
```

**Zero regressions.** This rung's diff touches only `domains/solver_dispatch.py`
(read-site fix + new helper) and `tests/test_solver_dispatch_migrated.py`
(new tests) — no seed file, no other module, no rule. Given the purely
additive/read-site nature of the diff (the same reasoning Rung 1/2/3 each
already used to justify not re-running the full ~9-minute composer-dispatch
A/B for a diff that touches none of `ground_concern`/`composer_dispatch.json`),
the previously-repeatedly-verified pre-existing
`test_ground_concern_dispatch_parity` failure was not re-checked a fourth
time — this diff does not touch `domains/reflective_faculty.py`,
`seeds/composer_dispatch.json`, or anything in that path, so there is no
plausible causal path from this fix to that failure. (Per
`QUESTION_DRIVER_RUNG3_RESULTS.md` §9.5's own honest note: a materially
different diff would be worth a fresh A/B; this diff is not materially
different from the prior three, which already established the same
result three times.)

### 1.6 Committed

`e2c61c8` on branch `qd-bugfix-recheck` (worktree
`/home/matt/ozmadev/ocelot-worktrees/qd-bugfix-recheck`), committed
immediately after the fix + its own isolated test pass, before running the
broader sweep — per house discipline point 7.

---

## Part 2 — Rung 3's two deferred pieces: data-sufficiency recheck

### 2.1 What Rung 3 deferred, and why (recap, not re-derived)

`QUESTION_DRIVER_RUNG3_RESULTS.md` §1/§8 named two explicit follow-ons and
gave each a precise, checkable blocking condition rather than a vague "not
enough data yet":

- **Rung 3.5 — pre-mint auto-dispatch.** Blocked on: *"a real adapter
  surfac[ing] genuinely unclassified problems"* — i.e., at least one real
  case where a `solve_*` Goal's KIND is not already known by the caller at
  mint time, so a recognizer would have something to decide. At Rung 3
  landing, every one of the 19 real instances was minted by a test author
  who already knew the kind (`mint_solve_deduction_goal`,
  `mint_solve_can_exact_goal`, etc. — the kind is baked into the function
  name the caller chose to call).
- **Rung 4 — the hold-open multi-candidate layer.** Blocked on: *"a real
  case of genuine candidate competition"* — i.e., at least one real problem
  instance whose extracted structural signature (the five real axes
  `domains/problem_shape.py::goal_signature` reads: `has_statement`,
  `has_targets_mt`, `has_targets_correspondence`, `direction`,
  `has_bound`) is compatible with TWO OR MORE seeded/minted `ProblemShape`
  entries at once, so there is something genuine to hold open and later
  collapse. At Rung 3 landing, the five real facts were mutually exclusive
  by construction of the seven `mint_solve_*_goal` functions (each writes
  a disjoint attr/edge set), so no real competing pair existed.

### 2.2 Has anything changed since Rung 3 landed? — checked directly, not
    inferred

Rung 3 was merged to `main` at `58b26cf` ("Merge qd-solver-rung3:
ProblemShape codebook recognizes real solve_* structure, GO on the small
slice"). Current base is `c87d065`, eight commits later:

```
$ git log --oneline 58b26cf..c87d065
c87d065 Merge progsyn-dictitems-sortby: DictItems + SortBy Terms, MBPP 61->62 (task 475), GO
8917134 progsyn DictItems/SortBy: RESULTS doc, GO delivered, MBPP +1 all arms
4c09dc9 progsyn: DictItems + SortBy Terms (task 475 witness confirmed live)
cd5beff progsyn: DictItems/SortBy (task 475) PREREG -- GO, priced
938b595 Merge progsyn-setlit-dictitems: Sort + SetMap/Intersect/Union, MBPP 56->61 measured
c805d25 progsyn SetLit/DictItems: RESULTS doc, GO delivered, MBPP 56->61 measured
cb8c97b progsyn SetLit/DictItems rung: fix _plain() to handle Set/FrozenSet, measured +5 MBPP
ebee2e3 progsyn SetLit/DictItems rung: Sort Term + SetMap/Intersect/Union ops, 141/232/473 witnessed in-budget
```

All eight are `program_synthesis`/MBPP work — **zero touch any file in the
solver-dispatch/problem-shape path**, confirmed directly:

```
$ git log --oneline 58b26cf..c87d065 -- domains/solver_dispatch.py \
    domains/problem_shape.py seeds/solver_dispatch.json \
    seeds/problem_shape_growth.json seeds/gap_awareness.json \
    tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py
(empty)
```

A whole-tree grep (not just the delta — checking for any NEW, previously
unseen caller anywhere) confirms no adoption anywhere else in the codebase
either:

```
$ grep -rln "mint_solve_" --include=*.py .
domains/problem_shape.py            # a stale docstring reference only, not a call
domains/solver_dispatch.py          # the seven definitions themselves
tests/test_problem_shape_migrated.py
tests/test_solve_gap_awareness_migrated.py
tests/test_solver_dispatch_migrated.py

$ grep -rln "solver_dispatch" --include=*.py --include=*.json .
domains/problem_shape.py  domains/solver_dispatch.py  seeds/gap_awareness.json
seeds/problem_shape_growth.json  seeds/solver_dispatch.json
tests/test_problem_shape_migrated.py  tests/test_solve_gap_awareness_migrated.py
tests/test_solver_dispatch_migrated.py  tools/build_problem_shape_growth_seed.py
```

Every hit is a Rung 1/2/3 file itself. **No other seed, script, world
adapter, or daemon path anywhere in this codebase mints, dispatches, or
reads a `solve_*` Goal or a `ProblemShape` node.** The organic population is
unchanged: still the same 19 real instances Rung 3's own PREREG counted,
still mutually exclusive by the same construction, still all minted by a
caller who already knew the kind.

### 2.3 Does THIS document's own Part 1 bugfix change the verdict? — no,
    argued explicitly, not just asserted

Part 1 added three new tests to `tests/test_solver_dispatch_migrated.py`,
which mint five NEW `solve_can_exact` Goal instances (raising that call
site's raw count from 2 to 7 within that one file; across all three test
files combined, `mint_solve_*_goal` raw call-site counts went from 36 to 41,
grepped directly: `solve_deduction` 18, `solve_can_exact` 6→11,
`solve_decompose` 5, `solve_can_relax`/`solve_reasoning_bridge`/
`solve_analogical_promote` 2 each, `solve_can_bp` 1).

Note on reconciling this against Rung 3's own "19 real instances" table
(§1.1 of that RESULTS doc): that table is a curated count of what Rung 3's
own author judged to be distinct real problem INSTANCES (e.g. it appears to
exclude at least one incidental settle-then-bridge `solve_can_exact` call
used only as setup for a `solve_reasoning_bridge` demo, not counted as its
own instance) — it is not identical to a raw `grep -c mint_solve_` count,
which this document did not attempt to re-derive or re-litigate. What
matters for this recheck is not reconciling the two counting methodologies
but the fact established directly in §2.2: the underlying test file
CONTENT that Rung 3's count was drawn from is byte-identical to Rung 3's own
landing state (`git log 58b26cf..c87d065` touches none of these files) —
so whatever Rung 3's real count was, by Rung 3's own methodology, it is
unchanged today except for this document's own five new additions, which
are argued below not to count.

Per the task's own explicit instruction ("do not pad the population with
synthetic cases to force a GO"), those five new instances do **not** count
toward either follow-on's data-sufficiency bar, and this is judged on the
substance, not just the letter of that instruction:

- They are all `solve_can_exact` — the SAME kind, dispatched the SAME way
  (`mint_solve_can_exact_goal` → `qd_bind_resolver` → `solve_can_exact`),
  by a test author who chose that kind explicitly. They add zero evidence
  toward Rung 3.5's blocker (a genuinely unclassified raw problem) — every
  one of the five new instances is exactly as pre-classified as the 11 that
  came before it.
  - Nor do they add competition evidence for Rung 4: `treewidth_bound` is
  not one of `goal_signature`'s five axes (only `has_targets_mt` is —
  `domains/problem_shape.py` reads structural PRESENCE of an edge, never a
  bound value), so all five new instances recognize as the exact same
  `can_shape` the other 11 `solve_can_exact` instances already recognize
  as. They exercise a real bug fix, not a new structural shape.
- They were built specifically to prove Part 1's fix (a deliberately
  engineered edgeless network, a deliberately too-tight bound) — the
  opposite of the "organic real usage" both follow-ons are blocked on. Rung
  3's own §1 table was explicit that the count that matters is REAL,
  CALLER-DRIVEN usage, not test-authored coverage of an existing kind.

**Verdict: unchanged.** The population these five new instances join is
still the same 19-instance corpus in every dimension that matters to §2.1's
two blockers — same kinds, same mutual exclusivity, same "caller already
knew" property.

### 2.4 GO / NO-GO

**NO-GO on both deferred pieces, precisely as Rung 3 left them, for the
identical reasons, re-verified rather than re-asserted:**

1. **Rung 3.5 (pre-mint auto-dispatch): still NO-GO.** No file anywhere in
   this codebase — checked by both delta (`git log` since Rung 3's merge)
   and whole-tree grep, not by memory of the prior rung's own claim — mints
   a `solve_*` Goal from a genuinely unclassified raw problem. The
   population is 100% pre-classified-by-caller, unchanged from Rung 3.
2. **Rung 4 (hold-open multi-candidate layer): still NO-GO.** No two real
   `solve_*` instances anywhere in the corpus produce overlapping
   `goal_signature` axes — the seven mint functions still write mutually
   exclusive attr/edge sets, unchanged from Rung 3, and this document's own
   five new instances (all `solve_can_exact`, all recognizing as the
   pre-existing `can_shape`) do not introduce a competing pair either.

No PREREG document was written for Part 2 (`QUESTION_DRIVER_BUGFIX_AND_
RECHECK_PREREG.md` does not exist) — per house discipline point 1, a PREREG
is only required "if Part 2 produces any GO." It did not.

This is intended as the task's own explicitly-sanctioned outcome: *"a
repeated, well-reasoned 'still not yet, here's the exact gap' is a valid,
complete outcome, not a failure to find something to build."* Nothing was
built for Part 2 beyond this recheck itself.

---

## 3. Regression (combined, both parts)

```
$ python3 -m pytest tests/test_solver_dispatch_migrated.py -q
14 passed in 13.44s

$ python3 -m pytest tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py tests/test_can_junction_tree.py -q
26 passed in 24.21s

$ python3 -m pytest tests/test_gap_awareness_migrated.py \
    tests/test_self_gaps_surfacing_migrated.py -q
14 passed in 230.18s
```

**54/54 green across every file the task named.** No new failing node ids;
no pre-existing failure re-encountered in this scope (the only known
pre-existing red in this arc,
`test_composer_driver_migrated.py::test_ground_concern_dispatch_parity`, is
outside this diff's causal reach — §1.5 — and was not part of this run's
target file list).

---

## 4. What this document does NOT establish

1. **Part 1 does not claim to have found every falsy-zero footgun in the
   codebase** — only every one in `domains/solver_dispatch.py`, the file
   the task named. `domains/problem_shape.py` and the other six toolbox
   modules (`propositional_deduction.py`, `can_native_orchestration.py`,
   `can_junction_tree.py`, `can_native_bp.py`, `reasoning_can_bridge.py`,
   `analogical_thinking.py`, `problem_decomposition.py`) were not swept —
   they were out of the task's own stated scope ("in the same file").
2. **`k_starts`'s fix has no live-observable behavioural effect today**
   (§1.2) — fixed for correctness/closure of the class, not because a real
   caller has hit it. Named honestly rather than folded into the same
   "real bug" bucket as `treewidth_bound`/`alpha`.
3. **Part 2's NO-GO is a snapshot, not a permanent verdict.** Both blockers
   are precisely stated, checkable conditions (§2.1) that a future rung can
   re-check cheaply the same way this one did (`git log` since the last
   check + a whole-tree grep) — this document does not claim the blockers
   can never be satisfied, only that they are not satisfied today.
4. **The five new `solve_can_exact` test instances (Part 1) are real
   toolbox calls, not synthetic strings** — but they are also not evidence
   of organic adoption, and §2.3 argues explicitly why they should not be
   read as such, rather than silently omitting them from the count.
