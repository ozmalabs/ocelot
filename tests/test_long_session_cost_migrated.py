"""Long-session cost fix (2026-10-10).

Measured: on one conversation session, per-turn time grew from 0.3 s (turn
25) to 6.5-10.6 s (turn 150). Causes and fixes, each behaviour-preserving
(a 150-turn offline session gives byte-identical replies before and after):

  * ~30 per-turn reply lookups scanned EVERY agent outbound message and
    filtered by `mid in responds_to(reply)` -> WorldAdapter.
    agent_outbound_replies_to(mid) reads mid's own responds_to in-edges;
  * note_unanswered_turn scanned all Messages for its class count -> the
    count lives on a TurnShape (unanswered_gap v2.0.0, the turn ring);
  * note_comprehension_latency_gap scanned all Messages for "latest turn" ->
    a datum comparison (comprehension_health v1.1.0);
  * escalate_unparsed_clauses / reform_overcomplex_clause enumerated every
    (goal, stage) / (parse, goal) pair -> flow-join index_hints
    (reading_aperture v1.2.0).
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "evaluation", "substrate_capability")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _seed(name):
    return json.load(open(os.path.join(ROOT, "seeds", f"{name}.json")))


def _rule(seed, name):
    return next(r for r in _seed(seed)["rules"] if r["name"] == name)


def test_outbound_replies_helper_matches_the_full_scan_on_a_real_session():
    import endemic_rsi_daemon_v1 as E
    st = E.boot(True, promote=False)
    a = st.adapter
    for t in ["Hello.", "I like to watch movies and TV shows.", "What do you do for fun?",
              "Bake the cake.", "That would be fun!", "Hi! I'm someone."]:
        E.say(st, t)
    inbound = [m for m in a.s.nodes("Message") if a.s.node(m)["attrs"].get("from") == "interlocutor"]
    assert len(inbound) >= 6
    for m in inbound:
        full = [r for r in a.agent_outbound_messages() if m in a.responds_to(r)]
        assert a.agent_outbound_replies_to(m) == full
        assert a.agent_outbound_replies_to(int(m.value)) == full
    assert a.agent_outbound_replies_to(None) == []


def test_unanswered_rule_reads_the_class_shape():
    """v2.0.0 (turn ring): the recurrence lives on a TurnShape; the rule never
    scans Messages."""
    tally = _rule("unanswered_gap", "tally_unanswered_class")
    assert tally["match"][0] == ["agent", "received", "m"]
    assert any(e[:3] == ["add_node_if_absent", "sh", "TurnShape"] for e in tally["effects"])
    r = _rule("unanswered_gap", "note_unanswered_turn")
    assert r["match"][:2] == [["agent", "has_turn_shape", "sh"], ["sh", "first_member", "m"]]
    s = json.dumps(r["where"])
    assert '"node_type": "Message"' not in s
    assert '"edge_type": "has_member"' in s


def test_latency_rule_compares_with_the_latest_turn_datum():
    """v1.1.0: 'm is the newest shadow-read turn' is a datum comparison, not a scan."""
    s = json.dumps(_rule("comprehension_health", "note_comprehension_latency_gap")["where"])
    assert '"node_type": "Message"' not in s and '"key": "latest_shadow_seq"' in s


def test_reading_rules_carry_flow_join_hints():
    for name, var, node_type in (("escalate_unparsed_clauses", "spine_stage", "AnalysisStage"),
                                 ("reform_overcomplex_clause", "sp", "SentenceParse")):
        hints = _rule("reading_aperture", name).get("index_hints")
        assert hints == [{"for_var": var, "via_var": "src", "via_key": "flow", "node_type": node_type,
                          "this_key": "flow"}]
