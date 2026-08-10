# PROGRAM SYNTHESIS ARC 4 — S1: BUDGET ISOLATION

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC4_PLAN.md` §2-S1,
`PROGRAM_SYNTHESIS_ARC4_PREREG.md` §1 (HA1), `PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md`
(the 17-id measured target list), `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` §9 (R2.5's
screen — the mechanism this phase generalises). Seed `seeds/program_synthesis.json`
v1.5.1 → v1.6.0 (57 → 58 rules).

**Status:** LANDED. 16/17 target ids fully escape `gapped:exhausted`; the 17th
(task 222) is root-caused as a genuinely different, non-starvation event (§4).

---

## 1. The design

### 1.1 Diagnosis

Pre-S1, ONE shared counter pair (`ps_attempts`/`ps_budget`, integer, budget 3)
gated three things at once: (a) how many real codebook-propose attempts a goal
could spend, (b) whether `ps_descend_mark` was allowed to fire at all
(`Lt(ps_attempts, ps_budget)`), and (c) whether `ps_enumerate_mark` was allowed
to fire at all (the SAME `Lt(ps_attempts, ps_budget)` check). Whenever the
propose rung (codebook or the chunk/diet codebook) burned the ENTIRE shared
budget on wrong candidates, `ps_ce_exhausted`/`ps_exhausted` transitioned the
goal straight to the terminal `exhausted` status — a status descend/enumerate's
own `match` pattern (`status == "pending"`) can never re-enter. Descent and the
enumerator were never denied for being WRONG; they were denied because the
COUNTER that measured "attempts spent proposing" was the SAME counter that
measured "is there any budget left for anything else."

R2.5's screen (Arc3) fixed the SCREENABLE (non-descend-applicable) half of this
by pre-judging candidates for free before they could spend a real attempt — but
it explicitly could not touch DESCEND_APPLICABLE goals (screening a partial
cover as a complete program is exactly Attempt-1's false-negative,
`PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` §1) and it only engages when the goal's
frozen initial codebook pool is `>=` the budget (`NOT_SLACK`) — a goal with any
initial slack is never screened at all, R2.5's own documented residual.

### 1.2 The fix: separate lanes, not a smarter screen

Two NEW counter lanes, minted once per goal (both `ps_goal` and `ps_goal_top`),
following the exact P6.5/P7-B "own integer lane, collision-free by construction"
idiom the codebase already uses for `ps_repair_attempts`/`ps_repair_budget` and
`ps_enum_round`/`ps_enum_round_budget`:

- **`ps_propose_attempts` / `ps_propose_budget` (= 3.0)** — the PROPOSAL lane.
  Every non-search proposal source draws from it: `ps_propose` (codebook/chunk
  picks) and `pr_ladder_accept` (a retrieval accept) each increment it by 1,
  alongside their EXISTING, UNCHANGED `ps_attempts` increment. `ps_attempts`/
  `ps_budget` keep their exact original meaning and every original increment
  site (nothing was removed) — they remain the TOTAL-attempts field every
  existing reader (tests, `read_goal`, HA5's future cost instrument) already
  depends on. `ps_propose_attempts` is always `<= ps_attempts` (a strict
  subset of what increments it), and for any goal that has not yet entered
  repair the two stay numerically IDENTICAL — this is what makes every
  substitution below a no-op for every previously-passing path.
- **`ps_enum_reserve_used` / `ps_enum_reserve_budget` (= 1.0)** — the
  RESERVED, untouchable ENUMERATE lane. Nothing but `ps_enumerate_mark`
  itself ever increments it. No proposal-lane consumption, however large,
  can ever reduce it.

### 1.3 What changed, rule by rule

| rule | change |
|---|---|
| `ps_goal`, `ps_goal_top` | mint the 4 new attrs (`ps_propose_attempts:0`, `ps_propose_budget:3`, `ps_enum_reserve_used:0`, `ps_enum_reserve_budget:1`), additive to the existing attr dict. |
| `ps_propose` | effects gain one line: `ps_propose_attempts += 1`. Its own `where` (`Lt(ps_attempts, ps_budget)`) is UNCHANGED — see §1.4 for why this is deliberate, not an oversight. |
| `pr_ladder_accept` | effects gain the same `ps_propose_attempts += 1` line — retrieval is a non-search proposal source per the plan and now draws from the same lane. |
| `ps_repair_mark` | effects gain `ps_repair_entered = 1.0` (additive; no existing `where` reads it). Marks "this goal has now entered the P7-B repair loop", so the isolation logic below can tell first-pass exhaustion from repair-loop exhaustion. |
| `ps_descend_mark` | (1) the `Lt(ps_attempts, ps_budget)` item is REMOVED outright — descent spends no `ps_attempts` of its own (no rule increments it there); this guard was pure collateral coupling to the propose lane, and removing it is what fixes class (a)'s 7 ids. (2) the `Not(Exists <eligible non-excluded codebook pick>)` item is widened to `Or(<that same check>, Gte(ps_propose_attempts, ps_propose_budget))` — a codebook pool LARGER than the propose budget still correctly hands off once the propose lane closes, not only when the pool is truly empty (closes a latent stall the old design would have hit on a pool > budget). |
| `ps_enumerate_mark` | (1) `Lt(ps_attempts, ps_budget)` → `Lt(ps_enum_reserve_used, ps_enum_reserve_budget)` — entry now depends ONLY on the reserved lane. (2) the same eligible-check widening as `ps_descend_mark`. (3) effects gain `ps_enum_reserve_used += 1` on entry. |
| `ps_ce_exhausted`, `ps_exhausted` | gain ONE new `where` item: `Not(And(Not(Eq(ps_repair_entered,1.0)), Or(DESCEND_STILL_AVAILABLE, ENUMERATE_STILL_REACHABLE)))`. Everything else — including the existing `Gte(ps_attempts, ps_budget)` and the enum-retry mutual-exclusion carve-out — is byte-unchanged. |
| **`ps_isolate_fallthrough`** (NEW) | the exact logical complement: same base state `ps_ce_exhausted` requires (kind, `status==counterexample`, the exclusion that just fired, `Gte(ps_attempts,ps_budget)`, the SAME enum-retry carve-out copied verbatim — never retyped) PLUS `Not(Eq(ps_repair_entered,1.0))` AND `Or(DESCEND_STILL_AVAILABLE, ENUMERATE_STILL_REACHABLE)`. Effects: `status := "pending"`. |

`DESCEND_STILL_AVAILABLE` = the exact 5-part condition `ps_descend_mark` itself
requires beyond kind/status/eligible-check (has-example, codebook still
trigger-covers the request ignoring exclusion, list-input-or-scalar-fold/branch
shaped, depth budget allows, descent not yet entered). `ENUMERATE_STILL_REACHABLE`
= has-example, enumerate not yet entered, reserve not yet spent. Both are
generated from ONE Python helper (`descend_still_available(sfx)` /
`enumerate_still_reachable(sfx)` in the one-off seed-authoring script used to
apply this change — see §7), parameterised by a suffix per call site so the
Exists-bound variable names never collide across rules, following the exact
R2.5 precedent ("generated from a single Python extraction point... rather than
hand-retyped"). A live bug this discipline caught before landing: `ps_ce_exhausted`/
`ps_exhausted`'s original `match` only bound `ag`/`g`, never `m` — the first cut of
the new guard referenced `Neighbours(m, has_example)` against an UNBOUND `m` and
silently evaluated to always-false everywhere. Fixed by adding `["g",
"about_message", "m"]` to both rules' (and the new rule's) `match`.

### 1.4 Why `ps_propose`'s own entry gate is UNCHANGED

`ps_propose`'s `Lt(ps_attempts, ps_budget)` gate was deliberately left alone.
Reasoning, proven not assumed: in the first-pass (pre-repair) state, `ps_attempts`
and `ps_propose_attempts` are always numerically equal (every increment site of
one is mirrored by the other, and nothing else increments either before repair
starts) — so `Lt(ps_attempts, ps_budget)` and `Lt(ps_propose_attempts,
ps_propose_budget)` are the SAME boolean there; changing it would have been a
no-op for correctness but an unforced, riskier edit. In the REPAIR-loop state,
`ps_attempts` and `ps_propose_attempts` diverge (repair's own `ps_localize_refuse_*`/
`ps_repair_exhausted`/`ps_enum_retry_mark` increment `ps_attempts` alone) — and the
repair loop's own "global CEGIS path" fallback (`PROGRAM_SYNTHESIS_P7B` design)
explicitly re-enters `ps_propose` via `ps_reproposal`, gated on the SAME
`ps_attempts`/`ps_budget` pair repair already depends on. Swapping `ps_propose`'s
gate to the new lane would have let a repair round re-propose MORE times than the
pre-S1 mechanism allowed (since `ps_propose_attempts` stays frozen at whatever the
first-pass phase spent, while `ps_attempts` climbs with every repair round) —
verified this would be a real behavioural change, not merely a differently-named
one, and therefore left `ps_propose`/`ps_reproposal` completely untouched. This is
the concrete instance of "isolation, not screening, and never touch what you
don't need to."

### 1.5 Isolation is not screening — the distinction, verified

The task explicitly asked this to be checked, not assumed. Screening (R2.5)
judges a CANDIDATE's correctness before it may spend an attempt (a dry-run
evaluate against revealed rows) — which is exactly what went wrong in Attempt 1
(PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md §1): a partial-cover construction fails a
dry-run-as-complete-program check even though it is the CORRECT descent starting
point once a hole is filled in. Isolation (S1) makes NO correctness judgment
about any candidate whatsoever — the real propose/exclude/reproposal/screen
pipeline is completely unchanged; every candidate that is tried for real is
still tried and judged exactly as before. S1 only changes BUDGET BOOKKEEPING:
which counter gates entry into `ps_descend_mark`/`ps_enumerate_mark`, and whether
the goal is allowed to keep living once the propose lane's own counter is spent.
Concretely verified live (`tests/test_budget_isolation_migrated.py::
test_isolation_does_not_change_screened_goals`): R2.5's own screen decoy-kill
fixture (pool0=4 chunk decoys >= budget=3) is a COMPLETE no-op under S1 — every
decoy still dies for free at the screen, `ps_propose_attempts` never moves off
0, `ps_isolate_fallthrough` never fires (there is no propose-lane exhaustion
event to redirect), and the outcome is byte-identical. Screening and isolation
have disjoint TRIGGERS: screening prevents an attempt from ever being spent;
isolation only changes what happens once real attempts ARE spent and the
propose lane closes.

---

## 2. The 17-id headline — before / after

`PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md`'s measured target list, re-verified LIVE
(PRIMARY protocol, FULL-R3 boot, `scripts/mbpp_arc3_battery.run_task` — the
`tests/test_budget_isolation_migrated.py::test_17_target_ids_headline` gate).

| id | class | pre-S1 outcome | post-S1 outcome | rungs (post) |
|---|---|---|---|---|
| 108 | (b) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 119 | (b) | gapped:exhausted | **accepted_holdout_fail** | none (resolved via retrieval before codebook was ever needed) |
| 222 | (b) | gapped:exhausted | gapped:exhausted (NAMED RESIDUAL, §4) | codebook, lattice, descend, enumerate all 1.0 |
| 223 | (b) | gapped:exhausted | **accepted_holdout_fail** | codebook, lattice, descend, enumerate all 1.0 |
| 229 | (b) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 240 | (b) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 245 | (b) | gapped:exhausted | **accepted_holdout_fail** | codebook, lattice, descend, enumerate all 1.0 |
| 280 | (b) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 286 | (a) | gapped:exhausted | **accepted_holdout_fail** | codebook, descend 1.0; enumerate never needed |
| 296 | (a) | gapped:exhausted | **accepted_holdout_fail** | none (resolved via retrieval) |
| 394 | (b) | gapped:exhausted | **pass** | none (resolved via retrieval) |
| 415 | (a) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 431 | (b) | gapped:exhausted | **accepted_holdout_fail** | codebook, lattice, descend, enumerate all 1.0 |
| 463 | (a) | gapped:exhausted | **accepted_holdout_fail** | codebook, lattice, descend, enumerate all 1.0 |
| 468 | (a) | gapped:exhausted | **gapped:enumerate_failed** | codebook, lattice, descend, enumerate all 1.0 |
| 471 | (a) | gapped:exhausted | **accepted_holdout_fail** | codebook, descend 1.0; enumerate never needed |
| 476 | (a) | gapped:exhausted | **accepted_holdout_fail** | none (resolved via retrieval) |

**16/17 escape `gapped:exhausted` entirely.** Every escaping id lands on one of
the plan's own registered legitimate outcomes (`accepted` — `pass` above —
`accepted_holdout_fail`, or `gapped:enumerate_failed`) — the claim is that the
enumerator/descender GOT ITS TURN, never that the task passes. Several ids
(119, 296, 394, 476) resolve via the retrieval ladder before the codebook is
even reached; this is orthogonal to S1 (retrieval's own screen already never
touched `ps_attempts` on a reject) and is reported for completeness, not
claimed as an S1 effect.

**Bonus, cross-arm generalisation (not in the original 17, found while
re-verifying the frozen battery/endgame artifacts, §3):** task 142 under the
`no_retrieval` arm ALSO moves off `gapped:exhausted` (→ `accepted_holdout_fail`)
— it was never in FULL-R3's own 17-id residual (S0-A only measured FULL-R3),
but the SAME isolation mechanism fixes it under a different arm where
retrieval is switched off. This is the "generalise, don't special-case"
instruction paying off exactly as intended: no id-specific code exists
anywhere in the fix.

---

## 3. Reserved-budget invariant — proof, pinned numbers

`tests/test_budget_isolation_migrated.py::
test_reserved_budget_invariant_pool_size_does_not_reduce_enumerator_turn`: a
20-decoy, all-wrong, DESCEND_APPLICABLE pool is compared against a 4-decoy pool
of the identical shape. **Pinned, byte-identical in both:** `attempts == 4.0`
(3 real propose attempts + 1 enumerate fresh-attempt bump), `excluded ==
["decoy_0", "decoy_1", "decoy_2"]` (decoy_3 through decoy_19 NEVER tried for
real, regardless of how many more exist), `rungs == {codebook:1.0, lattice:None,
descend:1.0, enumerate:1.0}`, `gap_reason == "enumerate_failed"`. The
enumerator's own reserved lane is therefore provably untouched by proposal-pool
size — a pathological all-wrong pool of any size cannot reduce the enumerator's
own guaranteed turn, nor can it push the propose lane's own real-attempt count
above its fixed budget (3, regardless of pool size).

---

## 4. The named residual — task 222, root-caused

Task 222 ("check if all elements in a tuple have the same data type") is the
ONE id in the 17-id list that STILL shows `outcome == "gapped:exhausted"` under
S1. This is reported, not excused, with the proof facts a live re-run shows
(`tests/test_budget_isolation_migrated.py::test_17_target_ids_headline` asserts
every one of these):

- `rungs.descend == 1.0` — descent WAS entered and ran (mark-once, fired for real).
- `rungs.enumerate == 1.0` and `enumerate_outcome == "ok"` — the enumerator was
  NOT starved: it was entered, and it genuinely FOUND a candidate (an "ok"
  outcome, not "unavailable"/"failed-to-run").
- `attempts == 6.0` (`> ps_propose_budget == 3.0`) — proof the goal spent real
  cycles well beyond the propose lane's own cap, exactly the isolation mechanism
  working (the propose lane closing at 3 did NOT stop the goal).
- `n_counterexamples == 12`, two enumerate-retry rounds consumed
  (`ps_enum_round`/`ps_enum_round_budget = 2`, the pre-existing, UNCHANGED
  P7-B repair-adjacent retry lane): the enumerator's OWN finding failed a
  revealed row, got excluded via `ps_enum_retry_mark`, re-enumerated with the
  exclude list, failed AGAIN, and only THEN — with the enum-retry round budget
  itself exhausted (a SEPARATE, orthogonal lane S1 never touches) — did the
  classic `ps_exclude_failed` → `ps_ce_exhausted` path close the goal, because
  at THAT point BOTH mark-once rungs (`ps_rung_descend`, `ps_rung_enumerate`)
  had already fired and neither `DESCEND_STILL_AVAILABLE` nor
  `ENUMERATE_STILL_REACHABLE` could be true any more (both require "not yet
  entered").

**The new structural fact this demonstrates, not assumed:** the status STRING
`exhausted` is not, by itself, proof of budget starvation. Once every mark-once
rung has genuinely had its turn, a SEPARATE pre-existing exhaustion source (the
enum-retry round budget, which predates this phase and is untouched by it) can
independently close the goal through the SAME terminal rule
(`ps_ce_exhausted`) and therefore the same status string — even though the
propose-lane starvation bug this phase targets played no part. This is
qualitatively different from every OTHER pre-S1 `gapped:exhausted` row (where
`rungs.descend`/`rungs.enumerate` were BOTH `null` — the rung never got a
chance at all). Renaming the terminal outcome to distinguish "every rung tried,
still failed" from "a rung was denied a turn" would be a clean, low-risk
follow-up (a new `gap_reason` value, e.g. `exhausted_all_rungs_tried`) but was
NOT undertaken here: it touches status-string semantics that other, out-of-
ownership frozen artifacts key on, and verifying it doesn't ripple elsewhere is
a separate, dedicated piece of work this phase's scope and file-ownership list
do not cover.

**Honest count against the registered bar:** HA1's own bar ("`gapped:exhausted`
→ 0 across all classes") is met for 16/17 unconditionally. Task 222 keeps the
status string but is proven, not assumed, to be a DIFFERENT kind of event than
the one this phase targets — the propose-lane starvation this phase exists to
fix is verifiably closed even for this id (both rungs fired, `enumerate_outcome
== "ok"`, `attempts` well past the propose budget). No further attempt to force
222 to a different status was made once this distinction was established live.

---

## 5. Descent / repair — unchanged, verified

`tests/test_prog_repair_migrated.py`, `tests/test_prog_descent_migrated.py`,
`tests/test_descent_widening_migrated.py`: run against BOTH the pre-S1
(v1.5.1, backed up before any edit) and post-S1 (v1.6.0) seed. **Identical
failing-test set on both**, confirming zero attributable regression from this
phase's own rule edits:

| suite | pre-S1 | post-S1 |
|---|---|---|
| `test_prog_repair_migrated.py` (13 total) | 2 fail (below) | same 2 |
| `test_prog_descent_migrated.py` (17 total) | 2 fail (below) | same 2 |
| `test_descent_widening_migrated.py` (11 total) | 0 fail | 0 fail |

The 4 pre-existing failures (`test_headline_unreachable_ids_reach_honest_
terminals[la_21_count_zeros]`, `test_repair_budget_is_integer_and_exhaustion_
falls_to_global`, `test_depth_budget_blocks_descent_honestly`,
`test_failed_descent_falls_to_enumerate_then_gap`) are traced to the
CONCURRENT sibling agent's engine work: `git status` shows `runners/dsl/src/
synth_enumerate.rs` modified in this working tree (untracked
`PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` alongside it), and the installed
`_native.abi3.so` was rebuilt after commit `752ff82933` ("program synthesis
ARC2 Q1 — THE ENGINE FLOOR IS WIDE" — 783 lines added to `synth_enumerate.rs`,
its own commit message noting "MBPP task 11 moved gapped:enumerate_failed ->
accepted_holdout_fail"). Every one of the 4 failures here is the SAME shape:
a fixture that pre-S1 relied on the enumerator being UNABLE to solve something
now finds the enumerator CAN solve it (`'accepted' == 'gapped'` in every one).
This is engine-floor widening from `runners/dsl/src/**`, explicitly out of this
phase's ownership (the task brief: "Do NOT touch those… its changes are
additive"), reproduced identically with or without any S1 edit, and therefore
not attributable to budget isolation. Not touched, not silenced, reported here
per the "root-cause, don't excuse" standing rule.

`br_19_pick_or_boost` and every other `test_prog_synthesis_battery_migrated.py`
frozen row not affected by the same engine drift: unaffected (2 pre-existing
la_03_running_sum-shaped failures, same drift, see below).

---

## 6. Full paired sweep

PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1,
`pytest --confcutdir=.` throughout. ~60s total across two batches, well under
budget.

| suite | result | note |
|---|---|---|
| `test_program_synthesis_migrated.py` | **17/17 green** | rule-count pin 57→58 (§7); one fixture (`test_budget_bounded_integer_attempts_and_honest_exhaustion`, renamed `..._then_isolated_rung_takeover`) updated to assert the NEW, correct outcome for the EXACT scenario it exercises (class (a)'s own shape) — see §7. |
| `test_budget_isolation_migrated.py` (NEW) | **7/7 green** | this phase's own canonical gate. |
| `test_screen_codebook_migrated.py` | **6/6 green** | unchanged, zero edits needed. |
| `test_prog_repair_migrated.py` | 11/13 green | 2 pre-existing (S4 engine drift, §5), identical pre/post S1. |
| `test_prog_descent_migrated.py` | 15/17 green | 2 pre-existing (S4 engine drift, §5), identical pre/post S1. |
| `test_descent_widening_migrated.py` | **11/11 green** | |
| `test_retrieval_migrated.py` | 28/31 green | 2 pre-existing (task 394 drift, S4); 1 caused by this phase's OWN seed-version bump (`d["version"] == "1.5.1"` pin) — NOT edited (out of file ownership), see §8. |
| `test_prog_synthesis_battery_migrated.py` | ~19/21 green | 2 pre-existing (la_03_running_sum drift, S4), identical pre/post S1. |
| `test_mbpp_endgame_migrated.py` | 28/30 green | 2 rows are task 108's OWN pin (`gapped:exhausted` → now `gapped:enumerate_failed`) — the INTENDED S1 effect landing in an out-of-ownership frozen file, see §8. |
| `test_mbpp_arc3_endgame_migrated.py` | 36/40 green | 4 rows: task 108 (×3 arms) + task 142 (`no_retrieval`) — the SAME intended effect, see §2/§8. |
| `test_arc4_anatomy_migrated.py` | 24/27 green | 2 pre-existing (S4 drift: hash + task 296); 1 is task 108's own pin (class-(b) reverify), the intended S1 effect, see §8. |
| `test_arc4_probe_migrated.py` | 18/19 green | 1 pre-existing (S4 drift, task 106 halt_reason), identical pre/post S1. |
| `test_mbpp_diet_migrated.py` | **18/18 green** | |
| `test_prog_chunks_migrated.py` | **11/11 green** | |
| `test_mbpp_spec_migrated.py` | **67/67 green** | |
| `test_mbpp_baseline_migrated.py` | **11/11 green** | |
| `test_retrieval_ceiling_migrated.py` | **19/19 green** | |

Every failure above is individually traced to one of exactly two causes, never
a third: (1) the concurrent S4 engine-widening work (`runners/dsl/src/
synth_enumerate.rs`, out of this phase's ownership, reproduced IDENTICALLY on
the untouched pre-S1 seed — proof, not assumption, §5/§8), or (2) this phase's
own INTENDED effect (task 108/142 escaping `gapped:exhausted`, landing in files
outside this phase's file ownership) plus the one unavoidable seed-version pin.
No failure traces to a third, unexplained cause.

---

## 7. Pins reconciled — `test_program_synthesis_migrated.py` (owned)

- **Rule count**: 57 → 58 (`test_seed_loads_clean`), matching the ONE new rule
  (`ps_isolate_fallthrough`) — every other change this phase makes is an
  in-place edit to an existing rule, not a new one.
- **`test_budget_bounded_integer_attempts_and_honest_exhaustion` →
  `test_budget_bounded_integer_attempts_then_isolated_rung_takeover`**: this
  fixture (4 wrong, strictly-decreasing-specificity, DESCEND_APPLICABLE decoys,
  `branch=True`) is EXACTLY class (a)'s own shape — R2.5 built it specifically
  to bypass the screen and exercise the classic propose→exclude→reproposal
  path. S1 correctly changes its terminal outcome: the propose lane's own
  integer honesty is UNCHANGED (still exactly 3 real attempts, `decoy_3`
  NEVER tried for real, `excluded` unchanged) but the goal is no longer
  terminally exhausted — it falls through to descent (`rungs['descend'] ==
  1.0`), whose hole-derivation finds the request's single revealed row
  consistent with the identity relation and ACCEPTS. Updated assertions
  verify BOTH halves: budget honesty (unchanged) and the isolated takeover
  (new). The `Program` count assertion follows the existing
  `test_prog_descent_migrated.py` fold-up-accept precedent exactly (`s.
  neighbours(r["goal"], "accepted_program")` has length 1 — the hole's own
  sub-goal mints its OWN, separate Program, `s.nodes("Program")` would show 2).

## 8. Pins NOT reconciled — out of this phase's file ownership

This phase's file ownership is explicit: `seeds/program_synthesis.json`,
`domains/prog_synthesis.py`, `tests/test_program_synthesis_migrated.py`,
`tests/test_screen_codebook_migrated.py` (additive), the two new files. Every
OTHER test file below is left completely untouched, including the ones whose
frozen pins this phase's own (correct, intended) fix breaks:

- **`test_retrieval_migrated.py::test_attempt1_codebook_screen_rules_stay_
  absent_from_the_seed`** pins `d["version"] == "1.5.1"` — this MUST diverge
  the moment the seed version bumps to 1.6.0 (an unavoidable, purely
  mechanical consequence of this phase's own required version bump, not a
  content change). R2.5 hit and fixed the identical line in the identical
  file for the identical reason (1.5.0 → 1.5.1); this phase does NOT repeat
  that reconciliation because the file is outside this phase's explicit
  ownership list, and is named here so it is not mistaken for an unexplained
  regression.
- **`test_mbpp_endgame_migrated.py`** (2 rows), **`test_mbpp_arc3_endgame_
  migrated.py`** (4 rows), **`test_arc4_anatomy_migrated.py`** (1 row) all pin
  task 108 (and, in the `no_retrieval` arm, task 142) as `gapped:exhausted`
  against their own frozen `results/*.json` artifacts via live-reverify
  assertions. This phase's fix makes task 108 land `gapped:enumerate_failed`
  (task 142: `accepted_holdout_fail`) instead — the INTENDED headline effect,
  verified precisely in §2 above — but reconciling these pins would mean
  editing (or the frozen-artifact-owning script re-generating) six files this
  phase does not own. `arc3 endgame 40` is explicitly named in this phase's
  own gate list as tolerating drift "reconciled… via the standing dated
  improvement-direction rule" — the SAME standing rule (`CLAUDE.md`'s
  2026-07-21 retraction note; the project's dated-pin-drift discipline) would
  apply equally to the other frozen files here, but this phase does not
  perform that reconciliation itself, to respect the explicit file-ownership
  boundary in its own brief. Named here, precisely, as pending reconciliation
  by whichever phase/owner next touches those files — never silently
  excused.

---

## 9. No-parks

`tests/test_budget_isolation_migrated.py::test_no_park_across_every_fixture_in_
this_file` — every fixture in the new file (both pool sizes, the screened
chunk-decoy fixture) reaches a terminal status (`accepted`/`gapped`/
`no_shape`/`enumerate_unavailable`), never left on `pending`/`counterexample`/
`screen_running`/`enumerate_pending`. The mutual-exclusivity analysis in §1.3
(worked through by hand before landing: `ps_propose`, `ps_no_shape`,
`ps_exhausted`, `ps_descend_mark`, `ps_enumerate_mark` all match on
`status == "pending"` simultaneously; the widened guards were checked to
produce EXACTLY one true guard in every reachable state, never zero, never
more than one) is the reason no stall-class regression was found.

---

## 10. Files

- `seeds/program_synthesis.json` — v1.5.1 → v1.6.0, 57 → 58 rules. Modified:
  `ps_goal`, `ps_goal_top`, `ps_propose`, `pr_ladder_accept`, `ps_repair_mark`,
  `ps_descend_mark`, `ps_enumerate_mark`, `ps_ce_exhausted`, `ps_exhausted`.
  New: `ps_isolate_fallthrough`.
- `domains/prog_synthesis.py` — `read_goal` gains the `isolation` sub-dict
  (mechanical read-back of the 4 new counters + `ps_repair_entered`; no
  decision, audited live).
- `tests/test_program_synthesis_migrated.py` — rule-count pin, one fixture
  reconciled per §7 (docstring + module-header gate-7 description updated).
- `tests/test_screen_codebook_migrated.py` — unchanged (already green).
- NEW `tests/test_budget_isolation_migrated.py` — 7 gates (seed structure,
  the 17-id headline, the reserved-budget invariant, isolation-is-not-
  screening, the fallthrough's repair-immunity structural check, no-park,
  the no-python-decision source audit).
- This file.

**One-off tooling note:** the seed edits above were applied via a small,
throwaway Python script (term-AST builder functions mirroring the seed's own
JSON shapes; not committed as a project script, not part of this phase's
deliverables) rather than hand-edited JSON, specifically to guarantee the
reused `DESCEND_STILL_AVAILABLE`/`ENUMERATE_STILL_REACHABLE` predicates are
generated from ONE source rather than hand-retyped into 3 separate rule
bodies — the exact discipline `PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md` §9.2
established for the same class of risk.
