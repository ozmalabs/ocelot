# LLVM ingestion — design notes

The substrate eats LLVM the same way it eats H.264 or English vocabulary:
grammar + structure absorbed as graph-resident Microtheories, Frames,
and Concepts. Compilation becomes graph rewriting; the agent owns the
knowledge, not a backend dependency.

This document is the curriculum + design for that ingestion. It is NOT
itself a teaching payload — those are produced by a teacher module (see
`domains/llvm_teacher.py`, to be written) that returns
`learn_from_teacher`-shaped dicts.

## Mapping LLVM → substrate

| LLVM concept | Substrate representation |
|---|---|
| LLVM IR (text/bitcode) | `Microtheory(name="llvm_ir", genl_mt="compiler_ir")` |
| `Module` | `Concept` + `Frame` w/ binding_pattern `predicate_of_subject` |
| `Function` | `Concept` w/ slots `name`, `return_type`, `parameters` |
| `BasicBlock` | `Concept` w/ slots `label`, `instructions`, `terminator` |
| `Instruction` (opcode) | `Concept` per opcode (`add`, `mul`, `load`, …) |
| `Value` / `Type` | `Concept` family — first-class graph nodes |
| `Use`/`Def` edges | `defines` / `uses` edge types between Value Concepts |
| LLVM pass | `Rule` — match pattern + where + effect over IR subgraph |
| Pass pipeline | `Sequence` of Rules under `Microtheory(name="opt_pipeline")` |
| Target description | `Microtheory(name="<isa>")` — registers, instructions, costs |
| Cost model | `score` rules per instruction kind |
| Calling convention | `Frame` per CC describing arg→register mapping |

The substrate already has the machinery for every cell of this table —
the work is identifying which LLVM artifact maps to which Microtheory
form and producing the teaching payloads that install them.

## What gets ingested vs. what gets observed

The earlier "feed LLVM to the agent, not feed agent to LLVM" framing
distinguishes:

- **Ingested** (graph-resident, agent owns it):
  - LLVM IR grammar (instruction set, type system, value categories)
  - Documented passes (LangRef + the standard optimization pipeline)
  - ISA descriptions (TableGen-style: opcodes, encoding, latencies)
  - Cost models, scheduling info, calling conventions

- **Observed** (characterized from behavior):
  - Microcode revisions (effects on instruction behavior)
  - Black-box LLVM pass behavior (validate ingested rules)
  - Hardware effects (port pressure, cache, branch predictor)

Both are valid ingestion paths. The substrate's `derived_galileo` /
`discovers_conservation` machinery handles observation-driven discovery;
the `learn_from_teacher` path handles documented-source ingestion.
LLVM straddles both — IR grammar is documented (ingest from LangRef);
real-world pass behavior is partly observed (validate against `opt`).

## Curriculum

Ordered for dependency. Each phase builds on the prior.

### Phase 1 — IR grammar (foundation)

Microtheory `llvm_ir` under `compiler_ir`. Frames for:

- `Module`, `Function`, `BasicBlock`, `Instruction`, `Value`, `Type`
- Type categories: integer types, float types, pointer types, vector types,
  aggregate types, function types, label, metadata
- Value categories: constants, instructions (which produce values),
  globals, function arguments, basic blocks (as branch targets)

First teaching payload: ~30-50 phrases covering the structural backbone
of LLVM IR. Source: the LLVM Language Reference's "Module Structure" and
"Type System" sections.

Validation: parse a small LLVM IR text snippet using the agent's
recognizer; check the parsed structure matches the teacher's
schema. Once the agent can ingest `define i32 @foo(i32 %x) { ... }` and
recognize it as a Function over an integer-Type Module, Phase 1 is done.

### Phase 2 — Instruction set

Microtheory `llvm_ir_instructions` depending on `llvm_ir`. One Concept
per opcode, organized by category:

- Arithmetic: `add`, `sub`, `mul`, `udiv`, `sdiv`, `urem`, `srem`,
  `fadd`, `fsub`, `fmul`, `fdiv`, `frem`
- Bitwise: `and`, `or`, `xor`, `shl`, `lshr`, `ashr`
- Comparison: `icmp`, `fcmp` (with predicate variants)
- Memory: `alloca`, `load`, `store`, `getelementptr`, `atomic*`
- Conversion: `trunc`, `zext`, `sext`, `bitcast`, `inttoptr`, `ptrtoint`,
  `fptrunc`, `fpext`, `uitofp`, `sitofp`, `fptoui`, `fptosi`
- Control flow: `br`, `switch`, `indirectbr`, `ret`, `unreachable`,
  `invoke`, `resume`
- Aggregate: `extractvalue`, `insertvalue`, `extractelement`,
  `insertelement`, `shufflevector`
- Other: `phi`, `select`, `call`, `landingpad`, `freeze`

Per opcode: operand schema, result type rules, side-effect class,
poison/undef semantics. Each is a Frame with a precise binding_pattern.

Source: LLVM Language Reference's "Instruction Reference" section. The
agent recognizes each instruction by its mnemonic and operand shape;
ground them once, recognize forever after.

### Phase 3 — Simplest passes (first useful work)

Microtheory `llvm_passes` depending on `llvm_ir_instructions`. Start
with passes that are pure rewrite rules with no analysis:

- **Constant folding** — `add i32 X, Y` where both X and Y are constants
  → reduce to a constant. Rule: match the pattern, where clause checks
  constness, effect computes + replaces.
- **Identity elimination** — `add X, 0` → `X`; `mul X, 1` → `X`;
  `and X, X` → `X`; `or X, 0` → `X`; `xor X, X` → `0`.
- **Dead code elimination** — instruction with no uses and no side
  effects → delete.
- **Trivially constant phi** — `phi [X, %a], [X, %b]` (same value from
  both predecessors) → `X`.

Each ingested as a graph-resident Rule. The agent matches the rule
against any LLVM IR subgraph it holds and applies the rewrite.

Validation: hand-built test IR snippets, agent applies the rule, result
matches what `opt -instcombine -dce` would produce.

### Phase 4 — Local analysis passes

Microtheory `llvm_analysis` — passes that compute information rather
than rewriting:

- **Constant propagation** — flow constants forward through SSA defs.
- **Reaching definitions** — for each use, which defs can reach it.
- **Liveness analysis** — for each basic block boundary, which values
  are live.
- **Dominator tree** — block dominance relation.

Each becomes a Rule or set of Rules that annotate the LLVM IR subgraph
with computed attributes. Subsequent rewrite passes read those
annotations.

### Phase 5 — Global passes (the meat)

- **GVN** (global value numbering) — equivalence classes over SSA values.
- **Mem2Reg** — promote alloca'd scalars to SSA registers.
- **LICM** (loop-invariant code motion) — needs loop structure.
- **InstCombine** — pattern-based local optimizations (many small rules).
- **SimplifyCFG** — block merging, branch simplification.
- **Sparse Conditional Constant Propagation (SCCP)** — interleave
  constant prop with reachability.

These are larger Rules with non-trivial where-clauses. Source: LLVM
`lib/Transforms/Scalar/` plus a careful reading of each pass's source
to extract the rewrite rules from imperative code.

### Phase 6 — Backend (lowering + codegen)

Microtheories per ISA: `x86_64`, `arm64`, `riscv`, `wasm`, etc.

Each ISA Mt holds:

- Opcode table — instruction Concepts with encoding rules
- Register description — register Concepts with class/size/aliasing
- Calling convention — Frame per ABI describing argument register
  selection
- Cost model — `score` rule per instruction giving relative latency
- Scheduling info — port pressure / dispatch constraints
- Selection patterns — Rules matching LLVM IR subgraph → target opcode
  sequence (analog of LLVM's TableGen patterns)

Phase 6 is where the substrate's own native-codegen ambition lives:
once it has the ISA Mt + selection patterns, it can render an
LLVM-IR-shaped Term-tree to native bytes without ever invoking `llc`.

### Phase 7 — Whole-program (the long horizon)

- Inter-procedural optimizations (inlining, IPSCCP)
- Link-time optimization (whole-module reasoning)
- Profile-guided optimization (cost models driven by runtime data)
- Specialization (constant args propagated into callees)

Each is conceptually familiar from the academic literature; ingestion
follows the same Microtheory + Frame + Rule pattern.

## Teaching mechanics

The `learn_from_teacher` payload format already supports everything
needed:

```python
{
  "answer": "<human-readable description>",
  "learn": [
    {
      "phrase": "llvm function",
      "microtheory": "llvm_ir",
      "genl_mt": "compiler_ir",
      "binding_pattern": "predicate_of_subject",
      "description": "the unit of code with a name, signature, and body",
      "source": "llvm_langref"
    },
    {
      "phrase": "icmp eq",
      "microtheory": "llvm_ir_instructions",
      "genl_mt": "llvm_ir",
      "binding_pattern": "function_of_two_subjects",
      "description": "integer compare equal — true iff both operands equal",
      "source": "llvm_langref"
    },
    # render rule for emitting LLVM IR text from the graph form
    {
      "rule": {
        "language": "llvm_ir_text",
        "head": "Function",
        "template": "define {return_type} @{name}({params}) {body}",
        "guard": null
      }
    }
  ]
}
```

The agent's existing impasse-resolver chains teachers; a new
`LLVMTeacher` in the chain consults a static knowledge base (LangRef
chunks, opcode tables) and returns these payloads when the agent
encounters an unknown LLVM phrase.

The same chain falls through to the LLM teacher for novel queries; the
LLM grounds them and the answer gets memoised via the standard path.

## Validation strategy

Per-phase property tests against `opt`:

1. Generate small LLVM IR snippets (or use a corpus from `llvm-test-suite`).
2. Feed the snippet to the agent — agent ingests as graph-resident IR.
3. Apply a learned pass via the agent's rule engine.
4. Render result back to LLVM IR text via the Phase-1 render rules.
5. Compare against `opt -<pass-name>` output.
6. Discrepancies → either the agent's rule is wrong (refine), or the
   discrepancy reveals a documented-but-undocumented LLVM behaviour
   (worth investigating).

This is also how the substrate observed undocumented LLVM behaviour:
disagreements between ingested-rule output and `opt` output are
information. The substrate doesn't trust documentation absolutely — it
trusts the system.

## What the agent gets when ingestion finishes

- A graph-resident LLVM IR model the agent can read, write, and modify
- A library of optimization passes as Rules the agent can introspect
  (`wonder_why InstCombine`), compose, reorder, and propose alternatives
  for
- An ISA mapping that turns LLVM IR into native bytes through the
  substrate's existing render machinery
- No runtime dependency on LLVM — the knowledge is graph data

This is the asymptote of "feed LLVM to the agent, not feed agent to
LLVM." Years of work in front of it, but each phase shipped is
permanent capability.

## First concrete step

Implement `domains/llvm_teacher.py` with a static knowledge base for
~20 foundational LLVM IR concepts (Module, Function, BasicBlock, the
arithmetic instructions, basic types). Returns
`learn_from_teacher`-shaped payloads when asked about any of them.

Wire it into the agent's impasse-resolver chain after `wiki_teacher`
(LLVM specifics aren't always on Wikipedia) and before the LLM
fallback (LLM costs money; the static knowledge base is free + faster).

Verification: agent encounters `"what is an llvm function"`, the
impasse fires, the llvm_teacher returns the payload, the agent
absorbs it as a Frame in the `llvm_ir` Microtheory, and on the next
question of the same shape the agent answers from its own Frame layer.

That closes the loop and proves the curriculum's mechanism works. Then
the bulk work is content: writing the teaching payloads for the
thousands of LLVM concepts. That's mostly mechanical — read LangRef,
write payloads, validate.

---

# Phase 3 — Transformation rule payload format

Phase 1 + 2 teach the agent *what LLVM IR is*. Phase 3 teaches it *how
to operate on it*: optimization passes as graph-resident `RewriteRule`s
the agent installs, introspects, composes, and modifies.

This section specifies (a) the substrate-side encoding of LLVM IR
itself — how a function's worth of IR becomes graph data the matcher
can pattern-match against — and (b) the teaching payload schema that
installs an optimization pass into the agent's graph as a `RewriteRule`.

The render-rule format that the agent already supports
(`agent.install_language` + `RenderRule` graph nodes, Phase 6.4) is the
direct precedent. Transformation rules are the same shape with
different effect semantics: render rules emit `Surface(Bytes)`,
transformation rules mutate the IR subgraph.

## IR encoding

LLVM IR becomes substrate graph data via the following schema. This is
the LingItFranca that all Phase-3 rules pattern-match against; the
schema must be installed before any rule that uses it.

### Node types

| Type | Role | Key attrs |
|---|---|---|
| `LLVMModule`     | Top-level translation unit            | `name`, `target_triple` |
| `LLVMFunction`   | Named code unit within a Module       | `name`, `return_type`, `linkage`, `cc` |
| `LLVMBasicBlock` | Linear instruction sequence           | `label` |
| `LLVMInstruction`| Single operation                      | `opcode`, optional flags (`nsw`, `nuw`, `exact`, `predicate`, `ordering`, `volatile`, `align`) |
| `LLVMValue`      | Anything that produces a typed result | `type`, optional `name` |
| `LLVMConstant`   | A subtype of Value with fixed bits    | `type`, `value` (int/float/bytes/sentinel) |
| `LLVMParameter`  | A function's formal arg               | `type`, `index` |
| `LLVMType`       | First-class type identity             | `kind`, `bit_width`, `address_space`, `element_type` (edge) |
| `LLVMMetadata`   | Annotation                            | `kind`, `payload` |

### Edge types

| Edge | Direction | Meaning |
|---|---|---|
| `contains`     | parent → child       | Module → Function → BasicBlock → Instruction |
| `uses_op0` … `uses_opN`  | Instruction → Value  | Operand at position N (fixed-arity ops) |
| `has_operand`  | Instruction → Operand| For variadic ops (phi, call, switch); Operand is an intermediate node with `index` attr |
| `produces`     | Instruction → Value  | The instruction's result Value (≤ 1; void instructions have none) |
| `has_type`     | Value → Type         | Every Value carries its type |
| `terminator_of`| Instruction → BasicBlock | The block's terminator |
| `successor`    | BasicBlock → BasicBlock | Static CFG edge |
| `phi_incoming` | Operand → BasicBlock | For phi nodes: which predecessor this operand came from |
| `defined_in`   | Value → BasicBlock   | Where the producing instruction lives (for dominator queries) |
| `dominates`    | BasicBlock → BasicBlock | Computed by analysis pass; cached on the graph |
| `attaches`     | Instruction → Metadata | Debug info, range info, etc. |

### Operand position — fixed vs variadic

**Fixed-arity** instructions (binary ops, comparisons, conversions,
loads, stores, etc.) get position-numbered edges: `uses_op0`,
`uses_op1`, `uses_op2`. This makes match-edges patterns clean.

**Variadic** instructions (`phi`, `call`, `switch`, `getelementptr` for
arbitrary indices, `shufflevector`'s mask) need an `LLVMOperand`
intermediate node:

```
inst -[has_operand]-> op[index=0] -[refers_to]-> value
inst -[has_operand]-> op[index=1] -[refers_to]-> value
...
```

This costs one extra node per operand but expresses arbitrary arity.
For `phi`, the Operand also carries `phi_incoming` to a block.

### Attribute conventions

- `opcode`: lowercase Sym matching LangRef (`"add"`, `"icmp"`, `"phi"`,
  `"getelementptr"`).
- `predicate`: for `icmp` / `fcmp`, lowercase Sym (`"eq"`, `"ult"`,
  `"oeq"`).
- `ordering`: for atomics, lowercase Sym (`"acquire"`, `"seq_cst"`).
- `type`: a `Sym` reference to an `LLVMType` node; for primitive
  integer types the convention is `"i32"`, `"i64"`, etc. For pointer
  types, `"ptr"` (opaque) or `"ptr<addrspace=N>"`. For aggregate types,
  a generated unique name keyed off the type's structural identity.
- `value` (on Constants): for integers, `Int(n)`; for floats,
  `Float(f)`; for null/undef/poison, `Str("null")`/`Str("undef")`/`Str("poison")`.
- `linkage`, `cc`: lowercase Sym matching LangRef.

## Pass payload schema

The `learn_from_teacher` payload extends with a new `"rule"` entry kind
alongside the existing render-rule entry. Both extend the existing
`learn_from_teacher` mechanism with no breakage to current callers.

### Concise (teacher-authored) form

```python
{
  "answer": "constant folding for integer add",
  "learn": [{
    "rule": {
      "kind": "transformation",
      "language": "llvm_ir",
      "name": "constfold_add",
      "microtheory": "llvm_passes",
      "genl_mt": "llvm_ir",
      "doc": "add(c1, c2) where both are integer constants → fold to c1 + c2.",
      "match": [
        ["?inst", "uses_op0", "?v1"],
        ["?inst", "uses_op1", "?v2"]
      ],
      "where": {
        "all": [
          {"type_of": "?inst", "is": "LLVMInstruction"},
          {"attr": ["?inst", "opcode"], "eq": "add"},
          {"type_of": "?v1", "is": "LLVMConstant"},
          {"type_of": "?v2", "is": "LLVMConstant"}
        ]
      },
      "effect": [
        # Compute the new constant value in a Let binding, then install
        # it as the replacement for the instruction's result.
        {"replace_value": {
          "old": {"produces_of": "?inst"},
          "new_node": {
            "type": "LLVMConstant",
            "attrs": {
              "value": {"add": [{"attr": ["?v1", "value"]},
                                {"attr": ["?v2", "value"]}]},
              "type": {"attr": ["?v1", "type"]}
            }
          }
        }},
        {"delete": "?inst"}
      ]
    }
  }]
}
```

The concise form is what the LLVM teacher authors. It maps directly
onto Phase-1/Phase-2 vocabulary (`uses_op0`, `LLVMInstruction`, etc.)
the agent has already learned.

### Canonical (substrate-native) form

`learn_from_teacher` compiles the concise form to the substrate's
existing `RewriteRule` shape — `match_edges`, `where: TermIdx`,
`effects: Vec<Effect>` — using the JSON Term encoding `jsonio.rs`
already implements.

Each concise `where` predicate maps to a `TermNode` JSON object:

| Concise form | Canonical `TermNode` |
|---|---|
| `{"type_of": "?x", "is": "T"}` | `Eq(TypeOf(Var("x")), Lit(Str("T")))` |
| `{"attr": ["?x", "k"], "eq": V}` | `Eq(Attr(Var("x"), "k"), Lit(V))` |
| `{"all": [P, Q, …]}` | `And([P, Q, …])` |
| `{"any": [P, Q, …]}` | `Or([P, Q, …])` |
| `{"not": P}` | `Not(P)` |
| `{"add": [a, b]}` (in attr value contexts) | `Plus(items=[a, b])` |

Each concise `effect` maps to one or a sequence of substrate `Effect`s:

| Concise effect | Canonical sequence |
|---|---|
| `{"add_edge": [s, et, t]}` | `[AddEdge { src_var: s, edge_type: et, tgt_var: t, attrs: [] }]` |
| `{"del_edge": [s, et, t]}` | `[DelEdge { … }]` |
| `{"add_node": {"var": v, "type": T, "attrs": A}}` | `[AddNode { new_var: v, type_: T, attrs: A }]` |
| `{"delete": "?v"}` | `[DelNode { var: v }]` |
| `{"set_attr": [v, k, val]}` | `[SetAttr { var: v, key: k, value: val }]` |
| `{"replace_value": …}` | **new primitive — see below** |

### The `replace_value` effect

The pattern "replace every use of OldValue with NewValue" is
fundamental to almost every LLVM transform. Expressing it as a sequence
of primitive `DelEdge` + `AddEdge` requires iterating over all uses,
which the current substrate `Effect` enum can't do in one step.

Two paths:

**(A) Add a new `Effect` variant `ReplaceValue { old_var, new_var }`.**

In `rewrite.rs`, this iterates over every `uses_op*` edge whose target
is `?old`, retargets it to `?new`. The `Apply` machinery records each
edge change for undo. Substrate-side change is ~30 LOC.

**(B) Compile `replace_value` to a HIGHER-ORDER rule.**

A meta-rule that the teacher installs once, separate from passes:

```
Rule "replace_value":
  match: [(?inst, uses_op0|uses_op1|…, ?old)]
  effect: [DelEdge(?inst, …, ?old), AddEdge(?inst, …, ?new)]
```

Then the constant-folding rule's effect just sets a `replaced_by` attr
on `?old`, and the meta-rule fires repeatedly to rewire uses.

Two-step but uses only existing primitives. Composes well with the
fixed-point semantics already in `run_rules`.

**Recommendation: ship (A).** It's small and matches the way LLVM
optimization passes are written; (B) is a curiosity that splits a
conceptually-single operation across passes.

### Worked example: full IR snippet → match → effect

LLVM IR before:
```
%result = add i32 3, 5
```

Substrate graph state:
```
add_inst : LLVMInstruction [opcode="add"]
  -[uses_op0]-> three : LLVMConstant [value=3, type="i32"]
  -[uses_op1]-> five  : LLVMConstant [value=5, type="i32"]
  -[produces]-> result : LLVMValue [type="i32", name="result"]
```

Applying `constfold_add`:

1. Matcher binds `?inst=add_inst, ?v1=three, ?v2=five`.
2. Where-clause:
   - `TypeOf(add_inst) == "LLVMInstruction"` ✓
   - `Attr(add_inst, "opcode") == "add"` ✓
   - `TypeOf(three) == "LLVMConstant"` ✓
   - `TypeOf(five) == "LLVMConstant"` ✓
3. Effects:
   - Compute `Attr(three, "value") + Attr(five, "value") = 8`.
   - Create `eight : LLVMConstant [value=8, type="i32"]`.
   - `ReplaceValue { old: result, new: eight }` — iterates over every
     `uses_op*` edge targeting `result`, retargets to `eight`.
   - Delete `add_inst` (cascade deletes its `uses_op0`/`uses_op1`/`produces`
     edges; cascade is the existing substrate behavior).

Substrate graph state after:
```
eight : LLVMConstant [value=8, type="i32"]
# add_inst, three, five, result all gone (three and five only if no
# other uses; tracking that is the orphan-cleanup pass's job).
```

LLVM IR rendered back (Phase 6 render rules):
```
; %result deleted; uses of %result now reference @eight directly
```

## What `learn_from_teacher` needs to add

The existing render-rule handling in `curious_agent.py:learn_from_teacher`
gets a parallel branch for `kind == "transformation"`:

```python
rule = entry.get("rule")
if rule and rule.get("kind") == "transformation":
    self.install_transformation_rule(
        name=rule["name"],
        microtheory=rule.get("microtheory", "llvm_passes"),
        match_edges=rule["match"],
        where_clause=self._compile_where(rule["where"]),
        effects=self._compile_effects(rule["effect"]),
    )
```

`install_transformation_rule` constructs a `RewriteRule` graph-data
representation (a `Rule` node with `match`/`where`/`effect` children)
and inserts it into the substrate's rule store. Once installed, the
substrate's `run_rules` fixed-point loop picks it up like any other
rule — semi-naive matching, JIT-able where-clauses, all the
infrastructure already in place.

`_compile_where` / `_compile_effects` recursively walk the concise
JSON into the substrate's TermNode JSON format (per `jsonio.rs`).
Roughly ~150-200 LOC of straightforward AST-to-AST translation, paired
with a Rust-side `Effect::ReplaceValue` variant (~30 LOC).

## Open questions

- **Pass ordering**: optimization quality often depends on which passes
  run before others (e.g., constant prop before DCE). The substrate's
  `run_rules` runs rules to fixed point in dirty-bit order; that's a
  fair-share schedule, not a curated pipeline. For LLVM-style pipeline
  fidelity, we'd want a sequencing primitive: install a `PassPipeline`
  node that names an ordered list of rules and a `tick_pipeline()`
  method that runs them in turn. Defer until we have ≥10 passes.

- **Worklist scheduling**: LLVM optimisers use worklists — process
  one instruction at a time, push consumers of changed values back on
  the queue. The substrate's semi-naive matcher already approximates
  this (delta edges drive re-matching). Worth measuring on actual
  passes before adding explicit worklist machinery.

- **Pass cost**: some passes (GVN, SCCP) have superlinear cost in
  function size. Need a way for the agent to bound pass execution
  (timeouts, iteration limits). The substrate's `complexity` /
  `reconsider` mechanism (graph-resident estimators per capability)
  applies directly — annotate each rule with a cost estimator,
  `tick_pipeline` checks budget.

- **Pass dependencies / preserved analyses**: GVN consumes a dominator
  tree. LLVM tracks "this pass preserves <these> analyses." For the
  substrate, dependency edges between rule nodes (`reads` /
  `invalidates` per analysis attr-kind) would let the engine know
  when to re-run an analysis. Add when the analysis-pass batch lands.

- **Profile-guided optimisation**: PGO weights cost models with
  runtime data. The substrate's observation-based discovery
  (`derived_galileo`-style) is the right machinery for ingesting
  profile data; passes that read it just check the appropriate
  attribute on their match bindings.

## Sequencing

1. **Ship `Effect::ReplaceValue`** in the Rust substrate (~30 LOC +
   test).
2. **Implement `_compile_where` and `_compile_effects`** on the Python
   teacher / agent side (~200 LOC).
3. **First pass — `constfold_add`** — full payload above as the test
   fixture. Validate against `opt -instcombine` on a hand-built IR.
4. **Constant folding for the rest of binary arithmetic**: `sub`,
   `mul`, `udiv`, `sdiv`, `urem`, `srem` — variants of the same shape.
5. **Identity elimination**: `add X, 0` → `X`; `mul X, 1` → `X`;
   `and X, X` → `X`; etc. Each is a separate Rule, all installable as
   transformation-rule payloads.
6. **DCE**: match `LLVMInstruction` with no `produces` outgoing edge
   AND no side effects → delete. One Rule, broad applicability.

That's a meaningful first slice of Phase 3 — enough rules to measurably
optimize hand-crafted IR snippets, all expressible in the format
specified above.
