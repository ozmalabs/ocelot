# The four shape levels — measured, 2026-08-25

The question: *what is the shape of graphs, of rules, of admissibility, and of the solution we
want?* This is the measurement before the design, so that the design is not built on an
impression.

Everything below is a static scan of this tree at `305a22b`, engine-free (the installed engine was
unmeasurable at the time — its `.so` had been replaced without its build record, so provenance
correctly refused).

## 1. They are not four kinds of shape. They are one operation on four objects.

`recognise → residual → mint → re-recognise` is the sd loop, and it is object-agnostic: the
codebook loader in `shape_decode.rs` turned out to be grain-agnostic already
(`META_SHAPE_FIRST_CLASS_RESULTS.md` confirmed that by reading it rather than assuming). What
actually differs between the four levels is not the operation. It is **whether the shape is HELD**.

| level | signature computed | codebook held | grows |
|---|---|---|---|
| **1. graphs** | 1371 refs to `ShapeSignature` | **yes** — 502 stroke + 54 character shapes | **yes** — 133 mint/epoch rules across 4 seeds |
| **3. admissibility** | — | **yes** — 1728 productions in seeds | **barely** — 9 minting rules in 3 seeds (`gamma_residual`, `gamma_production_adopt`, `reflective_codegen_axiom3`) |
| **2. rules** | 67 refs to `where_signature` | **NONE** | no |
| **4. solution** | yes (manifold tube per assessment) | **NONE** | no |

**A level that computes a shape and discards it can recognise but never accumulate.** The sd loop's
power was never the signature — it is the MINT. Levels 2 and 4 have signatures without mints, which
is exactly the shape of a system that can answer today's question and has learned nothing by
tomorrow.

This is not speculation about level 4: `CLAUDE.md` already states it as a limit — *"the current gate
enforces this shape residual within each assessment; it does not persist lineage across
assessments"*, and manifold momentum is *"nonphysical continuity when longitudinal callers reuse an
established manifold"*. The caller is asked to carry what the substrate does not hold.

## 2. Level 2 met level 3 today, and had nowhere to live

`stage_a::rule_is_derivable` decides whether a drain may be speculated, from
`read_set ∩ write_set` — **the shape of a rule**. That is an admissibility judgement keyed on a
shape. It is exactly what Γ is for.

It could not be a Γ production, because:

```rust
pub struct Production {
    pub src: NodePattern,      // a NODE
    pub edge_type: Sym,        // an EDGE TYPE
    pub tgt: NodePattern,      // a NODE
    pub where_: Option<TermIdx>,
    pub weight: TermIdx,
}
```

**Γ's only object is an edge.** It answers *may this edge exist?* and nothing else. So an
admissibility rule whose object is a RULE has to be hardcoded in Rust, outside the grammar, ungated
by the grammar's own machinery and invisible to anything that reasons about admissibility.

That is a vocabulary gap, not a missing feature: the substrate has a general notion of "what is
allowed" that can only be expressed about one kind of thing.

Corroborating scale, measured: **100 of 797 top-level seeds mint edges through ZERO productions**,
accounting for 449 `add_edge` effects. `f16_flight_path_control` alone has 54 edge-minting effects
and no productions. So even for edges — the one object Γ *can* talk about — admissibility is
frequently not consulted.

## 3. The solution level is the disconnected one

Two different things live at level 4, and they do not share machinery.

* **Goal composition DOES reuse level 1's codebook.** `compose_design_for_goal` / `induce_concern`
  are the same `ShapeDecode` op at two points of one loop — a goal is decoded against held parts,
  exactly as an observation is.
* **The future manifold does not.** `runners/dsl/src/future_manifold.rs` (854 lines) contains
  **zero** references to `ShapeDecode` or `ShapeSignature`. Its vocabulary is its own:
  `DeformationRecord`, `DimensionNarrativium`.

So the one place in the engine that gates **irreversible, externally consequential action** shares
no shape vocabulary with the layer that learns shapes. It computes a tube per assessment, checks
containment, and discards it.

## 4. What this says to build, in order of how well the evidence supports it

**(a) A rule-shape codebook — the best-evidenced.** `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` already
measured the payoff: 318 parallelograms in the rule corpus, and 200/200 sampled transfers
algebraically lossless, well-defined, and novel — a rule absent from all 2,851 corpus recognisers,
derived by one `AntiUnifyWitness` and one `Substitute`, installed, and firing correctly. The algebra
works and the corpus supports it. What is missing is that nothing is HELD: each transfer is
recomputed and forgotten. The same doc measured why the obvious approach fails (unconditional
mirroring: 190 at-risk files, +2,557 nodes per checkpoint cycle, no convergence) and named the fix
(lazy, via `add_term_subgraph`). This is the shortest path from "shape is computed" to "shape
accumulates".

**(b) Γ over objects other than edges.** Generalising `Production`'s `src`/`tgt` from node patterns
to a pattern over *any* addressable thing would let `rule_is_derivable` be graph data instead of
Rust — and would give the 9 existing Γ-minting rules something larger to grow. This is a bigger
change and touches `check_edge`, the hottest admissibility path.

**(c) Manifold shapes in the codebook.** The most valuable and the least supported by existing
evidence. If a tube were a `ShapeSignature`, then "this decision is the same shape as that one"
becomes decidable, and manifold momentum stops being something the caller must carry. But nothing
here has measured that solution-shapes recur often enough to be worth a codebook — and on this
tree's own standing rule, that measurement comes before the build.

## 5. The honest boundary of this document

This is a survey, not a result. It measures what is held and what is discarded; it does NOT show
that holding rule-shapes or manifold-shapes improves any outcome. (a) is well-evidenced by prior
measurement, (b) is a design observation with one concrete instance, and (c) is a hypothesis with
no supporting measurement at all. Nothing here has been built.
