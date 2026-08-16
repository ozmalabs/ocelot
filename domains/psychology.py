"""Psychology — basic mental-state concepts the agent needs to KNOW
about its own mind.

RETIRED (TOM_SYSTEM_UNIFICATION_RESULTS.md, this session): the
`install_psychology`/`install_self_capabilities`/`_retarget_sign`/
`has_theory_of_mind`/`mental_states`/`_ensure_concept`/`_ensure_edge`
functions this module originally defined were CuriousAgent-era Python
(`agent.mind_graph`, `agent._concept_nodes`, `agent.mind_substrate.
transform()`, `agent.install_microtheory`, `agent.operates_in`,
`agent.learn_sign`, `agent.runtime_capabilities` — none of which
`WorldAdapter`, the current agent, exposes; `CuriousAgent` itself was
deleted 2026-06-18). Confirmed dead before removal, not assumed: their
only caller was `domains/arc3_full_seed.py` (itself unreferenced by any
live test, importable only from `scripts/arc_archive/*`, and independently
broken — 11 further CuriousAgent-only calls of its own). Removed rather
than left to bit-rot; `_MENTAL_VERB_SIGNS` (the Sign data those functions
installed) went with them since nothing else read it.

**What remains and is LIVE**: the taxonomy CONSTANTS below
(`_MENTAL_STATES`, `_MENTAL_STATE_PARENT`, `_MIND_CONCEPTS`,
`_TOM_CONCEPTS`, `_PSYCHOLOGY_MT`) — `tests/test_psychology_migrated.py`
imports them directly to assert against the SEPARATE, already-migrated
`seeds/psychology.json` seed (loaded via the modern `WorldAdapter(seeds=...)`
path, not via any function in this file). The graph data this module
originally installed lives on as that seed; only the CuriousAgent-era
Python that once built it is gone.

The agent already DOES theory of mind work — it maintains a model of
the interlocutor's beliefs (Interlocutor.believed_concepts), it tracks
its own goals (desires), it recognises others' speech acts as
intentional categories — but it has no concepts for any of this. It
does the work without knowing what the work is. This module ONCE
installed the missing vocabulary as graph data (now `seeds/psychology.
json`'s job) and linked the agent's existing capabilities to the
concepts so the agent can introspect "I have theory of mind" as a real
graph query.

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
"""
from __future__ import annotations


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


__all__ = [
    "_PSYCHOLOGY_MT",
    "_MENTAL_STATE_PARENT",
    "_MENTAL_STATES",
    "_MIND_CONCEPTS",
    "_TOM_CONCEPTS",
]
