"""Migration shim: binary refers_to → causal_influence(J=+1).

Backwards compatibility while the substrate transitions to vector grounding.
Each existing refers_to(A, B) edge becomes a parallel causal_influence(A, B)
with weight = +1.0 (strong positive coupling). Legacy code reading refers_to
keeps working; new code reading causal_influence sees the same structure
plus the vector machinery.

This is a world-adapter operation: mechanical translation of graph state,
no decisions, no agent logic.
"""
from __future__ import annotations


def migrate_refers_to_to_causal_influence(substrate, weight: float = 1.0) -> int:
    """Walk all refers_to edges; create parallel causal_influence edges
    with the given weight (default +1.0 — strong positive coupling).

    Idempotent: if a causal_influence already exists between the same
    src/tgt, the existing weight is left alone.

    Returns the number of newly-created causal_influence edges.
    """
    created = 0
    # The substrate doesn't expose an "iterate edges of type" via Python,
    # so walk every node + read its out-refers_to neighbours.
    for nid in substrate.nodes():
        targets = substrate.neighbours(nid, "refers_to")
        for tgt in targets:
            # Skip if causal_influence already exists between this pair.
            existing = substrate.neighbours(nid, "causal_influence")
            if tgt in existing:
                continue
            try:
                substrate.add_edge(nid, "causal_influence", tgt,
                                   {"weight": float(weight)})
                created += 1
            except Exception:
                # Production not open for (src_type, causal_influence,
                # tgt_type) — silently skip; world adapter doesn't decide.
                pass
    return created


def seed_concept_state_attrs(substrate) -> int:
    """Initialise state + external_field on Concept nodes that lack them.

    Default values: state = 0.0 (no commitment yet); external_field = 0.0
    (no evidence yet). target_state intentionally NOT set here — it's
    Mt-specific and set by the Mt's seed installer.

    Returns the number of Concepts touched.
    """
    touched = 0
    for nid in substrate.nodes("Concept"):
        attrs = substrate.node(nid)["attrs"]
        changed = False
        if "state" not in attrs:
            substrate.set_attr(nid, "state", 0.0)
            changed = True
        if "external_field" not in attrs:
            substrate.set_attr(nid, "external_field", 0.0)
            changed = True
        if changed:
            touched += 1
    return touched


def seed_mt_temperature(substrate, default_beta: float = 1.0) -> int:
    """Initialise temperature (= β) on Microtheories that lack it.

    Default β = 1.0 (no particular attention emphasis). Foundational Mts
    typically want a higher β (substrate identity = focused commitment);
    domain Mts want lower β by default.

    Returns the number of Mts touched.
    """
    touched = 0
    for nid in substrate.nodes("Microtheory"):
        attrs = substrate.node(nid)["attrs"]
        if "temperature" not in attrs:
            substrate.set_attr(nid, "temperature", float(default_beta))
            touched += 1
    return touched


def full_migration(substrate, default_weight: float = 1.0,
                   default_beta: float = 1.0) -> dict:
    """One-shot full migration. Returns a dict with counters for each
    stage:
        edges_created: refers_to → causal_influence parallel edges
        concepts_seeded: Concept attrs (state, external_field) added
        mts_seeded: Microtheory temperature attrs added
    Idempotent; safe to call repeatedly.
    """
    return {
        "edges_created": migrate_refers_to_to_causal_influence(
            substrate, weight=default_weight),
        "concepts_seeded": seed_concept_state_attrs(substrate),
        "mts_seeded": seed_mt_temperature(substrate, default_beta=default_beta),
    }


__all__ = [
    "migrate_refers_to_to_causal_influence",
    "seed_concept_state_attrs",
    "seed_mt_temperature",
    "full_migration",
]
