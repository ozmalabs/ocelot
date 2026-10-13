"""Plan P1 (2026-10-10): judge v2 -- reply quality gates fixes and adoption.

  * scripts/convo_child_run.score_probes: a changed flagged turn is a fix only
    if its new reply is at least acceptable-minimal (a receipt for a question
    is a broken fix); an unflagged turn is `repaired` only if its quality did
    not decrease;
  * seeds/adoption_safety.json v1.2.0 adopt_denied_on_quality_drop denies an
    Experiment whose child reported quality_drops > 0 or quality_delta < 0;
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
    for r in seed["rules"]:
        a.inner.add_rule(r)
    return a


def _exp(a, **attrs):
    exp = a.s.add_node("Experiment", dict({"outcome": "supported", "adopt_ready": True}, **attrs))
    d = a.s.add_node("SeedDelta", {"act_rule_varied": "x"})
    a.inner.add_edge_unchecked(exp, "has_delta", d)
    return exp


def test_quality_drop_vetoes_adoption():
    a = _veto_agent()
    dropped = _exp(a, quality_drops=1, quality_delta=0.1, regressions=0)
    worse = _exp(a, quality_drops=0, quality_delta=-0.05, regressions=0)
    fine = _exp(a, quality_drops=0, quality_delta=0.2, regressions=0)
    unreported = _exp(a, regressions=0)
    a.inner.run_rules()
    at = lambda n: a.s.node(n)["attrs"]
    assert at(dropped).get("adopt_denied") is True and "quality" in at(dropped)["adopt_denied_reason"]
    assert at(worse).get("adopt_denied") is True
    assert not at(fine).get("adopt_denied")
    assert not at(unreported).get("adopt_denied"), "no quality report: the veto stays silent"


def test_adoption_safety_is_frozen_and_machinery():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "adoption_safety" in _FROZEN_SEED_IDS
    seed = json.load(open(os.path.join(ROOT, "seeds", "adoption_safety.json")))
    assert seed["version"] == "1.2.0"
    rule = next(r for r in seed["rules"] if r["name"] == "adopt_denied_on_quality_drop")
    assert rule["effects"][0] == ["set_attr", "exp", "adopt_denied", True]
    # the veto matches on has_delta and names no protected type, so what keeps
    # the loop from varying it is the frozen seed: its rules' RuleSummary is
    # non-skippable (reflective_faculty provenance mirrors read the closed set)
    from domains.frozen_core import frozen_seed_ids_closed
    assert "adoption_safety" in frozen_seed_ids_closed()
