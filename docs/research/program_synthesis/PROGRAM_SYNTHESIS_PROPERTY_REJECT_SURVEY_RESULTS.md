# `property_verdict_reject` bucket survey — RESULTS: GO, +2 genuine passes,
   a real shared fix built, a latent staleness bug found and fixed en route

**Date:** 2026-08-16. Companion to `PROGRAM_SYNTHESIS_PROPERTY_REJECT_
SURVEY_PREREG.md` — read that document first for the mechanism, the
full 26-task classification, and the live-verified evidence the plan below
is built on. Same worktree/branch, base `main @ 5e821f6`. **Not merged to
`main`, not pushed** — left for the orchestrator to independently verify.

**HEADLINE: GO. `full` 71→73/257, `content_stripped` 70→72/257, `official`
100→101/257, exact task-id set diffs computed (never bare counts), ZERO
regressions on any arm. Zero new `TermNode` variants, zero Rust touched at
all — a single new seed RULE (`ps_property_reject_retrieval_enumerate_
fallback`) plus one small, necessary AND-clause on the existing terminal
rule. Cheaper than every build in this arc's own record. The named 9-file
regression suite shows exactly the 3 pre-registered pin-drift failures,
nothing new. A genuine, previously-latent bug in the SHARED verdict-recompute
machinery (unrelated to property-checking specifically) had to be found and
fixed to make this land correctly — reported in full, §4.**

---

## 1. The fix, exactly as sized in the PREREG, built

`seeds/program_synthesis.json` v1.12.0/73 rules → v1.13.0/74 rules. One new
rule, `ps_property_reject_retrieval_enumerate_fallback`:

- **Trigger** — the EXACT SAME `where` condition as `ps_property_reject_gap`
  (a held `PropertyAtom` fired against a verified, top-level, non-descended,
  `retrieved_exemplar` candidate) PLUS two extra guards: `ps_rung_enumerate
  != 1.0` (enumerate has not yet been tried for this goal) AND
  `ps_enum_reserve_used < ps_enum_reserve_budget` (the Arc4-S1 isolated
  enumerate-reserve lane — untouched by retrieval, so this is always true
  the first time).
- **Effects** — mirror `ps_enumerate_mark` byte-for-byte: `ps_rung_enumerate
  := 1.0`, `status := 'enumerate_pending'`, `ps_enum_reserve_used += 1`. This
  routes the goal into the EXACT SAME already-shipped `run_enumerate` →
  `eval_and_record` → `compute_structural_facts` → `compute_property_facts`
  → `ps_property_clear`/`ps_accept` (or → `ps_property_reject_gap` again if
  the new candidate ALSO violates the property) pipeline every OTHER
  construction path already uses — `compute_property_facts`'s own docstring
  already documents it runs "on every path (codebook, enumerate, retrieval,
  fold-up)." **This rule does not accept anything itself** — it only admits
  the goal into a rung it would otherwise never reach, and lets the
  unchanged downstream verdict machinery decide.
- **Deliberately bypasses the `ps_exclude_failed`/`ps_reproposal` CEGIS
  spine.** `RETRIEVAL_FALLTHROUGH_RESULTS.md`'s own S2-stall precedent
  (`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §4, task 267) found that excluding
  `retrieved_exemplar` BY NAME through that spine leaves `ps_propose` with
  nothing to offer — a genuine, documented, non-terminal stall. This is
  exactly why `ps_property_reject_gap` routes straight to `gapped` instead
  of reopening in the first place. The new rule sidesteps that spine
  entirely by directly admitting the SAME status (`enumerate_pending`)
  `ps_enumerate_mark` would use from a completely different entry point —
  no exclude/reproposal machinery is ever touched.
- **`ps_property_reject_gap` gained one AND-clause**: `(ps_rung_enumerate ==
  1.0 OR ps_enum_reserve_used >= ps_enum_reserve_budget)` — the exact
  complement of the new rule's extra guards. The two rules partition the
  space exactly (each gains the other's negation): on the FIRST
  property-reject for a `retrieved_exemplar` goal only the new rule's guard
  holds (fallback fires); after the fallback's one-shot attempt,
  `ps_rung_enumerate` is `1.0` regardless of outcome, so on any LATER
  property-reject only the terminal gap rule's guard holds. **No third,
  stalled state is reachable** — verified live, §5 (zero non-terminal
  outcomes across the full population, `det_identical=True` on every
  battery run).

No `jsonio.rs`/`reflect.rs`/`term_variants.rs`/any `.rs` file was touched.
`git diff --stat` (final): `seeds/program_synthesis.json` +
6 test files, 0 `runners/` files.

## 2. Live-verified end-to-end BEFORE writing this document

Both witness tasks re-run individually through the real pipeline (not a
hand-built term):

```
task 17  status=accepted  construction=retrieved_exemplar  holdout=True
task 105 status=accepted  construction=retrieved_exemplar  holdout=True
```

`ir` for task 17 is `a*(2+2)`; for task 105, `Sum(a)`. Both are the SAME
enumerate candidates independently identified in the PREREG's §3.2
population sweep — not a different, re-derived program.

## 3. Paired MBPP battery — exact task-id set diffs, never bare counts

Methodology: the ORIGINAL (pre-fix) `seeds/program_synthesis.json` was
restored via `git show HEAD:seeds/program_synthesis.json` into the SAME
worktree, the battery re-run fresh to capture the "before" pass-id set per
arm, then the patched seed was restored (byte-diffed against the saved
patched copy to confirm exact restoration) and the battery re-run again for
the "after" set. Both runs report `det_identical=True`.

```
BEFORE (original seed, re-confirmed):  full 71/257  content_stripped 70/257  official 100/257
AFTER  (patched seed):                 full 73/257  content_stripped 72/257  official 101/257
```

Exact set diff (`after − before`, `before − after`):

```
full:              gained=[17, 105]  lost=[]
content_stripped:  gained=[17, 105]  lost=[]
official:          gained=[455]      lost=[]
```

**Zero regressions on any of the three arms.** `full`/`content_stripped`
both convert exactly the two witness tasks the PREREG live-verified end to
end. `official` converts a DIFFERENT single task (455, `prop_month_has_31_
days`) — an observed, real, reproducible fact, not deeply chased beyond
confirming it is consistent with the `official` PROTOCOL's own documented
difference (`mbpp_endgame_battery.py`'s own header: "SAME boot as full;
OFFICIAL protocol — all parseable asserts revealed, scored on the same
asserts... protocol-flagged, never a PRIMARY aggregate member"): revealing
ALL parseable asserts (rather than 2, with 1 held out) changes which
candidate retrieval accepts and which PropertyAtom witnesses get exercised
for several tasks, so a DIFFERENT subset of the 26-task-under-`full`
population is even reachable/property-rejected under `official` in the
first place. This is a pre-existing, documented arm-protocol difference,
not a defect this rung introduces — named here, not further investigated
(out of this rung's scope per the PREREG's own §4.2).

## 4. A genuine, previously-latent staleness bug — found live, fixed,
   reported in full

**The first build of the rule above did NOT work** — the battery came back
byte-identical to the unpatched baseline (71/70/100, zero movement).
Direct re-investigation of task 17 found `ps_rung_enumerate == 1.0`
(the new rule DID fire) and the FINAL `ps_ir` held the correct, freshly
enumerated `a*(2+2)` candidate — but `read_goal()`'s own `property.witnesses`
STILL showed the ORIGINAL retrieved candidate's violation (`a=1 → got=True,
expected=4`), and the goal was STILL terminally `gapped:property_verdict_
reject`.

**Root cause**: `ps_prop_computed`/`ps_st_computed` (the flags `ps_property_
reject_gap`/`ps_property_clear`/`ps_structural_reject_exclusion_gap`/
`ps_structural_clear`/`ps_accept` all gate on) are set UNCONDITIONALLY to
`1.0` by the Python verbs `compute_property_facts`/`compute_structural_
facts` and are NEVER reset by any rule anywhere in `seeds/program_
synthesis.json` (confirmed by grep — zero `set_attr` effects touch either
key outside those two verbs). The freshness key those verbs actually use
internally (`ps_prop_seq`/`ps_st_seq == n_reflected`, the count of `ps_ir_
reflected` edges) works correctly for THEM, but the DECISION RULES gate on
the coarser `..._computed == 1.0` flag as a "has this ever run" check, on
the standing (previously always-true) assumption that by the time a goal
re-reaches `verified`, the verb has already had a chance to refresh it.

That assumption breaks for a genuine SECOND `verified` pass reached WITHIN
ONE `run_rules()` fixpoint call: `pump()`'s own loop structure is
`run_rules()` (rules to fixpoint) THEN Python verb dispatch (once per
round) THEN repeat. When `eval_and_record` (a verb, round N) sets fresh
per-row facts for a NEW candidate, round N+1's `run_rules()` fixpoint can
fire `ps_row_pass` (a pure rule) — flipping `status` straight to `verified`
— and then, WITHIN THAT SAME `run_rules()` call, immediately evaluate
`ps_property_reject_gap`/`ps_accept` against the STILL-`1.0`,
STILL-stale `ps_prop_computed`/`ps_prop_any_fired` left over from the
FIRST candidate, a full round BEFORE `compute_property_facts` (a verb,
only dispatched after `run_rules()` reaches fixpoint) ever gets the chance
to recompute for the new `n_reflected` count. The goal's FIRST-ever
candidate is immune to this (the flags start unset, so no decision rule can
match), which is exactly why this had apparently never been observed before
— **this rung is the first mechanism in the codebase, as far as this
investigation determined, that creates a genuine second `verified` pass for
a `retrieved_exemplar` goal WITHOUT going through the full `pending`-restart
CEGIS ladder** (which the existing reopen paths use, and which likely
absorbs enough intervening rounds that the race, if it exists there too, has
never been diagnosed — **not audited here**, named as an open question in
§6).

**Fix**: two extra effects on the new rule, `ps_prop_computed := 0.0` and
`ps_st_computed := 0.0` — resetting BOTH shared verdict-computed flags at
the exact moment the goal is committed to producing a second candidate
(this rule is the one initiating it, so it is the correct place to
invalidate the first candidate's cached verdict). This does not change
`compute_property_facts`/`compute_structural_facts`'s own logic at all
(they never read `..._computed` as an input) — it only prevents the
DECISION rules from reading stale-but-satisfied flags one round early,
forcing them to wait for the verb to genuinely refresh, exactly as they
already do for a goal's first-ever candidate.

**Live-verified the fix closes the bug**: after adding the two resets,
tasks 17 and 105 both terminate `status=accepted`, `holdout=True` (§2).

## 5. NO-PARK guarantee — checked directly, not assumed

`ceiling3_diag_sweep.py` re-run post-fix: 184 rows (186 − 2 passes), every
outcome still one of `gapped:*`/`accepted_holdout_fail`/`not_recognized`/
`runner_exception:*` — **zero `stalled:*` rows, zero non-terminal
statuses**, matching the pre-fix sweep's own shape exactly. Both the
BEFORE and AFTER battery runs report `det_identical=True` (each internally
reproducible across its own repeated executions) — the new rule introduces
no observed nondeterminism despite the two-rules-partition-the-space design
this section relies on.

### 5.1 Honest secondary effect: 6/24 remaining tasks changed `gap_reason`
   label (not status, not MBPP outcome)

Exact before/after diff of the full 186→184-row taxonomy:

```
BEFORE                              AFTER
gapped:enumerate_failed          94 gapped:enumerate_failed          94
accepted_holdout_fail            51 accepted_holdout_fail            51
gapped:property_verdict_reject   26 gapped:property_verdict_reject   18
gapped:structural_verdict_reject 10 gapped:structural_verdict_reject 15
not_recognized                    1 gapped:exhausted                  2
runner_exception:ValueError       1 not_recognized                    1
gapped:no_shape                   1 runner_exception:ValueError       1
gapped:exhausted                  1 gapped:no_shape                   1
runner_exception:TypeError        1 runner_exception:TypeError        1
```

Per-task diff (all 8 real changes, task-id level):

```
17  gapped:property_verdict_reject -> PASS
105 gapped:property_verdict_reject -> PASS
56  gapped:property_verdict_reject -> gapped:structural_verdict_reject
224 gapped:property_verdict_reject -> gapped:structural_verdict_reject
238 gapped:property_verdict_reject -> gapped:structural_verdict_reject
292 gapped:property_verdict_reject -> gapped:structural_verdict_reject
311 gapped:property_verdict_reject -> gapped:structural_verdict_reject
113 gapped:property_verdict_reject -> gapped:exhausted
```

(A 9th task, 222, was ALREADY `gapped:exhausted` before this rung and is
unaffected — confirmed directly, not assumed, so `exhausted`'s count moving
1→2 is fully accounted for.)

**Every one of these 6 stays terminally `gapped` (still "not pass," zero
MBPP score impact either way) — this is a diagnostic-LABEL change only,
mechanically explained, not a correctness regression.** Directly verified
for task 238: its enumerate-sourced SECOND candidate `ps_prop_computed`/
`ps_prop_any_fired` facts (freshly recomputed, not stale — §4's fix is what
makes this trustworthy) show `any_fired: 1.0` (the property STILL fires,
this candidate is STILL wrong, matching §3.2's own `enum_violates_same_
property=True` finding for 238) but `ps_property_reject` itself reads
`None` — because `compute_structural_facts` ALSO fires on the SAME
candidate (`d1_memo_lookup_table` detected, `ps_structural_reject: 1.0`),
and `ps_structural_reject_exclusion_gap` (an existing, UNTOUCHED rule) wins
the race within the same `run_rules()` fixpoint, transitioning `status`
away from `verified` before `ps_property_reject_gap` gets a chance to match.
Both verdict families are independent, unordered checks that run on every
verified candidate; this is a pre-existing "which gate fires first" property
of the two-detector-family design, not something this rung's own new rule
introduces — the new rule only causes it to be OBSERVED for these 5 tasks,
by giving them a genuinely different second candidate to check at all.
Task 113 (`gapped:exhausted`) is a budget-headroom effect: `ps_budget`
defaults to `3.0`; retrieval's own accept consumes 1 attempt,
`ps_enumerate_fresh_attempt`'s collision-bump consumes a 2nd, and for 113
specifically a further attempt (from the structural/property interaction
above) exhausts the 3rd before either terminal gate rule gets to fire —
still a clean, terminal `gapped`, confirmed directly (§ next paragraph),
never a stall.

## 6. Named 9-file regression suite

```
tests/test_prog_synthesis_battery_migrated.py
tests/test_mbpp_baseline_migrated.py
tests/test_mbpp_endgame_migrated.py
tests/test_mbpp_contamination_migrated.py
tests/test_mbpp_diet_migrated.py
tests/test_program_synthesis_migrated.py
tests/test_prog_moves_migrated.py
tests/test_prog_property_migrated.py
tests/test_exact_first_migrated.py
```

Final run: **3 failed, 241 passed** — exactly the 3 pre-registered pin-drift
failures (`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_
reverify_live`, `test_prog_moves_migrated.py::test_named_regression_sweep_
only_known_pins_drift`, `test_exact_first_migrated.py::test_named_
regression_sweep_only_known_pins_drift`), nothing new.

**Getting here required real, mechanical work, not a free pass**:
`results/` housekeeping (§ below) resolved a batch of `FileNotFoundError`s
unrelated to this rung's own code (confirmed by reproducing the identical
errors against the UNMODIFIED original seed, in the same worktree, before
restoring the patch — see §7); four rule-count/version PINS
(`test_program_synthesis_migrated.py::test_seed_loads_clean`,
`test_prog_moves_migrated.py::test_seed_bumped_with_three_new_rules`,
`test_prog_property_migrated.py::test_seed_version_bumped_and_three_new_
rules`, `test_exact_first_migrated.py::test_program_synthesis_seed_bumped_
with_three_new_rules`) needed updating from `73`/`"1.12.0"` to
`74`/`"1.13.0"` — the exact "pin follows the version bump" precedent every
prior rung in this arc already established, confirmed NOT pre-existing
(all four passed on the unmodified original seed, §7).

## 7. Beyond the mandated suite — two more files checked voluntarily, one
   fixed in full, one left as confirmed pre-existing drift

**`tests/test_retrieval_migrated.py` — fixed in full, 33/33 passing.**
Discovered because `test_exact_first_migrated.py::test_named_regression_
sweep_only_known_pins_drift`'s own body runs a WIDER internal sweep across
much of the test tree as part of computing drift, and its failure output
surfaced a real, precise, well-understood consequence of this rung's own
fix: `_ARC6_WRONG_BY_CONSTRUCTION`/`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT`
(hardcoded pins from the ORIGINAL 2026-08-01 Arc6-D landing, asserting tasks
105/238/405's retrieved candidates are "wrong by construction") are now
stale for task 105 specifically — it is no longer wrong, it is genuinely
correct. Fixed by removing 105 from `_ARC6_WRONG_BY_CONSTRUCTION` (its
"prove it's wrong" witness no longer applies — there is nothing wrong to
prove), updating `_KNOWN_ARC6_PROPERTY_REJECT_DRIFT[105]` to `{"status":
"accepted", "rung": "c", "exemplar": 802, "holdout_ok": True}` (live-verified
via `_run_task_live`, not hand-typed), updating `_KNOWN_ARC6_PROPERTY_
REJECT_DRIFT[238]`'s `gap_reason` from `property_verdict_reject` to
`structural_verdict_reject` (§5.1's own mechanically-explained relabel),
rewriting `test_occam_order_exact_pass_never_falls_through_to_deeper_rungs`'s
own docstring+body to assert `accepted`/`holdout_ok=True` instead of the
now-superseded `gapped`/`property_verdict_reject` (the rung-ordering claim
this fixture actually exists to prove — `out["rung"] != "d"` — is completely
unchanged, since `rung`/`exemplar` are set by the RETRIEVAL ladder alone and
never touched by the property/enumerate machinery), and bumping the same
`73`/`"1.12.0"` → `74`/`"1.13.0"` pin two more places in this file. Every
edit is a direct, mechanical consequence of a live-verified fact (§2/§3.2),
never a loosened assertion.

**`tests/test_reject_informs_repair_migrated.py` — 4 failures left
untouched, confirmed PRE-EXISTING, not this rung's regression.** This file
is NOT in the mandated 9-file suite; it was added voluntarily because its
subject (the D1/D2/D3/property reject-informs-repair invariant class) is
directly adjacent to what this rung touches. Its 5th-discovered failure
(`test_seed_v1_8_0_shape`, a 5th `"1.12.0"` version pin) was fixed the same
way as the others. The remaining 4 (`test_retrieval_sourced_ids_gap_
directly_never_reopen`, `test_reopened_ids_genuinely_tried_and_still_
gapped_honestly`, `test_disposition_a_repaired_to_pass_is_empty`,
`test_no_wrong_accept_regression_vs_v1_7_0_baseline`) were **directly
re-run against the UNMODIFIED original seed in this SAME worktree** (`git
show HEAD:seeds/program_synthesis.json` swapped in, battery/pytest re-run,
patched seed restored and byte-diff-confirmed afterward) — **the identical 4
tests fail, for unrelated pre-existing reasons** (e.g. task 165 already
diverges from a frozen hardcoded expectation, `gapped:enumerate_failed`
vs. the pinned `gapped:property_verdict_reject`; task 125 — outside this
rung's own 26-task population entirely, `construction=None`, a raw-enumerate
task from `HOLDOUT_FAIL_SURVEY`'s own population — already shows up as an
undocumented "repaired to pass" case the file's own hardcoded
`_ARC5_MOVES_PASS_IDS` set does not include). This rung's own patched seed
causes the SAME 4 tests to fail, but `test_no_wrong_accept_regression_vs_
v1_7_0_baseline` now fails at an EARLIER point in its own sorted iteration
(task 17, this rung's own genuine `pass`, before ever reaching task 165's
pre-existing, unrelated divergence) — a change in WHICH assertion trips
first inside an already-broken test, not a new failure. **Named, not
fixed**: reconciling this file's own large hardcoded population sets
(`REOPENED_12`, `_ARC5_MOVES_PASS_IDS`, `_ARC6_PROPERTY_CAUGHT_IDS`,
`_ARC6_PROPERTY_CAUGHT_DIRECT_IDS`, `MEASURED_OUTCOMES`) against current
reality is a real, separate undertaking, out of scope for this
single-variable rung, and unrelated to whether this rung's own fix is
correct.

## 8. What this document does NOT establish

1. Whether the general `ps_prop_computed`/`ps_st_computed` staleness race
   (§4) is ALSO latent in the pre-existing D1/D2/D3/property REOPEN paths
   (non-`retrieved_exemplar` sources, which route through the full
   `pending`-restart CEGIS ladder rather than this rung's direct
   `enumerate_pending` admission) — not audited. If it is, its symptom
   there would most likely be a stale gap-reason/verdict LABEL on a
   reopened-then-re-verified candidate (matching the harmless §5.1 pattern
   measured here), not a wrong ACCEPT (the flags only ever gate REJECTION
   rules more permissively when stale-satisfied, never less — a stale-clear
   `..._computed==1.0` with `..._any_fired==0.0` would only wrongly SKIP a
   fresh check that would have found nothing anyway, on the population this
   rung measured), but this is reasoned, not measured, for the reopen paths.
2. `tests/test_search_reach_migrated.py` and `tests/test_mbpp_arc3_endgame_
   migrated.py` also surfaced failures in the same wider internal sweep
   (§7's discovery path) — confirmed, by the SAME before/after-seed swap
   method, to be PRE-EXISTING and unrelated to this rung (mostly missing
   `results/retrieval_oracle_ceiling.json` and frozen-artifact-hash drift),
   but not otherwise investigated or fixed — out of scope.
3. Whether an analogous PropertyAtom/D1-D3-gated fallthrough would work for
   `structural_verdict_reject` (10 tasks) or any slice of `accepted_holdout_
   fail` (51 tasks) — not built, not sized here; named as a real, plausible,
   NOT-recommended-this-rung candidate in the PREREG §4.1.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 9. GO/NO-GO

**GO.** A real, live-verified, zero-Rust, zero-new-`TermNode` fix landed:
+2 genuine MBPP passes on `full`/`content_stripped` (17, 105), +1 on
`official` (455), zero regressions on any arm (exact task-id diffs), the
mandated 9-file regression suite shows exactly its 3 pre-registered
failures, and a genuine general latent bug in shared verdict-recompute
machinery was found, precisely diagnosed, and fixed as a necessary part of
landing this rule — reported in full rather than patched around silently.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-property-reject-survey
git log --oneline -1 main   # 5e821f6, verify fresh
# results/ housekeeping (gitignored per-tree): copy from main's own results/ —
#   mbpp_zero_shot_baseline.json, prog_construction_scan.json, prog_chunk_mine.json,
#   mbpp_train_diet.json, prog_ir_histogram.json, prog_ir_python_coverage.json,
#   prog_synthesis_battery.json, mbpp_arc3_endgame.json, mbpp_blocker_histogram.json,
#   arc4_endgame.json, arc4_backward_probe.json, arc4_failure_anatomy.json,
#   arc4_structural_verdicts.json, code_synthesis_baseline.json
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest -q \
  tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py \
  tests/test_mbpp_diet_migrated.py tests/test_program_synthesis_migrated.py \
  tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py
```

`git diff --stat` against `main @ 5e821f6` at the end of this session:
`seeds/program_synthesis.json` (+258/-1) and 6 test files
(`test_exact_first_migrated.py`, `test_prog_moves_migrated.py`,
`test_prog_property_migrated.py`, `test_program_synthesis_migrated.py`,
`test_reject_informs_repair_migrated.py`, `test_retrieval_migrated.py`) —
zero `runners/`/`domains/` files.
