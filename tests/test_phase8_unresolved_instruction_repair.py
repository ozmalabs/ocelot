"""Unresolved deictic instructions must enter the repair faculty."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_unresolved_anaphoric_instruction_asks_before_action():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse(
        "Move it there.", speech_act="instruction",
        context={"interaction_mode": "non_turn"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]

    assert attrs.get("comp_anaphor") == 1.0
    assert attrs.get("communication_route") == "ask_back"
    assert reply.rstrip().endswith("?")
    assert "it" in reply.lower() or "there" in reply.lower()
    # A graph lifecycle goal may still record that an instruction was
    # interpreted; the decisive boundary is that the unresolved referent was
    # routed to repair rather than enacted by the action faculty.


def test_object_pronoun_is_not_replaced_by_following_adverb():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse(
        "Move it now.", speech_act="instruction",
        context={"interaction_mode": "non_turn"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]

    assert attrs.get("comp_content") == "it"
    assert attrs.get("communication_route") == "ask_back"
    assert "it" in reply.lower()
