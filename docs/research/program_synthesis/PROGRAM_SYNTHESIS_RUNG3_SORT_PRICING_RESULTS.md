# Program Synthesis — Rung 3 (`term:Sort` pricing) — RESULTS

**Status: the question is ALREADY ANSWERED and ALREADY BUILT. `cmp_value_lex`
fully supplies what `term:Sort` needs — `cmp_value` itself was never touched,
there is no fixture-migration blast radius, and `Sort` has been live on
`main` since commit `ebee2e3`, measured at +5 MBPP tasks with zero
regressions. This document's job turned out to be archaeology, not pricing:
locate the prior work, verify it against the code, and reconcile it against
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §5.3`, whose
"do not take this rung until priced" framing is stale — the pricing, the
build, and the measurement all predate that PREREG's own commit.**

Investigation-only. No code, seed JSON, or tests written by this task. This
document is itself the only artifact produced.

---

## 0. The chronology that resolves the question, read directly from `git log`

`git log --oneline -1 main` at the time this task was assigned: `1d7d437`
("Add orphaned PREREG: MBPP structural ceiling reassessment vs
SHAPES-NOT-NUMBERS" — the doc that names Rung 3 in its own §5.3, the brief
for this task). Its own commit message calls it "orphaned" — and reading
`git log` for the two files Rung 3 actually touches shows why: it is
orphaned because the work it asks to be priced was **already done, three
commits back in the same branch's own linear history**:

```
git log --oneline -- runners/dsl/src/synth_enumerate.rs | head -8
f0215c6 Derived-operator tier slice 1: ...
45e987c GroupCount/DictMerge: two new stdlib Term ports + a dict-key wire fix
84b3d04 progsyn: widen SortBy op-list gate to spec_has_list_of_lists (task 64)
3b2e3c0 Program synthesis: extend map-template-pool ...
4c09dc9 progsyn: DictItems + SortBy Terms (task 475 witness confirmed live)
ebee2e3 progsyn SetLit/DictItems rung: Sort Term + SetMap/Intersect/Union
         ops, 141/232/473 witnessed in-budget
5b8c2c7 Program synthesis Rung 1: 10 Tier-1 stdlib Term ports, MBPP 49->54
```

`git log --oneline -3 main` from `1d7d437`:

```
1d7d437 Add orphaned PREREG: MBPP structural ceiling reassessment vs SHAPES-NOT-NUMBERS
c4e6616 Merge derived-operator-tier-slice1: Call{name,args} + build-A fallback + Total2 parity
f0215c6 Derived-operator tier slice 1: Call TermNode + build-A fallback + Total2 parity
```

`ebee2e3` — the commit that built `term:Sort` — is a strict ancestor of
`f0215c6`/`c4e6616`, which are themselves the immediate parent of `1d7d437`.
**`term:Sort` was built and merged to `main` before the PREREG naming it as
"Rung 3, price before committing" was ever written.** The PREREG's §5.3 is
not wrong about what it says to do — it is simply describing a state of the
world (`Sort` unpriced, unbuilt) that had already stopped being true by the
time it was committed. This is exactly the failure mode the doc's own title
names: an "orphaned" document, disconnected from the branch it landed on.

---

## 1. `STRUCTURAL_CEILING.md §7.2`/§9 — the ORIGINAL pricing, read in full

`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` (2026-08-01) named the
problem precisely: `sorted`/`min`/`max`/`Gt`/`Lt` order strings by
**interner symbol id** (`value.rs::cmp_value`, `(Value::Str(x),
Value::Str(y)) => x.0.cmp(&y.0)`) — i.e. by the order the process happened
to first intern each string, not alphabetically. Blast radius as named
there: `sorted`/`min`/`max`/`Argmax`/`MaxOver`; the canonical storage order
of every `Value::Set`/`Value::FrozenSet`; `Value::Dict` key order;
`Gt`/`Lt`/`Gte`/`Lte`. §9's recommendation: **"Do not take `term:Sort` yet
... It drags in §7.2's cross-cutting order correction, and that correction
should be priced against frozen fixtures *before* it is committed to."**
Null condition 4 (§1) states the stakes: "If the only two options are a
wrong sort and a fixture migration, the ordering class is mis-scoped and its
4 ids must be re-priced." This is the objection Rung 3 was assigned to
resolve — read here directly from the source document, not inherited from
the reassessment PREREG's restatement of it.

---

## 2. `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md` — the narrower fix that
   actually resolves it, read in full

Landed at `4621dca` ("cmp_value lexicographic follow-on: 8 reported-order
sites fixed via cmp_value_lex, cmp_value itself untouched") — **before**
Rung 1 even started, per `VALUELAYER.md §9.3`'s own UPDATE note citing it.
The fix: a new function, `value.rs::cmp_value_lex(a: &Value, b: &Value,
interner: &Interner) -> Ordering`, structurally identical to `cmp_value`
except `(Value::Str(x), Value::Str(y)) => interner.resolve(*x).cmp(interner.resolve(*y))`
— resolves both interned symbols to their actual byte strings and compares
those, instead of comparing symbol ids. Read directly, `value.rs:461-538`
(current `main`):

```rust
pub fn cmp_value_lex(a: &Value, b: &Value, interner: &crate::sym::Interner) -> Ordering {
    // ... same tag() ordering as cmp_value for cross-type comparisons ...
    match (a, b) {
        // ... Int/Float/Rational arms identical to cmp_value ...
        (Value::Str(x), Value::Str(y)) => interner.resolve(*x).cmp(interner.resolve(*y)),
        (Value::Node(x), Value::Node(y)) => x.cmp(y),
        (Value::Bool(x), Value::Bool(y)) => x.cmp(y),
        (Value::Tuple(xa), Value::Tuple(ya)) | (Value::List(xa), Value::List(ya)) => {
            // recurses into cmp_value_lex, not cmp_value
        }
        (Value::Set(xa), Value::Set(ya)) | (Value::FrozenSet(xa), Value::FrozenSet(ya))
        | (Value::Set(xa), Value::FrozenSet(ya)) | (Value::FrozenSet(xa), Value::Set(ya)) => {
            // recurses into cmp_value_lex, not cmp_value
        }
        // ... Dict arm, same recursion pattern ...
    }
}
```

**Critically, `cmp_value` itself has zero changed lines** — verified in the
FOLLOWON_RESULTS doc by `git diff` on the function body (empty diff) and
independently re-confirmed here by reading `value.rs:325-460` (the
`cmp_value` function as it stands on current `main`): the `(Str, Str)` arm
is still `x.0.cmp(&y.0)` — untouched, boot-order comparison, exactly as
before.

**8 call sites were switched from `cmp_value` to `cmp_value_lex`**:
`cmp_bool` (`Lt`/`Lte`/`Gt`/`Gte`), `numeric_argmin`/`numeric_minmax`/
`numeric_argmax` (`ArgMin`/`Min`/`Max`/`ArgMax`), `min_or_max_over`
(`MinOver`/`MaxOver`), `argmin_or_argmax_over` (`Argmin`/`Argmax`/
`ArgminUnique`), and the `"min"`/`"max"`/`"sorted"` `ProgEval` externs.
**51 canonicalisation-only call sites — Set/Dict construction, persistence,
`shape_decode`'s frame correspondence — were read, classified, and
deliberately left on `cmp_value`, unchanged.** This is the load-bearing
design fact: the fix is scoped to *reported-order* comparisons (what a
caller or rule reads back as an ordering decision) and explicitly excludes
*canonicalisation* comparisons (internal storage order of a `Set`/`Dict`,
which any consistent order serves equally well and which frozen fixtures
depend on staying stable).

---

## 3. Is `cmp_value_lex` reusable for `term:Sort` directly? Yes — and it
   already was, verified against the actual evaluator, not inferred

The question this task was assigned to answer: is `cmp_value_lex` general
enough (works on arbitrary `Value::Str` pairs, not scoped to some narrower
"reported order" context) to drive a `Sort` TermNode directly, sidestepping
`cmp_value` and its fixture-touching blast radius entirely?

**Yes, on every count, confirmed by reading the actual code, not by
argument:**

1. **Signature is fully general.** `cmp_value_lex(a: &Value, b: &Value,
   interner: &Interner) -> Ordering` takes two arbitrary `Value`s and the
   interner already threaded through every `Term` evaluator's `ctx`
   (`ctx.interner`, the same field row 1's `cmp_bool` already reads). There
   is no narrower "reported order" wrapper type, no caller-supplied context
   object beyond the interner every evaluator call already carries.
2. **It recurses fully** — `Tuple`/`List`/`Set`/`FrozenSet`/`Dict` all
   recurse into `cmp_value_lex` (not `cmp_value`) for their nested elements,
   so a `Sort` over a list of tuples-containing-strings is lexicographic at
   every depth, not just the top level.
3. **It was already the exact template for a Term-native consumer.**
   `numeric_argmin`/`numeric_minmax`/`numeric_argmax`/`min_or_max_over`/
   `argmin_or_argmax_over` (rows 2-6 of the FOLLOWON_RESULTS call-site
   table) are `Term` evaluators — `ArgMin`/`Min`/`Max`/`MinOver`/`MaxOver`/
   `Argmin`/`Argmax` — already switched to `cmp_value_lex` before Rung 3 was
   ever assigned. `Sort` is the same class of consumer (an ordering
   decision a caller/rule observes) as these five, not a new class.
4. **And it is, in fact, exactly what was built.** Reading
   `runners/dsl/src/term.rs:5334-5349` (current `main`, `TermNode::Sort`'s
   evaluator) directly:

   ```rust
   TermNode::Sort { seq } => {
       let v = evaluate(arena, *seq, env, ctx);
       match v {
           Value::List(items) => {
               let mut v: Vec<Value> = items.iter().cloned().collect();
               v.sort_by(|a, b| crate::value::cmp_value_lex(a, b, ctx.interner));
               Value::List(std::sync::Arc::new(v.into_iter().collect()))
           }
           Value::Tuple(items) => {
               let mut v: Vec<Value> = items.iter().cloned().collect();
               v.sort_by(|a, b| crate::value::cmp_value_lex(a, b, ctx.interner));
               Value::Tuple(std::sync::Arc::new(v.into_iter().collect()))
           }
           other => other,
       }
   }
   ```

   This is the reuse the task asked me to check for feasibility — it is not
   hypothetical, it is the actual shipped implementation. `Sort` calls
   `cmp_value_lex` directly and never touches `cmp_value`. **No fixture
   migration is needed because nothing that produces or stores a `Set`/
   `Dict` was changed — `Sort`'s output is always a `List`/`Tuple` (or a
   pass-through for any other shape), never a canonicalised `Set`/`Dict`
   construction, so it never enters the 51 call sites that were
   deliberately left alone.**

**Answer to the precise question this document was assigned: `cmp_value_lex`
already supplies exactly what `Sort` needs, in full, with no gap.** The
"is it scoped too narrowly to reuse" branch of the task's own §3 does not
apply — there was no narrowness to find.

---

## 4. Was the fixture-migration cost priced anyway, as a check? Yes — the
   PREREG's own recommended fallback path — and it came back zero, not
   merely "not measured"

Because Rung 3 (under its original, earlier name, before the reassessment
PREREG re-raised the same question) was priced and built with the exact
discipline `STRUCTURAL_CEILING.md §9` demanded, the fixture-migration
question was not left as a theoretical "should be fine" — it was measured:

- **`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_PREREG.md`/
  `_RESULTS.md`** (commit `aecfe8b`, predating `ebee2e3`) is the FIRST pass
  at this exact question. Its own finding: "`cmp_value_lex` reuse retires
  the original cross-cutting-fixture-risk objection" — i.e., this exact
  reuse argument was already identified as sound at that point — but the
  REALISTIC REACH at that time was priced at exactly 1 unwitnessed task
  (`141` alone, since `232`/`473`/`475` also needed `SetLit`/`DictItems`,
  not yet built), an expected value judged too low against the multi-file
  Term touch-point cost. **NO-GO at that point was an expected-value call,
  not a fixture-risk call** — the fixture-risk objection had already been
  cleared by the same `cmp_value_lex` reasoning this document re-derives.
- **`PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_PREREG.md`/`_RESULTS.md`**
  (commits `ebee2e3`/`cb8c97b`) reopened the question once `SetLit` was
  found to already be fixed (a stale citation — `Lit({1,2,3})` had been
  fixed on 2026-08-03, two days after `STRUCTURAL_CEILING.md` measured it,
  by an unrelated `py.rs` wire-boundary rung) and `SetMap`/`Intersect`/
  `Union` were identified as zero-new-`TermNode` op-table exposures of
  already-shipped Terms. This raised `Sort`'s realistic reach from 1 to 3
  hand-witnessed, in-budget candidates (141, 232, 473) and this is where
  `Sort` was actually built, with the touch-point set Rung 1's own
  commit (`5b8c2c7`) served as the template for (`term.rs`, `jsonio.rs`,
  `reflect.rs`, `term_variants.rs` — no `value.rs` changes beyond the
  already-landed `cmp_value_lex`).

**Regression evidence, read from `SETLIT_DICTITEMS_RESULTS.md §5` and
independently spot-checked against `value.rs`/`term.rs` on current `main`
in this task's own reading (§1-3 above):**

- `cargo test --lib --release`: 774/774 (772 pass + 2 pre-documented,
  unrelated `dim_infer_tests` thread-race flakes, confirmed identical to
  the pre-existing baseline).
- Named 9-file Python regression suite: 3 failed / 241 passed, **byte-
  identical** between an independently-run "before" worktree and "after" —
  all three failures pre-existing, traced to unrelated causes (task-267
  construction-path drift; shared-mutable-output-path fragility in the
  battery script itself), none touching string ordering or Set/Dict
  fixtures.
- Full MBPP battery, exact task-id set diff: `56/257 → 61/257`, newly
  passing `{71, 141, 232, 428, 473}`, **regressed (lost): []** — the
  before-pass-id set is a strict subset of the after-pass-id set.

**No frozen fixture broke. None was expected to, because none was
touched** — the entire design, both as reasoned in §3 above and as verified
by the actual regression run, keeps `Sort` off `cmp_value` and off every
Set/Dict-construction call site. The "fixture-migration cost" the original
`STRUCTURAL_CEILING.md §7.2`/§9 worried about was priced at its true
value: **zero**, because it was never incurred — `cmp_value_lex` made the
wide `cmp_value` correction (which WOULD have had that cost) unnecessary
in the first place.

---

## 5. What this document does NOT establish

1. **This is not new pricing work.** Every number and finding above is
   read from three already-committed, already-merged documents
   (`CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md`,
   `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG2_RUNG3_RESULTS.md`,
   `PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_RESULTS.md`) and directly-read
   source (`value.rs`, `term.rs`, `synth_enumerate.rs`), cross-checked
   against `git log` for commit order. No new build, battery run, or test
   was executed by this task.
2. **`Sort`'s realized reach (5 tasks: 71, 141, 232, 428, 473) came bundled
   with `SetMap`/`Intersect`/`Union`/a `Sort(Var(__item))` map template**
   — the SETLIT_DICTITEMS rung's own scope, not `Sort` in isolation. This
   document does not attempt to isolate what fraction of the +5 is
   attributable to `Sort` alone vs. the companion ops; the source RESULTS
   doc's own §7 already names this same limitation for its `_plain()`
   fix's downstream readers and for task 428's construction path.
3. **Task 475 (`sort_counter`) remains unsolved** — it needs `DictItems`
   (built, `4c09dc9`) plus a key-projected `SortBy` (also built,
   `4c09dc9`/`3b2e3c0`/`84b3d04`, per the same git log), but whether that
   combination actually converts 475 is outside this document's scope to
   verify — it belongs to the `DICTITEMS_SORTBY_RESULTS.md` chain, not to
   the `term:Sort`/`cmp_value` question this document was assigned.
4. **The reassessment PREREG's other rungs (1, 2, 4) are untouched by this
   finding** — this document only resolves §5.3 (Rung 3 in that doc's own
   numbering). Whether the reassessment PREREG's Rung 1/2/4 are themselves
   similarly stale/already-actioned was not checked here and would need
   its own pass against `git log` the same way this document checked Rung
   3.
5. **`shape_decode.rs`'s 23 canonicalisation call sites and the other 28
   non-fixed `cmp_value` call sites are unaffected and unexamined further
   here** — they were already read and classified in
   `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md §2.2`, and this document
   adds no new information about them; it only confirms `Sort`'s evaluator
   is not among them.

---

## 6. Verdict

**GO — but retroactively: `term:Sort` is not a rung to take, it is a rung
already taken.** `cmp_value_lex` fully supplies what `Sort` needs (§3);
`cmp_value` and every canonicalisation-only call site remain byte-unchanged
(§2-3); the fixture-migration blast radius `STRUCTURAL_CEILING.md §7.2`/§9
warned about was priced at zero and confirmed at zero by a real, paired,
zero-regression battery run (§4). `term:Sort` has been live on `main` since
`ebee2e3`, contributing to a measured MBPP gain of 56→61 (+5:
`71, 141, 232, 428, 473`) with zero lost passes and zero new Rust or Python
regressions.

**Price, stated concretely, matching what the brief asked for:**

| item | value |
|---|---|
| new Term variants | 1 (`Sort { seq: TermIdx }`) — plus 4 more from the same rung's companion ops (`DictItems`, `SortBy`, `GroupCount`, `DictMerge` across follow-on commits), 0 new variants for `SetMap`/`Intersect`/`Union`/`Total2`-family (op-table exposures of already-shipped Terms) |
| new `value.rs` ids/functions | 0 beyond the already-landed, already-priced `cmp_value_lex` (a prior, separate rung) |
| `cmp_value` changes | **0 lines** — confirmed by direct read of `value.rs:325-460` on current `main` |
| fixture-touch count | **0** — no frozen fixture was found broken; none was expected to be, because `Sort`'s evaluator never reaches a `Set`/`Dict`-construction call site |
| regression risk | measured LOW: Rust 774/774, Python named-suite 3/241 identical before/after (pre-existing causes only), MBPP zero lost passes |
| MBPP yield | +5 measured (`71, 141, 232, 428, 473`), against the SETLIT_DICTITEMS PREREG's own pre-registered ceiling of 3 |

**The one substantive action item this document surfaces**: the reassessment
PREREG (`1d7d437`) should be treated as superseded on this point — a future
reader following its §5.3 literally would spend effort re-pricing and
re-building something that already shipped. This document is the
reconciliation record; no code follow-up is needed for `term:Sort` itself.
