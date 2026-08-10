# PROGRAM SYNTHESIS ARC 2 Q5 — THE POWERED MBPP ENDGAME

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (HQ1-HQ4,
the three-way PRIMARY/OFFICIAL/STRESS split protocol, §0), `PROGRAM_SYNTHESIS_
ARC2_Q0_BASELINE.md` (the frozen zero-shot/STRESS continuity row, cited
below, never re-run), `PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md` (HQ1, 55.0%),
`PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md` (HQ2, 100% PRIMARY-runnable),
`PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md` (the train diet this phase measures the
benchmark-level payoff of), `PROGRAM_SYNTHESIS_ARC2_Q4_NOTES.md` (descent/
repair widening — the mechanism this phase's non-regression gate protects).

This phase MEASURES the stack exactly as committed — no synthesis/engine/
seed/spec code was touched. **Deliverables:** `scripts/mbpp_endgame_battery.py`
(the driver), `results/mbpp_endgame.json` (the artifact — every number below
is re-derived from its per-task rows, never asserted bare), `tests/
test_mbpp_endgame_migrated.py` (30 passed, 1.82s).

---

## 1. THE EXTERNAL NUMBER — FULL, both denominators

**FULL** = the committed stack (descent + repair + exclude, `seeds/
program_synthesis.json` v1.4.0) + `install_mined_chunks` (P7-C's 15
arc-1-corpus idiom chunks) + `ensure_mbpp_train_diet` (Q3's 15 `mck_` chunks
+ 30 `mbpp_train` bigrams), PRIMARY protocol, on the full 257-task MBPP test
split, twin-run byte-identical (`determinism.identical == True`, both hashes
equal).

| denominator | k | n | p | Wilson 95% CI |
|---|---|---|---|---|
| **PRIMARY-runnable** (257/257, per HQ2) | 18 | 257 | **7.00%** | [4.48%, 10.80%] |
| all 257 test-split tasks (identical — runnable == 257) | 18 | 257 | 7.00% | [4.48%, 10.80%] |
| **all 427 sanitized-corpus tasks** (the standing coverage-denominator rule) | 18 | **427** | **4.22%** | [2.68%, 6.56%] |

**Reading:** the 427-denominator number is a *coverage* statement, not a
capability claim about the 170 non-test tasks — only the 257 test-split
tasks were ever run through the loop (per-task rows: `results/mbpp_endgame
.json`'s `arms.full.runnable_rows`, 257 entries, 0 excluded).

**Trajectory to here (every number an instrument, none a vibe):**

| moment | instrument | number |
|---|---|---|
| Q0-A zero-shot / STRESS (1 revealed row) | 240 runnable / 257 test | **0.42%** [0.07%, 2.32%] |
| Q1.5 representability+predictability ceiling (HQ1, a *mechanism* fact, not an accept rate) | 427 corpus | 55.0% [–] |
| **Q5 FULL, end-to-end accept rate (PRIMARY)** | 257 runnable / 257 test | **7.00%** [4.48%, 10.80%] |
| **Q5 FULL, end-to-end accept rate, 427-corpus coverage denominator** | 427 corpus | **4.22%** [2.68%, 6.56%] |
| Q5 OFFICIAL (all-rows-revealed, self-consistency analog) | 257 runnable / 257 test | 16.34% [12.32%, 21.35%] — protocol-distinct, see §5 |

A 0.42% → 7.00% headline move is real (Q1's representability widening + Q2's
richer PRIMARY protocol removed the single-example-overfitting floor that
drowned Q0-A), but the honest gap between HQ1's 55.0% representability
ceiling and the 7.00% end-to-end accept rate is the dominant fact of this
phase (§6) — representable is necessary, nowhere near sufficient; the
PROPOSE/search half remains the bottleneck, exactly the arc-1 standing
finding ("constructions propose, execution decides — the DECIDE half never
miscarried, the PROPOSE half has not yet paid a capability premium"),
confirmed again here at full MBPP-end-to-end grain.

## 2. Per-arm tables

| arm | protocol | k | n(runnable) | p | Wilson 95% CI | p/427 | CI/427 | det. identical |
|---|---|---|---|---|---|---|---|---|
| **FULL** | primary | 18 | 257 | 7.00% | [4.48%, 10.80%] | 4.22% | [2.68%, 6.56%] | True |
| **CONTENT-STRIPPED** | primary | 19 | 257 | 7.39% | [4.78%, 11.26%] | 4.45% | [2.87%, 6.84%] | True |
| **OFFICIAL** | official | 42 | 257 | 16.34% | [12.32%, 21.35%] | 9.84% | [7.36%, 13.03%] | True |

Every arm ran the full 257-task test split (no prefix cut was needed — the
full 3-arm x 2-twin-run sweep completed in 48.7s, far inside the ~30 min
box; `condition.time_box.official_prefix_cut: null` in the artifact records
this honestly rather than silently).

## 3. HQ3 VERDICT — a third null, with a sharp mechanistic explanation

**Delta (FULL − CONTENT-STRIPPED), Newcombe CI, same paired 257-task-id
set** (`hq3.same_paired_task_id_set: true`):

```
delta = -0.39pp,  95% CI = [-5.01pp, +4.22pp]  →  within_noise_no_measured_gain
```

**HQ3 NOT CONFIRMED.** CI spans zero; the point estimate is numerically
*negative* (content very slightly worse). This is the **third** null on
this exact hypothesis shape (after arc-1's H6 and H7c) — per the prereg's
own registered forking rule (§5), **this activates the retrieval-shaped-
proposal fork for arc 3**: decode against whole held train PROGRAMS (not
chunk shapes) is the next hypothesis, not a surprise requiring a new plan
document.

### 3a. The identity-list evidence (never a bare delta)

**FULL's pass set is a strict subset of CONTENT-STRIPPED's pass set:**

```
FULL pass ids     (18): 16,17,84,89,92,127,135,138,227,234,266,309,397,404,406,433,458,477
STRIPPED pass ids (19): 16,17,84,89,92,127,135,138,227,234,266,309,397,404,406,433,458,464,477
FULL − STRIPPED = {}            (zero exclusive passes bought by content)
STRIPPED − FULL = {464}         (one pass content LOST)
```

The learned content (mined chunks + the Q3 train diet + boarded bigrams)
bought **zero** net-exclusive passes and **cost exactly one** on this 257-task
split.

### 3b. The mechanism, verified per-row (the attribution table)

25 tasks change outcome class between FULL and CONTENT-STRIPPED
(`hq3.paired_changes`). The dominant pattern, verified on **all 24** of
FULL's `gapped:exhausted` rows (a class that is **completely absent** from
CONTENT-STRIPPED — 0/257):

| class | FULL | CONTENT-STRIPPED |
|---|---|---|
| `gapped:exhausted` | **24** | **0** |
| `gapped:enumerate_failed` | 142 | 159 |
| `accepted_holdout_fail` | 69 | 76 |
| `pass` | 18 | 19 |

**The mechanism, task 464 (the one lost pass) as the clean exemplar:**

```
task 464 "check if all values are same in a dictionary"
  FULL:      codebook=1 lattice=1 descend=None enumerate=None
             construction=ck_prog_if_stmt_n1_q0  attempts=3
             status=gapped  gap_reason=exhausted
  STRIPPED:  codebook=None lattice=None descend=None enumerate=1
             construction=None  attempts=1
             status=accepted  →  pass
```

A chunk (`ck_prog_if_stmt_n1_q0`, an arc-1-corpus chunk present only in
FULL) gets CUED by the codebook/lattice rungs, consumes the fixed
per-attempt budget on a wrong candidate, and the loop is **exhausted before
the enumerate rung ever runs** — the SAME enumerate rung that, with no
chunk to distract it, solves the task cleanly under CONTENT-STRIPPED at
attempt 1. All 24 `gapped:exhausted` rows in FULL carry a non-null
`construction` (chunk- or starter-codebook-cued); **zero** carry no
construction — i.e. every single budget-exhaustion case in this run is a
**decoy tax**, not a coincidence:

| decoy source | `gapped:exhausted` count (FULL) | `accepted_holdout_fail` count (FULL) |
|---|---|---|
| `mbpp_train_diet` chunk (`mck_*`) | 9 | 13 |
| arc-1 corpus chunk (`ck_*`/`ckt_*`) | 8 | 3 |
| starter codebook shape | 7 | 12 |
| bare enumerate (no cue at all) | 0 | 37 |
| other (`range_sum_spine`) | 0 | 4 |

Content-cued decoys account for **24/24** of the exhaustion class and
**28/69 (40.6%)** of the holdout-fail class in FULL — a real, measurable
cost, not noise.

**Content's positive footprint, for balance (`hq3.content_footprint_over_
full_accepts`):** 19 of FULL's accepted/passed rows show a chunk-named
construction and 20 show a successful lattice decode; **15 of those are
specifically `mck_*` (Q3 train-diet) chunks** — the diet mechanism DOES
engage, exactly as Q3's own leave-N-out probe found (55.0% mechanism
engagement, train-internal). What Q5 adds is the missing other half of the
ledger: **engagement is not free** — every chunk that gets cued and turns
out wrong (the far more common case, since most chunks are hole-fill-only
or apply to the wrong task) burns attempt budget that the enumerator, which
in this domain is doing essentially all of the real work, needed. The
proposal layer is currently a net-neutral-to-negative filter on the
decide layer's own attempt budget, at this corpus↔codebook pairing.

**Registered fork, stated plainly per the prereg:** HQ3 nulling a third
time under IN-DOMAIN, NL-paired content (Q3's whole reason to exist) rules
out "the content wasn't matched to the domain" as the explanation. The
mined chunks are 2-4 statement MBPP-idiom shapes; MBPP's actual solution
space is dominated by single-call native-oracle expressions
(`sorted(...)`/`sum(...)`/comprehensions) the chunk grain does not target.
**Arc 3's hypothesis is retrieval-shaped proposal**: decode against whole
held TRAIN PROGRAMS (nearest-neighbour over embedded/structural
similarity), not shape-grain chunks — a different PROPOSE-half
architecture, not a bigger diet.

## 4. Migration matrix vs Q0 — what each phase bought

Per-Q0-outcome-class crosswalk (`migration_matrix_vs_q0`, mechanical
per-task-id join across the Q0-A artifact and this phase's FULL/
CONTENT-STRIPPED arms — never re-run, only joined):

| Q0 class (STRESS, 1-revealed-row) | n | now (FULL) | now (CONTENT-STRIPPED) | content-attributable moves |
|---|---|---|---|---|
| `accepted_holdout_fail` (single-example overfit) | 146 | pass 16 / accepted_holdout_fail 65 / gapped:enumerate_failed 49 / gapped:exhausted 15 / runner_exc 1 | pass 17 / accepted_holdout_fail 70 / gapped:enumerate_failed 58 / runner_exc 1 | 15 |
| `gapped:enumerate_failed` (value-domain wall) | 90 | gapped:enumerate_failed 78 / accepted_holdout_fail 4 / gapped:exhausted 6 / pass 1 / runner_exc 1 | gapped:enumerate_failed 85 / accepted_holdout_fail 4 / pass 1 | 7 |
| `assert_unparseable` (math_isclose/set forms) | 17 | gapped:enumerate_failed 15 / gapped:exhausted 1 / runner_exc 1 | gapped:enumerate_failed 15 / accepted_holdout_fail 1 / runner_exc 1 | 1 |
| `gapped:exhausted` | 2 | gapped:exhausted 2 | accepted_holdout_fail 1 / gapped:enumerate_failed 1 | 2 |
| `not_recognized` | 1 | not_recognized 1 | not_recognized 1 | 0 |
| `pass` (coincidental) | 1 | pass 1 | pass 1 | 0 |

**The headline story, attributed honestly to the right phase:**

- **The 56.8% `accepted_holdout_fail` mass (Q0's single largest blocker) is
  the PROTOCOL's own effect, not content's.** Both FULL and CONTENT-STRIPPED
  move this class almost identically (65 vs 70 remain `accepted_holdout_fail`,
  16 vs 17 now PASS, ~49-58 move to an honest `gapped:enumerate_failed`) —
  this is **Q2's PRIMARY-protocol richer reveal** (last-row-held-out instead
  of 1-of-3-revealed) doing the work, distinguishable exactly because
  CONTENT-STRIPPED shares the protocol and shows the SAME shift. Every one
  of Q0-A's 17 `assert_unparseable` tasks is likewise now PRIMARY-runnable
  (Q2's HQ2 finding, confirmed again here in the migration matrix — no task
  is still `assert_unparseable`).
- **17 tasks total show a content-attributable divergence between FULL and
  CONTENT-STRIPPED** at the migration-matrix grain (the `content-attributable
  moves` column) — small next to the ~230 tasks the PROTOCOL alone moved,
  consistent with §3's CI-spans-zero verdict: content is a real but tiny,
  and slightly net-negative, lever at this corpus↔codebook pairing.
- **`assert_unparseable`'s Q1/Q2-boundary closure (math_isclose/set forms,
  17 tasks) is real** — none of those 17 tasks are excluded anymore; most
  land in `gapped:enumerate_failed` (an honest capability gap, not a parse
  failure) — Q1/Q2's value-domain + spec-extraction widening converted a
  parse-blocker into a search-blocker, the correct direction of travel.

## 5. Protocol comparison — PRIMARY (FULL) vs OFFICIAL

OFFICIAL reveals **every** parseable assert and scores on the **same** rows
(the published-MBPP pass@1 analog — a self-consistency check, not a
held-out generalization test). It is protocol-flagged on every row
(`protocol: "official"`) and never enters a PRIMARY aggregate or the HQ3
delta (`test_official_arm_never_enters_a_primary_aggregate`).

```
OFFICIAL − FULL = +9.34pp,  95% CI = [+3.81pp, +14.95pp]  →  CI-SEPARATED
```

This delta IS CI-separated — unsurprising and not a capability claim: with
2-3 rows revealed instead of 1-2 held back, the search has both more
constraint (fewer false accepts survive) and a strictly higher intrinsic
ceiling (asserts that PRIMARY holds back entirely can now directly guide a
codebook/lattice/enumerate proposal). OFFICIAL's own taxonomy shows two
`gapped:no_shape` tasks (228, 405) that never appear under PRIMARY — a
protocol-specific interaction (revealing the tie-breaking third row changes
which plan the descent rung selects) named here, not investigated further
(out of this phase's scope — a measurement fact, not a bug report).

## 6. Remaining failure taxonomy (FULL, ranked) — with the joint-curve context

| rank | class | n/257 | share |
|---|---|---|---|
| 1 | `gapped:enumerate_failed` | 142 | 55.3% |
| 2 | `accepted_holdout_fail` | 69 | 26.8% |
| 3 | `gapped:exhausted` | 24 | 9.3% |
| 4 | `pass` | 18 | 7.0% |
| 5 | `runner_exception:TypeError` | 3 | 1.2% |
| 6 | `not_recognized` | 1 | 0.4% |

**Context — the representability/predictability ceiling this taxonomy sits
under:** of the 427-task corpus, 355 tasks are Q1-in-scope type-coverable
(the joint curve's honest reachable ceiling, `PROGRAM_SYNTHESIS_ARC2_PREREG
.md` §2) and 235/427 (55.0%) are ACTUALLY representable+predictable,
post-Q1.5, measured live (`PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md`). Against
that ceiling, FULL's 18/257 (7.0%) end-to-end pass rate is a small fraction
of what is structurally reachable — the gap between 55.0% (can this
function's SHAPE be represented at all) and 7.0% (does the search loop
actually FIND and VERIFY a correct program for it) is the PROPOSE/search
half, not the representability floor. `gapped:enumerate_failed` (55.3% of
all outcomes) is the direct evidence: these are tasks where representability
was never the obstacle (many are in the 355-task Q1-scoped set) but no
rung — codebook, lattice, descent, or the enumerator itself — found a
program that fits ALL the PRIMARY-revealed rows.

**Named remaining levers (ranked by measured mass, this phase + carried
forward from Q1/Q1.5/Q4, deduped):**

1. **`RecvMethod:append` / mutating-method write-back** (22 corpus blocker
   occurrences at Q1.5, MBPP's single largest structural blocker) — no
   lvalue write-back path for `xs.append(v)`-shaped mutation; the Q1 Notes
   §3 named follow-on (`ProgMethodCallSet`-class IR variant), not landed.
2. **`CompTargetComplex` / comprehension_advanced** (18 blocker occurrences)
   — non-trivial comprehension targets/multi-clause, named Q1 stretch,
   not landed.
3. **`Lambda` / map+lambda** (15 blocker occurrences) — a first-class
   callable/closure value has no representation in the current DSL value
   model; `map`/`next` over it are honest engine refusals, not bugs.
4. **`KwargsCall`** (13 blocker occurrences) — kwargs plumbing, named
   exclusion since P1.
5. **`regex`** (28 tasks `ok=True but not predictable`, i.e. representable
   but not executable) — explicitly out of the plan's scope (risk #5, "no
   regex" — a genuinely new object model, not an op family).
6. **Same-corpus helper-function externs** — a declared-oracle/multi-
   function synthesis concern (task calls a sibling MBPP function), Q3+
   territory, not an emitter gap.
7. **The proposal-layer decoy tax** (this phase's own new finding, §3b) —
   chunk/codebook cues that turn out wrong consume the fixed attempt budget
   that the enumerator (currently carrying nearly all real capability)
   needs; a round-budget or exclude-on-decoy-detection mechanism is the
   named lever, distinct from "add more content."
8. **Retrieval-shaped proposal (the registered arc-3 fork, §3b)** — decode
   against whole held train PROGRAMS rather than chunk shapes, now that
   shape-grain content has nulled three times (H6, H7c, this phase's HQ3).
9. **The 3 `runner_exception:TypeError` residuals** (tasks 115, 124, 237) —
   named, not fixed (out of this MEASURE-only phase's scope): a raw `set`
   nested inside an example row's `inputs` breaks `json.dumps` in
   `_add_example_row` (the exact residual `domains/mbpp_spec.py`'s own
   docstring names); task 124's literal complex-number arg is similarly
   non-JSON-safe (and is one of the prereg's 2 permanently non-type-
   coverable tasks); task 237's dict-typed `expected` with tuple keys hits
   a PyO3 boundary error that is, additionally, ARM-DEPENDENT (it fires
   under FULL/OFFICIAL but not CONTENT-STRIPPED for the identical row —
   evidently only reachable via a codebook/chunk comparison path that
   CONTENT-STRIPPED's starter-only codebook never exercises for this task;
   named honestly, not chased further).

## 7. Contamination

`tests/test_mbpp_endgame_migrated.py`'s own scan of `results/mbpp_endgame
.json` is clean (it is an eval log — like Q0-A's own artifact, deliberately
excluded from the shared gate's `SCAN_TARGETS`, but scanned anyway by this
phase's own equivalent check for any leaked verbatim reference-code line —
zero hits). The runner's own source is AST-scanned to prove it never
indexes `task["code"]` anywhere in live code (docstring mentions of the
string are correctly not flagged). The shared gate,
`tests/test_mbpp_contamination_migrated.py`, was run as part of this
phase's own suite and **passes: 7 passed**.

## 8. Honest scope statement

- Every number above derives from `results/mbpp_endgame.json`'s per-task
  rows (`arms.*.runnable_rows`/`excluded_rows`) — this document performs no
  computation the artifact's own fields do not already carry, re-verified
  by `tests/test_mbpp_endgame_migrated.py`'s schema/re-derivation gates.
- All three arms ran the FULL 257-task test split; no time-box prefix cut
  fired (`condition.time_box.official_prefix_cut: null`), so there is no
  eval-subset caveat beyond the standing test/train/validation/few_shot
  split itself.
- HQ3's null is reported with its full mechanistic attribution (§3b), not
  as a bare CI-spans-zero shrug — the decoy-tax finding is a genuine new
  fact this phase adds beyond arc-1's H6/H7c.
- 3 tasks (115, 124, 237) hit `runner_exception` outcomes; these are named,
  reproducible, and NOT hand-patched (out of this phase's MEASURE-only file
  ownership) — reported as a distinct outcome class, never silently
  absorbed into `gapped`.
- The 427-denominator number is a coverage statement; it does not claim
  anything about the 170 non-test tasks, which were never run through the
  loop this phase.
