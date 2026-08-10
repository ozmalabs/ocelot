# ARC 6 — TIER 0: the `SynthEnumerate` op-table widening

**Date:** 2026-08-02
**Status:** BUILT AND MEASURED, against `PROGRAM_SYNTHESIS_ARC6_PREREG.md`.
**Artifact:** `results/arc6_tier0.json` (paired id lists, per-unit attribution,
three engine sha256s, witnesses).
**Gate:** `tests/test_arc6_tier0_migrated.py` — 18/18.
**Engines:** baseline `5c1b472fe674…` → tier-0 `48da7257f35d…`. Both
reproduced bit-for-bit from source in this tree (§2).

---

## 0. The one-paragraph answer

**All eight units were built, all eight fire, and the primary bar failed
anyway — because the block is not where the ceiling document said it was.**
The enumerator now proposes the *exact witness from
`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §5* for five of the ten
candidate ids, and `ProgEval` computes the **right answer on every revealed
row** for all five. They are then refused by the **row verdict**, which
cannot compare a non-scalar result: `ps_row_pass` reads `Attr(r, "got")`,
and the adapter sets that attribute to `None` for anything outside
`int/float/str/bool`. The correct comparison is *already computed and
already correct* — `cmp_ok = 1.0` on every one of those rows — and the plain
row rules do not read it. So HS1 fails **0/10**, HS2 holds
(**35 ⊂ 36**), HS3 and HS4 pass. The gap the arc set out to close was real
and is closed; a **different, unpriced gap one layer downstream** now
binds, and this document names it precisely rather than absorbing it.

---

## 1. Per-bar verdict

| bar | verdict | evidence |
|---|---|---|
| **HS1** — ≥3 of the 10 B0 ids convert, with constructed witnesses, zero coincidental fits | **FAIL (0 of 10)** | §3, §4 |
| **HS2** — 35/257 must not decrease; after-list ⊇ the 35 | **PASS (36 ⊃ 35, zero lost)** | §2 |
| **HS3** — zero new `TermNode` variants | **PASS** | §5 |
| **HS4** — op table diffs empty against one written from the operator list | **PASS** | §6 |

**HS1's registered null reading applies, but with one correction to its
premise.** The prereg said a fewer-than-3 result means "the S4 conversion
prior does not transfer to this class, and the inventory numbers should not
be pursued." That reading assumed the failure would be *at the proposal
layer*. It is not: the proposal layer did exactly what the ceiling document
predicted. **The honest null is narrower and more useful — the tier-0
inventory converts to zero not because the enumerator cannot find these
programs, but because the pipeline cannot ACCEPT a list-valued answer at
all.** See §7; that is a statement about the verdict layer, not about MBPP
and not about the op table.

---

## 2. The three arms — the rebuild is separated, and it is zero

This intervention *includes* an engine change, and an engine rebuild alone
has already silently moved MBPP results once in this project (34 → 32, with
no seed or Python change — `PROGRAM_SYNTHESIS_ARC5_FINAL.md`). So three arms
were measured, not two.

| arm | code | engine sha256 | pass n | outcome hash |
|---|---|---|---|---|
| **A** baseline | committed `.rs` | `5c1b472fe674…` | **35** | `6212c971…` |
| **B** rebuild-only | committed `.rs`, **rebuilt** | `5c1b472fe674…` | **35** | `6212c971…` |
| **C** tier 0 | tier-0 `.rs` | `48da7257f35d…` | **36** | `c49a0e30…` |

- **B − A = ∅ / ∅.** The build is **bit-reproducible**: rebuilding the
  committed source reproduced sha256 `5c1b472fe674…` *exactly*, so arm B is
  not merely equal to arm A, it is the same binary. The rebuild contributes
  nothing and **C − B = C − A**.
- Arm A reproduces the frozen `results/arc5_final.json` pass list exactly
  (35 ids, identical set). Every arm is twin-run identical.
- The tier-0 engine `48da7257f35d…` was itself rebuilt from source twice
  during this work and reproduced exactly both times.

**Paired lists.**

```
A/B pass (35): 16 20 58 59 69 82 84 85 89 90 127 132 135 138 139 142 145 227
               233 234 266 276 278 281 309 312 394 404 406 410 433 443 458
               472 477
C   pass (36): the same 35, PLUS 120
C − B gained : [120]      C − B lost : []          superset: TRUE
```

**Aggregate, with its caveat attached, as registered.** 35/257 = 13.6%
[9.96, 18.35] → 36/257 = 14.0% [10.3, 18.8]. **This is underpowered by
construction; the after point estimate sits inside the before interval. It
is not a detection and is not claimed as one.** The result is the id list and
the witnesses.

### 2.1 The one gained id is a COINCIDENTAL FIT and is not claimed

Task **120** is the only id the aggregate gained, and it does not survive a
constructed-witness sweep. The accepted program is

```
max(36, prod(__item for __item in a[0]))
```

It hard-codes **36** — an auto-appended spec-*output* constant — and reads
only `a[0]`, never the rest of the list. It fits every revealed **and**
held-out row by accident.

| constructed input | program | task's own meaning |
|---|---|---|
| `[[1,1],[1,1]]` | 36 | **1** |
| `[[3,3],[100,100]]` | 36 | **10000** |
| `[[2,2],[5,5],[1,1]]` | 36 | **25** |
| `[[0,5],[7,7]]` | 36 | **49** |

**Four of four constructed inputs refute it.** It is the eighth coincidental
fit on this project's record, it is *not* one of the 10 B0 ids, and it is
recorded as a **wrong accept** — pinned in
`tests/test_reject_informs_repair_migrated.py` with a live proof
(`test_arc6_tier0_wrong_accept_120_is_a_coincidental_fit`) so that no later
phase can inherit it as a genuine conversion.

**With it excluded, the honest conversion count for this build is ZERO.**

---

## 3. What was built — eight units, all firing

Every unit is verified by **live invocation**, never by name, because an
unknown op name in this engine is a **silent no-op** that reads exactly like
an honest null.

| # | unit | what it exposes | fires |
|---|---|---|---|
| 1 | `fix:StringAsSequence` | `Count`/`IndexAt`/`Last`/`In` accept a string | ✅ |
| 2 | `op:TupleOf` | the shipped `Vec` Term | ✅ |
| 3 | `op:ProdList` | the shipped `Prod` Term (the `SumList` twin) | ✅ |
| 4 | `op:ConcatList` | `Fold` + `Append` (the `JoinList` precedent) | ✅ |
| 5 | `op:ArgMaxLenOver` | the arg-twin of the shipped `MaxLenOver` | ✅ |
| 6 | `tmpl:item_in_listvar` | `item (not) in <list var>` | ✅ |
| 7 | `tmpl:len_item_vs_var` | `len(item) OP <scalar var>` | ✅ |
| 8 | `tmpl:nested_reduction` | a quantifier over the bound item in a predicate | ✅ |

`fix:StringAsSequence`, measured both directions (it was the riskiest unit —
a *semantic change to shipped Terms*, not an addition):

```
Count("abc")        0     -> 3          Count([1,2,3])     3 -> 3  (unchanged)
Count("héllo")      6*    -> 5 (chars)  Count(5)           0 -> 0  (unchanged)
IndexAt("abc", 1)   None  -> 'b'        IndexAt([7,8],0)   7 -> 7  (unchanged)
IndexAt("abc",-1)   None  -> 'c'        Last([7,8])        8 -> 8  (unchanged)
IndexAt("abc", 9)   None  -> None       In(1,[1,2])     True -> True (unchanged)
Last("abc")         None  -> 'c'        In("a",["ab"]) False -> False (unchanged)
In("a","cat")      False  -> True       In(1,"cat")    False -> False (unchanged)
In("at","cat")     False  -> True
```

Blast radius was held to the **four named Term arms only**. `Value::len` /
`snapshot` / `contains` / `iter` are untouched, so no reduction, fold, filter
or map silently began iterating strings. Every change replaces a *degenerate*
answer (`0` / `None` / `false`) with the right one; **no non-degenerate
shipped behaviour changed**. (\* `Surface(Text)` already answered with its
byte length and was deliberately left on that path.)

---

## 4. The finding: PROPOSAL is fixed, the ROW VERDICT now binds

For each of the 10 B0 ids, live, through the unchanged pipeline, on revealed
rows only:

| id | proposed term | ProgEval result vs expected | `cmp_ok` | row verdict | outcome |
|---|---|---|---|---|---|
| 106 | `fold(a, __acc=b, __item -> append(__acc, __item))` | **correct, every row** | **1.0** | **fail** | `no_shape` |
| 161 | `[__item for __item in a if not((__item in b))]` | **correct, every row** | **1.0** | **fail** | `no_shape` |
| 257 | `(b, a)` | **correct, every row** | **1.0** | **fail** | `exhausted` |
| 424 | `[__item[-1] for __item in a]` | **correct, every row** | **1.0** | **fail** | `exhausted` |
| 450 | `[__item for __item in a if (len(__item) == b)]` | **correct, every row** | **1.0** | **fail** | `exhausted` |
| 290 | `(len(a[-1]), a[-1])` | matches both revealed rows | 1.0 | fail | `no_shape` |
| 98 | `Div(Prod(a), Count(a))` | — | — | — | `runner_exception:TypeError` |
| 18 | — (budget) | — | — | — | `enumerate_failed` |
| 75 | — (budget) | — | — | — | `enumerate_failed` |
| 310 | — (budget) | — | — | — | `enumerate_failed` |

Five of those proposed terms are **the exact witnesses the structural-ceiling
document published in its §5 table**. The mechanism that refuses them,
verified live on task 257:

```
row inputs={"a": 10, "b": 20}   expected=(20, 10) [tuple]
  got_json = [20, 10]     <- ProgEval computed the RIGHT answer
  eval_ok  = 1.0
  cmp_ok   = 1.0          <- the correct comparison, already computed
  got      = None         <- the attribute ps_row_pass actually reads
  ps_verdict = fail
```

`domains/prog_synthesis.py::eval_and_record` does
`set_attr(r, "got", got if isinstance(got, _SCALARS) else None)` with
`_SCALARS = (int, float, str, bool)`, and `ps_row_pass` requires
`Eq(Attr(r,"got"), Attr(r,"expected"))`. **A tuple-valued answer can
therefore never agree, however correct it is.** The `cmp_ok` fact is right
and is read only by `ps_row_pass_special`, which is scoped to `tol` /
`unordered` rows.

**This is why arc-4 S4 moved 25 and converted 8**: its converting ops
(`SumList`, `MaxList`, `Len`, …) all return **scalars**. Every list-*output*
task was unreachable then for this same reason, and the S4 notes attributed
the shortfall to search rather than to the verdict. Tier 0's units are
overwhelmingly list-*output* units, so the whole inventory lands on the one
place the verdict cannot see.

**The ceiling document did not price this**, and it could not have: it
measured the enumerator's reach and the `Lit` input boundary, never the
output-side row verdict.

---

## 5. HS3 — cost, audited mechanically

**Zero new `TermNode` variants.** Files changed: `runners/dsl/src/term.rs`
(four evaluator arms + two private helpers) and
`runners/dsl/src/synth_enumerate.rs` (op table, template pool, one growth
arm). Gated by
`tests/test_arc6_tier0_migrated.py::test_hs3_no_new_termnode_variants`, which
parses the `TermNode` enum out of both the committed and the live `term.rs`
and asserts the added-variant set is empty. **No Python and no seed file was
touched at all** — `git status` over `domains/` and `seeds/` is empty, and
that too is a gate.

Applying the prereg's own rule — *in a structural seam audit the PRICE;
count variants, not names* — tier 0 cost **8 units, 0 variants, 4 op names,
3 template families**.

---

## 6. HS4 — task-independence, audited both ways

The op table adds exactly `TupleOf`, `ProdList`, `ConcatList`,
`ArgMaxLenOver` — the four op names implied by §9's unit list and nothing
else. The gate diffs the live `OP_TABLE` against the committed one and
asserts the difference **is** that set (no name the units do not imply, none
removed), and separately that each of the eight unit strings appears at its
own implementation site. No operator is named after a task; nothing like
`remove_odd_index_chars` or `binary_reflected_powerset` exists in the diff.

**One judgement call is recorded here rather than buried**, because it is the
only place a blind author might have written something different:
`op:TupleOf` is offered under a **narrower typed default** than the other
three — only when the spec's *output* is tuple-shaped. That is the module's
own existing mechanism (`DEFAULT_STR_OPS` / `spec_is_list_shaped`) applied by
the op's **return type**, not by any task; and it was forced by measurement,
see §7.1.

---

## 7. What broke — the real cost signal

### 7.1 `TupleOf` regressed an already-passing task, and the regression is now a pin

The first cut offered `TupleOf` to every list-shaped spec. **Task 132 went
from `pass` to `gapped:enumerate_failed`** — an HS2 hard fail. Root cause,
isolated by op-subset ablation on task 132's own spec:

| op set | found | size | tested | **distinct** | halt |
|---|---|---|---|---|---|
| S4 default (shipped) | ✅ | 6 | 34 014 | **167** | solved |
| S4 + `ProdList` | ✅ | 6 | 34 015 | 167 | solved |
| S4 + `ConcatList` | ✅ | 6 | 34 014 | 167 | solved |
| S4 + `ArgMaxLenOver` | ✅ | 6 | 34 015 | 167 | solved |
| **S4 + `TupleOf`** | ❌ | — | **200 000** | **14 709** | **budget** |

**Observational-equivalence pruning is what makes this search tractable, and
a tuple constructor defeats it**: two distinct operand pairs almost never
produce the same tuple, so every pair is a new signature, and every new
signature multiplies everything downstream. Two cost controls, both
principled and both documented at the source:

1. **Typed default** — `TupleOf` is offered only when the spec's output is
   tuple-shaped (§6).
2. **Terminal registration** — a `TupleOf` candidate is target-checked like
   any other but is **not stored as a building block**. Nothing in the
   inventory consumes a 2-tuple usefully (`SumList(Vec(a,b))` is just
   `a+b`, which `Plus` already reaches at the same size). **Honest price:
   a nested tuple `Vec(Vec(a,b), c)` is unreachable.**

With both, task 132's spec is solved again at size 6 with `distinct` = 993.
Pinned as `test_tuple_constructor_does_not_regress_an_already_solved_spec`.

### 7.2 `op:ArgMaxLenOver` is much weaker than the ceiling document implies

Caught by this build's own gate, which initially passed *without the unit
existing*. `value.rs::cmp_value` orders two `Tuple`s **by length first**, so
the shipped `MaxList` **already behaves as max-by-length** on tuple-valued
elements. `ArgMaxLenOver` adds nothing there except the **tie-break** (and
the string case, which `fix:StringAsSequence` newly enables). The gate now
carries a live control asserting `MaxList` does *not* fit its rows.

### 7.3 Task 98 turns a gap into a `TypeError` — an adapter fragility exposed

`Div(Prod(a), Count(a))` evaluates to an exact `Rational`, which reaches
Python as a `Fraction`, and `eval_and_record` does
`json.dumps(_plain(got))` → `TypeError: Object of type Fraction is not JSON
serializable`. The whole task now raises instead of gapping. It is a
**pre-existing** adapter fragility (the rational domain landed in arc 5) that
tier 0 is the first thing to reach; it is not a pass regression, and it is
**not fixed here** — fixing it means editing `domains/prog_synthesis.py`,
which is outside tier 0.

### 7.4 Tests reconciled — 6 attributable reds, all one-directional

Baseline for the touched files was measured on **arm A** (committed source,
`5c1b472fe674…`): **1 pre-existing red**
(`test_descent_widening_migrated::test_sum_to_n_class_scalar_loop…`, whose
own comment already flags it as predating every recent phase). After tier 0:
7 red → **6 attributable**, every one a *pin recording that the enumerator
could not do something it now can*. All reconciled in place, with dated
notes, in the improvement direction only:

| file | pin | reconciliation |
|---|---|---|
| `test_search_reach_migrated` | S4-era moved/residual id sets | added `_ARC6_TIER0_*` delta sets held **separately**, so S4's own attribution still bites exactly; plus a new one-directional assertion that the residual may only ever shrink |
| `test_retrieval_migrated` | `MEASURED_OUTCOMES[106]` = `rung "none"` | `_KNOWN_ARC6_TIER0_ENUM_REACH_DRIFT`, the file's own fourth such exception; frozen table **untouched** |
| `test_retrieval_migrated` | "retrieval finds nothing" pinned on 106 | re-pinned 106 → **412**, live-verified `rung=="none"`, `attempts==0.0`; 106's justification (*"the DSL has no op for [tuple+list concat] at all"*) is exactly what `op:ConcatList` falsifies |
| `test_prog_descent_migrated` | "falls to enumerate then **gap**" | now `accepted`; its docstring already named `ProdList` as the missing primitive. The accepted program is verified `Prod(items)` and **swept on 6 constructed inputs** so a correct accept is not mistaken for a coincidental one |
| `test_reject_informs_repair_migrated` | v1.7.0 wrong-accept diff | `_ARC6_TIER0_REACH_IDS` (11 ids), `_ARC6_TIER0_AHF_IDS` (74, an honest held-out catch), `_ARC6_TIER0_WRONG_ACCEPT_IDS` (120), the last with a live constructed-witness proof |
| `test_prog_moves_migrated` | meta-sweep | went green on its own once the above were reconciled |

`cargo test` for the crate does not link in this tree (a pyo3
`extension-module` linker failure across the whole crate, unrelated to these
two files) — pre-existing, recorded, not worked around.

---

## 8. What did not convert, and why — honestly

- **106, 161, 257, 424, 450** — the enumerator proposes the published
  witness and `ProgEval` computes the right answer. **Blocked solely by the
  non-scalar row verdict (§4).** These are the five that would convert if
  that one unit were taken.
- **290** — reaches the same block, but note its proposed term is
  `(len(a[-1]), a[-1])` — the *last* sublist, not the longest, which fits
  both revealed rows only because the longest happens to be last in each.
  **Even with the verdict fixed this would need a wider row set to avoid
  being a seventh coincidental fit.**
- **98** — §7.3, `Fraction` at the adapter boundary.
- **18** — needs `FilterList` + `JoinList` over a *string source*, size 11
  against `max_size = 9`. Over budget, and it additionally needs a string to
  be a valid list *source* (`is_listlike`), which is a fifth Term's worth of
  change beyond the named unit.
- **310** — "string → tuple of characters" needs a **variable-arity** tuple
  constructor. `Vec` as an op is binary; no fixed-arity op can produce an
  output whose length varies with the input. **Paper-reachable only.**
- **75** — `tmpl:nested_reduction` fires, but task 75's inner expression is a
  **divisibility** test and the per-element template grammar this unit reuses
  (deliberately, the shipped MapList pool: `{+, −, ×}`, index, len, lower)
  has **no `Mod`**. Adding `Mod` *because task 75 needs it* is the structural
  form of the A-ceiling's `perrin_sum`, so it was **not taken**. Whether
  `Mod` belongs in that pool on general grounds is a real question — it is
  raised in §9, not answered by helping itself to the id.

---

## 9. Wanting to exceed tier 0 — reported, not taken

Three things made a larger scope tempting. None was absorbed.

1. **The non-scalar row verdict.** This is the highest-value unit found by
   this build and it is *not* in the eight. It is small — the correct
   comparison (`cmp_ok`) is already computed and already right; the plain
   row rules simply do not read it. But it changes the ACCEPTANCE SEMANTICS
   OF EVERY TASK, not just these ten, so its blast radius is comparable to
   `fix:StrOrder`'s and it deserves pricing before it is committed to —
   exactly as the ceiling document said of the string-order fix. **Five B0
   ids are sitting behind it with published witnesses already produced.**
   Estimated shape: `eval_and_record` records the non-scalar result (or the
   existing `cmp_ok` fact is read by the plain rules), plus a re-run of the
   full 257 to price it. **Not taken.**
2. **`Mod` in the per-element template pool** (§8, task 75). Defensible as
   completing `{+, −, ×}` → `{+, −, ×, %}`; indefensible if taken *now*,
   because the population is known. Should be decided by someone who has not
   read task 75. **Not taken.**
3. **`Fraction` at the adapter boundary** (§7.3). A genuine defect, in
   Python, outside tier 0. **Not taken.**

**Nothing here required a new `TermNode` variant, so HS3's stop-and-report
trigger never fired.**

---

## 10. Reproduce

```
# the three arms (each writes results/arc6_tier0_<label>.json)
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_tier0_battery.py after
# the artifact (re-runs every witness sweep live)
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_tier0_report.py
# the gate
OZMA_NO_LLM=1 pytest tests/test_arc6_tier0_migrated.py -q --confcutdir=<this worktree>
```

`--confcutdir=<this worktree>` is required: the worktree is nested inside the
canonical repo, so pytest otherwise loads the parent's `conftest.py` and every
module collapses to `ImportError: cannot import name 'prog_synthesis' from
'domains'`. That is not a red.

**Contamination.** Every unit probe is a *constructed* spec written from the
operator list. The per-candidate trace uses
`split_rows(...)["revealed"]` only, through the unchanged pipeline. Held-out
rows never entered a detection or selection path. Test-split `code` was read
for measurement classification only and entered no codebook, cue vocabulary
or taught shape.
