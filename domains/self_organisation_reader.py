"""Lightweight graph reader for the agent's held microtheory organisation.

This query is a structural read, not a cognitive selector: the microtheories
and their `has_concept` edges are the complete answer evidence. Keeping the
reader separate lets the live adapter answer this narrow meta query without
importing the full reflective-faculty stack.
"""
from __future__ import annotations

import json
from typing import Any, Optional


def seed_inventory_from_graph(substrate):
    for node in substrate.nodes("Agent"):
        attrs = substrate.node(node)["attrs"]
        if attrs.get("microtheory_inventory_schema") != (
                "seed_microtheory_inventory.v1"):
            continue
        try:
            rows = json.loads(str(
                attrs.get("microtheory_inventory_areas_json") or "[]"))
        except (TypeError, ValueError):
            continue
        if isinstance(rows, list) and all(
                isinstance(row, dict) and isinstance(row.get("name"), str)
                and isinstance(row.get("concept_count"), int)
                for row in rows):
            return node, rows
    return None, None


def run_self_organisation(substrate, meta_arg: Optional[str] = None) -> dict[str, Any]:
    areas = []
    inventory_node, inventory = seed_inventory_from_graph(substrate)
    if inventory is not None:
        descriptions = {
            str(substrate.node(node)["attrs"].get("name")): str(
                substrate.node(node)["attrs"].get("description") or "")
            for node in substrate.nodes("Microtheory")
        }
        areas = [{"area": row["name"],
                  "concepts": row["concept_count"],
                  "about": descriptions.get(row["name"], "")}
                 for row in inventory]
        inventory_scope = "validated_seed_prepass_top12"
        total_area_count = int(
            substrate.node(inventory_node)["attrs"].get(
                "microtheory_inventory_area_count")
            or len(areas))
    else:
        for microtheory in substrate.nodes("Microtheory"):
            attrs = substrate.node(microtheory)["attrs"]
            name = attrs.get("name")
            if not name:
                continue
            concept_count = len(list(
                substrate.neighbours(microtheory, "has_concept")))
            areas.append({"area": name, "concepts": concept_count,
                          "about": attrs.get("description", "")})
        areas.sort(key=lambda row: (-row["concepts"], row["area"]))
        inventory_scope = "loaded_substrate_graph"
        total_area_count = len(areas)
    if not areas:
        return {"unwired": "no Microtheory areas held on this substrate "
                "(boot the full agent to read its self-organisation)"}
    return {
        "self_categorisation": "microtheory",
        "inventory_scope": inventory_scope,
        "complete_within_scope": True,
        "areas": [row["area"] for row in areas],
        "count": total_area_count,
        "detail": areas,
        "note": ("these are the seed-backed Microtheory areas in the cached "
                 "inventory; their grouping and concept counts are projected "
                 "from the validated seed manifests" if inventory is not None
                 else "these are the microtheories present in the currently "
                 "loaded graph; this inventory describes loaded graph scope, "
                 "not an assertion that every possible agent area is loaded"),
    }


__all__ = ["run_self_organisation", "seed_inventory_from_graph"]
