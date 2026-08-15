# `structural_verdict_reject` bucket survey — PREREG (and the whole story:
   NO-GO, the exact property-reject fix pattern ported and measured, zero
   conversions on the full eligible population)

**Date:** 2026-08-16. Base `main @ b8187aa` ("Merge progsyn-property-reject-
survey: property_verdict_reject survey -- GO, +2 genuine MBPP passes"),
verified fresh via `git log --oneline -1 main` before creating the
worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-structural-reject-survey`,
branch `progsyn-structural-reject-survey` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify per this
session's explicit instruction.

Investigation-only, like `HOLDOUT_FAIL_SURVEY_PREREG.md` immediately
before it in this arc. This document is itself the only artifact this rung
produces — `git status --short` in the worktree is empty at the time of
writing (the `results/*` probe JSON this document cites is gitignored,
`.gitignore:25`, matching this arc's own standing convention for scratch
diagnostic output).

---

**HEADLINE, stated up front: NO-GO on any build this rung — but not for
lack of a good candidate. The exact fix pattern the immediately-preceding
`property_verdict_reject` survey built (`ps_property_reject_retrieval_
enumerate_fallback`: give a rejected `retrieved_exemplar` candidate ONE
independent `SynthEnumerate`-sourced second opinion, re-checked against the
SAME detector that rejected the first) was ported to the structural bucket
and measured directly against the FULL eligible population — every one of
the 10 tasks where the fallback is even reachable (5 more are locked out,
§3.2). Result: 10/10 second candidates ALSO fire the identical structural
detector(s) that rejected the first candidate — ZERO conversions, versus
the property mechanism's 2/26. This is not "we didn't try the highest-
prior candidate" — it is the highest-prior candidate, built as a
side-channel probe (not a seed edit) and measured against 100% of the
eligible population, not sampled. The one case where the second candidate
DOES pass the real held-out row (task 109) is traced to a dataset-level
coincidence — MBPP's own test suite for this task only ever samples
`b == len(a)`, so a program that ignores `b` entirely can pass every row
including held-out while remaining wrong in general — and the structural
detector (D3, unread-but-varying declared parameter) is CORRECT to flag it,
not overly strict. No code was changed.**

---

## 1. Re-measurement against the CURRENT baseline, not the stale count

`results/` in this worktree was empty on checkout (gitignored per-tree,
this arc's own standing precedent) — the same 14-file list every recent
rung in this arc has documented needing was copied verbatim from `main`'s
own `results/` before anything would boot (`mbpp_zero_shot_baseline.json`,
`prog_construction_scan.json`, `prog_chunk_mine.json`,
`mbpp_train_diet.json`, `prog_ir_histogram.json`,
`prog_ir_python_coverage.json`, `prog_synthesis_battery.json`,
`mbpp_arc3_endgame.json`, `mbpp_blocker_histogram.json`,
`arc4_endgame.json`, `arc4_backward_probe.json`,
`arc4_failure_anatomy.json`, `arc4_structural_verdicts.json`,
`code_synthesis_baseline.json`).

`scripts/mbpp_endgame_battery.py`, run fresh:

```
full:              73/257  p=0.284047  ci=[0.232408, 0.342046]  det_identical=True
content_stripped:  72/257  p=0.280156  ci=[0.228799, 0.337987]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's own cited baseline (73/72/101).
`scripts/ceiling3_diag_sweep.py` (unmodified) then re-ran against every
non-passing runnable `full`-arm task (184 = 257 − 73):

```
gapped:enumerate_failed          94
accepted_holdout_fail            51
gapped:property_verdict_reject   18
gapped:structural_verdict_reject 15
gapped:exhausted                  2
not_recognized                    1
runner_exception:ValueError       1
gapped:no_shape                   1
runner_exception:TypeError        1
                                -----
total                            184
```

This is **byte-identical to `PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY_
RESULTS.md` §5.1's own "AFTER" taxonomy** — confirming the population has
not moved since that rung landed. **`structural_verdict_reject` is now
15, not 10** — exactly the shift `CEILING_REASSESSMENT_4`'s own citation
in this rung's task brief predicted: task 238 was named explicitly there,
and this sweep confirms the full mechanism: 5 tasks (`56, 224, 238, 292,
311`) moved from `property_verdict_reject` into `structural_verdict_
reject`, because the property-reject survey's own enumerate fallback
candidate for those 5 ALSO fires a D1/D2/D3 structural detector, and the
structural gate wins the race within the same `run_rules()` fixpoint
before the property gate re-fires (exactly as documented in that RESULTS
doc's §5.1, task 238 case study — re-confirmed here for all 5, not just
238, §3.2 below).

**Full task-id list (15):** `56, 68, 83, 86, 93, 109, 224, 238, 239, 269,
285, 292, 311, 420, 454`. The **original 10** (unaffected by the property
fix, byte-identical to `RETRIEVAL_FALLTHROUGH_RESULTS.md`'s own
structural-reject list measured two days earlier): `68, 83, 86, 93, 109,
239, 269, 285, 420, 454`. The **5 new arrivals**: `56, 224, 238, 292, 311`
— confirmed by exact set arithmetic against `PROGRAM_SYNTHESIS_PROPERTY_
REJECT_SURVEY_RESULTS.md` §5.1's own per-task diff table, not re-derived.

## 2. The exact mechanism, read from source

`domains/prog_synthesis.py::compute_structural_facts` (line 1798) is the
"mechanical rim": for a top-level, non-descended, `verified` candidate, it
walks the candidate's reflected Term subgraph and the goal's own revealed
`ExampleRow`s and records three raw facts (never held-out, never decides):

- **D1 `memo_lookup_table`** — the whole program is exactly one
  `ProgReturn` built ENTIRELY from `Lit` leaves combined by `IfThenElse`
  nodes whose own condition is an equality-like literal test, AND the
  reachable leaf VALUES equal the revealed `ExampleRow.expected` value SET
  exactly (≥2 distinct values) — a memoised big-if-else lookup table with
  no generalising logic.
- **D2 `dead_code_free_vars`** — some `Var` is read that is bound NOWHERE
  in the program (not a declared parameter, not any binding form) — a
  reference to nothing.
- **D3 `unread_declared_param`** — a declared parameter is never read
  anywhere in the program, AND its value takes ≥2 distinct values across
  the revealed rows (proves it isn't harmlessly-unused-because-constant).

`seeds/program_synthesis.json`'s four Arc4-S6 rules
(`ps_structural_reject_exclusion_gap`/`_exclusion_reopen`/`_repair_gap`/
`_repair_reopen`, read in full before writing this document) partition on
(which detector fired) × (`ps_construction == 'retrieved_exemplar'`,
literally the same discriminator the property-reject rules use): D1/D2
route to `exclusion` (no salvageable sub-part), D3 routes to `repair`
(names the ignored parameter); a `retrieved_exemplar` source of EITHER
kind goes straight to terminal `gapped` (`ps_structural_reject_exclusion_
gap`/`ps_structural_reject_repair_gap`) because — per those rules' own
comments, citing `PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §4's task-267 stall
— excluding the literal name `'retrieved_exemplar'` cannot distinguish a
next candidate and previously stalled the pipeline live. **This is the
EXACT same "unreopenable source" shape `ps_property_reject_gap` had before
the immediately-preceding rung fixed it**, and every one of the 15 current
`structural_verdict_reject` tasks is `ps_construction == 'retrieved_
exemplar'` (confirmed directly, §1's sweep output, all 15 rows).

**Answering the task brief's central question directly: `structural_
verdict_reject` means a `retrieved_exemplar` candidate that fit every
revealed row was rejected pre-accept by a purely STRUCTURAL (not
semantic/mathematical) heuristic tied to the candidate's own SHAPE — a
literal-dispatch lookup table matching the revealed outputs exactly, or a
declared-and-varying parameter the program never reads — and, because it
came from retrieval, has no reachable "try something else" lane in the
existing exclude/reproposal machinery.**

## 3. The highest-prior candidate, checked first as instructed

### 3.1 Does an analogous `ps_structural_reject_*_reopen`-style enumerate
   fallback already exist? — partially: the EXCLUDE-based reopen lane
   exists (for non-retrieval sources only) and was already measured to
   convert zero

`ps_structural_reject_exclusion_reopen`/`ps_structural_reject_repair_
reopen` (both read in full) already route a NON-`retrieved_exemplar`
structural reject through the standing exclude/reproposal/enum-retry
lane — the exact analogue of `ps_property_reject_reopen`. But
`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §2 (2026-08-01, the rung that
BUILT this reopen lane) already measured its own yield directly: **"(a)
Repaired into a passing accept: `[]` — zero"**, over the 26 tasks that
lane can reach, with the reason stated precisely: excluding the wrong
candidate removes it from consideration but supplies no new
discriminating information when the revealed rows are too sparse to
distinguish more than one candidate shape — verified there directly
against the raw `SynthEnumerate` engine (§4 of that document, the
`br_10_top_of_three` control: excluding the wrong candidate and
re-searching over the SAME 3 revealed rows finds nothing, not a budget
cutoff). **This lane does not apply to any of the 15 current
`structural_verdict_reject` tasks anyway** (all 15 are `retrieved_
exemplar`-sourced, which this lane explicitly excludes) — cited here as
prior evidence, not re-run.

**No `ps_structural_reject_*_retrieval_enumerate_fallback` rule exists in
the current seed** (confirmed: `grep` over
`seeds/program_synthesis.json`'s 74 rule names finds only the property
family's `ps_property_reject_retrieval_enumerate_fallback`, nothing
structural-named). This is exactly the gap the task brief predicted —
the property-reject survey's own §4 residual #1 named it explicitly:
*"Whether an analogous 'does the enumerate candidate ALSO clear D1/D2/D3'
gate would work is a real, plausible, NOT sized future rung."* This rung
sizes and live-measures exactly that gate.

### 3.2 The port, built as a side-channel probe (no seed edit) and
   measured against the FULL eligible population

Method (`structural_probe.py`, reproduced below): for each of the 15
current `structural_verdict_reject` tasks, let `synthesize_from_request`
run to its real, natural terminal `gapped` state on the UNCHANGED
pipeline. Then, on that SAME goal node, apply the exact same four effects
`ps_property_reject_retrieval_enumerate_fallback` uses — `ps_rung_
enumerate := 1.0`, `status := 'enumerate_pending'`, `ps_enum_reserve_used
+= 1`, and reset both shared verdict-computed flags (`ps_st_computed :=
0.0`, `ps_prop_computed := 0.0`, the exact staleness-avoidance fix the
property rung had to find and fix live) — gated on the SAME guard that
rule uses (`ps_rung_enumerate != 1.0` AND `ps_enum_reserve_used <
ps_enum_reserve_budget`). Then call `psy.pump()` again on the SAME
substrate/goal and let the UNCHANGED downstream pipeline
(`run_enumerate → eval_and_record → compute_structural_facts →
ps_structural_clear`/the terminal gap rules) decide, exactly as the real
rule would if it existed.

**Eligibility split, exact and exhaustive (15 total):**

| eligible for the fallback? | n | task ids | why |
|---|---|---|---|
| YES (`ps_rung_enumerate` never touched, reserve unspent) | 10 | 68, 83, 86, 93, 109, 239, 269, 285, 420, 454 | never matched a `PropertyAtom`, so the property fallback never fired for them |
| NO (reserve already spent) | 5 | 56, 224, 238, 292, 311 | the property-reject survey's own fallback ALREADY consumed the one-shot `ps_enum_reserve_budget==1.0` lane producing exactly the enumerate candidate that is now on the goal (its structural facts are what routed these 5 here in the first place, per `PROPERTY_REJECT_SURVEY_RESULTS.md` §5.1) |

**Result over the 10 eligible tasks — 0/10 conversions, 10/10 the SAME
detector fires again:**

```
task  detector(s) on candidate 1 (retrieved)   detector(s) on candidate 2 (enumerate)   status_2
68    d3_unread_declared_param                  d3_unread_declared_param                 gapped
83    d1_memo_lookup_table                       d1_memo_lookup_table                     gapped
86    d1_memo_lookup_table                       d1_memo_lookup_table                     gapped
93    d1_memo_lookup_table + d3                  d1_memo_lookup_table + d3                gapped
109   d3_unread_declared_param                   d3_unread_declared_param                 gapped
239   d3_unread_declared_param                   d3_unread_declared_param                 gapped
269   d1_memo_lookup_table                       d1_memo_lookup_table                     gapped
285   d3_unread_declared_param                   d3_unread_declared_param                 gapped
420   d1_memo_lookup_table                       d1_memo_lookup_table                     gapped
454   d3_unread_declared_param                   d3_unread_declared_param                 gapped
```

**Every one of the 10 second candidates fires the IDENTICAL detector
class as the first** — `any_fired == 1.0` on all 10, never a single
structurally-clean second candidate. `status_2` stays `gapped:structural_
verdict_reject` for all 10; none reaches `accepted`. This is a **full
population measurement, not a sample** — every eligible task was checked,
matching this arc's own "check the whole population, never just the
witness" discipline (the SortBy lesson the property-reject PREREG cites).

**Contrast with the property mechanism's own 26-task measurement (2/26
convert, 100% precision/recall separating correct-from-wrong second
candidates): the structural mechanism converts 0/10, with 100% of second
candidates re-triggering the SAME detector.** The reason is structural,
not incidental (§4).

### 3.3 The one held-out-correct exception (task 109) — a dataset
   coincidence, not an overly-strict check

Checked directly (per the task brief's own candidate cause #3: "an
overly-strict structural check rejecting a genuinely-correct program"):
for all 15 tasks, was the FIRST (retrieved, rejected) candidate actually
correct against the real held-out row despite the rejection? **14/15 no.
Task 109's first candidate IS correct on the real held-out row —** and
its enumerate-sourced second candidate (also D3-flagged, §3.2) is ALSO
correct on the real held-out row.

Read directly (`domains.mbpp_spec.parse_asserts`/`split_rows`, task
109's real revealed + held-out rows, not re-derived from the prompt):

```
revealed: a='011001', b=6, expected=3    (len('011001') == 6)
revealed: a='11011',  b=5, expected=4    (len('11011')  == 5)
held_out: a='1010',   b=4, expected=2    (len('1010')   == 4)
```

**`b == len(a)` in every single row this task's MBPP fixture ever
samples — revealed AND held-out.** The prompt ("find the number of
numbers with an odd value when rotating a binary string the given number
of times") genuinely requires both `a` and `b` in general (rotating fewer
or more times than `len(a)` gives a different count), but this specific
dataset's sampled test cases never exercise that generality — a program
that ignores `b` entirely and just counts `'1'` characters in `a`
(exploiting the mathematical fact that a full cycle of `len(a)`
rotations visits every bit position exactly once) passes every row
including held-out, while being WRONG for any `b != len(a)`.

**D3 is correct to flag this, not overly strict.** Its own guard is
exactly the right one: `b` is a declared parameter that is never read AND
takes ≥2 distinct values across the revealed rows (6, 5) — a genuine,
provable structural argument that the candidate cannot be a correct
GENERAL solution, independent of how many held-out rows it happens to
pass by luck. This is the same "≤1-3 examples cannot distinguish a
coincidental fit from the real relation" phenomenon `HOLDOUT_FAIL_
SURVEY_PREREG.md` named as this arc's single dominant failure shape,
here caught BEFORE accept instead of silently slipping into `accepted_
holdout_fail` — which is exactly what the structural gate exists to do.
**A narrower fallback variant that only re-checked D1 (ignoring D3) would
convert exactly this one task — by rewarding a program that is
demonstrably wrong in general and only coincidentally passes because of
a dataset sampling quirk.** This is not a fix; it is optimising the
number at the cost of the understanding behind it, the exact failure mode
CLAUDE.md's Purpose section opens by naming. Not built.

## 4. Why structural detectors, unlike PropertyAtoms, don't discriminate
   here — the real, general, shared cause

A `PropertyAtom` (perimeter = 4·side, bell numbers, …) is a MATHEMATICAL
RELATION entailed by the prompt, external to and independent of any
candidate's construction mechanism — a correct program must satisfy it BY
DEFINITION, and a wrong one satisfying it at 2-3 independently-chosen
witness points is vanishingly unlikely (measured: 0/26 either direction).
**D1/D2/D3 are not external oracles — they are SHAPE heuristics over the
candidate's OWN structure relative to the goal's OWN revealed rows**: "is
this program literally a big-if-else memo table over the exact revealed
outputs" (D1), "does this program read something unbound" (D2), "does
this program ignore a declared, varying input" (D3). These are properties
of *how hard the spec is relative to how few examples it has*, not
properties of *which mechanism guessed the candidate*. When a spec is
intrinsically underdetermined by 1-3 revealed rows (the SAME root cause
`HOLDOUT_FAIL_SURVEY_PREREG.md` §2 already measured drives the ENTIRE
`accepted_holdout_fail` bucket), retrieval and `SynthEnumerate` are both
drawing from the same small library of degenerate shapes (memoised
lookup tables, partial-parameter dispatch) that fit few examples cheaply
— so it is not a coincidence that both mechanisms independently converge
on the SAME detector, it is the expected behaviour of two different
search procedures hitting the same information-theoretic floor. This is
the exact same conclusion `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §2 already
reached for the EXCLUDE-based reopen lane ("exclude-and-retry from
revealed rows alone cannot manufacture information the revealed rows do
not contain") — this rung shows a completely FRESH, unconstrained second
search (not merely "excluding the first guess") hits the identical wall,
because the missing information was never in the search procedure to
begin with; it is missing from the revealed-row set itself.

This also directly answers the task brief's four candidate causes:

1. **A genuine Term/primitive semantics bug** — not found. Every
   detector firing traces to the candidate genuinely having the shape it
   is accused of (a real memo table, a real unread varying parameter),
   confirmed by direct read of every one of the 15 IRs.
2. **A systematically-missing edge case shared across ≥2 tasks** — not
   found in the sense of a repeated buggy Term; what IS shared is the
   information-theoretic cause (§4 above), not a fixable code defect.
3. **An overly-strict structural check rejecting a genuinely-correct
   program** — checked directly and NOT found; the one held-out-passing
   case (109) is a dataset-sampling coincidence the detector is right to
   distrust (§3.3).
4. **Genuinely idiosyncratic, no shared fix** — the closest match, with
   one refinement: the CAUSE is shared and well-understood (§4), but it
   is a property of the population's information content, not a
   primitive-layer bug, and the one mechanism that could plausibly touch
   it (an independent second construction attempt, re-checked against
   the SAME structural class) was built and measured to convert exactly
   zero of the eligible population.

## 5. The 5 reserve-locked tasks (56, 224, 238, 292, 311) — not
   independently probed further, and why that is the right call

These 5 already used their ONE `ps_enum_reserve_budget` slot via the
property-reject survey's own fallback (§1); their CURRENT `ps_ir` already
IS an enumerate-sourced candidate, and it already fires a structural
detector (that is why they are in this bucket at all — confirmed
directly for all 5 in §3.2's `structural_probe.py` output, `eligible_
for_fallback: false`, `detectors_1` populated). Giving them a genuinely
independent THIRD attempt would require either raising
`ps_enum_reserve_budget` above `1.0` (a shared-lane design change
touching every retrieved-exemplar goal, not scoped to this bucket) or a
second, separately-isolated reserve lane — real, unscoped engineering,
and given §3.2's 0/10 result on the population where a fresh second
attempt WAS cheaply reachable, there is no positive evidence to justify
building it: nothing in this rung's data suggests a third independent
search would behave differently from the second. Named, not built, not
sized further.

## 6. Why no build was attempted — the Occam test from CLAUDE.md, applied

CLAUDE.md's SHAPES-NOT-NUMBERS section asks: is this a quantity that
changes (sd-loop) or a set of allowed moves (Γ)? The candidate mechanism
here — "give a rejected retrieved candidate one independent construction
attempt, re-checked against the SAME rejecting detector" — is exactly the
shape the property-reject rung already built and landed successfully; it
was the right thing to TRY. But CLAUDE.md's Purpose section is equally
explicit that a task, a benchmark, a battery score is a target to aim at,
not the point — and §3.3 shows precisely the shape of harm a forced build
here would cause: the only task it could convert (109) would convert by
rewarding a demonstrably-wrong-in-general program that passes only
because of a dataset quirk, which is optimising the number at the direct
expense of the understanding behind it. Building the rule anyway, knowing
it converts zero tasks for a legitimate reason and one task for an
illegitimate one, would be exactly backwards. Matching this arc's own
recent precedent (`HOLDOUT_FAIL_SURVEY_PREREG.md`, `DICTFROMPAIRS_
RESULTS.md`, `MAX_SIZE_SEAM_PRICING_PREREG.md`, all NO-GO on the evidence):
no code was written, no seed rule was edited, `git status --short` is
empty at the end of this session (the probe scripts are scratch, not
committed, per this arc's own `fallthrough_probe.py`/`property_probe2.py`
precedent).

## 7. What this document does NOT establish

1. Whether raising `ps_enum_reserve_budget` (giving EVERY retrieved-
   exemplar goal a second independent enumerate attempt regardless of
   which detector rejected the first, or a dedicated second reserve lane
   for the 5 property-then-structural tasks) would convert any of the 5
   reserve-locked tasks (§5) — not measured; named as a real but
   unjustified-by-current-evidence candidate for a future rung, should
   new evidence arise.
2. Whether the SAME "does the second candidate ALSO fire" gate would
   behave differently against the `accepted_holdout_fail` bucket (51
   tasks, no structural rejection was ever raised there in the first
   place — no rejection event to route, per `HOLDOUT_FAIL_SURVEY_
   PREREG.md` §6's own identical scoping note for the property-shaped
   version of this same question) — out of scope, not this bucket.
3. Whether the `official` battery arm's own structural-reject population
   differs from `full`/`content_stripped` (the property-reject survey
   found a real, documented, pre-existing protocol difference here) —
   not investigated; this document scopes to the `full`-arm population
   the task brief itself measures against.
4. The exact internal reason retrieval and `SynthEnumerate` converge on
   the IDENTICAL detector (not just "both wrong," but the SAME named
   structural shape) for 10/10 tasks was reasoned about (§4) but not
   traced deeper — e.g., whether both draw from a shared small pool of
   "cheap degenerate shapes that fit 1-3 rows" is a claim about the
   POPULATION's mathematical structure, not verified against the
   enumerator's internal op-preference ordering.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. GO/NO-GO

**NO-GO on any build this rung.** The highest-prior candidate — porting
the property-reject survey's exact fallback pattern to the structural
bucket — was built as a side-channel probe and measured against the FULL
eligible population (10/10 tasks, not sampled): zero conversions, with
every second candidate re-triggering the identical structural detector
that rejected the first. The one case where the second candidate does
pass the real held-out row is a measured dataset-sampling coincidence a
correctly-functioning detector is right to distrust, not a bug to route
around. The 5 reserve-locked remaining tasks were not independently
re-probed (§5) for a stated, evidence-grounded reason. `git status
--short` is empty; no code was changed.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-structural-reject-survey
git log --oneline -1 main   # b8187aa, verify fresh
# results/ housekeeping (gitignored per-tree, copy read-only inputs from main):
#   mbpp_zero_shot_baseline.json, prog_construction_scan.json, prog_chunk_mine.json,
#   mbpp_train_diet.json, prog_ir_histogram.json, prog_ir_python_coverage.json,
#   prog_synthesis_battery.json, mbpp_arc3_endgame.json, mbpp_blocker_histogram.json,
#   arc4_endgame.json, arc4_backward_probe.json, arc4_failure_anatomy.json,
#   arc4_structural_verdicts.json, code_synthesis_baseline.json
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

The fallback-port probe (§3.2, `structural_probe.py`) and the held-out/
dataset-quirk checks (§3.3, `structural_probe2.py`/`structural_probe3.py`)
are scratch scripts (not committed, per this arc's own precedent for
`fallthrough_probe.py`/`property_probe2.py`); their logic is: run
`synthesize_from_request` to terminal, then on the SAME goal node directly
apply `ps_rung_enumerate:=1.0` / `status:='enumerate_pending'` /
`ps_enum_reserve_used += 1` / `ps_st_computed:=0.0` / `ps_prop_computed:=
0.0` (mirroring `ps_property_reject_retrieval_enumerate_fallback`'s own
effects byte-for-byte), call `domains.prog_synthesis.pump()` again, and
read back `read_goal()`'s `structural`/`ir`/`status` fields, comparing
against `mbpp_endgame_battery.holdout_verdict` for the real held-out row.
