"""Semantic relations — the predicate sign layer.

So far the agent's signs are either standalone ('mind', 'self', 'graph')
or unary ('know of X', 'learn of X'). That's enough to NAME things;
it isn't enough to ASSERT how they connect. Producing "process runs
on linux" or "design uses graph" needs INFIX signs with two typed
slots — left subject + right object — that produce can render as
"X verb Y" or "X verb marker Y".

This module installs a foundational set of binary relations as
Concept + Sign records, all infix. They're graph data — descriptions
on the Concept nodes, args on the Signs — so the agent can use them
in meaning Terms it constructs from its own state, and produce()
renders them through the lexicon.

Examples (after install):

  {"uses": {"left": "process", "right": "graph"}}
    → "process uses graph"
  {"runs_on": {"left": "agent", "right": "linux"}}
    → "agent runs on linux"
  {"is_a": {"left": "agent", "right": "mind"}}
    → "agent is a mind"

The set is COMPACT and FOUNDATIONAL — each relation is broadly
applicable across domains (architecture, biology, math, dialogue).
Domain-specific relations come from wiki/teaching as needed.

Reading-order conventions:

  left  → subject  (the entity the relation is "about")
  right → object   (what the subject relates to)
  marker → preposition/particle (rendered between subject and form, or
           between form and object) when the natural English form has
           one ("runs on", "depends on", "interacts with").
"""
from __future__ import annotations


_RELATIONS_MT = "relations"


# Single-word infix: produces "X verb Y".
# (form, concept_name, description)
_INFIX_RELATIONS = (
    ("uses",        "uses",
     "X uses Y as a tool, component, or means"),
    ("needs",       "needs",
     "X needs Y to function or exist"),
    ("requires",    "requires",
     "X requires Y as a precondition"),
    ("has",         "has_rel",
     "X has Y as a part, property, or possession"),
    ("implements",  "implements",
     "X implements Y as a concrete realisation of an abstraction"),
    ("extends",     "extends",
     "X extends Y by inheritance or addition"),
    ("produces",    "produces",
     "X produces Y as an output"),
    ("causes",      "causes",
     "X causes Y; X is sufficient for Y"),
    ("enables",     "enables",
     "X enables Y; X is necessary for Y"),
    ("contains",    "contains",
     "X contains Y as an element"),
    ("represents",  "represents",
     "X represents Y; X stands for Y in some encoding"),
    ("supports",    "supports",
     "X supports Y; X is a substrate for Y"),
)

# Two-arg with marker — produces "X form marker Y".
# (form, concept_name, marker, description)
_MARKED_RELATIONS = (
    ("runs",      "runs_on",        "on",
     "X runs on Y as its execution host"),
    ("depends",   "depends_on",     "on",
     "X depends on Y for correct operation"),
    ("interacts", "interacts_with", "with",
     "X interacts with Y bidirectionally"),
    ("optimised", "optimised_for",  "for",
     "X is optimised for Y as its target"),
    ("designed",  "designed_for",   "for",
     "X is designed for Y"),
    ("works",     "works_with",     "with",
     "X works with Y as a partner"),
    ("composed",  "composed_of",    "of",
     "X is composed of Y as constituents"),
)

# Taxonomic / identity relations. "is_a" is special because 'is' is a
# DROP marker in core_lexicon — production emits the form verbatim
# ("agent is_a mind"), still readable.
_TAXONOMY_RELATIONS = (
    ("is_a",      "is_a",       "X is a Y; instance-of-class"),
    ("kind_of",   "kind_of",    "X is a kind of Y; subtype"),
    ("part_of",   "part_of",    "X is part of Y; mereology"),
    ("instance_of", "instance_of", "X is an instance of Y"),
)


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def install_relations(agent) -> dict:
    """Install the relations Mt + all infix/marked/taxonomy relations
    as Concept + Sign records. Idempotent. Returns a dict of
    concept_name → NodeID for everything installed."""
    if _RELATIONS_MT not in agent._microtheory_nodes:
        agent.install_microtheory(
            _RELATIONS_MT,
            description="binary semantic relations the agent uses to "
                        "express how concepts connect",
            genl="general_knowledge")
    agent.operates_in(_RELATIONS_MT)

    out: dict = {}

    # Single-word infix: "X form Y" — args = [left, right], both
    # without markers, left is L-direction (subject before form),
    # right is R-direction (object after form).
    for form, concept_name, desc in _INFIX_RELATIONS:
        _ensure_concept(agent, concept_name, description=desc)
        out[concept_name] = agent._concept_nodes[concept_name]
        agent.learn_sign({
            "form": form, "concept": concept_name,
            "args": [{"role": "left",  "dir": "L"},
                     {"role": "right", "dir": "R"}],
        })

    # Marked: "X form marker Y" — args = [left without marker,
    # right with marker].
    for form, concept_name, marker, desc in _MARKED_RELATIONS:
        _ensure_concept(agent, concept_name, description=desc)
        out[concept_name] = agent._concept_nodes[concept_name]
        agent.learn_sign({
            "form": form, "concept": concept_name,
            "args": [{"role": "left",  "dir": "L"},
                     {"role": "right", "marker": marker, "dir": "R"}],
        })

    # Taxonomy: same shape as infix; underscored forms read OK in
    # output ("agent is_a mind").
    for form, concept_name, desc in _TAXONOMY_RELATIONS:
        _ensure_concept(agent, concept_name, description=desc)
        out[concept_name] = agent._concept_nodes[concept_name]
        agent.learn_sign({
            "form": form, "concept": concept_name,
            "args": [{"role": "left",  "dir": "L"},
                     {"role": "right", "dir": "R"}],
        })

    return out


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ensure_concept(agent, name: str, description: str = ""):
    existing = agent._concept_nodes.get(name)
    if existing is not None:
        return existing
    with agent.mind_substrate.transform() as tx:
        cid = tx.add_node("Concept",
                            {"name": name, "description": description})
        agent._concept_nodes[name] = cid
    return cid


__all__ = [
    "_INFIX_RELATIONS",
    "_MARKED_RELATIONS",
    "_RELATIONS_MT",
    "_TAXONOMY_RELATIONS",
    "install_relations",
]
