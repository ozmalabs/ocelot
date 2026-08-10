"""Persistence for the substrate's self-modifications.

Per the substrate's own state at the end of step 6a0dd52: the
self-modification loop runs end-to-end (detect unread observations
→ synthesise qualities → score them, 96% → 97.5%) but every fresh
substrate boot started from zero. Synthesised qualities, AST-migrated
FilterSpecs, ActionSpec nodes, gap reports — all rebuilt every run.

The substrate's existing graph_to_dict / graph_from_dict already
serialises the whole graph state. This module is the thin wrapper
that lets the substrate's self-modifications persist across restarts:

  save_state(substrate, path)  — graph_to_dict → JSON file
  load_state(substrate, path)  → bool — JSON file → graph_from_dict
  state_exists(path)            — has a saved state been written?

With this in place, the loop becomes incremental: each run starts
from where the previous left off. Synthesised qualities already
exist; detect_unread_observations finds nothing new; the substrate's
self-assessment reflects accumulated modifications, not fresh ones."""
from __future__ import annotations

import json
import os
from typing import Any


def save_state(substrate, path: str) -> dict:
    """Save the substrate's full graph state to a JSON file.

    Returns summary: {path, size_bytes, n_nodes, n_edges, n_productions}."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    graph_dict = substrate.graph_to_dict()
    with open(path, "w") as f:
        json.dump(graph_dict, f)
    return {
        "path": path,
        "size_bytes": os.path.getsize(path),
        "n_nodes": len(graph_dict.get("nodes", [])),
        "n_edges": len(graph_dict.get("edges", [])),
        "n_productions": len(graph_dict.get("productions", [])),
    }


def load_state(substrate, path: str) -> bool:
    """Restore substrate state from a saved JSON file. Returns True
    if the file existed and was loaded; False if no saved state
    exists (this is the substrate's first boot)."""
    if not os.path.exists(path):
        return False
    with open(path) as f:
        graph_dict = json.load(f)
    substrate.graph_from_dict(graph_dict)
    return True


def state_exists(path: str) -> bool:
    """Is there a saved state file at this path?"""
    return os.path.exists(path)


def summary_after_load(substrate) -> dict:
    """Quick introspection of what the loaded substrate contains.
    Used by demo scripts to confirm persistence."""
    counts: dict[str, int] = {}
    interesting_types = (
        "Microtheory", "Concept", "Rule",
        "FilterSpec", "ActionSpec",
        "ArchitecturalQuality", "ArchitecturalSmell",
        "RunnerObservation", "TheoryEnactmentGap",
        "UnreadObservationEvent", "DormantTheoryEvent",
        "Assessment", "QualityScore",
        "CodeWritingCortex", "ArchitectureCortex",
    )
    for t in interesting_types:
        counts[t] = len(list(substrate.nodes(t)))
    return counts


__all__ = ["save_state", "load_state", "state_exists",
           "summary_after_load"]
