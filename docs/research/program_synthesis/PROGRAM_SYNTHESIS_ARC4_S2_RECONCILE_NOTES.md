# PROGRAM SYNTHESIS ARC 4 — S2 TEST RECONCILIATION (structural verdict
# detectors vs. hand-authored CEGIS/repair fixtures)

**Date:** 2026-08-01. Reconciles the 9 known test failures caused by S2
(`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md`, seed `program_synthesis.json`
v1.6.0 → v1.7.0, `ps_structural_reject`/`ps_structural_clear` gating
`ps_accept`) landing on top of S1/S4's already-reconciled drift
(`PROGRAM_SYNTHESIS_ARC4_RECONCILE_NOTES.md`).

**No seed, adapter, or detector source was changed to do this
reconciliation.** Every fix below is a test-file change, per the two
categories the task was scoped to:

1. **Stale version/count pins** — literal `seed version`/`rule count`
   values that predate S2's 2 new rules (58 → 60 rules, 1.6.0 → 1.7.0).
2. **Improvement-direction outcome pins** — a task whose live outcome
   moved from a wrong accept to an honest rejection, re-pinned in the
   improvement direction only, per the `_KNOWN_CONSTRUCTION_DRIFT` /
   `_P7_KNOWN_LIVE_IMPROVEMENT` precedent.
3. **THE 4 ARCHITECTURAL-TENSION CASES** — hand-authored (or
   frozen-fixture) CEGIS/repair decoys that are structurally identical to
   D3's own target shape (`unread_declared_param`): a decoy that ignores a
   declared, varying input. S2's detector is CORRECT to reject these — the
   FIXTURES were unrealistic. 3 of the 4 were fixed by rewriting the decoy
   to genuinely read every declared input while still computing the wrong
   function. The 4th could not be fixed this way (§3) and is left failing,
   reported precisely below, per the task's own instruction not to add an
   exemption in that case.

Final state: **8 of the 9 named failures are green**; the 9th
(`test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-
br_10_top_of_three]`) is left failing, with the reason recorded in §3.

---

## 1. Per-test reconciliation

### 1.1 `tests/test_budget_isolation_migrated.py::test_seed_version_and_isolation_lanes_present`

**What it was proving:** the seed's own version string and rule count are
what the isolation-lane tests were written against, and S1's isolation
rule (`ps_isolate_fallthrough`) is present with the right shape.

**What changed:** pure version/count drift — S2 added exactly 2 new rules
(`ps_structural_reject`/`ps_structural_clear`), landing v1.6.0/58 →
v1.7.0/60. Nothing about the isolation lane itself changed.

**Fix:** updated the two literal pins (`d["version"] == "1.7.0"`,
`len(d["rules"]) == 60`), dated comment naming S2 as the cause. No other
assertion touched.

### 1.2 `tests/test_retrieval_migrated.py::test_attempt1_codebook_screen_rules_stay_absent_from_the_seed`

**What it was proving:** the Attempt-1 codebook screen (`pr_screen_*`)
never comes back under its own or a differently-named but still
screen-shaped rule; the corrected `ps_screen_*` rules stay present; S1's
`ps_isolate_fallthrough` is structurally isolation, not a screen.

**What changed:** same version/count drift as §1.1. Neither
`ps_structural_reject` nor `ps_structural_clear` contains "screen" in its
name, so the existing intent guard (`screen_named == {ps_screen_mark,
ps_screen_reject, ps_screen_admit}`) is unaffected and was re-verified
live (still passes with the two new rules present).

**Fix:** updated the same two literal pins, dated comment.

### 1.3–1.5 `tests/test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[242|284|414]`

**What it was proving:** each of the 12 R0 ceiling task ids re-verifies
LIVE against the frozen `MEASURED_OUTCOMES` baseline — the ceiling-capture
table's own data source, never silently re-derived.

**What changed:** all three ids are in S2's own measured
`structural_killable_ids` (`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`
§2 / `results/arc4_structural_verdicts.json`). Their frozen "measured"
outcome was a wrong accept that FAILED its held-out row
(`holdout_ok: False` on all three) — exactly the class of defect S2 exists
to catch. Live, S2 now rejects the wrong candidate outright
(`status`: `accepted` → `gapped`, `gap_reason`:
`structural_verdict_reject`) before it can ever stand as an accept.

Measured live:
- 242: `gapped`, rung `d` (retrieval still reaches exemplar 776 — the
  retrieval mechanism itself is unaffected — but the candidate it fills
  is now correctly rejected instead of accepted-wrong).
- 284: `gapped`, rung `none`.
- 414: `gapped`, rung `none`.

**Fix:** per reconciliation rule 2 (a wrong accept becoming a rejection is
a WIN, never a regression — `PROGRAM_SYNTHESIS_ARC4_PREREG.md`
§AMENDMENT A3), added a new, explicitly dated
`_KNOWN_S2_STRUCTURAL_REJECT_DRIFT` dict (same pattern as the existing
`_KNOWN_S4_DRIFT` for task 394, but a **replacement**, not a merge — a
gapped row carries no `exemplar`/`holdout_ok` key the way an accepted row
does, exactly like the pre-existing gapped rows 106/394-frozen/412 in
`MEASURED_OUTCOMES` never carried those keys). `MEASURED_OUTCOMES` itself
is untouched (frozen artifacts stay frozen); `test_ceiling_capture_headline_count`
(which reads `MEASURED_OUTCOMES` directly) is unaffected — it was already
green and stays green (242/284/414 were never in `CAPTURED_TASK_IDS`,
since their frozen `holdout_ok` was `False`).

### 1.6 `tests/test_prog_repair_migrated.py::test_refused_localization_falls_to_global_cegis_unchanged` — ARCHITECTURAL-TENSION CASE 1/4

**What it was proving:** a rung-1 codebook accept has no skeleton/hole
split, so localization honestly refuses and the EXISTING, UNCHANGED global
CEGIS machinery completes the repair (fresh attempt → CounterExample →
exclusion → re-proposal → correct accept).

**What changed:** the hand-planted decoy `grab_first_decoy` was a bare
`Var a` — ignoring `b` entirely. `b` varies across both revealed rows (2,
1), so this is byte-for-byte D3's own target shape
(`unread_declared_param` — the SAME pattern as MBPP tasks 397/404, per
`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §2.2). S2 now correctly
rejects it structurally before it can ever be "accepted" at all — the
initial `r0["status"] == "accepted"` assertion this test's whole narrative
depends on never happens.

**Fix — decoy realism rewrite (§2 below has the shape detail).** The
decoy term was changed from `{"type": "Var", "name": "a"}` to an
`IfThenElse` that reads BOTH declared params — `if a > 0 then a else b` (a
sign check standing in for the intended magnitude comparison). It is
"correct" on the two revealed rows (both have `a > 0`, and `a` happens to
be the larger of the pair both times) but wrong in general, and it passes
D2/D3 cleanly (both `a` and `b` are referenced by a `Var` node in the
term). Every original assertion in the test is UNCHANGED and re-verified
live: `r0["status"] == "accepted"`, `attempts == 1.0`, `holes == []`;
after the counterexample `{"a": 2, "b": 8} -> 8` (decoy's sign check picks
`a=2`, wrong), `repair.refused == 1.0`, `repair.localized is None`,
`repair.attempts == 0.0`; global CEGIS excludes `grab_first_decoy`, finds
`max_of_two` at `attempts == 3.0`; `progs == {"grab_first_decoy": 1.0,
"max_of_two": None}`; `eval_accepted(..., {"a": 1, "b": 5}) == (5, True)`.

### 1.7 `tests/test_descent_widening_migrated.py::test_flat_rung3_accept_converges_via_exclude_powered_retry` — ARCHITECTURAL-TENSION CASE 2/4

**What it was proving:** a FLAT (non-descended) rung-3 whole-goal-enumerate
accept that is first-fit-wrong converges to the correct candidate WITHIN
ONE bounded round via the engine's `exclude` contract
(`ps_enum_retry_mark`) — the P7-B "within-round candidate iteration"
stall-class shape converting (Arc2 Q4's own headline).

**What changed:** the fixture's 3 revealed rows for "the largest of three
numbers a, b, c" were chosen so the enumerator's natural first-fit is
`Max(a, b)` — ignoring `c` entirely. `c` varies across the 3 revealed rows
(3, 5, 4), so this is again byte-for-byte D3's target shape, now correctly
rejected before it becomes an "accepted" candidate for the retry mechanism
to ever exclude.

**Fix — decoy realism rewrite.** Re-derived, LIVE (not guessed), a
row set for which the enumerator's natural first-fit reads all three
declared params: `rows = [(a=1,b=12,c=0)->12, (a=4,b=0,c=9)->9,
(a=10,b=0,c=1)->10]` yields first-fit `Max(a, Plus(b, c))` — it SUMS `b`
and `c` instead of comparing them (a genuinely plausible "combined the
wrong two arguments" bug), and happens to coincide with the true max on
all three rows only because `b` or `c` is 0 in each (D3 does not flag it:
`b` and `c` are each referenced by a `Var` node in the term, satisfying
"genuinely reads its declared inputs"). Verified live it is wrong on a
constructed row where both `b` and `c` are positive and sum past the true
max (`a=1,b=5,c=5` → decoy gives 10, true max is 5). Feeding that row as
the counterexample: `ps_enum_round` goes 0 → 1 (converges within ONE
round, matching the gate's own headline), the excluded term is exactly the
wrong `Max(a, Plus(b,c))`, and the re-solve finds the correct
`Max(a, Max(b, c))`. All original held-out checks
(`(2,4,11)→11, (10,1,2)→10, (1,2,10)→10, (5,5,5)→5`) re-verified live
against the newly accepted candidate.

### 1.8 `tests/test_descent_widening_migrated.py::test_enum_round_budget_is_integer_and_forced_exhaustion_falls_honestly` — ARCHITECTURAL-TENSION CASE 3/4

**What it was proving:** `ps_enum_round_budget` is a real integer counter
on its own lane; forcing it to 0 makes the exclude-retry lever honestly
decline (never silently retry past budget) and fall through to repair,
which itself honestly refuses (no skeleton/hole split at this rung) —
zero parks.

**What changed:** the SAME fixture as §1.7 (same task text, same 3 rows) —
same D3-shaped `Max(a,b)`-ignoring-`c` decoy, same rejection-before-accept
problem: the mechanism under test (round-budget honesty) needs an
accepted-but-wrong candidate to exist FIRST, which S2 now prevents.

**Fix:** identical row/counterexample substitution as §1.7 (the two tests
share the same fixture shape by design). Re-verified live:
`ps_enum_round_budget == 2.0` (integer), `ps_enum_round == 0.0` initially;
forcing the budget to 0 and feeding the same counterexample
(`{"a":1,"b":5,"c":5} -> 5`) gives `status == "gapped"`,
`repair.refused == 1.0`, zero parks — byte-identical shape to the original
test's assertions.

---

## 2. Why fixing the fixtures (not the detector) is correct — the decoy-realism rewrites

S2's own notes (§7(b)) name this class of failure precisely: the
hand-authored CEGIS/repair fixtures in this codebase's test suite plant
*decoy* programs that **ignore a declared, varying input** to demonstrate
"here is a wrong-but-initially-plausible accept that CEGIS later
corrects." D3 (`unread_declared_param`) exists to catch exactly this
shape in real MBPP output (tasks 397/404 — `return max(a,b)` ignoring a
varying `c`; `return a` ignoring a varying `b`), and it is measured at
0.88 precision with the only 3 false positives being genuine label noise,
not detector error (`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §2.2).

**The detector cannot distinguish "a planted test decoy" from "a real
trap" — and it should not be able to, because structurally they are the
same thing.** A test fixture that wants to demonstrate the repair/CEGIS
lane converging on a wrong-then-corrected program must not lean on the
ONE wrongness shape the codebase has just taught its own pipeline to
refuse outright. That is not a detector bug to work around; it is the
fixture failing to keep up with a genuine capability gain, exactly as
CLAUDE.md's own standing discipline states ("do not weaken a detector to
preserve a number").

**Before / after, all 3 fixed decoys:**

| test | before (ignores a declared, varying input) | after (reads every declared input, wrong in general) |
|---|---|---|
| `test_refused_localization_falls_to_global_cegis_unchanged` | `Var a` (ignores `b`, which varies 2/1) | `IfThenElse(Gt(a, 0), a, b)` — a sign check standing in for a magnitude comparison; reads both `a` and `b` |
| `test_flat_rung3_accept_converges_via_exclude_powered_retry` | `Max(a, b)` (ignores `c`, which varies 3/5/4) | `Max(a, Plus(b, c))` — sums `b` and `c` instead of comparing them; reads `a`, `b`, and `c` |
| `test_enum_round_budget_is_integer_and_forced_exhaustion_falls_honestly` | same as above (shared fixture) | same as above (shared fixture) |

Each rewrite was verified LIVE (not hand-derived) to (a) be structurally
accepted at v1.7.0 (no D1/D2/D3 fire — confirmed the rewritten term
references every declared param via a `Var` node), (b) be "correct" on
the small revealed-row set for a genuine, explainable reason (not a
coincidence dressed up — the sign-check decoy is correct on the two
revealed rows because both happen to have `a > 0` and `a` is the larger
of the pair; the sum decoy is correct on its three rows because the
non-`a` term contributing to the sum is 0 in every revealed row), (c)
genuinely wrong on a constructed counterexample, and (d) still exercise
the EXACT mechanism each test was written to prove — localization
refusing then the untouched global CEGIS path completing the repair;
exclude-powered retry converging within one bounded round; the round
budget honestly declining and falling through to repair's own honest
refusal. No assertion in any of the three tests was weakened, deleted, or
had its comparison loosened — every original check still runs, now
against a fixture whose "wrongness" is realistic instead of structurally
identical to the very defect class this codebase just learned to catch.

---

## 3. The 4th architectural-tension case — left failing, reported precisely

### `tests/test_prog_synthesis_battery_migrated.py::test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-br_10_top_of_three]`

**What it was proving:** the `repair_oracle` arm's secondary protocol
(after a holdout-failing accept, feed back ONE failing held-out row via
`ingest_counterexample`) reproduces its stored, frozen row from
`results/prog_synthesis_battery.json` — specifically, for this task, the
Q4 exclude-powered-retry lane converges the accept from `gapped` (frozen,
pre-Q4) to `accepted_holdout_ok` (live, Q4-landed), a registered
improvement already captured in `_P7_KNOWN_LIVE_IMPROVEMENT`.

**Why it cannot be fixed by rewriting the decoy (this task's own rule 3
fallback applies).** The task fixture is
`tests/fixtures/prog_synthesis_battery/tasks.json`'s `br_10_top_of_three`
row — `request_text: "Write a function top_of_three that returns the
largest of three numbers."`, `example_rows` = `[(a=1,b=9,c=3)->9,
(a=7,b=2,c=5)->7, (a=4,b=4,c=4)->4]`. These are the EXACT SAME rows (up to
formatting) that produced the `Max(a,b)`-ignoring-`c` decoy fixed in §1.7
above. Live, `psy.synthesize_from_request` on this task now hits the
IDENTICAL structural rejection: `ps_structural_reject` fires before the
candidate can ever be "accepted", so
`prog_synthesis_battery.run_task_p7`'s own gate
(`if pre["outcome"] != "accepted_holdout_fail": return pre`) returns
immediately — the counterexample is never fed at all
(`oracle.rounds == 0`, `oracle.ce_fed is None`), and the mechanism this
test demonstrates never gets a turn. Measured live:

```
status: gapped, gap_reason: structural_verdict_reject, attempts: 0.0,
excluded: [], oracle: {ce_fed: null, pre_feedback_outcome: "gapped",
rounds: 0}
```

This matches NEITHER the frozen `stored` row (`gapped`/`no_shape`,
`attempts: 1.0`, `oracle.rounds: 1`) NOR the previously-registered
improvement (`accepted_holdout_ok`) — S2 introduced a genuinely NEW third
outcome for this pinned task.

**The fixture that would need to change to apply the SAME §2 fix
(`Max(a, Plus(b,c))`-style row substitution) is
`tests/fixtures/prog_synthesis_battery/tasks.json`, which is explicitly
OUTSIDE this task's file-ownership boundary** (the ownership list is
`tests/test_prog_repair_migrated.py`,
`tests/test_descent_widening_migrated.py`,
`tests/test_retrieval_migrated.py`,
`tests/test_budget_isolation_migrated.py`,
`tests/test_prog_synthesis_battery_migrated.py`, and this notes file —
`tests/fixtures/` is not in that list).

**Why a test-side workaround was rejected, not just the fixture edit:**
- Substituting a different row set INSIDE `test_prog_synthesis_battery_migrated.py`
  (constructing a task dict in Python instead of reading
  `tasks.json`) was considered and rejected: this test's entire purpose is
  to reverify the EXACT PINNED task (identified by `task_id`) against its
  EXACT frozen stored row from `results/prog_synthesis_battery.json`. A
  stored row captured against the ORIGINAL rows compared against a live
  run of DIFFERENT rows is not a reverification of anything — it would
  silently launder a fixture change through the test file, which is worse
  than leaving the test honestly red.
- Re-pinning the expected outcome to the new `gapped`/
  `structural_verdict_reject` result (treating "an even earlier, more
  reliable rejection" as the improvement direction, mirroring §1.3–1.5's
  `_KNOWN_S2_STRUCTURAL_REJECT_DRIFT`) was considered and rejected because
  this task's own brief is explicit for the 4 architectural-tension cases:
  *"If any of the 4 cannot be fixed this way, STOP on that one and report
  why — do not weaken the detector's scope or add an exemption."* Adding
  a new drift-dict entry here would be exactly the exemption the brief
  forbids for this category, even though the general improvement-direction
  mechanism (rule 2, used freely in §1.3–1.5) would otherwise support it.
  The distinguishing fact is that rule 3 governs this specific case (a
  hand/fixture-planted CEGIS decoy, not an organic MBPP task), and rule 3's
  own fallback is to stop, not re-pin.

**Left failing, as instructed.** This is the ONE test of the original 9
still red. `seeds/program_synthesis.json`, `domains/prog_synthesis.py`,
and `tests/fixtures/prog_synthesis_battery/tasks.json` were all left
untouched. A follow-up phase with file access to
`tests/fixtures/prog_synthesis_battery/tasks.json` should either (a)
rewrite `br_10_top_of_three`'s rows the same way §1.7/§1.8's fixtures
were rewritten (a decoy that reads all three params, still wrong in
general), preserving the Q4-improvement narrative under a realistic decoy,
or (b) accept that this pinned task's mechanism demonstration is retired
by a genuine capability gain and re-pin deliberately, with the authority
to edit the fixture that this phase does not have.

---

## 4. Full sweep

Every suite named in the task brief, run together
(`PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. <files> -q`):

`test_prog_repair_migrated.py` (13 passed), `test_prog_descent_migrated.py`,
`test_descent_widening_migrated.py` (11 passed), `test_retrieval_migrated.py`
(31 passed), `test_retrieval_ceiling_migrated.py`, `test_budget_isolation_migrated.py`
(7 passed), `test_screen_codebook_migrated.py`, `test_search_reach_migrated.py`,
`test_structural_verdicts_migrated.py`, `test_verdict_discrimination_migrated.py`,
`test_arc4_anatomy_migrated.py`, `test_arc4_probe_migrated.py`,
`test_prog_synthesis_battery_migrated.py` (20 passed, 1 failed — §3),
`test_program_synthesis_migrated.py`, `test_mbpp_baseline_migrated.py`,
`test_code_synthesis_baseline_migrated.py`, `test_prog_ir_migrated.py`,
`test_value_domain_migrated.py`, `test_synth_enumerate_migrated.py`:

**461 collected, 459 passed, 2 failed.**

The 2 failures:
1. `test_prog_synthesis_battery_migrated.py::test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-br_10_top_of_three]`
   — one of this task's 9 named failures, left red per §3.
2. `test_arc4_probe_migrated.py::test_pinned_task_106_reorders_and_mutually_exhausts_live`
   — **NOT one of the 9 named failures**, and `test_arc4_probe_migrated.py`
   is **NOT in this task's file-ownership list**. Pre-existing (confirmed
   present before any change in this reconciliation), already named and
   categorised by `PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §7(b) as "a minor
   downstream label change... not investigated further (outside file
   ownership either way)" — an unrelated enumerate-search `halt_reason`
   flip (`max_size` → `budget`) as a second-order consequence of other
   tasks' search dynamics. Left untouched, per file ownership.

---

## 5. Refusals

One. `test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-
br_10_top_of_three]` (§3) — the underlying decoy fixture lives outside
this task's file-ownership boundary, so the "fix the fixture" resolution
that worked for the other 3 architectural-tension cases cannot be applied,
and the brief explicitly forbids adding an exemption as a substitute. No
assertion anywhere was weakened, deleted, or wrapped to force a pass.
