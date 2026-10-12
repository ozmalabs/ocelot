"""Endemic self-improvement on the PRODUCTION path (tranche 21).

Pinned claims (each was a measured production defect):
  * the daemon's default `conversation` seed profile carries the
    self-improvement loop (self-promotion, the variation repertoire, judges,
    retry, adoption-safety veto, integrity list, comprehension self-observation);
  * a concern already routed to the experiment pipeline ('replay' head) reaches
    the experiment composer even when its own content words ground
    'comprehend' -- it used to dead-end in the comprehension composer;
  * the graph-requested dispatch host action stays alive while a dispatched
    child is running, so its result is ingested (it used to stall for good).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.reflective_faculty as rf          # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.boot_profiles import (             # noqa: E402
    CONVERSATION_SELF_IMPROVEMENT_ANCHORS, load_conversation_seed_profile)


def _profile_agent():
    a = WorldAdapter(seeds=())
    rep = load_conversation_seed_profile(a)
    assert rep.get("selection_complete") and not rep.get("failed")
    return a, rep


def test_conversation_profile_carries_the_self_improvement_loop():
    a, rep = _profile_agent()
    loaded = set(rep.get("loaded_seed_ids") or ())
    assert CONVERSATION_SELF_IMPROVEMENT_ANCHORS <= loaded, CONVERSATION_SELF_IMPROVEMENT_ANCHORS - loaded
    for t in ("SelfPromotionPolicy", "ImprovementIntegrity", "VariationOp", "InstructionRetryPolicy"):
        assert list(a.s.nodes(t)), t


def test_replay_routed_concern_reaches_the_experiment_composer():
    a, _ = _profile_agent()
    heads = ["test", "replay", "send", "judge", "adopt", "comprehend"]
    assert rf._pick_composer(a.s, a.inner, a.agent, heads) == "experiment"
    # a plain comprehension concern without the experiment bundle still goes to comprehension
    assert rf._pick_composer(a.s, a.inner, a.agent, ["comprehend"]) == "comprehension"


def test_dispatch_host_action_stays_alive_while_a_child_runs(monkeypatch, tmp_path):
    import jabberwock_daemon as jd
    import domains.experiment_dispatch as ed
    calls = []
    monkeypatch.setattr(ed, "scan_and_dispatch", lambda adapter, runs: calls.append(runs))
    a = WorldAdapter(seeds=())
    e = a.s.add_node("Experiment", {"status": "running", "game": "conversation"})
    assert jd._dispatch_tick(a, str(tmp_path)) == {"host_action_deferred": True}
    a.s.set_attr(e, "status", "done")
    assert jd._dispatch_tick(a, str(tmp_path)) is None
    assert len(calls) == 2
