# PROGRAM SYNTHESIS P1 — implementation notes (hub IR + ProgEval + naming)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §3.2/§4-P1,
`PROGRAM_SYNTHESIS_PREREG.md` §3, and `PROGRAM_SYNTHESIS_P0_HISTOGRAM.md`
(whose §4 recommendation picked the variant set implemented here).

## 1. The variant set (23 IR + ProgEval + 2 naming = 26 new TermNode variants)

The P0 histogram's 21-variant 80.5% set, plus `While` and `Raise` — both
included as the P0-registered **deviation-with-reason** (low corpus mass;
semantically load-bearing for a fueled interpreter: condition-terminated
loops and honest trap surfacing). `NUM_TERM_VARIANTS` 181 → **207**.

## 2. Reconciliation table — new variant ↔ existing Term

Every IR variant carries the `Prog` prefix: each is PROGRAM-domain data
(inert under the main `evaluate()`, executed only inside `ProgEval`), and
several superficially resemble existing DSL Terms they must never be
conflated with.

| new variant | existing Term consulted | verdict + why |
|---|---|---|
| `ProgAttrGet` | `Attr` | DISTINCT. `Attr` reads a GRAPH NODE's attr (requires `Value::Node`); `ProgAttrGet` reads a field of a program VALUE (records are Dicts) and traps honestly on a miss. |
| `ProgSubscript` | `IndexAt` | DISTINCT. `IndexAt` is the DSL list primitive (its own clamp/None conventions); `ProgSubscript` is Python subscript semantics — negative indices, Dict keys, string chars, trap `index:oob`/`key:<k>` on miss. `IndexAt` stays untouched. |
| `ProgContainerLit` | `Vec_` / `SetT` / `MkDict` | DISTINCT but REALISES onto their value space. The IR keeps the surface `kind` (list/tuple/set/dict — needed for rendering, which `Vec_`/`SetT`/`MkDict` erase); at ProgEval time list/tuple → `Value::Tuple`, set → `Set`, dict → `Dict` (MkDict's alternating-items + `cmp_value` sort convention reused for dict items). |
| `ProgAssignVar`/`ProgSeq`/`ProgIfStmt`/`ProgForEach`/`ProgWhile`/`ProgTupleUnpack`/`ProgAugAssign`/`ProgLoopCtl`/`ProgReturn`/`ProgTryOr`/`ProgRaise`/`ProgImportStmt`/`ProgSubscriptSet`/`ProgAttrSet`/`ProgDefFnParam` | (none) | NEW — the DSL is pure and has no statements at all. `IfThenElse` remains the EXPRESSION conditional; `ProgIfStmt` is statement-grain (bodies are statements, not values). `Fold` remains the DSL reduction; loops with mutation/break/continue are not expressible as `Fold`. |
| `ProgCallExtern` | `UseTool` | DISTINCT by design. `UseTool` is the effectful host-tool boundary (registered Python handlers). `ProgCallExtern` NEVER reaches the host: it evaluates only against the declared oracle Dict, natively, and traps `extern:<name>` otherwise — plan §3.2's "no shelling out mid-eval". |
| `ProgComprehensionList`/`ProgComprehensionGen` | `FilterList`+`MapList` | DISTINCT. The composition exists in the DSL but loses the surface form (list vs generator display) needed for rendering, and comprehension iterations must charge FUEL. Gen realises eagerly (Tuple) — consumers (`sum`) agree with CPython because the realised sequence is identical. |
| `ProgIsOp` | `Eq` | DISTINCT and deliberately narrow. P0 §4: identity must not be approximated by value equality. Honest scope: None-identity + Node/Bool identity; anything else traps `is_op:unsupported`. |
| `ProgFString` | `Cat`/`StringConcat` | DISTINCT. Cat's `str()` coercion is not Python's `str()` spelling (True/None/2.0); `ProgFString` renders each part via `py_str` (CPython-agreeing scalar spellings, gated). |
| `ProgEval` | `EvalSubgraph` | SIBLING. Same subgraph-rooted convention (`reflect::term_from_subgraph`, immutable-interner reconstruction); ProgEval additionally accepts an INLINE `Prog*` subtree, and is fueled. |
| `SnakeCase`/`CaseFold` | `StringConcat`/`StringSlice` | SIBLINGS in the string family; same `Surface(Text)`-out convention. |

## 3. ProgEval design decisions (engine: `runners/dsl/src/prog_eval.rs`)

- **Contract:** `ProgEval{prog, env, oracles, fuel, field}` →
  `Dict{result, env_out, steps, halted, trap}`. Pure Dict-in → Dict-out;
  no substrate mutation, no I/O. Module-per-engine precedent
  (shape_decode.rs); term.rs arm is a one-line handoff; `field` selector
  follows the ShapeDecode/strokes convention (local copy).
- **Env bridge:** program variables live in the interpreter's own ordered
  binding list. Prog-free expression subtrees are delegated WHOLE to the
  standard `evaluate()` with program bindings pushed as Var bindings over
  the caller's env (rule-match vars stay readable; program vars shadow).
  Mixed (Prog-under-DSL-operator) subtrees: And/Or/Not/IfThenElse are
  interpreted natively (short-circuit MUST hold over Prog subexpressions
  — a subscript in the unreached branch must not trap; gated), and a
  documented compositional core (arith/compare/set-algebra/collection
  constructors) rebuilds the operator over `Lit` children in a scratch
  arena and delegates — so DSL SEMANTICS GOVERN arithmetic everywhere.
  Any other operator over a Prog subexpression traps
  `expr:unsupported_over_prog` honestly.
- **Documented divergences from CPython** (fixtures respect these; each
  is a semantics choice, not an accident): DSL arithmetic conventions
  apply in expressions (`Div`-by-zero → 0.0, `Mod`-by-zero → 0 — no
  ZeroDivisionError); list/tuple collapse to `Value::Tuple`; lvalue
  writes REBUILD immutable values along a Var-rooted path (no aliasing);
  set iteration order is the substrate's canonical order.
- **Trap model:** traps are strings on interpreter control flow
  (`raise:<s>`, `extern:<name>`, `extern:unimplemented:<name>`,
  `name:<n>`, `attr:<a>`, `key:<k>`, `index:oob`, `unpack:arity`,
  `is_op:unsupported`, `iter:<kind>`, `lvalue:unsupported`,
  `loopctl:outside_loop`, `param:<n>`, `prog:invalid`). `ProgTryOr`
  catches any trap from its body (binding the reason string to
  `exc_var`); Break/Continue/Return pass through as in Python. **Fuel
  exhaustion is NOT a trap** (`Flow::Fuel` is a distinct variant) — it is
  never catchable, else a program could forge `halted`.
- **Fuel:** counts executed statements + loop/comprehension ITERATIONS
  (`ProgSeq` containers free). Exhaustion → `halted:false`,
  `steps == fuel`, `trap:"fuel"`, honest partial `env_out`, never a
  value. `fuel <= 0` → documented default 10_000. In-frame integer; no
  wall clock.
- **CallExtern / oracle declaration:** `oracles` is a Dict (extern name →
  any declaration value). Undeclared → `extern:<name>`; declared but
  outside the native set → `extern:unimplemented:<name>`. Native oracle
  set (the histogram's call_builtin mass): len / abs / min / max /
  range / sum / str / int / float / bool / sorted. `range` materialises
  eagerly; length > 1,000,000 traps `extern:range:too_large` — an honest
  trap, not a silent cap. No method-style native oracles at P1 (`recv`
  present → unimplemented trap).
- **prog forms:** an inline `Prog*` subtree in the same arena, or a Term
  evaluating to `Value::Node` rooting a reflected IR subgraph
  (`term_from_subgraph` into a scratch arena — the EvalSubgraph
  convention; reconstruction needs only `&Interner`). Anything else →
  `prog:invalid`, halted:false.

## 4. The interner decision (plan risk §6.3 — resolved: fallback (b))

**Investigated:** `EvalCtx::interner` is `&Interner` by construction —
`evaluate()` can never intern. The candidate "safe interning paths":

1. *Parse-time interning* — already exists and is the sound path for
   every identifier that ARRIVES as data: `jsonio::term_from_json` and
   the reflect reconstruction both run with real Syms minted at
   parse/install time. All IR identifier fields (`name`, `targets`,
   `var`, `attr`, `op`, `names`, …) are `Sym`s for exactly this reason.
2. *Interior mutability on the interner* — rejected. The Interner hands
   out `&str` borrows into its own storage across the whole evaluator
   (`resolve` during matching, selector audits, shape passes), and the
   crate's concurrency story (Substrate behind a mutex, but `EvalCtx`
   deliberately splitting immutable graph/interner from mutable
   counters/caches) treats the interner as frozen during evaluation.
   Making it a lock/RefCell would put a lock acquisition on the hottest
   compare path in the engine and widen the aliasing contract of every
   existing `resolve` call — a soundness-adjacent change this rung has
   no need for.

**Decision: the registered fallback — `Surface(Text)` end-to-end for
EVAL-PRODUCED strings** (identifiers synthesized at run time), which is
already the crate-wide convention (`StringConcat`, `ToJsonString`,
`TextShape` keys, ShapeDecode output). Verified TRUE, not assumed
(tests/test_prog_ir_migrated.py):

- a Computed `set_attr` effect stores a `SnakeCase` Surface(Text) result
  as a usable string attr (graph-resident Rule fired via `tick()` — the
  rule-minting-dialect finding-4 coercion path);
- render templates accept it (`Cat` over `SnakeCase` output concatenates).

New naming primitives: `SnakeCase{text}` (lowercase, camel-boundary →
`_`, non-alphanumeric runs → one `_`, trimmed) and `CaseFold{text}` —
Str/Surface(Text) in → Surface(Text) out; non-strings → honest `None`.
Together with `StringConcat`/`StringSlice` this is the minimal set that
lets a rule name a variable from spec words; no regex engine.

## 5. Gates (P1, all green at this commit)

- **Rust:** `cargo test --release --lib` — 673 passed / 0 failed
  (includes 20 new `prog_eval::tests` + `scale_audit::
  variant_table_covers_the_enum` over the regenerated 207-entry table).
  Note: linking the test binary on this box needs
  `RUSTFLAGS="-C link-arg=-lpython3.14 -C link-arg=-L/usr/lib"` (pyo3
  extension-module + rust-lld leaves Python symbols undefined in test
  binaries).
- **Python:** `tests/test_prog_ir_migrated.py` — 54 passed: per-variant
  reflect round-trip (all 26, canonical-JSON identity + idempotence, via
  the new mechanical `Substrate.term_subgraph_json` read-back);
  ProgEval ≡ CPython on the fixture corpus (~18 programs, every
  semantic variant covered, While + Raise included; disagreement list
  EMPTY); fuel honesty (halted:false, steps == fuel, uncatchable);
  structural honesty (bare statement variants inert under `evaluate()`);
  naming primitives end-to-end.
- Neighbor suites re-run on the rebuilt engine (see the P1 report):
  code_synthesis_baseline / code_curriculum / code_writing /
  composer_driver / dimension_inference.

## 6. Operational facts recorded en route (honesty ledger)

- **Worktree engine selection under pytest:** invoking pytest from a
  `.claude/worktrees/...` tree WITHOUT `--confcutdir=.` loads the
  CANONICAL tree's root `conftest.py` first (it is a filesystem
  ancestor), whose `engine_preamble` resolves `substrate_rs` to the
  canonical `_native.abi3.so` — a stale-engine measurement under this
  rung's own new Terms (they'd read as `UnknownTermType`). All P1 python
  numbers were produced with `--confcutdir=.` and the worktree's
  freshly-built engine (module `__file__` verified in-process). This is
  exactly the two-binary hazard `domains/engine_provenance.py` documents,
  in its worktree form.
- The install step is the established one: `cargo build --release` then
  atomic copy of `target/release/libsubstrate_rs.so` over
  `runners/dsl/python/substrate_rs/_native.abi3.so`
  (`domains/self_modification.py::rebuild_native`'s `_sync_native`).
