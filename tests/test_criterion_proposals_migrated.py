"""Plan P6 (2026-10-10): the agent proposes criterion changes; a human adopts.

Pinned claims:
  * the cap grammar (reply_quality.assess, criteria >= 1.2.0) is inert while
    the held criterion has no caps, and a cap lowers exactly its pair when its
    condition holds;
  * the frozen rules decide recommended / goodhart_rejected / not_recommended
    from the measurements, prefer one recommendation in MDL order, and only a
    recorded human decision moves an awaiting proposal;
  * the seed is frozen and its types are protected;
  * applying a proposal is a human-run script that refuses an unrecommended one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import criterion_proposals as CP     # noqa: E402
from domains import reply_quality as rq           # noqa: E402
from substrate.world_adapter import WorldAdapter   # noqa: E402


def test_caps_are_inert_until_held_and_narrow_when_held():
    base = rq.criteria()
    assert not base.get("caps")
    clar_q, clar = "What else do you like to do for fun?", "what should I use to answer that?"
    assert rq.assess(clar_q, clar)["score"] == 1
    c = CP.apply_edits(base, [{"op": "cap", "inbound": "question", "reply": "clarification",
                               "when": "addressed_to_agent", "to": 0}])
    got = rq.assess(clar_q, clar, None, c)
    assert got["score"] == 0 and "-cap_question_clarification_addressed_to_agent" in got["reason"]
    # not addressed to the agent: untouched; other pairs: untouched
    assert rq.assess("What is fun?", clar, None, c)["score"] == rq.assess("What is fun?", clar)["score"]
    assert rq.assess("I like to garden.", "got it", None, c)["score"] == 1
    cell = CP.apply_edits(base, [{"op": "cell", "inbound": "statement", "reply": "greeting", "value": 2}])
    assert rq.assess("Hello, my name is someone.", "good day", None, cell)["score"] == 2
    assert base["score_table"]["statement"]["greeting"] == 1              # pure


def test_adopted_criterion_records_the_human_decision():
    base = rq.criteria()
    assert all(base["score_table"][ic]["definition"] == 0 for ic in base["score_table"])
    adopted = base["adopted_proposals"]
    assert adopted[0]["candidate"] == "cell:question->definition=0" and adopted[0]["test_gain"] > 0
    assert adopted[1]["human_authored"] is True and adopted[1]["approved_by"].startswith("human")


def _agent():
    a = WorldAdapter(seeds=())
    seed = json.load(open(os.path.join(ROOT, "seeds", "criterion_proposals.json")))
    pol = a.s.add_node("CriterionPolicy", dict(seed["nodes"][0]["attrs"]))
    a.inner.add_edge_unchecked(a.agent, "has_criterion_policy", pol)
    for r in seed["rules"]:
        a.inner.add_rule(r)
    return a


def _cand(cid, size, dev, test, p0, success):
    return {"id": cid, "edits": [], "size": size, "dev": {"kappa": 0.9}, "test": {"kappa": 0.9, "precision0": p0},
            "dev_gain": dev, "test_gain": test, "loop_success": 0.7, "success_delta": success}


def test_rules_decide_prefer_and_wait_for_a_human():
    a = _agent()
    base = {"test": {"kappa": 0.9}}
    rows = {"narrow": _cand("narrow", 1, 0.01, 0.0177, 0.99, -0.05),
            "broad": _cand("broad", 1, 0.01, 0.0177, 0.99, -0.08),       # same gain, bigger change to the loop
            "pair": _cand("pair", 2, 0.03, 0.0177, 0.99, -0.05),
            "imprecise": _cand("imprecise", 1, 0.01, 0.02, 0.7, 0.0),
            "goodhart": _cand("goodhart", 1, 0.0, -0.5, 0.99, 0.45),
            "dev_only": _cand("dev_only", 1, 0.02, 0.0, 0.99, -0.01)}
    nodes = {k: CP.mint(a, v, base, i) for i, (k, v) in enumerate(rows.items())}
    for _ in range(3):
        a.inner.run_rules()
    at = lambda k: a.s.node(nodes[k])["attrs"]
    assert {k: at(k)["verdict"] for k in rows} == {
        "narrow": "recommended", "broad": "recommended", "pair": "recommended", "imprecise": "not_recommended",
        "goodhart": "goodhart_rejected", "dev_only": "not_recommended"}
    assert [k for k in rows if at(k).get("preferred") == 1] == ["narrow"]
    assert at("narrow")["status"] == "awaiting_human" and at("goodhart")["status"] == "closed"
    a.inner.run_rules()
    assert at("narrow")["status"] == "awaiting_human", "nothing but a human decision moves it"
    CP.decide(a, nodes["narrow"], "approved", "test-human")
    CP.decide(a, nodes["broad"], "denied", "test-human")
    a.inner.run_rules()
    assert at("narrow")["status"] == "approved" and at("broad")["status"] == "denied"


def test_seed_is_frozen_and_protected():
    from substrate.boot_all import _FROZEN_SEED_IDS
    assert "criterion_proposals" in _FROZEN_SEED_IDS
    man = json.load(open(os.path.join(ROOT, "seeds", "frozen_core_manifest.json")))
    assert "criterion_proposals" in man["frozen_seed_ids"]
    types = json.load(open(os.path.join(ROOT, "seeds", "improvement_integrity.json")))["nodes"][0]["attrs"][
        "protected_node_types"]
    assert {"CriterionPolicy", "CriterionProposal"} <= set(types)


def test_apply_script_refuses_an_unrecommended_proposal(tmp_path):
    rep = {"criteria_version": rq.criteria()["version"],
           "all_minted": [{"id": "x", "verdict": "goodhart_rejected", "edits": []}]}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(rep))
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "apply_criterion_proposal.py"), str(p), "x",
                          "--by", "t", "--dry"], capture_output=True, text=True)
    assert out.returncode != 0 and "not recommended" in (out.stderr + out.stdout)
