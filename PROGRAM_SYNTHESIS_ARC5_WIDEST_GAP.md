# PROGRAM SYNTHESIS ARC 5 — THE WIDEST-GAP CRITERION: gap as ONE weight, measured precisely

**Date:** 2026-08-01. Driver: `scripts/arc5_widest_gap_probe.py`. Artifact:
`results/arc5_widest_gap.json`. Gate: `tests/test_arc5_widest_gap_migrated.py`,
18/18 passed. No synthesis/engine/seed/spec code touched — measurement only,
no Rust changes.

**This document was reframed twice, mid-measurement, by the project author.**
Both reframes are addressed in place (§5 and §6) rather than folded silently
into the original question, because the ORIGINAL framing this arc started
from was itself wrong and the record should show why:

1. **Original framing:** "does a widest-gap CRITERION replace the hand-built
   LEXICON?" — a false either/or. The correct architecture is **weighted
   collapse**: gap is one weight among several that should feed one
   selection (Γ production weights, selection ∝ exp(w)), not a sole decider.
2. **Second addition:** record **intent-evidence** features (`arity_gap` —
   declared parameters the accepted program never reads) alongside gap, and
   run a head-to-head: does the cheapest available signal (arity_gap) beat
   the expensive one (gap-score)?

The headline still stands and is reported first (§1). The reframed verdict
(§5–§7) is the part that should govern what gets built next.

---

## 0. The criterion, precisely

**Refutation first, always.** A relaxation — a conjectured invariant of the
target function — is tested against the REVEALED rows alone before it is
ever scored or applied. If the rows already contradict it, it is discarded:
never scored, never used to manufacture data. This is checked live
(`relax_permutation`/`relax_idempotent`, `scripts/arc5_widest_gap_probe.py`)
and verified by a constructed counterexample fixture
(`tests/test_arc5_widest_gap_migrated.py::test_live_refuted_permutation_is_never_applied`).

**The relaxation family measured:**

| relaxation | conjecture | refutable how |
|---|---|---|
| `sym_full_S<n>` | full permutation symmetry over all `n` declared args | any permuted image of a revealed row collides with a differently-labelled revealed row |
| `sym_2cycle_<i>_<j>` (one per pair) | symmetry in JUST that pair of args, others fixed | same collision check, restricted to the pair |
| `idempotent_fixed_point` | `f(x,x,...,x) = x` | a revealed all-equal-args row whose output isn't that value; requires ≥1 SUPPORTING all-equal row before any augmentation (an unrefuted-but-unsupported conjecture manufactures nothing) |
| `monotone_{non}{de,in}creasing_arg_k` | directional in one argument | both directions observed in revealed-row pairs differing in exactly that arg → refuted in both directions |

**Monotonicity is refutation-tested but NOT gap-scored** — no augmentation
mechanism was built for it (there is no way to manufacture a new *labelled*
row from "the function doesn't decrease" without inventing a magnitude not
in the data). It contributes to the refutation-rate accounting only. Named
honestly, not smoothed into a positive.

**Output-range/bound constraints were considered and excluded from the
catalogue entirely** — a bound derived from revealed rows' own min/max
output cannot be refuted BY those same rows (true of them by construction),
which fails this measurement's own refutation-first discipline before it
even starts.

**The gap, operationally.** `V0` = the number of DISTINCT behaviours
(grouped by output signature over a WIDE PROBE grid — the cartesian
recombination of each argument's own observed values across the revealed
rows, plus the relaxation's own augmented-row inputs) reachable by a small,
FIXED op inventory (`Plus/Minus/Times/Max/Min/Abs/Neg`, term size ≤ 5, a
task-derived constant pool capped at 4) that are consistent with the
revealed rows alone. `V1` = the number ALSO consistent with the relaxation's
augmented rows (manufactured, oracle-consistent, zero new magnitudes — the
same discipline `PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md` validated for S3).
**`Gap = V0 − V1`** (both reported; `log2(V0/V1)` also recorded per
relaxation). Every candidate check runs through the REAL native `evaluate()`
Term evaluator (`s._inner.evaluate`) — arithmetic is never reimplemented in
Python.

This is an honest APPROXIMATION of "how much of the decision space" a
relaxation removes: distinctness is measured over a *finite, data-derived*
probe grid, never full extensional equality. Stated once here, not smoothed
over in the numbers below.

**Selection.** Among non-refuted, non-self-contradicting (`V1 > 0` — the
same "withdraw on unsatisfiability" rule the orbit result registered)
relaxations, pick the largest gap; ties break by smaller `V1`, then by name.
Held-out data is read ONLY afterward, by one function
(`verify_against_held_out`), for SCORING — never for selection (audited
live, `tests/test_arc5_widest_gap_migrated.py`'s isolation gates).

---

## 1. The headline: br_10, unaided

| | value |
|---|---|
| Revealed rows | `(1,9,3)→9`, `(7,2,5)→7`, `(4,4,4)→4` |
| Candidates generated (op inventory, size≤5) | 24,962 |
| Matching revealed rows alone | 138 |
| Relaxations considered | 5 (`sym_full_S3`, 3×`sym_2cycle`, `idempotent_fixed_point`) |
| Refuted | 0 |
| **Selected (widest gap)** | **`sym_2cycle_a_c`** (gap=1, tied with `sym_full_S3` and `sym_2cycle_b_c`, alphabetical tie-break) |
| Representative program | `Max(Max(a, b), c)` |
| Held-out check | `(2,4,11)→11` ✓, `(-3,-9,-5)→-3` ✓ |
| **Constructed witness** (independent of both revealed and held-out) | `(100,3,47)→100` ✓, `(-1,-50,-2)→-1` ✓ |
| **Converted** | **YES** |

**The tie is itself the interesting result, and it is exactly what the
brief anticipated ("selects S₃, *or a subgroup that suffices*").**
`sym_2cycle_a_b` (swapping the two args the trap `Max(a,b)` ALREADY treats
symmetrically) scores gap=0 — it adds no information, because the trap is
already symmetric in exactly those two arguments. `sym_full_S3` and both
2-cycles that involve `c` (the argument the trap ignores) score gap=1 —
each individually discriminates the trap from the truth, because `c` is
precisely the ignored argument. **The mechanism is not just numerically
right, it is right for the domain-correct reason**, verified without any
hand-coded knowledge of which argument the trap ignores.

`sym_full_S3` was among the non-refuted, gap-scored, held-out-verified
candidates the whole time (`correct_relaxation_names` in the artifact) — it
lost the tie-break only to alphabetical ordering against an equally-valid
2-cycle, not to a worse relaxation. `br_10`'s own `intent_evidence.arity_gap
== 1` (the accepted trap reads 2 of 3 declared params) — the cheap signal
agrees with the expensive one here (§6).

Gate: `tests/test_arc5_widest_gap_migrated.py::test_live_br10_selects_a_permutation_relaxation_and_converts`
re-derives this exact result live, independent of the frozen artifact.

---

## 2. Generalisation: REOPENED_12 and the 36 honest residual

**Applicability gate** (stated up front, not hidden): this grammar only
attempts arity-2/3, all-integer tasks — a narrow, DOCUMENTED scope (no
`Div`/comparisons/`IfThenElse` in the op inventory, and no str/list/bool
handling). Of 12 REOPENED_12 + 36 residual = 48 non-br_10 tasks, **9 are
applicable**: 5 of REOPENED_12 (`14, 103, 126, 430, 432`) and 3 of the 36
(`291, 292, 452`). The other 39 are excluded with a reason
(`arity_not_2_or_3`: 30; `non_integer_output`: 3; `non_integer_input`: 6 —
full list in `results/arc5_widest_gap.json`'s
`{reopened_12,residual_36}.summary.inapplicable_ids_and_reasons`).

| population | applicable | selected (gap>0) | **converted** | **false selection** | refutation rate |
|---|---|---|---|---|---|
| REOPENED_12 | 5 (`14,103,126,430,432`) | **0** | **0** | 0 | 0/21 (0%) |
| residual_36 | 3 (`291,292,452`) | 1 (`292`) | **0** | **1 (`292`)** | 0/9 (0%) |

**Zero conversions outside br_10.** This is a plain null, reported per the
brief's own instruction, not spun: *the widest-gap criterion, as built here,
does not generalise past the headline task in this run.* This is consistent
with (not contradicted by) `PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md`'s
independent, earlier finding that argument symmetry was applicable to only
3/76 traps — symmetry-shaped defects are genuinely rare in this task
population, and this measurement's own 5/12 + 3/36 applicability count
(mostly gated OUT by arity/type, not by refutation) corroborates it a second
way.

**The one false selection (`292`, "quotient of two numbers, rounded down")
is explained, not mysterious.** Its accepted trap is division-shaped; this
measurement's op inventory has NO `Div` at all (a documented scope choice,
§0). 1,271 candidates in the tiny grammar happened to match its sparse
revealed rows by numeric coincidence (`Minus`/`Times` combinations
approximating a quotient over 2 short rows), one relaxation (`sym_2cycle`)
scored gap=10 against that coincidental pool, and the selected
representative fails held-out (`false_selection=True`,
`held_out_verify.all_ok=False`). This is an honest ENGINE/GRAMMAR
limitation compounding with the criterion, not the widest-gap mechanism
failing on its own terms — but it is exactly the kind of case a real
deployment must guard against, which is precisely why §5's reframe matters:
**gap alone said nothing about whether a matching candidate was even
plausible; a weight that penalises "the true operation this task's prompt
implies isn't even in my inventory" would have suppressed this selection.**

**Tasks 291 and 452 correctly select nothing** (`selected_relaxation: None`)
— no relaxation scored a positive gap for either, and none was wrongly
forced. This is the criterion behaving conservatively where it lacks
information, which is the right failure mode.

---

## 3. Conversion id list and witness verification

**Converted (held-out AND witness-verified):** `["br_10_top_of_three"]` — 1
of 1 candidate conversion attempted with a hand-constructed witness,
verified.

**No coincidental fits.** Per the arc-4 precedent (`la_06_product_all` /
MBPP-394, both of which passed their single held-out row while being
verifiably wrong), every held-out check in this run is scored by
`verify_against_held_out`, a MEASUREMENT-ONLY function that never feeds its
result back into search (isolation-audited,
`tests/test_arc5_widest_gap_migrated.py::test_verify_against_held_out_is_the_sole_sanctioned_reader`).
br_10's ONE conversion is checked against BOTH the fixture's own two
held-out rows AND two constructed witness rows drawn from neither set
(`(100,3,47)→100`, `(-1,-50,-2)→-1`) — both pass. No second coincidental fit
was found because there was no second conversion to check.

---

## 4. The false-selection rate

**1/1 (100%) among tasks where gap SELECTED something outside the
headline; 1/2 (50%) among ALL tasks where gap selected anything at all**
(`br_10` selected correctly, `292` selected wrongly). Named with its id:
`292`. Root cause traced in §2 (a grammar gap, not merely a mis-ranked
relaxation — no relaxation in the catalogue was EVER going to be right for
a division-shaped task under a `Div`-free op inventory).

**The refutation half was never live-tested in this run — an honest gap in
the soundness evidence, not a soundness claim.** Across all 35 relaxation
instances considered live (5 for `br_10` + 21 across REOPENED_12's 5
applicable tasks + 9 across the 36's 3 applicable tasks — instance counts
per task vary with arity, since a 3-arg task has 3 `sym_2cycle` pairs and a
2-arg task has only 1), **zero were refuted by real revealed-row data.**
This is NOT evidence the refutation check is weak — MBPP's PRIMARY protocol
reveals only `n−1` rows (1–2 rows for most tasks here), which is usually too
sparse to contain a genuine permutation-pair or idempotence contradiction —
but it does mean the soundness mechanism's real-data behaviour is UNTESTED
here. It is verified correct only by construction
(`test_live_refuted_permutation_is_never_applied`, a hand-built fixture with
two revealed rows that ARE a permutation pair with different outputs). A
future measurement with denser revealed-row protocols (`official`, which
reveals every row) would be needed to see refutation fire on real data.

---

## 5. REFRAME 1 — gap as ONE weight, not the decider

**Verdict question, corrected:** not "does gap replace the lexicon" but
*"how good a weight is gap alone, and where does it fail?"*

**Gap-score's own accuracy** (`selected_relaxation is not None` as a
predictor, `any_correct_available` as ground truth, over the 9-task
applicable population):

| | value |
|---|---|
| Selections made | 2 (`br_10`, `292`) |
| Correct (`gap_argmax_correct`) | 1 (`br_10`) |
| Wrong | 1 (`292`) |
| **Gap selection accuracy** | **50%** (1/2) |
| Oracle ceiling (any correct relaxation available, whether selected or not) | 1/9 (`br_10` only — no case where gap picked wrong AND a correct alternative was sitting unselected in the catalogue) |

**Characterising the one wrong case, per the reframe's ask (§2):** `292`'s
failure is not "gap ranked the wrong relaxation among several plausible
ones" — `wrong_selection_characterization` is EMPTY (no task has both a
wrong selection AND a correct alternative available), because the catalogue
never contained a correct relaxation for `292` in the first place (its true
defect is division-shaped, outside this grammar entirely). **There is no
case in this run where a DIFFERENT weight would need to outvote gap among
competing correct-vs-incorrect relaxations — every miss here is a coverage
miss (the true fix isn't expressible), not a ranking miss.** This is an
important, specific finding: it means the feature-vector recording below
(§5.1) is honest infrastructure for a FUTURE weighted collapse, but this
run's own population is too small and too coverage-limited to show that
collapse earning its keep yet.

**Which reading applies (per the reframe's explicit menu):** *"gap does not
select correctly"* would be the informative-failure reading; *"gap carries
no signal at all"* would be the true null. **Measured: gap carries REAL
signal (50% precision against a ~11% base rate, 100% recall on the one true
positive) but is untested at any scale beyond n=2 selections** — squarely
the informative, "weak-but-real, needs company" reading, not the true null.

### 5.1 Per-candidate feature vector (for a later weighted collapse — recorded, not combined)

Every gap-scored relaxation entry in `results/arc5_widest_gap.json` carries,
alongside `gap`/`v0`/`v1`:

| feature | meaning | source |
|---|---|---|
| `refuted` | discarded before scoring | revealed rows alone |
| `mdl_bits` | `log2(group_order)` for permutation subgroups (2 for any 2-cycle, `log2(n!)` for full `S_n`); a fixed `1.0` placeholder for idempotence (no group-order analogue) | the conjecture's own structure |
| `n_supporting_revealed_rows` | revealed-row pairs/rows ALREADY consistent with the conjecture (evidence present before any augmentation) | revealed rows alone |
| `plausibility_signal` | permutation: do the swapped positions' observed value ranges actually overlap; idempotence: is there ≥1 supporting all-equal row | revealed rows alone |
| `held_out_check` | measurement-only, retrospective, NEVER used for selection | held-out (sanctioned exception) |

No combiner is built or tuned here — this is exactly the "record the
feature vector, don't fit weights" scope the reframe asked for. `br_10`'s
own winning relaxation: `mdl_bits=1.0` (a 2-cycle, cheaper than
`sym_full_S3`'s `mdl_bits≈2.58`), `n_supporting_revealed_rows=0`,
`plausibility_signal=True`. A future weighted collapse could, e.g., use
`mdl_bits` as an Occam PRIOR that would have preferred the 2-cycle over full
`S_3` even without the alphabetical tie-break — untested here, recorded for
that purpose.

---

## 6. REFRAME 2 — intent evidence (`arity_gap`) vs gap-score, head-to-head

**The features, computed mechanically, no lexicon, no held-out data:**
`declared_arity` (signature arg count), `used_arity` (params actually READ
by the accepted program's IR, via D3's own `collect_var_refs`, reused
verbatim), `arity_gap = declared − used`, `name_arity_hint` (a numeral word
in the function name or prompt — explicitly a LIGHT LEXICAL read, not an
NLU claim), `name_arity_agrees`.

**Head-to-head, same population (n=9 applicable tasks, ground truth =
`any_correct_available`):**

| predictor | TP | FP | FN | precision | recall |
|---|---|---|---|---|---|
| `arity_gap > 0` | `br_10` | `14, 103, 126, 430, 432` | — | **16.7%** | **100%** |
| gap-score selects something | `br_10` | `292` | — | **50%** | **100%** |

**Raw numbers say gap-score wins on precision. That reading is confounded,
and the confound is load-bearing, not a footnote.** Every one of
`arity_gap`'s five "false positives" has `n_matched_revealed_only == 0` —
gap-score's own version-space search found ZERO candidates at all for these
five tasks (verified live,
`test_arity_gap_false_positives_are_v0_empty_not_engine_noise`), so
gap-score was NEVER capable of predicting positive on them regardless of
its quality as a signal — it is silent by construction, not by correctly
judging them non-traps. Cross-checked against this project's own,
already-frozen D3 (`unread_declared_param`) detector
(`results/arc4_structural_verdicts.json`, read-only): **4 of 5
(`14, 126, 430, 432`) are INDEPENDENTLY CONFIRMED genuine structural
defects** — D3 fired on them using its own, stricter bar (the unread
parameter must also VARY across revealed rows). Task `103`'s unread
parameter does NOT vary across its 1–2 sparse revealed rows, so D3 declines
to fire there — the one case where `arity_gap`'s simpler, unconditional
check is arguably too loose, and D3's extra guard is doing real work.

**Correct reading: `arity_gap` is the sharper, cheaper, higher-coverage
signal — it catches real defects gap-score's own engine never had a chance
to attempt — but it is not directly comparable to gap-score on RAW
precision, because they were evaluated on different effective populations
(gap-score's effective population is a strict subset: only tasks where its
own tiny grammar found ANY match at all).** `arity_gap` is NOT "strictly
stronger" in the sense of beating gap-score on the exact same predictions —
it is stronger in **coverage** (it fires independent of engine/grammar
limits) while gap-score is stronger in **precision-where-it-can-fire-at-all**
(when a match exists, gap's selection is more often right, 1/2 vs the
implied population-wide rate of `arity_gap`). Neither claim was tuned to
win; both are read straight off the confusion matrices and the D3
cross-check.

**This is exactly the case for weighted collapse, made concrete:** a
combiner that used `arity_gap` as a HIGH-RECALL PRE-FILTER ("this
declaration is being violated, something is wrong here") and gap-score (or,
where gap's own grammar is too narrow, a WIDER-op-inventory gap re-run) as
the DISCRIMINATING weight for WHICH fix to apply, would dominate either
signal alone on this data — untested here (no combiner was built, per the
reframe's explicit instruction), but the confusion-matrix evidence directly
motivates it.

---

## 7. The verdict

**Does gap select S₃ (or a subgroup that suffices) for br_10, unaided, with
no hand-built lexicon?** **Yes** — measured live, gate-verified, with a
domain-correct explanation for exactly which subgroups tie and why one
(`sym_2cycle_a_b`) correctly scores zero.

**Does the criterion generalise past br_10?** **No — a plain null, reported
as instructed.** Zero conversions among the 8 other applicable tasks (5
REOPENED_12 + 3 residual-36); one false selection, root-caused to an
engine/grammar coverage gap (no `Div`), not a ranking failure.

**Is gap-alone a criterion that replaces a lexicon?** **The question was
wrong, per the author's own correction, and the corrected answer is:** gap
is a real, narrow, precision-leaning weight (50% precision at ~11% base
rate, 100% recall on n=2 selections — genuinely informative, not zero
signal, but measured at a sample size too small to generalise this exact
number) that is decisive exactly when (a) the relaxation family contains
the true invariant and (b) the op inventory can express the true program at
all — and silent or wrong otherwise. `arity_gap` is a cheaper, higher-recall
COMPANION signal that fires independent of engine/grammar coverage and is
independently corroborated by this project's own D3 detector. **Neither
signal alone is the answer; the per-candidate feature vectors recorded in
§5.1 and §6 are the concrete, reusable input a future weighted-collapse
selection (Γ production weights, selection ∝ exp(w)) would need — building
and fitting that combiner is explicitly OUT of scope here, per the
reframe's own instruction not to tune anything.**

---

## 8. Discipline notes

- **Revealed rows only** for every SEARCH-side function
  (`const_pool_for`, `generate_candidates`, `task_applicability`,
  `wide_probe_points`, `relax_permutation`, `relax_idempotent`,
  `check_monotonicity`, `matched_pool`, `count_distinct`,
  `gap_for_relaxation`, `name_arity_hint`, `intent_evidence`) — mechanically
  audited, no function's source contains the literal substring `held_out`
  (`_held_out_isolation_audit`, re-verified live and against the frozen
  artifact by `tests/test_arc5_widest_gap_migrated.py`). Exactly one
  function (`verify_against_held_out`) reads held-out data, for
  MEASUREMENT ONLY, and the selection logic itself (`eligible`/its sort
  key) is source-audited to never mention it.
- **Twin-run determinism.** `scripts/arc5_widest_gap_probe.py` computes the
  full result twice per invocation and asserts a SHA-256 match (excluding
  the two live-clock fields) before writing the artifact; the test suite
  reproduces this independently AND checks it against the frozen artifact's
  own recorded hash.
- **IDs never hand-typed twice differently.** `REOPENED_12` is quoted
  verbatim from `scripts/arc5_shape_constraint_probe.py`'s own citation of
  `tests/test_reject_informs_repair_migrated.py`; the 36 is read live from
  `results/arc4_structural_verdicts.json`; the D3 cross-check reads the
  SAME frozen artifact's own `per_task` detector verdicts, never
  re-derived.
- **A baseline is a list, never a count.** Every population above is an id
  list in the artifact (`applicable_ids`, `converted_ids`,
  `false_selection_ids`, `tp_ids`/`fp_ids`/`fn_ids`), gated by the test
  suite re-deriving them, never a bare percentage standing alone.
- **Frozen artifacts stay frozen.** `results/mbpp_arc3_endgame.json`,
  `results/arc4_structural_verdicts.json`,
  `tests/fixtures/prog_synthesis_battery/tasks.json` are read-only
  citations throughout; nothing in this phase re-runs FULL-R3 or the S6/D1–D7
  batteries.

---

## 9. Files

`scripts/arc5_widest_gap_probe.py` (driver — grammar/enumeration,
refutation-first relaxation family, wide-probe gap computation,
intent-evidence features, held-out isolation audit, twin-run determinism;
reads the frozen artifacts above plus the MBPP test fixture and the
`br_10` battery fixture; touches no synthesis/engine/seed/spec code).

`results/arc5_widest_gap.json` (the artifact — per-task rows for `br_10` +
REOPENED_12 + the 36 honest residual, each with `applicability`,
`intent_evidence`, per-relaxation refutation/gap/feature-vector/held-out-check
detail, selection/conversion/false-selection verdicts; population summaries;
the intent-vs-gap head-to-head with its D3 cross-check; determinism;
environment).

`tests/test_arc5_widest_gap_migrated.py` (18 passed, ~11s: schema; held-out
isolation (mechanical audit + sole-sanctioned-reader + selection-source
audit); 3 pinned live re-verifications — br_10's own selection/conversion,
a constructed-fixture refutation, and the wide-probe distinctness mechanism
directly; determinism; selection-vs-verification discipline;
intent-vs-gap arithmetic and the V0-empty confound characterisation).

This file.
