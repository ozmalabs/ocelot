"""Tranche 24: an adoption reopens the concerns it may now make answerable.

Pinned (all graph rules, on the production conversation profile):
  * an abstention is stamped with the repertoire epoch (count of Adoptions);
  * a promoted unanswered concern whose every experiment abstained is NOT
    reopened while the repertoire is unchanged, IS reopened once an Adoption
    exists, and is reopened at most once per epoch;
  * a concern with a judged (non-abstained) experiment is never reopened;
  * the scheduler requests the `concern` host action for a marked retry (its
    executor is otherwise only reached while a StandingConcern is pending);
  * variation_pick's abstention exclusion is epoch-scoped;
  * a re-promoted concern's builders read the live StandingConcern.
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


@pytest.fixture(scope="module")
def a():
    return E.boot(True, promote=False).adapter


def _concern(a, key, outcome="abstained", epoch=0):
    sc = a.s.add_node("SelfConcern", {"kind": "unanswered", "status": "promoted", "content": key})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    stn = a.s.add_node("StandingConcern", {"name": key, "status": "processed"})
    a.inner.add_edge_unchecked(sc, "promoted_to", stn)
    exp = a.s.add_node("Experiment", {"axis_tag": key, "status": "done", "outcome": outcome})
    d = a.s.add_node("SeedDelta", {"concern_key": key, "variation_op": "disposition_generalise",
                                   **({"variant_abstained": 1.0, "abstain_epoch": epoch} if outcome == "abstained" else {})})
    a.inner.add_edge_unchecked(exp, "has_delta", d)
    return sc


def _at(a, n):
    return a.s.node(n)["attrs"]


def test_reopen_waits_for_a_new_capability_then_fires_once_per_epoch(a):
    epoch = len(a.s.nodes("Adoption"))
    sc = _concern(a, "t24_probe_reopen", epoch=epoch)
    judged = _concern(a, "t24_probe_judged", outcome="refuted", epoch=epoch)
    a.inner.run_rules()
    assert not _at(a, sc).get("retry_requested"), "unchanged repertoire: the abstention stands"
    a.s.add_node("Adoption", {"rule_added": "t24_probe", "experiment_id": "probe"})
    a.inner.run_rules()
    at = _at(a, sc)
    assert at.get("retry_requested") == 1 and at.get("reopen_count") == 1
    assert at.get("reopened_at_epoch") == epoch + 1
    assert not _at(a, judged).get("retry_requested"), "a judged concern is not reopened"
    a.s.set_attr(sc, "retry_requested", 0)          # what the executor does
    a.inner.run_rules()
    assert not _at(a, sc).get("retry_requested"), "at most one reopen per repertoire epoch"


def test_scheduler_requests_the_concern_action_for_a_marked_retry():
    a = E.boot(True, promote=False).adapter          # own boot: one in-flight concern request at a time
    live = {r["name"] for r in a.inner.export_rules() if r.get("active", True)}
    assert {"supervise_requested_retry", "supervise_requested_retry_rearm", "irr_reopen_on_new_capability"} <= live
    sc = a.s.add_node("SelfConcern", {"kind": "unanswered", "status": "promoted", "retry_requested": 1})
    a.inner.run_rules()
    reqs = [n for n in a.s.nodes("HostActionRequest")
            if _at(a, n).get("action") == "concern" and _at(a, n).get("source_type") == "SelfConcern"]
    assert reqs and any(_at(a, n).get("source") == sc for n in reqs)


def test_abstention_stamp_and_epoch_scoped_exclusion_are_in_the_seeds():
    so = json.load(open(os.path.join(ROOT, "seeds", "self_optimisation.json")))
    close = next(r for r in so["rules"] if r["name"] == "close_abstained_variant")
    assert any(e[:3] == ["set_attr", "delta", "abstain_epoch"] for e in close["effects"])
    vo = json.load(open(os.path.join(ROOT, "seeds", "variation_ops.json")))
    prog = next(n for n in vo["nodes"] if n["type"] == "Program" and n["attrs"]["name"] == "variation_pick")
    assert '"key": "abstain_epoch"' in prog["attrs"]["program"]


def test_builders_read_the_live_standing_concern_after_repromotion(a):
    old = a.s.add_node("StandingConcern", {"name": "t24_probe_live", "status": "retired"})
    new = a.s.add_node("StandingConcern", {"name": "t24_probe_live", "status": "processed"})
    assert rf._live_standing_for_key(a.s, "t24_probe_live") == new
    assert rf._live_standing_for_key(a.s, "absent_key") is None
    assert old != new
