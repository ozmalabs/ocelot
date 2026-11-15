"""Ocelot adapter for ozagia: seed manifests, the IR edit engine and the
`dev_graph_query` tool.

Loaded by ozagia through `.ozagia.toml` (`[adapters] modules =
["tools.ozagia_ocelot_adapter:register"]`). It imports only `ozagia` and the
standard library. `scripts.graph_interrogate` and `scripts.ocelot_ir_edit`
(which need the Ocelot substrate) are imported lazily, from this checkout,
when `dev_graph_query` is called or an IR edit is applied.

The IR edit engine handles Python edit scripts with `engine: "ir"` or one of
its ops (`replace_expression_ir`, `replace_body_ir`, `replace_function_ir`,
`fallback_check`).

The indexer adds, from `seeds/*.json`:

    Repo -has_seed-> Seed
    File -defines-> Seed            Seed -defined_in-> File
    Seed -depends_on-> Seed         (a stub Seed for a missing dependency)
    Seed -contains-> Rule | Concept | Production | Microtheory | Reflex |
                     GoalSpec | <seed node type>
    item -in_seed-> Seed            item -defined_in-> File
    File -mentions_seed-> Seed      (source and test files naming seeds/x.json)
    Test -mentions_seed-> Seed
    Doc -documents-> Seed

and the Repo attribute `seeds` (the Seed node count).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

OCELOT_ROOT = Path(__file__).resolve().parents[1]
_SEED_PATH_RE = re.compile(r"seeds/([A-Za-z0-9_.-]+)\.json")


IR_OPS = ("replace_expression_ir", "replace_body_ir", "replace_function_ir",
          "fallback_check")


def register(registry: Any) -> None:
    # index_seeds reads seeds/*.json itself and depends on other files only
    # through their `seeds/<id>.json` mentions.
    try:
        registry.add_indexer(index_seeds, watch=("seeds/*.json",),
                             texts=_SEED_PATH_RE)
    except TypeError:  # an ozagia without indexer inputs
        registry.add_indexer(index_seeds)
    registry.add_mcp_tool(GRAPH_QUERY_TOOL, graph_query)
    registry.add_edit_engine("ir", IR_OPS, apply_ir_edit)


def _ocelot_on_path() -> None:
    if str(OCELOT_ROOT) not in sys.path:
        sys.path.insert(0, str(OCELOT_ROOT))


def apply_ir_edit(root: Any, script: dict[str, Any], *, write: bool = False) -> Any:
    """The `ir` edit engine: Ocelot's `scripts.ocelot_ir_edit`."""
    _ocelot_on_path()
    from scripts.ocelot_ir_edit import apply_ir_edit_script
    return apply_ir_edit_script(root, script, write=write)


# --------------------------------------------------------------------------- #
# seed indexer
# --------------------------------------------------------------------------- #
def _seed_items(d: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the several seed container shapes into SeedItem records."""
    items: list[dict[str, Any]] = []

    for i, node in enumerate(d.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        attrs = node.get("attrs") or {}
        typ = str(node.get("type") or "SeedItem")
        name = str(attrs.get("name") or attrs.get("id") or
                   f"{typ}#{node.get('local_id', i)}")
        items.append({"type": typ, "name": name, "attrs": dict(attrs),
                      "local_id": node.get("local_id", i), "container": "nodes"})

    for i, rule in enumerate(d.get("rules") or []):
        if isinstance(rule, dict):
            name = str(rule.get("name") or f"rule#{i}")
            items.append({"type": "Rule", "name": name, "attrs": {},
                          "local_id": i, "container": "rules",
                          "where_type": (rule.get("where") or {}).get("type", "")})
        elif isinstance(rule, str):
            items.append({"type": "Rule", "name": rule, "attrs": {},
                          "local_id": i, "container": "rules"})

    for i, concept in enumerate(d.get("concepts") or []):
        if isinstance(concept, dict):
            name = str(concept.get("name") or concept.get("id") or f"concept#{i}")
            attrs = {k: v for k, v in concept.items()
                     if isinstance(v, (str, int, float, bool))}
        else:
            name = str(concept)
            attrs = {}
        items.append({"type": "Concept", "name": name, "attrs": attrs,
                      "local_id": i, "container": "concepts"})

    for i, prod in enumerate(d.get("productions") or []):
        name = f"production#{i}"
        attrs: dict[str, Any] = {}
        if isinstance(prod, dict):
            name = str(prod.get("provenance") or prod.get("name") or name)
            attrs = {"src": str(prod.get("src", ""))[:200],
                     "edge_type": str(prod.get("edge_type", "")),
                     "tgt": str(prod.get("tgt", ""))[:200]}
        elif isinstance(prod, (list, tuple)):
            attrs = {"src": str(prod[0])[:200] if len(prod) > 0 else "",
                     "edge_type": str(prod[1]) if len(prod) > 1 else "",
                     "tgt": str(prod[2])[:200] if len(prod) > 2 else ""}
        items.append({"type": "Production", "name": name, "attrs": attrs,
                      "local_id": i, "container": "productions"})

    mt = d.get("microtheory")
    if isinstance(mt, dict):
        items.append({"type": "Microtheory",
                      "name": str(mt.get("name") or "microtheory"),
                      "attrs": {"description": str(mt.get("description", ""))[:1000]},
                      "local_id": 0, "container": "microtheory"})

    for i, reflex in enumerate(d.get("reflexes") or []):
        name = (str(reflex.get("name") or f"reflex#{i}")
                if isinstance(reflex, dict) else str(reflex))
        items.append({"type": "Reflex", "name": name, "attrs": {},
                      "local_id": i, "container": "reflexes"})

    for i, goal in enumerate(d.get("goals") or []):
        name = (str(goal.get("name") or f"goal#{i}")
                if isinstance(goal, dict) else str(goal))
        items.append({"type": "GoalSpec", "name": name, "attrs": {},
                      "local_id": i, "container": "goals"})

    return items


def _seed_attrs(seed_id: str, rel: str, d: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": seed_id,
        "id": seed_id,
        "version": str(d.get("version", "")),
        "path": rel,
        "description": str(d.get("description", ""))[:1000],
        "depends_on": list(d.get("depends_on") or []),
    }


def index_seeds(ctx: Any) -> None:
    """The `ozagia.adapters` indexer hook (see the module docstring)."""
    b = ctx.builder
    root = Path(ctx.root).resolve()

    seed_dir = root / "seeds"
    seed_paths = sorted(seed_dir.glob("*.json")) if seed_dir.exists() else []
    for p in seed_paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        rel = p.resolve().relative_to(root).as_posix()
        seed_id = str(d.get("id") or p.stem)
        fid = ctx.file_node(rel)
        sid = b.node("Seed", _seed_attrs(seed_id, rel, d), key=("seed", seed_id))
        # A dependency may have created a stub before the real manifest was
        # visited. Upgrade it in place; never leave a stub when the real seed
        # is present.
        seed_attrs = b.attrs(sid)
        if seed_attrs.get("stub"):
            seed_attrs.update(_seed_attrs(seed_id, rel, d))
            seed_attrs.pop("stub", None)
        b.edge(fid, "defines", sid)
        b.edge(sid, "defined_in", fid)
        b.edge(ctx.repo, "has_seed", sid)
        for dep in d.get("depends_on") or []:
            dep = str(dep)
            dep_nid = b.find(("seed", dep))
            if dep_nid is None:
                dep_nid = b.node("Seed", {
                    "name": dep, "id": dep, "version": "", "path": "",
                    "description": "", "depends_on": [], "stub": 1,
                }, key=("seed", dep))
            b.edge(sid, "depends_on", dep_nid)
        for item in _seed_items(d):
            inode = b.node(item["type"], {
                "name": item["name"],
                "seed": seed_id,
                "container": item["container"],
                "local_id": item["local_id"],
                **item["attrs"],
            }, key=("seed_item", seed_id, item["type"], item["name"]))
            b.edge(sid, "contains", inode)
            b.edge(inode, "in_seed", sid)
            b.edge(inode, "defined_in", fid)

    def seed_node(seed_id: str) -> int | None:
        return b.find(("seed", seed_id))

    # Source and test files that name a seed manifest, and their tests.
    for src in ctx.sources:
        for seed_id in set(_SEED_PATH_RE.findall(src.text)):
            b.edge(src.node, "mentions_seed", seed_node(seed_id))
    for tf in ctx.tests:
        for seed_id in set(_SEED_PATH_RE.findall(tf.text)):
            target = seed_node(seed_id)
            b.edge(tf.node, "mentions_seed", target)
            for tid in tf.tests:
                b.edge(tid, "mentions_seed", target)
    for doc in ctx.docs:
        for seed_id in set(_SEED_PATH_RE.findall(doc.text)):
            b.edge(doc.node, "documents", seed_node(seed_id))

    b.attrs(ctx.repo)["seeds"] = b.count("Seed")


# --------------------------------------------------------------------------- #
# dev_graph_query
# --------------------------------------------------------------------------- #
GRAPH_QUERY_TOOL = {
    "name": "dev_graph_query",
    "description": (
        "Evaluate a substrate DSL Term-tree against the snapshot on the "
        "substrate's own evaluator (read-only). Pass either `term` (wire "
        "dict) or `match` ('TYPE where attr OP value [and ...]')."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "term": {"type": "object"},
            "match": {"type": "string"},
        },
        "required": [],
        "additionalProperties": False,
    },
}


def graph_query(memory: Any, args: dict[str, Any]) -> Any:
    """`dev_graph_query`: GraphInterrogator over the memory's snapshot."""
    if bool(args.get("term")) == bool(args.get("match")):
        return {"ok": False, "error": "pass exactly one of term= or match="}
    gi = getattr(memory, "_ocelot_graph_interrogator", None)
    if gi is None:
        _ocelot_on_path()
        from scripts.graph_interrogate import GraphInterrogator
        gi = GraphInterrogator.from_dump(str(memory.dump))
        memory._ocelot_graph_interrogator = gi
    return gi.graph_query(term=args.get("term"), match=args.get("match"))
