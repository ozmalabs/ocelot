"""Cross-Mt insight propagation — cascades through shared Concepts.

The substrate's CAN architecture already produces propagation
implicitly: Concept state lives on the Concept node, not per-Mt. When
two Mts share a Concept (both have has_concept → C), an insight that
flips C in Mt_A means Mt_B's next relax will incorporate the new σ
on C — its basin may shift.

This module makes propagation EXPLICIT and within-step:
  · After primary insight detected in Mt_A, scan all other Mts
  · For each Mt_B that shares any flipped Concept with Mt_A:
      - Relax Mt_B with the updated shared state
      - Detect if Mt_B itself had a basin transition
      - If yes: consolidate, name, record as cascade
  · Stash post-cascade state on Mt_B so the main loop iteration
    sees it as already-handled (no double-detection)

A cascade carries `source_mt` + `is_cascade=True` markers so it's
distinguishable from a primary insight when queried later.
"""
from __future__ import annotations

from typing import Any


def find_shared_concepts(substrate, mt_a, mt_b) -> set[int]:
    """Return the set of Concept node_ids that both Mts own via
    has_concept edges."""
    ids_a = {c.value for c in substrate.neighbours(mt_a, "has_concept")}
    ids_b = {c.value for c in substrate.neighbours(mt_b, "has_concept")}
    return ids_a & ids_b


def find_connected_mts(
    substrate,
    source_mt,
    flipped_node_ids: set[int],
) -> list[tuple[Any, set[int]]]:
    """For each Mt ≠ source_mt, return (mt_handle, shared_flipped_ids)
    if the Mt owns any of the flipped Concepts."""
    source_id = source_mt.value if hasattr(source_mt, "value") else int(source_mt)
    out: list[tuple[Any, set[int]]] = []
    for other_mt in substrate.nodes("Microtheory"):
        other_id = other_mt.value if hasattr(other_mt, "value") else int(other_mt)
        if other_id == source_id:
            continue
        other_concept_ids = {
            c.value for c in substrate.neighbours(other_mt, "has_concept")
        }
        shared = other_concept_ids & flipped_node_ids
        if shared:
            out.append((other_mt, shared))
    return out


def propagate_insight(
    substrate,
    source_mt,
    insight_event: dict[str, Any],
) -> list[dict[str, Any]]:
    """After a primary insight in source_mt, propagate to all other Mts
    sharing any flipped Concept. Returns list of cascade records.

    For each connected Mt:
      1. Read previous frustration + state (already stashed from
         that Mt's previous step)
      2. Relax with the now-updated shared Concept σ values
      3. Audit basin
      4. Detect cascading insight (same thresholds as primary)
      5. If cascade detected: consolidate (policy-gated),
         name + record as InsightEvent with is_cascade=True +
         source_mt set
      6. Stash post-state so main loop won't double-detect

    Each cascade record dict: {target_mt, shared_node_ids,
    cascading_insight (or None if no transition)}"""
    from domains.insight_detection import (
        compute_delta_f_via_substrate,
        consolidate_insight,
        detect_insight,
        read_previous_state,
    )
    from domains.insight_naming import (
        build_name_lookup,
        name_insight,
        record_insight,
    )
    from domains.self_improvement_loop import _audit_basin, _stash_post_state, relax

    flipped_node_ids = {
        int(f["node"]) for f in insight_event.get("flipped_nodes", [])
    }
    if not flipped_node_ids:
        return []

    source_id = source_mt.value if hasattr(source_mt, "value") else int(source_mt)
    cascades: list[dict[str, Any]] = []

    for other_mt, shared in find_connected_mts(
        substrate, source_mt, flipped_node_ids
    ):
        # Read previous state (from this Mt's previous step's stash).
        prev_frust, prev_state = read_previous_state(substrate, other_mt)

        # Relax with the now-updated shared Concept σ. The Concepts'
        # state attrs were already written by source_mt's relax —
        # this Mt's relax now incorporates them.
        #
        # Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): STAYS BLOCKED
        # per CAN_FINAL_MIGRATION_RESULTS.md is now RESOLVED the same way
        # as consolidate_insight -- `relax`/`_audit_basin` (both already
        # discrete_mode-gated in self_improvement_loop.py) call
        # `run_rules_scoped(other_mt)` / read `state` directly, isolated
        # to `other_mt` only, never touching `source_mt` or any other
        # Microtheory sharing this tick.
        relax(substrate, other_mt)
        new_audit = _audit_basin(substrate, other_mt)

        # ΔF for this Mt via the substrate's Term-tree evaluator.
        delta_f = None
        if "previous_frustration" in substrate.node(other_mt)["attrs"]:
            delta_f = compute_delta_f_via_substrate(
                substrate, other_mt, float(new_audit["frustration"]))

        cascade_event = detect_insight(
            prev_frust,
            prev_state,
            new_audit,
            other_mt.value if hasattr(other_mt, "value") else int(other_mt),
            delta_f=delta_f,
        )

        if cascade_event is not None:
            cascade_event["is_cascade"] = True
            cascade_event["source_mt"] = source_id
            # Consolidate, name, record.
            consolidation = consolidate_insight(substrate, other_mt)
            if consolidation:
                relax(substrate, other_mt)
                new_audit = _audit_basin(substrate, other_mt)
            cascade_event["consolidation_edges"] = consolidation
            name_lookup = build_name_lookup(substrate, other_mt)
            cascade_event["names"] = name_insight(cascade_event, name_lookup)
            recorded = record_insight(
                substrate, other_mt, cascade_event, name_lookup
            )
            if recorded is not None:
                cascade_event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )

        # Stash post-state so the main loop's iteration for this Mt
        # sees the cascade as already-handled.
        _stash_post_state(substrate, other_mt, new_audit)

        cascades.append({
            "target_mt": other_mt.value if hasattr(other_mt, "value")
            else int(other_mt),
            "shared_node_ids": sorted(shared),
            "cascading_insight": cascade_event,
            "post_audit": new_audit,
        })

    return cascades


def list_cascades_from(substrate, source_mt) -> list[dict[str, Any]]:
    """Find all recorded InsightEvent nodes (across any Mt) whose
    `source_mt` attr equals source_mt's id. Returns list of summaries."""
    from domains.insight_naming import list_insights
    source_id = source_mt.value if hasattr(source_mt, "value") else int(source_mt)
    out: list[dict[str, Any]] = []
    for mt in substrate.nodes("Microtheory"):
        mt_id = mt.value if hasattr(mt, "value") else int(mt)
        if mt_id == source_id:
            continue
        for insight in list_insights(substrate, mt):
            # is_cascade + source_mt aren't part of list_insights's
            # default summary; read directly from node attrs.
            attrs = substrate.node_count  # placeholder reference
            # Actually need to look up the node — list_insights returns
            # the summary dict. We need to walk the actual nodes.
            pass
        # Walk Mt → has_insight directly for source_mt-marked events.
        for insight_node in substrate.neighbours(mt, "has_insight"):
            attrs = substrate.node(insight_node)["attrs"]
            if int(attrs.get("source_mt", -1)) == source_id:
                out.append({
                    "target_mt": mt_id,
                    "node_id": insight_node.value if hasattr(insight_node, "value")
                    else int(insight_node),
                    "short_name": str(attrs.get("short_name", "")),
                    "full_name": str(attrs.get("full_name", "")),
                    "fingerprint": str(attrs.get("fingerprint", "")),
                })
    return out


__all__ = [
    "find_shared_concepts",
    "find_connected_mts",
    "propagate_insight",
    "list_cascades_from",
]
