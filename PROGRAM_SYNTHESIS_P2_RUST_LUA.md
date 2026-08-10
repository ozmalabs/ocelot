# PROGRAM SYNTHESIS P2 — Rust + Lua READING into the hub Program IR

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §3.3/§4-P2,
`PROGRAM_SYNTHESIS_PREREG.md` §4, and `PROGRAM_SYNTHESIS_P1_NOTES.md` (the
`Prog*` variant set + ProgEval semantics this track reads INTO). The
python-frame half of P2 is the sibling track (`domains/prog_ir_emit.py`,
`PROGRAM_SYNTHESIS_P2_PYTHON.md`).

**Gate suite:** `tests/test_prog_read_rust_lua_migrated.py` — **62 passed**
(~3 s, `--confcutdir=.` per the P1 worktree-engine note). Neighbor suites:
P1 gates green; `tests/test_file_ingest.py` + upload suites green (12
passed); the only reds seen while sweeping neighbors
(`test_document_memory_migrated` ×2, `test_topic_span_migrated` ×1) are
**pre-existing entries in `results/failure_baseline.json`** — no new red.

## 1. Architecture (what landed where)

```
.rs/.lua source
  → domains/ts_ingest.ingest_source        MECHANICAL tree-sitter CST dump:
      CstNode{kind, field, child_index,    every node incl. anonymous
              named, text(leaves),         operator tokens; child edges.
              origin="world_adapter_ts"}   No decisions (ingest_ast twin).
  → seeds/rust_correspondence.json         THE CORRESPONDENCE as SEED DATA:
    seeds/lua_correspondence.json          CorrespondenceRow{cst_kind, op-
                                           guard, term+plan | handler, note}
                                           (ast_term_rules.CORRESPONDENCE
                                           spirit; agent-inspectable).
  → domains/ts_ingest.TableWalker          the SHARED mechanical applier:
                                           dispatch = table lookup ONLY;
                                           rows either apply a uniform
                                           field plan or name a registered
                                           shape handler (composer_dispatch
                                           name-keyed-registry precedent).
  → domains/prog_ir_rust.py                per-language handler registries
    domains/prog_ir_lua.py                 (mechanical desugars) + read_
                                           source/read_function read-outs.
  → hub Program IR (P1 Prog* Term-JSON)  → ProgEval / add_term_subgraph
```

Honest-residual contract: any construct without a row (or hitting a
handler's named boundary) records its cst kind / reason and the read
returns `{ok: False, ir: None, blockers: [...]}` — **never a silent
partial emit** (a placeholder keeps the walk total so the blocker list is
complete, but blocked reads never hand back IR). A statement variant
landing in a value slot is itself a named blocker
(`statement_in_value_position:*`) — the walk refuses category errors
rather than letting ProgEval mis-read them.

`domains/file_ingest.py` routing: `.py/.rs/.lua` classify as a NEW
`source` kind (checked before the text/mime test — a .py's mime is
`text/x-python`). `_ingest_source` lands an UploadedDocument with the
code graph (`has_code_root`), per-function hub IR as **reflected
graph-resident Term subgraphs** (`has_prog_ir`, runnable via
`ProgEval{prog: <node>}` — gated), the honest blocker list, and the code
REGISTER verdict (`register_source.decode_register` read-back:
`register`/`register_family` attrs). Source is deliberately NOT
mention-tokenised (the text pipeline's Mention chain is the wrong
instrument for code — it would pollute referent resolution); plain-text
uploads are byte-unaffected.

## 2. Scope per language (in / out)

### Rust (`seeds/rust_correspondence.json`, 38 rows)

| in scope | mapping |
|---|---|
| `fn` items, typed params | body → `ProgSeq`; **param types are ANNOTATIONS in the read-out record** (`params: [{name, ty}]`) — the IR is untyped at P2 |
| `let` / `let mut` | `ProgAssignVar` (`mut` is a frame fact the IR does not carry) |
| assignment / `xs[i] = v` | `ProgAssignVar` / `ProgSubscriptSet` |
| `+= -= *= /= %=` | `ProgAugAssign` add/sub/mult/floordiv/mod |
| `if`/`else`/`else if` | tail-only (pure) branches → `IfThenElse` EXPRESSION; statement branches → `ProgIfStmt`; a branch mixing statements AND a tail value → blocker `if_branch_mixed_tail` |
| `while` | `ProgWhile` |
| `loop` / `break` / `continue` | `ProgWhile(Lit true)` / `ProgLoopCtl` (`break <value>` → blocker) |
| `for x in a..b` / `a..=b` | `ProgForEach` over the declared `range` oracle (`..=` adds 1 to the stop) |
| `for x in expr` | `ProgForEach` over the value directly |
| `return` + TAIL EXPRESSION | tail desugars to `ProgReturn` (incl. tree-sitter's no-semicolon `expression_statement` wrapping of block-like tails); a unit-valued statement tail runs as a last statement |
| `vec![a,b]` / `[a,b]` / `xs[i]` | `ProgContainerLit(list)` / `ProgSubscript` (rust is 0-based like the hub — no shift) |
| calls: `f(x)` / `T::f(x)` / `x.m(y)` | `ProgCallExtern` — name verbatim / path-qualified dotted / `{name, recv}` (methods trap per the P1 recv contract) |
| arithmetic, comparison, `&&`/`||`, unary `-`/`!` | DSL Terms (ledger §3) |

**Out (named blockers, fixture-gated on `match`):** `match`, closures,
generics/traits/impls, `&`/`*` (borrows/deref), tuple/struct patterns,
`vec![x; n]`, non-`vec` macros, `break <value>`, shadowed non-identifier
lvalues, string-typed arithmetic beyond what the DSL defines.

### Lua (`seeds/lua_correspondence.json`, 36 rows)

| in scope | mapping |
|---|---|
| `function f(...)` decls (named, incl. `local function`) | body → `ProgSeq` |
| `local x = e` / `x = e` | `ProgAssignVar` (multiple targets/values → blocker) |
| `if/elseif/else` | nested `ProgIfStmt` |
| numeric `for i = a, b [, step]` | `ForEach` over the `range` oracle; the INCLUSIVE stop shifts by the literal step's sign (`b+1` / `b-1`); non-literal step → blocker |
| generic `for k, v in ipairs(xs)` | counter + `ForEach` desugar (k is 1-based exactly as ipairs); `pairs()`/custom iterators → blocker |
| `while` / `break` | `ProgWhile` / `ProgLoopCtl` |
| `repeat B until C` | `B; While(Not C){B}` — the body is emitted twice (exact for straight-line bodies); a body containing `break` → blocker `repeat_with_break` (the duplicated first pass would strand the break outside the loop) |
| `return e` | `ProgReturn` (multiple return values → blocker) |
| `{a, b, c}` array part | `ProgContainerLit(list)`; ANY keyed field (`{k=v}`, `[k]=v`) → blocker `table_map_part` — the map-part caveat, recorded, never dropped |
| `t[i]` read/write | `ProgSubscript`/`SubscriptSet` with **index `i-1`** — the 1-based→0-based CROSS-FRAME shift lives in the correspondence (array-part reading only; a string-literal key → blocker `table_string_key`) |
| `a .. b` | `ProgFString(a, b)` (ledger §3) |
| `#xs` | the declared `len` oracle (sound for the array part) |
| calls: `f(x)` / `a.b(x)` / `t:m(x)` | `ProgCallExtern` — lua names verbatim (`print`, `math.floor` dotted) / `{name, recv}` for method calls |
| arithmetic, comparison, `and`/`or`/`not`, unary `-` | DSL Terms (ledger §3) |

**Out (named blockers, fixture-gated on varargs + map-part):** varargs
(`...`), multiple assignment/return values, keyed table fields, string
keys, `pairs()`/iterator protocol, metatables, coroutines, method
definitions (`function t:m()`), `goto`, bare `t.a` field reads/stores.

## 3. Semantic divergence ledger (each is a recorded choice, not an accident)

ProgEval's expression semantics are the DSL's (P1 notes §3). Probed on the
installed engine (`Div 7/2=3.5`, `IDiv -7//2=-3` [trunc], `Mod -7%2=1`
[floor], `Pow 2**3=8`):

| surface | hub mapping | agreement | divergence |
|---|---|---|---|
| rust `/`, `/=` (i64) | `IDiv` / aug `floordiv` (both TRUNCATE) | **exact** for i64 | float division not modeled (fixtures integer-only) |
| rust `%`, `%=` | `Mod` (floor-style) | positives exact | negatives differ (rust `-7%2 = -1`, hub `1`) — fixtures avoid |
| rust i64 wrap | unbounded DSL ints | in-range exact | overflow wrap NOT modeled |
| rust `if` expr | `IfThenElse` where pure | exact | mixed statement+tail branch refused (blocker) |
| lua `/` | `Div` (true division) | **exact** (both always float-style) | — |
| lua `//` | `IDiv` | positives exact | negatives differ (lua floors `-7//2=-4`, hub truncates `-3`) — fixtures avoid |
| lua `%` | `Mod` | **exact** (both floor) | — |
| lua `^` | `Pow` | value-exact on int fixtures | lua `^` is always float (`2^3=8.0`), hub int on ints — fixtures avoid `^` |
| lua `and`/`or` | `And`/`Or` | boolean contexts exact | lua returns an OPERAND (`x and y` = `y` when x truthy), hub returns bool — sound in boolean contexts only; fixtures comply |
| lua `..` | `ProgFString(l, r)` | ints + strings exact (`py_str(1)='1'`) | extreme float spellings can drift (lua %.14g vs py_str repr) — fixtures use ints/strings |
| lua `t[i]` | `ProgSubscript(obj, i-1)` | array part exact | the shift is WRONG for map-part/string keys — those are blockers, not shifted |
| lua tables / rust Vec | `ProgContainerLit(list)` → `Value::Tuple` | element reads/writes exact (P1 lvalue rebuild) | no aliasing (P1 divergence), no lua nil-hole semantics |
| rust tail expr | desugared `ProgReturn` | exact | — (a unit-valued statement tail runs, returns nothing) |
| lua `repeat` | body ×2 + `While(Not c)` | exact for straight-line bodies | `break` inside → refused (blocker) |

In-frame integer discipline (the 2026-07-08 invariant): every number in
the emitted IR is an in-frame integer (indices, counts, the ±1 stop/index
shifts); the cross-frame maps themselves (the correspondence tables, the
comparator in the gates) are where the language semantics live.

## 4. The correspondence is graph data

Both seeds load via the Rust `load_seed_manifest` with **zero skipped
rules/reflexes** (the loader's warning channels — gated), landing one
`CorrespondenceRow` node per row: `{lang, cst_kind, op (operator guard),
emit: term|handler, term, plan (JSON field-plan), handler, note}`. The
walkers load THE SAME FILE (`ts_ingest.load_correspondence_rows`) — the
seed is the single source of truth, and the gate
`test_walker_table_comes_from_the_seed` pins that every handler a row
names is registered. `ts_ingest.install_correspondence_seed` installs the
rows into a live agent graph (idempotent by Seed id) for inspection /
future repair through the standing gap pipeline.

## 5. Fixture verification method (out-of-band, per the prereg)

Every pinned `(fixture, inputs) → expected` in the gate suite was executed
through the REAL toolchains present in this environment before being
pinned — `rustc` (with a generated `main` printing the call) and **both**
`lua5.4` and `luajit` (script + `print(call)`); driver:
scratchpad `verify_fixtures.py`, 2026-07-31. Full agreement; transcript:

```
rustc  max_of_two(7,3)→7   max_of_two(2,5)→5   sum_list(vec![1,2,3,4])→10
       count_matching(vec![1,2,2,3,2],2)→3     sum_range(5)→10
       while_countdown(6)→6  loop_break(4)→4   abs_diff(3,9)→6  abs_diff(9,3)→6
       vec_index()→16
lua5.4 = luajit:
       max_of_two(7,3)→7   max_of_two(2,5)→5   sum_list({1,2,3,4})→10
       count_matching({1,2,2,3,2},2)→3         while_countdown(6)→6
       repeat_until(4)→4   repeat_until(0)→1   concat('x','y')→x-y
       for_step(7)→16      for_step(6)→9       table_index()→20
       bool_and(2,3)→1     bool_and(2,-1)→0
```

ProgEval reproduces every value (the per-fixture gates assert it), and the
non-obvious edges were chosen deliberately: `for_step(6)→9` exercises the
inclusive-stop shift off the step grid; `repeat_until(0)→1` pins
repeat's execute-at-least-once; `table_index()→20` pins the 1-based
shift; `abs_diff` both orders pins the pure-`if` tail.

## 6. The cross-frame law (the headline gate)

Three triples — max-of-two, sum-of-list-loop, count-matching — written
natively in rust (fixtures), lua (fixtures) and python
(`domains/prog_ir_emit.emit_prog_ir`, the P2-Python track's emitter,
which had landed by run time and is used directly per the task order):
all three frames emit hub IR that ProgEval evaluates to the SAME result
on the same inputs (6 input points, incl. empty-match and single-element
cases). One program, three frames, one verdict — plan §2's frame doctrine,
measured.

## 7. Honest residuals (this track, still open)

- **Blocked reads file no gaps yet.** `{ok: False, blockers}` is returned
  and recorded on uploaded documents (`ir_blockers` attr), but nothing
  mints `SelfConcern`s from them; wiring residuals into the gap pipeline
  is P3+ work.
- **The fold runs in a Python walker, not in `run_rules`.** The
  correspondence TABLE is seed data, but the applier is the mechanical
  `TableWalker` (a cross-frame map, admissible per plan §5) — the
  rule-based bottom-up fold (the `ast_term_rules` engine path, extended
  to statement grain) is the recorded future migration, same as the
  python track's note.
- **Round-trip (parse → IR → render → parse → same IR) is NOT gated
  here**: rust/lua RENDERING at statement grain is P5; this track gates
  read-side determinism + execution parity instead (prereg §4's fixture
  round-trips need the P5 writers to exist).
- **Python-frame uploads** ingest the AstNode graph + register facts but
  do not emit hub IR in `_ingest_source` (the python emitter belongs to
  the sibling track's surface; wiring it into upload routing is a
  one-line follow-up once both tracks land).
- **`#x` on strings / lua string library**: `len` is declared-oracle only;
  string functions are externs that trap honestly.
- **Method calls** (`x.len()`, `t:m()`) read as recv-calls and trap
  `extern:unimplemented:<name>` even when declared — the P1 "no
  method-style native oracles" boundary, unchanged.

## 8. Files

- `domains/ts_ingest.py` — CST world adapter + shared table engine (NEW)
- `domains/prog_ir_rust.py`, `domains/prog_ir_lua.py` — handlers + read-outs (NEW)
- `seeds/rust_correspondence.json` (38 rows), `seeds/lua_correspondence.json`
  (36 rows) — the correspondence as seed data (NEW)
- `domains/file_ingest.py` — `source` kind + `_ingest_source` routing (EDIT)
- `tests/test_prog_read_rust_lua_migrated.py` — 62 gates (NEW)
- `tests/fixtures/prog_ir_read_rs_lua/{rust,lua}/` — 10 + 12 fixtures (NEW)

## 9. P2.5 (2026-07-31) — two §7 residuals CLOSED

- **§7 "Python-frame uploads … do not emit hub IR" — CLOSED.**
  `_ingest_source` now runs `domains/prog_ir_emit.emit_prog_ir` per
  TOP-LEVEL function of an uploaded `.py` and attaches ok reads exactly the
  way the rust/lua branch already did: reflected Term subgraph,
  `has_prog_ir` edge, `prog_name` attr, `n_ir_ok` counted; blocked
  functions feed the same `ir_blockers` aggregate. The one-line-ish
  follow-up recorded in §7, taken.
- **§7 "Blocked reads file no gaps yet" — CLOSED (graph decision, not
  Python).** The adapter records only FACTS
  (`domains/file_ingest._record_read_blocked`: `read_blocked=1.0`,
  `read_blockers="comma,joined,kinds"`, `frame="rust|lua|python"` on the
  ingested `UploadedDocument`, and per-function on a blocked python
  function's own code-root node). The DECISION is
  `seeds/prog_read_gap.json`'s `note_prog_read_gap` (depends_on
  gap_awareness — the same pattern: content-dedup Not-Exists guard,
  mint-once `prog_read_gap_noted`, single-anchor
  `agent -received-> m -has_attachment-> d` match): it mints
  `SelfConcern{kind:'prog_read', source:'implicit', status:'noted',
  content:'<frame> read blocked: <sorted blockers>'}` — entering the
  standing promote pipeline and the `_run_self_gaps` surfacing reader with
  zero new plumbing. Install is idempotent at source-ingest time
  (`_install_prog_read_gap_seed`, the `install_correspondence_seed` idiom,
  Seed/SeedSummary id check — a `load_all_seeds` boot already holds it; a
  lean upload-only agent gains it on first source ingest).
- **Gates:** `tests/test_prog_read_gap_migrated.py` — 5 passed (~6 s):
  two-function `.py` → the emittable one ProgEval-runs (42), the Lambda
  one carries `read_blocked` facts and files exactly one gap naming
  `Lambda`; same blocked file twice → ONE SelfConcern (content-dedup);
  blocked `.lua` (varargs) files a gap naming the frame; the gap surfaces
  through `reflective_faculty._run_self_gaps`; lean-agent install
  idempotence. Neighbors green at the same state:
  `test_prog_read_rust_lua_migrated` 62, `test_file_ingest` 2,
  `test_prog_read_python_migrated` 52, upload/attachment/gap suites
  (`test_upload_foveated_text_migrated`, `test_attachment_reply_migrated`,
  `test_gap_awareness_migrated`, `test_self_gaps_surfacing_migrated`) 24.
- **Honest residuals (still open):** rust/lua blocked reads record facts at
  the DOCUMENT grain only (`read_fn_node` returns no CST node id, so
  per-function `read_blocked` facts exist only on the python frame's
  func-root nodes); the gap content is the blocker-kind summary, not a
  per-construct source span; closing a `prog_read` gap (widening a
  correspondence seed / the emitter) remains human-gated work through the
  standing promote pipeline — the rule only FILES it.
