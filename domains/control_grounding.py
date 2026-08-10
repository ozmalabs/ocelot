"""control_grounding — MECHANICAL I/O: ground a control KIND from the on-disk Wikipedia into a ControlKind node.

The control-kind taxonomy is OPEN: a starter set is seeded, but ANY kind name grounds on demand (rotary switch,
mouse, joystick, trackball, steering wheel, pedal, ... and arbitrarily more). This module only fetches the
knowledge and mints the node (the same admissible boundary as teaching/perception ingest); the effect_family is
classified GRAPH-NATIVELY by the control_kinds seed's classify_kind_family rule from the gloss's signal-words.
No decision over graph state lives here.
"""
from __future__ import annotations
from domains.wiki_library import WikipediaLibrary


def kind_registry(agent):
    """The single KindRegistry node every ControlKind hangs off (so the classifier rule can find them)."""
    reg = next((n for n in agent.s.nodes("KindRegistry")), None)
    if reg is None:
        reg = agent.s.add_node("KindRegistry", {"name": "control_kinds"})
    return reg


def ground_control_kind(agent, name, lib=None):
    """Ground one control kind from the on-disk wiki: mint ControlKind{name, gloss, gloss_lc} linked to the
    KindRegistry. Returns the node id, or None if wiki has no article (teaching/observation can still define it
    — grounding is the first, cheapest channel, not the only one). Re-grounding the same name is a no-op."""
    existing = next((n for n in agent.s.nodes("ControlKind")
                     if agent.s.node(n)["attrs"].get("name") == name), None)
    if existing is not None:
        return existing
    lib = lib or WikipediaLibrary()
    art = lib.article(name)
    if art is None:
        return None
    gloss = getattr(art, "summary", None) or (art.section_text(0) if hasattr(art, "section_text") else "")
    gloss = (gloss or "")[:400]
    ck = agent.s.add_node("ControlKind",
                          {"name": name, "name_lc": name.lower(), "gloss": gloss,
                           "gloss_lc": gloss.lower(), "family_set": 0.0})
    agent.inner.add_edge_unchecked(kind_registry(agent), "has_kind", ck)
    return ck
