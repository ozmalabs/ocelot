"""Plan P5 (2026-10-10): operator authorship, propose-only.

Pinned claims:
  * seeds/operator_authorship.json is frozen, its node types are protected,
    and every FamilyMutation names a parameter site its FamilyProgram declares;
  * candidates are enumerated in MDL order (held, singles, pairs) under the
    policy's caps, and applied with the engine's EditAt: setting a site to its
    default reproduces the held program exactly;
  * within a family, fewer relaxed guards win (p_max_miss = 2 builds the same
    variant as the held family where a one-guard variant exists);
  * the realiser source role builds a one-rule variant for a short agreement
    the held reply rule misses on one guard, and installed it answers the turn;
  * the frozen rules decide the verdict; a qualifying proposal is
    install_blocked (propose-only).
The gate itself (A5a) is evaluation/substrate_capability/operator_authorship_a5a_v1.py.
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

import domains.operator_authorship as OA    # noqa: E402
import domains.reflective_faculty as rf     # noqa: E402
import endemic_rsi_daemon_v1 as E           # noqa: E402


def _seed(name):
    return json.load(open(os.path.join(ROOT, "seeds", f"{name}.json")))


def test_seed_is_frozen_protected_and_names_declared_sites():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "operator_authorship" in _FROZEN_SEED_IDS
    assert "operator_authorship" in _seed("frozen_core_manifest")["frozen_seed_ids"]
    types = _seed("improvement_integrity")["nodes"][0]["attrs"]["protected_node_types"]
    assert {"OperatorAuthorshipPolicy", "FamilyMutation", "FamilyProposal"} <= set(types)
    sites = {n["attrs"]["name"]: json.loads(n["attrs"]["parameter_sites"])
             for n in _seed("family_programs")["nodes"]}
    muts = [n["attrs"] for n in _seed("operator_authorship")["nodes"] if n["type"] == "FamilyMutation"]
    assert muts
    for m in muts:
        assert m["site"] in sites[m["program"]], m
        assert sites[m["program"]][m["site"]]["default"] not in json.loads(m["values"])


@pytest.fixture(scope="module")
def st():
    s = E.boot(True, promote=False)
    E.say(s, "Hello.")
    return s


def _turn(a, text):
    for m in sorted(a.s.nodes("Message"), key=lambda x: x.value, reverse=True):
        at = a.s.node(m)["attrs"]
        if at.get("from") == "interlocutor" and at.get("text") == text:
            return m
    raise AssertionError(text)


def test_enumeration_is_mdl_ordered_and_capped(st):
    cands = OA.enumerate_candidates(st.adapter)
    sizes = [c["size"] for c in cands]
    assert sizes == sorted(sizes) and sizes[0] == 0
    held = [c for c in cands if c["size"] == 0]
    assert {c["program"] for c in held} == {"family_disposition_generalise", "family_deep_reader_correct"}
    _pn, pol = OA.policy(st.adapter)
    assert len(cands) - len(held) <= pol["max_candidates"] and max(sizes) <= pol["max_size"]
    pair = [c for c in cands if c["size"] == 2]
    assert pair and all(len({s for s, _v in c["edits"]}) == 2 for c in pair)


def test_edit_at_applies_sites_and_default_is_identity(st):
    a = st.adapter
    held = rf._load_family_program(a.s, "family_disposition_generalise")
    same = OA.candidate_program(a, {"program": "family_disposition_generalise",
                                    "edits": [["p_max_miss", 1], ["p_source_role", "arbitration"]]})
    assert same == held
    two = OA.candidate_program(a, {"program": "family_disposition_generalise", "edits": [["p_max_miss", 2]]})
    assert two["value"] == {"type": "Lit", "value": 2} and two["body"] == held["body"]


def test_fewer_relaxed_guards_win(st):
    a = st.adapter
    status, _ = E.say(st, "That would be fun!")
    assert status == "explicit_error"
    m = _turn(a, "That would be fun!")
    held = OA.build_on_turn(a, rf._load_family_program(a.s, "family_disposition_generalise"), m, "t1")
    two = OA.build_on_turn(a, OA.candidate_program(
        a, {"program": "family_disposition_generalise", "edits": [["p_max_miss", 2]]}), m, "t1")
    assert held["built"], held
    assert rf.family_report_signature(two) == rf.family_report_signature(held)


def test_realiser_source_answers_a_short_agreement(st):
    a = st.adapter
    status, reply = E.say(st, "Yeah, it's the best.")
    assert not (reply or "").strip(), (status, reply)
    m = _turn(a, "Yeah, it's the best.")
    prog = OA.candidate_program(a, {"program": "family_disposition_generalise",
                                    "edits": [["p_source_role", "realiser"]]})
    rep = OA.build_on_turn(a, prog, m, "t2")
    assert rep["built"], rep
    assert rep["source_rule"] == "reply_to_deferred_typed_response_acknowledgement"
    assert rep["guard"] == "interaction_relation" and rep["new_value"] == ""
    assert len(rep["rules"]) == 1 and rep["rules"][0]["name"].endswith("_generalised")
    assert OA.delta_of(rep)["remove_rules"] == []                # add-only
    a.inner.add_rule(rep["rules"][0])
    _status, reply2 = E.say(st, "Yes, I do.")
    assert (reply2 or "").strip(), _status


def test_frozen_rules_decide_and_block_install(st):
    a = st.adapter
    rows = {"held": dict(size=0, fixed=3, harm=0, novel_fixed=0),
            "good": dict(size=1, fixed=2, harm=0, novel_fixed=1),
            "harmful": dict(size=1, fixed=5, harm=1, novel_fixed=1),
            "few": dict(size=1, fixed=1, harm=0, novel_fixed=1),
            "not_new": dict(size=2, fixed=4, harm=0, novel_fixed=0)}
    nodes = {k: OA.mint_proposal(a, dict(v, candidate=k)) for k, v in rows.items()}
    for _ in range(3):
        a.inner.run_rules()
    got = {k: a.s.node(n)["attrs"].get("verdict") for k, n in nodes.items()}
    assert got == {"held": "held_baseline", "good": "qualifies", "harmful": "does_not_qualify",
                   "few": "does_not_qualify", "not_new": "does_not_qualify"}
    assert a.s.node(nodes["good"])["attrs"].get("install_blocked") == 1
    assert not a.s.node(nodes["harmful"])["attrs"].get("install_blocked")
