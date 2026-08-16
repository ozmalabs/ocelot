# PBE string-transformation benchmark — PREREG

**Date:** 2026-08-17. Base `main @ 9dbad6d` (verified fresh via `git log
--oneline -1 main` before creating the worktree). Worktree:
`/home/matt/ozmadev/ocelot-pbe-string-benchmark`, branch
`pbe-string-benchmark`. No measurement has been run yet as of this
document — every number below is a PLAN or a falsifiable PREDICTION, not
a result. This document is written before `scripts/pbe_string_battery.py`
is ever executed against the real corpus.

**HEADLINE (there is no prior measurement to cite yet, so the headline is
the plan itself, per this arc's own house style): this rung tests whether
the MBPP arc's single most consequential finding — the
`literal_witness_cost` MDL/Occam repricing fix in `SynthEnumerate`
(`runners/dsl/src/synth_enumerate.rs`), shipped in
`MDL_OCCAM_WITNESS_PRICING_RESULTS.md` — generalizes to a task shape
DELIBERATELY unlike MBPP: raw input→output STRING pairs with NO natural-
language prompt at all (the classic FlashFill/PBE framing). Zero Rust
changes are made in this rung; it is a pure measurement of the ALREADY-
SHIPPED, unmodified engine against a newly built 26-task corpus, called
directly (no MBPP pipeline, no retrieval, no NL comprehension).**

---

## 0. Why this corpus, precisely (not re-derived from memory)

`docs/research/engine_substrate/DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md`
§2 and its shipped build,
`docs/research/engine_substrate/MDL_OCCAM_WITNESS_PRICING_PREREG.md` /
`_RESULTS.md`, diagnosed and fixed a specific defect: `SynthEnumerate`'s
search-ordering metric priced every literal leaf at a uniform cost of 1,
so a degenerate `IfThenElse(Eq(x, input_i), output_i, output_j)` 2-branch
lookup table (which any 2-revealed-row spec can ALWAYS build, trivially)
would register at the same small SIZE class as, and often smaller than, a
genuine multi-step composition — meaning the search's own Occam/MDL
ordering (shortest program found first) would hand back memorized lookup
tables instead of general rules whenever a task's genuine solution needed
more than ~2 ops. The fix, `literal_witness_cost` (currently
`runners/dsl/src/synth_enumerate.rs:1484-1502`, read directly for this
document): a string literal is priced 1 if it is DATA-DERIVED (a
substring of some revealed input) or ROW-INVARIANT (a substring of EVERY
revealed output — a genuine task constant); otherwise, if it is a
SINGLE-WITNESS OUTPUT QUOTE (appears in exactly one revealed row's
output and nowhere else), it is priced at its own character length. This
makes bare lookup tables expensive in proportion to how much they quote,
while leaving every data-derived or genuinely-constant literal untouched.

That design doc's own claim (quoted in the task brief that opened this
rung): *"every future few-shot synthesis task — MBPP or not — inherits
the same wall."* `MDL_OCCAM_WITNESS_PRICING_RESULTS.md` validated the fix
ONLY on MBPP (88/88 full, 87/87 content_stripped, 113→114 official, zero
regressions, one traced +1 conversion, and a live elimination of a named
5-task literal-lookup probe set). **The claim that the mechanism
generalizes beyond MBPP has never been tested until this rung.**

PBE string tasks (Gulwani 2011, "Automating String Processing in
Spreadsheets Using Input-Output Examples," the FlashFill lineage, and its
many SyGuS-benchmark descendants) are the sharpest available test of that
claim specifically BECAUSE they carry no NL prompt: MBPP's `prompt` field
gives the pipeline's retrieval/exemplar/codebook machinery something to
lean on regardless of how the raw enumerator prices literals (this is
exactly why task 451's own +1 conversion in the MBPP results traced
through `prog_retrieval.py`'s retrieval-ladder hole-fill rung, a SECOND
call site into the same repriced code, not the top-level enumerate path
alone). A PBE task has nothing but the rows. If the fix's benefit is real
and general, it must show up here with nothing else to fall back on. If
it does not, or shows up in a different shape, that is an equally
valuable, honestly reportable finding about the fix's actual generality
boundary — not a failure of this rung (the task brief's own framing,
preserved here).

**No prior citation exists for this corpus's own outcome anywhere in this
repository** — this document establishes the plan and the falsifiable
predictions; `PBE_STRING_BENCHMARK_RESULTS.md` will report what actually
happened, including where a prediction below turns out wrong.

---

## 1. The substrate, read directly (not assumed)

Source citations, all read in full for this document:
`runners/dsl/src/synth_enumerate.rs` (the search engine — `OP_TABLE`
lines 359-511, `DEFAULT_STR_OPS` lines 639-670, `literal_witness_cost`
lines 1484-1502, the const-set construction lines 2894-2966),
`runners/dsl/src/term.rs` (the evaluator for every string Term this
corpus exercises), `scripts/mbpp_endgame_battery.py` (the harness-design
template this rung's own harness mirrors structurally, NOT functionally
— see §3), `tests/test_synth_enumerate_migrated.py` (the exact
direct-call shape — `SYNTH()`/`rows()` helpers — this rung's harness
reuses verbatim).

### 1.1 The string-relevant op inventory (`OP_TABLE`, confirmed by reading
      each Term's evaluator in `term.rs`, not assumed from its name)

| op name | `term.rs` semantics, verified | in `DEFAULT_STR_OPS`? |
|---|---|---|
| `Concat` → `StringConcat{parts}` | binary string concat | yes |
| `CaseFold` → `CaseFold{text}` | `str.lower()` (NOT true Unicode casefold — plain lowercase, `term.rs:6602-6609`) | yes |
| `Replace` → `Replace{text,old,new}` | `text.replace(old,new)`, ALL occurrences, matches Python | yes |
| `Str` → `Str{value}` | Python `str()` | yes |
| `Split` → `Split{text,sep}` | `sep` non-empty → `text.split(sep)`; `sep` EMPTY or `None` → Python's no-arg WHITESPACE split (`term.rs:5222-5243`, doc-commented explicitly) | yes |
| `StrCount` → `StrCount{text,sub}` | non-overlapping substring count, matches Python `str.count` | yes |
| `Capitalize` → `Capitalize{text}` | first char upper, REST LOWERED (matches Python `str.capitalize()` exactly, not a per-word title-case) | yes |
| `Reverse` → `Reverse{seq}` | char-reverse for strings, element-reverse for List/Tuple | yes |
| `Slice` → `Slice{seq,start,stop}` | Python-style slicing incl. negative-index wraparound and CLAMPING an out-of-range stop to sequence length (`prog_eval.rs::slice_indices`, read directly) — step is always 1, no step arg exposed | yes |
| `MapList` → `MapList{source,item,value}` | per-element map, template drawn from `map_templates_by_size` (a bounded mini-search over `Var(item)` using the SAME op inventory) | yes |
| `JoinList` → `Fold{source,item,acc,init:"",body:Concat(acc,item)}` | **joins with the EMPTY STRING ONLY — no separator argument exists anywhere in `OP_TABLE`** | yes |
| `First` → `IndexAt{seq,index:0}` | first list element | **no** (an ordinary `LIST_EXTRA_OPS` entry — offered only for a list-shaped spec's typed default, not the string one; a caller wanting it on a string spec must name it explicitly) |
| `LastElem` → `Last{seq}` | last list element (or last CHAR if `seq` itself is a string — `term.rs:7011-7019`, StringAsSequence path) | **no**, same reason as `First` |

### 1.2 Confirmed-absent primitives (grepped across `term.rs`, not
      inferred)

- **No uppercase Term of any kind.** `CaseFold` is lowercase only.
  `grep -n "Upper\|to_uppercase" runners/dsl/src/term.rs` returns nothing
  relevant to a string-uppercase Term.
- **No `Strip`/`Lstrip`/`Rstrip`.** Nothing in `term.rs` trims
  variable-length whitespace.
- **No per-word title-case / no separator-aware join.** `SnakeCase`
  exists as a Term (`term.rs:6594`) but is NOT in `OP_TABLE` at all (so
  it is unreachable from `SynthEnumerate` regardless of `ops`). `JoinList`
  is the only list→string reducer and it hardcodes the empty-string
  separator (§1.1 above).

These three absences are used below (§4) to construct DELIBERATELY
unreachable control tasks, predicted impossible IN ADVANCE — the
distinction this rung's own task brief asks for ("a missing primitive...
vs a search-cost wall... vs a memorization wall").

### 1.3 Default constant-set construction (`synth_enumerate.rs:2894-2966`,
      read directly)

Absent an explicit `consts` argument, the constant pool is EXACTLY
`{0, 1, 2, -1}` (integers) plus every integer-VALUED spec OUTPUT
(irrelevant here — this corpus's outputs are strings, one int-output
exception noted in §2) plus, as a SEPARATE Q1 addition, every WHOLE
STRING value observed anywhere in the spec (input or output) and every
DISTINCT CHARACTER inside any of them — spec-derived only, never a
global alphabet. **No `None` literal is ever auto-derived, and no
integer beyond `{0,1,2,-1}` is auto-derived for a string-typed spec.**
This means, confirmed by reading the code rather than assumed: a task
needing `Slice(x, 0, 3)` (a literal `3`) or `Slice(x, -2, <end>)` (needing
a way to say "to the end," since `Slice` has no arity for an omitted
stop) is UNREACHABLE under the engine's own typed default with no
explicit `consts` — this is exactly the situation `DEFAULT_STR_OPS`'s
own doc comment anticipates ("a caller that wants more declares `ops`
explicitly") generalized one level to consts.

---

## 2. The corpus — `tests/fixtures/pbe_string/pbe_string_tasks.json`

26 tasks, hand-built from real Python callables (documentation/
verification only — never fed to the synthesizer, which sees ONLY the
`revealed`/`held_out` input→output rows, no `prompt` field anywhere in
the fixture). Generated via a small script
(`/tmp/.../scratchpad/gen_pbe_corpus.py`, not committed — a one-shot
generator, the `gen_program_synthesis_grounding_seed.py` precedent) that
calls the REAL Python function to compute every expected output, so no
row is hand-arithmetic'd into the JSON (eliminates transcription error as
a source of a false pass/fail). **No external FlashFill benchmark set was
found reachable from this environment in the time available for this
rung** (no network fetch of the SyGuS/PBE benchmark repositories was
attempted or claimed) — this corpus is built FRESH, task-shape-matched to
the FlashFill lineage's own published example TYPES (substring
extraction, case transforms, word-level split/join, char counting/
replacement), not copied from any single external source. This is stated
plainly rather than fabricating a citation, per the task brief's own
instruction.

Four tiers (`tier` field on every task):

| tier | n | shape |
|---|---|---|
| `tier1_single_op` | 9 | one primitive solves it (`Reverse`, `CaseFold`, `Capitalize`, `Slice`, `Replace`, `StrCount`, `Concat`) |
| `tier2_composition` | 8 | 2-3 op genuine compositions (`Split`+`First`, `Split`+`LastElem`, `Split`+`MapList`+`JoinList`, nested `Slice`/`Reverse`/`Capitalize`) |
| `tier3_deep_or_missing` | 5 | deeper (4-op) reachable compositions AND three DELIBERATE missing-primitive controls (`shout`=`upper()`, `title_case_words`, `strip_whitespace`) predicted impossible per §1.2, IN ADVANCE |
| `memorization_trap` | 4 | exactly 2 revealed rows (never 3, unlike every other tier), a genuine multi-step rule, and a 3rd held-out row a literal input→output lookup table would fail |

Every non-trap task carries 3 revealed rows (tier1/tier2/tier3); every
trap task carries exactly 2 (deliberately, to keep the 2-branch
`IfThenElse` lookup shape live as a competing candidate — 3 revealed rows
would trivially rule that shape out on its own and defeat the point of
the probe).

### 2.1 The memorization-trap size arithmetic, worked BEFORE running
      anything (falsifiable prediction, not a result)

`SynthEnumerate`'s SIZE = 1 (the node) + sum of child sizes; leaves cost
1 EXCEPT a witness-priced string literal, which registers at its own
`literal_witness_cost` instead of 1 (§1's citation). A bare 2-branch
lookup `IfThenElse(Eq(Var, Lit(input_1)), Lit(output_1), Lit(output_2))`
has size = 1 (`IfThenElse`) + 3 (`Eq(Var,Lit)` subtree: `Eq`+`Var`+`Lit`)
+ cost(`output_1`) + cost(`output_2`). `input_1` is DATA-DERIVED (appears
in a revealed input) so it is ALWAYS priced 1 regardless of the fix.
`output_1`/`output_2` are the load-bearing literals:

- **Pre-fix (uniform cost 1, the state before `c7db134`):** lookup size =
  1+3+1+1 = **6**, REGARDLESS of how long the output strings are.
- **Post-fix (witness-priced):** lookup size = 1+3+len(output_1)+len(output_2)
  (assuming neither output is row-invariant across the 2 revealed rows —
  true whenever the two revealed outputs differ, which every trap task
  below is built to ensure).

`pbe_024` (`trap_capitalize_reverse_slice`): genuine rule
`s[:4][::-1].capitalize()` = `Capitalize(Reverse(Slice(Var,Lit(0),Lit(4))))`,
size = 1(`Capitalize`) + 1(`Reverse`) + [1(`Slice`) + 1(`Var`) + 1(`Lit 0`)
+ 1(`Lit 4`)] = **7**. Revealed outputs `"Lleh"`/`"Htyp"` are both
4 characters, neither a substring of its own input (case differs) and
not row-invariant (they differ from each other) — SINGLE-WITNESS OUTPUT
QUOTES under `literal_witness_cost`'s own rule 3. **PREDICTION: pre-fix,
the lookup (size 6) is smaller than the genuine rule (size 7) and would
be RETURNED FIRST — a wrong answer, since it would fail the held-out row
`"data science"`→`"Atad"`. Post-fix, the lookup's own size becomes
1+3+4+4=12, and the genuine rule (still size 7, UNCHANGED by the fix)
should win instead — the exact mechanism this rung exists to test,
reproduced on a PBE task instead of an MBPP one.** This prediction is
checked empirically in §5 of the RESULTS document by running the SAME
probe on the current (post-fix) engine AND on the pre-fix commit
(`f4394fd`, `c7db134`'s own parent — confirmed via
`git log --oneline -1 c7db134^`), mirroring
`MDL_OCCAM_WITNESS_PRICING_RESULTS.md` Gate (2)'s own before/after
methodology exactly (checking out an already-existing, already-merged
prior commit for a scoped diagnostic rebuild is NOT a Rust code change
this rung authors — it is measurement, the same class of operation that
document's own Gate (1)/(2) already used).

`pbe_026` (`trap_slice_capitalize_reverse`) is a same-shape replication
(last-anchored slice instead of first-anchored) — a REPLICATION check,
not an independent prediction. `pbe_023` (`trap_reverse_simple`) is a
CONTROL: its genuine rule (`Reverse`, size 2) is far below ANY lookup
shape regardless of pricing, so it is predicted to pass under both
pre-fix and post-fix conditions — if it does not, that would indicate a
bug unrelated to this mechanism. `pbe_025` (`trap_replace_reverse`) sits
in a size TIE zone (genuine rule size 6, equal to the lookup's own
pre-fix size) and is reported EMPIRICALLY with no confident advance
prediction (registration/enumeration order, not size alone, decides ties
— not fully determined by reading the code alone within this rung's
scope).

---

## 3. The harness — `scripts/pbe_string_battery.py`

Mirrors `scripts/mbpp_endgame_battery.py`'s STRUCTURE (fixture load,
paired-arm design, exact task-id set-diff reporting, a written JSON
artifact under `results/`) but NOT its content — no
`domains.prog_synthesis.synthesize_from_request`, no retrieval ladder, no
`mbpp_spec` protocol machinery. Every task calls `SynthEnumerate` directly
via `sub._inner.evaluate(SYNTH(...), {})`, the exact shape
`tests/test_synth_enumerate_migrated.py`'s own `SYNTH()`/`rows()` helpers
use (reused, `domains.prog_synthesis._wire_rows` imported verbatim for
the wire-type-safety reason that module's own docstring gives — never
reimplemented).

**Two arms, both against the SAME unmodified engine:**

- `typed_default` — `ops=None, consts=None`. The engine's own typed
  default (`DEFAULT_STR_OPS`, since every task's inputs/output are
  string- or (for `count_letter`) int-shaped) with ZERO hints beyond the
  raw rows. This is the single most honest number this rung can produce
  — it is what "no NL prompt, no hints" actually means end to end.
- `declared` — a FIXED `PBE_OPS`/`PBE_CONSTS` inventory (§1's own gap
  analysis: `First`/`LastElem` for word-level tasks, `{3,4,-2,-3,-4,999,""}`
  for slice bounds/whitespace-split the auto-derived default can't
  reach), applied UNIFORMLY to all 26 tasks — never tuned per task. This
  is the standard PBE-tool convention (declare the DSL once) and answers
  a DIFFERENT, still-honest question: "given a reasonable, task-
  agnostic string DSL declared up front, what can the Occam-ordered
  search reach."

Both arms run at `max_size=15, max_candidates=0` (engine default
200,000) as the PRIMARY budget. Every `declared`-arm FAILURE is
re-probed once at `max_size=20, max_candidates=2,000,000` (the exact
budget `CEILING_REASSESSMENT_7_PREREG.md §5.1` used for its own MBPP
probe) — this is what separates "unreachable with this op/const
inventory, period" from "a search-cost wall the default budget doesn't
clear," per the task brief's own required diagnosis.

A task's outcome is `pass` only if `found=true` AND every held-out row
evaluates the returned Term to EXACTLY the expected value (plain Python
`==`, sufficient here — every expected value in this corpus is a plain
str or int, no float-tolerance/unordered-row schema needed, unlike
MBPP's `_row_cmp_ok`). `outcome_taxonomy` and exact task-id set-diffs
(`diff_declared_minus_typed_default`, `diff_high_budget_minus_declared_
default`) are computed the same way `mbpp_endgame_battery.py`'s own
`taxonomy()`/`outcome_signature()` do — paired task-id sets, never bare
counts, per this arc's own standing discipline.

---

## 4. Predictions, stated before running (falsifiable)

1. **All 9 `tier1_single_op` tasks pass in BOTH arms at default budget.**
   Each is directly reachable by one `DEFAULT_STR_OPS` primitive with a
   size of 2-4; none require a const outside `{0,1,2,-1}` except
   `first_three_chars` (needs `3`) and `last_two_chars` (needs `-2`+a
   right-open-slice sentinel) — those two are predicted to FAIL in
   `typed_default` (missing consts) and PASS in `declared`.
2. **Most `tier2_composition` tasks pass in `declared`; a minority pass
   in `typed_default`** (`double_string`, `capitalize_then_reverse`,
   `trim_first_and_last_char`, `first_and_last_char` need no consts
   beyond `{0,1,2,-1}` or no ops beyond `DEFAULT_STR_OPS` and may pass in
   `typed_default` too; `first_word`/`last_word`/`reverse_first_word`
   need `First`/`LastElem`, absent from `DEFAULT_STR_OPS` by construction
   — predicted to fail `typed_default`, pass `declared`).
3. **`shout`, `title_case_words`, `strip_whitespace` (the three
   `tier3_deep_or_missing` controls) FAIL in BOTH arms at BOTH budgets** —
   §1.2's confirmed-absent-primitive finding predicts this is a hard
   ceiling, not a search-cost wall; if either budget escalation finds
   them, that would falsify §1.2's reading of the source and is worth
   reporting as a correction, not suppressing.
4. **`first_three_reversed`/`initials_capitalized_concat`
   (`tier3_deep_or_missing`'s two REACHABLE members) pass in `declared`**
   at default or high budget — a contrast showing the tier's failures are
   primitive-shaped, not generically "tier 3 is too hard."
5. **`pbe_024`/`pbe_026` (the primary memorization-trap probes) reproduce
   the MBPP-measured mechanism**: found-but-wrong (a bare/lookup-shaped
   candidate that fails the held-out row) on the PRE-fix engine, found-
   correct (the genuine composition) on the POST-fix (current, unmodified)
   engine — checked via the git-history before/after comparison described
   in §2.1, NOT by editing any `.rs` file in this worktree.
6. **`pbe_023` (control) passes under both pre-fix and post-fix
   conditions.** **`pbe_025` (tie-zone) is reported with no confident
   advance prediction.**

Any prediction above that turns out FALSE is reported as found, exactly
as measured, in `PBE_STRING_BENCHMARK_RESULTS.md` — per this arc's
standing rule that a null which localises its own cause is a better
outcome than a smoothed-over pass.

---

## 5. What this document does NOT establish

1. No measurement has been run yet — every number above is a prediction
   derived from reading the source, not an observed result.
2. Whether an external, citable FlashFill/SyGuS benchmark set exists and
   is reachable from this environment was not conclusively determined
   (no network fetch was attempted) — this corpus is built fresh instead
   of asserting a citation that cannot be verified.
3. The `declared` arm's `PBE_OPS`/`PBE_CONSTS` inventory is ONE
   reasonable fixed choice, not a claim that it is the unique or minimal
   inventory needed — a different fixed inventory might reach more or
   fewer tasks; this is named as a design choice, not derived from first
   principles.
4. This rung makes NO Rust changes. The pre-fix/post-fix comparison in
   §2.1 uses `git checkout` of an ALREADY-EXISTING prior commit for a
   scoped, temporary diagnostic rebuild in this same worktree, restored
   to the current (post-fix) engine before this worktree is left for the
   orchestrator — it is not a code change authored by this rung.
