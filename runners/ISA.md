# Graph Lisp Machine ISA

**Status:** Phase 17a draft — architectural specification, *no implementation
in this document*. The Rust runner at `runners/dsl/` is the current
reference implementation and the source of truth for any divergence
between this spec and observed behaviour.

**Audience:** anyone implementing a conforming runner — Rust today;
FPGA / bare-metal microcontroller / ASIC / WebAssembly / second
Rust port tomorrow. Also: anyone evaluating a code change against
the "does this respect the layer separation" test.

**Scope:** what a runner exposes. What an agent is allowed to depend
on. What a world adapter speaks to.

**Non-scope:** how a particular runner implements anything. Specific
algorithms (Knuth-Bendix, Todd-Coxeter, etc.) — those live as agent-
side rules built on this ISA.

---

## 0. The Three Layers

Three artefacts, sharply separated. Cross-layer dependencies in only
ONE direction (agent ← runner ← world; agent does not see world, world
does not see agent).

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT                                                       │
│   Pure graph data: nodes, edges, attrs, productions Γ,      │
│   rewrite rules, reflexes, learned concepts, goals, drives. │
│   Portable bytecode — a region you can memcpy to flash.     │
│   Depends ONLY on: this ISA.                                │
└─────────────────────────────────────────────────────────────┘
                            │ invokes
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ RUNNER                                                      │
│   Provides every DSL primitive (§3).                        │
│   Runs the graph: term eval, rule firing, reflex dispatch.  │
│   Exposes the world I/O contract (§7).                      │
│   Implementation is opaque — Rust, FPGA, ASIC, Wasm, etc.   │
│   Depends ONLY on: the underlying machine + memory bus.     │
└─────────────────────────────────────────────────────────────┘
                            │ I/O channels
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ WORLD ADAPTER                                               │
│   Plugs into the runner's I/O contract (§7).                │
│   Translates between runner-typed channels and the actual   │
│   external world (peripheral protocol on bare metal:        │
│   I²C / SPI / I²S / GPIO / MIPI / mmap region; PyAV /       │
│   ViZDoom / file handle on a simulator deployment).         │
│   Depends ONLY on: the runner's I/O contract + the world's  │
│   physical interface.                                       │
└─────────────────────────────────────────────────────────────┘
```

**Litmus.** Delete every line of code next to the runner binary
(no Python helpers, no shell scripts, no driver shims). Does the
agent still execute correctly given a world adapter that speaks
this ISA's I/O contract? If yes — conforming. If no — find the
layer violation.

**Reference frame.** Symbolics Genera + MIT CADR + TI Explorer +
LMI Lambda already solved most of the systems questions here.
Where this spec mirrors those traditions, the rationale is "use
proven prior art." Where it diverges (typed graph instead of cons
cells; dynamic Γ; rule-based rewrites first-class; endogenous
drives), the divergence is load-bearing.

---

## 1. Tagged Values

Every value the runner manipulates carries its type. **Twelve tags.**

| Tag         | Meaning                                       | Hardware representation hint        |
|-------------|-----------------------------------------------|-------------------------------------|
| `None`      | Absent / missing-attr default                 | Single bit pattern; immediate        |
| `Bool`      | Boolean                                       | 1 bit + tag                          |
| `Int`       | Signed 64-bit integer                         | i64                                  |
| `Float`     | IEEE-754 double                               | f64                                  |
| `Str`       | Interned symbol (see §2)                      | u32 sym handle                       |
| `Node`      | NodeID handle (see §4)                        | u32                                  |
| `Tuple`     | Heterogeneous ordered sequence of Values      | bounded array on stack; spill to heap|
| `Set`       | Hashable deduped set of Values, sorted        | sorted slice, interned by hash       |
| `FrozenSet` | Semantically identical to `Set`               | as `Set`; separate tag for round-trip|
| `Dict`      | Sorted (key, value) pairs                     | sorted slice                         |
| `Surface`   | Rendered bytes — text or raw                  | (kind: 1 bit, payload: bytes)        |
| `TermRef`   | Handle for a Term in the Term arena (§3)      | u32                                  |

**Truthy rule.** `False`, `None`, numeric zero, empty string, empty
container → falsy. Everything else → truthy. (Same rule as Python.)

**Two distinct equalities — do not conflate them.**

* **`Eq` Term semantics** (`Eq { a, b }`) — what the agent's
  predicates see. Follows IEEE-754 for `Float`: `NaN ≠ NaN`,
  `-0.0 = +0.0`. Other tags compare by content. This is the
  user-facing equality.
* **Substrate Canonical Equivalence (SCE)** — used ONLY for
  collection internals (Set / FrozenSet / Dict canonical sorted
  form), eval-cache keys, and image byte-comparison in conformance.
  `Float` is normalised first (`-0.0 → +0.0`); `NaN` is forbidden
  in any SCE-participating Value (insert is rejected at the
  control-surface boundary, emitting a `value_rejected_nan` runtime
  event — see §7.6). With NaN excluded and `±0.0` normalised, SCE
  collapses to byte-level equality on the canonical form defined in
  Appendix A.

These can legitimately differ — `Eq` is for agent logic; SCE is
for substrate book-keeping — and they MUST be referenced by name
in any future ISA clause. Mixing the two is the keystone bug the
spec used to have.

**Hashing.** Every SCE-admissible Value is hashable. Hash function
is implementation choice — the agent never sees raw hashes (only
canonical-sorted collections and `Eq` results), so cross-runner
hash divergence is fine. SCE-rejected Values (NaN) MUST raise at
insert; they cannot enter the collection in the first place.

**Total order over Values.** See **Appendix A** for the full
specification. Every operation that sorts or canonicalises Values
(Set/FrozenSet/Dict, `Pick`, `TupleSort` default comparator,
binding-order tiebreakers in §5.3) refers to the Appendix-A order
by name. *Two conforming runners produce byte-identical canonical
forms.*

**Boxing.** Implementation choice. The reference Rust runner uses
`Arc<[_]>` to make Value-clone cheap; an FPGA implementation might
use refcounted on-chip RAM regions; a bare-metal C runner might
use a slab allocator. The agent does not see boxing.

**Mandatory size limits — implementation policy.** A runner MUST
declare its maximum sizes for `Tuple`, `Set`, `Dict`, and `Surface`
in its conformance report (§9). The reference Rust runner imposes
no hard limit beyond available memory. An embedded runner may cap
`Surface` at 64 KiB, `Set` at 4096 elements, etc. Agents portable
across multiple runners SHOULD avoid exceeding the smallest
declared limit they target.

---

## 2. Symbol Interner

All `Str` Values and all type names (node-type, edge-type,
attr-key, variable-name) live in an interner. Every interned
string maps bijectively to a `Sym` (a 32-bit handle).

**Why it's load-bearing.** `Eq` on `Str` becomes `u32 == u32`. The
grammar's `(src_type, edge_type, tgt_type)` index uses Sym triples
as keys. Rule pattern variables compare in O(1). On hardware, the
interner can be a content-addressable memory.

**Sym 0 is reserved** as "empty" / "any-type" / "wildcard". The
grammar uses `Sym::default()` to mean "any edge type"; the
conformance suite includes tests for this.

**Persistence.** The interner is part of the image (§6). On
resume, the table is reconstructed; Sym handles are STABLE within
one image but NOT comparable across different images. Two images
loaded into one runner must remap their Syms through that runner's
interner.

**Implementation hint.** Open-addressing hash table; entry size
~12 bytes; typical agent uses ≤ 4096 syms (mostly node-types,
edge-types, attr-keys, a few hundred grammar rule names). Embedded
runners can fix the table at compile time if the agent's symbol
set is known.

---

## 3. DSL ISA — the Term variants

Terms are the runner's primitive operations. The agent constructs
Term trees as graph data; the runner evaluates them under an
environment binding `Var(name) → Value`.

**Term arena.** Terms are interned in a per-substrate arena and
referenced by `TermIdx` (u32). A Term tree is therefore a DAG —
shared subterms are shared in memory. The arena is part of the
image (§6).

**Eval contract.** Every Term evaluates to a Value. Evaluation is
pure: same Term + same env + same graph → same Value. (Side-effect
operations live in Rules, not Terms — see §4.) An eval cache is
permitted (and the reference runner has one) — its behaviour MUST
be transparent.

**Eval errors → None.** A Term that cannot evaluate (missing
variable, wrong-typed operand, division by zero, etc.) returns
`None`. No exceptions cross the runner boundary.

**None has two distinct sources, both surface as `None`** inline
but are distinguishable out-of-band via the `runtime_events`
channel (§7.6): a `term_eval_none` event carries the offending
Term ref + env keys (eval failure), while an `Attr`/`MapGet`
miss does NOT emit any event (legitimately absent). Agents that
need to distinguish them in agent code install a reflex on
`runtime_events` filtering for `term_eval_none`.

**None propagation rules — fixed across all CORE Terms:**

| Term family            | None handling                                                 |
|------------------------|---------------------------------------------------------------|
| `Eq`, `Lt`, `Lte`, `Gt`, `Gte`, `In` | Either operand `None` → result `None`           |
| `And { items }`        | Short-circuit on first falsy (including `None`); `None` is falsy. Returns last truthy (or `False` if any falsy encountered before a truthy). |
| `Or { items }`         | Short-circuit on first truthy; `None` is falsy and skipped without poisoning. Returns first truthy (or `False` if exhausted). |
| `Not { arg }`          | `Not(None)` = `True` (None is falsy).                         |
| `Arithmetic` (Plus / Times / Minus / Div / etc.) | Any `None` operand → result `None`.   |
| `Reductions` over a set with `None` per-element results | The element's contribution is SKIPPED (Sum / Prod use identity; Count omits; MinOver/MaxOver ignore; Filter / Exists treat `None` predicate as falsy). |
| `IfThenElse`           | `cond=None` (falsy) → takes the `other` branch.                |

These rules are CORE-mandatory — runners may not vary them. The
table is the conformance test reference.

### 3.1 Term variants — current set

Variant counts may grow as the agent's needs surface. A runner
MUST implement every variant in this list to be conforming.

The CORE Term inventory is grouped here for readability; the
**authoritative numbered list is §3.1.2 below.** Group labels are
descriptive, not normative; group counts in `(N)` reflect the
actual member count.

**Bindings and access** (4):
- `Var { name: Sym }` — lookup `name` in env.
- `Lit { value: Value }` — embed a literal Value.
- `TypeOf { node }` — node's type as a `Str`.
- `Attr { node, key: Sym }` — node's `key` attr, or `None` if absent.

**Collections** (2):
- `SetT { items: Vec<TermIdx> }` — build a `Set` Value.
- `In { member, container }` — membership test.

**Comparators** (5):
- `Eq { a, b }`, `Lt { a, b }`, `Lte { a, b }`, `Gt { a, b }`, `Gte { a, b }`.

**Graph traversal** (3):
- `Neighbours { node, edge_type, any_type }` — outgoing neighbours
  along `edge_type`. `any_type=true` ignores the type filter.
- `InNeighbours { node, edge_type, any_type }` — incoming.
- `MapNeighbours { source, edge_type, any_type }` — flat-map over
  set, each element's neighbours.

**Reductions** (8):
- `Count { source }`, `Filter { source, var_name, predicate }`,
  `Exists { source, var_name, predicate }`, `Sum { source, var_name, value }`,
  `Prod { source, var_name, value }`, `MinOver { source, var_name, value, default }`,
  `MaxOver { source, var_name, value, default }`, `Pick { source }`.

**Concept lookup + Term reflection** (2):
- `Holds { concept: Sym, node, node2 }` — invoke a graph-resident
  concept Term-tree by name (see §3.4).
- `EvalSubgraph { node }` — evaluate the Term-tree rooted at the
  NodeID `node` resolves to. The substrate's "execute what this
  attr/edge points to" primitive (Phase 17b.1). See
  [[ozma-evalsubgraph-primitive]].

**Boolean** (3):
- `And { items }`, `Or { items }`, `Not { arg }`.

**Arithmetic** (11):
- `Abs { arg }`, `Neg { arg }`, `Plus { items }`, `Minus { a, b }`,
  `Times { items }`, `Div { a, b }`, `Mod { a, b }`, `Pow { a, b }`,
  `Sqrt { arg }`, `Min { items }`, `Max { items }`.

**Control** (1):
- `IfThenElse { cond, then, other }`.

**Geometry — N-D vectors** (5):
- `Vec_ { items }` (build Tuple as vector), `VecAdd { a, b }`,
  `VecSub { a, b }`, `Dot { a, b }`, `Magnitude { arg }`.

**Angle / rotation** (6):
- `Sin { arg }`, `Cos { arg }`, `Atan2 { y, x }`, `Bearing { arg }`,
  `Rotate { vec, angle }`, `AngleBetween { a, b }`.

**Set algebra** (4):
- `Union { a, b }`, `Intersect { a, b }`, `Difference { a, b }`,
  `MapSet { source, var_name, value }`.

**Edge-attr access** (3):
- `Edges { node, edge_type, any_type }` — set of edge handles
  `(src, edge_type, tgt)`.
- `EdgeAttr { edge, key }` — read attr from an edge handle.
- `NodesWhere { node_type, attr_key, value }` — indexed reverse
  lookup; O(1) if the index has been declared via the runtime
  control surface (§8), linear-scan fallback otherwise.

**Rendering — text + byte surfaces** (15):
- `Surface { kind, payload }`, `Cat { items }`, `Slot { name }`,
  `Join { separator, items }`, `Bytes { items }`, `U8 { expr }`,
  `U16LE { expr }`, `U32LE { expr }`, `U64LE { expr }`,
  `LEB128 { expr }`, `Lines { items }`, `Label { prefix }`,
  `Let { name, value, body }`, `Nth { items, index }`,
  `Render { term, lang }`.

**Group subtotal:** 4 + 2 + 5 + 3 + 8 + 2 + 3 + 11 + 1 + 5 + 6 + 4
+ 3 + 15 = **72 base CORE Terms**.

### 3.1.1 Core primitives — Phase 17a additions

These cover gaps the existing 30 cannot express. Every runner MUST
implement them. Total: **30 new core Terms** bringing CORE to ≈ 60.

**Bitwise** (6) — codec / fingerprint / hash work. Trivial on every CPU.
- `BitAnd { a, b }`, `BitOr { a, b }`, `BitXor { a, b }`.
- `BitShl { value, n }`, `BitShr { value, n }` — logical shift.
- `Popcount { arg }` — bit-population count of an `Int`.

**Ordered-sequence ops on Tuple** (5) — Tuples are already the
ordered sequence type; these expose operations on them. (Set is
unordered; sequence ops on Set don't apply.)
- `TupleLen { tuple }` → `Int`.
- `TupleSlice { tuple, start, end }` → `Tuple` (half-open).
- `TupleReverse { tuple }`.
- `TupleConcat { items }` → flat-concat of N tuples.
- `TupleSort { tuple, key: Option<TermIdx>, var_name: Sym }` — stable
  sort, with optional key Term evaluated per element under `var_name`.

**String operations** (3) — minimal set; locale-dependent ops (case
folding, Unicode normalisation) deliberately out of scope.
- `StrLen { str }` → `Int` (byte length).
- `StrSlice { str, start, end }` → `Str` (half-open, by byte).
- `StrIndexOf { haystack, needle }` → `Int` (-1 if not found).

**Byte-buffer access** (4) — for parsing world-adapter data without
a Python middleman.
- `BytesLen { surface }` → `Int`.
- `BytesAt { surface, offset }` → `Int` (single byte, 0–255).
- `BytesSlice { surface, offset, n }` → `Surface(Bytes, _)`.
- `BitsAt { surface, bitpos, n }` → `Int` — read `n` bits MSB-first
  starting at bit-offset `bitpos`. The substrate primitive the
  Phase-16 codec work needed.

**Maps — constructors and access** (3) — Dict Values exist already
but were attr-only; these promote them to first-class.
- `MapT { entries: Vec<(TermIdx, TermIdx)> }` → `Dict`.
- `MapGet { map, key }` → Value (`None` if absent).
- `MapKeys { map }` → `Set` of keys.

**Type conversion** (3) — explicit, no implicit coercion.
- `IntToFloat { arg }`.
- `FloatToInt { arg }` — truncates toward zero.
- `StrToInt { arg, radix: TermIdx }` → `Int` (`None` on parse fail).

**Hash** (1).
- `Hash { value }` → `Int` (deterministic across runs of the SAME
  runner; NOT guaranteed across runners — see §1 hashing notes).

**Value introspection** (1).
- `ValueTag { value }` → `Str` — returns the tag name as an
  interned Sym ("Int", "Set", "Node", etc.). Replaces a family of
  `IsX` predicates with one Term + `Eq` comparison.

**Runtime — time + randomness + diagnostics** (4) — the only
Terms whose evaluation is NOT pure under the §3.2 sense. Runners
MUST surface them honestly: deterministic re-evaluation cache
MUST NOT be applied to these tags or to any Term whose tree
transitively contains them.
- `Now {}` → `Int` — monotonic ticks since runner boot; tick rate
  declared in conformance report (default µs, ≥1 µs resolution).
  **Conformance mode** (§9.1): the synthetic world supplies a
  virtual clock — `Now` returns the world-declared tick value,
  not wall time. This is mandatory; without it, agents that store
  `Now` into the graph produce non-reproducible images and
  conformance is unsatisfiable.
- `Rand {}` → `Float` in `[0.0, 1.0)`. Pseudorandom. Seed mode is
  declared in the runner conformance report (`rand_seed_mode`):
  `"deterministic"` (seed in agent image header — for replay
  /conformance) or `"entropy"` (runner-provided — for production
  use). **Conformance mode requires `"deterministic"`**: the
  golden suite (§9.1) declares the seed and asserts the agent's
  post-state with that seed.
- `RandInt { lo, hi }` → `Int` in `[lo, hi)`.
- `Trace { label: Sym, value: TermIdx }` → returns `value`
  unchanged; side-effect is to emit a diagnostic record
  `(now, label, evaluated_value)` to the runner's diagnostic
  output channel (a built-in `Out` channel — see §7.6). The agent
  can read these back through the diagnostic input channel when
  introspecting its own behaviour.

### 3.1.2 Authoritative CORE inventory — the conformance contract

The conformance suite (§9) tests one variant at a time and asserts
identical post-state across runners. To make that suite well-
defined, this is the **single authoritative numbered enumeration**
of CORE Term variants. Any future revision adds to the END of this
list with a new index (additions are minor-version bumps);
re-numbering is a major bump.

| #  | Variant         | #  | Variant            | #  | Variant         |
|----|-----------------|----|--------------------|----|------------------|
| 1  | Var             | 35 | Pow                | 69 | Render           |
| 2  | Lit             | 36 | Sqrt               | 70 | BitAnd           |
| 3  | TypeOf          | 37 | Min                | 71 | BitOr            |
| 4  | Attr            | 38 | Max                | 72 | BitXor           |
| 5  | SetT            | 39 | IfThenElse         | 73 | BitShl           |
| 6  | In              | 40 | Vec_               | 74 | BitShr           |
| 7  | Eq              | 41 | VecAdd             | 75 | Popcount         |
| 8  | Lt              | 42 | VecSub             | 76 | TupleLen         |
| 9  | Lte             | 43 | Dot                | 77 | TupleSlice       |
| 10 | Gt              | 44 | Magnitude          | 78 | TupleReverse     |
| 11 | Gte             | 45 | Sin                | 79 | TupleConcat      |
| 12 | Neighbours      | 46 | Cos                | 80 | TupleSort        |
| 13 | InNeighbours    | 47 | Atan2              | 81 | StrLen           |
| 14 | MapNeighbours   | 48 | Bearing            | 82 | StrSlice         |
| 15 | Count           | 49 | Rotate             | 83 | StrIndexOf       |
| 16 | Filter          | 50 | AngleBetween       | 84 | BytesLen         |
| 17 | Exists          | 51 | Union              | 85 | BytesAt          |
| 18 | Sum             | 52 | Intersect          | 86 | BytesSlice       |
| 19 | Prod            | 53 | Difference         | 87 | BitsAt           |
| 20 | MinOver         | 54 | MapSet             | 88 | MapT             |
| 21 | MaxOver         | 55 | Edges              | 89 | MapGet           |
| 22 | Pick            | 56 | EdgeAttr           | 90 | MapKeys          |
| 23 | Holds           | 57 | NodesWhere         | 91 | IntToFloat       |
| 24 | EvalSubgraph    | 58 | Surface            | 92 | FloatToInt       |
| 25 | And             | 59 | Cat                | 93 | StrToInt         |
| 26 | Or              | 60 | Slot               | 94 | Hash             |
| 27 | Not             | 61 | Join               | 95 | ValueTag         |
| 28 | Abs             | 62 | Bytes              | 96 | Now              |
| 29 | Neg             | 63 | U8                 | 97 | Rand             |
| 30 | Plus            | 64 | U16LE              | 98 | RandInt          |
| 31 | Minus           | 65 | U32LE              | 99 | Trace            |
| 32 | Times           | 66 | U64LE              |    |                  |
| 33 | Div             | 67 | LEB128             |    |                  |
| 34 | Mod             | 68 | Lines              |    |                  |

Plus:
| #  | Variant         |
|----|-----------------|
| 100 | Label          |
| 101 | Let            |
| 102 | Nth            |
| 103 | Argmax         |
| 104 | Argmin         |
| 105 | BitsAt         |
| 106 | BitsWrite      |
| 107 | ExpGolombDecode |
| 108 | ExpGolombDecodeSigned |
| 109 | ExpGolombEncode |
| 110 | ExpGolombEncodeSigned |
| 111 | BitsWriteAll   |
| 112 | BitsAtAll      |

**CORE total: 112 variants.**

Argmax / Argmin added Phase 17b.3c.4 — return the ELEMENT of `source`
for which `value` is maximum / minimum (distinct from MaxOver /
MinOver which return the value itself). Needed for top-cause /
top-candidate selection rules without a recompute-after-max
workaround.

BitsAt / BitsWrite added Phase 16b/c — universal bit-field read /
write on `Surface(Bytes)` Values. Every binary format / codec /
network protocol needs them; promoted to CORE rather than the
codec-specific feature block because they are codec-agnostic.

BitsWriteAll / BitsAtAll added Phase 16c.2 — vectorised batches over
many bit-fields against a single buffer. `BitsWriteAll(buffer,
[(bp, val, nb), ...])` applies N writes in ONE buffer copy;
`BitsAtAll(buffer, [(bp, nb), ...])` reads N fields in ONE
runner call. Critical for bulk codec ops (JPEG DQT, multi-field
PPS rewrites, Huffman table swaps) — the per-call BitsWrite copies
the whole buffer each invocation, so 64 sequential writes on an
86 KB buffer take ~22 ms (5.5 MB of copying + Python↔Rust
overhead); the batched form takes ~1.2 ms (one copy, one round-
trip). 18x speedup at this size, scales with buffer-size × call-
count.

ExpGolombDecode / ExpGolombDecodeSigned / ExpGolombEncode /
ExpGolombEncodeSigned added Phase 16c — universal Exp-Golomb
variable-length entropy coding (ITU-T H.264 §9.1 ue(v) and §9.1.1
se(v)). Unsigned codeword: M leading zeros, 1-bit marker, M-bit
suffix; value = 2^M - 1 + suffix. Signed variant maps the unsigned
codeword via k → (k odd ? +ceil(k/2) : -k/2). Every H.264 / HEVC /
VVC / AVS3 field that isn't fixed-width is se(v) or ue(v); promoted
to CORE because it is codec-agnostic (not specific to any single
codec's table). A runner that exposes Exp-Golomb + Huffman + bit
read/write can express every video / image / audio entropy-coded
transcode shape as graph-resident Rules.

### 3.3.1 `huffman` feature block — implemented (Phase 16b/c)

The `huffman` block from §3.3's catalogue is the first feature
block implemented. Two Term variants, both consume graph-resident
`HuffmanTable` nodes:

* `HuffmanDecodeStream { buffer, bitpos, table, n_pairs }` →
  `Tuple(pairs_tuple, new_bitpos)`. Walks Huffman tree per pair
  using the table's `codes` + `hlens` attrs; handles linbits
  escapes; reads sign bits for non-zero values.
* `HuffmanEncodeStream { buffer, bitpos, pairs, table }` →
  `Tuple(new_buffer, new_bitpos)`. Mirror — writes Huffman code
  + linbits + sign bits per pair into a fresh buffer copy.

Combined with `BitsAt` / `BitsWrite`, these express MP3
requantize, H.264 QP-bump, JPEG transcoding, Vorbis bitrate
change, FLAC predictor switch — every Huffman-coded transcode
shape — as Rules + per-codec graph structure, no per-codec
runner primitives needed.

The agent learns new codecs by minting new `HuffmanTable` nodes +
writing Rules that compose these primitives over the new codec's
graph structure. No runner changes.

- **Base set (§3.1):** Terms 1–72. Implemented in the reference
  Rust runner today (`runners/dsl/src/term.rs`).
- **Phase 17a additions (§3.1.1):** Terms 70–99 (30 variants) +
  100–102 (rendering tail that was always present but moved here
  for numbering hygiene). Specified; partially implemented.

Per the conformance contract (§9), a runner MUST recognise every
tag-name in this table and produce the §A test-vector results for
each. Two runners on this enumeration produce identical
canonicalised images for identical operation sequences.

### 3.2 Term operational semantics

Four properties every Term-tree evaluation MUST satisfy.

**Determinism.** Same Term tree + same env + same graph state →
identical Value. Two conforming runners produce byte-identical
results for INTEGER, BOOLEAN, NODE, STR, SET, TUPLE, DICT, BYTES
Values. For FLOAT Values, byte-identical for scalar arithmetic per
the IEEE-754 mandate below; "within declared tolerance" for
feature-block-accelerated ops.

**Exception — Runtime Terms.** §3.1.1 Runtime Terms (`Now`,
`Rand`, `RandInt`, `Trace`) are inherently non-pure and MUST be
exempted from any eval-cache. Runners track which Terms in a tree
transitively depend on a Runtime Term and skip caching for them.

**IEEE-754 mandate (scalar Float ops).** For all scalar float
operations (`Plus`, `Minus`, `Times`, `Div`, `Pow`, `Sqrt`,
`Magnitude`, `Dot`, `VecAdd`, `VecSub`, `Mod` on float operands,
plus comparators on floats): MUST conform to IEEE-754 binary64
with round-half-to-even (RNE). Most CPUs (x86/AMD64, ARMv7+,
RISC-V with F+D, POWER) comply natively; FPGA / ASIC runners use
a compliant float core (proven open-source IP exists).

**Transcendentals — bounded precision.** `Sin`, `Cos`, `Atan2`,
`Sqrt` (and any future transcendental) are NOT bit-reproducible
across runners (the libm tradition does not constrain this).
Conformance: result MUST be within **1 ULP** of the correctly-
rounded value, tested at golden input points published with the
conformance suite (§9). Agents that need bit-reproducibility for
transcendentals must compute them via rules over scalar IEEE ops.

**Feature-block float ops — declared tolerance.** Block ops
(`tensor.MatMul`, `dsp.FFT`, etc.) have per-block tolerance
declared in the conformance report (§9.3 `block_tolerances`).
Default `1e-9` relative for tensor / dsp; `0` (bit-exact) for
crypto / huffman / bitwise.

**Termination bound.** Every Term-tree evaluation completes in
finite steps proportional to (1) the tree depth and (2) the size
of the set being reduced over. No unbounded recursion (Terms have
no self-reference). `Holds` invocations bound recursion through a
maximum call depth declared by the runner (default: 64; see §3.4).

**No side effects beyond Runtime Terms.** Term eval never mutates
the graph, the interner, or the arena. (Graph mutation lives in
Rules, §4.) Runtime Terms (`Now`, `Rand`, `RandInt`, `Trace`) have
the only permitted side effect — `Trace` writes a diagnostic
record to channel 0 (§7.6); the other three READ runner-managed
state (clock / RNG) and return a fresh Value each call. An
implementation MAY cache pure (non-Runtime-touching) Term results;
runners MUST taint cache entries that transitively depend on any
Runtime Term and skip caching those. Correctness must not depend
on the cache being hit or missed for pure Terms.

### 3.3 Optional Feature Blocks

Same shape as CPU ISA extensions (SSE / AVX / NEON) or GPU shader
models. Each block is a named bundle of Terms that a runner MAY
implement. Within a block, the agent uses the same Term names
regardless of the underlying hardware — falls back to scalar
software on a CPU runner, dispatches to silicon on an accelerated
runner.

**Why optional, not core.** Each block represents capability that
some target hardware has (GPU / TPU / DSP / SoC codec block /
crypto co-pro) but bare-metal microcontroller targets do not.
Forcing them into CORE would either bloat the smallest deployment
or force every embedded runner to ship a slow scalar fallback for
operations it will never execute.

**Behavioural contract.** When a runner implements a block, the
Terms in that block MUST produce results equivalent to the
scalar reference semantics (also published with the block spec).
Equivalence is byte-identical for integer / discrete ops; for
floating-point ops, "within block-declared tolerance" (e.g., FFT
within `1e-6` relative error).

**Block catalogue — Phase 17a:**

| Block | Members | Reference semantics | Hardware archetype |
|---|---|---|---|
| `tensor` | `MatMul`, `BatchMatMul`, `Conv1D`, `Conv2D`, `Conv3D`, `Transpose` | naïve nested loops on Tuples-of-Tuples or attr-byte tensors | GPU shader / TPU systolic array / NPU |
| `dsp` | `FFT`, `IFFT`, `FIR`, `IIR`, `Resample`, `Decimate` | naïve scalar implementations | DSP chip / SIMD / FPGA fabric |
| `simd` | `VecAddN`, `VecMulN`, `VecReduceSum`, `VecReduceMax` on large Tuples | element-wise scalar loop | SSE / AVX / NEON / SVE |
| `crypto` | `Sha256`, `Sha512`, `Crc32`, `Aes`, `SecureRand` | software reference (e.g., RustCrypto) | AES-NI / SHA-NI / TRNG / smart-card crypto co-pro |
| `image` | `ImgResize`, `BlitRect`, `ColorConvert`, `JpegDecode`, `JpegEncode` | software reference (e.g., libjpeg-turbo) | GPU 2D / ISP / dedicated image co-pro |
| `huffman` | `HuffDecode { stream, table }`, `HuffEncode { values, table }` | scalar bit-walk using graph-resident `HuffmanTable` nodes (§1's `Sym` interner gives us byte-keyed table lookup) | SoC codec block (H.264 / JPEG) — many embedded SoCs expose one |
| `mdct` | `MDCT { samples, window }`, `IMDCT { coeffs, window }` | scalar nested loops | Audio DSP / FPGA |
| `motion` | `MotionEstimate { ref_frame, cur_frame, block_size }`, `MotionCompensate { ref, mv }` | scalar block-matching | Video codec block on SoC |
| `nn` | `Relu`, `Sigmoid`, `Softmax`, `LayerNorm`, `Embedding` | scalar element-wise | NPU / GPU |

This list is open. New blocks land via the same versioning rule as
core Terms (§9.4): additions are minor bumps; removals are major.

**Block declaration.** A runner publishes the blocks it implements
in its conformance declaration:

```
RunnerConformance {
    isa_version: "17a-draft",
    implementation_id: String,
    feature_blocks: Set<String>,   // e.g. {"tensor", "huffman", "dsp"}
    block_tolerances: Map<String, f64>,   // float-tol per block; default 1e-9
    ...other fields from §1, §9.3...
}
```

The agent's image declares its required and preferred blocks:

```
AgentImageHeader {
    isa_version: "17a-draft",
    required_blocks: Set<String>,
    preferred_blocks: Set<String>,
    ...other fields...
}
```

**Load-time check.** Loading an agent into a runner verifies
`agent.required_blocks ⊆ runner.feature_blocks`. Mismatch →
refuse-to-load. `preferred_blocks` mismatch is a warning; agent
runs with fallback semantics (if the runner provides them — e.g.,
a runner without `dsp` MAY still expose `FFT` via scalar
software, declaring it as scalar).

**Per-block conformance sub-suites.** Each block has its own
golden-output test set (analogous to §9.2 core conformance). A
runner claims a block iff it passes the sub-suite for that block.
Cross-runner portability is per-block: an agent that uses
`huffman` runs on every runner that passes the `huffman`
sub-suite, scalar or hardware.

**Strategic implication.** The `huffman` + `mdct` + `motion`
blocks are exactly what Phase 16 (MP3 + H.264 transrate) was
trying to build in Python. Promoting them to optional ISA blocks
means:

- Bare-metal runner on an SoC with H.264 silicon → uses hardware
  Huffman + motion blocks → transrate at line rate.
- Bare-metal runner on a microcontroller → scalar fallback.
- Reference Rust runner → Rust software implementation.
- *Same agent runs on all three.*

The codec work that has been Python-trapped becomes substrate
work, properly graph-routed.

### 3.4 Concept resolution — how `Holds` works

The `Holds { concept: Sym, node, node2 }` Term invokes a
graph-resident concept Term-tree by name. The resolution mechanism
must be specified so two runners produce identical eval results.

**Resolution rule.** A concept is a node of type `"Concept"`
carrying:

- `name: Str` — the agent-given concept name (matched against
  `Holds.concept`).
- `body: TermRef` — handle into the Term arena referencing the
  concept's body Term tree.
- `arity: Int` — 0, 1, or 2; matches the number of `node` / `node2`
  arguments the body expects.
- `env_names: Tuple<Str>` — names the body uses to access its
  arguments. Conventionally `("self",)` for arity-1 and
  `("self", "other")` for arity-2; agent-defined otherwise.

**The runner maintains a Concept name index** — `Map<Sym, NodeID>`
keyed by Concept node `name` attr. This is one of the runner's
mandatory built-in attr-indexes; declared automatically at startup
(the agent doesn't need to call `declare_attr_index` for it).

**Evaluation steps:**

1. Look up `Holds.concept` in the Concept name index → `NodeID`.
2. If not found → return `None`. (Honest absence; agent can test.)
3. Read the Concept's `body: TermRef` and `env_names` attrs.
4. Build child env: bind `env_names[0] → node`, `env_names[1] → node2`
   (skipping unbound slots).
5. Evaluate `body` Term under the child env (NOT the parent env —
   concept evaluation is lexically scoped to its `env_names`).
6. Return the result.

**Recursion bound.** `Holds` recursion is bounded by the runner's
declared `holds_recursion_depth` (default 64; see §9.3). Exceeding
the bound → `None` (and emits a runtime event on the diagnostic
channel — see §7.6).

**Arity validation.** A Concept's `arity` MUST match the count of
non-`None` `env_names` (validated at Concept-node insert: mismatch
→ admissibility rejection + `concept_arity_mismatch` runtime
event). Argument supply rules:

* `Holds.node` MUST be present iff `arity >= 1`. Missing when
  required → `None` + `holds_arity_under_supplied` event.
* `Holds.node2` MUST be present iff `arity == 2`. Missing when
  required → same.
* `Holds.node` / `node2` supplied when arity is lower (e.g. arity
  0 with both supplied) → the extras are IGNORED; a
  `holds_arity_over_supplied` event is emitted at info verbosity
  only. (Tolerant for refactor-friendliness; honest via the
  event.)

**Hot code update implication.** A Concept node can be edited (or
replaced) by the agent while running. Subsequent `Holds`
invocations see the new body immediately — the eval cache
invalidates any cached eval that touched the changed Concept.
This is the same property that classical Lisp machines had via
`advise`-style indirection: behaviour rewrites are first-class.

**Why TermRef as a Value tag.** Without it, a Concept's body would
have to be encoded as a Tuple-of-Tuples (a serialised Term tree),
which the runner would parse-back-to-TermRef on every `Holds`
call. Adding TermRef as a tag lets the agent author Concept
bodies once, hand the runner a TermRef directly, and skip parsing
on every invocation. The `Lit { value: TermRef(idx) }` Term is the
canonical way to embed a Term reference inside another Term.

**Phase-15c PragmaticConcept compatibility.** The current Python
`PragmaticConcept` nodes carry `definition_term` as a serialised
dict. Phase 17b's Holds implementation will introduce a migration:
on substrate load, walk all PragmaticConcept (and similar) nodes
and convert `definition_term` dicts to TermRef Values, retyping
nodes to canonical `"Concept"` shape.

---

## 4. Graph Memory Model

The graph is the runner's primary data structure. Everything else
(rules, productions, Term arena, interner) lives alongside it as
separately-tagged regions of the image.

### 4.1 Nodes

A node is `(NodeID, type: Sym, attrs: Map<Sym, Value>)` plus
implicit substrate-managed fields (§4.1.1).

- `NodeID` is a **generational handle**: `(index: u24, generation:
  u8)` packed into a u32 (or `(u32, u32)` on larger targets). Slot
  reuse increments the generation; a stale `NodeID` (mismatched
  generation) resolves to `None` (see §4.4 below).
- `type` is a Sym (intern'd type name like `"AudioFrame"`,
  `"Mp3Granule"`).
- `attrs` is keyed by Sym, values are tagged Values.
- The runner maintains a `nodes-of-type` index `Sym → Vec<NodeID>`
  for O(1) "give me all nodes of type T."
- An attr index `(type: Sym, attr_key: Sym) → Map<Value, Set<NodeID>>`
  MAY be declared explicitly to accelerate `NodesWhere`. Undeclared
  indexes mean `NodesWhere` linear-scans.

**Mutation surface.** `add_node`, `set_attr`, `remove_node`,
`set_type`. All exposed through the runtime control surface (§8).
All mutations enforce admissibility against Γ (see §5.2).

### 4.1.1 Substrate-managed implicit fields (every node)

Every node carries two implicit fields the agent may READ but
cannot directly set — they are written by the substrate at
construction:

| Field             | Type | Meaning                                                              |
|-------------------|------|----------------------------------------------------------------------|
| `created_at_seq`  | Int  | Monotonic insertion sequence number. The Nth node ever created (across all types) has `created_at_seq = N`. Survives save/load — image (§6) serialises this verbatim and load restores it. |
| `created_at_tick` | Int  | `Now()` value at construction. Convenience read-only.                |

`created_at_seq` is the **canonical cross-runner identity** for a
node. It depends ONLY on the operation sequence the runner has
processed, not on freelist behaviour or any other implementation
choice. SCO compares `Node` Values by `created_at_seq` (see
Appendix A.2), and §5.3 binding-order tiebreakers do the same.
Raw `NodeID` is NEVER used for cross-runner-stable comparison.

Agents see these fields as standard attrs via `Attr(node,
"created_at_seq")` and `Attr(node, "created_at_tick")`. Setting
them via `set_attr` is rejected with a `reserved_attr` runtime
event.

### 4.1.2 Allocation discipline (informative — not constraining)

A conforming runner MAY use any allocation strategy for the
underlying slab (lowest-free-slot, LIFO freelist, bump allocator,
arena, etc.) — the choice does NOT affect cross-runner determinism
because the canonical identity is `created_at_seq`, not `NodeID`.
This is the explicit resolution of the prior contradiction between
§4.3 (allocation freedom) and §5.3 (deterministic binding order).

### 4.2 Edges

An edge is `(EdgeKey, attrs: Map<Sym, Value>)` where
`EdgeKey = (src: NodeID, edge_type: Sym, tgt: NodeID)`.

- Edges are directed.
- Multi-edges (same `EdgeKey`) are deduped — adding an existing
  edge is idempotent (updates attrs if differing).
- Per-node fast neighbour lookup: outgoing and incoming edge lists,
  each a small-vec of `EdgeIdx`.

**Mutation surface.** `add_edge`, `remove_edge`, `set_edge_attr`.
Same admissibility check as nodes.

### 4.3 Memory layout (recommended for hardware implementations)

The reference Rust runner uses slab-allocated `Vec<Option<_>>` with
freelists. For hardware:

- **Node region** — array of fixed-size node records; freelist of
  released slots; node-type-to-IDs index in parallel structure.
- **Edge region** — array of fixed-size edge records; per-node
  out-edge and in-edge index arrays.
- **Attr region** — keyed by `(NodeID, Sym)` or `(EdgeIdx, Sym)`;
  open-addressing hash table per node is one option.
- **Sym interner region** — separately addressable; CAM on FPGA.
- **Term arena region** — separately addressable; reference-shared.
- **Image header** — version + section bounds + magic; see §6.

Embedded runners SHOULD fix region sizes at compile time. The agent
can interrogate its limits via §8 control surface attrs on `agent_root`.

### 4.4 Frozen vs free slots — generational safety

Both node and edge regions have freelists. **Generational handles
(§4.1) eliminate the stale-handle UB the first draft had.** When a
slot is freed and later reused, the generation increments. A stale
`NodeID` whose generation does not match the slot's current
generation resolves to `None` — same honest-absence model as
missing attrs. No garbage reads.

This makes `Node` values safe to store in attrs without runtime
ceremony — a parent-pointer / cross-reference attr that survives
the referent's deletion just reads as `None`, exactly like an
unset attr. The agent observes the dangling reference and decides
what to do (re-resolve, prune, signal a runtime event).

The image format (§6) preserves generations across save/load —
load DOES NOT reset generations to 0, because doing so would let a
post-load `add_node` accidentally re-validate a stale pre-save
handle stored in some surviving attr.

**Embedded `Node` values in attrs ARE rewritten by save/load** —
see §6.3 for the renumber-map contract. A `Node` attr that was
valid before save remains valid after load (its `NodeID` may have
new bits, but the rewrite map updates every embedded reference).
This closes the prior corruption hole.

### 4.5 Storage Tiers — graph memory IS a hierarchy

The graph is not a flat memory; it's a hierarchy. Modern hardware
ALWAYS has one (L1 / L2 / L3 / RAM / SSD / network), and the
substrate exposes the hierarchy as graph data so the agent can
introspect and manage it. There is no special "blob region" — big
data goes to a slower tier; hot data lives in a fast tier; the
agent's memory-architecture rules ([[ozma-memory-architecture]])
decide policy. The runner only provides the primitives.

**StorageTier nodes.** At startup, the runner mints one
`StorageTier`-typed node per available tier (visible at
`nodes("StorageTier")`). Standard attrs every tier publishes:

| Attr                  | Type   | Meaning                                                |
|-----------------------|--------|--------------------------------------------------------|
| `name`                | Str    | Tier label (e.g. `"L1"`, `"RAM"`, `"flash"`, `"net"`) |
| `index`               | Int    | Ordinal (0 = closest to compute; ascending = slower)  |
| `latency_ns`          | Int    | Typical access latency in nanoseconds                  |
| `bandwidth_mb_s`      | Int    | Typical bandwidth in MB/s                              |
| `capacity_bytes`      | Int    | Total capacity                                         |
| `used_bytes`          | Int    | Current usage (live-updated by the runner)             |
| `persistent`          | Bool   | Survives a power cycle?                                |
| `survives_image_load` | Bool   | Tier contents preserved across `save`/`load`?         |
| `coherence`           | Str    | `"strict"` / `"eventual"` / `"weak"` / `"no-cache"`   |
| `access_pattern`      | Str    | `"random"` / `"sequential"` / `"append-only"`         |
| `pinned`              | Bool   | True iff nodes assigned here cannot be migrated out    |

Runners MAY add their own tier-specific attrs (e.g. a network tier
might publish `endpoint_url`, `auth_kind`; a flash tier might
publish `erase_block_size`). Agents that don't recognise the extra
attrs ignore them; that's fine.

**Standard tier names — recommended.** Runners SHOULD use canonical
names where they apply, so agents written against one runner have
something predictable to query on another:

| Name        | Typical hardware                          |
|-------------|--------------------------------------------|
| `"L1"`      | CPU L1 cache region / FPGA distributed RAM |
| `"L2"`      | CPU L2 cache                               |
| `"L3"`      | CPU L3 / FPGA block RAM                    |
| `"SRAM"`    | On-chip SRAM (microcontroller)             |
| `"RAM"`     | Main DRAM                                  |
| `"flash"`   | Internal flash (microcontroller / SoC)    |
| `"SSD"`     | Local SSD / NVMe                           |
| `"disk"`    | Spinning disk / network-attached SAN       |
| `"net"`     | Remote object store (S3 / GCS / etc.)      |

A bare-metal microcontroller deployment typically publishes
`SRAM` + `flash`. A hosted simulator typically publishes
`RAM` + `SSD`. An FPGA might publish `BRAM` + external `DDR`.

**Per-node tier assignment.** Every node carries a built-in attr
`storage_tier: Str` — the name of the tier currently holding its
data. Reading it is one attr lookup; comparing across nodes is one
Sym comparison. New nodes default to tier `"RAM"` (or the runner's
fastest writable non-pinned tier if `"RAM"` is absent — bare metal
might pick `"SRAM"`).

**Migration primitives — runtime control surface (§8 additions):**

```
storage_tiers() → Vec<NodeID>                       // enumerates StorageTier nodes
migrate_node(nid: NodeID, target_tier: Sym) → bool | Err
pin_node(nid: NodeID, tier: Sym) → bool             // refuses migration out
unpin_node(nid: NodeID) → bool
```

A migration may fail (target tier full, target tier read-only,
node pinned, target tier doesn't support the node's attr types —
e.g. transient tiers don't accept `TermRef` attrs). Failure
returns a typed error and emits a `migration_rejected` runtime
event (§7.6).

**Pinned nodes.** Some nodes MUST stay in fast tiers — `agent_root`,
grammar Γ productions, the Term arena entries currently being
evaluated, hot Concept bodies the reflex loop touches. The runner
pins them automatically; the agent can additionally pin its own
nodes via `pin_node`.

**The "blob" non-problem.** A 10-MB audio sample? Mint an
AudioBuffer node, set its `samples` attr to the bytes, then
`migrate_node(buf, "SSD")`. The agent's running state stays cool
in RAM; the buffer lives on disk; access materialises it on
demand (runner caches per its tier's `coherence` policy). On a
microcontroller with no SSD, the same agent's policy rule
(graph-resident) reads `nodes("StorageTier")`, sees only
`SRAM` + `flash`, and either declines to capture the buffer (drop
on the floor — sometimes that's the right call) or migrates to
`flash` instead. **The agent decides — because the agent can see
the tiers.**

**Image / persistence interaction.** Tiers with
`survives_image_load=true` (typically `flash`, `disk`, `SSD`,
`net`) keep their contents across save/load — `save` writes only
references to those tiers, not the bytes themselves. Tiers with
`survives_image_load=false` (typically `RAM`, `SRAM`, `L*`) get
their live contents serialised into the image bytes per §6.

**Agent introspection — the existing memory-architecture rules
already work here.** [[ozma-memory-architecture]]'s rewrite rules
(WorkingSet / Episode / Pointer / ExternalStore / Chunk /
GoalFrame) were written before tiers were formal; they currently
move nodes between *types*. Once tiers are first-class, the same
rules become *tier-migration rules* — promoting hot episodes from
`SSD` → `RAM`, demoting cold ones the other way, etc. No new
agent code; the rules just gain a tier-aware effect arm.

---

## 5. Grammar Γ + Rewrite Rules

Two related but distinct abstractions:

- **Γ (productions)** — admissibility grammar. Declares which
  `(src_type, edge_type, tgt_type)` triples are legal, with
  optional where-clause Term filters and weights. ALL mutations
  through the runtime control surface are checked against Γ.
- **Rewrite rules** — match-pattern + effect-list. Patterns match
  subgraphs; effects mutate the graph. Rules are the agent's
  primary computational mechanism (see [[ozma-constructive-rewrite-layer]]).

### 5.1 Production

```
Production {
    src: NodePattern { type_: Sym, var: Sym },
    edge_type: Sym,
    tgt: NodePattern { type_: Sym, var: Sym },
    where_: Option<TermIdx>,   // boolean Term evaluated under {src.var, tgt.var}
    weight: TermIdx,           // numeric Term, default Lit(1.0)
    provenance: Sym,           // human-readable label, survives Γ edits
}
```

**Grammar index.** `(src_type, edge_type, tgt_type) → Vec<ProdIdx>`.
Lookup on edge-insert is O(1+matching).

**Type vocabulary.** Γ tracks `node_types: Set<Sym>` and
`edge_types: Set<Sym>` derived from production patterns. Used by
the checker (next).

### 5.2 Admissibility check on mutation

Every `add_edge(src, et, tgt)` triggers:

1. Look up `(type_of(src), et, type_of(tgt))` in Γ's index.
2. If no matching production: **Type-1 inadmissibility** — return
   error; mutation rejected.
3. For each matching production: bind `src.var → src`, `tgt.var → tgt`;
   evaluate `where_` Term; if any returns truthy, mutation admitted.
4. If all match-but-fail-where: **Type-2 inadmissibility** —
   return error.

`add_node` is permitted only if `type` ∈ `Γ.node_types` OR the
caller is operating in **type-vocabulary-extension mode** (per
below). The agent extending its own Γ — Theorem C /
[[ozma-formal-terminology]] — uses this mode.

**Type-vocabulary-extension mode — how the bootstrap works.** The
chicken-and-egg (type vocabulary is derived from productions; new
types need to enter via something) resolves through one rule:

* Adding a `Production` whose `src.type_` or `tgt.type_` is a
  NEW type-Sym automatically extends `Γ.node_types` to include
  that type at production-insert time. The new vocabulary is
  immediately visible.
* `add_node(NewType, ...)` succeeds iff a Production has already
  introduced `NewType`. The "extension mode" is implicit: it's the
  window between `add_production(P_new_type)` and the first
  `add_node(new_type)` — no flag to toggle.
* The same applies to Rule effect `AddNode`: a rule whose effect
  mints a node of type `T` is admissible iff `T ∈ Γ.node_types` at
  rule-insert time. If the rule needs to mint a new type, the
  agent's authoring sequence must be: `add_production(...)` to
  introduce the type first, THEN `add_rule(...)` that mints it.
* For runners with Surface B exposed (§8.2), tooling can insert
  productions directly. For runners with Surface A only, the
  agent's own rules drive Γ extension via the `add_production`
  effect (which `Effect` does not yet support in the §5.3
  enumeration — adding it is a Phase 17b candidate; the spec
  flags this gap honestly).

### 5.3 Rewrite rules

```
RewriteRule {
    name: Sym,
    match_edges: Vec<MatchEdge>,   // pattern as a set of typed-edge constraints
    where_: Option<TermIdx>,       // boolean Term; rule applies only when truthy
    effects: Vec<Effect>,          // ordered mutation list
}

MatchEdge { src_var: Sym, edge_type: Sym, tgt_var: Sym }

Effect ∈ {
    AddEdge { src_var, edge_type, tgt_var, attrs: [(Sym, EffectArg)] },
    DelEdge { src_var, edge_type, tgt_var },
    AddNode { new_var, type_, attrs },     // binds new_var to fresh NodeID
    DelNode { var },
    SetAttr { var, key, value: EffectArg }
}

EffectArg ∈ { Literal(Value), Computed(TermIdx) }
```

**Match semantics.** Find every binding `Sym → NodeID` such that
every `MatchEdge` is satisfied and `where_` (if present) evaluates
truthy. Effects then apply in order under that binding.

**Fixed-point.** The runtime control surface (§8) exposes
`apply_rule_once(rule_idx)` (fires one binding) and
`run_rules(rule_set, max_steps)` (loops to fixed point or until
`max_steps`; `rule_set` is the subset of rules to iterate — `None`
means all). Both return the count of effects applied.

**Canonical binding order.** When multiple bindings satisfy a
rule's match + where in one tick, they are processed in **SCO
order** (Appendix A) over the binding map — equivalently:
lexicographically over `(var_name → matched_node)` pairs, where
each Node is compared by SCO (`created_at_seq` + type, per §4.1.1).
This makes the order implementation-independent — two conforming
runners process the same operation sequence and produce the same
binding-iteration order. Raw `NodeID` is NOT used.

**Rule atomicity — a rule firing is a transaction.** Effects 1..N
apply in order; each is admissibility-checked against Γ (§5.2). If
any effect is rejected, **ALL prior effects from this firing are
rolled back** via the UndoStep log; the rule firing emits a
`rule_effect_reject` runtime event (§7.6) carrying the offending
effect's index + reason; the engine moves to the next binding
(or, if none remain, the next rule) without partial state. The
agent never observes a half-applied rule.

The transaction unit is the WHOLE RULE FIRING — including any
`AddNode` effects whose new `new_var` bindings were consumed by
later effects (those nodes are rolled back too).

**Reversibility.** The `UndoStep` log is exposed beyond
transaction rollback: agents that perform speculative rewrites
(search algorithms — [[ozma-constructive-rewrite-layer]]) call
`undo(steps)` / `redo(steps)` on the control surface (§8).

**Determinism contract.** Two conforming runners executing the
same `(initial canonical graph, operation sequence)` produce
byte-identical final canonical graphs (per §6.3 canonicalisation:
Sym renumber + embedded-Node-rewrite + freelist-compact + SCO sort
of every container, then byte-compare). The SCO binding order
makes this tractable.

---

## 6. Image Format

The agent is a system image. `save(path)` writes; `load(path)`
restores. The on-disk shape is the persistence contract.

### 6.1 Logical contents

An image is the union of:

- **Interner table** — Sym → string. Sorted by Sym for stable
  ordering.
- **Term arena** — list of TermNode records; index = TermIdx.
- **Grammar Γ** — list of Production records.
- **Graph** — nodes (slot index, generation, type, attrs,
  implicit `created_at_seq` + `created_at_tick`), edges (slot
  index, src, edge_type, tgt, attrs).
- **Rules** — list of RewriteRule records.
- **Diagnostic counters** — cumulative operation counts
  (admissibility-check fires, rule-applies, term-evaluations).
  **NOT part of canonical state** — see §6.3 pass 4. They are
  telemetry; image bytes will differ between runners with
  different cache behaviours and this is acceptable. Conformance
  byte-compare excludes them.

### 6.2 Format (current)

Today: JSON (see `src/persist.rs`). Chosen because it survives
schema evolution and is human-inspectable. **The format is not
load-bearing** — agents and runners depend on the LOGICAL contents,
not the byte encoding. A future bare-metal runner MAY use a
flat binary format with:

```
[ header                                  // magic + version + region offsets ]
[ interner region                         // Sym table ]
[ term arena region                       // TermNode records ]
[ grammar region                          // Production records ]
[ graph node region                       // NodeData slab + freelist ]
[ graph edge region                       // EdgeData slab + freelist ]
[ rule region                             // RewriteRule records ]
[ checksum                                // CRC of everything above ]
```

Compaction on save: freelists collapsed, IDs renumbered, indexes
rebuilt on load. Round-trip equivalence: `load(save(image)) ==
image` (modulo ID renumbering).

### 6.3 Image canonicalisation

A loaded image's raw bytes vary with implementation choices (Sym
handle order, slab allocation pattern, free-list state). For
cross-runner byte-comparison (the basis of conformance §9), every
runner publishes its image in **canonical form** via the
canonicalisation function specified here. Two runners that
processed identical operation sequences produce byte-identical
canonical images.

**The canonicalisation function — five passes, applied in order:**

1. **Sym canonicalisation.** Collect every interned string
   (excluding the reserved `Sym 0 = ""`); sort by lexicographic
   byte content; renumber as `Sym 1 .. Sym N`. Build the renumber
   map `old_sym → new_sym`. Rewrite every embedded Sym in the
   image (node types, edge types, attr keys, Str Values) through
   the map. After this pass, two runners with identical interned
   string SETS have identical Sym handles.

2. **NodeID canonicalisation.** Sort nodes by `created_at_seq`
   (§4.1.1) ascending; assign new dense `NodeID` `0 .. M-1` in
   that order. Build the renumber map `old_nodeid → new_nodeid`.
   Rewrite every embedded NodeID through the map:
   * Edge `src` / `tgt` fields.
   * `Node` Values in node attrs and edge attrs (mandatory — no
     dangling references survive canonicalisation).
   * `TermRef` Values that point to subgraph roots.
   Generations reset to 0 (canonical-form nodes have no freelist
   history). Edges renumber similarly by `(src.new_nodeid,
   edge_type, tgt.new_nodeid)` order.

3. **Container interior canonicalisation.** Walk every Set,
   FrozenSet, Dict in every attr: re-sort under SCO (Appendix A),
   producing byte-identical serialised form. (Already required at
   insertion, but a freshly-loaded image may have container values
   written by a runner with a buggy SCO — canonicalisation re-
   normalises.)

4. **Counter zeroing.** Diagnostic counters (term evaluations,
   cache hits, admissibility checks, rule firings) are zeroed in
   the canonical form. They are runtime telemetry, not canonical
   state — and they CAN diverge between runners with different
   cache behaviour (§3.2). Excluding them resolves the prior
   contradiction between §6.1 and §3.2.

5. **Section order.** The canonical image lays out regions in
   the order specified by §6.2 (interner / term arena / grammar /
   nodes / edges / rules). Within each region, records appear in
   ascending key order (Sym for interner; canonical NodeID for
   nodes; `(canonical NodeID, edge_type Sym, canonical NodeID)`
   for edges; etc.).

The output of this function is the bytes the conformance suite
compares.

**Agents that store specific `NodeID` Values in attrs ARE
portable across loads** — the renumber map in pass 2 rewrites
them. The prior shrug ("not portable") was wrong; this draft
mandates the rewrite.

**`Now()` / `Rand()` values that flowed into attrs.** These are
NOT canonicalised — once an agent has stored a wall-clock value
or a random sample into the graph, those bytes are part of state.
For conformance comparisons (§9), the synthetic world MUST
virtualise `Now` and `Rand` (deterministic clock + deterministic
seed); for normal deployments, agents that store `Now`-derived
state into the graph accept that two physical deployments
naturally diverge in those bytes.

---

## 7. World I/O Bus

The runner's interface to whatever the agent's world is. **Byte-
oriented, typed channels** — not "give me a Python list."

### 7.1 Channels

A channel is a typed unidirectional stream:

```
Channel {
    id: u16,                  // channel handle
    direction: In | Out,
    element_type: ChannelType,
    rate_hz: Option<u32>,     // None = aperiodic / event-driven
    buffer_policy: Drop | Block | Coalesce,
}

ChannelType ∈ {
    Bytes,                                                // raw byte stream
    I16Samples { channels: u8, sample_rate_hz: u32 },     // audio
    PixelGrid { width, height, depth_bits, layout: Gray | RGB | RGBA },  // video
    TupleStream {                                         // structured event
        arity: u8,                                        //   element count per event
        elem_types: Vec<PrimType>,                        //   one PrimType per position; length = arity
        names: Vec<Sym>,                                  //   per-position labels for §7.4 byte-match
    },
}

PrimType ∈ { Bool, Int, Float, Str, Bytes }
```

A `TupleStream` channel produces / consumes events whose `Value`
is a `Tuple` of exactly `arity` elements; element `i` MUST be a
`Value` of tag matching `elem_types[i]`. Mismatch on
`channel_write` is rejected + emits `channel_type_violation`
runtime event; on `channel_read` materialisation, the adapter is
considered non-conforming and the runner shuts the channel down
with `adapter_protocol_violation`.

`names` lets agents address fields by name when destructuring the
Tuple via `Nth { items, index }` + a parallel name lookup, and
makes "types match byte-for-byte" (§7.4) actually verifiable.

**Aperiodic input channels** = interrupts. A byte-counted "give me
the next event" semantics, with an optional buffer.

**Periodic channels** = sampled streams (audio at 48 kHz, video at
30 fps, IMU at 1 kHz). The runner pulls or pushes at the channel
rate.

### 7.2 Channel discovery

At runtime startup, the runner enumerates the channels the
attached world adapter provides. Each channel registers with:
- ID (assigned by runner)
- Type (see above)
- Rate (if periodic)
- Buffer policy
- Provenance string for the agent's introspection

The agent reads `agent_root.channels` (a Set of channel-descriptor
nodes minted at startup) to discover its peripherals — same pattern
as a Lisp machine's `*peripherals*`.

### 7.3 Read / write operations

The runner exposes (via the runtime control surface §8):

- `channel_read(channel_id) → Value` — type-correct read; blocks or
  returns `None` per `buffer_policy`.
- `channel_write(channel_id, value) → bool` — type-checked write;
  returns success.
- `channel_pending(channel_id) → Int` — events waiting on input.

The agent's REFLEX mechanism (graph-resident, see
[[ozma-reflex-layer]]) is the primary consumer: a reflex with a
stimulus Term that includes `channel_pending(K) > 0` fires when
events arrive.

### 7.4 World adapter contract

A world adapter implements EITHER side of every channel it owns
(for `In` channels, the adapter PRODUCES values; for `Out`, the
adapter CONSUMES). On bare metal, this is a peripheral driver. On
a simulator, it's a Python module / Rust crate / shell pipe
wrapping the external world.

**Mandatory adapter properties:**
- Channel types match declared types byte-for-byte.
- Aperiodic adapters trigger an interrupt when an event is
  available. The runner's reflex dispatch (§8) responds.
- Periodic adapters meet their declared rate within the runner's
  scheduling tolerance.
- Adapter shutdown is graceful — the runner can revoke channel
  ownership without corrupting the agent.

### 7.5 Examples

**Audio-in on a microcontroller.** I²S codec produces 48 kHz / 16-bit
stereo samples to a DMA buffer. World adapter is the I²S driver
calling `channel_write(audio_in_id, samples_buffer)`. Agent reflex
fires on `channel_pending(audio_in_id) > 1024` — process when a
block arrives.

**Audio-in on a simulator.** PyAV demux thread; same channel
interface; world adapter calls `channel_write(audio_in_id,
decoded_pcm)`. Agent sees IDENTICAL events.

**Doom game state.** ViZDoom session as world adapter; one
`PixelGrid` input channel (game frame) + one `Tuple` input channel
(reward + status) + one `Tuple` output channel (action: 7 button
booleans). Agent reflexes drive perception/action.

**Robot servo on bare metal.** GPIO pins; `Out` channel of
`Tuple(channel: u8, value: u16)`; PWM driver as adapter. Agent
writes; servo moves.

### 7.6 Built-in channels — diagnostic + runtime events

Two channels are mandatory and always present, allocated by the
runner before any world-adapter-provided channel. Channel IDs 0
and 1 are reserved for them.

**Channel 0 — `diagnostic_out` (Out, Bytes).** The runner's own
output for diagnostic messages. `Trace` (§3.1.1) writes here;
runners MAY also write internal diagnostics (rule firings, eval
slowness, cache statistics) gated by a verbosity setting. The
world adapter MUST consume this channel — typically logging it.
On bare metal, the adapter might route to UART or a flash log
ring buffer.

**Channel 1 — `runtime_events` (In, Tuple, aperiodic).** Structured
event stream FROM runner TO agent. Each event is a Tuple:

```
(timestamp: Int,   // Now() at event
 kind: Str,        // see catalogue below
 payload: Dict)    // event-specific fields
```

Mandatory event kinds:

| `kind`                  | When emitted                                  | Payload fields                           |
|-------------------------|-----------------------------------------------|------------------------------------------|
| `"term_eval_none"`      | A non-leaf Term evaluated to `None`           | `term_ref: TermRef, env_keys: Set<Str>`  |
| `"rule_match_fail"`     | A rule application attempt found no binding   | `rule: Str, attempted_at: Tuple`         |
| `"rule_effect_reject"`  | An admissibility check rejected an effect     | `rule: Str, effect_kind: Str, reason: Str` |
| `"holds_unresolved"`    | `Holds` couldn't find a Concept by name       | `concept: Str`                           |
| `"holds_depth_exceed"`  | `Holds` recursion bound hit                   | `concept: Str, depth: Int`               |
| `"channel_overrun"`     | An `In` channel's buffer dropped data         | `channel_id: Int, dropped: Int`          |
| `"image_resource_low"`  | Node / edge / attr space approaching capacity | `region: Str, used: Int, limit: Int`     |

This is the runner's **condition system** (Lisp machine analog).
The agent installs reflexes (graph-resident, see
[[ozma-reflex-layer]]) on `runtime_events` channel-pending — when
a relevant event arrives, the agent reacts. The agent is its own
debugger.

**Verbosity control.** The agent sets `agent_root.diagnostic_level`
(an Int attr the runner reads on each Trace / internal-event
emission). Levels: `0` (silent — only mandatory events), `1`
(typical — Trace + rule failures), `2` (verbose — every rule
firing). Embedded runners with constrained log buffers honour the
setting; production deployments typically run at `0` or `1`.

**Why mandatory in the ISA.** Without these channels, agents are
blind to their own runtime behaviour. They cannot self-debug; they
cannot learn from execution failures; they cannot ask "why didn't
that rule fire?". The Lisp machine condition system is the
template — first-class observable runtime — and we adopt it.

### 7.7 Tick semantics

The runner has no inherent main loop — but it must publish what
"one tick" means so a world adapter can drive it.

**One tick is:**

1. **Drain pending input channels** — for each `In` channel with
   `channel_pending(id) > 0`, read events and mint the
   corresponding graph nodes (channel-specific; the channel
   declares its `event_to_graph` mapping). For aperiodic channels
   this is interrupt-driven; for periodic channels, batched per
   tick period.
2. **Fire reflexes** — invoke `run_rules(reflex_rule_set, max_steps)`
   where `reflex_rule_set` is the set of rules tagged `kind:
   "reflex"` (the runner maintains this index automatically by
   walking `Reflex`-typed nodes; the rules referenced by Reflex
   nodes ARE the reflex rule set).
3. **Run reflex effects to fixed point** — bounded by `max_steps`
   (declared per-tick by the world adapter; default 1024). If the
   bound hits without convergence, emit a `term_eval_none`-like
   runtime event and continue. (Spinning is a bug; the runner
   tells the agent about it.)
4. **Flush pending output channels** — write `Out` channel buffers
   to their adapters.

**Single-threaded mandate (CORE).** Tick is sequential. No
concurrent rule firing within one tick. Reflexes fire in
canonical priority order (sort by Reflex node `priority` attr,
NodeID as tiebreaker). This guarantees the determinism contract.
Multi-core runners use cores for orthogonal work (separate agents,
or §3.3 feature-block sub-runners) — not for parallelising one
agent's reflex firing.

**World-adapter pattern.** Bare-metal: timer interrupt fires every
N ms → call `tick()`. Hosted simulator: thread or async loop
calling `tick()` between channel-event injections. Test harness:
inject events synchronously, call `tick()`, assert post-state.

The world-adapter control surface (§8.1) exposes `tick()` +
channel I/O ONLY. The `run_rules` primitive (§5.3) is part of the
HOST-ORCHESTRATOR surface (§8.2), not the world-adapter one —
that's a layer the world adapter cannot reach. The world adapter
calls `tick`, period.

---

## 8. Runtime Control Surfaces — two tiers

The runner exposes TWO surfaces, deliberately separated. The
world adapter sees only Surface A; mutation-capable tooling (host
orchestrator, simulator harness, debugger, golden conformance
suite, offline agent authoring) sees Surface B as well. Bare-metal
deployments physically expose A only — there is no symbol for the
B ops in the runner binary.

This separation is the implementation of §0's layer axiom: a
conforming world adapter that speaks only A *cannot* author agent
behaviour; the agent's identity is closed under the channel
boundary.

### 8.1 Surface A — World-Adapter Control Surface

The ONLY surface the world adapter speaks. Tick + channel I/O +
image lifecycle:

```
tick(max_steps_per_phase: usize) → TickStats             // §7.7
tick_n(n: usize, max_steps_per_phase: usize) → Vec<TickStats>

channel_read(id: u16) → Value
channel_write(id: u16, value: Value) → bool
channel_pending(id: u16) → Int
channels() → Vec<ChannelDescriptor>                       // discovery; §7.2

save(buf: ImageBuffer) → bytes-written                    // image persistence (§6)
load(buf: ImageBuffer) → ()                               //   only at startup or explicit checkpoint
shutdown() → ()                                           // graceful adapter detach (§7.4)
```

That is the COMPLETE world-adapter surface. There is no
`add_node`, no `set_attr`, no `evaluate`, no `add_rule`. The world
adapter cannot author or mutate agent state by any path other than
channel writes (which the agent's own reflexes consume on its own
terms).

A bare-metal-targeted runner build compiles WITH Surface B ABSENT
— the binary contains only Surface A symbols. A simulator runner
compiles with both; the orchestrator harness uses B, the world-
adapter side uses only A.

### 8.2 Surface B — Host-Orchestrator Control Surface

For testing, debugging, the golden conformance suite, and offline
agent authoring tooling. NOT present in bare-metal deployments —
the agent must not depend on it. Carries every mutation primitive:

```
// --- graph mutation ---
add_node(type: Sym, attrs: Map) → NodeID | Err
add_edge(src: NodeID, edge_type: Sym, tgt: NodeID, attrs: Map) → () | Err
remove_node(NodeID) → bool
remove_edge(src, edge_type, tgt) → bool
set_attr(NodeID, key: Sym, value: Value) → () | Err
set_edge_attr(EdgeKey, key: Sym, value: Value) → () | Err
set_type(NodeID, type: Sym) → () | Err

// --- graph read ---
nodes(type: Option<Sym>) → Vec<NodeID>
nodes_where(type: Sym, attr_key: Sym, value: Value) → Vec<NodeID>
neighbours(NodeID, edge_type: Option<Sym>) → Vec<NodeID>
in_neighbours(NodeID, edge_type: Option<Sym>) → Vec<NodeID>
node(NodeID) → NodeData                                   // generation-checked; stale → None
has_node(NodeID) → bool
has_edge(src, edge_type, tgt) → bool
node_count() → usize
edge_count() → usize

// --- grammar Γ + rules (agent authoring) ---
add_production(p: Production) → ProdIdx
add_rule(r: RewriteRule) → RuleIdx
apply_rule_once(rule: RuleIdx) → bool
run_rules(rule_set: Option<Vec<RuleIdx>>, max_steps: usize) → usize
rule_count() → usize

// --- direct Term eval (for testing + REPL) ---
evaluate(term: TermIdx, env: Map<Sym, Value>) → Value
declare_attr_index(node_type: Sym, attr_key: Sym) → ()
has_attr_index(node_type: Sym, attr_key: Sym) → bool

// --- storage tiers (§4.5) ---
storage_tiers() → Vec<NodeID>
migrate_node(nid: NodeID, target_tier: Sym) → bool | Err
pin_node(nid: NodeID, tier: Sym) → bool
unpin_node(nid: NodeID) → bool

// --- diagnostics ---
counters() → Map                                          // NOT canonical state (§6.3)
counters_clear() → ()

// --- reversibility (search algorithms; §5.3) ---
undo(steps: usize) → usize
redo(steps: usize) → usize
```

The B surface has NO file-system APIs beyond `save`/`load`, NO
process APIs, NO thread APIs, NO `print` — same posture as A.

### 8.3 Which surface the agent uses

**The agent uses NEITHER.** The agent's behaviour lives in graph
data (rules, productions, reflexes, concept Terms); the runner's
tick fires those without going through either surface as an API
call. The two surfaces exist for code OUTSIDE the agent (world
adapter for A; orchestration tooling for B). This is the
implementation of the §0 layer test: delete all B code + leave
only the world adapter speaking A, and the agent still runs.

---

## 9. Conformance

A runner is conforming iff it passes the conformance suite.

### 9.1 What the suite is

A pre-built agent image + a synthetic world adapter + a golden
post-state. Run the suite against a candidate runner:

1. Load the agent image.
2. Attach the synthetic world adapter (it produces a deterministic
   event sequence on declared channels).
3. Run the agent's main reflex loop until a terminator event.
4. Save the agent's final image.
5. Byte-compare against the golden post-state (modulo Sym
   renumbering — interner contents must be identical as a set).

**Pass:** byte-identical. **Fail:** divergence.

### 9.2 What the suite covers

The synthetic agent + world exercise:
- All Term variants under representative inputs (golden output per
  Term).
- All Effect variants and rule fixed-point convergence.
- Grammar admissibility — both Type-1 and Type-2 rejection.
- Multi-channel I/O — periodic + aperiodic + bidirectional.
- Image save/load round-trip equivalence.
- Counter consistency.
- Reflex dispatch on channel events.

### 9.3 Runner declarations

Every conforming runner publishes a declaration:

```
RunnerConformance {
    isa_version: "17a-draft",
    implementation_id: String,        // e.g. "rust-pyo3-0.1"
    max_nodes: Option<u32>,            // None = bounded only by memory
    max_edges: Option<u32>,
    max_tuple_len: usize,
    max_set_size: usize,
    max_dict_size: usize,
    max_surface_bytes: usize,
    holds_recursion_depth: usize,      // default 64
    deterministic_eval_cache: bool,    // MUST be true: cache hit MUST return
                                       //   byte-identical Value to cache miss
                                       //   (correctness is cache-invariant per §3.2;
                                       //   `true` asserts the runner audits this)
    feature_blocks: Set<String>,       // see §3.3 — which optional blocks implemented
    block_tolerances: Map<String,f64>, // float tolerance per block, default 1e-9
    now_tick_resolution_ns: u64,       // Now's tick granularity, e.g. 1000 = 1µs
    rand_seed_mode: "deterministic" | "entropy",   // see §3.1.1 Runtime
}
```

Conforming runners MUST also pass:
- The CORE conformance suite (§9.2) — unconditional.
- The sub-suite for each block in `feature_blocks` (§3.3).

Loading an agent verifies `agent.required_blocks ⊆ feature_blocks`
or refuses (§3.3).

Agents that target a specific deployment can check the declaration
at load time. Conformance suite passes are recorded per
declaration.

### 9.4 Versioning

This ISA is versioned. Additions (new Term variants, new Effect
kinds, new channel types) are minor-version bumps. Removals or
semantic changes are major-version bumps. The agent image declares
the ISA version it was built against; the runner refuses to load
incompatible versions.

---

## 10. Status — what's specified vs what's built

### Specified + reference-implemented (Rust runner at `runners/dsl/`)
- §1 — twelve Value tags ✓ (TermRef added by §1; Rust implements
  the original 11; TermRef is spec'd not yet built)
- §2 — Sym interner ✓
- §3.1 — 72 of 102 Term variants ✓ (the base set per §3.1.2 table
  entries 1-69 + 100-102; 73-99 are §3.1.1 additions, spec'd not
  yet implemented)
- §4 — graph memory model ✓ (slab + freelists + by_type +
  attr indices). §4.1.1 `created_at_seq` + §4.4 generational
  handles spec'd not yet implemented — the Rust runner uses raw
  NodeID today.
- §5 — grammar Γ + admissibility check + rewrite rules + undo log
  ✓. §5.3 rule-atomicity (transaction rollback on rejection) is
  spec'd; current Rust implementation does per-effect (the
  rollback path is in the UndoStep machinery but not the rule-fire
  loop).
- §6 — image save/load via JSON ✓. §6.3 canonicalisation is spec'd
  not yet implemented (the JSON format is non-canonical today).
- §8 — Surface B (orchestrator) ✓ (the current Rust PyO3 bindings
  ARE Surface B). Surface A (world-adapter, no mutation) is
  spec'd not yet carved out as a separate API.

### Specified, partially implemented
- §3.1.1 — 30 new core Terms (bitwise / sequence / string / bytes /
  map / conversion / hash / introspection / runtime / diagnostics)
  are spec'd but not in the Rust runner yet. Bringing them in is
  the natural next implementation chunk — most are mechanical.
- §3.3 — Optional feature blocks (`tensor`, `dsp`, `simd`, `crypto`,
  `image`, `huffman`, `mdct`, `motion`, `nn`) — none implemented
  in the Rust runner today. Each is independent; the `huffman`
  block is the most strategically valuable to implement first
  (unblocks Phase 16 codec work properly).
- §7 World I/O bus — typed channels NOT yet implemented in the
  reference runner. Today's world adapters (in Python: PyAV demux,
  ViZDoom binding, etc.) bypass any channel abstraction and call
  the runtime control surface directly. Bringing this in is a
  prerequisite for the bare-metal vision.
- §9 conformance suite — does not yet exist. The reference runner
  has a test suite (`tests/`) but it doesn't carve out a golden
  conformance subset. Per-block sub-suites also don't exist.

### Specified in this draft — closed since first cut
- **Concept resolution / `Holds`** — §3.4 (now also covers arity
  validation + over-supply rules).
- **`TermRef` as a Value tag** — §1.
- **IEEE-754 reproducibility** — §3.2.
- **Tick semantics** — §7.7.
- **Diagnostic + runtime-event channels** — §7.6.
- **Time + randomness** — §3.1.1 (with conformance-mode virtual
  clock + deterministic seed).
- **Storage tiers (the hierarchy)** — §4.5.
- **Substrate Canonical Order (SCO) over Values** — **Appendix
  A**. The keystone fix for the determinism contract: total order
  across all 12 tags + within-tag rules + NaN/±0 handling +
  Sym-by-string-content + Node-by-`created_at_seq`. Every operation
  that sorts or canonicalises refers to SCO.
- **`created_at_seq` as canonical cross-runner node identity** —
  §4.1.1. Replaces raw `NodeID` as the basis for cross-runner
  determinism; resolves the §4.3 ↔ §5.3 contradiction.
- **Generational `NodeID` handles + Node-in-attr renumbering** —
  §4.4 + §6.3. Eliminates the stale-handle UB; save/load rewrites
  embedded Node values through a mandated renumber map.
- **`Eq` semantics vs SCE (Substrate Canonical Equivalence)** —
  §1. Two distinct equalities, named separately; `Eq` follows
  IEEE for Float (NaN ≠ NaN), SCE forbids NaN in containers +
  normalises ±0.0.
- **Image canonicalisation function (5 passes)** — §6.3.
  Specifies the exact operation that "byte-identical modulo Sym
  renumbering" used to gesture at.
- **Counters excluded from canonical compare** — §6.1 + §6.3.
  Resolves the §6.1 ↔ §3.2 contradiction.
- **Rule firing = transaction** — §5.3. Effect rejection rolls
  back all prior effects from the same firing via the UndoStep
  log.
- **Canonical binding order = SCO over binding map** — §5.3.
  Replaces "sort by NodeID" with implementation-independent order.
- **Two-tier control surfaces** — §8.1 / §8.2. World-Adapter
  surface (A) is channel I/O + tick + image lifecycle only;
  Host-Orchestrator surface (B) has all mutation primitives.
  Bare-metal deployments expose A only. Implements §0's layer
  test at the API boundary.
- **§8 has a header now.** And the contradictory paragraph (world
  adapter calls `run_rules` directly) is removed.
- **`None` propagation rules** — §3. Fixed table across all CORE
  Terms; runner can't vary.
- **Term inventory authoritative numbered table** — §3.1.2.
  Replaces the prose subtotal-that-didn't-add-up with one
  enumeration; CORE total = 102.
- **`add_node` bootstrap (Γ extension)** — §5.2. Adding a
  Production with a new type-Sym implicitly extends `Γ.node_types`;
  same for Rule effect AddNode.
- **`TupleStream` channel schema concrete** — §7.1. Arity +
  per-position elem_types + names; type violations emit specific
  runtime events.

### Not yet specified — remaining gaps
- **Endogenous drives + curiosity loop** — currently expressed as
  Python orchestration in `domains/curious_agent.py`. Needs to
  become graph-resident rules dispatched by §7.7 tick. The
  cleanest shape: drives are `Reflex` nodes with stimulus Terms
  that check agent-internal state (novelty / surprise / time-cost
  counters) and effect Terms that author Goals. The migration is
  mechanical — every Python orchestrator becomes a set of
  reflexes — but the rule set is sizable.
- **Threading / concurrency** — current Rust runner has a
  concurrency layer (Phase 9b), partially specified. §7.7 mandates
  single-threaded tick for CORE. Multi-agent or feature-block
  sub-runner concurrency is OUT of CORE scope; lift to an
  `concurrency` optional feature block (Phase 17 extension)
  if/when the agent's workload demands it.
- ~~Large data (waveforms, images, codec coefficient blocks)~~ —
  **closed by §4.5.** Big data goes to a slower tier; the agent
  uses `migrate_node` to place it; the runner caches per the
  tier's coherence policy. No special Blob tag needed; existing
  attrs work uniformly across tiers. The agent introspects
  `nodes("StorageTier")` to know what's available on its target.
- **Hot code update — cache invalidation contract.** §3.4 declares
  that Concept edits invalidate eval cache, but the spec doesn't
  yet say HOW (per-Concept versioning? full cache flush on any
  Term-arena edit? generation counter?). Whichever, the runner's
  guarantee is "eval after edit returns the new behaviour";
  implementation choice.
- **Garbage collection** — orphaned nodes / unreachable subgraphs
  are NOT collected today. For long-running embedded deployments,
  a reachability sweep rooted at `agent_root` is needed. CADR-style
  hardware GC is the obvious model. Open: incremental sweep vs
  stop-the-world; how much agent control over GC timing.

These remaining gaps are the Phase 17b+ work list.

---

## 11. References

- [[ozma-is-a-lisp-machine]] — why this document is named what it is.
- [[ozma-runner-agent-world-separation]] — the three-layer axiom.
- [[ozma-concepts-in-gamma]] — the agent-side discipline (reasoning
  must be graph-resident).
- [[ozma-constructive-rewrite-layer]] — the role of rewrite rules
  for the agent's computation.
- [[ozma-reflex-layer]] — how the agent handles channel events.
- [[ozma-master-thread-is-init]] — the runner's tick semantics.
- Paper I, *Everything Is A Graph — Part I: Core Mechanics* — the
  formal (G, Γ) substrate. Axioms 1–3, Theorems C and D, §2.1.
- Symbolics Genera Reference Manual — image format, FEP/IOB.
- MIT CADR documentation — microcode, hardware GC.
- TI Explorer technical reference — peripheral bus model.

---

---

## Appendix A — Substrate Canonical Order (SCO) over Values

The total order every conforming runner uses for all canonical-form
operations (Set/FrozenSet/Dict sorting, `Pick`, `TupleSort` default
comparator, binding-order tiebreakers, image canonicalisation).
**Two conforming runners produce byte-identical results.**

### A.1 Tag priority — the outer key

Compare Values first by tag, in this fixed priority order
(lowest first):

```
0  None
1  Bool
2  Int
3  Float
4  Str
5  Node
6  TermRef
7  Surface
8  Tuple
9  Set
10 FrozenSet
11 Dict
```

If tags differ, the tag with the lower priority sorts first. If
tags match, apply the within-tag rule.

### A.2 Within-tag ordering

* **`None`** — trivially equal to itself. Single element class.
* **`Bool`** — `false < true`.
* **`Int`** — numeric ascending (i64 native).
* **`Float`** — **NaN is rejected at SCE-admission** (raised at the
  control surface; cannot appear here). `-0.0` is **normalised to
  `+0.0` before comparison**. Otherwise numeric ascending (IEEE-754
  binary64 ordering, which is well-defined on finite + ±Inf
  values once NaN is excluded). `-Inf < any finite < +Inf`.
* **`Str`** — compared by **byte content of the interned string**,
  lexicographic, NOT by `Sym` handle. (Sym handles are per-runner;
  byte content is the cross-runner invariant.)
* **`Node`** — compared by **`(created_at_seq, type_str_bytes)`**
  pair, lexicographic. `created_at_seq` is the node's monotonic
  insertion-sequence number (mandatory attr; see §4.1.1). NOT by
  raw `NodeID`. Two runners that processed the same operation
  sequence assign identical `created_at_seq` to the same logical
  node; raw `NodeID` is freelist-dependent and NOT cross-runner.
* **`TermRef`** — compared by the SCE of the **canonicalised
  subgraph** the TermRef resolves to (Term-tree byte form per
  `term_to_subgraph` reflection, with child-edge ordering
  canonical and child Terms compared recursively under SCO).
* **`Surface`** — `(kind, byte-payload)` pair: kind first
  (`Text=0 < Bytes=1`), then byte-payload lexicographic.
* **`Tuple`** — **lexicographic** over elements under SCO. Shorter
  Tuple that is a prefix of a longer Tuple sorts first.
* **`Set` / `FrozenSet`** — internally sorted via SCO; then
  compared element-wise under SCO; if all common-prefix elements
  equal, shorter sorts first. (Cross-tag tiebreaker: Set < FrozenSet
  per tag priority above, so a Set and a FrozenSet with identical
  elements are NOT SCO-equal — only Eq-Term-equal across tag.)
* **`Dict`** — internally sorted by key under SCO; then compared as
  a sequence of `(key, value)` pairs under SCO (key first, then
  value).

### A.3 Forbidden Values

Two Value shapes are rejected at SCE-admission (and thus cannot
appear in any collection or eval-cache key):

* **`Float` with `NaN`** — IEEE-defines `NaN ≠ NaN`, which breaks
  the total-order property. Rejected; emit
  `value_rejected_nan` runtime event.
* **`Float` with `±Inf` IS permitted** — finite-or-infinite ordering
  is well-defined; infinities don't break the total order.

Agents that need NaN semantics use `Eq` (which follows IEEE) on
raw `Float` values that never enter a container. Storing a NaN
into a node attr is permitted only if no SCE operation will read
that attr (caveat surfaced via `value_unsafe_in_collection` event
when the attr is later accessed by a Set-building Term).

### A.4 Sym handle vs interned string

This is where many cross-runner bugs hide. `Sym` is a u32 handle
local to one runner. **The agent never directly sees a Sym** —
`ValueTag` returns the tag NAME (a `Str`), `TypeOf` returns the
type NAME, etc. SCO compares `Str` by interned-string byte content
(§A.2), so Sym renumbering during image canonicalisation (§6.3) is
invisible to the agent.

### A.5 Determinism + termination

SCO is a strict total order on the set of SCE-admissible Values.
Termination of the recursive comparison (`Tuple`/`Set`/`Dict` with
nested Values) is bounded by the Value's serialised byte length —
no Value can contain itself (the graph allows cycles, but Values
do not).

### A.6 Test points

Every runner's conformance suite (§9) MUST include the SCO test
vectors: a curated list of Value pairs with their SCO outcome
(less / equal / greater). Failing any vector means the runner is
non-conforming. Initial vector list will be published with the
first formal conformance suite (Phase 17e).

---

*Document status: first draft, Phase 17a. Edits welcome — this
spec evolves until the first FPGA-class implementation is on a
desk. Every future commit measures itself against this doc.*
