#!/usr/bin/env python3
"""Persist the Jabberwock-authored threshold classifier as graph data.

This is authoring/persistence tooling, not runtime cognition.  It validates the
accepted artifact, reflects its Program IR with the Rust substrate, and writes
the resulting Program/Term subgraph as a normal seed.  Fresh agents therefore
recall a learned program without Python reconstructing part of the agent.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from substrate.world_adapter import WorldAdapter  # noqa: E402


ARTIFACT = ROOT / "results" / "jabberwock_threshold_classifier.json"
OUTPUT = ROOT / "seeds" / "threshold_classifier.json"


def _assert_integer_native(value: Any, path: tuple[Any, ...] = ()) -> None:
    if isinstance(value, float):
        raise TypeError(f"float in classifier seed source at {path!r}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_integer_native(child, path + (key,))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_integer_native(child, path + (index,))


def manifest() -> dict[str, Any]:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    _assert_integer_native(artifact)
    if artifact.get("status") != "accepted":
        raise ValueError("classifier artifact is not accepted")
    if artifact.get("held_out_pass_count") != artifact.get("held_out_count"):
        raise ValueError("classifier artifact has a held-out failure")

    # Rust reflection owns the canonical Term graph shape.  Only the delta
    # created by reflecting this learned IR is captured.
    scratch = WorldAdapter(seeds=())
    before_ids = {int(node.value) for node in scratch.s.nodes()}
    root = scratch.inner.add_term_subgraph(artifact["program_ir"])
    graph = scratch.inner.graph_to_dict()
    reflected = [
        node for node in graph["nodes"] if int(node["id"]) not in before_ids
    ]
    reflected.sort(key=lambda node: int(node["id"]))
    local_for_global = {
        int(node["id"]): index + 2
        for index, node in enumerate(reflected)
    }
    program_local = 1
    nodes = [{
        "local_id": program_local,
        "type": "Program",
        "attrs": {
            "name": artifact["program_name"],
            "faculty_kind": "threshold_classifier",
            "status": "accepted",
            "learned": 1,
            "held_out_pass_count": artifact["held_out_pass_count"],
            "held_out_count": artifact["held_out_count"],
            "tested_candidates": artifact["synthesis"]["tested_candidates"],
            "solution_size": artifact["synthesis"]["solution_size"],
            "integer_native": 1,
            "output_authority": 0,
        },
    }]
    nodes.extend({
        "local_id": local_for_global[int(node["id"])],
        "type": node["type"],
        "attrs": node.get("attrs", {}),
    } for node in reflected)

    edges = [{
        "src": {"role": "agent_root"},
        "type": "holds_threshold_classifier",
        "tgt": {"local": program_local},
        "attrs": {},
    }, {
        "src": {"role": "agent_root"},
        "type": "holds_faculty",
        "tgt": {"local": program_local},
        "attrs": {},
    }, {
        "src": {"local": program_local},
        "type": "ir_subgraph",
        "tgt": {"local": local_for_global[int(root.value)]},
        "attrs": {},
    }]
    for edge in graph["edges"]:
        src = int(edge["src"])
        tgt = int(edge["tgt"])
        if src not in local_for_global or tgt not in local_for_global:
            continue
        edges.append({
            "src": {"local": local_for_global[src]},
            "type": edge["type"],
            "tgt": {"local": local_for_global[tgt]},
            "attrs": edge.get("attrs", {}),
        })

    edge_types = sorted({edge["type"] for edge in edges})
    return {
        "id": "threshold_classifier",
        "version": "1.0.0",
        "depends_on": [],
        "area": "program_synthesis",
        "latency_class": "soft_realtime",
        "description": "Persisted graph Program authored by the Jabberwock "
        "and verified on held-out integer examples. It returns micros iff "
        "processed exceeds progress times a supplied threshold.",
        "nodes": nodes,
        "edges": edges,
        "productions": [{
            "provenance": f"threshold_classifier:{edge_type}",
            "src": {"type": "Node", "var": "src"},
            "edge_type": edge_type,
            "tgt": {"type": "Node", "var": "tgt"},
        } for edge_type in edge_types],
        "rules": [],
    }


def main() -> int:
    payload = manifest()
    _assert_integer_native(payload)
    OUTPUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(payload['nodes'])} nodes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
