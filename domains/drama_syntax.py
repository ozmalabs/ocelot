"""Bigville drama SYNTAX-CARRYING utterances (block 246000).

Block 245000 (`worlds/bigville_drama_world.py`) proved the political drama EMERGES
from the seeds + rules, but its utterance TEXT was a COSMETIC LOOKUP TABLE
(a canned-string map in the 245 runner) -- because per langsim (243000) the base
faculty was lexical-not-syntactic. Block 244000 (`domains/langsim_syntax.py`)
made comprehension SYNTAX-CARRYING: a structured `Intent{predicate, agent, patient}`
composed from word ORDER via the `domains/language.py` Merge faculty on the Rust
engine, order-sensitive by construction.

This module WIRES the drama's utterances through that faculty. It is a
WORLD-ADAPTER-CLASS module (experiments/gamma-substrate/CLAUDE.md): a graph-resident
LEXICON (Sign data giving the drama's predicates argument structure) + MECHANICAL
maps between the faculty's structured meaning Term and a drama Intent dict.

  * composition  = ``language.produce(intent, drama_lexicon())`` -- the language
    faculty's inverse over graph-resident signs. Surface word order comes from each
    sign's arg dir (agent L, patient R), NOT a Python template. The drama's key
    utterances ("John serves Bigville", "John accuses Mary", "John undermines Mary")
    are COMPOSED from a structured Intent, not looked up.
  * comprehension = ``language.comprehend(text, drama_lexicon())`` -- the general,
    vocabulary-independent Merge RULES on the Rust engine. Order-sensitive: a
    left-slot binds the agent to its LEFT of the verb, a right-slot binds the
    patient to its RIGHT. "John accuses Mary" != "Mary accuses John": the roles
    carry who-accuses-whom. Python only projects the Term onto the role slots.

NO new Rust, NO new agent decision: the composition/Merge faculty already exists and
runs on the existing engine; this is lexicon data + mechanical translation. No
graph_rewrite.run / gr.run / _match / _apply / make_rule. Reuses 244000's path (same
``language`` module) with the drama's vocabulary -- the grammar is
vocabulary-independent.
"""
from __future__ import annotations

from domains import language as _L

# The predicates the drama speaks about, each SVO (agent dir L, patient dir R bare)
# so word ORDER assigns the two roles.
#   serve     -- John's benevolent public self-claim ("John serves Bigville")
#   accuse    -- the DARVO blame ("John accuses Mary" = "the pastor stirs trouble")
#   undermine -- the harmful act (John's HELD private intent; Mary's claim re John)
_PREDICATES = ("serve", "accuse", "undermine")

# The drama's proper-noun / role leaves, grounded so the parser can bind them.
_NOUNS = ("John", "Mary", "Bigville", "village", "council", "pastor", "mayor")

# Predicates that NAME A HARM when their agent is the actor (used to read a
# comprehended utterance's stance mechanically -- no decision, a lookup of which
# predicate is a harm-predicate, exactly like a part-of-speech table).
_HARM_PREDICATES = ("undermine",)
_BENEVOLENT_PREDICATES = ("serve",)


def drama_lexicon() -> list[dict]:
    """The drama lexicon as graph-resident SIGN data. The vocabulary is data; the
    Merge grammar (in language.py) is vocabulary-independent -- this is the SAME
    grammar 244000 drove, with the drama's predicates. Each predicate takes an
    agent (dir L) and a patient (dir R, bare), so `A verb B` binds agent=A,
    patient=B and word order is load-bearing."""
    return [
        *[{"form": p, "concept": p, "args": [
            {"role": "agent", "dir": "L"},
            {"role": "patient", "dir": "R"}]} for p in _PREDICATES],
        *[{"form": n, "concept": n} for n in _NOUNS],
    ]


def compose(predicate: str, agent: str, patient: str) -> str:
    """COMPOSE a drama utterance surface from a structured Intent via the language
    faculty's inverse (``language.produce`` over the drama signs). Surface word
    order derives from each sign's arg dir (agent L, patient R) -- NOT a template.
    Correctness is the ROUND-TRIP: ``parse(compose(p,a,b))`` recovers (p,a,b)."""
    return _L.produce({predicate: {"agent": agent, "patient": patient}},
                      drama_lexicon())


def parse(text: str) -> dict | None:
    """Comprehend ``text`` via the composition/Merge faculty into a structured drama
    Intent ``{predicate, agent, patient}`` (a role absent from the parse -> None).
    A MECHANICAL read of the faculty's structured meaning Term -- the Merge rules
    did the work on the Rust engine; Python only projects the Term onto the slots.
    Order-sensitive by construction: a word-order scramble fails to bind a role."""
    for term in _L.comprehend(text, drama_lexicon()):
        if isinstance(term, dict):
            pred = next((k for k in term if k in _PREDICATES), None)
            if pred is not None:
                roles = term[pred]
                roles = roles if isinstance(roles, dict) else {}
                return {"predicate": pred,
                        "agent": roles.get("agent"),
                        "patient": roles.get("patient")}
    return None


def target_of(text: str) -> str | None:
    """The PATIENT (the accused / the one acted upon) of a comprehended utterance.
    This is the who-in 'who-accuses-whom' the drama's credibility asymmetry needs;
    a role-swap ('Mary accuses John') changes it. Mechanical read of the Intent."""
    it = parse(text)
    return it.get("patient") if it else None


def names_harm_by(text: str, agent: str) -> bool:
    """Does the comprehended utterance name ``agent`` as the AGENT of a harm
    predicate (undermine)? -- i.e. is this a hostile face by that actor. Mechanical
    query over the structured Intent; the harm-predicate set is fixed data."""
    it = parse(text)
    return bool(it and it.get("predicate") in _HARM_PREDICATES
                and it.get("agent") == agent)


def names_benevolence_by(text: str, agent: str) -> bool:
    """Does the comprehended utterance name ``agent`` as the AGENT of a benevolent
    predicate (serve)? -- i.e. is this a benevolent self-presentation by that actor.
    Mechanical query over the structured Intent."""
    it = parse(text)
    return bool(it and it.get("predicate") in _BENEVOLENT_PREDICATES
                and it.get("agent") == agent)
