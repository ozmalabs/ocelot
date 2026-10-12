from domains.discourse_state import ensure_discourse_state, record_event
from substrate.world_adapter import WorldAdapter


def test_discourse_events_link_to_previous_event_in_same_state():
    agent = WorldAdapter(seeds=())
    state = ensure_discourse_state(agent, conversation_id="sequence-a")

    first = record_event(agent, state, kind="instruction")
    second = record_event(agent, state, kind="response")

    assert agent.s.node(first)["attrs"]["event_index"] == 0
    assert agent.s.node(second)["attrs"]["event_index"] == 1
    assert "predecessor_event_index" not in agent.s.node(first)["attrs"]
    assert agent.s.node(second)["attrs"]["predecessor_event_index"] == 0
    assert list(agent.inner.neighbours(second, "follows_event")) == [first]
    assert list(agent.inner.neighbours(first, "follows_event")) == []
    assert agent.s.node(state)["attrs"]["last_event_id"] == second


def test_discourse_event_sequence_rehydrates_legacy_state_and_stays_scoped():
    agent = WorldAdapter(seeds=())
    state_a = ensure_discourse_state(agent, conversation_id="sequence-a")
    state_b = ensure_discourse_state(agent, conversation_id="sequence-b")
    first_a = record_event(agent, state_a, kind="instruction")
    first_b = record_event(agent, state_b, kind="question")

    # Simulate a stale/recycled last-event handle from another conversation;
    # event_index and has_event are the authoritative recovery path.
    agent.inner.set_attr(state_a, "last_event_id", first_b)
    second_a = record_event(agent, state_a, kind="response")

    assert list(agent.inner.neighbours(second_a, "follows_event")) == [first_a]
    assert agent.s.node(second_a)["attrs"]["predecessor_event_index"] == 0
    assert first_b not in list(agent.inner.neighbours(second_a, "follows_event"))
    assert list(agent.inner.neighbours(first_b, "follows_event")) == []


def test_legacy_predecessor_without_index_keeps_edge_and_uses_scan_fallback():
    agent = WorldAdapter(seeds=())
    state = ensure_discourse_state(agent, conversation_id="sequence-legacy")
    legacy = agent.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "kind": "instruction"})
    agent.inner.add_edge_unchecked(state, "has_event", legacy, {})
    agent.inner.set_attr(state, "event_index", 1)
    agent.inner.set_attr(state, "last_event_id", legacy)

    following = record_event(agent, state, kind="response")

    assert list(agent.inner.neighbours(following, "follows_event")) == [legacy]
    assert "predecessor_event_index" not in agent.s.node(following)["attrs"]
