# PROGRAM SYNTHESIS PLAN — the jabberwock produces arbitrary programs, graph-natively

**Date:** 2026-07-31
**Directive:** *"Create a plan to have the jabberwock be able to produce arbitrary
programs in a similar way to LLMs, in all the languages it currently supports.
It should be completely graph native wherever possible."*

**Status:** PLAN (no code in this commit). Written from a three-way sweep of the
tree at c3fd855d22: the CODE arc modules, the full Rust Term/rule-engine surface,
and the seed layer / sd loop / self-improvement pipeline.

---

## 0. Scope pin — "all the languages it currently supports"

The languages the agent supports **today**, measured, are:

| Language | Read (source → graph) | Write (graph → source) | Where |
|---|---|---|---|
| **Python** | YES — stdlib `ast` → `AstNode` graph (`domains/ast_to_term.py`) | YES — `code_writing.write_function`, `seed_python_renderer` (~17 RenderRules, `substrate/world_adapter.py:4795`) | the CODE-0…CURRICULUM arc |
| **Rust** | no | partial — integer expressions only (`seed_rust_renderer`, `world_adapter.py:4972`) | write-only |
| **x86-64 asm** | no | YES for expressions (AT&T/SysV, `seed_x86_64_renderer`, `world_adapter.py:5058`) + full Term→LLVM→asm→`.so` chain (`domains/term_jit.py`) | write-only |
| **Lua** | no | YES (taught at runtime as pure graph data — the render-gap → self-teacher loop, `tests/test_teach_lua_renderer_migrated.py`) | write-only |
| **LLVM IR** | YES (`domains/llvm_ir_io.py parse_llvm_ir`, single-block integer subset + CFG modules) | YES (`emit_llvm_ir`, passes, cost model, interp) | read+write |

So "all languages it currently supports" = **python, rust, lua, x86-64, LLVM IR**.
The plan makes all five arbitrary-program targets, with x86-64 served through the
LLVM chain (rendering arbitrary programs to asm via direct templates is the wrong
instrument; the compile chain already exists and is graph-inspectable).
The sibling ozma stack (tree-sitter ×18 languages at
`/home/matt/ozma/ozma-ai/ozmalib`, currently **zero** imports from this tree) is
the read-side lever for rust/lua and, later, for languages beyond this scope pin —
but new languages are explicitly OUT of scope for this plan.

---

## 1. Where we stand (analysis)

### 1.1 Assets already in the tree (everything below is landed and gated)

**The CODE arc** (CODE-0…CODE-CURRICULUM, all in `domains/`):
- `ast_to_term.py` (800) — Python source → typed `AstNode` graph (`child` edges
  carrying field role + index), mechanical, plus the fixed AST→Term emitter.
- `ast_term_rules.py` (588) — the AST→Term correspondence as **graph rewrite
  rules** (Constant→Lit, BinOp:Add→Plus, …); the Rust engine does the fold.
- `code_reading.py` (775) — skeleton → ShapeDecode over the READ codebook
  (`seeds/code_constructions.json`, 7 shapes) → construction → "what it does".
- `code_writing.py` (657) — Term-tree → real runnable `def` with docstring;
  every *expression* surface comes from the graph renderer; the round-trip law
  `write(read(f))` is gated (`write_read_function`, `self_consistency_check`).
- `code_write_growth.py` (492) — the agent grows its own WRITE codebook
  (`seeds/code_write_constructions.json`, 8 shapes + taught) by example and by
  predication; adoption gated on render+exec agreeing with `native.evaluate`.
- `code_curriculum.py` (391) + `scripts/code_curriculum_run.py` — mixed-register
  published lessons; capability self-report; gap filing.

**Synthesis engines that already exist (Python-resident — migration targets):**
- `domains/generator.py` — bottom-up enumerative synthesis over the DSL Term
  grammar, MDL-ordered, observational-equivalence pruning.
- `domains/cegis_faculty.py` — CEGIS: synthesize smallest recipe → construct a
  divergence → oracle-label → add row → re-synthesize.
- `domains/capability_compose.py` — synthesized Term-trees as graph-resident
  `Capability` nodes.

**Runtime machinery the design leans on (all Rust / graph):**
- 181 DSL Term variants (`runners/dsl/src/term.rs`), incl. the render family
  (`Render`/`RenderRule`/`Cat`/`Join`/`Lines`/`Slot`/`Let`/`LitRepr`) and the
  dynamic-quantization ladder (`ShapeDecode`/`TransformDecode`/`DimInfer`/
  `GenInfer` + `sd_*` rules in `seeds/shape_decode_loop.json` v1.8.0).
- Term ↔ subgraph reflection (`runners/dsl/src/reflect.rs`, `Term.*` node types,
  `child.<field>` edges) + `EvalSubgraph` + `Program{name, program}` nodes
  (14 seeded Programs; `teach_program` persists new ones).
- The Viterbi lattice as **pure seed rules** (`seeds/viterbi_decode.json`:
  `vit_step`/`vit_backtrace` over `Hyp`/`LatEdge`/`Lattice`) — grain-agnostic,
  already reused for speech and ink (`domains/ink_decode.py`).
- Γ productions with weighted selection **∝ exp(w)** (`runners/dsl/src/grammar.rs`)
  — a native softmax over admissible continuations.
- The render-gap → self-teacher → `install_render_rule` loop (the Lua precedent)
  and the gap pipeline (`seeds/code_write_gap.json`, SelfConcern → StandingConcern
  → Experiment → judge → adopt).
- `seeds/generated/` — the landing zone for agent-authored seeds, loaded after
  the curated set.

### 1.2 The measured gaps (from `results/code_curriculum/` + the sweeps)

1. **Statement coverage is the wall.** Construction *recognition* is 6113/6252
   (97.8%) on the real `domains/` corpus, but Term *emission* is 27/6252
   (**0.43%**) and did not move at all across the whole curriculum run. The
   emitter's scope is: single pure-expression Return, Let-chains, one
   accumulation-fold shape. No while, no try, no multi-branch statements, no
   subscript/attribute evaluation, `Call` only to held leaves.
2. **Reading is Python-only.** No tree-sitter anywhere in the tree; `.py`/`.rs`/
   `.lua` are not even in `file_ingest._TEXT_EXTENSIONS`. Rust/lua/x86-64 are
   write-only frames.
3. **The DSL cannot make new names.** `evaluate()` holds `&Interner` — no
   interning path, so `StringConcat`/slices return `Surface(Text)`, and there is
   no case/replace/format/split primitive. Identifier synthesis (the thing LLMs
   do casually) currently has no graph-native path.
4. **Minted construction names are unbounded concatenations**
   (`learned_code_importfrom_importfrom_…_return`) — no abstraction step; 24 such
   quanta piled up in one run.
5. **`looks_like_write_request` has real false positives** on lesson prose (3 of
   4 "exercise requests" in the run were not requests).
6. **No corpus-derived sequence statistics for code.** The trigram-lattice
   precedent exists for words (`scripts/jabberwock_trigram_lattice.py`) but
   nothing plays the role of "next-construction distribution" for programs.

---

## 2. The design — what "like an LLM" maps to here

The point is not to imitate token-sampling; it is to supply the same functional
loop with graph-native parts. The correspondence, explicitly:

| LLM | Jabberwock (this plan) |
|---|---|
| token vocabulary | **construction quanta** — `ShapeSignature{kind:'code_*'}` codebook entries over the Program IR, grown by the sd loop (mint on residual, re-decode on epoch bump) |
| training on corpora | **corpus reading**: parse repos → IR graphs → sd-loop decode → mint/merge construction quanta + earn transition counts (the distributional-attrs precedent: `freq_norm`, `ctx_entropy_norm`) |
| next-token distribution | **lattice scores**: `Hyp`/`LatEdge` over candidate construction sequences with corpus-earned `trans_logp`, decoded by the unchanged `vit_step`/`vit_backtrace`; and Γ production weights (selection ∝ exp(w)) for surface grammar |
| context window | the graph itself: the `Goal`, the spec facts, retrieved held Programs (`memory_recall_by_shape`) |
| decoding / sampling | `Argmax`/`ArgminRefusal` collapse over the lattice; beam = `ShapeDecode{beam,cand_k}` |
| "the model writes code" | **propose–render–verify (AbS)**: constructions propose a Term/IR tree; per-language RenderRules render it; the verdict is execution/round-trip — "**constructions propose, execution decides**" (the run-16 synthesis, applied to code) |
| RLHF / self-correction | the standing gap pipeline: failed generation files `SelfConcern{kind:'code_write'}` → experiment → adopt; render gaps heal via the self-teacher loop (Lua precedent) |

**The frame doctrine applies cleanly and should be stated as the architecture:**
each surface language (python, rust, lua, LLVM IR, x86-64) is a **frame**. The
program lives once, as a language-neutral IR subgraph (the hub). Parsers and
renderers are **cross-frame maps** — exactly where the 2026-07-08 invariant says
the non-graph machinery (tree-sitter, `ast`, compilers, formatters) is allowed to
live. Porting python→rust is not a new capability; it is the same program quantum
read out in a different frame. In-frame structure (arity, child index, statement
count) stays integer; the continuous stuff (execution timings, similarity scores
used as verdicts) stays in the maps.

**The core generation loop (one `run_rules` fixpoint + adapter I/O at the rim):**

```
NL request / examples / spec
  → (adapter: mechanical parse facts onto Message; write-request cue rules decide it IS a request)
  → Goal{kind: write_program, spec facts as graph}
  → PROPOSE:  ShapeDecode over the write codebook composes a construction plan;
              for multi-statement bodies, a Hyp/LatEdge lattice over candidate
              construction sequences scored by corpus-earned trans_logp;
              vit_step/vit_backtrace pick the spine (rules, not Python)
  → BUILD:    the winning plan instantiates a Program-IR subgraph (Term.*/Prog.*
              nodes); slot binding from spec facts; identifier synthesis via the
              new naming primitives
  → RENDER:   Render + per-language RenderRule sets → source text per target frame
  → VERIFY:   (a) round-trip: parse the rendered source back, compare IR
              (write(read(f)) — the law already gated for Python);
              (b) execute: ProgEval (new, §3.2) on sample inputs vs. the spec /
              CEGIS counterexample rows; external toolchain runs are adapter I/O,
              their results written back as nodes for the judge RULES to read
  → on residual: sd loop mints a construction quantum / files a code_write gap
    (dedup by anti-unification, §4 P3); epoch bump re-arms decode
```

Everything that *decides* in that loop is a rule or a Rust Term. Python only:
file/process I/O (read a repo, invoke `rustc`/`python`/`luajit` sandboxed, write
outcome nodes) and the seed/Term builders that emit graph data — both explicitly
admissible under CLAUDE.md.

---

## 3. Architecture decisions (the three that matter)

### 3.1 The Program IR is the Term subgraph, extended — not a second reflection stack

Programs are already graph-resident twice (AstNode graphs on the read side,
Term-JSON strings in `Program` nodes on the write side). The plan unifies on the
**reflected Term subgraph** (`Term.*` nodes, `child.<field>` edges — reflect.rs)
as the single hub IR, and *retires Term-JSON-string attrs* for new work (they are
opaque to rules; a subgraph is matchable, decodable, and repairable by the agent —
"self-repair ⟺ graph-native").

`AstNode` graphs remain as the **python-frame parse artifact**; the
`ast_term_rules.py` correspondence rules (extended, §4 P2) fold them into hub IR.
Non-python frames get their own mechanical parse artifact → correspondence-rule
fold into the same hub IR.

### 3.2 Statement semantics live in ONE new Rust Term: `ProgEval` — the DSL stays pure

The DSL is a pure expression language and must stay one (the purity is what makes
`where`-clauses, probing, and undo sound). Arbitrary programs need statements:
sequencing, mutation, while, try, calls. Resolution: statements are **data**
(new `Term.Seq` / `Term.AssignVar` / `Term.While` / `Term.TryOr` /
`Term.CallExtern` / `Term.DefFn` IR variants that the evaluator does NOT execute
directly), and execution is **one pure Rust Term**:

```
ProgEval{prog: <IR subgraph root>, env: <Dict>, fuel: <Int>, field}
   → Dict{result, env_out, steps, halted, trap}
```

— a fueled interpreter, `Dict in → Dict out`, no substrate mutation, honest
`halted:false` on fuel exhaustion (the in-frame integer: fuel is the stepped
observation of the unbounded axis; never "run to completion"). This is the
prediction oracle for CODE-2-style understanding *and* the cheap verdict layer
for generation, and it follows the established pattern (ShapeDecode, DimInfer:
big engine in its own module, Dict-with-field out, py.rs one-line handoff).
`CallExtern` evaluates only against declared oracles/held faculties; unknown
externs trap honestly — an extern's semantics is a *knowledge* gap that heals via
the teacher chain, not a reason to shell out mid-eval.

### 3.3 Surface grammar per language = RenderRules for writing, correspondence rules for reading, Γ-weighted where generative choice exists

No hand-rolled per-language grammar interpreter. Writing stays on the proven
`Render`/`RenderRule` path (grown to statement grain, §4 P5). Reading goes
parse-artifact → correspondence rules (the `ast_term_rules` pattern, one table
per frame, shipped as seeds so the agent can inspect/vary/repair them). Where the
renderer has a genuine choice (idiom variants, statement vs. expression forms),
the alternatives are Γ productions whose weights are corpus-earned — the native
exp(w) selection is the temperature knob, as data.

---

## 4. Phases

Ordering is Occam/bottleneck order: the measured wall is statement coverage, so
the IR + interpreter come first; corpus statistics and multi-language reading are
worthless until there is an IR that can hold what they parse.

### P0 — Prereg + enumerated baseline (small; do first, per standing rules)
- `PROGRAM_SYNTHESIS_PREREG.md`: hypotheses, gates, protected controls.
- Freeze the current write battery (21/26) and the Term-emittable **list** (the
  27 node ids, not the count) as `results/code_synthesis_baseline.json`, gated by
  a `tests/test_code_synthesis_baseline_migrated.py` (a baseline must be a list,
  never a count — the 2026-07-21 retraction rule).
- Measure the statement-shape histogram over the 6252-function corpus (which
  `ast_type` sequences block emission, ranked by mass) — this **data picks the IR
  variant set** for P1; do not guess it.
- Gate: baseline test green; histogram in results/.

### P1 — Hub IR + `ProgEval` (Rust; the enabling primitive)
- Add the statement IR variants chosen by P0's histogram (expected: `Seq`,
  `AssignVar`, `AugAssign`, `While`, `ForEach`, `TryOr`, `Raise`, `Return`,
  `DefFn`/`Param`, `CallExtern`, `Subscript`, `AttrGet` — cut to what the
  histogram justifies; each variant must clear "does real corpus mass need it").
- `ProgEval` per §3.2 (`runners/dsl/src/prog_eval.rs`, py.rs one-liner).
- Naming primitives (the §1.2-3 gap): the minimal set to synthesize identifiers —
  an interning-capable path for eval-produced strings (or blessing
  `Surface(Text)` end-to-end through `RenderRule` templates + attr writes), plus
  `CaseFold`/`SnakeCase`-grade transforms. Smallest set that lets a rule name a
  variable from spec words; no regex engine.
- Gates: round-trip `reflect` law for every new variant; `ProgEval` vs. CPython
  agreement on a fixture corpus (the `validate_written_function_by_running`
  pattern, inverted); fuel honesty test.

### P2 — Reading: all five frames → hub IR
- **Python:** extend `ast_term_rules.py` CORRESPONDENCE to the P1 variant set.
  Target is set by P0's histogram, prereg'd (e.g. ≥60% of corpus functions fully
  IR-emittable; the number comes from the histogram's cumulative mass curve, not
  ambition). `Call` → `CallExtern` with declared-oracle binding where held.
- **Rust + Lua:** mechanical parse via tree-sitter as **adapter I/O** (dependency
  choice: import `ozmalib`'s tree-sitter wrapper vs. direct `tree-sitter`
  bindings — decide by what keeps gamma-substrate's build hermetic; the sweep
  found ozmalib is a *different repo*, so vendoring the two grammars directly is
  the likely answer). CST → hub IR via per-frame correspondence-rule seeds
  (`seeds/rust_correspondence.json`, `seeds/lua_correspondence.json`) — scoped to
  the same construction families Python covers; everything else is an honest
  parse residual node, countable, filed as gaps.
- **LLVM IR:** lift `parse_llvm_ir`'s output into hub IR (it is already
  graph-shaped; this is a correspondence-rule seed, not new parsing).
- Add source extensions to `file_ingest._TEXT_EXTENSIONS` + route through the
  existing `register_source` code-register detection so uploaded source files
  actually ingest.
- Gates: per-frame round-trip on fixtures (parse → IR → render → parse → same
  IR); per-frame coverage list (node ids of unparseable constructs, not counts).

### P3 — The codebook + corpus statistics (the "training run")
- Point the **unchanged sd loop** at IR observations: a scanned function becomes
  an `Observation{signature}` over its IR relation-system; `sd_recognize` /
  `sd_transform_decode` / `sd_mint_quantum` grow `ShapeSignature{kind:
  'code_construction_v2'}` quanta. Composition across levels (expression →
  statement → block → function → module) is the character-composition precedent
  (+21pp there; arrangement is the signal) — same loop, one level up per rung.
- **Fix minting-name unboundedness before the big scan:** merge-by-anti-unification
  at mint time (`AntiUnify` the residual against existing induced quanta; join
  instead of mint when the LGG is within an MDL bound), and name from the
  dominant `(predicate, role)` pair — a rule, not a Python namer. This is a
  precondition, or the scan mints thousands of concatenated names.
- Earn **transition statistics**: per ordered construction pair within a block,
  count → `trans_logp` attrs on `ConstructionBigram` nodes (the distributional-
  attrs precedent: adapter does the arithmetic mechanically during the scan; the
  agent authors/holds the rules that read them). Same for Γ idiom-variant weights.
- Corpus: this repo's own `domains/` + `substrate/` + fixtures (already the scan
  corpus), rendered-rust/lua fixtures, and — deliberately second — external repos
  via upload. Scale is a knob, not a gate.
- Gates: mint-dedup test (same shape twice → one quantum); scan determinism on
  the fixture corpus; codebook size vs. coverage curve recorded (no silent caps).

### P4 — Generation: propose–render–verify as seed rules (the LLM-analog loop)
- `seeds/program_synthesis.json`: the loop of §2 as rules —
  `ps_goal_from_request` (consumes the write-request decision the existing cue
  rules already make; tighten `looks_like_write_request` precision by moving the
  decision fully onto cue+parse rules, killing the §1.2-5 false positives),
  `ps_propose` (ShapeDecode plan over the write codebook),
  `ps_lattice_build` / reuse `vit_step`/`vit_backtrace` (sequence spine over
  construction candidates scored by P3's `trans_logp`),
  `ps_bind_slots` (spec facts → IR slot values, naming primitives for identifiers),
  `ps_render` (per-target Render), `ps_verdict_roundtrip`, `ps_verdict_exec`
  (reads `ProgEval` result nodes + adapter-written toolchain outcome nodes),
  `ps_accept` / `ps_counterexample` (CEGIS row as a node; re-propose excludes the
  failed plan — the CEGIS loop as rules, retiring `cegis_faculty.py`'s Python
  iteration for this path), `ps_residual_gap` (files `SelfConcern{code_write}`).
- Migrate `generator.py`'s enumerative search into a Rust `SynthEnumerate` Term
  (MDL-ordered, observational-equivalence pruning, budgeted) callable from
  `ps_propose`'s fallback rung — Occam ladder: codebook compose first, transform
  second, enumerate third, gap-file last (mirrors sd rungs).
- The adapter's only new verbs: write spec/example facts, run sandboxed
  toolchains and write outcome nodes, read off the accepted render. No branching.
- Gates: the **powered battery** (see P6); end-to-end fixpoint gate (request →
  exactly one accepted Program node + rendered source per target, no Python
  decisions — the ink-suite source-audit test pattern).

### P5 — Rendering completeness per frame
- Python: statement-grain RenderRules for every P1 variant (grow from the ~17).
- Rust: floats/bools/strings, statements, `fn` items, `match`→`IfThenElse`
  chains; ownership-safe subset only — what the IR can honestly mean, nothing
  speculative; everything else is a render gap that files.
- Lua: statement grain via the SAME taught-at-runtime path where possible — the
  self-teacher supplies templates, `install_render_rule` installs; this keeps the
  Lua frame as the living proof that a frame's writer is pure graph data.
- LLVM IR: extend `emit_llvm_ir` coverage to the IR statement set (branches,
  loops via CFG blocks — `llvm_ir_cfg.py` exists); x86-64 = IR → existing
  cfg_to_asm chain. No direct statement templates for asm.
- Render gaps file `SelfConcern` and heal via the teacher loop — this phase is
  deliberately *self-extending* rather than exhaustively hand-seeded.
- Gates: per-frame round-trip suite green on the P2 fixtures; render-gap →
  teach → re-render live test per frame.

### P6 — Powered evaluation + self-improvement wiring (the endgame gate)
- Battery: N≥100 tasks × {python, rust, lua, llvm-ir} (x86-64 scored via the
  chain), stratified: expression / single-statement / loop / error-handling /
  multi-function; each task = NL request + examples; score = verdict-layer pass
  (executes correctly) with Wilson CIs. **Protected controls:** the frozen P0
  battery arm and a codebook-frozen arm (no minting) — so "training helped" is a
  CI-separated claim, not narrative. Power the gate before the endgame — deltas
  within ~3× the per-episode step are not results.
- Wire the loop into the standing pipeline end-to-end: failed tasks → gaps →
  (human-gated) StandingConcern → experiment/adopt on the synthesis rules
  themselves; agent-authored construction seeds land in `seeds/generated/`.
- Ship the capability self-report ("what can you write?") through the existing
  `code_capabilities` dispatch, buckets by provenance.

### Explicit non-goals (this plan)
- New languages beyond the five (tree-sitter makes it cheap later; not now).
- LLM-in-the-loop authoring (`code_writing_cortex.py` stays a separate,
  already-landed facility; this plan is the native path).
- Whole-repo refactoring / editing existing codebases (generation of new
  programs only; editing is a follow-on that reuses the same IR).
- Byte-perfect style mimicry (formatters are cross-frame maps; adopt one per
  frame as adapter I/O if gates need it).

---

## 5. What stays Python, and why that's admissible

| Piece | Why it's legal |
|---|---|
| tree-sitter / `ast` / `parse_llvm_ir` invocation | mechanical translation of an opaque external form into graph nodes — the ChatWorld tokenizer, at code scale |
| sandboxed toolchain runs (`python`, `rustc`, `luajit`, `llc`) + outcome nodes | world I/O; the *decision* to accept reads those nodes in rules |
| correspondence/RenderRule/seed **builders** | emit graph data only (the `_compose_*_rule` precedent) |
| the corpus-scan driver | ingest loop + mechanical counting into attrs (the distributional-stats precedent) |

Everything else — proposal, sequencing, binding, verdict, growth, gap-filing —
is rules + Rust Terms. The self-repair boundary lands exactly where the directive
wants it: the whole synthesis loop becomes graph the agent can see, vary,
experiment on, and adopt.

## 6. Risks / open questions (honest)

1. **IR variant creep.** The pressure to add "one more statement kind" is
   unbounded; the P0 histogram + per-variant corpus-mass justification is the
   governor. Anything below threshold stays a parse residual + gap.
2. **`CallExtern` semantics.** Most real code calls libraries. `ProgEval` traps
   honestly, and the verdict layer falls back to sandboxed execution (adapter
   I/O) — but *prediction*-grade understanding of extern-heavy code will lag;
   that is the same honest wall CODE-2 already drew, now countable.
3. **Interner mutation** (naming primitives) touches an invariant
   (`EvalCtx::interner` is `&Interner` by design). If a clean interning path
   isn't safe, the fallback is Surface(Text)-everywhere for synthesized names —
   uglier, no soundness cost. Decide in P1 with the Rust surface in front of us.
4. **Scan scale.** 6k functions is fine; external corpora will need the foveated
   reading discipline (budgeted spans) or the scan becomes the bigville of this
   arc. Scale is a knob; the gates never depend on corpus size.
5. **Rust ownership.** The write-side subset must be chosen so rendered programs
   compile without a borrow-checker model in the IR (value semantics + clones
   first). A borrow model is real future work, not a P5 line item.
6. **Naming/abstraction of minted quanta** (P3's anti-unify merge) is a design
   the sd loop hasn't needed before at this volume; it needs its own small
   prereg before the big scan.

## 7. Compliance notes (standing rules this plan is written under)

- Baselines are **lists of node ids** (P0), never counts or characterisations.
- Every mechanism gate carries a protected control; the endgame gate is powered
  (Wilson CIs, n≥100/arm) before any headline number is quoted.
- Synthetic-proven mechanism ≠ benchmark value; both get reported.
- Eval-subset coverage (which languages, which strata) is part of every claim.
- No Python agent decisions: each phase lands with a source-audit test on its
  adapter surface (the ink-suite precedent).
- In-frame integer / cross-frame continuous: fuel, indices, arity, counts are
  integers in the IR; similarity scores, timings, and toolchain verdicts live in
  the maps (comparators), never as IR coordinates.
