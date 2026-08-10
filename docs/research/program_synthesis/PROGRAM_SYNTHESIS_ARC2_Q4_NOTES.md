# PROGRAM SYNTHESIS ARC 2 Q4 — DESCENT + REPAIR WIDENING (notes)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC2_PLAN.md` §2-Q4,
`PROGRAM_SYNTHESIS_P7A.md` / `P7B.md` (the scope cuts closed here),
`PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md` (the `exclude` engine contract this
phase consumes), `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (HQ bars — Q4's own
contribution is measured at Q5; the gates below are mechanism gates).

**Deliverables:** `seeds/program_synthesis.json` **v1.4.0** (43 → 49 rules,
+2 codebook constructions), `domains/prog_synthesis.py` (widened
derivation/splice helpers + 2 new mechanical verbs' worth of logic folded
into existing dispatch), `tests/test_prog_descent_migrated.py` (+2,
17 total), `tests/test_prog_repair_migrated.py` (+2, 13 total),
`tests/test_program_synthesis_migrated.py` (rule-count pin 43 → 49), NEW
`tests/test_descent_widening_migrated.py` (11 gates).

---

## 1. Which scope cuts closed

| P7-A/P7-B named cut | closed how | headline gate |
|---|---|---|
| **Scalar-loop descent guarded out** ("every scalar-row path in the tree is byte-unchanged by guard" — arc-1's OWN description of the boundary it deliberately did not cross) | `ps_descend_mark`'s scope guard widens from list-input-only to ALSO admit a scalar spec whose sole cover is a range()-sourced Fold (`tmpl_scalar_fold`, a new structural fact `_normalise_fold_marks` stamps). Two new codebook constructions (`factorial_of_n_spine` / `range_sum_spine`) give it real triggers. Fold-step's row derivation generalizes from "a singleton LIST row" to "the Fold's `source` materialises to exactly one element" (`_fold_source_list`), unifying list and scalar cases in ONE formula. | `test_factorial_class_scalar_loop_descends_and_holds_out_correct`, `test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct` — both `rungs.enumerate is None`, held-out correct on 3 unseen inputs each |
| **branch_arm derivation named-blocked** ("zero corpus mass in the battery's gapped set... taxonomy vocabulary reserved") | A NEW plan (`ps_plan_branch_arm`) fires when the sole cover is an IfThenElse template (`tmpl_branch`, same idiom as `tmpl_fold` one op-level up). The DECIDED CONDITION is kept from the covered template (the P7-A "skeleton keeps its structure, only the part in question changes" precedent, applied to the condition instead of the fold body). BOTH arms are solved DIRECTLY — one `SynthEnumerate` call per row partition, no further sub-goal recursion (a scope-limited but real closure — see §5 residual 1) — and recombined into one IfThenElse at fold-up. | `test_branch_arm_headline_condition_and_two_arms_accepted_and_holds_out` — `max_of_two`'s literal `a`/`b` arms tried+excluded first, condition `a>b` kept, both arms (`a-b`/`b-a`) solved and verified on 5 held-out (a,b) pairs incl. the tie boundary |
| **Within-round candidate iteration contract-blocked pre-exclude** (P7-B residual 2: *"a Rust `exclude` parameter on `SynthEnumerate` is the named lever if within-round iteration is ever needed"*) | Two closures, per the two places the P7-B block actually lived: (a) **hole-scope** — `run_enumerate` now threads `ps_enum_excluded` (repair's existing ExcludedSub transcription, previously used ONLY for the coarse const-drop heuristic) into the engine's real `exclude` param; (b) **top-level (flat, non-descended) accepts** — a NEW round-bounded lane (`ps_enum_round`/`ps_enum_round_budget`, `ExcludedTerm` provenance nodes, the `ps_enum_retry_mark` rule) retries a repair-refuted rung-3-only accept with the wrong candidate excluded via the engine contract. | `test_run_enumerate_threads_hole_scope_exclude_into_the_engine` (repair suite, additive) for (a); `test_flat_rung3_accept_converges_via_exclude_powered_retry` for (b) — a 3-arg-max task's wrong `Max(a,b)` first-fit converges to the correct nested-max within ONE bounded round |

All four are **real, measured mechanisms**, not relabelings: every headline
gate above checks `rungs.enumerate is None` (descent solved it — items 1–2)
or exhibits an actual second `SynthEnumerate` call with the wrong candidate
provably excluded (item 3), and every one verifies against multiple
never-revealed inputs.

## 2. Row-verdict widening (item 4)

Two new rules, `ps_row_pass_special`/`ps_row_fail_special`, mirror
`ps_row_pass`/`ps_row_fail` exactly but read a NEW recorded fact, `cmp_ok`
— a fixed-formula comparison `eval_and_record` computes for **every** row
(harmless extra fact on plain rows) from Q2's `mbpp_spec` row schema:

- **`tol`** (a row's declared float tolerance) → `abs(got - expected) <=
  tol`. Verified: `average_of_two`'s exact `3.0` passes against a declared
  `expected=3.001, tol=0.01` — the ORIGINAL `ps_row_pass`'s plain `Eq`
  check would have FAILED this row; `ps_row_pass_special` correctly passes
  it via `cmp_ok`.
- **`unordered`** (a row's declared set-comparison flag) → SET equality,
  order- **and duplicate-insensitive** (multiple copies of one element
  collapse to one — never multiset/bag equality; per `domains/mbpp_spec.py`'s
  own documented semantics for MBPP's `set(...) == set(...)` idiom).
  Verified: a candidate returning `[2, 1]` against a declared
  `expected=[1, 2], unordered=True` passes (`cmp_ok` computed off the RAW
  `got` value, BEFORE the `_SCALARS` cast that would otherwise have
  discarded the list — a real bug avoided, see §5 residual 2).
- **Mutual exclusion, by construction:** both new rules require
  `row_tol_active==1.0 OR row_unordered==1.0`; the ORIGINAL two rules gain
  the exact negation of that same predicate. Neither flag attr existed
  before this version, so the added clause is trivially true for every
  pre-Q4 row — `ps_row_pass`/`ps_row_fail` are byte-identical there.
- **The decision stays a rule; the comparison is a fixed formula**
  (`_row_cmp_ok`, pinned directly in `test_row_cmp_ok_fixed_formula_pinned`)
  — the exact ink `ps_spine_ok` class CLAUDE.md sanctions.

`ingest_spec`/`_add_example_row` widen additively to accept Q2's dict-shaped
rows (`{"inputs", "expected", "tol"?, "unordered"?}`) alongside the original
`(inputs, expected)` 2-tuple — a mechanical shape dispatch on the Python
type of each example, never a decision.

## 3. The engine limitation this phase discovered and worked around (no Rust touched)

**`ProgEval`'s real executor cannot run a bare `Fold` expression whose
`source` is a `Prog*` node** — confirmed empirically
(`{'result': None, 'halted': False, 'trap': 'expr:unsupported_over_prog'}`)
for `Fold{source: ProgCallExtern("range", ...), ...}` evaluated directly
under `ProgReturn`. `Fold` is a plain (non-`Prog`) DSL term; its own
evaluator (`term.rs`) calls the RAW `evaluate()` on `source`, which leaves
`ProgCallExtern` inert (`Value::None`) by the structural-honesty contract —
so a scalar-fold construction's literal `Fold` term can never be embedded
directly into an EXECUTED program.

**Fix, entirely in Python, no Rust:** `_lower_scalar_fold_stmts` LOWERS a
computed-source Fold into the EXACT statement shape `sum_of_list_spine`
already proves works end to end — `ProgAssignVar(acc, init)` +
`ProgForEach{var, iter: <the computed source>, body: ProgAssignVar(acc,
body)}` + a final read of `acc` (either a `ProgReturn` or an assignment to
a `final_expr` live var `vK`) — a `ProgForEach` statement's `iter` field IS
evaluated Prog-aware (confirmed: the identical range()-sourced loop,
written as statements, executes correctly for n=1..5, factorial and
sum-to-n both). Used at all three sites that ever embed a scalar-fold term
into an executable program: `splice_binding` (rung-1 direct bind),
`_splice_fold_step` (a solved hole's body spliced back), `_splice_final_expr`
(a scalar-fold cover's value assigned to a live var). A companion helper,
`_eval_covered_term`, REPLAYS the same accumulation in Python (materialise
`source` via `_fold_source_list`'s ProgEval execution, then loop the
`body` through raw `evaluate()`) for `_derive_final_expr`/`_trace_final_expr`'s
own PREFIX evaluation of a covered construction's value on a row — this is
what makes `v1` correctly equal the true factorial/sum value instead of
the constant `init` a naively-inert evaluation would have produced.

This is a **fixed, general structural transformation** — the write-side
twin of `code_writing._term_to_statements`'s own "a Fold becomes an init
line + a for-loop" rule, reproduced at Prog-IR JSON grain instead of
Python-source-text grain (that function renders text for a human reader;
this one builds an executable IR). No new decision; every dispatch is a
structural type check (`term.get("type")=="Fold"` and `source.get("type")
!= "Var"`), the SAME class as the existing `_DERIVERS`/`_SPLICERS`/
`_TRACERS` kind-keyed dispatch tables.

## 4. Guard-widening safety discipline

Every edit to an EXISTING rule adds **only** a clause that is trivially
satisfied for every pre-Q4 scenario (De Morgan complements of brand-new,
previously-impossible predicates):

| rule edited | new clause | why byte-identical pre-Q4 |
|---|---|---|
| `ps_goal` | mint `ps_enum_round`/`ps_enum_round_budget` | new attrs, additive |
| `ps_descend_mark` | `Or[<original list-row check>, <scalar/branch cover>]` | the new Exists needs `tmpl_scalar_fold`/`tmpl_branch`, which no pre-Q4 construction carries |
| `ps_enumerate_mark` | its OWN embedded copy of the descend-applicability check (found and fixed as a **real bug** — see §6) widens IDENTICALLY | same reason |
| `ps_plan_final_expr` | waits for the branch_arm plan to be inapplicable-or-tried too (Occam order) | `tmpl_branch` didn't exist pre-Q4 |
| `ps_exclude_failed` / `ps_ce_exhausted` | `Not(<enum-retry-eligible>)` | the predicate needs `ps_rung_enumerate==1` AND no folded hole AND round budget remaining — a state that (empirically) only arises via repair of a NEW-mechanism accept |
| `ps_row_pass` / `ps_row_fail` | `Not(<tol-or-unordered flag set>)` | neither flag attr existed pre-Q4 |

Full regression proof: every arc-1/P7-A/P7-B suite in the required sweep
(below) reproduces byte-identically except ONE test, reported honestly in
§7 as a genuine, understood, non-required drift.

## 5. Honest residuals

1. **branch_arm's two arms are solved by DIRECT `SynthEnumerate` calls, not
   full recursive sub-goals.** The P7-A design philosophy ("the hole
   becomes a sub-goal that runs the SAME ladder") is NOT followed here —
   each arm gets ONE search call over its own row partition, never a
   further descend/repair-eligible sub-Goal. For the MBPP-shaped mass this
   targets (two-way piecewise scalar functions), this is sufficient and
   real (verified); a THIRD-level piecewise split, or an arm whose own
   function needs further descent (e.g. a fold), is out of this phase's
   reach and would need the fuller (and considerably more complex, see the
   design exploration this phase went through) two-sequential-plan
   architecture. Named, not silently narrowed.
2. **Variable-name collision if two scalar-fold covers combine in one
   `final_expr` plan.** `_lower_scalar_fold_stmts` reuses the construction's
   OWN `acc_name`/`var_name` (e.g. both `factorial_of_n_spine` and
   `range_sum_spine` happen to use `acc`/`x`) rather than renaming per
   cover-index. Not exercised by any current construction pair (no fixture
   or gate combines two scalar-fold covers in one plan); a real, small fix
   if/when that combination is needed.
3. **`fold_up`'s own row-verdict lane (`fu_ok`/`fu_got` vs `expected`) does
   NOT consume `cmp_ok`/tol/unordered** — only the main `eval_and_record` →
   `ps_row_pass`/`ps_row_fail` path does (item 4's explicit scope). A
   descent-repaired accept over a tol/unordered spec would use PLAIN
   equality at fold-up time. No current gate combines descent with a
   tol/unordered spec; named for whoever needs that combination.
4. **Repair/localization has no tracer for `branch_then`/`branch_other`
   folded holes** (`_TRACERS` has no entry for them) — a counterexample
   against a branch_arm accept always falls to the honest global CEGIS
   path (`ps_localize_refuse_descended`, since `ps_trace_skel_agree` reads
   0 with no tracer) rather than localizing into one arm. Correct and
   safe (verified: no new-hole-shape confusion), just coarser than it
   could be.
5. **`ps_enum_round_budget` (2) and branch/enum-retry `max_size` (7/9,
   matching the existing whole-goal/hole conventions) are minted
   constants**, not tuned against any corpus — same status as
   `ps_repair_budget`/`ps_max_depth` before them.
6. **The scalar-fold constructions' stored per-item body (`Times`/`Plus`)
   is CORRECT, not a "wrong on purpose" placeholder** (an earlier design
   in this phase used a deliberately-wrong `Var(acc)` placeholder
   specifically to force descent every time; this was replaced once the
   engine limitation in §3 made clear that final_expr's `v1` feature is
   USELESS unless the covered construction's body is genuinely correct —
   the la_20 "double each element and total" precedent needs `total_of_list`'s
   real total, not a broken one). A plain, exact request for the
   construction's own accumulation (e.g. "the factorial of n" with no
   transform) now solves DIRECTLY at rung 1, with no descent at all — the
   realistic, intended behaviour once the shape is genuinely held.

## 6. A real bug found and fixed en route

`ps_enumerate_mark`'s own `where` clause carries an INDEPENDENT, seed-JSON-
baked COPY of the descend-applicability check (`DESCEND_APPLICABLE`, from
the P7-A builder script) — it is NOT a live reference to `ps_descend_mark`'s
guard. Widening `ps_descend_mark` alone left this embedded copy stale:
measured live, rung 3 fired IMMEDIATELY for a scalar-loop request, racing
ahead of `ps_descend_mark` because its own applicability check still only
recognised the list-input case. Fixed by structurally locating and
widening the SAME embedded predicate (found via a recursive JSON search for
the `rlst`-named `Exists` node, since the P7-A builder's `DESCEND_APPLICABLE`
constant is private to that script and not otherwise addressable). Caught
by empirical testing before any gate was written — recorded here because it
is exactly the kind of duplicated-predicate trap this project's own
"two independent copies of one condition WILL drift" lesson warns about.

## 7. Full paired sweep — results

| suite | count | status |
|---|---|---|
| `test_program_synthesis_migrated.py` | 17 | green (rule-count pin 43→49) |
| `test_prog_descent_migrated.py` | 17 (15 + 2 additive) | green |
| `test_prog_repair_migrated.py` | 13 (11 + 2 additive) | green |
| `test_descent_widening_migrated.py` (NEW) | 11 | green |
| `test_prog_synthesis_battery_migrated.py` | 21 | **1 informational drift** (below); frozen artifact byte-untouched |
| `test_prog_synthesis_selfimprove_migrated.py` | 5 | green |
| `test_prog_chunks_migrated.py` | 11 | green (re-ran clean; no interference from Q3's concurrent work observed) |
| `test_code_synthesis_baseline_migrated.py` | 11 | green |
| `test_value_domain_migrated.py` | 83 | green |
| `test_prog_ir_migrated.py` | 54 | green |

Total required sweep: 243 green, 1 reported drift, runtime ~8–10s (well
under the ~150s budget).

**The one drift, reported not hidden (the Q1-established precedent for
exactly this shape of finding):**
`test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-
br_10_top_of_three]` — a LIVE-reproduction-vs-frozen-snapshot test (NOT a
hash-pin on the frozen artifact itself, which is untouched) — flips from
the stored `gapped` to a LIVE `accepted_holdout_ok`. Traced precisely: this
task ("top of three", a 3-arg max) has zero codebook cover, so it lands on
rung 3 (whole-goal enumerate) with a first-fit `Max(a, b)` (ignoring `c`,
which coincidentally never wins on the task's own revealed rows); under the
`repair_oracle` protocol's counterexample feed, the NEW `ps_enum_retry_mark`
lever (item 3b above) now excludes that wrong candidate and finds the
correct `Max(a, Max(b, c))` — genuinely converging a task that used to
dead-end. This is the SAME class of finding Q1's own notes documented for
`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
(task 11 drifting `gapped:enumerate_failed` → `accepted_holdout_fail`) and
explicitly did not "fix" (fixing would mean reverting the capability). Per
the arc's own standing rule, this is NOT a "currently-passing row flips to
failing" STOP-defect — it is the opposite direction (a `gapped` row now
solves correctly) — and it is exactly what item 3's mechanism is FOR.

**A second, separately-caused drift found on a NEIGHBOURING team's file
(not in this phase's required sweep, reported for completeness):**
`tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_
live` (Q0-A-owned; that file's own notes already document it as
independently red on this worktree from the sibling Q1.5 track's concurrent
`prog_ir_emit.py` edits) ALSO now differs on task 267 ("sum of the squares
of the first n odd natural numbers") — the recorded interim `construction`
flips from `sum_of_two` to `range_sum_spine` (both are wrong for this task
and both get excluded on the way to the SAME final `accepted_holdout_fail`
verdict — `outcome`/`status` are UNCHANGED, only which wrong codebook
candidate got tried is different, because the task's tokens happen to
contain both "sum" and "natural"). Not a real regression — an internal,
non-outcome-affecting bookkeeping difference on a test this phase does not
own and was not asked to keep green (`baseline 11` in this phase's required
list is `test_code_synthesis_baseline_migrated.py`, confirmed green, not
this file).

## 8. Files

- `seeds/program_synthesis.json` — v1.3.0 → v1.4.0 (43 → 49 rules, 1 → 3
  nodes, 12 → 14 productions).
- `domains/prog_synthesis.py` — widened derivation/splice helpers (see §1–3).
- `tests/test_prog_descent_migrated.py` — +2 additive.
- `tests/test_prog_repair_migrated.py` — +2 additive.
- `tests/test_program_synthesis_migrated.py` — rule-count pin only.
- `tests/test_descent_widening_migrated.py` — new, 11 gates.
- `PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md` — this document.
