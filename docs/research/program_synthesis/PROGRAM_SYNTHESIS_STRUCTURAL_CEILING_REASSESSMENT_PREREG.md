# Re-assessing the MBPP structural ceiling against SHAPES-NOT-NUMBERS — PREREG

Base `main @ 1480d48` ("Merge problem-decomposition: race coupling-graph
guesses, decompose-or-refuse, GO"), verified via `git log --oneline -1 main`
before writing this document (the working tree carries unrelated in-flight
`bigville_*` modifications; none of the files this document reads or
discusses are among them). This is a **PREREG-ONLY / INVESTIGATION-ONLY
task**: no implementation code, no seed JSON, no tests, no worktree/branch.
Per the task's own instruction this document is the checkpoint the user
reviews before anything below it gets built, mirroring
`docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`'s
own discipline.

**The question this document answers.** MBPP pass rate has been pinned at
**48/257 (18.7%)** through the entire Arc6 Tier0→A25 series
(2026-08-01 through 2026-08-11/12 — verified against every ARC6 doc's own
`**Date:**` line, `PROGRAM_SYNTHESIS_ARC6_TIER0.md` through
`PROGRAM_SYNTHESIS_ARC6_QUESTION_DRIVER_IMPOTENCE.md`), unchanged since the
list/tuple value-layer fix landed
(`PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md`). The project's own diagnosis
(`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`) names the bottleneck as
**missing structural primitives** — filter/map templates, string ops, a
recursion binder, a value/JSON boundary fix — and states plainly that **zero
of the 42 unreached tasks are blocked by "missing mathematics" or "missing
reasoning strategy."** CLAUDE.md's own governing sections — SHAPES-NOT-NUMBERS,
SHAPE-IS-ACQUISITION/RULE-IS-EXECUTION, and BASE-AS-DIMENSION — establish two
generative primitives (the sd loop's decode/recognize/mint ladder, and the
admissibility grammar Γ) as the project's answer to "a hand-enumerated list
where a codebook belongs." **This document asks, with real code in hand, not
assumed: is the program-synthesis op-table that same anti-pattern, and if so,
which of the two primitives fixes it — or is it neither?**

**Headline finding, stated up front because it reshapes every answer below:**
**the 42-task ceiling is NOT sd-loop-shaped, and this codebase's own
strongest precedent for "safe automatic codebook growth" — the
`DimensionGenerator` mint path CLAUDE.md itself showcases in BASE-AS-DIMENSION
— proves it, on inspection, rather than merely suggesting it.** Every
`sd_mint_quantum`/`grow_part_library` mint this tree has ever performed adds
**DATA** (a relation-vector signature, a `CapabilityAxis`, a `LatentDimension`
naming an *existing* generator) consumed by an **already-written, fully
generic Rust evaluator** (`AntiUnifyWitness`, `apply_generator_once`'s fixed
7-arm dispatch). Not one mint in this tree has ever produced NEW INTERPRETER
CODE. A missing MBPP operator — `filter`, `Counter`, `combinations`, a
recursion binder, a correct string `sorted` — is not a relation pattern the
existing evaluator already knows how to run; it is new *evaluation
semantics*, exactly the thing `scale2` and `modular` needed hand-written Rust
for when they were added as `DimensionGenerator` kinds. This document's own
audit trail (§1) confirms `SHAPE_AUDIT.md` independently reached the same
boundary and drew it in the same place: it explicitly rejects the sanctioned
generator-kind dispatch table as **NOT** Pattern D, while separately flagging
a structurally identical sibling table (`NATIVE_ORACLES`, the `ProgEval`
oracle table) as a **live, unaddressed** Pattern-D risk. The honest verdict
lands as a **hybrid**, and the two halves are sized very differently (§5-6):
hand-extend the primitive/op-table layer (cheap, proven, CLAUDE.md's own
sanctioned "primitive in Rust" pathway), and — separately, smaller, and
optional — align the *op-selection* layer (`SynthesisOperatorShape`) to the
sd loop's recognize/mint discipline, because that layer really is doing
Pattern-A/D-shaped keyword matching over a closed, hand-authored table today,
with no growth path, over the same "recurring benchmark miss adds a row"
family `SHAPE_AUDIT.md §5.3` already named as a risk one module over.

---

## 1. Is the op-table a Pattern-D hand-enumeration? (Q1)

### 1.1 The real op-table, read directly, and which one actually matters

Two synthesizers exist in this tree and only one of them runs MBPP:

- **`domains/generator.py`** ("Brick 6" — a numeric-only, Python-side
  bottom-up enumerator; its own `_op_table`/`DEFAULT_OPS`,
  `generator.py:58-87`) is used by `domains/cegis_faculty.py`,
  `generator_self_improve*.py`, `generator_coarsen.py`, and a dozen
  `scripts/generator_*.py` one-offs (Euler descriptor, `sum_of_n`
  CEGIS demos) — **verified by grep: nothing under `domains/prog_*.py`
  imports it.** It is a documented *ancestor*, not the live MBPP path.
- **`runners/dsl/src/synth_enumerate.rs::OP_TABLE`** is the live path. It is
  invoked as the `SynthEnumerate` Term from
  `domains/prog_synthesis.py::run_enumerate` (`prog_synthesis.py:1090-1242`),
  which builds the spec (`examples`, `ops`, `consts`, `exclude`) from graph
  data and calls `sub._inner.evaluate(spec, {})` — one Rust call, the
  decision of *which* ops to pass already made by a graph verdict
  (`ps_enum_ops`, §1.3 below), and the rest of the function purely records
  outcome facts (`ps_enumerate_outcome`, `ps_ir`, …) exactly the
  `run_enumerate`/`run_exact_family` shape CLAUDE.md's own "What good Python
  code looks like" section sanctions.

`OP_TABLE` (`synth_enumerate.rs:270-311`, read in full) is a hand-authored
Rust `const`:

```rust
const OP_TABLE: &[(&str, OpKind)] = &[
    ("Plus", OpKind::Binary), ("Times", OpKind::Binary), ...
    ("Concat", OpKind::Binary),   // -> StringConcat{parts:[a,b]}
    ("CaseFold", OpKind::Unary),  // -> CaseFold{text}
    ("Len", OpKind::ListUnary),   ("SumList", OpKind::ListUnary), ...
    ("FilterList", OpKind::ListFilter), ("MapList", OpKind::ListMap),
    ("TupleOf", OpKind::Binary), ("ProdList", OpKind::ListUnary),
    ("ConcatList", OpKind::ListBinary), ("ArgMaxLenOver", OpKind::ListUnary),
];
```

29 entries today (the last 4 — `TupleOf`/`ProdList`/`ConcatList`/
`ArgMaxLenOver` — are Arc6 tier-0's own additions, already landed; the
structural-ceiling doc's "30 op names" count is from before that build).
Each entry is a `(name, arity_kind)` pair; the arity kind routes to a
`match name { "Plus" => TermNode::Plus{...}, ... }` builder
(`synth_enumerate.rs:377-518`) that constructs the concrete Term-tree node.
**Adding an operator means adding one row to `OP_TABLE`, one `match` arm per
builder function it participates in (`build_binary`/`build_unary`/etc.), and
— for anything not already a shipped `TermNode` (Tiers 1-3 of the ceiling
doc) — a NEW `TermNode` variant plus its `ProgEval`/DSL-evaluator
implementation.** This is by construction a hand-maintained, closed-at-any-
given-moment enumeration, extended by a human (or an agent doing Rust work)
reading a task, one row at a time — the literal shape `SHAPE_AUDIT.md §5`
calls Pattern D: *"a hand-maintained enumeration where a codebook belongs."*

### 1.2 The disanalogy that actually decides this, found by reading the sd
   loop's OWN growth mechanics, not by asserting it

`sd_mint_quantum` (`seeds/shape_decode_loop.json`, read in full) mints a
`CapabilityAxis` carrying **"the residual's predicates"** — i.e., a snippet
of the observation's OWN relation-vector signature — and its downstream
consumer, `grow_part_library` (the Python *builder*, mechanical per
CLAUDE.md's own "seeds are modular" doctrine), turns that into a new
`ShapeSignature` node: more DATA in the SAME positional-relation-vector
format every codebook entry already uses. The thing that *reads* a
`ShapeSignature` — `sd_recognize`'s `AntiUnifyWitness`/`FixedCount` fit, the
`ShapeDecode` Term itself — is **one generic Rust evaluator, written once,
that never changes when the codebook grows.** Minting a 500th
`ShapeSignature` costs the SAME Rust cycles as recognizing the 1st. This is
the property that makes `sd_mint_quantum` safe to fire automatically, at
tick-time, with no human in the loop: **the mint only ever adds data the
evaluator already knows how to interpret.**

`OP_TABLE` does not have this property, and BASE-AS-DIMENSION's own newest
rung proves it directly rather than by analogy. CLAUDE.md's own words:
*"a `scale2` (multiplicative ×2^k) and `modular` (cyclic Z_n step)"* landed
as new `DimensionGenerator` **kinds**. Read where that dispatches
(`shape_decode.rs:836-847`, `apply_generator_once`, read in full):

```rust
fn apply_generator_once(kind: &str, coord_dims: &[i64], sig: &[Value], ...) {
    match kind {
        "rotation90" => { ... }
        "reflection_r" => reflect_once(sig, ...),
        "reflection_c" => reflect_once(sig, ...),
        "scale2" => scale_pow2_once(sig, coord_dims),
        "modular" => modular_step_once(sig, coord_dims, modulus),
        _ => None,
    }
}
```

**Seven fixed match arms.** `DimInfer`'s rung-3 "mint a dimension" step
(`sd_recognize_dim`) does NOT invent a new `kind`; it decides that an
ALREADY-CODED generator (one of these seven) explains a residual, and mints
a `LatentDimension` node that *names* which one. `scale2` and `modular`
exist in this `match` because a human wrote `scale_pow2_once`/
`modular_step_once` in Rust — the exact same class of act as adding a row to
`OP_TABLE` plus a `match` arm in `build_binary`. **The sd loop's own most
celebrated recent growth (BASE-AS-DIMENSION) is, underneath the graph-native
framing, hand-Rust-authored primitive extension wearing a mint on top.** The
mint automates *selection among already-built primitives*; it has never once
automated *building* a primitive.

This is not this document's own inference — `SHAPE_AUDIT.md §5.5`
("Rejected as NOT Pattern D") independently reaches the identical line and
states it explicitly: *"`shape_decode.rs:838`'s 7 generator arms — this IS
the sanctioned codebook's transform dispatch, named in CLAUDE.md."* The
audit's own authors looked at exactly this table and concluded it is
legitimate, closed-primitive-kernel machinery, not an anti-pattern to fix.
`OP_TABLE`'s `match` dispatch is the direct structural sibling of that
sanctioned table — same shape (`name → fixed builder`), same reason it is
legitimate at the primitive-authoring layer.

### 1.3 What Q1 actually finds, precisely, because "is it Pattern D" has two
   different honest answers depending on WHICH layer is asked

There are two separable tables here, and conflating them is exactly the kind
of "sophisticated-sounding wrong answer" §4 below is written to guard
against:

1. **The primitive/interpreter layer** — `OP_TABLE`'s entries that require a
   NEW `TermNode` (Tiers 1-3: `Slice`, `Str`, `Split`, `Sort`, `Replace`,
   `Combinations`, `Recurse`, …, 17 variants for the full 42). **This layer
   is NOT Pattern-D-fixable by the sd loop**, for the reason §1.2 just
   proved with this tree's own code: no mint mechanism in this codebase has
   ever synthesized new Rust evaluation semantics from a residual, and
   there is no reason to expect one could — a `CapabilityAxis`/
   `LatentDimension` mint is a SELECTION over pre-built primitives, and
   these tasks need primitives that are not pre-built. This is squarely
   CLAUDE.md's own THIRD, already-sanctioned pathway — *"When a new
   primitive is needed → Rust... Add a new DSL Term."* Growing it is not a
   violation of SHAPES-NOT-NUMBERS; it is the documented, correct way to
   grow a primitive set, and the ceiling doc's own Tier-0 build
   (`PROGRAM_SYNTHESIS_ARC6_TIER0.md`) and the value-layer rung
   (`PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md`) are both already, literally,
   this pathway in action.
2. **The selection layer** — deciding WHICH ops (from the already-existing
   29) to pass into a given `SynthEnumerate` call. This is
   `SynthesisOperatorShape` (`seeds/program_synthesis_grounding.json`, read
   in full) — a hand-authored node per shape, each carrying a fixed
   `trigger_tokens` list and a `minimum_trigger_matches` count:

   ```json
   {"name": "thresholded_greater_branch",
    "trigger_tokens": ["MORE","GREATER","EXCEEDS","ABOVE","THAN","TIMES",
                        "THRESHOLD","WHEN","OTHERWISE","ELSE"],
    "minimum_trigger_matches": 5,
    "ops": ["Times","Gt","IfThenElse"]}
   ```

   This is scored by `ps_select_synthesis_operator_shape`
   (`program_synthesis_grounding.json:483-620`) — a keyword-count classifier
   over a fixed, hand-written trigger-token table, **the identical shape**
   `SHAPE_AUDIT.md §5.1` diagnosed and then fixed for
   `recognise_meta_shape` (*"scored by raw `text.contains` over discarded
   attribute keys"*), with no residual/mint growth path: a task whose prose
   doesn't hit five trigger tokens for any shape gets no operator-shape
   proposal at all, and there is no rule that adds an twelfth shape when
   one is needed — a new shape is, today, hand-authored JSON, exactly like
   the meta-shape vocabulary was before `META_SHAPE_FIRST_CLASS_RESULTS.md`.
   **This layer genuinely is Pattern-D/A-shaped, genuinely has no growth
   path, and is a legitimate, much smaller, alignment target** — separable
   from and far cheaper than trying to make the primitive layer sd-loop-grown.

**Verdict on Q1, stated once, precisely:** a missing *operator* (Tiers 1-3)
is not structurally analogous to a missing shape quantum — it is a missing
primitive, and this codebase's own BASE-AS-DIMENSION precedent shows that
even its most sophisticated existing "automatic growth" already draws this
exact line, hand-authoring the primitive and automating only the selection.
A missing *operator-shape recognition* (which of the 29 existing ops to try)
IS structurally analogous to a missing shape quantum, is currently solved by
exactly the kind of hand keyword table CLAUDE.md's own audit already flagged
as an anti-pattern one module over, and is a real (if secondary) alignment
opportunity.

### 1.4 A third primitive considered and set aside: is the enumerator itself
   Γ-shaped?

Worth naming because CLAUDE.md's own SHAPES-NOT-NUMBERS section poses
exactly this question ("a quantity that changes, or a set of allowed
moves?") and the enumerator's own module doc (`generator.py:1-29`) already
describes itself in generative-production language: *"SEARCH over the
production space = enumerate Term-trees from the DSL ops."* Is `OP_TABLE`
better understood as Γ (an admissibility grammar generating legal Term
compositions) than as a codebook? **Considered and rejected as the frame for
THIS document's recommendation**, for a concrete reason: the substrate's
actual Γ (`runners/dsl/src/grammar.rs`) generates admissible **graph
edges** — `Production{src-pattern, edge_type, tgt-pattern, where, weight}`
over a `TypedGraph`'s node/edge population, read by `admissible_moves`. The
enumerator's search space is a **Term-tree AST**, a different data model
entirely; `SynthEnumerate`'s bottom-up size-ordered enumeration is already,
independently, doing the job Γ does for graphs — generating an admissible
move set — just over a different substrate (Term compositions, not typed
edges). Re-platforming the DSL Term grammar onto the graph-edge Γ machinery
would be a large, separate architecture change with no present evidence it
buys anything over the enumerator's own already-working (if bespoke)
generative loop, and this document does not recommend it. The relevant
CLAUDE.md categories for `OP_TABLE`'s two layers are, precisely: primitive-
in-Rust (§1.3 item 1) and shape-decode-codebook (§1.3 item 2) — not Γ.

---

## 2. Is the value/JSON boundary fix a frame/continuum-invariant violation? (Q2)

### 2.1 What the actual bug is, read directly

`PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md §1` (read in full): `list` and `tuple`
realise as the SAME `Value::Tuple` at three boundaries — PyO3 in
(`py_to_value`), PyO3 out (`value_to_py`), and inside `ProgEval` itself
(`prog_eval.rs`'s own header: *"list/tuple displays both realise as
`Value::Tuple`"*). The fix (landed) adds a genuinely new `Value::List`
variant and makes ~15 call sites kind-**preserving** rather than
kind-**collapsing**. The still-open residual (§9.1 of that document,
`inputs_json = json.dumps(inputs)`) is the SAME class of bug at the row's
*input* side: JSON has one array type, so a tuple ARGUMENT arrives at every
downstream consumer already flattened to a list, before any evaluation runs.

### 2.2 Applying CLAUDE.md's own decision procedure directly, not by analogy

CLAUDE.md's frame/continuum invariant is precise about what it governs:
*"In-frame is INTEGER... Non-integer math is CROSS-FRAME... the decision
procedure for every number you write: is this value IN a frame, or BETWEEN
frames?"* — every example the section gives (π, real rotation angles, log
scale, Fourier, the SC+TPS/DTW verdict metrics) is about **numeric
magnitude and continuity**: whether a *quantity* is exact-and-stepped
(in-frame) or real-and-intensional (cross-frame, living in a map between
frames).

The list/tuple collapse involves **no numbers of this kind anywhere in its
own description.** Every value in play — a `Value::Tuple`, a `Value::List`,
a JSON array — is already discrete, already exact, already an in-frame
observation; nothing about `[5,6,7]` vs `(9,10)` is a question of magnitude,
scale, or continuity. What is lost at the boundary is **container-kind
identity** — a type tag, not a coordinate. `PROGRAM_SYNTHESIS_ARC6_
STRUCTURAL_CEILING.md §8` already ran the SAME "is this a coordinate the
frame lacks, or type coverage in a Term that refuses to handle a value it
already has" test on the 42 tasks' own operators and reached exactly this
conclusion for the closest-looking candidates (*"a string is atomic... the
Terms exist and simply refuse `Value::Str`. This is type coverage in
shipped Terms, not an absent coordinate. Verdict: operator."*). The
list/tuple boundary bug is the identical kind of finding one layer down, at
the `Value` enum itself rather than at a `TermNode`'s type guard: a
representational gap in what the value DOMAIN can express (no distinct
container-kind tag), not a magnitude the frame cannot represent.

**Verdict on Q2: no.** The value/JSON boundary fix is a real, and
genuinely still-unfinished (§9.1's input-side symmetric fix), defect — but
it is not an instance of the frame/continuum invariant. It is a
serialization/representational-completeness boundary bug: the same FAMILY
of defect as `persist::decode_value`'s bare-JSON-array-means-Tuple asymmetry
(`VALUELAYER.md §9.2`, named, not fixed) and the `Lit` boundary's refusal of
Python `set` (`§9.2`, `STRUCTURAL_CEILING.md §7.4`) — a boundary erasing a
TYPE distinction on the way across a language/format seam, not a frame
mixing an in-frame coordinate with a between-frame real number. CLAUDE.md's
own invariant does not need to be invoked to fix it, and misreading it as an
instance of that invariant would be exactly the kind of "borrow the
sophisticated-sounding frame" mistake §4 is written to guard against — the
fix is boundary I/O work (PyO3/persist plumbing), squarely inside CLAUDE.md's
own sanctioned "world adapter" and "expose via PyO3" categories, not a
shape-decode or dimension-inference matter at all.

---

## 3. Has the A9-A24 (ArcGoal/`ax_dispatch`) series tried sd-loop-style
   op-table growth? (Q3)

### 3.1 What that series actually built, read directly

The Arc6 A-series (`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md`,
`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md`,
`PROGRAM_SYNTHESIS_ARC6_GOAL_RESIDUALS.md`, plus the whole
2026-08-11/12 IMPOTENCE/EXECUTOR/REARM/RETIRE/PROGREAD_SELFIMPROVE run)
builds an **arc-grain research-planning dispatcher** — `ArcGoal` nodes
minted from measured "residuals" (named gaps like `enum_op_table`,
`property_atom`, `row_verdict`), a weighted collapse (`ag_select`) among
competing candidate research directions, and — in the later A-series docs —
a natural-language "ask" escalation and a self-improvement executor loop
that reads/writes `prog_read` gap facts. **This is a different layer than
the op-table itself: it decides which EXPERIMENT (build tier 1? price the
sort fix? measure seam C?) the agent should pursue next, not which
OPERATOR to add.**

`GOAL_RESIDUALS.md §"dimension"` (read in full) DOES use
`enum_op_table` as a **match token** — one of six named `sig_seam` values a
candidate `ArcGoal`/`MoveCandidate` can be scored against (`arc6.
structural.enum_op_table` → `enum_op_table / proposal / s4_residual_60`,
weight 63.0, `6/42` reach). This is the ArcGoal-collapse system
RECOGNIZING that a candidate experiment addresses the already-measured
op-table gap — it is bookkeeping over the ceiling document's own numbers,
via a residual-match rule (`gr_move_penalty`), not a mechanism that adds
rows to `OP_TABLE`. Confirmed by the design doc's own words:
*"There is no node in this tree that says 'build the import oracle'... no
`domains/prog_*.py` mints anything above one task"* (`ARC_GOALS_DESIGN.md
§1`) — i.e., the A-series is explicit that IT operates at the
arc-planning grain, one level above any single primitive addition, and
never claims to automate primitive addition itself.

### 3.2 Verdict on Q3

**No.** Nothing in the A9-A24 series attempts, proposes, or even names
growing the op-table's PRIMITIVE content via sd-loop mechanics. Every
op-table growth event that has actually happened in this project's history
— arc4's S4 widening (11 ops, 0 new `TermNode`), arc6's tier-0 (8 units, 0
new `TermNode`, `PROGRAM_SYNTHESIS_ARC6_TIER0.md`), and the value-layer rung
(`VALUELAYER.md`) — was a **hand-built, hand-measured, single Rust/Python
PR**, exactly matching §1.3's finding that this layer has never been
automated in this codebase and the A-series has never attempted to automate
it. The A-series' own contribution is upstream of this question: it decides
WHETHER to spend the next unit of build effort pricing the sort fix, taking
tier 1, or measuring seam C — a real and useful thing, but not an answer to
"how do new operators get added," which has always been, and remains,
manual.

---

## 4. The genuine third option, weighed honestly (Q4)

CLAUDE.md's own SHAPES-NOT-NUMBERS section states the discipline this
section is bound by: *"if it is neither [a decode-a-quantity problem nor a
generate-a-move-set problem], that is worth stating explicitly."* §1.3
already did the hard part of this — split the op-table into two layers with
two different honest answers. This section asks the sharper version of Q4:
even granting the primitive layer needs Rust and isn't sd-loop-automatable,
**is it worth building ANY new machinery for it at all, or is "hand-add the
known gaps" simply the correct, permanently-manual answer?**

### 4.1 The case FOR "hand-add and stop" (no new machinery, ever)

- **The known gap is finite and already fully enumerated.**
  `STRUCTURAL_CEILING.md §3-4` names the entire 42-task ceiling as 28
  distinct structural units, ranked, priced, with witnesses for the
  cheapest six. There is no "unknown unknown" tail here the way there is
  for, say, a conversation agent's vocabulary — the whole population (MBPP
  test split, 257 tasks) is fixed and has been read exhaustively.
  Building growth machinery to handle a population that will never exceed
  this one document's own table is over-engineering for a non-recurring
  problem, exactly the caution CLAUDE.md's Q4 framing calls out by name
  ("hand-adding 4 things might be strictly cheaper... for a problem that
  doesn't recur").
- **Every past instance of this exact widening was cheap and worked.** S4:
  11 ops, moved 25/85. Tier 0: 8 units, 0 new `TermNode` (though its
  *conversion* yield was blocked one layer downstream by the row-verdict
  scalar cast, not by the widening itself — `TIER0.md §0`). Value layer: 1
  new `Value` variant, +12 ids. The **measured** cost-per-unit
  (`STRUCTURAL_CEILING.md §4.2`: "10 new Term variants buy +16 ids = 1.6
  ids per Term variant") is a real, already-priced number, not a
  projection.

### 4.2 The case FOR building the (smaller) alignment anyway

- **`SynthesisOperatorShape`'s classifier is a live risk independent of
  whether the primitive layer ever grows again.** Every new operator-shape
  hand-authored so far (`thresholded_greater_branch`,
  `thresholded_lower_branch` — 2 shapes today) needs its own trigger-token
  list maintained by hand, and `SHAPE_AUDIT.md §5.3` already measured the
  sibling table (`NATIVE_ORACLES`) drifting at "each benchmark miss adds a
  row in two languages." If Tier 1/2 ship (§5-6 below), each new Term needs
  at least one new operator-shape trigger-token block to be discoverable by
  the selector at all (or falls back to `DEFAULT_OPS`/`LIST_EXTRA_OPS`
  blanket inclusion — confirmed by reading `synth_enumerate.rs:1486-1504`:
  `run_enumerate` omits the `"ops"` key entirely when `graph_ops` is empty,
  and the Term's own typed-default logic then picks `DEFAULT_STR_OPS` for a
  string-shaped spec or `DEFAULT_OPS ∪ LIST_EXTRA_OPS` (plus
  `TUPLE_BUILD_OPS` when the output is tuple-shaped) for a list-shaped one
  — which is a separate, real cost: an unfiltered op list is exactly what caused
  `TupleOf` to blow `distinct` from 167 to 14,709 candidates on task 132,
  `synth_enumerate.rs`'s own comment, cited in `STRUCTURAL_CEILING.md`).
  Growing the primitive set WITHOUT fixing the selection layer makes the
  selection layer's existing risk worse, not neutral.
- **The fix is cheap relative to the primitive-layer fixes it would sit
  next to.** `META_SHAPE_FIRST_CLASS_RESULTS.md` is the direct precedent —
  fixing an identically-shaped keyword scorer (11×11 shape pairs, delete
  the alphabetic tiebreak, wire recognize→transform→infer→mint) was a
  single scoped rung, not a multi-arc effort.

### 4.3 The judgment call, made and defended

**This document lands on a HYBRID, and states plainly that the "hand-add
and stop" case (§4.1) is the stronger of the two for the PRIMITIVE layer —
the evidence there is not mixed.** Every measured fact points the same way:
no automated-growth mechanism has ever synthesized a new Rust primitive in
this codebase's history, the population is closed and already fully
inventoried, and the per-unit cost of hand-adding is already priced and
cheap. Recommending sd-loop machinery for the primitive layer would be
building a shape matcher with no shape to match — the exact caution
CLAUDE.md's own SHAPES-NOT-NUMBERS section's closing line names.

For the SELECTION layer, the evidence is more genuinely mixed, and this
document says so rather than picking the more sophisticated-sounding
answer by default: there is real, measured drift risk (§4.2), but there is
also only ONE recurring consumer of it today (`ps_select_synthesis_
operator_shape`, 2 shapes) and no MBPP task currently fails FOR THIS REASON
— every one of the 42 named blockers is a primitive gap, not a
selection-layer miss (confirmed: `STRUCTURAL_CEILING.md`'s per-task
`why` column never cites operator-shape mismatch as a blocker; the
mechanism that fires today, `graph_ops` unset → the module falls back to
the Rust-side `DEFAULT_OPS`/typed defaults, §5.1). So the honest sizing is:
**do the primitive-layer work now (it is what actually moves the number),
and treat the selection-layer alignment as a smaller, independently
justified, LOWER-PRIORITY rung** — worth doing because the drift risk is
real and the precedent is cheap, not because it is required to unblock any
of the 42.

---

## 5. The plan

### 5.1 Rung 1 (primitive layer, do this first) — Tier 1 stdlib Term ports,
   exactly `STRUCTURAL_CEILING.md §9`'s own prioritised order

**10 new `TermNode` variants, +16 ids at inventory level (~+8 at the S4
32%-conversion discount, `STRUCTURAL_CEILING.md §6.3`), zero new
architecture.** Each is a Term-layer port of a behaviour `ProgEval` already
has (`STRUCTURAL_CEILING.md §2`: `sorted`, `split`, `replace`, `count`,
`round`, `reversed`, `str`, `int` are all already-shipped `ProgEval`
externs) — so each is genuinely "expose an existing capability as a
composable op," the SAME risk class as tier 0, not a fresh design:

| order | unit | new Term | ids (alone / necessary-for) |
|---|---|---|---|
| 1 | `term:Replace` | `Replace` | 2 / 2 |
| 2 | `term:Str` | `Str` | 1 / 4 |
| 3 | `term:Split` | `Split` | 1 / 3 |
| 4 | `term:StrCount` | `StrCount` | 1 / 1 |
| 5 | `term:Round` | `Round` | 1 / 1 |
| 6 | `term:Reverse` | `Reverse` | 1 / 1 |
| 7 | `term:IndexedMap` | `IndexedMap` | 0 / 3 |
| 8 | `term:Capitalize` | `Capitalize` | 0 / 2 |
| 9 | `term:ParseInt` | `ParseInt` | 0 / 1 |

**`term:Slice` is deliberately placed LAST inside this rung, not first**,
despite `necessary for: 5` being the single largest number in the table:
its blast radius touches `StringSlice`'s existing negative-index refusal
(`STRUCTURAL_CEILING.md §7.5`), so it should land after the other nine have
independently validated the "one new Term, byte-identical regression
sweep" workflow on lower-risk units.

**Each unit is gated exactly like `TIER0`/`VALUELAYER` already were**: a
hand-built witness Term reproducing the task's revealed rows before the op
is wired into search (the `STRUCTURAL_CEILING.md §5` discipline), a
`ps_row_pass`-level pass/fail check (not just search-layer `found`, per
`TIER0.md`'s own headline finding that inventory success and verdict
acceptance are SEPARATE gates), and a paired before/after MBPP battery run
with `lost_pass = []` as the non-regression bar.

### 5.2 Rung 2 (primitive layer, do this second, independently gateable) —
   the two named-but-not-taken value-layer residuals

Both are already fully designed and witnessed, not merely proposed:

- **§9.1 of `VALUELAYER.md`**: symmetric `_wire`/`_unwire` on
  `inputs_json`, converting task 106 (live witness: 670 candidates/solved
  vs. 16,603/budget-exhausted, already measured). This is the SAME kind of
  change as the already-shipped output-side `_wire`, at the INPUT side —
  low novelty, high confidence.
- **§9.2's `persist::decode_value` bare-array question** — deliberately
  NOT bundled with the above; it is a seed-semantics decision (does a bare
  JSON array mean list or tuple for the 68 `Lit` array literals already in
  seeds?) that `VALUELAYER.md` itself declines to make unilaterally, and
  this document does not resolve it either — it is named here as a
  dependency to price, not a rung to build blind.

### 5.3 Rung 3 (primitive layer, price before committing, do NOT bundle) —
   `term:Sort` + the string-order fix

`STRUCTURAL_CEILING.md §7.2`/§9 already prices this precisely: `term:Sort`
is one new Term, but it is USELESS without `cmp_value`'s `(Str, Str)` arm
moving off interner-symbol-id comparison, and that correction's blast
radius touches every frozen fixture containing a string-keyed `Set`/`Dict`.
**Do not take this rung until the fixture-migration cost is priced**,
exactly as recommended. Note the partial complication already measured:
`CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md` (`VALUELAYER.md §9.3`) landed
a NARROWER, reported-order-only fix (`cmp_value_lex`) that does not move
`cmp_value` itself — Rung 3's `term:Sort` should be priced against
`cmp_value_lex`'s existing precedent first, since it may already supply
what `Sort` needs without reopening the wider fixture-migration question.

### 5.4 Explicitly NOT recommended for this arc

- **`term:Recurse`** (7 ids on paper) — `STRUCTURAL_CEILING.md §6.3`'s own
  discount is worse than the 32% baseline for exactly this unit ("a
  self-referential binder makes an enumerative search combinatorially
  harder as it makes it richer"), and it is a capability decision (what the
  search space IS), not an additive widening. Re-price only after Rungs
  1-3 are in and the enumerator's real headroom is re-measured.
- **`term:Format`** — one task uses it, nothing else does; taking it is
  the structural-seam form of the A-ceiling's `perrin_sum` cherry-pick
  (`STRUCTURAL_CEILING.md §9` item 5), named explicitly to avoid quoting it
  as a reach number later.

### 5.5 Rung 4 (selection layer, independent, lower priority, optional) —
   align `SynthesisOperatorShape` to the sd-loop discipline

Scoped narrowly, per §4.3's judgment that this is real but not
number-moving today:

1. **Recognize**: replace `ps_select_synthesis_operator_shape`'s raw
   trigger-token count with a `Covers`/`AntiUnifyWitness`-shaped structural
   match over the task's own parsed shape facts (mirroring
   `META_SHAPE_FIRST_CLASS_RESULTS.md`'s scorer fix — delete the implicit
   tie behaviour, score the item's own evidence).
2. **Grow**: when NO `SynthesisOperatorShape` scores above threshold for a
   task whose search nonetheless finds something (or nothing, at
   `max_size`), mint a residual-shaped candidate — this is the ONE place
   in this whole plan where an `sd_mint_quantum`-style rule is genuinely
   the right primitive, because what is being minted is DATA (a new
   trigger-signature) over an ALREADY-EXISTING generic evaluator (the
   scorer), not new interpreter code. This is exactly the boundary §1.3
   draws.
3. **Explicitly out of scope for Rung 4**: it must never decide which
   NEW `TermNode` to build — that stays Rung 1/2/3's manual, priced,
   human-reviewed process. Rung 4 only grows the CHOICE of which
   already-existing ops (from the 29-and-growing `OP_TABLE`) to try for a
   given task's shape.

**This rung is explicitly separable from and not a prerequisite for Rungs
1-3.** It should be built, if at all, after Rung 1 has shipped a few more
operator-shapes to season the classifier's real drift, not before — sizing
a fix from a 2-entry table would repeat `SHAPE_AUDIT.md`'s own named
mistake ("a shape matcher built before there is a shape to match").

---

## 6. Risk and cost accounting, honestly

| rung | new Rust | new architecture | ids (inventory) | regression risk | confidence |
|---|---|---|---|---|---|
| 1 (Tier 1 ports) | 10 `TermNode` variants | none — same shape as Tier 0/value-layer | +16 (~+8 discounted) | LOW — same gated workflow that already worked twice; `IndexedMap`/`Capitalize`/`ParseInt` are net-new capability inside a shipped Term family, marginally higher risk than pure exposure | HIGH |
| 2 (input `_wire`) | 0 | none | +1 (106, witnessed) | LOW-MEDIUM — changes what every task's program *sees* on every row (`VALUELAYER.md §9.1`'s own caveat) | MEDIUM-HIGH |
| 3 (Sort + string order) | 1 `TermNode` + a `cmp_value` correction | none | +4 | HIGH — cross-cutting, can move frozen fixtures; must be priced before committing (§5.3) | LOW until priced |
| 4 (selection-layer align) | 0 | reuses sd loop (recognize/mint), no new Rust | 0 directly; risk-reduction only | LOW — additive rule, existing `DEFAULT_OPS` fallback is the safety net | MEDIUM (untested on a 2-entry population) |
| (rejected) full sd-loop primitive-mint | new Rust EVERY mint, by construction | new, unprecedented architecture | unclear — no comparable mechanism has ever existed in this tree | UNBOUNDED — asks a generic evaluator to acquire semantics it doesn't have | this document does not recommend building it |

**What this plan does NOT establish**, registered per this document's own
house style:

1. No code, seed JSON, or tests were written — investigation and design
   only.
2. The Rung-1 unit ordering is this document's own re-statement of
   `STRUCTURAL_CEILING.md §9`'s prioritisation, not a new measurement — it
   is not independently re-verified here.
3. Whether Rung 1's S4-discounted +8 estimate holds is untested — per
   `TIER0.md`'s own headline finding, an inventory number and a converted
   number are different gates, and Tier 0 itself converted ZERO of ten
   inventory ids until the row-verdict fix landed separately. **Rung 1
   should re-run the SAME `ps_row_pass`/non-scalar-verdict check Tier 0's
   own postmortem forces** before trusting any conversion count.
4. Rung 4's sizing is qualitative (mirrors `META_SHAPE_FIRST_CLASS_
   RESULTS.md`'s scope) and has not been priced against the actual current
   `SynthesisOperatorShape` population the way Rungs 1-3 were priced
   against the actual `STRUCTURAL_CEILING.md` ledger.
5. This document does not re-derive the 48/257 pinning or re-run any
   battery — it is built entirely on already-landed, already-measured
   artifacts (`STRUCTURAL_CEILING.md`, `TIER0.md`, `VALUELAYER.md`,
   `GOAL_RESIDUALS.md`, `SHAPE_AUDIT.md`, `META_SHAPE_FIRST_CLASS_
   RESULTS.md`), per this task's own instruction not to re-derive
   established context from scratch.

---

## 7. Recommendation and confidence

**Build Rung 1 next** (§5.1): it is the direct continuation of the
already-proven arc4-S4/arc6-tier0 shape, it requires no new architecture
and no dispatch-shape design risk, and — per §4.3's judgment — the evidence
that the primitive layer should stay a hand-authored, Rust-primitive-driven
process is not mixed; it is the strongest, most consistently pointing body
of evidence in this whole investigation (the DimensionGenerator precedent,
the SHAPE_AUDIT's own explicit rejection of the sibling table as Pattern D,
and the complete absence of any counter-example anywhere in this codebase's
history of a mint producing new interpreter code). **Do not build general
op-table-growth machinery for the primitive layer** — there is no shape to
match there, only primitives to write, and CLAUDE.md's own "primitive in
Rust" pathway already names the correct process.

**Treat Rung 4 (selection-layer alignment) as real but optional and
lower-priority** — it addresses a genuine, independently-diagnosed risk
(the same family `SHAPE_AUDIT.md §5.3` already flagged), but it does not
move the 48/257 number today and its population is currently too small (2
operator-shapes) to size confidently; build it after Rung 1 has shipped
enough new Terms to season the classifier.

**Confidence, stated plainly because this is a judgment call under real
uncertainty, not a measured fact.** The Q1/Q3 findings (primitive layer
needs Rust; nothing in the A-series has tried to automate it) are
HIGH-confidence — each is grounded in this tree's own code and its own
prior audits reaching the same line independently (`SHAPE_AUDIT.md §5.5`'s
rejection of the generator-dispatch table as Pattern D is the single
strongest piece of evidence in this document, because it was written by a
different investigation with a different goal and landed on the identical
boundary). The Q2 finding (value/JSON boundary ≠ frame/continuum invariant)
is HIGH-confidence — the invariant's own stated scope (numeric magnitude/
continuity) simply does not describe a container-kind-identity bug, and no
part of the value-layer defect involves a real number anywhere. The Q4
judgment (hybrid, primitive-hand-add/selection-align-later) is
MEDIUM-confidence on the SPLIT itself (the primitive-layer half is close to
certain; the selection-layer half rests on a smaller, more qualitative
risk argument that has not been measured the way the rest of this document
insists on) and the specific PRIORITISATION within Rung 1 (§5.1's ordering)
inherits `STRUCTURAL_CEILING.md §9`'s own confidence, which that document
already flags as inventory-level, not conversion-verified.
