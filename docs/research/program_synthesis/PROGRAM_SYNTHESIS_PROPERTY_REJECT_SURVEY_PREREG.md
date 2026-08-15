# `property_verdict_reject` bucket survey — PREREG

**Date:** 2026-08-16. Base `main @ 5e821f6` ("Merge progsyn-holdout-fail-survey:
survey accepted_holdout_fail (51/257) -- NO-GO, shared CAUSE found, no shared
FIX"), verified fresh via `git log --oneline -1 main` before creating the
worktree. Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-property-reject-survey`,
branch `progsyn-property-reject-survey` — **not merged to `main`, not pushed**,
left for the orchestrator to independently verify per this session's explicit
instruction.

Current live baseline, re-confirmed fresh in this worktree (§1): `full`
71/257, `content_stripped` 70/257, `official` 100/257 — byte-identical to the
task brief's own cited numbers and to `HOLDOUT_FAIL_SURVEY_PREREG.md`'s own
measurement one commit earlier (docs-only commit in between).

---

**HEADLINE, stated up front: this rung finds a real, cheap, evidence-gated
fix — not a Term bug, not a missing primitive, but a missing SECOND-OPINION
mechanism the prior `RETRIEVAL_FALLTHROUGH_RESULTS.md` rung explicitly named
and explicitly declined to build ("a possible narrow future variant — named,
not sized, not recommended this rung"). Every one of the 26
`property_verdict_reject` tasks is a `retrieved_exemplar` candidate that a
held `PropertyAtom` (a hand-authored, self-verified, prompt-entailed
mathematical relation — `domains/prog_property.py`) correctly and honestly
refutes; this is a TRUE POSITIVE population, not a verifier bug and not a
Term semantics bug. But `SynthEnumerate` — an INDEPENDENT construction
mechanism already in the pipeline — finds its OWN candidate for all 26/26 of
these tasks, and re-checking THAT candidate against the SAME fired
PropertyAtom (the exact oracle that caught the first candidate's error)
separates the 2 tasks where the second candidate is genuinely correct from
the 24 where it is ALSO wrong, with 100% precision and 100% recall, zero
exceptions, live-verified against the full population before any code was
written (§3).**

Investigation-only up to §4; §5 builds the fix under full house discipline
(pure seed-JSON rule edit, zero Rust, paired battery, named regression
suite) since this document's own plan survived contact with a live battery
run. See the companion `PROGRAM_SYNTHESIS_PROPERTY_REJECT_SURVEY_RESULTS.md`
for the full build, the general latent staleness bug this rung had to find
and fix to make the plan actually work, and the complete verification trail.

---

## 1. Re-measurement against the CURRENT baseline, not a stale count

`results/` in this worktree was empty on checkout (gitignored per-tree, this
arc's own standing precedent) — `mbpp_zero_shot_baseline.json`,
`prog_construction_scan.json`, `prog_chunk_mine.json`,
`mbpp_train_diet.json`, `prog_ir_histogram.json`,
`prog_ir_python_coverage.json`, `prog_synthesis_battery.json`,
`mbpp_arc3_endgame.json`, `mbpp_blocker_histogram.json`, and (needed later
for the regression suite, §5) `arc4_endgame.json`, `arc4_backward_probe.json`,
`arc4_failure_anatomy.json`, `arc4_structural_verdicts.json`,
`code_synthesis_baseline.json` were all copied verbatim from `main`'s own
`results/` before anything would boot.

`scripts/mbpp_endgame_battery.py`, run fresh:

```
full:              71/257  det_identical=True
content_stripped:  70/257  det_identical=True
official:         100/257  det_identical=True
```

`scripts/ceiling3_diag_sweep.py` (this arc's own standing per-task
diagnostic driver, unmodified) then re-ran against every non-passing
runnable `full`-arm task (186 = 257 − 71) and reproduced the taxonomy
`CEILING_REASSESSMENT_4_PREREG.md`/`RETRIEVAL_FALLTHROUGH_RESULTS.md`/
`HOLDOUT_FAIL_SURVEY_PREREG.md` all already measured, digit for digit:

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

**Full task-id list (26), byte-identical to `RETRIEVAL_FALLTHROUGH_
RESULTS.md`'s own property-reject list measured two days and several rungs
earlier:** `17, 56, 67, 72, 79, 91, 96, 105, 113, 143, 167, 224, 235, 238,
244, 268, 279, 291, 292, 311, 388, 405, 441, 444, 452, 455`. This population
has not moved since `RETRIEVAL_FALLTHROUGH_RESULTS.md` (2026-08-14) despite
three intervening rungs (`IntersectAll`/`UnionAll`, `DictFromPairs` probe,
`accepted_holdout_fail` survey) — none of them touched retrieval,
`PropertyAtom` checks, or this construction lane.

## 2. The exact mechanism, read from source before anything else (per this
   arc's own house style — never assume from the label)

`domains/prog_property.py` (Arc6 Seam D, `PROGRAM_SYNTHESIS_ARC6_M0_CD.md`)
is the "PROGRAM-PROPERTY faculty": prose → structured property → grounded →
checkable clause, `comprehend_theorem`'s shape applied to program-shaped
content instead of group-theoretic content. `seeds/program_properties.json`
holds 36 hand-authored `PropertyAtom`s, each pinned to ONE MBPP task (`perimeter
of a square = 4·side`, `bell numbers`, `divisible by 11`, `star number =
6n(n-1)+1`, …) via `phrases` (all must substring-match the goal's own prompt)
+ `arg_count` + a `reference` function (`domains/prog_property.py`'s
`ref_*` registry — elementary geometry/number theory/string-collection
semantics, external domain knowledge, never the candidate's own logic, never
a held-out row) + 2-3 hand-constructed `witnesses`.

`compute_property_facts` (the CLAUDE.md-compliant "mechanical rim" — records
facts, decides nothing) runs on every top-level, non-descended `verified`
candidate:

1. **MATCH** — the atom's phrases substring-match the goal's prompt.
2. **SELF-VERIFY** (`_self_verify_atom`, the `comprehend_theorem.self_verify_
   clause` precedent) — the reference relation must AGREE with the goal's
   own REVEALED rows (never held-out) on every row. A property the revealed
   data itself contradicts is refused before it can ever fire — the
   refutability gate, and the reason a wrong atom can never wrongly refute a
   correct candidate.
3. **CHECK** (`check_property`) — the CURRENT verified candidate's
   already-reflected Term subgraph is evaluated (the same `ProgEval`/
   `eval_and_record` idiom every verdict path uses) at each witness; the
   FIRST witness whose output disagrees with the reference is the
   refutation.

`ps_property_reject_gap` (`seeds/program_synthesis.json`, Arc6-D,
"unreopenable source") fires when a fired PropertyAtom + `ps_construction ==
'retrieved_exemplar'`: routes straight to terminal `gapped`
(`ps_gap_reason := 'property_verdict_reject'`), never the CEGIS exclude/
reproposal spine. The reason, read directly from the rule's own comment and
from `RETRIEVAL_FALLTHROUGH_RESULTS.md` §1 (which investigated exactly this
precedent): every `retrieved_exemplar` accept shares the ONE literal
construction name regardless of which exemplar produced it, so excluding it
by name cannot distinguish a next candidate — measured live as a genuine
pipeline stall (`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §4, task 267,
`pipeline_stall_nonterminal_status`). The non-retrieval twin,
`ps_property_reject_reopen`, DOES route through that spine, because a
codebook/enumerate-sourced candidate genuinely can propose something
different once excluded.

**Answering the task brief's central question directly: `property_verdict_
reject` means a candidate was VERIFIED (fit every revealed row) and then
REFUTED post-hoc by an independent, self-verified, prompt-entailed
mathematical relation the candidate's own execution disagrees with at a
hand-picked witness — never a held-out row, never the candidate's own
logic. A structurally-fine candidate fails it exactly when it is a
retrieved template that happens to fit 1-3 tiny revealed rows by
coincidence but does not implement the actual relation the prompt names.**

## 3. Per-task classification of all 26 — read the actual mechanism, not the
   label, per this arc's own house discipline

Method: `domains.prog_synthesis.synthesize_from_request` re-run individually
for all 26, reading back `read_goal()`'s own `property` section
(`fired_properties`, `witnesses`: property id, env, got, expected) and the
rejected candidate's `ir`. Each violation was INDEPENDENTLY re-checked two
ways, not merely read off the graph: (a) the reference relation recomputed
in plain Python at the SAME witness env (sanity-checking the atom/witness
pair itself is not the bug), and (b) the rejected candidate's `ir`
re-evaluated directly via `substrate_rs`'s own `evaluate()` at that SAME
env (sanity-checking the recorded `got` is not a read-back artifact).
Script: `property_probe2.py` (reproduce block below).

**Result: 26/26 are TRUE POSITIVES.** Every recomputed reference value
matches the recorded `expected`; every re-evaluated candidate output matches
the recorded `got`; every violation is a genuine, real disagreement between
what the candidate computes and what the prompt's own relation demands. No
atom/witness pair is wrong. **This answers the task brief's four candidate
causes directly: no genuine Term/primitive semantics bug was found anywhere
in the 26 (every mismatch traces to the RETRIEVED CANDIDATE being the wrong
program, evaluated correctly per its own wrong logic — never to a Term
computing its documented semantics incorrectly); no systematically-missing
edge case recurs (each atom targets a DIFFERENT, syntactically unrelated
task — perimeter/bell-number/divisor-count/popcount/tuple-membership/…, by
construction of the 1-task-per-atom design); no overly-strict property
check rejecting a genuinely-correct program was found (self-verification
against revealed rows is exactly the mechanism that would catch this, and
did not, on any of the 26).** This matches `HOLDOUT_FAIL_SURVEY_PREREG.md`'s
own finding for the sibling `accepted_holdout_fail` bucket almost exactly:
retrieval finds a candidate that fits ≤3 revealed rows by coincidence but is
semantically wrong. The difference is that THIS bucket's wrong candidates
get CAUGHT (by the property rung) instead of silently accepted.

### 3.1 The one lever this bucket has that the sibling bucket does not

`accepted_holdout_fail`'s own survey (`HOLDOUT_FAIL_SURVEY_PREREG.md` §6)
correctly declined to build anything: the only lever was "verify a candidate
generalises before accepting," and the existing verification machinery
(D1/D2/structural/property) does not transfer to that failure mode
(`RETRIEVAL_FALLTHROUGH_RESULTS.md` §4). **This bucket is different: the
verification machinery is ALREADY firing, correctly, on the FIRST candidate
— the open question is whether a SECOND, independently-sourced candidate can
be checked against the exact same oracle.** `RETRIEVAL_FALLTHROUGH_
RESULTS.md` §5 already measured that a BLIND fallthrough to `SynthEnumerate`
is decisively NO-GO on this exact population (93.3% false-accept rate
overall; on the 26-task property-reject sub-population specifically,
measured again in this rung, §3.2 below) — but named, in §6, a narrower
variant it explicitly did not build: *"requiring the enumerate result to
also satisfy an independently-held PropertyAtom self-verification the way
`ps_property_reject_gap` already does for retrieval."* This rung sizes and
live-verifies exactly that variant.

### 3.2 Live-verified: does SynthEnumerate's own candidate ALSO clear the
   SAME fired PropertyAtom? — checked against the WHOLE 26-task population,
   never just a witness pair (the SortBy lesson)

Method (`property_probe2.py`): for each of the 26 tasks, after the goal
reaches its natural terminal `gapped:property_verdict_reject` state on the
UNCHANGED pipeline, `domains.prog_synthesis.run_enumerate` is called
directly on the SAME (already-terminal) goal node — the exact
`RETRIEVAL_FALLTHROUGH_RESULTS.md` §3 probe methodology, reused verbatim (no
seed/rule edit, no state-machine change). `SynthEnumerate` finds a candidate
for **26/26** (matching that document's own 100%-candidate-rate finding).
Each enumerate candidate is checked two independent ways: (a) against the
task's REAL held-out row (`mbpp_endgame_battery.holdout_verdict`, ground
truth), and (b) against the SAME fired PropertyAtom(s) that refuted the
retrieved candidate (`check_property`'s own logic, re-run directly on the
enumerate candidate's `ir`).

```
task  enum finds ok?  enum correct (holdout)?  enum violates SAME property?
17    yes             TRUE                     False
56    yes             False                    True
67    yes             False                    True
72    yes             False                    True
79    yes             False                    True
91    yes             False                    True
96    yes             False                    True
105   yes             TRUE                     False
113   yes             False                    True
143   yes             False                    True
167   yes             False                    True
224   yes             False                    True
235   yes             False                    True
238   yes             False                    True
244   yes             False                    True
268   yes             False                    True
279   yes             False                    True
291   yes             False                    True
292   yes             False                    True
311   yes             False                    True
388   yes             False                    True
405   yes             False                    True
441   yes             False                    True
444   yes             False                    True
452   yes             False                    True
455   yes             False                    True
```

**`enum correct (holdout)` and `enum violates SAME property` are EXACT
complements across all 26 rows — zero exceptions.** `PropertyAtom`
agreement is a perfect (on this population), free, already-shipped signal
for whether SynthEnumerate's second candidate is worth accepting. This is
not a coincidence of the two witness tasks — it holds over the WHOLE
targeted population, checked before any code was written, matching this
arc's own standing "check the whole population, not just the witness"
discipline (the SortBy lesson).

**Why this is expected, not lucky:** a `PropertyAtom` is a genuine,
self-verified mathematical relation ENTAILED BY THE PROMPT (perimeter =
4·side is true of every square, not an artifact of 1-3 examples). A
correct program must satisfy it BY DEFINITION. A wrong program satisfying it
at 2-3 independently-chosen witness points by coincidence, while still
disagreeing with the true relation everywhere else, is exactly the kind of
event the self-verification step (§2) already exists to make vanishingly
unlikely — and empirically, on this population, it never happened either
direction.

**Task 17** (`perimeter of a square`): retrieved candidate is a `while`-loop
divisor-check template (an unrelated exemplar, structurally a "does `a` have
a divisor" predicate that returns `True` immediately for any `a`, since
`i=1` always divides — never reaches its own dead tail-return `a*(2+2)`).
Enumerate finds the literal `a*(2+2)` (`Times(a, Plus(2,2))`), holdout-verified
`a=4 → 16`.

**Task 105** (`count true booleans in a list`): retrieved candidate is a
"find first ascending index" template (unrelated), returns `0` when no such
index exists. Enumerate finds `Sum(a)` (`True == 1` in Python, so summing a
boolean list counts the `True`s), holdout-verified `a=[True,True,True] → 3`.

## 4. What this document does NOT establish (checked before building)

1. Whether the SAME "PropertyAtom-gated fallthrough" signal would transfer
   to the sibling `accepted_holdout_fail`/`structural_verdict_reject`
   populations — not tested; this rung is scoped to the population where a
   `PropertyAtom` already fired (26 tasks). `structural_verdict_reject`'s
   own D1/D2/D3 detectors are a different, non-property-shaped signal;
   whether an analogous "does the enumerate candidate ALSO clear D1/D2/D3"
   gate would work is a real, plausible, NOT sized future rung.
2. Why the `official` battery arm's own property-reject population differs
   from `full`/`content_stripped` (gains task 455 instead of 17/105) is
   observed and reported (§ RESULTS) but not deeply investigated beyond
   confirming it is the documented, pre-existing `official` PROTOCOL
   difference (all parseable asserts revealed, no held-out row, "never a
   PRIMARY aggregate member" per the battery's own header) — not a new
   defect this rung introduces.
3. Whether a general reset of the shared `ps_prop_computed`/`ps_st_computed`
   staleness pattern (found live while building this fix, § RESULTS) is
   needed anywhere else in the pipeline — named, not audited beyond the
   single rule this rung's own new mechanism touches.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-property-reject-survey
git log --oneline -1 main   # 5e821f6 (this rung's own base), verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/ceiling3_diag_sweep.py
```

The population-wide property/enumerate-recheck probe (§3.2, `property_probe2.py`)
is a scratch script (not committed, per this arc's own precedent for
`fallthrough_probe.py`); its logic is: for each of the 26 task ids, run
`synthesize_from_request` to terminal, call `domains.prog_synthesis.
run_enumerate` on the resulting goal, then re-run `domains.prog_property.
check_property`'s own witness-evaluation logic against the enumerate
candidate's `ir` for each of the goal's `property.fired_properties`, and
compare both to `mbpp_endgame_battery.holdout_verdict` against the task's
real held-out row.
