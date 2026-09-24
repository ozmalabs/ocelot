"""Audit existing substrate records for complete Phase 4 evidence.

This deliberately reports availability; it never derives missing dimensions.
The conversation bridge may transport a complete tuple from an approved
cognitive source, but it must not turn a near-match into evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PHASE4_DIMENSIONS = frozenset(
    {"grounding", "expected_value", "residual_cost", "consequence", "novelty"}
)
APPROVED_SOURCE_TYPES = frozenset({"ThoughtManifold"})


def audit_phase4_tuple_sources(root: str | Path = ".") -> dict[str, Any]:
    """Return exact and near-match evidence records present in seed manifests."""
    root = Path(root)
    exact: list[dict[str, Any]] = []
    near: list[dict[str, Any]] = []
    for path in sorted((root / "seeds").rglob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        manifest_overlap: set[str] = set()
        for node in payload.get("nodes", []):
            if not isinstance(node, dict) or not isinstance(node.get("attrs"), dict):
                continue
            keys = set(node["attrs"])
            overlap = keys & PHASE4_DIMENSIONS
            manifest_overlap |= overlap
            record = {
                "path": str(path),
                "type": node.get("type"),
                "local_id": node.get("local_id"),
                "dimensions": sorted(overlap),
            }
            if overlap == PHASE4_DIMENSIONS:
                exact.append(record)
            elif len(overlap) >= 2:
                near.append(record)
        if len(manifest_overlap) >= 2:
            near.append({
                "path": str(path),
                "type": "manifest",
                "local_id": None,
                "dimensions": sorted(manifest_overlap),
            })
    return {
        "required_dimensions": sorted(PHASE4_DIMENSIONS),
        "approved_source_types": sorted(APPROVED_SOURCE_TYPES),
        "exact": exact,
        "near_matches": near,
        "exact_count": len(exact),
    }
