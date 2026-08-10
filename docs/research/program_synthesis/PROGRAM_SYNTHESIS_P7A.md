# PROGRAM SYNTHESIS P7 — track A: RECURSIVE ShapeDecode descent (results)

**Date:** 2026-07-31. Prereg: `PROGRAM_SYNTHESIS_P7_PREREG.md` (H7a; written
first). Deliverables: `seeds/program_synthesis.json` **v1.2.0** (27 → 38
rules), `domains/prog_synthesis.py` (4 new mechanical descent verbs),
`tests/test_prog_descent_migrated.py` (15 gates, green, <1 s),
`tests/test_program_synthesis_migrated.py` (+1 additive guard test; the
seed-manifest rule-count pin follows the version bump, the P6.5 precedent).

**The governing insight, landed:** *"shapedecode will tell you what is going
on."* The decode's coverage assignment IS the plan. A partial rung-1 cover is
not failure — it is segmentation-by-recognition (the ink `_lattice_partition`
precedent at spec grain): covered spans instantiate their construction
templates as a SKELETON, each uncovered span becomes a HOLE sub-goal one
grain finer, only a residual that survives every grain reaches the
enumerator, and there is an execution verdict at every level.

## 1. The descent rung as landed (rules decide; the adapter is mechanical)

Occam position: **between the codebook/lattice rungs and whole-goal
enumerate.** Scope guard (the whole trick): descent fires ONLY on specs with
a **list-input example row** — exactly the whole-goal `SynthEnumerate`
inadmissibility boundary (its leaves are scalar; a list-input spec can NEVER
be solved at whole-goal grain). So descent targets precisely the recoverable
mass, and **every scalar-row path in the tree is byte-unchanged by guard,
not by luck** (gated).

```
pending (codebook spent: no eligible non-excluded construction)
  ├─ scalar rows / no cover / depth spent → ps_enumerate_mark (UNCHANGED path)
  └─ ps_descend_mark   cover-any (exclusions ignored: plan-level exclusion
     │                 retires a WHOLE-goal plan, not the part as skeleton
     │                 material) + list-row + ps_depth < ps_max_depth
     ▼
  descend_pending → build_descent (adapter): ONE ShapeDecode evaluation
     │             (same binding as ps_propose) recorded as goal FACTS:
     │             ps_cover_parts / ps_cover_first / ps_cover_count /
     │             ps_residual_tokens — boundaries ARE the decode assignment
     ▼
  plan ladder (rules, tried-once-per-kind, integer ps_plan_seq):
     ├─ ps_plan_fold_step   cover == 1 fold template (tmpl_fold, stamped
     │                      mechanically at ensure time) → Hole{fold_step}
     └─ ps_plan_final_expr  fold_step inapplicable-or-tried → Hole{final_expr}
     ▼
  hole_derive → derive_hole_rows (adapter): derived (inputs, expected) rows
     │          where the skeleton makes them DETERMINABLE (§2); counts
     │          recorded; ps_hole_derived / ps_hole_underivable JUDGE
     ▼
  hole_spawn → spawn_subgoal (adapter): Message{tokens = the decode
     │         RESIDUAL} + derived ExampleRows → ps_goal mints the sub-Goal
     │         → THE SAME LADDER runs one grain finer (ps_depth+1, its own
     │         integer ps_attempts/ps_budget — collision-free from the
     │         start, the P6.5 lesson) → hole-scoped enumeration: small
     │         holes, big reach
     ▼
  hole_wait → ps_hole_solved (sub accepted) / ps_hole_failed (sub gapped)
     ▼
  foldup_pending → fold_up (adapter): splice the accepted sub-IR into the
     │            skeleton (structural substitution), reflect (round-trip
     │            fact), ProgEval the FULL outer rows into the
     │            descent-scoped fu_* row lane (NEVER eval_attempt/
     │            verdict_attempt — the P6.5 collision cannot re-arm)
     ▼
  ps_foldup_accept → verified → ps_accept (the standard mint)
  ps_foldup_reject → descend_pending (next plan)
  ps_descend_exhausted → pending + ps_descend_done → whole-goal enumerate
                         → gap (a residual that survives every grain
                         reaches the enumerator; honest fall-through)
```

New rules (11): `ps_descend_mark`, `ps_plan_fold_step`, `ps_plan_final_expr`,
`ps_descend_exhausted`, `ps_hole_derived`, `ps_hole_underivable`,
`ps_hole_wait`, `ps_hole_solved`, `ps_hole_failed`, `ps_foldup_accept`,
`ps_foldup_reject`. Edited (3): `ps_goal` (Goal carries `ps_depth` from the
Message + integer `ps_max_depth` 2), `ps_enumerate_mark` (waits for
`ps_descend_done` where descent is applicable; identically-true guard
elsewhere), `ps_gap_file` (descent sub-goals, `ps_depth ≥ 1`, never file
SelfConcerns — a hole's gap is descent-internal; the outer goal files its
own; no-depth legacy goals still file). New productions: `Goal -has_hole→
Hole`, `Hole -sub_message→ Message`. Adapter verbs (4, all facts-in/
facts-out): `build_descent`, `derive_hole_rows`, `spawn_subgoal`, `fold_up`.

## 2. Hole taxonomy + derivability scopes (honest, as prereg'd)

| hole kind | skeleton | derived sub-rows | scope boundary |
|---|---|---|---|
| **fold_step** | the covered Fold template with its body holed: h(acc, x) | one-iteration unroll: a SINGLETON-list outer row pins acc_before = init (a literal, evaluated), item = the element, acc_after = the outer output — no inversion, no arithmetic | multi-item rows are counted `non_determinable`, never guessed; no singleton rows → hole refused |
| **final_expr** | live vars: `v_i := covered construction template_i(row inputs)` (prefix evaluation per row), hole = the final expression over v_i + scalar inputs | ALWAYS derivable modulo traps: (v_1..v_k, scalars) → outer expected, one per outer row | trapping / non-scalar parts skip the row (counted); stmts-mode covers skipped (named blocker) |
| **branch_arm** | — | — | **NAMED BLOCKER this rung** (prereg'd: zero corpus mass in the battery's gapped set); taxonomy vocabulary reserved |

## 3. The cited-task before/after (gate 1, exact and deterministic)

All three frozen `gapped:enumerate_failed` in MAIN and MAIN-POSTFIX; all
three now accept with held-out rows correct; whole-goal enumerate NEVER ran
(`rungs.enumerate is None`):

| task (frozen: gapped) | cover (decode) | descent solve | held-out |
|---|---|---|---|
| `la_20_double_each_total` | `total_of_list` | fold_step tried first: sub accepted `Lit 10` on the 1 derived row, **fold-up REFUSED it on [1,2,3]** (execution verdict at the outer level) → final_expr: v1 = total, hole-enumerate found `(v1 + v1)` → folded, verified | 24, 0 ✓ |
| `ms_09_count_then_double` | `count_of_list` | final_expr: v1 = count, `(v1 + v1)` | 8, 2 ✓ |
| `ms_04_avg_by_parts` | `total_of_list`, `count_of_list` (TWO covered spans) | final_expr: v1 = total, v2 = count, `(v1 / v2)` — the decode's multi-part cover composed | 5.0, 3.0 ✓ |

la_20's fold_step derived row is pinned by gate 2 against hand-computed
truth: exactly `{acc: 0, x: 5} → 10`, with `non_determinable=2` (the `[]`
and `[1,2,3]` rows) — counted, never guessed.

## 4. Diagnostic full sweep (informal — track D owns re-measurement)

One pass of the 125 tasks through `run_task` at this commit, compared
row-by-row to frozen MAIN-POSTFIX (no artifact writes):

- **Changed rows: 7, ALL previously `gapped:enumerate_failed`** — the
  paired identity holds exactly (no currently-passing row flipped; the
  changed-row set is an identity list, not a count):
  - → `accepted_holdout_ok` (3): `la_20_double_each_total`,
    `ms_04_avg_by_parts`, `ms_09_count_then_double` (the cited set,
    nothing else);
  - → `accepted_holdout_fail` (4): `la_10_count_positives`,
    `la_11_count_evens`, `la_21_count_zeros`, `la_29_count_above_ten` —
    weak derived rows (one singleton per task) let the hole overfit a
    len-only expression; the HELD-OUT rows caught every one (the §2.2
    class at descent grain, terminal-honest, prereg'd as a non-success
    taxonomy shift).
- Taxonomy: accepted_holdout_ok 77 → 80, accepted_holdout_fail 15 → 19,
  gapped 30 → 23, not_recognized 3 → 3, **stalled/parked 0** (every row
  terminal).
- **H7a primary reading: the registered NULL largely holds for the
  stratum.** loop_accumulation 7/30 → 8/30 (.267) — nowhere near the
  CI-separation bar (>.409). The stratum's remaining mass is (i)
  trigger-grain mismatch (SUM covers `sum_of_two`, an a/b expression, not
  a fold — `la_09_sum_squares_list`, `la_28_alternating_sum` cannot build
  a fold skeleton), (ii) no cover at all (`la_07/08/13/14/22/25/26`), and
  (iii) scalar-loop tasks (out of descent's prereg'd scope). The
  mechanism gate (≥2 cited conversions) is met at 3/3; multi_statement
  moved 6/10 → 8/10. Both readings reported, neither substitutes for the
  other.

## 5. Gates (all green at this commit)

`tests/test_prog_descent_migrated.py` — **15 passed, ~0.5 s**:
headline ×3 (frozen-row cross-checked, held-out via the reflected
`ir_subgraph` root, rung provenance) + the recursion-is-literal gate (the
folded hole's sub-goal is a `Goal{kind:synth_program}` at `ps_depth` 1 with
its own counters and `ps_rung_enumerate` 1); derived-row truth pinned;
boundaries-from-decode (goal facts ≡ an independent ShapeDecode; sub-spec
tokens ≡ the residual); depth budget honest; failed descent falls to
enumerate-then-gap with the frozen terminal and ONE SelfConcern (the
outer's — sub-goals file none); weak-derived-rows terminal; covered and
scalar requests never descend; paired identity ×4.

Neighbors, unchanged behaviour: `test_program_synthesis_migrated.py` **16
passed** (15 P4/P6.5 gates untouched — the only edit is the seed rule-count
pin 27 → 38 following the version bump, the P6.5 precedent — plus 1 additive
descend-guard test); battery gate **11 passed over the UNMODIFIED artifact**
(frozen rows untouched; pinned live-reverify ids reproduce — `ms_10` has
zero decode cover, measured, so descent cannot touch it); selfimprove 5,
baseline 11, prog_ir 54, prog_constructions/read/growth/render 218. Full
boot: `load_all_seeds` failed-list byte-identical to the pre-existing 8
`local_id` items; program_synthesis v1.2.0 loads with zero skipped rules.
The no-Python-decision source audit re-ran green over the modified adapter
(no argmin/argmax, no min/max(key=), no sort-on-score; the new verbs are
prefix-evaluation + record, structural splice, and name-keyed dispatch on
rule-minted kinds).

## 6. Honest residuals

1. **Weak derived rows overfit at the hole (4 new holdout_fails).** With
   one singleton-derived row, hole-enumerate's first MDL fit is often a
   constant/len-only term; fold-up (outer rows) or held-out rows catch it,
   but `SynthEnumerate` is first-fit — there is no candidate iteration at
   the hole. A hole-level CEGIS (exclude-and-re-enumerate, or a
   multi-candidate `SynthEnumerate` contract) is the named next lever;
   corpus mass: exactly the 4 count-variant ids above.
2. **Trigger-grain mismatch blocks the sum-family folds.** "sum of the
   squares" covers `sum_of_two` (scalar a/b), not a fold — descent then
   has no usable skeleton and falls through honestly. The fix is codebook
   content, not descent mechanics — precisely the P7-C chunk-mining seam
   (a mined `sum-of-list` fold shape with a SUM-family trigger would flip
   `la_09`-class tasks into la_20's shape).
3. **branch_arm holes** ship as reserved taxonomy only (prereg'd blocker,
   zero battery mass).
4. **Scalar-loop tasks** (`la_15..la_19, la_30` family) are outside
   descent's scope by design (no list row); they stay on the whole-goal
   enumerate rung.
5. **fold_step's reach is narrow** (exactly-one fold cover + singleton
   rows + literal init). On every gate it was out-raced by final_expr
   after fold-up refusal; it remains the honest home for
   acc-dependent steps the final_expr plan cannot express, and gate 2
   pins its derivation contract.
6. **Descent sub-goals persist their artifacts** (sub-Message/ExampleRows/
   Program named `<outer>__hole_*`) as graph-resident working state;
   read-off is via the OUTER goal's `accepted_program` edge only. Sub-goal
   gaps file no SelfConcern (rule-guarded), so the gap pipeline sees one
   concern per failed REQUEST, as before.
7. **`ps_construction` on a descent accept names the covered construction**
   (the skeleton's material), with `ps_descend_kind` + `rungs.descend` as
   the disambiguating provenance — the P6.5 "read the rung markers"
   convention extended.

## 7. Residual closures (P7-B, 2026-07-31 — appended, nothing above edited)

- **Residual 1 (weak derived rows overfit at the hole; no candidate
  iteration) — CLOSED at repair grain** (`PROGRAM_SYNTHESIS_P7B.md`, seed
  v1.3.0): hole-level CEGIS landed as TRACE-GUIDED LOCAL REPAIR. An
  externally-verified failing row refutes the accept (`ps_repair_mark`),
  the trace localizes the fault to the folded hole against DERIVED
  expectations (the same derivability scopes as §2, reused at trace grain),
  and the counterexample propagates INTO the re-opened hole's derived rows
  — the la-class holes get the second row and stop accepting Lit/len
  first-fits. Of the 4 count-variant ids above: `la_10_count_positives`
  converts to accepted_holdout_ok (post-failure work 1 hole re-solve vs 3
  units under global re-proposal, gated); `la_11/la_21/la_29` are PROVEN
  unreachable at the held grains (live-var collisions measured in-gate;
  parity/const-10 outside the enumerator's op/const reach) and now end on
  the honest `gapped:enumerate_failed` terminal instead of a standing wrong
  accept once a verifier reveals the failure. Exclusion-driven candidate
  iteration is bounded by an integer repair budget; the honest enumerator
  input shifts are the grown row set + non-output Lit const drops
  (`synth_enumerate.rs` re-appends output consts by contract — measured;
  op-drops rejected as unsound). Battery rows are untouched: without an
  ingested counterexample the repair lane is inert (gated).
- Residual 5's narrow fold_step reach gains one measured refinement:
  singleton-derived fold rows can never surface acc-DEPENDENT bodies
  (observational equivalence at acc = init prunes them, not ranks them) —
  recorded as P7-B residual 4; final_expr remains the corpus rescue.
