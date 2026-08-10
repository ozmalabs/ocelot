# PROGRAM SYNTHESIS ARC 5 FINAL — cross-phase reconciliation + ONE clean
# re-derived measurement

**Date:** 2026-08-01. Reconciles the cross-phase test drift left by three
concurrent builds landing on top of each other (the rational value domain,
commit `72ed5096a5`; the exact-first rung, commit `ec41d3001c`; the orbit/
decomposition moves, commit `4509632994`), and re-derives the MBPP number
ONE time, cleanly, at the fully reconciled state. Companion docs:
`PROGRAM_SYNTHESIS_ARC5_MOVES.md` (the moves build's own accounting of the
~22 failures this reconciliation resolves), `PROGRAM_SYNTHESIS_ARC5_RATIONAL.md`
(the rational-domain landing), `PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md`
(the exact-first rung). Driver: `scripts/arc5_final_battery.py`. Artifact:
`results/arc5_final.json`. Gate: `tests/test_arc5_final_migrated.py`.

Per this repo's own standing rule (`PROGRAM_SYNTHESIS_ARC4_PREREG.md`
§AMENDMENT A4): **mechanism first, score second.**

---

## 0. What this document is not

Arc 5 has no preregistration (`PROGRAM_SYNTHESIS_ARC5_SUMMARY.md` already
says so plainly). This document is not a powered endgame — it is a
**reconciliation and re-measurement**: three sub-phases landed concurrently,
each quoted a different "current" MBPP number under a different engine/seed
combination, and the standing discipline this repo enforces
(`results/failure_baseline.json`'s own gate; the retracted "optional-dep"
note in `CLAUDE.md`) is that a baseline is a list, re-derived, never carried
forward as a label. This is that re-derivation.

---

## 1. JOB 1 — the reconciliation outcome

### 1.1 What was found

The three concurrent builds left **exactly 22 failing tests** across the
20-file arc-4/arc-5 regression sweep (`test_prog_moves_migrated.py`'s own
`_REGRESSION_SWEEP_FILES`) — precisely the count the moves build's own doc
already enumerated. Re-running the sweep at the start of this reconciliation
reproduced all 22, byte-for-byte matching the moves doc's own list; no
additional, undocumented drift was present **in that specific 20-file
sweep**.

However, casting a wider net (running the full `test_exact_first_migrated.py`
sweep, which additionally covers `test_mbpp_endgame_migrated.py` and
`test_mbpp_arc3_endgame_migrated.py` — two files OUTSIDE the moves build's
own file-ownership scope, and therefore never checked by it) found **one
more genuine failure the moves build never saw**:
`test_mbpp_endgame_migrated.py::test_pinned_task_reverifies_live[content_stripped-464-pass]`.
This traces to the SAME root cause as two of the reconciliations below (task
464's coincidental fit) and was fixed the same way.

### 1.2 Attribution-aware fixes (23 tests total, across 12 files)

| class | count | files | disposition |
|---|---|---|---|
| (a) literal `seed["version"]` string pins | 5 | `test_exact_first_migrated.py`, `test_verdict_discrimination_migrated.py`, `test_budget_isolation_migrated.py`, `test_retrieval_migrated.py`, `test_reject_informs_repair_migrated.py` | bumped `1.9.0/66` → `1.10.0/70`, dated, chain of "why" comments preserved |
| (a2) self-referential nested sweep gates | 2 | `test_exact_first_migrated.py`, `test_prog_moves_migrated.py` | allowlists pruned to the 2 genuinely-remaining items (see §1.3) |
| (b) MOVE A converts `br_10` (and a differently-named "top of three" fixture hitting the SAME symmetric-max mechanism) | 9 | `test_descent_widening_migrated.py` (2), `test_reject_informs_repair_migrated.py` (7 incl. 2 new: task 404's genuine-defect claim and the 26-way diff) | re-expressed in terms of the mechanism: preserved what each test PROVED (the reject/reopen mechanism, isolated where still demonstrable) and verified the NEW convergence via fresh witness where superseded |
| (b2) MOVE A/B convert MBPP tasks (58, 59, 404 → pass; 162 → honest `accepted_holdout_fail`) | 6 | `test_search_reach_migrated.py` (4), `test_prog_synthesis_battery_migrated.py` (1), `test_arc4_endgame_migrated.py` (1) | new `_ARC5_MOVES_PASS_IDS`/`_ARC5_MOVES_ACCEPTED_HOLDOUT_FAIL_IDS` held out, exactly mirroring the `_ARC5_EXACT_FIRST_PASS_IDS` precedent |
| (c) a NEWLY FOUND, engine-exposed regression outside the moves build's own sweep scope | 1 | `test_mbpp_endgame_migrated.py` | task 464's `content_stripped` pin corrected `pass` → `accepted_holdout_fail`, witnessed |
| (d) pre-existing, verified-independent drift | 2 | `test_descent_widening_migrated.py`, `test_mbpp_baseline_migrated.py` | **left red, on purpose** — see §1.3 |

**23, not 22** — the extra one (464 in `test_mbpp_endgame_migrated.py`) was
found by this reconciliation's own witness-verification work, not by either
of the two builds whose failures were named in the brief.

### 1.3 The two tests left deliberately red

`test_descent_widening_migrated.py::test_sum_to_n_class_scalar_loop_descends_and_holds_out_correct`
and `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
both fail on a task-267 construction drift (`'sum_of_two' != 'range_sum_spine'`).
**Verified directly, as instructed, before touching anything**: checked out
commit `ec41d3001c` (moves' own starting point) into an isolated
`git worktree`, with `domains/prog_synthesis.py`, `seeds/program_synthesis.json`,
and both test files ALL at that commit (the current compiled `substrate_rs`
`.so` copied in — no `cargo` rebuild), and reproduced the SAME failure there.
It predates every phase this reconciliation covers and lives outside every
phase's file-ownership boundary (fixing it needs a change to
`domains/prog_synthesis.py`'s codebook decode order, which this
reconciliation's scope forbids). Left failing, dated, flagged for the
maintainer — never loosened.

### 1.4 The coincidental-fit sweep found a fifth and sixth

Per the brief's own standing rule ("arc 4 caught two coincidental fits, arc
5 caught a third and a fourth — do not let a fifth through"), reconciling
`test_reject_informs_repair_migrated.py`'s big 257-task diff surfaced **two
more, pre-existing** coincidental fits, both from the S6/arc4-era frozen
baseline (`results/arc4_endgame.json`'s `full_a4` arm), now correctly
exposed:

- **Task 92** ("is this number undulating?"): the frozen `pass` program is
  `Eq(a, Div(1, Div(1, a)))` — a mathematical **tautology**. Under exact
  arithmetic, `1/(1/a) == a` for every nonzero `a`, so this program returns
  `True` universally — proven directly (`a=1991, 123, 456, -7` all give
  `True`), which cannot correctly answer a predicate the task's OWN revealed
  row says is sometimes `False` (`a=1991 → False`). It only ever "passed"
  because the pre-rational-domain engine's floating-point `1/(1/a)`
  round-trip introduced just enough rounding noise on some inputs to
  occasionally read as unequal — pure numerical luck, not correctness.
- **Task 464** ("do all dict values equal a target?"): the frozen `pass`
  program is `Gt(b, 10)` — it **never reads the dict parameter `a` at
  all**. Proven wrong directly: `a={x:1,y:2}, b=11 → Gt(11,10)=True` but
  the correct answer is `False` (no value equals 11); `a={x:7,y:7}, b=7 →
  Gt(7,10)=False` but the correct answer is `True` (every value equals 7).
  Structural detection (D3, "unread declared parameter") did NOT catch this
  — not a detector bug: `a` never varies across ANY of the task's own 3
  corpus rows (all three revealed+held-out rows use the identical dict), so
  from the data alone "`a` is unread" and "`a` happens not to vary" are
  genuinely indistinguishable. This is a real spec-quality gap in the MBPP
  corpus, not an engine or detector defect.

Both are corrected in the current measurement (92 → `gapped:enumerate_failed`,
464 → `accepted_holdout_fail`) as a side effect of the rational-domain
engine landing (see §3), not because anyone re-verified them by hand before
this reconciliation. **No further coincidental fit was found** among the
current 35 passes (see §4's witness scope).

---

## 2. THE CLEAN NUMBER

**35/257 = 13.6% [9.96%, 18.35%] (Wilson 95% CI) over the runnable 257-task
MBPP test split; 35/427 = 8.2% [5.95%, 11.19%] over the whole vendored
corpus** (`results/arc5_final.json::aggregates`). Twin-run byte-identical
(`outcome_hash_run1 == outcome_hash_run2`), reproduced a second time on an
independent live run (`tests/test_arc5_final_migrated.py::
test_live_twin_run_reproduces_the_frozen_pass_set`).

This **supersedes** all three in-conversation numbers (34, 32, 35) — see §3
for why they differed and why 35 is the correct, final figure.

### 2.1 Per-id attribution — the paired diff against arc-4's `full_a4` (28/257)

| task | arc-4 `full_a4` | arc5 final | attribution |
|---|---|---|---|
| 82, 85, 139, 233, 276, 312 | `gapped:enumerate_failed` | **pass** | `exact_first_solved` — the `k·C^p·prod(arg^e)` geometry family, rational parameters + a cross-frame constant |
| 58, 404 | `gapped:structural_verdict_reject` | **pass** | `moves_solved` — MOVE A, orbit augmentation (full symmetry group), witnessed |
| 59 | `gapped:enumerate_failed` | **pass** | `moves_solved` — MOVE B, intermediate decomposition, witnessed |
| 162 | `gapped:enumerate_failed` | `accepted_holdout_fail` | `moves_engaged_not_solved` — an honest 2-row coincidental fit MOVE B finds and the held-out check correctly catches (NOT a wrong pass) |
| 14, 430 | `gapped:structural_verdict_reject` | `gapped:enumerate_failed` | `moves_engaged_not_solved` — MOVE B selects `intermediate_factor` but the final apply does not converge; still gapped either way |
| 103, 125, 126, 228, 304, 396, 414, 432 | `gapped:structural_verdict_reject` | `gapped:enumerate_failed` | `neither` — S6's OWN reject/reopen mechanism (predates all three arc5 builds), tries and honestly fails |
| 397 | `gapped:structural_verdict_reject` | `gapped:enumerate_failed` | `exact_first_engaged_not_solved` — the exact rung's own numeric-eligibility guard runs and correctly fails it (median-of-three is not a `scaled_power_product`/`sum_of_two_terms` shape); the outcome move itself is S6's reopen, same as the row above |
| 164 | `gapped:structural_verdict_reject` | `gapped:no_shape` | `neither` — S6 reopen, different specific gap label |
| 92 | **pass** | `gapped:enumerate_failed` | `neither` — engine-exposed coincidental-fit correction (§1.4) |
| 464 | **pass** | `accepted_holdout_fail` | `neither` — engine-exposed coincidental-fit correction (§1.4) |
| 77 | `accepted_holdout_fail` | `gapped:enumerate_failed` | `neither` — shares 92's exact decoy exemplar; already non-passing both before and after, zero score effect |

**Net: +7 passes** (9 gained: 82/85/139/233/276/312/58/59/404; 2 lost:
92/464, both proven-wrong corrections, never a genuine capability loss).
25 ids changed in total; every changed id is accounted for by exactly one
of: exact-first, moves, or a pre-existing coincidental-fit correction the
rational-domain engine change exposed. **No id moved into a wrong pass
anywhere in the 257-task split.**

---

## 3. THE 34-vs-32-vs-35 DISCREPANCY, EXPLAINED

Three numbers were quoted for "the current MBPP score" at nominally the
same moment: **34** (exact-first's own doc), **32** (moves' own "before"
arm), **35** (moves' own "after" arm, matching this document's own §2
figure). The 34-vs-32 gap at the SAME nominal commit was the unexplained
part, and it is exactly the stale-baseline failure mode this project has
been bitten by before.

**Candidates considered and ruled out:**

- **Seed/Python state.** `git diff ec41d3001c 4509632994^ -- domains/prog_synthesis.py seeds/program_synthesis.json`
  is **empty** — neither file changed between exact-first's landing and
  moves' own starting point. Moves' "before" arm reverting these two files
  to `ec41d3001c` via `git show` was therefore a byte-identical no-op; the
  seed/Python content it measured is IDENTICAL to exact-first's own final
  committed state. Not the cause.
- **`domains/prog_exact.py`'s rational rendering.** This file DID change
  (the rational-domain commit switched the fitted `k` parameter from a
  runtime `Div(int,int)` to an exact rational `Lit`). Tested directly: swap
  in the `ec41d3001c` (pre-rational) version of ONLY this one file, current
  engine, current seed — byte-identical outcomes on all 6 geometry tasks
  either way. Not the cause.
- **Nondeterminism.** Every arm in this measurement, and in every arc5
  sub-phase's own battery, is twin-run byte-identical. `SynthEnumerate` is a
  pure deterministic search. Ruled out.

**Confirmed cause: ENGINE-STATE.** The compiled `substrate_rs` binary was
rebuilt for the rational-domain landing (`72ed5096a5`) BETWEEN exact-first's
own "34" measurement and moves' "before" measurement. That commit
restructured `ProgEval`'s dispatch **globally** ("the compositional core
runs unconditionally") and widened `SynthEnumerate`'s own literal search
space to include exact rationals — a change with corpus-wide reach, not
scoped to the exact-family rung. This engine change, entirely on its own
(independent of any seed or Python file), corrected the two pre-existing
coincidental fits named in §1.4 (tasks 92 and 464): **34 − 2 = 32.**

**Reproduced live, not just argued:** `git worktree add --detach <tmp>
ec41d3001c`, copy the CURRENT `substrate_rs` `.so` into it (no `cargo`
rebuild — reuses the artifact this repo already has), run
`scripts/mbpp_arc3_battery.py`'s own `run_pass` there. Result: **32/257**,
EXACTLY reproducing moves' own "before" figure — with the 6 geometry ids
`pass` (exact-first, unaffected), tasks 58/59/162/404 correctly NOT yet
`pass` (this worktree predates moves), and tasks 92/464 correctly NOT
`pass` (`gapped:enumerate_failed` / `accepted_holdout_fail`) — confirming
the engine alone, with `ec41d3001c`'s own seed/Python content completely
unchanged, accounts for the full gap: 28 (pre-exact-first baseline) + 6
(geometry) − 2 (92, 464) = 32.

**Conclusion:** 34 and 32 are BOTH honest numbers for the engine state each
was measured under — this is the same standing lesson `CLAUDE.md`'s own
retracted "optional-dep" note already names (a status line is
condition-dependent and must carry its condition), not an error in either
measurement. 35 (moves' "after") = 32 + 3 (58, 59, 404, moves' own genuine
conversions). **This document's §2 number (35) is the ONE clean
re-derivation at the fully reconciled state and supersedes all three.**

### 3.1 A live collision with a FOURTH, concurrent, uncommitted build

While finishing this measurement, a **separate, concurrently-running agent**
was found live-editing this repo's SAME shared working tree — an
uncommitted "arc6 property verdict" build (`domains/prog_property.py`,
`seeds/program_properties.json`, a modified `domains/prog_synthesis.py` and
`seeds/program_synthesis.json` bumped to an uncommitted v1.11.0/73 rules).
Two consecutive in-place runs of `scripts/arc5_final_battery.py` produced
**different** results (25 vs. 59 changed ids) purely because that
concurrent, uncommitted edit landed mid-run — not because of any
nondeterminism in the reconciled arc5 stack. The final measurement in this
document was taken from an **isolated `git worktree add --detach` checkout
of the actual committed `HEAD`** (with the current compiled `.so` copied
in), reproduced byte-identically there, and is unaffected by that
concurrent work (which remains uncommitted and out of this reconciliation's
scope — arc6 is not one of the three builds this document reconciles).
This is the SAME failure mode as §3 happening live, a third time, caught in
real time rather than repeated. `results/arc5_final.json::head` records the
exact commit measured so this is independently re-verifiable — the
concurrent arc6 work continued landing measurement-only commits WHILE this
reconciliation was being finished (HEAD moved from `6ee58f39d1` to
`b7f02e9c24` between two consecutive isolated re-checks), and the isolated-
worktree measurement was re-run and reconfirmed byte-identical (35/257,
identical attribution) at each new HEAD — the property-verdict rule
landing itself remained uncommitted (seed `v1.10.0`/70 rules at every HEAD
checked) throughout this reconciliation, so it never actually entered the
"final committed state" this document measures.

---

## 4. WITNESS VERIFICATION — every pass, held-out AND a constructed witness

**Scope, stated honestly:** every id that DIFFERS from the arc-4 `full_a4`
baseline (10 ids: 6 exact-first geometry + 58/59/404 moves passes, plus the
2 engine-exposed corrections) carries a **hand-derived, task-specific
constructed witness**, verified beyond the corpus's own rows:

- The 6 geometry passes are checked with a **generic power-law scaling
  witness**: the family's shape is `k·C^p·prod(arg_i^e_i)`, so doubling one
  argument must scale the output by EXACTLY `2^e_i`, independent of
  `k`/`C`/every other argument — checked at fresh inputs the corpus never
  exercises. This is engine self-consistency, not a per-task formula
  lookup, and it would catch a rendering/argument-order bug the tiny
  2-3-row corpus check cannot.
- Tasks 58 (`0 > a*b`), 59 (`3n² − 2n`), and 404 (`Min(a,b)`) are checked
  against 4-5 hand-constructed input tuples each, values the task's own
  revealed+held-out rows never use.
- Tasks 92 and 464's OLD frozen programs are proven wrong-in-general
  directly (§1.4).

Ids **unchanged** from the `full_a4` baseline (the other 25 passes) are
**not** re-witnessed from scratch here — they predate every phase this
reconciliation covers, were already inside arc4 S2's own structural-verdict
ceiling accounting (40/76 union ceiling), and nothing in this reconciliation
touched their construction. Every accept, changed or not, is structurally
checked by the pipeline itself (`ps_structural_reject`/`ps_structural_clear`)
before it can ever reach `pass` — reported as the mechanical fact it is, not
claimed as independent new evidence for this reconciliation's own scope.

**Result: no fifth coincidental fit reached `pass`.** Two were found and
corrected (§1.4) — properly the "fifth and sixth" per the arc's own running
count (arc4: two; arc5: a third and a fourth, the fourth caught mid-build
and never reaching pass).

---

## 5. REMAINING-FAILURE TAXONOMY (257 runnable tasks)

| outcome | n | share |
|---|---|---|
| `gapped:enumerate_failed` | 117 | 45.5% |
| `accepted_holdout_fail` | 79 | 30.7% |
| **pass** | **35** | **13.6%** |
| `gapped:structural_verdict_reject` | 14 | 5.4% |
| `gapped:no_shape` | 6 | 2.3% |
| `runner_exception:TypeError` | 3 | 1.2% |
| `gapped:exhausted` | 2 | 0.8% |
| `not_recognized` | 1 | 0.4% |

The `runner_exception:TypeError` residual (3 ids) is a pre-existing
serialisation edge case in `ingest_spec` on non-JSON-native row values
(e.g. a `set`-typed literal argument) — unrelated to this reconciliation,
not investigated further here (out of scope; named so it is not mistaken
for a witness gap).

---

## 6. HONEST LIMITS

- Arc 5 has no preregistration and no powered endgame (per its own
  standing note) — this document's claims rest on paired identity lists
  and constructed witnesses, not CI-separated hypothesis tests, except
  where a Wilson CI is explicitly reported (§2).
- Witness verification (§4) is scoped to CHANGED ids; the 25 unchanged
  baseline passes rely on the pipeline's own structural-clearance guarantee
  plus arc4 S2's prior audit, not a fresh per-task witness in this
  document. A future arc that wants to re-audit the FULL 35 from scratch
  should say so explicitly, per this repo's own "a baseline is a list,
  read it" rule.
- Structural detection's own limits are now named precisely, not
  hand-waved: it cannot catch a parameter that never varies across a
  task's own corpus rows (464's shape), and it has no detector class for a
  vacuous/tautological formula (92's shape) — a real, open detector-
  coverage gap, distinct from either an engine bug or a scope exclusion.
- The `test_descent_widening_migrated.py`/`test_mbpp_baseline_migrated.py`
  task-267 drift (§1.3) is left red on purpose, verified pre-existing, and
  requires a `domains/prog_synthesis.py` change (codebook decode ordering)
  outside every phase's file-ownership boundary considered here.
- The measurement environment (§3.1) was concurrently, actively edited by
  another agent's uncommitted work during this reconciliation; the final
  number was isolated from that via a clean worktree checkout, but a
  reader re-running this WITHOUT the same care could reproduce either the
  contaminated or the clean result depending on timing — this is named
  explicitly rather than left as a silent hazard for the next reader.

---

## Files

- `scripts/arc5_final_battery.py` (new) — the measurement driver, reusing
  `scripts/mbpp_arc3_battery.py`'s own `run_pass`/`run_arm`/`boot_full_r3`/
  `prog_eval`/`holdout_verdict` verbatim.
- `results/arc5_final.json` (new) — the frozen artifact.
- `tests/test_arc5_final_migrated.py` (new, 16 tests) — schema/derivation,
  determinism, 3 pinned live re-verifications, witness-coverage gates.
- Reconciled (dated, attribution-aware, never blanket-loosened):
  `tests/test_exact_first_migrated.py`, `tests/test_verdict_discrimination_migrated.py`,
  `tests/test_budget_isolation_migrated.py`, `tests/test_retrieval_migrated.py`,
  `tests/test_reject_informs_repair_migrated.py`, `tests/test_descent_widening_migrated.py`,
  `tests/test_search_reach_migrated.py`, `tests/test_prog_synthesis_battery_migrated.py`,
  `tests/test_arc4_endgame_migrated.py`, `tests/test_mbpp_endgame_migrated.py`,
  `tests/test_mbpp_baseline_migrated.py` (2 pins left red on purpose, §1.3),
  `tests/test_prog_moves_migrated.py` (allowlist pruned to the 2 remaining
  known-red items).
