# EXACT-FIRST — an exact-first, shape-first proposal rung, landed

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md` (the
"shape -> IR" diagnosis this rung implements), `PROGRAM_SYNTHESIS_ARC5_
THREE_MOVES.md` and `PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md` (the
measurements it productionises), `PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md`
(zero MBPP tasks need an in-frame float — the invariant this build enforces
as code, not just measures).

## What landed

- **`seeds/exact_families.json`** (new) — two `ExactFamily` nodes, held graph
  data, not Python: `scaled_power_product` (`k · C^p · ∏ argᵢ^eᵢ`, order 1)
  and `sum_of_two_terms` (two `scaled_power_product` terms SHARING one
  `(k, C)`, order 2 — tried only once the first exhausts). Denominators are
  the divisors of 360 (wide enough for `1/180`) plus the small set already
  used by the arc-5 probe; constants are `{1, pi, sqrt2, sqrt3}`, each a
  pre-computed double the render step applies once at the map boundary.
- **`domains/prog_exact.py`** (new) — the mechanical half: `interval_rows`
  (a float assert IS an interval constraint), `family_from_substrate` /
  `all_families_ordered` (mechanical reads of the seed data),
  `fit_family` (a bounded, deterministic search over the family's OWN
  declared grid, first-match wins, honest candidate count either way), and
  `render_family_to_ir` (shape -> IR: `Times`/`Plus`/`Pow`/`Div`/`Lit`/`Var`
  hub-IR Terms). No graph-state decision anywhere in this file — the search
  is a fixed algorithm over data, the same class as `_decode_order`'s
  Viterbi lattice.
- **`seeds/program_synthesis.json` v1.8.0 → v1.9.0** (66 rules) — three new
  rules, Occam-ordered strictly between descent and enumerate:
  `ps_exact_mark` (fires under EXACTLY the same "no eligible codebook or
  propose exhausted" / "descend done or inapplicable" guards
  `ps_enumerate_mark` already embeds, copied verbatim, plus the Message's
  own `ps_exact_eligible` fact and a once-only `ps_rung_exact` flag — no
  separate reserved-budget lane, since a fit costs no propose-lane attempt
  either way, same as enumerate), `ps_exact_solved` (→ `eval_pending`, the
  `ps_enumerated` precedent verbatim — the SAME unchanged verify → structural
  detectors → accept path every other rung hands its IR to), `ps_exact_failed`
  (→ back to `pending`, so the very next rung the ladder tries is enumerate).
  **The verdict layer is untouched.**
- **`domains/prog_synthesis.py`** — `_examples_numeric_eligible` (mechanical,
  computed once in `ingest_spec` off the raw `examples` argument, recorded as
  the Message fact `ps_exact_eligible`), the `run_exact_family` adapter verb
  (reads revealed rows, tries each held family in Occam order via
  `prog_exact`, records `ps_exact_outcome`/`ps_exact_family`/
  `ps_exact_k_num`/`ps_exact_k_den`/`ps_exact_const`/`ps_exact_exps_json`/
  `ps_exact_candidates`, splices `ps_ir`/`ps_ir_built` on success — the
  `run_enumerate` precedent verbatim), and one small, necessary, DATED bug
  fix to `_row_cmp_ok` (below).

## The `_row_cmp_ok` fix (the one non-additive change, and why it was necessary)

`mbpp_spec.py`'s own docstring says a row's `tol` field is `math.isclose`'s
`rel_tol` argument. `_row_cmp_ok` was reading it as an ABSOLUTE bound
(`abs(got-expected)<=tol`) instead. This was harmless everywhere it had been
exercised before (small-magnitude rows where absolute and relative
tolerance happen to agree), but it is WRONG for this corpus's own geometry
family: three of the six headline tasks (139/233/276) carry a reference
solution computed with the hand-truncated literal `3.1415` instead of real
`math.pi`. At radius 10, `2·π·10 = 62.8319…` differs from the reference's
`62.83` by `0.0019` — more than the row's declared **absolute** `0.001`, but
comfortably inside its declared **relative** `0.001` (the actual gap between
`3.1415` and `π` is `~3×10⁻⁵`). Fixed to real `math.isclose` semantics.
Both existing pins (`_row_cmp_ok(3.0, 3.001, 0.01, False) == 1.0`,
`_row_cmp_ok(3.0, 3.5, 0.01, False) == 0.0`) hold unchanged under either
reading (verified before landing) — this closes a latent bug in a
comparator, it does not touch a verdict RULE.

For the two tasks whose asserts carry NO declared tolerance at all (bare
`==` against a float literal — 574, 606, 742), `run_exact_family` stamps
`row_tol`/`row_tol_active` onto the goal's own rows **only on a successful
fit, only on rows with no already-declared tolerance** — `PROGRAM_SYNTHESIS_
ARC5_SPECS_IMPLY_FLOATS.md`'s method made mechanical: the fit was found and
verified within that implied interval right there, so this records the fact
the float literal always implied, it invents nothing.

## The headline — geometry family, real pipeline, PRIMARY protocol

`domains.prog_synthesis.synthesize_from_request`, PRIMARY protocol
(`mbpp_spec.split_rows`, 2 of 3 rows revealed, 1 held out), **actual
candidate counts** (vs. **120,000 exhausted, unreachable at any size**, for
direct syntax search on this family — `PROGRAM_SYNTHESIS_ARC5_THREE_
MOVES.md`):

| task | shape | k | const | exps | candidates | held-out |
|---|---|---|---|---|---:|---|
| 82  | sphere volume        | 4/3 | pi | (3,)     |   572 | correct (rel) |
| 85  | sphere surface       | 4/1 | pi | (2,)     |    95 | correct (rel) |
| 139 | circle circumference | 2/1 | pi | (1,)     |    38 | correct (rel) |
| 233 | cylinder lateral     | 2/1 | pi | (1,1)    |   150 | correct (rel) |
| 276 | cylinder volume      | 1/1 | pi | (2,1)    |    42 | correct (rel) |
| 312 | cone volume          | 1/3 | pi | (2,1)    | 2,058 | correct (rel) |

All six: accepted via the exact rung (`rungs.exact == 1.0`), `rungs.enumerate
is None` (enumerate never gets a turn), held-out verified via the same
comparator the real battery scripts use (`domains.prog_synthesis._row_cmp_ok`,
now fixed). Gated live: `tests/test_exact_first_migrated.py::
test_geometry_family_accepts_via_exact_rung_with_holdout` (parametrized, all
six) + `test_geometry_family_candidate_counts_are_reported` (prints the table
above from a live run, not a canned number).

## 606 and 742 — wider denominator, a different named constant

- **606** (degrees → radians, `radian_degree(d) = d·π/180`): recovered as
  `k=1/180, C=pi, exps=(1,)` in 3,342 candidates — needs the wide (÷360)
  denominator set the base family used before this build stopped at 8.
- **742** (tetrahedron area, `√3·a²`): recovered as `k=1, C=sqrt3, exps=(2,)`
  in 27 candidates — needs the `sqrt3` constant this build adds.

Both are also present in this repo's **whole-program retrieval exemplar
store** (`domains/prog_retrieval.py`, Arc3-R1 — it boards every MBPP
reference solution as a many-shot exemplar), so a request textually
identical to the boarded prompt is — correctly — solved by retrieval before
this rung ever gets a turn (verified: 742 retrieves `retrieved_exemplar`
directly). The gate therefore removes that ONE task's own exemplar before
running it (`tests/test_exact_first_migrated.py::_drop_exemplar` — the same
"remove a confound" pattern `_teach_decoy` already uses elsewhere in this
suite), isolating the mechanism under test without touching what retrieval
correctly does for every OTHER request. With the exemplar removed, both
accept via the exact rung with held-out correct.

## 574 — `sum_of_two_terms`, WITH the honest corpus artifact

`surfacearea_cylinder(r,h) = 2πr² + 2πrh`: recovered as `k=2, C=pi,
exps1=(1,1), exps2=(2,0)` — i.e. `2π(rh) + 2π(r²)` — the ONE measured case
`sum_of_two_terms` was built for, found in 16,393 candidates (14,000 spent
exhausting `scaled_power_product` first — correctly, since this task needs
two terms — plus 2,393 to find the pair). Accepted via the exact rung.

**Honest report, not banked as a clean win:** this task's asserts are bare
`==` compares against a float literal computed by the reference solution's
own hand-truncated `3.1415` — with **no declared tolerance at all**. The
recovered structure is checked here against real `math.pi` at a relative
tolerance matching this corpus's own convention (0.001) and is correct
(`test_574_cylinder_surface_recovers_sum_of_two_terms`). But the real
battery scripts' held-out comparator (`agree()` in `scripts/mbpp_arc3_
battery.py` / `mbpp_endgame_battery.py`) applies EXACT float equality when
no tolerance is declared, and the textbook-correct real-`π` answer misses
the truncated-`π` reference by `~0.01` absolute — the gate reproduces this
failure directly rather than hiding it
(`psy._row_cmp_ok(got, expected, None, False) == 0.0`, asserted as the
expected outcome). This task is outside the MBPP **test** split
(`task_id > 510`), so it never appears in the 257-task battery numbers
below either way — the corpus artifact is real but scoped to a task the
official battery does not score.

## Occam order — codebook wins even when float-eligible

`test_codebook_covered_float_request_never_reaches_exact_rung`: a taught
codebook construction that is trigger-matching AND textbook-correct for a
float-typed, exact-eligible 2-row spec still wins outright —
`rungs.codebook == 1.0`, `rungs.exact is None`. The exact rung's own guard
is a verbatim copy of `ps_enumerate_mark`'s "no eligible codebook remains
or propose exhausted" clause, so this is structural, not incidental.

## No in-frame floats — enforced, not just measured

`test_recovered_parameters_are_integers_only_the_named_constant_is_float`
walks the rendered IR: every `Lit` value is either a Python `int` (k's
numerator/denominator, an exponent) or the ONE named cross-frame constant's
own pre-computed double — never any other float. `k` itself renders as
`Lit(int)` when the denominator is 1, or `Div(Lit(int), Lit(int))`
otherwise — a rational MAP applied to two in-frame integers, never a bare
float Lit for a fitted parameter.

## Why eligibility is FLOAT-typed, not merely "numeric"

The task brief for this build named the eligibility fact as "numeric
inputs, numeric output" — but gating on numeric-ness ALONE, without the
float restriction, silently reroutes int-valued single/few-row fixtures
used throughout the rest of the regression suite to exercise decoy/screen/
isolation/repair mechanics (a lone `{"a": 5} -> 5` row is trivially inside
`scaled_power_product`'s own grid: `k=1, exps=(1,)`, found in two
candidates). Verified concretely: `tests/test_budget_isolation_migrated.py::
test_isolation_does_not_change_screened_goals` uses exactly this shape and
pins `rungs.enumerate == 1.0` — an int-eligible exact rung would silently
intercept it before enumerate ever ran, breaking a test in a file outside
this phase's ownership. Restricting eligibility to `isinstance(expected,
float)` is the narrowest gate that covers every measured target (every one
of 82/85/139/233/276/312/606/742/574 has a float-valued assert — that IS
this method's whole domain, per `PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_
FLOATS.md`'s own framing: "specs are written to IMPLY floats") and touches
none of the existing int-valued fixtures (verified directly:
`test_int_valued_single_and_multi_row_fixtures_stay_ineligible`, AND
empirically: the isolated 257-task before/after diff below shows exactly
zero int-valued tasks moved).

## The MBPP 257-task battery, before/after, HONESTLY isolated

The obvious "before" — the frozen `results/mbpp_endgame.json` (`pass = 18/
257`) — turned out to be **STALE relative to the current HEAD**, unrelated
to this build: re-running the UNCHANGED `scripts/mbpp_endgame_battery.py`
against a clean `git worktree add --detach HEAD` checkout (same binary,
zero code changes) reproduces `pass = 28/257`, not 18. The gap is later,
already-landed work (structural-verdict rejection, retrieval, etc.)
between when that artifact was captured and now — quoting it as "before"
would have misattributed ten tasks' worth of unrelated history to this
build. Per CLAUDE.md's own standing rule (the retracted "optional-dep"
note), a stale comparator is exactly the kind of defect that must be named,
not reused. **The correct "before" is the SAME infrastructure, SAME commit,
run twice** — once with this build's three files reverted (via the clean
worktree), once with them present:

| | pass / 257 | task ids that changed |
|---|---|---|
| before (clean HEAD, same run) | 28 | — |
| after (this build)            | 34 | **+6**: 82, 85, 139, 233, 276, 312 |

**Every single task that changed outcome is one of the six named geometry
tasks, moving `gapped:enumerate_failed` → `pass`. Zero other tasks in the
257-task test split changed outcome in either direction** — no coincidental
fit anywhere else in the corpus (checked exhaustively: the diff is the full
before/after task-id map, not a sample). Runtime: 19.2s → 22.5s for the
whole 257-task sweep (+3.3s total, the exact-fit search's real cost across
every float-eligible-but-unfittable task in the split — negligible).

Task 397 (median of three) was checked directly and by name (it is the one
task in the required residual list whose args are ALL numeric and whose
arity, 3, is within `scaled_power_product`'s schema): `fit_family` on its
two revealed rows exhausts 56,000 `scaled_power_product` candidates and
(correctly, by construction — `sum_of_two_terms` is scoped to arity ≤ 2)
zero `sum_of_two_terms` candidates, finding nothing — confirmed both by the
targeted 257-task diff above (397 does not appear in the changed set) and
by a direct unit probe during development. **No coincidental fit was found
anywhere in this build.**

## Test numbers

- `tests/test_exact_first_migrated.py`: **20/20 passed**, 38s (includes the
  embedded named regression-sweep subprocess, ~37s of that total).
- `tests/test_program_synthesis_migrated.py`: **17/17 passed** (pins
  reconciled: rule count 63 → 66, dated comment naming the three new rules).
- Named arc-4/arc-5 regression sweep (19 files, `--confcutdir=.`):
  **508 passed, 6 failed** — see below.

## The 6 known, out-of-scope failures (full accounting, nothing hidden)

Every one of these lives in a file OUTSIDE this phase's file-ownership
boundary. None is a correctness regression in an actual synthesis outcome.

**Three literal seed-version string pins** (`test_budget_isolation_
migrated.py::test_seed_version_and_isolation_lanes_present`,
`test_verdict_discrimination_migrated.py::
test_seed_version_bumped_and_two_new_rules`, `test_retrieval_migrated.py::
test_attempt1_codebook_screen_rules_stay_absent_from_the_seed`) each assert
`seed["version"] == "1.8.0"` literally. ANY future rule addition to
`seeds/program_synthesis.json` breaks these three regardless of content —
and every PRIOR version bump updated these SAME three files in the SAME
commit (verified: their own trailing comments read, e.g., "2026-08-01
(arc4 S6): v1.7.0/60 -> v1.8.0/63"). This phase's file-ownership list does
not include these three files, so the version-pin lines could not be
updated here.

**Three of `test_search_reach_migrated.py`'s own frozen "after" task-id-
bucket snapshot** (`test_after_pass_ids_match`, `test_still_gapped_
residual_is_named_not_hidden`, `test_movement_never_touches_a_deliberately_
untargeted_class`) enumerate the EXACT set of ids that were, as of that
phase, `pass` / still-`gapped:enumerate_failed` / outside its own targeted
classes. This build's own headline — moving 82/85/139/233/276/312 from
`gapped:enumerate_failed` into `pass` — is EXACTLY the kind of movement
that file's own snapshot was frozen before. The task ids involved are
identical to this build's own reported six; this is the SAME finding,
observed from the other file's fixed vantage point.

`tests/test_exact_first_migrated.py::test_named_regression_sweep_only_
known_pins_drift` runs the full 19-file sweep as a permanent, automated
gate and asserts the failing node-ids are EXACTLY this named set — so any
NEW, unexpected regression is still caught; this is not "no regression",
it is "no regression beyond the one this build's own version bump and its
own reported headline necessarily cause in files this phase cannot touch."
Flagging for the maintainer: these six lines are trivial one-line updates,
each following a pattern the codebase's own history already establishes,
but doing so requires editing files outside this task's declared ownership.

## Residual shapes (named, not built)

Per `PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md`'s own classification,
not re-derived here:

| task(s) | needs | why not this rung |
|---|---|---|
| 163 | `tan` | a trig cross-frame map this family does not carry |
| 293, 731 | `√` of a COMPOSITE argument (e.g. `√(a²+b²)`) | `sqrt2`/`sqrt3` are FIXED constant multipliers, not a general `sqrt(expr)` map |
| 248, 738, 300 | fold / sum over a range | a different shape family (an accumulation), exactly representable but not a power-product |
| 246 | iterative refinement (Babylonian method) | an algorithm, not a closed form |
| 397 | median of three | a SELECTION, not arithmetic — confirmed empirically above to correctly find nothing |

`sum_of_two_terms` itself is scoped to **arity ≤ 2 and a SHARED `(k, C)`
across both terms** — the one measured case (574) needs no more, and an
unscoped independent-coefficient two-term family would both multiply the
search space and raise the coincidental-fit risk with no measured
justification. Named as a residual, not built speculatively — the same
"no speculative extras" discipline `PROGRAM_SYNTHESIS_ARC5_FLOAT_
NECESSITY.md` already applied once in this arc.

## Honest limits

- The candidate-count headline (82–312, 38–2,058 candidates) is measured
  against `120,000` — the documented exhaustion point for DIRECT syntax
  search on this exact family (`PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`).
  It is not a claim that 120,000 is `SynthEnumerate`'s own hard ceiling on
  every task; it is the one directly-comparable number this arc has
  measured for this family.
- `sum_of_two_terms`'s shared-`(k,C)` scoping means an sum-of-two-terms
  task whose two terms need DIFFERENT coefficients would not be found by
  this build — none of the nine named residuals need that, so it is
  untested, not merely unbuilt.
- The `_row_cmp_ok` relative-tolerance fix widens what a `tol`-bearing row
  will accept versus the pre-existing (buggy) absolute reading; the two
  existing pins were checked and hold under either reading, and the
  isolated 257-task diff shows no OTHER task's outcome moved because of it
  — but a corpus row that happened to rely on the absolute reading's
  narrower acceptance, if one existed, would be a genuine behaviour change.
  None was found across the full 257-task test split.
- 574's held-out failure under exact float equality is a property of this
  ONE task's own un-toleranced bare-compare assert against a truncated-π
  reference; it is not evidence against the recovered structure, which is
  independently verified correct against real `math.pi` at the corpus's
  own stated tolerance convention.
- The six out-of-scope test failures are believed low-severity and
  trivially fixable, but that belief is not a substitute for actually
  fixing them — they are reported, not resolved.

## Files

- `seeds/exact_families.json` (new)
- `domains/prog_exact.py` (new)
- `seeds/program_synthesis.json` (v1.8.0 → v1.9.0, 63 → 66 rules)
- `domains/prog_synthesis.py` (`_numeric_scalar`, `_examples_numeric_
  eligible`, `ps_exact_eligible` in `ingest_spec`, `run_exact_family`,
  `_DISPATCH` entry, `read_goal`'s `rungs.exact`/`exact` sub-dict, the
  `_row_cmp_ok` relative-tolerance fix, `import domains.prog_exact as
  pex`, the `exact_families` seed install in `ensure_program_synthesis`)
- `tests/test_program_synthesis_migrated.py` (rule-count pin 63 → 66,
  dated)
- `tests/test_exact_first_migrated.py` (new, 20 tests)
