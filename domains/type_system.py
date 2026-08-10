"""The agent's TYPE model — graph-resident understanding of what types ARE
and what they are on the Rust side of the substrate.

This is the enabler for the typed tool-use boundary (``domains.tool_use``).
Before the agent can KNOWINGLY call an external process or library as a
typed, composable operation, it has to understand the TYPES that cross the
boundary — both their Python-world form and their Rust-native form (the
``TermNode`` / engine value they correspond to).

Faithful to the architecture rule (``CLAUDE.md``):

  * The TYPE MODEL is GRAPH DATA — one ``Type`` node per base type, each
    carrying ``rust_type`` (the Rust-side form) and ``kind``. The agent
    reasons over these nodes natively, the same way it reasons over any
    Concept.
  * The helpers here (``type_of_value``, ``rust_type_for``, ``typecheck``)
    are MECHANICAL classifiers / lookups — a world-adapter boundary
    converting an opaque Python value into the smallest type token. They
    make NO agent decisions; they just translate.

The base types and their Rust-side forms:

  Int    ↔ i64
  Float  ↔ f64
  Bool   ↔ bool
  Str    ↔ String
  Bytes  ↔ Vec<u8>
  Node   ↔ NodeId
  Unit   ↔ ()
  List   ↔ Vec<T>      (parametric — element type recorded as an edge/attr)

These are exactly the value forms the Rust DSL evaluator already produces
and consumes, so a value classified here lines up with what a native
``UseTool`` TermNode (the named follow-on) would carry across the boundary.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# the base type table — type name -> (rust_type, kind)
# ---------------------------------------------------------------------------
# ``kind`` partitions the model: "scalar" (a single value), "ref" (a graph
# reference), "unit" (no value), "parametric" (carries an element type).
BASE_TYPES: dict[str, tuple[str, str]] = {
    "Int":   ("i64",     "scalar"),
    "Float": ("f64",     "scalar"),
    "Bool":  ("bool",    "scalar"),
    "Str":   ("String",  "scalar"),
    "Bytes": ("Vec<u8>", "scalar"),
    "Node":  ("NodeId",  "ref"),
    "Unit":  ("()",      "unit"),
    "List":  ("Vec<T>",  "parametric"),
}

TYPE_NODE_TYPE = "Type"


# ---------------------------------------------------------------------------
# install — the type model as graph data
# ---------------------------------------------------------------------------

def install_type_system(substrate) -> dict[str, Any]:
    """Install one ``Type`` node per base type into ``substrate``.

    Each node is ``Type{name, rust_type, kind}``. Idempotent: a second
    call reuses the existing nodes rather than minting duplicates (matched
    by the ``name`` attr). Returns ``{type_name: node_id}``.

    The ``List`` parametric type records its element type as an attr
    (``element``) when a concrete instance is registered via
    :func:`register_list_type`; the base ``List`` node carries the generic
    ``Vec<T>`` form.
    """
    # An attr index on (Type, name) makes the lookup O(1) and lets a second
    # install find existing nodes instead of duplicating them.
    try:
        substrate.declare_attr_index(TYPE_NODE_TYPE, "name")
    except Exception:
        pass

    ids: dict[str, Any] = {}
    for name, (rust_type, kind) in BASE_TYPES.items():
        existing = _find_type_node(substrate, name)
        if existing is not None:
            ids[name] = existing
            continue
        nid = substrate.add_node(TYPE_NODE_TYPE, {
            "name": name,
            "rust_type": rust_type,
            "kind": kind,
        })
        ids[name] = nid
    return ids


def register_list_type(substrate, element_type: str) -> Any:
    """Register a concrete ``List<element_type>`` Type node and link it to
    its element Type via an ``element_type`` edge — the parametric record.

    Returns the node id. Idempotent on ``name``.
    """
    name = f"List<{element_type}>"
    existing = _find_type_node(substrate, name)
    if existing is not None:
        return existing
    elem_rust = rust_type_for(element_type)
    nid = substrate.add_node(TYPE_NODE_TYPE, {
        "name": name,
        "rust_type": f"Vec<{elem_rust}>",
        "kind": "parametric",
        "element": element_type,
    })
    elem_node = _find_type_node(substrate, element_type)
    if elem_node is not None:
        try:
            substrate.add_edge_unchecked(nid, "element_type", elem_node)
        except Exception:
            pass
    return nid


def _find_type_node(substrate, name: str):
    """Locate a Type node by name. Tries the O(1) index, falls back to a
    scan so the helper works even if the index wasn't declared."""
    try:
        hits = substrate.nodes_where(TYPE_NODE_TYPE, "name", name)
        if hits:
            return hits[0]
    except Exception:
        pass
    try:
        for nid in substrate.nodes(TYPE_NODE_TYPE):
            if substrate.node(nid)["attrs"].get("name") == name:
                return nid
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# mechanical helpers — classify / look up / check. No decisions.
# ---------------------------------------------------------------------------

def type_of_value(v: Any) -> str:
    """Classify a Python value to a base type name (mechanical).

    ``bool`` is checked before ``int`` because ``bool`` is a subclass of
    ``int`` in Python and we want ``True``/``False`` typed as ``Bool``.
    A homogeneous ``list``/``tuple`` is typed as ``List<elem>`` when the
    element type is uniform, else the bare ``List``.
    """
    if isinstance(v, bool):
        return "Bool"
    if isinstance(v, int):
        return "Int"
    if isinstance(v, float):
        return "Float"
    if isinstance(v, str):
        return "Str"
    if isinstance(v, (bytes, bytearray)):
        return "Bytes"
    if v is None:
        return "Unit"
    if isinstance(v, (list, tuple)):
        elem_types = {type_of_value(x) for x in v}
        if len(elem_types) == 1:
            return f"List<{next(iter(elem_types))}>"
        return "List"
    # An unrecognised object — fall back to Str (its textual form crosses
    # the boundary as text, the same way an unstructurable tool result does).
    return "Str"


def rust_type_for(name: str) -> str:
    """The Rust-side form of a type name. Handles base types and the
    parametric ``List<elem>`` shape; unknown names echo back unchanged."""
    if name in BASE_TYPES:
        return BASE_TYPES[name][0]
    if name.startswith("List<") and name.endswith(">"):
        elem = name[len("List<"):-1]
        return f"Vec<{rust_type_for(elem)}>"
    return name


def kind_of(name: str) -> str:
    """The ``kind`` of a type name (scalar/ref/unit/parametric)."""
    if name in BASE_TYPES:
        return BASE_TYPES[name][1]
    if name.startswith("List<"):
        return "parametric"
    return "scalar"


def typecheck(arg_value: Any, expected_type_name: str) -> bool:
    """Does ``arg_value`` satisfy ``expected_type_name``?

    Exact base-type match, with two admissible widenings that mirror what
    the Rust evaluator accepts:

      * an ``Int`` value satisfies an expected ``Float`` (i64 widens to f64);
      * a concrete ``List<elem>`` value satisfies a bare ``List`` expectation,
        and any list satisfies ``List`` / ``List<X>`` when elements match.
    """
    actual = type_of_value(arg_value)
    if actual == expected_type_name:
        return True
    if expected_type_name == "Float" and actual == "Int":
        return True
    if expected_type_name == "List" and actual.startswith("List"):
        return True
    if expected_type_name.startswith("List") and actual.startswith("List"):
        # Compare element types when both are concrete; an empty list
        # (bare "List") satisfies any List<X>.
        if actual == "List":
            return True
        return actual == expected_type_name
    return False


__all__ = [
    "BASE_TYPES",
    "TYPE_NODE_TYPE",
    "install_type_system",
    "register_list_type",
    "type_of_value",
    "rust_type_for",
    "kind_of",
    "typecheck",
]
