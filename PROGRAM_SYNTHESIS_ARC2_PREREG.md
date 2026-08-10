# PROGRAM SYNTHESIS ARC 2 — PREREGISTRATION (Q0 track B)

**Date:** 2026-07-31. Written from the measured Q0 histogram
(`scripts/mbpp_blocker_histogram.py` → `results/mbpp_blocker_histogram.json`,
427 tasks, twin-run byte-identical) and the sibling Q0-A zero-shot baseline
(`PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md`, `results/mbpp_zero_shot_baseline.json`),
per the standing rules (power the gate before the endgame; a baseline is a
list of identities; synthetic-proven mechanism ≠ benchmark value — report
both; eval-subset coverage is part of every claim; no silent caps).
Companion to `PROGRAM_SYNTHESIS_ARC2_PLAN.md` §1-2 and
`PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md` (the curve tables in full).

**Point of departure (frozen, arc 1):** `results/prog_synthesis_battery.json`
arm **MAIN-P7** = 80/125 (.640 [.553, .719]) on the self-authored internal
battery; `results/code_synthesis_baseline.json` C-BATTERY = 7/26. Three
powered nulls (H6, H7a, H7c) all localized to the PROPOSE half's diet
(domain mismatch, trigger poverty, value-domain wall) — arc 1's DECIDE half
never miscarried once. Arc 2's job is content-in-domain, not a fourth
mechanism.

---

## 0. Cross-track reconciliation note (binding)

Q0-A's zero-shot baseline landed concurrently with this document and
changed one design decision below: the assert-split protocol. Q0-A's own
doc (§2) explicitly flagged this as needing reconciliation at this file —
this is that reconciliation, done here rather than deferred to Q5.

**What Q0-A measured, unmodified by this document:** running the arc-1
stack AS-IS on MBPP test (257 tasks) under a **1-revealed-row** split rule
(the first parseable assert revealed, every other parseable assert
held-out) scored **1/240 runnable = 0.42% [0.07%, 2.32%]** (Wilson), and —
the more important finding — the DOMINANT blocker was **not** the
value-domain wall:

| rank | class | n/257 | share |
|---|---|---|---|
| 1 | `accepted_holdout_fail` | 146 | 56.8% |
| 2 | `gapped:enumerate_failed` (the value-domain wall) | 90 | 35.0% |
| 3 | `assert_unparseable` | 17 | 6.6% |
| 4 | `gapped:exhausted` | 2 | 0.8% |
| 5 | `not_recognized` | 1 | 0.4% |
| 6 | `pass` (coincidental — see Q0-A §3) | 1 | 0.4% |

`accepted_holdout_fail` is **single-example overfitting**: every rung that
can accept (codebook / lattice / descend / enumerate) happily fits the ONE
revealed row and dies on the held-outs, at roughly its own base rate. This
is a **protocol artifact interacting with a real mechanism weakness** — an
enumerative synthesizer is structurally underdetermined by one example —
and it is *larger* than the value-domain wall the plan predicted would
dominate. It also means `not_recognized` was never a real bottleneck:
**256/257 test tasks were recognized as write requests zero-shot** (MBPP's
`"Write a [python] function to..."` phrasing already sits in the held cue
vocabulary).

**Resolution — the assert-split protocol is now THREE-WAY, registered
here, arc-wide, superseding this file's earlier working draft:**

1. **PRIMARY (arc-wide; every HQ bar below anchors to this).** Reveal
   **every parseable assert except the last**, in `test_list` order; the
   last parseable assert is the one held-out row. Maximum spec richness a
   3-assert benchmark can offer while still keeping one honest,
   never-revealed verdict row. A task needs ≥2 parseable asserts to be
   *runnable* under PRIMARY (1 revealed minimum + 1 held-out minimum); a
   task with exactly 1 parseable assert is `protocol_excluded:
   insufficient_holdout` (there is no example left to test against); a
   task with 0 parseable asserts is `assert_unparseable`.
2. **SECONDARY-OFFICIAL (comparability only).** All parseable asserts
   revealed, scored on the SAME asserts (no held-out) — the
   published-MBPP-style pass@1 analog. Reported strictly alongside PRIMARY,
   **never merged into a PRIMARY aggregate** (rows are protocol-tagged, the
   arc-1 REPAIR-ORACLE precedent for keeping a protocol-distinct arm out of
   a primary number).
3. **STRESS (registered, optional to run).** Q0-A's own rule — reveal only
   the FIRST parseable assert, hold out the rest — kept as the one-shot
   generalization probe. Q0-A's already-published run (1/240, 0.42%) IS
   this protocol's baseline number; it is **not re-run** under this
   reconciliation, it is re-labeled STRESS and stands as-is.

**Why PRIMARY, not Q0-A's original rule, anchors the arc:** §4 of the
baseline doc measured that revealing only 1 row starves every accepting
rung harder than the internal battery ever does (3–5 revealed rows there),
producing a blocker mass (56.8%) that has nothing to do with the content
Q1–Q4 add. Since **arc 2's central claim (HQ3) is about whether in-domain
paired CONTENT moves the needle**, measuring under a protocol that drowns
every arm in the SAME protocol-induced overfitting floor would make HQ3
undecidable — a Q1 representability win would just relabel
`gapped:enumerate_failed` as `accepted_holdout_fail`, never `pass` (named
explicitly as the risk in Q0-A §6). PRIMARY is the weakest protocol change
that removes this confound without inventing new information (it reveals
strictly fewer rows than SECONDARY-OFFICIAL and never touches the held-out
verdict guarantee arc 1's whole DECIDE-half discipline depends on).

**Cross-parser honesty note.** This document's own histogram (§2) uses an
INDEPENDENTLY implemented assert parser (`scripts/mbpp_blocker_histogram.
py`, never imports Q0-A's `classify_assert`) and the two disagree on scope
in a measured, informative way: this parser recognizes `math.isclose(...)`
as a distinct `float_tolerance` form and peels `set(...)` wraps / raw
`{...}` set literals directly, where Q0-A's parser treats all three as
named-unsupported (`math_isclose` 13 tasks / `set_wrapper` 3 tasks /
`set_literal_value` 2 tasks — cross-checked: this document's own count of
`math.isclose`-form tasks is **13**, an exact match). Both parsers are
honest under their own declared scope; the divergence is why this
document's non-type-coverable count (2/427 — see §2) is far lower than
Q0-A's assert-level `assert_unparseable` count (17/257, test only). This is
itself a Q2 finding: closing `set`-wrapper and raw-set-literal parsing (5
tasks combined) is cheap; `math.isclose` needs a genuine DESIGN decision
(a tolerance-based verdict comparator for float held-outs), not just a
parser fix — named as a Q1/Q2 boundary item, §5.

---

## 1. The Q0 blocker histogram (this document's own measurement)

Full method, all three curves in full, per-split tables: see
`PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md`. Headline facts used below:

- **Program-side (all 427 tasks, the REAL `emit_prog_ir`, never
  approximated):** 316/427 (74.0%) already IR-representable (`ok`); 147/427
  (34.4%) already `predictable` (no undeclared extern). MBPP reference
  solutions are dramatically simpler than the arc-1 repo-code corpus (P0/P2
  measured 56.4%/9.2% on `domains/` — MBPP is small, single-purpose,
  canonical solutions). Sole-blocker mass is high here (123 blocker
  occurrences over 111 blocked tasks, ≈1.1/task) — the opposite of P0's
  repo-corpus finding, and the reason a *joint* curve (not just op/feature)
  is still needed: 111 tasks blocked structurally, a DIFFERENT set of ~278
  tasks are ok-but-unpredictable via extern gaps, and these two axes
  overlap only partially.
- **A measured, non-obvious finding for the Q1 recommendation:** Python's
  `&`/`|`/`^` are overloaded between integer bitwise-and and SET ALGEBRA
  (`set(a) & set(b)` for intersection — task 2 `similar_elements`); the
  REAL emitter has no operand-type awareness at emit time and blocks BOTH
  uses identically as `OpExt:BitAnd`/`OpExt:BitOr`/`OpExt:BitXor`. The
  `bitwise_ops` family this document recommends is therefore NOT pure
  integer bit-twiddling — Q1 must give set intersection/union/symmetric-
  difference a real evaluation path too, or the family's measured mass is
  overstated by tasks it cannot actually fix. (Gated:
  `tests/test_mbpp_histogram_migrated.py::
  test_known_task_2_bitand_is_set_intersection_not_bitwise`.)
- **Value-domain (independent assert parser):** 425/427 (99.5%)
  type-coverable (≥1 fully-parsed assert); only 2 tasks are permanently
  non-type-coverable this arc — task 124 (`angle_complex`, a genuine
  complex-number literal `1j`, out of scope per the plan) and task 596
  (`tuple_size`, compared against `sys.getsizeof(...)`, an
  environment-dependent non-literal expected value, uncomparable by
  construction). This is a MUCH higher floor than arc 1's own
  25pp-over-prediction lesson would suggest to expect — MBPP's asserts are
  overwhelmingly `Compare(Eq)` against literal args/expected (1263/1324
  assert instances), plus a small, fully-characterized tail (12 bare-call
  truthy asserts, 10 `not`-wrapped falsy asserts, 39 `math.isclose`
  asserts — 1263+12+10+39 = 1324, exhaustive) — no boolean-op asserts, no
  chained compares, no other unsupported shape observed anywhere in the
  427-task corpus.
- **Prompt-side:** 95.3% (407/427) of prompts match one of 4 fixed
  request-verb prefixes (`write a [python] function to/that/which`);
  76.3% (326/427) contain ≥1 hit from a 55-word counted constraint
  vocabulary (sorted/prime/palindrome/maximum/... — full list in the
  script). Cross-confirmed by Q0-A's independent recognition measurement:
  256/257 test tasks recognized zero-shot by the EXISTING cue machinery.

## 2. The Q1 op-set recommendation (from the JOINT curve)

**Why the joint curve, not either single-axis curve, drives this
recommendation:** arc 1's own registered lesson (P0→P2) is that a
single-axis histogram over-predicts by ~25pp because sub-construct
features compound. Measured here: the unrestricted `op_feature_curve`
alone reaches 40.5% after just ONE addition (`comprehension_advanced`);
the `value_domain_curve` alone reaches 46% after just `str`. Neither
number is what a Q1 implementer actually gets, because a task typically
needs BOTH its types AND its ops covered simultaneously. The
`joint_curve_q1_scoped` (type-coverable tasks, **excluding** any task that
needs an out-of-plan-scope family — regex, complex numbers, a same-corpus
helper-function extern, or an un-named tail family; 355/425 tasks remain
in scope, 70 excluded) is the HONEST reachable ceiling for Q1 + the
value-domain floor, and its marks are:

| mark | first step ≥ mark | cumulative | additions THROUGH this step |
|---|---|---|---|
| **40%** | step 5 | **40.85%** (145/355) | `bool`, `bitwise_ops`, `str`, `float`, `math_native` |
| **55%** | step 10 | **56.90%** (202/355) | + `slicing`, `string_methods`, `general_builtins`, `tuple[int]`, `container_ctor` |
| **70%** | step 15 | **71.83%** (255/355) | + `collection_methods`, `lambda`, `list[str]`, `comprehension_advanced`, `list[tuple[int]]` |

(Full step-by-step table, all four curves: `PROGRAM_SYNTHESIS_ARC2_Q0_
HISTOGRAM.md` §3-5. Family definitions — which raw `emit_prog_ir` blockers
/ non-native externs / recv-methods group into which family — are in
`scripts/mbpp_blocker_histogram.py`'s `_STRUCTURAL_FAMILY` / `builtin_
family` / `method_family` tables, hand-audited against the measured
extern/blocker distribution, not guessed.)

**Recommendation: target the 55% mark as Q1's primary scope, with the 70%
mark's five additions as a stretch goal if the Rust phase's budget allows**
(P0's own precedent: "recommend the Nth mark since the next pair are
trivial siblings of variants already in the set" — here `collection_
methods`/`lambda` are cheap once `string_methods`/`container_ctor` already
exist, and `comprehension_advanced` is a natural DictComp/CompTargetComplex
extension of the P1 `ComprehensionList`/`ComprehensionGen` variants already
shipped). Concretely, Q1 should implement, regardless of the family's
individual greedy rank (all five value-domain types are ALREADY pinned by
`PROGRAM_SYNTHESIS_ARC2_PLAN.md` §1's scope pin — the greedy curve orders
the OP FAMILIES, not whether to support these types at all):

- **Value domain (fixed by the plan, confirmed reachable by this
  histogram):** `int`, `list[int]` (existing floor) + `str`, `bool`,
  `float`, `none`, `dict`.
- **Op families (histogram-derived, the 55% mark):** `bitwise_ops`
  (INCLUDING set intersection/union/symmetric-difference — see the §1
  finding above, not just integer `&`/`|`/`^`), `math_native` (round, pow,
  ord, `math.sqrt`/`math.pow`/etc. as native oracles), `slicing` (string
  AND list slice-with-step — 25 tasks), `string_methods` (join/replace/
  split/capitalize/strip/upper/lower/... as native oracles, resolving both
  the recv-form and accidental-dotted-Name-receiver cases the real emitter
  currently treats identically to computed-receiver calls), `general_
  builtins` (isinstance/map/all/any/next/enumerate/zip/reversed/iter as
  native oracles — cheap, no new semantics), `container_ctor` (`list`/
  `set`/`tuple`/`dict`/`frozenset` as native oracles — currently the single
  largest non-native extern mass: 35 tasks).
- **Stretch (the 70% mark, if budget allows):** `collection_methods`
  (append/add/sort/extend/... as native oracles), `lambda` (an inline
  anonymous-function IR variant), `comprehension_advanced` (dict
  comprehensions + non-trivial comprehension targets/multi-clause), plus
  `list[str]`/`list[tuple[int]]` reach in `SynthEnumerate`.
- **Named exclusions (explicit, per the plan's own scope pin):** `regex`
  (26 tasks; the plan's risk #5 "no regex" — a genuinely new object model,
  not an op family); a same-corpus helper-function extern (the 12
  multi-def tasks calling a sibling MBPP function — a declared-oracle /
  multi-function synthesis concern, Q3+ territory, not Q1); the long
  `misc_builtin:*`/`stdlib_misc:*` tail (Counter, complex, cmath, bisect,
  heapq, itertools, — each 1-2 tasks, correctly long-tailed exactly like
  P0's corpus tail, not worth a bespoke Q1 mechanism each).

**Set-vs-bitwise decision, explicit:** since task 2's finding (§1) shows
`bitwise_ops` conflates two unrelated capabilities, Q1's `bitwise_ops`
family must be implemented as (a) integer bit ops (`&`/`|`/`^`/`<<`/`>>`
over int operands) AND (b) set algebra (`&`/`|`/`^` over Set operands,
dispatched by the DSL's existing runtime `Value` type, not by static
syntax) — both under the SAME op-family label because they share exactly
one construct-histogram row, but two distinct evaluator code paths.

## 3. HQ1 — value-domain + op-set coverage bar (post-Q1 representable+predictable rate)

**Claim.** Once Q1 ships the fixed value-domain target (§2) plus the
55%-mark op set, the fraction of the 427 MBPP reference solutions that are
BOTH `ok` (IR-representable) AND `predictable` (no undeclared extern, no
un-native recv call) under the REAL `emit_prog_ir`+`ProgEval` scope reaches
**≥45%** (registered bar; measured pre-Q1 floor is 34.4%, measured
post-recommended-Q1-scope ceiling is **52.9% (226/427)** — computed
directly from this histogram's per-task rows: type-domain ⊆
{int,list[int],str,bool,float,none,dict} AND op-families ⊆ the 70%-mark
set — see the derivation table below).

| scope | n / 427 | % |
|---|---|---|
| pre-Q1 floor (measured, `predictable_count`) | 147 | 34.4% |
| + fixed value domain only, no op-family additions | 113 | 26.5%* |
| + 40%-mark op set (`bitwise_ops`, `math_native`) | 147 | 34.4% |
| + 55%-mark op set (Q1's recommended scope) | 190 | 44.5% |
| + 70%-mark op set (stretch) | 216 | 50.6% |
| + 70%-mark + `dict_methods`/`kwargs`/`floordiv_general` (full recommended) | **226** | **52.9%** |

*(the value-domain-only row is LOWER than the pre-Q1 floor because it
recomputes from scratch over the fixed type set with ZERO op-family
credit; it is not a regression, it isolates the type axis.)

**This bar names REPRESENTABILITY/PREDICTABILITY, not accept rate under
search** — a NECESSARY, not sufficient, condition for `pass`. Per the §0
reconciliation, Q0-A's own measurement shows search/overfitting
(`accepted_holdout_fail`, 56.8% under the STRESS protocol) is an
independent, LARGER blocker than the value-domain wall under an
impoverished split — this is exactly why PRIMARY reveals more rows: so
that Q1's representability gains show up as `pass`, not as a taxonomy
shift from `gapped:enumerate_failed` to `accepted_holdout_fail`.

**Null reading:** if the post-Q1 measured representable+predictable rate
(re-run this histogram's program-side pass over the ACTUAL Q1 `emit_prog_ir`)
is <40% (below even the 40%-mark floor measured here), Q1 undershot its own
registered op-family list and the family choices must be revisited before
Q2 starts — reported as a taxonomy of which families the implementation
actually delivered vs this document's list, never silently absorbed.

## 4. HQ2 — spec-fact extraction quality bar (not raw recognition)

**Registered correction from the §0 reconciliation:** the plan's original
framing ("request-recognition rate bar") is measured to be the WRONG
quantity to gate on. Q0-A's zero-shot run found recognition was never the
bottleneck (256/257 test tasks recognized zero-shot); this document's own
prompt-form measurement independently corroborates a similarly high
ceiling (95.3% fixed-prefix match, 407/427). **HQ2's bar is therefore about
SPEC-FACT EXTRACTION QUALITY** (row correctness + signature arity from the
PRIMARY split protocol's revealed asserts), not recognition:

- **Bar:** ≥95% of PRIMARY-runnable tasks (≥2 parseable asserts) produce a
  `Goal`/`ExampleRow` set whose (a) argument COUNT matches the reference
  function's actual parameter count, and (b) every revealed row's argument
  VALUES match the corresponding literal AST nodes exactly (a mechanical
  parse-correctness check, not a semantic one).
- **Recognition remains reported, at a lower and now honestly-labeled
  priority:** ≥90% of all 427 tasks mint a `Goal` (cue-vocabulary match),
  anchored to the measured 95.3%/256-257 ceilings above — a bar that was
  already effectively met at Q0, zero-shot, with no Q2 work at all.
- **Null reading:** if extraction quality is <90% despite recognition
  being met, the residual is in `test_list` PARSING (arity/value mapping),
  not comprehension routing — report the parse-failure taxonomy (mirroring
  §0's cross-parser divergence table) rather than re-tuning cue vocabulary
  that was never the bottleneck.

## 5. HQ3 — the decisive retest: FULL vs CONTENT-STRIPPED on MBPP test

**Unchanged from the plan's own framing — THE arc's central claim.** At Q5,
on the MBPP test subset (PRIMARY protocol, all in-scope tasks, Wilson CIs,
twin-run determinism):

- **FULL** = Q1-Q4 engine/rule scope + the Q3 train-mined diet (chunks +
  triggers + bigrams, in-domain, paired with prompts).
- **CONTENT-STRIPPED** = the identical Q1-Q4 mechanisms, starter codebook
  only, NO train content (the arc-1 `C-CODEBOOK-FROZEN` precedent, same
  protocol as H6/H7c).
- **Confirmed** iff the Newcombe CI for (FULL − CONTENT-STRIPPED) excludes
  zero, on the SAME paired task-id set (never a bare aggregate delta — the
  arc-1 standing rule: a stratum delta is claimed CI-separated only if the
  arms' Wilson 95% intervals are disjoint AND the identity list is
  reported).
- **Registered null (a THIRD null on this exact hypothesis shape, after
  H6 and H7c):** if HQ3 nulls again even with in-domain, NL-paired content,
  this is a finding about the architecture's PROPOSAL GRAIN, not its diet
  — it FORKS to arc 3, registered now per the plan §4 risk #1:
  retrieval-shaped proposal (decode against WHOLE held train programs, not
  chunk shapes) becomes the next hypothesis, not a surprise requiring a
  new plan document.
- **Refusal-taxonomy delta vs Q0** (Q0-A's baseline taxonomy, §0 above) is
  reported alongside the headline number every time: which Q0 classes
  (`gapped:enumerate_failed`, `accepted_holdout_fail`, `assert_unparseable`,
  `not_recognized`) shrank, by how much, paired by task id — never a
  count-only claim (the standing "a baseline is a list" rule).

## 6. HQ4 — internal-battery non-regression (paired, frozen)

**Unchanged, the arc-1 discipline verbatim.** Every arc-2 phase that
touches `seeds/program_synthesis.json` or the engine re-runs the FULL
125-task internal battery; the frozen arms (`FROZEN`, `MAIN`,
`MAIN-POSTFIX`, `MAIN-P7`, `C-CODEBOOK-FROZEN-P7`, `REPAIR-ORACLE`) in
`results/prog_synthesis_battery.json` stay byte-identical hash-pinned; NO
currently-passing row may flip to failing anywhere in the arc (a flip is a
STOP-defect, not a trade, per the arc-1 rule). Reported as a paired
identity-list diff every time, never a bare aggregate.

**Null reading:** any flip is reported immediately as a named regression
with its own root-cause paragraph before the phase that caused it is
considered complete — it is never absorbed into a "net positive" framing.

## 7. Contamination — the reading justification (binding)

Per `tests/fixtures/mbpp/provenance.json`'s `contamination_rule` and the
task's binding CONTAMINATION NOTE: **test-split reference `code`/`test_list`
fields MAY be read for MEASUREMENT (structural feature counting via ast,
the REAL `emit_prog_ir` verdict, assert-literal classification) — they may
NEVER enter any codebook entry, cue-vocabulary token, bigram row, or taught
shape.** The justification, stated precisely:

1. **Measurement is not learning.** `scripts/mbpp_blocker_histogram.py`
   writes ONE artifact — `results/mbpp_blocker_histogram.json` — containing
   feature NAMES, COUNTS, and TASK-ID LISTS only (gated:
   `test_artifact_contains_no_code_or_prompt_keys`, `test_artifact_
   contains_no_verbatim_reference_code_lines`, `test_artifact_contains_
   no_full_prompt_text`). No function body, no assert literal value string,
   no prompt sentence is ever written into the artifact. A downstream
   phase reading this artifact learns "task 9 needs `SliceSubscript`" —
   never "task 9's code is `tmp[i:i+n]`".
2. **The artifact is a SCOPE DECISION, made once, by a human/orchestrator
   reading a report — not a runtime input the synthesis loop consumes.**
   This is the same status as `results/prog_ir_histogram.json` (arc 1's P0
   histogram, which similarly scanned code to pick the P1 IR variant set
   and was never itself loaded by the synthesis loop). Q1's engine work and
   Q2's comprehension work are IMPLEMENTED from this document's
   recommendation text, not from a file the agent's rules read at runtime.
3. **The boundary that WOULD be contamination, and is explicitly guarded
   against:** a codebook entry, cue-vocabulary token, bigram row, or taught
   shape MINED FROM test-split code/prompts and then fed into the
   synthesis loop's PROPOSE half. This never happens here — this script
   has no seed-writing path, no `domains.teach.teach` call, no
   `install_mined_chunks`-style output. Q3's train-split mining (the actual
   learning step) is scoped to `task_id >= 601` only, independently gated
   by `tests/test_mbpp_contamination_migrated.py`'s list-scan (Q0-A's
   mechanism, unmodified by this document).
4. **Cross-check with Q0-A's stronger, mechanically-enforced guarantee:**
   Q0-A's baseline runner physically DELETES `task["code"]` for every
   test-split task before further processing (`_strip_code`) — a stricter
   guarantee than this document's (which reads code but writes no code).
   Both are correct for their own job: Q0-A RUNS the synthesis loop against
   MBPP (so it must never let code near a live substrate); this script only
   COUNTS features offline (so reading code for counting, while writing
   none of it out, is the measurement equivalent of reading a thermometer).

## 8. Standing rules (carried from arc 1, binding for arc 2)

- **Power the gate before the endgame.** Every capability claim from Q1
  onward is measured on an instrument with Wilson CIs (the 427-task MBPP
  set / the 125-task internal battery); deltas within ~3× the per-episode
  step are never claimed as movement.
- **A baseline is a list.** Every aggregate in this document and every
  later arc-2 artifact derives from per-item (per-task) rows; `results/
  mbpp_blocker_histogram.json`'s `per_task` array and `results/mbpp_
  zero_shot_baseline.json`'s `runnable_rows`/`excluded_rows` ARE the
  baselines — the numbers above are re-derivations, gated
  (`test_program_side_counts_derive_from_per_task` et al.).
- **Synthetic-proven mechanism ≠ benchmark value.** Every HQ reports BOTH:
  the engine-level mechanism fact (representability, recognition,
  extraction correctness) AND the benchmark-level accept rate, separately,
  never conflated.
- **Eval-subset coverage is part of every claim.** Every number above
  carries its denominator explicitly (427 total / 425 type-coverable / 355
  Q1-in-scope / 240-or-fewer PRIMARY-runnable at Q5) — never a bare
  percentage.
- **No silent caps.** N is never cut; excluded tasks (out-of-scope
  families, non-type-coverable, protocol-excluded) are always named as an
  id list, never absorbed into a smaller denominator without comment.
- **Protocol boundaries are labelled in the data.** SECONDARY-OFFICIAL and
  STRESS rows/arms carry their protocol tag on every row; no query may
  merge them into a PRIMARY aggregate (mirroring the arc-1 REPAIR-ORACLE
  gate).

## 9. § OUTCOMES (append-only — Q5, 2026-08-01)

Written after every HQ bar registered above was measured. Full detail:
`PROGRAM_SYNTHESIS_ARC2_Q5.md` (this section is the verdict summary only;
every number here derives from `results/mbpp_endgame.json`'s per-task
rows, gated by `tests/test_mbpp_endgame_migrated.py`, 30 passed).

- **HQ1 (§3, value-domain + op-set coverage): CONFIRMED at Q1.5.**
  235/427 = 55.0% representable+predictable, live-measured
  (`PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md`), clearing the ≥45% bar and
  EXCEEDING this document's own 226/427 = 52.9% projected ceiling by
  2.1pp. Null reading (§3's <40% trigger) was never hit.
- **HQ2 (§4, spec-extraction quality): CONFIRMED at Q2.** 100% of the test
  split is PRIMARY-runnable (≥2 parseable rows), 100% arg-count-correct
  (≥95% bar), 99.6% recognized (≥90%-of-427 bar) — every clause met, no
  residual routed to cue-vocabulary re-tuning (`PROGRAM_SYNTHESIS_ARC2_
  Q2_NOTES.md`).
- **HQ3 (§5, the decisive FULL vs CONTENT-STRIPPED retest): NOT
  CONFIRMED — measured at Q5.** Delta (FULL − CONTENT-STRIPPED) =
  −0.39pp, Newcombe 95% CI [−5.01pp, +4.22pp] — spans zero. This is the
  THIRD null on this exact hypothesis shape (after arc-1's H6 and H7c),
  now with in-domain, NL-paired, TRAIN-mined content. Per this section's
  own §5 registered rule, **the retrieval-shaped-proposal fork for arc 3
  is hereby ACTIVATED**: decode against whole held TRAIN PROGRAMS, not
  chunk-grain shapes, is registered as arc 3's next hypothesis. The
  refusal-taxonomy delta vs Q0 is reported in full in
  `PROGRAM_SYNTHESIS_ARC2_Q5.md` §4 (the migration matrix), paired by
  task id as required.
- **HQ4 (§6, internal-battery non-regression): CONFIRMED at every phase,
  including Q5.** `tests/test_prog_synthesis_battery_migrated.py` 21/21
  green at Q5; frozen arms byte-untouched; zero currently-passing rows
  flipped to failing anywhere in the arc. Broader neighbor sweep at Q5:
  422/422 passed across 15 suites, 9.0s.
- **The external number (Q5, both denominators, per the standing
  coverage-denominator rule):** FULL = 18/257 = 7.00% [4.48%, 10.80%]
  over PRIMARY-runnable test tasks; 18/427 = 4.22% [2.68%, 6.56%] over
  the whole sanitized corpus (a coverage statement, not a claim about the
  170 non-test tasks).
