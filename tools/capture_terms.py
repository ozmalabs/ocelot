"""Capture decision Terms as a seed manifest — Python DSL in, seed JSON out.

The migration's decision faculties are graph Terms. Rather than hand-transcribe
each into the `Term.<Variant>` node/edge JSON (laborious and error-prone for deep
nests), this tool takes Python `Term` objects — exactly what the agent's
`_make_X_term()` builders return — and produces the seed manifest mechanically:

    Python Term  --term_to_json-->  Term-JSON  --add_term_subgraph-->  graph subgraph
    --graph_to_dict-->  seed nodes/edges  + a named attachment edge to agent_root

So a faculty is captured by writing its formula once in the readable Python DSL
(`Minus(Lit(1.0), Div(Attr(Var("self"), "current"), ...))`) and naming it; the
tool emits a loadable, parity-faithful seed. This is migration tooling — a one-off
transpiler from Python Term-builders to graph-data seeds, deletable with the
Python it migrates.

Usage (programmatic):

    from substrate.dsl import Var, Lit, Attr, Minus, Div
    from tools.capture_terms import build_term_seed
    build_term_seed(
        "valuation_core", depends_on=[],
        description="...",
        named_terms={
            "resource_value_term": Minus(Lit(1.0),
                Div(Attr(Var("self"), "current"), Attr(Var("self"), "observed_max"))),
        },
        rules=[],
    )
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import substrate_rs as srs
from substrate.dsl import Term
from substrate.jsonio import term_to_json

SEED_DIR = ROOT / "seeds"


def terms_to_graph_fragment(named_terms: dict[str, Term]):
    """Materialise each named Python Term into a fresh substrate and return the
    seed (nodes, edges) — every Term as a `Term.*` subgraph, attached to
    agent_root by an edge named for the faculty. Mechanical."""
    scratch = srs.Substrate()
    inner = scratch._inner
    roots: dict[str, int] = {}
    for name, term in named_terms.items():
        tj = term_to_json(term)
        r = inner.add_term_subgraph(tj)
        roots[name] = r.value if hasattr(r, "value") else r
    d = inner.graph_to_dict()
    nodes = [{"local_id": n["id"], "type": n["type"], "attrs": n["attrs"]}
             for n in d["nodes"]]
    edges = [{"src": {"local": e["src"]}, "tgt": {"local": e["tgt"]},
              "type": e["type"], "attrs": e.get("attrs", {})}
             for e in d["edges"]]
    for name, rid in roots.items():
        edges.append({"src": {"role": "agent_root"}, "tgt": {"local": rid},
                      "type": name, "attrs": {}})
    return nodes, edges


def rule_node_to_dict(graph, rule_nid):
    """Extract a `make_rule`-built Rule node into the loader's rules-section
    format. `make_rule` already stored `match` / `where` (term_to_json) /
    `effect` (`{"__term__": ...}`-encoded) on the node — exactly what the Rust
    `parse_rule_json` accepts — so this only remaps `id`→`name` and the
    singular `effect`→`effects`. The mechanical inverse of the loader, for
    capturing graph-native Rules the agent built (e.g. the surprise cascade)."""
    attrs = graph.node(rule_nid).attrs
    return {
        "name": attrs.get("id") or "anonymous_rule",
        "match": attrs.get("match", []),
        "where": attrs.get("where"),
        "effects": attrs.get("effect", []),
    }


def build_term_seed(seed_id, *, depends_on, description,
                    named_terms, rules=(), version="1.0.0", write=True):
    """Build (and optionally write) a seed manifest from Python Term objects +
    optional RewriteRule dicts. Returns the manifest dict."""
    nodes, edges = terms_to_graph_fragment(named_terms)
    manifest = {
        "id": seed_id, "version": version, "depends_on": list(depends_on),
        "description": description,
        "nodes": nodes, "edges": edges, "productions": [], "rules": list(rules),
    }
    if write:
        path = SEED_DIR / f"{seed_id}.json"
        with open(path, "w") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return manifest
