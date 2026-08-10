# PROGRAM SYNTHESIS ARC 4 — TEST RECONCILIATION (S1+S4 cross-phase drift)

**Date:** 2026-08-01. Reconciles the 7 known test failures in
`tests/test_prog_repair_migrated.py`, `tests/test_prog_descent_migrated.py`,
`tests/test_retrieval_migrated.py` (`tests/test_descent_widening_migrated.py`
needed no change) caused by two already-landed phases:

- **S1 — budget isolation** (`PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md`, commit
  `d99d39208f`): seed `program_synthesis.json` v1.5.1 → v1.6.0 (57 → 58
  rules), one new rule `ps_isolate_fallthrough`, two new counter lanes
  (`ps_propose_attempts`/`ps_propose_budget`, `ps_enum_reserve_used`/
  `ps_enum_reserve_budget`).
- **S4 — search reach** (`PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md`, commit
  `e895724f6f`): `runners/dsl/src/synth_enumerate.rs` gained 11 new
  enumerable ops (`Len`/`SumList`/`MaxList`/`MinList`/`MaxLenOver`/
  `MinLenOver`/`First`/`LastElem`/`JoinList`/`FilterList`/`MapList`), every
  one a composition of a pre-existing pure DSL Term — no engine source was
  touched by this reconciliation; this document only reconciles TESTS
  against that already-landed capability.

**No seed, adapter, or engine source was changed to do this reconciliation.**
Every fix below is a test-file change: either re-expressing an assertion in
terms of the mechanism it was actually proving (dropping an outcome that
turned out to be incidental), or re-pinning to a task that still exercises
the intended scenario, per the reconciliation rules given for this task. One
finding (task 394, §3) is flagged as a **coincidental false-positive, not a
capability gain** — recorded as a documented, isolated drift, never folded
into the frozen headline numbers it would otherwise inflate.

---

## 1. The 7 failures — what each test was really proving, and how it was fixed

### 1.1 `test_prog_repair_migrated.py::test_headline_unreachable_ids_reach_honest_terminals[la_21_count_zeros]`

**What it was proving:** that `la_21_count_zeros` is *genuinely*
unreachable at live-var grain (proven in-gate: the derived rows are
contradictory for any function of `v1`) and that the repair lane engages,
honestly fails, and falls through to the untouched global path — never a
wrong accept left standing.

**What changed:** S4 added `FilterList`/`Count` (class B, list-filter) to
the enumerator. The hole re-solve can now express "count of zeros" directly
as `Count(FilterList(items, x, x==0))` — a shape that provably did not exist
in the enumerator's reach when P7-B proved this id unreachable (the P7-B
proof about the *live-var abstraction* is still correct; it is a proof
about what the OLD enumerator's candidate space could express, and S4
changed that space). Verified live: `la_21` now converts to
`accepted_holdout_ok` via the *exact same repair mechanism* as
`la_10_count_positives` (P7-B's headline convert) — two counterexample
rounds, localized into the `final_expr` hole, generalizing to BOTH held-out
rows.

**Fix:** removed `la_21_count_zeros` from `HONEST_TERMINALS` (dated
comment explaining why); added a new test,
`test_headline_la21_converts_to_holdout_ok_via_s4_capability_gain`, that
pins the NEW behaviour explicitly (mirrors `test_headline_la10_converts_...`
in shape) so this capability gain is itself guarded against regression.
`la_11_count_evens` / `la_29_count_above_ten` were reconfirmed live —
still genuinely unreachable (parity has no op in the DSL kernel; the
constant 10 is neither a default const nor a spec output) — and stay in
`HONEST_TERMINALS` unchanged.

### 1.2 `test_prog_repair_migrated.py::test_repair_budget_is_integer_and_exhaustion_falls_to_global`

**What it was proving:** the repair budget is a real integer counter on
its own lane; forcing it to 0 makes repair honestly `gaveup` (no repair
hole minted, no repair attempt spent) and fall through to the untouched
global CEGIS path.

**What changed:** on `la_10_count_positives` with the repair budget forced
to 0, the GLOBAL re-proposal (fresh codebook attempt → whole-goal
enumerate, entirely independent of the repair lane) now itself finds
`Count(FilterList(items, x, x>0))` — S4's widened enumerator solving
"count of positives" from scratch. This is verified genuinely
holdout-generalizing (both held-out rows checked), not an overfit.

**Fix:** kept every budget-honesty assertion (`ps_repair_budget==2.0`
integer, `gaveup==1.0`, `repair.attempts==0.0`, no repair hole minted);
added an explicit `rungs["enumerate"]==1.0` assertion to make the
fall-through itself a checked fact (previously only implied by the old
outcome pin); replaced the terminal-status pin from `gapped` to `accepted`
with a live held-out check, since that terminal is now a genuine capability
gain, not the mechanism under test. Dated comment contrasts this
(genuine) case with the la_06/task-394 coincidental cases below.

### 1.3 `test_prog_descent_migrated.py::test_depth_budget_blocks_descent_honestly`

**What it was proving:** at `ps_depth >= max_depth`, descent must never
fire (`rungs["descend"] is None`), and the goal falls through to
whole-goal enumerate.

**What changed:** `la_20_double_each_total` ("double each item then
total") is algebraically `2 * sum(items)`. S4's `SumList` op lets
whole-goal enumerate express this directly (`Times(2, SumList(items))`),
with NO descent needed — a genuine capability gain (verified against
held-out rows: this is a real solve, not a coincidental fit, since doubling
distributes over sum for every valid input, not just the sampled rows).

**Fix:** kept the `rungs["descend"] is None` assertion; added an explicit
`rungs["enumerate"]==1.0` assertion (the fall-through was previously
implied, not checked); replaced the outcome pin from `gapped` to
`accepted` + held-out verification.

### 1.4 `test_prog_descent_migrated.py::test_failed_descent_falls_to_enumerate_then_gap`

**What it was proving:** a BAD decomposition (codebook matches
`product_of_two`, an a/b scalar template, on the trigger word "product" in
a list-shaped request) gives the hole nothing solvable (contradictory
derived rows) — the sub-goal genuinely fails, and the OUTER goal falls
through descend → whole-goal enumerate → an honest gap, filing exactly
ONE `SelfConcern` (the outer goal's; the descent sub-goal's own gap files
none).

**What changed:** on the frozen 3-row `la_06_product_all` fixture, S4's
widened ops let whole-goal enumerate ALSO find something that fits by
COINCIDENCE: `Last(items) * Min(2, Count(items))`. This is **not** a
genuine solve — verified against `la_06`'s own held-out rows, it disagrees
(`[2,3,4]→24` expected, program gives `8`). Product-of-a-list needs a
multiply-reduce primitive S4 explicitly did not add (S4 Notes' own §4.1
honest-residuals names this exact open sub-case of class A: "task 98's
product-then-divide"). This is the SAME failure shape as task 394 (§3
below) — a spurious fit S4's broadened search space makes newly reachable
— but here it happens to occur inside the DESCENT test's own fixture, which
would otherwise silently start asserting a wrong program is this gate's
expected behaviour.

**Fix:** per the reconciliation rule ("re-pin to a task that genuinely
still gaps, drawing from S4's documented residual classes"), re-pinned the
mechanism check off a synthetic spec with the SAME request shape but more,
varied rows (lengths 1–5, negative values) so no accidental fit is
reachable — verified live that `product_of_two` is still selected as the
bad decomposition, the hole still fails on contradictory derived rows, the
outer goal still falls through descend → enumerate → an honest gap, and
exactly one `SelfConcern` is filed. Every original assertion is preserved;
only the fixture rows changed (still constructed via `psy.ingest_spec`
directly, the same idiom `test_prog_repair_migrated.py`'s own synthetic
tests already use — no fixture file was touched, since file ownership
excludes `tests/fixtures/`).

### 1.5 `test_retrieval_migrated.py::test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing`

**What it was proving:** when retrieval finds NOTHING at any rung,
`ps_attempts` is never spent.

**What changed:** task 394 ("check tuple contains no duplicates") used to
find nothing; S4's widened ops now let rung d's generate-and-test hole
fill try `Last(a) > Count(a)`, which coincidentally fits task 394's 2
revealed + 1 held-out rows (see §3 — this is the SAME false-positive as
la_06, just inside the retrieval ladder instead of descent). Task 394 can
no longer stand for "retrieval finds nothing."

**Fix:** re-pinned to task 106 ("append the given list to the given
tuples" — a heterogeneous tuple+list concatenation the DSL has no op for
at all), reconfirmed live: `status=="gapped"`, `rung=="none"`,
`attempts==0.0`. Also strengthened the assertion: the original test never
actually checked `attempts==0.0` (only `status`/`rung`) despite that being
the gate's own stated purpose (HR2) — added it.

### 1.6 `test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[394]`

**What it was proving:** all 12 R0 ceiling task ids re-verify LIVE against
the frozen `MEASURED_OUTCOMES` baseline, never silently re-derived.

**What changed:** task 394's live outcome now diverges (§3): `gapped`/
`none` → `accepted`/`d`/exemplar 760/holdout_ok `True`.

**Fix:** `MEASURED_OUTCOMES` (the frozen R0/R2 measurement) is
**untouched** — it stays byte-identical to its own measurement moment, per
the project's own standing rule that a historical record is never quietly
edited. Added a separate, explicitly-dated `_KNOWN_S4_DRIFT` override dict
(same pattern as `test_mbpp_baseline_migrated.py`'s
`_KNOWN_CONSTRUCTION_DRIFT`) that the live-reverify test consults for task
394 only, with the counter-example proof this is a coincidental fit spelled
out in-line. Crucially, `_KNOWN_S4_DRIFT` does **not** feed
`CAPTURED_TASK_IDS` / `test_ceiling_capture_headline_count` — that test was
already green and stays green (2/12 captured: 138, 406 only). Task 394 is
explicitly and permanently excluded from the "capture" narrative.

### 1.7 `test_retrieval_migrated.py::test_attempt1_codebook_screen_rules_stay_absent_from_the_seed`

**What it was proving:** Attempt-1's reverted, false-negative-producing
codebook screen (`pr_screen_*`) never comes back under its own names; the
corrected, scoped redo (`ps_screen_*`, Arc3-R2.5) stays present.

**What changed:** S1 bumped the seed to v1.6.0/58 rules, one new rule
(`ps_isolate_fallthrough`) — a purely version/count drift, not a
resurrection.

**Fix:** updated the literal pins (`version` 1.5.1→1.6.0, rule count
57→58). Per the task's own instruction to check the guard's INTENT, not
just its literal check, two INTENT-level guards were added:

1. **Every rule whose name even contains "screen"** must be exactly the 3
   corrected `ps_screen_*` ones — a generalisation of the banned-name list
   that would also catch a differently-named but still screen-shaped rule
   (the literal banned-name list only catches rules that reuse the exact
   OLD names).
2. **`ps_isolate_fallthrough` is checked structurally**, not just by
   presence: its own seed comment states it is "ISOLATION, not screening:
   no candidate's correctness is judged here" — verified by asserting its
   effects are `{"set_attr"}` only (never an `Excluded`/`ScreenPass` mint,
   which is exactly what `ps_screen_reject`/`ps_screen_admit` do to record
   a dry-run candidate verdict). A rule that judges a partial-cover
   candidate's correctness would have to mint one of those to have any
   effect visible to the ladder — `ps_isolate_fallthrough` structurally
   cannot, confirming S1 is isolation (which counter gates entry to the
   next rung), never a second screen (which candidate is correct).

---

## 2. Capability-gain table

Every task whose live outcome improved, across the four owned suites, as a
side effect of S1/S4 (not a regression; genuine unless flagged otherwise).

| task | suite | before (frozen/measured) | after (live) | mechanism |
|---|---|---|---|---|
| `la_21_count_zeros` | prog_repair | `gapped:enumerate_failed` (P7-B **proven unreachable**) | `accepted_holdout_ok` (via repair, 2 ce rounds) | S4 `FilterList`+`Count` — `Count(FilterList(items,x,x==0))` |
| `la_10_count_positives` (budget-forced-0 scenario) | prog_repair | `gapped:enumerate_failed` (repair exhausted → global gap) | `accepted_holdout_ok` (global re-proposal, no repair used) | S4 `FilterList`+`Count` — `Count(FilterList(items,x,x>0))`, found by a FRESH codebook+enumerate attempt |
| `la_20_double_each_total` (depth-blocked scenario) | prog_descent | `gapped:enumerate_failed` (descent blocked, whole-goal enumerate had no iteration op) | `accepted` (held-out verified) | S4 `SumList` — `Times(2, SumList(items))`, no descent needed at all |

**P7-B's other two "proven unreachable" ids, reconfirmed unchanged (not a
gain):**

| task | live status today | reason still unreachable |
|---|---|---|
| `la_11_count_evens` | `gapped:enumerate_failed` (honest terminal, repair engages and honestly fails) | parity has no op in the DSL kernel (`Div` is real division; no `Mod`/floor) — S4 did not add one |
| `la_29_count_above_ten` | `gapped:enumerate_failed` (honest terminal, repair engages and honestly fails) | the constant 10 is neither a default const nor a spec output — unreachable regardless of which ops exist |

**Flagged separately — NOT counted as capability gains (§3):** `la_06_product_all`
(re-pinned away from, prog_descent) and MBPP task 394 (re-pinned away
from / drift-documented, retrieval) both moved off an honest gap into an
`accepted` status via S4's widened ops, but the specific programs found are
**verifiably wrong** general solutions that happen to fit their small
revealed/held-out row sets by coincidence.

---

## 3. The coincidental-accept finding (not papered over)

Two tasks exercised by the owned suites produce a **spurious accept** as a
side effect of S4's widened search reach — worth flagging prominently
since it is the same failure SHAPE in both places and neither is a genuine
solve, despite each passing its own held-out check:

1. **`la_06_product_all`** (`tests/fixtures/prog_synthesis_battery/tasks.json`,
   3 example rows): whole-goal enumerate finds
   `Times(Last(items), Min(2, Count(items)))`. Fits `[1,2,3]→6`,
   `[2,5]→10`, `[4]→4` and even la_06's own frozen held-out rows
   BY COINCIDENCE. Disproved with a genuinely-distinct case:
   `[2,3,4]` → program gives `8`, correct answer is `24`.
2. **MBPP task 394** ("check if given tuple contains no duplicates"):
   retrieval rung d fills exemplar 760's masked statement with
   `Last(a) > Count(a)`. Fits both revealed rows AND the one held-out row
   (`(2,3,4,5,6)→True`) by coincidence. Disproved live:
   `a=(5, 1, 2)` is a genuinely duplicate-free tuple; the program answers
   `False` (wrong — verified via direct `ProgEval` with the same oracle
   config `scripts/mbpp_endgame_battery.py::prog_eval` uses).

**Why this matters and what was (and wasn't) done about it:** this is an
expected, already-named category in S4's own notes (`accepted_holdout_fail`
— a candidate that fits revealed rows but not held-out ones), but both
cases above additionally show the held-out check ITSELF can be fooled when
only one row is withheld — the program passes every row it is ever
checked against while being wrong in general. This is a measurement/
verification-strength issue (single held-out row is not a soundness
oracle), not a new bug in S1/S4's own landed code, and neither S1 nor S4
source was touched here (out of this task's scope: no seed/adapter/engine
edits). Both instances were handled by **refusing to let them re-enter the
test suite as if they were genuine passes**: `la_06`'s test was re-pinned
off a widened synthetic fixture where no accidental fit remains reachable
(§1.4), and task 394's drift is recorded but explicitly excluded from the
retrieval suite's "capture" headline (§1.6). No test was weakened to
accept a wrong program as correct.

**Recommendation for whoever owns verification-strength next:** both
counter-examples above are cheap, mechanical proof that a single held-out
row under-powers the ceiling/battery protocols against S4-class search
widening (more ops → more coincidental fits); a second held-out row (or a
property-style check) would very likely have caught both.

---

## 3b. Related drift found OUTSIDE this task's file ownership (not fixed)

While investigating, `tests/test_arc4_anatomy_migrated.py` (not in this
task's file-ownership list, and not one of the named "full sweep" suites)
was found with **3 additional failures**, all consistent with S1's own
documented effect and none touched here:

- `test_pinned_measurement1_class_b_task_108_reverifies_live`: pinned
  `gapped:exhausted`, live is now `gapped:enumerate_failed` — task 108 is
  literally one of S1's own named 17 "class (b)" starved-goal ids
  (`PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md`: "16/17 target ids fully escape
  `gapped:exhausted`"); this is S1 working as designed, reflected in a
  pin outside this reconciliation's scope.
- `test_pinned_measurement1_class_a_task_296_reverifies_live`: pinned
  `gapped:exhausted`, live is now `accepted_holdout_fail` — same S1
  mechanism, task 296 additionally reaching an accept post-escape.
  Whether that accept is genuine or a coincidental fit (§3's concern)
  was NOT checked — out of scope.
- `test_r3_consistency_reverifies_live`: a hash-based consistency check
  fails (a downstream artifact hash pinned before S1/S4 landed).

These are reported here for whoever owns that file next; per this task's
explicit file-ownership restriction, `tests/test_arc4_anatomy_migrated.py`
was NOT modified.

## 4. Refusals

None. All 7 failures were reconciled either by re-expressing the mechanism
being tested (dropping an incidental outcome pin) or by re-pinning to a
task that still genuinely exercises the scenario. No assertion was
weakened, deleted, or wrapped to force a pass; two prominent findings
(§3) that are NOT capability gains were flagged and explicitly excluded
from headline capture numbers.

---

## 5. Test counts

- `tests/test_prog_repair_migrated.py`: 13 passed (was 11 + 2 new
  failures; +1 new capability-gain test, +1 pre-existing test unaffected).
- `tests/test_prog_descent_migrated.py`: 17 passed (unchanged count; 2
  fixed in place).
- `tests/test_descent_widening_migrated.py`: unchanged, untouched — no
  drift found.
- `tests/test_retrieval_migrated.py`: 31 passed (unchanged count; 3 fixed
  in place).
- Full named sweep (`prog_repair` + `prog_descent` + `descent_widening` +
  `retrieval` + `program_synthesis` + `budget_isolation` +
  `screen_codebook` + `search_reach` + `battery` + `synth_enumerate` +
  `prog_ir` + `value_domain` + `code_synthesis_baseline` +
  `mbpp_baseline` + `retrieval_ceiling`): **370/370 green**.
