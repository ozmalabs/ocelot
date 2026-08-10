"""test_reframing_proposer — pins domains/reframing_proposer.py, the REFRAMING
PROPOSER (self-improvement #6): scan the agent's OWN faculties for a recurring
structure -> propose a candidate unifying abstraction (a Reframing node) -> TEST it
holds with the NOT-FOOLING-ITSELF faculty -> FLAG survivors for the creator.

DISCRIMINATIVE, donkey=0 (no LM, no fit). The proposer only SEQUENCES two held
faculties — analogical_thinking (the agent's own abstraction faculty) and
self_verification (verify_claim). Every verdict comes from verify_claim's Rust
term-tree over measured graph attrs.

  (1) PROPOSES A REAL, VERIFIED REFRAMING (headline): the scan surfaces a genuine
      recurring structure across the four collapse-plug faculties (they all realise
      the meta-shape `prediction_minus_observation` — predict -> residual -> learn),
      a Reframing is proposed, and it VERIFIES (control discriminates, grounded).
  (2) DISCRIMINATIVE (the crux): a SPURIOUS abstraction the instances do NOT actually
      share (`competitive_inhibition`) is PROPOSED-then-REJECTED — same instances,
      same grounding; only whether the abstraction holds flips the verdict. Real ->
      survives; spurious -> rejected.
  (3) FLAGGED-NOT-ASSERTED (honest boundary): a surviving candidate is a Reframing
      node flagged for_review, NOT installed/asserted as truth.
  (4) GRAPH-NATIVE audit: the Reframing/candidate is a graph node; the proposer uses
      analogical_thinking + self_verification; no new cognition/LLM; source audit.

Boots the real agent (WorldAdapter + load_all_seeds) once — the shape vocabulary
(seeds/shape_vocabulary.json) must be loaded for shape_hits to read meta-shapes.
"""
from __future__ import annotations

import json

import pytest

from domains import reframing_proposer as rp
import domains.analogical_thinking as at


@pytest.fixture(scope="module")
def agent():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    # donkey=0 guard: any teacher call increments; the battery asserts it stays 0.
    calls = {"n": 0}
    a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "D")[1])
    a._reframing_calls = calls
    return a


# ===========================================================================
# (1) PROPOSES A REAL, VERIFIED REFRAMING — the headline.
# ===========================================================================
def test_scan_surfaces_the_real_recurring_structure(agent):
    cands = rp.scan_for_recurring_structure(agent, min_instances=3, min_order=4)
    abstractions = {c["abstraction"] for c in cands}
    # the collapse-plug shape: all four faculties realise prediction_minus_observation
    assert "prediction_minus_observation" in abstractions
    real = next(c for c in cands if c["abstraction"] == "prediction_minus_observation")
    assert real["n_instances"] == 4
    assert set(real["instances"]) == set(rp.DEFAULT_FACULTIES)
    # corroborated by the agent's own analogy faculty at order 4 (meta-shape)
    assert real["order_n"] == 4 and real["analogous_pairs"]


def test_propose_and_verify_accepts_the_real_reframing(agent):
    _mt, defs = rp.introspect_faculties(agent)
    cands = rp.scan_for_recurring_structure(agent, min_instances=3, min_order=4)
    real = next(c for c in cands if c["abstraction"] == "prediction_minus_observation")
    node = rp.propose_reframing(agent, real)
    res = rp.verify_reframing(agent, node, defs)
    assert res["accepted"] is True
    assert res["discriminates"] is True
    assert res["grounded"] is True
    assert res["anchors"] == ["SensorAnchor"]
    # the verdict is written onto the graph node
    ra = agent.s.node(node)["attrs"]
    assert float(ra["verified"]) == 1.0


# ===========================================================================
# (2) DISCRIMINATIVE — a spurious abstraction is proposed-then-rejected. Same
# instances, same grounding; only whether the abstraction actually holds flips it.
# ===========================================================================
def test_spurious_abstraction_is_rejected(agent):
    _mt, defs = rp.introspect_faculties(agent)
    spurious = {
        "abstraction": "competitive_inhibition",   # the faculties do NOT do winner-take-all
        "kind": "meta_shape", "order_n": 4,
        "instances": sorted(rp.DEFAULT_FACULTIES),
        "n_instances": len(rp.DEFAULT_FACULTIES),
    }
    node = rp.propose_reframing(agent, spurious)
    res = rp.verify_reframing(agent, node, defs)
    assert res["accepted"] is False
    assert res["discriminates"] is False
    assert res["real_pass"] is False            # the abstraction does not hold on the instances
    assert "does NOT survive" in res["reason"]
    assert float(agent.s.node(node)["attrs"]["verified"]) == 0.0


def test_real_and_spurious_same_faculty_opposite_verdict(agent):
    """The load-bearing contrast: identical instances + grounding, the ONLY
    difference is whether the claimed abstraction actually holds across them — and
    the verdict flips. Same proposer, same verify path, no branch on which."""
    _mt, defs = rp.introspect_faculties(agent)
    insts = sorted(rp.DEFAULT_FACULTIES)
    real = {"abstraction": "prediction_minus_observation", "kind": "meta_shape",
            "order_n": 4, "instances": insts, "n_instances": len(insts)}
    fake = {"abstraction": "competitive_inhibition", "kind": "meta_shape",
            "order_n": 4, "instances": insts, "n_instances": len(insts)}
    r = rp.verify_reframing(agent, rp.propose_reframing(agent, real), defs)
    f = rp.verify_reframing(agent, rp.propose_reframing(agent, fake), defs)
    assert r["accepted"] is True
    assert f["accepted"] is False


# ===========================================================================
# (3) FLAGGED-NOT-ASSERTED — the honest boundary. A survivor stays a candidate.
# ===========================================================================
def test_survivor_is_flagged_for_review_not_installed_as_truth(agent):
    _mt, defs = rp.introspect_faculties(agent)
    cands = rp.scan_for_recurring_structure(agent, min_instances=3, min_order=4)
    real = next(c for c in cands if c["abstraction"] == "prediction_minus_observation")
    node = rp.propose_reframing(agent, real)
    res = rp.verify_reframing(agent, node, defs)
    ra = agent.s.node(node)["attrs"]
    assert res["accepted"] is True
    # verified, yet STILL flagged for the creator — not self-certified, not installed
    assert float(ra["verified"]) == 1.0
    assert float(ra["for_review"]) == 1.0
    # no Concept/Microtheory/Rule was minted asserting the abstraction as a held truth:
    # the only artifact is the Reframing candidate node itself.
    assert agent.s.node(node)["type"] == "Reframing"


# ===========================================================================
# (4) GRAPH-NATIVE audit — graph node + held faculties + no LLM + source audit.
# ===========================================================================
def test_reframing_is_a_graph_node_with_unifies_edges(agent):
    _mt, defs = rp.introspect_faculties(agent)
    cands = rp.scan_for_recurring_structure(agent, min_instances=3, min_order=4)
    real = next(c for c in cands if c["abstraction"] == "prediction_minus_observation")
    node = rp.propose_reframing(agent, real)
    sub = agent.s
    assert sub.node(node)["type"] == "Reframing"
    # instances stored as graph data + linked to the real faculty concepts
    stored = json.loads(sub.node(node)["attrs"]["instances"])
    assert set(stored) == set(rp.DEFAULT_FACULTIES)
    unified = {str(sub.node(t)["attrs"].get("name")) for t in sub.neighbours(node, "unifies")}
    assert set(rp.DEFAULT_FACULTIES) <= unified


def test_donkey_zero_no_llm(agent):
    """No model call anywhere in scan/propose/verify — the faculties are the
    agent's own held machinery."""
    before = agent._reframing_calls["n"]
    _mt, defs = rp.introspect_faculties(agent)
    cands = rp.scan_for_recurring_structure(agent, min_instances=3, min_order=4)
    real = next(c for c in cands if c["abstraction"] == "prediction_minus_observation")
    rp.verify_reframing(agent, rp.propose_reframing(agent, real), defs)
    assert agent._reframing_calls["n"] == before


def test_source_reuses_held_faculties_no_new_cognition():
    """Source audit: the proposer SEQUENCES the held faculties — it imports
    analogical_thinking (the abstraction faculty) and self_verification.verify_claim
    (the test faculty), and does NOT reimplement analogy scoring or the verdict gate,
    nor call any LLM."""
    import inspect
    src = inspect.getsource(rp)
    assert "import domains.analogical_thinking" in src
    assert "from domains.self_verification import Claim, verify_claim" in src
    # the decision is delegated to verify_claim, not re-decided here
    assert "verify_claim(agent, Claim(" in src
    # no reimplementation of the analogy exchange-rate or the verdict conjunction
    assert "def find_analogies" not in src
    assert "def verify_claim" not in src
    # no model/LLM invocation
    for banned in ("openai", "llm(", ".complete(", "gemma", "teacher_stub"):
        assert banned not in src.lower()


def test_shape_read_comes_from_the_agents_own_faculty(agent):
    """The recurring structure is the agent's OWN shape reading (shape_hits over the
    seeded meta-shape vocabulary), not a constant baked into the proposer."""
    _mt, defs = rp.introspect_faculties(agent)
    for name, text in defs.items():
        assert "prediction_minus_observation" in at.shape_hits(agent, text), name
