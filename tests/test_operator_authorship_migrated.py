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
  * v1.1.0 (P5b): the frozen rules weigh harm relatively (net against the
    parent family), install the best qualifying candidate on probation wired
    as its parent, file its residual turns as concerns, and retire or
    graduate it on its own judged trials; p_exclude_sources refines a family
    where it does harm.
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


def _held_op(a, name):
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == name:
            return n
    raise AssertionError(name)


def test_relative_rules_decide_install_and_file_residual(st):
    """v1.1.0: harm is weighed, not vetoed; the best candidate beating its
    parent is installed on probation, wired as the parent; what it still
    harms is filed as the agent's own concern."""
    a = st.adapter
    S = a.s
    prog = OA.candidate_program(a, {"program": "family_disposition_generalise", "edits": [["p_max_miss", 2]]})
    turn = _turn(a, "That would be fun!")
    base = dict(program="family_disposition_generalise", parent_op="disposition_generalise", bank_set="t")

    def cand(k, rank, **kw):
        attrs = dict(base, candidate=k, mdl_rank=rank, edits=[["p_max_miss", 2]], size=1,
                     family_name=f"family_authored_{k}", op_name=f"authored_{k}",
                     program_json=json.dumps(prog), **kw)
        return attrs
    rows = {"held": dict(base, candidate="held", size=0, mdl_rank=0, fixed=16, harm=15),     # net 1
            "better": cand("better", 2, fixed=18, harm=4),          # net 14, gain 13: harm weighed, not vetoed
            "best": cand("best", 3, fixed=16, harm=0),              # net 16: installed
            "worse": cand("worse", 1, fixed=18, harm=31),           # net -13
            "same": cand("same", 4, fixed=17, harm=16),             # gain 0 < min_gain
            "few": cand("few", 5, fixed=1, harm=0)}                 # below k_fix
    nodes = {k: OA.mint_proposal(a, v, [turn] if k == "best" else []) for k, v in rows.items()}
    for _ in range(4):
        a.inner.run_rules()
    got = {k: S.node(n)["attrs"].get("verdict") for k, n in nodes.items()}
    assert got == {"held": "held_baseline", "better": "qualifies", "best": "qualifies",
                   "worse": "does_not_qualify", "same": "does_not_qualify", "few": "does_not_qualify"}
    assert S.node(nodes["best"])["attrs"]["net"] == 16 and S.node(nodes["best"])["attrs"]["gain"] == 15
    assert S.node(nodes["best"])["attrs"].get("installed") == 1
    assert not S.node(nodes["better"])["attrs"].get("installed")          # one per program: the best
    op = _held_op(a, "authored_best")
    at = S.node(op)["attrs"]
    parent = S.node(_held_op(a, "disposition_generalise"))["attrs"]
    assert at["provenance"] == "agent_authored" and at["probation"] == 1
    assert at["family"] == "disposition_generalise" and at["requires_kind"] == parent["requires_kind"]
    assert at["cue_head"] == parent["cue_head"] and at["priority"] == parent["priority"] - 0.5
    assert rf._load_family_program(S, "family_authored_best") == prog
    assert rf._variation_op_family(a, "authored_best") == "disposition_generalise"
    assert rf._builder_for(a, "authored_best") is not None                # a held-Program builder
    res = [n for n in S.nodes("SelfConcern") if S.node(n)["attrs"].get("kind") == "family_residual"]
    assert len(res) == 1 and list(a.inner.neighbours(res[0], "about_message")) == [turn]
    for _ in range(2):
        a.inner.run_rules()
    assert len([n for n in S.nodes("SelfConcern") if S.node(n)["attrs"].get("kind") == "family_residual"]) == 1


def _trial(a, op_name, outcome):
    S, I = a.s, a.inner
    exp = S.add_node("Experiment", {"status": "done", "outcome": outcome, "axis_tag": "probation_probe"})
    d = S.add_node("SeedDelta", {"variation_op": op_name})
    I.add_edge_unchecked(exp, "has_delta", d)


def test_probation_retires_or_graduates_on_own_trials(st):
    a = st.adapter
    S = a.s
    op = _held_op(a, "authored_best")
    for o in ("refuted", "inconclusive"):
        _trial(a, "authored_best", o)
    a.inner.run_rules()
    assert S.node(op)["attrs"].get("probation") == 1 and not S.node(op)["attrs"].get("retired")   # 2 < trials
    _trial(a, "authored_best", "refuted")
    a.inner.run_rules()
    at = S.node(op)["attrs"]
    assert at["retired"] == 1 and at["cue_head"] == "retired" and at["retired_cue_head"] == "replay"
    # a second authored op that earns its keep leaves probation
    pol, _p = OA.policy(a)
    op2 = S.add_node("VariationOp", {"name": "authored_good", "parent_op": "disposition_generalise",
                                     "probation": 1, "priority": 9.5, "cue_head": "replay",
                                     "provenance": "agent_authored"})
    a.inner.add_edge_unchecked(pol, "installed_family", op2)
    for o in ("supported", "refuted", "supported"):
        _trial(a, "authored_good", o)
    a.inner.run_rules()
    at2 = S.node(op2)["attrs"]
    assert at2["probation"] == 0 and at2["priority"] == 9.5 and not at2.get("retired")


def test_exclusion_site_refines_a_family(st):
    a = st.adapter
    m = _turn(a, "That would be fun!")
    held = OA.build_on_turn(a, rf._load_family_program(a.s, "family_disposition_generalise"), m, "t3")
    assert held["built"]
    ref = OA.refined({"id": "x", "program": "family_disposition_generalise", "edits": []}, [held["source_rule"]])
    rep = OA.build_on_turn(a, OA.candidate_program(a, ref), m, "t3")
    assert rep.get("source_rule") != held["source_rule"]                 # changed where it harmed
