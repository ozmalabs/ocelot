"""The conversation ingress uses the native Concept.name index as a bounded
candidate-materialization seam; native intent rules retain referent authority.
"""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_message_ingress_materializes_only_indexed_concept_candidates():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    mid = agent.receive_utterance("Check the pressure.", speaker="alice")

    known = list(agent.inner.neighbours(agent.agent, "knows_concept"))
    names = {agent.s.node(node)["attrs"].get("name") for node in known}
    assert agent.inner.has_attr_index("Concept", "name")
    assert "pressure" in names
    # The old full vocabulary backfill creates thousands of edges. This path
    # keeps the evidence set bounded to concepts present in the event.
    assert len(known) < 100

    agent.comprehend()
    mentions = list(agent.inner.neighbours(mid, "has_mention"))
    referred_names = {
        agent.s.node(concept)["attrs"].get("name")
        for mention in mentions
        for concept in agent.inner.neighbours(mention, "refers_to")
        if agent.s.has_node(concept)
    }
    assert "pressure" in referred_names


def _referent_names(agent, mid):
    return {
        agent.s.node(concept)["attrs"].get("name")
        for mention in agent.inner.neighbours(mid, "has_mention")
        for concept in agent.inner.neighbours(mention, "refers_to")
        if agent.s.has_node(concept)
    }


def test_indexed_ingress_is_referent_equivalent_to_full_ledger():
    """The optimization changes materialization cost, not native resolution."""
    indexed = WorldAdapter(seeds=())
    full = WorldAdapter(seeds=())
    load_all_seeds(indexed)
    load_all_seeds(full)

    indexed_mid = indexed.receive_utterance("Check the pressure.", speaker="alice")
    full_mid = full.receive_utterance("Check the pressure.", speaker="alice")
    full._backfill_knows_concept()
    indexed.comprehend()
    full.comprehend()

    assert _referent_names(indexed, indexed_mid) == _referent_names(full, full_mid)
    indexed_edges = len(indexed.inner.neighbours(indexed.agent, "knows_concept"))
    full_edges = len(full.inner.neighbours(full.agent, "knows_concept"))
    assert indexed_edges < 100
    assert full_edges > indexed_edges


def test_question_ingress_matches_full_ledger_with_bounded_candidates():
    """Meta/self questions need their held graph evidence, not global links."""
    indexed = WorldAdapter(seeds=())
    full = WorldAdapter(seeds=())
    load_all_seeds(indexed)
    load_all_seeds(full)
    full._backfill_knows_concept()

    indexed_reply = indexed.converse(
        "How are you organised?", speech_act="question")
    full_reply = full.converse(
        "How are you organised?", speech_act="question")
    indexed_mid = indexed._last_turn_inbound
    full_mid = full._last_turn_inbound
    indexed_i = indexed.s.node(indexed_mid)["attrs"][
        "communication_interpretation_id"]
    full_i = full.s.node(full_mid)["attrs"][
        "communication_interpretation_id"]

    assert indexed_reply == full_reply
    assert indexed.s.node(indexed_i)["attrs"].get("cognitive_disposition") == \
        full.s.node(full_i)["attrs"].get("cognitive_disposition") == "answer"
    assert indexed._native_reflective_answer_selected(indexed_mid)
    assert full._native_reflective_answer_selected(full_mid)
    assert any(indexed.s.node(node)["attrs"].get("status") == "released"
               for node in indexed.s.nodes("ProductionGateReceipt")
               if indexed.s.node(node)["attrs"].get("turn_message_id")
               == int(indexed_mid.value))
    assert len(indexed.inner.neighbours(indexed.agent, "knows_concept")) < 100
    assert len(full.inner.neighbours(full.agent, "knows_concept")) > 100
