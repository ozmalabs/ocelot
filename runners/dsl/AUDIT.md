# Graph memory layout — measurement + wins landed

(Tracked separately from the kernel audit below.)

## Conway 100×100 baseline + measured deltas

| | Bytes/node | Bytes/edge | Total | Δ |
|---|---:|---:|---:|---:|
| Baseline | 576 | 144 | 5.49 MiB | — |
| + Win #5 (SmallVec[EdgeIdx;8→4]) | 544 | 136 | 5.19 MiB | −6% |
| + Win #1 (edge_index removed) | 416 | 104 | 3.97 MiB | −28% |
| + Wins #2 + #3 + #7 (Attrs newtype + drop EdgeKey) | 376 | 94 | 3.59 MiB | −35% |
| + Win #2b (split edge_attrs sparse) | **280** | **70** | **2.67 MiB** | **−51%** |

Per-edge cost is now 70 bytes (was 144), dominated by adjacency indexing (out + in + out_by_type + in_by_type entries). For 1M-node Conway extrapolation: **549 MiB → 267 MiB**.

## Type-size deltas

| Type | Before | After |
|---|---:|---:|
| NodeData | 40 | **32** |
| Option<NodeData> | 40 | 32 |
| EdgeData | 48 | **12** |
| Option<EdgeData> | 48 | 16 |
| SmallVec<[EdgeIdx; 8/4]> | 40 | 24 |
| `Attrs` (Vec-backed) | — | 24 (empty) |

## Wins landed

1. **`edge_index` removed.** `has_edge` / `edge_idx` now scan `out_by_type[(src, edge_type)]` (typically 0-4 entries; faster than hashmap probe + key hash for that arity).
2. **`Attrs` newtype** replacing `FxHashMap<Sym, Value>` for both node + edge attrs. Vec-backed (24 bytes empty, allocates lazily, linear scan over `Sym` u32 compares). `From<FxHashMap>` keeps callers ergonomic.
3. **`Attrs` for nodes** as point (2).
5. **SmallVec adjacency inline cap 8 → 4.** Conway never spills (max degree = 4). Saves 32 bytes/node × 2 (out + in_).
7. **`EdgeKey` dropped from `EdgeData`.** src/edge_type/tgt held as direct fields; `EdgeData::key()` rebuilds the structural triple on demand.
2b. **Edge attrs split into a sparse `FxHashMap<EdgeIdx, Attrs>`.** Edges with zero attrs cost zero attr-storage bytes — only populated entries occupy memory. Conway 4M zero-attr edges saved ~24 bytes/edge = 96 MiB at 1M-cell scale.

## Wins deferred

- **#4 (tagged 8-byte `Value` for scalars)** — saves ~6% of total memory (Conway-1M: 16 MiB / 267 MiB), at the cost of touching 700+ `Value::X(_)` pattern-match sites with subtle behaviour risk (NaN, ±0, signed-int truthy). Needs property-test-driven dedicated effort, not bundled in a layout pass.
- **#6 (per-node typed adj replacing `out_by_type` hashmap)** — saves ~8% on that line (~1.5% total). Restructuring complexity outweighs the gain for typical workloads.

## Future: opt-in edge-type indexing

The biggest remaining tax on Conway is `out_by_type` + `in_by_type` at 960 KB / 10K nodes. For Conway-style "1 edge type" workloads this is pure overhead — the untyped `out: Vec<SmallVec<EdgeIdx>>` would suffice (filter on edge_type at query time). For audio pipelines with N edge types per node, the typed index is necessary. The right shape is a **declared-index pattern** like `attr_indices` already implements: opt in to typed adj per `(node_type, edge_type)` pair, default to bare `out` scans. Adds query-path complexity but recovers the 17% Conway-1M memory tax.

---

# Kernel audit — `term.rs` 84 variants

**Source**: `runners/dsl/src/term.rs:30-254` (TermNode enum).

**Counts**: 84 variants → **26 KERNEL (primitive — irreducible)**, **55 DERIVABLE (reducible — compositions)**, **3 NATIVE** (perf-bound).

**Principle**: KERNEL = irreducible *primitives* (graph access, basic CPU arithmetic, control, transcendentals, bit-level access, set/byte constructors, bridge primitives). DERIVABLE = reducible compositions expressible as a Term-tree over the kernel; each one becomes a graph-resident *derivation* (a Concept with a `definition` Term-tree). NATIVE = codec-stream loops kept as direct kernel calls until the compiler does loop fusion well enough.

**Vocabulary**: only the 26 KERNEL items are *primitives* — they're irreducible by construction. The 55 DERIVABLE items get *derivations* (graph-resident definitions over the kernel). Calling the derivables "primitives" would mis-categorise reducible things as irreducible.

**Dynamic**: derivations are installed / replaced / removed by the agent dynamically, exactly the same way it manages Concepts, Microtheories, and Frames — `DerivationRegistry` is a fast-path lookup over graph-resident truth.

The architecture rule in `gamma-substrate/CLAUDE.md` ("primitive in Rust, composition in graph") exactly licenses this split — derivables ARE compositions, and they live in the graph.

---

## Bindings & access (4)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Var` | KERNEL | env access |
| `Lit` | KERNEL | embedded constant Value |
| `TypeOf` | KERNEL | graph header read |
| `Attr` | KERNEL | graph attr read |

## Collections (2)

| Variant | Class | Reason / sketch |
|---|---|---|
| `SetT` | KERNEL | Set/Tuple Value constructor; iteration root |
| `In` | DERIVABLE | `Exists(c, "_e", Eq(Var("_e"), x))` |

## Comparators (5)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Eq` | KERNEL | CPU op + Value-equality |
| `Lt` | KERNEL | CPU op |
| `Lte` | DERIVABLE | `Or(Lt(a,b), Eq(a,b))` |
| `Gt` | DERIVABLE | `Lt(b, a)` |
| `Gte` | DERIVABLE | `Or(Lt(b,a), Eq(a,b))` |

## Graph traversal (3)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Neighbours` | KERNEL | adjacency walk; memoised in Filter cache |
| `InNeighbours` | KERNEL | reverse-adjacency walk |
| `MapNeighbours` | DERIVABLE | `MapSet(Neighbours(src, et), "_n", Var("_n"))` — pure rename |

## Reductions (10) — biggest collapse

| Variant | Class | Reason / sketch |
|---|---|---|
| `Filter` | KERNEL | the iteration combinator (collection→collection); memoised |
| `Pick` | KERNEL | first-element of a set; primitive iteration cap |
| `Count` | DERIVABLE | `Fold(s, "_e", 0, Plus(Var("acc"), 1))` |
| `Exists` | DERIVABLE | `Gt(Count(Filter(s,v,p)), Lit(0))` |
| `Sum` | DERIVABLE | `Fold(s, v, 0, Plus(Var("acc"), value))` |
| `Prod` | DERIVABLE | `Fold(s, v, 1, Times(Var("acc"), value))` |
| `MinOver` | DERIVABLE | `Fold` with `If(Lt(value, acc), value, acc)` + default |
| `MaxOver` | DERIVABLE | symmetric (use direct `Gt`, NOT `Neg∘MinOver∘Neg` — NaN/±0 risk) |
| `Argmax` | DERIVABLE | `Fold(s, v, (None,−∞), If(Gt(value, Nth(acc,1)), (v,value), acc))` then `Nth(_,0)` |
| `Argmin` | DERIVABLE | symmetric |

**This subgroup is why we need a `Fold` kernel addition.**

## Codec primitives (10)

| Variant | Class | Reason / sketch |
|---|---|---|
| `BitsAt` | KERNEL | bit-level read; CPU-fundamental |
| `BitsWrite` | KERNEL | bit-level write; CPU-fundamental |
| `BitsAtAll` | DERIVABLE | `Fold(reads, r, (), append(BitsAt(...)))` |
| `BitsWriteAll` | DERIVABLE | `Fold(writes, w, buf, BitsWrite(acc, Nth(w,0), Nth(w,1), Nth(w,2)))` |
| `ExpGolombDecode` | DERIVABLE | count-leading-zeros via Fold + suffix BitsAt |
| `ExpGolombDecodeSigned` | DERIVABLE | `ExpGolombDecode` + zigzag map |
| `ExpGolombEncode` | DERIVABLE | inverse using BitsWrite |
| `ExpGolombEncodeSigned` | DERIVABLE | inverse zigzag + Encode |
| `HuffmanDecodeStream` | NATIVE | tight per-symbol loop; derivable but loses perf until compiler fuses |
| `HuffmanEncodeStream` | NATIVE | same |

## Bridge primitives (2)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Holds` | KERNEL | concept resolution + recursion-depth guard |
| `EvalSubgraph` | KERNEL | **the Axiom 3 bridge — load a Term subgraph + evaluate. THIS is what makes derivable definitions runnable** |

## Boolean (3)

| Variant | Class | Reason / sketch |
|---|---|---|
| `And` | KERNEL | short-circuit CPU op |
| `Or` | KERNEL | short-circuit CPU op |
| `Not` | KERNEL | CPU op |

## Arithmetic / scalar math (11)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Abs` | KERNEL | CPU op |
| `Neg` | KERNEL | CPU op |
| `Plus` | KERNEL | CPU op (n-ary) |
| `Minus` | KERNEL | CPU op |
| `Times` | KERNEL | CPU op (n-ary) |
| `Div` | KERNEL | CPU op |
| `Mod` | KERNEL | CPU op |
| `Pow` | KERNEL | special cases need native math |
| `Sqrt` | KERNEL | single CPU op |
| `Min` | KERNEL | CPU op (n-ary) |
| `Max` | KERNEL | CPU op (n-ary) |

## Control (1)

| Variant | Class | Reason / sketch |
|---|---|---|
| `IfThenElse` | KERNEL | control flow |

## Geometry / vectors (5)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Vec_` | DERIVABLE | tuple constructor; `SetT` (ordered) suffices |
| `VecAdd` | DERIVABLE | `Fold` over arity with `Plus` per element |
| `VecSub` | DERIVABLE | symmetric with `Minus` |
| `Dot` | DERIVABLE | `Fold(range(arity), i, 0, Plus(acc, Times(Nth(a,i), Nth(b,i))))` |
| `Magnitude` | DERIVABLE | `Sqrt(Dot(v, v))` |

## Rotation / angle (6)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Sin` | KERNEL | transcendental |
| `Cos` | KERNEL | transcendental |
| `Atan2` | KERNEL | transcendental + quadrant logic |
| `Bearing` | DERIVABLE | `Atan2(Attr(v,"y"), Attr(v,"x"))` |
| `Rotate` | DERIVABLE | element-wise `Sin/Cos` composition |
| `AngleBetween` | DERIVABLE | `Atan2(cross(a,b), Dot(a,b))` |

## Set algebra (4)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Union` | KERNEL | dedup merge; efficient impl matters |
| `Intersect` | DERIVABLE | `Filter(a, "_e", In(Var("_e"), b))` |
| `Difference` | DERIVABLE | `Filter(a, "_e", Not(In(Var("_e"), b)))` |
| `MapSet` | KERNEL | collection→collection iteration combinator |

## Edge-attr DSL (3)

| Variant | Class | Reason / sketch |
|---|---|---|
| `Edges` | KERNEL | enumerate outgoing edges |
| `EdgeAttr` | KERNEL | edge attr read |
| `NodesWhere` | KERNEL | index-backed lookup |

## Rendering / surfaces (15) — second biggest collapse

| Variant | Class | Reason / sketch |
|---|---|---|
| `Surface` | KERNEL | Value constructor |
| `Cat` | KERNEL | concat — fundamental |
| `Slot` | KERNEL | renderer sentinel |
| `Join` | DERIVABLE | fold with separator interleaving |
| `Bytes` | DERIVABLE | `Cat(U8(x), U8(y), ...)` |
| `U8` | KERNEL | 1-byte encode — fundamental |
| `U16LE` | DERIVABLE | `Cat(U8(Mod(x,256)), U8(Div(x,256)))` |
| `U32LE` | DERIVABLE | as U16LE, 4 bytes |
| `U64LE` | DERIVABLE | as U16LE, 8 bytes |
| `LEB128` | DERIVABLE | Term-tree using `BitsWrite` + control |
| `Lines` | DERIVABLE | `Join("\n", items)` |
| `Label` | KERNEL | symbolic sentinel |
| `Let` | KERNEL | env binding |
| `Nth` | KERNEL | tuple/array index — fundamental |
| `Render` | KERNEL | renderer dispatch sentinel |

---

## Kernel gaps to fill

**One required addition:**

- **`Fold { source, var_name, acc_name, init, body }`** — generic iteration combinator. Currently every reduction has its own native match arm because the kernel doesn't expose a fold. Adding one variant unlocks ~20 derivations.

  Semantics: iterate `source`, evaluate `body` with `var_name` ← element and `acc_name` ← running accumulator (starting at `init`), return final acc.

**Zero other kernel additions required.** Nth, SetT, IfThenElse, arithmetic — sufficient.

**Net change to term.rs:** +1 variant (Fold), −55 variants (derivables). **−54 variants**, ~2,269 LOC → ~700-800 LOC.

---

## Parity risks to test

- **`MaxOver`/`MinOver` empty-source `default`** — need sentinel threading through accumulator.
- **`Argmax`/`Argmin` tie-breaking** — "first encountered" requires `Gt` (strict), not `Gte`.
- **`Sum`/`Plus` numeric overflow** — derivation must use same `wrapping_add` semantics.
- **`ExpGolombDecode` leading-zero count** — fold derivation is correct but slow until compiler fuses; flag for codegen attention.
- **`Holds` recursion depth guard** — kernel; do not derive.

---

## Phasing

- **Phase A (this audit)**: done.
- **Phase B (in progress)**: add `Fold` to kernel. Install graph-resident `Derivation` Concept nodes (Term-tree definitions) for the 55 derivables. Runtime `evaluate()` checks the `DerivationRegistry` per variant; if a derivation is registered, args bind under conventional names and the derivation evaluates. Empty registry = native dispatch. Done so far: Fold + dispatch mechanism + 10 derivables (Gt, Lte, Gte, Bearing, In, Magnitude, Rotate, AngleBetween, Intersect, Difference). 23/23 tests green incl. a dynamic install-then-remove proof.
- **Phase C**: property-test parity per derivable.
- **Phase D**: remove the 55 native match arms + jsonio entries.
- **Phase E**: install-time compiler passes on kernel-only Term-trees — constant folding, CSE, fold fusion. The body-taking derivables (Sum/Prod/Count/MinOver/MaxOver/Argmax/Argmin/MapSet/Join/Bytes/Lines/LEB128/BitsAtAll/BitsWriteAll/ExpGolomb*) want install-time Term-rewriting because their derivation depends on the *Term* of `value`/`body`, not its value — which can't pass through the env-binding dispatch shape used in Phase B.
- **Phase F** (separate scope): native-callable Term wrappers for `cabac.rs` / `h264_*.rs` / audio cortex DSP.
