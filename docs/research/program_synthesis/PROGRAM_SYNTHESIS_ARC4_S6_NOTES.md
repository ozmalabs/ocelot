# PROGRAM SYNTHESIS ARC 4 PHASE S6 — A STRUCTURAL REJECTION INFORMS REPAIR, NOT A TERMINAL

**Date:** 2026-08-01. Closes the arc's named residual
(`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §4, `PROGRAM_SYNTHESIS_ARC4_S5.md`
§7 rank 2): S2's `ps_structural_reject` routed every pre-accept structural
rejection straight to `gapped`, discarding the detector's own precise
fault localisation. `seeds/program_synthesis.json` v1.7.0 → v1.8.0
(60 → 63 rules: the single `ps_structural_reject` is REPLACED by four
detector/source-routed rules; `ps_structural_clear` is untouched).
`domains/prog_synthesis.py` gained one read-back field
(`structural.reopen_count`) — no new adapter decision logic.

---

## 0. The residual, precisely, and why S2's first attempt failed

S2 measured 26 candidates it could correctly reject pre-accept (D1
memo_lookup_table, D2 dead_code_free_vars, D3 unread_declared_param) but
routed every one of them straight to `gapped:structural_verdict_reject`.
S2's OWN first attempt — reuse the standing counterexample/exclude/
reproposal lane for every rejection — was measured live and REVERTED: task
267 is retrieval-sourced (`pr_ladder_accept`; no codebook trigger ever
matched it, which is WHY it fell to retrieval), and EVERY retrieval accept
shares the ONE literal `ps_construction` value `'retrieved_exemplar'`
regardless of which exemplar produced it. Excluding that name blocks
nothing exemplar-specific — the retrieval ladder has no way to know which
candidate the exclusion meant, `ps_propose` had nothing else to try, and
the goal parked at a non-terminal status
(`failure_reason: pipeline_stall_nonterminal_status`).

The fix in this phase is **one condition**, not a rewrite of the reuse
idea: gate reopening on `ps_construction != 'retrieved_exemplar'`. That
literal is set by exactly one rule (`pr_ladder_accept`) and by nothing
else, so it is a clean, mechanical, already-recorded discriminator between
"a rung that can propose something genuinely different once excluded"
(codebook / lattice / enumerate) and "a rung that cannot" (retrieval).

---

## 1. The routing design, per detector, with justification

`seeds/program_synthesis.json` v1.8.0 replaces `ps_structural_reject`
with four rules, each firing on a MUTUALLY EXCLUSIVE combination of
(which detector(s) fired) × (is the source retrieval-sourced):

| rule | detector(s) | source | effect |
|---|---|---|---|
| `ps_structural_reject_exclusion_gap` | D1 and/or D2 | `retrieved_exemplar` | straight to `gapped` (route=`exclusion`, unreachable — same as v1.7.0) |
| `ps_structural_reject_exclusion_reopen` | D1 and/or D2 | anything else | routes DIRECTLY to `status='counterexample'` (route=`exclusion`) |
| `ps_structural_reject_repair_gap` | D3 alone | `retrieved_exemplar` | straight to `gapped` (route=`repair`, unreachable — localisation still recorded) |
| `ps_structural_reject_repair_reopen` | D3 alone | anything else | routes to `'counterexample'` (route=`repair`, `repair_target_param` := the ignored parameter(s)) |

**Priority: D1/D2 dominate D3.** If a candidate fires D1 (or D2) AND D3
simultaneously, it routes as D1/D2 (`exclusion`), never `repair` — a
lookup table that also happens to leave a declared parameter unread is
still "no correct sub-part to salvage," not "one parameter to fix."
Gated directly: `test_d1_and_d3_together_routes_as_d1_exclusion_not_repair`.

**D1 (memo_lookup_table) → `exclusion`.** A pure literal-dispatch table
built from the revealed rows' own output values has no computation to
correct — there is no sub-expression that is "almost right." The honest
response is to retire the WHOLE candidate (exclude it by construction
name) and let `ps_propose` try something else, when something else is
reachable.

**D2 (dead_code_free_vars) → `exclusion`, justified.** A read of a name
that is never bound ANYWHERE in the program is not "a declared input
being ignored" — it names no PARAMETER at all, so there is nothing for a
hole-reopen or a `repair_target_param` to point at. D2 gets the SAME
mechanical treatment as D1 (exclude + reproposal-if-safe), but its
Rejection never carries `repair_target_param` (verified:
`test_d2_only_nonretrieval_routes_exclusion_reopen_justified` asserts
`repair_target_param == []`) — the distinction the brief asked for is
representational (what gets recorded and why), not a different
mechanism, because both share the same root fact: neither detector names
a declared parameter.

**D3 (unread_declared_param) → `repair`.** This is the one detector that
supplies a strictly BETTER diagnosis than any counterexample: it names
*which* declared parameter is ignored (`ps_st_varying_unread_params`)
instead of exhibiting one failing row. That fact is now recorded on the
Rejection as `repair_target_param` and the goal is routed into the same
standing exclude/reproposal lane. This is the residual's own literal ask
("ignores parameter c" should inform repair, not be thrown away) — the
localisation is now on the graph even when it cannot be acted on
(retrieval-sourced) and threaded into the retry when it can be.

### Why this avoids S2's stall — the mechanism, explicitly

S2's reverted attempt routed **every** rejection into
`status='counterexample'` unconditionally. S6 routes into
`status='counterexample'` **only when `ps_construction !=
'retrieved_exemplar'`** — literally the SAME standing lane
(`ps_exclude_failed` / `ps_reproposal` / `ps_ce_exhausted` /
`ps_enum_retry_mark`, none of which were touched), now reached by a
narrower door. Task 267 (retrieval-sourced, fires D1+D2 live —
`test_task_267_fires_d1_and_d2_live` in `test_verdict_discrimination_
migrated.py`) hits `ps_structural_reject_exclusion_gap` and goes straight
to `gapped`, byte-identical to v1.7.0 — never enters the lane that
stalled. Verified exhaustively: a full live 257-task MBPP run under
v1.8.0 produces **zero** `stalled:*` outcomes
(`test_zero_parks_across_the_full_live_257_task_population`).

Skipping `eval_pending`/`ps_row_fail`/`ps_counterexample` en route to
`'counterexample'` is safe and deliberate: those downstream rules
(`ps_exclude_failed`, `ps_reproposal`, `ps_ce_exhausted`,
`ps_enum_retry_mark`) key ONLY on `status=='counterexample'` plus
`Excluded`/`ps_rung_enumerate`/budget facts — none of them require a
`CounterExample` node to exist. A structural trap by definition passes
every revealed row (that is why row-verification alone never caught it),
so there is no failing row to record; the goal is placed directly into
the state the standing machinery already knows how to drain.

---

## 2. The headline measurement — the 26 ids, disposed

Re-derived from the frozen `results/arc4_endgame.json` (never hand-typed):
`no_structural`'s `accepted_holdout_fail` ids minus `full_a4`'s = exactly
the 26 S2/S5 measured. Partitioned by source and measured live under
v1.8.0 (`tests/test_reject_informs_repair_migrated.py`):

**(d) Gapped directly — retrieval-sourced, reopen never attempted (14):**
`68, 83, 86, 93, 109, 239, 242, 247, 269, 285, 420, 427, 434, 454` — all
still `gapped:structural_verdict_reject`, byte-identical to v1.7.0.

**(b)/(c) Reopened via exclude+reproposal, still honestly gapped (12):**
`14, 58, 103, 125, 126, 164, 228, 304, 396, 414, 430, 432` — every one
mints at least one `Excluded` node and `ps_structural_reopen_count >= 1`
(verified live), and every one lands on a DIFFERENT terminal gap reason
(`enumerate_failed` ×11, `no_shape` ×1) — never
`structural_verdict_reject` again, never `accepted_holdout_fail`, never
`pass`.

**(a) Repaired into a passing accept: `[]` — zero.** Stated plainly, not
smoothed over. **Why zero, precisely, not "search reach was too weak":**
every one of these 26 is, by construction, a candidate that already
passes EVERY revealed row (that is the whole definition of a structural
trap — row-verification could not catch it). Excluding the wrong
candidate removes it from consideration but supplies **no new
discriminating information** — the search is left choosing among
whatever OTHER candidates also fit the same sparse revealed rows, and
most tasks' revealed rows are too sparse to have more than one or two
size-bounded fits at all (12 of 26 find literally nothing and reach
`enumerate_failed`/`no_shape`). This is verified directly and repeatably
against the SynthEnumerate engine for the sharpest instance of the shape
(§3 below), not asserted from the aggregate.

**No new traps introduced anywhere in the 257-task population.** A full
outcome diff of ALL 257 ids between the frozen v1.7.0 `full_a4` arm and a
fresh live v1.8.0 run shows **exactly these same 12 + the 2 genuine-defect
ids (§3) changed, and nothing else** — same `pass` count (28), same
`accepted_holdout_fail` count (78), before and after
(`test_no_wrong_accept_regression_vs_v1_7_0_baseline`).

---

## 3. No honest-score backsliding — 397, 404

397 (median-of-three via `max(a,b)`, `c` unread) and 404 (min-of-two via
bare `a`, `b` unread) are the genuine-defect rejections
`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §2.2 hand-verified with
witnesses. Both are non-retrieval-sourced (`mck_prog_assign_var_n2_q9` /
plain enumerate) and **do** reopen (`reopen_count == 1` on both, live) —
but for the SAME reason as §2's zero-conversions, excluding the decoy
supplies no discriminating signal, so both land on
`gapped:enumerate_failed`, never `accepted`. Gated:
`test_genuine_defects_397_404_still_never_accept`. Repairing these into
acceptance would have been the one real way this phase could have made
things worse; it does not happen, verified live, not assumed.

---

## 4. `br_10_top_of_three` — root-caused, not faked

**Does not converge.** This is measured, not assumed, and the precise
reason is pinned as its own regression test
(`test_br_10_root_caused_non_convergence`, `test_br_10_reopen_mechanism_
genuinely_fires`, `test_br_10_exhaustive_reenumeration_finds_nothing_
from_revealed_rows_alone`).

**The reopen mechanism genuinely fires.** Live: D3 fires alone
(`repair_target_param == ['c']`), the goal routes to `'counterexample'`,
`Max(a,b)` is excluded, and the arc2-Q4 exclude-powered enum-retry lane
re-runs — exactly the mechanism this phase built. It is not "never
tried."

**Why it cannot succeed, verified directly against the engine.**
`br_10`'s 3 revealed rows — `(1,9,3)→9`, `(7,2,5)→7`, `(4,4,4)→4` — are
ALL already satisfied by `max(a,b)` (that is WHY the decoy was ever
accepted). Probed directly against `runners/dsl/src/synth_enumerate.rs`'s
own engine: excluding `Max(a,b)` and exhaustively searching every term of
size ≤ 5 over these SAME 3 rows finds **nothing** (`halt_reason:
'max_size'` — an exhaustive negative, not a budget cutoff). The control
proves the engine itself is not the bottleneck: given a genuinely
discriminating 4th row (`(2,4,11)→11`, which `max(a,b)` fails), the SAME
engine finds `max(a, max(b,c))` trivially (`halt_reason: 'solved'`,
28,989 candidates). **The 3 revealed rows are information-theoretically
insufficient to distinguish the decoy from any correct fix — that is
what makes this shape a trap in the first place, and it is exactly the
gap a REVEALED-rows-only repair mechanism cannot close.**

**The architectural tension, stated precisely.** The `repair_oracle`
battery arm's own mechanism (`scripts/prog_synthesis_battery.py::
run_task_p7`) feeds its ONE externally-revealed held-out counterexample
**only after** a first pass reaches `accepted_holdout_fail` — i.e., only
once the goal has reached `status='accepted'`. S2's own correctness
guarantee (never accept a candidate a detector can prove defective) now
intercepts BEFORE that point for exactly this shape, so `run_task_p7`'s
`pre["outcome"] != "accepted_holdout_fail"` guard short-circuits and the
external counterexample is never fed (`oracle.rounds == 0`, verified
live, matching S2's own v1.7.0 measurement). **This is not a bug this
phase's file-ownership boundary prevented fixing — it is a genuine
consequence of getting S2 right.** You cannot both (a) never accept a
candidate a detector can prove defective, and (b) rely on a repair
mechanism that requires the defective candidate to have been accepted
first, for the exact class of trap where the detector's proof and the
revealed rows' insufficiency are the same fact. Closing this for real
would require either accepting br_10's decoy anyway (reintroducing the
S2 regression this whole arc fixed) or changing `run_task_p7`'s own gate
condition (`scripts/prog_synthesis_battery.py`, outside this phase's file
ownership) to feed its held-out row on a reopened-and-exhausted outcome
too — named here as the honest next lever, not attempted.

**A confirmed side benefit.** S2's OWN residual #4
(`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §7(b)) named three OTHER tests
(`test_prog_repair_migrated.py::test_refused_localization_falls_to_
global_cegis_unchanged`, `test_descent_widening_migrated.py::
test_flat_rung3_accept_converges_via_exclude_powered_retry` +
`test_enum_round_budget_is_integer_and_forced_exhaustion_falls_
honestly`) whose OWN decoy fixtures are D3's exact target shape, and
which S2's pre-accept rejection broke by preventing them from ever
reaching an intermediate "accepted, wrong" state to demonstrate repair
from. **All three pass again, unmodified, under v1.8.0** — S6's reopen
mechanism reaches the SAME eventual corrected state their own assertions
check, via a different (earlier, more honest) route. Verified live; no
edit was made to these files.

---

## 5. Loop safety

- **Zero parks, exhaustively.** A full live 257-task MBPP run under
  v1.8.0 produces no `stalled:*` outcome anywhere
  (`test_zero_parks_across_the_full_live_257_task_population`).
- **Exclusion bites, at the granularity this phase controls.** For every
  one of the 14 reopened ids (12 + 397/404), the `Excluded` node names
  the goal accumulates are pairwise DISTINCT — no construction name is
  ever excluded twice (`test_exclusion_never_mints_the_same_name_twice`).
  One id (228) shows the SAME construction name attributed to two
  separate Rejection records before its final gap — this is the
  pre-existing arc2-Q4 enum-retry sub-lane (`ps_enum_retry_mark`), which
  by design excludes at the SUB-TERM grain (`ps_enum_last_term_json` /
  `ExcludedTerm`) and deliberately does not change the goal's
  `ps_construction` label between rounds; it is independently tested
  (`test_descent_widening_migrated.py`) and out of this phase's scope —
  named here rather than hidden, and it does not change the outcome:
  exactly one `Excluded` node is minted for that name, and the goal still
  terminates honestly within its integer budgets.
- **Idempotence.** `compute_structural_facts` recomputes fresh D1/D2/D3
  facts for every new verified candidate (its own `ps_ir_reflected`-count
  freshness key, unchanged from S2), so a repaired-but-still-defective
  candidate is caught again by the SAME rule family — observed directly
  (id 125, 164, 228 each accumulate 2 Rejection records before their
  final gap, never re-accepting a re-rejected shape).
- **Termination.** Every lane this phase reuses (`ps_reproposal`'s
  `ps_attempts < ps_budget`, `ps_enum_retry_mark`'s
  `ps_enum_round < ps_enum_round_budget`) is gated by a pre-existing
  INTEGER budget this phase did not touch; S6 adds no new unbounded loop.

---

## 6. Files

`seeds/program_synthesis.json` (v1.7.0 → v1.8.0, 60 → 63 rules: the
single `ps_structural_reject` REPLACED by
`ps_structural_reject_exclusion_gap` /
`ps_structural_reject_exclusion_reopen` /
`ps_structural_reject_repair_gap` / `ps_structural_reject_repair_reopen`;
`ps_structural_clear` untouched; `ps_accept` untouched — it already reads
`ps_structural_reject`, set identically by all four new rules).

`domains/prog_synthesis.py` (one addition: `read_goal`'s `structural`
dict gained `reopen_count`, a mechanical read-back of the rule-minted
`ps_structural_reopen_count` counter — no new decision).

`tests/test_program_synthesis_migrated.py` (rule-count pin 60 → 63).

`tests/test_verdict_discrimination_migrated.py` (additive + two existing
scenario tests corrected to match their OWN documented intent: the
"task-267-shaped" D1+D2 test now uses `construction='retrieved_exemplar'`
— task 267 IS retrieval-sourced in the real population, which the
original placeholder construction name did not reflect; the
"task-397-shaped" D3 test is renamed
`test_unread_varying_param_rejected_then_informs_repair_no_park` and
exercises the reopen-then-honestly-exhaust path, since task 397 is NOT
retrieval-sourced; the seed version/rule-name pin bumped to v1.8.0/4
rules).

`tests/test_prog_synthesis_battery_migrated.py` (the br_10 drift note is
NOT retired — it did not converge — but its mapped value is updated,
dated, from `structural_verdict_reject` to `enumerate_failed`, with a
`_P7_KNOWN_GAP_REASON_DRIFT_ALSO_KEYS` addition excluding
`enumerate_outcome` from the pinned-key comparison for the same reason;
full root cause in §4 above).

NEW `tests/test_reject_informs_repair_migrated.py` (19 tests, ~43s: seed
shape; 8 per-detector routing unit tests incl. the D1-dominates-D3
priority case; the 26-id headline disposition; the 397/404 no-backslide
gate; loop safety incl. a full live 257-task zero-parks sweep and a full
257-task no-regression diff against the frozen v1.7.0 baseline; three
br_10 root-cause tests, one of which will FAIL LOUDLY with an explicit
"this is great news, now go update the pins" message if a future change
ever makes it converge, rather than silently going stale).

NEW this file.

---

## 7. Residuals — named, not hidden

**(a) br_10_top_of_three does not converge (§4).** Root-caused precisely
and pinned as a regression test on the analysis itself. The honest next
lever, if this is ever revisited: `scripts/prog_synthesis_battery.py`'s
`run_task_p7` would need to feed its held-out counterexample on a
reopened-and-exhausted outcome too, not only on `accepted_holdout_fail`
— outside this phase's file-ownership boundary.

**(b) Zero of the 26 structural rejections repair into a passing accept
(§2).** Not a shortfall in this phase's own mechanism — verified directly
that the underlying search engine is not the bottleneck (§4's control) —
but a real, named ceiling: exclude-and-retry from revealed rows alone
cannot manufacture information the revealed rows do not contain. Closing
it further would need either more revealed rows (a different phase's
lever) or a smarter proposal bias informed by the EXCLUDED shape (e.g.
"prefer a generator that provably reads every declared parameter" for a
D3-repair reopen) — not attempted here; flagged as the next honest lever
for a follow-up phase with search-behaviour scope.

**(c) Six pre-existing OUTSIDE this phase's file-ownership boundary,
directly caused by the (required, intentional) rule rename:**

  - **Two pure version/rule-count pins**, in files this phase is not
    authorised to edit: `tests/test_budget_isolation_migrated.py::
    test_seed_version_and_isolation_lanes_present` and
    `tests/test_retrieval_migrated.py::
    test_attempt1_codebook_screen_rules_stay_absent_from_the_seed` — both
    assert `seed_manifest["version"] == "1.7.0"` / `len(rules) == 60`,
    stale the moment this phase's version bump landed. Same category S2
    itself named for the prior version bump.
  - **Four in `tests/test_arc4_endgame_migrated.py`** (none in this
    phase's file list), all traced to the SAME root cause —
    `scripts/arc4_endgame_battery.py`'s ablation-manifest construction
    hardcodes the OLD rule names (`_S2_REMOVE_NAMES = {ps_structural_
    reject, ps_structural_clear}`) to build its `no_structural` seed
    variant by NAME-SUBTRACTION from the current manifest. Since the
    current manifest no longer contains `ps_structural_reject` (by this
    phase's own design, replaced by four differently-named rules), that
    subtraction no longer produces a genuine "S2 stripped" seed:
    `test_ablation_manifests_only_differ_in_the_declared_rule_names`
    (the name-set arithmetic itself), `test_three_task_live_reverify_per_
    arm[full_a4-397-...]` / `[no_isolation-397-...]` (task 397's pinned
    outcome string, same drift as the one fixed in `test_prog_synthesis_
    battery_migrated.py` §above, but in a file this phase cannot touch),
    and `test_a3_br10_reproduces_live` (its own `is_true_regression`
    check depends on the SAME broken `no_structural` ablation to
    reproduce a genuine pre-S2 boot). A follow-up phase with access to
    `scripts/arc4_endgame_battery.py` / `tests/test_arc4_endgame_
    migrated.py` should update `_S2_REMOVE_NAMES` to the new four-rule
    set (or rename it `_S2_REPLACE_NAMES` and splice the pre-v1.7.0
    `ps_accept`/absence-of-any-structural-rule body directly, mirroring
    how `_S1_REPLACE_NAMES` already works) and the task-397 pinned
    strings to `enumerate_failed`, exactly as this phase did for its own
    file.

  Full sweep, honestly reported: every suite this phase's own files
  could make green is green — `program_synthesis` (18/18),
  `verdict_discrimination` (26/26), `reject_informs_repair` (19/19, new),
  `structural_verdicts`, `prog_repair`, `prog_descent`,
  `descent_widening`, `retrieval_ceiling`, `search_reach`,
  `screen_codebook`, `anatomy`, `probe`, `battery`, `mbpp_baseline`,
  `mbpp_arc3_endgame`, `mbpp_endgame`, `failure_baseline`,
  `code_synthesis_baseline` all green — **447 passed / 6 failed** across
  the full named sweep, the 6 as categorised above, all outside this
  phase's file-ownership boundary and all directly attributable to the
  rule rename this phase's own brief required.
