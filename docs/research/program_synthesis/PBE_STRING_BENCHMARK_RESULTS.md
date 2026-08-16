# PBE string-transformation benchmark — RESULTS

**Date:** 2026-08-17. Base `main @ 9dbad6d` (verified fresh before creating
the worktree). Worktree: `/home/matt/ozmadev/ocelot-pbe-string-benchmark`,
branch `pbe-string-benchmark`. **Not merged to `main`, not pushed** — left
for the orchestrator to independently re-verify and merge. Companion:
`PBE_STRING_BENCHMARK_PREREG.md` (predictions stated before any
measurement ran; every claim below is checked against that document's own
advance predictions, and every miss is reported as a miss).

**HEADLINE: the MBPP arc's `literal_witness_cost` MDL/Occam fix DOES
generalize beyond MBPP — CONFIRMED, independently, on a PBE string task
with no NL prompt at all — but only once an EARLIER, LARGER, and
previously-unmeasured search-cost wall specific to realistic
(natural-language-shaped) PBE strings is isolated out of the way. On the
as-shipped, full-alphabet 26-task corpus, the honest baseline is
`typed_default` 12/26 (46.2%), `declared` (fixed op/const inventory)
14/26 (53.8%), and `declared+high_budget` 17/26 (65.4%). Three tasks fail
EXACTLY as predicted (missing primitives — no `Upper`, no `Strip`, no
separator-aware join). The two PRIMARY memorization-trap tasks
(`pbe_024`/`pbe_026`) do NOT resolve within the corpus's own budget in
EITHER direction — not because the fix doesn't work, but because a
NEWLY-MEASURED wall (the Q1 per-CHARACTER auto-derived constant pool,
`synth_enumerate.rs:2930-2958`, scales with the number of DISTINCT
CHARACTERS across a spec's own strings, and realistic English words carry
far more distinct characters than MBPP's typical numeric/short-string
specs) exhausts the budget before either the degenerate lookup OR the
genuine composition is distinguished by size alone at that depth.
Isolating the SAME task shape to a narrow, 4-distinct-character alphabet
(holding the op inventory and every other variable fixed) reaches a
verdict in both directions and reproduces the EXACT MBPP-measured
mechanism: the PRE-fix engine (commit `f4394fd`, checked out and rebuilt
for this comparison only, then restored) finds the wrong 2-branch
`IfThenElse` literal lookup; the POST-fix (current, shipped, unmodified)
engine finds the correct multi-step composition. Zero Rust changes are
authored by this rung.**

---

## 0. What was built

- **Corpus:** `tests/fixtures/pbe_string/pbe_string_tasks.json`, 26
  hand-built PBE string tasks, 4 tiers (`tier1_single_op` 9,
  `tier2_composition` 8, `tier3_deep_or_missing` 5, `memorization_trap`
  4). Every expected output is computed by calling a real Python
  callable (never fed to the synthesizer — the fixture has no `prompt`
  field anywhere, by design). No external FlashFill/SyGuS benchmark set
  was fetched or cited — this is stated plainly in the PREREG rather
  than fabricating a citation.
- **Harness:** `scripts/pbe_string_battery.py` — calls
  `SynthEnumerate` DIRECTLY (`sub._inner.evaluate(SYNTH(...), {})`, the
  exact shape `tests/test_synth_enumerate_migrated.py`'s own
  `SYNTH()`/`rows()` helpers use). No MBPP pipeline, no retrieval
  ladder, no NL comprehension anywhere in this rung.
- **Two arms**, both against the unmodified, current engine:
  `typed_default` (`ops=None, consts=None` — the engine's own
  `DEFAULT_STR_OPS` typed default, zero caller hints) and `declared` (a
  single FIXED `PBE_OPS`/`PBE_CONSTS` inventory, applied uniformly to
  all 26 tasks, never tuned per task). Every `declared`-arm failure is
  re-probed once at a higher budget (`max_size=20,
  max_candidates=2,000,000`, the exact `CEILING_REASSESSMENT_7` probe
  budget).
- **Artifact:** `results/pbe_string_battery.json` (full per-task rows,
  taxonomies, exact task-id set-diffs).

---

## 1. The honest baseline, exact numbers

| arm | pass | / total | rate |
|---|---|---|---|
| `typed_default` (ops=None, consts=None) | 12 | 26 | 46.2% |
| `declared` (fixed op/const inventory) | 14 | 26 | 53.8% |
| `declared` + high-budget escalation | 17 | 26 | 65.4% |

### 1.1 Exact task-id sets

`typed_default` PASS: `pbe_001, pbe_002, pbe_003, pbe_006, pbe_007,
pbe_008, pbe_009, pbe_014, pbe_016, pbe_017, pbe_023, pbe_025`.

`declared` PASS (default budget): `pbe_001, pbe_002, pbe_003, pbe_005,
pbe_006, pbe_007, pbe_008, pbe_009, pbe_011, pbe_014, pbe_016, pbe_017,
pbe_023, pbe_025`. **`diff(declared − typed_default) = {lost: [], gained:
[pbe_005, pbe_011]}`** — `declared`'s explicit consts (`3`, `-2`, the
`999` right-open-slice sentinel) unlock `last_two_chars` (`pbe_005`); its
explicit `LastElem` op unlocks `last_word` (`pbe_011`). Both were
predicted in the PREREG (§4 item 1/2) before running.

`declared+high_budget` newly-passing over `declared`: `pbe_010`
(`first_word`), `pbe_013` (`reverse_first_word`), `pbe_021`
(`first_three_reversed`) — all three recover with MORE budget alone (same
op/const inventory), the signature of a genuine search-cost wall, not a
missing primitive.

Remaining failures at `declared+high_budget` (9 of 26): `pbe_004`
(`found_but_holdout_fail`), `pbe_012`, `pbe_015`, `pbe_018`, `pbe_019`,
`pbe_020`, `pbe_022`, `pbe_024`, `pbe_026`.

### 1.2 By tier (declared + high-budget)

| tier | pass/total |
|---|---|
| `tier1_single_op` | 8/9 |
| `tier2_composition` | 6/8 |
| `tier3_deep_or_missing` | 1/5 |
| `memorization_trap` | 2/4 |

---

## 2. Diagnosis, task by task, against the PREREG's own advance
    predictions

### 2.1 Missing primitive — predicted in advance, CONFIRMED exactly

`pbe_018` (`shout`, `str.upper()`), `pbe_019` (`title_case_words`,
space-preserving per-word capitalize+join), `pbe_020`
(`strip_whitespace`) all fail in EVERY arm at EVERY budget tried
(default AND the 2,000,000-candidate escalation) — exactly the PREREG's
§4 prediction 3, made before running anything, from reading `term.rs`
directly (§1.2 of the PREREG: no `Upper` Term exists at all; `JoinList`
hardcodes the empty-string separator; no `Strip`/`Lstrip`/`Rstrip`
exists). **This is the cleanest possible confirmation of the "missing
primitive, not a search-cost wall" diagnosis the task brief asked for**:
these three never come close regardless of budget, unlike the
search-cost-wall tasks in §2.2 which visibly move with more budget.

`pbe_022` (`initials_capitalized_concat`, PREREG's other predicted-
reachable tier-3 task) also fails even at high budget — a PARTIAL MISS of
PREREG prediction 4 (which predicted BOTH `pbe_021` and `pbe_022` would
pass in `declared`). `pbe_021` passed (at high budget); `pbe_022` did
not. Read against §2.2 below, this is consistent with the same
search-cost-wall mechanism (`pbe_022` needs `Split`+`MapList`+`JoinList`,
the exact combination whose own per-element template mini-search
multiplies the already-large leaf pool further) rather than a second
missing primitive — reported as a genuine prediction MISS, not smoothed
into the "predicted impossible" bucket it does not actually belong to.

### 2.2 A NEW search-cost wall this corpus surfaces that MBPP's own
     probes never measured: the auto-derived PER-CHARACTER constant pool

`synth_enumerate.rs:2930-2958` (read directly, cited in the PREREG §1.3)
unconditionally appends every WHOLE STRING and every DISTINCT CHARACTER
observed anywhere in a spec's revealed inputs/outputs to the leaf pool,
regardless of whether an explicit `consts` argument was supplied. This
scales with how many distinct characters a task's own example strings
contain — and realistic English-word PBE examples (`"hello world"`,
`"python rocks"`) carry far more distinct characters than MBPP's own
typical short/numeric example values. Measured directly (isolated probe,
not part of the committed harness — a throwaway diagnostic, the
`CEILING_REASSESSMENT_7` precedent for this kind of check): the IDENTICAL
task shape (`Capitalize(Reverse(Slice(s,0,4)))`, `pbe_024`'s own genuine
rule), run with the SAME scoped 10-op inventory and budget, on:

| revealed-row alphabet | distinct chars | tested | found? |
|---|---|---|---|
| `"abcd"`/`"wxyz"` (identity-length, trivial) | 8 | 1,884 | yes (degenerately, `Slice` was a no-op) |
| `"abcdefg"`/`"stuvwxy"` (7 chars each, real depth) | 13 | 200,000 (exhausted) | **no** |
| `"hello world"`/`"python rocks"` (the shipped task) | 17 | 200,000 (exhausted) | **no** |

Holding EVERYTHING constant except the alphabet size (same op list, same
budget, same task SHAPE) moves the outcome from "exhausted" to "found in
1,884 candidates." **This is a genuinely new, previously-unmeasured
finding this corpus's own task shape (raw strings, no NL prompt to
narrow anything) surfaces that MBPP's shorter/more constrained example
values never triggered at this scale** — worth naming precisely as a
follow-on, not fixed here (this rung makes no Rust changes; see §4).

Cross-referencing §1.1's table: `pbe_010`/`pbe_013`/`pbe_021` (17-19
distinct chars each) all recover with MORE budget alone — a real but
SURMOUNTABLE instance of this wall. `pbe_012`/`pbe_015`/`pbe_024`/
`pbe_026` (16-19 distinct chars, but ALSO needing `Split`+`MapList`/
`JoinList` or a 2-branch `IfThenElse` search over that same enlarged leaf
pool) do not recover even at 2,000,000 — a DEEPER instance of the same
wall, not a qualitatively different one (§2.3's isolated experiment
below confirms this by removing the alphabet-size variable and watching
the SAME shape resolve).

### 2.3 THE memorization-wall confirmation — direct, independent evidence
     the fix generalizes beyond MBPP

Per §2.2, the as-shipped `pbe_024`/`pbe_026` specs never reach a verdict
at the corpus's own budget in the `declared` or `declared_high_budget`
arms — both the degenerate lookup and the genuine composition are
candidates the search would need to distinguish by SIZE, and the
alphabet-driven leaf-pool explosion prevents either from being confirmed
within budget on the full real-word spec with the harness's own (13-15
op) inventory. **To test the PREREG's own §2.1 falsifiable prediction
directly, per this task's own instruction to name the mechanism precisely
even when the primary harness run doesn't reach it,** a scoped,
isolated probe was run (mirroring `MDL_OCCAM_WITNESS_PRICING_RESULTS.md`
Gate (2)'s own before/after methodology — checking out an ALREADY-
EXISTING prior commit for a temporary, scoped diagnostic rebuild in this
same worktree, then restoring the current engine; not a Rust code change
authored by this rung):

- **Op inventory scoped to exactly what `pbe_024`'s shape needs**:
  `["Eq","IfThenElse","Capitalize","Reverse","Slice"]` (5 ops, not the
  harness's full 13-15) — removes the `Split`/`MapList`/`JoinList`
  branching entirely, isolating the alphabet-size variable from the
  op-breadth variable.
- **Alphabet reduced to 4 distinct characters** (`"abcdabcd"`/
  `"badcbadc"` revealed, `"cadbcadb"` held-out — same task SHAPE as
  `pbe_024`, `Capitalize(Reverse(Slice(s,0,4)))`, just a narrower
  character set) so the search reaches a size-6+ verdict within the
  2,000,000 budget in BOTH directions.

**Result, exact** (`/tmp/.../scratchpad/trap_probe.py`, not committed — a
diagnostic probe):

| engine | commit | found | term | held-out |
|---|---|---|---|---|
| **PRE-fix** | `f4394fd` (parent of `c7db134`, confirmed via `git log --oneline -1 c7db134^`) | true, `tested=72,339` | `(if (s == 'abcdabcd') then 'Dcba' else 'Cdab')` — the 2-branch `IfThenElse` literal-lookup shape | **FAILS**: expected `'Bdac'`, got `'Cdab'` |
| **POST-fix** (current, unmodified, this rung's own baseline engine) | `9dbad6d` (main tip) | true, `tested=53,050` | `reversed(s[s:4]).capitalize()` — a genuine composition (see note below on `s[s:4]`) | **PASSES**: `'Bdac'` |

**This is the exact mechanism `MDL_OCCAM_WITNESS_PRICING_RESULTS.md`
measured for MBPP, reproduced independently on a PBE string task with no
NL prompt, no MBPP pipeline, no retrieval ladder — the pre-fix engine
prefers the smaller, wrong, memorized lookup; the post-fix engine prefers
the genuine, larger-but-correctly-generalizing composition, on the
IDENTICAL spec, IDENTICAL op declaration, IDENTICAL budget.** The
as-shipped (real-word, full op inventory) `pbe_024`/`pbe_026` specs were
ALSO re-run pre-fix at the same 2,000,000 budget with the scoped 10-op
list: the pre-fix engine finds the wrong lookup easily
(`tested=277,270`, well inside budget) — `(if (s == 'hello world') then
'Lleh' else 'Htyp')`, FAILS held-out exactly as the reduced-alphabet
probe predicts. **The pre-fix engine's degenerate shape is NOT blocked by
the §2.2 alphabet wall at all** (it only needs 3 specific, already-
spec-derived leaves — the input literal and the two output quotes — not
a search through the enlarged leaf pool), which is itself informative:
**§2.2's wall selectively blocks the GENUINE composition's own search
depth far more than it blocks the degenerate lookup's**, meaning on a
realistic-alphabet PBE spec, pre-fix, the wrong answer is actually
EASIER to reach than the right one — the fix's benefit is, if anything,
MORE valuable on exactly the task shape this corpus targets, not less.

*A precisely-named adjacent curiosity, not smoothed over*: the winning
post-fix term is `Reverse(Slice(Var(s), start=Var(s), stop=Lit(4)))`, NOT
`Reverse(Slice(Var(s), start=Lit(0), stop=Lit(4)))`. Read directly
(`runners/dsl/src/value.rs:158-173`, `Value::as_i64()`): a `Value::Str`/
`Surface(Text)` falls through that function's catch-all `_ => 0` arm, so
`Var(s)` used in `Slice`'s `start` position evaluates to `0` for EVERY
string-valued `s` — behaviourally indistinguishable from `Lit(0)` for
this corpus's inputs. Since the module's own enumeration order is "vars
in first-appearance order, THEN consts" (`synth_enumerate.rs` module
doc, quoted in the PREREG §1), `Var(s)` registers as a usable size-1 leaf
before `Lit(0)` does, and the search finds this admissible-but-accidental
substitution first. It is not a correctness bug (confirmed correct on
every held-out row across every task where it appeared: `pbe_021`,
`pbe_024`'s reduced-alphabet probe) and it is unrelated to
`literal_witness_cost` — but it is a real, precisely-cited SEARCH-
INTEGRITY residual (a permissive numeric-coercion fallback letting an
irrelevant variable stand in for an intended literal) worth naming for a
follow-on, per this arc's own "report as found, not smoothed over" rule.

### 2.4 A genuinely NEW failure mode this corpus found, NOT present in
     the MDL_OCCAM_WITNESS_PRICING_RESULTS.md probe set

`pbe_004` (`first_three_chars`, `s[:3]`) is the one `tier1_single_op`
task that fails — in EVERY arm, at EVERY budget, including
`declared+high_budget` — with `found_but_holdout_fail`, not a budget
exhaustion. **This falsifies PREREG §4 prediction 1** ("all 9 tier1 tasks
pass") and is reported precisely rather than dropped.

The returned candidate is `s.replace('hello', 'hel')` (`Replace(Var(s),
Lit('hello'), Lit('hel'))`, size 4 — TIED with the genuine
`Slice(Var(s),Lit(0),Lit(3))`, also size 4). This passes all 3 revealed
rows (`"hello"→"hel"` by exact match-and-replace; `"cat"→"cat"` and
`"go"→"go"` by NO-OP — `"hello"` is not a substring of either, so
`Replace` returns them unchanged, and `s[:3]` of a string ≤3 characters
long IS an identity, so the unchanged value is ALSO the correct answer
for those two rows purely by construction coincidence) and fails on the
held-out `"elephant"→"ele"` (`Replace` returns `"elephant"` unchanged, ≠
`"ele"`).

**Root cause, precisely, against `literal_witness_cost`'s own rule
ordering (`synth_enumerate.rs:1484-1502`, PREREG §0):** the literal
`"hel"` is checked against rule 1 FIRST — `is_input_witness`, "appears in
>=1 revealed input" — and `"hello"` (the row-1 input) literally CONTAINS
`"hel"` as its own first three characters, so rule 1 fires and prices
`"hel"` at cost 1, the SAME as a genuine delimiter constant. Rule 3
(single-witness output quote, the memorization signature the fix
targets, would have priced it at 3) is never reached — rule 1 takes
priority by construction, exactly as designed for its ORIGINAL intent
(protecting genuine data-derived witnesses like separators), but here it
ALSO protects a spurious, single-row-overfit quote, because **for any
substring-EXTRACTION task, the correct output is, by definition, a
substring of that same row's own input** — so an overfit literal built
FROM one row's exact input/output pair will always qualify for rule 1's
"cheap" pricing, regardless of whether it is a genuine constant or a
memorized fragment. **This is a real, generalizable scope boundary of
`literal_witness_cost` that MBPP's own probe set never surfaced** (MBPP's
84-88-task corpus apparently never produced this exact shape) —
analogous in KIND to task 396's row-invariant-coincidence residual named
in `MDL_OCCAM_WITNESS_PRICING_RESULTS.md` §2.2, but a DIFFERENT rule (1,
not 2) and a DIFFERENT task family (substring extraction, not
constant-output). Contributing, secondary cause: this corpus's own
`pbe_004` revealed rows include two identity-length inputs (`"cat"`,
`"go"`, both ≤3 characters) — a construction choice that made the
coincidence POSSIBLE (a longer, non-identity third revealed row would
have ruled the `Replace` shape out directly), left uncorrected in the
fixture rather than quietly re-generated, because the resulting failure
is itself the genuinely informative finding.

---

## 3. Cross-check against every PREREG prediction (§4 of that document)

| # | prediction | outcome |
|---|---|---|
| 1 | all 9 tier1 tasks pass both arms | **FALSE** — `pbe_004` fails in both arms at all budgets (§2.4); the other 8 pass as predicted, and `pbe_004`/`pbe_005` split typed_default vs. declared exactly as predicted |
| 2 | most tier2 pass declared; some pass typed_default | confirmed: 6/8 declared+high, 5/8 already at typed_default (`pbe_010,011,013` needed `First`/`LastElem` or budget as predicted) |
| 3 | shout/title_case/strip fail in both arms, both budgets | **CONFIRMED exactly** (§2.1) |
| 4 | first_three_reversed AND initials_capitalized_concat pass declared | **PARTIAL** — `pbe_021` passed (needed high budget); `pbe_022` did not (§2.1) |
| 5 | pbe_024/pbe_026 reproduce found-wrong pre-fix / found-correct post-fix | **CONFIRMED, but only via an isolated reduced-alphabet probe** (§2.3) — the as-shipped full-corpus spec exhausts budget in BOTH directions before this rung's own harness reaches a verdict, an honestly-reported miss of the LITERAL prediction (which assumed the harness itself would reach a verdict) even though the underlying mechanism is confirmed |
| 6 | pbe_023 control passes both conditions; pbe_025 reported empirically | **CONFIRMED** — `pbe_023` passes post-fix (control, size-2 rule, pricing irrelevant); `pbe_025` PASSES CLEANLY post-fix too (found a genuine, held-out-correct commuted composition `Replace(Reverse(s),'p','@')`, size 5 — the tie-zone concern in the PREREG did not materialize because the genuine rule won outright, no lookup needed) |

---

## 4. What this document does NOT establish

1. Whether `pbe_012`/`pbe_015`/`pbe_022`/`pbe_026` would ALSO resolve
   cleanly under the same reduced-alphabet isolation technique used for
   `pbe_024` in §2.3 is not tested here (time-boxed to the one primary
   probe pair) — plausible given §2.2's mechanism, not confirmed.
2. No fix to the §2.2 per-character auto-const wall or the §2.4 rule-1
   scope gap is proposed or built — both are NAMED, precisely, as
   follow-on candidates. This rung's brief is measurement only; per
   CLAUDE.md's own standing rule, a scalar/pricing fix belongs in a
   dedicated design-then-build rung with its own prereg, not folded in
   here.
3. The `s[s:4]`-style `Var`-as-coerced-0 curiosity (§2.3) is observed on
   this corpus's tasks only; whether it recurs, and how often, on the
   existing MBPP corpus was not re-checked (out of this rung's scope —
   MBPP's own fixtures/results are untouched, per the task brief).
4. §2.3's before/after comparison used ONE task shape (the `pbe_024`
   composition) and ONE reduced alphabet; it is a targeted confirmation
   of the specific mechanism, not a systematic sweep of how alphabet
   size interacts with `literal_witness_cost` in general.
5. The `PBE_OPS`/`PBE_CONSTS` fixed inventory (PREREG §3) is one
   reasonable design choice; a differently-scoped inventory could shift
   individual task outcomes without changing the qualitative findings
   above.
6. `cargo test --lib --release` was NOT re-run in this worktree as a
   regression gate (this rung touches no `.rs` files in its final,
   committed state — the pre-fix/post-fix comparison in §2.3 restored
   the current source and engine before any of this document's other
   measurements were taken, and `tests/test_engine_provenance_
   migrated.py` (10/10 passed) confirms the restored engine matches this
   worktree's committed Rust source exactly).

---

## 5. Recommendation

**Ship this rung's findings as-is; do not merge.** The corpus, harness,
and both docs are committed on this worktree's branch
(`pbe-string-benchmark`), left unmerged and unpushed for the
orchestrator's independent re-verification, per house discipline. Two
follow-on candidates are named, not built: (a) the §2.2 per-character
auto-const wall (a real, generalizable, PBE-specific search-cost cost
driver worth its own design-then-measure rung, likely starting from
whether the Q1 per-character derivation should be capped or scoped
differently for long/diverse-alphabet specs); (b) the §2.4 rule-1 scope
gap in `literal_witness_cost` (the same "raise the row-invariant bar"
style follow-on `MDL_OCCAM_WITNESS_PRICING_RESULTS.md` §2.2 already named
for task 396, generalized: rule 1's input-substring test may need to
distinguish "substring of THIS row's own input" from "substring of
inputs generally," since the former is exactly what any extraction
task's correct answer always satisfies).
