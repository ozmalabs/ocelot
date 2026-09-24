"""Native deliberation-to-production gate.

The older gate named ``ThoughtSegment``. The live conversational substrate
uses ``DeliberationExecutionTrace`` and ``DeliberationSettlement`` for this
boundary; production still releases only the monitor-cleared ``Committed``
node.
"""
from __future__ import annotations

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from domains import conceptualizer as cc
from domains.conversation_deliberation import materialize_deliberation


def test_native_deliberation_precedes_monitored_commit():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    cc.ensure_conceptualizer_rules(agent)
    goal = cc.mint_communicative_goal(
        agent, "inform", {"grey"}, {"id": "user", "observed": False})
    deliberation = materialize_deliberation(
        agent, goal=goal, candidates=[{
            "candidate_id": "grey_reply", "grounding": 1.0,
            "expected_value": 1.0, "residual_cost": 0.0,
            "consequence": 1.0, "novelty": 1.0,
            "execution_ready": 1.0, "outcome_status": "resolved",
        }])
    agent.inner.run_rules(3000)

    executions = list(agent.s.nodes("DeliberationExecutionTrace"))
    settlements = list(agent.s.nodes("DeliberationSettlement"))
    assert executions and settlements
    assert any(goal in agent.inner.neighbours(node, "for_goal")
               for node in executions)
    assert all(agent.s.node(node)["attrs"]["status"] == "resolved"
               for node in executions + settlements)
    assert agent.s.node(deliberation)["attrs"]["status"] == "resolved"

    cc.run_pipeline(agent, [{"form": "grey", "concept": "grey"}], rounds=2)
    committed = cc.read_committed(agent, goal)
    assert committed["committed"] is not None
    assert committed["utterance"] == "grey"
