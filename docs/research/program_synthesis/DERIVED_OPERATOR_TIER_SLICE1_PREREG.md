# Derived-operator tier — first buildable slice — PREREG

Parent design: `DERIVED_OPERATOR_TIER_RESULTS.md` (merged to main, read in
full before this doc was written — this doc does not re-derive that
design, only prices and pins the exact implementation of §9 steps 1-3).

Base: `main @ a8cb4f5` ("Merge oplist-admissibility-grammar-slice1:
Γ-admissibility first slice for op-list gating"), verified via
`git log --oneline -1 main` immediately before creating the worktree
(the parent doc's own `df00b37` citation is stale — main has moved twice
since, confirmed live per this task's own instruction not to trust it).
Worktree: `/home/matt/ozmadev/ocelot-worktrees/derived-operator-tier-slice1`,
branch `derived-operator-tier-slice1` — **not merged to `main`**, left for
the orchestrator to review and merge.

## Scope (exactly `DERIVED_OPERATOR_TIER_RESULTS.md` §9, steps 1-3)

1. `TermNode::Call{name, args}` — one new Rust variant, ~60-100 lines
   across six files, priced against the `Reverse`/`Plus` precedents
   (§3.4). New `derived_ops` argument on `SynthEnumerate`, evaluating to
   a `Lit`-wrapped list of Term-JSON strings (registry entries, not bare
   Terms), parsed by an extension of `parse_excluded_term`'s existing
   local grammar.
2. Build (A)'s narrow fallback arms only (§4): on an unrecognized op
   name, the five existing name-dispatch functions check the registry
   and emit `Call{name,args}` instead of failing. Build (B) (the generic
   pool-typed combinator) is explicitly NOT built.
3. Parity check: one hand-authored derived op (Unary or Binary, general
   pool only), confirmed byte-identical against a hand-Rust equivalent,
   zero regressions/zero new passes on the 257-task MBPP battery.

Explicitly NOT in scope: build (B), the offline mint sweep, Γ-composition
wiring, registering `JoinListSep`, any motor-program unification — all
per §9's own exclusion list.

## Design decisions this slice pins down that the parent doc left open

The parent doc's §3.2 pseudocode reads `ctx.derived_ops` directly inside
`Call`'s evaluate arm and its §3.3 choice (b) says "not a new
`EvalCtx.derived_ops` field" when comparing to option (a) — that
sentence is about the **crossing point from Python** (option (a) would
have been a new PyO3-exposed `EvalCtx` setter, mirroring the
never-wired `derivations` field; rejected). It does not resolve, and
this slice must resolve, a real Rust borrow-checker question the parent
doc did not need to hit at design time: `EvalCtx<'a>` has ONE lifetime
parameter, shared by every field (`graph: &'a TypedGraph`,
`interner: &'a Interner`, `derivations: Option<&'a DerivationRegistry>`,
…). A `DerivedOpRegistry` built fresh *inside* `eval_synth_enumerate`
(from the new `derived_ops` argument, per (b)) is a local, short-lived
value — it cannot satisfy `'a`, which is fixed by whatever ancestor call
originally constructed `ctx` (typically far outliving one
`SynthEnumerate` call). Storing `Option<&'a DerivedOpRegistry>` and
assigning a local reference into it would not compile (or would require
splitting `EvalCtx` into two lifetime parameters, which breaks lifetime
elision at all ~19 files that write bare `&mut EvalCtx` today — far
outside this rung's budget, and not something any prior touch-point
accounting in the parent doc priced).

**Resolution, adopted here:** `EvalCtx` gains
`pub derived_ops: Option<std::sync::Arc<DerivedOpRegistry>>` — an
`Arc`, not a borrowed reference, matching the codebase's own existing
convention for shared immutable data (`Value::Surface` already carries
`Arc<[u8]>`). `Arc` carries no borrowed lifetime, so it sidesteps the
problem entirely: `EvalCtx<'a>` keeps its existing single lifetime
parameter, unchanged, so **zero other files need to change** for this
reason. `eval_synth_enumerate` sets `ctx.derived_ops = Some(registry_arc)`
for the scope of its own search and restores the previous value
(`None` in every real case today) before returning, via a small
`with_derived_ops` scope-guard helper, so a stale registry can never
leak to an unrelated `Call` node evaluated later in the same
`evaluate()` call tree. This is the one place this slice's own
engineering diverges from the parent doc's pseudocode shape (which
elided the lifetime question), and it is called out explicitly here
rather than silently deviating.

**The `derived_ops` argument's wire shape** is a list of Term-JSON
registry-entry strings (not bare Term-JSON), each
`{"name", "params":[{"name","pool"}], "extra_cost", "template"}` exactly
per the parent doc's §3.1 schema. Parsing is two-stage, because
`op_list` (which needs to know a derived op's arity/pool shape) is built
*before* `Search`/`search.scratch` exists (the arena the template body
must be parsed into, mirroring the `filter_templates_by_size` precedent
exactly): stage 1 (before `Search` exists) parses only the METADATA
(name, per-param pool, extra_cost, raw template JSON) — enough to infer
an `OpKind` for `op_list` construction; stage 2 (right after `Search` is
constructed, alongside where `exclude` is already parsed into
`search.scratch`) parses each entry's `template` into `search.scratch`
via `parse_excluded_term` called with an EXTENDED `var_by_name` (spec
vars plus this entry's own params) — reusing that function's existing
grammar unchanged (`Plus`/`Var`/etc. already cover the one parity op
this slice registers), which is the literal sense in which this is "an
extension of `parse_excluded_term`'s existing local grammar": a new
calling context (extended `var_by_name`), not a grammar rewrite.
Nested `Call`-referencing-`Call` composition inside a template is
explicitly NOT supported by this parser (out of scope; no entry this
slice registers needs it).

**Arity/pool → `OpKind` inference** (used only for the explicit `ops`
list; derived ops are never part of a typed default, exactly like
`JoinListSep`'s own precedent of being explicitly requested only):
`[general]` → `Unary`, `[general,general]` → `Binary`,
`[general,general,general]` → `Ternary`, `[list]` → `ListUnary`,
`[list,list]` → `ListBinary`. Any other pool combination (including
`JoinListSep`'s own mixed `[list,general]` shape) is correctly refused
— that is build (B)'s job, not this slice's.

**Fallback-arm reachability, stated honestly in advance:** `build_op`
(Unary/Binary/Ternary), `build_list_unary`, and `build_list_binary` are
reachable today (their `OpKind`s are exactly the ones the inference
above can produce). `build_list_ho` (`ListFilter`/`ListMap`) and
`build_indexed_map` (`IndexedMap`) will also get a mechanical fallback
arm per step 2's literal instruction, but per the parent doc's own §3.1
("the three template pools are NOT argument sources for a top-level
op"), no `op_list`-construction path this slice builds can route an
unrecognized name into those two `OpKind`s — so those two fallback arms
are added for completeness/symmetry but are DEAD CODE under this
slice's own registry-inference rules. This will be stated again,
plainly, in the RESULTS doc — not quietly left as an implied capability.

## The parity-check derived op

`Total2` — Binary, general pool, template `Plus{items:[Var(a),Var(b)]}`,
`extra_cost:0`. Chosen deliberately to be the CLEANEST possible parity
test: it is not a novel composition, it is a registry-authored
re-expression of the ALREADY-SHIPPED, byte-for-byte-identical `Plus` op
— so `Call{"Total2",[a,b]}` must evaluate to exactly the same `Value`
`Plus{items:[a,b]}` does, and (since `extra_cost:0` matches `Plus`'s own
implicit zero-extra-node shape) a search offered `ops:["Total2"]` must
find it at exactly the same size, with the same `tested`/`distinct`/
`pruned_equiv` counts, as an identical search offered `ops:["Plus"]` on
the same spec. This isolates dispatch-plumbing correctness with zero
confounds — exactly "a plumbing proof, not a capability claim," per the
parent doc's own framing.

## Gates

- `cargo build --release`
- `cargo test --lib --release -- --test-threads=1` — baseline 774 before
  this rung's changes (verified fresh in this worktree), expect 774+N
  after, N = new tests added (parity test(s) for `Call`/`Total2` plus
  any unit tests for the new parsing functions).
- `bash scripts/engine_build.sh` to install the built extension.
- `python3 scripts/mbpp_endgame_battery.py` — compare the resulting
  full/content_stripped/official task-ID sets against
  `results/mbpp_endgame.json` (69/68/98) — paired failing/passing ID
  lists, not bare counts. Expected: byte-identical to baseline (this
  rung's new code paths are never exercised by the battery's own
  `ops`/`derived_ops` usage, so zero drift is the correct, checked
  prediction, not merely hoped for).

## Revert condition

If any gate reads NO-GO, revert the unsafe/incomplete pieces before the
final commit rather than leaving broken state in the worktree.
