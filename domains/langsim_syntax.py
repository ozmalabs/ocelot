"""langsim SYNTAX-CARRYING language (block 244000).

The langsim language-limitation map (block 243000) measured the substrate's
graph-resident language carrying LEXICAL content but NOT SYNTAX: comprehension
was ORDER-INSENSITIVE (a bag of grounded referents), so the scrambled control
could not fail; generation had an ARITY-2 ceiling (a ditransitive dropped the
recipient).

This module WIRES the composition/Merge stage that already exists in
``domains/language.py`` into that content path, so word ORDER carries structured
roles. It is a WORLD-ADAPTER-CLASS module (experiments/gamma-substrate/CLAUDE.md):
a graph-resident LEXICON (sign data) + MECHANICAL maps between the faculty's
structured meaning Term and an ``Intent{predicate, agent, patient, recipient}``.

  * comprehension  = ``language.comprehend(text, langsim_lexicon())`` -- the
    general, vocabulary-independent Merge RULES driven on the Rust engine. It is
    order-sensitive by construction (a left-slot binds the constituent to its
    LEFT; a right-slot to its RIGHT). Python only reads the structured Term into
    an Intent dict -- no decision.
  * generation (3-place) = ``language.produce(meaning, langsim_lexicon())`` --
    comprehension's documented inverse over the SAME signs. Surface order comes
    from each sign's arg dir/marker (graph-resident lexicon data), not a Python
    template; correctness is the ROUND-TRIP ``comprehend(produce(m)) == m``.

NO new Rust, NO new agent decision: the composition/Merge faculty already exists
and runs on the existing engine; this is lexicon data + mechanical translation.
No graph_rewrite.run / gr.run / _match / _apply / make_rule.
"""
from __future__ import annotations

from domains import language as _L

# The predicates the langsim economy speaks about. `give` is the coordination
# verb (3-place); have/need/want are 2-place informatives/requests.
_PREDICATES = ("give", "have", "need", "want")

# The speaker's self-words: an utterance's `agent` role, when the speaker refers
# to itself ("I give wood"), resolves here for the receiver (the partner offers).
_SELF_WORDS = ("I", "me")

# Resource + role nouns grounded as leaf concepts so the parser can bind them.
_NOUNS = ("I", "you", "me", "wood", "stone", "grain", "two", "three", "build")


def langsim_lexicon() -> list[dict]:
    """The langsim lexicon as graph-resident SIGN data -- the vocabulary is data,
    the Merge grammar (in language.py) is vocabulary-independent. `give` carries
    THREE argument slots so a ditransitive keeps the recipient:

        give : agent (dir L) , patient (dir R, bare) , recipient (dir R, marker 'to')
        have/need/want : agent (dir L) , patient (dir R, bare)

    A 2-place `I give wood` binds agent+patient and leaves recipient unfilled
    (fine -- an unfilled slot is simply not read); a 3-place `I give wood to you`
    binds all three. Word ORDER assigns the roles."""
    return [
        {"form": "give", "concept": "give", "args": [
            {"role": "agent", "dir": "L"},
            {"role": "patient", "dir": "R"},
            {"role": "recipient", "marker": "to", "dir": "R"}]},
        *[{"form": f, "concept": f, "args": [
            {"role": "agent", "dir": "L"},
            {"role": "patient", "dir": "R"}]} for f in ("have", "need", "want")],
        *[{"form": v, "concept": v} for v in _NOUNS],
        {"form": "to", "mark": True},
    ]


def parse_intent(text: str) -> dict | None:
    """Comprehend ``text`` via the composition/Merge faculty into a structured
    Intent ``{predicate, agent, patient, recipient}`` (a role absent from the
    parse -> None). Returns None if no predicate composes. This is a MECHANICAL
    read of the faculty's structured meaning Term -- the Merge rules did the work
    on the Rust engine; Python only projects the Term onto the four role slots."""
    for term in _L.comprehend(text, langsim_lexicon()):
        if isinstance(term, dict):
            pred = next((k for k in term if k in _PREDICATES), None)
            if pred is not None:
                roles = term[pred]
                roles = roles if isinstance(roles, dict) else {}
                return {"predicate": pred,
                        "agent": roles.get("agent"),
                        "patient": roles.get("patient"),
                        "recipient": roles.get("recipient")}
    return None


def structured_offer_holds(intent: dict | None, needs: str) -> bool:
    """The STRUCTURED role gate (replaces langsim's token-presence bag read): the
    partner (``agent``) offers (``predicate == give``) exactly the resource the
    receiver needs (``patient == needs``). A word-order scramble fails to bind the
    patient to `give` (or binds the wrong role), so the match fails -- which is
    the entire point of making syntax load-bearing. A mechanical query over the
    structured Intent; no decision."""
    if not intent:
        return False
    return (intent.get("predicate") == "give"
            and intent.get("agent") in _SELF_WORDS
            and intent.get("patient") == needs)


def render_ditransitive(agent: str, patient: str, recipient: str) -> str:
    """Produce a 3-place ditransitive surface (`agent give patient to recipient`)
    via the language faculty's inverse (``language.produce`` over the SAME signs).
    KEEPS the recipient -- the langsim arity-2 ceiling is lifted for this frame.
    Non-lossy by ROUND-TRIP, not assertion: ``parse_intent(render_...) `` recovers
    all three roles."""
    return _L.produce(
        {"give": {"agent": agent, "patient": patient, "recipient": recipient}},
        langsim_lexicon())
