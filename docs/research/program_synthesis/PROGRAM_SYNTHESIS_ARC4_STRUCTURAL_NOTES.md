# PROGRAM SYNTHESIS ARC 4 — STRUCTURAL KILLABILITY: correcting a framing error

**Date:** 2026-08-01. Corrects a framing error in `PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md`
/ `results/arc4_failure_anatomy.json` (S0-A), which measured the 76
`accepted_holdout_fail` traps' killability using ONLY behavioural signals
(cross-frame execution, executed type/arity checks, metamorphic
re-evaluation) and concluded 23/76 (30.3%) killable, 53/76 (69.7%) an
"honest residual, unkillable by owned signals." That conclusion was true
of the signals it tested, but the brief that produced it was written in
black-box terms. **We are not a black box: the accepted program is a
reflected Term subgraph (the hub IR), and it can be INSPECTED without
executing it on unseen data.** This measurement re-runs the ceiling in
that structural space.

Driver: `scripts/arc4_structural_verdicts.py`. Artifact: `results/
arc4_structural_verdicts.json` (per-task rows for all 76 traps × 7
detectors, a false-positive run over the 21 correct `pass` tasks,
id lists per detector, union/overlap with S0-A's 23, determinism hashes).
Gate: `tests/test_structural_verdicts_migrated.py`, 21 passed.

---

## 0. A population note, recorded honestly before anything else

S0-A's own script LIVE RE-RAN FULL-R3 (`mbpp_arc3_battery.run_arm`)
because at the time it ran, HEAD had not moved since the frozen
`results/mbpp_arc3_endgame.json` citation. Since S0-A landed, **two
build phases changed the live pipeline**: arc4 S1 (budget isolation,
seed v1.6.0) and arc4 S4 (11 new enumerable ops, a genuine Rust change
to `runners/dsl/src/synth_enumerate.rs`). Re-running FULL-R3 live today
measures a DIFFERENT population — 104 `accepted_holdout_fail` / 30
`pass`, not 76/21 — because S1/S4 changed what the enumerator/screen
accept (confirmed live, one measurement, not used further).

Re-running live now would silently swap S0-A's own named 76 trap ids for
an uncited, different set — the exact "quoted without its condition"
failure this repo's `CLAUDE.md` already retracted once for a different
number. Instead: `results/mbpp_arc3_endgame.json` (frozen, cited,
read-only) already carries the exact `"ir"` Term-JSON for every one of
the 76 trap + 21 correct rows, and `domains/mbpp_spec.py` — confirmed
UNCHANGED across the S0A-to-HEAD commit range — recomputes byte-identical
revealed rows from the untouched fixture. **This measurement reads the
frozen artifact directly rather than re-running**, reproducing the EXACT
76/21 population S0-A measured (id-list-verified against `results/
arc4_failure_anatomy.json`'s own `ahf_task_ids`, not just counted).

---

## 1. The seven structural detectors

Every detector reads only the accepted program's IR (`Term-JSON`, the
same hub-IR shape `PROGRAM_SYNTHESIS_P1_NOTES.md` documents) and the
task's REVEALED rows (never held-out — isolation proof in §4). None
execute the program on unseen input, except D7, scoped to a provably
closed domain.

| id | definition |
|---|---|
| **D1 memo_lookup_table** | The function collapses to EXACTLY ONE `ProgReturn`, whose value expression is built entirely from `Lit` leaves combined by `IfThenElse` nodes gated by an "equality-like literal test" (`Eq`/`Minus`/`Not`, containing both a `Lit` and a `Var` — excludes order predicates `Gt`/`Lt`/`Gte`/`Lte`, the hallmark of generalising logic, not memorisation), AND the reachable literal leaves EXACTLY equal the revealed rows' expected-value SET. Task 267's known shape: `return (35 if (a - 2) else 10)`. |
| **D2 dead_code_free_vars** | A `Var` reference to a name never bound ANYWHERE in the whole program (param / assignment / augmented-assignment / tuple-unpack target / for-loop var / except-var / comprehension var) — a whole-program, scope-blind but conservative set (can only UNDER-report freeness). |
| **D3 unread_declared_param** | A declared parameter with zero `Var` references anywhere in the body, proven a genuine defect (not a harmless unused arg) by checking the revealed rows actually VARY that parameter's value. |
| **D4 constant_output** | The whole-program specialisation of D3: ALL declared params unread, while revealed rows show ≥2 distinct expected outputs. |
| **D5 vacuous_guard** | An `IfThenElse`/`ProgIfStmt` condition containing NO `Var` reference anywhere in its own subtree — a condition that could be constant-folded without knowing any input, so one branch is unreachable by construction. Scoped to branching only (not `ProgWhile`, where an input-independent condition is often the idiomatic `while True: ... break`). |
| **D6 arity_mismatch** | IR param COUNT vs revealed-row argument COUNT — PURELY STRUCTURAL, unlike S0-A's `type_arity_check`, which folds arity into an EXECUTED check. Never calls `prog_eval`. |
| **D7 exhaustive_domain_proof** | Eligible only when every declared param is a Python `bool` on every revealed row — a domain that is PROVABLY closed and complete ({True,False}^arity, bound documented at ≤10,000 tuples), never an inferred bound from an observed-but-unbounded numeric/str/list range (that would not be a proof). When eligible, the accepted program IS executed (native `ProgEval`, never a held-out value) over the WHOLE domain, checking trap-freedom and internal determinism — reference-free properties, no oracle beyond what this codebase already owns. |

---

## 2. Recall / false-positive / precision, measured against BOTH populations

Recall is measured over the 76 traps; false positives are measured by
running the IDENTICAL detector code over the 21 `pass` (accepted AND
holdout-correct) rows from the same frozen artifact — the population a
detector must never fire on.

| detector | recall (n/76) | FP on 21 correct | precision (TP/(TP+FP)) |
|---|---|---|---|
| D1 memo_lookup_table | 14 (18.4%) | 0/21 (0%) | 1.00 |
| D2 dead_code_free_vars | 5 (6.6%) | 0/21 (0%) | 1.00 |
| D3 unread_declared_param | 22 (28.9%) | 3/21 (14.3%) | 0.88 |
| D4 constant_output | 0 | 0/21 | n/a |
| D5 vacuous_guard | 0 | 0/21 | n/a |
| D6 arity_mismatch | 0 | 0/21 | n/a |
| D7 exhaustive_domain_proof | 0 (0 eligible) | 0 (0 eligible) | n/a |
| **union (any of D1–D7)** | **34/76 (44.7%)** | **3/21 (14.3%)** | — |

### 2.1 A false positive the detector caught DURING DEVELOPMENT, fixed before this artifact was final

D1's first version checked only "is this ONE return statement's own
value a literal-dispatch tree" without also requiring the function to
have exactly one `ProgReturn`. That version fired on tasks 20
("woodball number") and 281 ("unique list elements") — both correct,
`pass`-labelled programs whose shape is the extremely common
`for x in xs: if bad(x): return False` \ `return True` early-exit
idiom. Each individual `return True`/`return False` statement is
trivially "a bare `Lit`", satisfying the base case of literal-dispatch
with zero memorisation involved — the DECISION lives in the loop
condition, not in a closed dispatch expression. Requiring the whole
function to collapse to exactly one `ProgReturn` before checking the
literal-dispatch shape is what actually distinguishes "the whole
decision is a closed table" from "a loop reaches one of several
bare-literal exits", and it also correctly demotes task 113 (the same
shape, but genuinely wrong for an unrelated reason) out of D1's true
positives. **This is exactly the false-positive discipline the brief
asked for: a detector that flagged correct programs was found, measured,
and fixed before being reported, not smoothed over.**

### 2.2 D3's three remaining false positives are LABEL NOISE, not detector error — hand-verified

Tasks 397, 404, 433 are labelled `pass` yet D3 correctly finds they
structurally ignore a declared, revealed-varying parameter:

- **397** ("median of three numbers"): `return max(a, b)` — `c` is never
  read. Both revealed rows happen to have `max(a, b)` coincide with the
  true median (`a`/`b` happened to bracket the median both times).
  Witness `(a=1, b=5, c=3)` (self-constructed, NOT the held-out row):
  program returns `5`, true median is `3` — genuinely wrong.
- **404** ("minimum of two numbers"): `return a`, `b` never read. Both
  revealed rows happen to have `a <= b`. Witness `(a=5, b=1)`: program
  returns `5`, true minimum is `1` — genuinely wrong.
- **433** ("greater than elements of array"): `return b > 4`, the array
  `a` never read at all — a fixed-threshold check standing in for an
  array comparison. Witness `(b=3, a=[1, 2])`: program returns `False`,
  but `3` IS greater than every element of `[1, 2]` — genuinely wrong.

All three are re-verified live by
`tests/test_structural_verdicts_migrated.py::test_d3_false_positives_are_genuine_defects_on_a_fresh_witness`
using ONLY a hand-constructed witness input (never a task's held-out
row) evaluated through the same native `ProgEval` this artifact already
uses elsewhere. **The `pass` label itself is not a perfectly clean
correctness oracle under MBPP's PRIMARY protocol** (one held-out row is
not enough to catch a program that ignores a whole argument, if that
argument happens to be irrelevant on the one row tested) — D3 is more
likely correct than the label for these three cases. This does not
change how the false-positive rate is COMPUTED or REPORTED above (a
detector cannot know which `pass` labels are themselves wrong without
touching held-out data, so it is scored against the label as given,
mechanically) — but it means D3's TRUE precision against genuine
correctness is very likely higher than the measured 0.88.

---

## 3. The corrected ceiling

| | n/76 | % |
|---|---|---|
| S0-A behavioural-only (cited, unchanged) | 23 | 30.3% |
| **Structural-only (this measurement)** | **34** | **44.7%** |
| Overlap (caught by both) | 17 | 22.4% |
| Structural-only NEW catches (not in S0-A's 23) | 17 | 22.4% |
| **Union (structural OR behavioural) — the corrected ceiling** | **40** | **52.6%** |
| **Corrected honest residual** | **36** | **47.4%** |

The honest residual shrinks from **53/76 (69.7%)** to **36/76 (47.4%)**
once structural inspection is added as a second, independent signal
family. 17 of the 76 traps are structural-AND-behavioural (e.g. task
267 fires both S0-A's python cross-check AND D1/D2 here — the same
defect, two independent instruments agreeing); 17 more are catchable
ONLY by looking at the program (D1/D3 finding lookup tables and
ignored inputs that render/execute perfectly consistently and pass
every behavioural check S0-A ran); 6 remain catchable ONLY
behaviourally (61, 62, 100, 129, 407, 461 — genuine numeric/logic
errors in programs with no structural red flag: no dead code, every
declared input read, no vacuous guard, correct arity — S0-A's
cross-frame/type checks are the ONLY instrument that reaches these,
because the defect is in what the arithmetic COMPUTES, not in the
program's shape).

Overlap and union ids (task_ids), full lists in the artifact:
`overlap_structural_and_behavioral_ids` (17), `structural_only_ids`
(17), `behavioral_only_ids` (6), `new_honest_residual_ids` (36).

---

## 4. Held-out isolation — proof, not assertion

Every structural-detector function (`collect_var_refs`,
`collect_bound_names`, `collect_returns`, `is_equality_like_literal_test`,
`literal_dispatch`, `detect_memo_lookup_table`,
`detect_dead_code_free_vars`, `detect_unread_declared_param`,
`detect_constant_output`, `detect_vacuous_guard`,
`detect_arity_mismatch`, `detect_exhaustive_domain_eligible`,
`run_exhaustive_domain`, `analyze_task`) takes only `ir` and
`revealed_rows` (or neither) — the literal substring `"held_out"` does
not appear in any of their source (mechanical audit,
`_held_out_isolation_audit`, asserted before the artifact is written and
re-verified live, independently, by
`tests/test_structural_verdicts_migrated.py`). `revealed_rows` is
recomputed via `arc4_failure_anatomy._revealed_rows_for_task` (imported,
not duplicated — the exact same S0-A isolation-audited function). D7's
domain run executes the accepted program only over its own
provably-closed `bool^arity` domain — never a held-out value, and (this
population) never non-empty in practice: see §5.

---

## 5. Exhaustive-domain proof — which tasks qualified

**Zero tasks in this population (76 traps ∪ 21 correct) qualify.** The
documented eligibility bound requires EVERY declared parameter to be a
Python `bool` on every revealed row (a domain that is provably `{True,
False}^arity`, size ≤ 10,000 by construction for any arity ≤ 13 — never
reached here). A distribution check over the population's
`signature_facts` arg types found: `('int',)` 39, `('str',)` 18,
`('int','int')` 13, `('int','int','int')` 6, `('list',)` 5,
`('list','int')` 5, and single-digit counts for a handful of other
shapes — **not one all-bool signature anywhere in the population.**
This is an honest null, not a hidden one: MBPP's task distribution is
dominated by int/str/list arguments, and no weaker (observation-derived,
hence non-proof) domain bound was substituted — widening the bound to
"the observed range of an int argument ± a margin" would not be a
PROOF over that domain, only a stress-test with an invented boundary,
which this measurement declines to conflate with D7's actual claim.

---

## 6. What structural inspection CANNOT establish

- **Agreement with intent.** MBPP's intent is pinned only by prose (the
  task prompt) and a handful of example rows — never a formal spec. A
  structural detector can prove a program ignores a declared input, or
  contains dead code, or dispatches from a closed literal table; it
  cannot prove the program disagrees with what the prompt MEANS, because
  "what the prompt means" is not graph data this pipeline holds. Every
  detector above is scored against REVEALED ROWS (data) and the IR's own
  shape (structure) — never against a semantic reading of the prompt.
  This is why D3/D4's few false positives are genuinely ambiguous
  (§2.2): the detector is right about the STRUCTURE (an input is
  ignored); whether that structure is a "defect" still depends on
  whether the ignored input matters for the TRUE relation, which is a
  semantic fact this measurement does not have direct access to (though
  in all 3 cases here, a hand-constructed witness independently confirms
  it does matter).
- **Rice's theorem, and why it doesn't block this measurement anyway.**
  For an arbitrary Turing-complete language, every non-trivial semantic
  property of programs (halting, output-range membership, equivalence to
  a reference) is UNDECIDABLE in general. This measurement's IR is not
  Turing-complete in the relevant sense for these particular properties:
  `ProgEval` is FUELED (bounded steps, `PROGRAM_SYNTHESIS_P1_NOTES.md`
  §3), and every property D1–D7 checks is a SYNTACTIC/finite-fragment
  property (variable-binding closure, literal-set membership, condition
  var-freedom, parameter count, domain cardinality) decidable by a single
  finite tree walk with NO reference to the program's dynamic behaviour
  on an unbounded input space. D7 is the one detector that DOES execute
  the program, and it sidesteps Rice's theorem the standard way: by
  restricting to a domain SMALL AND CLOSED enough to enumerate
  completely, so "does this property hold everywhere" becomes a finite
  conjunction, not an unbounded quantifier. None of the seven detectors
  claims to decide an undecidable property over the FULL space of
  possible inputs; each is either syntactic-and-total or
  execution-and-finite-domain by construction.
- **The 36/76 (47.4%) residual is not a claim that these traps are
  unfixable** — only that neither this measurement's owned structural
  signals nor S0-A's owned behavioural signals catch them using only
  revealed rows. A stronger signal (more revealed rows, a
  property/verdict discriminator this codebase does not yet own, or
  search reach itself) remains the honest next lever, per
  `PROGRAM_SYNTHESIS_ARC4_PLAN.md` §5's own fallback.

---

## 7. Files

`scripts/arc4_structural_verdicts.py` (driver — reads `results/
mbpp_arc3_endgame.json` + `results/arc4_failure_anatomy.json` directly,
imports `mbpp_arc3_battery`/`arc4_failure_anatomy` verbatim, touches no
synthesis/engine/seed code), `results/arc4_structural_verdicts.json`
(the artifact — per-task rows for all 76 traps + 21 correct tasks × 7
detectors, per-detector recall/FP/precision, union/overlap id lists,
determinism hashes, environment), `tests/test_structural_verdicts_
migrated.py` (21 passed, <1s), this file.
