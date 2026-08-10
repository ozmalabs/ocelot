"""graph_interrogate — the "ASK" counterpart to the graph visualiser's "LOOK".

A READ-ONLY interrogation tool over the Jabberwock's (G, Γ) substrate. It does
NOT reimplement a query engine — it EXPOSES the one the agent already has. A
`graph_to_dict` snapshot is loaded into a real `substrate_rs.Substrate` via
`graph_from_dict` (the LIVE Rust runtime), and every query runs on the
substrate's OWN machinery:

  * structural queries (node / nodes_of_type / neighbours / in_neighbours /
    subgraph / path) use the native `Substrate.nodes()/neighbours()/…`
    accessors — the same graph accessors the Rust rule engine walks;
  * `graph_query` evaluates a substrate DSL Term-tree (the wire form the rules
    are written in — `NodesOfType`, `Filter`, `Neighbours`, `Eq`, `Attr`, …)
    against the graph with the substrate's OWN evaluator (`evaluate`). The
    query language IS the DSL, so "how you ask" == "how the agent thinks".

Discipline: READ-ONLY. This module never calls a mutation on the loaded graph
(no add_node / add_edge / set_attr / remove_* / set_type / load_seed_manifest /
tick / run_rules). It only reads and evaluates. A source-audit test lives at the
bottom of GRAPH_INTERROGATE.md.

There is NO Python re-derivation of query semantics: `graph_query` always runs on
the native evaluator (engine tag "live-dsl"). The optional `--match` mini-syntax
is pure sugar — it COMPILES to a DSL Term-tree that the native evaluator runs; it
is not a second engine. If a term the evaluator can't handle is submitted, the
tool reports the native error rather than silently inventing an answer.

Usage (CLI):
    python -m scripts.graph_interrogate node 734
    python -m scripts.graph_interrogate nodes-of-type Microtheory
    python -m scripts.graph_interrogate neighbours 0 --edge asserts
    python -m scripts.graph_interrogate in-neighbours 742
    python -m scripts.graph_interrogate subgraph 0 --depth 1
    python -m scripts.graph_interrogate path 746 745
    python -m scripts.graph_interrogate query --term '{"type":"NodesOfType","node_type":"Theorem"}'
    python -m scripts.graph_interrogate query --match 'Concept where kind == ontological_root'

    # any query: add --json for the machine form, --dump PATH for another snapshot.

Programmatic:
    from scripts.graph_interrogate import GraphInterrogator
    gi = GraphInterrogator.from_dump("var/encyclopedic_grounded_graph.json")
    gi.nodes_of_type("Microtheory")
    gi.graph_query(term={"type": "NodesOfType", "node_type": "Theorem"})
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import deque
from typing import Any, Iterable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "runners", "dsl", "python"))

from substrate_rs import Substrate  # noqa: E402

DEFAULT_DUMP = "var/encyclopedic_grounded_graph.json"

# Attribute keys tried, in order, to give a node a human label.
_LABEL_KEYS = ("name", "form", "word", "id", "label", "title", "text", "kind",
               "concept", "role", "node_type", "process", "topic", "description")


# --------------------------------------------------------------------------- #
# NodeID <-> int helpers. The native NodeID is an opaque wrapper with a `.value`
# int; `Substrate.node(nid)` needs a real NodeID, so we mint one from the loaded
# id-index map. No mutation involved — pure lookup.
# --------------------------------------------------------------------------- #
def _nid_int(nid: Any) -> int:
    """int of a native NodeID (has `.value`) or a plain int."""
    v = getattr(nid, "value", None)
    return int(v) if v is not None else int(nid)


class GraphInterrogator:
    """READ-ONLY interrogator over a loaded substrate snapshot."""

    def __init__(self, substrate: Substrate, raw: dict[str, Any]) -> None:
        self._s = substrate
        self._raw = raw
        # id(int) -> native NodeID, built once from the live node list so callers
        # can address nodes by their integer id (what a dump/visualiser shows).
        self._by_int: dict[int, Any] = {}
        for nid in self._s.nodes():
            self._by_int[_nid_int(nid)] = nid

    # -- construction -------------------------------------------------------- #
    @classmethod
    def from_dump(cls, path: str) -> "GraphInterrogator":
        with open(path) as fh:
            raw = json.load(fh)
        s = Substrate()
        s.graph_from_dict(raw)          # LIVE load into the Rust runtime
        return cls(s, raw)

    @classmethod
    def from_live_boot(cls, seeds: Iterable[str] | None = None) -> "GraphInterrogator":
        """Boot a fresh agent from seeds and interrogate the live graph.

        Thin convenience over the world adapter's boot path; the interrogation
        itself is identical (read-only over `graph_to_dict` state). Kept minimal
        because the default and primary path is a saved snapshot.
        """
        from substrate.boot_core import boot_core  # local import; heavy
        s = boot_core(list(seeds) if seeds else None)
        return cls(s, s.graph_to_dict())

    # -- id / label plumbing ------------------------------------------------- #
    def _resolve(self, node_id: int | Any) -> Any:
        if not isinstance(node_id, int):
            node_id = _nid_int(node_id)
        nid = self._by_int.get(node_id)
        if nid is None:
            raise KeyError(f"no node with id {node_id}")
        return nid

    def label(self, node_id: int | Any) -> str:
        """A short human label for a node, from its most identifying attr."""
        rec = self.node(node_id)
        attrs = rec["attrs"]
        for k in _LABEL_KEYS:
            v = attrs.get(k)
            if isinstance(v, str) and v.strip():
                s = v.strip()
                return s if len(s) <= 48 else s[:45] + "..."
        return rec["type"]

    def _node_view(self, node_id: int | Any) -> dict[str, Any]:
        i = _nid_int(node_id if not isinstance(node_id, int) else node_id)
        return {"id": i, "type": self.node(i)["type"], "label": self.label(i)}

    # -- structural queries (native accessors) ------------------------------- #
    def node(self, node_id: int | Any) -> dict[str, Any]:
        nid = self._resolve(node_id)
        rec = self._s.node(nid)
        return {"id": _nid_int(rec["id"]), "type": rec["type"], "attrs": dict(rec["attrs"])}

    def nodes_of_type(self, type_name: str) -> list[dict[str, Any]]:
        return [self._node_view(nid) for nid in self._s.nodes(type_name)]

    def type_histogram(self) -> dict[str, int]:
        from collections import Counter
        c: Counter = Counter()
        for nid in self._s.nodes():
            c[self._s.node(nid)["type"]] += 1
        return dict(c.most_common())

    def edge_type_histogram(self) -> dict[str, int]:
        from collections import Counter
        c: Counter = Counter(e["type"] for e in self._raw["edges"])
        return dict(c.most_common())

    def _grouped_neighbours(self, node_id: int | Any, edge_type: str | None,
                            incoming: bool) -> dict[str, list[dict[str, Any]]]:
        nid = self._resolve(node_id)
        edge_types = ([edge_type] if edge_type else self._edge_types())
        fn = self._s.in_neighbours if incoming else self._s.neighbours
        out: dict[str, list[dict[str, Any]]] = {}
        for et in edge_types:
            got = fn(nid, et)
            if got:
                out[et] = [self._node_view(x) for x in got]
        return out

    def neighbours(self, node_id: int | Any,
                   edge_type: str | None = None) -> dict[str, list[dict[str, Any]]]:
        return self._grouped_neighbours(node_id, edge_type, incoming=False)

    def in_neighbours(self, node_id: int | Any,
                      edge_type: str | None = None) -> dict[str, list[dict[str, Any]]]:
        return self._grouped_neighbours(node_id, edge_type, incoming=True)

    def _edge_types(self) -> list[str]:
        et = getattr(self, "_etypes_cache", None)
        if et is None:
            et = sorted({e["type"] for e in self._raw["edges"]})
            self._etypes_cache = et
        return et

    def subgraph(self, seed_ids: Iterable[int], depth: int = 1,
                 directed: bool = False) -> dict[str, Any]:
        """Ego / neighbourhood graph: all nodes within `depth` hops of any seed,
        plus every edge among the kept nodes. BFS over the native accessors.
        `directed=False` (default) follows both out- and in-edges."""
        seeds = [self._resolve(s) for s in seed_ids]
        kept: set[int] = {_nid_int(s) for s in seeds}
        frontier = deque((s, 0) for s in seeds)
        while frontier:
            nid, dist = frontier.popleft()
            if dist >= depth:
                continue
            outs = list(self._s.neighbours(nid))
            if not directed:
                outs += list(self._s.in_neighbours(nid))
            for nb in outs:
                i = _nid_int(nb)
                if i not in kept:
                    kept.add(i)
                    frontier.append((self._by_int[i], dist + 1))
        nodes = [self._node_view(i) for i in sorted(kept)]
        edges = [
            {"src": e["src"], "type": e["type"], "tgt": e["tgt"]}
            for e in self._raw["edges"]
            if e["src"] in kept and e["tgt"] in kept
        ]
        return {"seed_ids": [_nid_int(s) for s in seeds], "depth": depth,
                "directed": directed, "n_nodes": len(nodes),
                "n_edges": len(edges), "nodes": nodes, "edges": edges}

    def path(self, a: int, b: int, directed: bool = False) -> dict[str, Any]:
        """A shortest path from a to b if one exists. BFS over native accessors;
        `directed=False` (default) treats edges as undirected."""
        src, dst = self._resolve(a), self._resolve(b)
        si, di = _nid_int(src), _nid_int(dst)
        if si == di:
            return {"found": True, "length": 0, "nodes": [self._node_view(si)], "edges": []}
        prev: dict[int, tuple[int, str]] = {}
        seen = {si}
        q = deque([src])
        while q:
            cur = q.popleft()
            ci = _nid_int(cur)
            steps = [(nb, et, False) for et in self._edge_types() for nb in self._s.neighbours(cur, et)]
            if not directed:
                steps += [(nb, et, True) for et in self._edge_types() for nb in self._s.in_neighbours(cur, et)]
            for nb, et, rev in steps:
                ni = _nid_int(nb)
                if ni in seen:
                    continue
                seen.add(ni)
                prev[ni] = (ci, ("<" + et if rev else et))
                if ni == di:
                    return self._reconstruct_path(si, di, prev)
                q.append(self._by_int[ni])
        return {"found": False, "length": None, "nodes": [], "edges": []}

    def _reconstruct_path(self, si: int, di: int,
                          prev: dict[int, tuple[int, str]]) -> dict[str, Any]:
        chain = [di]
        edges: list[dict[str, Any]] = []
        cur = di
        while cur != si:
            p, et = prev[cur]
            edges.append({"src": p, "type": et, "tgt": cur})
            chain.append(p)
            cur = p
        chain.reverse()
        edges.reverse()
        return {"found": True, "length": len(edges),
                "nodes": [self._node_view(i) for i in chain], "edges": edges}

    # -- the load-bearing one: DSL evaluation via the substrate's OWN engine -- #
    def graph_query(self, term: dict[str, Any] | None = None,
                    match: str | None = None,
                    env: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate a substrate DSL Term-tree against the graph, using the
        substrate's OWN evaluator (the Rust runtime — engine "live-dsl").

        Pass EITHER `term` (a DSL wire-form dict, e.g.
        {"type":"NodesOfType","node_type":"Microtheory"}, or a nested
        Filter/Neighbours/Eq/Attr tree — the exact form the rules are written
        in) OR `match` (a compact convenience string that COMPILES to such a
        term; see `compile_match`). There is no third path: both feed the same
        native evaluator.

        The evaluator's result may be a set/list of nodes, a scalar, or another
        value; the return dict tags `result_kind` accordingly, and for node-set
        results also returns the INDUCED subgraph (edges among the matched
        nodes) so callers get the relevant subgraph, not just ids.
        """
        if (term is None) == (match is None):
            raise ValueError("graph_query needs exactly one of term= or match=")
        source = "term"
        if match is not None:
            term = compile_match(match)
            source = "match->term"
        # Straight to the native evaluator — the substrate's OWN DSL engine.
        raw = self._s._inner.evaluate(term, env)  # noqa: SLF001 (documented read-only use)
        return self._shape_result(term, source, raw)

    def _shape_result(self, term: dict[str, Any], source: str, raw: Any) -> dict[str, Any]:
        base = {"engine": "live-dsl", "source": source, "term": term}
        # A set/list/tuple of NodeIDs -> node list + induced subgraph.
        _NODE_TERMS = {"NodesOfType", "Filter", "Neighbours", "InNeighbours",
                       "MapNeighbours", "FilterList"}
        if isinstance(raw, (set, frozenset, list, tuple)):
            items = list(raw)
            node_like = (items and all(self._is_nodeid(x) for x in items)) or \
                        (not items and term.get("type") in _NODE_TERMS)
            if node_like:
                ids = sorted(_nid_int(x) for x in items)
                nodes = [self._node_view(i) for i in ids]
                idset = set(ids)
                edges = [{"src": e["src"], "type": e["type"], "tgt": e["tgt"]}
                         for e in self._raw["edges"]
                         if e["src"] in idset and e["tgt"] in idset]
                base.update({"result_kind": "nodes", "n": len(ids), "nodes": nodes,
                             "induced_edges": edges})
                return base
            # a plain value collection
            base.update({"result_kind": "list", "n": len(items),
                         "value": [self._jsonable(x) for x in items]})
            return base
        if self._is_nodeid(raw):
            i = _nid_int(raw)
            base.update({"result_kind": "node", "node": self.node(i)})
            return base
        base.update({"result_kind": "scalar", "value": self._jsonable(raw)})
        return base

    @staticmethod
    def _is_nodeid(x: Any) -> bool:
        return hasattr(x, "value") and type(x).__name__ == "NodeID"

    def _jsonable(self, x: Any) -> Any:
        if self._is_nodeid(x):
            return {"id": _nid_int(x), "type": self.node(_nid_int(x))["type"],
                    "label": self.label(_nid_int(x))}
        if isinstance(x, (set, frozenset, tuple)):
            return [self._jsonable(v) for v in x]
        if isinstance(x, dict):
            return {k: self._jsonable(v) for k, v in x.items()}
        return x


# --------------------------------------------------------------------------- #
# The `--match` mini-syntax -> DSL Term-tree compiler.
#
# This is PURE SUGAR: it emits a standard DSL wire-form dict (NodesOfType +
# Filter + Eq/Lt/Gt/… over Attr) that the NATIVE evaluator runs. It is not a
# separate query engine; every `--match` still executes as a live DSL term.
#
# Grammar (one node type, optional conjunctive attr predicates):
#     TYPE [where PRED [and PRED ...]]
#     PRED := ATTR OP VALUE
#     OP   := ==  !=  <  <=  >  >=  ~   (~ = substring contains, via StringIndexOf)
# Values: bare word/number, or a "quoted string". Numbers become numeric Lits.
# --------------------------------------------------------------------------- #
_OP_TERM = {"==": "Eq", "<": "Lt", "<=": "Lte", ">": "Gt", ">=": "Gte"}
_PRED_RE = re.compile(r"^\s*([A-Za-z0-9_.]+)\s*(==|!=|<=|>=|<|>|~)\s*(.+?)\s*$")


def _lit(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        return {"type": "Lit", "value": raw[1:-1]}
    for cast in (int, float):
        try:
            return {"type": "Lit", "value": cast(raw)}
        except ValueError:
            pass
    return {"type": "Lit", "value": raw}


def _pred_term(attr: str, op: str, val: str, var: str) -> dict[str, Any]:
    a = {"type": "Attr", "node": {"type": "Var", "name": var}, "key": attr}
    lit = _lit(val)
    if op in _OP_TERM:
        return {"type": _OP_TERM[op], "a": a, "b": lit}
    if op == "!=":
        return {"type": "Not", "arg": {"type": "Eq", "a": a, "b": lit}}
    if op == "~":   # substring contains: StringIndexOf(attr, needle) >= 0
        idx = {"type": "StringIndexOf", "haystack": a, "needle": lit}
        return {"type": "Gte", "a": idx, "b": {"type": "Lit", "value": 0}}
    raise ValueError(f"unknown operator {op!r}")


def compile_match(expr: str) -> dict[str, Any]:
    """Compile the `--match` mini-syntax to a DSL Term-tree (wire dict)."""
    if " where " in f" {expr} ".lower():
        # split on the first case-insensitive ' where '
        m = re.split(r"\s+where\s+", expr, maxsplit=1, flags=re.IGNORECASE)
        type_name, rest = m[0].strip(), m[1]
    else:
        type_name, rest = expr.strip(), ""
    source = {"type": "NodesOfType", "node_type": type_name}
    if not rest.strip():
        return source
    var = "n"
    preds = []
    for clause in re.split(r"\s+and\s+", rest, flags=re.IGNORECASE):
        mm = _PRED_RE.match(clause)
        if not mm:
            raise ValueError(f"cannot parse predicate: {clause!r}")
        preds.append(_pred_term(mm.group(1), mm.group(2), mm.group(3), var))
    pred = preds[0] if len(preds) == 1 else {"type": "And", "items": preds}
    return {"type": "Filter", "source": source, "var_name": var, "predicate": pred}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _emit(obj: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
        return
    print(_summarise(obj))


def _summarise(obj: Any) -> str:
    if isinstance(obj, dict) and "engine" in obj:  # graph_query result
        head = f"[{obj['engine']}] {obj.get('result_kind')} (source={obj.get('source')})"
        if obj.get("result_kind") == "nodes":
            lines = [head, f"  {obj['n']} nodes, {len(obj['induced_edges'])} induced edges"]
            for nd in obj["nodes"][:40]:
                lines.append(f"    #{nd['id']:<6} {nd['type']:<18} {nd['label']}")
            if obj["n"] > 40:
                lines.append(f"    ... (+{obj['n'] - 40} more)")
            return "\n".join(lines)
        if obj.get("result_kind") in ("scalar", "list", "node"):
            return head + "\n  value: " + json.dumps(obj.get("value", obj.get("node")), default=str)[:400]
        return head
    if isinstance(obj, dict) and "attrs" in obj and "type" in obj:  # node()
        lines = [f"#{obj['id']}  {obj['type']}"]
        for k, v in obj["attrs"].items():
            lines.append(f"    {k}: {json.dumps(v, default=str)[:200]}")
        return "\n".join(lines)
    if isinstance(obj, list):  # nodes_of_type
        lines = [f"{len(obj)} nodes"]
        for nd in obj[:60]:
            lines.append(f"    #{nd['id']:<6} {nd['type']:<18} {nd['label']}")
        if len(obj) > 60:
            lines.append(f"    ... (+{len(obj) - 60} more)")
        return "\n".join(lines)
    if isinstance(obj, dict) and ("n_nodes" in obj or "found" in obj):  # subgraph/path
        if "found" in obj:  # path
            if not obj["found"]:
                return "no path found"
            lines = [f"path length {obj['length']}"]
            for i, nd in enumerate(obj["nodes"]):
                et = f"  --[{obj['edges'][i-1]['type']}]-->" if i else ""
                lines.append(f"    {et} #{nd['id']} {nd['type']} {nd['label']}")
            return "\n".join(lines)
        lines = [f"subgraph: {obj['n_nodes']} nodes, {obj['n_edges']} edges "
                 f"(seeds={obj['seed_ids']}, depth={obj['depth']})"]
        for nd in obj["nodes"][:50]:
            lines.append(f"    #{nd['id']:<6} {nd['type']:<18} {nd['label']}")
        if obj["n_nodes"] > 50:
            lines.append(f"    ... (+{obj['n_nodes'] - 50} more)")
        return "\n".join(lines)
    if isinstance(obj, dict):  # histogram
        return "\n".join(f"    {k}: {v}" for k, v in obj.items())
    return str(obj)


def build_parser() -> argparse.ArgumentParser:
    # Shared options usable in EITHER position (before or after the subcommand).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dump", default=DEFAULT_DUMP,
                        help=f"graph_to_dict snapshot to load (default: {DEFAULT_DUMP})")
    common.add_argument("--json", action="store_true", help="emit machine JSON")

    p = argparse.ArgumentParser(
        prog="graph_interrogate", parents=[common],
        description="READ-ONLY interrogation of the Jabberwock (G,Γ) substrate.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def _sp(name, **kw):
        return sub.add_parser(name, parents=[common], **kw)

    sp = _sp("node", help="type + attrs of a node id")
    sp.add_argument("id", type=int)

    sp = _sp("nodes-of-type", help="ids/labels of all nodes of a type")
    sp.add_argument("type")

    sp = _sp("neighbours", help="out-neighbours grouped by edge type")
    sp.add_argument("id", type=int)
    sp.add_argument("--edge", default=None)

    sp = _sp("in-neighbours", help="in-neighbours grouped by edge type")
    sp.add_argument("id", type=int)
    sp.add_argument("--edge", default=None)

    sp = _sp("subgraph", help="ego/neighbourhood subgraph")
    sp.add_argument("ids", type=int, nargs="+")
    sp.add_argument("--depth", type=int, default=1)
    sp.add_argument("--directed", action="store_true")

    sp = _sp("path", help="a shortest path a -> b if one exists")
    sp.add_argument("a", type=int)
    sp.add_argument("b", type=int)
    sp.add_argument("--directed", action="store_true")

    sp = _sp("query", help="evaluate a DSL Term-tree (live substrate engine)")
    sp.add_argument("--term", default=None, help="DSL wire-form JSON (string or @file)")
    sp.add_argument("--match", default=None,
                    help="mini-syntax: 'TYPE where attr OP value [and ...]' (compiles to a DSL term)")

    _sp("types", help="node-type histogram")
    _sp("edge-types", help="edge-type histogram")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    gi = GraphInterrogator.from_dump(args.dump)
    if args.cmd == "node":
        _emit(gi.node(args.id), args.json)
    elif args.cmd == "nodes-of-type":
        _emit(gi.nodes_of_type(args.type), args.json)
    elif args.cmd == "neighbours":
        _emit(gi.neighbours(args.id, args.edge), args.json)
    elif args.cmd == "in-neighbours":
        _emit(gi.in_neighbours(args.id, args.edge), args.json)
    elif args.cmd == "subgraph":
        _emit(gi.subgraph(args.ids, args.depth, args.directed), args.json)
    elif args.cmd == "path":
        _emit(gi.path(args.a, args.b, args.directed), args.json)
    elif args.cmd == "query":
        term = None
        if args.term:
            spec = args.term
            if spec.startswith("@"):
                with open(spec[1:]) as fh:
                    spec = fh.read()
            term = json.loads(spec)
        _emit(gi.graph_query(term=term, match=args.match), args.json)
    elif args.cmd == "types":
        _emit(gi.type_histogram(), args.json)
    elif args.cmd == "edge-types":
        _emit(gi.edge_type_histogram(), args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
