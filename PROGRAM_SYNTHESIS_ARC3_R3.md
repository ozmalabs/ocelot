# PROGRAM SYNTHESIS ARC 3 R3 — THE POWERED MBPP ENDGAME (HR1/HR2/HR3)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC3_PREREG.md` (HR1/HR2/HR3,
the bars this document judges against), `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md`
(the 12-task honest oracle ceiling), `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md`
(R1/R2 landing + the R2.5 scoped codebook-side screen), `PROGRAM_SYNTHESIS_
ARC2_Q5.md` / `results/mbpp_endgame.json` (arc-2's FULL arm — the paired
continuity comparator, frozen, cited, never re-run). This phase MEASURES
the stack exactly as committed (seed v1.5.1) — no synthesis/engine/seed/spec
code was touched. **Deliverables:** `scripts/mbpp_arc3_battery.py` (the
driver), `results/mbpp_arc3_endgame.json` (the artifact — every number below
re-derives from it), `tests/test_mbpp_arc3_endgame_migrated.py` (40 passed,
~3.3s).

---

## 1. THE ARC NUMBER — FULL-R3, both denominators

| denominator | k | n | p | Wilson 95% CI |
|---|---|---|---|---|
| **PRIMARY-runnable** (257/257) | 21 | 257 | **8.17%** | [5.41%, 12.17%] |
| **all 427 sanitized-corpus tasks** (coverage denominator) | 21 | 427 | 4.92% | [3.24%, 7.40%] |

**Trajectory (every number an instrument):**

| moment | instrument | number |
|---|---|---|
| Q0-A zero-shot / STRESS | 240 runnable / 257 test | 0.42% [0.07%, 2.32%] |
| Arc 2 Q5 FULL (PRIMARY) | 257 runnable / 257 test | 7.00% [4.48%, 10.80%] |
| **Arc 3 R3 FULL-R3 (PRIMARY)** | 257 runnable / 257 test | **8.17%** [5.41%, 12.17%] |

**0.42% → 7.00% → 8.17%.** The move from arc 2 to arc 3 is real in the point
estimate (+1.17pp / +3 net passes over the arc-2 FULL arm: 4 gains, 1
regression, §5) but the two arms' own confidence intervals overlap
substantially ([4.48,10.80] vs [5.41,12.17]) — this is a genuinely small
movement, reported at its actual size, not rounded up.

**OFFICIAL-R3** (comparability row, protocol-flagged, never a PRIMARY
aggregate member): 47/257 = 18.29% [14.04%, 23.47%] (arc-2 Q5 OFFICIAL was
42/257 = 16.34% [12.32%, 21.35%] — consistent movement, same direction as
PRIMARY, not analysed further here).

## 2. Per-arm table

| arm | protocol | k | n | p | Wilson 95% CI | det. identical |
|---|---|---|---|---|---|---|
| **FULL-R3** | primary | 21 | 257 | 8.17% | [5.41%, 12.17%] | True |
| **NO-RETRIEVAL** | primary | 19 | 257 | 7.39% | [4.78%, 11.26%] | True |
| **OFFICIAL-R3** | official | 47 | 257 | 18.29% | [14.04%, 23.47%] | True |

Twin-run byte-identical on all three arms. Total elapsed 91.8s (well inside
budget — no time-box prefix cut fired).

**The NO-RETRIEVAL off switch** (documented in the artifact's
`condition.no_retrieval_off_switch` and gated live by `tests/test_mbpp_
arc3_endgame_migrated.py::test_no_retrieval_boot_installs_zero_exemplar_
nodes`): a `Seed{id:"mbpp_exemplars"}` marker is pre-added to the substrate
before `ensure_program_synthesis` runs, so `prog_retrieval.
ensure_exemplar_store`'s own idempotent guard boards **zero** Exemplar
nodes. This is the cleanest available seam — it touches no seed/engine/rule
file, leaves the scoped codebook-side screen (`ps_screen_*`, independent of
retrieval) fully live, and is confirmed a true no-op fall-through (not a
broken boot) by a live add-two-numbers reverify (`test_no_retrieval_boot_
still_solves_a_codebook_shaped_request`).

## 3. HR1 VERDICT — **null** (registered reading), net_passes = 2, CI spans zero

```
delta (FULL-R3 - NO-RETRIEVAL) = +0.78pp
95% CI (Newcombe)              = [-3.97pp, +5.55pp]   ->  CI SPANS ZERO
net_passes (paired count)      = 2   (3 gains - 1 loss)
registered band                = null
```

**Ladder placement, exactly as registered (`PROGRAM_SYNTHESIS_ARC3_PREREG.md`
§4):** strong requires >=6 net passes CI-separated; weak/marginal requires
1-5 net passes CI-separated; null is CI-spans-zero OR point delta <= 0. Here
net_passes (2) falls IN the weak/marginal COUNT range, but the CI is not
separated — the registered rule requires BOTH conditions, so the honest
verdict is **null**, not "weak." This is exactly the outcome the prereg's
own §5 anticipated for a null at this grain: *"a real R1 ranker ... will
realistically capture some FRACTION of this 12-task ceiling, not all of
it"* — 2 net passes against a 12-task ceiling is a small, real, sub-ceiling
capture, not evidence the mechanism is inert.

### 3a. The identity-list evidence (never a bare delta)

**Gains (FULL-R3 pass, NO-RETRIEVAL not pass) — 3:**

| task | no_retrieval outcome | full_r3 outcome | attribution |
|---|---|---|---|
| 20 | gapped:enumerate_failed | pass | retrieval rung **c**, exemplar 803 |
| 142 | gapped:exhausted | pass | retrieval rung **c**, exemplar 747 |
| 281 | gapped:enumerate_failed | pass | retrieval rung **c**, exemplar 741 |

**Loss (NO-RETRIEVAL pass, FULL-R3 not pass) — 1, a genuine regression
named honestly:**

| task | no_retrieval outcome | full_r3 outcome | attribution |
|---|---|---|---|
| 17 | **pass** (bare enumerate, attempt 0) | accepted_holdout_fail | retrieval rung **d**, exemplar 803 |

**The preemption regression, named plainly.** Task 17 previously PASSED
under the arc-2/NO-RETRIEVAL stack: the bare enumerator found a correct,
holdout-generalizing program on its very first attempt. Under FULL-R3, a
top-level goal enters the **retrieval ladder before the codebook/enumerate
stack ever runs** — rung (d) (retrieved-as-skeleton, exemplar 803) finds a
DIFFERENT candidate that fits every revealed row but fails the held-out
row, and because Occam order commits to the FIRST accepting rung it finds,
the goal never reaches the enumerator's own correct answer at all. This is
the SAME trap-mass phenomenon R0 measured (55.6%-60% of rung a-c revealed
passers fail held-out) manifesting one rung deeper, with a NEW consequence
R0's pure ceiling sweep could not see: **a trap-y retrieval accept can
silently displace an already-correct enumerator solution**, because
retrieval-first ordering gives it first claim on the goal. Reported as a
genuine, measured regression, not smoothed into the net-positive framing —
this is precisely why the net (2) is smaller than the raw gain count (3).

**Retrieval engagement footprint** (any rung reached, regardless of whether
the eventual outcome class changed): 63/257 tasks reach a non-"none" rung
in FULL-R3 — most of these are harmless no-ops (the same candidate class
the codebook/enumerate path would also have found, so the outcome CLASS is
unchanged even though the internal `construction` provenance now reads
`retrieved_exemplar`), consistent with `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.
md`'s own finding that retrieval is usually a harmless fall-through.

## 4. HR2 VERDICT — the registered "~0" bar is **NOT met** for the full
covered class; the root cause is a named, already-documented R2.5 boundary

Q5's FULL arm carried 24 `gapped:exhausted` rows. Per the prereg's own
narrowed scope (R2.5's honest residual, `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.
md` §9.4): 17/24 are chunk-cued (`mck_*`/`ck_*`/`ckt_*`, in the R2.5
screen's scope) and 7/24 are starter-codebook-shape-cued (DESCEND_APPLICABLE
by construction, explicitly OUT of the screen's scope by design).

| class | n/24 | now (FULL-R3) |
|---|---|---|
| covered (chunk-cued) | 17 | **10 still `gapped:exhausted`**, 7 moved |
| residual (starter-shape, registered residual) | 7 | **7/7 still `gapped:exhausted`** (unchanged, exactly as registered) |

**The residual class (7/7) behaves exactly as registered** — none of `286,
296, 415, 463, 468, 471, 476` moved; this is the DESIGNED scope boundary of
the R2.5 screen, not a defect.

**The covered class (17) does NOT reach ~0 — 10/17 remain unchanged.**
Per-task mechanism attribution (`hr2.covered_class_mechanism` in the
artifact):

| mechanism | n | task ids |
|---|---|---|
| unchanged (screen never engaged) | **10** | 108, 119, 222, 223, 229, 240, 245, 280, 394, 431 |
| screen engaged (kills>0) | 4 | 160 → gapped:enumerate_failed; 164, 300 → accepted_holdout_fail (traps); **464 → PASS** |
| retrieval-resolved (bypasses codebook path entirely) | 3 | 142 → PASS; 165, 452 → accepted_holdout_fail (traps) |

**Root cause of the 10 unchanged rows, verified per-row (`screen.kills ==
0.0` on every one of them):** the Arc3-R2.5 screen's own `NOT_SLACK` gate
only ever engages when a goal's FROZEN initial trigger-matching codebook
pool (`ps_screen_pool0`) is `>= ps_budget` (3) — a goal with ANY initial
slack (pool0 < 3) is **never screened at all**, by the screen's own
documented, all-or-nothing design (`PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md`
§9.4 residual 2: *"a goal with any initial slack is NEVER screened"*). For
these 10 tasks, fewer than 3 trigger-matching chunk constructions exist, so
the screen's own scoping condition is false and the goal proceeds exactly
as it did in Q5 — 3 wasted attempts, budget exhausted, enumerator never
reached. **This is not a new defect** — it is R2.5's own already-reported
residual, now measured at the full-corpus grain for the first time (R2.5's
own landing rung reported it as a design choice verified only on a
dedicated fixture, per its own §9.4 residual 4: *"a fresh mbpp_endgame_
battery.py re-run ... is a measurement phase, not this mechanism-landing
rung's own scope"*). This phase IS that measurement, and it shows the
residual has real, material weight: 10/17 (59%) of the covered class.

**attempts-per-accept vs Q5 FULL — the registered "non-increasing" bar is
also NOT met, honestly reported:**

| | n_accepts | mean_attempts | total_attempts |
|---|---|---|---|
| Q5 FULL | 87 | 0.931 | 81 |
| FULL-R3 | 97 | 1.000 | 97 |

**Verdict: increased**, not non-increasing. The mechanism reading: retrieval
accepts always cost exactly 1 attempt (`pr_ladder_accept` bumps `ps_attempts`
by exactly one), and retrieval now claims MANY more of the 257 goals as
"accepted" (`n_accepts` rose from 87 to 97) — including goals that would
previously have gone straight to a 0-attempt bare-enumerate pass (task 17,
§3a) or stayed gapped without ever reaching "accepted" at all. A higher
accept COUNT at a floor cost of 1 attempt each pulls the mean up from
0.931 toward (and slightly past) 1.0. This is a real, measured, honestly
labelled miss of the registered bar — not attempts BLOWING UP per accept
(no accept costs more than before), but more goals reaching "accepted" at
the 1-attempt floor, which mechanically raises the population mean above
Q5's own mix (which included some genuinely free, 0-attempt bare-enumerate
passes now displaced by retrieval, per §3a's regression).

## 5. Migration matrix vs the arc-2 FULL arm — paired ids

| | ids |
|---|---|
| arc-2 FULL pass (18) | 16,17,84,89,92,127,135,138,227,234,266,309,397,404,406,433,458,477 |
| Arc-3 FULL-R3 pass (21) | 16,20,84,89,92,127,135,138,142,227,234,266,281,309,397,404,406,433,458,464,477 |
| **gains over arc-2 FULL (4)** | 20, 142, 281 (retrieval), 464 (screen-recovered enumerate) |
| **regressions vs arc-2 FULL (1)** | 17 (pass → accepted_holdout_fail — the preemption regression, §3a) |
| new traps vs arc-2 FULL (7) | 17, 105, 143, 164, 165, 300, 452 (all `accepted_holdout_fail`) |

**Outcome-class moves, all 257 paired ids (only classes that moved shown):**

| move | n |
|---|---|
| `gapped:exhausted` → `accepted_holdout_fail` | 4 |
| `gapped:enumerate_failed` → `pass` | 2 |
| `gapped:enumerate_failed` → `accepted_holdout_fail` | 2 |
| `gapped:exhausted` → `pass` | 2 |
| `pass` → `accepted_holdout_fail` | 1 (the regression) |
| `gapped:exhausted` → `gapped:enumerate_failed` | 1 |

**Reading:** the net +3 pass count (21 vs 18) breaks down honestly as 4
gains − 1 regression. Task 464 is the SAME "clean exemplar" Q5's own §3b
named as the decoy-tax's headline example (`ck_prog_if_stmt_n1_q0` cued,
exhausted before the enumerator ever ran) — it now PASSES because the
R2.5 screen's `NOT_SLACK` condition happens to hold for this particular
goal (its trigger-matching pool meets the budget), letting the enumerator
run and find the correct program exactly as CONTENT-STRIPPED already did
in arc 2. Task 17's regression is the mirror image: a goal where the OLD
path (bare enumerate) was already correct, and the NEW retrieval-first
ordering intercepts it with a trap.

## 6. Remaining-failure taxonomy (FULL-R3, ranked)

| rank | class | n/257 | share |
|---|---|---|---|
| 1 | `gapped:enumerate_failed` | 139 | 54.09% |
| 2 | `accepted_holdout_fail` | 76 | 29.57% |
| 3 | `pass` | 21 | 8.17% |
| 4 | `gapped:exhausted` | 17 | 6.61% |
| 5 | `runner_exception:TypeError` | 3 | 1.17% |
| 6 | `not_recognized` | 1 | 0.39% |

Compare arc-2 Q5 FULL: `gapped:enumerate_failed` 142 (55.3%), `accepted_
holdout_fail` 69 (26.8%), `gapped:exhausted` 24 (9.3%), `pass` 18 (7.0%).
The composition barely moved: `gapped:exhausted` shrank by 7 (24→17,
exactly the 7/17 covered-class rows that moved, §4) but `accepted_holdout_
fail` GREW by 7 (69→76) — most of the exhausted class's movement landed in
the trap bucket, not the pass bucket (only 2 of the 7 covered-class movers
became actual passes: 142 and 464). `gapped:enumerate_failed` shrank
slightly (142→139) as the enumerator now runs on cases it previously never
reached. The dominant remaining bottleneck is unchanged from arc 2: the
PROPOSE/search half (`gapped:enumerate_failed`, 54% of all outcomes) —
representability was never the obstacle for most of these tasks; no rung
found a program fitting all PRIMARY-revealed rows.

## 7. Density extrapolation (honest, labelled — never a fresh measurement)

Base: 90-exemplar pool, 12/257 (4.67%) held-out-honest ceiling (R0), this
phase's own measured retrieval-attributable gain (3 tasks: 20, 142, 281 —
task 464 is screen-attributed, not retrieval, and is excluded from this
calculation) against that 12-task ceiling gives a **mechanism capture
rate of 3/12 = 0.25** (coincidentally numerically equal to P7B's own
repair-conversion rate cited in R0 §6 — a coincidence, not a causal link,
named so it is not mistaken for one).

**Assumption stated plainly:** ceiling mass scales LINEARLY with exemplar
pool size. This is untested and likely optimistic in one direction (R0's
own arity cross-tab shows the demand/supply gap is concentrated at arity
3/4, so a real corpus expansion would plausibly help THOSE arities
disproportionately, not scale uniformly) and pessimistic in another (a
larger pool also grows the near-miss/trap population roughly in
proportion, per R0 §1's "a bigger pool without matching screening rigor
would grow the trap count roughly in proportion to genuine hits, not just
the hits" — so realized captures could grow slower than this linear
extrapolation implies, not faster).

| pool scale | linearly-scaled ceiling (k/257) | extrapolated mechanism captures (0.25 rate) |
|---|---|---|
| 1x (measured, 90) | 12 (4.67%) | 3 (1.17%) — this measurement |
| 2x (180) | 24 (9.34%) | 6.0 (2.34%) |
| 5x (450) | 60 (23.35%) | 15.0 (5.84%) |
| 10x (900) | 120 (46.69%) | 30.0 (11.67%) |

**Reading:** even a 10x corpus expansion, under this labelled linear
assumption and the CURRENT measured capture rate, projects to roughly
11.7% end-to-end — a real, material lever, but not a step-change; the
corpus-scale lever the prereg's own §5 null-reading names remains the
correct next direction, quantified here for the first time, honestly
bounded by its own stated assumption.

## 8. HR3 VERDICT — confirmed, non-regression, frozen artifacts intact

| suite | count | status |
|---|---|---|
| `test_program_synthesis_migrated.py` | 17 | green |
| `test_retrieval_migrated.py` | 31 | green |
| `test_screen_codebook_migrated.py` | 6 | green |
| `test_prog_synthesis_battery_migrated.py` | 21 | green, frozen artifact untouched |
| `test_prog_descent_migrated.py` | 17 | green |
| `test_prog_repair_migrated.py` | 13 | green |
| `test_descent_widening_migrated.py` | 11 | green |
| `test_mbpp_endgame_migrated.py` | 30 | green, frozen artifact untouched |
| `test_mbpp_diet_migrated.py` | 18 | green |
| `test_prog_chunks_migrated.py` | 11 | green |
| `test_mbpp_spec_migrated.py` | 67 | green |
| `test_mbpp_baseline_migrated.py` | — | green |
| `test_code_synthesis_baseline_migrated.py` | 11 | green |
| `test_retrieval_ceiling_migrated.py` | 19 | green |
| `test_prog_synthesis_selfimprove_migrated.py` | 5 | green |
| `test_mbpp_contamination_migrated.py` | shared gate | green |
| **`test_mbpp_arc3_endgame_migrated.py` (NEW)** | **40** | **green, ~3.3s** |
| render/prog_ir/prog_read/prog_constructions neighbour sweep | 295 passed, 1 skipped (unrelated) | green |

**Total: 659 passed** across the two sweeps (core required sweep 364 +
wider neighbour sweep 295), ~93s combined. Zero failures, zero regressions.

**Frozen-artifact hash checks (both re-verified live by `tests/test_mbpp_
arc3_endgame_migrated.py`):**

- `results/mbpp_endgame.json` (arc-2 FULL continuity) — sha256 unchanged,
  cited `outcome_hash_run1` matches the live file.
- `results/retrieval_oracle_ceiling.json` (R0 ceiling) — sha256 unchanged.

`git status`/`git diff --stat` on both paths confirm zero working-tree
diff — this phase never wrote to either file.

## 9. Honest scope statement

- Every HR1/HR2/HR3/migration-matrix/taxonomy/density number above
  re-derives from `results/mbpp_arc3_endgame.json`'s own fields — this
  document performs no computation the artifact does not already carry,
  cross-checked by `tests/test_mbpp_arc3_endgame_migrated.py`.
- HR1 is a genuine, registered **null** — 2 net passes, CI spans zero. Not
  smoothed into "weak" by the raw gain count (3) alone; the registered
  bar requires CI separation too.
- HR2's "~0" covered-class bar and "non-increasing" attempts-per-accept
  bar are BOTH measured **misses**, with named, verified root causes
  (R2.5's own already-documented `NOT_SLACK` all-or-nothing scoping;
  more goals reaching the 1-attempt accept floor). Neither is smoothed
  into a net-positive framing.
- One genuine regression (task 17) is named, root-caused, and counted
  plainly in the net-pass arithmetic, not absorbed silently.
- The density extrapolation is explicitly labelled as an assumption-based
  projection, never a new measurement, with the assumption's own
  optimistic AND pessimistic biases both named.
