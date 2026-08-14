# Rung 2 (`inputs_json` symmetric fix) + Rung 3 (`Sort`/string-order pricing) — PREREG

Base `main @ fecd35e` ("Merge progsyn-rung1-tier1: 10 Tier-1 stdlib Term ports,
MBPP 49->54 measured"), verified via `git log --oneline -1 main` immediately
before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/progsyn-rung2-rung3`, branch
`progsyn-rung2-rung3`. Continues
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`'s own plan
(§5.2 Rung 2, §5.3 Rung 3) and `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
RUNG1_RESULTS.md`'s already-shipped Rung 1. Per this task's own instruction,
this document registers BOTH the Rung 2 design and the Rung 3
investigation/pricing plan before either is built.

---

## Rung 2 — `inputs_json` symmetric fix, design

### The exact gap, cited precisely (not re-derived)

`PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md` §6.2 (live witness) + §9.1 (named,
not taken): `_add_example_row`'s `attrs["inputs_json"] = json.dumps(inputs,
sort_keys=True)` (`domains/prog_synthesis.py:583`) round-trips through JSON,
which has one array type — so a **tuple argument** in a corpus assert
(task 106: `add_lists([5, 6, 7], (9, 10)) == (9, 10, 5, 6, 7)`) arrives at
every downstream consumer of `inputs_json` already flattened to a `list`,
before any search or evaluation runs. Measured live in that document,
both ways, same engine:

```
inputs as the pipeline sees them (via inputs_json)
    -> found=False   distinct=16603   halt=budget
inputs with the corpus's own argument types preserved
    -> found=True    distinct=670     halt=solved
       term = fold(a, __acc=b, __item -> append(__acc, __item))
```

The output-side twin of this exact bug was already fixed in the same rung
(the `_wire`/`Value::List` split) — this is the same defect at the row's
**input** side, explicitly named there as "the next rung," not built.

### The fix, symmetric, exactly as named

1. **Write side** (`_add_example_row`, `prog_synthesis.py:582-583`): wrap
   `inputs` in the ALREADY-EXISTING `_wire()` (`prog_synthesis.py:868`,
   built for exactly this tagged-JSON purpose — `{"__tuple__": [...]}` /
   `{"__list__": [...]}` / `{"__fset__": [...]}` / `{"__set__": [...]}`)
   before `json.dumps`, so the wire text itself carries the container-kind
   tag: `json.dumps(_wire(inputs), sort_keys=True)`.
2. **Read side**: add a new, mechanical inverse `_unwire()` next to `_wire`
   — the exact function this codebase does not yet have (confirmed by
   grep: no `_unwire` anywhere in `domains/` or `runners/dsl/src/`) — and
   apply it at every one of the 13 `inputs_json` reader call sites in
   `domains/prog_synthesis.py` (lines 840, 1053, 1128, 1292, 1649, 1798,
   1863, 1938, 2092, 2122, 2153, 2288, 2364, read in full, each confirmed
   to do `json.loads(_text(rat.get("inputs_json")) or "{}")` or the
   `sub.node(r)["attrs"]` equivalent): replace with
   `_unwire(json.loads(...))`.

`_unwire` is the structural inverse of `_wire`, mechanical translation, no
decision — the same class of function CLAUDE.md's own "what good Python
code looks like" sanctions (I/O-boundary translation, not agent logic):

```python
def _unwire(v):
    """Inverse of `_wire` — recovers a native Python tuple/list/set/
    frozenset from a wire-tagged JSON value read back off `inputs_json`.
    Mechanical translation; no decision. A plain dict whose keys are NOT
    exactly one of the four tag names (e.g. the top-level {param: value}
    row-inputs dict) falls through to per-value recursion, exactly
    mirroring `_wire`'s own dict handling."""
    if isinstance(v, dict):
        if list(v.keys()) == ["__tuple__"]:
            return tuple(_unwire(x) for x in v["__tuple__"])
        if list(v.keys()) == ["__list__"]:
            return [_unwire(x) for x in v["__list__"]]
        if list(v.keys()) == ["__fset__"]:
            return frozenset(_unwire(x) for x in v["__fset__"])
        if list(v.keys()) == ["__set__"]:
            return set(_unwire(x) for x in v["__set__"])
        return {k: _unwire(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_unwire(x) for x in v]
    return v
```

**Why every reader, not a subset:** the row's INPUT value now genuinely
carries its true container kind once wire-tagged at write time; any
consumer that skips `_unwire` and does a plain `json.loads` would see the
raw tag dicts (`{"__tuple__": [...]}` ) as opaque payload instead of the
value they encode — a worse, silently-wrong state than today's silent
flattening. Symmetric means EVERY reader, matching the doc's own words
("`_wire`/`_unwire` on `inputs_json`") exactly, not a partial application.

**What is deliberately NOT touched, named up front (matches §9.2's own
scope note):** `persist::decode_value`'s bare-JSON-array-means-`Tuple`
convention is unaffected — this fix only ever WRITES the tagged form
(`_wire` never emits a bare array for a `list`/`tuple`/`set`/`frozenset`),
so no existing bare-array `Lit` literal anywhere in a seed changes meaning.
This is a Python-only, world-adapter-side fix (mechanical I/O translation,
CLAUDE.md's own sanctioned category) — zero Rust changes.

### Predicted effect, stated before measuring

Task **106** converts (670 candidates, `found=True`, per the live witness
above) — the single named prediction, made before this rung's own
measurement, exactly the discipline this task's own brief asks for
("confirm the specific +1 task id matches what was witnessed, or report
honestly if it doesn't"). No other task is predicted to move: `VALUELAYER.md`
names 106 as the ONE task blocked by this specific boundary among the
corpus it examined; this document does not independently re-derive a wider
reach claim.

### Risk, named per the source doc's own caveat

`VALUELAYER.md` §9.1: *"it changes what every task's program **sees**, on
every row"* — every row of every task now passes its true tuple/list/
set/frozenset kind through, not just 106's. This is a real, if
low-probability, regression surface: any task whose PASSING candidate today
relies (even accidentally) on a tuple argument being silently flattened to
a list could, in principle, stop passing. This is exactly why the task
brief requires a full before/after MBPP set-diff (`before_pass_ids ⊆
after_pass_ids`), not a single-task spot-check.

---

## Rung 3 — `Sort` + string-order fix: investigation and pricing plan

### What is priced, cited precisely

`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §4.3/§7.2/§9: `term:Sort` is
one new `TermNode`, priced as "alone: 0, necessary for: 4 (`141, 232, 473,
475`)" — i.e., no task converts from `Sort` alone; all four need it in
combination with something else. `fix:StrOrder` is listed as "the same 4,"
cost **cross-cutting engine semantics**, because `value.rs::cmp_value`'s
`(Str, Str)` arm compares interner symbol ids (boot-order-dependent, not
lexicographic) and is read by `sorted`/`min`/`max`/`Argmax`/`MaxOver`, every
`Value::Set`/`Value::Dict`'s canonical storage order, and `Gt`/`Lt`/`Gte`/
`Lte` between strings — "shipping a sort that is knowingly wrong on strings
is not an option; shipping the fix is a fixture-migration question."

### The plan for this investigation (executed below, in this same
    document, before any code is written for Rung 3)

1. **Read each of the 4 tasks' real MBPP specs directly**
   (`tests/fixtures/mbpp/sanitized-mbpp.json`) rather than trusting the
   priced summary's task-id list at face value — confirm what EACH task
   actually needs beyond `Sort` itself, and whether string ordering is
   genuinely exercised by any of them.
2. **Check whether `cmp_value_lex` (`value.rs:461`, already shipped on
   `main` via `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md`, pre-dating
   this rung) can supply `Sort`'s comparator directly**, the same way its
   8 existing call sites already do (`cmp_value_lex(&a, &b, ctx.interner)`,
   `ctx.interner` already in scope in `term.rs`) — if so, a new `Sort` Term
   needs ZERO changes to `cmp_value` itself, and the "cross-cutting" /
   "can move frozen fixtures" risk the original pricing named does not
   apply to a `Sort` built this way, because `cmp_value`'s own
   boot-order-dependent behaviour (the thing every Set/Dict
   canonicalisation call site and every frozen fixture built on top of it
   depends on) is untouched.
3. **Search broadly** (not just the 9 MBPP-adjacent regression files) for
   tests/fixtures whose expectations depend on `cmp_value`'s CURRENT
   (boot-order) string-ordering behaviour, to size the population that
   WOULD be at risk if `cmp_value` itself were changed — even though step 2
   may make this population irrelevant to what actually ships.
4. **Size the realistic MBPP gain** for `Sort` scoped EXACTLY as this task's
   brief names it ("Sort + string-order fix" — not `boundary:SetLit`, not
   `term:DictItems`, both separate, un-bundled Tier-2 units in the source
   pricing table) — i.e., only count a task as reachable if `Sort` +
   string-safety is SUFFICIENT for it, not merely necessary.
5. **Apply this arc's own honesty discipline**: Arc4 S4's measured 32%
   reach-to-conversion prior, and Rung 1's own "~+8 estimated, +5 measured"
   experience (the estimate ran HIGH, not low) as the standing caution
   against trusting an inventory number.
6. **Make the GO/NO-GO call from what is found**, not from the source
   doc's original framing, and build Rung 3 only if the call is GO.

### Investigation, executed

**Step 1 — the 4 tasks' real specs**, read directly from
`tests/fixtures/mbpp/sanitized-mbpp.json`:

| id | prompt | asserts on | needs beyond `Sort` | strings sorted? |
|---|---|---|---|---|
| **141** | "sort a list of elements" | `pancake_sort([15,79,25,38,69]) == [15,25,38,69,79]` — plain list equality, ints only | nothing else identified | **no — all-integer inputs** |
| **232** | "n largest items" (`heapq.nlargest`) | `set(larg_nnum([...],2)) == set([100,90])` — set-wrapped, ints only | `boundary:SetLit` (the `Lit` boundary refusing Python `set`, §7.4 of the ceiling doc, **out of this rung's declared scope**) | no — ints |
| **473** | tuple intersection via `sorted(ele)` per-pair + set intersection | `tuple_intersection(...) == {(4,5),(3,4),(5,6)}` — set-of-tuples, ints only | `boundary:SetLit` (same gap, out of scope) | no — ints |
| **475** | "sort a dictionary by value" (`Counter(...).most_common()`) | `sort_counter({'Math':81,...}) == [('Chemistry',87),('Physics',83),('Math',81)]` — sorts by the INT value, string keys only carried along unsorted | `term:DictItems` (out of this rung's declared scope) | **no — sorts by value (int); keys (strings) are never compared to each other** |

**Finding, not in the source pricing document at this resolution:** of the
four tasks the original pricing lists as `Sort`'s reach, **three (232, 473,
475) require an additional primitive this rung's own declared scope
explicitly excludes** (`boundary:SetLit`, `term:DictItems` — both separate,
priced-separately Tier-2 units the task brief does not authorise building
alongside `Sort`). **Only task 141 is reachable by `Sort` + string-safety
alone, and 141's own inputs are pure integers — string ordering is not
exercised by the one task actually in reach.** The `alone: 0` cell in the
source table already implied this (no task converts from `Sort` in
isolation); reading the actual fixtures confirms WHY, and confirms the
"necessary for the same 4" framing bundled `Sort` and `StrOrder` at the
UNIT level (a general "don't ship an unsafe sort" engineering discipline)
rather than because any of the 4 specific tasks needs string comparison.

**Step 2 — `cmp_value_lex` reuse, confirmed live in source:**
`value.rs:461`, `pub fn cmp_value_lex(a: &Value, b: &Value, interner:
&crate::sym::Interner) -> Ordering` — already public, already the
comparator for `Lt`/`Lte`/`Gt`/`Gte` (`cmp_bool`), `ArgMin`/`Min`/`Max`/
`ArgMax`/`MinOver`/`MaxOver`/`Argmin`/`Argmax`/`ArgminUnique`, and the
`sorted`/`min`/`max` `ProgEval` externs (`CMP_VALUE_LEXICOGRAPHIC_
FOLLOWON_RESULTS.md` §2.1, 8 sites). `ctx.interner` is already in scope at
every `term.rs` evaluation site (confirmed: `ctx.interner.lookup`/
`.resolve` used at lines 2645, 2676, 4822-4845 and elsewhere). **A new
`Sort{seq}` Term calling `cmp_value_lex(&a, &b, ctx.interner)` — the
identical pattern its 8 existing sibling call sites already use — needs
ZERO changes to `cmp_value` itself.** `cmp_value` remains byte-unchanged,
boot-order-dependent, used only for canonicalisation (Set/Dict construction,
persistence, `shape_decode`'s frame correspondence) exactly as
`CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md` §2.2 already scoped it. This
means the "cross-cutting, can move frozen fixtures" risk in the ORIGINAL
`STRUCTURAL_CEILING.md` pricing (written before `cmp_value_lex` existed)
is **avoidable by construction** for a `Sort` Term built this way — the
population of fixtures depending on `cmp_value`'s own boot-order behaviour
is never touched.

**Step 3 — broad fixture search (not limited to the 9-file regression
scope):**

- Files directly referencing `cmp_value` by name: 6
  (`test_arc6_valuelayer_migrated.py`, `test_cmp_value_surface_migrated.py`,
  `test_arc6_tier0_migrated.py`, `test_emitter_widening_migrated.py`,
  `test_value_domain_migrated.py`, `test_rational_domain_migrated.py`) —
  all 6 already read and classified by
  `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md`'s own regression sweep as
  either unaffected or (2 of them) pinned to the specific NAMED defect and
  updated when it was fixed.
- Loose heuristic sweep (`==\s*\{...\}` / `== *set([...])` string-literal
  pattern) across `tests/*.py`: **226 files** contain SOME string-keyed
  dict/set-comparison-shaped text — a wide population, confirming the
  ORIGINAL pricing's "cross-cutting" characterisation was not overstated
  *for a fix that touches `cmp_value` itself*.
- **This population is the reason step 2 matters**: because this rung's
  design (§ above) never edits `cmp_value`, none of these 226 files' own
  string-ordering assumptions are put at risk by shipping `Sort` this way.
  The risk named in the original pricing is real, sized here as requested,
  and is **structurally avoided rather than accepted**, not because the
  population is small but because the fix this rung would build does not
  touch the code path that population depends on.
- Zero seed JSON files carry `__set__`/`__fset__` wire-tagged content
  (checked directly), so no seed-resident fixture is exposed to this
  question at all.

**Step 4 — realistic gain, this rung's exact declared scope:** **at most
+1 task (141)**, given 232/473/475 each need an additional primitive this
rung does not build. 141 is **not** in `STRUCTURAL_CEILING.md`'s own
witnessed-and-in-budget set (`75, 98, 106, 161, 257, 290` — the 6 strict
ids); it is an inventory-level reach claim only, unverified by a hand-built
witness Term the way the strict-6 were.

**Step 5 — honesty discipline applied:** a reach of 1 unwitnessed task,
under Arc4 S4's own measured 32% reach→conversion prior, is an EXPECTED
conversion of ~0.3 tasks — i.e., more likely than not that 141 does not
even convert once `Sort` is built and measured. Rung 1's own experience
this same arc (`STRUCTURAL_CEILING`'s "~+8" discounted estimate delivering
a measured +5) is the standing caution in the OTHER direction (estimates
overshoot); there is no precedent in this arc for an estimate
UNDER-shooting, and no reason to expect this one to.

**Step 6 — the GO/NO-GO call, made from what was found:**

Once the SetLit/DictItems-dependent tasks are excluded (they are not part
of this rung's authorised scope) and `cmp_value_lex` is confirmed as
available for zero-risk reuse, `Sort`'s reach collapses from the source
doc's headline "4" to **exactly 1 task, unwitnessed, expected value under
0.5**. This is now structurally identical to the reassessment prereg's own
explicit reasoning for rejecting `term:Format`: *"one task uses it, nothing
else does... named explicitly to avoid quoting it as a reach number
later"* (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`
§5.4). The engineering cost to build `Sort` properly is not small — it
requires the SAME full touch-point set every one of Rung 1's 10 primitives
needed (`term.rs` variant + evaluator + `copy_subtree` + children
collector, `term_variants.rs` regeneration, `jsonio.rs` serializer/reader,
`reflect.rs` describe/reconstruct) PLUS the evidence-gated `OP_TABLE`
wiring discipline Rung 1's own 3-pass regression walk proved is necessary
for ANY new op added to a shared bucket (to avoid a task-132-style budget
blowout on unrelated, currently-passing tasks) — real, multi-step
engineering effort for an expected gain under one task.

**VERDICT: NO-GO for Rung 3, as scoped in this task's brief.** The
`cmp_value_lex`-reuse finding is worth recording as a positive, genuinely
NEW result (it retires the "cross-cutting fixture risk" objection that
made the original pricing look expensive) — but it does not change the
GAIN side of the ledger, and the gain side, read against the real fixture
population rather than the priced task-id list alone, is too thin to
justify the build under this rung's own declared scope. Re-open this call
only if `boundary:SetLit` and/or `term:DictItems` are separately taken
first (unblocking 232/473/475's OTHER prerequisite), which would change
`Sort`'s realistic reach from 1 to up to 4 — that re-pricing is out of
scope here and is named as the natural next question, not answered.

**No Rung 3 code will be written.** Per this task's own instruction, a
well-reasoned NO-GO is the deliverable for Rung 3, and this document is
the reasoning.

---

## What this document does NOT establish

1. Rung 2's prediction (task 106 only) is stated before measurement; the
   RESULTS document carries the actual before/after set-diff, which is the
   authoritative check, not this prediction.
2. Rung 3's NO-GO is scoped to exactly what this task authorised building
   (`Sort` + string-safety alone). It is not a claim that `Sort` can never
   be worth building — only that, bundled with `SetLit`/`DictItems` out of
   scope, its own reach is too thin under this rung's own boundaries.
3. The 226-file loose heuristic sweep (step 3) is a heuristic population
   size, not a verified list of tests that would actually break under a
   `cmp_value` change — it was not necessary to verify further once step 2
   established that `cmp_value` itself is never touched by this rung's
   design, and is reported as an upper-bound sizing, not a precise count.
4. No live search-space-cost measurement (the Rung-1-style `OP_TABLE`
   budget-blowup risk) was taken for `Sort`, because no `Sort` code was
   written — this is a named, unmeasured risk factored qualitatively into
   the NO-GO cost estimate, not a live finding.
