# A derived-operator tier for `SynthEnumerate` — RESULTS

Prereg: `DERIVED_OPERATOR_TIER_PREREG.md`, same worktree/branch. Base
`main @ df00b37` ("Merge oplist-admissibility-grammar: Γ-production design
for op-list gating, GO on design"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/derived-operator-tier`, branch
`derived-operator-tier` — **not merged to `main`**, left for the
orchestrator to review and merge. **A sibling agent is concurrently building
`GroupCount`/`DictMerge` in a separate worktree
(`progsyn-groupcount-dictmerge`, uncommitted changes confirmed live in
`runners/dsl/src/{jsonio,reflect,synth_enumerate,term,term_variants}.rs` at
worktree-creation time); this task reads those five files only from
`main @ df00b37`, never from that worktree, and writes to none of them.**
`git diff --stat df00b37` is empty for every tracked source file — confirmed
at the end of this document (§9).

**Headline: GO on the design, NOT-YET-READY to build the full version
blind — and, read honestly against its own retroactive test case, this
mechanism would NOT have converted task 421.** A real, close, already-shipped
precedent for "named template + hole substitution, evaluated by the existing
interpreter" exists today (`DerivationRegistry`/`Derivation::ValueTaker`/
`try_derivation!`, `term.rs:2520-2556,3450-3479`) — but it is wired to
REPLACE an EXISTING native `TermNode`'s default implementation, keyed by a
kind name that must already be present in the global interner, and it has
**zero Python/PyO3/graph wiring anywhere in the tree** (confirmed by grep:
every non-test call site is inside `#[test]` functions in `term.rs` and
`shape.rs`). The genuinely new, one-time Rust needed is small and precisely
priced (§3: one `TermNode::Call{name,args}` variant, ~60-100 lines across
six files, all touch points matching an already-shipped single-field or
`Vec`-field variant's exact footprint). But "zero new Rust per derived op"
is **only true for a derived op whose argument pools match one of the SIX
existing hand-coded combinatorics shapes** — a derived op needing a NOVEL
pool combination (exactly `JoinListSep`'s own shape: one argument from
`list_by_size`, one from the general pool) still needs new Rust under a
narrow first slice, and closing that gap generally needs a second,
larger-but-still-one-time piece (§4) this document prices but does not build.
The mint discipline's sharpest finding (§5): `DELIMJOIN_BUDGETWALL_RESULTS.md
§2.3`'s own measured 6/6 spurious-under-relaxed-budget result makes
single-task held-out-row agreement an unsafe mint bar for something that
becomes REUSABLE, OFFERED, EXECUTABLE code — a cross-task recurrence floor
(support ≥ 2, independently verified, mirroring `META_SHAPE_FIRST_CLASS_
RESULTS.md §4.1`'s own support=2 floor) is the correct bar, and the
retroactive walkthrough (§7) shows this bar would have correctly REFUSED to
mint `JoinListSep` (DELIMJOIN's own investigation found it has no second
candidate task in the fixture) — a good discipline result, but it means the
mechanism does not unlock task 421 even in the best case.

---

## 0. A correction to a cited figure, checked directly

`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §1.3` states `OP_TABLE` "has 31
entries today." Recounted directly against `main @ df00b37`'s own
`synth_enumerate.rs:289-372` (both by manual enumeration of the read source
and by `awk '/^const OP_TABLE/,/^\];/' … | grep -c '^\s*("'`): **50
entries.** This document's own designs and sizing below use 50, the
directly-recounted figure, and flags the discrepancy here rather than
silently propagating the earlier document's number — per this task's own
instruction to verify every citation by reading the code, not by trusting an
earlier document's arithmetic.

---

## 1. The real architecture, read in full

### 1.1 `SynthEnumerate`'s search space is a Term-tree AST, not a graph

`synth_enumerate.rs:1-217` (module doc, read in full) confirms
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §1.4`'s own
prior finding, unchanged: candidates are `TermIdx` nodes in a scratch
`TermArena`, evaluated by the SAME `evaluate()` (`term.rs`) every other Term
in this codebase runs through, with only example-row bindings in scope.
Search is bottom-up, MDL/Occam-ordered by increasing `size` (`size = 1 + sum
of child sizes`), with observational-equivalence pruning (one term per
distinct output-signature survives as a future building block) and a
saturation halt. Budgets are counts (`max_size`, default 9;
`max_candidates`, default 200,000), never wall-clock — `synth_enumerate.rs:
227-229`.

### 1.2 Op names dispatch through SIX hand-coded combinatorics shapes, each with its own Rust builder

`OpKind` (`synth_enumerate.rs:263-287`): `Unary`, `Binary`, `Ternary`,
`ListUnary`, `ListFilter`, `ListMap`, `ListBinary`, `IndexedMap` — eight
tags, but `ListFilter`/`ListMap`/`IndexedMap` share one combinatorics SHAPE
(source-pool × template-pool cross-product) and `ListBinary` is its own
shape (both args from `list_by_size`), so **six genuinely distinct
combinatorics loops** live in the main growth loop
(`synth_enumerate.rs:2592-2653` for Unary/Binary/Ternary,
`2659-2722`+ for the list-shaped kinds, read in full):

| shape | pool(s) drawn from | example ops |
|---|---|---|
| Unary | general `by_size[size-1]` | `Abs`, `Str`, `Sort` |
| Binary | general `by_size` × general `by_size` (partitioned) | `Plus`, `Eq`, `TupleOf` |
| Ternary | general `by_size` × 3 | `IfThenElse`, `Replace`, `Slice` |
| ListUnary | `list_by_size[size-1-extra]` only | `Len`, `JoinList`, `ProdList` |
| ListMap/ListFilter/IndexedMap | `list_by_size` × a PRE-BUILT template pool | `MapList`, `SortBy`, `FilterList` |
| ListBinary | `list_by_size` × `list_by_size` | `ConcatList`, `Intersect`, `Union` |

Each shape's actual Term-tree is built by a small, hand-written Rust
function matching on the op NAME string: `build_list_unary`
(`synth_enumerate.rs:541-594`), `build_list_binary` (602-618), `build_list_ho`
(636-653, shared by `FilterList`/`MapList`/`SetMap`/`SortBy`), and
`build_indexed_map` (661-663). MDL cost accounting for the hidden fixed
nodes each shape injects is a SEPARATE hand-authored lookup table
(`list_unary_extra_cost`, 673-689; `list_binary_extra_cost`, 623-628) — e.g.
`JoinList` is documented as injecting exactly 4 extra fixed nodes beyond its
`source` child.

**This is the closest thing to a "pool taxonomy" this engine has, and it is
narrower than it first looks**: reading which `OpKind` each `OP_TABLE` entry
uses (§0's recount) shows only TWO independent value pools exist —
`by_size` (the general/scalar pool) and `list_by_size` (the
collection-shaped pool, shared by List/Tuple/Set/FrozenSet alike — `SetMap`
uses the SAME `OpKind::ListMap` path as `MapList`, and `Intersect`/`Union`
the SAME `OpKind::ListBinary` path as `ConcatList`) — plus three SPECIAL
per-element template pools (`filter_templates_by_size`/
`map_templates_by_size`/`indexed_map_templates_by_size`,
`synth_enumerate.rs:2197-2203`), each a `Vec<Vec<TermIdx>>` of small
hand-authored expression fragments built ONCE per `SynthEnumerate` call over
a locally-fabricated bound item/index variable
(`item_sym`/`acc_sym`/`inner_sym`/`index_sym`, minted via `local_sym`,
`synth_enumerate.rs:1739-1754`) and reused as SHARED subtrees across every
source they compose with — this is important for §4 below.

### 1.3 The `local_sym` and `exclude`-parser precedents

`local_sym` (`synth_enumerate.rs:1004-1020`): mints a Sym for a variable
name, checking the real interner FIRST, falling back to a locally-fabricated
NEGATIVE, wrapping-counter ID scoped to one `SynthEnumerate` call and NEVER
passed to `Interner::resolve` — the output serializer uses this module's own
local name table instead. This is the mechanism the four bound-variable
names (`__item`/`__acc`/`__inner`/`__index`) already use, and it is the
correct reuse target for any derived-op parameter name (§3), because it
sidesteps a real, load-bearing gotcha found in §2.2 below: the existing
`DerivationRegistry` dispatch path requires its argument names to ALREADY be
present in the real interner (`ctx.interner.lookup`, not `.intern`) — a
requirement `local_sym` was built precisely to avoid.

`exclude` (`synth_enumerate.rs:713-750`, read in full): a caller-supplied
list of Term-JSON STRINGS, parsed by a MINIMAL, LOCAL reader
(`parse_excluded_term`) scoped to this module's own Var/Lit/`OP_TABLE`
grammar, with its own doc comment stating explicitly why it does NOT reuse
`jsonio::term_from_json` — that function needs `&mut Interner` to intern
identifiers on the way in, and this engine only ever holds `&Interner` at
eval time. This is the exact, already-precedented shape for how a
NEW-format, cross-call, JSON-authored input reaches this module without
requiring a mutable interner — the right template for how a derived-op
REGISTRY's Term-JSON would reach the enumerator (§3.3).

`domains/prog_synthesis.py::run_enumerate` (`1172-1230`, read in full) is
the transcription precedent on the Python side: `spec["exclude"] =
{"type":"Lit","value": exclude_terms}` where `exclude_terms` is a
`List[str]` of Term-JSON strings sourced from graph attrs/neighbours
(`ps_enum_excluded`, `ps_enum_excluded_term`) — i.e. graph data flows into a
NEW `SynthEnumerate` argument as a `Lit`-wrapped list of strings, exactly the
shape a `derived_ops` argument would need.

---

## 2. Does anything ALREADY do "named template + hole substitution"?

Two candidates found, both real, neither a direct fit — read in full before
concluding either way, per this task's own instruction not to assume from
memory.

### 2.1 `Substitute`/`AntiUnifyWitness` — a VALUE-level template, not a Term-tree one

`term.rs:971-991` (read in full): `AntiUnifyWitness{values,wild}` computes
an anti-unified template PLUS the per-instance witness substitutions (a Dict
of position-path → value); `Substitute{template,sigma,wild}` walks a
template VALUE, replacing each WILD marker at a position-path with the value
`sigma` binds there. **This operates on `Value` trees (Tuples/Dicts/atoms —
the shape rule bodies and analogical-transfer structures are represented
as), not on `TermIdx` arena children.** It is the mechanism behind the
rules-as-shape arc's own analogical transfer (`RULES_AS_SHAPE_DESIGN_SPIKE.
md`), and it is a genuine, generalized "fill a template's holes" primitive
— but a derived synthesis op needs its ARGUMENTS to remain live, evaluatable
Term-tree children in the SAME arena as the rest of the candidate being
built (so `source`/`sep` in a `JoinListSep`-shaped op compose freely with
whatever the search built them from), not Values pre-computed and spliced
into a separate Value tree that would then need to be re-parsed back into a
Term (an extra round-trip `Substitute` was never designed to avoid). **Ruled
out as the direct vehicle — cited as the closest VALUE-level cousin, not
reused.**

### 2.2 `DerivationRegistry`/`Derivation::ValueTaker`/`try_derivation!` — the real, close precedent, with three honest gaps

`term.rs:2520-2556` (read in full): `DerivationRegistry = FxHashMap<Sym,
Derivation>`, mapping a *derivable variant kind name* (e.g. `"Bearing"`,
`"Sum"`, `"Lte"`) to a `Derivation`. Two shapes:

- **`ValueTaker(TermIdx)`** — the variant's own arguments are evaluated to
  Values FIRST, bound into `env` under CONVENTIONAL names, then ONE
  registered `TermIdx` (a plain Term-tree, itself composed of ordinary
  kernel Terms, possibly referencing the bound names via `Var`
  anywhere inside it — including inside a `Fold`/`MapList` body, since
  `Fold`'s own `source` field happily accepts a bare `Var` node that
  resolves via `env` at evaluate time) is evaluated and returned.
- **`BodyTaker`** — one or more of the variant's own FIELDS is itself a
  Term (e.g. `Sum`'s `value`), so today the expansion is hand-coded per
  variant in Rust (`expand_count`, `expand_sum`, `term.rs:3418-3448`), with
  its own doc comment (`term.rs:3411-3416`) stating explicitly: *"Today
  these live in Rust. **The next iteration moves them to graph-resident
  template Terms with splice-Var sentinels** (`Var("$source")`,
  `Var("$value")`, etc.), so `wonder_why Sum` returns a Term-tree the agent
  can inspect and modify."* — this is the SAME move this document is asked
  to design, named in the codebase's own words, for a DIFFERENT variant
  family (rule-self-modification derivations), **not yet built anywhere**.

`try_derivation!` (`term.rs:3462-3479`, read in full) is the dispatch: at
each derivable variant's own native match arm (e.g. `TermNode::Gt{a,b} =>
{ try_derivation!(ctx, arena, env, "Gt", [("a",*a),("b",*b)]); <native
impl> }`), it looks up `"Gt"` via `lookup_value_taker_def`
(`term.rs:2679-2703`), and on a hit evaluates each named arg, pushes it into
`env` under its conventional name, evaluates the registered `TermIdx`, pops,
returns — on a miss it falls through to the native implementation.

**This is genuinely the right SHAPE — bind named args as Values, evaluate
one registered template, done — and it is real, tested Rust, not a
proposal.** But three gaps keep it from being directly reusable as-is for a
derived synthesis op, each checked directly rather than assumed:

1. **It is keyed by an EXISTING native `TermNode` kind, and REPLACES that
   kind's default implementation** — there is no generic "any string name,
   no native variant required" dispatch site; `try_derivation!` is manually
   inserted at N specific existing match arms. A brand-new op name like
   `"JoinListSep"` has no native `TermNode` variant to host the macro call.
2. **`lookup_value_taker_def` requires the kind name to already be an
   INTERNED Sym** (`ctx.interner.lookup(kind_name)?`, `term.rs:2681`,
   `.lookup` not `.intern` — confirmed by reading the function body
   directly) — the SAME constraint `local_sym`'s own doc comment
   (§1.3) exists specifically to avoid. A derived-op parameter name minted
   fresh for one `SynthEnumerate` call is not guaranteed to already be
   interned.
3. **Zero Python/PyO3/graph wiring exists anywhere in the tree.** Grepped
   every `.rs` file for `with_derivations`/`DerivationRegistry` outside
   `term.rs` itself: the only other call sites are three lines in
   `shape.rs:900,956,957`, and all three are inside a SINGLE `#[test] fn
   derivation_dispatch_shape_pruned_falls_back_to_native()`
   (`shape.rs:877-878`) — confirmed by reading the surrounding function
   signature directly. `py.rs` was grepped in full for `DerivationRegistry`/
   `with_derivations`/`Derivation::`: **zero matches.** No seed loader, no
   `add_rule` effect, no PyO3 method populates a `DerivationRegistry` from
   graph data today. This is a genuinely different — and larger — gap than
   `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §4` found for the Γ
   admissibility probes (which ARE already PyO3-exposed and already call
   `check_edge`): the SHAPE of `ValueTaker` dispatch is proven and tested;
   the WIRING that would make it reachable from a live search is absent.

**Conclusion, stated precisely, mirroring `RULES_AS_SHAPE_DESIGN_SPIKE.md`'s
own framing exactly one level over: the missing piece here is also never the
substitution algebra — `ValueTaker`'s bind-then-evaluate shape already IS
the right algebra, proven in `term.rs` today. The missing piece is an
addressable object for a BRAND-NEW op name (no existing native variant) to
dispatch through, reachable without requiring the real interner.** That
object is a new generic `TermNode::Call{name,args}` variant (§3), not a
reuse of `DerivationRegistry`'s existing type (which is architecturally
scoped to a different job — overriding an EXISTING kernel/derivable
variant's default body for agent self-inspection/rewrite, not proposing a
brand-new named composite to a search) — though its DISPATCH LOGIC (bind
named args as Values, evaluate one template, pop) is copied nearly verbatim
from `try_derivation!`.

---

## 3. The `Call`-shaped dispatch: precise design and one-time cost

### 3.1 What a registered derived-operator entry encodes

Mirroring the `SynthOp`/`SynthSpecShape` node-attr idiom
`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §3.2` already designed (attrs on a
node, not a bespoke struct), a `DerivedOp` entry needs:

- `name` — the op string (`"JoinListSep"`).
- `params: [{name, pool}]`, ordered — `pool ∈ {"general","list"}` given
  §1.2's closed two-pool finding (the three template pools are NOT argument
  sources for a top-level op; they only ever back `ListMap`/`ListFilter`/
  `IndexedMap`'s own SECOND slot, and a derived op can reuse those existing
  op kinds' template machinery unchanged if it needs one — no new template
  pool type is implied by this design).
- `template` — Term-JSON (`jsonio::term_from_json`'s wire shape, so it is
  authorable/inspectable exactly like any other stored program), with each
  parameter referenced as `Var(<param name>)` — a local, `local_sym`-style
  fabricated binding, NOT required to be pre-interned (§3.2).
- `extra_cost: usize` — the hand-measured MDL floor beyond the sum of
  argument sizes, the DATA-driven generalization of
  `list_unary_extra_cost`/`list_binary_extra_cost`'s existing hand-authored
  Rust tables (§1.2).

### 3.2 The `Call` `TermNode` variant and its dispatch

```rust
// New variant:
Call { name: Sym, args: Vec<TermIdx> },
```

Evaluator arm (`term.rs`, new match arm — mirrors `try_derivation!`'s
logic, generalized to a runtime name and `local_sym`-safe binding instead of
`ctx.interner.lookup`):

```rust
TermNode::Call { name, args } => {
    let Some(reg) = ctx.derived_ops else { return Value::None };
    let Some(def) = reg.get(name) else { return Value::None };
    for (i, a) in args.iter().enumerate() {
        let v = evaluate(arena, *a, env, ctx);
        env.push((def.params[i], v));   // def.params[i] is a local_sym-fabricated Sym, resolved once at registry-build time — never ctx.interner.lookup
    }
    let r = evaluate(arena, def.body, env, ctx);
    for _ in 0..args.len() { env.pop(); }
    r
}
```

This is the ONE generic mechanism — built once, every derived op after that
is data, **for the population of derived ops whose argument pools already
match an existing combinatorics shape** (the honest fork in §4).

### 3.3 Where the registry lives and how it reaches Rust

Two candidate homes, priced against the real precedents in §1.3, not
invented:

- **(a) A new `EvalCtx` field**, `pub derived_ops: Option<&'a
  DerivedOpRegistry>`, mirroring `derivations` exactly (`term.rs:2586`) —
  architecturally clean, but per §2.2's own finding, this is the SAME shape
  that has never been wired from Python in this codebase; adopting it here
  would inherit that same unproven-wiring risk rather than avoid it.
- **(b) A new `SynthEnumerate` argument, `derived_ops`**, evaluating to a
  `Lit`-wrapped list of Term-JSON strings — **the precise mirror of
  `exclude`'s own, ALREADY-WORKING precedent** (§1.3): parsed by a small
  extension of `parse_excluded_term`'s own local grammar (which already
  needs to grow to recognize `Call` nodes referencing param names, since a
  registered template's own JSON will contain them), built into
  `search.scratch` ONCE per call exactly like the template pools already
  are, and reachable from Python via the SAME `_plain(...)`/neighbour-walk
  idiom `run_enumerate` already uses for `ps_enum_excluded_term` (§1.3).

**(b) is the honestly cheaper, better-grounded choice**: it reuses a
mechanism ALREADY PROVEN to cross the Rust/Python boundary for this exact
module (`exclude`), rather than adopting a mechanism (`EvalCtx.derivations`)
that has NEVER crossed that boundary anywhere in the tree. This is the
inverse-direction mirror of `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §7`'s
own forked decision (evidence flags need to reach FROM Rust TO Python,
unprecedented there): here, registry DATA needs to reach FROM Python/graph
TO Rust, and a precedent for that exact direction already exists and already
works. This document's plumbing problem is therefore strictly cheaper than
OPLIST's own.

### 3.4 Full touch-point accounting, priced against a real shipped variant

Priced directly against `Reverse{seq: TermIdx}` (a single-`TermIdx`-child
variant) and `Plus{items: Vec<TermIdx>}` (`Call`'s own exact
`Vec<TermIdx>`-child shape), both read in full at every site:

| touch point | `Reverse` precedent | `Plus` precedent (the `Vec<TermIdx>` shape `Call` needs) | `Call`'s own cost |
|---|---|---|---|
| enum variant | 1 line | 1 line | 1 line + doc comment |
| `evaluate()` arm | `term.rs` native impl | `term.rs:7411` (`numeric_variadic`) | ~15 lines (§3.2, new logic, not a native op) |
| `copy_subtree` | 2 lines | `term.rs:2925-2926`, `items.iter().map(...).collect()` | 2-3 lines, direct copy of the `Plus` idiom |
| `children()` collector | 1 line (`term.rs:10131` area) | same idiom, `Vec` flattened | 1-2 lines |
| `term_variants.rs` regen | mechanical | mechanical | `tools/gen_term_variants.py` (read in full, `tools/gen_term_variants.py:1-132`) — purely parses the enum body and re-emits a name/index table; confirmed real, confirmed mechanical, zero hand-editing |
| `jsonio.rs` | 3 arms (`jsonio.rs:211,620,1430`) | 3 arms, `Vec` variant (`jsonio.rs:241,737,1656`) | 3 small arms, ~10-15 lines total |
| `reflect.rs` | 2 arms (`reflect.rs:389,1248`) | 2 arms, `Children` collector variant (`reflect.rs:503,1360`) | 2 arms, ~6-10 lines total |

**Total: roughly 60-100 lines of new Rust, across six files, every single
touch point matching an ALREADY-SHIPPED variant's exact footprint — a
genuinely bounded, ONE-TIME cost.** This is the SAME class of change every
prior primitive-adding rung in this arc has priced (Rung 1's ten Tier-1
Term ports, the Sort/SetLit rung, `DELIMJOIN_BUDGETWALL_RESULTS.md`'s own
`JoinListSep` build) — not smaller in kind, but bounded to ONE variant
regardless of how many derived ops are later registered as data, which is
the entire point.

---

## 4. The honest fork: does this actually reach "zero new Rust per derived op"?

**No, not unconditionally — and this is the sharpest honesty test the task
brief asks for.** §1.2 found six distinct, hand-coded combinatorics shapes
(Unary / Binary / Ternary / ListUnary / the template-pool family /
ListBinary), each a different pool-and-arity combination. The `Call`
mechanism (§3) makes evaluation data-driven; it does NOT by itself make the
SEARCH LOOP's combinatorics data-driven — the growth loop
(`synth_enumerate.rs:2592-2653`+) still needs to know, for a size `s`, WHICH
pools to draw a new op's arguments from and in what partition.

**Two honestly different builds, priced separately:**

- **(A) Narrow: reuse the six existing loops unchanged, add ONE fallback
  arm to each of the five name-dispatch functions** (`build_op`'s implicit
  Unary/Binary/Ternary dispatch, `build_list_unary`, `build_list_ho`,
  `build_indexed_map`, `build_list_binary`) — on an unrecognized name,
  check the registry (§3.3) and emit `Call{name,args}` instead of failing.
  **A derived op whose arity+pool-shape matches ONE of the six existing
  shapes is zero further Rust from this point on** — register it as data,
  done. **A derived op needing a NOVEL pool combination is NOT covered** —
  it still needs a brand-new combinatorics loop, i.e. new Rust, exactly as
  today. This is a real, meaningful, but partial win.
- **(B) Full: a genuinely generic N-ary, pool-typed combinator** that reads
  each parameter's declared pool (`general` | `list`) and arity from the
  registry and performs the size-partition + cross-product generically for
  ANY combination — closing (A)'s gap entirely. This is bigger than (A) but
  **still bounded and still one-time**, because §1.2 already established
  the pool taxonomy is CLOSED at two independent value pools (general +
  list — Set/Dict already piggyback on `list_by_size` today) plus three
  template-pool types that are themselves unchanged existing machinery a
  derived op can still opt into via `ListMap`/`ListFilter`/`IndexedMap`
  directly rather than needing a fourth pool kind. A genuinely NEW pool
  (e.g. a future "dict-keyed" pool distinct from `list_by_size`) would
  still need Rust — this is `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §1.3`'s
  own "`OP_TABLE` itself is a closed, hand-authored PRIMITIVE population"
  finding, one level down: **the set of POOLS is the closed primitive
  population here; the set of derived-op TEMPLATES drawing from them is
  the growable one.**

**Honest verdict on the headline claim: "zero new Rust per derived op" is
true only for build (B), and only for derived ops whose arguments draw
exclusively from the CLOSED two-pool taxonomy — which is a real, useful,
but narrower claim than "any composition of existing Terms is now free."**
Build (A) alone does not make this claim true in general; it makes it true
for a real but bounded subset, and is the correct, cheaper first slice for
exactly that reason (§8).

---

## 5. The mint discipline, and the correctness risk investigated directly

### 5.1 Why this mint is NOT the sd loop's ordinary case

`sd_mint_quantum` (`seeds/shape_decode_loop.json`) mints from a residual
observed PASSIVELY inside one `run_rules()` tick, guarded by a cheap
`Not(Exists(...))` novelty check. **A derived-op candidate cannot recur
passively**: until it is registered, it is not in ANY `op_list`, so nothing
will spontaneously re-propose it for a second task the way a recurring
shape residual would surface again on its own. Recurrence evidence here has
to come from a DELIBERATE offline sweep — exactly
`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6`'s own design (force a
candidate into a failing task's `ops`, check `found:true` AND held-out-row
agreement), run over the same `gapped: enumerate_failed` population that
document already names (99 tasks, per `PROGRAM_SYNTHESIS_CEILING_
REASSESSMENT_3_RESULTS.md §2`), not observed for free inside a tick.

### 5.2 Why held-out-row agreement on the ORIGINATING task is not enough

`PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md §2.3` (read in full) is
the decisive, already-measured evidence: at every one of 6 checked tasks,
the first term the search finds under ANY budget large enough to reach
anything is a spurious two-revealed-row memorization (`Eq`-to-a-literal
`IfThenElse`, or an equivalent numeric-literal trick) — **and every one
fails its OWN held-out row.** This proves `found:true` alone is unsafe (it
already was known to be, hence the held-out check existing at all) — but it
also sharpens WHY held-out agreement on ONE task is a WEAKER bar for a
MINTED, REUSABLE primitive than it is for a one-off verification: held-out
agreement on task A only tests whether the candidate generalizes WITHIN
task A's own row distribution. It says nothing about whether the underlying
COMPOSITION is a genuinely reusable primitive or an accident of task A's
specific spec shape (few rows, a coincidentally-separable structure, a
degenerate case). A `CapabilityAxis`/`MetaShape` mint that turns out to be
wrong is comparatively inert — it sits as unused data until re-decoded. **A
minted derived op is not inert: once admitted (§6), it is OFFERED to every
future spec matching its admissibility gate, competes in the size-ordered
race, and consumes budget on every call it's offered to even when it loses**
— the exact mechanism `RUNG1_RESULTS.md`'s own regression investigation
already measured (`even cheap unconditional additions regress a
budget-fragile spec`). A bad mint here has an ONGOING blast radius a bad
shape-quantum mint does not.

### 5.3 The bar this design adopts

Mint only when **both**:

1. **Held-out-row agreement on the originating task** (the existing,
   already-used bar, `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md
   §3.1`'s own methodology) — necessary, not sufficient (§5.2).
2. **Cross-task recurrence, support ≥ 2** — the SAME literal template (not
   re-derived, not re-authored per task) also produces a held-out-row-
   verified `found:true` on at least ONE INDEPENDENT second task, found via
   the deliberate offline sweep (§5.1) — mirroring `META_SHAPE_FIRST_CLASS_
   RESULTS.md §4.1`'s own support=2 floor, cited by
   `seeds/problem_shape_growth.json`'s own `decompose_shape` comment as "the
   smallest cardinality at which recurs is defined," applied here at the
   TASK grain rather than the observation grain.

Guarded by the `Not(Exists(...))` dedup idiom
(`seeds/gap_awareness.json`) against re-minting an already-registered
template.

**Named, not resolved: even support=2 is a floor, not a guarantee** — two
tasks could share a coincidental structural similarity without the
composition being a genuinely well-formed general primitive. This document
states this honestly as an open residual risk rather than claiming the bar
is sufficient; it is the SAME kind of floor `decompose_shape`'s own
precedent already accepts elsewhere in this codebase, not a stronger one
invented for this case.

### 5.4 Where the sweep runs

Not inside `run_rules()` — an offline script, same family as
`scripts/ceiling3_diag_sweep.py`, run periodically or on-demand, exactly
`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6.4`'s own placement decision for
its own (related but distinct) op-admissibility mint sweep.

---

## 6. Composition with the just-landed Γ-admissibility design

**Two orthogonal growth axes, genuinely additive, no separate admissibility
path needed:**

- **This document's axis**: grow the VOCABULARY of named op templates
  (`Call`-dispatched, registry-resident).
- **`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md`'s axis**: grow the
  ADMISSIBILITY of an op (any op — primitive or derived) for new spec
  shapes, via Γ Productions over `SynthSpecShape`/`SynthOp` nodes.

A minted derived op becomes a NEW `SynthOp{name:"JoinListSep",
kind:"derived"}` node candidate under OPLIST's OWN design
(`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §3.2`) — the `kind` attr is the
only addition this document's composition needs, distinguishing "requires
`OP_TABLE` + Rust to exist" from "requires only a registry entry to exist."
`is_edge_admissible`/`admissible_moves` (`OPLIST_ADMISSIBILITY_GRAMMAR_
RESULTS.md §4`, already PyO3-exposed, already calling `check_edge`) do not
care which kind of `SynthOp` they are checking — the distinction lives
entirely downstream, in `run_enumerate`'s op-list construction and in the
enumerator's own name-dispatch (§4's fallback arms), never in the Γ layer.
**No separate admissibility path is needed; this is a genuinely additive
extension of the just-landed design, not a competing one.**

One efficiency worth naming, not yet built: the two documents' own offline
mint sweeps (this one's §5.4, OPLIST's own §6.4) could share ONE harness —
try a candidate (an existing op OR a derived-op template) against a failing
task, check held-out agreement, and on a cross-task hit, mint BOTH the
op/template (this document) and its admissibility Production (OPLIST)
together. Named as a real, cheap synergy; not priced or built here.

---

## 7. Retroactive walkthrough: would this have minted `JoinListSep`?

Read `PROGRAM_SYNTHESIS_DELIMJOIN_BUDGETWALL_RESULTS.md §1` in full again
against this design, concretely, in three parts.

### 7.1 Would the mechanism have EXPRESSED `JoinListSep`?

Yes, cleanly, but only under build (B) (§4), not build (A). `JoinListSep`'s
own two arguments — `source` (list-shaped, drawn from `list_by_size`) and
`sep` (a general-pool literal/expression) — are exactly the
`(list, general)` pool pair build (A)'s narrow fallback does NOT cover (no
existing `OpKind` shape draws one arg from each pool independently; the
closest, `ListMap`/`ListFilter`, pairs `list_by_size` against a TEMPLATE
pool, not the general `by_size` pool). Under build (B)'s generic combinator,
the registry entry is a direct, lossless transcription of the ALREADY-BUILT
Rust (`synth_enumerate.rs`'s own reverted `build_list_join_sep`, cited in
`DELIMJOIN_BUDGETWALL_RESULTS.md §1.1`):

```json
{"name": "JoinListSep",
 "params": [{"name": "source", "pool": "list"}, {"name": "sep", "pool": "general"}],
 "extra_cost": 7,
 "template": {"type":"Slice",
              "seq": {"type":"Fold","source":{"type":"Var","name":"source"},
                       "var_name":"$item","acc_name":"$acc",
                       "init":{"type":"Lit","value":""},
                       "body":{"type":"Cat","items":[{"type":"Var","name":"$acc"},
                                                       {"type":"Var","name":"sep"},
                                                       {"type":"Var","name":"$item"}]}},
              "start":{"type":"Count","source":{"type":"Var","name":"sep"}},
              "stop":{"type":"Lit","value":1000000000}}}
```

— exactly the seven fixed nodes `DELIMJOIN_BUDGETWALL_RESULTS.md §1.2`
counted by hand (`init`+`accv`+`itemv`+`body/Cat`+`joined/Fold`+
`sep_len/Count`+`big_stop/Lit`), now authored as data instead of a Rust
function. **Correctness of the ValueTaker-style binding is sound here**:
`source`/`sep` are each evaluated exactly once (identical to today's
behaviour, since `Fold`'s own native arm already evaluates its `source`
field exactly once per call, side-effect-free per this Term's own documented
"Pure. No substrate mutation" contract) — binding them as pre-computed
Values referenced via `Var` inside the template changes nothing observable.

### 7.2 Would it have changed DELIMJOIN's measured OUTCOME?

**No — and this is the sharp, honest finding, not an assumed one.** Two
independent reasons, both already measured in `DELIMJOIN_BUDGETWALL_
RESULTS.md`, neither touched by WHERE the composition lives:

1. **The reachability ceiling is a property of the template's own fixed
   structure**, not of its authoring location. `DELIMJOIN_BUDGETWALL_
   RESULTS.md §1.2` found the extra=7 floor is confirmed by TWO
   independently-designed constructions converging on the same number —
   minimum size at `sa=1,sb=1` is `size = 1(Slice) + 7(extra) + 1 + 1 = 10`,
   one level past `max_size:9`. A registry-authored `JoinListSep` has the
   identical extra-cost floor (`extra_cost:7` in the registry entry above,
   unchanged) — it is unreachable under production settings for exactly the
   same arithmetic reason, regardless of whether it is a Rust builder
   function or a parsed JSON template.
2. **The independently-decisive spurious-memorization finding is
   orthogonal to authoring location.** `DELIMJOIN_BUDGETWALL_RESULTS.md
   §1.3`'s diagnostic `max_size:10` probe found a DIFFERENT construction
   (`IfThenElse`/`Gt` over a lowered last element) wins the race first,
   because it is built from ops near the FRONT of `DEFAULT_OPS` and this
   file's own "always append, never interleave" ordering discipline places
   any newly-registered op — derived or primitive — LAST. A registry-driven
   `Call{"JoinListSep",...}` candidate, size-ordered exactly like any other
   op, loses this same race for the same reason: this design does not
   change enumeration ORDER, only WHERE a template's definition lives.

### 7.3 Would `JoinListSep` even have PASSED the mint bar (§5.3)?

**No — and this is a positive result for the design's own discipline, even
though it means no capability gain here.** `DELIMJOIN_BUDGETWALL_RESULTS.md
§1.4` states directly: *"No other task in the fixture benefits... 421 is
the sole candidate for a real non-empty-separator, heterogeneous-element
join."* Support = 1, not ≥ 2. Under §5.3's own cross-task recurrence bar,
this candidate would correctly NEVER be minted as a trusted, registered,
admitted derived op — it would sit exactly where it sits today: a real,
verified-safe one-off, reverted, not persisted. **The mint discipline
designed in §5 would have correctly refused to promote a support=1
candidate — which is the discipline working as intended, not a gap in it.**
The larger, real, honestly-stated payoff of this whole design is therefore
NOT "task 421 would now pass" (it would not, under any build variant, for
reasons §7.2 shows are independent of this design entirely) — it is: **the
NEXT task that needs a `sep.join(...)`-shaped construction, on a spec where
the reachability floor and the spurious-race problem do NOT also bind,
would no longer require re-deriving and re-building the same Rust twice** —
a real, but narrower and more honestly-scoped, gain than a first read of the
task brief's framing might suggest.

---

## 8. GO / NOT-YET-READY, and the buildable first slice

**Design-level call: GO.** §2 finds a real, close, already-tested precedent
for exactly the right dispatch shape (`DerivationRegistry`'s `ValueTaker`),
missing only an addressable object for brand-new op names — precisely the
`RULES_AS_SHAPE_DESIGN_SPIKE.md` pattern, one level over. §3 prices the one
generic mechanism needed at a bounded, one-time, ~60-100-line, six-file cost
matching an already-shipped variant's exact footprint.

**Build-level call: NOT-YET-READY to build the full (build-B) generic
pool-typed combinator blind.** §4 found the "zero new Rust per derived op"
claim is real but conditional — true only for derived ops whose pools match
the existing (A) shapes, or once the larger (B) combinator is built. §7
found the mechanism, even fully built, would not have converted its own
concrete test case (`JoinListSep`/task 421) for two reasons unrelated to
this design (a fixed reachability floor, a fixed enumeration-order race) —
so building (B) speculatively, before a SECOND real candidate needing its
generality is identified, risks the exact "grew capability with no evidence
it moves a number" pattern this arc's own `RUNG1_RESULTS.md` and
`CEILING_REASSESSMENT_3` measured against.

**The buildable first slice, mirroring `OPLIST_ADMISSIBILITY_GRAMMAR_
RESULTS.md §8`'s own discipline exactly (prove the mechanism reproduces a
known-safe fact before trusting it with anything novel):**

1. **Build `TermNode::Call{name,args}`** (§3.2-3.4) — the one generic,
   one-time, ~60-100-line mechanism, sized precisely against `Reverse`/
   `Plus`'s own real footprint. New `derived_ops` `SynthEnumerate` argument
   (§3.3(b)), parsed by an extension of `parse_excluded_term`'s existing
   local grammar — NOT a new `EvalCtx.derived_ops` field, since that would
   adopt the SAME never-wired-from-Python shape §2.2 found for
   `DerivationRegistry` rather than reusing `exclude`'s already-proven
   direction.
2. **Add build (A)'s narrow fallback arms only** (§4) — one small addition
   to each of the five existing name-dispatch functions, covering derived
   ops that fit an EXISTING pool shape. Do NOT build the generic (B)
   combinator yet.
3. **PARITY CHECK**: hand-author exactly ONE derived op as registry data
   that fits an existing `OpKind` shape (Unary or Binary, general pool
   only — NOT `JoinListSep`, which needs (B)) and confirm byte-identical
   search behaviour against a hand-Rust equivalent, on the existing
   257-task battery — zero regressions, zero new passes expected (a
   plumbing proof, exactly OPLIST's own Step 4 discipline).
4. **Only then**, as an explicitly separate, independently-gateable
   follow-on rung: price and build (B)'s generic pool-typed combinator —
   gated on identifying a SECOND real candidate (support ≥ 2 evidence, or
   at minimum a second plausible task) that actually needs the
   heterogeneous-pool shape (A) cannot cover, so the larger build is
   evidence-driven rather than speculative.
5. **Only then**: build the offline mint sweep (§5.4) and wire the Γ
   composition (§6) — reusing `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md
   §3-4`'s own design unchanged, adding only the `kind` attr distinction.

**Explicitly NOT in this first slice**: the generic (B) combinator, the
mint sweep, the Γ-composition wiring, registering `JoinListSep` itself
(§7.3 already shows it would fail the mint bar even if built), and any
claim that this design moves the MBPP pass count — per §7.2, it honestly
does not, for the one concrete case this document could check against real,
already-measured data.

---

## 9. What this document does NOT establish

1. **No code was written or run.** `git diff --stat df00b37` in this
   worktree is empty for every tracked source file — confirmed directly
   before writing this section (`git status` shows only the two new docs
   under `docs/research/program_synthesis/`, untracked until this commit).
2. **Build (B)'s real size is a design-time estimate** ("bounded by a
   closed two-pool taxonomy"), not a measured line count — unlike §3.4's
   `Call`-variant pricing, which IS measured against a real shipped
   variant's exact footprint.
3. **The mint bar's own sufficiency (§5.3) is stated as a floor, not
   proven safe** — a support=2 candidate that passes both held-out checks
   could still, in principle, be a coincidental double-fit rather than a
   genuine primitive; no corpus-wide false-positive rate is measured here.
4. **This document's own retroactive test case (§7) is exactly ONE
   candidate** (`JoinListSep`), and it is a NEGATIVE case for capability
   gain (support=1, reachability-bound, race-bound) — this document does
   NOT claim a positive retroactive case exists anywhere in the corpus; no
   sweep was run to look for one (that sweep is itself named as future,
   gated work, §8 step 4).
5. **Whether a derived-operator tier, once built, ever moves the MBPP pass
   count is unmeasured and — per §7.2 — is not established even
   qualitatively for the one case this document could check against real
   data.** Its claimed value is REUSE (avoiding re-deriving a composition
   in fresh Rust each time it recurs) and REGISTRY HYGIENE (a stricter
   cross-task mint bar than the sd loop's ordinary single-observation
   mint), not a demonstrated capability gain.
6. **This document does not re-verify `OPLIST_ADMISSIBILITY_GRAMMAR_
   RESULTS.md`'s own findings** beyond the one figure corrected in §0 — it
   extends that document's design (§6) and cites the rest as landed.

---

## Reproduce (read-only; nothing here writes to the graph or the engine)

```bash
cd /home/matt/ozmadev/ocelot-worktrees/derived-operator-tier
git log --oneline -1   # on top of main @ df00b37
git diff --stat df00b37   # empty for every tracked source file
sed -n '1,217p' runners/dsl/src/synth_enumerate.rs        # module doc, architecture
sed -n '263,372p' runners/dsl/src/synth_enumerate.rs      # OpKind + OP_TABLE (recount: 50, not 31)
awk '/^const OP_TABLE/,/^\];/' runners/dsl/src/synth_enumerate.rs | grep -c '^\s*("'
sed -n '541,663p' runners/dsl/src/synth_enumerate.rs      # per-OpKind hand-written builders
sed -n '1004,1020p' runners/dsl/src/synth_enumerate.rs    # local_sym
sed -n '2197,2203p' runners/dsl/src/synth_enumerate.rs    # the three template pools
sed -n '2592,2722p' runners/dsl/src/synth_enumerate.rs    # the six combinatorics loops
sed -n '2520,2556p' runners/dsl/src/term.rs                # DerivationRegistry / Derivation
sed -n '2561,2586p' runners/dsl/src/term.rs                # EvalCtx (graph + derivations fields)
sed -n '2674,2703p' runners/dsl/src/term.rs                # lookup_value_taker_def (ctx.interner.lookup)
sed -n '3403,3479p' runners/dsl/src/term.rs                # body-taker doc note + try_derivation!
grep -rn "with_derivations\|DerivationRegistry" runners/dsl/src/*.rs | grep -v term.rs
sed -n '870,880p' runners/dsl/src/shape.rs                 # confirms #[test] context
sed -n '1,132p' tools/gen_term_variants.py                 # mechanical regen, read in full
sed -n '1172,1230p' domains/prog_synthesis.py               # exclude precedent, run_enumerate
```
