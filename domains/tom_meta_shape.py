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

from domains.meta_shape import observe

ATTRIBUTED_MENTAL_STATE_TYPE = "AttributedMentalState"


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
]
