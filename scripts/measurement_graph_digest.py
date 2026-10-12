"""Canonical graph projection and digest for substrate evaluation artifacts."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

_UNORDERED_WRAPPERS = frozenset({"__set__", "__fset__", "__frozenset__"})
_DEFAULT_VOLATILE = {"SystemModel": frozenset({"ts", "runtime_s"})}


def normalize_unordered(value: Any) -> Any:
    """Normalize graph-JSON set wrappers while preserving ordinary list order."""
    if isinstance(value, dict):
        if len(value) == 1:
            key = next(iter(value))
            if key in _UNORDERED_WRAPPERS:
                values = [normalize_unordered(x) for x in value[key]]
                values.sort(key=lambda x: json.dumps(
                    x, sort_keys=True, separators=(",", ":"), default=str))
                return {key: values}
        return {k: normalize_unordered(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_unordered(x) for x in value]
    if isinstance(value, (set, frozenset)):
        values = [normalize_unordered(x) for x in value]
        return sorted(values, key=lambda x: json.dumps(
            x, sort_keys=True, separators=(",", ":"), default=str))
    if isinstance(value, tuple):
        return [normalize_unordered(x) for x in value]
    return value


def canonical_graph_projection(
    graph: Mapping[str, Any],
    *,
    volatile_attrs: Mapping[str, frozenset[str]] | None = None,
) -> dict[str, Any]:
    """Canonicalize node/edge order and unordered attr values.

    The default projection matches the historical semantic graph digest's
    exclusion of SystemModel timestamps/runtime. Other attributes are retained.
    """
    omitted = dict(_DEFAULT_VOLATILE)
    if volatile_attrs:
        omitted.update(volatile_attrs)
    nodes = []
    for row in graph.get("nodes", ()):
        kind = str(row.get("type", ""))
        attrs = dict(row.get("attrs", {}))
        for key in omitted.get(kind, ()):
            attrs.pop(key, None)
        nodes.append({"id": row["id"], "type": kind,
                      "attrs": normalize_unordered(attrs)})
    nodes.sort(key=lambda n: (n["type"], str(n["id"]), json.dumps(
        n["attrs"], sort_keys=True, separators=(",", ":"), default=str)))
    edges = [{"src": row["src"], "type": str(row["type"]), "tgt": row["tgt"]}
             for row in graph.get("edges", ())]
    edges.sort(key=lambda e: (str(e["src"]), e["type"], str(e["tgt"])))
    return {"nodes": nodes, "edges": edges}


def canonical_graph_digest(
    graph: Mapping[str, Any],
    *,
    volatile_attrs: Mapping[str, frozenset[str]] | None = None,
) -> str:
    projection = canonical_graph_projection(graph, volatile_attrs=volatile_attrs)
    blob = json.dumps(projection, sort_keys=True, separators=(",", ":"),
                      default=str).encode()
    return hashlib.sha256(blob).hexdigest()
