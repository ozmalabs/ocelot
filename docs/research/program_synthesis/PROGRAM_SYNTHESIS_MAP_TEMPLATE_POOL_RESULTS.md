# Map-template-pool + list-shaped-branch widening — RESULTS

**Date:** 2026-08-14. Base `main @ c80f24d` ("Correct unintentional-abuser
scoping: intent, not knowledge"), verified fresh via `git log --oneline -1
main` immediately before creating the worktree, per house discipline. Built
and measured in an isolated worktree
(`/home/matt/ozmadev/ocelot-worktrees/progsyn-map-template-pool`, branch
`progsyn-map-template-pool`, commit `3b2e3c0`) — **not merged to `main`**;
left for the orchestrator to independently verify and merge, per this
session's explicit instruction (a sibling agent violated this earlier today
and is not to be repeated).

This document builds exactly what
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §3 priced and
recommended as the next rung ("map-template-pool + list-shaped-branch
widening") — it does not redesign the target, only measures the real,
evidence-gated build against the live 257-task MBPP battery.

**Headline: +3/257 on every one of the three battery arms
(`full`/`content_stripped`/`official`), zero regressions, confirmed by a
real set-diff against a freshly-rebuilt unmodified baseline — not the 8 the
PREREG's own witnesses hoped for.** Newly passing: **tasks 104, 118, 456**
(identical set on all three arms). Tasks 102, 411, 419, 421, 439 do **not**
convert under a measured-safe, narrowly-gated build — this matches the
PREREG's own explicit caveat (§8 item 1: *"the actual converted count after
a real, regression-safe build could be smaller than 8, the same way Rung
1's own +16 inventory ceiling converted only +5"*) almost exactly (3/8
converted here vs. 5/16 there).

---

## 1. What was built

Two kinds of change, exactly the two the PREREG named (§3.3):

### 1.1 Per-element map-template-pool additions (low blast radius)

`map_templates_by_size` (`runners/dsl/src/synth_enumerate.rs`, built inside
the `if map_wanted { ... }` block, ~line 2358) gained five new per-element
template entries, all **appended** after the existing ones (never
interleaved — every pre-existing template keeps its exact arena index, so
any already-shipped `MapList` spec's own enumeration order is byte-
identical to before this rung):

| template | size | gate | line | task |
|---|---|---|---|---|
| `sorted(item)` (widened) | 2 | `set_map_wanted \|\| spec_has_list_of_lists` | 2460 | 104 |
| `reverse(item)` | 2 | `spec_has_string_value \|\| spec_has_string_list_elements` | 2482 | 456 |
| `capitalize(item)` | 2 | `spec_has_string_value \|\| spec_has_string_list_elements` | 2489 | 102/411 (unreached — see §3) |
| `str(item)` | 2 | unconditional under `map_wanted` | 2495 | 439/421 (unreached — see §3) |
| `round(item, c)` | 3 (× `numeric_consts`) | `spec_has_float_value \|\| spec_has_float_list_elements` | 2509 | 419 (unreached — see §3) |

Three new **nested, one-level-down evidence flags** were added
(`synth_enumerate.rs:1848-1884`) because the existing flat evidence tests
(`spec_has_string_value`/`spec_has_float_value`, computed at
`synth_enumerate.rs:1790-1794`) only inspect the TOP-LEVEL env/output value
and miss evidence one level inside a list (e.g. task 456's own input
variable is a `List[Str]`, never a bare `Str`, so `spec_has_string_value`
is `false` for it):

- `spec_has_list_of_lists` (`:1856`) — a list var/output whose own elements
  are themselves list-shaped (task 104, widening the pre-existing
  `set_map_wanted`-only `sorted(item)` gate).
- `spec_has_string_list_elements` (`:1870`) — a list var/output whose own
  elements are all string-shaped (task 456).
- `spec_has_float_list_elements` (`:1878`) — a list var/output containing
  at least one float element (task 419).

These three flags are used **only** to gate `map_templates_by_size` entries
— never `op_list`/`DEFAULT_OPS` — deliberately, because the PREREG's own
cited precedent (Rung 1's `RUNG1_RESULTS.md`, referenced in the code
comment at `:1861-1869`) already measured that this exact "list has string
elements" evidence regresses task 132 when it widens the TOP-LEVEL op
inventory. Confined to the bounded per-element pool, it does not carry that
risk (confirmed in §4 below — task 132 is unaffected).

### 1.2 Top-level `op_list` widening (the real regression-risk piece, per PREREG §3.3 item 2)

- **`DEFAULT_STR_OPS`** (`:475-489`) gained `MapList`/`JoinList` —
  unconditional for every string-shaped spec (the const's own existing gate,
  "every var+output string-typed," is already narrow; no further layering
  was added on top, matching the existing `DEFAULT_STR_OPS` discipline).
  Intended to let a string-shaped spec MAP a per-element transform over
  `Split`'s pieces and rejoin them (tasks 102/411's witness).
- **`Split`** added to the list-shaped branch's `op_list`
  (`:1938`, `if spec_output_is_listlike && spec_has_string_value`) — the
  exact same narrow gate `Sort`/`TUPLE_BUILD_OPS` already use one line
  above, plus the string-content evidence `Round` already uses below (task
  118's witness).
  - Note this gate structurally excludes task 132 (its output is a bare
    `Str`, never listlike, so `spec_output_is_listlike` is `false` for it
    and this arm is never reached) — the same discriminator the PREREG's
    own Rung-1 citation already established as safe.
- **`ParseInt`** added to the list-shaped branch, narrowly gated on
  `!spec_output_is_listlike && spec_output_is_bare_int &&
  !spec_has_string_value && !spec_has_float_value` (`:1970-1981`) — a
  list-shaped spec whose output is a bare `Int` and which carries **no**
  top-level string/float evidence at all (so it never overlaps `Split`'s
  own gate or `Round`'s). Intended for task 439's witness
  (`ParseInt(JoinList(MapList(a,item,Str(item))))`).

---

## 2. Live-verified witnesses (semantic correctness, independent of search reach)

Before touching the search at all, every witness the PREREG cited was
re-verified directly against the task's own real revealed rows via
`substrate_rs.Substrate()._inner.evaluate(term, env)` — the standing
"invocation, not inference" discipline this whole arc uses
(`STRUCTURAL_CEILING.md` §7.3). All eight witnesses evaluate correctly
(exact match on every revealed row):

- 456: `MapList(a, item, Reverse(item))` ✓
- 104: (found live by the search itself, `mck_prog_assign_var_n2_q9`
  construction, not hand-witnessed)
- 439: `ParseInt(Fold(MapList(a,item,Str(item)), acc, "", Concat(acc,item)))`
  ✓ (`Fold` here is the `JoinList` fixed-body shape, field names
  `source`/`var_name`/`acc_name`/`init`/`body`)
- 118: `Split(a, " ")` ✓

This confirms §1's build target was semantically right; §3 below is purely
about whether the SEARCH, under a measured-safe (narrow) op/template
inventory, actually REACHES each witness within budget — the PREREG's own
"reach is not conversion" discount (`STRUCTURAL_CEILING.md` §6.3).

---

## 3. Which of the 8 actually convert — measured per-task, not assumed

Diagnostic re-runs of `domains.prog_synthesis.synthesize_from_request`
directly per task (same harness the PREREG's own §2 diagnostic sweep used),
before and after each incremental change, walked the search space live:

| id | witness | converts? | why / why not |
|---|---|---|---|
| **456** | `MapList(a,item,Reverse(item))` | **YES** | `reverse(item)` template reachable once gated on the nested `spec_has_string_list_elements` evidence (the flat `spec_has_string_value` alone misses it) |
| **104** | (search-found, not the hand witness) | **YES** | widened `sorted(item)` gate (`spec_has_list_of_lists`) — `tested` dropped from 102,313 (budget-exhausted) to 828 (found, size 4) |
| **118** | `Split(a," ")` | **YES** | `Split` reachable via the narrow `spec_output_is_listlike && spec_has_string_value` gate |
| 102 | `JoinList(MapList(Split(a,"_"),item,Capitalize(item)))` | no | `MapList`/`JoinList` now present in `DEFAULT_STR_OPS`, but `distinct` stayed **exactly** 16,049 before and after — the search never even reaches a `MapList`/`JoinList` registration before the 200,000-candidate budget is exhausted by breadth at smaller sizes. Genuinely reachable-in-principle, not reachable-in-budget. |
| 411 | (twin of 102) | no | same as 102 |
| 419 | `Times(Sum(MapList(a,item,Round(item,0))),Count(a))` | no | `round(item,c)` template present (nested float evidence fires), but `tested=200,000` (budget-exhausted) both before and after — same shape as 102/411 |
| 439 | `ParseInt(JoinList(MapList(a,item,Str(item))))` | no | `ParseInt` op added and confirmed present in `op_list` (verified via a temporary debug trace, removed before commit), `Str(item)` template unconditional — but `tested=200,000` (budget-exhausted); the composition is 3 levels deep (~size 9) and never reached before budget runs out |
| 421 | `Fold(MapList(a,item,Str(item)), concat-with-"-")` | no | same budget wall as 439 **and** a second, unpriced gap: there is no DELIMITER-join primitive in `OP_TABLE` — `JoinList` is a FIXED empty-string join (`Fold{...,init:"",body:Concat(acc,item)}`); a `"-"`-joined witness needs either a new op or a different construction this rung does not add |

**3/8 convert. This is a measured result, not an assumption** — every
"does not convert" row above was checked by running the actual search
(`enumerate.tested`/`enumerate.distinct` read back live), not inferred from
the op/template inventory being theoretically sufficient.

---

## 4. Regression discipline — the Rung-1 lesson, walked the same way

Per the PREREG's own instruction to mirror Rung 1's "build → measure →
narrow if regressed" discipline (`STRUCTURAL_CEILING_RUNG1_RESULTS.md`),
every change was evidence-gated from the start (never blanket-appended),
and task 132 — Rung 1's own canary for exactly this class of regression —
was checked explicitly at every step:

- `Split`/`ParseInt` (the two op_list widenings with real regression
  risk) are both gated to exclude task 132 by construction: task 132's
  output is a bare `Str` (not listlike), so `spec_output_is_listlike` is
  `false` and neither gate is ever reached for it.
- `MapList`/`JoinList` in `DEFAULT_STR_OPS` are unconditional for every
  string-shaped spec (task 132 IS string-shaped) — but the live diagnostic
  trace confirmed `distinct` counts for the affected string-shaped tasks
  did not change from these two additions in the runs that mattered
  (they only ever crowd the budget once the search reaches a size these
  two ops would occupy, which — per §3 — it never does inside budget for
  the tasks checked here).

## 5. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (unmodified `c80f24d`, rebuilt from source in a separate
isolated baseline worktree
`progsyn-map-template-pool-BASELINE`, engine hash `3d7535e7481a`):

```
full:              63/257  p=0.245136  ci=[0.196552, 0.301228]  det_identical=True
content_stripped:  62/257  p=0.241245  ci=[0.192996, 0.297116]  det_identical=True
official:          91/257  p=0.354086  ci=[0.298158, 0.414311]  det_identical=True
```

**After** (this rung, engine hash `d7091fb79c52`):

```
full:              66/257  p=0.256809  ci=[0.207253, 0.313529]  det_identical=True
content_stripped:  65/257  p=0.252918  ci=[0.203680, 0.309434]  det_identical=True
official:          94/257  p=0.365759  ci=[0.309252, 0.426219]  det_identical=True
```

**Every task's outcome across all 257 runnable rows was diffed, not just
the pass count**, on all three arms independently:

| arm | n_moved | movement |
|---|---|---|
| full | 3 | 104, 118, 456: `gapped:enumerate_failed` → `pass` |
| content_stripped | 3 | 104, 118, 456: `gapped:enumerate_failed` → `pass` |
| official | 3 | 104, 118, 456: `gapped:enumerate_failed` → `pass` |

No other task's outcome changed on any arm. `before_pass_ids ⊆
after_pass_ids` **confirmed by direct set difference** on all three arms
(`regressed = before_pass − after_pass` is the empty set on every arm).

Exact pass-id sets:

```
full        before (63): 11,16,20,58,59,69,71,74,82,84,85,89,90,98,106,115,120,127,131,132,135,138,139,141,142,145,161,227,230,232,233,234,249,257,266,272,276,278,281,290,309,312,393,394,404,406,410,413,418,428,433,436,443,450,451,457,458,460,472,473,474,475,477
full        after  (66): 11,16,20,58,59,69,71,74,82,84,85,89,90,98,104,106,115,118,120,127,131,132,135,138,139,141,142,145,161,227,230,232,233,234,249,257,266,272,276,278,281,290,309,312,393,394,404,406,410,413,418,428,433,436,443,450,451,456,457,458,460,472,473,474,475,477

content_stripped before (62): 11,16,20,58,59,69,71,74,82,84,85,89,90,98,106,115,120,127,131,132,135,138,139,141,142,145,161,227,230,232,233,234,249,257,266,272,276,278,281,290,309,312,393,394,404,406,410,413,418,428,433,436,443,450,451,457,458,460,472,474,475,477
content_stripped after  (65): 11,16,20,58,59,69,71,74,82,84,85,89,90,98,104,106,115,118,120,127,131,132,135,138,139,141,142,145,161,227,230,232,233,234,249,257,266,272,276,278,281,290,309,312,393,394,404,406,410,413,418,428,433,436,443,450,451,456,457,458,460,472,474,475,477

official before (91): 11,14,16,17,19,20,58,62,66,68,69,70,71,82,84,85,89,90,95,98,105,106,115,120,127,131,132,135,138,139,141,142,143,145,161,164,168,171,227,230,232,233,234,249,250,253,257,266,272,276,278,281,284,285,290,294,296,309,311,312,393,394,400,404,406,410,413,414,418,424,425,428,433,434,436,443,446,450,452,457,458,460,461,464,471,472,473,474,475,476,477
official after  (94): 11,14,16,17,19,20,58,62,66,68,69,70,71,82,84,85,89,90,95,98,104,105,106,115,118,120,127,131,132,135,138,139,141,142,143,145,161,164,168,171,227,230,232,233,234,249,250,253,257,266,272,276,278,281,284,285,290,294,296,309,311,312,393,394,400,404,406,410,413,414,418,424,425,428,433,434,436,443,446,450,452,456,457,458,460,461,464,471,472,473,474,475,476,477
```

Newly passing on every arm: **104, 118, 456**. No arm's set diverges from
this — the PREREG's own note that arms "can genuinely diverge on marginal
tasks" did not materialise for this rung (all three moved identically).

---

## 6. Regression suite — the named 9-file MBPP suite + full Rust test suite

**Rust:** `cargo build --release` from source succeeded cleanly (as
documented, `a6f04f3`-era fix holds). `cargo test --lib --release --
--test-threads=1` (using the documented pyo3 linking workaround): **752
passed, 0 failed, 4 ignored** (the 4 ignored are the pre-existing known-
flaky `dim_infer_tests`, explicitly skipped per this session's own
instruction). `synth_enumerate::tests::*` specifically: **21/21 passed**.

**Python, the named 9-file suite**
(`test_prog_synthesis_battery_migrated.py`, `test_mbpp_baseline_migrated.py`,
`test_mbpp_endgame_migrated.py`, `test_mbpp_contamination_migrated.py`,
`test_mbpp_diet_migrated.py`, `test_program_synthesis_migrated.py`,
`test_prog_moves_migrated.py`, `test_prog_property_migrated.py`,
`test_exact_first_migrated.py`): **3 failed / 241 passed** (byte-identical
failure signature to the PREREG's own citation of this exact suite,
§5: *"3 failed / 241 passed, byte-identical failure signature to every
prior rung today"*). Each of the 3 was independently reproduced on a
**freshly rebuilt, unmodified `c80f24d` baseline worktree** (not assumed
stale from a prior doc's characterization, per house discipline #6):

- `test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`
  — task 267's construction pin (`range_sum_spine` expected, `sum_of_two`
  live); the test file's own code comment already documents this as
  "LEFT RED, NOT FIXED, verified pre-existing" since 2026-08-01, outside
  this rung's file-ownership boundary. Reproduced identically on baseline.
- `test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  and `test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`
  — both run the SAME arc-4 regression sweep as a subprocess; both fail
  with the identical 8-node-id "unexpected" set
  (`test_mbpp_arc3_endgame_migrated.py::test_arc2_endgame_artifact_hash_is_unchanged`,
  `test_arc2_full_headline_number_unchanged`,
  `test_retrieval_ceiling_migrated.py::test_q5_failure_coverage_ids_are_a_subset_of_q5_failures`,
  and five `test_search_reach_migrated.py` node ids) on **both** the
  modified worktree and the freshly rebuilt baseline — confirmed
  pre-existing, not caused by this change.

None of these three are new; all three reproduce byte-for-byte on an
unmodified baseline built from source in this same session.

---

## 7. GO/NO-GO

**GO, at the measured (not hoped-for) scope: 3/8 witnesses convert
(104, 118, 456), all three MBPP arms +3, zero regressions, confirmed by a
real set-diff and an independently rebuilt baseline.** This is smaller than
the PREREG's own upper bound (+8) but is a genuine, honestly measured net
gain with no shared-bucket budget-exhaustion side effects on any
currently-passing task — the exact outcome the PREREG's own §8 predicted as
plausible ("the actual converted count... could be smaller than 8").

## 8. What this does NOT establish

1. **102/411/419/439 remain genuinely reachable in principle, not in
   budget.** Their `enumerate.distinct` counts are essentially unchanged by
   this rung's additions, meaning the search never even reaches a
   registration of the new ops/templates before the 200,000-candidate cap
   — this is a budget/size problem, not an inventory problem, and is
   **not** solved by this rung. A future rung would need to either raise
   the budget for specifically-gated specs, or add search-order
   prioritization (try `MapList`/`JoinList`-shaped compositions earlier for
   a spec whose flat op set has already saturated) — neither attempted
   here.
2. **421 additionally needs a delimiter-join primitive that does not
   exist.** `JoinList` is a fixed empty-string join; a `"-"`-delimited join
   needs either a new `TermNode`/op or a different construction path this
   rung does not add. This is a genuinely NEW, unpriced gap the PREREG did
   not call out explicitly (it described 421's witness only informally as
   "concat-with-'-'").
3. **This rung's evidence gates are hand-written, not derived.** The three
   new nested-evidence flags (`spec_has_list_of_lists`/
   `spec_has_string_list_elements`/`spec_has_float_list_elements`) are a
   direct, mechanical generalisation of the existing flat
   `spec_has_dict_value`/`spec_has_string_value`/`spec_has_float_value`
   pattern one grain down — CLAUDE.md's own SHAPES-NOT-NUMBERS section
   would call this exactly the kind of thing that SHOULD eventually be a
   codebook/shape-decode grain (a "does this spec's structure nest one
   level" question is itself a shape question), not three more hand-tuned
   booleans. This rung does not attempt that generalisation — it follows
   the existing hand-gated `synth_enumerate.rs` idiom throughout, matching
   every prior rung in this arc's own style, and names the tension rather
   than resolving it.
4. **Whether any of this reflects real human program-synthesis cognition**
   remains exactly as open as every prior document in this arc left it.
5. **The `retrieved_exemplar` construction label on 456/118's accepted
   programs was not fully traced to its exact internal mechanism.** Both
   converted tasks show `construction: "retrieved_exemplar"` in the
   read-back rather than an `enumerate`-tagged construction, even though
   their witnesses are built entirely from this rung's new `SynthEnumerate`
   templates/ops (confirmed by inspecting the accepted program's IR
   directly, which matches the intended witness term-for-term). This
   suggests the retrieval/codebook rung upstream of raw enumerate shares
   enough machinery with `SynthEnumerate`'s own template/op grammar that a
   newly-reachable shape can be recognized there first — plausible given
   this codebase's own documented pipeline order (codebook → lattice →
   descend → exact → enumerate), but not traced end-to-end in this
   document. The PASS verdict itself (held-out row agreement) is
   independently confirmed by the battery's own `holdout_verdict`, so this
   residual is about attribution/labeling, not correctness.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-map-template-pool
git log --oneline -1   # 3b2e3c0, on top of c80f24d
bash scripts/engine_build.sh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Isolated Rust tests (documented pyo3 linking workaround):
```bash
cd runners/dsl
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1 --skip dim_infer_tests
```

Named 9-file regression suite:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
```
