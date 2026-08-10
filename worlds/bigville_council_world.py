"""BigvilleCouncilWorld -- bigville R20 (block 268000): COUNCIL MEETINGS & the
NOTICEBOARD -- two-tier governance + the public written record.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R20 + sec 2 "HOW the
council actually governs -- TWO-TIER MEETINGS + the NOTICEBOARD" + sec 0 "THE ROOM
WHERE IT HAPPENED")
--------------------------------------------------------------------------------
Governance is not an instantaneous lever-set -- it runs on SCHEDULED two-tier
meetings + a public written record:

  * A SCHEDULED meeting (R3 cadence) fires a PUBLIC session -- the mayor's ADDRESS,
    which attending townsfolk PERCEIVE -- then a PRIVATE session (council-only,
    OCCLUDED: R19 observe-vs-hear) where the collective decision_value over the
    council backing-graph sets the outcome. The town sees the council convene but
    does NOT hear the deliberation.
  * The public-discussion content (public_demand) does or does not move the private
    decision: a RESPONSIVE council tracks it (agency); a CAPTURED council ignores
    it (theatre). The correlation is READ OFF the graph (a measurement).
  * The mayor's public ADDRESS vs the private DECISION is the 234 stated!=held atom
    at INSTITUTIONAL scale.
  * The decision is WRITTEN by ONE council member (a biased clerk DISTORTS the
    minutes) and POSTED on the town-hall noticeboard; a resident LEARNS it only by
    going to the town hall (R1) AND being LITERATE (R18).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It edits no tracked file and holds NO governance decision.
Governance runs in an ISOLATED substrate (`substrate_rs.Substrate`) loading two
SEED manifests (bigville_council_gov / bigville_council_board). EVERY decision is a
RULE there -- convene (R3 cadence), address, member vote, the collective decision,
the private occlusion, the 234 gap, the clerk's minutes, promulgation, the
literacy+access-gated reading. None lives in Python. This adapter only does
mechanical I/O: register the graph data, ARM one meeting (set now_day / cadence /
public_demand / private_on / malice_on / literacy_gate_on), run the Rust run_rules
fixpoint, and read state back. No Python if/else over agent state decides the vote /
the decision / the gap / the minutes / who learns the law -- source-audit gate.
The public/private correlation (G-public-influence-or-theatre) is a MEASUREMENT
computed by the run script from per-meeting read-offs -- NOT a new primitive.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble            # noqa: E402
engine_preamble(strict=False)                                    # resolve THIS tree's engine

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402

# defaults set on every node so a rule never reads a missing key. Population
# variation (base_position, malice, literacy, ...) is set by the caller -- ingest,
# not a decision.
MEMBER_DEFAULTS = dict(base_position=0.0, self_serving_premium=0.0, vote=0.0,
                       clerk_bias=0.0)
RESIDENT_DEFAULTS = dict(literate=0.0, at_hall=0.0, knows_law=0.0,
                         knows_law_flag=0.0, knows_address=0.0, heard_address=0.0,
                         knows_decision=0.0, heard_decision=0.0)


class BigvilleCouncilWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_council_gov"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_council_board"), None)
        self._council = None
        self._mayor = None
        self._board = None
        self._members = {}      # name -> Member nid
        self._residents = {}    # name -> Resident nid
        self._meeting = None
        self._notice = None

    # ------------------------------------------------------------------ ingest
    def add_council(self, *, captured=0):
        c = self.eng.add_node("Council", {"captured": float(captured)})
        self._council = c
        return c

    def add_member(self, name, *, base_position, self_serving_premium=0.0,
                   is_clerk=0, clerk_bias=0.0):
        """A council member on the backing-graph. base_position = their true
        preference; self_serving_premium = how much malice inflates it; is_clerk
        marks the ONE member who writes the minutes (clerk_bias distorts them)."""
        attrs = dict(MEMBER_DEFAULTS)
        attrs.update(name=name, base_position=float(base_position),
                     self_serving_premium=float(self_serving_premium),
                     clerk_bias=float(clerk_bias))
        m = self.eng.add_node("Member", attrs)
        self.eng.add_edge_unchecked(self._council, "has_member", m)
        self._members[name] = m
        if is_clerk:
            self._clerk = name
        return m

    def add_mayor(self, name, *, stated_position):
        """The mayor -- gives the PUBLIC ADDRESS (a benevolent stated position)."""
        m = self.eng.add_node("Mayor", {"name": name,
                                         "stated_position": float(stated_position)})
        self._mayor = m
        return m

    def add_resident(self, name, *, literate=0, at_hall=0):
        """A townsperson who may attend the public meeting and/or read the notice.
        literate = the R18 literacy outcome; at_hall = R1 co-location at the hall."""
        attrs = dict(RESIDENT_DEFAULTS)
        attrs.update(name=name, literate=float(literate), at_hall=float(at_hall))
        r = self.eng.add_node("Resident", attrs)
        self._residents[name] = r
        return r

    def add_board(self):
        self._board = self.eng.add_node("Board", {})
        return self._board

    # ------------------------------------------------- rule-driven meeting
    def convene(self, *, now_day=0, cadence=1, public_demand=0, private_on=1,
                malice_on=0, attendees=None):
        """Mint + ARM a Meeting and run the governance rules. Reads back the public
        address, the private held_decision, the 234 gap, and each attendee's
        perception. All DECISIONS are rules; this only ingests + reads."""
        attendees = attendees if attendees is not None else list(self._residents)
        mtg = self.eng.add_node("Meeting", {
            "now_day": float(now_day), "cadence": float(cadence),
            "armed": 1.0, "convened": 0.0,
            "public_demand": float(public_demand), "private_on": float(private_on),
            "malice_on": float(malice_on),
            "public_address": 0.0, "held_decision": 0.0, "stated_held_gap": 0.0})
        self.eng.add_edge_unchecked(mtg, "convenes", self._council)
        if self._mayor is not None:
            self.eng.add_edge_unchecked(mtg, "addressed_by", self._mayor)
        for a in attendees:
            self.eng.add_edge_unchecked(mtg, "attended_by", self._residents[a])
        self._meeting = mtg
        self.eng.run_rules(1000000)
        return dict(convened=self.convened(), public_address=self.public_address(),
                    held_decision=self.held_decision(),
                    stated_held_gap=self.stated_held_gap())

    def post_notice(self, *, literacy_gate_on=1):
        """The clerk WRITES the minutes (recorded = held_decision + clerk_bias) and
        the board POSTS them; then residents who VISIT the board read it iff at the
        hall AND literate (or the gate is ablated). All rules -- this only wires the
        Notice + visits edges and runs the fixpoint."""
        if self._board is None:
            self.add_board()
        n = self.eng.add_node("Notice", {
            "recorded": 0.0, "posted": 0.0, "officially_known": 0.0,
            "literacy_gate_on": float(literacy_gate_on)})
        self.eng.add_edge_unchecked(n, "of_meeting", self._meeting)
        self.eng.add_edge_unchecked(n, "written_by", self._members[self._clerk])
        self.eng.add_edge_unchecked(self._board, "posts", n)
        for r in self._residents.values():
            self.eng.add_edge_unchecked(r, "visits", self._board)
        self._notice = n
        self.eng.run_rules(1000000)
        return dict(recorded=self.recorded(),
                    officially_known=self.officially_known())

    # ------------------------------------------------- glass-box read-offs
    def _matt(self, node, key, default=0.0):
        return float(self.eng.node(node)["attrs"].get(key, default))

    def convened(self):
        return int(self._matt(self._meeting, "convened"))

    def public_address(self):
        return self._matt(self._meeting, "public_address")

    def held_decision(self):
        return self._matt(self._meeting, "held_decision")

    def stated_held_gap(self):
        return self._matt(self._meeting, "stated_held_gap")

    def vote_of(self, name):
        return self._matt(self._members[name], "vote")

    def recorded(self):
        return self._matt(self._notice, "recorded")

    def officially_known(self):
        return int(self._matt(self._notice, "officially_known"))

    def knows_address_of(self, name):
        return self._matt(self._residents[name], "knows_address")

    def heard_address_of(self, name):
        return int(self._matt(self._residents[name], "heard_address"))

    def heard_decision_of(self, name):
        return int(self._matt(self._residents[name], "heard_decision"))

    def knows_decision_of(self, name):
        return self._matt(self._residents[name], "knows_decision")

    def knows_law_flag_of(self, name):
        return int(self._matt(self._residents[name], "knows_law_flag"))

    def knows_law_of(self, name):
        return self._matt(self._residents[name], "knows_law")

    def close(self):
        self._members.clear()
        self._residents.clear()
