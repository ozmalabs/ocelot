"""Explicit uncertainty is a language-neutral native error disposition."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_explicit_uncertainty_is_not_released_as_generic_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "[unintelligible]",
        speech_act="statement",
        context={
            "interaction_mode": "turn_compatible",
            "interaction_relation": "turn_compatible",
            "literal_form": "fragment",
            "evidence": ["explicit_uncertainty", "explicit_failure", "discourse_state"],
        },
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert reply == "ERROR: no communicative response could be generated."
    assert interpretation["explicit_uncertainty"] == 1
    assert interpretation["explicit_failure"] == 1
    assert interpretation["cognitive_disposition"] == "error"
    assert interpretation["cognitive_goal"] == "error"
    assert interpretation["arbitration_basis"] == "explicit_failure"


def test_without_typed_uncertainty_the_existing_repair_path_remains_distinct():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse("[unintelligible]", speech_act="statement")
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation.get("explicit_uncertainty") == 0
    assert interpretation.get("cognitive_disposition") != "error"


def test_ordinary_uncertainty_does_not_become_error():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "Please—",
        speech_act="statement",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "continuation",
            "literal_form": "fragment",
            "evidence": ["explicit_uncertainty", "discourse_state"],
        },
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["explicit_uncertainty"] == 1
    assert interpretation["explicit_failure"] == 0
    assert interpretation.get("cognitive_disposition") != "error"
