"""Symbolic naming + persistence for detected insights.

When the substrate detects an insight (large ΔF + node flips between
steps), this module generates a structural name and records the event
as an InsightEvent node in the graph. The substrate accumulates a
queryable history of its own realisations.

The naming itself is pure translation: take the flipped-node list +
their post-insight σ values and build a canonical string. No agent
decisions — the name is determined entirely by what changed and how.

Schema:
  Microtheory ─has_insight→ InsightEvent
  InsightEvent attrs:
    short_name      — primary flipped node + direction (e.g. "ground_vec+")
    full_name       — all flipped nodes ranked by |Δσ| (e.g. "ground_vec+
                       ground_bin- frame_privil-")
    fingerprint     — canonical, deduplication-friendly form
    magnitude       — |ΔF|
    delta_F         — signed frustration delta (negative = good)
    flipped_count   — how many σ flipped
"""
from __future__ import annotations

from typing import Any


def _direction_symbol(value: float) -> str:
    return "+" if value > 0 else "-"


def name_insight(
    event: dict[str, Any],
    name_lookup: dict[int, str],
) -> dict[str, Any]:
    """Generate names from an insight event dict + a node_id → name map.

    Returns a dict carrying:
      short_name   — "<primary_node><direction>" using node with largest |Δσ|
      full_name    — "<n1><dir> <n2><dir> ..." ranked by |Δσ| descending
      fingerprint  — canonical form (sorted) suitable for dedup queries
      magnitude    — passed through from event
      delta_F      — passed through from event

    If event has no flipped nodes, returns a sentinel name."""
    flipped = event.get("flipped_nodes", []) if event else []
    if not flipped:
        return {
            "short_name": "no_flip",
            "full_name": "no_flip",
            "fingerprint": "",
            "magnitude": float(event.get("magnitude", 0.0)) if event else 0.0,
            "delta_F": float(event.get("delta_F", 0.0)) if event else 0.0,
        }

    def _label(item: dict[str, Any]) -> str:
        nid = int(item["node"])
        name = name_lookup.get(nid, f"node_{nid}")
        return f"{name}{_direction_symbol(item['after'])}"

    # Primary = largest |Δσ|.
    primary = max(flipped, key=lambda f: abs(float(f["delta"])))

    # Rank by |Δσ| descending for full_name; alphabetic for fingerprint.
    by_magnitude = sorted(flipped, key=lambda f: -abs(float(f["delta"])))
    labels_by_magnitude = [_label(f) for f in by_magnitude]
    labels_sorted = sorted(_label(f) for f in flipped)

    return {
        "short_name": _label(primary),
        "full_name": " ".join(labels_by_magnitude),
        "fingerprint": "|".join(labels_sorted),
        "magnitude": float(event.get("magnitude", 0.0)),
        "delta_F": float(event.get("delta_F", 0.0)),
    }


def build_name_lookup(substrate, mt) -> dict[int, str]:
    """Build a node_id → name map for all Concepts owned by mt. Used by
    name_insight/record_insight to translate flipped-node IDs into
    human-readable labels."""
    lookup: dict[int, str] = {}
    for c in substrate.neighbours(mt, "has_concept"):
        nid = c.value if hasattr(c, "value") else int(c)
        attrs = substrate.node(c)["attrs"]
        lookup[nid] = str(attrs.get("name", f"node_{nid}"))
    return lookup


def record_insight(
    substrate,
    mt,
    event: dict[str, Any],
    name_lookup: dict[int, str] | None = None,
) -> Any | None:
    """Create an InsightEvent node (or increment recurrence on an
    existing match) + link Mt → has_insight.

    Behaviour:
      · Build the insight's fingerprint
      · If an InsightEvent linked from this Mt has the same fingerprint:
        - Increment its recurrence_count attr
        - Update its magnitude/delta_F to the maximum seen so far
        - Set event['is_recurrence']=True + event['recurrence_count']
        - Return the existing node
      · Otherwise:
        - Create a new InsightEvent with recurrence_count=1
        - Return the new node

    The substrate accumulates a deduplicated history. Same realisation
    twice → one node, count = 2. The substrate can answer 'have I had
    this insight before?' by fingerprint match.

    Returns None if the production isn't configured.
    """
    if name_lookup is None:
        name_lookup = build_name_lookup(substrate, mt)
    names = name_insight(event, name_lookup)
    fingerprint = names["fingerprint"]

    # Check for existing event with same fingerprint.
    existing = find_insight_by_fingerprint(substrate, mt, fingerprint)
    if existing is not None:
        # Find the actual node handle.
        for insight_node in substrate.neighbours(mt, "has_insight"):
            nid = insight_node.value if hasattr(insight_node, "value") else int(insight_node)
            if nid == existing["node_id"]:
                attrs = substrate.node(insight_node)["attrs"]
                new_count = int(attrs.get("recurrence_count", 1)) + 1
                substrate.set_attr(insight_node, "recurrence_count", new_count)
                # Update magnitude / delta_F to the larger of recorded
                # vs current (substrate's most extreme experience).
                new_mag = max(float(attrs.get("magnitude", 0.0)),
                              float(event.get("magnitude", 0.0)))
                substrate.set_attr(insight_node, "magnitude", new_mag)
                new_df = min(float(attrs.get("delta_F", 0.0)),
                             float(event.get("delta_F", 0.0)))
                substrate.set_attr(insight_node, "delta_F", new_df)
                event["is_recurrence"] = True
                event["recurrence_count"] = new_count
                return insight_node
        # Shouldn't get here, but fall through to creation if we do.

    attrs: dict[str, Any] = {
        "short_name": names["short_name"],
        "full_name": names["full_name"],
        "fingerprint": fingerprint,
        "magnitude": float(event.get("magnitude", 0.0)),
        "delta_F": float(event.get("delta_F", 0.0)),
        "flipped_count": len(event.get("flipped_nodes", [])),
        "recurrence_count": 1,
    }
    if event.get("is_cascade"):
        attrs["is_cascade"] = True
        attrs["source_mt"] = int(event.get("source_mt", -1))

    try:
        insight_node = substrate.add_node("InsightEvent", attrs)
    except Exception:
        return None

    try:
        substrate.add_edge(mt, "has_insight", insight_node, {})
    except Exception:
        pass
    event["is_recurrence"] = False
    event["recurrence_count"] = 1
    return insight_node


def list_insights(substrate, mt) -> list[dict[str, Any]]:
    """Walk Mt → has_insight → InsightEvent. Return list of insight
    summary dicts in graph order."""
    out: list[dict[str, Any]] = []
    for insight_node in substrate.neighbours(mt, "has_insight"):
        attrs = substrate.node(insight_node)["attrs"]
        nid = insight_node.value if hasattr(insight_node, "value") else int(insight_node)
        out.append({
            "node_id": nid,
            "short_name": str(attrs.get("short_name", "")),
            "full_name": str(attrs.get("full_name", "")),
            "fingerprint": str(attrs.get("fingerprint", "")),
            "magnitude": float(attrs.get("magnitude", 0.0)),
            "delta_F": float(attrs.get("delta_F", 0.0)),
            "flipped_count": int(attrs.get("flipped_count", 0)),
            "recurrence_count": int(attrs.get("recurrence_count", 1)),
        })
    return out


def find_insight_by_fingerprint(
    substrate,
    mt,
    fingerprint: str,
) -> dict[str, Any] | None:
    """Look up a recorded insight by its canonical fingerprint. Returns
    None if no insight with that fingerprint is linked from mt."""
    for insight in list_insights(substrate, mt):
        if insight["fingerprint"] == fingerprint:
            return insight
    return None


__all__ = [
    "name_insight",
    "build_name_lookup",
    "record_insight",
    "list_insights",
    "find_insight_by_fingerprint",
]
