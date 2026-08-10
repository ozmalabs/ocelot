# PROGRAM SYNTHESIS ARC 3 R0 — THE ORACLE CEILING (notes)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC3_PLAN.md` (R0),
`PROGRAM_SYNTHESIS_ARC3_PREREG.md` (HR1's bar, derived from this
document's numbers), `scripts/retrieval_oracle_ceiling.py` (the driver),
`results/retrieval_oracle_ceiling.json` (the artifact — every number below
re-derives from its `runnable_rows`), `tests/test_retrieval_ceiling_
migrated.py` (16 gates, 0.86s). No synthesis/engine/seed/spec code was
touched — this phase is a pure measurement, structurally the same class as
`scripts/mbpp_endgame_battery.py` / `scripts/mbpp_train_diet.py`'s own
leave-N-out probe.

---

## 1. The pool

| metric | value |
|---|---|
| train-split tasks (task_id >= 601) | 120 |
| emit through `emit_prog_ir` whole | **90** |
| emit rate | **75.0%** |
| arity distribution | `{1: 58, 2: 27, 3: 5}` |
| predictable (native-oracle-only) | 63/90 |

Byte-identical to `PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md`'s own measured
75.0% train emit rate — the SAME 90-program population Q3's chunk-mining
phase measured, confirming this is the correct, canonical exemplar pool
for retrieval-shaped proposal (never a different or re-filtered set).

**A structural density gap, quantified:** the pool has ZERO arity-4
exemplars, while 2/257 test tasks have arity 4
(`{1: 171, 2: 66, 3: 18, 4: 2}`) — these 2 tasks are unreachable by
retrieval at ANY rung, at the current pool size, regardless of ranking
quality. Named here because it is the cleanest single number for "how far
the 90-exemplar pool is from covering the failures" (§6 of the prereg's
null reading).

## 2. The ceiling table (per rung, revealed vs held-out)

All figures over n=257 (100% PRIMARY-runnable, per arc-2's HQ2), Wilson
95% CIs.

| rung (cumulative through) | k rev | p rev | CI rev | k held | p held | CI held |
|---|---|---|---|---|---|---|
| (a) as-is | 20 | 7.78% | [5.09, 11.71] | 8 | 3.11% | [1.59, 6.02] |
| (a)-(b) +perm | 21 | 8.17% | [5.41, 12.17] | 9 | 3.50% | [1.85, 6.52] |
| (a)-(c) +leaf-delta | **27** | **10.51%** | [7.32, 14.85] | **12** | **4.67%** | [2.69, 7.98] |
| (a)-(d) +one-hole (UPPER BOUND) | 201 | 78.21% | [72.77, 82.82] | 185 | 71.98% | [66.20, 77.12] |

**The honest ceiling for arc 3's mechanically-buildable rungs (a)-(c) is
12/257 = 4.67% held-out-verified.** Rung (d) is reported per its own
requirement to be measured, but see §4 — it is an unreliable upper bound
and must not be read as an achievable target.

## 3. The trap-mass finding

| rung | revealed-solved | held-out-solved | trap n | trap rate |
|---|---|---|---|---|
| (a) | 20 | 8 | 12 | 60.0% |
| (a)-(b) | 21 | 9 | 12 | 57.1% |
| (a)-(c) | 27 | 12 | 15 | 55.6% |

**Trap task ids (a)-(c):** `56, 62, 67, 68, 72, 113, 129, 143, 164, 281,
285, 434, 454, 455, 461` (15 ids — a train exemplar fits every revealed
row of these test tasks but fails the row PRIMARY holds back).

More than half of every rung-(a)-(c) revealed-pass is a trap. This is
retrieval's own version of Q0-A's `accepted_holdout_fail` finding
(56.8% under the STRESS protocol) — the SAME overfitting shape, one layer
up (whole-program retrieval instead of enumerator search), and it is the
core justification for R1's universal screening lane requiring the SAME
held-out verification discipline the CEGIS/repair loop already performs,
not a revealed-rows-only pre-filter.

**Worked trap example — task 56** (pinned live in the test suite):
exemplars `762`/`803`, run as-is, both pass every revealed row of task
56 but fail its held-out row.

## 4. Rung (d) is an unreliable upper bound — the headline residual

Rung (d)'s own held-out filter barely discriminates:

| rung | revealed-only-here | ALSO held-out-passes | survival rate |
|---|---|---|---|
| (a)-(c) | 27 | 12 | 44.4% |
| (d), exclusive of (a)-(c) | 174 | 173 | **99.4%** |

99.4% vs 44.4% is not a coincidence — it is a measured DEFECT in the rung
(d) proxy, honestly reported per the task's own "label it" instruction.
Rung (d) masks the near-miss exemplar's own final compute statement and
asks only "does the PREFIX (everything before it) execute without
trapping on this row" — it never checks whether the masked statement's
REQUIRED value is actually derivable, unique, or consistent with what the
row needs. For a short exemplar (many MBPP reference solutions are 1-3
statements — 25/90 are a single `return <expr>`, per
`PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md` §4), the "prefix" is often EMPTY or
trivial, so the check passes almost vacuously regardless of row content —
which is exactly why it barely changes between revealed and held-out rows
(both come from the SAME task, so they share argument types/domain, and
an empty-or-trivial prefix cannot trap on either).

**This is reported honestly, not smoothed over, and rung (d) is EXCLUDED
from the registered HR1 bar** (`PROGRAM_SYNTHESIS_ARC3_PREREG.md` §2) —
the discounted arithmetic the task asks for is stated in full there, but
flagged as an unreliable "optimistic envelope," never the actual target.
A sharper rung (d) would need a genuine per-row hole-value DERIVATION
(the P7B `_derive_final_expr`/`_derive_fold_step` scopes, applied at the
retrieved-exemplar grain instead of the codebook-construction grain) —
named as a residual for R1/R2, not attempted here (R0 is measurement-only
and the task explicitly sanctioned an approximate proxy for this rung).

## 5. Q5-failure coverage

Of `results/mbpp_endgame.json`'s FULL arm's 239 non-pass rows:

| coverage class | n/239 | % |
|---|---|---|
| covered by rung (a)-(c), held-out-honest | **10** | **4.2%** |
| covered ONLY by rung (d)'s upper-bound proxy | 160 | 66.9% |
| uncovered at any rung | 69 | 28.9% |

**The 10 honestly-covered task ids:** `105, 106, 115, 238, 242, 284, 394,
405, 412, 414`. Each of these is a Q5 FULL-arm failure for which SOME
train exemplar, adapted at rung (a), (b), or (c), passes every revealed
row AND the held-out row — a genuine, small, real target set for arc 3's
R1-R3 mechanism to actually reach. The 160-task "(d)-only" figure is
reported per §4's caveat and must not be read as "160 latent passes."

Two of the 10 (`105`, `115`) are worth naming: `105` is rung-(a) genuine
(exemplar `798`, as-is); `115` and the rest span rungs (a)-(c) — see the
artifact's `runnable_rows` for the full per-task breakdown.

## 6. HR1's bar — the arithmetic, stated exactly as instructed

```
a-c heldout-honest mass         = 12 / 257  (4.67%)
d-only incremental mass         = 173 / 257 (67.3%), heldout-upper-bound reading
P7B measured repair conversion  = 0.25  (1/4 of the P7-A holdout_fail set
                                  converted — PROGRAM_SYNTHESIS_P7B.md §4/§7)
discounted d contribution       = 173 * 0.25 = 43.25 tasks  (16.83%)
"optimistic combined envelope"  = 12 + 43.25 = 55.25 / 257  (21.5%)
```

**Registered bar (the number actually used to judge FULL-R):** 12 net
passes (4.67pp) — the a-c honest ceiling ONLY, because §4 shows rung
(d)'s mass was never properly held-out-verified, so discounting it by a
conversion rate measured on a DIFFERENT (properly-verified) population
would overstate the target by an unknown amount. Reading bands:
**strong** confirmation >= 6 net passes CI-separated; **weak/marginal**
1-5 net passes CI-separated; **null** if the CI spans zero or the point
delta is <= 0 (full detail: `PROGRAM_SYNTHESIS_ARC3_PREREG.md` §4).

## 7. Pool stats and arity cross-tab (full)

| test arity | n test tasks | n pool exemplars this arity |
|---|---|---|
| 1 | 171 | 58 |
| 2 | 66 | 27 |
| 3 | 18 | 5 |
| 4 | 2 | **0** |

The arity-1 population dominates both sides (171 test tasks, 58 pool
exemplars) — the highest-density pairing, and correspondingly where all
of rungs (a)-(c)'s honest passes concentrate (verified in the per-task
rows). Arity-3 has only 5 pool exemplars against 18 test tasks (a 3.6x
demand/supply gap); arity-4 has zero supply at all.

## 8. Determinism, runtime, gates

- **Twin-run byte-identical**: `determinism.identical: true`, both
  outcome hashes equal, total elapsed **6.96s** (well inside the ~20 min
  box; no time-box prefix cut was ever needed).
- **`tests/test_retrieval_ceiling_migrated.py`: 16 gates, 0.86s** —
  artifact schema (rows are the baseline, aggregates re-derive, `bounds`
  block matches the script's own `BOUNDS` dict verbatim), monotonicity
  (cumulative ceilings never decrease; held-out never exceeds revealed at
  the same rung), trap-mass arithmetic re-derived from the ceiling
  tables, Q5-failure-coverage partition sums to 239, 3 pinned per-task
  rows re-verified LIVE (task 56 — rung-a trap; task 105 — rung-a genuine
  pass; task 138 — rung-c genuine pass via a real `Eq -> Gt` comparator
  edit), the shared contamination gate run as a subprocess (passes), an
  AST-scan proving the script's only two `["code"]` reads are both
  train-scoped inside `build_pool`.
- **Neighbor check**: `tests/test_mbpp_contamination_migrated.py` passes
  (7 passed) when run standalone from this phase's own test file.

## 9. Honest residuals

1. **Rung (d) is a weak upper bound** (§4) — the headline residual of
   this phase. Reported in full, excluded from the registered bar, named
   as an R1/R2 design item (a genuine per-row derivability check, not a
   prefix-crash proxy) rather than fixed here (R0 is measurement-only).
2. **The leaf-delta search (rung c) is bounded and may miss a genuine
   near-miss fix outside its catalog** — only ONE literal or ONE operator
   is ever changed, from a fixed numeric offset/absolute set (documented
   in `BOUNDS`) or a fixed op family; a task needing a two-leaf edit, or
   an operator outside `{Plus,Minus,Times,Div,Mod}`/`{Eq,Lt,Lte,Gt,Gte}`,
   is honestly reported as unsolved at rung (c), never silently searched
   further. This bound is a deliberate, documented scope limit (the task
   brief's own "bounded, exclude-powered" instruction), not an oversight.
3. **The near-miss anchor for rungs (c)/(d) is a SINGLE candidate**
   (max revealed-rows-passed, ties broken by fewest divergent leaves,
   then by exemplar/perm order for determinism) — a task could in
   principle have a DIFFERENT near-miss that a different tie-break would
   have surfaced and that rung (c)'s edit search would have solved; this
   is a real, bounded scope choice (the task brief specifies "the BEST"
   near-miss singular), not an oversight, but it means the (a)-(c)
   ceiling reported here is itself a slight underestimate of what an
   exhaustive multi-anchor search could find (bounded, honestly, in the
   opposite direction from rung (d)'s overestimate).
4. **The arity-4 test tasks (2/257) are structurally unreachable** at
   this pool size (§1) — a direct, quantified instance of the corpus-
   scale null reading the prereg registers (§6): more paired train
   exemplars, not a fifth rung, is the lever this measurement points at.
5. **`emit_prog_ir`'s all-or-nothing scope caps the pool at 90/120**
   (unchanged from Q3 — a function with any blocker contributes zero
   exemplars, never a partial one) — the SAME honestly-reported ceiling
   Q3 named, reproduced here rather than re-litigated.
6. **The one-hole-skeleton mask is scoped to exactly one statement**
   (the exemplar's own final compute statement, or the statement
   assigning a trailing bare-var return — a single, fixed, mechanical
   rule) — a deeper program with a bug two statements from the end would
   not be helped by this rung's mask, by design (the task brief specifies
   masking "exactly ONE statement").
