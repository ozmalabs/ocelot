"""ID-independent Weisfeiler-Lehman fingerprint for serialized substrate graphs.

SystemModel.ts and SystemModel.runtime_s are execution metadata and are excluded;
NodeID-valued attributes are represented as labeled reference edges.
"""
from __future__ import annotations

import collections
import hashlib
import json
import re


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_graph_fingerprint(graph: dict, rounds: int = 4) -> tuple[str, dict]:
    nodes = {int(node["id"]): node for node in graph.get("nodes", [])}
    references = collections.defaultdict(list)

    def walk(value, path=()):
        if isinstance(value, dict):
            if set(value) == {"__nid__"}:
                try:
                    yield path, int(value["__nid__"])
                except (TypeError, ValueError):
                    pass
            else:
                for key, item in value.items():
                    yield from walk(item, path + (str(key),))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from walk(item, path + (str(index),))

    def id_target(value):
        match = re.search(r"(?:#)?(\d+)$", str(value))
        if match:
            candidate = int(match.group(1))
            if candidate in nodes:
                return candidate
        return None

    def node_core(node_id, node):
        attrs = dict(node.get("attrs", {}))
        if node.get("type") == "SystemModel":
            attrs.pop("ts", None)
            attrs.pop("runtime_s", None)
        for path, target in walk(attrs):
            if target in nodes:
                references[node_id].append(("attrref:" + ".".join(path), target))
        for key, value in attrs.items():
            if "foreign" in key.lower() or not (key.lower().endswith("_id") or key.lower().endswith("_ids")):
                continue
            values = value.get("__list__", []) if isinstance(value, dict) and "__list__" in value else (
                value if isinstance(value, list) else [value])
            for index, item in enumerate(values):
                target = id_target(item)
                if target is not None:
                    references[node_id].append((f"attrref:{key}[{index}]", target))

        def clean(value, key=""):
            if isinstance(value, dict):
                if set(value) == {"__nid__"}:
                    return {"__nref__": True}
                return {name: clean(item, name) for name, item in value.items()}
            if isinstance(value, list):
                return [clean(item, key) for item in value]
            if (key.lower().endswith("_id") or key.lower().endswith("_ids")) and "foreign" not in key.lower():
                if id_target(value) is not None:
                    return {"__nref__": True}
            return value

        return json.dumps({"type": node.get("type"), "attrs": clean(attrs)},
                          sort_keys=True, separators=(",", ":"), default=str)

    cores = {node_id: node_core(node_id, node) for node_id, node in nodes.items()}
    colors = {node_id: _sha(core.encode()) for node_id, core in cores.items()}
    edges = [(int(edge["src"]), int(edge["tgt"]), str(edge["type"]),
              json.dumps(edge.get("attrs", {}), sort_keys=True, separators=(",", ":"), default=str))
             for edge in graph.get("edges", [])]
    for _ in range(rounds):
        neighborhoods = {node_id: [] for node_id in nodes}
        for src, tgt, kind, attrs in edges:
            neighborhoods[src].append(("out", kind, attrs, colors[tgt]))
            neighborhoods[tgt].append(("in", kind, attrs, colors[src]))
        for src, refs in references.items():
            for kind, tgt in refs:
                neighborhoods[src].append(("ref", kind, "", colors[tgt]))
        colors = {node_id: _sha((cores[node_id] + "|" + json.dumps(
            sorted(neighborhoods[node_id]), separators=(",", ":"))).encode())
            for node_id in nodes}

    payload = {
        "nodes": sorted(colors.values()),
        "edges": sorted((colors[src], kind, colors[tgt], attrs) for src, tgt, kind, attrs in edges),
        "attribute_references": sorted((colors[src], kind, colors[tgt])
                                       for src, refs in references.items() for kind, tgt in refs),
    }
    return _sha(json.dumps(payload, separators=(",", ":")).encode()), {
        "node_count": len(nodes), "edge_count": len(edges),
        "normalized_node_references": sum(len(refs) for refs in references.values()),
        "excluded_system_model_timing_nodes": sum(
            node.get("type") == "SystemModel" and ("ts" in node.get("attrs", {}) or
                                                    "runtime_s" in node.get("attrs", {}))
            for node in nodes.values()),
    }
