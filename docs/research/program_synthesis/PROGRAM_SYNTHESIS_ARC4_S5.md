# PROGRAM SYNTHESIS ARC 4 — S5: THE POWERED ENDGAME + ARC CLOSE-OUT

**Date:** 2026-08-01. Governed by `PROGRAM_SYNTHESIS_ARC4_PREREG.md`,
**especially the §AMENDMENT** (A1 corrects HA2's ceiling to the union
40/76 = 52.6%; A2 withdraws HA3 — it does not appear below; A3 registers
the honest-score clause; A4 fixes the reporting order — mechanism first,
score second). Driver: `scripts/arc4_endgame_battery.py`. Artifact:
`results/arc4_endgame.json`. Gate: `tests/test_arc4_endgame_migrated.py`.

This is a MEASUREMENT phase. No synthesis/engine/seed/spec code was
touched. Every number below is read from `results/arc4_endgame.json`,
itself derived from a live, twin-run-deterministic 257-task MBPP
PRIMARY-protocol battery.

---

## 0. Reporting order (per SAMENDMENT A4): mechanism first

**The headline is not the pass rate.** It is how much of its own
wrongness the system can now detect before shipping it.

### 0.1 Self-detected wrongness — THE headline

Of the programs the system would otherwise have accepted **wrongly**
(measured as `NO-STRUCTURAL`'s own `accepted_holdout_fail` population —
104 traps, on the SAME 257-task run, with S1's budget isolation and S4's
search-reach widening already active), **FULL-A4 now rejects 26 of them
PRE-ACCEPT** (`gapped:structural_verdict_reject`) instead of silently
shipping a wrong answer:

**26/104 = 25.0% of its own live wrongness self-detected before accept.**

This number reproduces `PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md`'s own
closed-loop measurement (104 → 78, 26 converted) exactly — a strong
cross-validation, since that measurement isolated the identical S2-only
delta on the identical FULL-R3+S1+S4 boot.

**Standing unknown, stated with the headline, not hidden below it:**
36/76 (47.4%) is the corrected honest residual at the ceiling measured
against the FROZEN arc-3 76-trap population
(`PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`) — traps with no dead
code, no unread input, no vacuous guard, correct arity, and no owned
behavioural signal either: genuine arithmetic/logic errors this
measurement cannot yet catch by inspection or cross-frame execution.

### 0.2 A population-mismatch caveat, stated once, applying everywhere below

The 40/76 = 52.6% ceiling (SAMENDMENT A1) was measured on the **FROZEN**
76-trap arc-3 population, captured *before* S1/S4 landed. This phase's
own `accepted_holdout_fail` population is a **different, live, larger**
set (104 under NO-STRUCTURAL, because S1+S4 already changed what gets
accepted before S2 is even switched on). The two populations are never
merged into one ratio in this document — every place a ceiling is cited,
its own population is cited beside it (the standing "two figures from
two populations are never silently merged" rule).

---

## 1. HA1 — budget isolation

**Registered bar:** 17/17 eliminated (0 remaining `gapped:exhausted`
anywhere), no task regresses elsewhere.

| | ids | n |
|---|---|---|
| arc-3 FULL-R3 `gapped:exhausted` (the target list) | 108,119,222,223,229,240,245,280,286,296,394,415,431,463,468,471,476 | 17 |
| FULL-A4 `gapped:exhausted` | 222, 272 | 2 |
| escaped under FULL-A4 | all but 222 | **16/17** |

**Both remaining rows are independently verified NOT to be budget
starvation**, per the SAME facts `PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md` §4
used to root-cause task 222:

| task | rungs (codebook/lattice/descend/enumerate) | enumerate_outcome | attempts | verdict |
|---|---|---|---|---|
| 222 | 1.0/1.0/1.0/1.0 | `ok` | 6.0 (> propose budget 3) | NOT starvation — every mark-once rung fired, enumerate genuinely found a candidate, the goal closes via the separate enum-retry-round-budget lane |
| 272 | 1.0/1.0/1.0/1.0 | `ok` | 5.0 (> propose budget 3) | NOT starvation — the SAME signature; this is S4's own named residual (a downstream shape/reflection gap on a newly-composable candidate, `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` §4.2), unrelated to budget isolation |

**Verdict: STRONG_WITH_NAMED_EXCEPTIONS.** Read literally, the prereg's
own bar text excuses exactly this case: *"Any row still `gapped:
exhausted` ... is a genuine new miss ... [unless] attributed to a task
that was already failing for an unrelated, independently-verified
reason."* Zero rows fail for the propose-lane-starvation reason S1
targets; the two survivors fail for two DIFFERENT, already-named,
independently-verified reasons (the enum-retry-round lane; S4's
downstream shape gap).

**HA1 vs NO-ISOLATION (the ablation):** under NO-ISOLATION (S1's 9 rules
reverted, S2/S4 intact), 14/17 of the original ids remain
`gapped:exhausted` — the mechanism this phase targets genuinely closes
14 rows that would otherwise still be starved. The other 3 (119, 296,
394, 476 minus one that stays via retrieval in both arms — see the
artifact for the exact id) resolve via the retrieval ladder before the
codebook is even reached in EITHER arm, orthogonal to isolation, exactly
as `S1_NOTES.md` documented.

**A new arrival, not an S1 miss.** Task 272 was never in arc-3's 17-row
population; it is a fresh `gapped:exhausted` that appeared because S4's
widened enumerator can now COMPOSE a candidate for it that a downstream
stage rejects — S4's own residual, surfacing here for the first time in
a full 257-task run rather than the 85-task isolated bucket S4's own
notes measured.

---

## 2. HA2 — verdict discrimination + the A3 accounting

**Registered bar (A1-corrected):** STRONG = ≥20/76 net conversions
(half the corrected reachable mass 40 — the prereg's literal text still
says "≥12" because it predates A1's correction; 20 is the SAME "half the
reachable" formula applied to the corrected ceiling, not a new number).

| | n | ids |
|---|---|---|
| NO-STRUCTURAL `accepted_holdout_fail` (the "before" population, S1+S4 active) | 104 | — |
| FULL-A4 `accepted_holdout_fail` (the "after" population) | 78 | — |
| **Converted (pre-accept reject)** | **26** | see artifact `converted_pre_accept_reject_ids` |

**26 ≥ 20 → STRONG.** (Reading the raw count against the bar's
absolute-count formula; the live population this count is measured
against, 104, differs from the ceiling's own 76-population per §0.2's
caveat — the count itself, not a ratio against 76, is what the
registered bar actually specifies.)

### 2.1 The A3 three-way honest-score accounting (load-bearing)

**(1) Pass rate, before/after, both denominators:**

| | NO-STRUCTURAL (before) | FULL-A4 (after) |
|---|---|---|
| pass / runnable | 30/257 = 11.67% [8.30, 16.18] | 28/257 = 10.89% [7.65, 15.30] |
| pass / all-257 | 30/257 = 11.67% | 28/257 = 10.89% |

Pass rate **fell** 30 → 28. Per SAMENDMENT A3, this is checked against
witnesses before being called anything.

**(2) Genuine-defect rejection ids, with witnesses (independently
verified, never touching a held-out row):**

| task | accepted-but-wrong program (NO-STRUCTURAL) | witness input | witness result | correct answer | live-reverified |
|---|---|---|---|---|---|
| 397 | `max(a, b)`, `c` never read (median-of-three) | `a=1, b=5, c=3` | `5` | `3` | ✓ wrong |
| 404 | bare `a`, `b` never read (min-of-two) | `a=5, b=1` | `5` | `1` | ✓ wrong |

Both are re-verified LIVE in this phase's own gate
(`tests/test_arc4_endgame_migrated.py::
test_a3_genuine_defect_ids_carry_witness_inputs`) via `prog_eval` on the
hand-constructed witness — never the task's held-out row. **These are
the entire "regression" set the pass-rate drop consists of.**

**(3) True regression ids (a CORRECT program wrongly rejected) — the
ONLY list that counts against S2:**

- **Within the 257-task MBPP population: ZERO.** The only two
  pass→`gapped:structural_verdict_reject` transitions in the whole run
  are exactly 397 and 404 above — both witness-confirmed genuine
  defects. Subtracting them from the transition set leaves the empty
  list.
- **Outside the MBPP population, in the `repair_oracle` fixture battery:
  ONE — `br_10_top_of_three`, verified live, not hidden.**

  `scripts/prog_synthesis_battery.py`'s `repair_oracle` arm on
  `tests/fixtures/prog_synthesis_battery/tasks.json`'s
  `br_10_top_of_three` ("largest of three numbers") reproduces
  structurally identical to D3's own target shape by design — a decoy
  fixture built to demonstrate CEGIS repair converging FROM a
  plausible-but-wrong accept. Live, under FULL-A4:

  ```
  status: gapped, gap_reason: structural_verdict_reject, attempts: 0.0,
  oracle: {ce_fed: null, rounds: 0, pre_feedback_outcome: "gapped"}
  ```

  S2's rejection fires BEFORE `run_task_p7`'s own
  `pre["outcome"] != "accepted_holdout_fail"` gate can ever see an
  accepted-but-wrong candidate, so the counterexample the fixture is
  built to feed is **never fed** (`oracle.rounds == 0`) — the Q4
  exclude-powered-retry / repair mechanism this fixture demonstrates
  never gets a turn. Under NO-STRUCTURAL (S2 reverted), this task
  reaches `accepted_holdout_ok` via repair — a genuinely correct
  program, reachable, that FULL-A4 now forecloses outright. **This is a
  real, named, unresolved true regression**, distinct in kind from
  397/404: it discards a REPAIR OPPORTUNITY rather than shipping a wrong
  answer, and `PROGRAM_SYNTHESIS_ARC4_S2_RECONCILE_NOTES.md` §3 already
  refused a test-side workaround for it (the fixture lives outside S2's
  file-ownership boundary; a re-pin would have been the exact exemption
  the reconciliation task explicitly forbade). Left open here as the
  arc's own named residual — see §7.

**Rule, stated verbatim:** *"A pass-rate DROP attributable to
genuine-defect-rejection is NOT a regression... 'Fewer wrong accepts at
a lower score' is a PASS for this arc."* Measured outcome: 2 pass→reject
transitions, both genuine-defect catches, zero true regressions within
the benchmark population, one true regression named outside it. **This
arc's honest-score clause paid out exactly as registered, with one
uncomfortable but honestly reported exception.**

---

## 3. HA4 — search reach

**NO-REACH is OMITTED.** No OFF switch exists for S4's 11
`SynthEnumerate` ops that avoids either (a) touching
`runners/dsl/src/synth_enumerate.rs` (forbidden this phase — no Rust, no
cargo) or (b) re-implementing the engine's own `spec_is_list_shaped`/
`spec_is_string_shaped` typed-default selection logic in Python well
enough to trust the result as a faithful ablation rather than a
different, untested instrument. (A class-level monkeypatch of the native
`Substrate.evaluate` method IS mechanically possible — verified live —
but correctly gating it per spec-shape requires shadowing engine
internals in this measurement script, a duplicate/drift-prone
reimplementation, not a switch.) Per the task's own registered fallback,
this arm is omitted rather than hacked.

**HA4 rests on S4's own measured, gated 85-task bucket**
(`results/arc4_backward_probe.json::ha4_search_reach_sizing.
ok_already_no_named_lever`, `tests/test_search_reach_migrated.py`):

| outcome | n/85 | 
|---|---|
| `pass` | 8 |
| `accepted_holdout_fail` | 13 |
| moved to a different gap reason | 4 |
| still `gapped:enumerate_failed` | 60 |
| **moved off `gapped:enumerate_failed` entirely** | **25 (29.4%)** |

**Registered bar:** WEAK = 20-49% conversion. **25/85 = 29.4% → WEAK.**

**Cross-check against this phase's own full 257-task FULL-A4 run
(paired against arc-3's frozen `gapped:enumerate_failed` population,
139 ids):**

| | n | 
|---|---|
| arc-3 FULL-R3 `gapped:enumerate_failed` | 139 |
| FULL-A4 `gapped:enumerate_failed` | 112 |
| escaped (moved off entirely) | 33 |
| still `gapped:enumerate_failed` | 106 |
| **newly arrived** | **6 — [108, 229, 240, 280, 415, 468]** |

**The 6 "newly arrived" ids are not new failures — they are S1's own
migration destinations.** Every one of the 6 is on S1's own 17-id target
list, moving `gapped:exhausted → gapped:enumerate_failed` (exactly the
table in `PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md` §2): the enumerator now
gets its turn on these goals (S1's whole point) and honestly fails there
instead of being denied a turn — a `gapped:enumerate_failed` outcome is
the CORRECT, intended landing for a goal S1 unstarves and S4/S2 cannot
yet solve, not a regression.

---

## 4. HA5 — the ONE cost-instrument shot

**Primary metric:** mean `attempts` to first accept, over the shared
accepted-task set per comparison.

| arm | n accepted | mean attempts |
|---|---|---|
| FULL-A4 | 106 | 1.2264 |
| NO-ISOLATION | 100 | 1.0800 |
| NO-STRUCTURAL | 134 | 1.1493 |
| arc-3 continuity (FULL-R3, frozen) | 97 | 1.0000 |

**FULL-A4 vs arc-3 continuity, on the 69 tasks accepted in BOTH arms:**
mean diff = **0.0**, bootstrap CI95 = **[0.0, 0.0]** (10,000 resamples).
Not a rounding artifact — every one of the 69 shared tasks has
IDENTICAL `attempts` in both arms (verified directly, zero non-zero
diffs). This is a real, structural finding: the tasks that were already
easy accepts under arc-3 cost exactly the same today — S1/S2/S4 only
change WHICH additional tasks become reachable (HA1/HA4) or which wrong
ones get caught (HA2); they do not cheapen an accept that was already
easy.

**Smallest per-arm ablation's own attempts increase:** 0.0 (both
NO-ISOLATION and NO-STRUCTURAL's own shared-with-FULL-A4 means are
likewise unchanged — the same structural fact, from the ablation side).

**Verdict: NULL.** No CI-separated fall (mean diff is exactly zero, CI
degenerate at zero). Per the prereg's own rule (§5/§6): **this triggers
the fourth-null rule.** The proposal-content line — arc 1 H6/H7c, arc 2
HQ3, arc 3 HR1, and now arc 4 HA5 — nulls a fourth time, under a
preregistered bar designed specifically to avoid rescuing the hypothesis
with a different metric. Per the standing rule, this is registered here
as **CONCLUSIVE for this architecture at this scale**: remaining effort
goes to verdict + search + protocol, not a fifth cost instrument.

**Note on HA3/NO-BACKWARD:** withdrawn per SAMENDMENT A2 — the
"smallest ablation increase" denominator above is computed over the two
REGISTERED remaining arms only (NO-ISOLATION, NO-STRUCTURAL), not three,
a narrowing stated here rather than smuggled in silently.

---

## 5. The arc number

| protocol population | k/n | % | CI95 |
|---|---|---|---|
| pass / runnable (257) | 28/257 | 10.89% | [7.65, 15.30] |
| pass / all-427-sanitized | 28/427 | 6.56% | [4.58, 9.31] |

**Trajectory:** 0.42% (arc 1, Q0-A stress zero-shot) → 7.00% (arc 2,
Q5 FULL) → 8.17% (arc 3, FULL-R3) → **10.89% (arc 4, FULL-A4)**.

Net gain over arc-3 continuity: +9 gains (`gapped:enumerate_failed →
pass` ×8, `gapped:exhausted → pass` ×1), −2 losses (397/404, both
genuine-defect rejections per §2.1) = **+7 net passes**, 21 → 28.

Per SAMENDMENT A4, this number is reported LAST, not first: the pass
rate moved because S4 widened reach (new accepts) while S2
simultaneously REMOVED two label-noise "passes" the benchmark itself
certified wrongly (§2.1) — a mixed movement in the SAME run, exactly as
registered before either number existed.

---

## 6. Migration matrix vs arc-3 FULL-R3 (paired ids)

| move | n |
|---|---|
| `accepted_holdout_fail → gapped:structural_verdict_reject` (S2 catches) | 26 |
| `gapped:enumerate_failed → accepted_holdout_fail` (S4 reach, new traps) | 19 |
| `gapped:exhausted → accepted_holdout_fail` (S1 isolation, new traps) | 9 |
| `gapped:enumerate_failed → pass` (S4 reach, genuine gains) | 8 |
| `gapped:exhausted → gapped:enumerate_failed` (S1 isolation, honest fall-through) | 6 |
| `gapped:enumerate_failed → gapped:no_shape` (S4's downstream shape gap) | 5 |
| `pass → gapped:structural_verdict_reject` (S2, genuine-defect catches — NOT regressions) | 2 |
| `gapped:enumerate_failed → gapped:exhausted` | 1 |
| `gapped:exhausted → pass` (S1 isolation, genuine gain) | 1 |

**New traps introduced: 28** (19+9, all from goals that could not
previously reach an accept at all — reach and verdict strength are
SEPARATE factors, measured directly: widening reach creates both new
correct answers AND new wrong ones, exactly as S4's own notes predicted).
**Traps killed: 26** (S2's own catch). **Regressions vs arc-3: 2 (397,
404) — both genuine-defect rejections, cross-referenced to §2.1, never
double-counted as true regressions.**

**What each phase bought, in one line each:**
- **S1 (isolation):** `gapped:exhausted` class → 2 remaining, both
  independently verified non-starvation (§1).
- **S2 (structural verdicts):** 26 wrong accepts caught pre-accept (25%
  of live wrongness); pass rate fell by exactly the 2 genuine-defect
  catches, by design (§2).
- **S4 (search reach):** 33 tasks escaped `gapped:enumerate_failed`
  entirely on the full run (29.4% of its own isolated 85-bucket); it
  also created 28 new traps — the core/specialised trade, observed
  directly (§3/§6).

---

## 7. Remaining-failure taxonomy, ranked

| rank | class | n/257 | % |
|---|---|---|---|
| 1 | `gapped:enumerate_failed` | 112 | 43.6% |
| 2 | `accepted_holdout_fail` | 78 | 30.3% |
| 3 | `gapped:structural_verdict_reject` | 28 | 10.9% |
| 4 | `pass` | 28 | 10.9% |
| 5 | `gapped:no_shape` | 5 | 1.9% |
| 6 | `runner_exception:TypeError` | 3 | 1.2% |
| 7 | `gapped:exhausted` | 2 | 0.8% |
| 8 | `not_recognized` | 1 | 0.4% |

**Named residuals, ranked by what they represent, not just by count:**

1. **The 36/76 unkillable trap residual (§0.1)** — genuine
   arithmetic/logic errors with no structural or behavioural red flag
   this codebase owns. The single largest honest unknown in the arc.
2. **`br_10_top_of_three` — the one true regression (§2.1(3))** —
   structural rejection terminates a goal instead of INFORMING repair;
   the detector localises the fault perfectly ("ignores parameter c")
   and that information is currently thrown away rather than handed to
   the CEGIS lane. A real design gap, not a measurement artifact.
   Closing it (routing a structural rejection's diagnosis into repair
   rather than a hard gap) is the arc's own clearest next-lever
   recommendation.
3. **S4's classes D/F/G, untouched by design** — sort/combinatorics (7
   ids), string-transform beyond Concat/CaseFold (11 ids), dict
   construction (3 ids) — no primitive exists for any of them; each is
   its own future lever, sized in `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md`
   §1.
4. **S4's class E, an orthogonal axis** — arithmetic depth / missing
   math ops (19 ids) — not a list/iteration problem at all; explicitly
   out of S4's scope.
5. **S4's own downstream shape/reflection gap** — 5 tasks
   (`gapped:no_shape`) plus task 272 (`gapped:exhausted`) where the
   enumerator now composes a candidate (`enumerate_outcome:"ok"`) but a
   later stage does not yet recognize the new embedded Term shape.
6. **3 `runner_exception:TypeError` rows** — unexamined this phase (out
   of scope: this phase measures, it does not debug the pipeline's
   exception paths).
7. **1 `not_recognized` row** — the request cue classifier never minted
   a goal at all; unexamined this phase.

---

## 8. Contamination

`tests/test_mbpp_contamination_migrated.py` (the standing suite): **7/7
passed**, reproduced live by this phase's own gate. `task["code"]` is
stripped at split time; `mbpp_spec.parse_asserts`/`split_rows` never
read it; every substrate this phase boots is fresh and
`OZMA_SEED_PERSIST_DISABLED`; no `domains.teach.teach` call anywhere in
`scripts/arc4_endgame_battery.py`.

---

## 9. Determinism and frozen-artifact integrity

Every arm (FULL-A4, NO-ISOLATION, NO-STRUCTURAL) is twin-run; all three
reproduce byte-identical outcome hashes across both runs (`determinism.
identical: true`). Five frozen artifacts this phase cites are hash-
verified byte-unchanged: `results/mbpp_endgame.json` (arc-2),
`results/mbpp_arc3_endgame.json` (arc-3), `results/
retrieval_oracle_ceiling.json` (R0), `results/arc4_failure_anatomy.json`,
`results/arc4_structural_verdicts.json` — sha256 values pinned in
`tests/test_arc4_endgame_migrated.py`.
