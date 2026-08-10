# PROGRAM SYNTHESIS ARC 4 PHASE S2 — VERDICT DISCRIMINATION: rejecting wrong programs before accept, as rules

**Date:** 2026-08-01. Lands `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`'s
measured detector catalogue (D1 memo_lookup_table, D2 dead_code_free_vars, D3
unread_declared_param — the three with non-zero recall and held precision)
as GRAPH-NATIVE seed rules gating `ps_accept` in `seeds/program_synthesis.json`
(v1.6.0 → v1.7.0), with `domains/prog_synthesis.py`'s `compute_structural_facts`
as the mechanical rim. Gate: `tests/test_verdict_discrimination_migrated.py`,
24 passed, ~1.3s.

---

## 0. The design, and why it is graph-native

The measurement (`scripts/arc4_structural_verdicts.py`) walked a JSON dict
OFFLINE, on a frozen artifact. This landing does the SAME three detectors'
job LIVE, on the graph: the accepted candidate IS a reflected Term subgraph
already sitting in the substrate (`Term.<Variant>` nodes, `child.<field>`
edges — `runners/dsl/src/reflect.rs`, confirmed empirically: `Term.ProgSeq`
→ direct children via `sub.neighbours(root, None)`; singular fields like
`child.cond`/`child.then`/`child.other`/`child.value` addressable by exact
edge type). `domains/prog_synthesis.py` gained:

- `_st_walk`/`_st_has_type`/`_st_var_refs`/`_st_bound_names`/`_st_returns`/
  `_st_single_child`/`_st_is_equality_like_literal_test`/
  `_st_literal_dispatch`/`_st_params` — graph-native transliterations of the
  frozen script's own `collect_var_refs`/`collect_bound_names`/
  `collect_returns`/`is_equality_like_literal_test`/`literal_dispatch`/
  `_param_names`, operating on `sub.node`/`sub.neighbours` instead of a JSON
  dict walk.
- `compute_structural_facts(sub, ag_node, g)` — the new adapter verb,
  dispatched on `status == "verified"` (the SAME status `ps_accept` reads),
  idempotent per candidate via the COUNT of `ps_ir_reflected` edges on `g`
  (a fresh edge is added by every accept path before a goal can reach
  'verified', so this count strictly increases per distinct verified
  candidate — robust across attempt-counter lanes that don't all touch
  `ps_attempts`, e.g. fold-up). It walks the reflected subgraph + the
  goal's own revealed `ExampleRow`s (never held-out — an `ExampleRow` IS
  the revealed set the goal was ingested with) and records D1/D2/D3's raw
  facts as goal attrs (`ps_st_d1_fired`/`ps_st_d2_fired`/`ps_st_d3_fired`,
  `ps_st_free_vars`, `ps_st_varying_unread_params`, `ps_st_fired_detectors`,
  `ps_st_any_fired`, `ps_st_computed`). **It never decides anything** — the
  transitive/aggregate properties (whole-program bound-name closure,
  literal-dispatch-tree leaf collection, revealed-row value-set matching)
  exceed one `where`-clause rule application (a single match is a
  fixed-depth pattern; these need an unbounded-depth walk), so per
  CLAUDE.md's own documented honest split (the `record_trace`/`ps_reflect_ok`/
  `cmp_ok` precedent) the adapter performs the walk and records
  FIXED-FORMULA facts; the RULES decide the verdict.

Two new rules in `seeds/program_synthesis.json` v1.7.0 read those facts:

- **`ps_structural_clear`** — `status=='verified'`, `ps_depth==0.0`,
  `ps_rung_descend != 1.0`, `ps_st_computed==1.0`, `ps_st_any_fired==0.0` →
  `set_attr g ps_structural_reject 0.0`.
- **`ps_structural_reject`** — the same guard with `ps_st_any_fired==1.0` →
  mints a `Rejection{detectors, construction, attempt, free_vars,
  varying_unread_params}` node (`Goal -has_structural_rejection-> Rejection`,
  a new production), `set_attr g ps_structural_reject 1.0`, `ps_gap_reason
  'structural_verdict_reject'`, `status 'gapped'` — **directly**, not
  through the counterexample/exclude/reproposal lane (see §4 for why).

`ps_accept`'s own `where` gained one item: `Or(Not(Eq(ps_depth,0.0)),
Eq(ps_rung_descend,1.0), Eq(ps_structural_reject,0.0))` — a top-level, FLAT
(non-descended) goal must read `ps_structural_reject==0.0` before minting a
Program; a sub-goal or a descend-engaged goal is untouched (see §4).

---

## 1. Detector design, per rule

| detector | what the RULE decides | what the ADAPTER records |
|---|---|---|
| **D1 memo_lookup_table** | fires iff `ps_st_d1_fired==1.0` | walk: exactly one `Term.ProgReturn` in the whole program; its `child.value` is built ENTIRELY from `Term.Lit` leaves combined by `Term.IfThenElse` nodes whose `child.cond` is `Term.Eq`/`Term.Minus`/`Term.Not` AND contains both a `Lit` and a `Var` in its own subtree (excludes `Gt`/`Lt`/`Gte`/`Lte` — order predicates are generalising logic, not memorisation); the reachable leaf VALUES equal the revealed `ExampleRow.expected` value SET exactly (type-distinguishing: bool never conflated with numeric 1/0, the `_row_cmp_ok` convention). |
| **D2 dead_code_free_vars** | fires iff `ps_st_d2_fired==1.0` | walk: every `Term.Var.name` read anywhere, minus every name BOUND anywhere (`Term.ProgDefFnParam`/`ProgAssignVar`/`ProgAugAssign`/`ProgTupleUnpack`/`ProgForEach`/`ProgTryOr`/`ProgComprehensionList`/`ProgComprehensionGen`, **plus, found and fixed during this landing (§3), any node carrying a `var_name` or `acc_name` attr** — the plain DSL higher-order terms `Filter`/`FilterList`/`Exists`/`Sum`/`Prod`/`MinOver`/`MaxOver`/`Argmax`/`Argmin`/`ArgminUnique`/`ArgminRefusal`/`Fold`/`MapList`/… all bind their iteration variable this way). A non-empty difference fires. |
| **D3 unread_declared_param** | fires iff `ps_st_d3_fired==1.0` | walk: the leading `Term.ProgDefFnParam` direct children of the `Term.ProgSeq` root, minus every read `Var` name anywhere = unread params; a param is a genuine defect iff the revealed `ExampleRow.inputs_json` values for that param name take ≥2 distinct values across the revealed rows (proves it isn't a harmless-because-constant unused arg). |

D4–D7 (constant_output, vacuous_guard, arity_mismatch, exhaustive_domain_proof)
are **not landed** — the frozen measurement recorded zero recall for all
four on the 76/21 population (`results/arc4_structural_verdicts.json`'s own
`per_detector` block), and the plan explicitly scopes this phase to "the
three with measured recall." Landing a zero-measured-recall rule would add
surface area (more rule/attr plumbing, more places a future edit could
regress) for zero demonstrated catch — declined on that basis, not
forgotten.

---

## 2. Re-derivation vs the frozen measurement

`tests/test_verdict_discrimination_migrated.py`'s `live_rederivation`
fixture runs the LIVE graph-native `compute_structural_facts` (via a
throwaway synthetic goal per task — no propose/lattice/screen machinery
needed, just the reflected IR + revealed rows) over the EXACT frozen
76-trap / 21-correct population (`results/mbpp_arc3_endgame.json`'s
`full_r3` rows, the SAME population `arc4_structural_verdicts.py` measured)
and compares every id list against `results/arc4_structural_verdicts.json`'s
own `per_detector` block.

| detector | trap ids match | FP ids match |
|---|---|---|
| D1 memo_lookup_table | **exact** (14/76) | **exact** (0/21) |
| D2 dead_code_free_vars | **exact** (5/76) | **exact** (0/21) |
| D3 unread_declared_param | **exact** (22/76) | **exact** (3/21 = [397, 404, 433]) |

Zero divergence — every trap id and every false-positive id byte-matches
the frozen measurement's own lists (`test_rederivation_trap_ids_match_
frozen_measurement` / `test_rederivation_false_positive_ids_match_
frozen_measurement`, parametrized over d1/d2/d3).

---

## 3. A false positive found DURING this landing, fixed before it shipped

The frozen reference script's own `_BINDING_TYPES` tuple (and my first
graph-native transliteration of it) covers only the Prog*-STATEMENT
binders (param/assign/for-loop/tuple-unpack/except-var/comprehension-var).
Neither the frozen measurement nor my first draft accounted for the plain
DSL HIGHER-ORDER-FUNCTION terms (`Filter`, `Exists`, `Sum`, `Prod`,
`MinOver`, `MaxOver`, `Argmax`, `Argmin`, `ArgminUnique`, `ArgminRefusal`,
`Fold`, `MapList`, …), which ALSO bind an iteration variable — via a
`var_name` (and, for `Fold`, `acc_name`) SCALAR ATTR, not a Prog*-typed
binding node.

This never showed up against the FROZEN 76/21 population (captured before
Arc4 S1/S4 landed 11 new enumerable ops), so the re-derivation gate above
is unaffected. It DID show up live: measured against the CURRENT MBPP
battery (`mbpp_arc3_battery.run_pass`, live, full 257-task test split,
`full_r3` arm), tasks 90 ("length of the longest word" —
`MaxOver(MapList(a, var_name='__item', CaseFold(item)), var_name='__item',
Count(item))`), 132 ("tuple to string" — `Fold(a, acc_name='__acc',
var_name='__item', StringConcat(acc, item))`), and 410 ("min of a
heterogeneous list" — `MinOver(a, var_name='__item', item)`) — all three
`pass`-labelled, all three CORRECT programs — were false-flagged by D2:
`__item`/`__acc` were treated as free (never bound) because the walk only
knew about Prog*-typed binders.

**Fix:** `_st_bound_names` now ALSO binds any node's `var_name`/`acc_name`
attr value, regardless of Term type — a FIELD-NAME-keyed rule (this
codebase's own consistent naming convention for "the bound iteration
variable") rather than an enumerated type list, so it covers every current
HOF term uniformly and does not need updating when a new one is added.
Re-verified: the frozen-population re-derivation (§2) is byte-identical
before and after the fix (the frozen population never used these terms);
the three live false positives (90, 132, 410) are gone
(`ps_st_fired_detectors == ()` on all three, confirmed live).

This is exactly the false-positive discipline
`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §2.1 already modelled for
D1's single-return guard: **a detector that flagged correct programs was
found, measured, and fixed before being reported, not smoothed over.**

---

## 4. Reject-before-accept routing — a real stall found, and why 'gapped' directly

**First attempt (reverted):** route a structurally-rejected candidate
through the SAME `status='counterexample'` state a genuine failing row
already produces, letting the existing `ps_exclude_failed`/
`ps_reproposal`/`ps_ce_exhausted` machinery exclude the construction and
retry. Measured LIVE against the real MBPP battery, this STALLED: task 267
(retrieved via `pr_ladder_accept` — no codebook construction ever matched
this goal's tokens, which is WHY it fell to retrieval in the first place)
got excluded, re-armed to `pending`, and `ps_propose` had nothing else to
propose — `failure_reason: pipeline_stall_nonterminal_status`, `status:
verified` forever, well past the pump's `max_rounds`. The retry/exclude
lane's own state machine was built and tested around a codebook/enumerate
construction NAME being excludable and re-decidable; it is not universally
safe for every rung a structurally-rejected candidate might have come from.

**Landed design:** `ps_structural_reject` routes DIRECTLY to `status
'gapped'` (`ps_gap_reason := 'structural_verdict_reject'`) — the existing
`ps_gap_file`/`ps_gap_dedup_mark` rules (unchanged) then file the standing
`SelfConcern` exactly as any other gap does. "Gaps" is an explicitly
honest outcome per the plan's own framing ("falls to the next rung /
gaps"), and going straight there is a NO-PARK guarantee independent of
which rung produced the candidate — verified live: the 257-task battery
re-run below shows **zero** goals left at a non-terminal status.

**Scope narrowing this required, and why it costs nothing measured:** a
top-level goal that engaged descent (`ps_rung_descend==1.0`) is ALSO
excluded from this rung entirely (`compute_structural_facts` returns
`False`; `ps_accept`'s `Or` guard gained a third arm, `Eq(ps_rung_descend,
1.0)`, so such a goal is never gated). This was necessary because the
P7-B repair lane deliberately accepts a plausibly-overfit descend/fold-up
candidate FIRST and corrects it via LOCALIZED counterexample repair when a
real held-out row is fed back
(`tests/test_prog_repair_migrated.py::test_headline_la10_converts_to_
holdout_ok_via_repair` and siblings) — a strictly MORE TARGETED correction
than this rung's blunt reject-to-gapped, so this rung stands down and lets
repair do its own, better job. Checked against the measured catalogue: the
34 structural-killable ids in `results/arc4_structural_verdicts.json`
include zero descend-engaged accepts (the frozen population's own
`construction`/`enumerate_outcome` fields confirm every measured hit is a
FLAT codebook/enumerate/retrieval accept), so this scoping costs nothing
against the phase's own measured target.

---

## 5. The honest-score section (read twice, per the brief)

Measured LIVE (not from a frozen artifact — `mbpp_arc3_battery.run_pass`,
single pass, `full_r3` arm/protocol, the full 257-task MBPP TEST split,
imported/not modified) with the SEED SWAPPED between v1.6.0 (before, this
phase's own git-HEAD baseline) and v1.7.0 (after, this landing) — the ONLY
file that changed between the two runs was `seeds/program_synthesis.json`;
`domains/prog_synthesis.py`'s `compute_structural_facts` was present in
BOTH runs (it is dispatched every time a goal reaches `status=='verified'`
regardless of seed version, but with v1.6.0's seed there is no
`ps_structural_reject`/`ps_structural_clear` rule to read its facts, and
`ps_accept`'s own `where` does not check `ps_structural_reject` at all, so
the v1.6.0 run reproduces pre-S2 behaviour byte-for-byte — confirmed: it
matches the population `arc4_structural_verdicts.py`'s own `condition.
engine_drift` note already recorded, "104 accepted_holdout_fail / 30 pass",
exactly).

| | before (v1.6.0) | after (v1.7.0) |
|---|---|---|
| `pass` | **30** | **28** |
| `accepted_holdout_fail` | **104** | **78** |
| `gapped:structural_verdict_reject` | 0 | **28** |
| `gapped:enumerate_failed` | 112 | 112 |
| `gapped:no_shape` | 5 | 5 |
| `runner_exception:TypeError` | 3 | 3 |
| `gapped:exhausted` | 2 | 2 |
| `not_recognized` | 1 | 1 |
| **total accepted (pass + accepted_holdout_fail)** | **134** | **100** |
| pass rate (pass / 257 runnable) | 11.67% | **9.73%** |

**Pass rate went DOWN (30→28, 11.67%→9.73%). This is the correct outcome
and it is not being tuned away.** A task-by-task diff (all 257 ids,
before vs after) shows **exactly 28 changes, every single one a
transition to `gapped:structural_verdict_reject`, and zero other outcome
changes anywhere** (no task moved between any two OTHER outcome buckets —
the scoping in §4 cost nothing beyond the 28 intended catches):

- **26 genuine `accepted_holdout_fail` traps correctly caught**: 14, 58,
  68, 83, 86, 93, 103, 109, 125, 126, 164, 228, 239, 242, 247, 269, 285,
  304, 396, 414, 420, 427, 430, 432, 434, 454.
- **2 genuine-defect-rejections from the `pass` population**: **397**
  (median-of-three via `max(a,b)`, `c` unread) and **404**
  (minimum-of-two via bare `return a`, `b` unread) — both independently
  re-verified on a hand-constructed witness input (never a held-out row):
  397 on `(a=1,b=5,c=3)` returns 5, true median is 3; 404 on `(a=5,b=1)`
  returns 5, true min is 1 (`tests/test_verdict_discrimination_migrated.
  py::test_d3_known_false_positives_are_genuine_defects_on_a_fresh_
  witness`, reusing the exact witnesses `PROGRAM_SYNTHESIS_ARC4_
  STRUCTURAL_NOTES.md` §2.2 hand-verified).
- **0 true regressions** — no task that was genuinely correct moved to
  `gapped:structural_verdict_reject` (confirmed both by the live diff
  above and by the precision re-derivation in §2, which shows D3's ONLY
  three false positives against the frozen 21-`pass` population are
  exactly the three known label-noise ids).

**A condition, stated plainly (per this repo's own "quote the condition"
discipline):** the brief's own three named label-noise ids are 397, 404,
**433**. On the FROZEN population, all three are D3 false positives
(`results/arc4_structural_verdicts.json`). On the CURRENT LIVE population,
**433 is no longer even a `pass`-population member with the old defect** —
Arc4 S1/S4 already regenerated a DIFFERENT, better candidate for it
(`b > Count(a)`, which genuinely reads `a` via `Count`'s own source, unlike
the frozen `return b > 4`) between the frozen measurement and this
landing, for reasons unrelated to this phase. D3 correctly does NOT fire
on the live 433 — that is the detector agreeing with a program that is
now actually correct, not a missed catch. This is recorded here rather
than silently reusing the frozen number, per the same discipline that
retracted this file's own count-shaped baseline claims before.

---

## 6. What remains in the 36/76 (47.4%) honest residual

Unchanged from `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §3 — this
phase LANDS three of the seven measured detectors as rules; it does not
raise the measured ceiling itself (that was §3's own job, already done).
36/76 traps on the FROZEN population have accepted IR with no dead code,
no unread/independent inputs, no vacuous guard, no arity defect, no
lookup-table shape, AND render/execute consistently everywhere, match
their own revealed rows' types, and violate none of five invariance
checks — genuine arithmetic/logic errors (e.g. 61, 62, 100, 129, 407, 461
per S0-A) that need a different signal family (more revealed rows, a
stronger property/verdict discriminator, or search reach itself) than
structural inspection can offer.

---

## 7. Residuals — named, not hidden

**(a) A found-and-fixed detector bug (§3).** `_st_bound_names` was missing
the DSL HOF terms' `var_name`/`acc_name` binding — fixed before landing;
documented above rather than smoothed over.

**(b) Full-sweep failures OUTSIDE this phase's file-ownership boundary.**
This phase's file ownership is `seeds/program_synthesis.json`,
`domains/prog_synthesis.py`, `tests/test_program_synthesis_migrated.py`,
and the two new files. Ten tests in OTHER `_migrated` files regressed and
CANNOT be fixed from within that boundary (their pins live in files this
phase is not authorised to edit). Categorised honestly:

  - **Pure version/rule-count pins (2, no behavioural content)**:
    `test_budget_isolation_migrated.py::test_seed_version_and_isolation_
    lanes_present` and `test_retrieval_migrated.py::test_attempt1_
    codebook_screen_rules_stay_absent_from_the_seed` assert an exact seed
    rule count/name-list that predates this phase's 2 new rules (58→60).
    Not a regression — a stale literal count in a file outside this
    phase's ownership.
  - **Genuine MBPP improvement, pin unreachable (3)**:
    `test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_
    outcome_live[242|284|414]` — all three ids are in this phase's own
    measured `structural_killable_ids` (§2); their "measured outcome"
    pin needs updating to reflect the now-correctly-rejected outcome, the
    SAME direction as task 267 in `test_mbpp_baseline_migrated.py` (which
    this phase's file list also cannot touch, for the same reason).
  - **A minor downstream label change (1)**:
    `test_arc4_probe_migrated.py::test_pinned_task_106_reorders_and_
    mutually_exhausts_live` — task 106 is not itself structurally rejected;
    an unrelated enumerate-search `halt_reason` flips from `max_size` to
    `budget` as a second-order consequence of OTHER tasks' search
    dynamics changing earlier in the same population run. Not
    investigated further (outside file ownership either way).
  - **A genuine, systemic architectural tension (4) — the important one.**
    `test_prog_repair_migrated.py::test_refused_localization_falls_to_
    global_cegis_unchanged`, `test_descent_widening_migrated.py::
    test_flat_rung3_accept_converges_via_exclude_powered_retry` +
    `test_enum_round_budget_is_integer_and_forced_exhaustion_falls_
    honestly`, and `test_prog_synthesis_battery_migrated.py::
    test_p7_live_reverify_pinned_task_matches_stored_row[repair_oracle-
    br_10_top_of_three]` all use the SAME canonical fixture shape to
    demonstrate the P7-B CEGIS-repair lane: a decoy candidate that reads
    only SOME of its declared params (e.g. `grab_first_decoy` returns
    bare `a`, `b` unread and varying across the 2 revealed rows; `Max(a,
    b)` ignoring `c`, which also varies) — coincidentally consistent on
    the FEW revealed rows, then corrected via an EXTERNALLY-fed held-out
    counterexample. This is STRUCTURALLY IDENTICAL to D3's own target
    shape (task 397/404's exact pattern) — my detector correctly flags
    it, but doing so PREEMPTS the test's own narrative (it needs to
    observe an intermediate "accepted, wrong" state before it can feed
    the counterexample that exercises repair). This is not a scoping bug
    I can patch further: whether a future `ingest_counterexample` call is
    coming is, by construction, unknowable at the moment a goal reaches
    `verified` — MBPP's real battery (which never calls
    `ingest_counterexample`) and these repair-demonstration fixtures are
    INFORMATION-THEORETICALLY INDISTINGUISHABLE at that point, for any
    rule that only reads graph state. Weakening D3 to dodge this would
    violate the phase's own "do not weaken a detector to preserve a
    number" instruction (the number here is a different test file's pin,
    but the principle is the same). The honest resolution: land the
    detector at full measured strength (as this phase does), and flag
    that a FOLLOW-UP phase, with file access to `tests/test_prog_repair_
    migrated.py`/`tests/test_descent_widening_migrated.py`/`tests/
    test_prog_synthesis_battery_migrated.py`, should update these
    fixtures' pins to reflect the new, earlier, more reliable rejection
    (arguably a BETTER outcome than depending on a lucky externally-fed
    counterexample) — or deliberately construct their decoy fixtures
    from a shape structural inspection cannot see (e.g. a genuine
    arithmetic error), if the intent is specifically to exercise repair
    in isolation from this rung.

**Full sweep, honestly reported:** `program_synthesis` (17/17),
`structural_verdicts` (21/21, frozen, unchanged), `verdict_discrimination`
(24/24, new), and the broader battery run together — 296 passed / 10
failed across all 16 named suites, the 10 as categorised above. Every
suite this phase's own files could make green is green.

---

## 8. Files

`seeds/program_synthesis.json` (v1.6.0 → v1.7.0, 58 → 60 rules:
`ps_structural_reject`/`ps_structural_clear` new, `ps_accept` edited in
place, one new production `Goal -has_structural_rejection-> Rejection`),
`domains/prog_synthesis.py` (new: `_st_hashable`/`_st_walk`/`_st_has_type`/
`_st_var_refs`/`_st_bound_names`/`_st_returns`/`_st_single_child`/
`_st_is_equality_like_literal_test`/`_st_literal_dispatch`/`_st_params`/
`compute_structural_facts`, registered in `_DISPATCH`; `read_goal` gained
a `structural`/`rejections` read-back section), `tests/test_program_
synthesis_migrated.py` (rule-count pin 58→60), NEW `tests/test_verdict_
discrimination_migrated.py` (24 passed, ~1.3s), this file.
