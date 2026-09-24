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
