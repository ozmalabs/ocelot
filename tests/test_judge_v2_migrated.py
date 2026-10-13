"""Plan P1 (2026-10-10): judge v2 -- reply quality gates fixes and adoption.

  * scripts/convo_child_run.score_probes: a changed flagged turn is a fix only
    if its new reply is at least acceptable-minimal (a receipt for a question
    is a broken fix); an unflagged turn is `repaired` only if its quality did
    not decrease;
  * seeds/adoption_safety.json v1.2.0 adopt_denied_on_quality_drop denied an
    Experiment whose child reported quality_drops > 0 or quality_delta < 0;
    v1.3.0 (P5c) replaces it, and the regression veto, with a weighed net,
    and an unflagged change is a regression only if worse in the frame;
  * adoption_safety is frozen (boot_all._FROZEN_SEED_IDS).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from domains import reply_quality as rq                  # noqa: E402
from substrate.world_adapter import WorldAdapter          # noqa: E402

ERR = "ERROR: no communicative response could be generated."


def _score(probe, control_reply, variant_reply):
    import convo_child_run as ccr
    probes = [dict({"turn_id": 1, "reply": control_reply, "flagged": False}, **probe)]
    control = {"replies": [control_reply], "errors": [None], "turn_ms": [0.0]}
    stats = {"replies": [variant_reply], "errors": [None], "turn_ms": [0.0]}
    qc = [rq.assess(probes[0]["text"], control_reply)["score"]]
    qv = [rq.assess(probes[0]["text"], variant_reply)["score"]]
    return ccr.score_probes(probes, control, stats, qc, qv), qc[0], qv[0]


def test_receipt_for_a_question_is_a_broken_fix():
    out, qc, qv = _score({"text": "What do you like to do for fun?", "flagged": True}, ERR, "got it")
    assert qv == 0, "premise: ReplyQuality scores a receipt to a question inappropriate"
    assert out["broken_fixes"] == 1 and out["flagged_changed"] == 0 and out["score"] == -1
    assert out["quality_vetoed_fixes"] == 1


def test_receipt_for_a_statement_is_still_a_fix():
    out, qc, qv = _score({"text": "I like to watch movies and TV shows.", "flagged": True}, ERR, "got it")
    assert qv == 1
    assert out["flagged_changed"] == 1 and out["score"] == 1 and out["quality_vetoed_fixes"] == 0


def test_honest_goal_take_for_an_imperative_is_a_fix():
    # the child passes the turn's literal_form (communication interpretation);
    # without it ReplyQuality reads 'Condense the data.' as a statement
    import convo_child_run as ccr
    text, reply = "Condense the data.", ("I took on the goal to condense the data, but I have no world "
                                         "or faculty attached to carry it out here.")
    assert rq.assess(text, reply)["score"] == 0
    probes = [{"turn_id": 1, "text": text, "reply": ERR, "flagged": True, "literal_form": "imperative"}]
    q = lambda r: [rq.assess(text, r, "imperative")["score"]]
    out = ccr.score_probes(probes, {"replies": [ERR], "errors": [None], "turn_ms": [0.0]},
                           {"replies": [reply], "errors": [None], "turn_ms": [0.0]}, q(ERR), q(reply))
    assert out["flagged_changed"] == 1 and out["quality_vetoed_fixes"] == 0


def test_repair_requires_quality_not_to_drop():
    # error -> receipt on an unflagged statement: repaired (quality 0 -> 1)
    out, qc, qv = _score({"text": "I like to garden.", "flagged": False}, ERR, "got it")
    assert (qc, qv) == (0, 1) and out["repaired"] == 1 and out["regressions"] == 0
    # an in-scope turn whose quality falls is a regression, not a repair
    out, qc, qv = _score({"text": "Hello!", "flagged": False, "in_scope": True}, "hello", "got it")
    assert qv < qc
    assert out["repaired"] == 0 and out["regressions"] == 1


def _veto_agent():
    a = WorldAdapter(seeds=())
    seed = json.load(open(os.path.join(ROOT, "seeds", "adoption_safety.json")))
    for n in seed["nodes"]:                  # v1.3.0: the AdoptionWeighing exchange rates
        a.s.add_node(n["type"], dict(n["attrs"]))
    for r in seed["rules"]:
        a.inner.add_rule(r)
    return a


def _exp(a, **attrs):
    exp = a.s.add_node("Experiment", dict({"outcome": "supported", "adopt_ready": True}, **attrs))
    d = a.s.add_node("SeedDelta", {"act_rule_varied": "x"})
    a.inner.add_edge_unchecked(exp, "has_delta", d)
    return exp


def test_adoption_weighs_fixes_against_harm():
    """P5c (adoption_safety v1.3.0): no absolute veto. net = 1.0*fixes +
    0.5*improved - 1.5*regressions - 0.25*lateral; adopted only at net >= 1."""
    a = _veto_agent()
    cases = {"clean": dict(flagged_changed=1, regressions=0),                       # 1.0
             "one_regression": dict(flagged_changed=2, regressions=1),              # 0.5 -> denied
             "outweighed": dict(flagged_changed=3, regressions=1),                  # 1.5 -> adopted
             "laterals": dict(flagged_changed=2, regressions=0, lateral_changes=3),  # 1.25 -> adopted
             "many_laterals": dict(flagged_changed=1, regressions=0, lateral_changes=1),   # 0.75 -> denied
             "improved": dict(flagged_changed=1, regressions=1, improved_changes=3),        # 1.0 -> adopted
             "nothing": dict(flagged_changed=0, regressions=0)}                     # 0 -> denied
    exps = {k: _exp(a, **v) for k, v in cases.items()}
    refuted = _exp(a, outcome="refuted", flagged_changed=0, regressions=3)
    unreported = _exp(a)
    a.inner.run_rules()
    at = lambda n: a.s.node(n)["attrs"]
    denied = {k for k, n in exps.items() if at(n).get("adopt_denied")}
    assert denied == {"one_regression", "many_laterals", "nothing"}, denied
    assert at(exps["outweighed"])["weighed_net"] == 1.5 and at(exps["one_regression"])["weighed_net"] == 0.5
    assert "weighed net" in at(exps["one_regression"])["adopt_denied_reason"]
    assert at(refuted).get("adopt_denied") and at(refuted)["weighed_net"] == -4.5   # weighed at ingest, any verdict
    assert not at(unreported).get("adopt_denied"), "no child report (an ARC trial): the gate stays silent"


def test_unflagged_change_is_a_regression_only_if_worse_in_the_frame():
    # same quality, different text: lateral, not a regression
    out, qc, qv = _score({"text": "I like to garden.", "flagged": False}, "got it", "Noted.")
    assert qc == qv and out["regressions"] == 0 and out["lateral_changes"] == 1 and out["changed_unflagged"] == 1
    # better quality: an improvement
    out, qc, qv = _score({"text": "What is your name?", "flagged": False}, "got it", "My name is Ocelot.")
    assert qv > qc and out["regressions"] == 0 and out["improved_changes"] == 1
    # a working turn that now fails: a regression even when both score 0 (the simple case)
    out, qc, qv = _score({"text": "What is a cat?", "flagged": False}, "got it", ERR)
    assert out["regressions"] == 1 and out["score"] == -1


def test_adoption_safety_is_frozen_and_machinery():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "adoption_safety" in _FROZEN_SEED_IDS
    seed = json.load(open(os.path.join(ROOT, "seeds", "adoption_safety.json")))
    assert seed["version"] == "1.3.0"
    rule = next(r for r in seed["rules"] if r["name"] == "adopt_denied_on_weighed_net")
    assert rule["effects"][0] == ["set_attr", "exp", "adopt_denied", True]
    # the veto matches on has_delta and names no protected type, so what keeps
    # the loop from varying it is the frozen seed: its rules' RuleSummary is
    # non-skippable (reflective_faculty provenance mirrors read the closed set)
    from domains.frozen_core import frozen_seed_ids_closed
    assert "adoption_safety" in frozen_seed_ids_closed()
