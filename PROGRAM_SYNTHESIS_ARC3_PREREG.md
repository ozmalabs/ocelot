# PROGRAM SYNTHESIS ARC 3 — PREREGISTRATION (R0: the oracle ceiling)

**Date:** 2026-08-01. Written from `scripts/retrieval_oracle_ceiling.py` /
`results/retrieval_oracle_ceiling.json` (twin-run byte-identical,
`determinism.identical: true`, 6.96s total), per
`PROGRAM_SYNTHESIS_ARC3_PLAN.md`'s own instruction (§2, R0): *"measure
before building"* — this document's HR1 bar is derived from that
measurement, not from ambition. Companion to
`PROGRAM_SYNTHESIS_ARC2_PREREG.md` (the PRIMARY/OFFICIAL/STRESS split
protocol, unchanged and reused verbatim), `PROGRAM_SYNTHESIS_ARC2_Q5.md`
(the FULL arm's 18 passes / 239 failures this document's null reading
quantifies against), `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md` (the full
write-up, tables, and residuals this prereg's numbers are drawn from).

## 0. What R0 measured, in one paragraph

For every one of the 257 MBPP test tasks (PRIMARY protocol: every
parseable assert revealed except the last, which is held out), R0 swept
the pool of every train-split (task_id >= 601) reference program that
`emit_prog_ir` accepts whole (90/120 = 75.0% emit rate, byte-identical to
`PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md`'s own measured train emit rate) and
asked, at four increasingly permissive rungs, whether ANY exemplar could be
adapted to pass it: **(a) as-is** (args mapped by position), **(b)** under
**argument permutation** (bounded: exemplar arity <= 4), **(c)** under a
**bounded single-leaf edit** (one numeric/string literal, or one binary
operator swapped within a fixed op family), **(d)** an explicit **upper
bound**: masking the exemplar's own final compute statement and asking
only whether the remaining skeleton is derivable (does not trap) on every
row — never a claim that step is actually synthesizable.

## 1. The measured ceiling (the numbers HR1's bar is built from)

| rung (cumulative through) | k (revealed-pass) | k (held-out-honest) | n | p (revealed) | p (held-out) |
|---|---|---|---|---|---|
| (a) as-is | 20 | 8 | 257 | 7.78% [5.09%, 11.71%] | 3.11% [1.59%, 6.02%] |
| (a)-(b) +permutation | 21 | 9 | 257 | 8.17% [5.41%, 12.17%] | 3.50% [1.85%, 6.52%] |
| (a)-(c) +leaf-delta | **27** | **12** | 257 | **10.51%** [7.32%, 14.85%] | **4.67%** [2.69%, 7.98%] |
| (a)-(d) +one-hole (UPPER BOUND, see §2) | 201 | 185 | 257 | 78.21% [72.77%, 82.82%] | 71.98% [66.20%, 77.12%] |

**The honest, retrieval-executable ceiling is rungs (a)-(c): 12/257 =
4.67% [2.69%, 7.98%]** — every one of these three rungs is exactly what
R1/R2 mechanically build (retrieve whole exemplar → run as-is / permute
args / swap one leaf), so this is a REAL, achievable-in-principle upper
bound for arc 3's FULL-R mechanism, not a hypothetical.

**Trap mass (the gap between revealed-pass and held-out-honest at each
rung) is large and must not be discounted:**

| rung | revealed-solved | held-out-solved | trap count | trap rate |
|---|---|---|---|---|
| (a) | 20 | 8 | 12 | **60.0%** |
| (a)-(b) | 21 | 9 | 12 | 57.1% |
| (a)-(c) | 27 | 12 | 15 | 55.6% |

More than half of every retrieval candidate that fits the revealed rows
FAILS the one held-out row it never saw — this is the SAME overfitting
shape Q0-A's own STRESS-protocol baseline found (`accepted_holdout_fail`,
56.8%) reproduced one layer up, at the retrieval grain instead of the
enumerator grain. **This is the decisive argument for R1's universal
screening lane: screening on revealed rows alone is NOT enough to avoid
burning an attempt on a bad retrieval — the screen must be paired with the
held-out verification the CEGIS/repair loop already performs, never
treated as a substitute for it.**

## 2. Rung (d) is measured to be an unreliable upper bound — reported honestly, excluded from the bar

Rung (d)'s own held-out filter barely discriminates from its revealed
filter: **174 tasks clear revealed-(d) exclusively; 173 of those (99.4%)
ALSO clear the held-out-(d) filter** — compare rungs (a)-(c), where only
12/27 (44.4%) of revealed-passers survive held-out. The reason is
structural, not a coincidence: rung (d)'s held-out check only asks whether
the near-miss exemplar's OTHER statements execute without trapping on the
held-out row, which is nearly always true regardless of whether the
MASKED statement's required value is actually derivable or consistent —
it never verifies the thing HR1 actually needs to know. **Rung (d) is
therefore reported for completeness (the task's own instruction: "label
it") but is EXCLUDED from the registered HR1 bar below.** A future,
sharper version of rung (d) would need a genuine per-row hole-value
derivation (the P7B `_derive_final_expr`/`_derive_fold_step` scopes,
applied to a retrieved exemplar's own final statement instead of a
codebook construction's), not this prefix-crash proxy — named as an R1/R2
residual, not attempted here (out of R0's pure-measurement scope).

**The discounted arithmetic, stated as instructed (never silently
smoothed over, always paired with the residual above):**

```
a-c heldout-honest mass         = 12 / 257  (4.67%)
d-only incremental mass         = 173 / 257 (67.3%), heldout-upper-bound reading
P7B measured repair conversion  = 0.25  (1/4 of the P7-A holdout_fail set
                                  converted by trace-guided repair —
                                  PROGRAM_SYNTHESIS_P7B.md §4/§7)
discounted d contribution       = 173 * 0.25 = 43.25 tasks  (16.83%)
"optimistic combined envelope"  = 12 + 43.25 = 55.25 / 257  (21.5%)
```

This 21.5% "optimistic envelope" is reported because the task instructs
stating the arithmetic — **it is NOT the registered bar.** Given §2's own
finding that rung (d)'s held-out filter is measured to be nearly
non-discriminating, applying a repair-conversion-rate discount to a mass
that was never properly held-out-verified in the first place would
overstate the target by an unknown, unbounded amount. The registered bar
uses only the a-c mass.

## 3. Q5 FULL failure coverage — how much of the 239-task failure set has an oracle solution

| coverage class | n / 239 | % |
|---|---|---|
| covered by rung (a)-(c), held-out-honest | **10** | **4.2%** |
| covered ONLY by rung (d)'s upper-bound proxy | 160 | 66.9% |
| uncovered at any rung | 69 | 28.9% |

Task ids covered honestly (a)-(c): `105, 106, 115, 238, 242, 284, 394,
405, 412, 414` — a genuine, small, real target: these 10 failing MBPP test
tasks have a train exemplar that a retrieval mechanism COULD have found
and adapted (as-is, permuted, or one-leaf-edited) to a fully-verified
pass, including the row PRIMARY never reveals. The 160-task "(d)-only"
figure is reported per §2's caveat and must never be read as "160 latent
passes" — only as "the near-miss's other statements don't obviously
crash," a much weaker claim.

## 4. Hypotheses

### HR1 (the fourth try at making held content pay, now at program grain)

**Claim.** FULL-R (retrieval + screen + adapt, arc 3's R1-R3 stack) minus
NO-RETRIEVAL (the arc-2 stack, screening ON so the delta isolates
retrieval, not the screen) on MBPP test (PRIMARY protocol), Newcombe CI,
same paired task-id set: **CI-separated > 0.**

**The bar, derived from §1-§3, not ambition:** the maximum HONEST ceiling
any working rung-(a)-(c) mechanism could gain over the arc-2 stack on this
exact 90-exemplar/257-task pairing is **12 net passes (4.67pp)** — R1/R2
cannot manufacture a pass beyond what SOME pool exemplar's adapted form
already encodes, and 15/27 (55.6%) of even the revealed-fitting candidates
are traps a correct screen+holdout discipline must reject. Registered
reading:

- **Strong confirmation:** FULL-R gains >= 6 net passes (roughly half the
  12-task ceiling, ~2.3pp), CI-separated.
- **Weak/marginal confirmation:** FULL-R gains 1-5 net passes,
  CI-separated (a real but small effect, consistent with retrieval
  engaging on a genuine subset of the 12-task honest ceiling but not all
  of it — R1/R2's own ranking/screening quality will determine where in
  this range the result lands).
- **Null (the registered reading, §6):** the CI spans zero, OR the point
  delta is <= 0 net passes. Given the ceiling is already only 12/257
  (a SMALL target that even a perfect oracle ranker cannot exceed), a
  null here is a materially different finding from arc 2's HQ3 nulls
  (which nulled against an UNBOUNDED chunk-shape diet with no measured
  ceiling) — it would mean R1/R2's retrieval+adapt+screen mechanism could
  not even reach its OWN honestly-measured, small, upper bound.

### HR2 (decoy tax eliminated)

**Claim, unchanged from `PROGRAM_SYNTHESIS_ARC2_PREREG.md`'s framing but
now the primary defect this arc's screening lane targets.** Q5 measured
24/257 (9.3%) `gapped:exhausted` rows in the FULL arm, ALL 24 carrying a
non-null (chunk- or codebook-cued) construction that consumed the fixed
attempt budget before the enumerator ran (`PROGRAM_SYNTHESIS_ARC2_Q5.md`
§3b) — the decoy tax. Under R1's universal execution screen (every
proposal, retrieved OR codebook, is ProgEval'd on revealed rows before it
may occupy an attempt), this class should fall to **~0**, and
attempts-per-accept should be non-increasing versus the arc-2 FULL arm on
the SAME paired task-id set. This bar is a mechanism claim (screening
removes wrong-candidate attempt burn), independently verifiable from
HR1's retrieval-content claim — a task could gain nothing from retrieval
content (HR1 null) while still eliminating the decoy tax (HR2 confirmed),
and the two must be reported separately, never conflated into one
"arc 3 worked/didn't" verdict.

### HR3 (non-regression)

Unchanged, the arc-1/arc-2 discipline verbatim: the internal battery
(`results/prog_synthesis_battery.json`, 21+ gates) and the arc-2 endgame
continuity rows (`results/mbpp_endgame.json`'s FULL/CONTENT-STRIPPED
arms, per-task-id) stay green/byte-identical wherever frozen; any flip is
a named STOP-defect with its own root-cause paragraph, never absorbed
into a net-positive framing.

## 5. The registered null reading (if HR1 nulls even at this ceiling's grain)

**If FULL-R's measured gain over NO-RETRIEVAL nulls (CI spans zero or the
point delta is <= 0), the honest reading is NOT "retrieval doesn't work"
in general — it is that 90 exemplars sit below retrieval's useful
density on THIS corpus, quantified precisely by this phase's own
per-task nearest-miss data:**

- **12/257 (4.67%) is the entire honestly-reachable ceiling** at the
  current pool size — even a PERFECT ranker (always picks the single
  best-matching exemplar, at zero search cost) cannot exceed this number
  on this pool. A real R1 ranker, working under a top-k budget and a
  noisy scoring signal, will realistically capture some FRACTION of this
  12-task ceiling, not all of it — so a small or null HR1 delta is the
  EXPECTED outcome of a small ceiling, not evidence the mechanism is
  broken.
- **2/257 test tasks (arity-4) have ZERO pool exemplars of matching
  arity at all** (`results/retrieval_oracle_ceiling.json`'s
  `pool.pool_arity_distribution`: arities {1: 58, 2: 27, 3: 5}, no arity-4
  entries) — these are PERMANENTLY unreachable by retrieval at the
  current pool size regardless of ranking quality, a direct, quantified
  density gap.
- **The trap rate (55.6%-60.0% across rungs a-c) means density alone is
  not the whole story** — even where an arity-matched exemplar exists,
  more often than not it is a false-positive under revealed rows alone,
  so a bigger pool without matching screening rigor would grow the trap
  count roughly in proportion to genuine hits, not just the hits.
- **The next lever, registered now:** corpus SCALE (more paired
  train/test exemplar pairs — MBPP's own 120-task train split is small;
  a broader same-domain corpus, or synthetic paraphrase expansion of the
  existing 90, are the two concrete directions), not a fourth proposal
  MECHANISM. This mirrors arc 2's own registered-null discipline (HQ3
  nulling three times pointed at proposal GRAIN, not diet size; this
  null, if it occurs, would point at corpus SCALE, not proposal grain,
  since grain is exactly what arc 3 already changed).

## 6. Contamination — restated for arc 3

Unchanged from `PROGRAM_SYNTHESIS_ARC2_PREREG.md` §7, restated because R0
is the first arc-3 phase to lean on it for BENCHMARK-facing (not
train-internal) rows: **running a TRAIN-split program against TEST-split
ROWS (parsed asserts only — never code or prompt text) at EVALUATION time
is measurement, not learning, and is contamination-legal.**

1. **Train-split `code` is the entire, legal content source for this
   phase** — arc 3's whole premise (retrieval against whole held train
   programs) requires reading it; the canonical MBPP split assigns
   task_id >= 601 to be learned/retrieved from.
2. **Test-split `code` is never read.** `mbpp_zero_shot_baseline.
   split_tasks`'s `_strip_code` removes it at split time (imported and
   reused verbatim, the same enforcement point every prior arc-2 phase
   uses); `domains.mbpp_spec.parse_asserts`/`split_rows` never read
   `task["code"]` by construction (Q2's own module-level guarantee).
   `tests/test_retrieval_ceiling_migrated.py::
   test_script_never_reads_test_split_code_field` AST-scans this phase's
   own runner and proves exactly 2 `["code"]` subscripts exist in the
   whole file, both inside `build_pool`, both operating on its
   `train_tasks` parameter.
3. **No learning path exists in this script at all** — R0 performs no
   seed-writing, no `domains.teach.teach` call, no codebook/rule
   installation of any kind (unlike Q3's train-diet MINER, which DOES
   install content — this is a pure oracle SWEEP, one level more
   conservative than Q3's own contamination posture). The pool exemplars
   (whole IR Term-JSON, derived from train code) exist only as in-memory
   Python objects for the duration of one process; nothing is written
   into `seeds/`.
4. **The artifact (`results/retrieval_oracle_ceiling.json`) is an eval
   log** (the Q0-A/Q5 precedent), legitimately recording which train
   exemplar id solved which test task — this is not a codebook, cue
   token, bigram row, or taught shape, and it is excluded from
   `tests/test_mbpp_contamination_migrated.py`'s `SCAN_TARGETS` for the
   same reason Q5's own artifact is.

## 7. Standing rules (carried, binding for arc 3)

- **Power the gate before the endgame.** Every R0 number above carries a
  Wilson 95% CI over n=257 (the PRIMARY-runnable denominator, 100% per
  arc-2's HQ2); deltas within ~3x the per-episode step (1/257 = 0.39pp)
  are never claimed as movement.
- **A baseline is a list.** `results/retrieval_oracle_ceiling.json`'s
  `runnable_rows` array (257 entries) IS the baseline — every aggregate
  in this document re-derives from it, gated by
  `tests/test_retrieval_ceiling_migrated.py`.
- **No silent caps.** Every bound this phase used (permutation arity
  <= 4, the leaf-delta numeric/op catalogs, the rung-(d) masked-statement
  scope) is named explicitly in `results/retrieval_oracle_ceiling.json`'s
  own `bounds` block AND transcribed here (op families:
  `{Plus, Minus, Times, Div, Mod}` arithmetic /
  `{Eq, Lt, Lte, Gt, Gte}` comparison), never silently applied.
- **Synthetic-proven mechanism != benchmark value.** This document
  reports a CEILING (what retrieval COULD buy with perfect ranking), not
  a benchmark accept rate — R1-R3 will separately measure the actual,
  imperfect-ranker accept rate against this ceiling.
- **Eval-subset coverage is part of every claim.** Every number above
  carries its denominator (257 PRIMARY-runnable test tasks; 90/120 = 75%
  train-emittable exemplar pool; 239 Q5 FULL-arm failures) — never a bare
  percentage.
- **Protocol boundaries are labelled in the data.** This phase runs
  PRIMARY only (the arc-wide anchor); no OFFICIAL/STRESS arm was run
  (R0's job is the ceiling under the SAME protocol arc 3's endgame will
  use, not a protocol comparison).

## 8. OUTCOMES (append-only — recorded as each phase closed, never edited
   retroactively)

### R0 (commit `06a24dcade`)

Ceiling measured exactly as this document's §1 states: 12/257 (4.67%)
[2.69%, 7.98%] held-out-honest at rungs (a)-(c); trap mass 55.6%-60.0%;
rung (d) measured unreliable and excluded from the bar. Registered HR1 bar
above (strong >=6, weak 1-5, null otherwise) is the bar R3 judges against,
unchanged. `PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md`.

### R1+R2 (commit `ed701de747`)

Store (90 exemplars) + ranked retrieval (rule-selected top-5) + the a-d
adaptation ladder landed. End-to-end ceiling capture: 2/12 (tasks 138,
406), both via rung (d) with a DIFFERENT exemplar than R0's own oracle
anchor. The codebook-side universal screen was attempted, MEASURED to
false-negative legitimate partial-cover constructions (a regression
against `test_prog_repair_migrated.py`'s `la_10` fixture, no pin
allowance), and REVERTED. HR2 confirmed at retrieval grain only.
`PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md`.

### R2.5 (commit `0a513033a5`)

The codebook-side screen redone SCOPED: SCREENABLE iff NOT
DESCEND_APPLICABLE (the reused 3-part predicate), frozen at goal-mint
against the FULL budget. Confirmed on a dedicated fixture: a chunk-cued
over-budget decoy pool dies for free, the goal reaches the enumerator
with its whole budget; `la_10`'s partial-cover regression scenario
reproduces byte-identical pre-Arc3 behaviour. Scope named honestly at
landing: 17/24 of Q5's `gapped:exhausted` mass is in scope by
construction, 7/24 (starter-codebook-shape, DESCEND_APPLICABLE) is not,
by design. Seed v1.5.1 (57 rules); sweep 657 green.

### R3 — THE POWERED ENDGAME (this phase)

**FULL-R3: 21/257 = 8.17% [5.41%, 12.17%]** (up from arc-2 Q5 FULL's
18/257 = 7.00%; trajectory 0.42% → 7.00% → 8.17%).

**HR1: NULL (registered reading).** net_passes = 2 (3 gains: tasks 20,
142, 281, all retrieval rung-c/d; 1 regression: task 17 — a retrieval
rung-d trap PREEMPTED an already-correct bare-enumerate pass, a genuinely
new failure mode this phase names). Newcombe delta +0.78pp, 95% CI
[-3.97pp, +5.55pp] — CI spans zero. Below the registered weak/marginal
band (which additionally requires CI separation the raw 1-5 count alone
does not supply). Consistent with the ceiling's own small size (12/257)
under an imperfect ranker, exactly as §5's null-reading anticipated.

**HR2: PARTIALLY CONFIRMED, materially narrower than registered.** The
7-row registered residual (starter-codebook-shape) is 100% unchanged, per
R2.5's own design. The 17-row covered (chunk-cued) class does NOT reach
"~0": 10/17 remain `gapped:exhausted` unchanged because the screen's own
`NOT_SLACK` gate (frozen pool0 >= budget) never engages for them — an
already-documented R2.5 residual, now measured at full-corpus scale for
the first time and found to carry real weight (59% of the covered class).
4/17 resolve via the screen (only 1 becomes an actual pass — task 464,
Q5's own named decoy-tax exemplar, now confirmed fixed in the wild); 3/17
resolve via retrieval independently. Attempts-per-accept also measurably
INCREASED (0.931 → 1.000 vs Q5 FULL), missing that registered bar too,
root-caused to more goals reaching the 1-attempt retrieval-accept floor.

**HR3: CONFIRMED.** 659 tests green (364 required sweep + 295 wider
neighbour sweep), zero regressions in the test suite; both frozen
continuity artifacts (`results/mbpp_endgame.json`, `results/retrieval_
oracle_ceiling.json`) sha256-verified byte-untouched. One CONTENT
regression (task 17) is named and root-caused, not a suite failure.

Full detail: `PROGRAM_SYNTHESIS_ARC3_R3.md` (the powered tables and
per-verdict writeup), `PROGRAM_SYNTHESIS_ARC3_SUMMARY.md` (the arc-wide
synthesis and three-arc meta-finding), `results/mbpp_arc3_endgame.json`
(the artifact), `tests/test_mbpp_arc3_endgame_migrated.py` (40 gates).
