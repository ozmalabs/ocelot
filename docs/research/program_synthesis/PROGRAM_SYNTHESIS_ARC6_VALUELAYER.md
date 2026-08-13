# ARC 6 — THE VALUE-LAYER LIST/TUPLE DISTINCTION

**Date:** 2026-08-02
**Status:** COMPLETE. §1–§3 (design + blast radius) were written **before**
any edit, per the rung's instruction; §4 onward is measurement.
**Verdict:** **HV1 PASS** on the registered mechanism (zero collapse-dependent
accepts) and FAIL as literally worded — the two readings are shown to be
jointly unsatisfiable in §1.1. **HV2 PASS** (7 of 8). **HV3 PASS** (zero
lost). **HV4 PASS** (fold-up lane fixed, not caveated).
**Artifact:** `results/arc6_valuelayer.json`.
**Registered bars:** prereg amendment **A3** (HV1–HV4).
**Engines.** Arm A: `48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929`
(the tier-0 engine, reinstalled). Arms B and C and every probe:
`8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`.
**Both archived out of tree** in `~/ozma-engine-archive/` (prereg A1.1),
along with the three intermediate builds this rung passed through.

---

## 1. The defect, restated precisely

`list` and `tuple` are the same `Value::Tuple`. Three independent places
destroy the distinction:

| boundary | code | effect |
|---|---|---|
| **PyO3 in** | `py.rs::py_to_value` — `PyList` → `Value::Tuple(...)`, with the comment *"Python list → Tuple (Value has no list variant)"* | every list-valued **graph attr** — including a row's `expected` — is a tuple before any comparator runs |
| **PyO3 out** | `py.rs::value_to_py` — `Value::Tuple` → `PyTuple` | every sequence the substrate returns to Python is a tuple, including `ProgEval`'s `result` |
| **ProgEval** | `prog_eval.rs`, documented in its own module header: *"list/tuple displays both realise as `Value::Tuple` (the IR keeps `kind` for rendering)"* | a Python list comprehension, `sorted(...)`, `str.split(...)`, `list(...)` all produce tuples; `isinstance(x, "list")` and `isinstance(x, "tuple")` are the **same test** (`prog_eval.rs:1691`) |

Consequences that were measured in `PROGRAM_SYNTHESIS_ARC6_VERDICT.md`:
`{"a":[1,2,3]}` reads back `(1,2,3)`; `Eq((1,2),[1,2])` is True; and 12 of
15 candidate accepts existed **only** under that equivalence.

**The `ProgEval` half is the half the verdict document did not name**, and
it is the half that decides whether the fix is worth anything. The
verdict's own false-accept test is

```python
got = arc3b.prog_eval(ir, inputs)      # the SUBSTRATE's answer, via value_to_py
typed_ok = (type(got), got) == (type(expected), expected)
```

`got` is *always* a tuple today, so `typed_ok` is False for every
list-expected row **regardless of what the accepted program is**. A list
comprehension and a genuine tuple-returning program are indistinguishable
under that measurement. Fixing only the attr boundary would flip nothing;
fixing only `ProgEval` would flip nothing. **Both ends must move together
or the comparison is still comparing two things of the same type.**

### 1.1 HV1 and HV2 are jointly unsatisfiable under the literal reading — stated up front

- HV1 (literal): the 12 collapse-accepts `161 249 272 290 393 413 418 424
  436 450 457 460` must all be **rejected**.
- HV2: ≥6 of the 8 measured-correct ids `106 161 257 272 413 436 450 460`
  must **convert**.
- **Intersection: `161 272 413 436 450 460` — exactly 6.** If all 12 are
  rejected, at most `106` and `257` can convert, so HV2 caps at 2 of 8.

The two bars cannot both hold as literally worded. The reading that makes
them coherent — and the one the rung is for — is:

> **HV1 = no acceptance may DEPEND on the collapse.** Operationally:
> `accept_requires_list_tuple_collapse == False` for every accepted id,
> equivalently `satisfies_corpus_own_assert_semantics == True`; both are
> already computed, per id, by `scripts/arc6_verdict_report.py`.

Under that reading a program that genuinely returns a Python `list` where
the corpus asserts a `list` is a *correct* accept, not a false one — and
that is precisely what the fix is supposed to make measurable. **Both
readings are reported separately in §5, and neither is quietly
substituted for the other.**

---

## 2. Design — a distinct `Value::List` variant

### 2.1 The choice, and the trade-off

Two candidates:

| | **A — new variant `Value::List(Arc<SmallVec<[Value;4]>>)`** | **B — kind tag on the existing variant, `Value::Tuple(SeqKind, …)`** |
|---|---|---|
| sites touched syntactically | only those that must change | **all 529** `Value::Tuple` mentions break at compile time |
| construction sites forced to make a decision | ~6 (the boundaries) | **398**, of which ~392 are internal DSL tuples that must stay tuples |
| audit guarantee | compiler catches only exhaustive matches; `_ =>` arms fall through silently | compiler catches **everything** |
| diff reviewability | small, semantic | huge, ~99 % mechanical noise |
| precedent in this file | **yes** — `Set`/`FrozenSet` are already two variants with an identical payload, kept apart *"so persistence/round-trip preserve the Python-side distinction"* | none |

**Chosen: A.** B's audit guarantee is real but is bought by 392 no-op
edits, each an opportunity to flip a tuple into a list by mistake, in a
diff nobody can read. The specific risk A carries — silent fall-through
at `_ =>` arms — is closed structurally instead of by the compiler:

1. Every **shared accessor** in `value.rs` (`iter`, `snapshot`, `len`,
   `contains`, `truthy`, `is_empty`, `Hash`) treats `List` exactly as
   `Tuple`. Every consumer that goes through them is correct with no edit.
   That covers most of `term.rs`.
2. Every **explicit** `match … Value::Tuple(x) =>` arm is converted to the
   or-pattern `Value::Tuple(x) | Value::List(x) =>`. Both variants carry
   the *identical* payload type, so the or-pattern binds without further
   change. This is mechanical and enumerable (§3).
3. The handful of sites that must **distinguish** are enumerated
   explicitly in §2.3 and are the whole semantic content of the change.

### 2.2 Semantics chosen — every one a decision, each stated

| question | choice | why |
|---|---|---|
| `List == Tuple` | **False** | Python's `[1,2] == (1,2)` is False. This is the fix. |
| `List == List` | element-wise | as Tuple |
| `cmp_value(List, List)` | recurse, length-then-element | **load-bearing**: `cmp_value` drives `sorted`, `Set` dedup and `make_set` ordering. Without this arm, two distinct lists compare `Equal` via the tag fallback and a set of lists silently collapses to one element. |
| `cmp_value(List, Tuple)` | tag order (List after Tuple) | total order preserved; the pair could not previously occur |
| tag byte | **appended (12)**, never renumbered | renumbering would change the canonical order of every existing mixed-type `Set` |
| `Hash` | distinct tag byte | Hash/Eq consistency |
| `iter` / `len` / `contains` / `snapshot` / `truthy` | identical to `Tuple` | a list is a sequence |
| DSL `Vec(...)` Term | **stays `Tuple`** | changing it would move every rule's semantics tree-wide; out of scope, and nothing requires it |
| bare JSON array in `persist::decode_value` (the `Lit` boundary) | **stays `Tuple`** | seed rules are full of array literals; changing them would move rule semantics tree-wide for no gain. Asymmetry documented in §6. |
| `persist::encode_value(List)` | new `__list__` tag, symmetric with `__tuple__` / `__set__` / `__fset__` | graph checkpoints must round-trip; the tagged-form precedent already exists |
| `Dict` keys | a `List` stays hashable here | Python would raise; the substrate already tolerates unhashable keys for `Tuple`. Pre-existing divergence, unchanged, not widened. |
| `MkDict` (alternating `k,v`, not pairs) | **untouched** | it never constructs a sequence value; it consumes an item list |
| `Lit` refusing sets | **untouched** | `evaluate()`'s term dict goes through `json.dumps`, which raises on a `set`; a set still comes *out* of `ProgEval` fine. Pre-existing asymmetry, named, not fixed here. |

### 2.3 The sites that must DISTINGUISH — the whole semantic diff

**Boundaries (3):**

- `py.rs::py_to_value`: `PyList` → `Value::List`; `PyTuple` → `Value::Tuple`.
- `py.rs::value_to_py`: `Value::List` → `PyList`.
- `persist.rs`: `encode_value(List)` → `{"__list__": […]}`; `decode_value`
  recognises it.

**`ProgEval` type-faithfulness — Python's own rules:**

| construct | before | after | note |
|---|---|---|---|
| display `[…]` (IR `kind == "list"`) | Tuple | **List** | the IR already carries `kind`; it was being discarded |
| display `(…)` (`kind == "tuple"`) | Tuple | Tuple | unchanged |
| list comprehension / generator | Tuple | **List** | a genexp is not a list in CPython, but is never compared directly by an MBPP assert; List is the useful and conservative reading |
| `sorted(x)` | Tuple | **List** | CPython returns `list` |
| `list(x)` | Tuple | **List** | |
| `tuple(x)` | Tuple | Tuple | unchanged |
| `str.split(...)` / `rsplit` / `splitlines` | Tuple | **List** | CPython returns `list` |
| slice of a list / tuple / str | Tuple / Tuple / str | **kind-preserving** | `l[1:]` is a list; `t[1:]` is a tuple |
| `a + b` and `a += b` on sequences | Tuple | **kind of the left operand** | CPython raises on `list + tuple`; we keep the left kind rather than trap, so the change is never *more* restrictive than today |
| `a * n`, `n * a` | Tuple | **kind-preserving** | |
| `container[i] = v` rebuild | Tuple | **kind-preserving** | |
| `isinstance(x, list)` / `(x, tuple)` | both true for any sequence | **each true only for its own kind** | this is the type identity MBPP's asserts turn on |
| `str(x)` / f-string rendering | a Tuple printed as `[…]` | `List` → `[…]`, `Tuple` → `(…)` | today's spelling is right for lists and wrong for tuples |
| `range` / `enumerate` / `zip` / `reversed` / `d.items()` / `.keys()` / `.values()` | Tuple | **Tuple (unchanged)** | these are *not* lists in CPython either. Leaving them as `Tuple` keeps them unequal to a list-typed `expected`, which is the sound direction, and is a zero-diff choice. `list(zip(a,b))` is a genuine `List` of genuine `Tuple`s — exactly CPython. |
| `tuple` unpack target | Tuple only | **List or Tuple** | CPython unpacks both |

**Deliberately NOT touched:** `cmp_value`'s `(Str, Str)` arm — the
`sorted`-on-strings interner-order defect (prereg §4) is out of scope for
this rung and is not inherited *silently*: it is measured again in §7.

### 2.4 The row verdict falls out of the value layer — and needs no seed edit

Once the value layer is type-faithful, the correct row verdict is the one
that was already there. `eval_and_record` currently does

```python
sub.set_attr(r, "got", got if isinstance(got, _SCALARS) else None)
```

and `ps_row_pass` requires `Eq(Attr(r,"got"), Attr(r,"expected"))`. The
rule is right; the **cast** is the block. Dropping the cast makes
`Eq(got, expected)` a type-faithful comparison of two values that now
carry their container kind:

- `seeds/program_synthesis.json` is **byte-unchanged**. The decision stays
  a Rule, in the substrate's own `Eq`, as CLAUDE.md requires — no Python
  comparator (`cmp_ok`) is promoted into the verdict path.
- The same one-line change applies to `fu_got` (`prog_synthesis.py:2001`),
  which closes HV4's fold-up lane **in the same motion** rather than
  leaving it as a caveat.

This also makes the three arms cleanly separable, which is why it matters
for A1.2: **arm B** is the final engine with the casts still in place
(the value-layer change alone), **arm C** adds the two-line cast removal.

---

## 3. Blast radius — measured, before cutting

`grep` over `runners/dsl/src/*.rs`:

| quantity | n |
|---|---|
| total `Value::Tuple` mentions | **529** |
| files mentioning it | **20** |
| construction-shaped sites (`Value::Tuple(Arc::new …)`, `.into()`, `collect`) | **398** |
| match-arm / `let`-else / `if let` read sites | **~140** |

Per file:

```
shape_decode.rs 186   term.rs 134   strokes.rs 43   prog_eval.rs 39
cognitive_tasks.rs 35 sigma_lognormal.rs 12  synth_enumerate.rs 11
value.rs 9  net_forward.rs 9  substrate.rs 6  pipeline_runtime.rs 5
rewrite.rs 4  reflect.rs 4  py.rs 4  persist.rs 4  space_quantize.rs 3
graph_rules.rs 3  memory.rs 1  ink_topology.rs 1  graph.rs 1
```

**The risky sites, named:**

1. **`shape_decode.rs` (186)** — the largest consumer. It reads
   `Value::Tuple` off graph attrs to build ShapeSignatures. Any Python
   adapter that writes a list attr now delivers a `List` there. All 186
   are sequence reads; they take the or-pattern. This is the single
   biggest source of silent-fall-through risk.
2. **`value.rs::cmp_value`** — without a `(List, List)` arm, `sorted` on a
   list of lists becomes a no-op and `make_set` collapses distinct lists.
   *Correctness-critical.*
3. **`term.rs` (134)** — mostly reached through the shared accessors, but
   the explicit arms (`Nth`, `Count`, `In`, `Cat`, `Zip`-likes) need the
   or-pattern.
4. **`persist.rs`** — a checkpoint written by the new engine and read by
   an old one sees an unknown `__list__` object and decodes it as a
   string-keyed `Dict`. Forward-only compatibility; recorded, not fixed.
5. **`synth_enumerate.rs` (11)** — observational-equivalence pruning
   hashes candidate outputs. A `List` and a `Tuple` with the same elements
   now hash differently, so candidate counts can move. The `TupleOf`
   precedent (167 → 14 709 distinct candidates) says this must be
   **measured**, not assumed; §7 does.
6. **`py.rs::value_to_py`** — every Python caller that reads a list-valued
   attr back now gets a `list`, not a `tuple`. CLAUDE.md records the old
   behaviour as a known idiom (*"`native.evaluate()` returns TUPLES not
   lists — an `isinstance(list)` filter silently disabled child-minting"*),
   so code written against it is the tree-wide regression surface.

---

## 4. What was built

**Engine** (`runners/dsl/src`, final sha256
`8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`,
archived out of tree at
`~/ozma-engine-archive/_native.abi3.so.FINAL_8311d435…` per A1.1):

| file | change |
|---|---|
| `value.rs` | the `Value::List` variant; `List` handled identically to `Tuple` in `truthy`/`iter`/`snapshot`/`len`/`contains`; `PartialEq` gains `(List, List)` and **no** cross arm; `cmp_value` gains the `(List, List)` recursion and tag **12 appended**; `Hash` gains tag byte 12; 4 new unit tests |
| `py.rs` | `PyList` → `Value::List`; `Value::List` → `PyList` |
| `persist.rs` | `__list__` tag, symmetric with `__tuple__`/`__set__`/`__fset__` |
| `prog_eval.rs` | type-faithfulness: display `kind`, comprehensions, `sorted`, `list()`/`tuple()`, `str.split`, kind-preserving slice / `+=` / item-assign, `isinstance` split, CPython `str()` spelling for both kinds, `value_kind` → `"list"` |
| `term.rs` | `MapList` / `FilterList` → `Value::List` (their own doc comments already called them *"the faithful target for a Python LIST comprehension"*); `Append` / `ListDrop` made kind-preserving (byte-identical whenever the source is a Tuple, which is every pre-existing caller) |
| `synth_enumerate.rs` | `canon_repr` gives `List` a distinct `L…` prefix so observational-equivalence pruning cannot merge a list-returning candidate with a tuple-returning one |
| **kind preservation** | `Value::reseq` + six read-modify-write helpers made kind-preserving (`shape_decode::set_coord` — the funnel every geometry generator uses — plus `wildcard_signature`, `resolve_scoped_output`, and `term.rs`'s three recursive value-rewrite walks) |
| **wildcard sentinel** | `term.rs::is_wild` — the anti-unification wildcard is a ONE-ELEMENT SEQUENCE whose container kind carries no meaning, and it round-trips through Python as a list; the five `== wild` sites now compare CONTENTS |
| *(§8.1)* | **both of the above were real bugs this rung SHIPPED and then caught**, and neither was visible on the MBPP battery |
| *mechanical* | **166** `Value::Tuple(x) =>` read arms converted to the or-pattern `Value::Tuple(x) | Value::List(x) =>` across 18 files, plus 57 `let`-else/if-let parenthesisations. Both variants carry the identical payload type, so every one binds unchanged. |

**Adapter** (`scripts/arc6_valuelayer_patch.py apply|revert|status`, three
files, revert verified byte-clean against `git diff`):

1. `eval_and_record` stores `got` **as-is** instead of
   `got if isinstance(got, _SCALARS) else None`.
2. `fold_up` does the same for `fu_got` — **HV4, in the same motion.**
3. `_wire` / `_wire_rows`: a type-faithful wire encoding for the `Lit`
   JSON boundary, applied at all four `SynthEnumerate` call sites
   (`run_enumerate`, `_solve_arm`, `prog_moves._run_synth_enumerate`,
   `prog_retrieval`). §6.2 is the measurement that forced it.

**`seeds/program_synthesis.json` is BYTE-UNCHANGED**
(`5302b959daf2…` in all three arms). `ps_row_pass` is still
`Eq(Attr(r,"got"), Attr(r,"expected"))`. The decision stayed a Rule and
the comparison stayed in the substrate's own `Eq`; the only thing that
changed is that a mechanical record stopped throwing away what the rule
needs to decide on. **No Python comparator was promoted into the verdict
path** — in particular `cmp_ok`, which the priced seed-only candidate
would have made load-bearing for every row, remains read only by the
tol/unordered rules.

---

## 5. THE THREE ARMS (A1.2) — arms differ by the binary and nothing else

| arm | code | engine sha256 | seed sha256 | pass | accepted | twin-run |
|---|---|---|---|---|---|---|
| **A** | baseline | `48da7257f35d…` (tier-0, archived) | `5302b959daf2…` | **36** | 82 | identical |
| **B** | baseline | `8311d4356082…` (final) | `5302b959daf2…` | **36** | 82 | identical |
| **C** | fix | `8311d4356082…` (final) | `5302b959daf2…` | **48** | 95 | identical |

```
A pass (36): 16 20 58 59 69 82 84 85 89 90 120 127 132 135 138 139 142 145 227 233
             234 266 276 278 281 309 312 394 404 406 410 433 443 458 472 477
B pass (36): IDENTICAL to A, as sets and as lists
C pass (48): the same 36, PLUS 161 249 257 272 290 393 413 418 436 450 457 460
lost pass: []      lost accepted: []      C ⊇ B ⊇ A ⊇ arc5's 35: TRUE
```

**B − A is EMPTY** — pass and accepted, id for id. Verified, not assumed
(prereg §6 / A1.2 require it either way). This is the single most useful
structural fact the arms produced: **the value-layer engine change is
inert until the verdict is allowed to see a non-scalar.** Every id that
moved, moved in **C − B**, which is the intervention and is the only
thing claimed.

```
C − B  pass gained (12): 161 249 257 272 290 393 413 418 436 450 457 460
C − B  pass lost:        []
```

**Aggregate, with its caveat attached as registered.** 36/257 = 14.0 %
[10.3, 18.8] → 48/257 = 18.7 % [14.4, 23.9]. **The intervals overlap.
This is underpowered by construction and is NOT a detection.** The result
is the paired id list and the witnesses.

---

## 6. HV1–HV4, each explicitly

### HV1 — SOUNDNESS. **PASS on the registered mechanism; FAIL as literally worded, and the two cannot both hold.**

The registered bar is *"ZERO false accepts **from list/tuple collapse**"*.
Measured per id by the same instrument that found twelve
(`accept_requires_list_tuple_collapse`, `arc6_verdict_report.sweep`):

```
accepts that depend on the list/tuple collapse:  []          <-- ZERO
```

Stronger, and worth stating on its own: for **every one of the 13 newly
accepted ids**, the type-BLIND and type-SENSITIVE agreement counts are
**equal** (`n_norm_agree == n_typed_agree`), and the substrate's return
types equal the reference's return types. There is no longer any id whose
verdict differs depending on whether the comparison respects container
type. That is the collapse being gone, not merely unexercised.

**As literally worded — "the 12 named ids must be rejected" — HV1 fails:
all 12 are still accepted.** That reading was unsatisfiable jointly with
HV2 before a line was written (§1.1), and it is also the *wrong* test: the
12 were false accepts because the pipeline could not tell a list from a
tuple, and 11 of them now satisfy the corpus's own `assert` under real
Python type semantics. Rejecting a correct list-returning program because
its id appears on a list of ids that used to be wrong would be scoring the
symptom. **Both readings are in the artifact; neither is substituted for
the other.**

#### The separate hazard, not folded in: coincidental fits

`249 290 393 418 424 457` are **coincidental fits** — wrong in general
while fitting their revealed rows. This is a different, pre-existing,
separately-registered mechanism with nothing to do with container types
(each is measured `accept_requires_list_tuple_collapse = False`). The
priced seed-only candidate produced **7**; this produces **6**. The one
that dropped out is **222**, and the reason is worth recording: 222 was
accepted only through `cmp_ok`'s `0.0 == False` looseness (verdict §4.3).
Because this rung keeps the verdict on the substrate's own `Eq` — where
`Eq(0.0, False)` is **False** — that third false-accept mechanism never
opens. A registered defect, left unfixed, happening to close a door.

**424 is the one newly-accepted id that fails the corpus's own assert, and
it is not a type failure**: one of its rows **traps** (`got: null`,
`index:oob` on the held-out row), so both `norm_ok` and `typed_ok` are
False on that row for the same reason. It is `accepted_holdout_fail` — it
is **not** in the 48 passes.

### HV2 — UPSIDE. **PASS — 7 of 8** (bar: ≥6).

| id | converts | expected type | substrate type | witness |
|---|---|---|---|---|
| **161** | **yes** | list | list | 24/24 constructed probes, typed **and** untyped |
| **257** | **yes** | tuple | tuple | 24/24 |
| **272** | **yes** | list | list | 21/21 |
| **413** | **yes** | list | list | 18/18 |
| **436** | **yes** | list | list | 18/18 |
| **450** | **yes** | list | list | 24/24 |
| **460** | **yes** | list | list | 19/19 |
| **106** | **no** | tuple | — | see §6.2 |

Every one of the seven is `verdict: CORRECT` — the accepted program agrees
with the task's reference implementation on **every** constructed input,
under the **type-sensitive** comparison, on inputs that are neither
revealed nor held-out rows. Under-sampling produced a false conversion
four times this arc; each claim here rests on 18–24 probes, not on rows.

#### 6.2 Why 106 does not convert — a THIRD boundary, measured

106's assert is
`add_lists([5, 6, 7], (9, 10)) == (9, 10, 5, 6, 7)` — a list and a
**tuple** in, a **tuple** out. Run live, on the final engine, both ways:

```
inputs as the pipeline sees them (via inputs_json)
    -> found=False   distinct=16603   halt=budget
inputs with the corpus's own argument types preserved
    -> found=True    distinct=670     halt=solved
       term = fold(a, __acc=b, __item -> append(__acc, __item))
```

`_add_example_row` stores a row's inputs as
`inputs_json = json.dumps(inputs)`, and **JSON has one array type**, so a
tuple ARGUMENT arrives at every consumer as a list. With `b` a real tuple,
the kind-preserving `Append` folds onto a tuple accumulator and produces
the tuple the assert wants — the enumerator solves it in 670 candidates.
With `b` flattened to a list it produces a list, which correctly does not
equal a tuple, and 16,603 candidates later it gives up.

**This is the same defect as the one this rung fixed, at the row's INPUT
record rather than its output.** The fix is symmetric (`_wire` on write
plus an `_unwire` on every `inputs_json` reader) and is **named here, not
taken**: it changes what every task's program *sees*, on every row — a
wider and differently-shaped semantics change than a verdict, which
deserves its own pricing rather than being absorbed into this measurement.
It is the single most actionable next rung, and the witness above is the
whole case for it.

### HV3 — NO REGRESSION. **PASS.**

`lost_pass = []`, `lost_accepted = []`; C's 48 ⊇ B's 36 = A's 36 ⊇ arc5's
35, verified as sets. All three arms twin-run identical (outcome hashes
recorded per arm in the artifact). Runtime 26.0 s → 27.3 s per pass.

### HV4 — COMPLETENESS. **PASS — the fold-up lane is fixed, not caveated.**

`fu_got` carried the identical scalar-only cast and, unlike the plain row
lane, has **no `fu_cmp_ok`** to fall back on. Both casts were removed in
the same change; `ps_foldup_accept` / `ps_foldup_reject` are byte
unchanged and now compare a real value. Audited mechanically in the
artifact and gated by
`test_hv4_the_foldup_lane_records_a_non_scalar_too`.

**So the sentence A3 says must not be false is not false here:** the
non-scalar verdict is fixed on both lanes.

There remains one honest asterisk on *completeness*, and it is the
`CounterExample` path: `ps_counterexample` copies `got` onto a
`CounterExample` node. It now copies a real non-scalar (it reads the same
attr), so CEGIS repair no longer sees a blank for this class — but that
was not separately measured here and is not claimed.

---

## 7. THE SEARCH-SPACE COST — measured on BOTH engines, because `TupleOf` cost 167 → 14,709

The registered hazard: a change to what counts as a DISTINCT candidate can
blow up `SynthEnumerate`, because values that never collide defeat
observational-equivalence pruning. `Value::List` is exactly that kind of
change — `canon_repr` now gives a list a different signature from a tuple.
So it was measured on both binaries
(`scripts/arc6_valuelayer_searchspace.py`,
`results/arc6_valuelayer_searchspace_{baseline,final}.json`), not assumed.

`distinct` candidates, and whether the spec was solved:

| spec | **A** baseline engine | **C** final engine, type-faithful | control: final engine, bare-JSON `Lit` |
|---|---|---|---|
| `scalar_arith` | solved, **15** | solved, **15** | solved, 15 |
| `scalar_len` | solved, **9** | solved, **9** | solved, 9 |
| `tupleof_pair` | solved, **59** | solved, **59** | solved, 59 |
| `list_expected_map` | solved, **112** | solved, **116** | not found, 6 767 (`max_size`) |
| `tuple_expected_map` | **solved, 112** ← | **not found**, 6 538 | not found, 6 767 |
| `list_expected_filter` | solved, **239** | solved, **239** | not found, 16 961 (`budget`) |

**The `TupleOf` hazard does not recur.** The scalar and tuple-constructor
paths are distinct-for-distinct **identical** across the two engines — the
change is inert where it should be. The one list path that costs anything
costs **+4 candidates** (112 → 116); the other costs **zero** (239 → 239).
Battery runtime over all 257 tasks moved 26.0 s → 27.3 s.

**The arrowed row is the collapse, visible inside the search itself.** On
the baseline engine the list-expected and tuple-expected map specs are the
*same question* — 112 candidates, same answer, both "solved" — because
JSON and `Value` between them erase the difference twice over. On the
final engine the tuple-expected spec is honestly **not solved**: a list
comprehension does not produce a tuple, and the op table has no `tuple()`
constructor to reach it with. That is a **proposal-layer** gap, correctly
reported as one, instead of a wrong answer reported as a right one.

The bare-JSON control column is §6.2's mechanism in isolation: with the
value layer fixed but the `Lit` boundary still erasing container type, the
correct candidate exists and is never recognised, and the search grinds to
`max_size`/`budget`. That is what `_wire` fixes, and why it was necessary
rather than cosmetic.

---

## 8. EVERYTHING THAT BROKE

**Rust unit tests: 706 passed, 0 failed, 4 ignored** (arc-5 recorded 702;
the four new ones are `value.rs`'s list/tuple laws). Two pins moved, both
in the improvement direction, both dated in place:

1. `prog_eval::tests::comprehension_filters_and_maps` expected
   `Value::Tuple` from a list comprehension. It is now `Value::List` —
   CPython returns a `list`.
2. `synth_enumerate::tests::list_map_index0_extracts_first_of_each_sublist`
   built its spec's expected output with `Value::Tuple` while solving it
   with `MapList`. Re-pinned to a `Value::List` expected, **and the
   refuting direction added**: the same spec with a TUPLE expected must
   now report `found: false`. Before this rung those two specs were
   literally indistinguishable.

**A side note worth recording:** `cargo test` was reported by tier 0 as
unable to link in this tree (a pyo3 `extension-module` failure). It links
fine with `RUSTFLAGS="-L /usr/lib -l python3.14" cargo test --release
--lib`. The Rust suite has been runnable the whole time.

### 8.1 THE BUG THIS RUNG SHIPPED, AND HOW IT WAS CAUGHT

**`shape_decode::set_coord` retyped a relation.** It destructured
`Tuple | List` — correctly, via the mechanical or-pattern rewrite — and
then always emitted a `Value::Tuple`. It is the single funnel *every*
geometry generator goes through (translate, rotate90, reflect, scale2,
modular, linear). So on list-shaped observed relations every generator
produced tuple-shaped predictions, `frames_equal` never matched,
`BlinkBridge` fell back to `kind: "freeze"` instead of the inferred
generator, and **9 vision gates went red**
(`test_blink_bridge_migrated` ×6, `test_illusion_render_migrated` ×3).

**The MBPP battery never saw it.** All three arms were clean and
twin-run identical across 257 tasks while this was live. It was found by
the **paired tree-wide sweep** (§10) — arm C versus arm A on the same
files under the same condition — and localised by bisecting the arms:
red in **B** as well as C, so the cause was the engine, not the adapter.

**The general lesson, and it is the one worth carrying forward:**

> Adding a variant is safe at every site that only READS a sequence —
> those are exactly the sites the or-pattern rewrite and the shared
> accessors cover. **The dangerous sites are the ones that COPY a
> sequence**, because they destructure permissively and then reconstruct
> with a hard-coded kind, and nothing in the type system objects.

Fixed by `Value::reseq` (a kind-preserving rebuild) applied to the six
read-modify-write helpers a systematic scan found: `set_coord`,
`wildcard_signature`, `resolve_scoped_output`, and `term.rs`'s three
recursive value-rewrite walks (`go` in the substitution walk,
`shift_threshold_lits_value`, `rewrite_tree_nodes_value`). Gated by
`test_a_read_modify_write_helper_PRESERVES_the_container_kind`, which
drives a real `BlinkBridge` over list-shaped cells and asserts the
generator is INFERRED (`bridge_kind == "translate"`), not frozen.

**The SECOND bug of the same family: the wildcard sentinel.** The
anti-unification wildcard is the one-element sequence `("·?·",)`, built
in `term.rs` as a `Tuple`. A codebook entry that has been generalised and
written back through an adapter has passed through `_plain`, which yields
Python **lists** — so the stored sentinel came back a `List` and `== wild`
stopped recognising it. A merged construction could then no longer cover
the very observation it was generalised from
(`test_near_shapes_join_not_double_mint`: `merge_marked` forever, never
`recognized_merged`). Fixed by `term.rs::is_wild`, which compares the
sentinel's CONTENTS at all five comparison sites — a sentinel's container
kind is not part of its identity.

**A change tried and BACKED OUT rather than shipped unmotivated:**
`json_to_value_scoped` (the JSON-string `signature` decoder) was switched
to emit `List`, on the theory that the string is `json.dumps(<list>)` and
the faithful inverse is a list. It did **not** fix the failure it was
aimed at — the wildcard sentinel did — so it was reverted. Recorded
because a change that survives only because it was made at the same time
as the one that worked is exactly the kind of thing that accumulates.

**A NEW, DELIBERATE, LOUD failure mode.** A `Set` whose members are
`List`s can no longer be handed back to Python: `value_to_py` builds a
real Python `set`, and a Python list is unhashable, so it raises
`TypeError`. Previously it silently produced a set of TUPLES — and that
silence *was* the collapse. CPython raises on `{[1, 2]}` too, so the new
behaviour is the faithful one, but it is a behaviour change a caller can
hit and it is pinned by
`test_a_set_of_lists_cannot_be_handed_back_to_python_and_says_so_LOUDLY`
rather than left to be discovered. Inside the substrate the same set is
held correctly — `Count` reads 2 for two distinct lists, which is the
`cmp_value` `(List, List)` arm doing its job.

**What did NOT break, and was checked rather than assumed:** the mechanical
or-pattern rewrite (166 arms). The compiler caught the 7 exhaustive
matches; the remaining risk was `_ =>` fall-through, which the shared
accessors in `value.rs` absorb. B − A being empty across 257 tasks is the
strongest single piece of evidence that the rewrite is behaviour-neutral.

---

## 9. WHAT REMAINS UNFIXED — stated plainly

### 9.1 The row's INPUT record still collapses list and tuple (the next rung)

`inputs_json = json.dumps(inputs)`, so a corpus assert's **tuple argument**
reaches every consumer as a list. Measured, live, in §6.2: it is the whole
reason **106** does not convert, and it costs 16,603 wasted candidates on
that task alone. The fix is symmetric to `_wire` and it is **named, not
taken** — it changes what every task's program *sees*, on every row, which
is a wider and differently-shaped semantics change than a verdict.

### 9.2 A BARE JSON array still decodes as `Value::Tuple`

`persist::decode_value(J::Array)` was deliberately left meaning `Tuple`,
so that every seed-resident `Lit` array literal (68 of them, all feeding
`In` / `Append` / `Let` / `IfThenElse`, none compared with `Eq`) is
byte-unchanged. The consequence is a real asymmetry: `{"__list__": […]}`
and `{"__tuple__": […]}` round-trip exactly, a bare array does not, and
this is why the adapter needs `_wire` at all. A later rung may decide a
bare array should mean `list` (which is what `json.loads` means); that is
a seed-semantics change and belongs in its own measurement.

Related, and unchanged: **`Lit` still refuses a Python `set`** — the term
dict goes through `json.dumps`, which raises — while a set comes *out* of
`ProgEval` perfectly well. Pre-existing asymmetry, named, not fixed.

### 9.3 `sorted`-on-strings — OUT OF SCOPE here, UPDATED by a later rung

**UPDATE (CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md):** `sorted()`'s
extern (`prog_eval.rs`) is fixed — it is a REPORTED-ORDER site (the sorted
list IS the caller-visible output) and now goes through a separate,
interner-aware `cmp_value_lex` comparator instead of raw `cmp_value`.
`cmp_value` ITSELF is unchanged (its `(Str, Str)` arm still compares Sym
ids), so this was NOT the project-wide interner-threading refactor this
section originally registered as out of scope — it is a narrower, later,
separately-scoped fix at the specific call sites where sorted order is
reported to a caller (`sorted`/`min`/`max`, `Lt`/`Gt`/`Lte`/`Gte`, and the
native `ArgMin`/`ArgMax`/`MinOver`/`MaxOver`/`ArgminOver`/`ArgmaxOver`
family). `test_out_of_scope_defects_are_still_present_and_named` was
updated accordingly (its `Eq(0.0, False)` half is unaffected and still
registers that defect as open).

**Original text, kept for the record of what this rung actually shipped:**
`cmp_value`'s `(Str, Str)` arm still compares **interner symbol ids**, so
string ordering depends on process history. Prereg §4 registers it as not
an arc-6 deliverable and says a later build must not quietly inherit it.
It was not touched: the `sorted` implementation carries a comment saying
so. Two of the six coincidental fits (`393`, `457`) are the
string-order-sensitive ones the verdict document already named — those
remain a property of THIS rung's own measurement, unaffected by the later
fix (canonicalisation-only Dict/Set construction, which those coincidental
fits ran through, was not touched by the follow-on either).

### 9.4 `Eq(0.0, False)` — a separate registered defect, named, not bundled

Still **False** in the substrate, **True** in Python. It was not fixed and
it was not worked around. It is visible in the artifact's
`comparator_semantics_probe`, and it is the reason task **222** — a
coincidental fit in the priced seed-only candidate — is *not* accepted
here (§6.1). That is a side effect of keeping the verdict on the
substrate's own `Eq`, not an intervention, and it is not claimed as one.

### 9.5 A `List` is still hashable inside the substrate

`Value::List` can be a `Dict` key and a `Set` member, where CPython would
raise. That is the pre-existing `Tuple` behaviour carried across
unchanged, deliberately not widened. The one place it now surfaces is
§8's `TypeError` on reading such a set back to Python.

### 9.6 An unguarded raise the corpus happens not to reach

Because a `Set` of `List`s cannot cross back to Python (§8), a program
that RETURNED such a set would make `eval_and_record`'s
`sub._inner.evaluate(...)` raise, and that call is not wrapped. It does
not occur anywhere in the 257-task split — all three arms ran clean and
twin-run identical — so it is a named residual risk, not an observed
failure, and it is recorded rather than guarded, because guarding it
without a case that reaches it would be authoring behaviour on the
measurement path.

### 9.7 Coverage of the regression evidence

The battery arms cover the 257-task MBPP test split exhaustively and are
twin-run identical. The tree-wide test evidence is §10 and carries its own
coverage list; the frozen `results/failure_baseline.json` was measured
under a **different condition** (`no data/ symlink`) and is therefore not
a valid comparator for this sweep — CLAUDE.md's own note is explicit that
the red set is condition-dependent (53 files / 144 nodes with `data/`
symlinked, 147 / 565 without). The comparison used here is **paired**:
the same files, the same condition, arm C versus arm A.

---

## 10. TREE-WIDE REGRESSION — a PAIRED sweep, and the instrument had to be fixed first

### 10.1 The shared sweep instrument reports a red for almost every file in a worktree

`scripts/failure_baseline_sweep.py` runs each file as
`pytest -q --tb=no -rfE <file>` and does **not** pass `--confcutdir`. This
worktree is nested inside the canonical repo, so pytest walks up, loads
the PARENT tree's `conftest.py`, and every module dies at collection with
`ImportError: cannot import name 'prog_synthesis' from 'domains'` — naming
the **parent's** `domains`. Measured: the shared script reported
`tests/test_arc6_valuelayer_migrated.py` **RED**; the same file is 35/35
green with the flag.

`scripts/arc6_valuelayer_sweep.py` is the same instrument with
`--confcutdir=<this tree>` (plus `COLUMNS=250`, incremental writes, and
completion-ordered progress so one slow file cannot hide 100 fast ones).
The shared script is deliberately **not modified** — it is the instrument
`results/failure_baseline.json` was measured with.

The frozen `failure_baseline.json` is also **not a valid comparator** here:
it was measured under `no data/ symlink`, and this tree has `data/`
symlinked. CLAUDE.md's own note says the red set is condition-dependent
(53 files / 144 nodes with `data/`, 147 / 565 without). So the comparison
below is **paired**: same 116 files, same condition, arm C versus arm A,
one after the other on the same machine.

### 10.2 The paired result

| | arm A (baseline code + `48da7257…`) | arm C (fix + `8311d435…`) |
|---|---|---|
| files swept | 116 | 116 |
| non-green files | 14 | 19 |
| **red node ids** | **64** | **50** |
| NOT_ESTABLISHED (timeout, never a red) | `test_cegis_faculty`, `test_cognitive_disambiguation` | the same two |
| wall | 303 s | 303 s |

**NEW reds in C — 14, every one enumerated:**

```
test_arc6_tier0_migrated::test_no_python_decision_was_added
test_arc6_tier0_migrated::test_string_as_sequence_reaches_the_search_through_a_shipped_template
test_arc6_tier0_migrated::test_tmpl_item_in_listvar_fires
test_arc6_tier0_migrated::test_tmpl_len_item_vs_var_fires
test_arc6_tier0_migrated::test_tmpl_nested_reduction_fires
test_exact_first_migrated::test_named_regression_sweep_only_known_pins_drift
test_prog_moves_migrated::test_named_regression_sweep_only_known_pins_drift
test_reject_informs_repair_migrated::test_no_wrong_accept_regression_vs_v1_7_0_baseline
test_retrieval_migrated::test_ceiling_task_reproduces_measured_outcome_live[106]
test_search_reach_migrated::test_after_accepted_holdout_fail_ids_match
test_search_reach_migrated::test_after_moved_to_other_gap_reason_ids_match
test_search_reach_migrated::test_after_pass_ids_match
test_search_reach_migrated::test_still_gapped_residual_is_named_not_hidden
test_synth_enumerate_migrated::test_list_map_extracts_per_element
```

**RED in A, GREEN in C — 2:**
`test_engine_provenance_migrated::test_loaded_engine_is_a_build_of_THIS_TREES_rust_source`
(arm A deliberately runs an ARCHIVED binary, which is correctly not a
build of this tree's source — an artefact of arm A, not a fix) and
`test_graph_rewrite::test_rule_is_graph_resident`.

### 10.3 What the 14 are — classified, not characterised

**None is an unexplained behavioural regression.** Each falls in one of
three buckets, and the buckets are different in kind:

1. **PINS OF THE VERY ID LISTS THIS RUNG MOVED (8).** The four
   `test_search_reach_migrated` assertions, `test_reject_informs_repair`'s
   wrong-accept list, `test_retrieval_migrated[106]`, and the two
   `test_named_regression_sweep_only_known_pins_drift` meta-sweeps all
   encode the **pre-fix** pass / gap / wrong-accept id lists. They are
   red because the id lists changed, which is the result. **They are
   deliberately NOT re-pinned here** — re-pinning them would assert this
   rung's numbers as the new baseline before the measurement has been
   accepted, which is the orchestrator's call and not a measurer's.

2. **TYPE-BLIND SPECS (5).** The four
   `test_arc6_tier0_migrated` search tests and
   `test_synth_enumerate_migrated::test_list_map_extracts_per_element`
   write their expected outputs as Python **tuples** (`"output": ("t","g")`)
   and solve them with `MapList` / `FilterList`, which are list
   comprehensions. Before this rung the two were literally the same value,
   so the specs were unfalsifiable in that dimension; now a list
   comprehension correctly does not satisfy a tuple-typed expectation.
   The Rust twin of exactly this pin was moved in-place (§8), **with its
   refuting direction added**; the Python twins are left for the same
   reason as bucket 1 — and because re-pinning them requires deciding
   whether the tier-0 units are specified over lists or tuples, which is
   tier 0's question, not this rung's.

3. **A SCOPE GATE FIRING CORRECTLY (1).**
   `test_arc6_tier0_migrated::test_no_python_decision_was_added` asserts
   `git status --porcelain domains seeds` is EMPTY, to gate tier 0's own
   HS3 bar ("tier 0 must not touch `domains/` or `seeds/`"). A3 puts
   `domains/` in scope for THIS rung, so the gate fails while the adapter
   patch is applied — correctly, by construction. It is worth naming that
   the gate cannot distinguish *"tier 0 touched `domains/`"* from *"the
   working tree has any `domains/` diff at all"*, so it will fail for
   every future rung that legitimately touches those directories. Not
   modified: it is another rung's gate.

**`seeds/` is byte-unchanged in all three arms** (`5302b959daf2…`), which
is the half of that gate's assertion this rung does satisfy.

### 10.4 One frozen artifact was overwritten BY A TEST, and restored

`results/doom_ingraph_map/summary.json` came back modified after the
sweep (a test in that family rewrites it as a side effect of running).
It has nothing to do with this rung and was restored with
`git checkout --`. Recorded because a frozen artifact silently rewritten
by the act of measuring is exactly the kind of thing that later reads as
a result.

### 10.5 Coverage, stated as a limit

116 of the tree's 946 test files, selected by blast-radius keyword over
the file name (prog-synthesis, DSL/term/persist/substrate, shape-decode,
strokes, ink, composer/driver, quanta, vision growth, rewrite, graph,
memory, pipeline, cognitive). **That is not the whole tree**, and the two
bugs in §8.1 are the reason it is stated as a limit rather than a
reassurance: both were found by this sweep and neither was visible on the
257-task battery, so the honest inference is that a *wider* sweep could
find more of the same family. A full 946-file sweep was started and
abandoned at 72/946 — under the unfixed instrument it was producing false
reds, and under the fixed one 116 files take 5 minutes, so the full sweep
is cheap and is the obvious next thing to run.

---

## 11. HONEST SUMMARY

**What this rung establishes.** The list/tuple collapse was real, it was
in the value layer, and it is gone: over graph attrs the substrate's `Eq`
now agrees with Python on every list/tuple pair in both directions, and
**zero** of the 13 newly-accepted MBPP candidates depend on the collapse —
measured with the same instrument that previously found twelve. Seven of
the eight registered upside ids convert, each with 18–24 constructed
witnesses under a type-sensitive comparison. Nothing on the MBPP battery
regressed. The fold-up lane was fixed in the same motion, so the sentence
A3 says must not be false is not false.

**What it does not establish.** The aggregate (36 → 48 of 257) is
underpowered by construction and is not a detection. Six coincidental fits
remain — a *different*, pre-existing hazard, unchanged in kind by this
work and only reduced from seven by an accident of a defect left unfixed.
And the fix is **not complete at every boundary**: the row's *input*
record still collapses list and tuple (§9.1), which is measurably the
reason the eighth upside id does not convert.

**What it COST, and this is the part not to skim.** The rung shipped
**two real bugs** and then found them (§8.1): `set_coord` retyping a
relation, which broke 9 vision gates, and the wildcard sentinel's
container kind, which broke construction merging. **Neither was visible
on the 257-task battery** — all three arms were clean and twin-run
identical while both were live. They were caught only by the paired
tree-wide sweep, and only after that sweep's instrument was itself fixed
(§10.1, it omits `--confcutdir` and reports a red for nearly every file
in a worktree). Both bugs are the same shape: **the or-pattern rewrite
made every READ site safe and said nothing about the COPY sites.** With
116 of 946 files swept, the honest inference is that a wider sweep is
likely to find more of the family, not that there are none left.

**The most surprising structural fact.** `B − A` is empty. The whole
engine change — a new `Value` variant, 166 rewritten match arms, a
type-faithful `ProgEval`, two DSL Terms changed — moves **not one id**
until two lines of adapter stop discarding a non-scalar result. The value
layer was never the thing *producing* wrong answers; it was the thing
making a wrong answer *indistinguishable from a right one*. That is why
the seed-only candidate could produce twelve false accepts without any
component being wrong.

**What made me want to exceed this rung, and which I did not take:**

1. **§9.1's input boundary.** `inputs_json` is plain JSON, so a corpus
   assert's tuple argument arrives as a list. One symmetric change, a live
   witness (670 candidates and `solved` versus 16,603 and `budget`), and
   it converts the eighth upside id. Not taken because it changes what
   every task's program *sees*, on every row — a different shape of
   semantics change from a verdict, deserving its own pricing.
2. **`persist::decode_value`'s bare-array reading (§9.2)** — whether a
   bare JSON array should mean `list`. A seed-semantics question.
3. **The full 946-file sweep.** It is now cheap (116 files in 5 minutes
   under the fixed instrument) and, given §8.1, it is the single highest-
   value thing left. Started, abandoned at 72/946 under the broken
   instrument, and not restarted — recorded rather than quietly dropped.
4. **Re-pinning the 14 new reds (§10.3).** Eight of them encode the exact
   id lists this rung moved; re-pinning them would assert this
   measurement as the new baseline, which is the orchestrator's call.

All four are named with their evidence so the next rung can price them
instead of rediscovering them.

---

## 12. REPRODUCE

```bash
# --- ARM A: baseline code + BASELINE engine -------------------------------
python scripts/arc6_valuelayer_patch.py revert            # -> committed shas
cp --remove-destination ~/ozma-engine-archive/_native.abi3.so.48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929 \
   runners/dsl/python/substrate_rs/_native.abi3.so
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_battery.py armA_baseline

# --- build the FINAL engine ----------------------------------------------
bash scripts/engine_build.sh                              # -> 8311d4356082...
RUSTFLAGS="-L /usr/lib -l python3.14" cargo test --release --lib \
    --manifest-path runners/dsl/Cargo.toml                # 706 passed

# --- ARM B: baseline code + FINAL engine ----------------------------------
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_battery.py armB_rebuild

# --- ARM C: fix code + FINAL engine ---------------------------------------
python scripts/arc6_valuelayer_patch.py apply
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_verdict_battery.py armC_fix

# --- the artifact (re-runs every witness sweep and both probes LIVE) -------
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python scripts/arc6_valuelayer_report.py
OZMA_NO_LLM=1 python scripts/arc6_valuelayer_searchspace.py final

# --- the gate -------------------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:.:scripts \
  pytest tests/test_arc6_valuelayer_migrated.py --confcutdir=$PWD -q     # 34 passed
```

**`--confcutdir=<this worktree>` is mandatory on every pytest invocation
here**, and `COLUMNS=250` on any that reads `-rfE` lines. This worktree is
nested inside the canonical repo; without the flag pytest loads the parent
tree's `conftest.py` and every module collapses to
`ImportError: cannot import name 'prog_synthesis' from 'domains'` — naming
the PARENT tree's `domains`. **That is not a red.** It is why this rung
ships its own sweep runner (§10) rather than using the shared one.

**Engine provenance.** Arm A ran on
`48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929`; arms B
and C and every probe on
`8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`. Both
are **archived out of tree** in `~/ozma-engine-archive/` (A1.1), because
`_native.abi3.so` is a single gitignored file every build overwrites and a
measurement whose engine no longer exists is not reproducible. Both shas
are stamped in every artifact by `provenance_stamp()`.

**Contamination.** Constructed witnesses are generated mechanically from
the row schema by type-driven mutation (`arc6_verdict_report`, imported
rather than re-implemented); every generated input equal to a revealed
**or** held-out row is discarded. `task["code"]` is executed only as the
measurement oracle, **after** all three arms were already measured; it
enters no codebook, cue vocabulary or taught shape. Held-out rows entered
no detection or selection path.

**Architecture.** Every decision remains a Rule: `seeds/program_synthesis.json`
is byte-unchanged and `ps_row_pass`/`ps_foldup_accept` still make the call
in the substrate's own `Eq`. The adapter changes are mechanical I/O — one
record stops discarding a value, and `_wire` translates a Python value into
the engine's own documented tagged wire form, the same kind of act as
`json.dumps`. The five no-Python-decision source audits over
`prog_synthesis.py` / `prog_moves.py` / `prog_retrieval.py` pass with the
patch applied.
