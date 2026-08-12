# Γ reflection wiring — pre-registration

**Posture:** MEASURE-THEN-BUILD. `SELF_REFERENCE_INFINITY_GROUNDING.md` §3.2
found that the admissibility grammar Γ (`ConsistencyChecker.grammar`, a plain
Rust `Grammar { productions: Vec<Production>, .. }` struct owned by
`Substrate.checker`) is not routed through `reflect::term_to_subgraph` and has
no `production_from_node`/`grammar_from_graph` reader, unlike the exactly
analogous Rule layer (`graph_rules::rule_from_node`). §5 recommendation 2(ii)
is this rung's literal charter: add the reader, and route
`Substrate::add_production` through `reflect::term_to_subgraph` for the
`where_`/`weight` Terms specifically. This doc registers the GO/NO-GO bar
**before** writing any Rust, per this folder's own house discipline
(`GENERIC_ORDER_N_PREREG.md`, `INCREMENTAL_MATCH_PREREG.md`).

**Engine baseline (unchanged source, `main` tip `003a121`).**
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`.
Worktree: `/home/matt/ocelot-gamma-reflection-wiring`, branch
`gamma-reflection-wiring`, detached from `003a121`.

---

## 0. Investigation findings (the actual current shape — verified against code, not the stale plan doc)

**0.1 `Production`'s real fields** (`runners/dsl/src/grammar.rs:32-39`):

```rust
pub struct Production {
    pub src: NodePattern,       // { type_: Sym, var: Sym }
    pub edge_type: Sym,
    pub tgt: NodePattern,
    pub where_: Option<TermIdx>,
    pub weight: TermIdx,        // always present; defaults to Lit(1.0)
    pub provenance: Sym,
}
```

`Grammar` (`grammar.rs:48-57`) is `{ productions: Vec<Production>, index:
FxHashMap<(Sym,Sym,Sym), SmallVec<[ProdIdx;2]>>, node_types: FxHashSet<Sym>,
edge_types: FxHashSet<Sym> }`, owned by `ConsistencyChecker` (`checker.rs:44`),
owned by `Substrate.checker`.

**0.2 `Substrate::add_production` (the literal target of recommendation-ii)
has exactly TWO Rust-internal callers**, both in `substrate.rs`:
`declare_shares_shape` (line 1852) and `declare_relation_edge` (line 1959) —
both audio/vision "wire one relation type admissible" helpers. Neither is
referenced by name in any Python test (`grep -rn "declare_shares_shape\|shares_shape" tests/*.py`
returns nothing). This is a small, low-traffic call site — the blast radius of
editing `Substrate::add_production` itself is tiny.

**0.3 A REAL, PREVIOUSLY-UNFLAGGED DISCONNECT, found during this
investigation.** The PyO3-exposed `PySubstrate::add_production`
(`py.rs:7803-7820` — the method every Python caller actually uses: 129
`add_production(` call sites across `tests/*.py`, plus `substrate/world_adapter.py`)
does **NOT** call the Rust inherent `Substrate::add_production`. It calls
`inner.checker.grammar.add(p)` directly:

```rust
fn add_production(&mut self, py: Python<'_>, production_json: &Bound<'_, PyAny>) -> PyResult<()> {
    ...
    for p in parsed.productions {
        inner.checker.grammar.add(p);   // NOT self.add_production(p)
    }
    Ok(())
}
```

This means the PyO3 surface — the path essentially all real usage (seed
loading, every test) goes through — **already silently bypasses
`gamma_epoch.bump()`** (the L2 adaptive-dispatcher cache-invalidation-on-Γ-change
contract `substrate.rs:794-796`/`809-816` documents as "wired path that an
installed dispatcher observes"). This is a genuine, real bug independent of
this rung's charter, found as a side effect of reading `add_production`'s two
call sites side by side. **Scoping decision (stated up front, see §2):** this
rung edits the Rust inherent `Substrate::add_production` only (the literal
text of recommendation 2(ii)), and does **not** additionally reroute the PyO3
binding to fix this pre-existing epoch-bump gap or to pick up the new mirror —
that is a materially larger, separately-risked change (see §2.3). It is named
here, not fixed, and recommended as explicit follow-up.

**0.4 A second, more important piece of prior art: a graph-resident
"Γ_dynamic" ALREADY EXISTS — in Python, disconnected from the real Γ.**
`substrate/grammar.py` (`Grammar.to_subgraph`/`from_subgraph`) and
`substrate/world_adapter.py` (`boot_gamma_meta`, `gamma_dynamic` property,
`_append_production`, `_supersede_production`, `grow_gamma`) are NOT deleted —
they are the live implementation of `gamma_meta_core_migration_plan.md`'s
Slice A/B, built directly against `self.s`/`self.inner` (the PyO3-wrapped Rust
substrate). They write `Production`/`NodePattern`/`Grammar`-typed nodes onto
the SAME Rust `TypedGraph` this rung targets, via generic `add_node`/`add_edge`
calls. Two things distinguish this from what recommendation 2(ii) actually
asks for, and both matter for scoping this rung correctly:

- **It is disconnected from `ConsistencyChecker.grammar`.** `grow_gamma`
  (`world_adapter.py:6788-6852`) calls `self._append_production(...)`, which
  only ever calls `self.s.add_node("Production", ...)` +
  `self.inner.add_edge(...)` — it never calls `add_production` (neither the
  PyO3 binding nor, transitively, the Rust inherent method) for the newly
  discovered production. The discovered relation becomes graph-resident
  bookkeeping (feeding `quality_of_gamma`'s monotone score) but is **never
  admissible** — it does not touch the object `check_edge` actually gates
  against. This is Γ_dynamic in the CuriousAgent sense (an observational
  record of discovered relation shapes), not Γ in the paper's Definition-2
  sense (the admissibility grammar). CLAUDE.md's "Γ_meta substrate ... now
  runs graph-native" sentence is accurate for THIS mechanism but, per
  `SELF_REFERENCE_INFINITY_GROUNDING.md` §3.2's finding, still conflates it
  with the (unrelated) admissibility Γ.
- **Its `where`-clause is not a Term subgraph — it's a JSON string.**
  `_append_production` stores `attrs["where_json"] = json.dumps(term_to_json(production.where))`
  on the `Production` node — an opaque string attr, not a `Term.*` subgraph
  reachable via `reflect::term_to_subgraph`/`term_from_subgraph`. It does not
  use the generic reflection mechanism at all.

**Conclusion from §0.4:** this existing Python mechanism does not substitute
for recommendation 2(ii) and does not change this rung's charter — it targets
a different, already-graph-native object (Γ_dynamic, the discovered-relations
record) using a cheaper JSON-blob shortcut, not the paper's Γ
(`ConsistencyChecker.grammar`) via genuine Term reflection. But it is real,
tested (`tests/test_curious_agent_gamma_meta_migrated.py`,
`tests/test_gamma_growth_migrated.py`), and its existence means: **to avoid a
type-name collision that would make `substrate/world_adapter.py`'s existing
`gamma_dynamic` view ambiguous or confusable with this rung's new mirror**,
this rung's new node types must NOT reuse the strings `"Grammar"` /
`"Production"` / `"NodePattern"` — see §1.2.

---

## 1. The build, registered

### 1.1 Scope (literal recommendation 2(ii), no more)

- `production_from_node` / `grammar_from_graph` — a reader, the exact
  analogue of `graph_rules::rule_from_node`, in a new file
  `runners/dsl/src/grammar_reflect.rs` (mirrors `graph_rules.rs`'s naming and
  module-doc precedent).
- Route the Rust inherent `Substrate::add_production` (substrate.rs:809-816)
  through `reflect::term_to_subgraph` for the `where_`/`weight` Terms
  specifically (not the whole `Production` struct — src/tgt/edge_type/
  provenance are scalar Syms, encoded as plain node attrs exactly like
  `graph_rules::rule_from_node` encodes a Rule's scalar fields).
- A `gamma_graph_root: Option<NodeID>` field on `Substrate`, lazily
  initialised on first mirrored `add_production` call — the auto-vivified
  root the mirror's `Grammar-production->Production` edges hang off,
  matching `gamma_meta_core_migration_plan.md`'s Slice-A shape
  (`gamma_root` node + `Production`-typed nodes + `Grammar-production->
  Production` edges), re-targeted at the Rust runtime.

**Explicitly out of scope, and why (see §0.3):** rerouting the PyO3
`add_production` binding. **Explicitly out of scope, and why (§0.4):**
touching `substrate/grammar.py` / `substrate/world_adapter.py`'s existing
Γ_dynamic machinery — different object, working, not this rung's charter, and
`domains/`/`seeds/` edits are outside this rung's file-scope constraint
anyway.

### 1.2 New graph vocabulary — deliberately distinct names

To avoid colliding with the pre-existing (§0.4) Python Γ_dynamic node types,
this rung's mirror uses distinct type strings: `GammaGrammar` (root),
`GammaProduction`, `GammaNodePattern`. This is also more honest: it is a
mirror of the paper's actual Γ (`ConsistencyChecker.grammar`), not the
CuriousAgent's discovered-relations record, and the name should not suggest
otherwise.

### 1.3 GO/NO-GO thresholds, registered before measuring

| # | Bar | Threshold |
|---|---|---|
| 1 | New Rust LOC | ≤ 300 net new lines across `grammar_reflect.rs` + the `substrate.rs`/`grammar.rs` edits. Above this, the "cheap doc-only fix" (recommendation i) should be reconsidered instead. |
| 2 | `check_edge` hot path | ZERO change to its algorithm or complexity — still an O(\|candidates\|) scan over `checker.grammar.index`, no graph traversal added. (`checker.grammar` remains the authoritative struct `check_edge` reads; see §3 for what this means for "same data".) |
| 3 | `grammar_to_json`/`grammar_from_json` wire format | Byte-identical JSON output for the SAME `Grammar` struct, before and after — verified by NOT editing `jsonio.rs` at all (the mirror is a parallel write path, not a replacement), plus a direct round-trip check. Every caller of `grammar_to_json`/`grammar_from_json` (grepped repo-wide: `viz/server.py`, `substrate/jsonio.py`/`graph.py`/`__init__.py`/`world_adapter.py`, 10 test files, `runners/dsl/python/substrate_rs/__init__.py`, `py.rs`'s own PyO3 `grammar_to_json`/`add_production` methods, a handful of `scripts/jabberwock_omniglot_run*.py`, `domains/memory_shape_faculty.py`) reads/writes `Grammar`/`Production` Rust structs or their JSON — NONE of them touch `TypedGraph` nodes, so none can be affected by an ADDITIVE graph-mirror write as long as `jsonio.rs` itself is untouched. |
| 4 | Blast radius on existing behaviour | The mirror write only fires on `Substrate::add_production`'s ~2 real call sites (§0.2) plus new tests calling it directly. `pytest -k migrated` (full breadth, not scoped) must be paired-identical before/after (same failing node-id list, ideally empty-vs-empty). `cargo test` must be green before/after. |
| 5 | Round-trip / "same data" demonstration | `grammar_from_graph` on the mirror root must reconstruct a `Grammar` whose productions are content-equal (via `jsonio::term_to_json` comparison on `where_`/`weight`, plus Sym-string comparison on src/tgt/edge_type/provenance) to `checker.grammar`'s own productions, for every production added since the mirror started. This demonstrates the two representations are written from ONE call and cannot yet drift *for productions added via `Substrate::add_production`* — see §3 for the honest boundary on what this does NOT prove. |

**GO** iff bars 1-4 all clear and bar 5's reconstruction succeeds (content-equal,
not merely "some graph nodes exist"). **NO-GO** (fall back to recommendation
i, the doc-only fix) iff bar 3 cannot be held without editing `jsonio.rs`, or
bar 4 shows any regression in the full migrated pytest bench that isn't a
trivial, obviously-safe fix (e.g. a test asserting an exact node count that
legitimately needs updating because it is now measuring the mirror's own
nodes — see next paragraph for the pre-identified risk).

**Known risk flagged before building, not after (bar 4's teeth).** 18 test
files were found (`grep`) to combine `add_production(` calls with
node-count-shaped assertions (`len(...nodes...)`, `graph_to_dict()["nodes"]`,
etc.) in the same file. Because this rung's mirror does **not** touch the
PyO3 `add_production` binding those 129 call sites all go through (§0.3), the
mirror should not fire for any of them and this risk should be theoretical —
but it is exactly the kind of thing "measure, don't assume" exists to catch,
so the full `pytest -k migrated` run (not a scoped slice) is the actual
arbiter, per the brief's own instruction.

---

## 2. What "graph-resident" will and will not mean after this build

Per §3.2's own "conflates two related but formally distinct objects" finding,
this PREREG commits, in advance, to the exact honesty boundary the RESULTS
doc must hold to:

1. **`ConsistencyChecker.grammar` remains the sole thing `check_edge` reads.**
   It is not replaced, and its performance characteristics are unchanged.
   This build does NOT make the graph the "source of truth" for admissibility
   checking — that would require either rebuilding the index from the graph on
   every `check_edge` call (too slow) or invalidating/rebuilding on every
   `gamma_epoch` bump (a materially different, riskier design not attempted
   here).
2. **What genuinely becomes graph-resident:** every `Production` added via
   the Rust inherent `Substrate::add_production` gets a real `GammaProduction`
   node, with its `where_`/`weight` Terms as real `Term.*` subgraphs
   (reachable via `reflect::term_from_subgraph`), wired to a `GammaGrammar`
   root via `GammaGrammar -production-> GammaProduction` edges — literal graph
   data, not a JSON blob, satisfying recommendation 2(ii)'s literal text.
3. **What does NOT become graph-resident:** anything added via the PyO3
   `add_production` binding (§0.3) — i.e., essentially all current real-world
   usage (seed loading, every existing Python test, `world_adapter.py`'s own
   Γ-growth). For that traffic, Γ remains exactly as `SELF_REFERENCE_INFINITY_GROUNDING.md`
   §3.2 found it: a pure Rust-side struct. The RESULTS doc must say this
   plainly, not fold it into a headline "Γ is now graph-native" claim.
4. **"Same data, not two copies that can drift" is TRUE only for the
   `Substrate::add_production` call path, and only in the forward
   (write) direction** — nothing currently reads the mirror back into
   `checker.grammar` (no rebuild-on-load, no supersede-via-mirror). If a
   future caller mutated `checker.grammar.productions` directly (bypassing
   `add_production`), or removed a production without a corresponding graph
   edit, the two would desync silently — there is no consistency check
   enforcing they stay equal after this build. This is the honest scope
   this rung's own brief asked to be named precisely rather than overclaimed.

---

## 3. Regression protocol

1. Build: `cd runners/dsl && maturin develop --release` (watch OOM; drop to
   `CARGO_BUILD_JOBS=2` if needed). Coherence probe: `add_node("T",
   {"lst":[1,2,3],"tup":(1,2,3)})` round-trips list/tuple distinctly.
2. `cargo test` (debug) inside `runners/dsl/`, full suite — before (baseline
   commit, pre-edit) and after.
3. `pytest tests/ -k migrated` (full repo bench, not scoped) — before (on
   the freshly-built baseline `.so`) and after (on the rebuilt `.so` with
   changes) — paired failing-node-id lists, not counts.
4. New Rust unit tests in `grammar_reflect.rs`/`substrate.rs` proving bar 5.
5. Report GO/NO-GO plainly against the registered bars in §1.3; a clean NULL
   (falling back to recommendation i) is a complete, acceptable outcome if
   any bar fails to clear.
