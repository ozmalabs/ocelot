# Seven unregistered `TermNode` ops — witness check — RESULTS: GO on `XorList` alone, `Shl`/`BitXor`/`BitAnd` priced and declined, one genuine engine panic fixed en route

Prereg: `UNREGISTERED_OPS_WITNESS_CHECK_PREREG.md`, same worktree/branch. Base
`main @ de1845d` ("Merge mdl-occam-witness-pricing: witness-priced literals,
the Occam-ordering metric fix -- +1 (task 451), zero regressions"), verified
fresh via `git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/unregistered-ops-witness-check`, branch
`unregistered-ops-witness-check` — **not merged to `main`, not pushed**, left
for the orchestrator to independently verify per this session's explicit
instruction.

---

**HEADLINE: of the three ops the PREREG found genuine witnesses for (`Shl`,
`BitXor`, `BitAnd`), only ONE — `XorList`, a new `OpKind::ListUnary` fold
reduction over the already-shipped `BitXor` `TermNode` (task 119) — survives
live measurement. `Shl` (task 274, single-op witness) and the joint
`Shl`+`BitXor`+`BitAnd` composition (task 228, single witness) were BOTH
built, BOTH measured, and BOTH declined after live regression evidence —
twice over, not once. The final, shipped, GO build is `XorList` alone:
`full` 88/88 and `content_stripped` 87/87 byte-identical to baseline (zero
gained, zero lost), `official` 114→115 (gained {119}, lost {}). `Pow`,
`BitOr`, `Lshr`, `Ashr` remain a confirmed, honest null — zero witnesses in
the current failing population (PREREG §1.2-1.3, re-confirmed unchanged
here).**

**A genuine, pre-existing engine panic was found and fixed en route, unasked
for but necessary: `Shl`'s own exposure let the search construct
`1i64 << 63 == i64::MIN`, and `TermNode::Mod`'s evaluator used
`i64::rem_euclid`, which panics UNCONDITIONALLY (not merely under
`overflow-checks`, per Rust's own stdlib docs) on `i64::MIN % -1` — crashing
the entire `evaluate()` call, not just producing a wrong answer. Fixed with
`wrapping_rem_euclid`, mirroring the EXACT existing precedent
`TermNode::IDiv`'s own `wrapping_div` already sets for the identical
`i64::MIN / -1` overflow case a few lines away. This fix stays in the build
regardless of the ops-exposure outcome below — it is a real robustness gap in
already-shipped code, independent of whether `Shl` itself ships.**

**Why `Shl`/`BitXor`/`BitAnd` were declined, in two separate measured steps,
both matching this arc's own pre-registered fallback discipline exactly:**

1. **First build** (`Shl`+`BitXor`+`BitAnd`, all three, scoped bare-scalar):
   live-measured full-battery diff showed `full`/`content_stripped` LOST
   `{59, 135, 138, 406, 435}` — a direct reopening of the
   `MODSQRT_SCOPED_FIX` arc's own already-fixed cross-lane mechanism (b),
   because the two call sites that arc scoped (`prog_retrieval.py` rung (d),
   `prog_moves.py`'s shared `_run_synth_enumerate`) only excluded
   `["Mod","Sqrt"]`, never the three new names. Fixed by adding
   `"Shl"`/`"BitXor"`/`"BitAnd"` to both `exclude_ops` lists (§2) — this
   restored 59/135/138/406/435 cleanly (`gained={92,274}, lost={}` on
   `full`/`content_stripped`, `435` restored) but left ONE genuine residual:
   task 435 regressed via a DIFFERENT, unscoped-by-design mechanism.
2. **Second finding**: task 435's true `Mod(a,10)` formula lost a
   candidate-discovery-order race, AT THE UNSCOPED TOP-LEVEL
   `run_enumerate` call itself (the one call site that structurally cannot
   be scoped without also losing `Shl`'s own top-level conversions), to a
   spurious two-row-coincidence `5 - (a & 2)`. This is the SAME
   "mechanism (a)" class `MODSQRT_SCOPED_FIX_RESULTS.md` §3 already named
   and accepted as an unavoidable cost of exposing `Mod`/`Sqrt` at all —
   but it now claims a NEW casualty (435, previously saved by
   `MODSQRT_SCOPED_FIX`'s own scoping) because THREE more ops widened the
   SAME already-widened branch. Per this document's own pre-registered §5
   fallback ("if the joint `Shl`+`BitXor`+`BitAnd` cost for task 228 alone
   turns out disproportionate... keep `Shl`... while REVERTING the
   bare-scalar `BitXor`/`BitAnd` exposure"), `BitXor`/`BitAnd` were dropped
   from the bare-scalar branch, keeping `Shl` alone (§3).
3. **Third finding, worse than the first two**: with `BitXor`/`BitAnd`
   dropped and `Shl` alone still exposed, the NAMED 9-file regression suite
   (not the coarse battery) caught a THIRD, more serious instance of the
   identical mechanism: `test_prog_moves_migrated.py::
   test_mbpp_58_opposite_signs_converts_correctly` — previously-passing
   task 58 ("opposite signs", true formula `(a^b)<0`, needing `BitXor`,
   which this build had just declined) now gets ACCEPTED with a WRONG
   general program, `a > (a << b)`, that happens to coincidentally pass the
   task's own single official held-out row but fails other real inputs
   (e.g. `(100,100)`, same-sign, should be `False`, evaluates `True`). The
   full-battery task-id diff did NOT catch this — task 58 stayed in the
   "pass" set (`lost=[]` on `full`/`content_stripped` with `Shl` alone) —
   because the battery's own per-task check only verifies ONE held-out row,
   and `a > (a << b)` happens to also satisfy that one row. **The coarse
   battery pass/fail metric is not sufficient, on its own, to detect every
   regression this class of search-cost widening can cause; the named
   regression suite's own wider hand-picked probe sets are what actually
   caught this one.** Per the SAME pre-registered fallback logic, `Shl` was
   also dropped from the bare-scalar branch (§4) — the final build exposes
   NEITHER `Shl` NOR `BitXor`/`BitAnd` unconditionally anywhere; all three
   remain `OP_TABLE`-registered (reachable via an explicit `ops` request)
   but not part of any typed default.

**`XorList` was never implicated in any of this** — it is a `ListUnary` Fold
reduction (the `IntersectAll`/`UnionAll` precedent) that never touches the
bare-scalar branch's own op inventory at all, gated narrowly to
`spec_output_is_bare_int` in the list-shaped branch, and it is the one
exposure that survived every regression check clean.

---

## 1. What the PREREG established, unchanged

- `OP_TABLE` re-grepped fresh: `Mod`/`Sqrt` present (post-`MODSQRT_SCOPED_
  FIX`); `Pow`, `BitAnd`, `BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr` absent as
  general entries; `BitAnd`/`BitXor` exist only inside `ZipWith`'s own
  self-contained `ZIP_ELEMENTWISE_OP_NAMES` pool, structurally independent
  of `OP_TABLE` (confirmed by reading both call sites — `build_zip_
  elementwise_op` never consults `OP_TABLE`/`table_kind`).
- Twelve currently-failing test-split tasks' reference code textually uses
  a bitwise/power operator; three are genuine, hand-verified (revealed AND
  held-out, 100% agreement) witnesses:
  - task 274 (`2^(n-1)`) — `Shl` alone, `Shl(1, Minus(a,1))`.
  - task 228 (bit-range-unset check) — `Shl`+`BitXor`+`BitAnd` jointly.
  - task 119 (unique element via XOR self-cancellation) — a NEW list-fold
    op, `XorList` = `Fold(source, init=0, body=BitXor(acc,item))`.
  - The other nine (163, 166, 167, 224, 235, 311, 388, plus false-positive
    396, plus 447) need either genuinely unbounded iteration (the
    already-named, already-deferred `Range` gap) or nothing beyond
    already-composable ops (447's `x**3` = `Times(Times(x,x),x)`).
- Zero witnesses anywhere in the current population for `Pow`, `BitOr`,
  `Lshr`, `Ashr` — re-confirmed unchanged by this document (nothing in the
  build/measurement phase touched that finding).

## 2. First build: all three (`Shl`+`BitXor`+`BitAnd` bare-scalar, `XorList`
list-branch) — regression found, scoped via `exclude_ops`

Implementation (matching the `MODSQRT_SCOPED_FIX` precedent exactly): `Shl`,
`BitXor`, `BitAnd` added to `OP_TABLE` as `OpKind::Binary`; `build_op` match
arms added; pushed onto the bare-scalar `else` branch's LOCAL `v` (never
`DEFAULT_OPS`, so list-shaped specs including task 132 are byte-unchanged);
`term_json` arm added for `Shl` (mandatory — that match is exhaustive and
`unreachable!()`s otherwise; `BitXor`/`BitAnd` already had one, installed
for `ZipWith`'s own rendering). `XorList` added as `OpKind::ListUnary`,
`build_list_unary` arm building the `Fold`+`BitXor` composition,
`list_unary_extra_cost` entry (`4`, the `JoinList`-precedent accounting:
`Lit(0)` init (1) + `BitXor`+`Var(acc)`+`Var(item)` body (3)), gated in the
list-shaped branch to `spec_output_is_bare_int` (reusing the SAME
already-computed variable `ParseInt`'s own gate uses).

**Full paired battery, exact task-id diff against `main @ de1845d`'s own
pristine `results/mbpp_endgame.json` (88/87/114, independently re-confirmed
byte-identical before use):**

```
full:              88 -> 85/257  gained {92, 274}    lost {59, 135, 138, 406, 435}
content_stripped:  87 -> 84/257  gained {92, 274}    lost {59, 135, 138, 406, 435}
official:         114 -> 118/257 gained {56,61,92,119,260,274,464} lost {138,406,441}
```

**A direct reopening of `MODSQRT_SCOPED_FIX`'s own already-fixed
mechanism (b)**: the two call sites that arc scoped
(`domains/prog_retrieval.py`'s rung (d), `domains/prog_moves.py`'s shared
`_run_synth_enumerate`) only excluded `["Mod","Sqrt"]` — confirmed by
direct read, both sites unchanged since that rung. `Shl`/`BitXor`/`BitAnd`
reach the SAME unconditional bare-scalar typed default those two callers
omit an explicit `ops` key for, exactly the way `Mod`/`Sqrt` did before
being scoped. Fixed by adding `"Shl"`, `"BitXor"`, `"BitAnd"` to both
`exclude_ops` lists (one edit apiece, no Rust rebuild — pure data/Python
change).

**Re-measured after the `exclude_ops` fix:**

```
full:              88 -> 89/257  gained {92, 274}  lost {435}
content_stripped:  87 -> 88/257  gained {92, 274}  lost {435}
official:         114 -> 117/257 gained {56,92,119,274} lost {441}
```

135/138/406/59 all restored (matching `MODSQRT_SCOPED_FIX`'s own mechanism-
(b) fix exactly). **435 stayed lost** — a live trace (the SAME
proxy-substitution method `MODSQRT_SCOPED_FIX_PREREG.md` §2 used, a thin
wrapper reassigned to `sub._inner` logging every `SynthEnumerate` call's
caller frame) showed why:

```
task 435 (last digit, true formula Mod(a,10)):
  prog_retrieval.py:614  has_exclude_ops=True  -> found=False tested=136904 halt=max_size
  prog_moves.py:358      has_exclude_ops=True  -> found=False tested=40000  halt=budget
  prog_synthesis.py:1112 has_exclude_ops=False -> found=True  tested=1      term=Lit(0)  [unrelated max_size=1 probe]
  prog_synthesis.py:1406 has_exclude_ops=False -> found=True  tested=5769   term=Minus(Lit(5), BitAnd(Var(a), Lit(2)))
  RESULT: accepted, construction=mck_prog_assign_var_n2_q6
```

`5 - (a & 2)` fits BOTH revealed rows (`a=123: 123&2=2, 5-2=3`; `a=25:
25&2=0, 5-0=5`) by two-row coincidence, is found at the TOP-LEVEL
`run_enumerate` call (`prog_synthesis.py:1406`, which by design has NO
`exclude_ops` — scoping it there would also remove `Shl`'s/`BitXor`'s own
top-level conversions), and is ACCEPTED before the true `Mod(a,10)` formula
is ever reached. This is `MODSQRT_SCOPED_FIX_RESULTS.md` §3's own named
"mechanism (a)" (candidate-discovery-order shift, not budget exhaustion in
this instance — a WRONG candidate is pulled INTO reach) — already accepted
once for tasks 14/164/455/464; here it claims a NEW casualty because three
more ops widened the same branch a second time.

## 3. Second build: drop `BitXor`/`BitAnd` from the bare-scalar branch,
keep `Shl` alone — per the PREREG's own pre-registered fallback

`UNREGISTERED_OPS_WITNESS_CHECK_PREREG.md` §5's own GO/NO-GO criterion
named this exact contingency in advance: *"If the joint `Shl`+`BitXor`+
`BitAnd` cost for task 228 alone (a single witness) turns out to carry a
disproportionate regression cost relative to its own single-task gain, this
document's own honest fallback is to keep `Shl` (2 witnesses) and `XorList`
... while REVERTING the bare-scalar `BitXor`/`BitAnd` exposure."* Removed
`v.push("BitXor")`/`v.push("BitAnd")` from the bare-scalar branch (kept
`OP_TABLE`/`build_op` entries — harmless, reachable via an explicit `ops`
request); trimmed both `exclude_ops` lists back to `["Mod","Sqrt","Shl"]`
(excluding `BitXor`/`BitAnd` there would now be a no-op, so they were
dropped rather than left in defensively). Task 228 (needed all three
jointly) is thereby priced-but-declined — its only witness, and not worth
the measured collateral cost.

**Rebuilt from source** (genuine, non-cached: touched `synth_enumerate.rs`,
1m57s), Rust suite **778 passed, 0 failed, 4 ignored** (byte-identical to
baseline), installed, `record_build()`/`test_engine_provenance_migrated.py`
green.

**Full paired battery, re-measured:**

```
full:              88 -> 89/257  gained {274}         lost {}
content_stripped:  87 -> 88/257  gained {274}          lost {}
official:         114 -> 116/257 gained {119,260,274}  lost {441}
```

Clean on `full`/`content_stripped` — empty lost-set, 435 restored. One
`official`-arm-only residual (441, unrelated to any of this rung's own
witnesses) traced live:

```
task 441 (cube surface area, true formula 6*a*a):
  prog_retrieval.py:618  has_exclude_ops=True  -> found=False tested=200000 halt=budget
  prog_moves.py:360 (x2) has_exclude_ops=True  -> found=False tested=40000  halt=budget
  prog_synthesis.py:1112 has_exclude_ops=False -> found=True  tested=1      term=Lit(0)
  prog_synthesis.py:1406 has_exclude_ops=False -> found=False tested=200000 halt=budget
  RESULT: gapped
```

Pure search-cost inflation (mechanism (a), the OTHER direction — an
in-budget formula pushed OUT of budget by one more op in the same branch)
at the same unscoped top-level call — the identical, already-accepted
residual class `MODSQRT_SCOPED_FIX_RESULTS.md` §7 named for its own
official-arm churn (14/164/455/464). Per this document's own §5 criterion
("official-arm churn... treated honestly as a NAMED, not disqualifying,
limitation... provided `full`/`content_stripped` show a clean, empty
lost-set" — which they do), this alone would have been a GO. It was NOT
the final build, per §4.

Also traced why task 119 (`XorList`'s own witness) converts on `official`
but not `full`/`content_stripped`: under `primary` (used for `full`/
`content_stripped`), only 2 rows are revealed, and `run_retrieval_ladder`'s
rung (d) finds `Last(arr)` (return the array's last element) — a spurious
fit, since both revealed examples happen to have the unique element last
(`[1,1,2,2,3]->3`, `[1,1,3,3,4,4,5,5,7,7,8]->8`) — and accepts it BEFORE
`XorList` ever gets a turn. Under `official`, all 3 rows (including the
held-out one, `[1,2,2,3,3,4,4]->1`, where the unique element is FIRST, not
last) are revealed, so `Last(arr)` no longer fits and the search proceeds to
`XorList`'s correct formula. **This is not caused by this rung's build** —
task 119 was never passing on `full`/`content_stripped` before or after;
it is the SAME "Group A" cheap-degenerate-fit mechanism
`BUDGET_EXHAUSTED_SURVEY_PREREG.md` §4 already named and explicitly
declined to fix (a spec underdetermined by 1-3 revealed rows admits a cheap
coincidental shape) — named here for completeness, not re-investigated.

## 4. Third finding: `Shl` alone still regresses a previously-passing task —
caught only by the NAMED regression suite, not the battery

The named 9-file regression suite, run against the second build (§3):

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live        [EXPECTED, pre-existing]
FAILED tests/test_prog_moves_migrated.py::test_mbpp_58_opposite_signs_converts_correctly     [NEW]
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift  [EXPECTED, pre-existing]
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift [EXPECTED, pre-existing]
```

One NEW failure. Investigated live (`domains.prog_synthesis.
synthesize_from_request` run directly for task 58, "opposite signs",
`(x^y)<0`):

```
task 58 revealed: [(1,-2)->True, (3,2)->False, (-10,-10)->False]
held_out: [(-2,2)->True]
status=accepted, ps_move_sel_kind=orbit_augment
IR: Gt(a, Shl(a, b))   ==  "a > (a << b)"
```

Checked against the actual revealed+held-out rows: `Gt(a, Shl(a,b))` fits
ALL FOUR of them by coincidence (`Shl` returns 0 for any out-of-`[0,64)`
shift amount, per its own bounds guard, and every one of this task's four
rows happens to land in a regime where the comparison works out). It does
NOT fit the general case — `test_mbpp_58_opposite_signs_converts_correctly`'s
own additional hand-picked probe set catches it:
`(100,100)` (same sign, expected `False`) evaluates to `Gt(100, Shl(100,100))
= Gt(100, 0) = True` — wrong. **`opposite_Signs`'s true formula is
`(x^y)<0`, needing `BitXor` — which this build had already declined for the
bare-scalar branch (§3)** — so once `Shl` is available and `BitXor` is not,
the search finds and ACCEPTS a coincidentally-fitting wrong formula instead
of failing honestly.

**Why the full-battery task-id diff (§3) did not catch this**: task 58
stayed in the `full`/`content_stripped` "pass" set the whole time
(`lost=[]` in §3's own measurement) — the battery's own per-task check
verifies exactly ONE held-out row (`(-2,2)`), and `Gt(a, Shl(a,b))` happens
to also satisfy that one row. **This is the headline methodological finding
of this document: the coarse pass/fail battery, on its own, is not
sufficient to detect every regression a search-space-widening rung can
cause — a wrong-but-holdout-passing accept is invisible to a metric that
only checks one row.** The named regression suite's wider, hand-picked
per-task probe sets are what actually surfaced this one. This is not a new
mechanism in the abstract (any accepted program is only verified against
however many held-out rows exist — this risk exists for every rung in this
arc, in principle) but this is the first time in this arc it has been
CAUGHT concretely, on a real task, by the regression suite rather than the
battery.

## 5. Final build: drop `Shl` too — `XorList` alone

Per the SAME pre-registered fallback logic (§3's own citation, applied a
second time): `v.push("Shl")` removed from the bare-scalar branch entirely
(kept `OP_TABLE`/`build_op`/`term_json` registration — harmless, reachable
via an explicit `ops` request); both `exclude_ops` lists trimmed back to
`["Mod", "Sqrt"]` (the pristine `MODSQRT_SCOPED_FIX` state — `Shl` is no
longer in the typed default at all, so excluding it would be a no-op).

**Rebuilt from source** (genuine, non-cached: touched `synth_enumerate.rs`,
1m54s), Rust suite **778 passed, 0 failed, 4 ignored**, installed,
`record_build()`/`test_engine_provenance_migrated.py` green.

**`test_mbpp_58_opposite_signs_converts_correctly` re-run alone: PASSES**
(the search reverts to a pre-existing, already-composable, CORRECT formula
once `Shl` is no longer available to distract it — not independently
re-traced to name the exact restored formula, since the test's own
assertion — `ps_move_sel_kind == "orbit_augment"` plus five extra
hand-picked probe points including `(100,100)` — is the authoritative
correctness check and it is green).

**Full paired battery, exact task-id diff against the pristine baseline:**

```
full:              88 -> 88/257  gained {}     lost {}   -- BYTE-IDENTICAL
content_stripped:  87 -> 87/257  gained {}     lost {}   -- BYTE-IDENTICAL
official:         114 -> 115/257 gained {119}  lost {}
```

`det_identical=True` on all three arms. `full`/`content_stripped` show
ZERO task-id movement in either direction — the entire diff of this rung's
final, shipped build is `official`'s own clean `+1` (task 119, via
`XorList`, converting only under the `official` protocol's 3-revealed-row
split for the reason traced in §3).

**Named 9-file regression suite, final build:**

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live        [EXPECTED, pre-existing]
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift  [EXPECTED, pre-existing]
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift [EXPECTED, pre-existing]
3 failed, 241 passed in 173.97s
```

Exactly the 3 known pre-existing pin-drift failures, nothing new — the
brief's own stated bar, met exactly.

## 6. The `Mod` overflow panic — found and fixed, independent of the ops
decision above

While measuring §2's first build, the full battery crashed hard (Rust
`panic!`, not a Python exception) on the very first `full`-arm pass:

```
thread '<unnamed>' panicked at src/term.rs:7723:40:
attempt to calculate the remainder with overflow
```

Root cause: `TermNode::Mod`'s evaluator (`term.rs:7716-7725`, pre-existing,
shipped by `MODSQRT_SCOPED_FIX`, untouched by this rung until now) computed
`av.as_i64().rem_euclid(bi)`. Per Rust's own stdlib documentation,
`i64::rem_euclid` **panics unconditionally** (not merely under an
`overflow-checks` build flag) when `self == i64::MIN` and `rhs == -1` — this
is the identical `i64::MIN`-divisor-`-1` degenerate case `TermNode::IDiv`'s
own evaluator (`term.rs:8006-8015`, a few lines away) ALREADY guards
against, with an explicit comment: *"wrapping_div handles the i64::MIN / -1
overflow case."* `Mod` had no equivalent guard. `Shl`'s own exposure
(`1i64 << 63 == i64::MIN`, reachable once `Shl` is in the search's op
inventory) made this reachable by the search for the first time — a latent
bug in already-shipped code, newly triggered, not a defect introduced by
this rung's own new code.

**Fix** (`term.rs`): `av.as_i64().wrapping_rem_euclid(bi)`, the exact
`wrapping_*` counterpart `IDiv` already uses for the sibling operator.
Verified directly: `Mod(1<<63, -1)` now evaluates to `0` (Python's own
`(-2**63) % -1 == 0` semantics) instead of panicking.

**This fix ships regardless of the ops-exposure outcome** — it closes a
real robustness gap in the engine's own `Mod` evaluator that any future
rung reaching `i64::MIN` (not only via `Shl` — any sufficiently large
intermediate value, e.g. from nested `Times`, could in principle reach it
too) would also have hit. Rust suite `778 passed, 0 failed` both before and
after (this fix does not change any existing test's expected behavior,
since no currently-tested code path previously reached `i64::MIN % -1`).

## 7. What this document does NOT establish

1. Whether `Pow`, `BitOr`, `Lshr`, `Ashr` would show the SAME class of
   regression if built and measured — not attempted, since they have zero
   witnesses in the current population (PREREG §1.3, unchanged).
2. Whether task 228's own joint `Shl`+`BitXor`+`BitAnd` witness could ever
   be shipped via some THIRD scoping mechanism not tried here (e.g. a
   task-shape-conditioned gate narrower than "every bare-scalar spec," or a
   smaller/adaptive search budget specifically for the widened portion of
   the op inventory) — named as a real, unpriced possibility, not attempted
   in this rung (task 228 is a single witness; the cost of building and
   measuring a third scoping mechanism for one task was judged not worth it
   here, matching this arc's own single-variable-rung discipline).
3. Whether other currently-PASSING tasks beyond 435/58/441 hold latent,
   not-yet-measured vulnerability to this SAME "coincidental accept" class
   of regression from some future op-table widening — this document found
   two live instances (435, 58) by exhaustive full-battery diff plus the
   named regression suite, not by a general audit of every passing task's
   robustness to hypothetical future widenings.
4. Whether the `i64::MIN`/`-1` overflow fixed in §6 has sibling gaps
   elsewhere in `term.rs` (e.g. other `rem_euclid`/`div_euclid`/unguarded
   arithmetic call sites) — only the ONE site this rung's own build
   actually triggered was found and fixed; a broader audit was not
   performed.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. GO/NO-GO

**GO on `XorList` alone.** `full`/`content_stripped` are byte-identical to
the pristine `main @ de1845d` baseline (zero task-id movement in either
direction); `official` gains exactly `{119}` with an empty lost-set. The
named 9-file regression suite shows exactly the 3 pre-registered
pre-existing pin-drift failures, nothing new. The Rust suite is
byte-identical to the 778-baseline. Engine provenance confirmed installed
and matching source.

**NO-GO, honestly, on `Shl` (task 274) and the joint `Shl`+`BitXor`+
`BitAnd` composition (task 228)** — both were built, both were measured
through the real pipeline (not assumed), and both were found, via live
evidence rather than guesswork, to reopen the SAME class of regression
`MODSQRT_SCOPED_FIX` already fixed once for `Mod`/`Sqrt`: first as a
scopeable cross-lane reach (fixed), then as an unscopeable top-level
search-cost/candidate-order cost that first cost a previously-passing task
its correct formula outright (435, mechanism (a) pulling a wrong candidate
into reach) and then, even after `BitXor`/`BitAnd` were dropped, cost a
SECOND previously-passing task (58) its correctness silently (a
coincidentally-holdout-passing wrong accept, caught only by the named
regression suite's wider probes, not the battery). Both declines match this
document's own pre-registered PREREG §5 fallback criterion exactly, applied
twice.

**Pow/BitOr/Lshr/Ashr: confirmed null, unchanged from the PREREG** — no
witness in the current failing population, not built, not attempted.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/unregistered-ops-witness-check
git log --oneline -1 main   # de1845d, verify fresh
git diff --stat             # domains/prog_moves.py, domains/prog_retrieval.py,
                             # runners/dsl/src/{synth_enumerate,term}.rs,
                             # + the built .so/.build.json
```

`XorList` hand-check (no code change needed to reproduce, matching every
prior op-exposure rung's own precedent):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
t119 = {'type':'Fold','source':{'type':'Var','name':'a'},'var_name':'item','acc_name':'acc',
        'init':{'type':'Lit','value':0},
        'body':{'type':'BitXor','a':{'type':'Var','name':'acc'},'b':{'type':'Var','name':'item'}}}
for a, exp in [([1,1,2,2,3],3), ([1,1,3,3,4,4,5,5,7,7,8],8), ([1,2,2,3,3,4,4],1)]:
    print('119', a, s._inner.evaluate(t119, {'a': a}), 'expected', exp)
"
```

`Mod` overflow fix hand-check:
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
t = {'type':'Mod','a':{'type':'Shl','a':{'type':'Lit','value':1},'b':{'type':'Lit','value':63}},'b':{'type':'Lit','value':-1}}
print('Mod(1<<63, -1) =', s._inner.evaluate(t, {}))  # 0, no panic
"
```

Copy the eight gitignored fixtures named in prior rungs' RESULTS docs from
the canonical tree's `results/` directory before running anything below
(already done in this worktree).

```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
cd ../.. && bash scripts/engine_build.sh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py \
  tests/test_mbpp_diet_migrated.py tests/test_program_synthesis_migrated.py \
  tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q --tb=line -rf
```

Task-58/435/441 traces (§2-4) reproducible via the same proxy-substitution
method as `MODSQRT_SCOPED_FIX_PREREG.md` §2: a thin wrapper object
reassigned to `sub._inner` logging every `SynthEnumerate`-typed
`evaluate()` call's caller frame (via `inspect.currentframe().f_back`),
then calling `domains.prog_synthesis.synthesize_from_request` normally for
the task in question.
