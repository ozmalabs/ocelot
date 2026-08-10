# graph_interrogate — the "ASK" counterpart to the graph visualiser's "LOOK"

A **READ-ONLY** interrogation tool over the Jabberwock's (G, Γ) substrate. The
visualiser (`graph_visualiser.html`) lets you *look* at the glass box; this lets
you *ask* it questions — using the agent's **own query language**.

## The principle: expose the query engine, don't rebuild it

The Jabberwock is already a typed graph **and already has a query language** — the
substrate DSL that its rules' `where`/`MATCH` clauses are written in
(`NodesOfType`, `Filter`, `Neighbours`, `InNeighbours`, `Eq`, `Attr`, `Count`, …).
So this tool does **not** reimplement a matcher. It loads a `graph_to_dict`
snapshot into a real `substrate_rs.Substrate` via `graph_from_dict` (the **live
Rust runtime**) and every query runs on the substrate's own machinery:

* **structural queries** (`node`, `nodes_of_type`, `neighbours`, `in_neighbours`,
  `subgraph`, `path`) use the native `Substrate.nodes()/node()/neighbours()/
  in_neighbours()` accessors — the same accessors the Rust rule engine walks;
* **`graph_query`** ships a DSL Term-tree straight to the substrate's own
  evaluator (`evaluate`). The query language **is** the DSL, so *how you ask* ==
  *how the agent thinks*.

## Files

| File | What |
|---|---|
| `scripts/graph_interrogate.py` | The tool: `GraphInterrogator` class + CLI. |
| `scripts/graph_interrogate_mcp.py` | Thin MCP server — 9 tools, each a one-line delegation to `GraphInterrogator`. No new logic. |

## Query surface

| Query | CLI | What it returns |
|---|---|---|
| node | `node ID` | type + attrs of one node |
| nodes-of-type | `nodes-of-type TYPE` | ids + labels of all nodes of a type |
| neighbours | `neighbours ID [--edge E]` | out-neighbours grouped by edge type |
| in-neighbours | `in-neighbours ID [--edge E]` | in-neighbours grouped by edge type |
| subgraph | `subgraph ID... [--depth D] [--directed]` | ego/neighbourhood: nodes within D hops + induced edges |
| path | `path A B [--directed]` | a shortest path A→B if one exists (undirected by default) |
| **graph_query** | `query --term JSON` / `query --match STR` | **evaluate a DSL Term-tree on the live substrate engine** |
| types | `types` | node-type histogram |
| edge-types | `edge-types` | edge-type histogram |

Global flags (usable **before or after** the subcommand): `--dump PATH`
(default `var/encyclopedic_grounded_graph.json`), `--json` (machine form).

## `graph_query` — how it evaluates (no silent semantic invention)

`graph_query` **always** runs on the substrate's native evaluator. The result dict
is tagged `"engine": "live-dsl"`. There is **no** Python re-derivation of query
semantics and **no fallback engine** — the live Rust evaluator handled every
common pattern (`NodesOfType`, `Filter`, `Neighbours`, `Count`, `Eq`/`Gt`/…,
`Attr`, `And`, `StringIndexOf`) directly against the loaded snapshot, so a
fallback was neither needed nor built. If a term the evaluator cannot handle is
submitted, the tool surfaces the **native error** rather than guessing.

Two input forms, **both feeding the same evaluator**:

1. `--term` — a DSL **wire-form dict**, the exact JSON the rules are written in.
   Nest freely: `Filter(NodesOfType(...), var, Eq(Attr(Var, key), Lit))`.
   Accepts an inline string or `@file.json`.
2. `--match` — a **compact convenience string** that *compiles to* a DSL
   Term-tree. Pure sugar, not a second engine:
   ```
   TYPE [where ATTR OP VALUE [and ATTR OP VALUE ...]]
   OP ∈  ==  !=  <  <=  >  >=  ~     (~ = substring-contains, via StringIndexOf)
   ```
   `Concept where kind == ontological_root` compiles to a `Filter` over
   `NodesOfType("Concept")` with an `Eq(Attr(c,"kind"), Lit("ontological_root"))`
   predicate, which the native evaluator runs. The result is tagged
   `source: "match->term"`.

Node-set results also return the **induced subgraph** (edges among the matched
nodes), so you get the relevant subgraph, not just ids. Scalar results
(`Count`, …) come back tagged `result_kind: "scalar"`.

## Worked examples (against `var/encyclopedic_grounded_graph.json`)

```bash
# 1. all Microtheory nodes
python -m scripts.graph_interrogate nodes-of-type Microtheory
#   3 nodes: #734 lexical_ontology, #743 relations, #1006 psychology

# 2. one node's attrs
python -m scripts.graph_interrogate node 1006
#   #1006 Microtheory  name: "psychology"  description: "basic psychology..."

# 3. neighbours of the Agent hub (#0) along a specific edge type
python -m scripts.graph_interrogate neighbours 0 --edge asserts
#   asserts -> #713 sensed_implies_modeled, #719 quality_monotone..., #725 discovery_converges  (Theorems)

# 4. graph_query, RAW DSL term: the ontological-root Concepts
python -m scripts.graph_interrogate query --term \
  '{"type":"Filter","source":{"type":"NodesOfType","node_type":"Concept"},
    "var_name":"c","predicate":{"type":"Eq",
    "a":{"type":"Attr","node":{"type":"Var","name":"c"},"key":"kind"},
    "b":{"type":"Lit","value":"ontological_root"}}}'
#   [live-dsl] nodes: 7 nodes, 6 induced edges — entity, abstraction, physical_entity, ...

# 5. graph_query, --match sugar: Term-trees that reference node_type "BodyType"
#    (the DSL introspecting the agent's OWN query terms — analog of "rules referencing X")
python -m scripts.graph_interrogate query --match 'Term.NodesOfType where node_type == BodyType'
#   [live-dsl] nodes (source=match->term): #124 Term.NodesOfType BodyType

# 6. subgraph: ego-neighbourhood of the lexical_ontology Microtheory
python -m scripts.graph_interrogate subgraph 734 --depth 1
#   9 nodes, 14 edges — the Mt, its 7 root Concepts, and the Agent hub

# 7. path: Theorem #713 -> Microtheory #734 (both hang off the Agent hub)
python -m scripts.graph_interrogate path 713 734
#   length 2:  #713 --[<asserts]--> #0 Agent --[operates_in]--> #734
#   ("<asserts" = the edge was traversed against its direction, undirected mode)

# 8. graph_query scalar: Count all Lexeme nodes
python -m scripts.graph_interrogate query --term \
  '{"type":"Count","source":{"type":"NodesOfType","node_type":"Lexeme"}}'
#   [live-dsl] scalar  value: 235

# 9. --match numeric predicate (compiles Gt): LexSlots with order > 0
python -m scripts.graph_interrogate query --match 'LexSlot where order > 0'
#   [live-dsl] nodes: 47 nodes
```

### A genuine structural finding this surfaced

`path 746 0` (a Lexeme → the Agent hub) reports **no path found** — not a bug. In
this encyclopedic snapshot the lexicon cluster (`Lexicon -entry-> Lexeme -arg->
LexSlot`, ~120 nodes) is a **separate connected component** from the
Agent/Theorem/Term-tree machinery. The tool reports the true topology rather than
inventing a connection. (A `path` within a component, e.g. Theorem→Microtheory
above, resolves in length 2.)

## MCP server

`scripts/graph_interrogate_mcp.py` exposes the same nine queries as MCP tools
(`node`, `nodes_of_type`, `neighbours`, `in_neighbours`, `subgraph`, `path`,
`graph_query`, `types`, `edge_types`), each a one-line delegation to the same
`GraphInterrogator` — so `graph_query` over MCP still runs on the live DSL engine.

```bash
GRAPH_INTERROGATE_DUMP=var/encyclopedic_grounded_graph.json \
    python -m scripts.graph_interrogate_mcp     # stdio MCP server
```

The snapshot loads once at startup (env `GRAPH_INTERROGATE_DUMP`, else the
default). Requires the `mcp` Python SDK (already present in this environment).

## Discipline — READ-ONLY, mechanical

This tool **only reads and evaluates**. Source-audit:

```bash
# no mutation call anywhere in the tool:
grep -nE '\.add_node\(|\.add_edge|\.set_attr|\.set_type|\.remove_node|\.remove_edge|\.load_seed_manifest|\.tick\(|\.run_rules' \
    scripts/graph_interrogate.py     # -> no matches

# the only substrate methods it calls are reads + the evaluator:
grep -oE 'self\._s\.[a-z_]+' scripts/graph_interrogate.py | sort -u
#   self._s._inner  (-> .evaluate, read-only)
#   self._s.in_neighbours / neighbours / node / nodes
```

No mutation, no agent decisions, no Rust rebuild, no seed/canonical/gate/prereg
ceremony. It is a read-only lens on a saved (or freshly booted, via
`GraphInterrogator.from_live_boot`) substrate snapshot.

## Substrate API notes (gaps hit)

* `substrate_rs` exposes no Python factory for `NodesOfType` (it exists as a Rust
  DSL term, used throughout the seeds). `graph_query` therefore takes the DSL
  **wire dict** directly and hands it to the native evaluator — which is the
  cleaner surface anyway (arbitrary nested terms, no per-term Python factory).
* Native `NodeID` is an opaque wrapper (`.value` int, repr `#N`), not an `int`.
  The tool builds an `id → NodeID` index once at load so callers can address
  nodes by the plain integer id the dump/visualiser shows.
* `Substrate.node(nid)` needs a real `NodeID`; passing a bare int raises. Handled
  by the index above.
