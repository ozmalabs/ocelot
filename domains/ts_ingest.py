"""ts_ingest — the MECHANICAL tree-sitter WORLD ADAPTER (P2, Rust+Lua track).

The `ast_to_term.ingest_ast` twin for tree-sitter languages: parse source
(rust / lua) and dump the CONCRETE SYNTAX TREE into the substrate as typed
`CstNode` graph nodes with `child` edges. A pure CST-to-graph translation —
no decisions, no graph-state conditionals (CLAUDE.md world-adapter layer;
PROGRAM_SYNTHESIS_PLAN.md §5: "tree-sitter invocation = mechanical
translation of an opaque external form into graph nodes — the ChatWorld
tokenizer, at code scale").

Each CST node becomes one `CstNode` with attrs:

  kind         the tree-sitter node type ("binary_expression", "+" …)
  field        the field role under its parent ("left", "operator", "") —
               the tree-sitter analogue of ast_to_term's child_field
  child_index  position among the parent's children (ALL children, so
               anonymous operator tokens keep their place)
  named        tree-sitter's named flag (True for grammar rules, False
               for anonymous tokens like "(" / "+" / "..")
  text         the source text, for LEAVES only (child_count == 0) —
               operator tokens, identifiers, literals
  origin       "world_adapter_ts"

plus a `child` edge parent → child per CST edge.

This module also carries the SHARED CORRESPONDENCE-TABLE ENGINE
(`TableWalker`, `load_correspondence_rows`): the mechanical applier the
per-language walkers (domains/prog_ir_rust.py, domains/prog_ir_lua.py) use
to fold a CstNode graph into hub Program IR. The TABLE (which cst_kind
means which Prog*/DSL Term) is SEED DATA — `seeds/rust_correspondence.json`
/ `seeds/lua_correspondence.json`, rows of CorrespondenceRow nodes in the
spirit of ast_term_rules.CORRESPONDENCE — so the agent can inspect / vary /
repair the correspondence as graph data. The engine has NO per-construct
if/elif: dispatch is a (cst_kind, operator-guard) lookup in the rows; a row
either names a Term + a uniform field plan, or names a HANDLER the
language module registers (the composer_dispatch name-keyed-registry
precedent — structural desugars are mechanical shape transformers, the
AstTermEmitter precedent). An unmapped construct is an HONEST RESIDUAL:
the walk records the blocking cst kinds and the read returns
{ok: False, blockers: [...]} — never a silent partial emit.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_DIR = os.path.join(_ROOT, "seeds")

# language name -> tree-sitter grammar module. One entry per language;
# adding a language = one row here + one correspondence seed.
_GRAMMARS = {
    "rust": "tree_sitter_rust",
    "lua": "tree_sitter_lua",
}


def _language(language: str):
    """The tree_sitter.Language for `language` — mechanical module lookup."""
    import importlib

    from tree_sitter import Language

    mod_name = _GRAMMARS.get(language)
    if mod_name is None:
        raise ValueError(
            f"no tree-sitter grammar registered for {language!r} "
            f"(have: {sorted(_GRAMMARS)})")
    mod = importlib.import_module(mod_name)
    return Language(mod.language())


def open_cst_productions(substrate) -> int:
    """Open the Γ production admitting CstNode -child-> CstNode (the
    code-as-graph vocabulary — the `open_ast_productions` twin).
    Idempotent; part of the world-adapter boot, not an agent decision."""
    try:
        substrate.add_production({
            "src": {"type": "CstNode", "var": "a"},
            "edge_type": "child",
            "tgt": {"type": "CstNode", "var": "b"},
            "where": None,
            "provenance": "ts_ingest:code_as_graph",
        })
        return 1
    except Exception:  # noqa: BLE001 — already open / grammar-less substrate
        return 0


def ingest_source(substrate, source: str, language: str, *,
                  root_label: str = "") -> Dict[str, Any]:
    """WORLD ADAPTER: parse `source` with the `language` grammar and ingest
    the full CST as typed CstNode graph nodes under `child` edges. Returns
    {"root": NodeID, "n_nodes": int, "language": str}. Pure mechanical
    translation — every CST node (named and anonymous) is dumped verbatim;
    nothing is interpreted here."""
    from tree_sitter import Parser

    parser = Parser(_language(language))
    tree = parser.parse(source.encode("utf-8"))
    inner = getattr(substrate, "_inner", substrate)
    n_nodes = 0

    def _ingest(node, field: str, child_index: int):
        nonlocal n_nodes
        attrs: Dict[str, Any] = {
            "kind": node.type,
            "field": field or "",
            "child_index": child_index,
            "named": bool(node.is_named),
            "origin": "world_adapter_ts",
            "language": language,
        }
        if root_label:
            attrs["module"] = root_label
        if node.child_count == 0:
            attrs["text"] = node.text.decode("utf-8", errors="replace")
        nid = substrate.add_node("CstNode", attrs)
        n_nodes += 1
        for i, child in enumerate(node.children):
            cid = _ingest(child, node.field_name_for_child(i), i)
            inner.add_edge_unchecked(nid, "child", cid)
        return nid

    root = _ingest(tree.root_node, "", -1)
    return {"root": root, "n_nodes": n_nodes, "language": language}


# ---------------------------------------------------------------------------
# Correspondence rows — SEED DATA the walkers apply.
# ---------------------------------------------------------------------------
def correspondence_seed_path(language: str) -> str:
    return os.path.join(_SEED_DIR, f"{language}_correspondence.json")


def load_correspondence_manifest(language: str) -> Dict[str, Any]:
    """The raw seed manifest (mechanical file I/O)."""
    with open(correspondence_seed_path(language)) as f:
        return json.load(f)


def load_correspondence_rows(language: str) -> List[Dict[str, Any]]:
    """The correspondence TABLE: the seed's CorrespondenceRow node attrs,
    with each row's `plan` JSON-string decoded. The seed file is the single
    source of truth — the same rows `load_seed_manifest` installs as graph
    nodes for the agent to inspect."""
    manifest = load_correspondence_manifest(language)
    rows: List[Dict[str, Any]] = []
    for node in manifest.get("nodes", []):
        if node.get("type") != "CorrespondenceRow":
            continue
        attrs = dict(node.get("attrs", {}))
        plan = attrs.get("plan")
        attrs["plan"] = json.loads(plan) if plan else {}
        rows.append(attrs)
    return rows


def install_correspondence_seed(substrate, language: str, agent_root=None) -> Dict[str, Any]:
    """Install the correspondence seed into a live substrate via the Rust
    seed loader (graph-resident, inspectable) + record the Seed node.
    Idempotent by Seed{id}. Mechanical seed I/O — the register_source
    `ensure_register_codebook` idiom."""
    manifest = load_correspondence_manifest(language)
    seed_id = manifest.get("id", f"{language}_correspondence")
    for n in substrate.nodes("Seed"):
        if substrate.node(n)["attrs"].get("id") == seed_id:
            return {"installed": False, "reason": "already present", "id": seed_id}
    inner = getattr(substrate, "_inner", substrate)
    summary = inner.load_seed_manifest(manifest, agent_root)
    substrate.add_node("Seed", {"id": seed_id,
                                "version": manifest.get("version", "1.0.0")})
    return {"installed": True, "id": seed_id, "summary": summary}


# ---------------------------------------------------------------------------
# The shared table-application engine.
# ---------------------------------------------------------------------------
def _lit(v) -> Dict[str, Any]:
    return {"type": "Lit", "value": v}


class TableWalker:
    """Applies a correspondence table over an ingested CstNode graph,
    emitting hub Program-IR Term-JSON (the P1 emission dialect: optional
    children explicit null, optional identifier sentinels explicit "").

    Dispatch is ONLY by table lookup: (cst_kind, optional operator-text
    guard) -> row; the row names a Term + field plan (applied uniformly)
    or a registered handler. Unmapped kinds are recorded as blockers and
    the caller reports {ok: False} — the honest residual, never a silent
    partial emit."""

    def __init__(self, substrate, rows: List[Dict[str, Any]],
                 handlers: Dict[str, Callable]):
        self.s = substrate
        self.handlers = dict(handlers)
        self._by_kind: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            self._by_kind.setdefault(r.get("cst_kind", ""), []).append(r)
        self.blockers: List[str] = []

    # ---- CstNode graph accessors (mechanical reads) ----
    def attrs(self, nid) -> Dict[str, Any]:
        return self.s.node(nid)["attrs"]

    def kind(self, nid) -> str:
        return self.attrs(nid).get("kind", "")

    def text(self, nid) -> str:
        return self.attrs(nid).get("text", "")

    def children(self, nid) -> List[Any]:
        out = [(self.attrs(c).get("child_index", -1), c)
               for c in self.s.neighbours(nid, "child")]
        out.sort(key=lambda t: t[0])
        return [c for _, c in out]

    def named_children(self, nid) -> List[Any]:
        return [c for c in self.children(nid) if self.attrs(c).get("named")]

    def field_child(self, nid, field: str) -> Optional[Any]:
        for c in self.children(nid):
            if self.attrs(c).get("field") == field:
                return c
        return None

    def field_children(self, nid, field: str) -> List[Any]:
        return [c for c in self.children(nid)
                if self.attrs(c).get("field") == field]

    def flat_text(self, nid) -> str:
        """The node's source text rebuilt from its leaf descendants in
        order (leaves carry `text`; interior nodes don't)."""
        a = self.attrs(nid)
        if "text" in a:
            return a["text"]
        return "".join(self.flat_text(c) for c in self.children(nid))

    def leaf_texts(self, nid) -> List[str]:
        a = self.attrs(nid)
        if "text" in a:
            return [a["text"]]
        out: List[str] = []
        for c in self.children(nid):
            out.extend(self.leaf_texts(c))
        return out

    def has_descendant_kind(self, nid, kind: str) -> bool:
        if self.kind(nid) == kind:
            return True
        return any(self.has_descendant_kind(c, kind) for c in self.children(nid))

    # ---- residuals ----
    def block(self, reason: str) -> Dict[str, Any]:
        """Record an honest blocker; the placeholder keeps the walk total
        but the caller NEVER returns IR when blockers exist."""
        self.blockers.append(reason)
        return _lit(None)

    # ---- dispatch ----
    def _row_for(self, nid) -> Optional[Dict[str, Any]]:
        rows = self._by_kind.get(self.kind(nid))
        if not rows:
            return None
        op_child = self.field_child(nid, "operator")
        op_text = self.text(op_child) if op_child is not None else ""
        fallback = None
        for r in rows:
            guard = r.get("op", "")
            if guard == "":
                fallback = fallback or r
            elif guard == op_text:
                return r
        return fallback

    def emit(self, nid) -> Dict[str, Any]:
        row = self._row_for(nid)
        if row is None:
            return self.block(self.kind(nid))
        if row.get("emit") == "handler":
            handler = self.handlers.get(row.get("handler", ""))
            if handler is None:
                return self.block(f"handler:{row.get('handler')}")
            return handler(self, nid, row)
        return self._apply_plan(row, nid)

    def emit_field(self, nid, field: str) -> Dict[str, Any]:
        c = self.field_child(nid, field)
        if c is None:
            return self.block(f"{self.kind(nid)}:missing_field:{field}")
        return self.emit(c)

    # ---- the uniform plan applier (no per-construct branching; the plan
    # vocabulary is fixed and every row goes through the same fold) ----
    def _apply_plan(self, row: Dict[str, Any], nid) -> Dict[str, Any]:
        plan = row.get("plan") or {}
        term_t = row.get("term", "")
        arity = plan.get("arity")
        if arity == "leaf":
            out = self._leaf_value(plan, nid)
        elif arity == "items":
            out = {"type": term_t,
                   "items": [self.emit_field(nid, f) for f in plan.get("fields", [])]}
        elif arity == "fields":
            out = {"type": term_t}
            for cst_field, term_field in plan.get("map", []):
                out[term_field] = self.emit_field(nid, cst_field)
        else:
            return self.block(f"{self.kind(nid)}:bad_plan")
        for k, v in (plan.get("extra") or {}).items():
            out[k] = v
        if plan.get("wrap") == "not":
            out = {"type": "Not", "arg": out}
        return out

    def _leaf_value(self, plan: Dict[str, Any], nid) -> Dict[str, Any]:
        reader = plan.get("value", "const")
        if reader == "const":
            return _lit(plan.get("const"))
        if reader == "name":
            return {"type": "Var", "name": self.text(nid)}
        if reader == "int_text":
            return _lit(int(self.text(nid)))
        if reader == "num_text":
            t = self.text(nid)
            if any(ch in t for ch in ".eE") and not t.startswith("0x"):
                return _lit(float(t))
            return _lit(int(t, 0))
        if reader == "bool_text":
            # P5-B §6.1 finding, owner-fixed (P6-B): rust's `boolean_literal`
            # carries its text on a token CHILD (the node itself is not a
            # leaf, so `text` is absent); read the node's flat leaf text so
            # `true` re-reads as Lit true. `flat_text` is the identity on a
            # genuine leaf, so a leaf-borne bool (lua-style) is unchanged.
            return _lit(self.flat_text(nid) == "true")
        if reader == "string":
            # the string literal's content leaf (rust string_literal /
            # lua string both wrap a string_content child); an empty
            # string has no content leaf.
            for c in self.children(nid):
                if self.kind(c) == "string_content":
                    return _lit(self.text(c))
            return _lit("")
        return self.block(f"leaf_reader:{reader}")


def find_kind(substrate, root, kind: str) -> List[Any]:
    """All CstNodes of `kind` under `root`, document order — mechanical."""
    inner_walker = TableWalker(substrate, [], {})
    out: List[Any] = []

    def _walk(nid):
        if inner_walker.kind(nid) == kind:
            out.append(nid)
        for c in inner_walker.children(nid):
            _walk(c)

    _walk(root)
    return out


__all__ = ["ingest_source", "open_cst_productions", "TableWalker",
           "load_correspondence_rows", "load_correspondence_manifest",
           "install_correspondence_seed", "correspondence_seed_path",
           "find_kind"]
