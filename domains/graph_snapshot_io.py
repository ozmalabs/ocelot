"""Mechanical JSON persistence for a substrate graph.

This module deliberately knows nothing about schedulers, cortex wrappers, or
policy state.  It only moves the Rust substrate's graph dictionary across the
filesystem boundary.
"""
from __future__ import annotations

import json
import os
from typing import Any


def save_graph_snapshot(substrate: Any, path: str) -> dict[str, Any]:
    """Write ``substrate.graph_to_dict()`` to ``path``."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(substrate.graph_to_dict(), handle)
    return {
        "graph_path": path,
        "graph_size": os.path.getsize(path),
    }


def load_graph_snapshot(substrate: Any, path: str) -> dict[str, Any]:
    """Load one graph JSON document into a fresh substrate."""
    with open(path, "r", encoding="utf-8") as handle:
        graph_dict = json.load(handle)
    substrate.graph_from_dict(graph_dict)
    return graph_dict


__all__ = ["load_graph_snapshot", "save_graph_snapshot"]
