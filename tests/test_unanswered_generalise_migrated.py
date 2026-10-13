"""Tranche 22: the agent files its own unanswered turns and generalises a held
reply to them, judged on the production path.

Pinned claims:
  * a recurring unanswered turn class (>= UnansweredGapPolicy.min_recurrence
    turns whose production outcome was the explicit error floor) files exactly
    one SelfConcern{kind:'unanswered'}; a single one files nothing;
  * disposition_generalise builds an add-only (arbitration, reply) pair with one
    guard relaxed to the unanswered turn's own evidence;
  * installed, the pair answers the class on the production path and leaves
    other turns unchanged;
  * the scheduler's close demand fires on the boolean conclusion_ready the
    judge rules write (it never fired before, so nothing was ever adopted in
    production);
  * the conversation replay keeps error-floor turns as probes.
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

import domains.reflective_faculty as rf   # noqa: E402
import endemic_rsi_daemon_v1 as E         # noqa: E402


def _unanswered(a):
    return [n for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("kind") == "unanswered"]


@pytest.fixture(scope="module")
def st():
    s = E.boot(True)
    for n in s.adapter.s.nodes("SelfPromotionPolicy"):
        s.adapter.s.set_attr(n, "enabled", 0)       # isolate filing from the loop
    E.say(s, "Hello.")
    return s


def test_recurring_unanswered_class_files_one_concern(st):
    a = st.adapter
    status, _ = E.say(st, "That would be fun!")
    assert status == "explicit_error"
    a.inner.run_rules()
    assert _unanswered(a) == [], "one unanswered turn is not yet a pattern"
    E.say(st, "The sky is blue.")
    E.say(st, "That sounds great!")
    a.inner.run_rules()
    sc = _unanswered(a)
    assert len(sc) == 1, [a.s.node(n)["attrs"].get("content") for n in sc]
    at = a.s.node(sc[0])["attrs"]
    assert at["status"] == "noted" and at["sig_evidence_force"] == "assertion_or_correction"
    assert list(a.inner.neighbours(sc[0], "about_message"))


def test_generalised_pair_answers_the_class_on_the_production_path(st):
    a = st.adapter
    sc = _unanswered(a)[0]
    standing = a.s.add_node("StandingConcern", {"name": "t22_probe", "status": "processed"})
    a.inner.add_edge_unchecked(sc, "promoted_to", standing)
    rf._ensure_where_literal_rule_provenance(a.s, a.inner)
    rep = rf._compose_disposition_generalise(a, ["t22_probe"], "t22")
    assert rep["built"], rep
    assert rep["source_rule"] == "defer_response_assertion_without_proposition_uptake"
    assert rep["guard"] == "interaction_relation"
    assert all(r["name"].endswith("_generalised") for r in rep["rules"]) and len(rep["rules"]) == 2
    # plan P4: the held FamilyProgram builds the identical variant
    prog = rf._compose_from_program(a, "family_disposition_generalise", ["t22_probe"], "t22")
    assert rf.family_report_signature(prog) == rf.family_report_signature(rep)
    before_bake = E.say(st, "Bake the cake.")[1]
    for r in rep["rules"]:
        a.inner.add_rule(r)
    status, reply = E.say(st, "The weather is nice today.")
    assert status == "reply_released" and reply and not reply.startswith("ERROR"), (status, reply)
    assert E.say(st, "Bake the cake.")[1].startswith("I took on the goal") == before_bake.startswith("I took on the goal")
    assert E.say(st, "Hello.")[0] == "reply_released"


def test_scheduler_close_demand_fires_on_boolean_conclusion_ready():
    d = json.load(open(os.path.join(ROOT, "seeds", "cognitive_scheduler.json")))
    r = next(r for r in d["rules"] if r["name"] == "supervise_ready_experiment_close")
    s = json.dumps(r["where"])
    assert '"key": "conclusion_ready"}, "b": {"type": "Lit", "value": true}' in s


def test_replay_corpus_keeps_error_floor_turns(st):
    import convo_child_run as ccr
    probes = ccr.read_corpus(st.adapter)
    texts = {p["text"]: p for p in probes}
    assert "That would be fun!" in texts
    assert texts["That would be fun!"]["flagged"] is True
