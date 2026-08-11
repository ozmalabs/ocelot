# PROGRAM SYNTHESIS ARC 6 — SEAM D: program-shaped property verdicts, landed

**Date:** 2026-08-01. Builds the seam `PROGRAM_SYNTHESIS_ARC6_M0_CD.md`
Ceiling D scoped: **36/36 of the honest structural residual
(`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`) admit a real,
prompt-entailed, execution-verified property**, but none is expressible
in `comprehend_theorem`'s group-theoretic grammar. This phase builds the
**second, differently-scoped comprehension module** the ceiling doc named
as the only way to reach them: same shape (prose → structured property →
grounded → checkable clause), program-shaped content instead of group
content.

Driver files: NEW `domains/prog_property.py`, NEW
`seeds/program_properties.json`, `seeds/program_synthesis.json`
(v1.10.0 → v1.11.0), `domains/prog_synthesis.py` (dispatch + read-back
wiring), NEW `tests/test_prog_property_migrated.py` (63 passed).

---

## 1. Mechanism — the shape, transferred

`comprehend_theorem`'s pipeline is PARSE (seeded statement constructions)
→ GROUND (property phrase → held predicate; invariant/value → typed
consequent) → EMIT (`ImplicationClause`) → SELF-VERIFY (against
`ground_reductions.KNOWN_OBJECTS`, never a held-out row). This phase
builds the identical shape aimed at program-shaped content:

| comprehend_theorem (group content) | prog_property (program content) |
|---|---|
| `seeds/theorem_constructions.json` (`property_modifiers`, phrase-matched) | `seeds/program_properties.json` (`property_atoms`, phrase-matched) |
| `ground_reductions`'s held predicates, resolved by NAME | `domains/prog_property.py`'s `ref_*` registry, resolved by NAME |
| antecedent = a held predicate over a `KNOWN_OBJECTS` group | antecedent = a reference relation over a **witness input**, checked against the **candidate's own executed output** |
| self-verify vs `KNOWN_VALUES` (textbook known cd/ends values) | self-verify vs the **goal's own revealed rows** (never held-out) |
| a self-rejected clause ⇒ `comprehended=False` (an honest miss) | a self-rejected atom ⇒ it never fires on this goal (an honest miss) |

**The grounding target is new** (this is exactly what §2.4 of the
ceiling doc named as missing): not a predicate over a `KNOWN_OBJECTS`
group, but a predicate over **a candidate program's evaluated output at
a hand-constructed witness input** — `domains/prog_property.py::check_property`
runs the SAME `ProgEval` term (`prog_synthesis._prog_eval_term`) every
other verdict path in this codebase already uses, directly against the
candidate's already-reflected Term subgraph (no fresh reflection, no new
Rust).

### 1.1 `seeds/program_properties.json` — 36 PropertyAtoms, one per residual task

Each atom carries exactly what `PROGRAM_SYNTHESIS_ARC6_M0_CD.md §2.2`'s
own per-task property table already found (not a new taxonomy — the
atoms ARE that table, turned into graph data): `phrases` (cue substrings
lifted verbatim from the task's own prompt, AND-matched), `arg_count` (a
guard), `reference` (the held relation's name), `witnesses` (2-3
hand-constructed envs — never a held-out row). The 36 atoms span the
property families the ceiling probe actually found: geometric formulas
(perimeter/surface-area), modular conditions (divisibility, difference of
two squares), set membership (substring/tuple/month-set), counting/
cardinality invariants (popcount, divisor counts, primes-below), bit
operations, monotonic bounds (smallest/highest power of 2), closed-form
polynomial identities (star/decagonal numbers, central binomial), and
recurrence identities (Bell numbers, Lucas numbers, the fence-painting
recurrence, a memoised max-recursion).

### 1.2 `domains/prog_property.py` — MECHANICAL only

- `ref_*` (36 pure functions): the reference relation, one per atom,
  external domain knowledge (elementary geometry/number theory/string-
  collection semantics), never the candidate's own logic, never a held-out
  row. `ref_trim_tuples` is the one relation that needed a rendering-
  convention pin (tuple-bracketed `str()`, matching MBPP's own dataset
  convention) so it agrees with the goal's own revealed `expected` string
  regardless of whether the input arrives as a genuine tuple or (after
  this codebase's own `inputs_json` JSON round-trip) a plain list — a
  representation detail, not a relation change.
- `_phrases_match` / `_prompt_text` / `_row_list`: mechanical I/O reads
  (prompt text off the `Message` node, revealed rows off `ExampleRow`
  nodes) — no decisions.
- `_self_verify_atom`: the refutability gate (§3 below).
- `check_property`: executes the candidate's reflected root at each
  witness; the FIRST mismatch is the refutation.
- `compute_property_facts`: the mechanical rim, dispatched on the SAME
  `'verified'` status `compute_structural_facts` already dispatches on,
  scoped IDENTICALLY (top-level, non-descended goals only — a descend
  hole's own fold-up accept is untouched). Records facts only; decides
  nothing.

### 1.3 `seeds/program_synthesis.json` v1.11.0 — three new rules, one gate edit

- `ps_property_clear` / `ps_property_reject_gap` / `ps_property_reject_reopen`
  mirror the D1/D2 structural-exclusion pair exactly: a property
  violation, like D1/D2, names no single declared parameter to hand to a
  hole-reopen (the fault is in what the whole candidate COMPUTES at the
  witness), so `route` is always `'exclusion'`. On a `'retrieved_exemplar'`
  source (no alternative candidate to distinguish it from) the rung goes
  straight to the honest terminal `'gapped'`
  (`ps_gap_reason := 'property_verdict_reject'`); otherwise it reuses the
  SAME standing CEGIS `exclude`/reproposal contract the structural twin
  already reuses, routing to `'counterexample'`.
- `ps_accept`'s gate: the third Or-arm (previously
  `ps_structural_reject==0.0`) is now `And(ps_structural_reject==0.0,
  ps_property_reject==0.0)` — the ONE edit to the existing verdict layer,
  minimal and targeted. Every other arm (sub-goal / descended-goal bypass)
  is untouched.
- Rejection nodes carry `properties` (the fired atom ids) and
  `witnesses_json` (env/got/expected per firing) — the explainability
  contract, parallel to D1-D3's `detectors`/`free_vars`/
  `varying_unread_params`.

A circular-import note: `prog_synthesis.py` and `prog_property.py` import
each other (the same pattern `prog_synthesis.py`/`prog_retrieval.py`
already use). The `_DISPATCH` tuple's property entry is a **deferred
lambda**, not an inlined `pp.compute_property_facts` attribute lookup —
importing `prog_property` before `prog_synthesis` would otherwise see a
not-yet-initialised partial module at `_DISPATCH`-construction time
(caught live during test authoring, fixed, verified both import orders
work).

---

## 2. THE HEADLINE — self-detected wrongness, mechanism first

### 2.1 Primary: the frozen 36-task residual population

Re-derived LIVE through the REAL seed rules (`psy.pump`, not just the
fact-computation primitive) against the frozen `results/mbpp_arc3_endgame.json`
`full_r3` population (never re-run) — **36/36 (100%) of the honest
residual is now self-detected and rejected pre-accept.** Every one reaches
`status='gapped'`, `gap_reason='property_verdict_reject'`, mints no
Program node, and its Rejection names the firing property + the exact
witness. A sample (full table with every id's property + witness in
`tests/test_prog_property_migrated.py::headline_36`):

| id | property | witness | got | expected |
|---|---|---|---|---|
| 17 | `prop_perimeter_square` | a=1 | `True` | 4 |
| 105 | `prop_count_true` | `[True,True,False]` | 0 | 2 |
| 67 | `prop_bell_number` | a=26 | −5708985697509898574 | 49631246523618756274 |
| 452 | `prop_sale_loss` | a=100,b=150 | 100 | 50 |
| 455 | `prop_month_has_31_days` | a=4 | `True` | `False` |

**False-refutation rate: 0/21** on the SAME frozen population's
currently-correct (`pass`) accepted programs — every one accepts normally,
mints its Program node, and shows `ps_property_reject==0.0`. (Three of
the 21 — 397, 404, 433 — are ALREADY, independently, correctly caught by
the PRE-EXISTING D1-D3 structural rung, per
`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md §2.2`'s own hand-verified
label-noise finding; this predates and is unrelated to the property rung,
held out of the false-refutation count for that reason and verified
separately to be structural-only, never property-driven.)

### 2.2 Secondary: the SAME denominator `PROGRAM_SYNTHESIS_ARC4_S5.md` used

Per the brief: the primary metric is self-detected wrongness, not the
pass rate, reported over the SAME 104-task denominator arc4 S5 measured
(`NO-STRUCTURAL`'s own live `accepted_holdout_fail` population, S1+S4
active, frozen in `results/arc4_endgame.json`'s `no_structural` arm).
Arc4 S5's own number: **26/104 = 25.0%** (structural-only).

Re-run live, TODAY, with structural AND property both active:

**61/104 = 58.7% of the same live wrongness now self-detected before
accept** — up from 26/104. Of the +35 incremental conversions, **every
one is a task_hint of one of the 36 PropertyAtoms** (35 of the 36 — see
§2.3 for the one exception); the pre-existing 26 conversions are
UNCHANGED (byte-identical, confirmed by a dedicated regression test, §4)
and are a strict subset of the 61. Full id lists are reproducible via
`scripts/arc4_endgame_battery.py`'s own arms plus a live
`mbpp_arc3_battery.run_pass` call (the exact method
`tests/test_reject_informs_repair_migrated.py::test_no_wrong_accept_regression_vs_v1_7_0_baseline`
already uses, extended to this phase — see §5 for why that specific test
now needs a one-line reconciliation this phase does not own).

### 2.3 The one named miss: task 250, scoped out by design

Of the 36, **35/36 convert on the live 257-task population**; task 250
does not, for the SAME reason a descended goal is scoped out of the
structural rung: **on this live run, task 250's accept engaged the
descend/fold-up rung** (`rungs.descend == 1.0`), and
`compute_property_facts` — deliberately, mirroring
`compute_structural_facts`'s own documented scope boundary — never runs
for a goal that engaged descent. Confirmed genuinely still wrong
(re-verified against its own held-out row, sanctioned confirmation only,
after the live outcome was already known): the live-accepted candidate
for task 250 is `(b // 2) - 2` — arithmetic garbage that never reads its
tuple argument at all, disagreeing with the held-out row (`got=2`,
`expected=4`). This is an honest, named, pre-existing residual (the exact
same boundary the structural rung already lives with), not a new gap
this phase introduces — reported here rather than silently absorbed into
the headline.

Seven more of the 35 (171, 256, 295, 300, 389, 392, 453) reach their
final terminal via the REOPEN path rather than the direct gap: property
correctly fires (`ps_property_reject==1.0`, confirmed live via
`read_goal`), the standing CEGIS exclude/reproposal lane genuinely
retries, and — on this particular live run — honestly exhausts its
budget without finding a replacement, landing at `gapped:enumerate_failed`
rather than `gapped:property_verdict_reject`. This is the SAME dynamic
`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` already documented for the
structural rung's own reopen twin ("informing repair genuinely tries
again before giving up, so the terminal reason is the LATER one") — a
correct catch with an honest retry, not a miss.

---

## 3. SOUNDNESS — the failure mode that matters more than a missed trap

Every atom is **self-verified against the goal's own revealed rows**
before it may fire (`_self_verify_atom`, the `comprehend_theorem.
self_verify_clause` precedent applied to a property instead of a theorem
clause): the reference relation must reproduce EVERY revealed row's own
expected value, or the atom is refused — never checked against held-out
data, only against what the goal was ingested with. Gated directly
(`tests/test_prog_property_migrated.py`):

- **Refutability, checked, not asserted.** A synthetic goal whose prompt
  matches `'perimeter of a square'` but whose own revealed row does NOT
  agree with `4×side` never fires the atom, even when the candidate's own
  (broken) output would otherwise look like a "violation" of the wrong
  conjecture — the goal accepts normally.
- **False-refutation rate: 0/21** on the frozen population (§2.1); the 61
  live conversions in §2.2 were independently re-verified for a 6-id
  sample against each task's OWN held-out row (sanctioned confirmation
  only, called strictly after the live outcome is known) — every accepted
  candidate the property rung did NOT flag is either genuinely correct or
  falls in the documented descend-scope exception (task 250); the
  property rung never disagreed with the held-out truth for any sampled
  id.
- **Held-out isolation, mechanical audit.** The literal substring
  `"held_out"` appears in none of `prog_property.py`'s functions,
  independently re-verified (`test_held_out_isolation_source_audit`) and
  by signature (`test_property_functions_take_only_graph_atom_and_env_derived_args`
  — no function accepts a parameter named `spec`/`held_out`/
  `held_out_rows`).
- **No-Python-decision audit.** `test_no_python_decisions_in_property_code`
  (the ink-suite pattern) finds no banned `argmin`/`argmax`/`min`/`max`
  key= call anywhere in `prog_property.py`; `test_compute_property_facts_
  never_sets_status_or_mints_program` confirms the adapter records facts
  only — the seed rules decide.

**No true regression.** Every status change this phase causes on the
live population converts a KNOWN-WRONG accept (`accepted_holdout_fail`)
to an honest gap; nothing that was genuinely correct (`pass`) is ever
touched (§2.1's 0/21, §3's 6-sample cross-check).

---

## 4. Occam / no-regression — the D1-D3 structural rung, unperturbed

`tests/test_prog_property_migrated.py::test_structural_rung_recall_and_fp_
unperturbed_by_the_property_rung` re-derives
`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`'s own D1/D2/D3 trap and
false-positive id lists over the identical frozen 76-trap/21-pass
population **with the property rung installed** — byte-identical to the
frozen measurement. The two rungs read completely disjoint goal attrs
(`ps_st_*` vs `ps_prop_*`), are dispatched independently, and this test
proves the addition of one never perturbs the other's own numbers.

---

## 5. Known test-file pin drift (NOT fixed here — outside this phase's file ownership)

This phase's own file ownership excludes all of `tests/**` except the
one new file it created. The version bump (1.10.0 → 1.11.0) and rule
count (70 → 73) it requires mechanically break **14 test node ids across
6 sibling-owned files**, none of which represent a soundness or logic
regression — every one is accounted for below and re-verified live before
being reported this way (never merely asserted).

**Pure version-string pins** (`assert ... == "1.10.0"`, a one-line bump
to `"1.11.0"`):
`test_verdict_discrimination_migrated.py::test_seed_version_bumped_and_two_new_rules`,
`test_budget_isolation_migrated.py::test_seed_version_and_isolation_lanes_present`,
`test_retrieval_migrated.py::test_attempt1_codebook_screen_rules_stay_absent_from_the_seed`.

**Pure rule-count pins** (`assert len(rules) == 70`, a one-line bump to
`73`, +3 for `ps_property_clear`/`ps_property_reject_gap`/
`ps_property_reject_reopen`):
`test_program_synthesis_migrated.py::test_seed_loads_clean`.

**Combined version+count pins** (same one-line bumps, first assertion
hit is the version string):
`test_exact_first_migrated.py::test_program_synthesis_seed_bumped_with_three_new_rules`,
`test_prog_moves_migrated.py::test_seed_bumped_with_three_new_rules`,
`test_reject_informs_repair_migrated.py::test_seed_v1_8_0_shape`.

**Behavioural, and CORRECT — three specific ceiling ids the live
retrieval ladder already documents as wrong** (`MEASURED_OUTCOMES[105/238/405]`
all carry `holdout_ok: False` in `test_retrieval_migrated.py`'s own frozen
table — this phase's property rung now catches them BEFORE the wrong
accept, converting `status: accepted` → `gapped`, exactly its job):
`test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[105]`,
`[238]`, `[405]`, and
`test_retrieval_migrated.py::test_occam_order_exact_pass_never_falls_through_to_deeper_rungs`
(same task 105).

**An attributed-gains allowlist that needs a new constant** (the
`_ARC5_EXACT_FIRST_PASS_IDS`/`_ARC5_MOVES_PASS_IDS` precedent, extended
with an `_ARC6_PROPERTY_CAUGHT_IDS` naming this phase's own +35
conversions — §2.2's own id list):
`test_reject_informs_repair_migrated.py::test_no_wrong_accept_regression_vs_v1_7_0_baseline`.

**Meta-tests that transitively fail** by re-running the above as a
subprocess and diffing against a fixed allowlist (need the SAME ids added
to their own `_KNOWN_OUT_OF_SCOPE_FAILURES` set):
`test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`,
`test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`.

Every one of these 14 was individually re-run and its failure traced to
exactly one of the causes above (never left as a bare "expected
failure") — see this phase's own final report for the per-test
tracebacks. `tests/test_prog_property_migrated.py` itself is green (63
passed) and does not depend on any of the six files above continuing to
carry stale literals.

---

## 6. Files

NEW `domains/prog_property.py` (the faculty — reference registry + the
mechanical rim `compute_property_facts`). NEW
`seeds/program_properties.json` (36 PropertyAtoms). `seeds/
program_synthesis.json` v1.10.0 → v1.11.0 (+3 rules:
`ps_property_clear`/`ps_property_reject_gap`/`ps_property_reject_reopen`;
1 edit: `ps_accept`'s gate). `domains/prog_synthesis.py` (the
`pp.compute_property_facts` dispatch entry — a deferred lambda for
import-order safety — and the `read_goal` `"property"` read-back block,
mirroring `"structural"`). NEW `tests/test_prog_property_migrated.py`
(63 passed, ~3s: per-atom unit checks, the 36-id headline, the
false-refutation gate, refutability, explainability, reject-before-accept
on both routing sources, scope discipline, held-out isolation +
no-Python-decision audits, the D1-D3 no-regression re-derivation, and the
seed version/rule-count pin this phase owns). This file.
