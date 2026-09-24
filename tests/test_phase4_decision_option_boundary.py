"""Phase 4 audit: legacy conversation values are not Phase 4A evidence."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_decision_option_is_not_promoted_without_phase4_dimensions():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    mid = agent.receive_utterance("A residual remains.", speech_act="statement")
    agent._record_conversation_decision("residual_inquiry", mid)

    options = [
        node for node in agent.s.nodes("DecisionOption")
        if agent.s.node(node)["attrs"].get("token") == "residual_inquiry"
    ]
    assert len(options) == 1
    attrs = agent.s.node(options[0])["attrs"]
    assert "consequence" not in attrs
    assert "novelty" not in attrs

    # Phase 4A requires explicit evidence-bearing dimensions.  The live
    # bridge must therefore expose no candidate rather than infer mappings.
    agent._record_live_discourse_state(mid, None)
    agent._bind_live_goals_and_deliberation(mid)
    assert not list(agent.s.nodes("DeliberativeCandidate"))
