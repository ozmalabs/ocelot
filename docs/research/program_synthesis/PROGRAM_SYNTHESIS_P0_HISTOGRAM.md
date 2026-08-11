# PROGRAM SYNTHESIS P0 — the statement-shape histogram that picks the P1 IR variant set

**Date:** 2026-07-31
**Task:** PROGRAM_SYNTHESIS_PLAN.md §4 P0, part B — *"Measure the statement-shape
histogram over the corpus (which ast_type sequences block emission, ranked by
mass) — this data picks the IR variant set for P1; do not guess it."*
**Script:** `scripts/prog_ir_statement_histogram.py` (deterministic, stdlib-ast,
no network, no substrate boot).
**Data:** `results/prog_ir_histogram.json` (full per-feature masses, id lists for
the top-15 features/variants, the greedy curve, corpus scope).

## 1. Method

- **Corpus:** every `*.py` under `domains/` + `substrate/` (the
  `code_curriculum.scan_repo_functions` walk — sorted paths, parse-or-skip —
  widened per the P0 task to substrate/ and to EVERY
  `FunctionDef`/`AsyncFunctionDef`, nested functions and methods included).
  **9,522 functions over 683 files** (7,237 top-level; 1,777 methods; 508
  nested; 2 async; 0 syntax-error files).
- **"Would the current emitter take it" is MEASURED, not approximated:** the
  script imports and runs the REAL dispatch —
  `code_reading._single_return_value` → `AstTermEmitter.emit_term`, else
  `code_reading._multi_stmt_skeleton_and_kind` → `emit_let_chain` /
  `emit_accumulation` / `emit_branching_return` (exactly `_read_one`'s
  emission ladder, `held_leaves={}`, `range_bind=None` — `scan_repo_functions`'
  configuration), over `ast_to_term.ingest_ast` on a minimal mechanical graph
  container (same `add_node`/`add_edge`/`node`/`neighbours` contract; the
  container is bookkeeping — every decision is the imported real code).
- **Per function:** ordered statement shape (nested compounds recorded, e.g.
  `For[If[Return]]|Return`), statement-type multiset, the expression-level
  blocker features (Call classified builtin/attribute/name, Attribute,
  Subscript, Lambda, comprehensions by kind, f-strings, With/Try/Raise/While,
  Global/Nonlocal, Yield/Await, star-args, kwargs, default args, decorators,
  methods/self), and the set of candidate IR variants its FULL subtree
  requires (candidates per the plan's P1 list, extended by what the corpus
  forces: `TupleUnpack`, `AttrSet`, `SubscriptSet`, `IfStmt`, `LoopCtl`,
  `ContainerLit`, `OpExt`, `IsOp`, …).
- **Greedy curve:** start from current-emitter coverage; repeatedly add the
  candidate variant that unlocks the most additional functions (a function
  unlocks only when its ENTIRE required set is chosen; tie-break by
  missing-set mass, then name); recompute; repeat.

**Cross-checks.** (a) The real-emitter check reproduces the frozen baseline
EXACTLY: over domains/ top-level functions it finds **27 emittable** — the same
count the curriculum run froze (`results/code_synthesis_baseline.json` owns the
id list). (b) Corpus-wide the current emitter takes **49/9,522 = 0.51%**
(48 single_return + 1 let_chain) — the statement wall, re-measured on today's
tree. (c) The domains/ top-level population has grown since the curriculum run
(7,185 now vs 6,252 then — the tree grew; emittable did not move).
**Determinism:** the script was run twice; `results/prog_ir_histogram.json` was
**byte-identical** across runs (sha256
`4a58c1e2…5461b93`, verified with `cmp`).

## 2. What blocks emission (ranked by function mass)

A function counts toward every feature it uses. Top of the table
(full ranking + id lists in the JSON):

| feature | functions | of 9,522 |
|---|---|---|
| attribute_load | 7,418 | 77.9% |
| multi_statement_body | 7,200 | 75.6% |
| call_attribute (method calls) | 7,142 | 75.0% |
| assign | 6,777 | 71.2% |
| container_literal (list/tuple/set/dict display) | 6,070 | 63.7% |
| call_builtin | 5,729 | 60.2% |
| if_stmt | 4,997 | 52.5% |
| call_name (local/imported function) | 4,541 | 47.7% |
| subscript_load | 4,300 | 45.2% |
| expr_stmt (bare call statement) | 3,667 | 38.5% |
| for_loop | 3,647 | 38.3% |
| tuple_unpack_target | 2,359 | 24.8% |
| is_comparison (`is None` etc.) | 2,309 | 24.2% |
| default_args | 2,288 | 24.0% |
| kwargs_call | 2,093 | 22.0% |

**91.3% of all functions contain at least one Call** (8,689/9,522) — the single
widest fact in the corpus. **Sole-blocker mass is nearly zero** (Return: 3,
Seq: 3 — bare-`return` and pure-statement-sequence bodies): almost no real
function is one variant away from emittable. Coverage comes from SETS of
variants landing together, which is why the greedy curve, not any single
feature's mass, picks the P1 set.

## 3. The greedy cumulative-coverage curve

Baseline = 0.51% (current emitter). ✗ marks variants that are
IR-**representable** but NOT ProgEval-**predictable** as such (§4).

| step | variant added | newly unlocked | cumulative |
|---|---|---|---|
| 1 | Return | +3 | 0.55% |
| 2 | ContainerLit | +486 | 5.65% |
| 3 | CallExtern ✗ | +278 | 8.57% |
| 4 | AttrGet | +432 | 13.11% |
| 5 | DefFnParam | +209 | 15.30% |
| 6 | Subscript | +103 | 16.38% |
| 7 | ComprehensionList | +135 | 17.80% |
| 8 | Seq | +84 | 18.68% |
| 9 | AssignVar | +568 | 24.65% |
| 10 | IfStmt | +415 | 29.01% |
| 11 | ForEach | +538 | 34.66% |
| 12 | TupleUnpack | +450 | 39.38% |
| 13 | IsOp ✗ | +580 | 45.47% |
| 14 | SubscriptSet | +352 | 49.17% |
| 15 | LoopCtl | +382 | 53.18% |
| 16 | TryOr | +415 | 57.54% |
| 17 | ImportStmt ✗ | +473 | **62.51%** |
| 18 | FString | +455 | 67.29% |
| 19 | ComprehensionGen | +500 | **72.54%** |
| 20 | AugAssign | +382 | 76.55% |
| 21 | AttrSet | +377 | **80.51%** |
| 22–36 | ComprehensionDict, Lambda, DefFn, Raise, ComprehensionSet, OpExt, While, With ✗, Decorator ✗, GlobalNonlocal ✗, Yield ✗, Delete ✗, Assert, Await ✗, ClassDef ✗ | +1,856 | 100.00% |

Never-unlockable under the candidate set: **0 functions**.

## 4. Recommended P1 variant set

- **60% mark (62.51%, 17 variants):** `Return, ContainerLit, CallExtern,
  AttrGet, DefFnParam, Subscript, ComprehensionList, Seq, AssignVar, IfStmt,
  ForEach, TupleUnpack, IsOp, SubscriptSet, LoopCtl, TryOr, ImportStmt`.
- **70% mark (72.54%, +2):** the above + `FString, ComprehensionGen`.
- **80% mark (80.51%, +2):** the above + `AugAssign, AttrSet`.

**Recommendation: the 70% set (19 variants) as the P1 target, with `AugAssign`
+ `AttrSet` (the 80% pair) included since both are trivial siblings of variants
already in the set** — i.e. 21 variants for 80.5% IR-representability. Notes
against the plan's expected list (`Seq, AssignVar, AugAssign, While, ForEach,
TryOr, Raise, Return, DefFn/Param, CallExtern, Subscript, AttrGet, …`):

- The corpus FORCES five variants the plan's sketch did not name: **IfStmt**
  (general statement-`if`, 5,075 non-emittable functions — plausibly just
  `IfThenElse` over `Seq` blocks in ProgEval, but it must exist at statement
  grain), **TupleUnpack** (2,400), **ContainerLit** (6,100 — cheap: `Vec` /
  `Dict` / `SetT` values already exist in the DSL; the emitter just refuses the
  display syntax today), **SubscriptSet/AttrSet** (mutation, 1,215/501 — NOT
  the same op as the read-side `Subscript`/`AttrGet`), and **LoopCtl**
  (break/continue, 1,357).
- **While (177 unlocked, step 28) and Raise (192, step 25) are LOW-mass** on
  this corpus, despite headline billing in the plan — they stay in P1 only
  because they are semantically load-bearing for ProgEval (loops that
  terminate on a condition; honest trap surfacing), not because corpus mass
  demands them. That is an explicit deviation-with-reason, not histogram
  evidence.
- **IsOp** (`x is None` etc.: 2,344 non-emittable functions, 24.6%) was a deliberate emitter
  residual (identity ≠ value equality). The histogram says it cannot stay
  out of the IR; the P1 design must give it an honest representation (e.g.
  `IsNone` for the dominant `is None`/`is not None` idiom) rather than
  approximating it with `Eq`.
- **ImportStmt** (955 functions carry in-body imports) is representable as a
  statement node but is pure extern surface for evaluation.

## 5. "IR-representable" vs "ProgEval-predictable" — two separate claims

The curve above is a **representability** claim only: the IR can HOLD the
function as matchable/renderable graph data. It is NOT the claim that
`ProgEval` can PREDICT the function's output. Measured separation:

| mark | IR-representable | predictable-eligible (no gapped variant) |
|---|---|---|
| 60% set | 5,952 (62.5%) | 659 (6.9%) |
| 70% set | 6,907 (72.5%) | 710 (7.5%) |
| 80% set | 7,666 (80.5%) | 785 (8.2%) |
| ceiling (all variants) | 9,522 (100%) | 803 (8.4%) |

`CallExtern` alone gates 91.3% of the corpus: **unlocking it moves
representability by a factor of ~10 but moves prediction almost nothing** —
per §3.2 of the plan, `ProgEval` evaluates a `CallExtern` only against a
DECLARED oracle/held faculty and traps honestly on unknown externs. The
predictable fraction GROWS as extern declarations accumulate (each declared
oracle converts its callers), but that is P2+ work (teacher chain / declared
oracles), not an IR-variant question. The gapped set as measured here:
`CallExtern, With, ImportStmt, Yield, Await, ClassDef, Decorator,
GlobalNonlocal, IsOp, Match, Delete` (IsOp's `is None` reading is actually
evaluable if given first-class None-identity semantics — the 8.4% ceiling is
therefore slightly conservative).

## 6. Honest caveats

- **The variant map is an analyst's mapping, not measured emitter behaviour**
  (only the CURRENT-emitter verdict is measured against the real code). If P1
  implements a variant with narrower semantics than the map assumed (e.g.
  `TryOr` without `finally`, `ForEach` without `else`), realized coverage
  will be below the curve. The map is deliberately construct-complete so the
  curve is an upper bound for the listed variants.
- **Star-args/kwargs in calls are folded into `CallExtern`** (recorded
  separately as features: 2,093 kwargs-call, 44 star-args functions);
  defaults/`*args`/kw-only in SIGNATURES are `DefFnParam` (2,399). Decorators
  are their own variant (73 non-emittable functions), excluded from the
  def-shell claim.
- **Requirements include nested def/class subtrees** (representing the outer
  function honestly requires them); nested functions are also corpus members
  in their own right, so their constructs count twice by design ("a function
  counts toward every feature it uses").
- **Ordered-shape cardinality is real:** 4,601 distinct nested shapes; the
  single dominant shape is the bare `Return` (1,950 — the expression corridor
  the current emitter already lives in), followed by `Assign…|Return` chains.
  The JSON carries the top 50 with counts; the multiset table carries all.
- **Corpus drift:** domains/ top-level is 7,185 functions today vs 6,252 at
  the curriculum run — the 27-emittable cross-check matched exactly, but any
  percentage quoted against "the 6252 corpus" is against a smaller, older
  population. This histogram's population (9,522, scope enumerated in the
  JSON) is the one its own percentages are conditioned on.
- **Determinism:** two consecutive runs produced byte-identical JSON
  (`cmp` clean; sha256 `4a58c1e25c85f22bc05331d4e3e4c2109561c95f8fd08bdf460a30dfa5461b93`).
