"""LangSimSyntaxWorld -- langsim's economy+building world with a SYNTAX-CARRYING
promise gate (block 244000).

REUSES langsim's world + value economy VERBATIM (worlds/langsim_world.py is
UNTOUCHED) so the coordination comparison is apples-to-apples. The ONLY change is
the promise gate: langsim set ``promise_in`` from a BAG read ("give" in names AND
needed resource in names -- order-insensitive, so the scrambled control could not
fail). Here a SyntaxAgent sets it from a STRUCTURED role match on the composed
Intent (``domains/langsim_syntax``), so a word-order scramble fails to carry the
offer -- the pre-shaped success of the map's #1 build-out.

ARCHITECTURE RULE. This is a WORLD ADAPTER. The composition is the Merge RULES on
the Rust engine (language.comprehend, reached via langsim_syntax.parse_intent);
the gate is a MECHANICAL read of the structured Intent (structured_offer_holds).
The give/keep decision remains the unchanged ``gb_choose_give`` value rule. No
graph_rewrite.run / gr.run / _match / _apply / make_rule; every conditional here
is over WORLD state, mechanical.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np                                          # noqa: E402

from domains import langsim_syntax as _ls                   # noqa: E402
from worlds.langsim_world import Agent, LangSimWorld         # noqa: E402


class SyntaxAgent(Agent):
    """A langsim Agent whose comprehension is SYNTAX-CARRYING. It composes the
    delivered utterance's word ORDER into a structured Intent, MIRRORS that Intent
    into its own live graph as an ``Intent{predicate, agent, patient, recipient}``
    node (glass-box, readable via graph_to_dict), and gates the promise on the
    STRUCTURED role match -- not a bag of tokens."""

    def hear(self, text, speaker_name="partner"):
        # Keep langsim's referent-bag read for transcript-shape compatibility...
        mid, resolved = super().hear(text, speaker_name)
        # ...then COMPOSE word order into a structured Intent via the faculty.
        self._last_intent = _ls.parse_intent(text)
        self._write_intent_node(mid, self._last_intent)
        return mid, resolved

    def _write_intent_node(self, mid, intent):
        """GLASS-BOX: mirror the structured Intent into the live substrate. Roles
        absent from the parse are stored as '' so the node shows what word order
        did and did NOT bind (e.g. a scramble that leaves `patient` empty)."""
        it = intent or {}
        node = self.s.add_node("Intent", {
            "predicate": it.get("predicate") or "",
            "agent": it.get("agent") or "",
            "patient": it.get("patient") or "",
            "recipient": it.get("recipient") or ""})
        self.inner.add_edge_unchecked(mid, "has_intent", node)
        return node

    def comprehended_offer_of(self, resolved):
        """STRUCTURED gate: the partner (agent) offers (give) exactly the resource
        this agent needs (patient). Replaces langsim's bag membership test."""
        return _ls.structured_offer_holds(getattr(self, "_last_intent", None),
                                          self.needs)

    def last_intent_node(self):
        """Read back the most-recently written Intent node's attrs (glass-box
        read for the harness/tests)."""
        msgs = [n for n in self.s.nodes("Intent")]
        return self.s.node(msgs[-1])["attrs"] if msgs else None


class LangSimSyntaxWorld(LangSimWorld):
    """langsim's world with SyntaxAgents. Only construction changes (to build
    SyntaxAgents); the entire step/encounter/value machinery is INHERITED
    UNCHANGED from LangSimWorld, so the economy is identical and the ONLY causal
    difference from langsim is the structured promise gate."""

    def __init__(self, w_supergraphs, mode="language", seed=0):
        assert mode in ("language", "none", "scrambled")
        self.mode = mode
        self.ws = [float(w) for w in w_supergraphs]
        self.n = len(self.ws)
        self.rng = np.random.default_rng(seed)
        comms = (mode != "none")
        self.agents = [SyntaxAgent(i, i % 2, self.ws[i], comms) for i in range(self.n)]
        self.pos = [int(self.rng.integers(0, self.P_RING)) for _ in range(self.n)]

        self.total_value = 0.0
        self.n_builds = 0
        self.n_encounters = 0
        self.tick = 0
        self.transcripts = []
        self.trade_log = []
        self.promise_nodes_readable = []
