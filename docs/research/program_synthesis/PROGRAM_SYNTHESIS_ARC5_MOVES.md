# PROGRAM SYNTHESIS ARC 5 — MOVE A (orbit augmentation) + MOVE B
# (intermediate decomposition), selected by WEIGHTED COLLAPSE

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`
(the three moves and what each is worth), `PROGRAM_SYNTHESIS_ARC5_
ORBIT_RESULT.md` (MOVE A's own measurement), `PROGRAM_SYNTHESIS_ARC5_
WIDEST_GAP.md` (the gap / arity_gap features productionised here), and
`PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md` (the third move — already
landed, seed v1.9.0 — this build sits alongside).

## What landed

- **`domains/prog_moves.py`** (new, mechanical) — orbit-augmentation and
  intermediate-decomposition candidate generation, refutation, group
  closure, and application, all as fixed algorithms over data (the
  `prog_exact.py`/`fit_family` precedent) using the REAL, unmodified
  `SynthEnumerate` Term for every search/score, never a re-implemented
  arithmetic engine.
- **`seeds/program_synthesis.json` v1.9.0 → v1.10.0** (66 → 70 rules) —
  four new rules, Occam-ordered **RUNG 2.6** strictly between the exact
  rung (2.5) and enumerate (3):
  - `ps_move_mark` — entry conditions copied VERBATIM from `ps_exact_
    mark` (no eligible codebook or propose exhausted; example rows
    exist; descend done or inapplicable), PLUS a structural mutual-
    exclusion arm against the exact rung (`ps_rung_exact==1` OR never
    exact-eligible) and the Message's own `ps_moves_eligible` fact.
    Stamps the WEIGHT COEFFICIENTS (`ps_move_w_gap`/`ps_move_w_arity`/
    `ps_move_w_mdl`) onto the goal as graph data.
  - `ps_move_select` — the weighted-collapse Argmax: among every
    MoveCandidate attached to the goal that is BOTH un-refuted AND
    demonstrates a strictly positive `gap` (both are pool-membership
    filters, never weight terms — refutation is a hard veto, and a
    move with zero measured advantage must not preempt blind search),
    picks the highest `w_gap*gap + w_arity*arity_gap - w_mdl*mdl_bits`.
  - `ps_move_none` — no surviving candidate → honest fall-through to
    `pending` (enumerate's normal turn), the `ps_exact_failed` shape.
  - `ps_move_fresh_attempt` — the `ps_enumerate_fresh_attempt` P6.5-
    stall precedent applied to this rung (closes a live bug found on
    the real corpus — §5).
  - `ps_enumerate_mark` was EDITED IN PLACE to add the reciprocal
    mutual-exclusion arm (`ps_rung_moves==1` OR never moves-eligible),
    making the RUNG 2.6 → RUNG 3 ordering structural rather than a
    reliance on engine tie-break order (see §6 — this ordering is NOT
    guaranteed by array position alone, measured directly).
- **`domains/prog_synthesis.py`** — `import domains.prog_moves as pmv`,
  `ps_moves_eligible` stamped in `ingest_spec` (the `ps_exact_eligible`
  idiom), two new `_DISPATCH` entries (`moves_scan` → `run_structural_
  moves`, `move_apply_pending` → `apply_selected_move`).
- **`tests/test_program_synthesis_migrated.py`** — rule-count pin
  66 → 70, dated.
- **`tests/test_prog_moves_migrated.py`** (new, 32 tests).

## MOVE A — orbit augmentation, real pipeline

`br_10_top_of_three`, from its 3 revealed rows
(`(1,9,3)→9`, `(7,2,5)→7`, `(4,4,4)→4`):

| | value |
|---|---|
| candidates minted | 5 (3 audit 2-cycles + the closure `sym_full_S3` + 1 refuted `intermediate_factor` candidate) |
| SELECTED (facts, not hard-coded) | `ps_move_sel_kind=orbit_augment`, `ps_move_sel_key=sym_full_S3`, `ps_move_sel_gap=24708.0` |
| rows added | 10 (13 orbit rows, 3 already present) |
| enumerate (unchanged, on the augmented rows) | `Max(a, Max(b, c))` |
| held-out | `(2,4,11)→11` ✓, `(-3,-9,-5)→-3` ✓ |
| constructed witness (independent of held-out) | `(100,3,47)→100` ✓, `(-1,-50,-2)→-1` ✓ |
| **converted** | **YES** |

The direct-revealed-rows-only decoy (`Max(a,b)`) is exactly the wrong
program `PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md` measured; augmentation
still eliminates it here, reproducing that result live rather than
quoting it: a plain re-run of the SAME direct/augmented `SynthEnumerate`
calls this build makes internally gives `tested=532` (direct) →
`tested=25,240` (augmented) — the SAME two numbers the earlier
measurement reported, byte for byte.

**Selection is real, not hard-coded**: `sym_2cycle_0_1` (the pair the
trap `Max(a,b)` is ALREADY symmetric in) never even reaches candidacy as
a selectable move — see §4 on why individual 2-cycles are audit-only —
and the closure (`sym_full_S3`, generated from all three individually-
sound 2-cycles) is the only relaxation scored, at `gap=24708`, `arity_gap
=1` (the accepted decoy `Max(a,b)` reads 2 of 3 declared args — the SAME
number `PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md` measured for this task).

### Two bonus, genuine MBPP conversions (§7's before/after sweep found these)

| task | function | mechanism | held-out | witness |
|---|---|---|---|---|
| 58 | `opposite_Signs(a,b)` | orbit (full S2) → `0 > a*b` | ✓ | 5 constructed pairs, all correct |
| 404 | `minimum(a,b)` | orbit (full S2) → `Min(a,b)` | ✓ | 4 constructed pairs, all correct |

Both are genuinely, unconditionally correct (product-sign test; literal
minimum) — not coincidental fits (checked below, §5).

## MOVE B — intermediate decomposition, real pipeline, real MBPP fixture

Task 59 (nth octagonal number, `is_octagonal(n) = 3n² − 2n`), PRIMARY
protocol (`n=5→65`, `n=10→280` revealed; `n=15→645` held out):

| approach | candidates tested | outcome |
|---|---|---|
| direct, full default budget (`max_size=9`, `max_candidates=0`→200,000) | **200,000 exhausted** | **not found** — reproduced live (`tested==200000`, `found==False`), not quoted |
| decompose: solve the inner factor `expected/n` alone | **28,490** | found, `n + (n + (n − 2))` (= `3n−2`) |
| compose `n · inner(n)` | 1 step | **CORRECT on held-out**: `n=15 → 645` ✓ |

**~7× cheaper than the direct budget, and it succeeds where direct
search cannot finish at all within the budget it does exhaust.** The
exact candidate counts (28,490 / 200,000) differ from `PROGRAM_
SYNTHESIS_ARC5_THREE_MOVES.md`'s own numbers (8,529 / 200,000) because
that measurement used a different row set; this is the number the REAL
pipeline, with the actual PRIMARY-protocol two-row reveal, produces —
reported honestly rather than reused.

`ps_move_sel_kind=intermediate_factor`, `ps_move_sel_key=factor:a`,
`ps_move_sel_gap=11510.0` (the scoring-time probe is capped at 40,000
candidates for cost control — see §3 — so this gap is `40000 −
28490`, not the full 200,000 headline; the FINAL apply step always
re-runs the inner solve at the engine's own unmodified default budget).

## Selection — weighted collapse, measured two ways

### 1. A live case where gap and arity_gap disagree (br_10 itself)

Every candidate relaxation's `arity_gap` is IDENTICAL for one goal
(computed once, off the direct-only probe's own accepted candidate —
it is a per-goal, not per-relaxation, signal), so the disagreement the
brief asks for is demonstrated more directly by a controlled unit case
(below) — the live evidence br_10 DOES contribute is that `arity_gap=1`
(WIDEST_GAP's own number) and `gap=24708` AGREE here (both point at the
same winner), which is itself worth recording: this build's mechanism
reproduces the earlier, independently-computed `arity_gap` figure
exactly, from first principles, live.

### 2. A controlled case where they disagree — the collapse picks by weight

Two synthetic `MoveCandidate`s on one goal:

| candidate | gap | arity_gap | weight (default: `1·gap + 3·arity_gap − 0.5·mdl`) |
|---|---|---|---|
| `cand_high_gap` (minted FIRST) | 10.0 | 0.0 | **10.0** |
| `cand_high_arity` (minted SECOND) | 1.0 | 5.0 | **16.0** |

`cand_high_arity` wins — despite the LOWER raw gap, and despite being
minted SECOND (ruling out "whichever is considered first"). Zeroing
`ps_move_w_arity` (a GOAL ATTR — graph data, no code or rule edit) flips
the winner back to `cand_high_gap` — the concrete demonstration of
"Argmax over a weight expression the seed carries, so the weighting is
graph data and tunable without code."

### 3. Refutation is a veto, never outvoted

A candidate with `gap=100000, arity_gap=100000` but `refuted=1.0` loses
to a candidate with `gap=1.0, refuted=0.0` — refutation is a pool
membership filter, never a weight term, verified directly.

Gates: `test_selection_picks_by_weight_not_by_gap_alone_or_mint_order`,
`test_selection_weight_is_tunable_graph_data_not_code`, `test_
refutation_is_a_veto_never_outvoted_by_a_higher_weight`.

## Soundness — two constructed cases, both refuted, never augmented

- **Arity 2, subtraction** (`f(a,b)=a−b`): the one candidate (`sym_
  2cycle_0_1`, arity 2's only relaxation) is refuted directly from the
  revealed rows (`(2,5)→−3` collides with `(5,2)→3`'s swap). Never
  selected, never applied; the goal falls through to plain enumerate
  and finds the correct, un-augmented `Minus(a,b)`.
- **Arity 3, weighted sum** (`f(a,b,c)=4a+2b+c`, rows constructed as
  permutations of `{1,2,3}`): all THREE 2-cycles are individually
  refuted (every pairwise swap collides with a differently-labelled
  row); no closure is even attempted (`_sound_closure_relaxation`
  returns `None` before scoring). The goal correctly ends `gapped` —
  no wrong accept.

## The soundness bug FOUND AND FIXED — the fourth coincidental fit, caught

This is the most important finding in this build, and it is reported in
full rather than smoothed over.

**What happened.** An early version of `orbit_candidates` scored EACH
relaxation (full S_n and every individual 2-cycle) as an INDEPENDENT,
separately-selectable candidate — exactly mirroring `PROGRAM_SYNTHESIS_
ARC5_WIDEST_GAP.md`'s own catalogue. Run against MBPP task 397 (median
of three numbers — genuinely symmetric under the FULL group), with only
2 sparse PRIMARY-protocol revealed rows:

- `sym_full_S3`'s own augmented-orbit search did not converge within a
  generous (40,000-candidate) probe budget — an honest resource/
  expressiveness limit, correctly flagged `refuted` under soundness
  rule 2 (unsatisfiability withdrawal).
- But `sym_2cycle_1_2` (swap the 2nd/3rd argument) survived refutation
  from the SAME sparse data (median genuinely IS symmetric in that
  pair too — the conjecture is TRUE, just weaker than full symmetry)
  and scored `gap=16,516` — the highest of any candidate.
- The old selection logic picked it, and enumerate (on the 2-cycle's
  own orbit) found `Max(a, Min(b, c))` — genuinely symmetric in
  `(b,c)`, genuinely consistent with the revealed rows, and genuinely
  consistent with the task's own held-out row (`15,45,75 → 45`, where
  `a` is never the true maximum) **by coincidence**.
- **It is wrong in general**: `Max(100, Min(1, 2))  = 100`, but
  `median(100,1,2) = 2`. Verified directly (this exact witness is
  gated in `test_median_of_three_coincidental_fit_is_caught_by_the_
  closure_fix`).

This is precisely the failure mode the brief warned against by name:
*"arc 4 caught two coincidental fits and arc 5 caught a third; do not
add a fourth."* This would have been the fourth, discovered by running
the real corpus rather than only the hand-picked headline cases.

**The root cause, precisely.** A subgroup's own orbit is a SUBSET of a
containing group's orbit — satisfying a subgroup's (weaker) constraint
set is strictly LESS evidence of correctness than satisfying the full
group's. Treating each relaxation as an independently-scoreable,
independently-selectable candidate lets a merely-locally-true symmetry
outcompete an untested-but-stronger one purely because the stronger
one's own search happened to exceed a resource budget — conflating
"not verified satisfiable" with "false," and rewarding the weaker,
under-constrained conjecture for being cheaper to satisfy.

**The fix** (`_sound_closure_relaxation`, `domains/prog_moves.py`):
every individual 2-cycle surviving revealed-row refutation is recorded
for AUDIT only (`gap` pinned to `0.0` — it can never independently win
the earns-its-keep gate). The ONLY relaxation ever eligible for
selection is the GROUP CLOSURE of every rule-1-sound 2-cycle taken
TOGETHER (composed to full closure, then RE-CHECKED for refutation as a
whole — a composition of two individually-sound generators can produce
a THIRD permutation the data does refute even when neither generator
alone does). There is no fallback to a weaker subgroup if the closure
itself is unsatisfiable — for task 397 this correctly means orbit
augmentation contributes NO selectable candidate, and the goal returns
to its ORIGINAL, honest `gapped:enumerate_failed` outcome (verified: the
before/after MBPP sweep, §7, shows task 397 UNCHANGED by this build).

For br_10, all three 2-cycles are individually sound, so their closure
IS full S3 — identical to what the un-fixed version already found for
that task. **The fix costs nothing on the headline and closes a real,
demonstrated, live wrong-accept elsewhere.**

## Two more live bugs found by running the real corpus (both fixed)

Neither of these was visible from the hand-built headline cases; both
were found only by running the real 257-task MBPP battery (§7) — the
exact discipline the brief's "honest reporting" section asks for.

1. **A crash on non-integer output** (MBPP 160 — a tuple/`None`-valued
   spec; 257 — a tuple-valued spec). Both are MOVE-A-eligible (int
   inputs, arity 2–3) but NOT MOVE-B-eligible (non-int output) —
   `moves_eligible` is an OR of the two moves' own type gates, so a
   goal can reach `run_structural_moves` on MOVE A's weaker
   requirement alone while MOVE B's `factor_candidates` unconditionally
   assumed an already-int `expected` and crashed
   (`TypeError: unsupported operand type(s) for %: 'tuple' and 'int'`).
   Fixed with a defensive per-row int check in `factor_candidates`.
   Gated: `test_mbpp_160_...`, `test_mbpp_257_...`.
2. **A P6.5-class attempt-collision stall** (MBPP 162). A codebook
   candidate (`sum_of_two`) is proposed, evaluated, and rejected FIRST
   — consuming `ps_attempts=1` and stamping `ps_eval_done==1` — before
   the moves rung ever gets a turn. `apply_selected_move`'s
   intermediate-factor branch follows the exact-first convention of
   writing `ps_ir_built = ps_attempts` WITHOUT incrementing (`"a fit
   costs no propose-lane attempt"`), but here that attempt number
   COLLIDES with the one the failed codebook candidate already
   consumed, so `eval_and_record`'s own `ps_eval_done == ps_attempts`
   freshness guard silently treats the move's fresh IR as already
   evaluated — the goal parks forever on the non-terminal `evaluated`
   status (reproduced live before the fix). **Fixed with the exact
   `ps_enumerate_fresh_attempt` precedent applied to this rung**
   (`ps_move_fresh_attempt`, seed v1.10.0's fourth new rule): on
   `move_apply_pending`, if any row's `eval_attempt` already equals
   `ps_attempts`, bump `ps_attempts += 1` first — self-extinguishing,
   naturally single-shot. Gated: `test_mbpp_162_...`.

**This is itself a finding worth stating plainly**: the exact-first
rung's OWN `ps_ir_built = attempts, no increment` design carries the
SAME latent vulnerability whenever a prior codebook attempt is consumed
before it fires — it was simply never exercised, because none of exact-
first's own 9 measured (float-typed) tasks happen to match a codebook
trigger first. This build's broader (int-typed) eligibility surface hit
it. Flagged for the maintainer; `domains/prog_exact.py` is outside this
build's ownership and was not touched.

## Occam order / no-regression

- **Codebook wins even when moves-eligible** (the exact-first
  precedent, generalised): a moves-eligible request whose prompt
  matches an existing codebook trigger is solved by the codebook
  outright; `ps_rung_moves` is never touched. Gated.
- **The exact rung's own six geometry tasks are untouched**: spot-
  checked live (task 82, sphere volume) — `ps_rung_exact==1`,
  `ps_rung_moves` never reached (exact solved first). Gated.
- **A trivially-easy fixture is not preempted** (`double_it(a)=2a`): a
  candidate factor decomposition EXISTS (`a` divides evenly), and the
  raw candidate-count arithmetic alone is not a strong enough gate — the
  direct search converges in 22 candidates and the inner fit in 4,
  which still scores `gap=18>0` under the plain "gap>0" rule, wrongly
  preempting a rung that needed no help (measured directly, then
  fixed). The real, doc-faithful discriminator is `direct_found`: MOVE
  B candidates are refuted outright whenever the DIRECT search already
  converges within the SAME bounded probe — the doc's own framing
  ("intermediate problems UNLOCK TRACTABILITY") made literal, since a
  move whose whole justification is unblocking a search that doesn't
  converge has none when that search already converges. Gated.

### An engine-ordering finding, stated because it surprised the build

Two independently-guarded rules whose entry conditions are ALL
satisfied simultaneously do NOT reliably fire in a fixed, predictable
order (neither "declaration order" nor "declaration order reversed"
held consistently across two different rule pairs measured directly:
`ps_exact_mark` vs `ps_enumerate_mark` favoured the LATER-declared rule
in one measurement; `ps_move_mark` vs `ps_enumerate_mark` favoured the
EARLIER-declared rule in another, before either was given an explicit
mutual-exclusion guard). **Consequently this build never relies on
engine tie-break order for RUNG ADJACENCY** — every rung boundary
(exact↔moves, moves↔enumerate) is pinned by an EXPLICIT `Or(other_rung_
ran, never_other_rung_eligible)` guard in both directions, verified live
by constructing the exact collision scenario and observing deterministic
behaviour across repeated fresh boots. This is recorded here because it
is a genuine engine-behaviour finding this build needed and future
rungs at this same Occam boundary will need again.

## The MBPP 257-task battery, before/after, honestly re-derived

Per the standing rule (this repo's own retracted "optional-dep" note:
quote a live number, not a stale artifact), `results/mbpp_endgame.json`
was NOT reused. Both arms were run with the SAME infrastructure
(`scripts/mbpp_endgame_battery.py`'s own `boot_full` + `run_pass`,
PRIMARY protocol, the full 257-task MBPP test split), the "before" arm
against the pristine `git show HEAD` content of `domains/prog_
synthesis.py` + `seeds/program_synthesis.json` (this build's own
starting point, commit `ec41d3001c` — the exact-first landing), the
"after" arm against this build's own working tree:

| | pass / 257 | task ids that changed |
|---|---|---|
| before (HEAD, `ec41d3001c`) | 32 | — |
| after (this build)          | 35 | **+3**: 58, 404 (pass), 59 (pass), 162 (accepted_holdout_fail, NOT pass) |

(32, not the exact-first doc's own quoted 28→34 — that comparison was
made at a DIFFERENT point in the repo's history; both numbers are
honest for their own moment, per this repo's own standing rule that a
baseline is re-derived, never carried forward as a label.)

**Four task outcomes changed in total; three became genuine passes; the
fourth (162) is an honest `accepted_holdout_fail`, NOT a wrong pass** —
its 2-revealed-row inner fit (`sum_series`, `PROGRAM_SYNTHESIS_ARC5_
MOVES.md` §5's second bug) is a coincidental 2-point fit that the
project's own held-out scoring correctly catches, exactly the
"accepted_holdout_fail" bucket this corpus already has a name for. **No
task moved into a wrong PASS anywhere in the 257-task split** — checked
exhaustively (the diff above is the complete before/after task-id map,
not a sample).

## Honest scope and residuals

- **Applicability remains narrow, as `PROGRAM_SYNTHESIS_ARC5_WIDEST_
  GAP.md` predicted**: 3 real MBPP conversions (58, 404 via MOVE A; 59
  via MOVE B) out of 257 — grammar/type coverage (arity bounds,
  integer-only for MOVE B, numeric-only for MOVE A), not the selection
  mechanism, is the binding constraint, exactly as that document's own
  "9/48 applicable" finding anticipated.
- **MOVE B's arity is capped at 3** (matching the `ExactFamily`/probe
  precedent's own scoping discipline) and factors on ONE argument at a
  time — a genuinely multi-argument decomposition (e.g. `f(a,b) =
  a·g(a,b)` where the inner problem still depends on `b`) is not
  attempted; named as a residual, not built speculatively (this arc's
  own recurring "no speculative extras" rule).
- **The scoring-probe budget (40,000 candidates) is a real, load-
  bearing number**, calibrated against the SPECIFIC measured needs of
  this arc (25,240 for br_10's full orbit, 28,490 for task 59's inner
  factor) — a task needing more than 40,000 candidates to demonstrate
  its own advantage would be scored as "not found" (soundness-rule-2
  withdrawal) even if a bigger budget would have found it. This is a
  documented, deliberate cost/completeness trade-off, not an oversight.
- **MOVE B's inner-solve reuses the SAME engine call the enumerate
  rung's OWN adapter makes**, rather than spawning a nested descent-
  style sub-Goal — a documented simplification consistent with
  the exact-first rung's own precedent of calling the engine directly.
  "Solve it with the same ladder" is satisfied at the level of "the
  same underlying search primitive," not "a full recursive Goal
  lifecycle" — named here so the choice is visible, not silently made.
- **`ps_exact_mark`'s own `ps_ir_built = attempts, no increment`
  convention carries the SAME attempt-collision vulnerability this
  build found and fixed for its own rung** (§5) — `domains/prog_
  exact.py` is outside this build's file-ownership boundary and was
  not touched; flagged for the maintainer.

## Test numbers

- `tests/test_prog_moves_migrated.py`: **32/32 passed** (includes the
  embedded named-regression-sweep subprocess).
- `tests/test_program_synthesis_migrated.py`: rule-count pin 66 → 70,
  dated.
- Named arc-4/arc-5 regression sweep (20 files, `--confcutdir=.`):
  **492 passed, 22 allowlisted failures** (final, converged run) — every
  one of the 22 is
  root-caused above and lives OUTSIDE this phase's file-ownership
  boundary. By category (full enumeration in `tests/test_prog_moves_
  migrated.py::_KNOWN_OUT_OF_SCOPE_FAILURES`, cross-checked live, not
  hand-waved):
  - **5 literal `seed["version"]` string pins** (`test_exact_first_
    migrated.py`, `test_verdict_discrimination_migrated.py`, `test_
    budget_isolation_migrated.py`, `test_retrieval_migrated.py`, `test_
    reject_informs_repair_migrated.py`) — ANY future rule addition to
    this seed breaks these regardless of content, the SAME class of
    drift exact-first itself named against its OWN predecessor, plus
    `test_exact_first_migrated.py`'s own nested regression-sweep gate
    (self-referential: it fails until this exact allowlist exists,
    which it now does).
  - **9 failures attributable to MOVE A converting br_10** (two in
    `test_descent_widening_migrated.py` against a DIFFERENTLY-named
    "top of three" fixture that hits the SAME symmetric-max mechanism;
    six in `test_reject_informs_repair_migrated.py`, whose entire S6
    finding WAS br_10's non-convergence; one each in `test_prog_
    synthesis_battery_migrated.py` and `test_arc4_endgame_migrated.py`) —
    every one is the SAME headline effect this build exists to produce,
    observed from a different frozen vantage point, exactly the
    "S4/S6 widening moves ids out of a frozen snapshot" shape exact-
    first's own doc already reported against several of these SAME
    files for its six geometry ids.
  - **4 failures in `test_search_reach_migrated.py`** — its own frozen
    id-bucket snapshot predates MOVE B; task 59 moving from `gapped` to
    `pass` (and 162 to `accepted_holdout_fail`) is exactly this build's
    OWN reported headline, observed from that file's fixed vantage
    point (the `_ARC5_EXACT_FIRST_PASS_IDS` precedent this file already
    uses for the SAME reason).
  - **2 pre-existing failures, NOT introduced by this build** (`test_
    mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`,
    `test_descent_widening_migrated.py::test_sum_to_n_class_scalar_
    loop_descends_and_holds_out_correct` — both a `'sum_of_two' !=
    'range_sum_spine'` construction drift on task 267) — verified
    directly to ALSO fail against the pristine, unmodified `git show
    HEAD` (commit `ec41d3001c`) this build started from, with NEITHER
    this build's seed nor its Python files present.

## Files

- `domains/prog_moves.py` (new)
- `seeds/program_synthesis.json` (v1.9.0 → v1.10.0, 66 → 70 rules)
- `domains/prog_synthesis.py` (`import prog_moves as pmv`, `ps_moves_
  eligible` in `ingest_spec`, two new `_DISPATCH` entries)
- `tests/test_program_synthesis_migrated.py` (rule-count pin 66 → 70,
  dated)
- `tests/test_prog_moves_migrated.py` (new, 32 tests)
