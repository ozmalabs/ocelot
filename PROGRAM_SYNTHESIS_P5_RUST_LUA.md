# PROGRAM SYNTHESIS P5 (track B) — statement-grain RUST + LUA WRITING from the hub Program IR

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P5,
`PROGRAM_SYNTHESIS_PREREG.md` §7, and `PROGRAM_SYNTHESIS_P2_RUST_LUA.md`
(the readers these writers invert). The python renderer and LLVM emit are
sibling tracks.

**Gate suite:** `tests/test_render_rust_lua_migrated.py` — **47 passed
(~0.4 s**; rustc/lua5.4/luajit are subprocess world-I/O in the tests and are
that fast on this box; `--confcutdir=.` worktree-engine discipline).
Neighbors at the same state: `test_prog_read_rust_lua` 62,
`test_program_synthesis` 14, `test_code_synthesis_baseline` 11,
`test_teach_lua_renderer` 2, `test_prog_ir` 54, `test_prog_read_python` 52,
`test_prog_read_gap` 5, `test_prog_read_llvm` 19 (**219 passed**), plus the
legacy renderer suites (`test_renderer`, `test_graph_renderer`,
`test_renderer_variadic`, `test_prog_constructions`: 36 passed). No file
owned by another track was modified; `domains/prog_ir_rust.py` /
`prog_ir_lua.py` needed **no read-side fix** (one latent read defect was
found and worked around render-side — §6.1).

## 1. Architecture — the renderer IS graph data

```
hub Program IR (P1 Prog* + expression DSL, as Term-JSON)
  → domains/render_rust_lua.py pre-passes     PURE IR→IR rewrites: the P2
      (prep_rust / prep_lua)                  cross-frame maps run BACKWARDS
                                              (decl marks, 1-based shift
                                              strip, numeric-for stop strip,
                                              ipairs fold, repeat fold,
                                              Return(IfThenElse) split)
  → _add_ir                                   render-source Term subgraph in
                                              reflect.rs conventions + the
                                              pre-pass annotation attrs
  → Rust `Render` engine                      seeds/render_rust_statements
      (term.rs::render_source_node —          .json (29 RenderRules) /
       the SAME machinery as the taught       seeds/render_lua_statements
       expression renderers)                  .json (31 RenderRules);
                                              templates are Term subgraphs
                                              (Cat/Join/Slot/Render +
                                              IfThenElse/Eq/ToJsonString/
                                              TypeOf/AttrByName/Nth)
  → mechanical fn wrapper                     name + params (+ the rust
                                              type-annotation ladder, §3.1)
```

Every *decision the templates can express* lives in the graph (RenderRule
templates branching with `IfThenElse` over slot presence, scalar attrs,
child node types via `TypeOf`, child attrs via `AttrByName`). The Python
module is the same class of artifact as the P2 readers: a cross-frame map
(plan §5) — pre-passes are pure structural inverses of documented read-side
desugars; no conditional anywhere reads agent graph state.

Template-language findings worth keeping: **`ToJsonString` is a correct
type-aware literal speller for both frames** (true/false, 7, 2.0, `"s"` —
closing the old `seed_rust_renderer` integer-only `<n>i64` gap; bare ints
keep rustc's literal polymorphism so index positions infer `usize` for
free); optional fields (absent `orelse`/`recv`/`value`) bind as `None` and
branch on slot truthiness; `Lit None` inside a template is an honest
engine-level gap (poisons `Cat` → render returns None, never wrong source).

## 2. ROUND-TRIP LAW — measured result: byte-identical, zero deltas needed

For **every ok P2 fixture** (9 rust + 10 lua): read → IR → render →
tree-sitter re-read → **IR JSON byte-identical** (`json.dumps(...,
sort_keys=True)` equality) and param names preserved. The canonicalization
choices were made so that re-reads *restore the original IR exactly* rather
than drift:

### 2.1 Rust canonicalization ledger (form chosen → why it round-trips)

| IR / source form | rendered as | re-read gives |
|---|---|---|
| let vs assignment (read-side conflated into `ProgAssignVar`) | pre-pass `decl` mark on the PRE-ORDER FIRST assignment → `let mut x = v` / later `x = v` | first-assignment position = the original `let` position for read IR → identical |
| tail expression vs `return` | **explicit `return e;` always** (the pinned single form) | read-side desugars both to `ProgReturn` → identical |
| `loop` (read as `While(Lit true)`) | **`loop { .. }`** — the exact `rs_loop` inverse (template tests the cond child's `value` attr via `AttrByName`) | `While(Lit true)` — identical (and dodges the `bool_text` read defect, §6.1) |
| `else if` chains | `else ` + nested render (surface `else if c { }`) | nested `ProgIfStmt` — identical |
| array literal `[a, b]` | `vec![a, b]` | both read to `ProgContainerLit{list}` — identical |
| `a..=b` (read adds +1) | `(a..(b + 1))` exclusive form | `Plus[b, 1]` stop — identical |
| statement termination | `ProgSeq` joins with `;\n`, every block context appends `; }` | stray `;` = empty statements the reader skips — transparent |
| parens around every op/if/range | `(a + b)` etc. | `rs_unwrap_paren` — transparent (rustc `unused_parens` warns only) |
| pure if expression | `(if c { a } else { b })` | `IfThenElse` — identical |

### 2.2 Lua canonicalization ledger

| IR / source form | rendered as | re-read gives |
|---|---|---|
| local vs global assignment (conflated) | `decl` mark → `local x = v` at first assignment / plain later | both read to `ProgAssignVar` — identical |
| 1-based subscript (read stores `i - 1`) | pre-pass strips the `Minus[·,1]` → `t[i]`; a non-shifted index gets `+ 1` wrapped | the read re-applies `- 1` — identical (the cross-frame map, both directions) |
| numeric `for` (read: `range` with ±1-shifted stop) | pre-pass recovers the INCLUSIVE stop structurally (strip `Plus[X,1]` / `Minus[X,1]` by step sign) → `for i = a, b[, s] do` | the read re-shifts — identical (`for_step`'s off-grid stop included) |
| generic `for`/ipairs (read: counter+ForEach desugar) | pre-pass folds `[k=0, ForEach{body=[k+=1, rest]}]` back to `for k, v in ipairs(xs) do rest end` | the read re-desugars — identical |
| `repeat B until C` (read: `B; While(Not C){B}`) | pre-pass detects the duplicated body and renders `repeat B until C` | the read re-duplicates — identical |
| `elseif` | `else` + nested if (each with its own `end`) | the read folds `elseif` and `else{if}` to the SAME nested `ProgIfStmt` — identical |
| `#x` (read: `len` extern) | `#(x)` | `len` extern — identical |
| `..` (read: `ProgFString` pairs) | `(l .. r)` per pair | left-assoc pairs — identical |

Deltas that CAN occur (cross-frame renders only; never on the P2 fixture
round-trips): a cross-frame `ForEach` over a plain list renders as the
`for _, x in ipairs(..)` fallback and re-reads as the counter desugar; a lua
`ProgAugAssign` (cross-frame only — read IR holds AugAssign solely inside
the folded ipairs desugar) renders `x = (x op v)` and re-reads as
`ProgAssignVar`; an un-shaped numeric-for stop re-reads with an extra
`±1` pair. Each is enumerated here per the prereg; none is silent.

## 3. Toolchain truth (world I/O in tests, batched)

- **rustc** (one batch file, `-O`): all 9 compilable fixtures (extern_trap
  excluded — its callee is deliberately undeclared) run printing exactly the
  **P2-pinned expected outputs** (10 case rows: max_of_two×2, sum_list,
  count_matching, sum_range, while_countdown, loop_break, abs_diff×2,
  vec_index). Warnings only (`unused_parens`, `unused_mut` from the
  always-`let mut` choice) — never errors.
- **lua5.4 AND luajit** (one batch script each): all 13 pinned case rows
  match, including `repeat_until(0)→1` (execute-at-least-once),
  `for_step(6)→9` (inclusive-stop off the step grid), `table_index()→20`
  (the 1-based shift) and `concat→"x-y"`.

### 3.1 Rust type-annotation ladder (mechanical, documented per the task pin)

Param types come **verbatim from the P2 read-side annotations** when present
(`max_of_two(a: i64, b: i64)`, `sum_list(xs: Vec<i64>)`). Synthesized
programs (P4 — no annotations) default **i64**, except a param used as a
`ForEach` iterable or subscript object defaults **Vec<i64>**. Return type:
default **i64** when any valued `ProgReturn` exists (bool for comparison/
logic heads, `Vec<i64>` for container literals, `String`/`f64` for
str/float literals), none otherwise. A param the body reassigns renders
`mut ` (not exercised by any gate fixture — §6.5).

## 4. CROSS-FRAME HEADLINE — one graph program, three executable surfaces

The **P4-accepted** Programs (produced live by the unmodified synthesis
pipeline: `max_of_two` rung-1, `sum_of_list` lattice-spine) render to BOTH
frames, compile/run, and agree with **ProgEval** on held-out inputs
(`max_of_two(11,5)=11`, `max_of_two(-3,4)=4`, `sum_of_list([2,4,6,8,10])=30`):

```rust
fn max_of_two(a: i64, b: i64) -> i64 {          fn sum_of_list(items: Vec<i64>) -> i64 {
return (if (a > b) { a } else { b });           let mut acc = 0;
}                                               for x in items { acc += x; };
                                                return acc;
                                                }
```
```lua
function max_of_two(a, b)                       function sum_of_list(items)
if (a > b) then                                 local acc = 0
return a                                        for _, x in ipairs(items) do
else                                            acc = (acc + x)
return b                                        end
end                                             return acc
end                                             end
```

rustc, lua5.4 and luajit all print `11 / 4 / 30` — the ProgEval values.
(The lua `max_of_two` shows the `Return(IfThenElse)` → if-statement split:
lua has no if-expression, so the pre-pass splits at the statement grain —
semantics preserved, gate-verified.) With the sibling python track, that is
one graph-resident Program with three executable surfaces.

## 5. THE TEACH-LOOP FINDING (measured, the task's explicit question)

**Does the runtime render-gap → self-teacher → `install_render_rule` loop
carry statement-grain rules?** Measured answer: **partially — and the
boundary is exactly the spec grammar of `_spec_to_renderer_term`.**

- **Live gate (green):** on a fresh `WorldAdapter` with NO seeded renderer,
  the `while_countdown` fixture's statement IR converged through the REAL
  loop (`render_via_teach_loop` files `render_gap:<head> in lua` questions
  into the adapter's `_render_gaps` channel + Impasse nodes;
  `drain_all_taught_threads` absorbs the teacher's rule specs via the
  unchanged `install_render_rule`/`_spec_to_renderer_term`): 9 rules taught
  live — including the statement-grain **ProgSeq, ProgWhile, ProgAssignVar,
  ProgReturn** — all landing as graph-resident RenderRules on the Language
  node, and the taught renderer's output **runs under lua5.4** (prints 6).
  Statement grain through the same loop that taught the original
  expression-grain Lua renderer: the frame stays living proof the writer is
  pure graph data.
- **The measured delta:** `_spec_to_renderer_term` accepts only
  Cat/Lines/Surface/Slot/Render/Join/Nth/Let/Label/Lit/Var. The canonical
  statement templates need **IfThenElse** (optional `orelse`/`value`/`recv`
  slots, decl/repeat marks, op-symbol chains), **ToJsonString** (type-aware
  literals), **TypeOf/AttrByName/Eq** — all KeyError in the spec converter
  (gate-pinned). Those rules ship as seed data installed by
  `install_renderer`. Per-rule accounting lives in the seeds themselves:
  **rust 18/29 teachable, lua 23/31 teachable**, each teachable rule
  carrying its loop-format `teach_spec` twin and each TEACH DELTA noted
  inline (the taught twins are weaker: plain assignment instead of
  decl-aware `local`/`let mut`, valued-only return, while-only loop,
  int-faithful-only Lit — exactly the original precedent's weaknesses,
  now named).
- **Conclusion for the plan:** growing the teach loop to statement grain
  needs the spec grammar extended by four heads (IfThenElse, Eq,
  ToJsonString, Nth would cover everything shipped here except
  TypeOf/AttrByName's two uses) — an adapter-surface change deliberately
  NOT made in this track (`world_adapter.py` left untouched for the
  sibling).

## 6. Honest residuals

1. **Read-side `bool_text` defect found (not fixed — file ownership).**
   tree-sitter's `boolean_literal`/`true` nodes carry their text on a token
   CHILD, but `ts_ingest._leaf_value("bool_text")` reads the parent's
   (absent) text, so ANY re-read rust `true`/`false` literal comes back
   `Lit false`. Never exercised by the P2 fixtures (no rust bool literal).
   This track dodges it by rendering `While(Lit true)` as `loop` (the true
   `rs_loop` inverse); a rendered standalone rust bool literal is correct
   SOURCE but would mis-read on a round-trip. The fix belongs to the P2
   files (`ts_ingest.py`/`rust_correspondence.json`), both outside this
   track's ownership — recorded here as the found gap.
2. **Declared render gaps (the per-frame LIST, in the seed manifests since
   `results/` is outside this track's file ownership —
   `seeds/render_*_statements.json` `"render_gaps"`, gate-checked):**
   rust: Div (true division has no i64 surface), Pow, ProgFString,
   ProgTryOr, ProgRaise, ProgImportStmt, ProgAttrGet/Set, ProgTupleUnpack,
   ProgIsOp, comprehensions. lua: IfThenElse (expression position outside
   `Return` — the pre-pass splits only the return position), ProgTryOr,
   ProgRaise, ProgImportStmt, ProgAttrGet/Set, ProgTupleUnpack, ProgIsOp,
   comprehensions. Every one files a graph-resident Impasse
   (`render_gap:<head> in <lang>`, deduped) — gate-verified; wiring those
   Impasses into `SelfConcern` minting is the standing prog_read_gap
   pattern, not re-built here.
3. **Scope hazards of the `decl` mark (documented, not hit):** a variable
   whose FIRST assignment sits inside a nested block but is used outside
   would render a block-scoped `let mut`/`local` — read IR can't produce
   this (the original source compiled/ran, and first-assignment order
   mirrors the original declaration), synthesized IR could; it would fail
   the rustc/lua gate honestly, never silently.
4. **Value semantics / clone-first:** no borrow model (per plan §6.5); the
   fixture/headline subset never reuses a container after a move, so no
   `.clone()` is ever emitted (a clone would re-read as a blocked method
   call). A container reuse-after-move is a compile-level honest failure.
5. **`mut` params + non-literal rust subscript indices:** implemented
   (`mut ` prefix; bare index rendering relies on rustc `usize` inference)
   but not exercised by any gate fixture; a genuinely i64-pinned index
   variable would be a compile-level residual.
6. **Lua string literals** use JSON escaping — exact for the printable
   subset the fixtures use; exotic `\uXXXX` escapes are not lua syntax
   (recorded, not reached).
7. **The renderer language nodes are `rust`/`lua`** — co-installing on an
   agent that already holds the legacy integer-expression
   `seed_rust_renderer` rules would collide head-first-wins per head
   (`install_renderer` skips already-present heads, so whichever installed
   first wins); the gates use fresh substrates/adapters. Reconciling the
   two rust rule sets (retiring the `<n>i64` Lit rule) is follow-up work.

## 7. Files

- `seeds/render_rust_statements.json` — 29 RenderRules + gap list (NEW)
- `seeds/render_lua_statements.json` — 31 RenderRules + gap list (NEW)
- `domains/render_rust_lua.py` — installer, pre-passes, wrapper, teach-loop
  driver (NEW)
- `tests/test_render_rust_lua_migrated.py` — 47 gates (NEW)
- `PROGRAM_SYNTHESIS_P5_RUST_LUA.md` — this document (NEW)

## 8. Residual closure (P6-B, 2026-07-31)

**§6.1 (`bool_text` read defect) is CLOSED by the owner fix.**
`domains/ts_ingest.py`'s `bool_text` leaf reader now reads the node's FLAT
leaf text (`flat_text` — the identity on a genuine leaf) instead of the
parent's absent `text` attr, so rust `boolean_literal` (whose text rides on
a token CHILD) re-reads `true` as `Lit true`. `seeds/rust_correspondence.json`
needed no change (the row was correct; the reader was not). Gated in the
owning suite: `tests/test_prog_read_rust_lua_migrated.py::
test_rust_boolean_literal_reads_as_the_right_lit` (+ the `if true` branch
gate) — suite now 64 passed, the pre-existing 62 byte-unaffected. The
`loop`/`While(Lit true)` render decision above stands on its own merits;
a rendered standalone rust bool literal now also ROUND-TRIPS correctly.
Details: `PROGRAM_SYNTHESIS_P6_SELFIMPROVE.md` §4.
