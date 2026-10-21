"""tom_meta_shape -- registers character_tom.py's nested belief-world and
bigville's controllability_for ToM belief as instances of ONE shared
meta-shape: "a mental state attributed to a mind other than the
reasoner's own" (TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_PREREG.md).

Reuses 100% of already-landed infrastructure -- domains.meta_shape.observe
and seeds/meta_shape_growth.json's already-tested sd-loop ladder
(recognize -> transform -> infer-dimension -> mint -> redecode). This
module adds exactly one mechanical thing: two small translator functions
projecting each domain's REAL attrs (character_tom's belief_holder/
flavor; bigville_theory_of_mind's target/aspect) into a shared relation
vocabulary neither domain's own representation carries natively. No
decision, no scoring, no Python matching loop -- the WHOLE recognize/
mint decision lives in the SAME Rust Term (RecogniseShape/MetaShapeMint)
and the SAME seeded rules `teach()` already uses for arbitrary items.

CAUTION for callers: `meta_shape.observe(agent, ...)` requires
`agent.s` (the Python Substrate wrapper) and `agent.agent` (a real Agent
node) -- a full WorldAdapter, not the bare `inner`/`Microtheory` pattern
bigville's own hate_attribution/shared_arousal tests use. This is an
EXPLICIT registration action (mirroring teach()'s own explicit-invocation
precedent), not wired into either domain's runtime ingest flow.
"""
from __future__ import annotations

import json

from domains.meta_shape import observe

ATTRIBUTED_MENTAL_STATE_TYPE = "AttributedMentalState"
UNKNOWN_SOURCE_EPOCH = {"known": False}


def _emit_source(agent, *, source_kind: str, source_node, holder: str,
                 target, content_ref: str, modality: str,
                 epistemic_kind: str, source_epoch=None):
    """Mechanically translate one source record into the opt-in source schema.

    No source is emitted unless the caller's graph has explicitly loaded
    `tom_unified_view`; the native policy still controls whether it becomes a
    view. The source record and shared MetaShape observation retain separate
    provenance and do not replace the domain node.
    """
    sub = getattr(agent, "s", None)
    native = getattr(agent, "inner", None)
    root = getattr(agent, "agent", None)
    if sub is None or native is None or root is None:
        return None
    policies = list(native.neighbours(root, "has_tom_view_policy"))
    if not policies:
        return None
    owner_id = str(root)
    source_node_id = str(source_node)
    epoch = UNKNOWN_SOURCE_EPOCH if source_epoch is None else source_epoch
    source_key = json.dumps([source_kind, owner_id, source_node_id],
                            ensure_ascii=False, separators=(",", ":"))
    source_attrs = {
        "schema_version": 1,
        "source_key": source_key,
        "source_is_current": True,
        "source_kind": source_kind,
        "source_node": source_node_id,
        "source_epoch": epoch,
        "owner_id": owner_id,
        "holder": str(holder),
        "target": None if target is None else str(target),
        "content_ref": str(content_ref),
        "modality": str(modality),
        "epistemic_kind": str(epistemic_kind),
    }
    sources = [n for n in native.nodes("TomAttributedStateSource")
               if native.node(n)["attrs"].get("source_key") == source_key]
    source = next((n for n in sources
                   if native.node(n)["attrs"].get("source_epoch") == epoch), None)
    policy_enabled = native.node(policies[0])["attrs"].get("enabled", 0.0) >= 1.0
    observation = None
    if source is None:
        for prior in sources:
            if native.node(prior)["attrs"].get("source_is_current"):
                native.set_attr(prior, "source_is_current", False)
        source = sub.add_node("TomAttributedStateSource", source_attrs)
        native.add_edge_unchecked(root, "has_tom_attributed_source", source)
    existing_observations = list(native.neighbours(source, "has_tom_source_observation"))
    if policy_enabled and not existing_observations:
        observation = observe(agent, ATTRIBUTED_MENTAL_STATE_TYPE,
                              attributed_mental_state_signature(
                                  str(holder), "" if target is None else str(target),
                                  str(epistemic_kind)))
        if observation is not None:
            native.add_edge_unchecked(source, "has_tom_source_observation", observation)
    elif existing_observations:
        observation = existing_observations[0]
    native.run_rules()
    return {"source": source, "observation": observation}


def project_character_tom_node(agent, source_node):
    """Translate an existing nested `SmEntity` without changing it."""
    sub = getattr(agent, "s", None)
    if sub is None:
        return None
    attrs = sub.node(source_node)["attrs"]
    content = attrs.get("proposition") or attrs.get("proposition_span") or attrs.get("referent") or ""
    return _emit_source(
        agent, source_kind="character_tom", source_node=source_node,
        holder=attrs.get("belief_holder", "unknown"), target=attrs.get("referent"),
        content_ref=content, modality=attrs.get("flavor", "belief"),
        epistemic_kind="attributed", source_epoch=attrs.get("source_epoch"),
    )


def project_interlocutor_estimate(agent, party):
    """Translate the agent's accumulated estimate of an interlocutor."""
    sub = getattr(agent, "s", None)
    if sub is None:
        return None
    attrs = sub.node(party)["attrs"]
    content = json.dumps({"feat_counts": attrs.get("feat_counts", {}),
                          "known_concepts": attrs.get("known_concepts", [])},
                         ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _emit_source(
        agent, source_kind="interlocutor_estimate", source_node=party,
        holder="agent", target=attrs.get("name", str(party)), content_ref=content,
        modality="estimate", epistemic_kind="estimate",
        source_epoch=attrs.get("estimate_epoch", attrs.get("turns")),
    )


def project_interlocutor_assertion(agent, party, assertion):
    """Translate an immutable self-report record, separate from belief estimates."""
    sub = getattr(agent, "s", None)
    if sub is None:
        return None
    party_attrs = sub.node(party)["attrs"]
    attrs = sub.node(assertion)["attrs"]
    return _emit_source(
        agent, source_kind="interlocutor_assertion", source_node=assertion,
        holder=party_attrs.get("name", str(party)), target=None,
        content_ref=attrs.get("content", ""), modality=attrs.get("flavor", "asserted"),
        epistemic_kind="world_assertion", source_epoch=attrs.get("turn"),
    )


def project_resident_agency_belief(agent, concept, *, resident: str, target: str):
    """Translate only resident ToM concepts; own-affect concepts are excluded."""
    sub = getattr(agent, "s", None)
    if sub is None:
        return None
    attrs = sub.node(concept)["attrs"]
    name = str(attrs.get("name", ""))
    if not name.startswith("controllability_for:"):
        return None
    content = json.dumps({"name": name, "state": attrs.get("state"),
                          "external_field": attrs.get("external_field")},
                         ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _emit_source(
        agent, source_kind="bigville_tom", source_node=concept,
        holder=resident, target=target, content_ref=content,
        modality="attributed", epistemic_kind="attributed",
        source_epoch=attrs.get("source_epoch"),
    )


def attributed_mental_state_signature(attributor: str, target: str, content_kind: str) -> dict:
    """The shared relation vocabulary both domains project into. Mechanical
    dict construction, no decision."""
    return {"attributor": attributor, "target": target, "content_kind": content_kind}


def character_tom_mental_state_signature(belief_holder: str, flavor: str) -> dict:
    """`character_tom.py`'s own real attrs (`_nested_entity`'s
    `belief_holder`/`flavor` fields) projected into the shared vocabulary.
    The attributor is always "reader" -- the comprehension process
    modeling the character's mind, not another character."""
    return attributed_mental_state_signature("reader", belief_holder, flavor)


def resident_tom_mental_state_signature(target: str, aspect: str) -> dict:
    """Mirrors `bigville_theory_of_mind.mint_resident_tom_belief`'s own
    `(aspect, target)` parameters, projected into the shared vocabulary.
    The attributor is always "resident" -- the OTHER resident doing the
    attributing."""
    return attributed_mental_state_signature("resident", target, aspect)


def register_character_tom_attitude(agent, belief_holder: str, flavor: str):
    """Explicit registration -- NOT called automatically by character_tom's
    own ingest. Returns the ShapeObservation node id, or None if `agent`
    has no live graph (matches meta_shape.observe's own degrade-gracefully
    contract)."""
    return observe(agent, ATTRIBUTED_MENTAL_STATE_TYPE,
                    character_tom_mental_state_signature(belief_holder, flavor))


def register_resident_tom_belief(agent, target: str, aspect: str):
    """Explicit registration -- NOT called automatically by
    hate_attribution's own controllability_for minting. Returns the
    ShapeObservation node id, or None if `agent` has no live graph."""
    return observe(agent, ATTRIBUTED_MENTAL_STATE_TYPE,
                    resident_tom_mental_state_signature(target, aspect))


__all__ = [
    "ATTRIBUTED_MENTAL_STATE_TYPE",
    "attributed_mental_state_signature",
    "character_tom_mental_state_signature",
    "resident_tom_mental_state_signature",
    "register_character_tom_attitude",
    "register_resident_tom_belief",
    "project_character_tom_node",
    "project_interlocutor_estimate",
    "project_interlocutor_assertion",
    "project_resident_agency_belief",
]
