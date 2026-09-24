"""Focused tests for the WorldAdapter/DiscourseStore identity seam."""

from domains.reference_resolution import DiscourseConceptProvider, DiscourseStore
from substrate.world_adapter import WorldAdapter


def _referents(adapter, concept):
    return [
        node for node in adapter.s.nodes("DiscourseReferent")
        if adapter.s.node(node)["attrs"].get("concept") == concept
    ]


def test_repeated_current_topic_projection_reuses_one_canonical_referent():
    adapter = WorldAdapter(seeds=())

    adapter._set_current_topic("gate")
    referents = _referents(adapter, "gate")
    assert len(referents) == 1
    referent = referents[0]
    before = dict(adapter.s.node(referent)["attrs"])

    adapter._set_current_topic("gate")

    referents = _referents(adapter, "gate")
    assert referents == [referent]
    current_topics = list(adapter.inner.neighbours(adapter.agent, "current_topic"))
    assert len(current_topics) == 1
    assert list(adapter.inner.neighbours(current_topics[0], "refers_to")) == [referent]

    # Creating/replacing the compatibility projection is not a mention.
    assert dict(adapter.s.node(referent)["attrs"]) == before


def test_world_adapter_store_rehydrates_existing_referent_after_save_load(tmp_path):
    path = tmp_path / "referent-seam.json"
    adapter = WorldAdapter(seeds=())
    adapter._set_current_topic("gate")
    original = _referents(adapter, "gate")[0]
    adapter.save(path)

    restored = WorldAdapter.load(path)
    provider = DiscourseConceptProvider(
        restored.s,
        lookup=restored._concept_by_name,
        ensure=restored._ensure_concept,
    )
    store = DiscourseStore(restored.s, concept_provider=provider)

    assert store.ensure_referent("gate") == original
    assert _referents(restored, "gate") == [original]

    restored._set_current_topic("gate")
    assert _referents(restored, "gate") == [original]
