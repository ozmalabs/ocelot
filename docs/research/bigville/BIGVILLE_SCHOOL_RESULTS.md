# BIGVILLE R18 — THE SCHOOL (block 266000) — RESULTS

Measured AFTER the pre-registration commit (`BIGVILLE_SCHOOL_PREREG.md`). Every
number below is reproduced by `python scripts/bigville_school_run.py`
(→ `results/bigville_school/summary.json`) and gated by
`tests/test_bigville_school_migrated.py` (**15/15 green**). Base merge-base:
`0618653a3446c86510b35bdf6d580beabd4857a3`.

## Headline

The school is where **R6 (teaching) × R9 (fiscal salary) × R14 (children) × the
STANDING 239 window** meet, entirely graph-native: nine rule decisions across
three `self_load_only` seeds, ZERO new Rust. The adapter subclasses
`BigvilleFiscWorld` (the read-only reuse of R9/R6/239) and grounds R14's deferred
capability with a **school-derived** capability.

## Gate-by-gate (all green)

### G-council-funds-the-schoolmaster
- **Funded → open.** Tax ON → the purse is funded → the schoolmaster is paid his
  salary from the Treasury (`master coin = 20`, `paid_count = 1`, `unpaid = 0`) →
  the school **OPENS** (`open = 1`). The salary is R9's `fs_pay_salary`, reused
  unchanged — the schoolmaster is the THIRD public-payroll name (`role = 3`).
- **Ablate revenue → closed.** Collect nothing → empty purse → `fs_salary_unfunded`
  (`unpaid = 1`) → the school **CLOSES** (`closed = 1`). Funding is load-bearing.
- **Tax-cutting council → closed.** `base_rate_bp = 0` → zero revenue even with
  collection → unpaid schoolmaster → school closes. A clean structural
  counterfactual: same schoolmaster, the COUNCIL's rate decides whether the school
  runs.

### G-classroom-learning-is-affect-gated (HEADLINE, R6 × the 239 window)
- **Within-window child learns.** An unstressed (regulated) child in an open school
  with a willing master acquires the full rate (`skill 0 → 1.0`, `fail_reason = 0`).
- **Dysregulated + co-regulated learns.** A stressed child (`dysregulated = 1`)
  whom a SAFE schoolmaster co-regulates (the STANDING 239 `coreg_pull`) returns
  within the window (`dysregulated → 0`) and learns (`skill → 1.0`); the window
  **widened** (`widen_count = 1`).
- **THE FALSIFIER — ablate co-regulation → does NOT learn.** The SAME dysregulated
  child with no `attended_by` schoolmaster stays `dysregulated = 1` at lesson time
  → does NOT acquire (`skill = 0`, `fail_reason = 1`). The school was OPEN, the
  master willing, the prerequisite met — **only the affect differs. The window, not
  the lesson, is the bottleneck.**

### G-heterogeneous-classroom (outcome DISTRIBUTION + confound-dissolution)
One class, identical school + master, four children with DIFFERENT drawn states →
a **non-uniform** outcome, and the glass box reads a DISTINCT `fail_reason` for
each non-learner:

| child | learned? | WHY (read off the graph) |
|---|---|---|
| well-regulated, prepared | yes | learned |
| missing prerequisite | no | `missing-prereq` (2) |
| dysregulated, no co-reg | no | `dysregulated` (1) |
| low safety-prior | no | `low-safety-prior` (4) |

Three DISTINCT causes of the same failing grade — "does well if it CAN", the
marshmallow confound-dissolution applied to a failing grade, not a will to fail.

### G-generational-hinge (grounds R14's deferred capability)
- **School → capability → adult.** A child schooled through 5 willing lessons
  (`skill = 5.0`) comes of age with `capability = 0.8` (`= 0.3 base + 0.1 × 5`); an
  unschooled child comes of age with `capability = 0.3` (base only). What a child
  LEARNED determines the adult it becomes — computed in THIS adapter (R14 not
  edited; its rearing-proxy is grounded here with school-derived capability).
- **Defunded cohort under-capable.** A defunded school (closed → no acquisition)
  → the whole cohort comes of age with a LOWER mean capability (`0.3` vs the funded
  cohort's `0.8`), `skill = 0` for every child. A structural, generational lever no
  individual child escapes.

### G-schoolmaster-has-an-inner-life
| master | `held_rate` | `sabotaged` | `stated − held` | child gain |
|---|---|---|---|---|
| willing (fairly paid) | 1.00 | 0 | 0.00 | 1.00 |
| underpaid (salary 5 < fair 20) | 0.25 | 1 | 0.75 | 0.25 |
| coerced | 0.25 | 1 | 0.75 | 0.25 |

An underpaid OR coerced master SABOTAGES — delivers `sabotage_rate` while
professing `stated_rate` (the 234 `stated ≠ held` atom) → children acquire
DEGRADED. A willing master transfers cleanly.

### ETHICS (induce → measure → RESTORE)
INDUCE a learning failure via dysregulation (stressed child, no co-regulation:
`skill = 0`, `fail_reason = dysregulated`); **RESTORE by co-regulation** (a safe
schoolmaster re-attends → the 239 widens/returns the window → the child learns,
`skill → 1.0`, `widen_count > 0`). The RESTORE is co-regulation, not a reset; the
dysregulation is a STATE, reversed, never a punishment. No reward/punishment token
appears in any seed's rule logic (seed-level + source audit).

## Discipline ledger (all satisfied)

- `tests/test_bigville_school_migrated.py` — **15/15 green**.
- `tests/test_failure_baseline_migrated.py` — **11/11**.
- `tests/test_engine_provenance_migrated.py` — **7/7**; `source_match` in
  `{own, shared}` (invariant asserted; NO pinned md5).
- `git diff 0618653a34 -- runners/dsl` — **empty** (no Rust, incl. `term.rs`). The
  seeds compose only known DSL Terms (`Attr/Var/Lit/Plus/Times/Min/Max/Eq/Gte/Lt/
  And/Or/IfThenElse`).
- Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` — UNCHANGED
  START==END; no `.so` committed.
- Additive-only: six NEW `bigville_school_*` files; **no existing tracked file
  edited**; one prefix; explicit `git add` paths.
- All three seeds `self_load_only`, `depends_on: []` ⇒ the rung cannot regress any
  other suite. (Per the 2026-07-29 directive, the ~43-min
  `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` oracles were NOT
  run — additive `self_load_only` + the fast baseline gate is sufficient.)

## R17 deferral (honest)

R17 (affect closes the loop — the general affect→`decision_value` coupling) is a
CONCURRENT sibling and is NOT on this base. R18's affect-gated-LEARNING front-end
is the STANDING 239 `arousal_window_coreg` window (used directly, exactly as R14
used it for rearing) — **no R18 gate depends on R17.** DEFERRED to R17: coupling
the child's felt affect into a general BEHAVIOURAL `decision_value` beyond the
learning gate (e.g. a grief-narrowed child making worse LIFE choices). R18 claims
only the learning gate.

## Honest residuals

1. **The class period is a fixed tick count (`LESSON_SETTLE = 4`), a WORLD FACT.**
   It is chosen so that a co-regulated child settles within the window in a class
   period while an unsupported one (self-regulation only, `k_self ≪ k_co`) does
   not. This is the affect-gate calibration, pre-registered as a world parameter,
   not a claimed result; a longer unsupported period would let self-regulation
   return the child (the R14 neglect-arm behaviour), which is realistic but is not
   what a single class period models.
2. **The prerequisite is a single boolean (`prereq_met`).** Real curricula are a
   dependency DAG; R18 models the prerequisite as one gate so the "missing-prereq"
   fail-reason is first-class. A richer prerequisite lattice is future work.
3. **The taught subject is a single scalar Skill (`LITERACY`).** One learnable
   competence suffices for every R18 gate; a multi-subject classroom is additive
   future work.
4. **Capability at coming-of-age is linear in the acquired Skill.level** (clamped to
   [0,1]). The grounding of R14's proxy is deliberately the simplest faithful map;
   the point is that it is SCHOOL-DERIVED (funded/regulated → high; defunded → base),
   not the exact functional form.
5. **The generational chain is demonstrated in the R18 adapter, not wired into the
   R14 life-cycle seeds** (R14 is not edited, per the build rule). Fusing
   school-derived capability into R14's `bl_come_of_age` is a future integration
   rung, not this one.
