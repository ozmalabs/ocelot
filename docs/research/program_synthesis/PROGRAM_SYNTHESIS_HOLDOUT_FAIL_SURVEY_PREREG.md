# `accepted_holdout_fail` bucket survey — PREREG (and the whole story: NO-GO,
   a real shared CAUSE found, no shared FIX exists)

**Date:** 2026-08-16. Base `main @ fd4893f` ("Merge progsyn-maxsize-seam: price
`run_enumerate`'s hardcoded `max_size` seam -- NO-GO, zero yield"), verified
fresh via `git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-holdout-fail-survey`, branch
`progsyn-holdout-fail-survey` — **not merged to `main`**, left for the
orchestrator to independently verify (this session's explicit instruction:
never merge to `main`, never `git stash`, never push).

Investigation-only, like `MAX_SIZE_SEAM_PRICING_PREREG.md` immediately before
it. This document is itself the only artifact this rung produces — `git diff
--stat` against `main @ fd4893f` is empty except for this file, confirmed
directly at the end of the session.

---

**HEADLINE, stated up front: NO-GO on any build this rung. The
`accepted_holdout_fail` bucket (re-measured live: 51/257, exact-id-identical
to `CEILING_REASSESSMENT_4`'s own count) DOES share one root CAUSE across
essentially the whole population — 51/51 tasks are a construction lane
(retrieval, raw top-level `SynthEnumerate`, a descent-hole's own
`SynthEnumerate` call, or one codebook CEGIS-repair accept) finding a
program that syntactically fits 1-3 revealed rows but is semantically the
WRONG program — but this shared cause has NO shared FIX, because it is not a
primitive bug: every one of the 51 wrong-accepted programs is a DIFFERENT,
idiosyncratic wrong composition (`Max(2,a[0])`, `b*(b==3)`, `a*min(3,a//3)`,
a bare `Lit(0)`, …), not one repeated buggy Term or one repeated missing edge
case. The only lever that could move any of these — a stronger
generalisation-verification check gating ACCEPT, not a Term fix — was
already investigated, priced, and explicitly NOT recommended two days
earlier by `PROGRAM_SYNTHESIS_RETRIEVAL_FALLTHROUGH_RESULTS.md` for the
retrieval-sourced 24/51 of this same bucket (93.3% false-accept rate,
existing D1/D2/property checks structurally do not transfer, building a new
one is "real, unscoped engineering," and even if built it converts
`accepted_holdout_fail`→`gapped`, never →`pass`, since the underlying
candidates are actually wrong). This rung's own fresh, per-task read of the
REMAINING 27/51 tasks (not covered by that document's own scope) finds the
identical phenomenon with zero exceptions — extending that NO-GO to the full
bucket rather than reopening it. A genuine, secondary, diagnostic-hygiene
defect was found en route (§4) and is named, not fixed, as out of scope for
a primitive-layer rung.**

---

## 0. Re-measurement against the CURRENT baseline, not the stale count

`scripts/mbpp_endgame_battery.py`, freshly run in this worktree (this
worktree's `results/` was empty on checkout — gitignored per-tree, per this
arc's own standing precedent; `mbpp_zero_shot_baseline.json`,
`prog_construction_scan.json`, `prog_chunk_mine.json`,
`code_synthesis_baseline.json`, `mbpp_train_diet.json`,
`prog_synthesis_battery.json`, `mbpp_arc3_endgame.json`,
`arc4_structural_verdicts.json` copied verbatim from `main`'s own `results/`
before anything would boot, same housekeeping `DICTFROMPAIRS_RESULTS.md` §6
and `MAX_SIZE_SEAM_PRICING_PREREG.md` §5 both already documented needing):

```
full:              71/257  det_identical=True
content_stripped:  70/257  det_identical=True
official:         100/257  det_identical=True
```

Confirms the task brief's cited live baseline exactly. `scripts/
ceiling3_diag_sweep.py` (this arc's own standing per-task diagnostic driver,
re-used unmodified — same `boot_full()`, same `synthesize_from_request` call,
same held-out comparator as the battery) then re-ran against every
non-passing runnable `full`-arm task (186 = 257 − 71) and reproduced the
**exact** `CEILING_REASSESSMENT_4` outcome taxonomy, digit for digit:

```
gapped:enumerate_failed          94
accepted_holdout_fail            51
gapped:property_verdict_reject   26
gapped:structural_verdict_reject 10
not_recognized                    1
runner_exception:ValueError       1
gapped:no_shape                   1
gapped:exhausted                  1
runner_exception:TypeError        1
                                -----
total                            186
```

**51 `accepted_holdout_fail` tasks, byte-identical count to the stale
citation** — the population did not shift between `CEILING_REASSESSMENT_4`
and this rung (`IntersectAll`/`UnionAll`, `DictFromPairs`, and the
`max_size` probe all landed/were-tested in between and none touched this
bucket, confirmed by the taxonomy's other three big buckets — 94/26/10 —
also matching exactly).

Full task-id list (51): `12, 19, 57, 61, 62, 63, 65, 66, 70, 95, 99, 100,
101, 116, 119, 125, 129, 130, 133, 162, 166, 168, 223, 245, 247, 250, 253,
267, 270, 271, 284, 286, 287, 294, 296, 306, 398, 400, 407, 409, 424, 425,
431, 434, 438, 446, 461, 463, 464, 471, 476`.

## 1. First split: `construction` field, then a discovery that field is
   unreliable for the rest (§4) — reclassified by the REAL producing rung

Grouping raw `goal["construction"]` (`ceiling3_diag_sweep.json`'s own
recorded field) gives:

| `construction` | n | task ids |
|---|---|---|
| `retrieved_exemplar` | 24 | 12, 19, 57, 61, 62, 65, 95, 100, 116, 119, 129, 133, 166, 247, 270, 296, 398, 400, 407, 424, 434, 446, 461, 476 |
| `None` | 6 | 99, 125, 130, 253, 294, 464 |
| `sum_of_two` | 6 | 162, 267, 271, 286, 287, 306 |
| `mck_prog_aug_assign_n2_q3` | 4 | 63, 70, 250, 284 |
| `count_of_list` | 4 | 66, 168, 425, 438 |
| `product_of_two` | 3 | 409, 463, 471 |
| `mck_prog_assign_var_n2_q6` | 1 | 101 |
| `mck_prog_assign_var_n2_q9` | 1 | 223 |
| `ck_prog_if_stmt_n1_q0` | 1 | 245 |
| `ck_prog_if_stmt_n1_q1` | 1 | 431 |

The `retrieved_exemplar` 24 is **byte-identical, task-id for task-id,
verified directly (`set` equality, not eyeballed)**, to
`RETRIEVAL_FALLTHROUGH_RESULTS.md` §2's own `accepted_holdout_fail` list
(`12, 19, 57, 61, 62, 65, 95, 100, 116, 119, 129, 133, 166, 247, 270, 296,
398, 400, 407, 424, 434, 446, 461, 476`) — zero engine drift on this
subpopulation across the two intervening rungs (`IntersectAll`/`UnionAll`,
`DictFromPairs`, `max_size` probe). That document already measured this
24-task-class population's mechanism directly and decisively (§3 below cites
it rather than re-deriving it).

The other 27 needed fresh investigation — `sum_of_two`/`product_of_two`/
`count_of_list`/`mck_prog_*`/`ck_prog_*` are NOT literal template names being
naively applied (initial hypothesis, retracted in place, §4): they are
`code_write_constructions.json`/mined-train-diet `ShapeSignature` names the
CODEBOOK rung (`ps_construction`, rung 1 of the Occam ladder documented in
`seeds/program_synthesis.json`'s own top-of-file comment) proposed **and
then either failed to verify or only partially solved** — but the attribute
is never cleared/updated when a LATER rung (top-level `SynthEnumerate`, or a
descent hole's own `SynthEnumerate`) produces the actual accepted candidate.
Reading each of the 27 tasks' full `read_goal()` output directly
(`domains.prog_synthesis.synthesize_from_request`, same call the battery/diag
sweep both use — `rungs`, `holes`, `descend_kind` fields, not previously
read by the diag sweep's own row shape) resolves what ACTUALLY produced each
accept:

| real producing mechanism | n | task ids |
|---|---|---|
| raw top-level `SynthEnumerate` (`construction=None`, `rungs={'enumerate':1.0}`, no codebook/descend at all) | 6 | 99, 125, 130, 253, 294, 464 |
| codebook proposes a skeleton whose hole is `refused`/`failed`; top-level `enumerate:1.0` ALSO fires and its own accept is what's read back (codebook name is a STALE label on the goal, §4) | 15 | 63, 70, 101, 223, 245, 250, 267, 271, 284, 287, 409, 431, 438, 463, 66 |
| codebook proposes a skeleton; a descent HOLE's own `SynthEnumerate` sub-call solves+splices (`hole_status:'folded'`) — a genuinely descent-produced accept, still a coincidental few-row fit at the hole grain | 5 | 168, 286, 306, 425, 471 |
| codebook rung alone (`rungs={'codebook':1.0}` only, no descend/enumerate) — task 162, already independently documented | 1 | 162 |

24 + 6 + 15 + 5 + 1 = **51**, exhaustive, no residual category.

## 2. Live-verified IR for every one of the 27 non-`retrieved_exemplar` tasks
   — every accept is a DIFFERENT, idiosyncratic wrong program

Method: `domains.prog_synthesis.synthesize_from_request` re-run individually
for all 27, reading `r['ir']` (the accepted candidate, real pipeline, not a
forced/hand-built term) and `mbpp_endgame_battery.holdout_verdict` (the SAME
comparator the live battery uses) against each task's real held-out row.
Representative sample (full 27/27 read directly, not sampled — every one
shows the same signature):

```
66  (count positive numbers in a list)        accepted: Max(2, a[0])
                                               revealed: [1,-2,3,-4]->2, [3,4,5,-1]->3
                                               holdout:  [1,2,3,4] expected 4, got 2
168 (count occurrences of a number in list)   accepted: b * (b==3)          -- 'a' is DEAD, never read
                                               revealed: (a=[1,2,3],b=4)->0, (a=[..],b=3)->3
                                               holdout:  (a=[0,1,2,3,1,2],b=1) expected 2, got 0
162 (sum n-2i for i=0..n//2)                  accepted: a * min(3, a//3)
                                               revealed: 6->12, 10->30
                                               holdout:  9, expected 25, got 27
267 (sum of squares of first n odd numbers)   accepted: IfThenElse(a-2, then=35, other=10)
                                               revealed: 2->10, 3->35
                                               holdout:  4, expected 84, got 35
284 (all list items equal to element)         accepted: Lit(0)                -- bare constant, D1-class
                                               revealed: (['green',...],'blue')->False, ([1,2,3,4],7)->False
                                               holdout:  (['green']*4,'green') expected True, got 0
286 (largest sum of contiguous subarray,      accepted: a size-573 IR, still a coincidental 2-row fit
     3-arg spec)                              holdout row disagrees (expected -1, got 30)
409 (min product from pairs of tuples)        accepted: 2 * IndexAt(0, sorted-by-something(a))
                                               holdout:  expected 100, got 40
463 (max product subarray)                    accepted: 180 - (112 - ...) -- arithmetic constant-fit shape
                                               holdout:  expected 80, got -224
```

Every one of the 27 is a **structurally different wrong composition** (Max,
IfThenElse, a bare Lit, Times/Eq, IndexAt chains, size-573 multi-statement
IR for the 3-arg tasks). **This is the diagnostic signature of "search finds
whatever fits ≤3 examples," not "one repeated buggy Term."** No two tasks in
this 27-task set share the same wrong construction; several (168, 284, and
by inspection others) have the classic D1 "dead free variable"/"bare
constant" pathology `RETRIEVAL_FALLTHROUGH_RESULTS.md` §3 already named for
its own 56-wrong-accept population (11/56 there were literal bare integer
constants).

**No Term semantics bug was found anywhere in this 27-task read.** Every
mismatch traces to the ACCEPTED PROGRAM being semantically the wrong
program, evaluated correctly per its own (wrong) logic — never to a Term
(`Max`/`Fold`/`Count`/`IndexAt`/`Eq`/`IfThenElse`/`Times`/…) computing its
own documented semantics incorrectly. This directly answers the task
brief's central question: **wrong primitive semantics — not found; a
systematically-missing edge case (off-by-one, empty-input, `dict()`
duplicate-key, negative-index slicing) shared across ≥2 tasks — not found;
genuinely idiosyncratic per-task wrong programs sharing one CAUSE
(information-theoretic underdetermination from ≤3 examples) but not one
FIX — confirmed, 27/27, zero exceptions.**

## 3. The retrieval-sourced 24 — cited, not re-derived, and the reason that
   is the right call

`RETRIEVAL_FALLTHROUGH_RESULTS.md` (2026-08-14, two rungs before this one)
already measured this exact 24-task population's mechanism directly and at
scale: forcing `SynthEnumerate` on the same specs (a hypothetical
"fallthrough" design) finds a syntactically-complete candidate 100% of the
time, and it is **WRONG on the held-out row 93.3% of the time** (56/60
across its own slightly wider 60-task probe population, which strictly
contains this rung's 24). That document further showed the existing D1
(memo-lookup-table)/D2/structural/property verdict checks **cannot
structurally transfer** to catch this failure mode (`run_enumerate` never
produces the `ps_ir_reflected` Term subgraph those checks require; D1 also
needs ≥2 distinct literal-dispatch leaves, so it cannot catch a single-leaf
bare-constant wrong accept like task 284 above) — and concluded a fallthrough
or new verification gate would be "real, unscoped engineering," explicitly
not sized or built.

**This rung does not re-run that probe.** Re-deriving an already-measured,
two-days-fresh, same-population result would not change the conclusion and
would not honour this arc's own single-variable-rung discipline any better
than citing it precisely does. What THIS rung adds is confirming (§1, §2)
that the SAME phenomenon — not merely a similar one — extends past
retrieval's own 24 to cover the FULL 51-task bucket, closing
`RETRIEVAL_FALLTHROUGH_RESULTS.md` §7 residual #2 verbatim (*"whether the
remaining `accepted_holdout_fail` tasks share this shape wasn't checked"*).

## 4. A genuine, secondary, out-of-scope finding: `ps_construction` is a
   STALE label on 20/27 of the non-retrieval tasks — named, not fixed

Discovered while classifying §1's 27-task remainder: `goal["construction"]`
(read by `ceiling3_diag_sweep.py`, and by extension every prior
`CEILING_REASSESSMENT_*` document's own per-task table) reports the NAME of
whichever codebook `ShapeSignature` the rung-1 propose step picked —
**even when that skeleton's own hole later returns `refused`/`failed` and
the actually-accepted candidate comes from a completely different rung**
(top-level `SynthEnumerate`, or in one case the codebook rung's own internal
repair). Confirmed directly: task 168's `ps_construction` reads
`count_of_list` (the `Fold(...,body=Plus(acc,1))` len-of-list template), but
its accepted `ir` (§2) is `b * (b==3)` — the `count_of_list` Fold assignment
(`v1 = Fold(...)`) is present in the IR tree as a **dead, unread local
variable**, never referenced by the actual `ProgReturn`.

**This is a diagnostic/observability defect, not a correctness defect** — it
does not change what candidate gets accepted, does not change any MBPP
outcome, and does not affect the held-out verdict (which evaluates the real
IR, not the `construction` label). Its cost is entirely borne by anyone
reading `construction` as "the mechanism that solved this task" — which
`ceiling3_diag_sweep.py` and prior `CEILING_REASSESSMENT_*` documents' own
per-task tables implicitly do. **Named here, not fixed**: fixing it would
mean either (a) clearing/overwriting `ps_construction` when a later rung's
accept supersedes the codebook propose, or (b) adding a second attribute
(e.g. `ps_accept_rung`) recording the rung that actually produced the
terminal accept — both are real, `seeds/program_synthesis.json`-rule-level
changes (per CLAUDE.md, a decision over graph state belongs in a Rule, not a
Python read patch), out of scope for a primitive-layer, single-variable
survey rung, and or independent value from whether this rung's own
NO-GO holds (§2's direct IR reads do not depend on the label being
accurate — they read past it).

## 5. Task 162 — the one pure-codebook accept, already independently
   documented

`rungs={'codebook':1.0}` only (no descend, no enumerate) for task 162, and
its accepted IR (`a * min(3, a//3)`) does not match `sum_of_two`'s own
literal `Plus(a,b)` ground template — the codebook rung's own CEGIS
repair/retry evidently explored past the first literal proposal before
landing on this fit. This exact task and exact mechanism were already
independently named by `PROGRAM_SYNTHESIS_ARC5_FINAL.md` (row 142 of its own
table): *"162 | `gapped:enumerate_failed` → `accepted_holdout_fail` |
`moves_engaged_not_solved` — an honest 2-row coincidental fit MOVE B finds
and the held-out check correctly catches (NOT a wrong pass)."* Not
re-investigated further here — it is the SAME phenomenon as every other task
in this bucket (a coincidental few-row fit, correctly caught by the held-out
check, already understood as expected/honest behaviour of a bounded
exploratory search lane), not a new or different defect class.

## 6. Why no build was attempted — the Occam test from CLAUDE.md, applied

CLAUDE.md's SHAPES-NOT-NUMBERS section asks, before adding any new
mechanism: is this a quantity that changes (sd-loop: decode/recognise/
transform/infer/mint) or a set of allowed moves (Γ: a production)? Neither
applies here in a way that yields a CHEAP fix. The candidate lever this
bucket implies — "verify a candidate generalises past its tiny revealed-row
set before accepting" — is a genuinely new VERIFICATION mechanism, not a
missing primitive and not a missing admissible move; §3 already measured
(via `RETRIEVAL_FALLTHROUGH_RESULTS.md`) that the existing verification
machinery (D1/D2/structural/property checks) does not transfer to this
failure shape, and building a new one was explicitly sized as "real,
unscoped engineering" there. Critically, **any such check can only ever
convert `accepted_holdout_fail` → `gapped`** (an honest "I don't know"),
**never → `pass`** — the accepted candidates are actually wrong, not merely
unverified-but-secretly-right (§2's holdout mismatches are real semantic
disagreements, not comparator artefacts). Building it would improve the
substrate's self-honesty (real, valued by this project's gap-awareness
design, CLAUDE.md "THE AGENT FINDS ITS OWN GAPS") but move the MBPP NUMBER
by exactly zero — and would still require design work this single-variable
survey rung is not scoped to do (a generalisation check shaped for
"trivial/coincidental fit," which the prior rung already showed the
codebase does not yet hold, for either the retrieval-sourced or the raw-
enumerate-sourced half of this bucket).

**Matching this arc's own recent precedent** (two consecutive honest NO-GOs,
`DICTFROMPAIRS_RESULTS.md` and `MAX_SIZE_SEAM_PRICING_PREREG.md`, both
explicitly declining to force a build against the evidence): no code was
written, no Term was touched, no seed rule was edited. `git diff --stat`
against `main @ fd4893f` is empty except for this document.

## 7. What this document does NOT establish

1. Whether a NEW, purpose-built generalisation-verification mechanism
   (§3, §6) is worth building as its own, separately-scoped rung — named as
   a real candidate by BOTH this document and its predecessor, not sized,
   not attempted. Any such rung would need to (a) design a check that
   transfers to bare-constant/dead-free-variable/coincidental-numeric-fit
   patterns across retrieval, top-level enumerate, AND descent-hole
   enumerate (three different call sites, confirmed in §1), and (b) accept
   up front that its yield is `accepted_holdout_fail`→`gapped` conversions
   only, zero MBPP score movement, valued purely for the agent's own
   self-honesty per CLAUDE.md's gap-awareness design.
2. The `ps_construction` staleness defect (§4) — named and evidenced on 20/27
   tasks, not fixed, not sized as its own rung. Whether it affects any
   OTHER prior document's per-task table in this arc (several
   `CEILING_REASSESSMENT_*` tables cite `construction` values) was not
   audited here; this document only establishes that the field is unreliable
   as a mechanism label, not which specific prior citations it invalidates.
3. Task 286/306's full accepted IR (§2's 573/631-byte trees, 3-4 argument
   specs) was read in full during this investigation but is not reproduced
   in full here — both were confirmed to be coincidental-fit accepts with a
   real held-out disagreement, matching every other task in the bucket; the
   exact internal composition was not further analysed beyond that
   confirmation.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. GO/NO-GO

**NO-GO on any build this rung.** The `accepted_holdout_fail` bucket (51/257,
re-measured live, exact-id-identical to the cited baseline) is confirmed,
by direct per-task evidence covering 100% of the population (not sampled),
to share exactly ONE root cause — construction-lane acceptance of a
candidate that fits ≤3 revealed rows but is semantically the wrong program —
across all four producing mechanisms (retrieval, raw enumerate, descent-hole
enumerate, one codebook CEGIS accept). It does NOT share one fixable
primitive-layer bug: every accepted wrong program is structurally distinct,
no Term semantics defect was found, and no systematically-missing edge case
recurs across ≥2 tasks. The one lever that could touch this bucket (a new
generalisation-verification gate) was already priced by
`RETRIEVAL_FALLTHROUGH_RESULTS.md` and found to require unscoped design work
for a yield that can only ever be honest-gap conversions, never new passes —
this document extends that finding's scope from 24/51 to 51/51 and does not
overturn its conclusion. A genuine secondary diagnostic-hygiene defect (§4)
was found and named, not fixed, as out of this rung's scope.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-holdout-fail-survey
git log --oneline -1 main   # fd4893f, verify fresh
# results/ housekeeping (gitignored per-tree, copy read-only inputs from main):
#   mbpp_zero_shot_baseline.json, prog_construction_scan.json, prog_chunk_mine.json,
#   code_synthesis_baseline.json, mbpp_train_diet.json, prog_synthesis_battery.json,
#   mbpp_arc3_endgame.json, arc4_structural_verdicts.json
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

Per-task mechanism read (§1/§2, any task id from the 27-task remainder):
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 -c "
import sys, json
sys.path.insert(0,'runners/dsl/python'); sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import substrate_rs as srs
import domains.prog_synthesis as psy
import domains.prog_chunk_growth as pcg
import domains.mbpp_spec as ms
import mbpp_endgame_battery as battery

s = srs.Substrate()
ag = s.add_node('Agent', {})
psy.ensure_program_synthesis(s, s._inner, ag)
pcg.install_mined_chunks(s)
pcg.ensure_mbpp_train_diet(s, s._inner, ag)

tasks = {t['task_id']: t for t in json.load(open('tests/fixtures/mbpp/sanitized-mbpp.json'))}
task = tasks[168]   # any of the 27
parsed = ms.parse_asserts(task)
spec = ms.split_rows(parsed['rows'], 'primary')
r = psy.synthesize_from_request(s, ag, task['prompt'], spec['revealed'])
print('construction=', r['construction'], 'rungs=', r['rungs'], 'holes=', r['holes'])
print('ir=', json.dumps(r['ir']))
print('holdout=', battery.holdout_verdict(r['ir'], spec['held_out']))
"
```

`git diff --stat` against `main @ fd4893f` is empty except for this document
at the time of writing.
