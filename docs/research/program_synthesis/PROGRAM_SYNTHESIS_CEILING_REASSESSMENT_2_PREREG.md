# Re-running the structural ceiling at 62/257 — where is the NEXT bottleneck — PREREG

**Date:** 2026-08-14. Base `main @ 4a6b63f` ("Abusive-relationship line R5:
leaving/recovery (the hopeful half)"), verified fresh via `git log --oneline
-1 main` immediately before starting — re-verified again mid-task per the
house discipline's own warning that main moves from unrelated concurrent
Bigville work. This is a **fresh investigation, not a continuation of any
named rung** — today's whole priced-gap queue (SetLit/DictItems, Sort,
SetMap/Intersect/Union, DictItems/SortBy, the `SynthesisOperatorShape`
tiebreak bug, task 242's retrieval drift) is confirmed landed on `main`
before this document's own measurement begins.

**One thing WAS built during this investigation** (contrary to the task's
default "investigation only" framing) — a single, same-day repeat of an
already-landed precedent, not a new design; see §5 and its own RESULTS doc,
`PROGRAM_SYNTHESIS_CEILING2_PLAIN_FRACTION_RESULTS.md`. **Every other finding
below is priced and NOT built** — this document is otherwise exactly what it
was asked to be: an honest re-run of the structural-ceiling methodology,
mirroring `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`'s own grouping-first
approach, at today's real baseline.

**Headline findings, stated up front:**

1. **The real, verified baseline is 62/257 (24.1%), matching the task's own
   stated number exactly** — confirmed by running the live battery, not
   trusted blind (§1). One same-day fix (§5, built) moves it to **63/257**.
2. **The population of 195 (now 194) failing tasks is dominated by TWO
   things neither of which is "a missing primitive" in the Tier-1/2/3 sense
   every rung today has been closing** (§2-3): (a) a **value-template-pool**
   gap that leaves several already-shipped Terms (`Reverse`, `Capitalize`,
   `Str`, `Round`, `Sort`) unreachable INSIDE a `MapList`/list-shaped
   composition even though every individual op is landed and correct, and
   (b) a **construction-precedence** gap where a rejected `retrieved_exemplar`
   candidate NEVER falls through to try `SynthEnumerate` at all — a
   deliberate, well-reasoned, but now five-rungs-stale design decision from
   Arc4-S6/Arc6-D (2026-08-01-era) that blocks **60 of the 194 remaining
   failures (31%)** from ever reaching the search this whole day's work has
   been improving.
3. **The reassessment PREREG's own Q4 judgment on Rung 4 ("no MBPP task
   currently fails for this reason... today") is now measurably FALSE.**
   Every one of the 102 `gapped:enumerate_failed` tasks reaches
   `SynthEnumerate` with `ops=None` — `SynthesisOperatorShape` never
   contributes a hint to ANY of them — and at least one (task 118) is
   **proven** to solve in 25 candidates under a precise, narrow op list
   while burning the full 200,000-candidate budget under today's typed
   default. This was true in a WEAKER form when the reassessment PREREG was
   written (fewer ops existed to crowd the buckets); it is unambiguously
   true now.
4. **Recurse and Format were honestly re-checked, not re-cited.** Neither
   reach number changed. Recurse gained NEW negative evidence (a spurious,
   holdout-failing accept on task 99) that *strengthens* the existing NO-GO
   rather than weakening it. Format is still exactly one task.

---

## 1. The real current MBPP state — verified, not trusted

`OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3
scripts/mbpp_endgame_battery.py`, run live in the primary tree at `main @
4a6b63f` before any code was read for this document's own conclusions:

```
full:             62/257  p=0.241245  ci=[0.192996, 0.297116]  det_identical=True
content_stripped: 61/257  p=0.237354  ci=[0.189445, 0.292999]  det_identical=True
official:         90/257  p=0.350195  ci=[0.294468, 0.410333]  det_identical=True
```

This matches the task's own stated "62/257 (24.1%)" exactly — the whole
morning's priced-gap queue (Rung 1, Rung 2, Rung 3-NO-GO, SetLit/DictItems,
DictItems/SortBy, the bugfix sweep) is genuinely reflected in the live
number, not a stale citation. **`full` (`n=257`, the primary protocol) is
used as the denominator for every count in this document**, per the
harness's own docstring ("THE arc's own external number").

Pass ids (62): `11, 16, 20, 58, 59, 69, 71, 74, 82, 84, 85, 89, 90, 106, 115,
120, 127, 131, 132, 135, 138, 139, 141, 142, 145, 161, 227, 230, 232, 233,
234, 249, 257, 266, 272, 276, 278, 281, 290, 309, 312, 393, 394, 404, 406,
410, 413, 418, 428, 433, 436, 443, 450, 451, 457, 458, 460, 472, 473, 474,
475, 477`.

## 2. Failure-cause grouping, real data — the 195 non-passing runnable tasks

Every non-passing runnable task was **re-run individually through
`domains.prog_synthesis.synthesize_from_request`** (the exact same call
`mbpp_endgame_battery.py::run_task` makes), reading the FULL `read_goal()`
dict — not just the battery's own trimmed row — to get `enumerate.tested`/
`enumerate.ops`/`enumerate.operator_shape`, `gap_reason`, `construction`,
`retrieval`, `cover_parts`, and `residual_tokens` for every one of the 195.
(`/tmp/.../diag_results.json`, reproducible via `domains.mbpp_spec.split_rows`
+ `psy.synthesize_from_request` per task_id, same boot as `boot_full`.)

| outcome | n | what it means |
|---|---|---|
| `gapped:enumerate_failed` | **102** | reached `SynthEnumerate`, found nothing |
| `accepted_holdout_fail` | **51** | a candidate was ACCEPTED (revealed rows fit) but disagrees on a held-out row |
| `gapped:property_verdict_reject` | **26** | a candidate was built and REJECTED by a held self-verifying property check |
| `gapped:structural_verdict_reject` | **10** | a candidate was built and REJECTED by a structural-trap detector (D1/D2) |
| `runner_exception:TypeError` | 3 → **2** (§5 fixes one) | an uncaught Python exception aborted the whole attempt |
| `not_recognized` | 1 | the request text itself was never recognized as a write-request |
| `gapped:no_shape` | 1 | no cover-parts / operator shape matched at all |
| `gapped:exhausted` | 1 | attempt budget exhausted before any status resolved |

**This is a materially different shape than `ARC6_STRUCTURAL_CEILING.md`'s
own 2026-08-01 population** (which measured "42 of 53 live-unreached" tasks
purely as *structural-primitive* blocks). Two entire outcome classes —
`accepted_holdout_fail` and the two `*_verdict_reject` classes, **87 tasks,
44.6% of the 195** — do not appear as categories in that document at all,
because in 2026-08-01's much smaller op-table almost nothing reached
"accepted" on a wrong candidate in the first place. **The ceiling has moved
qualitatively, not just numerically.**

### 2.1 `gapped:enumerate_failed` (102) — budget-exhausted vs. genuinely saturated, and a total absence of operator-shape selection

```
budget-exhausted (tested == 200,000 exactly):  85
genuinely saturated under budget:              17
tasks with ops != None/empty (graph-level SynthesisOperatorShape fired): 0 / 102
```

**Every single one of the 102 currently-enumerate-reaching failures uses
`ops=None`** — `ps_select_synthesis_operator_shape`'s two hand-authored
trigger-token shapes (`thresholded_greater_branch`/`thresholded_lower_branch`,
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md` §1.3 item 2)
never fire for any of them, so every one of the 102 falls through to the
Rust-side typed defaults (`DEFAULT_OPS`/`DEFAULT_STR_OPS`/`LIST_EXTRA_OPS`/
`SET_DEFAULT_OPS` + the evidence gates, `synth_enumerate.rs:1744-1922`).

### 2.2 `accepted_holdout_fail` / `*_verdict_reject` (87) — a DIFFERENT subsystem, not the op-table at all

```
construction breakdown, all 87:
  retrieved_exemplar             60   (24 accepted_holdout_fail + 26 property_verdict_reject + 10 structural_verdict_reject)
  mck_*/sum_of_two/count_of_list/
    product_of_two/other template 27   (all accepted_holdout_fail)
```

**Confirmed by direct probe, not inferred:** for every sampled
`property_verdict_reject`/`structural_verdict_reject`/`retrieved_exemplar`-
sourced `accepted_holdout_fail` task, `enumerate.tested is None` —
`SynthEnumerate` is **never invoked at all**. This is by design, and the
design is explicitly documented and reasoned (`seeds/program_synthesis.json`,
`ps_structural_reject_exclusion_gap`/`ps_property_reject_gap` comments,
Arc4-S6/Arc6-D, 2026-08-01-era): re-trying RETRIEVAL after excluding a bad
`retrieved_exemplar` candidate cannot help, because every retrieval accept
shares one literal construction label regardless of which exemplar produced
it, so exclusion-based reopening can't distinguish a "next" candidate — a
real, measured finding from that era (`PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md`
§4, task 267). **But that reasoning is about retrying retrieval, not about
falling through to a DIFFERENT construction mechanism (`SynthEnumerate`) —
and no fallthrough to enumerate exists for a rejected retrieval today.** See
§4 for why this is now a live, unpriced opportunity.

The other 27 (`mck_*`/template-family `accepted_holdout_fail`) are
different: `enumerate.tested` IS populated (a few hundred to ~170k) — the
search DOES run — but a different, non-enumerate construction lane still
wins the accept, wrongly. This is a narrower, separate "construction
precedence" issue (which lane's candidate wins when several are tried), not
a "no attempt" issue, and is named but not further chased here.

### 2.3 The remainder (6 tasks)

`94` (not_recognized — a genuinely unparsed request shape), `164`
(no_shape), `222` (exhausted), and — before §5's fix — `98`/`124`/`237`
(runner_exception). Each is its own small, distinct residual; see §5 for 98,
and §6.5 for 124/237.

---

## 3. What's newly reachable now — the map-template-pool gap (8 tasks, zero new `TermNode`, priced not built)

Per the task's own instruction to check for "one more small thing" before
assuming everything needs new machinery: **eight currently-failing tasks
have a hand-built, LIVE-VERIFIED witness using ONLY already-shipped Terms**
— every `TermNode` these witnesses use (`MapList`, `Reverse`, `Capitalize`,
`Str`, `Round`, `Sort`, `Split`, `Fold`, `ParseInt`, `Sum`, `Count`) already
exists in `runners/dsl/src/term.rs`, most landed by TODAY's own Rung 1/
SetLit-DictItems/DictItems-SortBy rungs. **They do not convert because two
DIFFERENT hand-maintained enumerations were never extended when those Terms
landed:**

### 3.1 The bug, precisely located

`map_templates_by_size` (`synth_enumerate.rs:2098`, built at
`synth_enumerate.rs:2314-2375`) is a **fixed, hand-authored list of VALUE
TEMPLATES** a `MapList`/`SetMap`/`SortBy` composition can draw its per-
element body from: identity, `len(item)`, `lower(item)` (`CaseFold`),
`item±c`/`item*c` for a numeric const, `item[0]`/`item[-1]`,
`item[scalar_var]`, and — added by today's SetLit/DictItems rung, gated to
`set_map_wanted` only — `sorted(item)`. **There is no `Reverse(item)`,
`Capitalize(item)`, `Str(item)`, `Round(item, 0)`, or `Sort(item)`-for-
general-`MapList` entry** — every one of Rung 1's five new unary Terms
landed WITHOUT a matching map-template, and `Sort`'s own template
(`synth_enumerate.rs:2370-2374`) was gated so narrowly (`set_map_wanted`
only) that a plain `MapList` never sees it either. **This is the exact same
"hand-maintained enumeration where a codebook belongs" shape
`RULES_AS_SHAPE_DESIGN_SPIKE.md`/`SHAPE_AUDIT.md` already diagnosed
elsewhere in this tree** (CLAUDE.md's own SHAPES-NOT-NUMBERS section) — a
second, DEEPER instance of it than the OP_TABLE layer the reassessment
PREREG already examined.

Separately, `synth_enumerate.rs:1867-1917`'s list-shaped-output typed
default **deliberately excludes** `Replace`/`Split`/`StrCount`/
`Capitalize`/`Str`/`ParseInt` from ever being offered at all (Rung 1's own
measured decision, to protect task 132's budget) — so a task whose OUTPUT
happens to be list-shaped (e.g. task 118, a string split into a list) can
never reach `Split` even though `Split` exists and `DEFAULT_STR_OPS`
carries it for string-OUTPUT specs.

### 3.2 Eight live, hand-verified witnesses (all revealed rows match exactly)

| id | prompt (abridged) | witness (already-shipped Terms only) | blocked by |
|---|---|---|---|
| 456 | reverse each string in a list | `MapList(a, item, Reverse(item))` | no `Reverse(item)` map-template |
| 104 | sort each sublist of strings | `MapList(a, item, Sort(item))` | `Sort(item)` template gated to `set_map_wanted` only |
| 419 | round every number, sum × length | `Times(Sum(MapList(a,item,Round(item,0))), Count(a))` | no `Round(item,c)` map-template |
| 102, 411 | snake_case → CamelCase (twin tasks) | `Fold(MapList(Split(a,"_"),item,Capitalize(item)), concat)` | no `Capitalize(item)` map-template |
| 439 | join list of ints into one int | `ParseInt(Fold(MapList(a,item,Str(item)), concat))` | no `Str(item)` map-template |
| 421 | join tuple elements with a delimiter | `Fold(MapList(a,item,Str(item)), concat-with-"-")` | no `Str(item)` map-template |
| 118 | split a string on space, as a list | `Split(a, " ")` alone | `Split` excluded from the list-shaped-output typed default entirely |

Every witness above was evaluated directly against the task's own real
revealed rows via `substrate_rs.Substrate()._inner.evaluate(term, env)` — not
inferred from the op table, not assumed from the Term's name (this project's
own standing discipline, `STRUCTURAL_CEILING.md` §7.3: *"reading the source
would have confirmed each of these; invocation refuted [some of] them"*).
All eight are **exact matches on every revealed row**, no `runner_exception`.

### 3.3 Pricing

**Zero new `TermNode` variants.** The fix is two small, additive extensions
to `synth_enumerate.rs`, mirroring the `sorted(item)`/`set_map_wanted`
precedent that already exists in the same function:

1. Add `Reverse(item)` / `Capitalize(item)` / `Str(item)` / `Round(item, c)`
   map-template entries, each gated on the corresponding op being "wanted"
   (`reverse_wanted`/`capitalize_wanted`/`str_wanted`/`round_wanted`,
   mirroring `set_map_wanted`) — by construction, a spec that never asks for
   that op gets the SAME template pool as today (byte-identical), so this
   piece is genuinely risk-free in isolation.
2. Widen the list-shaped-output typed default to actually OFFER
   `Reverse`/`Capitalize`/`Str`/`Split`/`ParseInt`/general `Sort` under some
   string-content evidence gate — **this is the piece with real regression
   risk**, because it is exactly the bucket Rung 1 had to narrow THREE times
   to protect task 132 (`STRUCTURAL_CEILING_RUNG1_RESULTS.md` §2). Any
   widening here needs the SAME measured build → test-132 → narrow-if-
   needed walk Rung 1 already used as its own template.

**This is NOT a "so cheap and clearly evidenced it would be irresponsible
not to build" case** in the way §5's one-line `_plain()` fix was — it is
real, correctly-scoped engineering (two touch points, a shared-pool
regression discipline, ~8 tasks) of the same SIZE and SHAPE as Rung 1/
SetLit-DictItems themselves, not a same-day one-liner repeat. It is priced
here, not built, and is this document's top-ranked candidate (§7).

---

## 4. The bigger, riskier, unpriced opportunity — retrieved-exemplar fallthrough (up to 60 tasks, NOT recommended to build blind)

§2.2 already established the fact: **60 of the 194 remaining failures are
permanently blocked from ever attempting `SynthEnumerate`**, because a
`retrieved_exemplar` candidate is tried, rejected by a property/structural/
holdout check, and the pipeline's own reasoned design (§2.2, Arc4-S6/
Arc6-D) routes straight to `gapped` rather than trying a different
construction lane.

**Why this is named as a candidate but NOT sized into §7's ranking with
real confidence:** the original 2026-08-01 reasoning for not reopening
retrieval was sound and is UNCHANGED by anything this document found — it
is specifically about why re-trying RETRIEVAL doesn't help. Whether trying
`SynthEnumerate` INSTEAD would help is a genuinely open, unmeasured
question, and there are real reasons it might not:

- These 60 tasks were hard enough that RETRIEVAL was the construction path
  tried first (implying the direct-search/lattice/exact rungs upstream of
  retrieval already declined or weren't reached) — there is no guarantee
  `SynthEnumerate`, even with today's much richer op-table, would do better
  than "budget-exhausted, same as the 85 already in that bucket."
- A blind "always try enumerate after a rejected retrieval" change touches
  EVERY task's control flow, not a scoped subset — the real analogue of
  Rung 1's own "additivity is not safe by construction" lesson, at a much
  larger blast radius (60 tasks' worth of NEW `SynthEnumerate` calls where
  today there are zero) and touching an OLDER, less-recently-exercised
  subsystem than the op-table work this whole day has been validating.
- Reopening a 2026-08-01 design decision deserves its own investigation —
  specifically, whether `ps_propose`'s retrieval-reject handling should
  route to `SynthEnumerate` as an EXPLICIT next construction rung (a new,
  bounded control-flow addition analogous to `ps_enum_retry_mark`'s already-
  standing precedent for the codebook/lattice/enumerate SOURCES), not a
  reflexive "just try harder" patch.

**This is this document's single highest-consequence finding and its
single lowest-confidence-to-build recommendation, stated as plainly as
that tension deserves.** It is not sized into a build estimate here because
sizing it responsibly requires answering "would `SynthEnumerate` actually
solve any meaningful fraction of the 60" BEFORE costing the control-flow
change — and answering that requires running `SynthEnumerate` against all 60
specs, which is itself the next document's job, not a paragraph in this one.

### 4.1 A cheap probe that partially answers the sizing question anyway

A quick, non-committal check: of the 60 retrieved_exemplar-touched failures,
how many ALSO look like they'd hit the exact same `ops=None`-budget-
exhaustion wall §2.1 already measured for the 102? Sampling their prompts
against the same "needs a stdlib primitive already shipped" heuristic used
in §3 suggests most are NOT simple stdlib-composition tasks (they lean
toward number-theory/bit-manipulation prompts — "smallest power of 2
greater than n", "set the leftmost unset bit", "nth centered hexagonal
number" — the SAME flavour of task the original `ARC6_STRUCTURAL_CEILING.md`
found `sympy`-import-shaped, not primitive-shaped). **This is a soft,
qualitative read, not a measurement** — it suggests the naive fallthrough
would recover FEWER of the 60 than the raw count implies, but does not
replace actually running the 60 specs through `SynthEnumerate`, which this
document does not do.

---

## 5. What was built — `_plain()`'s missing Fraction case (task 98)

**One thing met the "so cheap and clearly evidenced it would be
irresponsible not to build" bar** — a direct, same-day repeat of an
already-landed precedent (the SetLit/DictItems rung's own `_plain()`
frozenset fix, same function, same day), not a new design. Full detail,
live traceback, and full before/after measurement in
`PROGRAM_SYNTHESIS_CEILING2_PLAIN_FRACTION_RESULTS.md` (built in isolated
worktree `progsyn-ceiling2-plain-fraction`, commit `89f4496`, merged to
`main` at `32f38c9`). Summary:

- `domains/prog_synthesis.py::eval_and_record`'s `json.dumps(_plain(got))`
  crashed (`TypeError: Object of type Fraction is not JSON serializable`)
  whenever a candidate's `Div` produced an exact non-integer ratio
  (`Value::Rational` realises as Python's `fractions.Fraction` at the PyO3
  boundary) — task 98's own already-witnessed `Div(Prod(a), Count(a))`
  candidate (Arc6 tier-0's own priced witness for this task,
  `ARC6_STRUCTURAL_CEILING.md` §5, landed 2026-08-01/03) hits this on its
  very first evaluation (`-336/5`), aborting the WHOLE synthesis attempt
  rather than just that one candidate.
- Fix: one `isinstance(v, Fraction): return float(v)` branch, purely
  additive, matching every downstream comparator's own existing float
  expectation.
- **Measured: MBPP `full` 62→63, `content_stripped` 61→62, `official`
  90→91, all three arms +1, exact id `{98}`, zero regressions** (before-set
  ⊆ after-set on all three arms, confirmed by direct set diff). Task 98's
  held-out row independently confirmed passing (`1710 == 1710.0` within
  tolerance).
- Zero Rust touched (diff against HEAD confirmed empty before editing).
  Named 9-file regression suite: 3 failed / 241 passed, byte-identical
  failure signature to every prior rung today, independently re-confirmed
  present on a genuinely clean, unmodified `main @ 4a6b63f` (not inherited
  from a prior doc's characterization — re-run directly in this session).

This closes a loose end that has been open since **2026-08-01/03** — the
primitive (`ProdList`) was always sufficient; a downstream serialization gap
silently converted every attempt into a dead `runner_exception`, invisible
to every prior op-table-level investigation (including this document's own
§2-3 survey) until direct reproduction of the live exception surfaced it.

---

## 6. Recurse and Format, honestly re-checked

### 6.1 Recurse — still 7 ids, reach UNCHANGED, and the discount got WORSE

`STRUCTURAL_CEILING.md`'s 7 Recurse-necessary ids (`99, 260, 265, 283, 301,
448, 462`) are **all still failing today**, none closed by any of today's
five rungs (confirmed directly against the diagnostic dump, §2's own data
source):

```
99  | accepted (holdout FAIL) | tested=171271 | decimal->binary
260 | gapped:enumerate_failed | tested=200000 | nth Newman-Shanks-Williams prime
265 | gapped:enumerate_failed | tested=200000 | strided split
283 | gapped:enumerate_failed | tested=197967 | digit-frequency check
301 | gapped:enumerate_failed | tested=75070  | dict depth
448 | gapped:enumerate_failed | tested=200000 | sum of Perrin numbers
462 | gapped:enumerate_failed | tested=88079  | powerset (order-sensitive, §6.2 of the original doc already excludes it)
```

**New evidence found this rung, not present in the original doc: task 99
is "accepted" (not merely gapped) by a NON-recursive candidate that fits
both revealed rows but FAILS the held-out row.** This is exactly the kind
of spurious/overfit accept the original ceiling doc's §6.3 discount already
warned Recurse's conversion rate would be WORSE than the 32% S4 baseline
for ("a self-referential binder makes an enumerative search combinatorially
harder as it makes it richer") — except here the danger shows up even
WITHOUT Recurse: the enumerator, given a richer op inventory than 2026-08-01
had, now finds MORE spurious near-fits for recursion-shaped tasks, not
fewer. **This strengthens, not weakens, the original NO-GO.** Verdict:
**still NO-GO, and more confidently so than before.**

### 6.2 Format — still exactly 1 task

Task 390 (`apply a format string to every element`) is unchanged: still the
ONLY task in the entire 257-task split that needs `term:Format`
(`STRUCTURAL_CEILING.md`'s own per-task requirements, re-confirmed against
today's failure population — no other prompt in the 194 remaining failures
mentions format-string application). `gap_reason=enumerate_failed,
tested=200000` — budget-exhausted under the (Format-less) typed default, as
expected. **Verdict: still NO-GO**, for the identical reason the original
doc gave (`STRUCTURAL_CEILING.md` §9 item 5: *"one task uses it, nothing
else does"*) — taking it would be the structural-seam form of the
A-ceiling's `perrin_sum` cherry-pick, unchanged by anything landed today.

### 6.3 Combinations — still exactly 1 legitimate task

Task 255 (`combinations_with_replacement`) remains the one clean use;
task 462's powerset still needs the ORDER-SPECIFIC binary-reflected
generator the original doc's §6.2 already excluded as a cherry-pick.
**Verdict: still NO-GO** for a general-purpose build (would need to be
scoped exactly to 255's own shape to avoid the cherry-pick, and one task
alone does not justify a new `TermNode` under this arc's own standing
discipline).

### 6.4 GroupCount (Counter) and DictMerge — small, still separately prices to ~1 id each

- `term:GroupCount` (frequency map / `Counter`): task 88 needs ONLY this
  (`STRUCTURAL_CEILING.md`'s own per-task table: `{'requires':
  ['term:GroupCount']}`), confirmed still failing
  (`gapped:enumerate_failed, tested=200000`). Task 283 also cites
  `GroupCount` but ALSO needs `Recurse` (§6.1's NO-GO), so building
  `GroupCount` alone converts at most **+1** (task 88). One new `TermNode`,
  same "stdlib Term port" shape as Rung 1's own ten — a legitimate small
  unit, but ONE task, same caution as Format.
- `term:DictMerge`: task 87 alone, unchanged, still failing
  (`gapped:enumerate_failed, tested=53179`). Same "one task" caution.

Neither is individually worth a dedicated rung under this arc's own
standing rule; both are cheap enough (stdlib Term ports, zero architecture)
that they would be reasonable to BUNDLE into a future primitive-layer rung
alongside §3's map-template fix, but are not ranked as a standalone
candidate here.

### 6.5 The two remaining `runner_exception`s (124, 237) — named, not solved

- **124** (`angle of a complex number`) needs genuine complex-number
  support (Python's `cmath`) — the DSL has no complex value domain at all.
  Out of scope for anything this arc has built; would be a new value
  domain, not a Term port.
- **237** (`map each unique tuple to its count`) crashes with `unhashable
  type: 'list'` — a DIFFERENT defect than §5's Fraction gap, likely a
  tuple-arriving-as-list boundary issue (the SAME general family
  `VALUELAYER.md` §9.1/9.2 already named as unresolved: a tuple used as a
  DICT KEY, not merely a value, hits Python's own hashability requirement
  the moment `_unwire`/`_plain` produces a `list` where the source was a
  `tuple`). Not chased further here — named as a residual for a future
  rung, not sized.

---

## 7. Ranked candidates (consequence × confidence ÷ cost)

| rank | candidate | consequence (ids) | confidence | cost | status |
|---|---|---|---|---|---|
| — | `_plain()` Fraction case | +1 (98) | verified | ~zero | **BUILT, merged (`32f38c9`)** |
| 1 | map-template-pool + list-shaped-branch widening (§3) | up to +8 (456,104,419,102,411,439,421,118) | HIGH on witnesses, MEDIUM on conversion (task-132-class regression risk, needs Rung-1-style narrowing) | MEDIUM (2 touch points, shared pool, real but bounded regression surface) | **priced, recommended next rung** |
| 2 | retrieved-exemplar → enumerate fallthrough (§4) | up to +60 inventory, REAL number unknown | LOW-MEDIUM (untested; soft read suggests fewer than the raw count) | HIGH (control-flow change to an older, deliberately-reasoned subsystem; 60-task blast radius) | **named, explicitly NOT recommended to build blind — needs its own sizing investigation first** |
| 3 | `term:GroupCount` (+1, task 88) | +1 | HIGH | LOW (1 Term, stdlib port) | priced, bundleable, not standalone-worth |
| 3 | `term:DictMerge` (+1, task 87) | +1 | HIGH | LOW (1 Term, stdlib port) | priced, bundleable, not standalone-worth |
| — | `term:Recurse` | +7 on paper, ~0-2 realistic | LOW (new negative evidence this rung) | HIGH (capability, not additive) | **still NO-GO, reconfirmed** |
| — | `term:Format` | +1 | HIGH | LOW-MEDIUM | **still NO-GO** (one task) |
| — | `term:Combinations` (general) | +1 legitimate | HIGH | LOW | **still NO-GO** (one task; 462 remains a cherry-pick) |
| — | 124 (complex numbers) | +1 | — | HIGH (new value domain) | out of scope |
| — | 237 (tuple-as-dict-key hashability) | +1 | — | unknown, unpriced | named, not sized |

---

## 8. Overall recommendation

**There IS a real, sized, buildable next rung — §3's map-template-pool
widening — and it is the right next thing to build, following the exact
Rung-1 discipline (build, measure against the real battery, narrow against
task 132 if it regresses, ship the measured-safe shape).** It is smaller
than Rung 1 (2 touch points vs 10 new Terms) but carries a real, non-zero
regression surface that must be walked the same way Rung 1 walked it, not
assumed safe.

**The ceiling has also genuinely changed shape, and that is this document's
more important finding than any single priced rung.** As of this baseline,
primitive availability is no longer the dominant constraint on MBPP pass
rate — the DOMINANT failure modes are now (a) a value-template/op-selection
gap that leaves already-shipped primitives unreachable in composition
(§3, priced), and (b) a construction-precedence gap where 31% of all
remaining failures never get a chance at the search this whole arc has
spent the day improving (§4, named, unpriced, NOT recommended to build
without its own sizing pass first). **A rung that keeps adding Tier-N
stdlib Term ports without addressing either of these two gaps will keep
finding smaller and smaller yields**, because the population of tasks that
are BOTH reachable by `SynthEnumerate` AND blocked purely by a missing
primitive is shrinking faster than the population blocked by these two
structural, non-primitive gaps.

**What this document does NOT establish:**

1. §3's 8 witnesses prove INVENTORY sufficiency, not SEARCH reach at the
   real, evidence-gated typed-default level — per this whole arc's own
   standing "reach is not conversion" discount (`STRUCTURAL_CEILING.md`
   §6.3), the actual converted count after a real, regression-safe build
   could be smaller than 8, the same way Rung 1's own +16 inventory ceiling
   converted only +5.
2. §4's 60-task retrieved-exemplar-fallthrough population was NOT run
   through `SynthEnumerate` — the real yield if fallthrough were added is
   completely unmeasured, deliberately, because doing so responsibly is a
   sizing investigation in its own right, not a paragraph here.
3. The 27 `mck_*`/template-family `accepted_holdout_fail` tasks (§2.2) were
   named but not investigated further — which lane's candidate should win
   when several are tried and only one is genuinely correct is a real,
   separate "construction precedence" question this document does not
   answer.
4. §2's classification was run once, live, on this baseline; it was not
   independently re-verified by a second harness the way this arc's
   PRIMARY battery numbers were (mirroring `mbpp_endgame_battery.py` vs
   `arc6_verdict_battery.py gr4_gate`'s own cross-check discipline) —
   the PASS/FAIL counts themselves (§1) WERE taken from the real, primary
   battery; only the per-task diagnostic detail (§2's table) is this
   document's own single-harness measurement.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it —
   this document is about this substrate's own best-fitted mechanism.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot
git log --oneline -1 main   # 4a6b63f (pre-fix) / 32f38c9 (post-fix), verify fresh
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

The per-task diagnostic sweep (§2's own data source) re-runs
`domains.prog_synthesis.synthesize_from_request` directly per failing
`task_id` against `domains.mbpp_spec.split_rows(..., "primary")["revealed"]`,
under the same `boot_full()` the battery itself uses, reading the FULL
`read_goal()` dict rather than the battery's own trimmed row.
