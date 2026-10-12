"""Audit partial Phase 4 evidence without promoting or scoring it.

Phase 4R is an integration audit, not a candidate generator.  The substrate
already has faculties that expose useful but non-equivalent measurements.  This
module records those measurements' provenance and missing tuple dimensions so
the live bridge can distinguish reusable evidence from an invented candidate.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from evaluation.phase4_substrate_tuple_audit import APPROVED_SOURCE_TYPES


PHASE4_DIMENSIONS = (
    "grounding", "expected_value", "residual_cost", "consequence", "novelty"
)


def _source_id(value: Any) -> str:
    """Return a deterministic, display-safe source identifier."""
    if hasattr(value, "value"):
        value = value.value
    return str(value)


def _record(source: Mapping[str, Any]) -> dict[str, Any]:
    """Audit one already-materialized evidence record.

    Only keys physically present in ``attrs`` count.  In particular, zero is a
    valid measured value while an absent key remains absent; no dimension is
    filled from a neighboring faculty or from a default.
    """
    attrs = source.get("attrs")
    if not isinstance(attrs, Mapping):
        attrs = {}
    present = [key for key in PHASE4_DIMENSIONS if key in attrs]
    missing = [key for key in PHASE4_DIMENSIONS if key not in attrs]
    complete = not missing
    source_type = str(source.get("source_type", "unknown"))
    authorized = source_type in APPROVED_SOURCE_TYPES
    eligible = complete and authorized
    return {
        "source_id": _source_id(source.get("source_id", "")),
        "source_type": source_type,
        "faculty": str(source.get("faculty", "unspecified")),
        "dimensions_present": present,
        "dimensions_missing": missing,
        "complete_tuple": complete,
        "promotion_eligible": eligible,
        "promotion_reason": (
            "complete_existing_tuple"
            if eligible else "unapproved_source_type"
            if complete else "missing_phase4_dimensions"
        ),
    }


def audit_partial_evidence(sources: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return a deterministic, JSON-safe partial-evidence audit.

    ``sources`` is an observation boundary: callers supply graph-resident
    records and their owning faculty.  This function never computes missing
    dimensions, ranks sources, creates graph nodes, or selects a candidate.
    """
    records = [_record(source) for source in sources]
    records.sort(key=lambda row: (row["source_type"], row["source_id"],
                                  row["faculty"]))
    complete = [row for row in records if row["complete_tuple"]]
    eligible = [row for row in records if row["promotion_eligible"]]
    return {
        "schema": "phase4_partial_evidence_audit.v1",
        "required_dimensions": list(PHASE4_DIMENSIONS),
        "source_count": len(records),
        "complete_tuple_count": len(complete),
        # This module is an observation boundary only.  Eligibility is reported
        # separately; no candidate is created or promoted here.
        "promotion_eligible_count": len(eligible),
        "promotion_count": 0,
        "records": records,
        "replay_deterministic": True,
    }


def _graph_sources(agent, event) -> list[dict[str, Any]]:
    """Read explicitly event-linked evidence nodes without deriving evidence."""
    substrate = getattr(agent, "s", agent)
    inner = getattr(agent, "inner", getattr(substrate, "_inner", substrate))
    if not substrate.has_node(event):
        return []
    sources: list[dict[str, Any]] = []
    event_links = (
        "derived_from_discourse_event", "generated_from_discourse_event",
        "evidence_for_event", "for_event",
    )
    bridge_nodes: set[Any] = {event}
    # Read the exact incoming/outgoing adjacency sets rather than scanning
    # every graph node and testing four relations in both directions for each
    # event. This preserves the explicit-link boundary while making discovery
    # proportional to the event's actual degree.
    for relation in event_links:
        try:
            bridge_nodes.update(inner.neighbours(event, relation))
        except Exception:
            pass
        try:
            bridge_nodes.update(inner.in_neighbours(event, relation))
        except Exception:
            pass

    # Follow only explicit provenance edges from the event/manifold bridge.
    # This is a graph read, not a search for a convenient combination of
    # dimensions: each returned node remains the owner of its own attrs.
    evidence_relations = (
        "has_goal_evidence", "has_repair_evidence", "has_stance_evidence",
        "has_residual_evidence", "has_partial_evidence",
        "proposes_candidate", "derived_from_evidence",
    )
    direct_nodes = bridge_nodes - {event}
    provenance_bridges = set()
    direct_sources = set()
    for bridge in direct_nodes:
        has_explicit_child = False
        for relation in evidence_relations:
            try:
                children = set(inner.neighbours(bridge, relation))
            except Exception:
                children = set()
            if children:
                has_explicit_child = True
                break
        (provenance_bridges if has_explicit_child else direct_sources).add(bridge)

    linked_nodes = set(direct_sources) | set(provenance_bridges)
    for bridge in tuple(provenance_bridges):
        for relation in evidence_relations:
            try:
                linked_nodes.update(inner.neighbours(bridge, relation))
            except Exception:
                continue
    for node in sorted(linked_nodes, key=_source_id):
        if node in provenance_bridges or not substrate.has_node(node):
            continue
        attrs = dict(substrate.node(node)["attrs"])
        nested = attrs.get("phase4_evidence")
        observed_attrs = dict(attrs)
        if isinstance(nested, Mapping):
            observed_attrs.update(nested)
        # Empty manifolds and deliberation containers are structural trace
        # nodes, not partial evidence sources.  Keep them out of source
        # coverage while retaining their native no-candidate traces elsewhere.
        if not any(key in observed_attrs for key in PHASE4_DIMENSIONS):
            continue
        sources.append({
            "source_id": node,
            "source_type": substrate.node(node)["type"],
            "faculty": attrs.get("evidence_faculty", attrs.get("source", "graph")),
            "attrs": observed_attrs,
        })
    return sources


def audit_live_event(agent, event) -> dict[str, Any]:
    """Audit explicitly event-linked graph evidence for one live event."""
    return audit_partial_evidence(_graph_sources(agent, event))


__all__ = ["PHASE4_DIMENSIONS", "audit_partial_evidence", "audit_live_event"]
