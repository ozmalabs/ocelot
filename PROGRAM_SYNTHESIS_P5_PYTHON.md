# PROGRAM SYNTHESIS P5 — track A: python statement-grain rendering (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P5,
`PROGRAM_SYNTHESIS_PREREG.md` §7 (H5), `PROGRAM_SYNTHESIS_P1_NOTES.md` (the
IR variant set), `PROGRAM_SYNTHESIS_P2_PYTHON.md` (the reader this track
round-trips against), `PROGRAM_SYNTHESIS_P4B.md` (the accepted-Program
artifact this track reads off). Deliverables:
`seeds/render_python_statements.json` (42 RenderRule specs, pure graph
data), `domains/render_python.py` (builder + installer + mechanical render
walker), `tests/test_render_python_migrated.py` (52 gates, green, 0.24 s).

## 1. The indentation decision (the registered hard bit) — GRAPH-SIDE, measured

Both candidate mechanisms named in the task card were measured on the live
engine before a line of the rule set was authored.

**Chosen: indentation is threaded through the Render env as graph data.**
The Rust `Render` evaluator (`term.rs::render_source_node`) pushes a rule's
slot bindings onto the CALLER's env and evaluates the template there, so an
env binding made by an enclosing template is visible to every nested
statement render. The whole mechanism is three template idioms:

* the walker's single top-level `evaluate` binds `indent` (`""`, or a base
  prefix);
* block-introducing rules deepen it around their body render:
  `Let("indent", Cat(Slot("indent"), "    "), …)`;
* `ProgSeq` applies it per line: `Join` with separator
  `Cat("\n", Slot("indent"))`, first line unindented (the statement
  contract: the PLACING container prefixes the first line, so a statement
  composes identically at any depth).

Measured evidence (probe, then pinned by
`test_indentation_is_threaded_graph_side`): a for/if/for/assign nest renders
at columns 0/4/8/12, and re-rendering the same IR at a base indent shifts
every interior line uniformly — zero Python indent logic anywhere on the
path. The documented fallback (`code_writing._term_to_statements`'s Python
depth-walker) was **not needed**; the only scaffolding the walker performs
is the `write_function`-precedent header assembly (§2).

**The engine fact that shaped the rule set — env fall-through (measured
hazard).** The same shared env means an ABSENT optional slot on an inner
node falls through to an ENCLOSING render's same-named binding: measured
live, a nested `ProgIfStmt` with no `orelse` rendered the OUTER if's else
branch as its own. No engine change is allowed this wave (correctly — the
fall-through is what makes `indent` threading work), so the rule set
carries a **shadow discipline**: every child render goes through
`Let("__sh", Slot(field), Let(<each optional name>, Lit(None), Render(Var
"__sh")))` — the slot is read in the rule's own frame, then all
optional/variadic slot names (`orelse value exc handler default recv cond
args stmts items parts`) are shadowed with an explicit falsy None; a child
that has the slot re-binds it on top, one that lacks it sees the shadow.
Pure graph data, measured fixed (the probe's leak case now renders
correctly; the whole fixture battery is the regression).

## 2. What the Python walker does (and what it may not)

`render_program` (domains/render_python.py) does exactly the CODE-3
`write_function` scaffolding precedent, at IR grain:

* split the leading `ProgDefFnParam` prefix off the top-level `ProgSeq`
  (a mechanical takewhile — the IR's own documented layout);
* render EACH param surface via the graph (`ProgDefFnParam` rule:
  `name`/`name=<default rendered in-language>`), join with `", "`;
* emit `def <name>(…):`, the optional docstring line, and the body rendered
  by ONE graph call at base indent `"    "`.

Every expression and statement surface — operators, literals (`LitRepr`),
containers incl. the dict `k: v` pairing (a Fold whose accumulator carries
text + parity), f-strings (literal parts read RAW off the part node's own
`value` attr via `TypeOf`/`Attr`; expression parts render in-language inside
`{…}`), comprehensions, aug-assign op spelling (a nested-ITE map over the
ProgEval native op set) — is produced by the Rust engine from the
graph-resident templates. Python never assembles an expression.

Honest outcome contract: `{"ok": True, "source"}` |
`{"ok": False, "render_gaps": [...]}` (§4) |
`{"ok": False, "refusals": [...]}` (mechanical renderability validation:
f-string literals needing escapes, unknown aug op / container kind /
loop-ctl kind, malformed dict item list, params after body — refused by
name, never bent).

## 3. The canonicalization delta ledger (the round-trip law's allowed set)

`canonical_ir` (domains/render_python.py) is the DOCUMENTED comparison
form; the law is `canon(emit(render(ir))) == canon(ir)`, and a gate
(`test_canonicalization_does_not_conflate_distinct_programs`) pins that the
instrument does not erase semantics. The complete allowed-delta set:

| # | delta | why it exists (each is forced by a reader/writer asymmetry) |
|---|---|---|
| C1 | `null` ≡ absent key | the P1 reflect-dialect law, already established |
| C2 | ProgSeq flattening (a ProgSeq element directly in a ProgSeq.stmts list splices inline) | the emitter's statement-lift preludes (floordiv `__uN`) and multi-alias imports nest a Seq inside a Seq; the rendered text is flat, so re-reading cannot reproduce the nesting |
| C3 | `And`/`Or` fold to the emitter's own right-nested IfThenElse operand desugar | only chained comparisons emit a bare `And`; rendering it as `(a and b)` re-reads through the P2 BoolOp desugar. C3 maps both sides to the same tree — semantics-exact under ProgEval (the desugar IS the emitter's registered operand semantics) |
| C4 | `Neg(Lit k)` ≡ `Lit(-k)` (non-bool numerics) | Python's grammar has no negative literals (parse always yields `Neg(Lit)`); synthesized IR may carry `Lit(-k)` directly |
| C5 | variadic `Plus`/`Times` with >2 items left-fold into binary nests | parse-derived trees are always binary; a synthesized variadic renders as `(a + b + c)` which re-reads left-nested |

Nothing else is normalized. The gates additionally assert the extern-name
list survives the trip verbatim (`e2["externs"] == e1["externs"]`).

## 4. Render-gap honesty — the established convention, at IR grain

`render_gap_check` mirrors `WorldAdapter.render_in_graph`'s DFS precheck at
IR-JSON grain: any head with no RenderRule in the language is recorded as
`render_gap:<head> in <language>` on `agent._render_gaps` (the
`drain_all_taught_threads` teacher channel's exact question format) plus a
graph-resident `Impasse{reason:'render_gap', render_gap_head,
render_gap_lang, question}` node (deduped), and the walker returns the
structured refusal — not an exception, not silent None. Gated both ways:
withholding `ProgWhile` at install fires the full convention (exact node
attrs, dedup on re-render, other heads still render), and installing the
missing rule afterwards heals the SAME IR (`test_gap_heals_by_installing_
the_missing_rule` — the mechanical half of the render-gap → teach →
re-render loop; the teacher-driven half rides the existing
`_spec_to_renderer_term` / `drain_all_taught_threads` seam unchanged).

## 5. Round-trip + executable-equivalence results

All measured on the worktree engine with `--confcutdir=.` (the P1
worktree-engine discipline). Suite: **52 passed, 0.24 s** (budget 90 s).

| corpus | round-trip law | ast.parse | exec ≡ ProgEval (≡ CPython original) |
|---|---|---|---|
| P2 ok fixtures (12: arith_flow, attr_record, branchy, comp_pipeline, dotted_call, fstring_is, import_noop, loop_ctl, try_raise, undeclared_extern, unpack_containers, while_gcd) | 12/12 identical under §3 | 12/12 | 15/15 semantic input cases + the attr_record object-twin gate (dotted_call / undeclared_extern are round-trip-only: ProgEval honestly traps their undeclared externs — the P2 fact — so there is no value to compare) |
| P4-shape synthesized programs (6: double_it, abs_diff, sum_of_list, clamp, count_evens, negate_or_default — hand-built write-side IR, incl. ProgIsOp, comprehension-under-call, default params, aug-assign loop body) | 6/6 | 6/6 | 10/10 input cases |
| the REAL P4 accepted Program (max_of_two via the full seed-rule loop, rendered straight from the `Program{name, program}` node) | law holds on the accepted IR | ✓ | 3/3 held-out inputs, exec ≡ ProgEval over the accepted `ir_subgraph` |
| docstring variant | law holds (the emitter's docstring peel) | ✓ | — |

Variant coverage: the seed carries a rule for **all 23 P1 `Prog*` variants**
plus the P2 IR expression closure (`Lit Var Plus Minus Times Div Mod Pow Neg
Not Eq Lt Lte Gt Gte In IfThenElse And Or`) — 42 heads; the fixture+synth
corpus exercises every `Prog*` variant end-to-end (the P2 variant-span fact,
carried through render).

Determinism: rendering the same IR twice is byte-identical (gated).

Seed integrity: the seed file byte-equals `build_render_rules()` output
(gated), installation is idempotent per head (second install: 0 installed,
42 skipped), and `load_seed_manifest`/`load_all_seeds` tolerate the file
(measured: loads clean; the `render_rules` key is this module's manifest
extension — the native loader ignores it, `install_python_statement_
renderer` consumes it).

Neighbor suites on the same engine, after: `test_prog_ir` (54) +
`test_prog_read_python` (52) + `test_program_synthesis` (14) +
`test_code_synthesis_baseline` (11) + the three renderer suites
(`test_render` / `test_graph_renderer` / `test_renderer`) — **155 passed**,
zero regressions. No shared file was modified: this track added only the
seed, the module, the test file, and this document.

## 6. Honest residuals

1. **Legacy-renderer coexistence.** The installer is install-if-absent per
   head, so on an agent whose `python` Language already carries
   `seed_python_renderer`'s ~17 expression rules, those heads keep the
   legacy templates (first-rule-wins dispatch stays deterministic). The
   legacy `IfThenElse`/binary rules do NOT carry the shadow discipline —
   an optional-slot leak is possible through them in one shape (a
   `cond`-less comprehension nested under a ternary). This track's suites
   install on fresh substrates; unifying the two rule sets (replacing the
   legacy heads with the shadowed templates) is a follow-up that must
   re-gate the CODE-arc write path, not a silent swap here.
2. **`recv`-form canonicalization gap (synthesized-only).** A synthesized
   `ProgCallExtern{recv: Var x, name: m}` renders `x.m(…)`, which the
   reader (correctly, per its own P2 rule) re-emits as the DOTTED name form
   `"x.m"`. Parse-derived IR can never hit this (a Name-rooted receiver
   always goes dotted at emit), no gate corpus hits it, and the ledger (§3)
   deliberately does NOT paper over it — if a future synthesized program
   carries a Var-rooted recv, the law fails loudly and this residual is the
   named cause.
3. **Float spelling.** `LitRepr` uses Rust's shortest-round-trip f64
   display (`0.000000015`, not CPython's `1.5e-08`) — value-identical after
   `ast.parse` (both spell the same double), surface differs from CPython
   `repr`. The P1 `python_repr` residual (exotic control / non-ASCII string
   escaping not byte-CPython) also stands, unchanged.
4. **F-string escaping.** There is no graph-side string-replace primitive
   (and no Rust changes this wave), so f-string LITERAL parts containing
   `{ } " \` or newlines are refused by name
   (`fstring_literal_unspellable`), never mis-rendered. A rendered
   f-string whose EXPRESSION part contains a double-quoted string literal
   needs Python ≥ 3.12 (quote reuse) to re-parse; the toolchain here is
   3.14. Format specs / conversions never reach the renderer (P2 blocks
   them at read).
5. **`ProgTupleUnpack` renders the always-parenthesized target spelling**
   (`(a, b) = v`, `(a,) = v`) — parse-identical to the bare form, needed
   because 1-target unpacks require the comma the graph counts via `Count`.
6. **The seed is installed by the module, not the boot loader.** The
   `render_rules` manifest key parallels P4B's `reflexes` precedent before
   its native support landed; moving RenderRule installation into the
   native `load_seed_manifest` (or the teach path) is named future work.
   The file loads clean under `load_all_seeds` today (measured — no new
   entry in the failed list).
7. **Gap detection is the Python-side DFS precheck** (the render_in_graph
   convention verbatim); the engine's own None-on-gap remains the backstop
   (`body_render_none` in the walker's outcome vocabulary), so a gap can
   never yield partial source.
