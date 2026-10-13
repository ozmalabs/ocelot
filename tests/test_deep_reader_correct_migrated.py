"""Tranche 23: the deep reader corrects a recurrent shallow misreading, judged on
the production path.

Pinned claims:
  * on a fresh conversation boot, a statement the shallow reader classifies as
    an instruction ("I like to play video games too!") gets a spurious
    goal-take, and the deep reader (shadow_speech_act) disagrees;
  * deep_reader_correct, given a comprehension concern about that turn, builds
    a REPLACEMENT of the misreading arbitration rule (vetoed only for that
    shallow/deep disagreement) plus an added receipt arbitration and reply;
  * installed, the same class of turn gets a non-error, non-goal-take receipt
    on the production path, while a real imperative ("Bake the cake.") still
    gets its goal-take and a greeting is unchanged;
  * the replay corpus marks every turn with the concern's disagreement as
    in_scope (changing it is the point, not a regression).
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

MISREAD = "I like to play video games too! I'm not much of a reader, though."
SAME_CLASS = "You should! It's a lot of fun."


def _goal_take(reply):
    return bool(reply) and (reply.startswith("I took on the goal to") or "is deferred" in reply)


@pytest.fixture(scope="module")
def st():
    s = E.boot(True)
    for n in s.adapter.s.nodes("SelfPromotionPolicy"):
        s.adapter.s.set_attr(n, "enabled", 0)       # isolate the family from the loop
    E.say(s, "Hello.")
    return s


@pytest.fixture(scope="module")
def misread(st):
    import jabberwock_daemon as jd
    import substrate_rs as srs
    with jd.AGENT_LOCK:
        tid = jd._ingest_daemon_chat_turn(st, MISREAD)
    for _ in range(30):
        done = E.one_cycle(st)
        if tid in done:
            return srs.NodeID(tid), done[tid]
    pytest.fail("misread turn never concluded")


def test_shallow_reader_misreads_a_statement_as_an_instruction(st, misread):
    mid, (status, reply) = misread
    at = st.adapter.s.node(mid)["attrs"]
    assert at.get("comp_kind") == "instruction" and at.get("shadow_speech_act") == "statement", at
    assert _goal_take(reply), (status, reply)


@pytest.fixture(scope="module")
def built(st, misread):
    a = st.adapter
    mid, _ = misread
    sc = a.s.add_node("SelfConcern", {"kind": "comprehension", "status": "promoted", "content": "t23 probe"})
    standing = a.s.add_node("StandingConcern", {"name": "t23_probe", "status": "processed"})
    a.inner.add_edge_unchecked(sc, "promoted_to", standing)
    a.inner.add_edge_unchecked(sc, "about_message", mid)
    return rf._compose_deep_reader_correct(a, ["t23_probe"], "t23")


def test_family_program_builds_the_identical_correction(st, built):
    # plan P4: the held FamilyProgram (seeds/family_programs.json) builds the
    # same variant the Python builder does
    prog = rf._compose_from_program(st.adapter, "family_deep_reader_correct", ["t23_probe"], "t23")
    assert prog["built"], prog
    assert rf.family_report_signature(prog) == rf.family_report_signature(built)


def test_builder_replaces_the_misreading_arbitration(built):
    assert built["built"], built
    assert built["removed_rule"] == "arbitrate_instruction_as_action_request"
    assert (built["shallow"], built["deep"]) == ("instruction", "statement")
    variant, receipt_arb, receipt_reply = built["rules"]
    assert variant["name"] == "arbitrate_instruction_as_action_request_deepread_t23"
    assert variant["where"]["type"] == "And" and variant["where"]["items"][-1]["type"] == "Not"
    assert ["set_attr", "i", "receipt_selected_by_rule", "neutral_receipt"] in receipt_arb["effects"]
    assert receipt_reply["name"].startswith("reply_deep_reader_instruction_as_statement_function_receipt")
    # scoped to the concern turn's literal class too, not the reader pair alone
    assert '"literal_first_role"}, "b": {"type": "Lit", "value": "function"}' in json.dumps(receipt_arb["where"])


def test_installed_correction_answers_the_class_and_spares_imperatives(st, built):
    a = st.adapter
    # "Paint the fence." is a real imperative the deep reader ALSO hears as a
    # statement (same reader pair, content-word first): it must keep its goal
    controls = ["Bake the cake.", "Paint the fence.", "Open the door."]
    before = {t: _goal_take(E.say(st, t, max_cycles=20)[1]) for t in controls}
    assert all(before.values()), before
    rules = a.inner.export_rules()
    idx = next(i for i, r in enumerate(rules)
               if r.get("name") == built["removed_rule"] and r.get("active", True))
    a.inner.remove_rule(idx)
    for r in built["rules"]:
        a.inner.add_rule(r)
    status, reply = E.say(st, SAME_CLASS, max_cycles=20)
    assert status == "reply_released" and reply and not reply.startswith("ERROR"), (status, reply)
    assert not _goal_take(reply), reply
    after = {t: _goal_take(E.say(st, t, max_cycles=20)[1]) for t in controls}
    assert after == before, after
    assert E.say(st, "Hello.", max_cycles=20)[0] == "reply_released"


def test_replay_marks_the_disagreement_class_in_scope(st, built):
    import convo_child_run as ccr
    probes = {p["text"]: p for p in ccr.read_corpus(st.adapter)}
    assert probes[MISREAD]["flagged"] is True and probes[MISREAD]["in_scope"] is True
    assert probes["Hello."]["in_scope"] is False
    # same reader pair, but a content-word-first imperative: out of scope
    assert probes["Paint the fence."]["in_scope"] is False


def test_child_delta_keeps_the_parent_turn_path(tmp_path):
    """Before tranche 23 _load_delta dropped parent_turn_path, so every
    'production' replay silently ran on converse()."""
    import json
    from arc_child_run import _load_delta
    p = tmp_path / "delta.json"
    p.write_text(json.dumps({"parent_turn_path": "production", "parent_shadow_read": True}))
    assert _load_delta(str(p))["parent_turn_path"] == "production"
    assert _load_delta(None)["parent_turn_path"] == ""
