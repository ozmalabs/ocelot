"""Mechanical scheduling bridge for the generic allocentric world-view seed.

The optic-flow faculty first decides, in graph rules, which retinal motion
supports an ``OpticRangeEvidence`` node.  A node minted during that rule pass
does not enqueue a downstream rule in the native incremental matcher.  This
adapter therefore reifies each already-admitted, current-epoch evidence node
as a ``WorldViewIngress`` token and starts a second rule pass.

It performs no binning, thresholding, ranking, association, map mutation, or
occupancy inference.  Those operations—including exact-tie refusal—belong to
``seeds/allocentric_world_view.json``.  Deduplication is read from graph edges;
the adapter holds no private state.
"""
from __future__ import annotations


def ingest_current_optic_evidence(world_adapter, *, run_rules: bool = True) -> int:
    """Reify current graph-admitted optic evidence for world-view rules.

    Returns the number of new ingress tokens.  ``sensor_epoch`` equality is a
    protocol freshness handshake, not a perceptual threshold or selection.
    """
    substrate = world_adapter.s
    native = world_adapter.inner
    agent = world_adapter.agent
    epoch = substrate.node(agent)["attrs"].get("vision_settled_epoch")
    if epoch is None:
        return 0

    already_ingested = set()
    for ingress in native.neighbours(agent, "has_world_view_ingress"):
        already_ingested.update(
            native.neighbours(ingress, "based_on_spatial_evidence"))

    emitted = 0
    for evidence in native.neighbours(agent, "holds_spatial_evidence"):
        attrs = substrate.node(evidence)["attrs"]
        if attrs.get("sensor_epoch") != epoch or evidence in already_ingested:
            continue
        ingress = substrate.add_node(
            "WorldViewIngress",
            {
                "sensor_epoch": epoch,
                "status": "current_graph_admitted_spatial_evidence",
            },
        )
        native.add_edge_unchecked(agent, "has_world_view_ingress", ingress)
        native.add_edge_unchecked(
            ingress, "based_on_spatial_evidence", evidence)
        emitted += 1

    if emitted and run_rules:
        native.add_node("NativeAllocentricViewReceipt", {
            "schema": "native_allocentric_view_receipt_v1",
            "cluster": "allocentric_world_view.ingress",
            "provenance": "native_rule_readback:allocentric_view",
            "native_rule": "allocentric_world_view_native_rules",
            "native_steps": ["ingest_spatial_evidence", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        native.run_rules()
    return emitted
