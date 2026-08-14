# Retrieved-exemplar fallthrough, sized — RESULTS: NO-GO, decisively, for a new and sharper reason than expected

**Date:** 2026-08-14. Worktree `progsyn-retrieval-fallthrough`, base
`main @ c80f24d`, re-verified fresh immediately before and after the probe
(unchanged both times). **Zero files under `domains/`, `runners/`, or
`seeds/` were touched at any point in this investigation** — confirmed by
`git diff --stat` returning empty against `main @ c80f24d` at the end of
the session (§6). This document answers
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_PREREG.md` §4's own deferred
question with real data instead of a soft qualitative guess.

**Headline finding, stated up front:** SynthEnumerate does NOT hit the
same budget-exhaustion wall on these 60 tasks the way §4.1's soft guess
predicted — it finds a syntactically complete candidate for **60/60
(100%)** of them, every time, well within budget. But **56 of those 60
(93.3%) are WRONG on the held-out row** — a false-accept rate an order of
magnitude worse than anything else measured in this arc. **The original
gate is not just still valid — the probe surfaces a NEW, more general
reason it needs to exist that has nothing to do with retrieval at all.**
**Verdict: NO-GO on a general fallthrough.** A narrow, evidence-gated
variant is named as a possible future micro-rung (§5) but is not itself
sized or recommended to build this rung.

---

## 1. The exact gate, read in its original context

`seeds/program_synthesis.json::ps_structural_reject_exclusion_gap` (line
5661) and `::ps_property_reject_gap` (line 6987) are the two rules that
route a rejected `retrieved_exemplar` candidate straight to terminal
`status='gapped'` rather than letting it retry. Their own comments cite
the reasoning precisely:

> "`ps_construction=='retrieved_exemplar'` means it can't [find a
> different candidate] (every retrieval accept shares that ONE literal
> construction name regardless of which exemplar produced it — excluding
> it can't distinguish candidates and measured live as the S2 stall,
> `PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` Sec.4, task 267)."

Reading `PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md` §4 directly (not inferring
from the seed comment alone): the FIRST attempt at this landing routed a
structurally-rejected candidate through the SAME `status='counterexample'`
retry/exclude machinery a genuine failing revealed-row already uses
(`ps_exclude_failed`/`ps_reproposal`/`ps_ce_exhausted`). Measured live
against the real MBPP battery, **this stalled**: task 267's retrieval
accept got excluded, the goal re-armed to `pending`, and `ps_propose` had
nothing else to offer (`failure_reason: pipeline_stall_nonterminal_status`)
— the retry/exclude state machine was built and tested around a
codebook/enumerate construction NAME being excludable and re-decidable,
and a retrieval-sourced reject doesn't fit that shape. The landed fix
(routing straight to `gapped`) was chosen specifically as a **NO-PARK
guarantee**, verified by re-running the 257-task battery and confirming
zero goals left at a non-terminal status.

**This is the precise, important nuance the task brief's own framing
slightly overstates:** the original reasoning is about why RE-TRYING
RETRIEVAL (via the shared exclude/reproposal lane) doesn't help and
actively stalls — it was never a considered, reasoned rejection of
"try SynthEnumerate as a genuinely different mechanism instead." That
specific question was left open, and `CEILING_REASSESSMENT_2_PREREG.md`
§4 said so explicitly. This document closes that opening — with a result
that reinstates the gate for a different, better-evidenced reason (§3-4).

One more structural fact worth stating precisely, confirmed by reading
`seeds/program_synthesis.json` (line ~243, "Arc3-R1" comment): **retrieval
is tried FIRST for a top-level goal**, before the codebook rung, not as a
last resort after everything else fails. A `retrieved_exemplar` accept
means retrieval found something that passed the revealed-row SCREEN
immediately; the structural/property verdict checks are a SEPARATE,
post-accept verification pass that later disagrees. So the 60 tasks in
this population are not necessarily "too hard for anything else" — they
are tasks where a shallow revealed-row match exists (via retrieval) but is
spurious. This framing matters for §3's result: it predicts SynthEnumerate
would face the exact same shallow-match trap, and it does.

## 2. The 60-task population, reproduced live (not re-cited)

`domains.prog_synthesis.synthesize_from_request` was re-run individually
against all 257 MBPP-test tasks at `main @ c80f24d` (five rungs later than
the reassessment doc's own `4a6b63f` baseline — Program-Synthesis Rung 1's
ten stdlib Term ports, the question_driver/problem-decomposition rungs,
and Bigville work unrelated to this arc all landed in between). The full
per-task outcome distribution:

```
gapped:enumerate_failed        102
pass                            64
accepted_holdout_fail           50
gapped:property_verdict_reject  26
gapped:structural_verdict_reject 10
runner_exception:TypeError       2
not_recognized                   1
gapped:no_shape                  1
gapped:exhausted                 1
                              -----
total                          257
```

(`pass` moved 62→64 and `accepted_holdout_fail` moved 51→50 vs. the
reassessment doc's own numbers — consistent with Rung 1's later stdlib
Term ports converting a few more tasks; `gapped:enumerate_failed`/
`property_verdict_reject`/`structural_verdict_reject` are UNCHANGED,
confirming those three outcome classes are untouched by anything landed
since 2026-08-01.)

Filtering `construction=='retrieved_exemplar'` AND outcome in
`{accepted_holdout_fail, gapped:property_verdict_reject,
gapped:structural_verdict_reject}` reproduces **exactly 60 tasks** — the
same count the reassessment doc reported, five rungs later. Breakdown:

| bucket | n | terminal status today | is this actually "a rejected candidate dead-ending"? |
|---|---|---|---|
| `gapped:property_verdict_reject` | 26 | gapped (honest) | YES — hits `ps_property_reject_gap` |
| `gapped:structural_verdict_reject` | 10 | gapped (honest) | YES — hits `ps_structural_reject_exclusion_gap` |
| `accepted_holdout_fail` | 24 | **accepted** (silently wrong) | **NO** — no rejection signal was ever raised at synthesis time; the pipeline believes it succeeded, and only the battery's external held-out check (which the agent never sees) reveals the error |

**This is a real scoping correction worth stating plainly**: only 36 of
the 60 (property + structural reject) are actually "a rejected exemplar
that dead-ends instead of falling through" in the literal sense the task
brief describes. The other 24 are a DIFFERENT defect — a wrongly-ACCEPTED
retrieval candidate, which a "fallthrough on rejection" design cannot
touch at all (there is no rejection event to route). Both buckets were
probed (§3) since both are plausible fallthrough targets, but the design
implications differ (§5).

Task-id lists for reproducibility: property-reject `17, 56, 67, 72, 79,
91, 96, 105, 113, 143, 167, 224, 235, 238, 244, 268, 279, 291, 292, 311,
388, 405, 441, 444, 452, 455`; structural-reject `68, 83, 86, 93, 109, 239,
269, 285, 420, 454`; accepted-holdout-fail `12, 19, 57, 61, 62, 65, 95,
100, 116, 119, 129, 133, 166, 247, 270, 296, 398, 400, 407, 424, 434, 446,
461, 476`.

## 3. The probe: what SynthEnumerate actually produces for all 60, real data

Method (`fallthrough_probe.py`, in the worktree's own scratch script, not
committed): for each of the 60 tasks, let `synthesize_from_request` run to
its real, natural terminal state on the UNCHANGED pipeline (identical to
what the live battery does — no seed edit, no rule patch, no state-machine
change of any kind), then call `domains.prog_synthesis.run_enumerate`
directly on the resulting (already-terminal) goal node. `run_enumerate` is
a leaf Python helper — it reads the message's `has_example` rows and
whatever `ps_enum_ops` hint the (unconditional, already-fired)
`ps_select_synthesis_operator_shape` rule decided, and evaluates the
`SynthEnumerate` Rust Term exactly as a live rung-3 firing would; it does
not touch the graph rule engine, so this is not a patch to the gate, it is
a direct measurement of "what would enumerate alone produce for this
spec." Each result was then scored against the task's own held-out row
using the SAME comparator the real battery uses
(`prog_synthesis._row_cmp_ok` via `ProgEval`).

**Result, all 60/60:**

```
enum_outcome == 'ok' (SynthEnumerate found A syntactically complete candidate): 60 / 60  (100%)
  of those:
    CORRECT on held-out row:     4 / 60  ( 6.7%)
    WRONG on held-out row:      56 / 60  (93.3%)
```

Per bucket:

| bucket | n | enumerate found something | correct | wrong |
|---|---|---|---|---|
| property/structural reject (36, honestly gapped today) | 36 | 36/36 | **3** (17, 105, 109) | 33 |
| accepted_holdout_fail (24, already silently wrong today) | 24 | 24/24 | **1** (424) | 23 |
| **total** | **60** | **60/60** | **4** | **56** |

**This refutes the reassessment doc's own soft prediction, in an important
and more decisive direction than expected.** §4.1 of
`CEILING_REASSESSMENT_2_PREREG.md` guessed the naive fallthrough would
recover FEWER than the raw 60 because these tasks would mostly hit the
same budget-exhaustion wall the 102 `gapped:enumerate_failed` tasks
already show. **That is not what happens — SynthEnumerate never
exhausts budget on this population (0/60 budget-exhausted, vs. 85/102 in
the enumerate_failed population); it always finds SOMETHING.** The actual
failure mode is sharper and worse: on a spec this hard with only 1-3
revealed rows, an enumerator with today's much richer op-table reliably
finds a SPURIOUS syntactic match, not an empty search. The correct-vs-wrong
programs, for a sample:

```
17  (perimeter of a square)          CORRECT   (a * (2 + 2))                    tested=2255
105 (sum of a list)                  CORRECT   sum(__item for __item in a)      tested=249
109 (count '1' chars in a string)    CORRECT   a.count('1')                     tested=1551
424 (last char of each string)       CORRECT   [__item[-1] for __item in a]     tested=2287

56  (check n is one less than 2*x)   WRONG     0                                tested=2
61  (count substrings with sum in..) WRONG     6                                tested=6
68  (array is monotonic)             WRONG     1                                tested=3
285 (string contains 'a')            WRONG     0                                tested=2
65  (harder numeric task)            WRONG     <complex expr>                   tested=68077
238 (harder numeric task)            WRONG     <complex expr>                   tested=158429
```

11/56 (19.6%) of the wrong accepts are literal bare-integer-constant
programs (`0`, `1`, `6`, ...) — the exact "the enumerator finds a trivial
degenerate program that coincidentally fits 1-3 revealed rows" failure
already named as a real risk class in this arc's own standing discipline
(the D1 `memo_lookup_table` detector exists precisely because this
pathology is known). **But a `tested`-count or complexity floor would NOT
fix this**: median `tested` among the wrong accepts is 3101 (same order of
magnitude as the CORRECT accepts' 249-2287 range), and several wrong
accepts burn 68k-158k candidates before landing on a plausible-looking but
still-incorrect program (tasks 65, 238, and others). **This is exactly the
"a scalar knob is not a simplification — it is the unpaid debt" pattern
CLAUDE.md's SHAPES-NOT-NUMBERS section warns against**: no single threshold
on the numbers `run_enumerate` already exposes (`tested`, term size)
cleanly separates the 4 real answers from the 56 spurious ones.

## 4. Risk assessment — does the original safeguard concern actually apply?

**Yes, more strongly than the question anticipated, and for a broader
reason than the documented 2026-08-01 concern.** The original
Arc4-S6/Arc6-D reasoning was specifically about why RE-TRYING RETRIEVAL
after excluding a bad candidate can't distinguish a next candidate (§1).
This probe shows something the original design never needed to establish,
because it was never tried: **`SynthEnumerate` ITSELF has a 93.3%
false-accept rate on this exact task population — a property of the
population (numerically/structurally hard MBPP prompts with only 1-3
revealed rows), not a property of retrieval specifically.** Whatever
construction mechanism is asked to guess a program from 1-3 examples on
these tasks will find something that fits the examples; almost none of
those somethings generalise.

This directly engages the wrong-accept invariant class
`tests/test_reject_informs_repair_migrated.py` exists to protect (a
structural/property rejection is a REAL signal that must not be silently
discarded or routed around) — and the measured finding here is that the
signal these two gate rules protect (26+10=36 honest `gapped` verdicts) is
NOT a false-negative-prone over-caution; on this population it is, if
anything, UNDER-firing relative to what a naive fallthrough would produce
(the D1/D2/property detectors would need to independently re-fire against
enumerate's OWN candidate to catch it, and — checked directly,
`compute_structural_facts`, `domains/prog_synthesis.py:1635` — that
function requires a REFLECTED Term subgraph (`ps_ir_reflected` edges),
which `run_enumerate` never produces (it only sets a flat `ps_ir` JSON
string); D1 specifically also requires >=2 distinct literal-dispatch
leaves, so it structurally CANNOT catch a bare-constant wrong accept like
tasks 56/61/68/285 above — a single-leaf return never triggers "memo
lookup table"). **The existing verification machinery is shaped for
retrieval's own failure mode (memoised big-if-else dispatch, dead-code
free vars, generic property violations) — not for "trivial candidate
coincidentally fits 1-3 tiny examples," which is `SynthEnumerate`'s own,
different, and here much larger, failure mode.** A gated variant that
reused the existing D1/D2/property checks on enumerate's candidate would
NOT catch most of these wrong accepts, and building a new check shaped for
this specific pathology is real, unscoped engineering, not a small
addition — named in §5, not sized here.

## 5. What a fallthrough would actually do to the MBPP number, if built blind

Computed directly from the probe (not re-run through the full battery
harness — see "what this does not establish" below): if a policy of
"always prefer `SynthEnumerate`'s answer over `gapped`/`accepted_holdout_
fail` whenever it returns `ok`" were applied to exactly these 60 tasks:

- **+4 exact ids would flip to `pass`: `{17, 105, 109, 424}`.** Projected
  `full`-arm delta: 64/257 → a hypothetical 68/257 (+1.6pp).
- **33 of the 36 currently-honest `gapped:property_verdict_reject`/
  `gapped:structural_verdict_reject` tasks would become CONFIDENTLY WRONG
  `accepted` verdicts** — zero change to the MBPP pass-rate NUMBER (both
  `gapped` and `accepted_holdout_fail` already count as "not pass" for the
  battery's own scoring), but a real degradation of what the substrate
  reports about itself: an honest "I could not verify this" becomes a
  silently wrong claim of success. **This is optimizing the benchmark
  number at the direct expense of the understanding behind it** — exactly
  the failure mode CLAUDE.md's opening section names as the project
  getting its own purpose backwards ("if a rung ever optimises the number
  at the cost of the understanding behind it, that rung has the purpose
  backwards, regardless of what the number says").
- **23 of the 24 `accepted_holdout_fail` tasks would simply become
  differently-wrong** (no battery-score change either way, since both
  outcomes are "not pass").

**The MBPP score itself cannot see this cost — which is precisely why it
would be the wrong thing to build for the score.** The real cost is paid
in the gap-awareness/self-concern machinery this project has built
specifically so the agent knows the difference between "I solved this"
and "I don't know" (CLAUDE.md, "THE AGENT FINDS ITS OWN GAPS"). Silently
converting 33 honest gaps into false-confident wrong answers is a direct,
measured violation of that design intent, for a benchmark-only gain the
task's own held-out check cannot distinguish from real competence.

## 6. GO/NO-GO/SIZE call

**NO-GO on a general/blind retrieved-exemplar → enumerate fallthrough.**
Not because the original 2026-08-01 stall-avoidance reasoning is
insufficient (it remains correct and unchanged) but because the probe
found a NEW, independent, and more decisive reason the gate belongs where
it is: on this specific task population, `SynthEnumerate` is not a safer
alternative construction path — it is, if anything, a WORSE one, wrong
93.3% of the time versus retrieval's own already-known failure rate on the
same population (60/194 = 30.9% of remaining failures, all already
counted as failing either way).

**A possible narrow future variant — named, not sized, not recommended
this rung:** a fallthrough gated on a NEW verification signal specifically
shaped for "does this candidate generalise past its tiny revealed-row set"
(e.g., requiring the enumerate result to also satisfy an independently-held
`PropertyAtom` self-verification the way `ps_property_reject_gap` already
does for retrieval, or requiring agreement between the enumerate solution
and a SECOND independent search over a disjoint op subset) could
plausibly raise the true-positive fraction — but building and validating
such a check is itself a real, unscoped design effort (the audit in §4
shows the EXISTING checks do not transfer to this failure mode), not a
control-flow flag flip. This is named exactly as `PROGRAM_SYNTHESIS_
CEILING_REASSESSMENT_2_PREREG.md`'s own §3 map-template-pool candidate was
named — real, plausible, and explicitly NOT built this rung.

**No code was built or changed.** Per the task's own house discipline,
"COMMIT PROMPTLY once any implementation is complete" does not apply here
— there is no implementation, by design, because the evidence did not
support one. This document and its PREREG sibling are the full
deliverable of this rung.

## 7. What this document does NOT establish

1. The probe's "always prefer enumerate when ok" projection (+4,
   `{17,105,109,424}`) was computed directly from the probe's own
   held-out comparator, mirroring the real battery's comparator
   function-for-function — but it was NOT run through the actual
   `mbpp_endgame_battery.py` 3-arm/determinism-checked harness, because
   doing so would require building the real control-flow change this
   document concludes should NOT be built blind. If a future rung builds
   the narrow gated variant named in §5, it must re-verify this projection
   against the real battery, not cite this number as a pre-verified result.
2. The 24-task `accepted_holdout_fail` bucket is a fundamentally different
   defect (a wrongly-ACCEPTED candidate, not a rejected one) from the
   36-task gate-rejected bucket the task brief's framing centres on; this
   document probed both but a real fix for the 24 would need to touch
   retrieval's own accept-time verification, not the reject-fallthrough
   gate at all — out of scope here.
3. Whether a different, non-enumerate construction mechanism (e.g. a
   second independent retrieval pass with a stricter screen, or descent)
   would do better on this specific 60-task population was not measured —
   only `SynthEnumerate` was probed, because that was the specific
   fallthrough named in the source document.
4. This is a single-harness measurement (the probe script), like
   `CEILING_REASSESSMENT_2_PREREG.md`'s own §2 diagnostic sweep — it was
   not independently cross-checked by a second, differently-built harness.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-retrieval-fallthrough
git log --oneline -1 main   # c80f24d, verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 /tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/diag_sweep.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 /tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/fallthrough_probe.py
```

`git diff --stat` against `main @ c80f24d` is empty at the end of this
session — confirmed directly, not assumed.
