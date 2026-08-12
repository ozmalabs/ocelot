# ENGINE CORRECTNESS — `cmp_value` HAS NO `(Surface, Surface)` ARM — RESULTS

*Branch `cmp-value-surface-fix`, worktree `/home/matt/ocelot-cmp-value-surface-fix`,
based on `main` @ `a624375`. Prereg: `CMP_VALUE_SURFACE_FIX_PREREG.md`
(committed `e1b74f1`, before any code was read further or written).*

*Engine built in this worktree. Pre-fix engine `sha256 8963fb4dcc…`
(the artifact committed at `a624375`); post-fix engine `sha256 632b455f44…`
(`runners/dsl/target/release/libsubstrate_rs.so`, verified byte-identical to
what is committed here). `--release`, coherence probe green.*

---

## The one-line result

**One `match` arm, and it was a data-loss bug, not a tidiness one.** `cmp_value`
had no `(Surface, Surface)` case, so every runtime-built string compared `Equal`
to every other — `PartialEq` and `Hash` both got it right, so this was an
**Ord/Eq inconsistency**, and every container that canonicalises through
`cmp_value` silently lost members. The half of the sibling defect that this arm
also fixes for free is real: **`sorted` over computed strings was an INERT
NO-OP** and is now byte-lexicographic. `(Str, Str)` is a **different** defect —
self-consistent, not local, **registered NO-GO** with the follow-on scoped
precisely.

---

## Verdict table

| bar | verdict | headline |
|---|---|---|
| AR1 — root cause, read from the code | **MET** | missing arm → `_ => tag(a).cmp(&tag(b))` → 10 vs 10 → `Equal`; `PartialEq` (`value.rs:308`) and `Hash` (`value.rs:463-467`) both correct — §1. *All line numbers in this doc are the PRE-FIX file at `a624375`, verified by `git show`.* |
| AR2 — live confirmation BEFORE any fix | **MET, all four cases + controls** | `{'a0'}`, `frozenset({'a0'})`, `{'a0': 2}`, set-of-tuples → 1; literal controls all correct — §2 |
| AR3 — the `(Surface,Surface)` fix, live before/after | **MET, transcript inverts on every case** | 8 new Rust unit tests (7 of 8 RED with the arm removed, *verified by removing it*) + 11 end-to-end tests (7 RED on the pre-fix engine, 11 GREEN after) — §3 |
| AR4 — `(Str,Str)`: same cause or different, GO/NO-GO | **DIFFERENT DEFECT; registered NO-GO**, and the pre-registered decision rule decided it, not hindsight | not an Ord/Eq inconsistency; fix is **not local** (interner is per-`Substrate`, `cmp_value` is a free function) — §4 |
| AR5 — blast radius, before shipping | **MET; nothing found that depends on the buggy behaviour** | **0** persisted `Surface` values in any committed JSON; the three `prog_eval` dict sites carrying a workaround become *correct*; both paired sweeps byte-identical — §5 |
| AR6 — no regression, paired LISTS | **MET, after-list == before-list on both sweeps** | `cargo test --lib` 758→766 passed / **0 failed** both sides; Python 39 files, identical node-id lists — §6 |

---

## §1 AR1 — the root cause, read off the source

`runners/dsl/src/value.rs`. Three implementations of "are these two Values the
same", and **only one of them was wrong**:

| impl | `Surface` handling | line (pre-fix) | correct? |
|---|---|---|---|
| `PartialEq::eq` | `(Surface(ka,ba), Surface(kb,bb)) => ka == kb && ba == bb` | `308` | **yes** |
| `Hash::hash` | `Surface(k,b) => { 10u8.hash(); k.hash(); b.hash(); }` | `463-467` | **yes** |
| `cmp_value` | *no arm* → `_ => tag(a).cmp(&tag(b))` | `409` | **NO** |

`tag(Value::Surface(_,_)) == 10` for both operands, so the fallback returns
`Ordering::Equal` for **any** two surfaces. That is not a missing feature — it
is a violated contract: `a != b` while `cmp_value(a,b) == Equal`.

**The chain from that arm to user-visible data loss, each link cited:**

1. `Value::make_set` / `Value::make_frozenset` (`value.rs:229-241`) sort by
   `cmp_value` and then `dedup_by(|a,b| cmp_value(a,b) == Ordering::Equal)`.
   Two distinct surfaces are `Equal` ⇒ **the second is dropped.**
2. `Value::Dict` is a **cmp-sorted pair vec** — `MkDict` (`term.rs:4924`),
   `persist.rs:203`, `prog_eval.rs:1063/2142/2224/2675` all sort keys by
   `cmp_value`.
3. `prog_eval`'s dict **item-assign** (`prog_eval.rs:800-819`) replaces the
   first slot whose key `cmp_value`-compares `Equal`. With every Surface equal
   to every other, `d[computed] = v` **overwrites an unrelated key**.
4. `prog_eval`'s `sorted` (`prog_eval.rs:1535`) sorts by `cmp_value`, so over
   computed strings it is a **no-op that returns input order**.
5. Selection: `Argmin`/`Argmax` tie detection is `cmp_value(v, best) == Equal`
   (`term.rs:8055`, `9232`; `argmin_tie.rs`), so Surface-keyed selection saw an
   all-way tie.

**`Surface` vs `Str` — what they actually are** (needed for AR4, so stated
here): `Value::Str(Sym)` is an **interned** string — a `u32` handle into the
per-`Substrate` `Interner`; `Value::Surface(SurfaceKind, Arc<[u8]>)` **carries
its own payload bytes** and is what the Cat/Join/Bytes/U*LE/Render/`ToJsonString`
/`SnakeCase` family produces. A *literal* string in a seed is a `Str`; a string
**built at runtime** is a `Surface`. That is exactly why the defect was
invisible for so long: seeds are literals, and literals were fine.

---

## §2 AR2 — the live confirmation, on the pre-fix engine, before any code changed

Engine `sha256 8963fb4dccaad4f8b07550ac8c8000583a5350f9d1d07d7057850b922a35f115`
(the artifact committed at `a624375`). Two independent routes — bare Term
evaluation, and hub Program IR under `ProgEval`:

```
== TERM LEVEL ==
SetT(Cat('a','0'), Cat('a','1'), Cat('a','2'))   -> ['a0']                len 1   WRONG
SetT('a0','a1','a2')                    (control) -> ['a0','a1','a2']      len 3   ok
SetT(('rt',Cat…) x3)                              -> ["('rt', 'a0')"]      len 1   WRONG

== PROGEVAL ==
set(["".join(["a", str(i)]) for i in range(3)])   -> {'a0'}                        WRONG
set(["a0","a1","a2"])                   (control) -> {'a0','a1','a2'}              ok
frozenset([computed x3])                          -> frozenset({'a0'})             WRONG
d["".join(["a",str(i)])] = i, i in 0..3           -> {'a0': 2}                     WRONG
d["a0"]=0; d["a1"]=1; d["a2"]=2         (control) -> {'a0':0,'a1':1,'a2':2}        ok
sorted([computed strings])                        -> input order (INERT)           WRONG
```

All four cases §5.1 named reproduce, **including `{'a0': 2}` exactly**, and
every literal control is correct — so the diagnosis is specific to `Surface`,
not to sets or dicts in general.

**Two things the reproduction found that §5.1 did not say**, both worth having:

- **`sorted` over computed strings was INERT** — not merely non-lexicographic
  (which is §5.2's complaint about `Str`) but a **no-op**, because every
  comparison returned `Equal`. This is strictly worse than the `Str` defect and
  belongs to *this* one.
- **Two dict-construction routes behave differently.** `dict([(k,v), …])` and
  `MkDict` **sort but do not dedup**, so they kept all three pairs (in an
  arbitrary, comparison-free order); only the **item-assign** route
  (`d[k] = v`) lost keys. §5.1's dict measurement is the item-assign one. The
  distinction matters because the surviving-but-unordered dict is the *quieter*
  failure of the two.

---

## §3 AR3 — the fix, and the before/after

**The fix, in full** (`runners/dsl/src/value.rs`, plus `PartialOrd, Ord` added
to `SurfaceKind`'s derive):

```rust
(Value::Surface(ka, ba), Value::Surface(kb, bb)) => {
    ka.cmp(kb).then_with(|| ba.as_ref().cmp(bb.as_ref()))
}
```

Kind first, payload second. **Kind must be in the order** because a `Text` and a
`Bytes` surface with identical payloads are `!=` under `PartialEq` — ordering
them `Equal` would have reproduced the same class of bug one level down.
`[u8]`'s own `Ord` is lexicographic, so for `SurfaceKind::Text` this **is**
byte-lexicographic string order.

**The AR2 transcript, inverted** (engine `sha256 632b455f44…`):

| case | before | after |
|---|---|---|
| `SetT(Cat…)` × 3 | `['a0']` | `['a0','a1','a2']` |
| set of `('rt', computed)` tuples | 1 element | 3 elements |
| `set([computed × 3])` | `{'a0'}` | `{'a0','a1','a2'}` |
| `frozenset([computed × 3])` | `frozenset({'a0'})` | `frozenset({'a0','a1','a2'})` |
| `d[computed] = i` × 3 | `{'a0': 2}` | `{'a0':0,'a1':1,'a2':2}` |
| `d["a1"]` after computed writes | **trap `key:a1`** | `8` |
| `d.get("a1", -1)` after computed writes | **`-1`, silently** | `8` |
| `sorted([computed strings])` | input order (inert) | `['a_zzz','b','source','var_name','where']` |
| every literal control | correct | correct, unchanged |

The `.get` row is the one to look at twice: before the fix a key that **had been
written** read back as the caller's default, with **no trap and no error**.

**Gates, and the RED was verified by actually removing the arm** (not asserted):

- `runners/dsl/src/value.rs` unit tests, 8 new:
  `cmp_value_distinguishes_two_computed_surfaces`,
  `surface_set_does_not_collapse`, `surface_set_of_tuples_does_not_collapse`,
  `surface_ord_agrees_with_eq_in_both_directions` (both directions, both kinds,
  8×8 exhaustive), `surface_ord_is_antisymmetric_and_total`,
  `surface_ord_is_transitive_on_a_ladder`, `surface_kind_is_part_of_the_order`,
  `surface_text_order_is_byte_lexicographic`.
  With the arm deleted: **7 of the 8 FAIL.** The one that passes,
  `surface_ord_is_antisymmetric_and_total`, passes *vacuously* — `Equal
  .reverse()` is `Equal` — and is recorded here as a **weak** test rather than
  quietly counted as evidence.
- `tests/test_cmp_value_surface_migrated.py`, 11 end-to-end tests:
  **7 RED on the pre-fix engine, 11 GREEN on the post-fix engine** (both
  measured by swapping the pinned `.so`). The 4 that pass on *both* are
  deliberate controls — the literal control, the cross-type fallback, and the
  two behaviours this rung **did not** change (§4, §5.3), pinned so a future
  change to them has to be deliberate.

---

## §4 AR4 — `(Str, Str)`: a DIFFERENT defect, and a registered NO-GO

### 4.1 Same root cause? **No.** Different class of defect.

| | `(Surface, Surface)` | `(Str, Str)` |
|---|---|---|
| the arm | **absent** → tag fallback | **present**: `x.0.cmp(&y.0)` (`value.rs:363`) |
| Ord vs Eq | **INCONSISTENT** — `a != b` yet `Equal` | **consistent** — `Sym == Sym` under both |
| symptom | **silent data loss** in every Set/Dict | **wrong order**, no data lost |
| payload reachable from the Value? | **yes** — `Arc<[u8]>` is right there | **no** — `Sym` is a bare `u32` index |

The `Surface` bug destroys data; the `Str` bug orders it by the sequence in
which strings were first interned. They present similarly (both about strings)
and are structurally unrelated.

### 4.2 Is the `(Str,Str)` fix local? **No** — and this is what decided it

The pre-registered rule was: *GO only if the fix is local to `value.rs` (no
signature change to `cmp_value`) AND the blast-radius check finds no dependent.*

`Sym(pub u32)` carries **no content** (`sym.rs:19`). Resolving it needs the
`Interner`, and the interner is **owned per-`Substrate` on purpose** —
`sym.rs`'s own module doc: *"Interner is owned per-Substrate; tying it to the
substrate guarantees a Sym is only meaningful in the context it was minted, so
we never mix Syms across two graphs."* So a process-global side table is ruled
out by design, not by taste, and lexicographic `(Str,Str)` **requires threading
an interner into the comparison**. That means changing:

- `pub fn cmp_value(a: &Value, b: &Value) -> Ordering` — the signature itself;
- **≈74 call sites across 7 modules** (`term.rs` 27, `shape_decode.rs` 23,
  `prog_eval.rs` 13, `synth_enumerate.rs` 5, `persist.rs` 5, `py.rs` 1, plus
  `argmin_tie.rs`), most of them inside `sort_by(cmp_value)` closures;
- **50 `Value::make_set` / `Value::make_frozenset` sites** — and `make_set`
  is an **associated function on `Value` that has no interner and no place to
  get one**, so it would have to take one too, changing a public API used from
  `py.rs`, `persist.rs`, `prog_eval.rs`, `synth_enumerate.rs`, `term.rs` and
  `selector_audit.rs`.

**Not local. NO-GO, by the rule as registered.**

### 4.3 The second reason, which would still bite even if it were local

Changing `(Str,Str)` changes the **canonical storage order of every `Set` /
`FrozenSet` / `Dict` that holds strings** — which is most of them. `value.rs`'s
own tag-table comment already records this hazard for the type tags
(*"renumbering would change the canonical order of every existing mixed-type
Set"*); the string order is the same hazard with a much larger footprint.
That is a re-canonicalisation with its own before/after evidence requirement,
not a rider on a one-arm fix.

### 4.4 The follow-on, scoped precisely (NOT done here)

The finding that makes the follow-on tractable: **`cmp_value` is doing two jobs,
and only one of them needs lexicographic order.**

- **CANONICALISATION** (`make_set`, dict key sort, persistence) needs a total
  order that is *consistent* — it does not care which. Symbol IDs are fine.
  **Leave it alone**, and every persisted structure stays byte-identical.
- **REPORTED ORDER** (`sorted`, `min`, `max`, `Lt`/`Gt`/`Lte`/`Gte`) is the
  order a *caller sees*, and it must be lexicographic. **Verified: every one of
  those sites already has an interner in scope** — `prog_eval.rs:1535`'s
  `sorted` takes `interner` directly, and `term.rs:7798`'s comparison helper has
  `ctx: &mut EvalCtx`.

So the follow-on is: **add `cmp_value_lex(a, b, interner)` and route only the
order-reporting sites through it**, leaving `cmp_value` and every canonical
order untouched. That is a bounded change with a natural before/after gate. It
is *named* here, not built.

**Prior art that prices it:** `RULE_SIGNATURE_TO_RUST_RESULTS.md` §5.2 measured
the tax — the graph-resident signature program carries **its own selection-sort
comparator, inlined twice, ~40 of ~230 lines**, purely because the engine has no
lexicographic string order. That is the concrete cost this follow-on removes.

---

## §5 AR5 — blast radius, searched before shipping

### 5.1 Persisted data: **nothing to break**

A `Surface` inside a persisted `Set`/`Dict` would serialise with the
`"__surface__"` tag (`persist.rs:120-140`). Searched **every `.json` in the
tree**: **0 files contain `__surface__`.** Also **0** seed files contain
`__set__` / `__fset__` / `__dict__`. **No stored structure changes order or
membership under this fix.** (Surfaces are a runtime render type — `persist.rs`
says so in its own comment: *"they're a Rust-side runtime type for render
output, not a stored attribute shape"*.)

### 5.2 The three sites that were WORKING AROUND this defect — they get *better*

`prog_eval.rs`'s dict lookups are all written as
`cmp_value(k, key) == Equal || <rendered-string equality>`:
`subscript_set` (`:804`), `subscript_get` (`:980`), `.get` (`:1811`).

The `||` fallback exists because `Str` and `Surface` have different type tags
and so are correctly *not* `Equal` — a `Str`-keyed dict must still be findable
by a `Surface` probe. **Before the fix the first half was actively harmful**
(every Surface key matched the first Surface slot); after it, the first half is
correct and the second half still carries the cross-type case. Measured on both
engines:

| probe | before | after |
|---|---|---|
| `{"a0":7,"a1":8}["".join(["a","1"])]` — `Str` key, `Surface` probe (**the fallback**) | `8` | `8` |
| computed-key dict, literal probe | **trap `key:a1`** | `8` |
| computed-key dict, `.get("a1", -1)` | **`-1`** | `8` |

The fallback is **still load-bearing and still gated**
(`test_the_cross_type_string_fallback_still_works`).

### 5.3 Two behaviours this fix deliberately does NOT change — named, not assumed

Both are self-consistent and out of the registered scope; both are now **pinned
by a test** so a future change has to be deliberate rather than accidental:

- **`sorted` over string LITERALS is still interner-symbol-ID order** (§4).
  `test_str_literals_are_deliberately_NOT_fixed_here` asserts it is *not*
  lexicographic, and says in its docstring that it is the test to update when
  `(Str,Str)` is fixed.
- **A literal `"a0"` and a computed `"a0"` are still two distinct set members**
  (`Str` tag 4 vs `Surface` tag 10). Measured 2 before **and** after.
  `test_a_literal_and_an_identical_computed_string_stay_distinct` pins it.

### 5.4 Anything relying on the buggy behaviour? **Searched; none found**

The precedent the prereg named is real — `test_galileo_migrated.py` deliberately
relies on a *different* dedup quirk being present — so this was checked
directly, not assumed:

- **Both paired Python sweeps returned byte-identical failing-node-id lists**
  before and after (§6). A test relying on the collapse would have flipped.
- **`cargo test --lib` has zero failures on both sides** — the 758 pre-existing
  unit tests include the `Set`/`Dict`/`persist`/`shape_decode`/`prog_eval`
  coverage.
- No Python source anywhere asserts anything about `Surface` ordering
  (searched `tests/`, `domains/`, `substrate/`).
- The only in-tree code that *referred* to the defect is the workaround set in
  §5.2 plus `prog_eval.rs:1529`'s note about the `(Str,Str)` half — which this
  rung deliberately leaves standing, since that half is unfixed.

### 5.5 One incidental finding, recorded because it will mislead the next reader

**`test_arc_decompose_migrated.py::test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`
asserts `git diff HEAD -- runners/dsl/src/` is EMPTY.** It therefore goes red for
*any* uncommitted Rust edit, including a correct one mid-rung. It was red in
**both** the before and after sweeps (the working tree held the same uncommitted
`value.rs` in both), and is **GREEN once the change is committed** — verified
after `7303723`. It is not a regression and not a dependent; it is a
working-tree-cleanliness assertion that any engine rung will trip while in
flight.

---

## §6 AR6 — no regression, paired LISTS not counts

### 6.1 Rust — and a real methodology finding

`cargo test --lib` **single-threaded**:

| | passed | failed | list |
|---|---|---|---|
| before (`a624375` source) | 758 | **0** | *(empty)* |
| after | 766 | **0** | *(empty)* |

The +8 is exactly this rung's new tests.

**The finding: `cargo test --lib` run in PARALLEL is not reproducible in this
crate, and its red set is noise.** Two consecutive parallel runs on the
*unmodified* baseline gave **different** failing sets:

```
run 1 (4 failed): scale_audit::known_counts_are_exact,
                  scale_audit::term_units_attribute_to_the_innermost_variant,
                  scale_audit::totals_are_always_emitted_even_when_every_cell_is_zero,
                  shape_decode::dim_infer_tests::d_codebook_growth_is_seen_by_the_encoder
run 2 (3 failed): scale_audit::term_counters_are_inert_when_disabled,
                  shape_decode::dim_infer_tests::d_green_different_goals_are_seven_distinct,
                  shape_decode::dim_infer_tests::d_red_identical_arguments_collapse_to_one
```

Both are **process-global-counter instruments** (`scale_audit`, and
`shape_decode`'s codebook-epoch counters) racing across threads — the same
"global instrument" design `argmin_tie.rs`/`selector_audit.rs` document and
justify. Single-threaded, **all 758 pass**. Anyone quoting a `cargo test --lib`
red count for this crate without `--test-threads=1` is quoting noise, and this
rung would have "found 4 regressions" if it had.

### 6.2 Python — two paired sweeps, 39 files, engine swapped by pinned `.so`

**Sweep A — the direct consumers** (20 files: `rule_signature_program`, the
Program-IR/`ProgEval`/synthesis family, `arc6_valuelayer`, `persistence`,
`selector_winner_value`, `term_eval_counter`, the codebook/dimension-inference
suites). *346 passed, 1 skipped* both sides.

| | before (`8963fb4dcc`) | after (`632b455f44`) |
|---|---|---|
| failing node ids | 3 | **3, identical** |

```
tests/test_codebook_axis_migrated.py::test_cost_STILL_TRACKS_CONTENT_and_the_unexplained_path_is_untouched
tests/test_codebook_axis_migrated.py::test_the_short_circuit_ACTUALLY_FIRES_on_the_explained_path
tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**All 3 are in `results/failure_baseline.json`** — pre-existing, unrelated.

**Sweep B — everything downstream of a Surface-producing Term.** Selected by
grepping the seed corpus for the Terms that actually mint a `Surface`:
`Cat` (5 seeds), `Join` (4), `SnakeCase` (2), `ToJsonString` (15, including
`shape_decode_loop.json`), `Render` (4) — then running the suites those seeds
serve (19 files: `arc_decompose`/`arc_goals`/`arc_magnitude`/`arc_executor`,
`arc6_*`, `composer_*`, `embodied_development`, the four `prog_read_*`,
`dimension_inference`, `transform_decode`, `ink_decode`, `self_prose_rendering`).
*480 passed, 3 skipped* both sides, **~9m34s each**.

| | before | after |
|---|---|---|
| failing node ids | 6 | **6, identical** |

```
tests/test_arc_decompose_migrated.py::test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED   <- §5.5, green once committed
tests/test_arc_executor_migrated.py::test_ex1_the_frozen_artifacts_are_STILL_byte_identical
tests/test_arc6_tier0_migrated.py::test_hs4_op_table_is_the_unit_list_and_nothing_else
tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions
tests/test_self_prose_rendering.py::test_self_model_touches_reply_is_fluent_and_preserves_facts
```

The other **5 are all in `results/failure_baseline.json`**. Post-commit the red
set for this sweep is **5, every one pre-existing**.

**New gate, run separately** (it did not exist at baseline):
`tests/test_cmp_value_surface_migrated.py` — **11 passed** (and 7 of them RED on
the pre-fix engine, §3).

### 6.3 Measurement conditions, stated because a claim without its condition is the defect CLAUDE.md retracted

`data/` symlinked to the canonical tree; `results/` per-entry symlinks to the
canonical tree (**1179 artifacts** — without them Sweep A alone shows **94** red
node ids that are pure missing-artifact `FileNotFoundError`, which is exactly
the kind of environment-conditional number that must never be quoted bare);
`-p no:randomly`; single worker; each sweep run under
`systemd-run --scope -p MemoryMax=8G`. Both sides of each pair were measured in
**this same worktree** with only the `.so` swapped, so nothing but the engine
differs.

---

## §7 What a reviewer should look at first, and what is NOT done

**Look at first, in order:**

1. **The arm itself** — `runners/dsl/src/value.rs`, the `(Value::Surface, …)`
   case in `cmp_value`. Six lines of code, and the question worth asking is
   whether **kind-before-payload** is the right order (it is what keeps Ord
   agreeing with Eq, §3).
2. **§5.2's table** — the three `prog_eval` dict sites that were *working around*
   this defect. If the reviewer disagrees with anything here, it will be about
   whether that `||` fallback should now be simplified. **It should not** — it
   still carries the `Str`-vs-`Surface` cross-type case, which is gated.
3. **§4.4** — the follow-on. The split between *canonicalisation order* (leave
   alone) and *reported order* (must be lexicographic) is the load-bearing idea,
   and it is what makes the `(Str,Str)` fix bounded instead of a
   re-canonicalisation of every persisted set.
4. **§6.1** — `cargo test --lib` needs `--test-threads=1` in this crate. This
   will bite the next engine rung otherwise.

**Not done, named:**

1. **`(Str, Str)` is NOT fixed** (§4). Registered NO-GO on the pre-registered
   rule. `sorted`/`min`/`max`/`Lt` over string *literals* remain boot-history
   order. Pinned by a test that says so.
2. **`Str` and `Surface` remain distinct values** (§5.3) — a literal `"a0"` and
   a computed `"a0"` are two members of a set. Self-consistent under Ord, Eq and
   Hash, so out of scope here, but it is a genuine semantic wart and the next
   person to be surprised by it should find §5.3 rather than rediscover it.
3. **No full-tree sweep.** Two targeted sweeps (39 files, 826 passing tests)
   chosen by *where Surfaces are actually minted* (§6.2), not the whole bench.
   The selection method is stated so it can be disputed; the full-tree protocol
   is `results/failure_baseline.json`'s, which is a 12-shard job.
4. **The `surface_ord_is_antisymmetric_and_total` unit test is weak** — it
   passes vacuously without the fix (§3). Recorded rather than counted.
