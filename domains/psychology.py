"""Psychology — basic mental-state concepts the agent needs to KNOW
about its own mind.

The agent already DOES theory of mind work — it maintains a model of
the interlocutor's beliefs (Interlocutor.believed_concepts), it tracks
its own goals (desires), it recognises others' speech acts as
intentional categories — but it has no concepts for any of this. It
does the work without knowing what the work is. This module installs
the missing vocabulary as graph data, and links the agent's existing
capabilities to the concepts so the agent can introspect "I have
theory of mind" as a real graph query.

Concepts installed:

  mental_state — parent class. Anything in this taxonomy is a
                 mental state.
    belief         — a proposition the agent takes to be true
    desire         — a wanted state of affairs (the agent's GOALS are
                     these)
    intention      — a commitment to a course of action
    knowledge      — belief plus grounding (one is knowing iff one's
                     belief is grounded)
    perception     — an experiential mental state caused by sensing
    attention      — selective focus of cognitive resources
    awareness      — being conscious of something
    emotion        — affective mental state
    expectation    — anticipation about future state

  mind, self, other — the agent / interlocutor as MINDS, not just
                      entities
  perspective — a viewpoint on the world (one mind's perspective is
                distinct from another's; the heart of ToM)
  attribution — assigning a mental state to a mind
  theory_of_mind — the meta-capability of attributing mental states
                   to others, distinguishing one's own mental states
                   from another's. Sources: Premack & Woodruff (1978),
                   Wimmer & Perner false-belief task (1983), Baron-
                   Cohen mindblindness (1995).

Capability links (the agent's own machinery → the concept that names
what it's doing):

  Interlocutor.believed_concepts → demonstrates: attribution +
                                                  belief +
                                                  theory_of_mind
  agent's goal nodes              → demonstrates: desire + intention
  speech_act subtypes             → demonstrates: intention
  agent.addressee edge            → demonstrates: other + perspective

When the agent reasons over "do I have theory_of_mind?" it walks
these demonstrates edges and finds: yes, my graph has machinery
matching the theory_of_mind concept.

install_psychology(agent) is idempotent.
"""
from __future__ import annotations

from substrate import NodePattern, Production


_PSYCHOLOGY_MT = "psychology"


# Mental-state taxonomy. Each entry: (name, description).
_MENTAL_STATE_PARENT = "mental_state"

_MENTAL_STATES = (
    ("belief",      "proposition the holder takes to be true"),
    ("desire",      "wanted state of affairs (the agent's goals are these)"),
    ("intention",   "commitment to a course of action"),
    ("knowledge",   "grounded belief"),
    ("perception",  "experiential state caused by sensing the world"),
    ("attention",   "selective focus of cognitive resources"),
    ("awareness",   "being conscious of something"),
    ("emotion",     "affective mental state"),
    ("expectation", "anticipation about future state"),
)

# Mind concepts — entities that bear mental states.
_MIND_CONCEPTS = (
    ("mind",        "the bearer of mental states"),
    ("self",        "the mind whose perspective is this agent's own"),
    ("other",       "a mind distinct from self"),
    ("perspective", "a mind's viewpoint on the world; the heart of ToM"),
    ("viewpoint",   "alias of perspective"),
)

# Theory of mind + attribution — the meta-capability.
_TOM_CONCEPTS = (
    ("attribution",
     "assigning a mental state to a mind"),
    ("theory_of_mind",
     "attributing mental states to others; distinguishing own from other's; "
     "Premack & Woodruff 1978, Wimmer & Perner 1983, Baron-Cohen 1995"),
    ("false_belief",
     "another mind's belief that diverges from one's own — the canonical ToM test"),
)

# Verb signs — let the agent talk about minds, beliefs, desires.
# Each is a Sign with form, concept name, and arg structure.
# Patterns:
#   "X believes Y"     — left subject (the believer), right object (the belief)
#   "X wants Y"        — same shape
#   "I am aware of Y"  — predicate-of-subject (no right object)
_MENTAL_VERB_SIGNS = (
    # "X believes Y" with marker-free right object
    ("believe", "believe", [{"role": "of", "marker": "of", "dir": "R"}]),
    ("want",    "want",    [{"role": "of", "marker": "of", "dir": "R"}]),
    ("intend",  "intend",  [{"role": "of", "marker": "of", "dir": "R"}]),
    ("perceive","perceive",[{"role": "of", "marker": "of", "dir": "R"}]),
    ("see",     "see",     [{"role": "of", "marker": "of", "dir": "R"}]),
    ("hear",    "hear",    [{"role": "of", "marker": "of", "dir": "R"}]),
    ("feel",    "feel",    [{"role": "of", "marker": "of", "dir": "R"}]),
    ("attend",  "attend",  [{"role": "of", "marker": "to", "dir": "R"}]),
    ("expect",  "expect",  [{"role": "of", "marker": "of", "dir": "R"}]),
)


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def install_psychology(agent) -> dict:
    """Install the psychology Mt, mental-state taxonomy, mind concepts,
    theory-of-mind concept, and the verb signs that let the agent
    express mental states via produce(). Also links the agent's
    existing capabilities (addressee, believed_concepts on the
    interlocutor, goals, speech acts) to the matching concepts via
    `demonstrates` edges — so the agent's introspection over its own
    graph can find "yes, I have theory_of_mind" as a real result.
    """
    if _PSYCHOLOGY_MT not in agent._microtheory_nodes:
        agent.install_microtheory(
            _PSYCHOLOGY_MT,
            description="basic psychology: mental states, mind, theory of mind",
            genl="general_knowledge")
    agent.operates_in(_PSYCHOLOGY_MT)

    grammar = agent.mind_substrate.checker.grammar
    # Productions we need: subtype_of (already in conversation Mt),
    # demonstrates (Concept ↔ Capability/Edge it implements).
    for src, edge, tgt, prov in (
        ("Concept", "subtype_of", "Concept",
         "meta:Concept-subtype_of-Concept"),
        ("Concept", "demonstrates", "Concept",
         "meta:Concept-demonstrates-Concept (psychology link)"),
        ("Agent", "has_mind", "Concept",
         "meta:Agent-has_mind-Concept"),
        ("Interlocutor", "has_mind", "Concept",
         "meta:Interlocutor-has_mind-Concept"),
    ):
        try:
            grammar.add(Production(
                src=NodePattern(src, "src"),
                edge_type=edge,
                tgt=NodePattern(tgt, "tgt"),
                provenance=prov))
        except Exception:
            pass

    out: dict = {}

    # Mental-state taxonomy
    parent_id = _ensure_concept(
        agent, _MENTAL_STATE_PARENT,
        description="parent class for mental states")
    out[_MENTAL_STATE_PARENT] = parent_id
    for name, desc in _MENTAL_STATES:
        cid = _ensure_concept(agent, name, description=desc)
        out[name] = cid
        _ensure_edge(agent, cid, "subtype_of", parent_id)

    # Mind concepts
    for name, desc in _MIND_CONCEPTS:
        out[name] = _ensure_concept(agent, name, description=desc)

    # Theory of mind + attribution + false belief
    for name, desc in _TOM_CONCEPTS:
        out[name] = _ensure_concept(agent, name, description=desc)

    # Capability links — the agent's existing machinery → the concept it
    # implements. These are the lines the agent's introspection walks
    # when asked "do I have X?" — for X in {belief, desire, intention,
    # theory_of_mind, perspective}, the demonstrates edges find the
    # graph machinery already doing the work.
    #
    # Belief: the Interlocutor's believed_concepts attribute. We point
    # the 'belief' concept at the 'interlocutor' concept (already
    # installed by conversation) to record the demonstration.
    inter_concept = _ensure_concept(
        agent, "interlocutor",
        description="the other entity in a conversation")
    out["interlocutor"] = inter_concept
    _ensure_edge(agent, out["belief"], "demonstrates", inter_concept)

    # Desire: the agent's own Goal nodes. Point 'desire' at a 'goal'
    # concept (placeholder if not present).
    goal_concept = _ensure_concept(
        agent, "goal",
        description="a desired state of affairs the agent pursues")
    out["goal"] = goal_concept
    _ensure_edge(agent, out["desire"], "demonstrates", goal_concept)

    # Intention: the speech-act 'intention' (Searle's illocutionary
    # force). If the conversation Mt's speech_act concept is present,
    # link intention to it.
    sa_concept = agent._concept_nodes.get("speech_act")
    if sa_concept is not None:
        _ensure_edge(agent, out["intention"], "demonstrates", sa_concept)

    # Theory of mind: the meta-capability. Demonstrated by the
    # combination of (other ↔ addressee), (belief ↔ believed_concepts),
    # (perspective ↔ the agent treating its own state vs the
    # interlocutor's state as distinct).
    _ensure_edge(agent, out["theory_of_mind"], "demonstrates", out["belief"])
    _ensure_edge(agent, out["theory_of_mind"], "demonstrates",
                  out["attribution"])
    _ensure_edge(agent, out["theory_of_mind"], "demonstrates",
                  out["perspective"])

    # Mental-state verb signs — Concept nodes + Sign in the agent's
    # default lexicon so produce(meaning, lex) can render:
    #   {"believe": {"of": <thing>}}  → "believe of <thing>"
    for form, concept_name, args in _MENTAL_VERB_SIGNS:
        _ensure_concept(agent, concept_name,
                          description=f"mental verb: {concept_name}")
        sign: dict = {"form": form, "concept": concept_name}
        if args:
            sign["args"] = args
        agent.learn_sign(sign)

    # Deictic self-reference: "you" (in user → agent direction) and
    # "I" / "me" (in agent → user direction) both refer to the agent's
    # SELF. Rebind those signs so comprehension yields self-concepts
    # the agent can introspect on. learn_sign would refuse to overwrite
    # an existing sign, so use _retarget_sign which updates the
    # denotes edge directly.
    _retarget_sign(agent, "you", "self")
    _retarget_sign(agent, "your", "self")
    _retarget_sign(agent, "i", "self")
    _retarget_sign(agent, "me", "self")
    _retarget_sign(agent, "my", "self")

    # Identity question Frame: "what are you" / "who are you" routes
    # to describe_self. The realised concept is 'describe_self'; the
    # capability lives in runtime_capabilities (set up by
    # install_self_capabilities below).
    _ensure_concept(agent, "describe_self",
                      description="report the agent's identity")
    agent.install_frame(
        name="self_identity_query_frame",
        evoked_by=["what are you", "who are you", "what am i",
                   "tell me about you", "tell me about yourself",
                   "describe yourself"],
        realised_by="describe_self",
        holds_in=_PSYCHOLOGY_MT,
        core_elements=[],
        binding_pattern="predicate_of_subject")

    install_self_capabilities(agent)

    return out


def _retarget_sign(agent, form: str, concept_name: str) -> None:
    """Point an existing Sign's denotes edge at ``concept_name`` (a
    Concept that must already exist). Idempotent. Adds the sign if
    absent."""
    from domains.language import signs_from_graph
    lex = agent._ensure_lexicon()
    sign_node = None
    for e in agent.mind_graph.out_edges(lex, "entry"):
        if (agent.mind_graph.node(e.key.tgt).attrs.get("form")
                == form):
            sign_node = e.key.tgt
            break
    if sign_node is None:
        # No sign yet — install one fresh
        if concept_name not in agent._concept_nodes:
            _ensure_concept(agent, concept_name)
        agent.learn_sign({"form": form, "concept": concept_name})
        return
    # Sign exists — update its denotes edge to point at the new concept
    target_cid = agent._concept_nodes.get(concept_name)
    if target_cid is None:
        _ensure_concept(agent, concept_name)
        target_cid = agent._concept_nodes[concept_name]
    # remove existing denotes edges, then add new one
    existing = list(agent.mind_graph.out_edges(sign_node, "denotes"))
    for e in existing:
        if e.key.tgt == target_cid:
            return                       # already correct
    with agent.mind_substrate.transform() as tx:
        for e in existing:
            try:
                tx.remove_edge(sign_node, "denotes", e.key.tgt)
            except Exception:
                pass
        tx.add_edge(sign_node, "denotes", target_cid)
    # also update the sign node's concept attribute so downstream
    # signs_from_graph reads the right concept name
    agent.mind_graph.node(sign_node).attrs["concept"] = concept_name


# ---------------------------------------------------------------------------
# self capability — graph-resident introspection that returns a meaning
# ---------------------------------------------------------------------------

def install_self_capabilities(agent) -> None:
    """Wire describe_self into runtime_capabilities. Returns a meaning
    Term (not text) — the chat renders via produce(). The meaning
    structure references the most identifying concepts the agent has
    grounded for itself: 'mind' (it bears mental states) plus 'self'."""
    def describe_self(_args: dict) -> dict:
        """Returns a meaning Term about the agent. Bounded by what
        concepts the agent has signs for — produce() will render
        whatever pieces it can express."""
        # For the moment: bare 'mind' — the agent is a mind. Richer
        # self-description meanings (chains via has_theory_of_mind /
        # operates_in / etc.) require composing signs that don't yet
        # exist in the lexicon. As the lexicon grows, this can return
        # a richer meaning.
        return {"mind": {}}

    original = agent.runtime_capabilities
    new_caps = {"describe_self": describe_self}

    def merged():
        out = dict(original())
        out.update(new_caps)
        return out

    merged._gamma_psychology = True       # type: ignore[attr-defined]
    agent.runtime_capabilities = merged


# ---------------------------------------------------------------------------
# query helpers
# ---------------------------------------------------------------------------

def has_theory_of_mind(agent) -> bool:
    """Returns True iff the agent's graph contains the theory_of_mind
    concept AND the demonstrates edges pointing at the underlying
    capabilities (attribution + belief + perspective). The agent CAN
    use this to introspect whether it has ToM."""
    tom = agent._concept_nodes.get("theory_of_mind")
    if tom is None:
        return False
    needed = {"belief", "attribution", "perspective"}
    demonstrated = set()
    for e in agent.mind_graph.out_edges(tom, "demonstrates"):
        attrs = agent.mind_graph.node(e.key.tgt).attrs
        name = attrs.get("name")
        if name in needed:
            demonstrated.add(name)
    return demonstrated == needed


def mental_states(agent) -> list[str]:
    """Names of mental-state concepts installed on this agent."""
    parent = agent._concept_nodes.get(_MENTAL_STATE_PARENT)
    if parent is None:
        return []
    names = []
    # walk in-edges with subtype_of
    for e in agent.mind_graph.in_edges(parent, "subtype_of"):
        nm = agent.mind_graph.node(e.key.src).attrs.get("name")
        if nm:
            names.append(nm)
    return sorted(names)


__all__ = [
    "_PSYCHOLOGY_MT",
    "_MENTAL_STATE_PARENT",
    "_MENTAL_STATES",
    "_MIND_CONCEPTS",
    "_TOM_CONCEPTS",
    "has_theory_of_mind",
    "install_psychology",
    "mental_states",
]


# ---------------------------------------------------------------------------
# helpers (kept duplicated from conversation.py so this module stands alone)
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


def _ensure_edge(agent, src_id, edge_type: str, tgt_id) -> None:
    for e in agent.mind_graph.out_edges(src_id, edge_type):
        if e.key.tgt == tgt_id:
            return
    with agent.mind_substrate.transform() as tx:
        tx.add_edge(src_id, edge_type, tgt_id)
