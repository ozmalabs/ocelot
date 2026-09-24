"""Conversation — the agent's graph-resident model of dialogue.

A real understanding of conversation, drawn from established theory and
installed as graph data so the agent's drives can reason over it.

Theoretical sources installed as structure:

  Speech Act Theory                       Searle (1969, 1979)
    Five illocutionary classes:
      Assertive   — commit to truth                (statement, answer)
      Directive   — get hearer to do / tell        (question, request, command)
      Commissive  — commit speaker to future       (promise, offer)
      Expressive  — psychological state            (greeting, apology, thanks)
      Declarative — change institutional reality   (announce, name)

  Adjacency Pairs                         Sacks, Schegloff, Jefferson (1974)
    A first-pair-part MAKES RELEVANT a second-pair-part of a specific
    type. Question → Answer, Greeting → Greeting, Request → Grant/Refuse,
    Offer → Accept/Decline, Summons → Answer. When the first part lands
    in the conversation, the SECOND is conditionally relevant — its
    absence is itself noticeable (an "absent answer" is information).

  Common Ground                           Clark (1996)
    The mutually-believed propositions a conversation accumulates.
    Grows through presentation + acceptance + registration. Used to
    avoid repeating known content + ground deictic / anaphoric refs.

  Cooperative Principle + Maxims          Grice (1975)
    Quantity — be as informative as required, no more.
    Quality  — be truthful; don't say what you lack evidence for.
    Relation — be relevant to the topic + turn.
    Manner   — be perspicuous; avoid obscurity, ambiguity, prolixity.

  Repair                                  Schegloff, Jefferson, Sacks (1977)
    Self vs other initiation × self vs other completion: four cells.
    Self-initiated self-repair is most common; other-initiated
    self-repair ("what do you mean?") is the conversational mechanism
    for handling miscomprehension.

  Turn-taking + TRPs                      Sacks, Schegloff, Jefferson (1974)
    Conversation is ordered by Transition Relevance Places where a
    speaker change can occur. The current_speaker attr on the Channel
    flips at each turn; the agent's argmax cares about whose turn it
    is (act when it is, listen when it isn't).

Each of these is installed as Concepts + relations the agent can read.
Adjacency pairs become a graph table (first-pair-part Concept →
second-pair-part Concept) the agent walks when an inbound Message
lands, auto-creating a response communicate-goal of the right kind.
The pragmatics of WHEN the agent speaks is goal-arbitration; the
content is produce(meaning, lexicon); none of it is Python templates.

install_conversation(agent) is idempotent; the chat calls it on attach.
"""
from __future__ import annotations

from substrate import NodePattern, Production


_CONVERSATION_MT = "conversation"


# ---------------------------------------------------------------------------
# Searle's illocutionary taxonomy — five parent classes, specific
# speech acts hang under them as subtypes
# ---------------------------------------------------------------------------

_SEARLE_CLASSES = (
    "assertive",      # commit to truth of a proposition
    "directive",      # get hearer to do or tell
    "commissive",     # commit speaker to a future course
    "expressive",     # convey a psychological state
    "declarative",    # change institutional reality through utterance
)

# Specific speech-act concepts. Each maps to its Searle class via
# instance_of (CYC-shaped), so the agent can query both the specific
# act and its illocutionary class.
_SPEECH_ACTS = (
    # (act_name, searle_class, description)
    ("statement",      "assertive",  "asserts a proposition is true"),
    ("answer",         "assertive",  "supplies info responsive to a question"),
    ("acknowledgment", "assertive",  "registers receipt of a prior turn"),
    ("question",       "directive",  "asks the hearer for information"),
    ("inquiry",        "directive",  "asks specifically about an unknown"),
    ("request",        "directive",  "asks the hearer to do something"),
    ("clarification",  "directive",  "asks for refinement of a prior turn"),
    ("offer",          "commissive", "commits speaker to a future act if accepted"),
    ("promise",        "commissive", "commits speaker unconditionally"),
    ("greeting",       "expressive", "social opener / closer"),
    ("thanks",         "expressive", "gratitude"),
    ("apology",        "expressive", "regret for an act or state"),
    ("announce",       "declarative", "makes something institutionally so"),
)


# ---------------------------------------------------------------------------
# Adjacency pairs — first-pair-part → expected second-pair-part(s)
# (Sacks, Schegloff, Jefferson 1974). The second is "conditionally
# relevant" once the first lands; its absence is meaningful in itself.
# ---------------------------------------------------------------------------

# Each entry: (first_pair_part, second_pair_part, preferred_alt).
# preferred_alt is the dispreferred alternative (Pomerantz preference
# structure). None when only one normal second exists. We install both
# as graph data; the agent's goal-arbitration can later prefer the
# "preferred" alt when other things are equal.
_ADJACENCY_PAIRS = (
    ("question",      "answer",        "non_answer"),
    ("inquiry",       "answer",        "non_answer"),
    ("greeting",      "greeting",      None),
    ("statement",     "acknowledgment", None),
    ("request",       "grant",         "refusal"),
    ("offer",         "acceptance",    "decline"),
    ("clarification", "answer",        None),
    ("thanks",        "acknowledgment", None),
    ("apology",       "acknowledgment", None),
)


# ---------------------------------------------------------------------------
# Grice's maxims — installed as named concepts the agent can query.
# Used as goal-priority weights at communicate-action selection time.
# ---------------------------------------------------------------------------

_GRICE_MAXIMS = (
    ("quantity",  "be as informative as required, no more"),
    ("quality",   "say only what you believe; have evidence"),
    ("relation",  "be relevant to the topic and turn"),
    ("manner",    "be perspicuous — clear, brief, orderly, unambiguous"),
)


# ---------------------------------------------------------------------------
# Repair mechanisms — four cells of {self,other} × {initiate,complete}
# ---------------------------------------------------------------------------

_REPAIR_KINDS = (
    "self_initiated_self_repair",
    "self_initiated_other_repair",
    "other_initiated_self_repair",
    "other_initiated_other_repair",
)


# ---------------------------------------------------------------------------
# Conversational vocabulary — Concept+Sign records so the agent can
# RENDER meanings about knowing, learning, saying, agreement etc. via
# the graph-native produce(meaning, lexicon) engine.
# ---------------------------------------------------------------------------

_CONVERSATIONAL_SIGNS = (
    # cognitive-state verbs the agent uses to talk about ITSELF
    ("know",       "know",       [{"role": "of", "marker": "of", "dir": "R"}]),
    ("learn",      "learn",      [{"role": "of", "marker": "of", "dir": "R"}]),
    ("understand", "understand", [{"role": "of", "marker": "of", "dir": "R"}]),
    ("think",      "think",      [{"role": "of", "marker": "of", "dir": "R"}]),
    # communicative-act verbs
    ("tell",       "tell",       [{"role": "of", "marker": "of", "dir": "R"}]),
    ("say",        "say",        [{"role": "of", "marker": "of", "dir": "R"}]),
    ("ask",        "ask",        [{"role": "of", "marker": "about",
                                   "dir": "R"}]),
    ("answer",     "answer",     [{"role": "of", "marker": "of", "dir": "R"}]),
    # standalone affirmation / negation / acknowledgment
    ("yes",        "yes",        []),
    ("no",         "no",         []),
    ("hello",      "hello",      []),
    # CONJUNCTIONS — chain multiple concepts in a meaning Term.
    # "and" is the basic additive coordinator; nested produces
    # "A and B and C" via right-recursion.
    ("and",        "and_conj",   [{"role": "left",  "dir": "L"},
                                    {"role": "right", "dir": "R"}]),
    ("with",       "with_rel",   [{"role": "left",  "dir": "L"},
                                    {"role": "right", "dir": "R"}]),
    ("for",        "for_rel",    [{"role": "left",  "dir": "L"},
                                    {"role": "right", "dir": "R"}]),
    ("on",         "on_rel",     [{"role": "left",  "dir": "L"},
                                    {"role": "right", "dir": "R"}]),
)


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def install_conversation(agent) -> dict:
    """Install the conversation Mt + speech-act taxonomy + adjacency-pair
    structure + Grice maxims + repair concepts + conversational signs.
    Returns a flat dict of NodeIDs for the concepts installed.
    """
    if _CONVERSATION_MT not in agent._microtheory_nodes:
        agent.install_microtheory(
            _CONVERSATION_MT,
            description="the agent's model of dialogue",
            genl="general_knowledge")
    agent.operates_in(_CONVERSATION_MT)

    grammar = agent.mind_substrate.checker.grammar
    # Message-level edges
    for src, edge, tgt, prov in (
        ("Message", "has_speech_act", "Concept",
         "meta:Message-has_speech_act-Concept"),
        ("Message", "responds_to", "Message",
         "meta:Message-responds_to-Message"),
        # Concept-level taxonomy edges
        ("Concept", "subtype_of", "Concept",
         "meta:Concept-subtype_of-Concept"),
        ("Concept", "expects_response", "Concept",
         "meta:Concept-expects_response-Concept (adjacency pair)"),
        ("Concept", "preferred_over", "Concept",
         "meta:Concept-preferred_over-Concept (preference)"),
        # Common ground accumulates on the Channel
        ("Channel", "common_ground_concept", "Concept",
         "meta:Channel-common_ground_concept-Concept"),
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

    # Searle classes
    for cls in _SEARLE_CLASSES:
        out[cls] = _ensure_concept(
            agent, cls, description=f"Searle illocutionary class: {cls}")

    # Specific speech acts, each subtyped under its Searle class
    for act, cls, desc in _SPEECH_ACTS:
        cid = _ensure_concept(agent, act, description=desc)
        out[act] = cid
        _ensure_edge(agent, cid, "subtype_of", out[cls])

    # Adjacency pairs — link first-pair-part → second-pair-part
    # via expects_response. preferred_over for preference pairs.
    for first, second, dispref in _ADJACENCY_PAIRS:
        f_id = out.get(first)
        s_id = _ensure_concept(agent, second,
                                description=f"second-pair-part: {second}")
        out.setdefault(second, s_id)
        if f_id is not None:
            _ensure_edge(agent, f_id, "expects_response", s_id)
        if dispref is not None:
            d_id = _ensure_concept(agent, dispref,
                                     description=f"dispreferred alt: {dispref}")
            out.setdefault(dispref, d_id)
            _ensure_edge(agent, s_id, "preferred_over", d_id)

    # Grice maxims
    grice_parent = _ensure_concept(
        agent, "cooperative_principle",
        description="Grice's overarching principle")
    out["cooperative_principle"] = grice_parent
    for maxim, desc in _GRICE_MAXIMS:
        mid = _ensure_concept(agent, maxim, description=desc)
        out[maxim] = mid
        _ensure_edge(agent, mid, "subtype_of", grice_parent)

    # Repair concepts
    repair_parent = _ensure_concept(
        agent, "repair",
        description="conversational mechanism for handling trouble")
    out["repair"] = repair_parent
    for kind in _REPAIR_KINDS:
        rid = _ensure_concept(agent, kind,
                                description=f"repair kind: {kind}")
        out[kind] = rid
        _ensure_edge(agent, rid, "subtype_of", repair_parent)

    # Conversational signs — Concept + Sign in the agent's default
    # lexicon so produce() can render meanings about these acts.
    # 'and' / 'with' / 'for' / 'on' are already installed as
    # function-word markers (kind=mark) by core_lexicon — learn_sign
    # dedupes by form and overriding the parser's view of them is
    # invasive. The conjunction concepts (and_conj etc.) are
    # installed below for future use; multi-concept chaining needs
    # the marker-vs-concept conflict resolved in the parser/producer.
    for form, concept_name, args in _CONVERSATIONAL_SIGNS:
        if form in ("and", "with", "for", "on"):
            # only create the Concept; skip the Sign install since
            # the marker would shadow it and we'd break parsing
            _ensure_concept(
                agent, concept_name,
                description=f"conversational concept: {concept_name}")
            continue
        _ensure_concept(agent, concept_name,
                          description=f"conversational concept: {concept_name}")
        sign: dict = {"form": form, "concept": concept_name}
        if args:
            sign["args"] = args
        agent.learn_sign(sign)

    return out


# ---------------------------------------------------------------------------
# query helpers — graph reads the agent (and chat) can use
# ---------------------------------------------------------------------------

def expected_response_kind(agent, first_act: str) -> str | None:
    """For a speech-act name (e.g. 'question'), return the name of the
    expected second-pair-part ('answer'). Reads the expects_response
    edge — graph query, not a Python lookup table.
    """
    first_id = agent._concept_nodes.get(first_act)
    if first_id is None:
        return None
    for e in agent.mind_graph.out_edges(first_id, "expects_response"):
        return agent.mind_graph.node(e.key.tgt).attrs.get("name")
    return None


def add_to_common_ground(agent, channel_id, concept_id) -> None:
    """Append a concept to the Channel's common-ground accumulator.
    Idempotent — common ground is set-like."""
    for e in agent.mind_graph.out_edges(channel_id, "common_ground_concept"):
        if e.key.tgt == concept_id:
            return
    with agent.mind_substrate.transform() as tx:
        tx.add_edge(channel_id, "common_ground_concept", concept_id)


def common_ground(agent, channel_id) -> list:
    """The concepts established as mutually known in this conversation.
    Used to avoid restating + to ground deictic references."""
    return [e.key.tgt for e in
            agent.mind_graph.out_edges(channel_id, "common_ground_concept")]


# ---------------------------------------------------------------------------
# speech-act classification at the I/O boundary
# ---------------------------------------------------------------------------

_QUESTION_LEADS = frozenset([
    "what", "who", "where", "when", "why", "how", "which",
    "is", "are", "was", "were", "do", "does", "did",
    "can", "could", "will", "would", "should", "may", "might",
    "tell", "have",
])

_GREETING_FORMS = frozenset([
    "hello", "hi", "hey", "greetings", "good morning",
    "good afternoon", "good evening",
])

_THANKS_FORMS = frozenset([
    "thanks", "thank you", "thx",
])

_IMPERATIVE_LEADS = frozenset([
    "read", "write", "run", "execute", "open", "show",
])


def classify_speech_act(text: str) -> str:
    """Classify ``text`` into a speech-act name. The classifier is at
    the I/O BOUNDARY — the agent's structural model is the graph data
    we write into, not the classifier itself. Surface cues only."""
    s = text.strip()
    if not s:
        return "statement"
    low = s.lower()
    head = low.split(None, 1)[0]
    # Greeting / thanks heuristics — fixed expressives
    if low in _GREETING_FORMS or head in _GREETING_FORMS:
        return "greeting"
    if low in _THANKS_FORMS or head in _THANKS_FORMS:
        return "thanks"
    # Question via punctuation or interrogative lead
    if s.endswith("?") or head in _QUESTION_LEADS:
        return "question"
    # Imperative — agent treats these as routable acts; they're
    # directive in Searle's sense but the agent's existing capability
    # Frames handle them as if they were function-of-subject queries
    if head in _IMPERATIVE_LEADS:
        return "request"
    return "statement"


__all__ = [
    "_ADJACENCY_PAIRS",
    "_CONVERSATION_MT",
    "_REPAIR_KINDS",
    "_SEARLE_CLASSES",
    "_SPEECH_ACTS",
    "add_to_common_ground",
    "classify_speech_act",
    "common_ground",
    "expected_response_kind",
    "install_conversation",
]


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


def _ensure_edge(agent, src_id, edge_type: str, tgt_id) -> None:
    """Idempotent edge insert (no duplication)."""
    for e in agent.mind_graph.out_edges(src_id, edge_type):
        if e.key.tgt == tgt_id:
            return
    with agent.mind_substrate.transform() as tx:
        tx.add_edge(src_id, edge_type, tgt_id)
