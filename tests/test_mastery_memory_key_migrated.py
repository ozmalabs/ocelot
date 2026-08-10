"""MASTERY WAS KILLING THE PROCESS — the migrated gate.

`ed_store_mastered_capability_by_structural_body_shape` keys its memory by
`episode.body_capability_signature`, which NOTHING in any seed writes. Minted
anyway, the part carried a `name` (a StringConcat — always a present string)
beside a `signature` of None: exactly `load_parts`'s malformed case, which
panics and poisons the substrate mutex.

The rule's own guard is `status == 'mastered'`, so the panic fired AT THE MOMENT
OF MASTERY. Runs 4, 5 and 6 all reached retention/mastery at 142-146 trials and
died there — which is why this line has never recorded an ordinal advance.

The remedy is not to default the signature. It is to refuse to mint a codebook
part that has no key, and to make that refusal visible rather than silent.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.seed_loader import manifest_for                          # noqa: E402
from substrate.world_adapter import WorldAdapter                        # noqa: E402


def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(manifest_for("embodied_development"),
                                   agent.agent)
    return agent


def _mastered(agent, *, signature=None):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode",
                               {"development_learning_active": 1})
    agent.inner.add_edge_unchecked(
        agent.agent, "has_embodied_development_episode", episode)
    if signature is not None:
        agent.inner.set_attr(episode, "body_capability_signature", signature)
    instance = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "spontaneous_general_movement", "goal": "spontaneous_variation",
        "evidence_kind": "spontaneous_configuration_change",
        "status": "mastered", "ordinal": 0, "integer_native": 1})
    agent.inner.add_edge_unchecked(
        episode, "has_embodied_developmental_capability", instance)
    agent.inner.run_rules()
    return episode, instance


def _memories(agent):
    return list(agent.s.nodes("EmbodiedDevelopmentalCapabilityMemory"))


def test_a_mastered_capability_with_no_body_key_mints_no_codebook_part():
    """THE CRASH, GATED. A part with a name and a null signature is exactly
    what `load_parts` panics on."""
    agent = _agent()
    _episode, _instance = _mastered(agent)
    assert _memories(agent) == []


def test_no_part_anywhere_carries_a_name_beside_a_null_signature():
    """The panic predicate itself, asserted over the whole graph."""
    agent = _agent()
    _mastered(agent)
    for node in agent.s.nodes("EmbodiedDevelopmentalCapabilityMemory"):
        attrs = agent.s.node(node)["attrs"]
        if "name" in attrs and attrs.get("name") is not None:
            assert attrs.get("signature") is not None


def test_the_refusal_is_recorded_rather_than_silent():
    """A part silently dropped from a codebook is the disease being removed.
    The withheld memory must be legible, and must say WHY."""
    agent = _agent()
    _episode, instance = _mastered(agent)
    attrs = agent.s.node(instance)["attrs"]
    assert attrs["mastery_memory_withheld"] == 1
    assert "body_capability_signature" in attrs["mastery_memory_withheld_reason"]


def test_mastery_itself_is_not_blocked_by_the_missing_key():
    """Only the cross-body transfer memory is withheld; the developmental
    advance is untouched."""
    agent = _agent()
    _episode, instance = _mastered(agent)
    assert agent.s.node(instance)["attrs"]["status"] == "mastered"


def test_a_keyed_episode_still_stores_its_memory():
    """The guard must not cost the capability where the key exists."""
    agent = _agent()
    _episode, instance = _mastered(agent, signature="body-shape-42")
    memories = _memories(agent)
    assert len(memories) == 1
    attrs = agent.s.node(memories[0])["attrs"]
    assert attrs["signature"] == "body-shape-42"
    assert "mastery_memory_withheld" not in agent.s.node(instance)["attrs"]


def test_the_withheld_marker_is_recorded_once():
    agent = _agent()
    _episode, instance = _mastered(agent)
    for _ in range(3):
        agent.inner.run_rules()
    assert agent.s.node(instance)["attrs"]["mastery_memory_withheld"] == 1
