# BIGVILLE R18 — THE SCHOOL: public education, a council-paid schoolmaster, the glass-box classroom (block 266000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** Committed in a separate prereg commit,
ahead of the build/measurement commit. It fixes the claims, the gates, the
failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `0618653a3446c86510b35bdf6d580beabd4857a3`
(carries R1–R9 + R11 + R12 + R13 + R14 + R16 + R19).
Branch: `worktree-agent-a39aae2acb665595d`
Block: **266000–266999** (R18 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R18 + §2 FISCAL + §2.9 children).

## Seed claim (verbatim, `python scripts/seed_claim.py 266000 266999`)

```
SEED CLAIM 266000-266999: CLEAN -- no collision DETECTED.
  Scope: 975 files with seed sinks; 686 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 266 266` — the single-integer form the
supervisor named — is likewise CLEAN.)

## Architecture (target: ZERO new Rust)

- The school (funding, classroom acquisition, the schoolmaster's inner life, the
  generational hinge) is **graph rules over existing DSL Terms** only
  (Attr / Var / Lit / Plus / Minus / Times / Min / Max / Eq / Gt / Gte / Lt /
  And / Or / Not / IfThenElse / set_attr). **No new Rust Term.**
  `git diff 0618653a34 -- runners/dsl` MUST be empty (incl. `term.rs`).
- **The world adapter SUBCLASSES R9 (`BigvilleFiscWorld`) by import** — this is
  the READ-ONLY reuse of **R9** (the Treasury / Council / public-salary machinery
  — the schoolmaster is a public servant paid from the purse, the THIRD payroll
  name after mayor/constable), of **R6** (skill / teaching, via the
  `BigvilleSkillWorld` ancestor — `Skill` nodes, `learns_from`, teach/coerce/
  sabotage), and of the **STANDING 239 `arousal_window_coreg`** window/co-regulation
  rules (loaded by the `BigvilleTimeWorld` ancestor). **R14 (`bigville_life_*`) is
  reused by pattern, not edited**: the child's 239 window nodes are attached in the
  adapter exactly as R14's `rear()` does, and the come-of-age→capability→adult
  chain is demonstrated in THIS adapter with a **school-derived** capability that
  grounds R14's deferred rearing-proxy. No existing tracked file is edited.
- New additive files only, all prefixed `bigville_school_`:
  `seeds/bigville_school_fund.json`, `seeds/bigville_school_learn.json`,
  `seeds/bigville_school_life.json`, `worlds/bigville_school_world.py`,
  `scripts/bigville_school_gen_seeds.py`, `scripts/bigville_school_run.py`,
  `tests/test_bigville_school_migrated.py`, this file,
  `BIGVILLE_SCHOOL_RESULTS.md`, `results/bigville_school/summary.json`.
- All three seeds are **`self_load_only`** (`depends_on: []`), never auto-loaded
  into the default agent. Additive + self-load ⇒ the rung cannot regress any
  other suite.
- **Every DECISION is a rule.** The adapter only: mints the School / Schoolmaster /
  child / 239-dyad nodes (ingest), wires edges (`staffed_by`, `enrolled_in`,
  `learns_from`, `attended_by`), delivers world facts (a stressor tick, whether a
  co-regulating schoolmaster is present, the tax/salary phase), arms one-shots,
  runs the Rust `run_rules` fixpoint, and reads state. No Python `if`/`else` over
  agent state decides who is paid / who learns / who sabotages / who matures —
  source-audit gate.

## R17 DEPENDENCY — DEFERRED HONESTLY

R17 (affect closes the loop — the general affect→`decision_value` coupling) is a
CONCURRENT sibling, NOT on this base. R18's affect-gated-learning HEADLINE needs
only the **window-gates-LEARNING** front-end, which is the STANDING 239
`arousal_window_coreg` machinery (exactly as R14 used it for rearing). We use 239
DIRECTLY. **No R18 gate depends on R17.** The one thing DEFERRED to R17: coupling
the child's felt affect into a general behavioural `decision_value` beyond the
learning gate (e.g. a grief-narrowed child making worse LIFE choices). R18 claims
only the learning gate; the broader affect→behaviour coupling is out of scope and
recorded as deferred.

## Rules (9; all in the three seeds; every one a decision)

**`bigville_school_fund.json`** — funding sets whether the school is OPEN:
- `sc_school_open` — `school.open=1, closed=0` when armed AND the schoolmaster is
  paid (`unpaid==0 AND paid_count>=1`). The salary itself is the R9
  `fs_pay_salary` (reused unchanged: the schoolmaster is a Treasury-paid servant).
- `sc_school_close` — `school.open=0, closed=1` when armed AND the schoolmaster is
  `unpaid==1`. (Ablate tax revenue / a tax-cutting council ⇒ `fs_salary_unfunded`
  sets `unpaid=1` ⇒ the school CLOSES.)

**`bigville_school_learn.json`** — the schoolmaster's inner life + the affect-gated
classroom (HEADLINE):
- `sc_master_quality` — the schoolmaster's DELIVERED transfer rate (234 `stated≠held`):
  `resentful = coerced OR salary < fair_salary`; `held_rate =
  IfThenElse(resentful, sabotage_rate, stated_rate)`; sets `sabotaged/willing/underpaid`.
  A willing (fairly-paid, uncoerced) master delivers `stated_rate` (clean transfer);
  an underpaid / coerced one delivers `sabotage_rate` (degraded).
- `sc_acquire` (**HEADLINE**) — a child's `Skill.level += held_rate` (capped at
  ceiling), `acquired += 1`, iff armed AND `school.open==1` AND child **within
  window** (`AffectiveState.dysregulated==0` — the 239 gate) AND `prereq_met==1`.
- `sc_fail_closed` — armed AND `school.open==0` ⇒ `fail_reason=3` (defunded school).
- `sc_fail_no_prereq` — armed AND open AND `prereq_met==0` ⇒ `fail_reason=2`.
- `sc_fail_low_safety` — armed AND open AND prereq AND `dysregulated==1` AND
  `window.safety_prior < safety_floor` ⇒ `fail_reason=4` (low safety-prior).
- `sc_fail_dysreg` — armed AND open AND prereq AND `dysregulated==1` AND
  `safety_prior >= safety_floor` ⇒ `fail_reason=1` (transient dysregulation).
  (The five open/prereq/dysreg/safety branches PARTITION the space ⇒ exactly one
  fires per armed child ⇒ the glass box reads WHY each child did or did not learn.)

**`bigville_school_life.json`** — the generational hinge (grounds R14's proxy):
- `sc_come_of_age` — armed AND not matured ⇒ `capability = clamp01(base_capability
  + coa_gain * Skill.level)` (SCHOOL-DERIVED, from what was acquired), `adult=1`,
  `matured=1`. What a child LEARNED determines the adult it becomes.

## Gates (each a test in `tests/test_bigville_school_migrated.py`)

### G-council-funds-the-schoolmaster
1. `test_council_funds_schoolmaster_school_opens` — tax ON ⇒ purse funded ⇒ the
   schoolmaster is paid his salary from the Treasury (his coin rises by the salary,
   `paid_count==1`, `unpaid==0`) ⇒ the school OPENS.
2. `test_ablate_revenue_closes_the_school` — FAILING CONTROL: ablate tax revenue
   (collect nothing) ⇒ empty purse ⇒ `fs_salary_unfunded` (`unpaid==1`) ⇒ the
   school CLOSES (`open==0, closed==1`).
3. `test_tax_cutting_council_closes_the_school` — a tax-cutting council
   (`base_rate_bp=0`) ⇒ zero revenue ⇒ the schoolmaster unpaid ⇒ the school closes
   (a structural counterfactual: same schoolmaster, the COUNCIL's rate decides).

### G-classroom-learning-is-affect-gated (HEADLINE, R6 × the 239 window)
4. `test_within_window_child_learns` — a within-window (regulated) child in an open
   school with a willing master ACQUIRES (`Skill.level` rises, `acquired>0`,
   `fail_reason==0`).
5. `test_dysregulated_child_coregulated_learns` — a hungry/dysregulated child
   (stressor delivered) whom a SAFE schoolmaster CO-REGULATES (239 widens/returns
   the window) returns within window and ACQUIRES; `window.widen_count` rose.
6. `test_ablate_coregulation_dysregulated_child_does_not_learn` — **the falsifier**:
   the SAME dysregulated child with co-regulation ABLATED (no safe caregiver present)
   stays `dysregulated==1` at lesson time ⇒ does NOT acquire (`fail_reason==1`, the
   window not the lesson is the bottleneck). Skill level unchanged vs gate 5.

### G-heterogeneous-classroom (outcome DISTRIBUTION + confound-dissolution)
7. `test_heterogeneous_classroom_outcome_distribution` — a class of children with
   DIFFERENT drawn priors / states (well-regulated; missing-prerequisite;
   dysregulated-no-coreg; low-safety-prior) yields a NON-uniform outcome
   distribution (some learn, some don't), and the glass box reads a DISTINCT
   `fail_reason` for each non-learner (`{no_prereq, dysreg, low_safety}` all present)
   — "does well if it can", not a will to fail.

### G-generational-hinge (grounds R14's deferred capability)
8. `test_school_derived_capability_at_coming_of_age` — a schooled child comes of age
   with a HIGHER `capability` than an unschooled one; capability tracks the acquired
   `Skill.level` (school→capability→adult, demonstrated in THIS adapter).
9. `test_defunded_school_cohort_comes_of_age_undercapable` — ablate the school
   (defunded ⇒ closed ⇒ no acquisition) for a whole cohort ⇒ the cohort's mean adult
   capability DROPS vs a funded cohort (a structural, generational lever no
   individual child escapes).

### G-schoolmaster-has-an-inner-life
10. `test_willing_master_clean_transfer` — a fairly-paid, uncoerced master delivers
    `stated_rate` (`willing==1`, `sabotaged==0`, `stated_minus_held==0`); children
    acquire the full gain.
11. `test_underpaid_or_coerced_master_sabotages` — an underpaid OR coerced master
    delivers `sabotage_rate < stated_rate` (`sabotaged==1`, `stated_minus_held>0`,
    the 234 atom) ⇒ children acquire DEGRADED (a smaller gain than the willing arm).

### ETHICS (induce → measure → RESTORE)
12. `test_ethics_dysregulation_is_restored_by_coregulation` — INDUCE a learning
    failure via dysregulation (measure: does not acquire, window narrowed); RESTORE
    by co-regulation (a safe schoolmaster re-attends ⇒ 239 widens the window back ⇒
    the child returns within window and ACQUIRES). No reward/punishment token — the
    dysregulation is a STATE, reversed, never a badness (seed-level + source audit).

### Discipline / source-audit
13. `test_no_python_school_decision_source_audit` — the nine decisions are rule
    names in the three seeds; the adapter runs no Python rule engine and branches on
    no decision parameter; no reward/punishment token in the seed rule logic.
14. `test_seeds_self_load_only_and_no_new_rust` — the three seeds are
    `self_load_only` with `depends_on: []`; provenance passes
    (`source_match in {own, shared}`, NEVER a pinned md5); the seeds compose only
    known DSL Terms (no new Rust).

## Discipline ledger the results must satisfy

- `git diff 0618653a34 -- runners/dsl` **empty** (no Rust, incl. `term.rs`).
- Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED START==END;
  no `.so` committed.
- `tests/test_bigville_school_migrated.py` all green.
- `tests/test_failure_baseline_migrated.py` 11/11; `tests/test_engine_provenance_migrated.py` 7/7.
- Only NEW `bigville_school_*` files added; no existing tracked file edited; one
  prefix; `git add` explicit paths only.
- Honest residuals recorded in `BIGVILLE_SCHOOL_RESULTS.md`; the R17 deferral above
  is the one scoped-out coupling.
