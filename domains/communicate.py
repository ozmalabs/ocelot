"""Objective-driven production — speaking as goal-directed action.

An utterance is an ACTION: the entity chooses whether and what to say so that the
predicted effect (across the participation framework — addressee AND overhearers)
best achieves THE OBJECTIVE. This reuses the agent's general action-selection
shape — predict each candidate's effect, value it against the goal, take the
argmax — with utterances as the action space and the objective as the value.

What this makes fall out of ONE selection (not special cases):
  * THIRD-PARTY targeting — the objective may be a party who isn't the addressee;
    since overhearers are in the framework, the chosen utterance is the one that
    moves THAT party, even if nominally said to someone else;
  * WHETHER TO SPEAK — silence is a candidate; if the goal is already met, saying
    nothing wins;
  * EFFICIENCY / meeting-them-where-they-are — among utterances that achieve the
    goal, the cheapest (least redundant for the target) wins, so the entity
    conveys only what's new.
Understanding, efficiency and audience-fit are INSTRUMENTAL here — they serve the
objective; the objective is the objective. Effect is modelled thinly (a party in
earshot gains the conveyed concepts); readiness / misconceptions are the next
axes. Objective satisfaction is a graph-resident judgement (`audience.knows`);
other objective kinds (get an action, change a belief) plug in as new kinds.
"""
from __future__ import annotations

from substrate_rs import _native

from domains import audience as aud

# Scene/Party/Concept + the audience edges (party/concept/knows) come from the
# participation framework; communicate adds Objective + target.
_TYPES = ("Scene", "Party", "Concept", "Objective")
_EDGES = ("party", "concept", "knows", "target")


def new_graph():
    """A native substrate whose grammar admits both the audience schema and the
    objective the communicate layer adds, since they share one graph."""
    g = _native.Substrate()
    for a in _TYPES:
        for b in _TYPES:
            for e in _EDGES:
                g.add_production({
                    "src": {"type": a, "var": "s"}, "edge_type": e,
                    "tgt": {"type": b, "var": "t"}, "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "communicate"})
    return g


def set_objective(graph, target, concept: str, kind: str = "knows") -> int:
    """The communicative goal — e.g. (kind='knows') make ``target`` know
    ``concept``. ``target`` may be ANY party in the framework, not the addressee."""
    o = graph.add_node("Objective", {"id": "obj", "kind": kind, "concept": concept})
    graph.add_edge(o, "target", target, {})
    return o


def _satisfied(graph, objective) -> bool:
    a = graph.node(objective)["attrs"]
    target = graph.neighbours(objective, "target")[0]
    if a["kind"] == "knows":
        return aud.knows(graph, target, a["concept"])
    return False


def _concept_node(graph, scene, name: str) -> int:
    for t in graph.neighbours(scene, "concept"):
        if graph.node(t)["attrs"]["name"] == name:
            return t
    n = graph.add_node("Concept", {"id": f"c_{name}", "name": name})
    graph.add_edge(scene, "concept", n, {})
    return n


def _value(graph, scene, objective, content: frozenset,
           cost_weight: float = 0.01) -> float:
    """Value of uttering ``content`` (the set of concepts conveyed; empty =
    silence): simulate the effect (every party in earshot gains those concepts),
    score the objective (graph-resident), subtract a subordinate signal cost,
    then undo the simulation. Goal achievement dominates; cost only breaks ties."""
    added = []
    for p in graph.neighbours(scene, "party"):
        for c in content:
            if not aud.knows(graph, p, c):
                cn = _concept_node(graph, scene, c)
                graph.add_edge(p, "knows", cn, {})
                added.append((p, cn))
    val = (1.0 if _satisfied(graph, objective) else 0.0) - cost_weight * len(content)
    for p, cn in added:
        graph.remove_edge(p, "knows", cn)
    return val


def choose(graph, scene, objective, candidates):
    """Pick the utterance (by conveyed-concept content) that best achieves the
    objective; silence is always a candidate. Returns (chosen_content, value).
    The chosen content is what the articulator (`language.produce`) then renders."""
    options = [frozenset()] + [frozenset(c) for c in candidates]
    best, best_v = None, None
    for c in options:
        v = _value(graph, scene, objective, c)
        if best_v is None or v > best_v:
            best, best_v = c, v
    return best, best_v
