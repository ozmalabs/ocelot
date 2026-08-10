"""The receiver model — theory of mind for communication.

A communicative act happens inside a PARTICIPATION FRAMEWORK: not one listener
but a set of modeled minds — the addressee, plus overhearers/bystanders and
possible third-party targets (the real target may not be the addressee). Each
party is a modeled entity (the substrate already models others via `models`
boundary relations) carrying a believed mind-state. This is the thin first
slice: each party holds a believed-knowledge set (which grounded concepts it is
believed to know) and a level; richer state (misconceptions, attention, goals,
readiness) are the next axes.

The first instrumental capability — what objective-driven production consumes —
is NOVELTY: for a meaning and a given party, which concepts are NEW to that
party versus already held. The "does this party know X" judgement is a graph-
resident Term (theory of mind read off the party's believed graph); novelty is
computed for ANY party, so the objective can target a third party, not just the
addressee. Novelty is instrumental (it serves whatever the objective is — inform,
emphasise, signal to an overhearer); it is not itself the objective.
"""
from __future__ import annotations

from substrate_rs import Attr, Eq, Exists, Neighbours, Var, _native

_TYPES = ("Scene", "Party", "Concept")
_EDGES = ("party", "concept", "knows")


def new_graph():
    """A native substrate carrying a permissive grammar for the participation-
    framework schema (Scene/Party/Concept linked by party/concept/knows)."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "audience"})
    return g


def make_scene(graph) -> int:
    """A participation framework — the anchor the modeled parties hang off."""
    return graph.add_node("Scene", {"id": "scene"})


def add_party(graph, scene, name: str, knows,
              role: str = "addressee", level: int = 1) -> int:
    """Add a modeled mind to the scene: its role (addressee / overhearer /
    target), level, and believed-knowledge (the concepts it is believed to hold,
    linked to Concept nodes)."""
    p = graph.add_node("Party", {"id": f"party_{name}", "name": name,
                                 "role": role, "level": level})
    graph.add_edge(scene, "party", p, {})
    for c in knows:
        node = next((t for t in graph.neighbours(scene, "concept")
                     if graph.node(t)["attrs"]["name"] == c), None)
        if node is None:
            node = graph.add_node("Concept", {"id": f"concept_{c}", "name": c})
            graph.add_edge(scene, "concept", node, {})
        graph.add_edge(p, "knows", node, {})
    return p


def _knows_term():
    """Theory-of-mind read: does the party (``p``) believe-know the concept
    named ``name``? — an Exists over the party's ``knows`` edges."""
    return Exists(Neighbours(Var("p"), "knows"), "c",
                  Eq(a=Attr(Var("c"), "name"), b=Var("name")))


def knows(graph, party, concept: str) -> bool:
    return bool(_knows_term().evaluate({"p": party, "name": concept}, graph))


def _concepts(meaning) -> set:
    """The grounded concepts a meaning Term mentions (numbers carry none)."""
    if isinstance(meaning, bool) or isinstance(meaning, int):
        return set()
    if isinstance(meaning, str):
        return {meaning}
    out = set()
    for k, v in meaning.items():
        if k == "force":
            continue
        out.add(k)
        for child in v.values():
            out |= _concepts(child)
    return out


def novelty(graph, meaning, party) -> dict:
    """Classify the meaning's concepts as ``known`` vs ``new`` for ``party`` —
    the basis for meeting that party where they are (convey/emphasise the new,
    lean on the known). Works for any party in the framework, addressee or not."""
    cs = _concepts(meaning)
    known = {c for c in cs if knows(graph, party, c)}
    return {"known": sorted(known), "new": sorted(cs - known)}
